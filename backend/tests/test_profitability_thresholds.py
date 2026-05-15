"""
Tests unitaires pour le seuil de rentabilité de l'algorithme Métro-Taxi.

Règle métier (validée par le Capitaine) :
- Berline   : min 3 abonnés (idéal 4) — capacité 4
- Monospace : min 4 abonnés (idéal 5) — capacité 5
- Van       : min 5 abonnés (idéal 7) — capacité 7

Un dispatch n'est autorisé que si :
- le remplissage projeté ≥ min_fill, OU
- l'abonné attend depuis plus que queue_timeout_minutes (anti-frustration).

Run: cd /app/backend && pytest tests/test_profitability_thresholds.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.algorithm_config import (
    DEFAULT_VEHICLE_FILL_THRESHOLDS,
    DEFAULT_QUEUE_TIMEOUT_MINUTES,
    assess_dispatch_profitability,
    normalize_vehicle_type,
)


# ============================================
# DEFAULTS - VALIDATION DES VALEURS MÉTIER
# ============================================
def test_defaults_berline_min_fill_is_3():
    assert DEFAULT_VEHICLE_FILL_THRESHOLDS["berline"]["min_fill"] == 3
    assert DEFAULT_VEHICLE_FILL_THRESHOLDS["berline"]["target_fill"] == 4
    assert DEFAULT_VEHICLE_FILL_THRESHOLDS["berline"]["capacity"] == 4


def test_defaults_monospace_min_fill_is_4():
    assert DEFAULT_VEHICLE_FILL_THRESHOLDS["monospace"]["min_fill"] == 4
    assert DEFAULT_VEHICLE_FILL_THRESHOLDS["monospace"]["target_fill"] == 5
    assert DEFAULT_VEHICLE_FILL_THRESHOLDS["monospace"]["capacity"] == 5


def test_defaults_van_min_fill_is_5():
    assert DEFAULT_VEHICLE_FILL_THRESHOLDS["van"]["min_fill"] == 5
    assert DEFAULT_VEHICLE_FILL_THRESHOLDS["van"]["target_fill"] == 7
    assert DEFAULT_VEHICLE_FILL_THRESHOLDS["van"]["capacity"] == 7


# ============================================
# NORMALIZATION DES TYPES DE VÉHICULE
# ============================================
def test_normalize_vehicle_type_aliases():
    assert normalize_vehicle_type("berline") == "berline"
    assert normalize_vehicle_type("sedan") == "berline"
    assert normalize_vehicle_type("monospace") == "monospace"
    assert normalize_vehicle_type("minivan") == "monospace"
    assert normalize_vehicle_type("van") == "van"
    assert normalize_vehicle_type("minibus") == "van"


def test_normalize_vehicle_type_fallback():
    # Type inconnu → berline par défaut (le plus prudent)
    assert normalize_vehicle_type("unknown") == "berline"
    assert normalize_vehicle_type(None) == "berline"
    assert normalize_vehicle_type("") == "berline"


def test_normalize_vehicle_type_case_insensitive():
    assert normalize_vehicle_type("BERLINE") == "berline"
    assert normalize_vehicle_type("Van") == "van"
    assert normalize_vehicle_type(" Monospace ") == "monospace"


# ============================================
# VAN — CAS LE PLUS STRICT (seuil 5)
# ============================================
def test_van_solo_passenger_refused():
    """Cas réel évoqué par le Capitaine : 1 seul abonné dans un van → REFUSÉ."""
    result = assess_dispatch_profitability(
        vehicle_type="van",
        current_passengers=0,
        pending_compatible_passengers=1,
        waiting_minutes=0,
    )
    assert result["can_dispatch"] is False
    assert result["reason"] == "wait_for_fill"
    assert result["projected_fill"] == 1
    assert result["min_fill"] == 5
    assert result["missing_passengers"] == 4


def test_van_with_4_passengers_still_refused():
    """Van avec 4 abonnés → toujours refusé (seuil 5)."""
    result = assess_dispatch_profitability(
        vehicle_type="van",
        current_passengers=4,
        pending_compatible_passengers=0,
    )
    assert result["can_dispatch"] is False
    assert result["reason"] == "wait_for_fill"


def test_van_with_5_passengers_dispatched():
    """Van plein à 5 → DISPATCH OK."""
    result = assess_dispatch_profitability(
        vehicle_type="van",
        current_passengers=3,
        pending_compatible_passengers=2,
    )
    assert result["can_dispatch"] is True
    assert result["reason"] == "threshold_met"
    assert result["projected_fill"] == 5


def test_van_full_capacity_dispatched():
    """Van à pleine capacité (7) → dispatch et fill_ratio = 1.0."""
    result = assess_dispatch_profitability(
        vehicle_type="van",
        current_passengers=7,
        pending_compatible_passengers=0,
    )
    assert result["can_dispatch"] is True
    assert result["projected_fill"] == 7
    assert result["fill_ratio"] == 1.0


# ============================================
# BERLINE — seuil 3
# ============================================
def test_berline_solo_passenger_refused():
    result = assess_dispatch_profitability(
        vehicle_type="berline",
        current_passengers=1,
        pending_compatible_passengers=0,
    )
    assert result["can_dispatch"] is False
    assert result["reason"] == "wait_for_fill"


def test_berline_2_passengers_refused():
    result = assess_dispatch_profitability(
        vehicle_type="berline",
        current_passengers=2,
        pending_compatible_passengers=0,
    )
    assert result["can_dispatch"] is False


def test_berline_3_passengers_dispatched():
    """Seuil minimum atteint pour berline."""
    result = assess_dispatch_profitability(
        vehicle_type="berline",
        current_passengers=2,
        pending_compatible_passengers=1,
    )
    assert result["can_dispatch"] is True
    assert result["reason"] == "threshold_met"


def test_berline_full_dispatched():
    """Berline à capacité max (4)."""
    result = assess_dispatch_profitability(
        vehicle_type="berline",
        current_passengers=4,
        pending_compatible_passengers=0,
    )
    assert result["can_dispatch"] is True
    assert result["projected_fill"] == 4


# ============================================
# MONOSPACE — seuil 4
# ============================================
def test_monospace_3_passengers_refused():
    result = assess_dispatch_profitability(
        vehicle_type="monospace",
        current_passengers=3,
        pending_compatible_passengers=0,
    )
    assert result["can_dispatch"] is False


def test_monospace_4_passengers_dispatched():
    result = assess_dispatch_profitability(
        vehicle_type="monospace",
        current_passengers=4,
        pending_compatible_passengers=0,
    )
    assert result["can_dispatch"] is True


# ============================================
# CAPACITY CAP — projected_fill ne dépasse JAMAIS la capacité
# ============================================
def test_projected_fill_capped_at_capacity():
    """Si pending + current > capacity, on plafonne à capacity."""
    result = assess_dispatch_profitability(
        vehicle_type="berline",
        current_passengers=3,
        pending_compatible_passengers=10,  # absurde, mais on doit cap à 4
    )
    assert result["projected_fill"] == 4  # capacity berline
    assert result["can_dispatch"] is True


def test_projected_fill_capped_van():
    result = assess_dispatch_profitability(
        vehicle_type="van",
        current_passengers=5,
        pending_compatible_passengers=20,
    )
    assert result["projected_fill"] == 7
    assert result["can_dispatch"] is True


# ============================================
# TIMEOUT — anti-frustration abonné
# ============================================
def test_force_dispatch_after_timeout():
    """Abonné solo qui attend depuis trop longtemps → on dispatch même si seuil non atteint."""
    result = assess_dispatch_profitability(
        vehicle_type="van",
        current_passengers=1,  # 1 abonné déjà à bord
        pending_compatible_passengers=0,
        waiting_minutes=DEFAULT_QUEUE_TIMEOUT_MINUTES + 1,
    )
    assert result["can_dispatch"] is True
    assert result["reason"] == "force_after_timeout"


def test_no_force_dispatch_if_zero_passengers_even_after_timeout():
    """Si aucun abonné, même après timeout, on ne dispatch pas (rien à transporter)."""
    result = assess_dispatch_profitability(
        vehicle_type="van",
        current_passengers=0,
        pending_compatible_passengers=0,
        waiting_minutes=DEFAULT_QUEUE_TIMEOUT_MINUTES + 5,
    )
    assert result["can_dispatch"] is False


def test_no_force_before_timeout():
    """Juste avant le timeout, on attend encore."""
    result = assess_dispatch_profitability(
        vehicle_type="van",
        current_passengers=2,
        pending_compatible_passengers=0,
        waiting_minutes=DEFAULT_QUEUE_TIMEOUT_MINUTES - 1,
    )
    assert result["can_dispatch"] is False


# ============================================
# CUSTOM THRESHOLDS — overrides admin
# ============================================
def test_custom_thresholds_override():
    """L'admin peut surcharger les seuils via thresholds= argument."""
    custom = {
        "berline": {"min_fill": 1, "target_fill": 2, "capacity": 4},
        "monospace": {"min_fill": 4, "target_fill": 5, "capacity": 5},
        "van": {"min_fill": 5, "target_fill": 7, "capacity": 7},
    }
    # Avec seuil custom à 1 pour la berline, 1 abonné suffit
    result = assess_dispatch_profitability(
        vehicle_type="berline",
        current_passengers=1,
        pending_compatible_passengers=0,
        thresholds=custom,
    )
    assert result["can_dispatch"] is True
    assert result["min_fill"] == 1


# ============================================
# FILL RATIO — métrique de performance
# ============================================
def test_fill_ratio_van_optimal():
    """Van à 7 abonnés (cible 7) → ratio 1.0."""
    result = assess_dispatch_profitability(
        vehicle_type="van",
        current_passengers=7,
        pending_compatible_passengers=0,
    )
    assert result["fill_ratio"] == 1.0


def test_fill_ratio_berline_partial():
    """Berline à 3 abonnés (cible 4) → ratio 0.75."""
    result = assess_dispatch_profitability(
        vehicle_type="berline",
        current_passengers=3,
        pending_compatible_passengers=0,
    )
    assert result["fill_ratio"] == 0.75
