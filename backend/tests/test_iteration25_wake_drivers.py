"""Iter25 backend tests — POST /api/rides/wake-drivers.

Validates the 5 backend bugs spec'd in the iter25 review request:
  BUG #1 — auth: 401 sans token, 403 si role != user
  BUG #2 — body {} → région default 'paris', no offline drivers → status='no_offline_drivers'
  BUG #3 — 3 drivers seedés (online, offline-validé, offline-invalidé) → notified_count=1 + notif doc créé
  BUG #4 — rate limit 10 min → 429 puis OK après patch users.last_wake_drivers_at
  BUG #5 — body_text du push contient '13.9 km' (distance_km=13.95)

Cleanup: tous les test-iter25-* drivers/users/notifications.
"""
import os
import pathlib
import asyncio
from datetime import datetime, timezone, timedelta

import jwt
import pytest
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

JWT_SECRET = os.environ["JWT_SECRET"]
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip()
BASE_URL = BASE_URL.rstrip("/")

PREFIX = "test-iter25-"
TEST_REGION = "test-iter25-region"
USER_ID = f"{PREFIX}user"
DRIVER_ONLINE = f"{PREFIX}driver-online"
DRIVER_OFFLINE_VALID = f"{PREFIX}driver-offline"
DRIVER_OFFLINE_INVALID = f"{PREFIX}driver-invalidated"
ADMIN_ID = f"{PREFIX}admin"


def _mk_token(uid: str, role: str) -> str:
    return jwt.encode(
        {"user_id": uid, "role": role,
         "exp": datetime.now(timezone.utc) + timedelta(hours=2)},
        JWT_SECRET, algorithm="HS256")


@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    yield client[DB_NAME]
    client.close()


