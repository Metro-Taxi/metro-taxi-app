"""
Régénération du fond du flyer V3 — angle différent + nouveaux passagers
+ création d'une BANDEROLE VERTICALE 50 cm pour les portes de taxiphones
"""
import asyncio
import base64
import os
from pathlib import Path

import qrcode
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

load_dotenv("/app/backend/.env")
from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

OUTPUT_DIR = Path("/app/frontend/public/marketing")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# A6 @ 300 DPI
DPI = 300
W = int(105 * DPI / 25.4)  # 1240
H = int(148 * DPI / 25.4)  # 1748

# Banderole verticale : 25 cm large × 50 cm haut @ 200 DPI = 1968 × 3937 px
BW = int(25 * 200 / 2.54)   # ~1968
BH = int(50 * 200 / 2.54)   # ~3937

YELLOW = (255, 214, 10)
BLUE = (10, 132, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def get_font(size, bold=False):
    path = (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    )
    return ImageFont.truetype(path, size)


async def gen_image(prompt: str, session_id: str, out_name: str) -> Path:
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="You are an expert marketing visual designer.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(
        modalities=["image", "text"]
    )
    msg = UserMessage(text=prompt)
    _, images = await chat.send_message_multimodal_response(msg)
    if not images:
        raise RuntimeError(f"Aucune image générée pour {out_name}")
    out_path = OUTPUT_DIR / out_name
    out_path.write_bytes(base64.b64decode(images[0]["data"]))
    print(f"Image: {out_path}")
    return out_path


def draw_text_outline(draw, xy, text, font, fill, outline=BLACK, w=3):
    x, y = xy
    for dx in range(-w, w + 1):
        for dy in range(-w, w + 1):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


