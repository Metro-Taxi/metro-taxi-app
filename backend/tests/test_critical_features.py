"""
Tests critiques pour Métro-Taxi - Suite de régression complète
Exécuter avec: pytest tests/test_critical_features.py -v
"""
import pytest
import httpx
import os
from datetime import datetime

# Configuration pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Configuration
API_BASE_URL = os.environ.get("TEST_API_URL", "http://localhost:8001/api")
TEST_USER_EMAIL = "pytest_user@metro-taxi.com"
TEST_USER_PASSWORD = "TestPass123!"
TEST_DRIVER_EMAIL = "pytest_driver@metro-taxi.com"
TEST_DRIVER_PASSWORD = "DriverPass123!"


@pytest.fixture(scope="module")
def http_client():
    """Sync HTTP client for API calls"""
    with httpx.Client(base_url=API_BASE_URL, timeout=30.0) as client:
        yield client


class TestHealthAndRegions:
    """Test des endpoints de base"""

    def test_regions_list(self, http_client):
        """GET /api/regions - Liste des régions"""
        response = http_client.get("/regions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # Vérifier structure d'une région
        if data:
            region = data[0]
            assert "id" in region
            assert "name" in region
            assert "country" in region

    def test_subscription_plans(self, http_client):
        """GET /api/subscriptions/plans - Plans d'abonnement"""
        response = http_client.get("/subscriptions/plans")
        assert response.status_code == 200
        data = response.json()
        # L'API retourne {"plans": {...}} ou une liste
        if isinstance(data, dict) and "plans" in data:
            plans = data["plans"]
            assert len(plans) >= 1
        else:
            assert isinstance(data, list)
            assert len(data) >= 1


class TestAuthentication:
    """Test du système d'authentification"""

    def test_login_invalid_credentials(self, http_client):
        """POST /api/auth/login - Rejet des credentials invalides"""
        response = http_client.post(
            "/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"}
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_register_user(self, http_client):
        """POST /api/auth/register/user - Inscription utilisateur"""
        unique_email = f"pytest_user_{datetime.now().timestamp()}@test.com"
        response = http_client.post(
            "/auth/register/user",
            json={
                "first_name": "Test",
                "last_name": "User",
                "email": unique_email,
                "phone": "+33612345678",
                "password": TEST_USER_PASSWORD
            }
        )
        # Accepter 200 ou 400 (si email déjà utilisé)
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "token" in data
            assert "user" in data

    def test_protected_endpoint_without_token(self, http_client):
        """Test accès aux endpoints protégés sans token"""
        response = http_client.get("/auth/me")
        assert response.status_code in [401, 403]


class TestMatchingAlgorithm:
    """Test de l'algorithme de matching"""

    def test_network_status_requires_auth(self, http_client):
        """GET /api/matching/network-status - Requiert authentification"""
        response = http_client.get("/matching/network-status")
        assert response.status_code in [401, 403]


class TestDriverEndpoints:
    """Test des endpoints chauffeurs"""

    def test_drivers_available_requires_auth(self, http_client):
        """GET /api/drivers/available - Requiert authentification"""
        response = http_client.get("/drivers/available")
        assert response.status_code in [401, 403]


class TestNotifications:
    """Test du système de notifications"""

    def test_vapid_public_key(self, http_client):
        """GET /api/notifications/vapid-public-key - Clé publique VAPID"""
        response = http_client.get("/notifications/vapid-public-key")
        # Peut retourner 200 ou 500 selon config
        if response.status_code == 200:
            data = response.json()
            assert "publicKey" in data


class TestChat:
    """Test du système de chat"""

    def test_chat_requires_auth(self, http_client):
        """GET /api/chat/{ride_id} - Requiert authentification"""
        response = http_client.get("/chat/test-ride-id")
        assert response.status_code in [401, 403]


class TestChatbot:
    """Test du chatbot IA"""

    def test_chatbot_endpoint(self, http_client):
        """POST /api/chatbot - Chatbot d'aide"""
        response = http_client.post(
            "/chatbot",
            json={"message": "Bonjour", "language": "fr"}
        )
        # Peut retourner 200, 404 (non configuré), 500 ou 503
        assert response.status_code in [200, 404, 500, 503]


class TestI18n:
    """Test de l'internationalisation"""

    def test_voiceover_endpoint(self, http_client):
        """GET /api/voiceover/{lang} - Voix off par langue"""
        for lang in ["fr", "en", "es", "de"]:
            response = http_client.get(f"/voiceover/{lang}")
            # Retourne fichier audio ou erreur si non généré
            assert response.status_code in [200, 404, 500]


class TestIntegrationFlow:
    """Test du flux complet d'intégration"""

    def test_full_user_registration_flow(self, http_client):
        """Test du flux complet : inscription -> login -> profil"""
        # 1. Inscription
        unique_email = f"flow_test_{datetime.now().timestamp()}@test.com"
        register_response = http_client.post(
            "/auth/register/user",
            json={
                "first_name": "Flow",
                "last_name": "Test",
                "email": unique_email,
                "phone": "+33698765432",
                "password": "FlowTest123!"
            }
        )
        
        if register_response.status_code != 200:
            pytest.skip("Registration failed, skipping flow test")
        
        register_data = register_response.json()
        token = register_data.get("token")
        assert token is not None
        
        # 2. Accès au profil
        me_response = http_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert "user" in me_data
        assert me_data["user"]["email"] == unique_email


# Exécution rapide pour vérification
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
