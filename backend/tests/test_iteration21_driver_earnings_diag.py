"""
Backend integration tests for iteration 21 — Driver earnings diagnose + recompute.

Endpoints covered:
  GET  /api/admin/diagnose/driver-earnings?email=
  POST /api/admin/recompute/driver-earnings  body {driver_id, dry_run}

Bugs covered:
  #1 auth gating (admin only / 401 no token / 400 empty email)
  #2 unknown email -> profiles_count=0, is_duplicate=False
  #3 duplicate profiles (case-insensitive)
  #4 sum_revenue_from_completed_rides vs sum_revenue_stored discrepancy
  #5 recompute dry_run=true does not persist
  #6 recompute dry_run=false persists driver_earnings
  #7 diagnose after recompute -> discrepancy=0
  #8 recompute does NOT touch 'paid' months
  #9 orphan rides surfaced in last 30 days
  #10 validation: missing driver_id -> 400, unknown driver_id -> 404

JWT admin bypass pattern same as iter20.
"""
import os
import sys
import uuid
import pathlib
from datetime import datetime, timezone, timedelta

import jwt
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

# Public base URL
FRONTEND_ENV = pathlib.Path("/app/frontend/.env").read_text()
BASE_URL = None
for line in FRONTEND_ENV.splitlines():
    if line.startswith("REACT_APP_BACKEND_URL="):
        BASE_URL = line.split("=", 1)[1].strip().strip('"').rstrip("/")
        break
assert BASE_URL, "REACT_APP_BACKEND_URL missing"

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGO = "HS256"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "contact@metro-taxi.com")

PREFIX = "test-iter21-"
ORPHAN_DRIVER_ID = "fake-orphan-id-iter21"


def _mongo():
    client = MongoClient(os.environ["MONGO_URL"])
    return client, client[os.environ["DB_NAME"]]


def _get_admin_id() -> str:
    client, db = _mongo()
    doc = db.admins.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "id": 1})
    client.close()
    assert doc, "Admin user not found in DB"
    return doc["id"]


def _make_token(user_id: str, role: str) -> str:
    return jwt.encode(
        {
            "user_id": user_id,
            "role": role,
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        },
        JWT_SECRET, algorithm=JWT_ALGO,
    )


