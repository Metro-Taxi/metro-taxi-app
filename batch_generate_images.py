"""
Génération batch des 11 images restantes (3 scénarios) via Gemini Nano Banana 3.1.
"""
import asyncio
import os
import base64
import json
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

from emergentintegrations.llm.chat import LlmChat, UserMessage

OUTPUT_DIR = "/app/frontend/public/marketing"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============= STYLE DE BASE COMMUN =============
STYLE_BASE = """
Cinematic vertical 9:16 mobile photograph, hyper-realistic documentary style, photojournalism quality.
Shot on Sony A7 with 35mm lens, shallow depth of field.
Color grading: warm earth tones, natural daylight, slight muted shadows.
NO text overlays, NO logos, NO watermarks. Photorealistic, not stylized.
Aspect ratio: 9:16 vertical (mobile portrait).
"""

# ============= SCÉNARIO 1 — Bus bondé (images 02-04) =============
PROMPTS = {
    "scenario1_bus_bonde_02": f"""{STYLE_BASE}
Scene: SAME senior woman wearing beige hijab and earth-tone long dress from the previous frame, still standing on Saint-Denis market sidewalk holding two shopping bags. She is now looking at her smartphone screen with a hopeful expression, having just opened a mobility app.
Foreground: Close-up profile shot of her face, her aged hands holding the phone, fingers tapping a yellow button on screen (no app interface visible, just the warm yellow glow reflecting on her face).
Background: blurred Saint-Denis market stalls and the silhouette of Basilique de Saint-Denis in the very distant background.
Lighting: warm late morning sunlight on her face, soft contrast highlighting renewed hope in her expression.
Composition: rule of thirds, woman's face in upper third, phone in middle, hands and bags in lower third.
""",

    "scenario1_bus_bonde_03": f"""{STYLE_BASE}
Scene: A modern clean yellow VTC sedan car (smooth design, looks like a recent Renault or Peugeot in bright taxi yellow color, not RATP-branded) arrives smoothly on the Saint-Denis market street, parking on the curb next to the same senior woman.
Foreground: the yellow car taking up most of the right side of the frame, side view showing clean modern design.
Middle: the senior woman with hijab and shopping bags from previous images, visible in profile relaxing as she sees the car arriving, slight smile of relief beginning.
Background: same Saint-Denis Saturday market scene, RATP bus has already left, less crowded street.
Lighting: golden hour warm sun reflecting on the yellow car paint, creating a hopeful contrast vs the previous tired scene.
""",

    "scenario1_bus_bonde_04": f"""{STYLE_BASE}
Scene: Interior of the yellow VTC car. The senior woman from previous frames now seated comfortably in the back seat, both shopping bags placed beside her on the seat, hands resting peacefully on her lap. She is gently smiling, exhaling with visible relief, looking out the window.
Foreground: her face shown in 3/4 profile, the soft window light bathing her features. We can see the seatbelt across her chest.
Middle: driver's silhouette in the front (we don't see his face clearly, just the back of his head, professional appearance).
Background: through the window, Saint-Denis urban street passing by, blurred motion.
Lighting: soft warm interior daylight, the woman's face glowing peacefully.
Color: warm beige interior with yellow accents (subtly matching the brand colors).
""",
}

# ============= SCÉNARIO 2 — Métro vs Métro-Taxi (4 images) =============
PROMPTS.update({
    "scenario2_metro_vs_01": f"""{STYLE_BASE}
Scene: Crowded RATP metro line 13 at rush hour at Saint-Denis Université station. The interior of a packed metro car: diverse working-class commuters tightly pressed against each other and the doors, many holding handrails, faces showing fatigue, phones in hands, sweat visible on foreheads. Stark fluorescent metro lighting.
Foreground: close shot of a young man's tired face leaning against the door window, eyes half-closed.
Background: other commuters packed behind him, RATP metro interior visible (gray seats, yellow handles).
Mood: claustrophobic, exhausting, hyper-realistic Parisian metro experience.
Lighting: harsh fluorescent metro light, cold blue tones.
""",

    "scenario2_metro_vs_02": f"""{STYLE_BASE}
Scene: Saint-Denis Université metro station platform during morning rush. Massive crowd of commuters pushing toward an arriving train, frustrated and impatient. Diverse working class of Paris northern suburbs.
Foreground: a young Black woman in business casual looking at her watch with frustration, late for work.
Background: dense crowd, RATP station signage visible (but blurry, no specific text), train arriving.
Mood: overwhelming, stress, urban suffocation.
Lighting: artificial cold station lighting, harsh shadows.
""",

    "scenario2_metro_vs_03": f"""{STYLE_BASE}
Scene: Clean spacious interior of a yellow Métro-Taxi VTC car. Three passengers seated comfortably and respectfully spaced: a young Black woman in business casual (left), a senior Maghrebi man with a leather briefcase (middle), a young white man with a backpack (right). All three are calm, the Black woman looking peacefully out the window, the older man reading something on his phone, the young man relaxing. Driver visible in front (back of head, focused).
Foreground: all three passengers visible in the back, soft natural light through windows.
Background: through windows, Saint-Denis modern boulevard passing by.
Atmosphere: warm, dignified, premium yet accessible. The opposite of the metro suffocation.
Lighting: warm natural daylight, soft golden tones.
""",

    "scenario2_metro_vs_04": f"""{STYLE_BASE}
Scene: Exterior wide shot of the same yellow Métro-Taxi VTC sedan driving smoothly on a sunlit boulevard in Saint-Denis, the Basilique de Saint-Denis prominently visible in the background, late afternoon golden hour.
Foreground: the yellow car in motion, side angle, slight motion blur on the wheels showing smooth driving.
Middle: a typical Saint-Denis street with modern buildings mixed with older Haussmann-style architecture, trees lining the sidewalk.
Background: the iconic Basilique de Saint-Denis cathedral spires against a warm sky.
Mood: hopeful, premium, dignified urban mobility solution.
Lighting: golden hour, warm reflections on the car paint.
""",
})

