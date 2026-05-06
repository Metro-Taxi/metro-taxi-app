"""
Flyer A5 RECTO/VERSO pour distribution terrain (CDG, gares, stations VTC)
Format : 148 × 210 mm @ 300 DPI = 1748 × 2480 px
Fond noir, logo officiel Métro-Taxi, chiffres clés, QR code metro-taxi.com/chauffeur
Sortie : PDF haute qualité prêt à imprimer
"""
import qrcode
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

OUTPUT_DIR = Path("/app/marketing_assets/flyers")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGO_PATH = "/app/frontend/public/icons/metro-taxi-logo.png"

# A5 @ 300 DPI
DPI = 300
WIDTH_MM = 148
HEIGHT_MM = 210
W = int(WIDTH_MM * DPI / 25.4)   # 1748 px
H = int(HEIGHT_MM * DPI / 25.4)  # 2480 px

# Couleurs Métro-Taxi
BLACK = (0, 0, 0)
YELLOW = (255, 213, 0)
WHITE = (255, 255, 255)
GREY = (160, 160, 160)


def get_font(size, bold=False):
    """Charge la police Liberation Sans (toujours dispo sur Linux)"""
    path = (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    )
    return ImageFont.truetype(path, size)


def draw_centered_text(draw, text, y, font, fill, w=W):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    x = (w - text_w) // 2
    draw.text((x, y), text, fill=fill, font=font)
    return bbox[3] - bbox[1]


def generate_qr_code(url: str, size: int = 600) -> Image.Image:
    """Génère un QR code blanc sur fond noir"""
    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High = robuste
        box_size=20,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="white", back_color="black").convert("RGB")
    img = img.resize((size, size), Image.LANCZOS)
    return img


