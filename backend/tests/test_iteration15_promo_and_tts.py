"""
Iteration 15 — Saint-Denis launch P0 features.

Covers:
- Promo codes admin endpoints (generate / list / stats)
- User redeem flow (404/409/410)
- /promo-codes/my-promo
- Auto-attach promo at /auth/register/user
- /rides/request promo logic (free ride / over cap 400 / no promo no sub 403)
- TTS transfer alerts (8 langs/roles, info, admin pregenerate, caching)
- Regression: driver register with source_inscription

Admin auth: JWT forged via JWT_SECRET (bypass OTP for backend testing).
"""
import os
import uuid
import time
import asyncio
from datetime import datetime, timezone, timedelta

import jwt
import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")
load_dotenv("/app/frontend/.env")

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
JWT_SECRET = os.environ["JWT_SECRET"]
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

ADMIN_EMAIL = "contact@metro-taxi.com"


def _mongo():
    return AsyncIOMotorClient(MONGO_URL)[DB_NAME]


async def _get_admin_id():
    db = _mongo()
    a = await db.admins.find_one({"email": ADMIN_EMAIL}, {"_id": 0, "id": 1})
    return a["id"]


def _make_jwt(user_id: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=2),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@pytest.fixture(scope="module")
def admin_token():
    user_id = asyncio.get_event_loop().run_until_complete(_get_admin_id())
    return _make_jwt(user_id, "admin")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture
def fresh_user():
    """Register a new user via API, return (token, user_id, email)."""
    suffix = uuid.uuid4().hex[:10]
    email = f"test_{suffix}@example.com"
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "phone": "+33600000000",
        "password": "Password123!",
        "street_address": "1 rue test",
        "postal_code": "93200",
        "city": "Saint-Denis",
        "date_of_birth": "1990-01-01",
    }
    r = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    return {
        "token": data["token"],
        "user_id": data["user"]["id"],
        "email": email,
        "promo_attached": data.get("promo_attached"),
        "response": data,
    }


