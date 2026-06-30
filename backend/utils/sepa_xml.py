"""
SEPA Credit Transfer batch file generator (pain.001.001.03).

Génère un fichier XML conforme à la norme SEPA SCT (Single Euro Payments Area —
Credit Transfer) que l'administrateur peut uploader dans son interface bancaire pro
(Société Générale, BNP, etc.) pour exécuter en 1 clic tous les virements de la semaine
vers les chauffeurs Métro-Taxi.

Référence norme : ISO 20022 pain.001.001.03
Doc Société Générale : https://entreprises.societegenerale.fr/preferences-virement-sepa
"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


_IBAN_CLEAN_RE = re.compile(r"\s+")
_IBAN_VALID_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$")
_BIC_VALID_RE = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")


def clean_iban(iban: str) -> str:
    """Normalise un IBAN : retire les espaces, met en majuscules."""
    if not iban:
        return ""
    return _IBAN_CLEAN_RE.sub("", iban).upper()


def is_valid_iban(iban: str) -> bool:
    """Valide le format d'un IBAN (longueur, checksum mod-97)."""
    iban = clean_iban(iban)
    if not _IBAN_VALID_RE.match(iban):
        return False
    # Mod-97 checksum (ISO 7064)
    rearranged = iban[4:] + iban[:4]
    numeric = ""
    for ch in rearranged:
        if ch.isdigit():
            numeric += ch
        else:
            numeric += str(ord(ch) - 55)
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


def is_valid_bic(bic: str) -> bool:
    if not bic:
        return False
    return bool(_BIC_VALID_RE.match(bic.strip().upper()))


def _clean_name(name: str, max_len: int = 70) -> str:
    """Nettoie un nom pour qu'il passe la validation SEPA (caractères latin de base)."""
    if not name:
        return "Beneficiaire"
    # Remove characters not in SEPA-allowed charset
    cleaned = re.sub(r"[^A-Za-z0-9 /\-?:().,'+]", " ", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_len] or "Beneficiaire"


def _format_amount(amount: float) -> str:
    """Format SEPA: 2 decimals, dot separator."""
    d = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{d:.2f}"


@dataclass
class SEPACreditTransfer:
    """Une instruction de virement vers un chauffeur."""
    end_to_end_id: str           # Identifiant unique (ex: ride_id ou earning_id)
    creditor_name: str           # Nom du chauffeur
    creditor_iban: str           # IBAN du chauffeur
    creditor_bic: str = ""       # BIC du chauffeur (optionnel pour SEPA intra-zone)
    amount_eur: float = 0.0      # Montant en EUR (>0)
    remittance_info: str = ""    # Libellé qui apparaît sur le relevé du chauffeur


@dataclass
class SEPABatchResult:
    message_id: str
    payment_info_id: str
    execution_date: str
    transactions_count: int
    total_amount_eur: str
    xml_bytes: bytes
    filename: str


