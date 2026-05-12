"""
Tests d'intégration pour le plafond de l'abonnement 24h (5 trajets max).
Run: cd /app/backend && pytest tests/test_subscription_24h_cap.py -v
"""
import sys
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import jwt
import os
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from server import app
from database import db


def _make_token(user_id: str, role: str = "user") -> str:
    secret = os.environ["JWT_SECRET"]
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest_asyncio.fixture
async def test_user_24h():
    """Create a test user with active 24h subscription. Cleanup after."""
    user_id = f"test-24h-{uuid.uuid4()}"
    now = datetime.now(timezone.utc)
    sub_started = now - timedelta(hours=1)
    sub_expires = now + timedelta(hours=23)

    await db.users.insert_one({
        "id": user_id,
        "first_name": "Test",
        "last_name": "User24h",
        "email": f"{user_id}@test.local",
        "phone": "0600000000",
        "role": "user",
        "subscription_active": True,
        "subscription_plan": "24h",
        "subscription_started_at": sub_started.isoformat(),
        "subscription_expires": sub_expires.isoformat(),
        "created_at": now.isoformat(),
    })

    yield user_id

    # Cleanup
    await db.users.delete_one({"id": user_id})
    await db.ride_requests.delete_many({"user_id": user_id})


@pytest.mark.asyncio
async def test_24h_cap_blocks_at_5_rides(test_user_24h):
    """After 5 rides in the 24h window, the 6th should return 429."""
    user_id = test_user_24h
    now = datetime.now(timezone.utc)

    # Seed 5 existing rides within the period
    for i in range(5):
        await db.ride_requests.insert_one({
            "id": f"ride-{user_id}-{i}",
            "user_id": user_id,
            "driver_id": f"driver-{i}",
            "pickup_lat": 48.85, "pickup_lng": 2.35,
            "destination_lat": 48.86, "destination_lng": 2.34,
            "status": "completed",
            "created_at": (now - timedelta(minutes=10 * (i + 1))).isoformat(),
        })

    token = _make_token(user_id, role="user")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/rides/request",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "driver_id": "some-driver",
                "pickup_lat": 48.85,
                "pickup_lng": 2.35,
                "destination_lat": 48.86,
                "destination_lng": 2.34,
            },
        )

    assert resp.status_code == 429, f"Expected 429, got {resp.status_code}: {resp.text}"
    assert "Plafond atteint" in resp.json().get("detail", "")


@pytest.mark.asyncio
async def test_24h_cap_allows_4th_ride(test_user_24h):
    """With only 4 prior rides, the 5th request should be allowed (not blocked by cap)."""
    user_id = test_user_24h
    now = datetime.now(timezone.utc)

    # Seed 4 existing rides
    for i in range(4):
        await db.ride_requests.insert_one({
            "id": f"ride-{user_id}-{i}",
            "user_id": user_id,
            "driver_id": f"driver-{i}",
            "pickup_lat": 48.85, "pickup_lng": 2.35,
            "destination_lat": 48.86, "destination_lng": 2.34,
            "status": "completed",
            "created_at": (now - timedelta(minutes=10 * (i + 1))).isoformat(),
        })

    token = _make_token(user_id, role="user")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/rides/request",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "driver_id": "some-driver",
                "pickup_lat": 48.85,
                "pickup_lng": 2.35,
                "destination_lat": 48.86,
                "destination_lng": 2.34,
            },
        )

    # Should NOT be blocked by cap (status 200 or other non-429 error like driver not found)
    assert resp.status_code != 429, f"Should not be capped at 4 rides: {resp.text}"


@pytest.mark.asyncio
async def test_24h_cap_does_not_count_rejected_rides(test_user_24h):
    """Rejected/cancelled rides should NOT count toward the cap."""
    user_id = test_user_24h
    now = datetime.now(timezone.utc)

    # Seed 5 rejected rides + 0 valid → cap should NOT trigger
    for i in range(5):
        await db.ride_requests.insert_one({
            "id": f"ride-{user_id}-{i}",
            "user_id": user_id,
            "driver_id": f"driver-{i}",
            "pickup_lat": 48.85, "pickup_lng": 2.35,
            "destination_lat": 48.86, "destination_lng": 2.34,
            "status": "rejected",
            "created_at": (now - timedelta(minutes=10 * (i + 1))).isoformat(),
        })

    token = _make_token(user_id, role="user")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/rides/request",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "driver_id": "some-driver",
                "pickup_lat": 48.85,
                "pickup_lng": 2.35,
                "destination_lat": 48.86,
                "destination_lng": 2.34,
            },
        )

    assert resp.status_code != 429, f"Rejected rides should not count: {resp.text}"


@pytest_asyncio.fixture
async def test_user_1month():
    """Create a test user with 1-month subscription (no cap should apply)."""
    user_id = f"test-1month-{uuid.uuid4()}"
    now = datetime.now(timezone.utc)
    sub_expires = now + timedelta(days=30)

    await db.users.insert_one({
        "id": user_id,
        "first_name": "Test",
        "last_name": "User1month",
        "email": f"{user_id}@test.local",
        "phone": "0600000000",
        "role": "user",
        "subscription_active": True,
        "subscription_plan": "1month",
        "subscription_expires": sub_expires.isoformat(),
        "created_at": now.isoformat(),
    })

    yield user_id

    await db.users.delete_one({"id": user_id})
    await db.ride_requests.delete_many({"user_id": user_id})


@pytest.mark.asyncio
async def test_1month_plan_has_no_cap(test_user_1month):
    """Monthly plan users should never be capped (unlimited rides)."""
    user_id = test_user_1month
    now = datetime.now(timezone.utc)

    # Seed 10 rides — should be fine
    for i in range(10):
        await db.ride_requests.insert_one({
            "id": f"ride-{user_id}-{i}",
            "user_id": user_id,
            "driver_id": f"driver-{i}",
            "pickup_lat": 48.85, "pickup_lng": 2.35,
            "destination_lat": 48.86, "destination_lng": 2.34,
            "status": "completed",
            "created_at": (now - timedelta(minutes=30 * (i + 1))).isoformat(),
        })

    token = _make_token(user_id, role="user")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/rides/request",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "driver_id": "some-driver",
                "pickup_lat": 48.85,
                "pickup_lng": 2.35,
                "destination_lat": 48.86,
                "destination_lng": 2.34,
            },
        )

    assert resp.status_code != 429, f"Monthly plan should have no cap: {resp.text}"
