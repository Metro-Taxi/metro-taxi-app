"""
Routes API pour le Text-to-Speech (Voiceover) - Métro-Taxi
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, Field
import os
import logging

from emergentintegrations.llm.openai import OpenAITextToSpeech
from services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["tts"])

# Video voiceover scripts for each language
VIDEO_SCRIPTS = {
    "fr": """Métro-Taxi, le système de déplacement intelligent par covoiturage.
Bienvenue sur Métro-Taxi, le réseau de mobilité urbaine par abonnement.
En choisissant le covoiturage intelligent, vous contribuez à la protection de l'environnement en réduisant votre empreinte carbone.
Inscrivez-vous et choisissez votre forfait. Localisez les véhicules allant dans votre direction.
Demandez à monter d'un simple clic. Le chauffeur vous récupère et vous dépose où vous voulez.
Grâce à notre système de transbordement intelligent, changez de véhicule en route pour atteindre votre destination.
Métro-Taxi, vos trajets sans limites, pour un avenir plus vert.""",

    "en": """Métro-Taxi, the intelligent ridesharing transportation system.
Welcome to Métro-Taxi, the subscription-based urban mobility network.
By choosing intelligent ridesharing, you contribute to environmental protection by reducing your carbon footprint.
Sign up and choose your plan. Locate vehicles heading in your direction.
Request a ride with a single click. The driver picks you up and drops you off wherever you want.
Thanks to our intelligent transfer system, switch vehicles along the way to reach your destination.
Métro-Taxi, your rides without limits, for a greener future.""",

    "en-GB": """Métro-Taxi, the intelligent ridesharing transportation system.
Welcome to Métro-Taxi, the subscription-based urban mobility network.
By choosing intelligent ridesharing, you contribute to environmental protection by reducing your carbon footprint.
Sign up and choose your plan. Locate vehicles heading in your direction.
Request a ride with a single click. The driver picks you up and drops you off wherever you want.
Thanks to our intelligent transfer system, switch vehicles along the way to reach your destination.
Métro-Taxi, your rides without limits, for a greener future.""",

    "de": """Métro-Taxi, das intelligente Fahrgemeinschafts-Transportsystem.
Willkommen bei Métro-Taxi, dem abonnementbasierten urbanen Mobilitätsnetzwerk.
Durch die Wahl intelligenter Fahrgemeinschaften tragen Sie zum Umweltschutz bei, indem Sie Ihren CO2-Fußabdruck reduzieren.
Registrieren Sie sich und wählen Sie Ihren Plan. Finden Sie Fahrzeuge, die in Ihre Richtung fahren.
Fordern Sie eine Fahrt mit einem Klick an. Der Fahrer holt Sie ab und setzt Sie ab, wo Sie möchten.
Dank unseres intelligenten Umstiegssystems können Sie unterwegs das Fahrzeug wechseln, um Ihr Ziel zu erreichen.
Métro-Taxi, Ihre Fahrten ohne Grenzen, für eine grünere Zukunft.""",

    "nl": """Métro-Taxi, het intelligente carpoolsysteem voor vervoer.
Welkom bij Métro-Taxi, het abonnementsgebaseerde stedelijke mobiliteitsnetwerk.
Door te kiezen voor intelligent carpoolen, draagt u bij aan milieubescherming door uw CO2-voetafdruk te verminderen.
Registreer en kies uw plan. Vind voertuigen die uw richting uitgaan.
Vraag een rit aan met één klik. De chauffeur pikt u op en zet u af waar u wilt.
Dankzij ons intelligente overstapsysteem kunt u onderweg van voertuig wisselen om uw bestemming te bereiken.
Métro-Taxi, uw ritten zonder grenzen, voor een groenere toekomst.""",

    "es": """Métro-Taxi, el sistema de transporte inteligente por coche compartido.
Bienvenido a Métro-Taxi, la red de movilidad urbana por suscripción.
Al elegir el coche compartido inteligente, contribuyes a la protección del medio ambiente reduciendo tu huella de carbono.
Regístrate y elige tu plan. Localiza vehículos que van en tu dirección.
Solicita un viaje con un solo clic. El conductor te recoge y te deja donde quieras.
Gracias a nuestro sistema inteligente de transbordo, cambia de vehículo en ruta para llegar a tu destino.
Métro-Taxi, tus viajes sin límites, para un futuro más verde.""",

    "pt": """Métro-Taxi, o sistema de transporte inteligente por boleias partilhadas.
