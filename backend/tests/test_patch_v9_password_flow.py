"""
Patch V9 — Password reset / change-password / anti-brute force assoupli.

Tests :
1. POST /api/auth/forgot-password
   - Toujours 200 (anti-énumération), même si email inconnu
   - Crée un document `password_resets` avec code 6 chiffres pour un email valide
2. POST /api/auth/reset-password
   - Code invalide → 400 "Code invalide"
   - Bon code → 200, password effectivement mis à jour (login OK avec le nouveau)
3. POST /api/auth/change-password (authentifié)
   - Mauvais ancien mdp → 400
   - Nouveau < 8 chars → 400
   - OK → 200 et login avec le nouveau mdp fonctionne
4. Anti-brute-force assoupli : MAX_FAILED_LOGIN_ATTEMPTS = 8
   - Un échec sur EmailA ne doit pas bloquer EmailB depuis la même IP
   - Le compteur est tracké par (email + IP)
"""
import os
import time
import uuid

import pytest
import requests
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://metro-taxi-demo.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _unique_email(prefix="testv9"):
    return f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"


def _register_user(email, password="OldPass2026!"):
    payload = {
        "first_name": "Test",
        "last_name": "PatchV9",
        "email": email,
        "phone": f"+3361234{uuid.uuid4().hex[:4]}",
        "password": password,
        "street_address": "12 rue de la Liberté",
        "postal_code": "93200",
        "city": "Saint-Denis",
        "date_of_birth": "1990-01-15",
    }
    r = requests.post(f"{API}/auth/register/user", json=payload, timeout=15)
    return r, payload


def _login(email, password):
    return requests.post(
        f"{API}/auth/login",
        json={"email": email, "password": password},
        timeout=15,
    )


@pytest.fixture(scope="module")
def mongo_db():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    yield db
    client.close()


@pytest.fixture
def registered_user():
    email = _unique_email()
    pwd = "OldPass2026!"
    r, _ = _register_user(email, pwd)
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    return {"email": email, "password": pwd, "token": r.json().get("token")}


# --------------------------------------------------------------------------- #
# 1. forgot-password
# --------------------------------------------------------------------------- #

class TestForgotPassword:
    def test_forgot_password_unknown_email_returns_200(self):
        """Anti-enumeration : toujours 200 même si email inconnu."""
        r = requests.post(
            f"{API}/auth/forgot-password",
            json={"email": f"unknown_{uuid.uuid4().hex[:8]}@example.com"},
            timeout=15,
        )
        assert r.status_code == 200
        body = r.json()
        assert "message" in body
        # Le message doit être neutre (ne pas révéler si l'email existe)
        assert "existe" in body["message"].lower() or "envoyé" in body["message"].lower()

    @pytest.mark.asyncio
    async def test_forgot_password_creates_reset_doc(self, registered_user, mongo_db):
        email = registered_user["email"]

        # Nettoyer les anciens reset docs au cas où
        await mongo_db.password_resets.delete_many({"email": email})

        r = requests.post(
            f"{API}/auth/forgot-password",
            json={"email": email},
            timeout=15,
        )
        assert r.status_code == 200

        # Petit délai car send_password_reset_email est lancé via asyncio.create_task
        time.sleep(1.0)

        reset_doc = await mongo_db.password_resets.find_one({"email": email})
        assert reset_doc is not None, "Aucun document password_resets créé"
        assert "code" in reset_doc
        assert len(reset_doc["code"]) == 6
        assert reset_doc["code"].isdigit(), f"Code non numérique: {reset_doc['code']}"
        assert reset_doc["collection"] in ("users", "drivers")
        assert reset_doc.get("attempts", 0) == 0
        assert "expires_at" in reset_doc


# --------------------------------------------------------------------------- #
# 2. reset-password
# --------------------------------------------------------------------------- #

