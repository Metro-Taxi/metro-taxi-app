"""Iter22 seed helper — creates test driver + test user in MongoDB and prints JWTs.
Cleanup: invoke with --cleanup."""
import os
import sys
import json
import pathlib
from datetime import datetime, timezone, timedelta

import jwt
from dotenv import load_dotenv
from pymongo import MongoClient

ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

JWT_SECRET = os.environ["JWT_SECRET"]
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

PREFIX = "test-iter22-"
DRIVER_ID = f"{PREFIX}driver"
USER_ID = f"{PREFIX}user"


def make_token(uid: str, role: str) -> str:
    return jwt.encode(
        {"user_id": uid, "role": role,
         "exp": datetime.now(timezone.utc) + timedelta(hours=2)},
        JWT_SECRET, algorithm="HS256")


def seed():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    now = datetime.now(timezone.utc).isoformat()
    db.drivers.delete_one({"id": DRIVER_ID})
    db.drivers.insert_one({
        "id": DRIVER_ID,
        "first_name": "Iter22",
        "last_name": "Driver",
        "email": "test-iter22-driver@metro-taxi.com",
        "phone": "+33600000022",
        "password": "x",
        "role": "driver",
        "is_active": True,
        "is_validated": True,
        "email_verified": True,
        "vehicle_plate": "TT-022-TT",
        "vehicle_type": "berline",
        "seats": 4,
        "vtc_license": "VTC-ITER22",
        "created_at": now,
    })
    db.users.delete_one({"id": USER_ID})
    db.users.insert_one({
        "id": USER_ID,
        "first_name": "Iter22",
        "last_name": "User",
        "email": "test-iter22-user@metro-taxi.com",
        "phone": "+33600000122",
        "password": "x",
        "role": "user",
        "email_verified": True,
        "subscription_active": True,
        "subscription_expires": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "created_at": now,
        "street_address": "1 rue Test",
        "postal_code": "93200",
        "city": "Saint-Denis",
        "date_of_birth": "1990-01-01",
    })
    out = {
        "driver_token": make_token(DRIVER_ID, "driver"),
        "user_token": make_token(USER_ID, "user"),
        "driver_id": DRIVER_ID,
        "user_id": USER_ID,
    }
    client.close()
    print(json.dumps(out))


def cleanup():
    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    db.drivers.delete_one({"id": DRIVER_ID})
    db.users.delete_one({"id": USER_ID})
    client.close()
    print(json.dumps({"cleaned": True}))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        cleanup()
    else:
        seed()