def create_recto():
    """Recto - Accroche + Logo + QR code"""
    img = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)
    
    # === Bandeau jaune en haut ===
    BANDEAU_H = 100
    draw.rectangle([(0, 0), (W, BANDEAU_H)], fill=YELLOW)
    bandeau_font = get_font(48, bold=True)
    draw_centered_text(draw, "🚖 RECRUTEMENT CHAUFFEURS VTC", 25, bandeau_font, BLACK)
    
    # === Logo officiel ===
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo_w = 700
    logo_h = int(logo.height * logo_w / logo.width)
    logo = logo.resize((logo_w, logo_h), Image.LANCZOS)
    img.paste(logo, ((W - logo_w) // 2, BANDEAU_H + 80), logo)
    
    # === Slogan accrocheur ===
    y = BANDEAU_H + 80 + logo_h + 60
    
    title_font = get_font(82, bold=True)
    draw_centered_text(draw, "1,50€/km", y, title_font, YELLOW)
    y += 110
    
    sub_font = get_font(54, bold=True)
    draw_centered_text(draw, "GARANTI", y, sub_font, WHITE)
    y += 90
    
    # === Encadré chiffres clés ===
    box_y = y + 30
    box_h = 320
    box_margin = 100
    draw.rectangle(
        [(box_margin, box_y), (W - box_margin, box_y + box_h)],
        outline=YELLOW, width=4
    )
    
    bullet_font = get_font(38, bold=True)
    bullet_y = box_y + 30
    bullets = [
        "✓  0% de commission",
        "✓  Paiement le 10 de chaque mois",
        "✓  Aucun objectif imposé",
        "✓  100% libre, multi-plateformes",
    ]
    for bullet in bullets:
        draw.text((box_margin + 50, bullet_y), bullet, fill=WHITE, font=bullet_font)
        bullet_y += 70
    
    # === QR code en bas ===
    qr_size = 500
    qr_y = box_y + box_h + 120
    qr = generate_qr_code("https://metro-taxi.com/chauffeur", qr_size)
    img.paste(qr, ((W - qr_size) // 2, qr_y))
    
    # === URL sous le QR ===
    url_y = qr_y + qr_size + 30
    url_font = get_font(50, bold=True)
    draw_centered_text(draw, "metro-taxi.com/chauffeur", url_y, url_font, YELLOW)
    
    scan_font = get_font(34)
    draw_centered_text(draw, "📱 Scanne le QR code pour t'inscrire", url_y + 80, scan_font, WHITE)
    
    return img


def create_verso():
    """Verso - Détail rémunération + comparatif + zone légale"""
    img = Image.new("RGB", (W, H), BLACK)
    draw = ImageDraw.Draw(img)
    
    # === Titre ===
    y = 80
    title_font = get_font(72, bold=True)
    draw_centered_text(draw, "Combien tu peux gagner ?", y, title_font, YELLOW)
    y += 130
    
    # === Tableau revenus ===
    box_margin = 80
    sub_font = get_font(42, bold=True)
    line_font = get_font(38)
    line_bold = get_font(40, bold=True)
    
    # Encadré 1
    box1_y = y
    box1_h = 280
    draw.rectangle(
        [(box_margin, box1_y), (W - box_margin, box1_y + box1_h)],
        fill=(20, 20, 20), outline=YELLOW, width=3
    )
    draw.text((box_margin + 40, box1_y + 30), "Exemple 100 km/jour", fill=WHITE, font=sub_font)
    draw.text((box_margin + 40, box1_y + 110), "→ 150€ / jour", fill=YELLOW, font=line_bold)
    draw.text((box_margin + 40, box1_y + 180), "→ 3 300€ / mois (22j)", fill=YELLOW, font=line_bold)
    
    y = box1_y + box1_h + 50
    
    # Encadré 2
    box2_h = 280
    draw.rectangle(
        [(box_margin, y), (W - box_margin, y + box2_h)],
        fill=(20, 20, 20), outline=YELLOW, width=3
    )
    draw.text((box_margin + 40, y + 30), "Exemple 150 km/jour", fill=WHITE, font=sub_font)
    draw.text((box_margin + 40, y + 110), "→ 225€ / jour", fill=YELLOW, font=line_bold)
    draw.text((box_margin + 40, y + 180), "→ 4 950€ / mois (22j)", fill=YELLOW, font=line_bold)
    
    y += box2_h + 80
    
    # === Encadré "Pionniers" ===
    pio_h = 220
    draw.rectangle(
        [(box_margin, y), (W - box_margin, y + pio_h)],
        fill=YELLOW
    )
    pio_title = get_font(48, bold=True)
    pio_sub = get_font(34)
    draw_centered_text(draw, "🏆  AVANTAGE PIONNIER", y + 30, pio_title, BLACK)
    draw_centered_text(draw, "100 premiers chauffeurs partenaires", y + 100, pio_sub, BLACK)
    draw_centered_text(draw, "Inscription gratuite ✓", y + 150, pio_sub, BLACK)
    
    y += pio_h + 60
    
    # === Zone bas - mention légale + URL ===
    mini_font = get_font(26)
    draw_centered_text(
        draw,
        "Plateforme française de mise en relation",
        y, mini_font, GREY
    )
    y += 40
    draw_centered_text(
        draw,
        "Chauffeurs VTC indépendants - Cadre LOM 2019",
        y, mini_font, GREY
    )
    
    # URL en bas
    final_font = get_font(56, bold=True)
    draw_centered_text(draw, "metro-taxi.com", H - 130, final_font, YELLOW)
    
    flag_font = get_font(36)
    draw_centered_text(draw, "🇫🇷 Fier de bâtir en France", H - 70, flag_font, WHITE)
    
    return img


if __name__ == "__main__":
    print("🎨 Génération flyer A5 chauffeurs Métro-Taxi")
    print("=" * 60)
    
    print("📄 Recto en cours...")
    recto = create_recto()
    recto_path = OUTPUT_DIR / "flyer_chauffeur_RECTO.png"
    recto.save(recto_path, dpi=(DPI, DPI), quality=95)
    print(f"  ✅ {recto_path}")
    
    print("📄 Verso en cours...")
    verso = create_verso()
    verso_path = OUTPUT_DIR / "flyer_chauffeur_VERSO.png"
    verso.save(verso_path, dpi=(DPI, DPI), quality=95)
    print(f"  ✅ {verso_path}")
    
    # PDF combiné recto-verso
    pdf_path = OUTPUT_DIR / "flyer_chauffeur_A5.pdf"
    recto.save(pdf_path, "PDF", resolution=DPI, save_all=True, append_images=[verso])
    print(f"  ✅ PDF combiné: {pdf_path}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Format final: A5 ({WIDTH_MM}×{HEIGHT_MM} mm) @ {DPI} DPI")
    print(f"📐 Dimensions pixels: {W}×{H}")
    print(f"🖨️  Prêt à imprimer chez Vistaprint, photocopieur, ou imprimante perso")
