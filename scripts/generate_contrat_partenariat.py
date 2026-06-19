"""
Génère un CONTRAT DE PARTENARIAT MÉTRO-TAXI propre format A4 PDF.
Style document juridique professionnel avec en-tête logo officiel.
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Paragraph, Frame
from PIL import Image as PILImage

OUT = Path("/app/frontend/public/marketing/contrat_partenariat_taxiphone_v2.pdf")
LOGO = Path("/app/frontend/public/icons/metro-taxi-logo.png")

YELLOW = HexColor("#FFD60A")
BLUE = HexColor("#0A84FF")
DARK = HexColor("#0A0A0A")
GRAY = HexColor("#6E6E73")
LIGHT = HexColor("#F5F5F7")

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


def draw_header(c):
    # Bandeau noir en-tête (50mm haut)
    c.setFillColor(DARK)
    c.rect(0, PAGE_H - 50 * mm, PAGE_W, 50 * mm, stroke=0, fill=1)

    # Logo à gauche (35mm)
    try:
        c.drawImage(
            str(LOGO),
            MARGIN, PAGE_H - 43 * mm,
            width=30 * mm, height=30 * mm,
            preserveAspectRatio=True, mask='auto'
        )
    except Exception:
        pass

    # Nom + slogan
    c.setFillColor(YELLOW)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(MARGIN + 36 * mm, PAGE_H - 20 * mm, "MÉTRO-TAXI")

    c.setFillColor(white)
    c.setFont("Helvetica", 10)
    c.drawString(MARGIN + 36 * mm, PAGE_H - 27 * mm, "Covoiturage VTC • Transbordement Intelligent")
    c.drawString(MARGIN + 36 * mm, PAGE_H - 32 * mm, "Île-de-France")

    # Right side - coordonnées
    c.setFillColor(YELLOW)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 20 * mm, "metro-taxi.com")
    c.setFillColor(white)
    c.setFont("Helvetica", 8)
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 26 * mm, "contact@metro-taxi.com")
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 31 * mm, "Tél : 06 05 78 64 25")

    # Ligne jaune sous header
    c.setFillColor(YELLOW)
    c.rect(0, PAGE_H - 52 * mm, PAGE_W, 2 * mm, stroke=0, fill=1)


def draw_footer(c, page_num=1):
    y = 15 * mm
    c.setFillColor(YELLOW)
    c.rect(0, y, PAGE_W, 1.5 * mm, stroke=0, fill=1)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN, y - 5 * mm, "Métro-Taxi — Saint-Denis (93) • SIRET 918 687 864 • R.C.S. Bobigny")
    c.drawRightString(PAGE_W - MARGIN, y - 5 * mm, f"Page {page_num} / 1 — v2 du 12/06/2026")


def draw_section_title(c, y, text):
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 10.5)
    c.drawString(MARGIN, y, text)
    # underline jaune
    c.setFillColor(YELLOW)
    c.rect(MARGIN, y - 1.3 * mm, len(text) * 2.2, 0.7 * mm, stroke=0, fill=1)
    return y - 5 * mm


def draw_body(c, y, text, font_size=8.5, max_width=PAGE_W - 2 * MARGIN, bold=False, color=DARK):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", font_size)
    # Manual wrap
    words = text.split()
    line = ""
    line_h = font_size * 1.3
    for w in words:
        candidate = (line + " " + w).strip()
        if c.stringWidth(candidate, "Helvetica-Bold" if bold else "Helvetica", font_size) > max_width:
            c.drawString(MARGIN, y, line)
            y -= line_h
            line = w
        else:
            line = candidate
    if line:
        c.drawString(MARGIN, y, line)
        y -= line_h
    return y


def draw_bullet(c, y, text, font_size=8.5):
    c.setFillColor(YELLOW)
    c.circle(MARGIN + 1.5 * mm, y + 1 * mm, 0.8 * mm, stroke=0, fill=1)
    c.setFillColor(DARK)
    c.setFont("Helvetica", font_size)
    return draw_body(c, y, text, font_size=font_size, max_width=PAGE_W - 2 * MARGIN - 6 * mm) - 0 * mm


def draw_rem_table(c, y):
    """Tableau Rémunération 3 plans"""
    headers = ["Plan d'abonnement", "Prix TTC", "Commission partenaire (15%)"]
    rows = [
        ["24 HEURES", "6,99 €", "1,05 €"],
        ["7 JOURS",   "19,99 €", "3,00 €"],
        ["30 JOURS",  "53,99 €", "8,10 €"],
    ]
    col_w = [(PAGE_W - 2 * MARGIN) * 0.4, (PAGE_W - 2 * MARGIN) * 0.25, (PAGE_W - 2 * MARGIN) * 0.35]
    row_h = 7 * mm

    # Header row (yellow)
    c.setFillColor(YELLOW)
    c.rect(MARGIN, y - row_h, sum(col_w), row_h, stroke=0, fill=1)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 9.5)
    x = MARGIN + 2 * mm
    for i, h in enumerate(headers):
        c.drawString(x, y - row_h + 2.5 * mm, h)
        x += col_w[i]
    y -= row_h

    # Data rows
    for ri, row in enumerate(rows):
        if ri % 2 == 0:
            c.setFillColor(LIGHT)
            c.rect(MARGIN, y - row_h, sum(col_w), row_h, stroke=0, fill=1)
        c.setFillColor(DARK)
        c.setFont("Helvetica", 9.5)
        x = MARGIN + 2 * mm
        for i, cell in enumerate(row):
            if i == 0:
                c.setFont("Helvetica-Bold", 9.5)
            else:
                c.setFont("Helvetica", 9.5)
            c.drawString(x, y - row_h + 2.5 * mm, cell)
            x += col_w[i]
        y -= row_h
    # Borders
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.4)
    c.rect(MARGIN, y, sum(col_w), row_h * 4, stroke=1, fill=0)
    return y - 2 * mm


def draw_signature_blocks(c, y):
    """2 blocs signature côte-à-côte avec CACHET officiel pré-imprimé au milieu"""
    # 2 colonnes + 1 colonne centrale pour le cachet (taille compacte pour tenir en 1 page)
    cachet_w = 38 * mm
    gap = 3 * mm
    box_w = (PAGE_W - 2 * MARGIN - cachet_w - 2 * gap) / 2
    box_h = 38 * mm
    cachet_path = "/app/frontend/public/marketing/cachet_metrotaxi_LOGO_CENTRE.png"

    # --- BLOC GAUCHE : Métro-Taxi ---
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.4)
    c.rect(MARGIN, y - box_h, box_w, box_h, stroke=1, fill=0)
    c.setFillColor(YELLOW)
    c.rect(MARGIN, y - 5.5 * mm, box_w, 5.5 * mm, stroke=0, fill=1)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(MARGIN + 2 * mm, y - 4 * mm, "POUR MÉTRO-TAXI")
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN + 2 * mm, y - 9.5 * mm, "Nom : Judée SOULEYMANE")
    c.drawString(MARGIN + 2 * mm, y - 13 * mm, "Fonction : Fondateur")
    c.drawString(MARGIN + 2 * mm, y - 16.5 * mm, "Date : ___ / ___ / 2026")
    c.drawString(MARGIN + 2 * mm, y - 20 * mm, "Signature :")

    # --- CACHET CENTRAL OFFICIEL ---
    cachet_x = MARGIN + box_w + gap
    cachet_y = y - box_h + (box_h - cachet_w) / 2
    try:
        c.drawImage(
            cachet_path,
            cachet_x, cachet_y,
            width=cachet_w, height=cachet_w,
            preserveAspectRatio=True, mask='auto'
        )
    except Exception:
        pass
    c.setFillColor(GRAY)
    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(cachet_x + cachet_w / 2, y - box_h + 0.5 * mm, "CACHET OFFICIEL")

    # --- BLOC DROITE : Partenaire ---
    pright_x = cachet_x + cachet_w + gap
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.4)
    c.rect(pright_x, y - box_h, box_w, box_h, stroke=1, fill=0)
    c.setFillColor(YELLOW)
    c.rect(pright_x, y - 5.5 * mm, box_w, 5.5 * mm, stroke=0, fill=1)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 8.5)
    c.drawString(pright_x + 2 * mm, y - 4 * mm, "POUR LE PARTENAIRE")
    c.setFont("Helvetica", 7.5)
    c.drawString(pright_x + 2 * mm, y - 9.5 * mm, "Commerce : __________________________")
    c.drawString(pright_x + 2 * mm, y - 13 * mm, "Gérant(e) : __________________________")
    c.drawString(pright_x + 2 * mm, y - 16.5 * mm, "Date : ___ / ___ / 2026")
    c.drawString(pright_x + 2 * mm, y - 20 * mm, "Signature + cachet :")

    return y - box_h - 2 * mm


def generate():
    c = canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("Contrat de Partenariat Métro-Taxi — Point Inscription Officiel")
    c.setAuthor("Métro-Taxi")

    draw_header(c)
    y = PAGE_H - 58 * mm

    # Title
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(PAGE_W / 2, y, "CONTRAT DE PARTENARIAT")
    y -= 6 * mm
    c.setFont("Helvetica", 11)
    c.setFillColor(BLUE)
    c.drawCentredString(PAGE_W / 2, y, '« POINT INSCRIPTION OFFICIEL MÉTRO-TAXI »')
    y -= 8 * mm

    # Parties
    y = draw_section_title(c, y, "ENTRE LES SOUSSIGNÉS")
    y = draw_body(
        c, y,
        "D'une part, MÉTRO-TAXI, marque exploitée par Judée SOULEYMANE, "
        "ayant son siège à Saint-Denis (93), représentée par Judée SOULEYMANE en qualité de Fondateur, ci-après dénommée \"MÉTRO-TAXI\",",
    )
    y -= 2 * mm
    y = draw_body(c, y, "ET", bold=True)
    y -= 1 * mm
    y = draw_body(
        c, y,
        "D'autre part, le commerce ____________________________________, "
        "situé à _____________________________________________, "
        "représenté par M./Mme ___________________________ en qualité de gérant(e), ci-après dénommé \"LE PARTENAIRE\".",
    )
    y -= 3 * mm

    # Article 1 — Objet
    y = draw_section_title(c, y, "ARTICLE 1 — OBJET DU CONTRAT")
    y = draw_body(
        c, y,
        "Le PARTENAIRE s'engage à assister les clients souhaitant s'abonner à la plateforme Métro-Taxi "
        "en mettant à disposition son matériel informatique (ordinateur, tablette, smartphone) "
        "et en accompagnant l'utilisateur dans la procédure d'inscription en ligne sur metro-taxi.com.",
    )
    y -= 3 * mm

    # Article 2 — Rémunération
    y = draw_section_title(c, y, "ARTICLE 2 — RÉMUNÉRATION")
    y = draw_body(
        c, y,
        "Pour chaque inscription validée (compte créé + abonnement payé), MÉTRO-TAXI versera au "
        "PARTENAIRE une commission de 15% (quinze pour cent) du montant TTC de chaque abonnement payé "
        "(initial ou renouvellement) selon la grille suivante :",
    )
    y -= 2 * mm
    y = draw_rem_table(c, y)
    y = draw_body(
        c, y,
        "• Versement : HEBDOMADAIRE (chaque lundi par virement SEPA ou espèces selon préférence).",
        font_size=9,
    )
    y = draw_body(
        c, y,
        "• La commission s'applique à CHAQUE paiement d'abonnement effectif via le code PARTENAIRE (initial + renouvellements manuels ou automatiques) tant que le client reste actif.",
        font_size=9,
    )
    y -= 3 * mm

    # Article 3 — Contreparties
    # Article 3 — Contreparties (compact bullets)
    y = draw_section_title(c, y, "ARTICLE 3 — CONTREPARTIES OFFERTES PAR MÉTRO-TAXI")
    y = draw_bullet(c, y, "Affiche \"Point Inscription Officiel\" (A3 — 25×50 cm) à apposer en vitrine.")
    y = draw_bullet(c, y, "Flyers Métro-Taxi (50 exemplaires par mois minimum).")
    y = draw_bullet(c, y, "Logo et nom du PARTENAIRE sur supports publicitaires Métro-Taxi.")
    y = draw_bullet(c, y, "Code partenaire unique pour traçabilité : PARTENAIRE-______ (4 lettres).")
    y -= 1 * mm

    # Article 4 — Suivi
    y = draw_section_title(c, y, "ARTICLE 4 — SUIVI ET TRAÇABILITÉ DES INSCRIPTIONS")
    y = draw_body(
        c, y,
        "Chaque inscription assistée par le PARTENAIRE est tracée via le code unique attribué, saisi lors de l'inscription en ligne. "
        "Un récapitulatif est fourni au PARTENAIRE avec le virement hebdomadaire des commissions.",
    )
    y -= 1 * mm

    # Article 5 — Durée
    y = draw_section_title(c, y, "ARTICLE 5 — DURÉE & RÉSILIATION")
    y = draw_body(
        c, y,
        "Contrat conclu pour 12 mois renouvelable par tacite reconduction. Préavis de résiliation : 30 jours par lettre recommandée ou email. "
        "Résiliation immédiate en cas de non-respect des obligations.",
    )
    y -= 1 * mm

    # Article 6 — Confidentialité
    y = draw_section_title(c, y, "ARTICLE 6 — CONFIDENTIALITÉ & DONNÉES")
    y = draw_body(
        c, y,
        "Le PARTENAIRE s'engage à protéger les données personnelles des utilisateurs assistés (RGPD). "
        "Aucune donnée d'inscription ne peut être conservée, partagée ou utilisée à d'autres fins.",
    )
    y -= 2 * mm

    # Lieu signature
    y = draw_body(
        c, y,
        "Fait à Saint-Denis, le ___ / ___ / 2026, en deux exemplaires originaux, dont un pour chaque partie.",
        bold=True, font_size=9.5,
    )
    y -= 2 * mm

    # FORCE position des blocs signature au-dessus du footer
    # Footer commence à 15mm. Avec box_h=38mm + caption 2mm, min y = 60mm depuis le bas
    min_sig_y = 60 * mm
    if y < min_sig_y:
        y = min_sig_y
    # Signature blocks
    y = draw_signature_blocks(c, y)

    draw_footer(c, 1)
    c.showPage()
    c.save()
    print(f"✅ Contrat PDF: {OUT}")


if __name__ == "__main__":
    generate()
