"""
Génération Flyer A6 Métro-Taxi pour Vistaprint
- Format A6 avec bleed: 109 x 152 mm @ 300 DPI = 1287 x 1795 px
- Recto: fond cinématique via Gemini Nano Banana + textes overlay PIL
- Verso: design textuel PIL pur (fond noir + accents jaunes + QR code)
- Export: 2 PNG haute résolution + 1 PDF combiné prêt pour Vistaprint
"""
import asyncio
import os
import base64
from PIL import Image, ImageDraw, ImageFont
import qrcode
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage

# ==== CONSTANTES VISTAPRINT A6 ====
# A6 final = 105 x 148 mm | Bleed safety = +2mm chaque côté = 109 x 152 mm
# À 300 DPI : 1287 x 1795 pixels
DPI = 300
MM_TO_PX = DPI / 25.4
BLEED_MM = 2
A6_W_MM = 105 + 2 * BLEED_MM  # 109 mm
A6_H_MM = 148 + 2 * BLEED_MM  # 152 mm
W_PX = round(A6_W_MM * MM_TO_PX)
H_PX = round(A6_H_MM * MM_TO_PX)
SAFE_MARGIN_PX = round(5 * MM_TO_PX)  # 5mm safe area depuis les bords

print(f"📐 Format flyer : {A6_W_MM}x{A6_H_MM} mm @ {DPI} DPI = {W_PX}x{H_PX} px")

# ==== COULEURS BRAND ====
YELLOW = (255, 214, 10)       # FFD60A
YELLOW_DARK = (200, 165, 0)
BLACK = (10, 10, 10)
WHITE = (255, 255, 255)
GREY = (60, 60, 60)
RED_ACCENT = (220, 38, 38)    # Pour le compte à rebours

# ==== FONTS ====
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD_NARROW = "/usr/share/fonts/truetype/liberation/LiberationSansNarrow-Bold.ttf"

OUTPUT_DIR = "/app/frontend/public/marketing"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==================== ÉTAPE 1 : Fond cinématique RECTO via Nano Banana ====================
async def generate_recto_background():
    """Génère un visuel cinématique impactant pour le recto."""
    prompt = """Cinematic vertical photograph 9:16, ultra-high resolution, hyper-realistic, like a National Geographic cover or Mercedes commercial.

Scene: The Basilique de Saint-Denis cathedral (Paris northern suburbs 93) photographed from a low angle at sunset golden hour. The iconic single tower of the gothic cathedral dominates the composition, the warm sunset light bathes the stone facade in golden orange tones.

In the lower portion of the frame: a clean modern yellow taxi sedan (Renault Megane style, glossy bright yellow) parked or driving on the boulevard in front of the cathedral. The taxi reflects the warm sunset light.

Foreground: tree-lined boulevard, smooth asphalt, summer green leaves framing both sides.

CRITICAL REQUIREMENTS — READ CAREFULLY:
- The UPPER 35% of the image must be CLEAN SKY ONLY: warm sunset gradient from soft orange near horizon to deeper blue at top. NO clouds with strange shapes, NO architectural elements in the upper 35%.
- ABSOLUTELY NO TEXT anywhere in the image. NO words. NO letters. NO headlines. NO captions. NO watermarks. NO logos. NO brand names. NO signs with visible writing. The image must be 100% TEXT-FREE.
- NO writing on buildings, NO signs with letters, NO advertisements in the background.
- Pure photorealistic outdoor scene, no graphic design elements, no overlays.

Style: Premium brand photography, Mercedes/BMW commercial quality. Sharp focus on cathedral and taxi. Warm cinematic color grading: golden orange, soft brown, brilliant yellow.

Aspect ratio: 9:16 vertical portrait.
"""
    print("🎨 Étape 1/4 : Génération fond cinématique RECTO via Nano Banana...")
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id="flyer-recto-bg",
        system_message="You are a premium brand photographer specialized in cinematic urban mobility marketing visuals.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
    msg = UserMessage(text=prompt)
    text, images = await chat.send_message_multimodal_response(msg)

    if not images:
        raise Exception("Aucune image générée par Nano Banana")

    img_bytes = base64.b64decode(images[0]["data"])
    raw_path = f"{OUTPUT_DIR}/flyer_recto_raw.png"
    with open(raw_path, "wb") as f:
        f.write(img_bytes)
    print(f"   ✅ Fond brut sauvegardé : {raw_path}")
    return raw_path


