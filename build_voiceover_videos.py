"""
Génération voix off française + textes incrustés pour Vidéos 2 & 3 Métro-Taxi.
Voix : OpenAI TTS-1-HD (Onyx, masculine pro). Sous-titres burn-in via ffmpeg.
"""
import asyncio
import os
import subprocess
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

from emergentintegrations.llm.openai import OpenAITextToSpeech

MARKETING_DIR = "/app/frontend/public/marketing"

# ============================================================
# SCRIPTS — 2 vidéos avec timeline précise
# ============================================================
# Durée totale visée: 12 sec / vidéo. La voix off occupe ~9-10 sec, 2 sec de respiration.
# Sous-titres SRT avec timings synchronisés sur la voix.

SCRIPTS = {
    "metrotaxi_scenario2_metro_vs": {
        "voice_text": "Le métro, bondé. Le stress quotidien. Et si on changeait ? Métro-Taxi. Confort, dignité, prix juste. Saint-Denis. À partir du 13 juin.",
        "subtitles_srt": """1
00:00:00,500 --> 00:00:02,800
Le métro, bondé.

2
00:00:03,000 --> 00:00:05,500
Le stress quotidien.

3
00:00:06,000 --> 00:00:08,500
Et si on changeait ?

4
00:00:09,000 --> 00:00:11,500
Métro-Taxi — Saint-Denis, 13 juin.
""",
    },
    "metrotaxi_scenario3_transbordement": {
        "voice_text": "Trois personnes. Une voiture. Un trajet intelligent. C'est ça, le transbordement Métro-Taxi. Moins de trafic. Plus de partage. Saint-Denis, 13 juin 2026.",
        "subtitles_srt": """1
00:00:00,500 --> 00:00:02,800
Trois personnes. Une voiture.

2
00:00:03,000 --> 00:00:05,500
Un trajet intelligent.

3
00:00:06,000 --> 00:00:08,500
Le transbordement Métro-Taxi.

4
00:00:09,000 --> 00:00:11,500
Saint-Denis — 13 juin 2026.
""",
    },
}


async def generate_voice(text: str, output_path: str):
    api_key = os.getenv("EMERGENT_LLM_KEY")
    tts = OpenAITextToSpeech(api_key=api_key)
    audio_bytes = await tts.generate_speech(
        text=text,
        model="tts-1-hd",
        voice="onyx",
        response_format="mp3",
        speed=1.0,
    )
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    return output_path


def get_duration(file_path: str) -> float:
    """Retourne la durée en secondes d'un fichier audio/vidéo."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


def assemble_final_video(base_video: str, voice_mp3: str, srt_file: str, output: str):
    """Mixe la vidéo de base avec voix off + sous-titres burn-in."""
    cmd = [
        "ffmpeg", "-y",
        "-i", base_video,
        "-i", voice_mp3,
        "-vf", f"subtitles={srt_file}:force_style='Fontname=Helvetica,Fontsize=22,PrimaryColour=&H0000D6FF,OutlineColour=&H00000000,Outline=3,Bold=1,Alignment=2,MarginV=140'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        "-movflags", "+faststart",
        output,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ❌ ffmpeg error: {result.stderr[-500:]}")
        return False
    return True


async def process_video(video_id: str, config: dict):
    print(f"\n=== {video_id} ===")
    base_video = f"{MARKETING_DIR}/{video_id}.mp4"
    voice_mp3 = f"{MARKETING_DIR}/{video_id}_voice.mp3"
    srt_file = f"{MARKETING_DIR}/{video_id}.srt"
    output = f"{MARKETING_DIR}/{video_id}_FINAL.mp4"

    # 1. Génère voix off
    print(f"  [1/3] Génération voix off (Onyx, FR)...")
    started = datetime.now()
    await generate_voice(config["voice_text"], voice_mp3)
    voice_duration = get_duration(voice_mp3)
    elapsed = (datetime.now() - started).total_seconds()
    print(f"        ✅ Voix générée: {voice_duration:.1f}s ({os.path.getsize(voice_mp3)//1024} Ko) en {elapsed:.1f}s")

    # 2. Écrit le SRT
    print(f"  [2/3] Écriture sous-titres SRT...")
    with open(srt_file, "w", encoding="utf-8") as f:
        f.write(config["subtitles_srt"])
    print(f"        ✅ {srt_file}")

    # 3. Assemble vidéo finale
    print(f"  [3/3] Assemblage final (vidéo + voix + sous-titres)...")
    ok = assemble_final_video(base_video, voice_mp3, srt_file, output)
    if ok:
        size = os.path.getsize(output) // 1024
        duration = get_duration(output)
        print(f"        ✅ {output} ({size} Ko, {duration:.1f}s)")
    else:
        print(f"        ❌ ÉCHEC")


async def main():
    for video_id, config in SCRIPTS.items():
        await process_video(video_id, config)
    print("\n" + "=" * 60)
    print("✅ TERMINÉ")
    print("=" * 60)
    print("\nFichiers finaux:")
    for video_id in SCRIPTS:
        path = f"{MARKETING_DIR}/{video_id}_FINAL.mp4"
        if os.path.exists(path):
            print(f"  • https://metro-taxi-demo.preview.emergentagent.com/marketing/{os.path.basename(path)}")


if __name__ == "__main__":
    asyncio.run(main())