def _insert_driver(db, email: str, suffix: str) -> str:
    drv_id = f"{PREFIX}drv-{suffix}"
    db.drivers.insert_one({
        "id": drv_id,
        "first_name": "Test21",
        "last_name": f"Drv{suffix}",
        "email": email,
        "phone": f"+33600000{suffix[:3] if len(suffix) >= 3 else '000'}",
        "role": "driver",
        "is_active": True,
        "is_validated": True,
        "email_verified": True,
        "vehicle_plate": "AA-000-AA",
        "vehicle_type": "berline",
        "seats": 4,
        "vtc_license": "VTC-TEST",
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return drv_id


def _insert_ride(db, driver_id: str, revenue: float, days_ago: int = 1,
                 status: str = "completed", suffix: str = None) -> str:
    rid = f"{PREFIX}ride-{suffix or uuid.uuid4().hex[:8]}"
    when = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    db.ride_requests.insert_one({
        "id": rid,
        "driver_id": driver_id,
        "user_id": f"{PREFIX}user",
        "user_name": "Test User",
        "pickup_address": "1 rue test",
        "status": status,
        "driver_revenue": revenue,
        "km_with_user": 5.0,
        "created_at": when,
        "completed_at": when if status == "completed" else None,
    })
    return rid


@pytest.fixture(scope="module")
def admin_headers():
    return {
        "Authorization": f"Bearer {_make_token(_get_admin_id(), 'admin')}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module")
def user_headers():
    # mint a token with role=user (won't pass admin gate)
    return {
        "Authorization": f"Bearer {_make_token('not-an-admin-iter21', 'user')}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module", autouse=True)
def _cleanup():
    yield
    client, db = _mongo()
    db.drivers.delete_many({"id": {"$regex": f"^{PREFIX}"}})
    db.drivers.delete_many({"email": {"$regex": f"^{PREFIX}", "$options": "i"}})
    db.ride_requests.delete_many({"id": {"$regex": f"^{PREFIX}"}})
    db.ride_requests.delete_many({"driver_id": {"$regex": f"^{PREFIX}"}})
    db.ride_requests.delete_many({"driver_id": ORPHAN_DRIVER_ID})
    db.driver_earnings.delete_many({"driver_id": {"$regex": f"^{PREFIX}"}})
    client.close()


# ---- BUG #1 auth gating ---------------------------------------------------
class TestAuthGating:
    def test_no_token_unauthorized(self):
        r = requests.get(f"{BASE_URL}/api/admin/diagnose/driver-earnings?email=x@y.com", timeout=15)
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"

    def test_user_token_forbidden(self, user_headers):
        r = requests.get(
            f"{BASE_URL}/api/admin/diagnose/driver-earnings",
            params={"email": "x@y.com"}, headers=user_headers, timeout=15,
        )
        assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text}"

    def test_empty_email_returns_400(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/admin/diagnose/driver-earnings",
            params={"email": ""}, headers=admin_headers, timeout=15,
        )
        assert r.status_code == 400, f"expected 400 got {r.status_code} {r.text}"

    def test_recompute_no_token(self):
        r = requests.post(f"{BASE_URL}/api/admin/recompute/driver-earnings",
                          json={"driver_id": "x"}, timeout=15)
        assert r.status_code in (401, 403)

    def test_recompute_user_token_forbidden(self, user_headers):
        r = requests.post(f"{BASE_URL}/api/admin/recompute/driver-earnings",
                          json={"driver_id": "x"}, headers=user_headers, timeout=15)
        assert r.status_code == 403


# ---- BUG #2 unknown email -------------------------------------------------
class TestUnknownEmail:
    def test_unknown_email(self, admin_headers):
        r = requests.get(
            f"{BASE_URL}/api/admin/diagnose/driver-earnings",
            params={"email": f"{PREFIX}does-not-exist@example.com"},
            headers=admin_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["profiles_count"] == 0
        assert body["is_duplicate"] is False
        assert body["profiles"] == []
        assert body["orphan_rides"] == []


# ---- BUG #3 duplicate profiles (case-insensitive) -------------------------
class TestDuplicateProfiles:
    def test_duplicate_case_insensitive(self, admin_headers):
        email_lower = f"{PREFIX}dup@example.com"
        email_upper = f"{PREFIX.upper()}DUP@example.com"  # different case
        client, db = _mongo()
        db.drivers.delete_many({"email": {"$regex": f"^{PREFIX}dup@", "$options": "i"}})
        _insert_driver(db, email_lower, "dup1")
        _insert_driver(db, email_upper, "dup2")
        client.close()

        r = requests.get(
            f"{BASE_URL}/api/admin/diagnose/driver-earnings",
            params={"email": email_lower}, headers=admin_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["profiles_count"] == 2, f"expected 2 got {body['profiles_count']}"
        assert body["is_duplicate"] is True
        assert len(body["profiles"]) == 2


# ---- BUG #4 / #5 / #6 / #7 ------------------------------------------------
@pytest.fixture(scope="module")
def maaz_driver():
    """Single driver with 3 completed rides totalling 7.94€."""
    client, db = _mongo()
    email = f"{PREFIX}maaz@example.com"
    db.drivers.delete_many({"email": email})
    db.ride_requests.delete_many({"driver_id": {"$regex": f"^{PREFIX}drv-maaz"}})
    db.driver_earnings.delete_many({"driver_id": {"$regex": f"^{PREFIX}drv-maaz"}})
    drv_id = _insert_driver(db, email, "maaz")
    _insert_ride(db, drv_id, 2.5, days_ago=2, suffix="maaz1")
    _insert_ride(db, drv_id, 3.0, days_ago=2, suffix="maaz2")
    _insert_ride(db, drv_id, 2.44, days_ago=2, suffix="maaz3")
    client.close()
    return {"id": drv_id, "email": email}


class TestRevenueDiscrepancy:
    def test_diagnose_shows_discrepancy(self, admin_headers, maaz_driver):
        r = requests.get(
            f"{BASE_URL}/api/admin/diagnose/driver-earnings",
            params={"email": maaz_driver["email"]}, headers=admin_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["profiles_count"] == 1
        prof = body["profiles"][0]
        assert prof["id"] == maaz_driver["id"]
        assert prof["rides_by_status"].get("completed") == 3
        assert abs(prof["sum_revenue_from_completed_rides_eur"] - 7.94) < 0.01
        assert prof["sum_revenue_stored_in_driver_earnings_eur"] == 0.0
        assert abs(prof["discrepancy_eur"] - 7.94) < 0.01

    def test_recompute_dry_run(self, admin_headers, maaz_driver):
        # Ensure no driver_earnings yet
        client, db = _mongo()
        db.driver_earnings.delete_many({"driver_id": maaz_driver["id"]})
        client.close()

        r = requests.post(
            f"{BASE_URL}/api/admin/recompute/driver-earnings",
            json={"driver_id": maaz_driver["id"], "dry_run": True},
            headers=admin_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["dry_run"] is True
        assert body["total_completed_rides"] == 3
        assert len(body["actions"]) >= 1
        a = body["actions"][0]
        assert a["action"] == "would_recompute"
        assert abs(a["computed_revenue_after"] - 7.94) < 0.01

        # DB MUST be untouched
        client, db = _mongo()
        count = db.driver_earnings.count_documents({"driver_id": maaz_driver["id"]})
        client.close()
        assert count == 0, "dry_run should not persist"

    def test_recompute_persists(self, admin_headers, maaz_driver):
        r = requests.post(
            f"{BASE_URL}/api/admin/recompute/driver-earnings",
            json={"driver_id": maaz_driver["id"], "dry_run": False},
            headers=admin_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["dry_run"] is False
        actions = body["actions"]
        assert len(actions) >= 1
        assert all(a["action"] in ("recomputed", "skipped_already_paid") for a in actions)

        # Verify persisted
        client, db = _mongo()
        docs = list(db.driver_earnings.find({"driver_id": maaz_driver["id"]}, {"_id": 0}))
        client.close()
        assert len(docs) >= 1
        total_stored = sum(d.get("total_revenue", 0) for d in docs)
        total_rides = sum(d.get("rides_count", 0) for d in docs)
        assert abs(total_stored - 7.94) < 0.01
        assert total_rides == 3
        for d in docs:
            assert d["payout_status"] == "pending"
            assert d["source"] == "recomputed_by_admin"

    def test_diagnose_after_recompute(self, admin_headers, maaz_driver):
        r = requests.get(
            f"{BASE_URL}/api/admin/diagnose/driver-earnings",
            params={"email": maaz_driver["email"]}, headers=admin_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        prof = r.json()["profiles"][0]
        assert abs(prof["sum_revenue_stored_in_driver_earnings_eur"] - 7.94) < 0.01
        assert abs(prof["discrepancy_eur"]) < 0.01


# ---- BUG #8 paid months untouched -----------------------------------------
class TestPaidMonthsUntouched:
    def test_paid_month_skipped(self, admin_headers):
        client, db = _mongo()
        email = f"{PREFIX}paid@example.com"
        db.drivers.delete_many({"email": email})
        db.ride_requests.delete_many({"driver_id": {"$regex": f"^{PREFIX}drv-paid"}})
        db.driver_earnings.delete_many({"driver_id": {"$regex": f"^{PREFIX}drv-paid"}})
        drv_id = _insert_driver(db, email, "paid")
        _insert_ride(db, drv_id, 10.0, days_ago=2, suffix="paid1")
        # Determine month_key from ride
        ride = db.ride_requests.find_one({"id": f"{PREFIX}ride-paid1"})
        month_key = (ride.get("completed_at") or ride.get("created_at"))[:7]
        # Force a 'paid' earnings doc with a sentinel value 999.99
        db.driver_earnings.insert_one({
            "driver_id": drv_id,
            "month": month_key,
            "total_revenue": 999.99,
            "rides_count": 1,
            "payout_status": "paid",
            "source": "test-iter21-seed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        client.close()

        r = requests.post(
            f"{BASE_URL}/api/admin/recompute/driver-earnings",
            json={"driver_id": drv_id, "dry_run": False},
            headers=admin_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        actions = r.json()["actions"]
        skipped = [a for a in actions if a.get("month") == month_key]
        assert skipped, f"month {month_key} not in actions"
        assert skipped[0]["action"] == "skipped_already_paid"

        # Confirm DB still 999.99 and 'paid'
        client, db = _mongo()
        doc = db.driver_earnings.find_one({"driver_id": drv_id, "month": month_key}, {"_id": 0})
        client.close()
        assert doc["payout_status"] == "paid"
        assert abs(doc["total_revenue"] - 999.99) < 0.01


# ---- BUG #9 orphan rides --------------------------------------------------
class TestOrphanRides:
    def test_orphan_ride_listed(self, admin_headers):
        client, db = _mongo()
        # ensure an unrelated profile exists (so 'profiles' is non-empty,
        # which triggers the orphan_rides block)
        email = f"{PREFIX}orphan-owner@example.com"
        db.drivers.delete_many({"email": email})
        _insert_driver(db, email, "orphan-owner")
        # Insert an orphan ride whose driver_id is NOT in any profile
        db.ride_requests.delete_many({"driver_id": ORPHAN_DRIVER_ID})
        rid = f"{PREFIX}ride-orphan-{uuid.uuid4().hex[:6]}"
        db.ride_requests.insert_one({
            "id": rid,
            "driver_id": ORPHAN_DRIVER_ID,
            "user_id": f"{PREFIX}user",
            "user_name": "Orphan User",
            "pickup_address": "Orphan address",
            "status": "completed",
            "driver_revenue": 5.0,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
            "completed_at": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
        })
        client.close()

        r = requests.get(
            f"{BASE_URL}/api/admin/diagnose/driver-earnings",
            params={"email": email}, headers=admin_headers, timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        orphan_ids = [o.get("driver_id") for o in body["orphan_rides"]]
        assert ORPHAN_DRIVER_ID in orphan_ids, f"orphan ride driver_id not surfaced. Got: {orphan_ids[:5]}"


# ---- BUG #10 validation ---------------------------------------------------
class TestRecomputeValidation:
    def test_missing_driver_id_400(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/admin/recompute/driver-earnings",
            json={"dry_run": True}, headers=admin_headers, timeout=15,
        )
        assert r.status_code == 400, f"expected 400 got {r.status_code} {r.text}"

    def test_empty_driver_id_400(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/admin/recompute/driver-earnings",
            json={"driver_id": "  ", "dry_run": True}, headers=admin_headers, timeout=15,
        )
        assert r.status_code == 400

    def test_unknown_driver_id_404(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/admin/recompute/driver-earnings",
            json={"driver_id": f"{PREFIX}does-not-exist", "dry_run": True},
            headers=admin_headers, timeout=15,
        )
        assert r.status_code == 404, f"expected 404 got {r.status_code} {r.text}"
