"""
Génération Sora 2 Pro — Vidéo Métro-Taxi
Sauvegarde dans /app/frontend/public/sora/ pour servir publiquement.
"""
import os
import sys
import time
import json
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

sys.path.insert(0, '/app')

from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration

OUTPUT_DIR = "/app/frontend/public/sora"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate(video_id: str, prompt: str, model: str = "sora-2-pro", size: str = "1024x1792", duration: int = 12):
    started_at = datetime.now()
    output_path = os.path.join(OUTPUT_DIR, f"{video_id}.mp4")
    status_path = os.path.join(OUTPUT_DIR, f"{video_id}.json")

    def write_status(status, **extra):
        with open(status_path, "w") as f:
            json.dump({
                "video_id": video_id,
                "status": status,
                "model": model,
                "size": size,
                "duration": duration,
                "started_at": started_at.isoformat(),
                "updated_at": datetime.now().isoformat(),
                "output_path": output_path if status == "completed" else None,
                "prompt": prompt,
                **extra,
            }, f, indent=2)

    write_status("processing")
    print(f"[{video_id}] Starting Sora 2 generation...")
    print(f"  Model: {model} | Size: {size} | Duration: {duration}s")

    try:
        video_gen = OpenAIVideoGeneration(api_key=os.environ['EMERGENT_LLM_KEY'])
        video_bytes = video_gen.text_to_video(
            prompt=prompt,
            model=model,
            size=size,
            duration=duration,
            max_wait_time=900,  # 15 min for sora-2-pro
        )
        if video_bytes:
            video_gen.save_video(video_bytes, output_path)
            elapsed = (datetime.now() - started_at).total_seconds()
            print(f"[{video_id}] ✅ SUCCESS — saved to {output_path} ({elapsed:.0f}s)")
            write_status("completed", elapsed_seconds=elapsed, file_size=os.path.getsize(output_path))
        else:
            print(f"[{video_id}] ❌ Sora returned empty bytes")
            write_status("failed", error="empty_bytes")
    except Exception as e:
        traceback.print_exc()
        print(f"[{video_id}] ❌ Exception: {e}")
        write_status("failed", error=str(e))


if __name__ == "__main__":
    video_id = sys.argv[1] if len(sys.argv) > 1 else f"video_{int(time.time())}"
    prompt_file = sys.argv[2] if len(sys.argv) > 2 else None
    if prompt_file and os.path.exists(prompt_file):
        with open(prompt_file) as f:
            prompt = f.read()
    else:
        prompt = sys.argv[2] if len(sys.argv) > 2 else "A cat playing piano"
    generate(video_id, prompt)