Bem-vindo ao Métro-Taxi, a rede de mobilidade urbana por assinatura.
Ao escolher boleias partilhadas inteligentes, contribui para a proteção do ambiente reduzindo a sua pegada de carbono.
Registe-se e escolha o seu plano. Localize veículos que vão na sua direção.
Peça uma viagem com um clique. O motorista apanha-o e deixa-o onde quiser.
Graças ao nosso sistema inteligente de transbordo, mude de veículo no caminho para chegar ao seu destino.
Métro-Taxi, as suas viagens sem limites, para um futuro mais verde.""",

    "no": """Métro-Taxi, det intelligente samkjøringssystemet.
Velkommen til Métro-Taxi, det abonnementsbaserte bymobilitetsnettverket.
Ved å velge intelligent samkjøring bidrar du til miljøvern ved å redusere ditt karbonavtrykk.
Registrer deg og velg din plan. Finn kjøretøy som går i din retning.
Be om en tur med ett klikk. Sjåføren henter deg og setter deg av hvor du vil.
Takket være vårt intelligente overgangssystem kan du bytte kjøretøy underveis for å nå målet ditt.
Métro-Taxi, dine turer uten grenser, for en grønnere fremtid.""",

    "sv": """Métro-Taxi, det intelligenta samåkningssystemet.
Välkommen till Métro-Taxi, det prenumerationsbaserade stadsmobilitetsnätverket.
Genom att välja intelligent samåkning bidrar du till miljöskydd genom att minska ditt koldioxidavtryck.
Registrera dig och välj din plan. Hitta fordon som åker i din riktning.
Begär en resa med ett klick. Föraren hämtar dig och släpper av dig var du vill.
Tack vare vårt intelligenta övergångssystem kan du byta fordon på vägen för att nå ditt mål.
Métro-Taxi, dina resor utan gränser, för en grönare framtid.""",

    "da": """Métro-Taxi, det intelligente samkørselssystem.
Velkommen til Métro-Taxi, det abonnementsbaserede bymobilitetsnetværk.
Ved at vælge intelligent samkørsel bidrager du til miljøbeskyttelse ved at reducere dit CO2-aftryk.
Tilmeld dig og vælg din plan. Find køretøjer, der kører i din retning.
Anmod om en tur med ét klik. Chaufføren henter dig og sætter dig af, hvor du vil.
Takket være vores intelligente overgangssystem kan du skifte køretøj undervejs for at nå dit mål.
Métro-Taxi, dine ture uden grænser, for en grønnere fremtid.""",

    "zh": """Métro-Taxi，智能拼车出行系统。
欢迎来到Métro-Taxi，订阅式城市交通网络。
选择智能拼车，您将通过减少碳足迹为环境保护做出贡献。
注册并选择您的计划。找到前往您方向的车辆。
一键请求乘车。司机会接您并送您到想去的地方。
借助我们的智能换乘系统，您可以在途中换乘车辆以到达目的地。
Métro-Taxi，无限出行，共创绿色未来。""",

    "hi": """मेट्रो-टैक्सी, स्मार्ट राइड शेयरिंग ट्रांसपोर्ट सिस्टम।
मेट्रो-टैक्सी में आपका स्वागत है, सदस्यता-आधारित शहरी गतिशीलता नेटवर्क।
स्मार्ट राइड शेयरिंग चुनकर, आप अपने कार्बन फुटप्रिंट को कम करके पर्यावरण संरक्षण में योगदान करते हैं।
रजिस्टर करें और अपना प्लान चुनें। अपनी दिशा में जाने वाले वाहन खोजें।
एक क्लिक से यात्रा का अनुरोध करें। ड्राइवर आपको उठाएगा और जहां चाहें वहां छोड़ देगा।
हमारे स्मार्ट ट्रांसफर सिस्टम के कारण, अपने गंतव्य तक पहुंचने के लिए रास्ते में वाहन बदलें।
मेट्रो-टैक्सी, असीमित यात्रा, हरित भविष्य के लिए।""",

    "pa": """ਮੈਟਰੋ-ਟੈਕਸੀ, ਸਮਾਰਟ ਰਾਈਡ ਸ਼ੇਅਰਿੰਗ ਟ੍ਰਾਂਸਪੋਰਟ ਸਿਸਟਮ।
