import os
import sys
sys.path.insert(0, '/app/backend')
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

from emergentintegrations.llm.openai import OpenAISoraVideoGeneration

async def check_and_generate():
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    print(f"Using key: {api_key[:20]}...")
    
    generator = OpenAISoraVideoGeneration(api_key=api_key)
    
    prompt = """Aerial view of a modern European city at sunset. Yellow taxis smoothly navigate through clean streets. 
    Happy passengers wave as they share rides. The MÉTRO-TAXI logo appears in golden yellow. 
    Urban mobility reimagined. Professional cinematic quality, warm golden hour lighting."""
    
    try:
        print("Initiating video generation...")
        result = await generator.generate_video(
            prompt=prompt,
            duration=10,
            resolution="720p",
            aspect_ratio="16:9"
        )
        print(f"Success! Video URL: {result}")
        return result
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return None

import asyncio
asyncio.run(check_and_generate())
