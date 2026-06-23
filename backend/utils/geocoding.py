"""
Reverse geocoding via Nominatim (OpenStreetMap).
Politique d'usage : 1 req/sec max, User-Agent obligatoire. Voir https://operations.osmfoundation.org/policies/nominatim/
Cache en mémoire 24h pour éviter de spammer.
"""
import httpx
import asyncio
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

_cache: dict = {}
_cache_ttl = timedelta(hours=24)
_last_call_ts: float = 0.0
_lock = asyncio.Lock()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "Metro-Taxi/1.0 (contact@metro-taxi.com)"


def _cache_key(lat: float, lng: float) -> str:
    # Précision ~10m : on arrondit à 4 décimales pour mutualiser le cache
    return f"{round(lat, 4)},{round(lng, 4)}"


async def reverse_geocode(lat: float, lng: float, lang: str = "fr") -> str | None:
    """Retourne une adresse lisible à partir d'une position GPS, ou None si échec.
    Bloque max 5s. Respecte la politique Nominatim (1 req/sec).
    """
    if lat is None or lng is None:
        return None
    key = _cache_key(lat, lng)
    cached = _cache.get(key)
    if cached and cached["expires_at"] > datetime.now(timezone.utc):
        return cached["address"]

    async with _lock:
        # Rate limit 1 req/sec
        global _last_call_ts
        now_ts = asyncio.get_event_loop().time()
        elapsed = now_ts - _last_call_ts
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)
        _last_call_ts = asyncio.get_event_loop().time()

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    NOMINATIM_URL,
                    params={
                        "lat": lat,
                        "lon": lng,
                        "format": "json",
                        "accept-language": lang,
                        "zoom": 18,  # niveau adresse précise
                        "addressdetails": 1,
                    },
                    headers={"User-Agent": USER_AGENT},
                )
                resp.raise_for_status()
                data = resp.json()
                # Compose une adresse courte et lisible (rue + ville)
                addr = data.get("address", {})
                house = addr.get("house_number", "")
                road = addr.get("road") or addr.get("pedestrian") or addr.get("residential") or ""
                postcode = addr.get("postcode", "")
                city = addr.get("city") or addr.get("town") or addr.get("village") or addr.get("suburb") or ""
                parts = []
                if road:
                    parts.append(f"{house} {road}".strip())
                if postcode or city:
                    parts.append(f"{postcode} {city}".strip())
                short = ", ".join([p for p in parts if p])
                full = short or data.get("display_name") or None
                if full:
                    _cache[key] = {
                        "address": full,
                        "expires_at": datetime.now(timezone.utc) + _cache_ttl,
                    }
                return full
        except Exception as e:
            logger.warning(f"[reverse_geocode] {lat},{lng} -> {type(e).__name__}: {e}")
            return None
