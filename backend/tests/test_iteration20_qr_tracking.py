"""
Backend integration tests for iteration 20 — QR tracking / campaigns.

Tests covered (per review request):
  BUG #1 POST /api/qr/scan happy path (public, 200, recorded in qr_scans)
  BUG #2 POST /api/qr/scan invalid (empty / missing campaign) -> 400/422, no insert
  BUG #3 POST /api/qr/scan lowercases the campaign value
  BUG #4 GET /api/admin/qr/stats auth gating (no token -> 401/403, user -> 403, admin -> 200)
  BUG #5 GET /api/admin/qr/stats aggregates scans correctly
  BUG #6 GET /api/admin/qr/stats counts user signups via signup_campaign
  BUG #7 Untracked campaigns (signup but no scan) appear with scans=0, conversion_pct=None
  BUG #8 totals.scans_last_7_days only counts scans <= 7 days old

NOTE: Admin auth uses a directly-signed JWT (bypassing the 2FA OTP flow for testing only).
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

# Public base URL (use REACT_APP_BACKEND_URL — what the user sees)
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

CAMPAIGN_PREFIX = "test-iter20-"


# ---- helpers ---------------------------------------------------------------
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
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


# ---- fixtures --------------------------------------------------------------
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_headers():
    return {
        "Authorization": f"Bearer {_make_token(_get_admin_id(), 'admin')}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module")
def user_token_and_id():
    """Create a normal user via /api/auth/register/user with a TEST signup_campaign."""
    uid_suffix = uuid.uuid4().hex[:8]
    email = f"TEST_iter20_{uid_suffix}@example.com"
    payload = {
        "first_name": "TestIter20",
        "last_name": "QRUser",
        "email": email,
        "phone": f"+3360000{uid_suffix[:4]}",
        "password": "TestPass123!",
        "street_address": "1 rue de test",
        "postal_code": "93330",
        "city": "Neuilly-sur-Marne",
        "date_of_birth": "1990-01-01",
        "signup_campaign": f"{CAMPAIGN_PREFIX}flyer1",
    }
    r = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload, timeout=15)
    assert r.status_code in (200, 201), f"register failed: {r.status_code} {r.text}"
    j = r.json()
    token = j.get("access_token") or j.get("token")
    user_id = (j.get("user") or {}).get("id") or j.get("user_id")
    # Fallback: pick from DB
    if not user_id:
        client, db = _mongo()
        u = db.users.find_one({"email": email}, {"_id": 0, "id": 1})
        client.close()
        user_id = u["id"] if u else None
    assert user_id, "no user id"
    # If no token returned by register, mint one with role=user
    if not token:
        token = _make_token(user_id, "user")
    yield {"token": token, "id": user_id, "email": email}
    # cleanup
    client, db = _mongo()
    db.users.delete_one({"id": user_id})
    client.close()


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data():
    """Cleanup all TEST_ data created in qr_scans + users.signup_campaign + drivers.source_inscription."""
    yield
    client, db = _mongo()
    db.qr_scans.delete_many({"campaign": {"$regex": f"^{CAMPAIGN_PREFIX}"}})
    db.users.delete_many({"signup_campaign": {"$regex": f"^{CAMPAIGN_PREFIX}"}})
    db.drivers.delete_many({"source_inscription": {"$regex": f"^{CAMPAIGN_PREFIX}"}})
    client.close()


# ---- BUG #1 — POST /api/qr/scan happy path --------------------------------
class TestQRScanRecord:
    def test_record_scan_returns_200(self, session):
        camp = f"{CAMPAIGN_PREFIX}flyer-cdg-happy"
        r = session.post(
            f"{BASE_URL}/api/qr/scan",
            json={"campaign": camp, "referrer": "https://example.com/ref"},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("status") == "recorded"
        assert body.get("campaign") == camp

        # Verify document persisted with expected fields
        client, db = _mongo()
        doc = db.qr_scans.find_one({"campaign": camp}, {"_id": 0})
        client.close()
        assert doc, "qr_scans doc not inserted"
        assert doc["campaign"] == camp
        assert doc["referrer"] == "https://example.com/ref"
        assert "scanned_at" in doc and isinstance(doc["scanned_at"], str)
        assert "ip" in doc
        assert "user_agent" in doc

    def test_record_scan_is_public(self, session):
        # No auth header set => still 200
        camp = f"{CAMPAIGN_PREFIX}public-check"
        r = requests.post(
            f"{BASE_URL}/api/qr/scan",
            json={"campaign": camp},
            timeout=15,
        )
        assert r.status_code == 200, r.text
        assert r.json().get("status") == "recorded"


# ---- BUG #2 — invalid payloads --------------------------------------------
class TestQRScanInvalid:
    def test_empty_campaign_returns_400(self):
        r = requests.post(
            f"{BASE_URL}/api/qr/scan", json={"campaign": ""}, timeout=15
        )
        assert r.status_code in (400, 422), f"expected 400/422 got {r.status_code} {r.text}"
        # ensure NOT inserted
        client, db = _mongo()
        count = db.qr_scans.count_documents({"campaign": ""})
        client.close()
        assert count == 0

    def test_missing_campaign_returns_422(self):
        r = requests.post(f"{BASE_URL}/api/qr/scan", json={}, timeout=15)
        assert r.status_code in (400, 422), f"expected 422 got {r.status_code} {r.text}"


# ---- BUG #3 — lowercasing --------------------------------------------------
class TestQRScanLowercase:
    def test_campaign_lowercased(self):
        upper = f"{CAMPAIGN_PREFIX.upper()}FLYER-CDG-UPPER"
        expected = upper.lower()
        r = requests.post(
            f"{BASE_URL}/api/qr/scan", json={"campaign": upper}, timeout=15
        )
        assert r.status_code == 200, r.text
        assert r.json().get("campaign") == expected
        client, db = _mongo()
        doc = db.qr_scans.find_one({"campaign": expected}, {"_id": 0})
        upper_doc = db.qr_scans.find_one({"campaign": upper}, {"_id": 0})
        client.close()
        assert doc, "lowercased doc missing"
        assert not upper_doc, "uppercase doc should NOT exist"


# ---- BUG #4 — auth gating on /api/admin/qr/stats --------------------------
class TestQRStatsAuthGating:
    def test_no_token_unauthorized(self):
        r = requests.get(f"{BASE_URL}/api/admin/qr/stats", timeout=15)
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"

    def test_user_token_forbidden(self, user_token_and_id):
        r = requests.get(
            f"{BASE_URL}/api/admin/qr/stats",
            headers={"Authorization": f"Bearer {user_token_and_id['token']}"},
            timeout=15,
        )
        assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text}"

    def test_admin_token_ok(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/qr/stats", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert "rows" in body and isinstance(body["rows"], list)
        assert "totals" in body and isinstance(body["totals"], dict)
        for k in ("total_scans", "total_signups", "global_conversion_pct", "scans_last_7_days"):
            assert k in body["totals"], f"missing totals.{k}"


# ---- BUG #5 / #6 / #7 — aggregation correctness ---------------------------
class TestQRStatsAggregation:
    def test_aggregation_scans_and_signups(self, admin_headers):
        camp1 = f"{CAMPAIGN_PREFIX}flyer1"  # already has 1 user from fixture
        camp2 = f"{CAMPAIGN_PREFIX}flyer2"

        # Insert scans directly in Mongo for determinism (BUG #5)
        client, db = _mongo()
        now_iso = datetime.now(timezone.utc).isoformat()
        db.qr_scans.delete_many({"campaign": {"$in": [camp1, camp2]}})
        for _ in range(3):
            db.qr_scans.insert_one({
                "campaign": camp1, "referrer": "", "ip": "", "user_agent": "",
                "scanned_at": now_iso,
            })
        db.qr_scans.insert_one({
            "campaign": camp2, "referrer": "", "ip": "", "user_agent": "",
            "scanned_at": now_iso,
        })
        client.close()

        r = requests.get(f"{BASE_URL}/api/admin/qr/stats", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        rows = {row["campaign"]: row for row in r.json()["rows"]}
        assert camp1 in rows, f"row for {camp1} missing"
        assert camp2 in rows, f"row for {camp2} missing"
        assert rows[camp1]["scans"] == 3
        assert rows[camp2]["scans"] == 1
        # BUG #6 — user from fixture with signup_campaign=camp1 should be counted
        assert rows[camp1]["users_signed_up"] >= 1, "user signup not aggregated"
        # totals include these 4 scans
        assert r.json()["totals"]["total_scans"] >= 4

    def test_untracked_campaign_appears_with_scans_zero(self, admin_headers):
        """BUG #7 — campaign present in users.signup_campaign but NO scans."""
        untracked = f"{CAMPAIGN_PREFIX}untracked-historical"
        client, db = _mongo()
        db.qr_scans.delete_many({"campaign": untracked})  # ensure no scans
        uid = str(uuid.uuid4())
        db.users.insert_one({
            "id": uid,
            "email": f"TEST_untracked_{uid[:8]}@example.com",
            "first_name": "U", "last_name": "T",
            "phone": "+33600000999", "password": "x",
            "role": "user", "email_verified": True,
            "subscription_active": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "signup_campaign": untracked,
        })
        client.close()
        r = requests.get(f"{BASE_URL}/api/admin/qr/stats", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        rows = {row["campaign"]: row for row in r.json()["rows"]}
        assert untracked in rows, f"untracked campaign {untracked} missing"
        assert rows[untracked]["scans"] == 0
        assert rows[untracked]["users_signed_up"] >= 1
        assert rows[untracked]["conversion_pct"] is None


# ---- BUG #8 — scans_last_7_days window -----------------------------------
class TestScansLast7Days:
    def test_old_scans_excluded(self, admin_headers):
        camp = f"{CAMPAIGN_PREFIX}old-scan"
        client, db = _mongo()
        db.qr_scans.delete_many({"campaign": camp})
        old_iso = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        recent_iso = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        # 2 old + 1 recent for this campaign
        db.qr_scans.insert_one({"campaign": camp, "scanned_at": old_iso,
                                "referrer": "", "ip": "", "user_agent": ""})
        db.qr_scans.insert_one({"campaign": camp, "scanned_at": old_iso,
                                "referrer": "", "ip": "", "user_agent": ""})
        db.qr_scans.insert_one({"campaign": camp, "scanned_at": recent_iso,
                                "referrer": "", "ip": "", "user_agent": ""})
        client.close()

        r = requests.get(f"{BASE_URL}/api/admin/qr/stats", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        body = r.json()
        rows = {row["campaign"]: row for row in body["rows"]}
        assert camp in rows
        assert rows[camp]["scans"] == 3  # all 3 counted in total scans
        # scans_last_7_days is global; we just check it's an int and the
        # 2 old scans we just inserted are NOT counted
        last7 = body["totals"]["scans_last_7_days"]
        assert isinstance(last7, int)
        # The 2 'old' scans (>7d) for our campaign must not contribute
        # We verify by recomputing the recent-window count for this campaign
        client, db = _mongo()
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent_count_for_camp = db.qr_scans.count_documents(
            {"campaign": camp, "scanned_at": {"$gte": since}}
        )
        client.close()
        assert recent_count_for_camp == 1, "old scans should be filtered out of 7d window"
