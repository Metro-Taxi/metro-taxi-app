"""Génération de la vidéo Sora #2 - Le calcul simple"""
import time
import requests
from pathlib import Path

OUTPUT_DIR = Path("/app/marketing_assets")
EMERGENT_LLM_KEY = "sk-emergent-44391E9Cd6f68CcA72"
BASE_URL = "https://integrations.emergentagent.com/llm/openai/v1"

PROMPT = """Cinematic vertical video 9:16 aspect ratio, 12 seconds.
Scene 1 (0-4s): Aerial drone shot of a single car driving through empty Paris boulevards at golden hour. Eiffel Tower visible in distant background, soft warm sunlight.
Scene 2 (4-8s): Smooth transition to a clean modern infographic on dark blue background. Numbers animate elegantly: '150 km × 1,50€ = 225€/jour'. Then: '× 22 jours = 4 950€/mois'. Clean minimalist typography in white and gold.
Scene 3 (8-12s): Final shot fades to royal blue background with 'Métro-Taxi' logo emerging. Subtitle: 'Chauffeurs : 1,50€/km garanti.'
Style: Premium French commercial, professional cinematography, elegant motion graphics."""

headers = {
    "Authorization": f"Bearer {EMERGENT_LLM_KEY}",
    "Content-Type": "application/json"
}

print("🎬 Génération vidéo Sora #2 - 'Le calcul simple'")
response = requests.post(f"{BASE_URL}/videos", headers=headers, json={
    "model": "sora-2",
    "prompt": PROMPT,
    "size": "720x1280",
    "seconds": "12"
}, timeout=60)

if response.status_code != 200:
    print(f"❌ Erreur: {response.status_code} - {response.text}")
    exit(1)

video_id = response.json().get("id")
print(f"✅ ID: {video_id}")

start = time.time()
while time.time() - start < 600:
    time.sleep(20)
    elapsed = int(time.time() - start)
    
    try:
        status_resp = requests.get(f"{BASE_URL}/videos/{video_id}", headers=headers, timeout=60)
        status_data = status_resp.json()
        status = status_data.get("status")
        progress = status_data.get("progress", 0)
        print(f"  [{elapsed}s] {status} | {progress}%")
        
        if status == "completed":
            video_resp = requests.get(f"{BASE_URL}/videos/{video_id}/content", headers=headers, timeout=180)
            output_path = OUTPUT_DIR / "video_2_calcul_simple.mp4"
            output_path.write_bytes(video_resp.content)
            size_mb = len(video_resp.content) / (1024 * 1024)
            print(f"✅ Sauvegardée: {output_path} ({size_mb:.1f} MB)")
            break
        elif status == "failed":
            print(f"❌ Échec: {status_data}")
            break
    except Exception as e:
        print(f"  [{elapsed}s] Retry après erreur: {type(e).__name__}")
        continue
