"""
Génération des vidéos Sora #2 et #3 en parallèle
"""
import os
import time
import requests
import threading
from pathlib import Path

OUTPUT_DIR = Path("/app/marketing_assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EMERGENT_LLM_KEY = "sk-emergent-44391E9Cd6f68CcA72"
BASE_URL = "https://integrations.emergentagent.com/llm/openai/v1"

VIDEOS = {
    "video_2_calcul_simple": """Cinematic vertical video 9:16 aspect ratio, 12 seconds.
Scene 1 (0-4s): Aerial drone shot of a single car driving through empty Paris boulevards at golden hour. Eiffel Tower visible in distant background, soft warm sunlight.
Scene 2 (4-8s): Smooth transition to a clean modern infographic on dark blue background. Numbers animate elegantly: '150 km × 1,50€ = 225€/jour'. Then: '× 22 jours = 4 950€/mois'. Clean minimalist typography in white and gold.
Scene 3 (8-12s): Final shot fades to royal blue background with 'Métro-Taxi' logo emerging. Subtitle: 'Chauffeurs : 1,50€/km garanti.'
Style: Premium French commercial, professional cinematography, elegant motion graphics.""",

    "video_3_liberte_retrouvee": """Cinematic vertical video 9:16 aspect ratio, 12 seconds.
Scene 1 (0-4s): POV shot through a clean car windshield driving through scenic Parisian streets at sunset. Hands lightly resting on the steering wheel, relaxed posture. Warm golden hour light bathes the scene.
Scene 2 (4-8s): Camera pulls back to show the car driving freely through wide empty avenues. Text overlay fades in elegantly: 'Travaille quand tu veux. Où tu veux.'
Scene 3 (8-12s): Final reveal: 'Métro-Taxi - La plateforme qui respecte le chauffeur' on royal blue background with subtle logo animation.
Style: Cinematic, emotional, freedom-themed French commercial, professional color grading."""
}


def generate_video(name, prompt):
    print(f"🎬 [{name}] Démarrage...")
    
    headers = {
        "Authorization": f"Bearer {EMERGENT_LLM_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sora-2",
        "prompt": prompt,
        "size": "720x1280",
        "seconds": "12"
    }
    
    response = requests.post(f"{BASE_URL}/videos", headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
        print(f"❌ [{name}] Erreur init: {response.status_code} - {response.text[:200]}")
        return
    
    video_id = response.json().get("id")
    print(f"✅ [{name}] ID: {video_id}")
    
    start = time.time()
    while time.time() - start < 600:
        time.sleep(15)
        elapsed = int(time.time() - start)
        
        status_resp = requests.get(f"{BASE_URL}/videos/{video_id}", headers=headers, timeout=30)
        if status_resp.status_code != 200:
            continue
        
        status_data = status_resp.json()
        status = status_data.get("status")
        progress = status_data.get("progress", 0)
        
        print(f"  [{name}] [{elapsed}s] {status} | {progress}%")
        
        if status == "completed":
            download_url = f"{BASE_URL}/videos/{video_id}/content"
            video_resp = requests.get(download_url, headers=headers, timeout=120)
            if video_resp.status_code == 200:
                output_path = OUTPUT_DIR / f"{name}.mp4"
                output_path.write_bytes(video_resp.content)
                size_mb = len(video_resp.content) / (1024 * 1024)
                print(f"✅ [{name}] Sauvegardée: {output_path} ({size_mb:.1f} MB)")
                return
            else:
                print(f"❌ [{name}] Download error: {video_resp.status_code}")
                return
        
        elif status == "failed":
            print(f"❌ [{name}] Génération échouée")
            return
    
    print(f"⏰ [{name}] Timeout")


if __name__ == "__main__":
    threads = []
    for name, prompt in VIDEOS.items():
        t = threading.Thread(target=generate_video, args=(name, prompt))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    print("\n🎯 Toutes les générations terminées")
