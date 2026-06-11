"""
FLYER V3 USAGER MÉTRO-TAXI — Stade de France background + 3 passagers heureux
Date : 11/06/2026 — Pour lancement SAMEDI 13 JUIN 2026
Format A6 portrait (105×148 mm @ 300 DPI = 1240×1748 px)

Pipeline :
1. Génération de l'image de fond via Gemini Nano Banana (gemini-3.1-flash-image-preview)
2. Composition finale via PIL (textes, QR code, accents jaunes/bleus)
"""
import asyncio
import base64
import os
import sys
from pathlib import Path

import qrcode
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

load_dotenv("/app/backend/.env")

from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: E402

OUTPUT_DIR = Path("/app/frontend/public/marketing")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# A6 @ 300 DPI
DPI = 300
W = int(105 * DPI / 25.4)  # 1240 px
H = int(148 * DPI / 25.4)  # 1748 px

YELLOW = (255, 214, 10)   # #FFD60A
BLUE = (10, 132, 255)     # accent bleu Stade de France
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)


def get_font(size, bold=False):
    path = (
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    )
    return ImageFont.truetype(path, size)


async def generate_background():
    """Génère l'image de fond via Nano Banana."""
    prompt = (
        "Photorealistic marketing image for a ride-sharing app in France. "
        "Vibrant urban scene at golden hour. In the background, the iconic Stade de France stadium "
        "(elliptical white roof structure) is visible but slightly blurred and de-emphasized. "
        "In the foreground, three diverse smiling passengers (one African woman in her 30s, "
        "one Maghrebi man in his 40s, one Asian woman in her 20s) are comfortably seated inside "
        "a modern black taxi van, laughing together. The interior is bright, clean, with yellow "
        "accent lighting. The atmosphere is joyful, friendly, premium. "
        "Color palette: deep black background, bright golden yellow accents (#FFD60A), "
        "soft blue tones. Style: high-end automotive advertising photography, dramatic lighting, "
        "cinematic composition. Portrait orientation 9:16. No text overlay. No watermark."
    )
    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        raise RuntimeError("EMERGENT_LLM_KEY manquant dans backend/.env")

    chat = LlmChat(
        api_key=api_key,
        session_id="metro-taxi-flyer-v3-stade-france",
        system_message="You are an expert marketing visual designer.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(
        modalities=["image", "text"]
    )

    msg = UserMessage(text=prompt)
    text, images = await chat.send_message_multimodal_response(msg)
    print(f"Gemini response text: {text[:120] if text else '(none)'}")
    if not images:
        raise RuntimeError("Aucune image générée par Gemini")

    img_data = base64.b64decode(images[0]["data"])
    raw_path = OUTPUT_DIR / "flyer_v3_raw_background.png"
    raw_path.write_bytes(img_data)
    print(f"Image brute sauvegardée : {raw_path}")
    return raw_path


def generate_qr_code(url: str, size: int = 280) -> Image.Image:
    qr = qrcode.QRCode(
        version=4,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img.resize((size, size), Image.LANCZOS)


def draw_text_with_outline(draw, xy, text, font, fill, outline_color=BLACK, outline_w=3):
    x, y = xy
    for dx in range(-outline_w, outline_w + 1):
        for dy in range(-outline_w, outline_w + 1):
            if dx or dy:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=fill)


def draw_centered(draw, text, y, font, fill, outline=True):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (W - tw) // 2
    if outline:
        draw_text_with_outline(draw, (x, y), text, font, fill)
    else:
        draw.text((x, y), text, font=font, fill=fill)
    return bbox[3] - bbox[1]