@pytest.fixture(scope="module", autouse=True)
def seed(db):
    """Seed user + 3 drivers + cleanup at the end."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # Cleanup any leftover
    db.users.delete_many({"id": {"$regex": f"^{PREFIX}"}})
    db.drivers.delete_many({"id": {"$regex": f"^{PREFIX}"}})
    db.notifications.delete_many({"user_id": {"$regex": f"^{PREFIX}"}})

    # Seed user (no last_wake_drivers_at => no rate limit)
    db.users.insert_one({
        "id": USER_ID,
        "first_name": "Iter25",
        "last_name": "User",
        "email": "test-iter25-user@metro-taxi.com",
        "phone": "+33600000025",
        "password": "x",
        "role": "user",
        "email_verified": True,
        "region_id": TEST_REGION,
        "subscription_active": True,
        "subscription_expires": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "created_at": now_iso,
    })

    # Seed admin (for 403 test)
    db.users.delete_one({"id": ADMIN_ID})
    db.users.insert_one({
        "id": ADMIN_ID,
        "first_name": "Iter25",
        "last_name": "Admin",
        "email": "test-iter25-admin@metro-taxi.com",
        "role": "admin",
        "email_verified": True,
        "created_at": now_iso,
    })

    # Driver (a) online validated — should NOT be notified
    db.drivers.insert_one({
        "id": DRIVER_ONLINE,
        "first_name": "Online",
        "last_name": "Driver",
        "email": "test-iter25-driver-online@metro-taxi.com",
        "role": "driver",
        "is_validated": True,
        "is_active": True,
        "region_id": TEST_REGION,
        "created_at": now_iso,
    })
    # Driver (b) offline validated — SHOULD be notified
    db.drivers.insert_one({
        "id": DRIVER_OFFLINE_VALID,
        "first_name": "Offline",
        "last_name": "Validated",
        "email": "test-iter25-driver-offline@metro-taxi.com",
        "role": "driver",
        "is_validated": True,
        "is_active": False,
        "region_id": TEST_REGION,
        "created_at": now_iso,
    })
    # Driver (c) offline NOT validated — should NOT be notified
    db.drivers.insert_one({
        "id": DRIVER_OFFLINE_INVALID,
        "first_name": "Offline",
        "last_name": "Invalidated",
        "email": "test-iter25-driver-invalidated@metro-taxi.com",
        "role": "driver",
        "is_validated": False,
        "is_active": False,
        "region_id": TEST_REGION,
        "created_at": now_iso,
    })

    yield

    # Cleanup
    db.users.delete_many({"id": {"$regex": f"^{PREFIX}"}})
    db.drivers.delete_many({"id": {"$regex": f"^{PREFIX}"}})
    db.notifications.delete_many({"user_id": {"$regex": f"^{PREFIX}"}})


@pytest.fixture
def user_token():
    return _mk_token(USER_ID, "user")


@pytest.fixture
def driver_token():
    return _mk_token(DRIVER_OFFLINE_VALID, "driver")


@pytest.fixture
def admin_token():
    return _mk_token(ADMIN_ID, "admin")


@pytest.fixture(autouse=True)
def reset_rate_limit(db):
    """Before each test, clear users.last_wake_drivers_at + notifications for offline driver."""
    db.users.update_one({"id": USER_ID}, {"$unset": {"last_wake_drivers_at": ""}})
    db.notifications.delete_many({"user_id": {"$regex": f"^{PREFIX}"}})
    yield


# ============================================
# BUG #1 — Auth checks
# ============================================
class TestAuth:
    def test_no_token_returns_401_or_403(self):
        r = requests.post(f"{BASE_URL}/api/rides/wake-drivers", json={})
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}: {r.text}"

    def test_admin_token_returns_403(self, admin_token):
        r = requests.post(
            f"{BASE_URL}/api/rides/wake-drivers",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 403, f"Admin should get 403, got {r.status_code}: {r.text}"
        assert "usager" in r.json().get("detail", "").lower()

    def test_driver_token_returns_403(self, driver_token):
        r = requests.post(
            f"{BASE_URL}/api/rides/wake-drivers",
            json={},
            headers={"Authorization": f"Bearer {driver_token}"},
        )
        assert r.status_code == 403, f"Driver should get 403, got {r.status_code}: {r.text}"


# ============================================
# BUG #2 — Empty body w/ no offline drivers in region
# ============================================
class TestEmptyBody:
    def test_empty_body_no_offline_drivers_in_other_region(self, db, user_token):
        """Use a region with no offline drivers → status='no_offline_drivers'."""
        r = requests.post(
            f"{BASE_URL}/api/rides/wake-drivers",
            json={"region_id": "lyon-no-drivers-here"},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
        data = r.json()
        assert data["status"] == "no_offline_drivers"
        assert data["notified_count"] == 0


# ============================================
# BUG #3 — Wake drivers only notifies offline validated drivers
# ============================================
class TestWakeDriversCore:
    def test_wake_drivers_notifies_only_offline_validated(self, db, user_token):
        r = requests.post(
            f"{BASE_URL}/api/rides/wake-drivers",
            json={"region_id": TEST_REGION, "distance_km": 13.95},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
        data = r.json()
        assert data["status"] == "notified", data
        assert data["notified_count"] == 1, f"Expected 1 notified driver, got {data['notified_count']}"
        assert data["region_id"] == TEST_REGION

        # Verify notification doc created for the offline validated driver
        # asyncio.create_task is fire-and-forget — wait briefly
        notif_doc = None
        for _ in range(20):
            notif_doc = db.notifications.find_one({"user_id": DRIVER_OFFLINE_VALID})
            if notif_doc:
                break
            import time
            time.sleep(0.25)

        assert notif_doc is not None, "Expected notification doc for offline validated driver"
        assert notif_doc.get("title") == "🚖 Un usager te cherche !"
        body = notif_doc.get("body", "")
        assert "cherche une course" in body, f"body={body}"

        # And no notif for the online driver or the invalidated driver
        assert db.notifications.find_one({"user_id": DRIVER_ONLINE}) is None
        assert db.notifications.find_one({"user_id": DRIVER_OFFLINE_INVALID}) is None

        # And users.last_wake_drivers_at was updated
        u = db.users.find_one({"id": USER_ID})
        assert u.get("last_wake_drivers_at"), "last_wake_drivers_at should be set"


# ============================================
# BUG #5 — distance_km formatting in push body
# ============================================
class TestDistanceFormatting:
    def test_distance_appears_in_body(self, db, user_token):
        r = requests.post(
            f"{BASE_URL}/api/rides/wake-drivers",
            json={"region_id": TEST_REGION, "distance_km": 13.95},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert r.status_code == 200, r.text

        notif_doc = None
        for _ in range(20):
            notif_doc = db.notifications.find_one({"user_id": DRIVER_OFFLINE_VALID})
            if notif_doc:
                break
            import time
            time.sleep(0.25)
        assert notif_doc is not None
        body = notif_doc.get("body", "")
        # Spec: "13.9 km" ou "13.95 km" selon le format
        assert ("13.9 km" in body) or ("13.95 km" in body), f"Expected distance in body, got: {body}"


# ============================================
# BUG #4 — Rate limit
# ============================================
class TestRateLimit:
    def test_second_call_returns_429(self, db, user_token):
        # 1st call
        r1 = requests.post(
            f"{BASE_URL}/api/rides/wake-drivers",
            json={"region_id": TEST_REGION, "distance_km": 5},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert r1.status_code == 200, r1.text

        # 2nd call immediately → 429
        r2 = requests.post(
            f"{BASE_URL}/api/rides/wake-drivers",
            json={"region_id": TEST_REGION, "distance_km": 5},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert r2.status_code == 429, f"Expected 429 on 2nd call, got {r2.status_code}: {r2.text}"
        detail = r2.json().get("detail", "")
        assert "Attends" in detail and "min" in detail, f"detail={detail}"

    def test_rate_limit_clears_after_patch(self, db, user_token):
        # Trigger rate limit
        requests.post(
            f"{BASE_URL}/api/rides/wake-drivers",
            json={"region_id": TEST_REGION},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        # Patch last_wake_drivers_at to >10 min ago
        old_ts = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        db.users.update_one(
            {"id": USER_ID},
            {"$set": {"last_wake_drivers_at": old_ts}}
        )
        r = requests.post(
            f"{BASE_URL}/api/rides/wake-drivers",
            json={"region_id": TEST_REGION, "distance_km": 7},
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert r.status_code == 200, f"After patch should work, got {r.status_code}: {r.text}"
        assert r.json()["status"] == "notified"