# ============= SCÉNARIO 3 — Transbordement intelligent (4 images) =============
PROMPTS.update({
    "scenario3_transbordement_01": f"""{STYLE_BASE}
Scene: Bird's eye aerial drone shot of Saint-Denis at late afternoon. The Basilique de Saint-Denis cathedral clearly visible in the upper portion, surrounded by typical northern Paris suburbs streets, the Stade de France visible in the distance.
3 distinct GLOWING YELLOW spots visible on three different street locations across the city — these are subtle, like soft golden orbs marking pickup points (one near the Basilique, one near a market, one near a residential block). NO arrows, NO text, just the 3 yellow glows.
Mood: bird's eye perspective revealing the smart connection across the city.
Lighting: late afternoon natural light, slight haze giving a cinematic depth.
Aspect ratio: vertical 9:16 (the city scape stretches vertically).
""",

    "scenario3_transbordement_02": f"""{STYLE_BASE}
Scene: Same aerial drone shot of Saint-Denis, but now ONE single yellow car (Métro-Taxi VTC sedan) is visible from above, mid-route on a connecting boulevard. Its path is suggested by a very subtle warm trail/light line connecting the 3 yellow glowing points from the previous frame, drawing an optimized route across the urban grid.
Foreground: the yellow car clearly visible from above with the warm trail behind it.
Background: rest of Saint-Denis cityscape, Basilique visible.
Mood: efficient, smart, optimized mobility revealed from above.
Lighting: late afternoon natural light with slight warmth.
""",

    "scenario3_transbordement_03": f"""{STYLE_BASE}
Scene: Interior of the same yellow Métro-Taxi VTC car. Three passengers seated together in the back: a young African woman in colorful work clothes (left), a Maghrebi student with a backpack (middle), a senior white woman with a small grocery bag (right). All three are smiling and chatting respectfully, like neighbors sharing a smart ride. The atmosphere is friendly, community-oriented, dignified.
Foreground: the three passengers seen at angle, soft daylight through windows.
Background: through windows, Saint-Denis residential boulevard.
Mood: community, sharing, friendliness, smart mobility.
Lighting: warm natural daylight, soft golden tones inside the car.
""",

    "scenario3_transbordement_04": f"""{STYLE_BASE}
Scene: Cinematic exterior wide shot of the yellow Métro-Taxi VTC car driving along a sunlit boulevard at late afternoon golden hour, with the Basilique de Saint-Denis cathedral majestic in the background. The car is shown in motion, beautiful, almost heroic composition.
Foreground: the yellow car centered, side view with slight rear angle showing the car driving away towards the sunset.
Middle: a tree-lined Saint-Denis boulevard.
Background: the Basilique de Saint-Denis with warm sunset behind it, sky painted with gold and soft pink.
Mood: hopeful, iconic, the future of community urban mobility.
Lighting: spectacular golden hour, lens flare from the setting sun, cinematic.
""",
})


async def generate_one(image_id: str, prompt: str):
    started_at = datetime.now()
    output_path = os.path.join(OUTPUT_DIR, f"{image_id}.png")
    meta_path = os.path.join(OUTPUT_DIR, f"{image_id}.json")

    api_key = os.getenv("EMERGENT_LLM_KEY")
    session_id = f"metro-taxi-{image_id}-{int(time.time())}"

    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="You are an expert cinematic photographer creating marketing visuals for an urban mobility brand.",
    )
    chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])

    print(f"[{image_id}] START")
    try:
        msg = UserMessage(text=prompt)
        text, images = await chat.send_message_multimodal_response(msg)
        elapsed = (datetime.now() - started_at).total_seconds()

        if not images:
            print(f"[{image_id}] ❌ No images returned")
            return (image_id, False, "no_images")

        img = images[0]
        image_bytes = base64.b64decode(img["data"])
        with open(output_path, "wb") as f:
            f.write(image_bytes)

        meta = {
            "image_id": image_id,
            "mime_type": img.get("mime_type", "image/png"),
            "file_size": os.path.getsize(output_path),
            "elapsed_seconds": elapsed,
            "generated_at": datetime.now().isoformat(),
            "model": "gemini-3.1-flash-image-preview",
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        print(f"[{image_id}] ✅ OK in {elapsed:.1f}s")
        return (image_id, True, output_path)
    except Exception as e:
        print(f"[{image_id}] ❌ Exception: {e}")
        return (image_id, False, str(e))


async def main():
    # Lance les 11 générations en parallèle par batch de 4 (pour éviter rate limit)
    image_ids = list(PROMPTS.keys())
    print(f"Total images à générer : {len(image_ids)}")
    print("=" * 60)

    batch_size = 4
    all_results = []
    for i in range(0, len(image_ids), batch_size):
        batch = image_ids[i:i+batch_size]
        print(f"\n--- Batch {i//batch_size + 1} ({len(batch)} images) ---")
        tasks = [generate_one(iid, PROMPTS[iid]) for iid in batch]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        all_results.extend(results)

    print("\n" + "=" * 60)
    print("BILAN FINAL")
    print("=" * 60)
    success = [r for r in all_results if r[1]]
    failed = [r for r in all_results if not r[1]]
    print(f"✅ Succès : {len(success)}/{len(all_results)}")
    print(f"❌ Échecs : {len(failed)}/{len(all_results)}")
    if failed:
        for f in failed:
            print(f"  - {f[0]} : {f[2]}")


if __name__ == "__main__":
    asyncio.run(main())
