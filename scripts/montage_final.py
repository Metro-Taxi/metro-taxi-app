"""
Montage final des 3 vidéos campagne chauffeurs Métro-Taxi
- Coupe les 2 dernières secondes de la vidéo Sora (où le texte halluciné apparait)
- Ajoute une outro 3 secondes avec logo officiel + URL metro-taxi.com
- Fusionne avec la voix off TTS
"""
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path("/app/marketing_assets")
OUTPUT_DIR = Path("/app/marketing_assets/final")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGO_PATH = "/app/frontend/public/icons/metro-taxi-logo.png"

VIDEOS = [
    {
        "name": "video_1_chiffre_qui_fait_mal",
        "video": ASSETS_DIR / "video_1_chiffre_qui_fait_mal.mp4",
        "voice": ASSETS_DIR / "voix_1_chiffre_qui_fait_mal.mp3",
    },
    {
        "name": "video_2_calcul_simple",
        "video": ASSETS_DIR / "video_2_calcul_simple.mp4",
        "voice": ASSETS_DIR / "voix_2_calcul_simple.mp3",
    },
    {
        "name": "video_3_liberte_retrouvee",
        "video": ASSETS_DIR / "video_3_liberte_retrouvee.mp4",
        "voice": ASSETS_DIR / "voix_3_liberte_retrouvee.mp3",
    },
]


def create_outro_image(output_path: str):
    """Crée une image d'outro avec logo officiel + URL"""
    # Format vertical 720x1280 (Sora output)
    W, H = 720, 1280
    
    # Background bleu Métro-Taxi
    img = Image.new("RGB", (W, H), (15, 35, 90))  # Bleu nuit profond
    draw = ImageDraw.Draw(img)
    
    # Logo au centre haut
    logo = Image.open(LOGO_PATH).convert("RGBA")
    
    # Resize logo (max 400px wide)
    logo_target_w = 480
    aspect = logo.height / logo.width
    logo_target_h = int(logo_target_w * aspect)
    logo = logo.resize((logo_target_w, logo_target_h), Image.LANCZOS)
    
    # Center logo (positioned slightly above middle)
    logo_x = (W - logo_target_w) // 2
    logo_y = (H - logo_target_h) // 2 - 150
    img.paste(logo, (logo_x, logo_y), logo)
    
    # Try to load a nice font, fallback to default
    try:
        font_url = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except Exception:
        font_url = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    
    # URL principale - centred
    url_text = "metro-taxi.com"
    url_bbox = draw.textbbox((0, 0), url_text, font=font_url)
    url_w = url_bbox[2] - url_bbox[0]
    url_x = (W - url_w) // 2
    url_y = logo_y + logo_target_h + 80
    draw.text((url_x, url_y), url_text, fill=(255, 215, 0), font=font_url)  # Or
    
    # Sous-titre
    sub_text = "Inscription gratuite"
    sub_bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (W - sub_w) // 2
    sub_y = url_y + 90
    draw.text((sub_x, sub_y), sub_text, fill=(255, 255, 255), font=font_sub)
    
    img.save(output_path, quality=95)
    print(f"  ✅ Outro image créée: {output_path}")


def get_video_duration(video_path: str) -> float:
    """Récupère la durée d'une vidéo"""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())


def process_video(video_info: dict):
    name = video_info["name"]
    video_in = video_info["video"]
    voice_in = video_info["voice"]
    
    print(f"\n🎬 [{name}]")
    
    # 1. Get original video duration
    duration = get_video_duration(video_in)
    print(f"  📏 Durée originale: {duration:.1f}s")
    
    # 2. Cut last 2 seconds (where Sora hallucinated logo/text)
    cut_duration = duration - 2.0
    cut_path = OUTPUT_DIR / f"{name}_cut.mp4"
    cmd_cut = [
        "ffmpeg", "-y", "-i", str(video_in),
        "-t", str(cut_duration),
        "-c", "copy",
        str(cut_path)
    ]
    subprocess.run(cmd_cut, capture_output=True, check=True)
    print(f"  ✂️  Cut à {cut_duration:.1f}s")
    
    # 3. Create outro image
    outro_img_path = OUTPUT_DIR / f"{name}_outro.png"
    create_outro_image(str(outro_img_path))
    
    # 4. Convert outro image to 3-second video
    outro_video_path = OUTPUT_DIR / f"{name}_outro.mp4"
    cmd_outro = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(outro_img_path),
        "-c:v", "libx264", "-t", "3",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=720:1280,fps=30",
        str(outro_video_path)
    ]
    subprocess.run(cmd_outro, capture_output=True, check=True)
    print(f"  🎨 Outro vidéo créée (3s)")
    
    # 5. Concatenate cut video + outro
    concat_list = OUTPUT_DIR / f"{name}_concat.txt"
    concat_list.write_text(f"file '{cut_path.absolute()}'\nfile '{outro_video_path.absolute()}'\n")
    
    concat_path = OUTPUT_DIR / f"{name}_concat.mp4"
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", "scale=720:1280,fps=30",
        str(concat_path)
    ]
    subprocess.run(cmd_concat, capture_output=True, check=True)
    print(f"  🔗 Concaténation OK")
    
    # 6. Add voice-over audio
    final_path = OUTPUT_DIR / f"{name}_FINAL.mp4"
    cmd_audio = [
        "ffmpeg", "-y",
        "-i", str(concat_path),
        "-i", str(voice_in),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        str(final_path)
    ]
    subprocess.run(cmd_audio, capture_output=True, check=True)
    
    final_size_mb = final_path.stat().st_size / (1024 * 1024)
    final_duration = get_video_duration(final_path)
    print(f"  ✅ FINAL: {final_path.name} ({final_size_mb:.1f}MB, {final_duration:.1f}s)")
    
    # Cleanup intermediate files
    for f in [cut_path, outro_video_path, outro_img_path, concat_list, concat_path]:
        try:
            f.unlink()
        except Exception:
            pass
    
    return str(final_path)


if __name__ == "__main__":
    print("🎬 MONTAGE FINAL - Campagne Chauffeurs Métro-Taxi")
    print("=" * 60)
    
    results = []
    for video_info in VIDEOS:
        try:
            result = process_video(video_info)
            results.append((video_info["name"], result))
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            results.append((video_info["name"], None))
    
    print("\n" + "=" * 60)
    print("📊 RÉCAPITULATIF FINAL:")
    for name, path in results:
        status = "✅" if path else "❌"
        print(f"  {status} {name}: {path or 'ÉCHEC'}")
