"""
Montage final V2 - Élimine le faux logo Sora ET adapte à la durée de la voix off
- Coupe la vidéo Sora à 7 secondes (AVANT que Sora insère son faux logo)
- Crée une outro avec logo officiel dont la durée = (durée voix off) - 7s + 1s buffer
- Résultat : voix off complète, aucun faux logo Sora visible
"""
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path("/app/marketing_assets")
OUTPUT_DIR = Path("/app/marketing_assets/final")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOGO_PATH = "/app/frontend/public/icons/metro-taxi-logo.png"

# Coupe la vidéo Sora à 7s (avant que Sora hallucine son faux logo)
SORA_CUT_DURATION = 7.0
# Buffer après la fin de la voix off
END_BUFFER = 1.0

VIDEOS = [
    {"name": "video_1_chiffre_qui_fait_mal",
     "video": ASSETS_DIR / "video_1_chiffre_qui_fait_mal.mp4",
     "voice": ASSETS_DIR / "voix_1_chiffre_qui_fait_mal.mp3"},
    {"name": "video_2_calcul_simple",
     "video": ASSETS_DIR / "video_2_calcul_simple.mp4",
     "voice": ASSETS_DIR / "voix_2_calcul_simple.mp3"},
    {"name": "video_3_liberte_retrouvee",
     "video": ASSETS_DIR / "video_3_liberte_retrouvee.mp4",
     "voice": ASSETS_DIR / "voix_3_liberte_retrouvee.mp3"},
]


def create_outro_image(output_path: str):
    """Outro fond NOIR + logo officiel + URL metro-taxi.com"""
    W, H = 720, 1280
    img = Image.new("RGB", (W, H), (0, 0, 0))  # Noir pur
    draw = ImageDraw.Draw(img)
    
    # Logo officiel Métro-Taxi (taxi jaune avec damier sur fond noir)
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo_target_w = 620
    aspect = logo.height / logo.width
    logo_target_h = int(logo_target_w * aspect)
    logo = logo.resize((logo_target_w, logo_target_h), Image.LANCZOS)
    logo_x = (W - logo_target_w) // 2
    logo_y = (H - logo_target_h) // 2 - 100
    img.paste(logo, (logo_x, logo_y), logo)
    
    try:
        font_url = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 68)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
    except Exception:
        font_url = ImageFont.load_default()
        font_sub = ImageFont.load_default()
    
    url_text = "metro-taxi.com"
    url_bbox = draw.textbbox((0, 0), url_text, font=font_url)
    url_w = url_bbox[2] - url_bbox[0]
    url_x = (W - url_w) // 2
    url_y = logo_y + logo_target_h + 80
    draw.text((url_x, url_y), url_text, fill=(255, 213, 0), font=font_url)
    
    sub_text = "Inscription gratuite"
    sub_bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_x = (W - sub_w) // 2
    sub_y = url_y + 100
    draw.text((sub_x, sub_y), sub_text, fill=(255, 255, 255), font=font_sub)
    
    img.save(output_path, quality=95)


def get_duration(path: str) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
           "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
    return float(subprocess.run(cmd, capture_output=True, text=True).stdout.strip())


def process_video(video_info: dict):
    name = video_info["name"]
    video_in = video_info["video"]
    voice_in = video_info["voice"]
    
    print(f"\n🎬 [{name}]")
    
    voice_duration = get_duration(voice_in)
    outro_duration = max(voice_duration - SORA_CUT_DURATION + END_BUFFER, 4.0)
    total_duration = SORA_CUT_DURATION + outro_duration
    
    print(f"  📏 Voix off: {voice_duration:.1f}s | Sora cut: {SORA_CUT_DURATION}s | Outro: {outro_duration:.1f}s | Total: {total_duration:.1f}s")
    
    # 1. Cut Sora video à 7s (avant le faux logo halluciné)
    cut_path = OUTPUT_DIR / f"{name}_cut.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(video_in),
        "-t", str(SORA_CUT_DURATION),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", "scale=720:1280,fps=30",
        "-an",  # Pas d'audio
        str(cut_path)
    ], capture_output=True, check=True)
    print(f"  ✂️  Sora coupée à {SORA_CUT_DURATION}s (avant faux logo)")
    
    # 2. Outro image (noir + logo officiel)
    outro_img = OUTPUT_DIR / f"{name}_outro.png"
    create_outro_image(str(outro_img))
    
    # 3. Outro video (durée adaptée à la voix off)
    outro_video = OUTPUT_DIR / f"{name}_outro.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(outro_img),
        "-c:v", "libx264", "-t", f"{outro_duration:.2f}",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=720:1280,fps=30",
        str(outro_video)
    ], capture_output=True, check=True)
    print(f"  🎨 Outro logo officiel ({outro_duration:.1f}s)")
    
    # 4. Concat
    concat_list = OUTPUT_DIR / f"{name}_concat.txt"
    concat_list.write_text(f"file '{cut_path.absolute()}'\nfile '{outro_video.absolute()}'\n")
    
    concat_path = OUTPUT_DIR / f"{name}_concat.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-vf", "scale=720:1280,fps=30",
        str(concat_path)
    ], capture_output=True, check=True)
    
    # 5. Add voice-over (la voix peut maintenant aller jusqu'au bout sans coupure)
    final_path = OUTPUT_DIR / f"{name}_FINAL.mp4"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(concat_path),
        "-i", str(voice_in),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        # Pas de -shortest : on garde la durée totale de la vidéo
        str(final_path)
    ], capture_output=True, check=True)
    
    final_size = final_path.stat().st_size / (1024 * 1024)
    final_dur = get_duration(final_path)
    print(f"  ✅ FINAL: {final_path.name} ({final_size:.1f}MB, {final_dur:.1f}s)")
    
    # Cleanup
    for f in [cut_path, outro_video, outro_img, concat_list, concat_path]:
        try:
            f.unlink()
        except Exception:
            pass
    
    return str(final_path)


if __name__ == "__main__":
    print("🎬 MONTAGE V2 - Élimination faux logo Sora + voix off complète")
    print("=" * 60)
    
    for video_info in VIDEOS:
        try:
            process_video(video_info)
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Toutes les vidéos finales générées")
