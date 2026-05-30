"""
Générateur d'images IA pour Métro-Taxi via Gemini Nano Banana 3.1
Sauvegarde dans /app/frontend/public/marketing/ pour servir publiquement.
"""
import asyncio
import os
import sys
import json
import base64
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage

OUTPUT_DIR = "/app/frontend/public/marketing"
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def generate_image(image_id: str, prompt: str, session_id: str = None):
    started_at = datetime.now()
    output_path = os.path.join(OUTPUT_DIR, f"{image_id}.png")
    meta_path = os.path.join(OUTPUT_DIR, f"{image_id}.json")

    api_key = os.getenv("EMERGENT_LLM_KEY")
    if not api_key:
        print(f"[{image_id}] ❌ EMERGENT_LLM_KEY manquante")
        return None

    session_id = session_id or f"metro-taxi-{int(time.time())}"
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="You are an expert cinematic photographer creating marketing visuals for an urban mobility brand.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

    print(f"[{image_id}] Génération en cours...")
    try:
        msg = UserMessage(text=prompt)
        text, images = await chat.send_message_multimodal_response(msg)
        elapsed = (datetime.now() - started_at).total_seconds()

        if not images:
            print(f"[{image_id}] ❌ Aucune image retournée")
            return None

        # On prend la 1ère image retournée
        img = images[0]
        image_bytes = base64.b64decode(img["data"])
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        file_size = os.path.getsize(output_path)
        meta = {
            "image_id": image_id,
            "prompt": prompt[:200] + ("..." if len(prompt) > 200 else ""),
            "mime_type": img.get("mime_type", "image/png"),
            "file_size": file_size,
            "elapsed_seconds": elapsed,
            "generated_at": datetime.now().isoformat(),
            "session_id": session_id,
            "model": "gemini-3.1-flash-image-preview",
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        print(f"[{image_id}] ✅ OK — {file_size//1024} Ko en {elapsed:.1f}s — {output_path}")
        return output_path
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[{image_id}] ❌ Exception: {e}")
        return None


async def main():
    if len(sys.argv) < 3:
        print("Usage: python3 image_generate.py <image_id> <prompt_file>")
        sys.exit(1)

    image_id = sys.argv[1]
    prompt_file = sys.argv[2]
    with open(prompt_file) as f:
        prompt = f.read()
    await generate_image(image_id, prompt)


if __name__ == "__main__":
    asyncio.run(main())