# ==================== ÉTAPE 2 : Compose RECTO avec textes ====================
def compose_recto(raw_bg_path: str) -> str:
    print("\n🖌️ Étape 2/4 : Composition RECTO avec textes overlay...")

    # Charger et redimensionner le fond au format flyer
    bg = Image.open(raw_bg_path).convert("RGB")
    # Cover : conserve le ratio, crop si besoin pour remplir W_PX x H_PX
    bg_ratio = bg.width / bg.height
    target_ratio = W_PX / H_PX
    if bg_ratio > target_ratio:
        # bg trop large, on crop horizontalement
        new_h = bg.height
        new_w = int(new_h * target_ratio)
        x = (bg.width - new_w) // 2
        bg = bg.crop((x, 0, x + new_w, new_h))
    else:
        # bg trop haut, on crop verticalement
        new_w = bg.width
        new_h = int(new_w / target_ratio)
        y = (bg.height - new_h) // 2
        bg = bg.crop((0, y, new_w, y + new_h))
    bg = bg.resize((W_PX, H_PX), Image.LANCZOS)

    # Ajouter un dégradé sombre en haut + en bas pour lisibilité du texte
    overlay = Image.new("RGBA", (W_PX, H_PX), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    # Top gradient — RENFORCÉ pour couvrir tout texte parasite éventuel
    for y in range(int(H_PX * 0.40)):
        # Top 18% complètement noir (couvre tout texte parasite), puis fade
        if y < int(H_PX * 0.18):
            alpha = 255
        else:
            fade_zone = int(H_PX * 0.40) - int(H_PX * 0.18)
            progress = (y - int(H_PX * 0.18)) / fade_zone
            alpha = max(0, int(255 * (1 - progress)))
        draw_overlay.rectangle([(0, y), (W_PX, y + 1)], fill=(0, 0, 0, alpha))
    # Bottom gradient
    for y in range(int(H_PX * 0.5), H_PX):
        alpha = max(0, int(210 * ((y - H_PX * 0.5) / (H_PX * 0.5))))
        draw_overlay.rectangle([(0, y), (W_PX, y + 1)], fill=(0, 0, 0, alpha))

    bg = bg.convert("RGBA")
    bg = Image.alpha_composite(bg, overlay)
    img = bg.convert("RGB")
    draw = ImageDraw.Draw(img)

    # ==== TOP HEADLINE ====
    # "MÉTRO-TAXI" en gros
    f_brand = ImageFont.truetype(FONT_BOLD, 180)
    text = "MÉTRO-TAXI"
    bbox = draw.textbbox((0, 0), text, font=f_brand)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (W_PX - tw) // 2
    y = round(20 * MM_TO_PX)
    # Ombre
    draw.text((x + 4, y + 4), text, font=f_brand, fill=(0, 0, 0, 200))
    draw.text((x, y), text, font=f_brand, fill=YELLOW)

    # Tagline
    f_tag = ImageFont.truetype(FONT_REG, 50)
    tag = "Le VTC partagé intelligent"
    bbox = draw.textbbox((0, 0), tag, font=f_tag)
    tw = bbox[2] - bbox[0]
    x = (W_PX - tw) // 2
    draw.text((x, y + 200), tag, font=f_tag, fill=WHITE)

    # ==== BOTTOM BLOC SAINT-DENIS ====
    bottom_y = round(110 * MM_TO_PX)

    # Bandeau jaune
    band_h = round(45 * MM_TO_PX)
    band_top = H_PX - band_h - round(8 * MM_TO_PX)
    draw.rectangle([(0, band_top), (W_PX, band_top + band_h)], fill=YELLOW)

    # "SAINT-DENIS"
    f_city = ImageFont.truetype(FONT_BOLD, 145)
    text = "SAINT-DENIS"
    bbox = draw.textbbox((0, 0), text, font=f_city)
    tw = bbox[2] - bbox[0]
    x = (W_PX - tw) // 2
    draw.text((x, band_top + 30), text, font=f_city, fill=BLACK)

    # "Ouverture vendredi 13 juin 2026"
    f_date = ImageFont.truetype(FONT_BOLD, 60)
    text = "Ouverture vendredi 13 juin 2026"
    bbox = draw.textbbox((0, 0), text, font=f_date)
    tw = bbox[2] - bbox[0]
    x = (W_PX - tw) // 2
    draw.text((x, band_top + 220), text, font=f_date, fill=BLACK)

    # Badge "1ère course offerte" en pastille rouge
    badge_text = "1ère course OFFERTE aux 30 premiers abonnés"
    f_badge = ImageFont.truetype(FONT_BOLD, 42)
    bbox = draw.textbbox((0, 0), badge_text, font=f_badge)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x, pad_y = 30, 20
    bx = (W_PX - tw) // 2 - pad_x
    by = band_top + 320
    draw.rounded_rectangle(
        [(bx, by), (bx + tw + 2 * pad_x, by + th + 2 * pad_y + 10)],
        radius=20, fill=RED_ACCENT
    )
    draw.text((bx + pad_x, by + pad_y), badge_text, font=f_badge, fill=WHITE)

    out_path = f"{OUTPUT_DIR}/flyer_metrotaxi_RECTO_A6.png"
    img.save(out_path, "PNG", dpi=(DPI, DPI))
    print(f"   ✅ RECTO sauvegardé : {out_path}")
    return out_path


# ==================== ÉTAPE 3 : Compose VERSO ====================
def compose_verso() -> str:
    print("\n🖌️ Étape 3/4 : Composition VERSO (full PIL design)...")
    img = Image.new("RGB", (W_PX, H_PX), BLACK)
    draw = ImageDraw.Draw(img)

    # Bande jaune en haut
    band_h = round(20 * MM_TO_PX)
    draw.rectangle([(0, 0), (W_PX, band_h)], fill=YELLOW)

    f_top_brand = ImageFont.truetype(FONT_BOLD, 90)
    text = "MÉTRO-TAXI 🚖"
    text = "MÉTRO-TAXI"
    bbox = draw.textbbox((0, 0), text, font=f_top_brand)
    tw = bbox[2] - bbox[0]
    x = (W_PX - tw) // 2
    draw.text((x, 30), text, font=f_top_brand, fill=BLACK)

    # Sous-titre sous bandeau
    y = band_h + round(8 * MM_TO_PX)
    f_subtitle = ImageFont.truetype(FONT_BOLD, 65)
    text = "Pourquoi t'abonner ?"
    bbox = draw.textbbox((0, 0), text, font=f_subtitle)
    tw = bbox[2] - bbox[0]
    x = (W_PX - tw) // 2
    draw.text((x, y), text, font=f_subtitle, fill=YELLOW)

    # Liste avantages (utiliser puces ASCII compatibles toutes fonts)
    y += 130
    f_list = ImageFont.truetype(FONT_REG, 48)
    f_list_bold = ImageFont.truetype(FONT_BOLD, 60)
    avantages = [
        "Trajet partagé intelligent",
        "Moins cher que Uber/Bolt",
        "Chauffeurs locaux 93",
        "Confort + dignité",
    ]
    for text in avantages:
        x = round(12 * MM_TO_PX)
        # Puce jaune ronde solide
        bullet_size = 24
        draw.ellipse([(x, y + 20), (x + bullet_size, y + 20 + bullet_size)], fill=YELLOW)
        draw.text((x + bullet_size + 30, y), text, font=f_list, fill=WHITE)
        y += 75

    # Séparateur
    y += 20
    draw.line([(round(10 * MM_TO_PX), y), (W_PX - round(10 * MM_TO_PX), y)], fill=YELLOW, width=4)
    y += 40

    # Tarifs
    f_price_label = ImageFont.truetype(FONT_BOLD, 55)
    text = "Abonnement dès"
    bbox = draw.textbbox((0, 0), text, font=f_price_label)
    tw = bbox[2] - bbox[0]
    x = (W_PX - tw) // 2
    draw.text((x, y), text, font=f_price_label, fill=WHITE)
    y += 75

    f_price_big = ImageFont.truetype(FONT_BOLD, 160)
    text = "6,99€"
    bbox = draw.textbbox((0, 0), text, font=f_price_big)
    tw = bbox[2] - bbox[0]
    x = (W_PX - tw) // 2
    draw.text((x, y), text, font=f_price_big, fill=YELLOW)
    y += 175

    f_price_small = ImageFont.truetype(FONT_REG, 38)
    text = "par jour  •  19,99€/7j  •  53,99€/30j"
    bbox = draw.textbbox((0, 0), text, font=f_price_small)
    tw = bbox[2] - bbox[0]
    x = (W_PX - tw) // 2
    draw.text((x, y), text, font=f_price_small, fill=WHITE)
    y += 60

    # Bandeau bas avec QR code
    bottom_band_h = round(55 * MM_TO_PX)
    band_y = H_PX - bottom_band_h - round(2 * MM_TO_PX)
    draw.rectangle([(0, band_y), (W_PX, H_PX)], fill=YELLOW)

    # QR code
    qr = qrcode.QRCode(version=2, box_size=10, border=1)
    qr.add_data("https://metro-taxi.com/saint-denis")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="yellow").convert("RGB")
    qr_size = round(38 * MM_TO_PX)
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    qr_x = round(10 * MM_TO_PX)
    qr_y = band_y + (bottom_band_h - qr_size) // 2
    img.paste(qr_img, (qr_x, qr_y))

    # Texte côté QR
    text_x = qr_x + qr_size + round(8 * MM_TO_PX)
    f_cta = ImageFont.truetype(FONT_BOLD, 52)
    draw.text((text_x, band_y + round(7 * MM_TO_PX)), "Scanne-moi !", font=f_cta, fill=BLACK)

    f_url = ImageFont.truetype(FONT_BOLD, 36)
    draw.text((text_x, band_y + round(18 * MM_TO_PX)), "metro-taxi.com", font=f_url, fill=BLACK)
    draw.text((text_x, band_y + round(25 * MM_TO_PX)), "/saint-denis", font=f_url, fill=BLACK)

    f_phone = ImageFont.truetype(FONT_BOLD, 36)
    draw.text((text_x, band_y + round(35 * MM_TO_PX)), "06 05 78 64 25", font=f_phone, fill=BLACK)

    out_path = f"{OUTPUT_DIR}/flyer_metrotaxi_VERSO_A6.png"
    img.save(out_path, "PNG", dpi=(DPI, DPI))
    print(f"   ✅ VERSO sauvegardé : {out_path}")
    return out_path