ਮੈਟਰੋ-ਟੈਕਸੀ ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ, ਸਬਸਕ੍ਰਿਪਸ਼ਨ-ਅਧਾਰਤ ਸ਼ਹਿਰੀ ਗਤੀਸ਼ੀਲਤਾ ਨੈੱਟਵਰਕ।
ਸਮਾਰਟ ਰਾਈਡ ਸ਼ੇਅਰਿੰਗ ਚੁਣ ਕੇ, ਤੁਸੀਂ ਆਪਣੇ ਕਾਰਬਨ ਫੁੱਟਪ੍ਰਿੰਟ ਨੂੰ ਘਟਾ ਕੇ ਵਾਤਾਵਰਣ ਦੀ ਸੁਰੱਖਿਆ ਵਿੱਚ ਯੋਗਦਾਨ ਪਾਉਂਦੇ ਹੋ।
ਰਜਿਸਟਰ ਕਰੋ ਅਤੇ ਆਪਣਾ ਪਲਾਨ ਚੁਣੋ। ਆਪਣੀ ਦਿਸ਼ਾ ਵੱਲ ਜਾਣ ਵਾਲੀਆਂ ਗੱਡੀਆਂ ਲੱਭੋ।
ਇੱਕ ਕਲਿੱਕ ਨਾਲ ਸਫ਼ਰ ਦੀ ਬੇਨਤੀ ਕਰੋ। ਡਰਾਈਵਰ ਤੁਹਾਨੂੰ ਲੈ ਜਾਵੇਗਾ ਅਤੇ ਜਿੱਥੇ ਚਾਹੋ ਉੱਥੇ ਛੱਡ ਦੇਵੇਗਾ।
ਸਾਡੇ ਸਮਾਰਟ ਟ੍ਰਾਂਸਫਰ ਸਿਸਟਮ ਕਰਕੇ, ਆਪਣੀ ਮੰਜ਼ਿਲ ਤੱਕ ਪਹੁੰਚਣ ਲਈ ਰਸਤੇ ਵਿੱਚ ਗੱਡੀ ਬਦਲੋ।
ਮੈਟਰੋ-ਟੈਕਸੀ, ਬੇਅੰਤ ਸਫ਼ਰ, ਹਰੇ ਭਰੇ ਭਵਿੱਖ ਲਈ।""",

    "ar": """مترو-تاكسي، نظام التنقل الذكي بالمشاركة.
مرحباً بكم في مترو-تاكسي، شبكة التنقل الحضري بالاشتراك.
باختيار المشاركة الذكية في التنقل، تساهم في حماية البيئة من خلال تقليل بصمتك الكربونية.
سجل واختر خطتك. حدد موقع المركبات المتجهة في اتجاهك.
اطلب رحلة بنقرة واحدة. سيأتي السائق لاصطحابك وإيصالك حيث تريد.
بفضل نظام التحويل الذكي، يمكنك تغيير المركبة أثناء الطريق للوصول إلى وجهتك.
مترو-تاكسي، رحلاتك بلا حدود، من أجل مستقبل أكثر اخضراراً.""",

    "ru": """Метро-Такси, интеллектуальная система совместных поездок.
Добро пожаловать в Метро-Такси, сеть городской мобильности по подписке.
Выбирая умные совместные поездки, вы вносите вклад в защиту окружающей среды, сокращая свой углеродный след.
Зарегистрируйтесь и выберите свой план. Найдите автомобили, едущие в вашем направлении.
Запросите поездку одним кликом. Водитель заберёт вас и довезёт куда захотите.
Благодаря нашей интеллектуальной системе пересадок, вы можете сменить автомобиль по пути к месту назначения.
Метро-Такси, ваши поездки без ограничений, ради более зелёного будущего.""",

    "it": """Métro-Taxi, il sistema di trasporto intelligente in carpooling.
