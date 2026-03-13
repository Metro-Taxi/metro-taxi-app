import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

from emergentintegrations.llm.openai.video_generation import OpenAIVideoGeneration

def generate_metro_taxi_video():
    """Generate promotional video for Métro-Taxi"""
    
    prompt = """
    A cinematic promotional video for an eco-friendly urban ride-sharing service called Métro-Taxi.
    
    Scene 1: Aerial view of a modern European city at golden hour, showing clean streets and sustainable transport.
    
    Scene 2: A sleek yellow taxi with black accents smoothly driving through city streets, picking up a young professional woman with blonde hair who smiles as she gets in.
    
    Scene 3: Inside the vehicle, passengers are comfortable, using their smartphones. The atmosphere is modern and premium.
    
    Scene 4: The same blonde woman exits the first taxi at a designated transfer point and seamlessly enters another yellow taxi - demonstrating the unique "transbordement" feature.
    
    Scene 5: Final shot showing multiple yellow Métro-Taxi vehicles moving efficiently through the city, with green parks and clean air visible in the background.
    
    Style: Modern, professional, cinematic look with warm golden tones. Black, yellow and white color scheme. Premium feel like Uber but emphasizing environmental sustainability.
    """
    
    print("🎬 Génération de la vidéo Métro-Taxi en cours...")
    print("⏳ Cela peut prendre 3-5 minutes...")
    
    video_gen = OpenAIVideoGeneration(api_key=os.environ['EMERGENT_LLM_KEY'])
    
    video_bytes = video_gen.text_to_video(
        prompt=prompt,
        model="sora-2",
        size="1792x1024",  # Widescreen cinematic format
        duration=8,  # 8 seconds for promotional video
        max_wait_time=600
    )
    
    if video_bytes:
        output_path = '/app/frontend/public/videos/metro-taxi-promo.mp4'
        os.makedirs('/app/frontend/public/videos', exist_ok=True)
        video_gen.save_video(video_bytes, output_path)
        print(f'✅ Vidéo sauvegardée: {output_path}')
        return output_path
    else:
        print('❌ Échec de la génération vidéo')
        return None

if __name__ == "__main__":
    result = generate_metro_taxi_video()
    if result:
        print(f"\n🎉 Vidéo Métro-Taxi créée avec succès!")
        print(f"📁 Chemin: {result}")