# ==================== ÉTAPE 4 : Export PDF combiné ====================
def export_pdf(recto: str, verso: str) -> str:
    print("\n📄 Étape 4/4 : Export PDF Vistaprint...")
    out_pdf = f"{OUTPUT_DIR}/flyer_metrotaxi_A6_VISTAPRINT.pdf"
    r = Image.open(recto).convert("RGB")
    v = Image.open(verso).convert("RGB")
    r.save(out_pdf, "PDF", resolution=DPI, save_all=True, append_images=[v])
    print(f"   ✅ PDF combiné : {out_pdf}")
    return out_pdf


async def main():
    raw_bg = await generate_recto_background()
    recto = compose_recto(raw_bg)
    verso = compose_verso()
    pdf = export_pdf(recto, verso)
    print("\n" + "=" * 60)
    print("🎉 FLYER VISTAPRINT GÉNÉRÉ")
    print("=" * 60)
    print(f"\n📥 LIENS DE TÉLÉCHARGEMENT :")
    base = "https://metro-taxi-demo.preview.emergentagent.com/marketing"
    print(f"   • RECTO (PNG) : {base}/flyer_metrotaxi_RECTO_A6.png")
    print(f"   • VERSO (PNG) : {base}/flyer_metrotaxi_VERSO_A6.png")
    print(f"   • PDF VISTAPRINT : {base}/flyer_metrotaxi_A6_VISTAPRINT.pdf")


if __name__ == "__main__":
    asyncio.run(main())