Benvenuti su Métro-Taxi, la rete di mobilità urbana in abbonamento.
Scegliendo il carpooling intelligente, contribuisci alla protezione dell'ambiente riducendo la tua impronta di carbonio.
Registrati e scegli il tuo piano. Trova i veicoli che vanno nella tua direzione.
Richiedi un passaggio con un clic. L'autista ti viene a prendere e ti lascia dove vuoi.
Grazie al nostro sistema di trasbordo intelligente, puoi cambiare veicolo lungo il percorso per raggiungere la tua destinazione.
Métro-Taxi, i tuoi viaggi senza limiti, per un futuro più verde."""
}


class TTSRequest(BaseModel):
    language: str = Field(..., description="Language code")
    voice: str = Field(default="nova", description="Voice to use")


@router.post("/tts/voiceover")
async def generate_voiceover(request: TTSRequest):
    """Generate voiceover audio for the promotional video"""
    if request.language not in VIDEO_SCRIPTS:
        raise HTTPException(status_code=400, detail=f"Language '{request.language}' not supported")

    cache_dir = "/app/frontend/public/audio/voiceover"
    cache_file = f"{cache_dir}/voiceover_{request.language}.mp3"

    if os.path.exists(cache_file):
        logging.info(f"Serving cached voiceover for {request.language}")
        with open(cache_file, "rb") as f:
            audio_bytes = f.read()
        return Response(content=audio_bytes, media_type="audio/mpeg",
                        headers={"Content-Disposition": f"inline; filename=voiceover_{request.language}.mp3", "Cache-Control": "public, max-age=31536000"})

    script = VIDEO_SCRIPTS[request.language]
    try:
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="TTS API key not configured")

        logging.info(f"Generating voiceover for {request.language}")
        tts = OpenAITextToSpeech(api_key=api_key)
        audio_bytes = await tts.generate_speech(text=script, model="tts-1", voice=request.voice, speed=1.0, response_format="mp3")

        try:
            os.makedirs(cache_dir, exist_ok=True)
            with open(cache_file, "wb") as f:
                f.write(audio_bytes)
            logging.info(f"Cached voiceover for {request.language}")
        except Exception as cache_error:
            logging.warning(f"Could not cache voiceover: {cache_error}")

        return Response(content=audio_bytes, media_type="audio/mpeg",
                        headers={"Content-Disposition": f"inline; filename=voiceover_{request.language}.mp3", "Cache-Control": "public, max-age=31536000"})
    except Exception as e:
        logging.error(f"TTS generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating voiceover: {str(e)}")


@router.get("/tts/languages")
async def get_available_languages():
    """Get list of available languages for voiceover"""
    return {"languages": [
        {"code": "fr", "name": "Français", "flag": "🇫🇷"},
        {"code": "en", "name": "English (US)", "flag": "🇺🇸"},
        {"code": "en-GB", "name": "English (UK)", "flag": "🇬🇧"},
        {"code": "es", "name": "Español", "flag": "🇪🇸"},
        {"code": "pt", "name": "Português", "flag": "🇵🇹"},
        {"code": "de", "name": "Deutsch", "flag": "🇩🇪"},
        {"code": "nl", "name": "Nederlands", "flag": "🇳🇱"},
        {"code": "no", "name": "Norsk", "flag": "🇳🇴"},
        {"code": "sv", "name": "Svenska", "flag": "🇸🇪"},
        {"code": "da", "name": "Dansk", "flag": "🇩🇰"},
        {"code": "zh", "name": "中文", "flag": "🇨🇳"},
        {"code": "hi", "name": "हिन्दी", "flag": "🇮🇳"},
        {"code": "pa", "name": "ਪੰਜਾਬੀ", "flag": "🇮🇳"},
        {"code": "ar", "name": "العربية", "flag": "🇸🇦"},
        {"code": "ru", "name": "Русский", "flag": "🇷🇺"},
        {"code": "it", "name": "Italiano", "flag": "🇮🇹"}
    ]}


@router.post("/admin/tts/pregenerate-all")
async def pregenerate_all_voiceovers(current_user: dict = Depends(get_current_user)):
    """Pre-generate and cache all voiceover audio files (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    cache_dir = "/app/frontend/public/audio/voiceover"
    os.makedirs(cache_dir, exist_ok=True)

    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="TTS API key not configured")

    tts = OpenAITextToSpeech(api_key=api_key)
    results = {"generated": [], "failed": [], "skipped": []}

    for lang, script in VIDEO_SCRIPTS.items():
        cache_file = f"{cache_dir}/voiceover_{lang}.mp3"
        if os.path.exists(cache_file):
            results["skipped"].append(lang)
            continue
        try:
            logging.info(f"Pre-generating voiceover for {lang}...")
            audio_bytes = await tts.generate_speech(text=script, model="tts-1", voice="nova", speed=1.0, response_format="mp3")
            with open(cache_file, "wb") as f:
                f.write(audio_bytes)
            results["generated"].append(lang)
        except Exception as e:
            logging.error(f"Failed to generate voiceover for {lang}: {e}")
            results["failed"].append({"lang": lang, "error": str(e)})

    return {"status": "complete", "results": results, "total_cached": len(results["generated"]) + len(results["skipped"])}


@router.get("/admin/tts/cache-status")
async def get_voiceover_cache_status(current_user: dict = Depends(get_current_user)):
    """Check which voiceovers are cached (Admin only)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    cache_dir = "/app/frontend/public/audio/voiceover"
    status = {}
    for lang in VIDEO_SCRIPTS.keys():
        cache_file = f"{cache_dir}/voiceover_{lang}.mp3"
        if os.path.exists(cache_file):
            status[lang] = {"cached": True, "size_kb": round(os.path.getsize(cache_file) / 1024, 1)}
        else:
            status[lang] = {"cached": False}

    cached_count = sum(1 for s in status.values() if s["cached"])
    return {"cached": cached_count, "total": len(VIDEO_SCRIPTS), "languages": status}