def compose_flyer(bg_path: Path) -> Path:
    """Compose le flyer final (background Gemini + texte + QR)."""
    # Resize bg to fit A6 portrait
    bg = Image.open(bg_path).convert("RGB")
    bg = bg.resize((W, H), Image.LANCZOS)

    # Légère assombrissement pour lisibilité du texte
    enhancer = ImageEnhance.Brightness(bg)
    bg = enhancer.enhance(0.85)

    # Overlay sombre dégradé en haut et bas (pour lisibilité texte)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    # Top dark gradient (260px)
    for i in range(260):
        alpha = int(220 * (1 - i / 260))
        odraw.line([(0, i), (W, i)], fill=(0, 0, 0, alpha))
    # Bottom dark gradient (380px)
    for i in range(380):
        alpha = int(230 * (1 - i / 380))
        odraw.line([(0, H - 1 - i), (W, H - 1 - i)], fill=(0, 0, 0, alpha))
    bg = Image.alpha_composite(bg.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(bg)

    # ===== TOP : Logo / Brand =====
    f_brand = get_font(76, bold=True)
    f_tagline = get_font(28, bold=False)
    draw_centered(draw, "MÉTRO-TAXI", 50, f_brand, YELLOW)
    draw_centered(
        draw,
        "Covoiturage VTC avec transbordement intelligent",
        140,
        f_tagline,
        WHITE,
        outline=True,
    )
    draw_centered(draw, "TOUTE L'ÎLE-DE-FRANCE", 180, f_tagline, BLUE)

    # ===== MIDDLE : main slogan (over the bright image) =====
    f_slogan_big = get_font(64, bold=True)
    f_slogan_med = get_font(48, bold=True)

    # Date band (yellow background strip)
    date_y = H - 720
    band = Image.new("RGBA", (W, 110), (255, 214, 10, 245))
    bg.paste(band, (0, date_y), band)
    draw_centered(draw, "SAMEDI 13 JUIN 2026", date_y + 25, f_slogan_big, BLACK, outline=False)

    # ===== BOTTOM HALF : key messages =====
    y = H - 560
    draw_centered(draw, "SAINT-DENIS PASSE EN", y, f_slogan_med, WHITE)
    draw_centered(draw, "MODE MÉTRO-TAXI 🚖", y + 60, f_slogan_med, YELLOW)

    # Offer block
    y2 = H - 380
    f_offer = get_font(46, bold=True)
    f_offer_sub = get_font(30, bold=False)
    draw_centered(draw, "🎁 1ÈRE COURSE OFFERTE", y2, f_offer, YELLOW)
    draw_centered(draw, "(jusqu'à 10 km)", y2 + 60, f_offer_sub, WHITE)
    draw_centered(draw, "Aux 30 premiers abonnés", y2 + 105, f_offer_sub, WHITE)

    # ===== FOOTER : QR + URL =====
    qr_url = "https://metro-taxi.com/inscription"
    qr = generate_qr_code(qr_url, size=260)
    # Yellow rounded frame
    frame = Image.new("RGB", (qr.width + 28, qr.height + 28), YELLOW)
    frame.paste(qr, (14, 14))
    bg.paste(frame, ((W - frame.width) // 2, H - 200))

    # URL text under QR
    f_url = get_font(22, bold=True)
    draw_centered(draw, "metro-taxi.com", H - 58, f_url, YELLOW)
    f_micro = get_font(18, bold=False)
    draw_centered(draw, "Scanne le QR — Inscris-toi en 2 minutes", H - 30, f_micro, WHITE)

    out_path = OUTPUT_DIR / "flyer_metrotaxi_V3_A6_STADE_DE_FRANCE.png"
    bg.save(out_path, "PNG", optimize=True, quality=95)
    print(f"Flyer composé : {out_path}")
    return out_path


async def main():
    print("🎨 Génération background via Nano Banana...")
    bg_path = await generate_background()
    print("🖼️  Composition du flyer final...")
    final = compose_flyer(bg_path)
    print(f"\n✅ TERMINÉ : {final}")
    print(f"URL publique : https://metro-taxi-demo.preview.emergentagent.com/marketing/{final.name}")


if __name__ == "__main__":
    asyncio.run(main())
