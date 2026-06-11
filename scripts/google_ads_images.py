"""
Génère 2 images Google Ads à partir du fond Stade de France :
- Paysage 1200×628 px (landscape)
- Carrée  1200×1200 px (square)
"""
from pathlib import Path
import qrcode
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

BG = Path("/app/frontend/public/marketing/flyer_v3_1_raw_background.png")
OUTPUT_DIR = Path("/app/frontend/public/marketing")

YELLOW = (255, 214, 10)
BLUE = (10, 132, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def F(s, b=False):
    p = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if b else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    return ImageFont.truetype(p, s)


def outline(d, xy, text, font, fill, oc=BLACK, w=3):
    x, y = xy
    for dx in range(-w, w + 1):
        for dy in range(-w, w + 1):
            if dx or dy:
                d.text((x + dx, y + dy), text, font=font, fill=oc)
    d.text((x, y), text, font=font, fill=fill)


def centered(d, text, y, font, fill, cw, ol=True):
    bb = d.textbbox((0, 0), text, font=font)
    x = (cw - (bb[2] - bb[0])) // 2
    if ol:
        outline(d, (x, y), text, font, fill)
    else:
        d.text((x, y), text, font=font, fill=fill)


def make_landscape():
    """1200×628 — Format Google Ads paysage."""
    W, H = 1200, 628
    bg = Image.open(BG).convert("RGB")
    # Crop center to 16:9 ratio approx
    bw, bh = bg.size
    target_ratio = W / H
    src_ratio = bw / bh
    if src_ratio > target_ratio:
        new_w = int(bh * target_ratio)
        x0 = (bw - new_w) // 2
        bg = bg.crop((x0, 0, x0 + new_w, bh))
    else:
        new_h = int(bw / target_ratio)
        y0 = (bh - new_h) // 2
        bg = bg.crop((0, y0, bw, y0 + new_h))
    bg = bg.resize((W, H), Image.LANCZOS)
    bg = ImageEnhance.Brightness(bg).enhance(0.78)

    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(180):
        od.line([(0, H - 1 - i), (W, H - 1 - i)], fill=(0, 0, 0, int(225 * (1 - i / 180))))
    # Left side dark overlay (text zone)
    for x in range(640):
        a = int(180 * (1 - x / 640))
        od.line([(x, 0), (x, H)], fill=(0, 0, 0, a))
    bg = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(bg)

    # Texte gauche
    outline(d, (40, 35), "MÉTRO-TAXI", F(60, True), YELLOW)
    outline(d, (40, 110), "Saint-Denis & Île-de-France", F(28), WHITE)
    outline(d, (40, 170), "🎁 1ère course OFFERTE", F(38, True), YELLOW)
    outline(d, (40, 220), "(jusqu'à 10 km)", F(24), WHITE)

    # Bandeau date
    band = Image.new("RGBA", (W, 70), (255, 214, 10, 240))
    bg.paste(band, (0, 320), band)
    centered(d, "SAMEDI 13 JUIN 2026 — LANCEMENT", 335, F(38, True), BLACK, W, ol=False)

    # Abonnement
    outline(d, (40, 430), "ABONNEMENTS dès 6,99€", F(36, True), YELLOW)
    outline(d, (40, 480), "24h : 6,99€  •  7 jours : 19,99€  •  30 jours : 53,99€", F(22, True), WHITE)
    outline(d, (40, 545), "📱 metro-taxi.com — inscris-toi en 2 min", F(26, True), WHITE)

    out = OUTPUT_DIR / "google_ads_paysage_1200x628.png"
    bg.save(out, "PNG", optimize=True, quality=95)
    print(f"✅ Paysage: {out}")
    return out


def make_square():
    """1200×1200 — Format Google Ads carré."""
    S = 1200
    bg = Image.open(BG).convert("RGB")
    bw, bh = bg.size
    side = min(bw, bh)
    x0 = (bw - side) // 2
    y0 = (bh - side) // 2
    bg = bg.crop((x0, y0, x0 + side, y0 + side))
    bg = bg.resize((S, S), Image.LANCZOS)
    bg = ImageEnhance.Brightness(bg).enhance(0.75)

    ov = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    for i in range(280):
        od.line([(0, i), (S, i)], fill=(0, 0, 0, int(235 * (1 - i / 280))))
    for i in range(380):
        od.line([(0, S - 1 - i), (S, S - 1 - i)], fill=(0, 0, 0, int(240 * (1 - i / 380))))
    bg = Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(bg)

    centered(d, "MÉTRO-TAXI", 40, F(76, True), YELLOW, S)
    centered(d, "Saint-Denis & Île-de-France", 130, F(32), WHITE, S)

    # Bandeau date
    band = Image.new("RGBA", (S, 100), (255, 214, 10, 245))
    bg.paste(band, (0, 250), band)
    centered(d, "SAMEDI 13 JUIN 2026", 270, F(60, True), BLACK, S, ol=False)

    # Offre
    centered(d, "🎁  1ÈRE COURSE OFFERTE", 410, F(42, True), YELLOW, S)
    centered(d, "(jusqu'à 10 km — 30 premiers abonnés)", 470, F(26), WHITE, S)

    # Abonnements
    centered(d, "ABONNEMENTS DÈS 6,99€", 580, F(40, True), YELLOW, S)

    # 3 cartes prix
    plans = [("24H", "6,99€"), ("7 JOURS", "19,99€"), ("30 JOURS", "53,99€")]
    cw_, ch_, gap = 320, 200, 30
    total_w = cw_ * 3 + gap * 2
    sx = (S - total_w) // 2
    cy = 660
    for i, (lbl, prix) in enumerate(plans):
        cx = sx + i * (cw_ + gap)
        card = Image.new("RGBA", (cw_, ch_), (255, 214, 10, 245))
        bg.paste(card, (cx, cy), card)
        # Label
        bb = d.textbbox((0, 0), lbl, font=F(32, True))
        d.text((cx + (cw_ - (bb[2] - bb[0])) // 2, cy + 20), lbl, font=F(32, True), fill=BLACK)
        # Prix
        bb = d.textbbox((0, 0), prix, font=F(64, True))
        d.text((cx + (cw_ - (bb[2] - bb[0])) // 2, cy + 80), prix, font=F(64, True), fill=BLACK)

    centered(d, "📱 metro-taxi.com — inscris-toi en 2 min", S - 90, F(30, True), WHITE, S)

    out = OUTPUT_DIR / "google_ads_carre_1200x1200.png"
    bg.save(out, "PNG", optimize=True, quality=95)
    print(f"✅ Carré: {out}")
    return out


if __name__ == "__main__":
    make_landscape()
    make_square()
    print("\nURLs:")
    print("Paysage: https://metro-taxi-demo.preview.emergentagent.com/marketing/google_ads_paysage_1200x628.png")
    print("Carré: https://metro-taxi-demo.preview.emergentagent.com/marketing/google_ads_carre_1200x1200.png")
