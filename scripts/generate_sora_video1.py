"""
Génération de la vidéo Sora #1 - "Le chiffre qui fait mal"
Format: 15 secondes, vertical 9:16
Cible: Chauffeurs VTC France
"""
import os
import time
import requests
from pathlib import Path

OUTPUT_DIR = Path("/app/marketing_assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EMERGENT_LLM_KEY = "sk-emergent-44391E9Cd6f68CcA72"
BASE_URL = "https://integrations.emergentagent.com/llm/openai/v1"

# Prompt Sora #1 - Le chiffre qui fait mal
PROMPT = """Cinematic vertical video 9:16 aspect ratio, 15 seconds.
Scene 1 (0-5s): Close-up of male hands counting euro banknotes on a dark wooden desk under dim moody lighting. The counting motion is slow and deliberate. Camera slowly zooms in.
Scene 2 (5-10s): Counting stops abruptly. Bold white text appears in cinematic typography: '30% disparait en commissions'. Background fades to deep black.
Scene 3 (10-15s): Smooth transition to bright royal blue background. Modern minimalist taxi app logo emerges with text 'Métro-Taxi' in clean elegant typography. Subtitle: '0% commission. 1,50€/km.'
Style: Cinematic French commercial, realistic, urban Paris mood, premium quality, professional color grading."""

def generate_sora_video():
    print("🎬 Génération vidéo Sora #1 - 'Le chiffre qui fait mal'")
    print(f"📁 Output: {OUTPUT_DIR}/video_1_chiffre_qui_fait_mal.mp4")
    print("-" * 60)
    
    headers = {
        "Authorization": f"Bearer {EMERGENT_LLM_KEY}",
        "Content-Type": "application/json"
    }
    
    # Step 1: Initiate video generation
    payload = {
        "model": "sora-2",
        "prompt": PROMPT,
        "size": "720x1280",  # Vertical 9:16
        "seconds": "12"  # 12 seconds (Sora 2 supports 4, 8, 12)
    }
    
    print("⏳ Initialisation de la génération Sora...")
    response = requests.post(f"{BASE_URL}/videos", headers=headers, json=payload, timeout=60)
    
    if response.status_code != 200:
        print(f"❌ Erreur init: {response.status_code}")
        print(response.text)
        return None
    
    data = response.json()
    video_id = data.get("id")
    print(f"✅ Génération initiée. ID: {video_id}")
    
    # Step 2: Poll for completion
    print("⏳ Attente de la génération (peut prendre 1-3 minutes)...")
    max_wait = 600  # 10 minutes max
    start = time.time()
    
    while time.time() - start < max_wait:
        time.sleep(15)
        elapsed = int(time.time() - start)
        
        status_resp = requests.get(f"{BASE_URL}/videos/{video_id}", headers=headers, timeout=30)
        if status_resp.status_code != 200:
            print(f"⚠️  Erreur de statut: {status_resp.status_code}")
            continue
        
        status_data = status_resp.json()
        status = status_data.get("status")
        progress = status_data.get("progress", 0)
        
        print(f"  [{elapsed}s] Status: {status} | Progress: {progress}%")
        
        if status == "completed":
            print("✅ Vidéo générée !")
            
            # Download
            download_url = f"{BASE_URL}/videos/{video_id}/content"
            print(f"⬇️  Téléchargement depuis {download_url}...")
            
            video_resp = requests.get(download_url, headers=headers, timeout=120)
            if video_resp.status_code == 200:
                output_path = OUTPUT_DIR / "video_1_chiffre_qui_fait_mal.mp4"
                output_path.write_bytes(video_resp.content)
                size_mb = len(video_resp.content) / (1024 * 1024)
                print(f"✅ Vidéo sauvegardée: {output_path} ({size_mb:.1f} MB)")
                return str(output_path)
            else:
                print(f"❌ Erreur download: {video_resp.status_code}")
                print(video_resp.text)
                return None
        
        elif status == "failed":
            print(f"❌ Génération échouée: {status_data}")
            return None
    
    print("⏰ Timeout: la génération prend trop de temps")
    return None


if __name__ == "__main__":
    result = generate_sora_video()
    if result:
        print(f"\n🎯 SUCCESS: {result}")
    else:
        print("\n❌ ÉCHEC de la génération")
