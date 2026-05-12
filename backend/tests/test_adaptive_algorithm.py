"""
Tests unitaires pour la détection de zone et la config algorithme adaptatif.
Run: cd /app/backend && pytest tests/test_adaptive_algorithm.py -v
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

# Make backend root importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.zone_detector import (
    detect_zone,
    detect_zone_by_postal_code,
    detect_zone_by_gps,
    is_night_time,
)
from utils.algorithm_config import DEFAULT_ZONE_SEGMENT_CONFIG


# ============================================
# CODE POSTAL
# ============================================
def test_postal_code_paris_intra():
    assert detect_zone_by_postal_code("75001") == "paris_intra"
    assert detect_zone_by_postal_code("75020") == "paris_intra"
    assert detect_zone_by_postal_code("75011") == "paris_intra"


def test_postal_code_banlieue_92_93_94():
    assert detect_zone_by_postal_code("92100") == "banlieue"  # Boulogne
    assert detect_zone_by_postal_code("93200") == "banlieue"  # Saint-Denis
    assert detect_zone_by_postal_code("94300") == "banlieue"  # Vincennes


def test_postal_code_grande_couronne():
    assert detect_zone_by_postal_code("77100") == "grande_couronne"  # Meaux
    assert detect_zone_by_postal_code("78000") == "grande_couronne"  # Versailles
    assert detect_zone_by_postal_code("91100") == "grande_couronne"  # Corbeil
    assert detect_zone_by_postal_code("95800") == "grande_couronne"  # Cergy


def test_postal_code_hors_zone():
    assert detect_zone_by_postal_code("69001") == "hors_zone"  # Lyon
    assert detect_zone_by_postal_code("13001") == "hors_zone"  # Marseille
    assert detect_zone_by_postal_code("33000") == "hors_zone"  # Bordeaux


def test_postal_code_invalid():
    assert detect_zone_by_postal_code(None) is None
    assert detect_zone_by_postal_code("") is None
    assert detect_zone_by_postal_code("ABCDE") is None
    assert detect_zone_by_postal_code("1234") is None  # too short


# ============================================
# GPS
# ============================================
def test_gps_paris_intra():
    # Notre-Dame
    assert detect_zone_by_gps(48.8530, 2.3499) == "paris_intra"
    # Tour Eiffel
    assert detect_zone_by_gps(48.8584, 2.2945) == "paris_intra"


def test_gps_banlieue():
    # Saint-Denis
    assert detect_zone_by_gps(48.9362, 2.3574) == "banlieue"
    # Vincennes (94)
    assert detect_zone_by_gps(48.8472, 2.4391) == "banlieue"


def test_gps_grande_couronne():
    # Versailles
    assert detect_zone_by_gps(48.8049, 2.1204) == "grande_couronne"
    # Cergy
    assert detect_zone_by_gps(49.0381, 2.0769) == "grande_couronne"


def test_gps_hors_zone():
    # Lyon
    assert detect_zone_by_gps(45.7640, 4.8357) == "hors_zone"
    # Marseille
    assert detect_zone_by_gps(43.2965, 5.3698) == "hors_zone"


# ============================================
# DETECT_ZONE HYBRIDE
# ============================================
def test_hybrid_postal_priority_over_gps():
    """Postal code takes priority over GPS coordinates."""
    # Lyon coordinates but Paris postal → should return paris_intra
    z = detect_zone(lat=45.7640, lng=4.8357, postal_code="75001")
    assert z == "paris_intra"


def test_hybrid_gps_fallback_when_no_postal():
    z = detect_zone(lat=48.8530, lng=2.3499, postal_code=None)
    assert z == "paris_intra"


def test_hybrid_no_info():
    assert detect_zone() == "hors_zone"
    assert detect_zone(lat=None, lng=None, postal_code=None) == "hors_zone"


# ============================================
# DETECTION NUIT
# ============================================
def test_night_at_23h_utc_summer():
    # 23h UTC en été = 01h Paris (DST +2) → nuit
    dt = datetime(2026, 7, 15, 23, 0, tzinfo=timezone.utc)
    assert is_night_time(dt) is True


def test_night_at_03h_utc_winter():
    # 03h UTC hiver = 04h Paris (CET +1) → nuit
    dt = datetime(2026, 1, 15, 3, 0, tzinfo=timezone.utc)
    assert is_night_time(dt) is True


def test_day_at_14h_utc_summer():
    # 14h UTC été = 16h Paris → jour
    dt = datetime(2026, 7, 15, 14, 0, tzinfo=timezone.utc)
    assert is_night_time(dt) is False


def test_day_at_10h_utc_winter():
    # 10h UTC hiver = 11h Paris → jour
    dt = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
    assert is_night_time(dt) is False


def test_night_at_21h_utc_summer():
    # 21h UTC été = 23h Paris → nuit
    dt = datetime(2026, 7, 15, 21, 0, tzinfo=timezone.utc)
    assert is_night_time(dt) is True


def test_dawn_at_04h_paris_is_night():
    # 02h UTC été = 04h Paris (avant 05h) → nuit
    dt = datetime(2026, 7, 15, 2, 0, tzinfo=timezone.utc)
    assert is_night_time(dt) is True


def test_morning_at_05h_paris_is_day():
    # 03h UTC été = 05h Paris (limite jour) → jour
    dt = datetime(2026, 7, 15, 3, 0, tzinfo=timezone.utc)
    assert is_night_time(dt) is False


# ============================================
# CONFIGURATION PAR DÉFAUT
# ============================================
def test_default_config_all_zones_present():
    expected_zones = {"paris_intra", "banlieue", "grande_couronne", "hors_zone", "night"}
    assert expected_zones.issubset(set(DEFAULT_ZONE_SEGMENT_CONFIG.keys()))


def test_paris_intra_segment_is_smallest():
    paris = DEFAULT_ZONE_SEGMENT_CONFIG["paris_intra"]
    banlieue = DEFAULT_ZONE_SEGMENT_CONFIG["banlieue"]
    gc = DEFAULT_ZONE_SEGMENT_CONFIG["grande_couronne"]
    assert paris["segment_max_km"] < banlieue["segment_max_km"] < gc["segment_max_km"]


def test_night_segment_is_largest():
    night = DEFAULT_ZONE_SEGMENT_CONFIG["night"]
    gc = DEFAULT_ZONE_SEGMENT_CONFIG["grande_couronne"]
    assert night["segment_max_km"] >= gc["segment_max_km"]


def test_config_values_match_spec():
    """Spec Métro-Taxi : Paris 3-4km, Banlieue 5-7km, GC 8-12km, Nuit 10-15km."""
    cfg = DEFAULT_ZONE_SEGMENT_CONFIG
    assert cfg["paris_intra"]["segment_min_km"] == 3.0
    assert cfg["paris_intra"]["segment_max_km"] == 4.0
    assert cfg["banlieue"]["segment_min_km"] == 5.0
    assert cfg["banlieue"]["segment_max_km"] == 7.0
    assert cfg["grande_couronne"]["segment_min_km"] == 8.0
    assert cfg["grande_couronne"]["segment_max_km"] == 12.0
    assert cfg["night"]["segment_min_km"] == 10.0
    assert cfg["night"]["segment_max_km"] == 15.0
