"""
Génération d'assets marketing pour Métro-Taxi
- 3 voix off TTS françaises (campagne chauffeurs)
- Format MP3, voix masculine grave (autorité)
"""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from emergentintegrations.llm.openai import OpenAITextToSpeech

# Output directory
OUTPUT_DIR = Path("/app/marketing_assets")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EMERGENT_LLM_KEY = "sk-emergent-44391E9Cd6f68CcA72"

# 3 voice scripts (campagne chauffeurs, voix masculine "onyx" - grave et autoritaire)
VOICE_SCRIPTS = {
    "voix_1_chiffre_qui_fait_mal": (
        "Chaque mois, trente pour cent de tes revenus disparaissent en commissions plateformes. "
        "Métro-Taxi change ça. "
        "Zéro commission. Un euro cinquante du kilomètre. "
        "Paiement garanti le dix de chaque mois. "
        "Métro-Taxi point com. Inscription gratuite."
    ),
    "voix_2_calcul_simple": (
        "Cent cinquante kilomètres par jour, à un euro cinquante du kilomètre, "
        "c'est deux cent vingt-cinq euros par jour. "
        "Multiplié par vingt-deux jours ouvrés, c'est quatre mille neuf cent cinquante euros par mois. "
        "Sans commission. "
        "Métro-Taxi point com."
    ),
    "voix_3_liberte_retrouvee": (
        "Être son propre patron. Vraiment. "
        "Pas d'objectifs imposés. Pas de sanctions sur les notes clients. Pas d'exclusivité. "
        "Juste toi, la route, et tes revenus. "
        "Métro-Taxi. La plateforme qui respecte le chauffeur."
    ),
}


async def generate_voice(name: str, text: str):
    """Generate a single voice file using OpenAI TTS"""
    print(f"[TTS] Génération de {name}...")
    
    tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
    
    audio_bytes = await tts.generate_speech(
        text=text,
        voice="onyx",  # Voix masculine grave
        model="tts-1-hd",  # HD quality
        speed=1.0,
        response_format="mp3"
    )
    
    output_path = OUTPUT_DIR / f"{name}.mp3"
    output_path.write_bytes(audio_bytes)
    
    size_kb = len(audio_bytes) / 1024
    print(f"[TTS] ✅ {name}.mp3 généré ({size_kb:.1f} KB)")
    return str(output_path)


async def main():
    print("🎤 Génération des 3 voix off Métro-Taxi (campagne chauffeurs)")
    print(f"📁 Dossier de sortie: {OUTPUT_DIR}")
    print("-" * 60)
    
    tasks = [
        generate_voice(name, text)
        for name, text in VOICE_SCRIPTS.items()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    print("-" * 60)
    print("📊 RÉCAPITULATIF:")
    for name, result in zip(VOICE_SCRIPTS.keys(), results):
        if isinstance(result, Exception):
            print(f"  ❌ {name}: ERREUR - {result}")
        else:
            print(f"  ✅ {name}: {result}")
    
    print("\n🎯 Voix off prêtes pour montage CapCut/Sora")


if __name__ == "__main__":
    asyncio.run(main())
