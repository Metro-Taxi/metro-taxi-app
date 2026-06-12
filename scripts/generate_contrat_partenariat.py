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
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 31 * mm, "WhatsApp : 06 68 55 00 19")
    c.drawRightString(PAGE_W - MARGIN, PAGE_H - 36 * mm, "Siège : Saint-Denis (93)")

    # Ligne jaune sous header
    c.setFillColor(YELLOW)
    c.rect(0, PAGE_H - 52 * mm, PAGE_W, 2 * mm, stroke=0, fill=1)


def draw_footer(c, page_num=1):
    y = 15 * mm
    c.setFillColor(YELLOW)
    c.rect(0, y, PAGE_W, 1.5 * mm, stroke=0, fill=1)
    c.setFillColor(GRAY)
    c.setFont("Helvetica", 7.5)
    c.drawString(MARGIN, y - 5 * mm, "Métro-Taxi — Saint-Denis (93) • SIRET en cours d'attribution • R.C.S. Bobigny")
    c.drawRightString(PAGE_W - MARGIN, y - 5 * mm, f"Page {page_num} / 1 — v2 du 12/06/2026")


def draw_section_title(c, y, text):
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 11.5)
    c.drawString(MARGIN, y, text)
    # underline jaune
    c.setFillColor(YELLOW)
    c.rect(MARGIN, y - 1.5 * mm, len(text) * 2.4, 0.8 * mm, stroke=0, fill=1)
    return y - 6 * mm


def draw_body(c, y, text, font_size=9.5, max_width=PAGE_W - 2 * MARGIN, bold=False, color=DARK):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", font_size)
    # Manual wrap
    words = text.split()
    line = ""
    line_h = font_size * 1.35
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


def draw_bullet(c, y, text, font_size=9.5):
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
    return y - 3 * mm


def draw_signature_blocks(c, y):
    """2 blocs signature côte-à-côte"""
    box_w = (PAGE_W - 2 * MARGIN - 8 * mm) / 2
    box_h = 38 * mm
    # Métro-Taxi
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.4)
    c.rect(MARGIN, y - box_h, box_w, box_h, stroke=1, fill=0)
    c.setFillColor(YELLOW)
    c.rect(MARGIN, y - 7 * mm, box_w, 7 * mm, stroke=0, fill=1)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN + 2.5 * mm, y - 5 * mm, "POUR MÉTRO-TAXI")
    c.setFont("Helvetica", 8.5)
    c.drawString(MARGIN + 2.5 * mm, y - 12 * mm, "Nom : Judée SOULEYMANE")
    c.drawString(MARGIN + 2.5 * mm, y - 17 * mm, "Fonction : Fondateur")
    c.drawString(MARGIN + 2.5 * mm, y - 22 * mm, "Date : ___ / ___ / 2026")
    c.drawString(MARGIN + 2.5 * mm, y - 27 * mm, "Signature + cachet :")

    # Partenaire
    c.rect(MARGIN + box_w + 8 * mm, y - box_h, box_w, box_h, stroke=1, fill=0)
    c.setFillColor(YELLOW)
    c.rect(MARGIN + box_w + 8 * mm, y - 7 * mm, box_w, 7 * mm, stroke=0, fill=1)
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN + box_w + 10.5 * mm, y - 5 * mm, "POUR LE PARTENAIRE")
    c.setFont("Helvetica", 8.5)
    c.drawString(MARGIN + box_w + 10.5 * mm, y - 12 * mm, "Nom commerce : ________________________")
    c.drawString(MARGIN + box_w + 10.5 * mm, y - 17 * mm, "Nom / Prénom gérant : __________________")
    c.drawString(MARGIN + box_w + 10.5 * mm, y - 22 * mm, "Date : ___ / ___ / 2026")
    c.drawString(MARGIN + box_w + 10.5 * mm, y - 27 * mm, "Signature + cachet :")

    return y - box_h - 3 * mm


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
        "PARTENAIRE une commission de 15% (quinze pour cent) du montant TTC du premier abonnement souscrit "
        "selon la grille suivante :",
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
        "• Bonus volume : +50 € si plus de 25 inscriptions validées au cours d'un mois calendaire.",
        font_size=9,
    )
    y = draw_body(
        c, y,
        "• La commission s'applique uniquement au PREMIER abonnement souscrit. Les renouvellements automatiques sont exclus.",
        font_size=9,
    )
    y -= 3 * mm

    # Article 3 — Contreparties
    y = draw_section_title(c, y, "ARTICLE 3 — CONTREPARTIES OFFERTES PAR MÉTRO-TAXI")
    y = draw_body(c, y, "MÉTRO-TAXI s'engage à fournir au PARTENAIRE :")
    y = draw_bullet(c, y, "Une affiche \"Point Inscription Officiel Métro-Taxi\" (format A3 — 25×50 cm) à apposer en vitrine.")
    y = draw_bullet(c, y, "Des flyers Métro-Taxi (50 exemplaires par mois minimum).")
    y = draw_bullet(c, y, "L'affichage du logo et du nom du PARTENAIRE sur les supports publicitaires de Métro-Taxi (flyers V3 imprimés, publications Facebook/Instagram, site web).")
    y = draw_bullet(c, y, "Un code partenaire unique pour le suivi des inscriptions : PARTENAIRE-______ (4 lettres).")
    y -= 2 * mm

    # Article 4 — Suivi
    y = draw_section_title(c, y, "ARTICLE 4 — SUIVI ET TRAÇABILITÉ DES INSCRIPTIONS")
    y = draw_body(
        c, y,
        "Chaque inscription assistée par le PARTENAIRE est tracée via le code unique attribué, saisi par l'utilisateur "
        "lors de l'inscription en ligne. Un récapitulatif mensuel sera fourni au PARTENAIRE accompagné du virement de commissions.",
    )
    y -= 3 * mm

    # Article 5 — Durée
    y = draw_section_title(c, y, "ARTICLE 5 — DURÉE & RÉSILIATION")
    y = draw_body(
        c, y,
        "Le présent contrat est conclu pour une durée initiale de 12 mois à compter de sa signature, "
        "renouvelable par tacite reconduction. Chacune des parties peut y mettre fin moyennant un préavis "
        "de 30 jours par lettre recommandée avec accusé de réception ou message électronique. "
        "En cas de non-respect des obligations, la résiliation est immédiate.",
    )
    y -= 3 * mm

    # Article 6 — Confidentialité
    y = draw_section_title(c, y, "ARTICLE 6 — CONFIDENTIALITÉ & DONNÉES")
    y = draw_body(
        c, y,
        "Le PARTENAIRE s'engage à protéger les données personnelles des utilisateurs assistés (RGPD). "
        "Aucune donnée d'inscription ne peut être conservée, partagée ou utilisée à d'autres fins.",
    )
    y -= 4 * mm

    # Lieu signature
    y = draw_body(
        c, y,
        "Fait à Saint-Denis, le ___ / ___ / 2026, en deux exemplaires originaux, dont un pour chaque partie.",
        bold=True, font_size=10,
    )
    y -= 4 * mm

    # Signature blocks
    y = draw_signature_blocks(c, y)

    draw_footer(c, 1)
    c.showPage()
    c.save()
    print(f"✅ Contrat PDF: {OUT}")


if __name__ == "__main__":
    generate()
