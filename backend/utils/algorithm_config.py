"""
Configuration adaptative de l'algorithme de transbordement - Métro-Taxi

Segments dynamiques selon la zone géographique + tranche horaire (jour/nuit).
Les valeurs par défaut peuvent être overridées par l'admin via MongoDB.

Règle Métro-Taxi (modèle covoiturage à maillage intelligent) :
- Paris intra-muros  : 3-4 km par segment (fort maillage, transbordements fréquents OK)
- Banlieue (92/93/94) : 5-7 km (densité moyenne)
- Grande couronne     : 8-12 km (densité faible)
- Nuit (22h-05h)      : 10-15 km partout (peu de chauffeurs, on évite les transbordements abusifs)
"""
from typing import Optional


# ============================================
# CONFIGURATION PAR DÉFAUT (hardcoded fallback)
# ============================================
DEFAULT_ZONE_SEGMENT_CONFIG = {
    "paris_intra": {
        "segment_min_km": 3.0,
        "segment_max_km": 4.0,
        "max_pickup_distance_km": 2.0,
        "max_transfers": 2,
        "direction_threshold": 60,
    },
    "banlieue": {
        "segment_min_km": 5.0,
        "segment_max_km": 7.0,
        "max_pickup_distance_km": 3.0,
        "max_transfers": 2,
        "direction_threshold": 55,
    },
    "grande_couronne": {
        "segment_min_km": 8.0,
        "segment_max_km": 12.0,
        "max_pickup_distance_km": 5.0,
        "max_transfers": 2,
        "direction_threshold": 50,
    },
    "hors_zone": {
        # Pas de zone pilote → comportement par défaut prudent (banlieue-like)
        "segment_min_km": 5.0,
        "segment_max_km": 7.0,
        "max_pickup_distance_km": 3.0,
        "max_transfers": 2,
        "direction_threshold": 55,
    },
    # Profil spécial "nuit" qui PRIME sur la zone (entre 22h et 05h Paris)
    "night": {
        "segment_min_km": 10.0,
        "segment_max_km": 15.0,
        "max_pickup_distance_km": 5.0,
        "max_transfers": 1,  # Moins de transbordements la nuit
        "direction_threshold": 50,
    },
}

# Fenêtre aéroport : on autorise un segment plus long pour le départ/arrivée aéroport
AIRPORT_WINDOW_MINUTES = 30
AIRPORT_SEGMENT_MAX_KM_BONUS = 5.0  # km supplémentaires autorisés près d'un aéroport

# Capacité véhicule max (abonnés à bord simultanément)
MAX_PASSENGERS_PER_VEHICLE = 4


# ============================================
# CACHE EN MÉMOIRE pour éviter de spammer Mongo
# ============================================
_config_cache: Optional[dict] = None
_cache_timestamp: float = 0
_CACHE_TTL_SECONDS = 30  # Recharge la conf admin toutes les 30s


async def get_zone_config(db, zone: str, is_night: bool = False) -> dict:
    """
    Get segment config for a given zone (+ night override if applicable).

    The config is loaded from MongoDB collection `algorithm_config` (single doc
    id="default") if present, else falls back to DEFAULT_ZONE_SEGMENT_CONFIG.
    """
    global _config_cache, _cache_timestamp
    import time

    now_ts = time.time()
    if _config_cache is None or (now_ts - _cache_timestamp) > _CACHE_TTL_SECONDS:
        # Reload from MongoDB
        admin_doc = await db.algorithm_config.find_one({"id": "default"}, {"_id": 0})
        if admin_doc and "zones" in admin_doc:
            # Merge admin overrides with defaults (admin wins per-key)
            merged = {k: dict(v) for k, v in DEFAULT_ZONE_SEGMENT_CONFIG.items()}
            for zone_name, overrides in admin_doc["zones"].items():
                if zone_name in merged and isinstance(overrides, dict):
                    merged[zone_name].update(overrides)
            _config_cache = merged
        else:
            _config_cache = {k: dict(v) for k, v in DEFAULT_ZONE_SEGMENT_CONFIG.items()}
        _cache_timestamp = now_ts

    # Night profile takes priority over zone profile
    if is_night and "night" in _config_cache:
        return dict(_config_cache["night"])
    return dict(_config_cache.get(zone, _config_cache["hors_zone"]))


def invalidate_config_cache():
    """Force reload of config on next call (used by admin PUT endpoint)."""
    global _config_cache, _cache_timestamp
    _config_cache = None
    _cache_timestamp = 0
