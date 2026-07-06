"""Service SMS Twilio — Métro-Taxi.

Envoie un SMS à tous les chauffeurs validés à chaque nouvelle course broadcast.

Mode DRY-RUN :
- Si TWILIO_ENABLED != "true" dans .env → aucun SMS réel envoyé.
- Les envois qui *auraient* eu lieu sont loggés en INFO pour audit.
- Utile pour tester l'intégration sans coût, et pour désactiver rapidement en cas d'urgence.

Le kill-switch peut être basculé à la volée depuis l'admin (endpoint /admin/twilio/toggle).
"""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from typing import Iterable

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
except ImportError:  # pragma: no cover
    Client = None  # type: ignore
    TwilioRestException = Exception  # type: ignore


logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    """Kill-switch global lu depuis l'env à chaque appel (rechargeable à chaud)."""
    return os.environ.get("TWILIO_ENABLED", "false").strip().lower() == "true"


def _get_client() -> Client | None:
    sid = os.environ.get("TWILIO_ACCOUNT_SID")
    token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not sid or not token or Client is None:
        return None
    return Client(sid, token)


def _normalize_fr_phone(raw: str | None) -> str | None:
    """Normalise un numéro français en E.164 (+33...).

    Accepte : 0612345678, 06 12 34 56 78, +33612345678, 33612345678, 33 6 12 34 56 78.
    Rejette les numéros manifestement invalides (moins de 9 chiffres significatifs).
    """
    if not raw:
        return None
    # Ne garder que chiffres et un éventuel + de tête
    cleaned = re.sub(r"[^\d+]", "", raw)
    if cleaned.startswith("+33"):
        digits = cleaned[3:]
    elif cleaned.startswith("33") and len(cleaned) >= 11:
        digits = cleaned[2:]
    elif cleaned.startswith("0"):
        digits = cleaned[1:]
    else:
        digits = cleaned.lstrip("+")

    # Doit rester 9 chiffres après indicatif (numéros FR)
    if len(digits) != 9 or not digits.isdigit():
        return None
    return "+33" + digits


def _short(text: str | None, max_len: int = 30) -> str:
    """Tronque une adresse pour ne pas exploser le SMS."""
    if not text:
        return "?"
    txt = text.strip()
    if len(txt) <= max_len:
        return txt
    return txt[: max_len - 1].rstrip() + "…"


def _build_sms_body(
    *,
    prenom: str,
    depart: str,
    arrivee: str,
    heure: str,
    nb_pax: int,
    km: float,
) -> str:
    """Construit le corps du SMS de nouvelle course.

    Format cible (145 chars max = 1 SMS = 0,075€) :
        Metro-Taxi: {prenom} demande un trajet {depart} -> {arrivee}
        pour {heure}, {nb} pers, ~{km} km.
        SOS {sos}. Prends-le: {url}
    """
    sos = os.environ.get("TWILIO_SOS_PHONE", "0668550019")
    url = os.environ.get("TWILIO_APP_URL", "https://metro-taxi.com")
    return (
        f"Metro-Taxi: {prenom} demande un trajet "
        f"{_short(depart)} -> {_short(arrivee)} "
        f"pour {heure}, {nb_pax} pers, ~{km:.0f} km. "
        f"SOS {sos}. Prends-le: {url}"
    )


async def send_ride_broadcast_sms(
    *,
    ride_id: str,
    user_first_name: str,
    pickup_address: str,
    destination_address: str,
    distance_km: float,
    passengers_count: int,
    drivers: Iterable[dict],
) -> dict:
    """Envoie (ou simule) un SMS de nouvelle course à chaque chauffeur validé.

    Retour : dict {"sent": int, "failed": int, "dry_run": bool, "skipped_no_phone": int}
    Fire-and-forget côté appelant (via asyncio.create_task).
    """
    heure = datetime.now().strftime("%H:%M")
    body = _build_sms_body(
        prenom=user_first_name or "Un usager",
        depart=pickup_address or "?",
        arrivee=destination_address or "?",
        heure=heure,
        nb_pax=max(1, int(passengers_count or 1)),
        km=max(0.0, float(distance_km or 0)),
    )

    dry_run = not _is_enabled()
    from_number = os.environ.get("TWILIO_PHONE_NUMBER")

    stats = {"sent": 0, "failed": 0, "dry_run": dry_run, "skipped_no_phone": 0}

    if not from_number:
        logger.warning("[TwilioSMS] TWILIO_PHONE_NUMBER manquant — abort")
        stats["failed"] = -1
        return stats

    client = _get_client() if not dry_run else None

    for drv in drivers:
        raw = drv.get("phone") or drv.get("phone_number") or ""
        to = _normalize_fr_phone(raw)
        if not to:
            stats["skipped_no_phone"] += 1
            logger.info(
                "[TwilioSMS] SKIP driver=%s raison=phone_invalide raw=%r",
                drv.get("id"), raw,
            )
            continue

        if dry_run:
            logger.info(
                "[TwilioSMS][DRY-RUN] ride=%s driver=%s to=%s body=%r",
                ride_id, drv.get("id"), to, body,
            )
            stats["sent"] += 1
            continue

        try:
            client.messages.create(from_=from_number, to=to, body=body)  # type: ignore[union-attr]
            stats["sent"] += 1
        except TwilioRestException as exc:
            logger.warning(
                "[TwilioSMS] ERROR ride=%s driver=%s to=%s code=%s msg=%s",
                ride_id, drv.get("id"), to, getattr(exc, "code", "?"), str(exc)[:200],
            )
            stats["failed"] += 1
        except Exception as exc:
            logger.exception("[TwilioSMS] Unexpected error: %s", exc)
            stats["failed"] += 1

    logger.info("[TwilioSMS] ride=%s stats=%s", ride_id, stats)
    return stats
