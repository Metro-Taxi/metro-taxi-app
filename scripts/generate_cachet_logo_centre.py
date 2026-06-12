"""
Nouveau cachet rond avec LOGO OFFICIEL au centre.
- Logo Métro-Taxi au centre (image circulaire)
- Texte en arc autour : nom + adresse + tél + site web
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUTPUT = Path("/app/frontend/public/marketing")
LOGO = Path("/app/frontend/public/icons/metro-taxi-logo.png")

YELLOW = (255, 214, 10)
BLUE = (10, 132, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def F(s, b=False):
    p = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if b else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    return ImageFont.truetype(p, s)


def circular_text(d, img, text, radius, center, font, fill, start_angle=180, end_angle=0):
    """Dessine du texte le long d'un arc de cercle."""
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
        rot = -(start_angle + i * angle_per_char) - 90
        # Inverser si arc du bas (texte à l'envers sinon)
        if 0 < (start_angle + i * angle_per_char) % 360 < 180:
            rot += 180
        tmp = Image.new("RGBA", (font.size * 2, font.size * 2), (0, 0, 0, 0))
        td = ImageDraw.Draw(tmp)
        bb = td.textbbox((0, 0), ch, font=font)
        cw, chh = bb[2] - bb[0], bb[3] - bb[1]
        td.text(((tmp.width - cw) / 2, (tmp.height - chh) / 2 - 2), ch, font=font, fill=fill)
        rotated = tmp.rotate(rot, resample=Image.BICUBIC, expand=False)
        img.paste(rotated, (int(x - tmp.width / 2), int(y - tmp.height / 2)), rotated)


def cachet_logo_centre():
    size = 1400
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2

    # Cercle extérieur noir épais
    d.ellipse([25, 25, size - 25, size - 25], outline=BLACK, width=16)
    # Cercle intermédiaire fin
    d.ellipse([100, 100, size - 100, size - 100], outline=BLACK, width=3)

    # === LOGO AU CENTRE ===
    try:
        logo = Image.open(LOGO).convert("RGBA")
        logo_size = 580
        # Resize en gardant ratio
        logo.thumbnail((logo_size, logo_size), Image.LANCZOS)
        # Centrer sur le cachet
        lx = cx - logo.width // 2
        ly = cy - logo.height // 2
        img.paste(logo, (lx, ly), logo)
    except Exception as e:
        print(f"Logo error: {e}")

    # === Texte arc supérieur : MÉTRO-TAXI ===
    circular_text(d, img, "★  ★  MÉTRO-TAXI  ★  ★",
                  radius=size // 2 - 70, center=(cx, cy),
                  font=F(72, True), fill=BLACK,
                  start_angle=205, end_angle=335)

    # === Texte arc inférieur : metro-taxi.com · Tél 06 05 78 64 25 ===
    circular_text(d, img, "metro-taxi.com  ·  Tél : 06 05 78 64 25",
                  radius=size // 2 - 70, center=(cx, cy),
                  font=F(48, True), fill=BLACK,
                  start_angle=155, end_angle=25)

    # 2 petites étoiles latérales (à 0° et 180°)
    d.text((100, cy), "★", font=F(60, True), fill=BLACK, anchor="lm")
    d.text((size - 100, cy), "★", font=F(60, True), fill=BLACK, anchor="rm")

    out = OUTPUT / "cachet_metrotaxi_LOGO_CENTRE.png"
    img.save(out, "PNG", optimize=True)
    print(f"✅ {out}")
    return out


if __name__ == "__main__":
    cachet_logo_centre()
    print("URL: https://metro-taxi-demo.preview.emergentagent.com/marketing/cachet_metrotaxi_LOGO_CENTRE.png")
