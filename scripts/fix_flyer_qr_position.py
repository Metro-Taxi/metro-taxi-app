"""
Fix V3.2 — Remonte le QR code et l'agrandit pour scan facile.
Réutilise le fond existant (pas de regénération Gemini).
"""
from pathlib import Path
import qrcode
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

OUTPUT_DIR = Path("/app/frontend/public/marketing")
BG = OUTPUT_DIR / "flyer_v3_1_raw_background.png"

DPI = 300
W = int(105 * DPI / 25.4)
H = int(148 * DPI / 25.4)
BW = int(25 * 200 / 2.54)
BH = int(50 * 200 / 2.54)

YELLOW = (255, 214, 10)
BLUE = (10, 132, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def F(s, b=False):
    p = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if b else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    return ImageFont.truetype(p, s)


def outline(draw, xy, text, font, fill, oc=BLACK, w=3):
    x, y = xy
    for dx in range(-w, w + 1):
        for dy in range(-w, w + 1):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=oc)
    draw.text((x, y), text, font=font, fill=fill)


def centered(draw, text, y, font, fill, cw, ol=True):
    bb = draw.textbbox((0, 0), text, font=font)
    x = (cw - (bb[2] - bb[0])) // 2
    if ol:
        outline(draw, (x, y), text, font, fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)


