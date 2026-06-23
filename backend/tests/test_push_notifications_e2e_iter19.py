"""
Iteration 19 — Push notifications fire-and-forget e2e test
Validates that 5 ride-flow endpoints emit push notifications stored in db.notifications
without blocking or failing the main API.

Endpoints covered:
  1. POST /api/rides/request           -> push to driver  (type=ride_request)
  2. POST /api/rides/{id}/accept       -> push to user    (type=ride_accepted)
  3. POST /api/rides/{id}/reject       -> push to user    (type=ride_rejected)
  4. POST /api/rides/{id}/cancel       -> push to driver  (type=ride_cancelled)
  5. PUT  /api/rides/{id}/progress     -> push to user    (type=driver_arrived) when status=pickup
"""
import os
import time
import uuid
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://metro-taxi-demo.preview.emergentagent.com").rstrip("/")
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "test_database"

TEST_TAG = f"TEST_E2E_{uuid.uuid4().hex[:8]}"


# ----- Shared fixtures -----
@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    return client[DB_NAME]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def created_ids():
    """Tracks ids for cleanup after the module."""
    return {"users": [], "drivers": [], "rides": []}


@pytest.fixture(scope="module", autouse=True)
def cleanup(db, created_ids):
    yield
    # Best-effort teardown
    if created_ids["users"]:
        db.users.delete_many({"id": {"$in": created_ids["users"]}})
        db.notifications.delete_many({"user_id": {"$in": created_ids["users"]}})
    if created_ids["drivers"]:
        db.drivers.delete_many({"id": {"$in": created_ids["drivers"]}})
        db.notifications.delete_many({"user_id": {"$in": created_ids["drivers"]}})
    if created_ids["rides"]:
        db.ride_requests.delete_many({"id": {"$in": created_ids["rides"]}})
    db.email_verifications.delete_many({"email": {"$regex": f"^{TEST_TAG.lower()}"}})


@pytest.fixture(scope="module")
def test_user(session, db, created_ids):
    """Register a user, mark email verified + subscription active."""
    email = f"{TEST_TAG.lower()}_user@example.com"
    payload = {
        "first_name": "TestU",
        "last_name": "Push",
        "email": email,
        "phone": "+33600000001",
        "password": "Password123!",
        "region_id": "paris",
        "street_address": "1 rue de Test",
        "postal_code": "75001",
        "city": "Paris",
        "date_of_birth": "1990-01-01",
    }
    r = session.post(f"{BASE_URL}/api/auth/register/user", json=payload)
    assert r.status_code in (200, 201), f"register user failed: {r.status_code} {r.text}"
    # Mark email verified + activate subscription
    db.users.update_one(
        {"email": email},
        {"$set": {"email_verified": True, "subscription_active": True}},
    )
    user_doc = db.users.find_one({"email": email})
    assert user_doc, "user not found after registration"
    created_ids["users"].append(user_doc["id"])

    # Login
    lr = session.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "Password123!"})
    assert lr.status_code == 200, f"login user failed: {lr.status_code} {lr.text}"
    token = lr.json().get("access_token") or lr.json().get("token")
    assert token, f"no token in login response: {lr.json()}"
    return {"id": user_doc["id"], "token": token, "email": email}


