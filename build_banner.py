"""
Génération bâche 3x1m Métro-Taxi pour Vistaprint.
Format paysage panoramique : 3000 x 1000 mm @ 150 DPI (bâche grande dimension, 150 DPI suffit)
= 17716 x 5905 px

Le visuel doit être LISIBLE à 50 mètres de distance.
Règle d'or : Texte principal en MAJUSCULES, hauteur minimum 25% de la hauteur totale.
"""
import asyncio
import os
import base64
from PIL import Image, ImageDraw, ImageFont
import qrcode
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage

# ==== FORMAT BÂCHE 3x1m ====
# Vistaprint conseille 100-150 DPI pour les grands formats (économise RAM, suffisant à distance)
DPI = 150
MM_TO_PX = DPI / 25.4
# Bleed 5mm pour bâche (plus que pour flyer)
W_MM = 3000 + 10  # 3010 mm avec bleed
H_MM = 1000 + 10  # 1010 mm avec bleed
W_PX = round(W_MM * MM_TO_PX)
H_PX = round(H_MM * MM_TO_PX)

print(f"📐 Bâche : {W_MM}x{H_MM} mm @ {DPI} DPI = {W_PX}x{H_PX} px")

# Couleurs
YELLOW = (255, 214, 10)
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
RED_ACCENT = (220, 38, 38)

FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

OUTPUT_DIR = "/app/frontend/public/marketing"


async def generate_banner_bg():
    """Fond cinématique paysage pour la bâche."""
    prompt = """Cinematic ULTRA-WIDE panoramic photograph 3:1 aspect ratio, hyper-realistic, premium brand quality.

Scene: A wide cinematic view of Saint-Denis (Paris northern suburbs 93). On the RIGHT half of the image: the Basilique de Saint-Denis gothic cathedral with its iconic single tower, photographed at golden hour with warm orange and golden sunset light bathing the stone facade.

On the LEFT half: a modern yellow taxi sedan (glossy bright yellow, premium feel like a Mercedes commercial) driving toward the cathedral on a tree-lined boulevard at golden hour. Slight motion blur on wheels.

Center of the image: warm summer atmosphere, tree-lined boulevard, smooth asphalt, soft late afternoon light.

CRITICAL REQUIREMENTS:
- ABSOLUTELY NO TEXT anywhere in the image. NO words. NO letters. NO captions. NO signs with writing. NO graphics. NO watermarks. NO logos.
- NO buildings with visible writing in background.
- The LEFT 30% of the image should have relatively clean composition (sky + boulevard) to allow brand headline overlay.
- The CENTER 40% should have empty sky area for tagline overlay.
- Pure photorealistic outdoor scene only.

Style: Mercedes/BMW commercial quality. Cinematic ultra-wide panorama. Premium golden hour color grading: warm orange, golden yellow, soft browns, deep blue sky.

Aspect ratio: 3:1 ULTRA-WIDE PANORAMIC LANDSCAPE.
"""
    print("🎨 Étape 1/3 : Génération fond panoramique via Nano Banana...")
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id="banner-bg",
        system_message="You are a premium brand photographer creating cinematic ultra-wide panoramic visuals.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
    msg = UserMessage(text=prompt)
    text, images = await chat.send_message_multimodal_response(msg)

    if not images:
        raise Exception("Aucune image générée")

    img_bytes = base64.b64decode(images[0]["data"])
    raw_path = f"{OUTPUT_DIR}/banner_raw_bg.png"
    with open(raw_path, "wb") as f:
        f.write(img_bytes)
    print(f"   ✅ Fond brut : {raw_path}")
    return raw_path