# =============================================================================
# Admin: generate / list / stats
# =============================================================================
class TestPromoAdmin:
    def test_generate_requires_admin(self):
        # No auth
        r = requests.post(f"{BASE_URL}/api/admin/promo-codes/generate", json={
            "campaign": "x", "count": 1, "expires_at": "2026-12-31T23:59:59Z",
        })
        assert r.status_code in (401, 403)

    def test_generate_forbidden_for_user(self, fresh_user):
        h = {"Authorization": f"Bearer {fresh_user['token']}"}
        r = requests.post(f"{BASE_URL}/api/admin/promo-codes/generate", json={
            "campaign": "TEST-forbidden", "prefix": "TSFOR", "count": 1, "max_distance_km": 10,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }, headers=h)
        assert r.status_code == 403

    def test_generate_and_list_and_stats(self, admin_headers):
        campaign = f"TEST-it15-{uuid.uuid4().hex[:6]}"
        payload = {
            "campaign": campaign,
            "prefix": "TSTDEN",
            "count": 3,
            "max_distance_km": 10,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "region": "saint-denis",
        }
        r = requests.post(f"{BASE_URL}/api/admin/promo-codes/generate", json=payload, headers=admin_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["status"] == "ok"
        assert data["generated_count"] == 3
        assert len(data["codes"]) == 3
        for c in data["codes"]:
            assert c["code"].startswith("TSTDEN-2026-")
            assert c["max_distance_km"] == 10
            assert c["used"] is False
            assert c["campaign"] == campaign

        # List with filter
        r2 = requests.get(f"{BASE_URL}/api/admin/promo-codes", params={"campaign": campaign}, headers=admin_headers)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["total"] == 3
        assert d2["used_count"] == 0
        assert d2["available_count"] == 3
        assert len(d2["codes"]) == 3

        # Stats
        r3 = requests.get(f"{BASE_URL}/api/admin/promo-codes/stats", headers=admin_headers)
        assert r3.status_code == 200
        rows = r3.json()["by_campaign"]
        match = [row for row in rows if row["campaign"] == campaign]
        assert len(match) == 1
        assert match[0]["total"] == 3

    def test_generate_invalid_expiry(self, admin_headers):
        r = requests.post(f"{BASE_URL}/api/admin/promo-codes/generate", json={
            "campaign": "TEST-past", "count": 1, "max_distance_km": 10,
            "expires_at": "2020-01-01T00:00:00Z",
        }, headers=admin_headers)
        assert r.status_code == 400


# =============================================================================
# User redeem flow
# =============================================================================
class TestRedeem:
    def _create_code(self, admin_headers, expires_days=30, max_km=10, used=False):
        campaign = f"TEST-redeem-{uuid.uuid4().hex[:6]}"
        r = requests.post(f"{BASE_URL}/api/admin/promo-codes/generate", json={
            "campaign": campaign, "prefix": "TSRED", "count": 1, "max_distance_km": max_km,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=expires_days)).isoformat(),
        }, headers=admin_headers)
        assert r.status_code == 200, r.text
        return r.json()["codes"][0]["code"]

    def test_redeem_404_unknown(self, fresh_user):
        h = {"Authorization": f"Bearer {fresh_user['token']}", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/promo-codes/redeem", json={"code": "NOPE-2026-XXXX"}, headers=h)
        assert r.status_code == 404

    def test_redeem_ok_then_409_already_pending(self, admin_headers, fresh_user):
        code = self._create_code(admin_headers)
        h = {"Authorization": f"Bearer {fresh_user['token']}", "Content-Type": "application/json"}
        r = requests.post(f"{BASE_URL}/api/promo-codes/redeem", json={"code": code}, headers=h)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["pending_promo"]["code"] == code
        assert body["pending_promo"]["max_distance_km"] == 10

        # my-promo returns it
        r2 = requests.get(f"{BASE_URL}/api/promo-codes/my-promo", headers=h)
        assert r2.status_code == 200
        assert r2.json()["pending_promo"]["code"] == code

        # second redeem -> 409 (user already has a pending_promo)
        code2 = self._create_code(admin_headers)
        r3 = requests.post(f"{BASE_URL}/api/promo-codes/redeem", json={"code": code2}, headers=h)
        assert r3.status_code == 409

    def test_redeem_409_used_code(self, admin_headers, fresh_user):
        # Use 2nd user
        code = self._create_code(admin_headers)
        # consume via first user (signup with promo_code)
        suffix = uuid.uuid4().hex[:8]
        r = requests.post(f"{BASE_URL}/api/auth/register/user", json={
            "first_name": "A", "last_name": "B", "email": f"u_{suffix}@example.com",
            "phone": "+33600000001", "password": "Password123!",
            "street_address": "x", "postal_code": "93200", "city": "Saint-Denis",
            "date_of_birth": "1990-01-01", "promo_code": code,
        }, timeout=20)
        assert r.status_code == 200, r.text
        assert r.json()["promo_attached"]["code"] == code

        # Now fresh_user tries to redeem the already used code -> 409
        h = {"Authorization": f"Bearer {fresh_user['token']}", "Content-Type": "application/json"}
        r2 = requests.post(f"{BASE_URL}/api/promo-codes/redeem", json={"code": code}, headers=h)
        assert r2.status_code == 409

    def test_redeem_410_expired(self, admin_headers, fresh_user):
        """Insert an expired code directly in DB (admin endpoint refuses past dates)."""
        import pymongo
        cli = pymongo.MongoClient(MONGO_URL)
        db = cli[DB_NAME]
        code = f"TSEXP-2026-{uuid.uuid4().hex[:4].upper()}"
        db.promo_codes.insert_one({
            "id": str(uuid.uuid4()),
            "code": code,
            "type": "free_first_ride",
            "campaign": "TEST-exp",
            "region": "saint-denis",
            "max_distance_km": 10,
            "expires_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "used": False, "used_by": None, "used_at": None,
            "redeemed_at": None, "consumed_at": None, "ride_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        try:
            h = {"Authorization": f"Bearer {fresh_user['token']}", "Content-Type": "application/json"}
            r = requests.post(f"{BASE_URL}/api/promo-codes/redeem", json={"code": code}, headers=h)
            assert r.status_code == 410, r.text
        finally:
            db.promo_codes.delete_one({"code": code})


# =============================================================================
# Auto-attach at signup + register without promo
# =============================================================================
class TestSignupPromo:
    def test_signup_no_promo_returns_attached_null(self, fresh_user):
        # fresh_user fixture already registered without promo_code
        resp = fresh_user["response"]
        assert resp.get("promo_attached") is None

    def test_signup_with_promo_attaches(self, admin_headers):
        # Generate a code
        r = requests.post(f"{BASE_URL}/api/admin/promo-codes/generate", json={
            "campaign": "TEST-signup", "prefix": "TSSIG", "count": 1, "max_distance_km": 8,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }, headers=admin_headers)
        code = r.json()["codes"][0]["code"]
        suffix = uuid.uuid4().hex[:8]
        r2 = requests.post(f"{BASE_URL}/api/auth/register/user", json={
            "first_name": "Sig", "last_name": "Up", "email": f"sig_{suffix}@example.com",
            "phone": "+33600000002", "password": "Password123!",
            "street_address": "x", "postal_code": "93200", "city": "Saint-Denis",
            "date_of_birth": "1990-01-01", "promo_code": code,
        }, timeout=20)
        assert r2.status_code == 200, r2.text
        d = r2.json()
        assert d["promo_attached"] is not None
        assert d["promo_attached"]["code"] == code
        assert d["promo_attached"]["max_distance_km"] == 8

        # Verify my-promo from API as that user
        h = {"Authorization": f"Bearer {d['token']}"}
        r3 = requests.get(f"{BASE_URL}/api/promo-codes/my-promo", headers=h)
        assert r3.status_code == 200
        assert r3.json()["pending_promo"]["code"] == code


# =============================================================================
# /rides/request promo logic
# =============================================================================
class TestRidesPromoLogic:
    # Coords ~10 km apart in Paris area
    SD_LAT, SD_LNG = 48.9358, 2.3539  # Saint-Denis
    NEAR_LAT, NEAR_LNG = 48.9420, 2.3600  # ~ 1 km
    FAR_LAT, FAR_LNG = 48.7500, 2.3700  # ~ 20 km

    def _user_with_promo(self, admin_headers, max_km=10):
        # generate a code, register user with it
        r = requests.post(f"{BASE_URL}/api/admin/promo-codes/generate", json={
            "campaign": "TEST-ride", "prefix": "TSRID", "count": 1, "max_distance_km": max_km,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        }, headers=admin_headers)
        code = r.json()["codes"][0]["code"]
        suffix = uuid.uuid4().hex[:8]
        r2 = requests.post(f"{BASE_URL}/api/auth/register/user", json={
            "first_name": "Rid", "last_name": "Er", "email": f"rid_{suffix}@example.com",
            "phone": "+33600000003", "password": "Password123!",
            "street_address": "x", "postal_code": "93200", "city": "Saint-Denis",
            "date_of_birth": "1990-01-01", "promo_code": code,
        }, timeout=20).json()
        return r2["token"], r2["user"]["id"], code

    def test_no_promo_no_sub_returns_403(self, fresh_user):
        """User with no pending_promo and no subscription -> 403 Abonnement requis."""
        h = {"Authorization": f"Bearer {fresh_user['token']}", "Content-Type": "application/json"}
        body = {
            "driver_id": "fake-driver-id",
            "pickup_lat": self.SD_LAT, "pickup_lng": self.SD_LNG,
            "destination_lat": self.NEAR_LAT, "destination_lng": self.NEAR_LNG,
        }
        r = requests.post(f"{BASE_URL}/api/rides/request", json=body, headers=h)
        assert r.status_code == 403, r.text
        assert "Abonnement" in r.json().get("detail", "")

    def test_promo_too_far_returns_400_with_clear_message(self, admin_headers):
        token, uid, code = self._user_with_promo(admin_headers, max_km=10)
        h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        body = {
            "driver_id": "fake-driver-id",
            "pickup_lat": self.SD_LAT, "pickup_lng": self.SD_LNG,
            "destination_lat": self.FAR_LAT, "destination_lng": self.FAR_LNG,
        }
        r = requests.post(f"{BASE_URL}/api/rides/request", json=body, headers=h)
        assert r.status_code == 400, r.text
        msg = r.json()["detail"]
        # DGCCRF: limit must be explicit
        assert "10 km" in msg or "10.0 km" in msg or "plafonnée à 10" in msg
        # User still has pending_promo (not consumed)
        r2 = requests.get(f"{BASE_URL}/api/promo-codes/my-promo", headers=h)
        assert r2.json()["pending_promo"]["code"] == code

    def test_promo_within_limit_creates_free_ride_and_consumes(self, admin_headers):
        token, uid, code = self._user_with_promo(admin_headers, max_km=10)
        h = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        body = {
            "driver_id": "fake-driver-id",
            "pickup_lat": self.SD_LAT, "pickup_lng": self.SD_LNG,
            "destination_lat": self.NEAR_LAT, "destination_lng": self.NEAR_LNG,
        }
        r = requests.post(f"{BASE_URL}/api/rides/request", json=body, headers=h)
        assert r.status_code == 200, r.text
        # my-promo cleared
        r2 = requests.get(f"{BASE_URL}/api/promo-codes/my-promo", headers=h)
        assert r2.json()["pending_promo"] is None
        # promo code marked consumed in DB
        import pymongo
        cli = pymongo.MongoClient(MONGO_URL)
        doc = cli[DB_NAME].promo_codes.find_one({"code": code})
        assert doc is not None
        assert doc.get("consumed_at") is not None
        assert doc.get("ride_id") is not None
        assert doc.get("used") is True


# =============================================================================
# TTS transfer alerts
# =============================================================================
class TestTransferAlerts:
    def test_info_endpoint(self):
        r = requests.get(f"{BASE_URL}/api/tts/transfer-alerts/info")
        assert r.status_code == 200
        d = r.json()
        assert d["voice"] == "nova"
        assert set(d["languages"]) == {"fr", "ar", "en", "es"}
        assert set(d["roles"]) == {"user", "driver"}
        assert "alerts" in d
        for role in ("user", "driver"):
            for lang in ("fr", "ar", "en", "es"):
                assert role in d["alerts"]
                assert lang in d["alerts"][role]
                assert d["alerts"][role][lang]["text"]

    @pytest.mark.parametrize("role,lang", [
        ("user", "fr"), ("user", "en"), ("user", "es"), ("user", "ar"),
        ("driver", "fr"), ("driver", "en"), ("driver", "es"), ("driver", "ar"),
    ])
    def test_transfer_alert_mp3(self, role, lang):
        r = requests.get(f"{BASE_URL}/api/tts/transfer-alert", params={"lang": lang, "role": role}, timeout=60)
        assert r.status_code == 200, r.text[:200]
        assert r.headers.get("content-type", "").startswith("audio/mpeg")
        assert len(r.content) > 500  # non-empty MP3

    def test_transfer_alert_cached_second_call(self):
        # Two calls — second should be served quickly from cache
        params = {"lang": "fr", "role": "user"}
        r1 = requests.get(f"{BASE_URL}/api/tts/transfer-alert", params=params, timeout=60)
        assert r1.status_code == 200
        t0 = time.time()
        r2 = requests.get(f"{BASE_URL}/api/tts/transfer-alert", params=params, timeout=30)
        dt = time.time() - t0
        assert r2.status_code == 200
        assert r1.content == r2.content  # identical bytes
        assert dt < 5  # cache hit must be fast

    def test_transfer_alert_bad_params(self):
        r = requests.get(f"{BASE_URL}/api/tts/transfer-alert", params={"lang": "zz", "role": "user"})
        assert r.status_code == 400
        r2 = requests.get(f"{BASE_URL}/api/tts/transfer-alert", params={"lang": "fr", "role": "alien"})
        assert r2.status_code == 400

    def test_pregenerate_admin_only(self, fresh_user):
        # No auth
        r0 = requests.post(f"{BASE_URL}/api/admin/tts/pregenerate-transfer-alerts")
        assert r0.status_code in (401, 403)
        # User token
        h = {"Authorization": f"Bearer {fresh_user['token']}"}
        r = requests.post(f"{BASE_URL}/api/admin/tts/pregenerate-transfer-alerts", headers=h)
        assert r.status_code == 403

    def test_pregenerate_admin_ok(self, admin_headers):
        r = requests.post(f"{BASE_URL}/api/admin/tts/pregenerate-transfer-alerts", headers=admin_headers, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["status"] == "complete"
        assert isinstance(d["results"]["generated"], list)
        assert isinstance(d["results"]["skipped"], list)


# =============================================================================
# Regression: driver register source_inscription
# =============================================================================
class TestDriverRegisterRegression:
    def test_register_driver_with_source_inscription_parrainage(self):
        suffix = uuid.uuid4().hex[:8]
        payload = {
            "first_name": "Drv",
            "last_name": "Test",
            "email": f"drv_{suffix}@example.com",
            "phone": "+33611111111",
            "password": "Password123!",
            "vehicle_plate": f"AA-{suffix[:3].upper()}-99",
            "vehicle_type": "berline",
            "seats": 4,
            "vtc_license": f"VTC{suffix}",
            "region_id": "paris",
            "source_inscription": "Parrainage (Jean Dupont)",
        }
        r = requests.post(f"{BASE_URL}/api/auth/register/driver", json=payload, timeout=20)
        assert r.status_code == 200, r.text
        # verify persisted
        import pymongo
        cli = pymongo.MongoClient(MONGO_URL)
        doc = cli[DB_NAME].drivers.find_one({"email": payload["email"]})
        assert doc is not None
        assert doc.get("source_inscription") == "Parrainage (Jean Dupont)"


# =============================================================================
# Teardown: clean TEST_ data after all tests
# =============================================================================
def teardown_module(module):
    import pymongo
    cli = pymongo.MongoClient(MONGO_URL)
    db = cli[DB_NAME]
    db.promo_codes.delete_many({"campaign": {"$regex": "^TEST-"}})
    db.users.delete_many({"email": {"$regex": r"^(test|u|sig|rid|drv)_[0-9a-f]+@example\.com$"}})
    db.drivers.delete_many({"email": {"$regex": r"^drv_[0-9a-f]+@example\.com$"}})
    db.ride_requests.delete_many({"user_name": {"$regex": "^(Test User|Sig Up|Rid Er)"}})