@pytest.fixture(scope="module")
def test_driver(session, db, created_ids):
    """Register a driver, mark email verified + active + validated."""
    email = f"{TEST_TAG.lower()}_drv@example.com"
    payload = {
        "first_name": "TestD",
        "last_name": "Push",
        "email": email,
        "phone": "+33600000002",
        "password": "Password123!",
        "vehicle_plate": "TEST-PUSH-1",
        "vehicle_type": "berline",
        "seats": 4,
        "vtc_license": "VTC-TEST-PUSH",
        "tax_id": "SIRET-TEST-PUSH",
        "region_id": "paris",
    }
    r = session.post(f"{BASE_URL}/api/auth/register/driver", json=payload)
    assert r.status_code in (200, 201), f"register driver failed: {r.status_code} {r.text}"
    db.drivers.update_one(
        {"email": email},
        {"$set": {"is_active": True, "is_validated": True, "email_verified": True, "available_seats": 4}},
    )
    drv = db.drivers.find_one({"email": email})
    assert drv, "driver not found after registration"
    created_ids["drivers"].append(drv["id"])

    lr = session.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": "Password123!"})
    assert lr.status_code == 200, f"login driver failed: {lr.status_code} {lr.text}"
    token = lr.json().get("access_token") or lr.json().get("token")
    assert token, f"no driver token: {lr.json()}"
    return {"id": drv["id"], "token": token, "email": email}