def compose_banner(raw_bg_path: str) -> str:
    print("\n🖌️ Étape 2/3 : Composition bâche avec textes...")

    bg = Image.open(raw_bg_path).convert("RGB")
    # Cover crop pour ratio 3:1 paysage
    bg_ratio = bg.width / bg.height
    target_ratio = W_PX / H_PX
    if bg_ratio > target_ratio:
        new_h = bg.height
        new_w = int(new_h * target_ratio)
        x = (bg.width - new_w) // 2
        bg = bg.crop((x, 0, x + new_w, new_h))
    else:
        new_w = bg.width
        new_h = int(new_w / target_ratio)
        y = (bg.height - new_h) // 2
        bg = bg.crop((0, y, new_w, y + new_h))
    bg = bg.resize((W_PX, H_PX), Image.LANCZOS)

    # Overlay : assombrir GAUCHE (zone titre) + BAS (zone date/offre)
    overlay = Image.new("RGBA", (W_PX, H_PX), (0, 0, 0, 0))
    draw_o = ImageDraw.Draw(overlay)
    # Gradient gauche : du noir à 70% à transparent à 50% de la largeur
    for x in range(int(W_PX * 0.55)):
        alpha = max(0, int(180 * (1 - x / (W_PX * 0.55))))
        draw_o.rectangle([(x, 0), (x + 1, H_PX)], fill=(0, 0, 0, alpha))
    # Bandeau jaune en bas (bandeau d'urgence)
    band_h = int(H_PX * 0.22)
    draw_o.rectangle([(0, H_PX - band_h), (W_PX, H_PX)], fill=(255, 214, 10, 255))

    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, overlay).convert("RGB")
    draw = ImageDraw.Draw(bg)

    # ==== TITRE GAUCHE — MÉTRO-TAXI ====
    f_brand = ImageFont.truetype(FONT_BOLD, int(H_PX * 0.18))  # ~180px de haut
    text = "MÉTRO-TAXI"
    x = int(W_PX * 0.04)
    y = int(H_PX * 0.10)
    draw.text((x + 6, y + 6), text, font=f_brand, fill=(0, 0, 0, 220))
    draw.text((x, y), text, font=f_brand, fill=YELLOW)

    # Tagline sous le titre
    f_tag = ImageFont.truetype(FONT_BOLD, int(H_PX * 0.055))
    text = "Le VTC partagé intelligent"
    y += int(H_PX * 0.19)
    draw.text((x + 3, y + 3), text, font=f_tag, fill=(0, 0, 0, 200))
    draw.text((x, y), text, font=f_tag, fill=WHITE)

    # Saint-Denis 93
    f_loc = ImageFont.truetype(FONT_BOLD, int(H_PX * 0.06))
    text = "Saint-Denis  93"
    y += int(H_PX * 0.08)
    draw.text((x, y), text, font=f_loc, fill=YELLOW)

    # ==== BANDEAU JAUNE BAS — "LANCEMENT 13 JUIN 2026" + offre ====
    band_top = H_PX - int(H_PX * 0.22)
    band_center_y = band_top + int(H_PX * 0.22) // 2

    # Texte principal du bandeau
    f_band = ImageFont.truetype(FONT_BOLD, int(H_PX * 0.10))
    text = "LANCEMENT VENDREDI 13 JUIN 2026"
    bbox = draw.textbbox((0, 0), text, font=f_band)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    bx = (W_PX - tw) // 2
    by = band_center_y - th // 2 - int(H_PX * 0.025)
    draw.text((bx, by), text, font=f_band, fill=BLACK)

    # Sous-texte offre
    f_offre = ImageFont.truetype(FONT_BOLD, int(H_PX * 0.05))
    text = "1ère course OFFERTE aux 30 premiers abonnés  •  metro-taxi.com/saint-denis"
    bbox = draw.textbbox((0, 0), text, font=f_offre)
    tw = bbox[2] - bbox[0]
    bx = (W_PX - tw) // 2
    by += int(H_PX * 0.11)
    draw.text((bx, by), text, font=f_offre, fill=BLACK)

    # ==== QR Code en bas à droite (sur le bandeau jaune) ====
    qr = qrcode.QRCode(version=2, box_size=10, border=0)
    qr.add_data("https://metro-taxi.com/saint-denis")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="yellow").convert("RGB")
    qr_size = int(H_PX * 0.18)
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    qr_x = W_PX - qr_size - int(W_PX * 0.025)
    qr_y = band_top + (int(H_PX * 0.22) - qr_size) // 2
    bg.paste(qr_img, (qr_x, qr_y))

    out_path = f"{OUTPUT_DIR}/banner_metrotaxi_3x1m.png"
    bg.save(out_path, "PNG", dpi=(DPI, DPI), optimize=True)
    print(f"   ✅ Bâche sauvegardée : {out_path}")
    return out_path


def export_pdf(banner: str) -> str:
    print("\n📄 Étape 3/3 : Export PDF Vistaprint...")
    out_pdf = f"{OUTPUT_DIR}/banner_metrotaxi_3x1m_VISTAPRINT.pdf"
    img = Image.open(banner).convert("RGB")
    img.save(out_pdf, "PDF", resolution=DPI)
    print(f"   ✅ PDF : {out_pdf}")
    return out_pdf


async def main():
    raw = await generate_banner_bg()
    banner = compose_banner(raw)
    pdf = export_pdf(banner)
    print("\n" + "=" * 60)
    print("🎉 BÂCHE 3x1m GÉNÉRÉE")
    print("=" * 60)
    base = "https://metro-taxi-demo.preview.emergentagent.com/marketing"
    print(f"   • PNG : {base}/banner_metrotaxi_3x1m.png")
    print(f"   • PDF : {base}/banner_metrotaxi_3x1m_VISTAPRINT.pdf")


if __name__ == "__main__":
    asyncio.run(main())