def qr(url, size):
    q = qrcode.QRCode(version=4, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    q.add_data(url)
    q.make(fit=True)
    return q.make_image(fill_color="black", back_color="white").convert("RGB").resize((size, size), Image.LANCZOS)


def compose_flyer_v3_2():
    bg = Image.open(BG).convert("RGB").resize((W, H), Image.LANCZOS)
    bg = ImageEnhance.Brightness(bg).enhance(0.78)

    # Overlay gradients (renforce le bas pour zone QR claire)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(280):
        od.line([(0, i), (W, i)], fill=(0, 0, 0, int(230 * (1 - i / 280))))
    for i in range(620):  # plus large pour zone QR
        od.line([(0, H - 1 - i), (W, H - 1 - i)], fill=(0, 0, 0, int(245 * (1 - i / 620))))
    bg = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(bg)

    # --- TOP ---
    centered(draw, "MÉTRO-TAXI", 40, F(78, True), YELLOW, W)
    centered(draw, "Covoiturage VTC • Transbordement Intelligent", 140, F(26), WHITE, W)
    centered(draw, "TOUTE L'ÎLE-DE-FRANCE", 175, F(28, True), BLUE, W)

    # --- SAINT-DENIS bloc (plus haut) ---
    y_sd = 240
    centered(draw, "SAINT-DENIS", y_sd, F(92, True), YELLOW, W)
    centered(draw, "passe en mode", y_sd + 100, F(34), WHITE, W)
    centered(draw, "MÉTRO-TAXI 🚖", y_sd + 150, F(62, True), YELLOW, W)

    # --- Date band (au milieu) ---
    date_y = 545
    band = Image.new("RGBA", (W, 110), (255, 214, 10, 250))
    bg.paste(band, (0, date_y), band)
    centered(draw, "SAMEDI 13 JUIN 2026", date_y + 28, F(60, True), BLACK, W, ol=False)

    # --- Offer (juste après le bandeau jaune) ---
    y_off = 700
    centered(draw, "🎁  1ÈRE COURSE OFFERTE", y_off, F(46, True), YELLOW, W)
    centered(draw, "jusqu'à 10 km — 30 premiers abonnés", y_off + 60, F(28), WHITE, W)

    # --- TARIFS ABONNEMENTS (3 plans) ---
    y_tar = y_off + 130
    centered(draw, "ABONNEMENTS À PARTIR DE 6,99€", y_tar, F(34, True), YELLOW, W)
    # 3 cards horizontales
    card_y = y_tar + 55
    card_w = 360
    card_h = 130
    gap = 25
    total_w = card_w * 3 + gap * 2
    start_x = (W - total_w) // 2
    plans = [
        ("24H",    "6,99€",  "5 courses"),
        ("1 SEM",  "19,99€", "15 courses"),
        ("1 MOIS", "53,99€", "Illimité"),
    ]
    for i, (lbl, prix, info) in enumerate(plans):
        cx = start_x + i * (card_w + gap)
        card = Image.new("RGBA", (card_w, card_h), (255, 214, 10, 245))
        bg.paste(card, (cx, card_y), card)
        centered(draw, lbl, card_y + 10, F(26, True), BLACK, W, ol=False)
        # Need draw price at card position
        bb = draw.textbbox((0, 0), prix, font=F(40, True))
        px = cx + (card_w - (bb[2] - bb[0])) // 2
        draw.text((px, card_y + 45), prix, font=F(40, True), fill=BLACK)
        bb2 = draw.textbbox((0, 0), info, font=F(20))
        px2 = cx + (card_w - (bb2[2] - bb2[0])) // 2
        draw.text((px2, card_y + 95), info, font=F(20), fill=BLACK)

    # --- QR XL et CENTRÉ DANS LE BAS (mais bien visible) ---
    qr_size = 420  # ⬆️ plus grand (était 270)
    qi = qr("https://metro-taxi.com/inscription", qr_size)
    fr = Image.new("RGB", (qi.width + 36, qi.height + 36), YELLOW)
    fr.paste(qi, (18, 18))
    qr_y = H - fr.height - 160  # ⬆️ remonté (160px du bas au lieu d'être collé)
    bg.paste(fr, ((W - fr.width) // 2, qr_y))

    # --- Footer URL ---
    centered(draw, "metro-taxi.com", H - 110, F(38, True), YELLOW, W)
    centered(draw, "Scanne POUR T'INSCRIRE ET T'ABONNER", H - 60, F(24, True), WHITE, W)

    out = OUTPUT_DIR / "flyer_metrotaxi_V3_2_A6_STADE_DE_FRANCE.png"
    bg.save(out, "PNG", optimize=True, quality=95)
    print(f"✅ Flyer V3.2: {out}")
    return out


def compose_banner_v2():
    bg = Image.open(BG).convert("RGB").resize((BW, BH), Image.LANCZOS)
    bg = ImageEnhance.Brightness(bg).enhance(0.72)

    ov = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(550):
        od.line([(0, i), (BW, i)], fill=(0, 0, 0, int(235 * (1 - i / 550))))
    for i in range(1500):  # gros gradient bas pour zone QR
        od.line([(0, BH - 1 - i), (BW, BH - 1 - i)], fill=(0, 0, 0, int(248 * (1 - i / 1500))))
    bg = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    draw = ImageDraw.Draw(bg)

    # --- TOP ---
    centered(draw, "MÉTRO-TAXI", 120, F(180, True), YELLOW, BW)
    centered(draw, "Covoiturage VTC • Transbordement Intelligent", 330, F(48), WHITE, BW)
    centered(draw, "TOUTE L'ÎLE-DE-FRANCE", 410, F(54, True), BLUE, BW)

    # --- SAINT-DENIS bloc ---
    y_sd = 620
    centered(draw, "SAINT-DENIS", y_sd, F(180, True), YELLOW, BW)
    centered(draw, "passe en mode", y_sd + 200, F(70), WHITE, BW)
    centered(draw, "MÉTRO-TAXI 🚖", y_sd + 290, F(130, True), YELLOW, BW)

    # --- DATE BAND ---
    yb = 1280
    band = Image.new("RGBA", (BW, 230), (255, 214, 10, 250))
    bg.paste(band, (0, yb), band)
    centered(draw, "SAMEDI 13 JUIN 2026", yb + 60, F(130, True), BLACK, BW, ol=False)

    # --- OFFER ---
    y_off = 1620
    centered(draw, "🎁  1ÈRE COURSE OFFERTE", y_off, F(92, True), YELLOW, BW)
    centered(draw, "jusqu'à 10 km — 30 premiers abonnés", y_off + 110, F(50), WHITE, BW)

    # --- TARIFS ABONNEMENTS (3 cards XL) ---
    y_tar = y_off + 200
    centered(draw, "ABONNEMENTS À PARTIR DE 6,99€", y_tar, F(70, True), YELLOW, BW)
    card_y = y_tar + 100
    card_w = 580
    card_h = 280
    gap = 40
    total_w = card_w * 3 + gap * 2
    start_x = (BW - total_w) // 2
    plans = [
        ("24H",    "6,99€",  "5 courses"),
        ("1 SEM",  "19,99€", "15 courses"),
        ("1 MOIS", "53,99€", "Illimité"),
    ]
    for i, (lbl, prix, info) in enumerate(plans):
        cx = start_x + i * (card_w + gap)
        card = Image.new("RGBA", (card_w, card_h), (255, 214, 10, 248))
        bg.paste(card, (cx, card_y), card)
        # Label haut
        bb = draw.textbbox((0, 0), lbl, font=F(54, True))
        draw.text((cx + (card_w - (bb[2]-bb[0]))//2, card_y + 20), lbl, font=F(54, True), fill=BLACK)
        # Prix gros
        bb = draw.textbbox((0, 0), prix, font=F(86, True))
        draw.text((cx + (card_w - (bb[2]-bb[0]))//2, card_y + 90), prix, font=F(86, True), fill=BLACK)
        # Info bas
        bb = draw.textbbox((0, 0), info, font=F(42))
        draw.text((cx + (card_w - (bb[2]-bb[0]))//2, card_y + 200), info, font=F(42), fill=BLACK)

    # --- POINT INSCRIPTION (sous les cards de tarifs) ---
    y_pi = card_y + card_h + 60
    centered(draw, "📍 POINT INSCRIPTION OFFICIEL", y_pi, F(70, True), BLUE, BW)
    centered(draw, "Demandez à l'intérieur — aide gratuite", y_pi + 90, F(52, True), WHITE, BW)

    # --- QR (taille ajustée pour rentrer + footer) ---
    qr_size = 700
    qi = qr("https://metro-taxi.com/inscription", qr_size)
    fr = Image.new("RGB", (qi.width + 50, qi.height + 50), YELLOW)
    fr.paste(qi, (25, 25))
    qr_y = y_pi + 220
    bg.paste(fr, ((BW - fr.width) // 2, qr_y))

    # --- Footer ---
    centered(draw, "metro-taxi.com", qr_y + fr.height + 40, F(80, True), YELLOW, BW)
    centered(draw, "📱 Scanne POUR T'INSCRIRE ET T'ABONNER", qr_y + fr.height + 130, F(50, True), WHITE, BW)

    out = OUTPUT_DIR / "banderole_metrotaxi_PORTE_25x50cm_v2.png"
    bg.save(out, "PNG", optimize=True, quality=95)
    print(f"✅ Banderole V2: {out}")
    return out


if __name__ == "__main__":
    f = compose_flyer_v3_2()
    b = compose_banner_v2()
    print(f"\nURLs:")
    print(f"Flyer: https://metro-taxi-demo.preview.emergentagent.com/marketing/{f.name}")
    print(f"Banderole: https://metro-taxi-demo.preview.emergentagent.com/marketing/{b.name}")