def _auth(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _wait_for_notif(db, user_id, user_type, title_contains, timeout=4.0):
    """Poll db.notifications since asyncio.create_task is fire-and-forget."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        n = db.notifications.find_one({
            "user_id": user_id,
            "user_type": user_type,
            "title": {"$regex": title_contains}
        })
        if n:
            return n
        time.sleep(0.2)
    return None


# ----- Test scenarios -----
class TestPushNotificationsE2E:

    def test_01_create_ride_request_pushes_driver(self, session, db, test_user, test_driver, created_ids):
        ride_payload = {
            "driver_id": test_driver["id"],
            "pickup_lat": 48.8566,
            "pickup_lng": 2.3522,
            "destination_lat": 48.8606,
            "destination_lng": 2.3376,
            "pickup_address": "Place de la Concorde, Paris",
            "destination_address": "Louvre, Paris",
        }
        r = session.post(
            f"{BASE_URL}/api/rides/request",
            json=ride_payload,
            headers=_auth(test_user["token"]),
        )
        assert r.status_code in (200, 201), f"create ride failed: {r.status_code} {r.text}"
        ride = r.json().get("ride") or r.json()
        ride_id = ride.get("id")
        assert ride_id, f"no ride id in response: {r.json()}"
        created_ids["rides"].append(ride_id)
        # Save for later tests
        TestPushNotificationsE2E.ride_id = ride_id

        notif = _wait_for_notif(db, test_driver["id"], "driver", "Nouvelle course")
        assert notif is not None, "Driver did NOT receive push notif on ride request"
        assert notif["data"]["type"] == "ride_request"
        assert notif["data"]["ride_id"] == ride_id

    def test_02_accept_ride_pushes_user(self, session, db, test_user, test_driver):
        ride_id = TestPushNotificationsE2E.ride_id
        r = session.post(
            f"{BASE_URL}/api/rides/{ride_id}/accept",
            headers=_auth(test_driver["token"]),
        )
        assert r.status_code in (200, 202), f"accept failed: {r.status_code} {r.text}"
        notif = _wait_for_notif(db, test_user["id"], "user", "accept")
        assert notif is not None, "User did NOT receive push on accept"
        assert notif["data"]["type"] == "ride_accepted"

    def test_03_progress_pickup_pushes_user_with_otp(self, session, db, test_user, test_driver):
        ride_id = TestPushNotificationsE2E.ride_id
        payload = {"ride_id": ride_id, "status": "pickup"}
        r = session.post(
            f"{BASE_URL}/api/rides/{ride_id}/progress",
            json=payload,
            headers=_auth(test_driver["token"]),
        )
        assert r.status_code in (200, 202), f"progress pickup failed: {r.status_code} {r.text}"
        notif = _wait_for_notif(db, test_user["id"], "user", "arriv")
        assert notif is not None, "User did NOT receive 'driver arrived' push"
        assert notif["data"]["type"] == "driver_arrived"
        # OTP must be in body but NOT in data.url (BUG #5)
        assert "url" in notif["data"]
        url_val = str(notif["data"].get("url", ""))
        # url should be a navigation path, not contain raw OTP digits exclusively
        assert "/dashboard" in url_val or url_val.startswith("/"), f"unexpected url: {url_val}"
        # Verify OTP is not leaked in any data field besides body
        ride = db.ride_requests.find_one({"id": ride_id})
        otp = (ride or {}).get("pickup_otp")
        if otp:
            for k, v in notif["data"].items():
                assert str(otp) not in str(v), f"OTP leaked in data.{k}={v}"

    def test_04_cancel_after_accept_pushes_driver(self, session, db, test_user, test_driver, created_ids):
        # Create a fresh ride to test cancel-after-accept (the previous one is already in pickup status,
        # which is not cancellable)
        ride_payload = {
            "driver_id": test_driver["id"],
            "pickup_lat": 48.8566,
            "pickup_lng": 2.3522,
            "destination_lat": 48.8606,
            "destination_lng": 2.3376,
            "pickup_address": "Test cancel",
            "destination_address": "Dest",
        }
        r = session.post(
            f"{BASE_URL}/api/rides/request",
            json=ride_payload,
            headers=_auth(test_user["token"]),
        )
        assert r.status_code in (200, 201), f"create ride2 failed: {r.text}"
        ride = r.json().get("ride") or r.json()
        ride_id = ride["id"]
        created_ids["rides"].append(ride_id)

        # Driver accepts
        ra = session.post(
            f"{BASE_URL}/api/rides/{ride_id}/accept",
            headers=_auth(test_driver["token"]),
        )
        assert ra.status_code in (200, 202), f"accept2 failed: {ra.text}"
        time.sleep(0.3)

        # User cancels
        rc = session.post(
            f"{BASE_URL}/api/rides/{ride_id}/cancel",
            headers=_auth(test_user["token"]),
        )
        assert rc.status_code in (200, 202), f"cancel failed: {rc.status_code} {rc.text}"

        notif = _wait_for_notif(db, test_driver["id"], "driver", "annul")
        assert notif is not None, "Driver did NOT receive cancel push"
        assert notif["data"]["type"] == "ride_cancelled"

    def test_05_reject_ride_pushes_user(self, session, db, test_user, test_driver, created_ids):
        # Fresh ride for reject path
        ride_payload = {
            "driver_id": test_driver["id"],
            "pickup_lat": 48.8566,
            "pickup_lng": 2.3522,
            "destination_lat": 48.8606,
            "destination_lng": 2.3376,
            "pickup_address": "Test reject",
            "destination_address": "Dest",
        }
        r = session.post(
            f"{BASE_URL}/api/rides/request",
            json=ride_payload,
            headers=_auth(test_user["token"]),
        )
        assert r.status_code in (200, 201), f"create ride3 failed: {r.text}"
        ride = r.json().get("ride") or r.json()
        ride_id = ride["id"]
        created_ids["rides"].append(ride_id)

        rj = session.post(
            f"{BASE_URL}/api/rides/{ride_id}/reject",
            headers=_auth(test_driver["token"]),
        )
        assert rj.status_code in (200, 202), f"reject failed: {rj.status_code} {rj.text}"
        notif = _wait_for_notif(db, test_user["id"], "user", "refus")
        assert notif is not None, "User did NOT receive reject push"
        assert notif["data"]["type"] == "ride_rejected"

    def test_06_no_regression_response_shape(self, session, test_user, test_driver):
        """Ensure endpoints return proper status even though push runs in background."""
        # We already exercised statuses above; just sanity-check that ride request response includes ride.id
        ride_payload = {
            "driver_id": test_driver["id"],
            "pickup_lat": 48.8566,
            "pickup_lng": 2.3522,
            "destination_lat": 48.8606,
            "destination_lng": 2.3376,
        }
        r = session.post(
            f"{BASE_URL}/api/rides/request",
            json=ride_payload,
            headers=_auth(test_user["token"]),
        )
        assert r.status_code in (200, 201)
        body = r.json()
        ride = body.get("ride") or body
        assert "id" in ride