def generate_sepa_batch_xml(
    transfers: list[SEPACreditTransfer],
    debtor_name: str,
    debtor_iban: str,
    debtor_bic: str,
    execution_date: str | None = None,
    initiator_name: str | None = None,
) -> SEPABatchResult:
    """Génère un fichier XML SEPA pain.001.001.03 prêt à uploader dans la banque.

    :param transfers: liste des virements à exécuter.
    :param debtor_name: nom du donneur d'ordre (ex: "Metro-Taxi").
    :param debtor_iban: IBAN du donneur d'ordre.
    :param debtor_bic: BIC du donneur d'ordre.
    :param execution_date: date d'exécution souhaitée (YYYY-MM-DD). Default = aujourd'hui.
    :param initiator_name: nom de l'initiateur (= debtor_name si non fourni).
    :raises ValueError: si une donnée est invalide (IBAN, BIC, montant).
    """
    if not transfers:
        raise ValueError("Aucun virement à inclure dans le batch SEPA.")

    debtor_iban = clean_iban(debtor_iban)
    if not is_valid_iban(debtor_iban):
        raise ValueError(f"IBAN donneur d'ordre invalide : {debtor_iban}")
    if not is_valid_bic(debtor_bic):
        raise ValueError(f"BIC donneur d'ordre invalide : {debtor_bic}")

    now = datetime.now(timezone.utc)
    if not execution_date:
        execution_date = now.strftime("%Y-%m-%d")

    message_id = f"METROTAXI-{now.strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
    payment_info_id = f"PMT-{now.strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    initiator = _clean_name(initiator_name or debtor_name)
    creation_dt_iso = now.strftime("%Y-%m-%dT%H:%M:%S")

    # Validation préalable de tous les transferts
    cleaned_transfers: list[tuple[SEPACreditTransfer, str]] = []
    total = Decimal("0.00")
    for t in transfers:
        if t.amount_eur is None or t.amount_eur <= 0:
            raise ValueError(f"Montant invalide ({t.amount_eur}) pour {t.creditor_name}")
        iban = clean_iban(t.creditor_iban)
        if not is_valid_iban(iban):
            raise ValueError(f"IBAN chauffeur invalide pour {t.creditor_name} : {t.creditor_iban}")
        amount_str = _format_amount(t.amount_eur)
        total += Decimal(amount_str)
        cleaned_transfers.append((t, iban))

    total_str = f"{total:.2f}"

    # Construction XML pain.001.001.03
    ns = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"
    root = Element("Document", attrib={"xmlns": ns})
    cstmr = SubElement(root, "CstmrCdtTrfInitn")

    # GroupHeader
    grp = SubElement(cstmr, "GrpHdr")
    SubElement(grp, "MsgId").text = message_id
    SubElement(grp, "CreDtTm").text = creation_dt_iso
    SubElement(grp, "NbOfTxs").text = str(len(cleaned_transfers))
    SubElement(grp, "CtrlSum").text = total_str
    initg = SubElement(grp, "InitgPty")
    SubElement(initg, "Nm").text = initiator

    # PaymentInformation block (1 seul, contenant tous les transferts)
    pmt = SubElement(cstmr, "PmtInf")
    SubElement(pmt, "PmtInfId").text = payment_info_id
    SubElement(pmt, "PmtMtd").text = "TRF"
    SubElement(pmt, "BtchBookg").text = "true"
    SubElement(pmt, "NbOfTxs").text = str(len(cleaned_transfers))
    SubElement(pmt, "CtrlSum").text = total_str

    pmt_tp = SubElement(pmt, "PmtTpInf")
    svc_lvl = SubElement(pmt_tp, "SvcLvl")
    SubElement(svc_lvl, "Cd").text = "SEPA"

    SubElement(pmt, "ReqdExctnDt").text = execution_date

    # Debtor (= donneur d'ordre = Métro-Taxi)
    dbtr = SubElement(pmt, "Dbtr")
    SubElement(dbtr, "Nm").text = _clean_name(debtor_name)

    dbtr_acct = SubElement(pmt, "DbtrAcct")
    dbtr_id = SubElement(dbtr_acct, "Id")
    SubElement(dbtr_id, "IBAN").text = debtor_iban

    dbtr_agt = SubElement(pmt, "DbtrAgt")
    fin = SubElement(dbtr_agt, "FinInstnId")
    SubElement(fin, "BIC").text = debtor_bic.strip().upper()

    SubElement(pmt, "ChrgBr").text = "SLEV"

    # Chaque transfert
    for t, creditor_iban in cleaned_transfers:
        cdt_tx = SubElement(pmt, "CdtTrfTxInf")
        pmt_id = SubElement(cdt_tx, "PmtId")
        SubElement(pmt_id, "EndToEndId").text = (t.end_to_end_id or "NOTPROVIDED")[:35]

        amt = SubElement(cdt_tx, "Amt")
        instd = SubElement(amt, "InstdAmt", attrib={"Ccy": "EUR"})
        instd.text = _format_amount(t.amount_eur)

        if t.creditor_bic and is_valid_bic(t.creditor_bic):
            cdtr_agt = SubElement(cdt_tx, "CdtrAgt")
            cdtr_fin = SubElement(cdtr_agt, "FinInstnId")
            SubElement(cdtr_fin, "BIC").text = t.creditor_bic.strip().upper()

        cdtr = SubElement(cdt_tx, "Cdtr")
        SubElement(cdtr, "Nm").text = _clean_name(t.creditor_name)

        cdtr_acct = SubElement(cdt_tx, "CdtrAcct")
        cdtr_id = SubElement(cdtr_acct, "Id")
        SubElement(cdtr_id, "IBAN").text = creditor_iban

        if t.remittance_info:
            rmt = SubElement(cdt_tx, "RmtInf")
            SubElement(rmt, "Ustrd").text = _clean_name(t.remittance_info, max_len=140)

    # Pretty-print + UTF-8 BOM not needed
    raw = tostring(root, encoding="utf-8", xml_declaration=True)
    pretty = minidom.parseString(raw).toprettyxml(indent="  ", encoding="utf-8")

    filename = f"sepa_metrotaxi_{now.strftime('%Y%m%d')}_{message_id[-8:]}.xml"

    return SEPABatchResult(
        message_id=message_id,
        payment_info_id=payment_info_id,
        execution_date=execution_date,
        transactions_count=len(cleaned_transfers),
        total_amount_eur=total_str,
        xml_bytes=pretty,
        filename=filename,
    )
