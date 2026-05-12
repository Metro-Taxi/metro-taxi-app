"""
Détection de zone géographique pour l'algorithme de transbordement adaptatif - Métro-Taxi

Stratégie hybride :
1. Code postal (priorité) - si fourni à l'inscription chauffeur/usager
2. GPS (fallback) - bounds approximatifs des zones Île-de-France

Zones définies :
- paris_intra : Paris intra-muros (75)
- banlieue : Petite couronne (92, 93, 94)
- grande_couronne : Grande couronne (77, 78, 91, 95)
- hors_zone : En dehors de l'Île-de-France
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


# ============================================
# CODES POSTAUX PAR ZONE
# ============================================
CP_PARIS_INTRA = {f"750{str(i).zfill(2)}" for i in range(1, 21)}  # 75001 → 75020
CP_PETITE_COURONNE_PREFIXES = ("92", "93", "94")
CP_GRANDE_COURONNE_PREFIXES = ("77", "78", "91", "95")


# ============================================
# BOUNDS GPS (rectangles englobants approximatifs)
# Ces bounds servent de FALLBACK quand le code postal n'est pas dispo.
# ============================================
ZONE_GPS_BOUNDS = {
    "paris_intra": {
        # Paris intra-muros (boulevard périphérique)
        "south": 48.8156, "north": 48.9022,
        "west": 2.2530, "east": 2.4150,
    },
    "banlieue": {
        # Petite couronne (92/93/94) - couronne autour de Paris
        "south": 48.7400, "north": 48.9700,
        "west": 2.1300, "east": 2.5800,
    },
    "grande_couronne": {
        # Île-de-France complète (77/78/91/95)
        "south": 48.1200, "north": 49.2400,
        "west": 1.4500, "east": 3.5500,
    },
}


# ============================================
# DÉTECTION DE ZONE
# ============================================

def detect_zone_by_postal_code(postal_code: Optional[str]) -> Optional[str]:
    """Detect zone from French postal code (5 digits). Returns None if not detectable."""
    if not postal_code:
        return None
    cp = str(postal_code).strip().replace(" ", "")
    if len(cp) != 5 or not cp.isdigit():
        return None

    if cp in CP_PARIS_INTRA:
        return "paris_intra"
    if cp.startswith(CP_PETITE_COURONNE_PREFIXES):
        return "banlieue"
    if cp.startswith(CP_GRANDE_COURONNE_PREFIXES):
        return "grande_couronne"
    return "hors_zone"


def detect_zone_by_gps(lat: float, lng: float) -> str:
    """Detect zone from GPS coordinates using bounds (fallback when no postal code)."""
    # Check from most specific (Paris intra) to least specific (grande couronne)
    for zone_name in ("paris_intra", "banlieue", "grande_couronne"):
        b = ZONE_GPS_BOUNDS[zone_name]
        if b["south"] <= lat <= b["north"] and b["west"] <= lng <= b["east"]:
            return zone_name
    return "hors_zone"


def detect_zone(
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    postal_code: Optional[str] = None,
) -> str:
    """
    Hybrid zone detection: postal code FIRST, GPS as FALLBACK.

    Returns one of: "paris_intra", "banlieue", "grande_couronne", "hors_zone"
    """
    # Priority 1: postal code
    zone_by_cp = detect_zone_by_postal_code(postal_code)
    if zone_by_cp is not None:
        return zone_by_cp

    # Priority 2: GPS fallback
    if lat is not None and lng is not None:
        return detect_zone_by_gps(lat, lng)

    # No info → assume hors_zone (conservative)
    return "hors_zone"


# ============================================
# DÉTECTION HEURE NUIT (Europe/Paris)
# ============================================

# Tranche nocturne : 22h00 → 04h59 (heure de Paris)
NIGHT_START_HOUR = 22
NIGHT_END_HOUR = 5  # exclusif (05:00 = jour)

# Décalage UTC → Paris (CET = +1, CEST = +2). Approximation : on prend +2 en été.
# En production réelle, utiliser zoneinfo pour plus de précision.
# Approximation simple : DST entre dernier dimanche de mars et dernier dimanche d'octobre.
def _paris_offset_hours(dt_utc: datetime) -> int:
    """Approximate Paris UTC offset (1h winter, 2h summer DST)."""
    # DST en Europe : dernier dimanche de mars → dernier dimanche d'octobre
    y = dt_utc.year
    # Dernier dimanche de mars
    march = datetime(y, 3, 31, tzinfo=timezone.utc)
    march_last_sunday = march - timedelta(days=(march.weekday() + 1) % 7)
    # Dernier dimanche d'octobre
    october = datetime(y, 10, 31, tzinfo=timezone.utc)
    october_last_sunday = october - timedelta(days=(october.weekday() + 1) % 7)
    if march_last_sunday <= dt_utc < october_last_sunday:
        return 2  # CEST
    return 1  # CET


def is_night_time(dt: Optional[datetime] = None) -> bool:
    """Return True if current time (Paris) is within night hours (22h-05h)."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    offset = _paris_offset_hours(dt)
    paris_hour = (dt.hour + offset) % 24
    return paris_hour >= NIGHT_START_HOUR or paris_hour < NIGHT_END_HOUR
