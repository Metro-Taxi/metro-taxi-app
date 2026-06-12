"""
Génère 3 maquettes de cachet officiel Métro-Taxi pour commande VistaPrint.
Format : PNG haute résolution prêt à uploader sur vistaprint.fr
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT = Path("/app/frontend/public/marketing")

YELLOW = (255, 214, 10)
BLUE = (10, 132, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def F(s, b=False):
    p = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if b else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    return ImageFont.truetype(p, s)


def circular_text(d, text, radius, center, font, fill, start_angle=180, end_angle=0):
    """Dessine du texte le long d'un arc de cercle (de start à end, en degrés)."""
    cx, cy = center
    total_angle = end_angle - start_angle
    n = len(text)
    if n == 0:
        return
    angle_per_char = total_angle / max(n - 1, 1)
    for i, ch in enumerate(text):
        angle = math.radians(start_angle + i * angle_per_char)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        # rotation = angle de tangente + ajustement
        rot = -(start_angle + i * angle_per_char) - 90
        # Render char on temp image then paste rotated
        tmp = Image.new("RGBA", (font.size * 2, font.size * 2), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        bb = td.textbbox((0, 0), ch, font=font)
        cw, chh = bb[2] - bb[0], bb[3] - bb[1]
        td.text(((tmp.width - cw) / 2, (tmp.height - chh) / 2 - 2), ch, font=font, fill=fill)
        rotated = tmp.rotate(rot, resample=Image.BICUBIC, expand=False)
        d._image.paste(rotated, (int(x - tmp.width / 2), int(y - tmp.height / 2)), rotated)


# ============ CACHET #1 : CIRCULAIRE NOIR + JAUNE ============
def cachet_circulaire():
    size = 1200  # 40mm @ 762 DPI ~ haute qualité
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # Cercle extérieur noir épais
    d.ellipse([20, 20, size - 20, size - 20], outline=BLACK, width=14)
    # Cercle intérieur fin
    d.ellipse([90, 90, size - 90, size - 90], outline=BLACK, width=4)

    # Texte en haut (arc) : MÉTRO-TAXI
    circular_text(d, "★  MÉTRO-TAXI  ★", radius=size // 2 - 65, center=(cx, cy),
                  font=F(78, True), fill=BLACK, start_angle=200, end_angle=340)

    # Texte en bas (arc inversé) : SAINT-DENIS · ÎLE-DE-FRANCE
    # arc bottom from angle 30 to 150
    circular_text(d, "SAINT-DENIS  ·  ÎLE-DE-FRANCE", radius=size // 2 - 65, center=(cx, cy),
                  font=F(46, True), fill=BLACK, start_angle=160, end_angle=20)

    # Centre — symbole taxi (carré jaune avec damier noir au-dessus du texte)
    # Damier noir/blanc bandeau
    band_h = 40
    band_y = cy - 175
    bw = 50
    for i in range(8):
        color = BLACK if i % 2 == 0 else WHITE
        d.rectangle([cx - 4 * bw + i * bw, band_y, cx - 4 * bw + (i + 1) * bw, band_y + band_h],
                    fill=color, outline=BLACK)

    # Texte central : nom marque + slogan
    d.text((cx, cy - 90), "TAXI", font=F(110, True), fill=BLACK, anchor="mm")
    d.text((cx, cy + 20), "Covoiturage VTC", font=F(38), fill=BLACK, anchor="mm")
    d.text((cx, cy + 70), "Transbordement", font=F(38), fill=BLACK, anchor="mm")
    d.text((cx, cy + 120), "Intelligent", font=F(38), fill=BLACK, anchor="mm")

    # 3 étoiles
    d.text((cx - 200, cy + 180), "★", font=F(60, True), fill=BLACK, anchor="mm")
    d.text((cx, cy + 180), "★", font=F(60, True), fill=BLACK, anchor="mm")
    d.text((cx + 200, cy + 180), "★", font=F(60, True), fill=BLACK, anchor="mm")

    out = OUTPUT / "cachet_metrotaxi_circulaire_NOIR.png"
    img.save(out, "PNG", optimize=True)
    print(f"✅ {out}")
    return out


# ============ CACHET #2 : CIRCULAIRE JAUNE FOND ============
def cachet_circulaire_jaune():
    size = 1200
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # Disque jaune avec contour noir
    d.ellipse([20, 20, size - 20, size - 20], fill=YELLOW, outline=BLACK, width=12)
    d.ellipse([90, 90, size - 90, size - 90], outline=BLACK, width=3)

    circular_text(d, "★  MÉTRO-TAXI  ★", radius=size // 2 - 65, center=(cx, cy),
                  font=F(78, True), fill=BLACK, start_angle=200, end_angle=340)
    circular_text(d, "SAINT-DENIS  ·  ÎLE-DE-FRANCE", radius=size // 2 - 65, center=(cx, cy),
                  font=F(46, True), fill=BLACK, start_angle=160, end_angle=20)

    # Centre — damier
    band_h = 40
    band_y = cy - 175
    bw = 50
    for i in range(8):
        color = BLACK if i % 2 == 0 else WHITE
        d.rectangle([cx - 4 * bw + i * bw, band_y, cx - 4 * bw + (i + 1) * bw, band_y + band_h],
                    fill=color, outline=BLACK)

    d.text((cx, cy - 90), "TAXI", font=F(110, True), fill=BLACK, anchor="mm")
    d.text((cx, cy + 20), "Covoiturage VTC", font=F(38), fill=BLACK, anchor="mm")
    d.text((cx, cy + 70), "Transbordement", font=F(38), fill=BLACK, anchor="mm")
    d.text((cx, cy + 120), "Intelligent", font=F(38), fill=BLACK, anchor="mm")

    d.text((cx - 200, cy + 180), "★", font=F(60, True), fill=BLACK, anchor="mm")
    d.text((cx, cy + 180), "★", font=F(60, True), fill=BLACK, anchor="mm")
    d.text((cx + 200, cy + 180), "★", font=F(60, True), fill=BLACK, anchor="mm")

    out = OUTPUT / "cachet_metrotaxi_circulaire_JAUNE.png"
    img.save(out, "PNG", optimize=True)
    print(f"✅ {out}")
    return out


# ============ CACHET #3 : RECTANGULAIRE CLASSIQUE ============
def cachet_rectangulaire():
    """Format rectangulaire 38×14mm @ 762 DPI = 1141 × 421 px"""
    W, H = 1400, 500
    img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)

    # Cadre noir épais
    d.rectangle([10, 10, W - 10, H - 10], outline=BLACK, width=10)
    # Cadre intérieur fin
    d.rectangle([40, 40, W - 40, H - 40], outline=BLACK, width=2)

    # Damier au-dessus (rappel taxi)
    band_h = 32
    band_y = 70
    bw = 40
    for i in range((W - 200) // bw):
        color = BLACK if i % 2 == 0 else WHITE
        d.rectangle([100 + i * bw, band_y, 100 + (i + 1) * bw, band_y + band_h],
                    fill=color, outline=BLACK)

    # MÉTRO-TAXI (gros, centré)
    d.text((W // 2, 200), "MÉTRO-TAXI", font=F(140, True), fill=BLACK, anchor="mm")
    # Sous-ligne
    d.text((W // 2, 290), "Covoiturage VTC  ·  Transbordement Intelligent", font=F(46), fill=BLACK, anchor="mm")
    d.text((W // 2, 350), "SAINT-DENIS  ·  ÎLE-DE-FRANCE", font=F(48, True), fill=BLACK, anchor="mm")
    # Site web
    d.text((W // 2, 420), "metro-taxi.com  ·  Tél : 06 68 55 00 19", font=F(38), fill=BLACK, anchor="mm")

    out = OUTPUT / "cachet_metrotaxi_RECTANGULAIRE.png"
    img.save(out, "PNG", optimize=True)
    print(f"✅ {out}")
    return out


if __name__ == "__main__":
    cachet_circulaire()
    cachet_circulaire_jaune()
    cachet_rectangulaire()
    print("\nURLs:")
    print("Circulaire NOIR : https://metro-taxi-demo.preview.emergentagent.com/marketing/cachet_metrotaxi_circulaire_NOIR.png")
    print("Circulaire JAUNE: https://metro-taxi-demo.preview.emergentagent.com/marketing/cachet_metrotaxi_circulaire_JAUNE.png")
    print("Rectangulaire  : https://metro-taxi-demo.preview.emergentagent.com/marketing/cachet_metrotaxi_RECTANGULAIRE.png")
