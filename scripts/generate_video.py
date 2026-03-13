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
    A cinematic promotional video for Métro-Taxi, an eco-friendly urban ride-sharing subscription service.
    
    Scene 1: A beautiful young blonde woman in a modern apartment, smiling as she downloads and opens the Métro-Taxi app on her smartphone. She registers on the app, her face lit by the yellow glow of the screen showing the Métro-Taxi logo.
    
    Scene 2: Close-up of her phone screen showing a map interface with multiple yellow taxi icons around her location. She scrolls and taps, browsing through available VTC vehicles nearby, checking their destinations and available seats. Her expression shows excitement as she finds the perfect ride.
    
    Scene 3: The blonde woman gets into a sleek yellow and black Métro-Taxi vehicle. The driver, a friendly middle-aged man in professional attire, smiles warmly and greets her. They drive through beautiful city streets.
    
    Scene 4: The transbordement scene - The taxi stops at a designated transfer point in a clean urban plaza. The blonde woman thanks the first driver who waves goodbye with satisfaction. She walks a few steps to another waiting yellow Métro-Taxi. A second driver, a happy woman, welcomes her with a warm smile. The transfer is seamless and elegant.
    
    Scene 5: Multiple shots of satisfied Métro-Taxi drivers - a diverse group of professional drivers smiling in their vehicles, waving to passengers, looking proud and content with their work. Yellow taxis moving efficiently through green, eco-friendly city streets.
    
    Scene 6: Final shot - the blonde woman arrives at her destination, exits the taxi with a grateful smile, waves to the driver. The Métro-Taxi drives away into a beautiful sunset cityscape.
    
    Style: Premium, modern, warm cinematography. Yellow, black and white color palette. Professional and friendly atmosphere. Emphasis on human connection, satisfaction, and sustainable urban mobility.
    """
    
    print("🎬 Génération de la vidéo Métro-Taxi en cours...")
    print("⏳ Cela peut prendre 3-5 minutes...")
    
    video_gen = OpenAIVideoGeneration(api_key=os.environ['EMERGENT_LLM_KEY'])
    
    video_bytes = video_gen.text_to_video(
        prompt=prompt,
        model="sora-2",
        size="1280x720",  # HD format
        duration=12,  # 12 seconds for more detailed scenes
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