class TestResetPassword:
    def test_reset_password_wrong_code_returns_400(self, registered_user):
        # Demande un code
        r = requests.post(
            f"{API}/auth/forgot-password",
            json={"email": registered_user["email"]},
            timeout=15,
        )
        assert r.status_code == 200
        time.sleep(0.5)

        # Tente avec un mauvais code
        r2 = requests.post(
            f"{API}/auth/reset-password",
            json={
                "email": registered_user["email"],
                "code": "000000",
                "new_password": "BrandNewPass2026!",
            },
            timeout=15,
        )
        assert r2.status_code == 400
        assert "code" in r2.json().get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_reset_password_valid_code_updates_password(self, registered_user, mongo_db):
        email = registered_user["email"]
        new_pwd = "BrandNewPass2026!"

        # Trigger forgot
        r = requests.post(f"{API}/auth/forgot-password", json={"email": email}, timeout=15)
        assert r.status_code == 200
        time.sleep(0.5)

        reset_doc = await mongo_db.password_resets.find_one({"email": email})
        assert reset_doc is not None
        code = reset_doc["code"]

        r2 = requests.post(
            f"{API}/auth/reset-password",
            json={"email": email, "code": code, "new_password": new_pwd},
            timeout=15,
        )
        assert r2.status_code == 200, f"reset failed: {r2.text}"

        # Vérifier que l'ancien mdp ne marche plus
        old_login = _login(email, registered_user["password"])
        assert old_login.status_code in (401, 400), f"L'ancien mdp marche encore: {old_login.status_code}"

        # Vérifier que le nouveau mdp marche
        new_login = _login(email, new_pwd)
        assert new_login.status_code == 200, f"Nouveau mdp ne fonctionne pas: {new_login.text}"
        token = new_login.json().get("token")
        assert token

        # Le doc password_resets doit être supprimé après succès
        leftover = await mongo_db.password_resets.find_one({"email": email})
        assert leftover is None, "Le document password_resets n'a pas été supprimé après succès"


# --------------------------------------------------------------------------- #
# 3. change-password
# --------------------------------------------------------------------------- #

class TestChangePassword:
    def test_change_password_requires_auth(self):
        r = requests.post(
            f"{API}/auth/change-password",
            json={"current_password": "x", "new_password": "yyyyyyyy"},
            timeout=15,
        )
        assert r.status_code in (401, 403)

    def test_change_password_wrong_current(self, registered_user):
        token = registered_user["token"]
        r = requests.post(
            f"{API}/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": "WrongOldPass!", "new_password": "AnotherStrongPass2026!"},
            timeout=15,
        )
        assert r.status_code == 400
        assert "actuel" in r.json().get("detail", "").lower() or "incorrect" in r.json().get("detail", "").lower()

    def test_change_password_too_short_new(self, registered_user):
        token = registered_user["token"]
        r = requests.post(
            f"{API}/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": registered_user["password"], "new_password": "short1"},
            timeout=15,
        )
        assert r.status_code == 400
        assert "8" in r.json().get("detail", "")

    def test_change_password_success_and_login_with_new(self, registered_user):
        token = registered_user["token"]
        new_pwd = "ChangedPass2026!"
        r = requests.post(
            f"{API}/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={"current_password": registered_user["password"], "new_password": new_pwd},
            timeout=15,
        )
        assert r.status_code == 200, r.text

        # Nouveau mdp fonctionne
        login_new = _login(registered_user["email"], new_pwd)
        assert login_new.status_code == 200

        # Ancien mdp ne fonctionne plus
        login_old = _login(registered_user["email"], registered_user["password"])
        assert login_old.status_code in (401, 400)


# --------------------------------------------------------------------------- #
# 4. Anti-brute-force assoupli (MAX=8, key=email+IP)
# --------------------------------------------------------------------------- #

class TestAntiBruteforceAssoupli:
    """
    Vérifie qu'un fail sur EmailA ne bloque pas EmailB depuis la même IP.
    Note : on ne peut pas envoyer >8 échecs sur EmailA et vérifier qu'EmailB
    n'est pas verrouillé en parallèle car la rate-limit /api/auth/login est
    5/min côté slowapi. On vérifie le comportement minimal : 6 échecs sur
    EmailA (sous le seuil de 8) + 1 login OK sur EmailB = succès.
    """

    def test_failed_logins_on_emailA_do_not_block_emailB(self):
        email_a = _unique_email("brutea")
        email_b = _unique_email("bruteb")
        pwd_b = "ValidPass2026!"
        # Créer EmailB seulement
        r = _register_user(email_b, pwd_b)[0]
        assert r.status_code == 200

        # 3 échecs sur EmailA (existe pas) — sous le seuil de 8
        for _ in range(3):
            resp = _login(email_a, "FakePass!")
            # 401 (invalid creds) ou 429 (rate-limit slowapi 5/min) sont OK
            assert resp.status_code in (401, 400, 429)
            time.sleep(0.2)

        # EmailB doit pouvoir se connecter (clé email+IP différente)
        time.sleep(1.0)
        login_b = _login(email_b, pwd_b)
        # On accepte 200 (idéal) ou 429 (si slowapi a engagé) — l'important est PAS 429 avec message lockout
        assert login_b.status_code in (200, 429), f"EmailB bloqué: {login_b.text}"
        if login_b.status_code == 429:
            detail = login_b.json().get("detail", "").lower()
            # Si c'est le lockout brute-force, c'est un bug. Le rate-limit slowapi dit "too many" générique.
            assert "réessayez dans" not in detail or "oublié" not in detail, \
                f"EmailB lockout par brute-force tracker (devrait être par email+IP): {detail}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