def draw_centered(draw, text, y, font, fill, canvas_w, outline=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (canvas_w - (bbox[2] - bbox[0])) // 2
    if outline:
        draw_text_outline(draw, (x, y), text, font, fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)


def qr(url: str, size: int = 280) -> Image.Image:
    q = qrcode.QRCode(version=4, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    q.add_data(url)
    q.make(fit=True)
    return q.make_image(fill_color="black", back_color="white").convert("RGB").resize((size, size), Image.LANCZOS)


def compose_flyer_v3_1(bg_path: Path) -> Path:
    """V3.1 — meilleure hiérarchie texte (SAINT-DENIS plus grand)."""
    bg = Image.open(bg_path).convert("RGB").resize((W, H), Image.LANCZOS)
    bg = ImageEnhance.Brightness(bg).enhance(0.82)

    # Overlay top/bottom gradient
    ovl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ovl)
    for i in range(260):
        od.line([(0, i), (W, i)], fill=(0, 0, 0, int(225 * (1 - i / 260))))
    for i in range(420):
        od.line([(0, H - 1 - i), (W, H - 1 - i)], fill=(0, 0, 0, int(235 * (1 - i / 420))))
    bg = Image.alpha_composite(bg.convert("RGBA"), ovl).convert("RGB")
    draw = ImageDraw.Draw(bg)

    # TOP — Branding
    draw_centered(draw, "MÉTRO-TAXI", 45, get_font(80, True), YELLOW, W)
    draw_centered(draw, "Covoiturage VTC • Transbordement Intelligent", 145, get_font(28), WHITE, W)
    draw_centered(draw, "TOUTE L'ÎLE-DE-FRANCE", 185, get_font(30, True), BLUE, W)

    # SAINT-DENIS — plus gros maintenant
    y_sd = H - 870
    draw_centered(draw, "SAINT-DENIS", y_sd, get_font(96, True), YELLOW, W)
    draw_centered(draw, "passe en mode", y_sd + 105, get_font(38), WHITE, W)
    draw_centered(draw, "MÉTRO-TAXI 🚖", y_sd + 155, get_font(64, True), YELLOW, W)

    # Date band (jaune plein)
    date_y = H - 600
    band = Image.new("RGBA", (W, 115), (255, 214, 10, 250))
    bg.paste(band, (0, date_y), band)
    draw_centered(draw, "SAMEDI 13 JUIN 2026", date_y + 30, get_font(64, True), BLACK, W, outline=False)

    # Offer
    y2 = H - 430
    draw_centered(draw, "🎁  1ÈRE COURSE OFFERTE", y2, get_font(48, True), YELLOW, W)
    draw_centered(draw, "(jusqu'à 10 km)", y2 + 65, get_font(32), WHITE, W)
    draw_centered(draw, "Aux 30 premiers abonnés", y2 + 110, get_font(32), WHITE, W)

    # QR
    qr_img = qr("https://metro-taxi.com/inscription", 270)
    frame = Image.new("RGB", (qr_img.width + 30, qr_img.height + 30), YELLOW)
    frame.paste(qr_img, (15, 15))
    bg.paste(frame, ((W - frame.width) // 2, H - 200))
    draw_centered(draw, "metro-taxi.com", H - 58, get_font(26, True), YELLOW, W)
    draw_centered(draw, "Scanne et inscris-toi en 2 minutes", H - 28, get_font(22), WHITE, W)

    out = OUTPUT_DIR / "flyer_metrotaxi_V3_1_A6_STADE_DE_FRANCE.png"
    bg.save(out, "PNG", optimize=True, quality=95)
    print(f"Flyer V3.1: {out}")
    return out


def compose_banner_50cm(bg_path: Path) -> Path:
    """Banderole verticale 25×50 cm pour porte de taxiphone."""
    bg = Image.open(bg_path).convert("RGB").resize((BW, BH), Image.LANCZOS)
    bg = ImageEnhance.Brightness(bg).enhance(0.78)

    # Overlay gradient top/bottom (plus marqué car format long)
    ovl = Image.new("RGBA", (BW, BH), (0, 0, 0, 0))
    od = ImageDraw.Draw(ovl)
    for i in range(500):
        od.line([(0, i), (BW, i)], fill=(0, 0, 0, int(230 * (1 - i / 500))))
    for i in range(900):
        od.line([(0, BH - 1 - i), (BW, BH - 1 - i)], fill=(0, 0, 0, int(240 * (1 - i / 900))))
    # Bande sombre centrale très légère
    for i in range(int(BH * 0.45), int(BH * 0.55)):
        od.line([(0, i), (BW, i)], fill=(0, 0, 0, 80))
    bg = Image.alpha_composite(bg.convert("RGBA"), ovl).convert("RGB")
    draw = ImageDraw.Draw(bg)

    # ===== TOP =====
    draw_centered(draw, "MÉTRO-TAXI", 130, get_font(180, True), YELLOW, BW)
    draw_centered(draw, "Covoiturage VTC • Transbordement Intelligent", 340, get_font(48), WHITE, BW)
    draw_centered(draw, "TOUTE L'ÎLE-DE-FRANCE", 410, get_font(54, True), BLUE, BW)

    # ===== MILIEU — Slogan =====
    y_mid = int(BH * 0.40)
    draw_centered(draw, "SAINT-DENIS", y_mid, get_font(190, True), YELLOW, BW)
    draw_centered(draw, "passe en mode", y_mid + 200, get_font(70), WHITE, BW)
    draw_centered(draw, "MÉTRO-TAXI 🚖", y_mid + 290, get_font(130, True), YELLOW, BW)

    # ===== DATE BAND =====
    y_band = int(BH * 0.62)
    band = Image.new("RGBA", (BW, 230), (255, 214, 10, 250))
    bg.paste(band, (0, y_band), band)
    draw_centered(draw, "SAMEDI 13 JUIN 2026", y_band + 60, get_font(130, True), BLACK, BW, outline=False)

    # ===== OFFER =====
    y_offer = int(BH * 0.74)
    draw_centered(draw, "🎁  1ÈRE COURSE OFFERTE", y_offer, get_font(94, True), YELLOW, BW)
    draw_centered(draw, "jusqu'à 10 km — 30 premiers abonnés", y_offer + 120, get_font(56), WHITE, BW)

    # ===== POINT INSCRIPTION =====
    y_point = int(BH * 0.83)
    draw_centered(draw, "📍 POINT INSCRIPTION OFFICIEL", y_point, get_font(70, True), BLUE, BW)
    draw_centered(draw, "Demandez à l'intérieur — aide gratuite", y_point + 90, get_font(52), WHITE, BW)

    # ===== BOTTOM QR =====
    qr_img = qr("https://metro-taxi.com/inscription", 600)
    frame = Image.new("RGB", (qr_img.width + 50, qr_img.height + 50), YELLOW)
    frame.paste(qr_img, (25, 25))
    bg.paste(frame, ((BW - frame.width) // 2, BH - 760))
    draw_centered(draw, "metro-taxi.com", BH - 110, get_font(80, True), YELLOW, BW)

    out = OUTPUT_DIR / "banderole_metrotaxi_PORTE_25x50cm.png"
    bg.save(out, "PNG", optimize=True, quality=95)
    print(f"Banderole 50cm: {out}")
    return out


async def main():
    # 1. Nouveau fond (autre angle Stade de France + autres passagers)
    new_prompt = (
        "Photorealistic marketing photo for a ride-sharing brand in Paris region. "
        "Wide cinematic shot. The iconic Stade de France stadium is visible from a different angle "
        "(low angle view, looking up at the white elliptical roof against a vibrant sunset sky). "
        "In the foreground, three different smiling passengers are seated inside a modern premium "
        "black minivan (one African man in his 30s in business casual, one young Moroccan woman in "
        "her 20s wearing colorful clothes, one elderly French man with white hair smiling warmly). "
        "They look happy and relaxed, talking together. Bright golden hour lighting through windows. "
        "The vehicle interior is luxurious with yellow ambient LED lighting. "
        "Color palette: deep blacks, vibrant yellow accents (#FFD60A), warm sunset blue/orange sky. "
        "Style: premium automotive advertising photography, dramatic depth of field, professional. "
        "Portrait orientation 9:16. No text overlay. No watermark. No AI artifacts."
    )
    new_bg = await gen_image(new_prompt, "metro-taxi-flyer-v3-1", "flyer_v3_1_raw_background.png")

    # 2. Compose le flyer V3.1
    flyer_v31 = compose_flyer_v3_1(new_bg)

    # 3. Compose la banderole 25×50 cm (utilise le NOUVEAU fond — image gaie)
    banner = compose_banner_50cm(new_bg)

    print("\n=== LIVRABLES ===")
    print(f"Flyer V3.1: https://metro-taxi-demo.preview.emergentagent.com/marketing/{flyer_v31.name}")
    print(f"Banderole 25×50cm: https://metro-taxi-demo.preview.emergentagent.com/marketing/{banner.name}")


if __name__ == "__main__":
    asyncio.run(main())
