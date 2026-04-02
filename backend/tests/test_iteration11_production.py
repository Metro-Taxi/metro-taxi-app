"""
Production validation tests for Métro-Taxi - Iteration 11
Tests all critical features before production deployment:
- Landing page and audio
- User/Driver authentication
- Regions API
- Matching algorithm with 3 active drivers
- Network status
- Help center
- Internationalization
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
USER_EMAIL = "testeur@metro-taxi.com"
USER_PASSWORD = "Test123!"
DRIVER_EMAIL = "pierre.chauffeur@test.com"
DRIVER_PASSWORD = "Chauffeur123!"
ADMIN_EMAIL = "admin@metrotaxi.fr"
ADMIN_PASSWORD = "admin123"


class TestLandingAndPublicEndpoints:
    """Test public endpoints accessible without authentication"""
    
    def test_frontend_loads(self):
        """Test that frontend loads correctly"""
        response = requests.get(BASE_URL)
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type', '')
        print("✅ Frontend loads correctly")
    
    def test_regions_returns_3_regions(self):
        """Test that /api/regions returns exactly 3 regions"""
        response = requests.get(f"{BASE_URL}/api/regions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3, f"Expected 3 regions, got {len(data)}"
        
        region_ids = [r['id'] for r in data]
        assert 'paris' in region_ids
        assert 'lyon' in region_ids
        assert 'london' in region_ids
        
        print(f"✅ Regions API: {len(data)} regions (paris, lyon, london)")
    
    def test_paris_region_is_active(self):
        """Test that Paris region is active"""
        response = requests.get(f"{BASE_URL}/api/regions/paris")
        assert response.status_code == 200
        
        data = response.json()
        assert data['is_active'] == True
        assert data['name'] == 'Île-de-France'
        assert data['currency'] == 'EUR'
        
        print(f"✅ Paris region active with {data.get('driver_count', 0)} drivers")
    
    def test_subscription_plans_available(self):
        """Test subscription plans endpoint"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        
        data = response.json()
        assert 'plans' in data
        plans = data['plans']
        
        assert '24h' in plans
        assert '1week' in plans
        assert '1month' in plans
        
        # Verify prices
        assert plans['24h']['price'] == 6.99
        assert plans['1week']['price'] == 16.99
        assert plans['1month']['price'] == 53.99
        
        print("✅ Subscription plans: 24h (€6.99), 1week (€16.99), 1month (€53.99)")


class TestAudioVoiceover:
    """Test audio voiceover files for landing page"""
    
    def test_french_voiceover(self):
        """Test French voiceover audio file"""
        response = requests.head(f"{BASE_URL}/audio/voiceover/voiceover_fr.mp3")
        assert response.status_code == 200
        print("✅ French voiceover audio accessible")
    
    def test_english_voiceover(self):
        """Test English voiceover audio file"""
        response = requests.head(f"{BASE_URL}/audio/voiceover/voiceover_en.mp3")
        assert response.status_code == 200
        print("✅ English voiceover audio accessible")


class TestUserAuthentication:
    """Test user login and authentication"""
    
    def test_user_login_success(self):
        """Test user login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": USER_EMAIL, "password": USER_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'token' in data
        assert 'user' in data
        assert data['user']['email'] == USER_EMAIL
        assert data['user']['subscription_active'] == True
        
        print(f"✅ User login successful: {data['user']['first_name']} (subscription active)")
    
    def test_user_login_invalid_credentials(self):
        """Test user login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        print("✅ Invalid user login returns 401")


class TestDriverAuthentication:
    """Test driver login and authentication"""
    
    def test_driver_login_pierre(self):
        """Test driver login for Pierre"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": DRIVER_EMAIL, "password": DRIVER_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'token' in data
        assert 'driver' in data
        assert data['driver']['first_name'] == 'Pierre'
        assert data['driver']['is_active'] == True
        assert data['driver']['is_validated'] == True
        
        print(f"✅ Driver Pierre login: active={data['driver']['is_active']}, validated={data['driver']['is_validated']}")
    
    def test_driver_login_marie(self):
        """Test driver login for Marie"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "marie.chauffeur@test.com", "password": DRIVER_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['driver']['first_name'] == 'Marie'
        assert data['driver']['is_active'] == True
        
        print(f"✅ Driver Marie login: active={data['driver']['is_active']}")
    
    def test_driver_login_jean(self):
        """Test driver login for Jean"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "jean.chauffeur@test.com", "password": DRIVER_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['driver']['first_name'] == 'Jean'
        assert data['driver']['is_active'] == True
        
        print(f"✅ Driver Jean login: active={data['driver']['is_active']}")


class TestMatchingAlgorithm:
    """Test matching algorithm with authenticated user"""
    
    @pytest.fixture
    def user_token(self):
        """Get user authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": USER_EMAIL, "password": USER_PASSWORD}
        )
        if response.status_code == 200:
            return response.json()['token']
        pytest.skip("User authentication failed")
    
    def test_find_drivers_returns_3_active(self, user_token):
        """Test that find-drivers returns 3 active drivers"""
        response = requests.post(
            f"{BASE_URL}/api/matching/find-drivers",
            json={
                "user_lat": 48.8566,
                "user_lng": 2.3522,
                "dest_lat": 48.8738,
                "dest_lng": 2.295
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert 'drivers' in data
        drivers = data['drivers']
        
        # Should have 3 active drivers
        assert len(drivers) == 3, f"Expected 3 drivers, got {len(drivers)}"
        
        # Verify driver names
        driver_names = [d['first_name'] for d in drivers]
        assert 'Pierre' in driver_names
        assert 'Marie' in driver_names
        assert 'Jean' in driver_names
        
        # Verify matching scores
        for driver in drivers:
            assert 'matching' in driver
            assert 'score' in driver['matching']
            assert driver['matching']['score'] > 0
        
        print(f"✅ Find drivers: {len(drivers)} drivers found")
        for d in drivers:
            print(f"   - {d['first_name']}: score={d['matching']['score']}, seats={d['available_seats']}")
    
    def test_network_status_shows_3_vehicles(self, user_token):
        """Test network status shows 3 active vehicles"""
        response = requests.get(
            f"{BASE_URL}/api/matching/network-status",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data['network_status'] == 'active'
        assert data['active_vehicles'] == 3
        assert data['total_available_seats'] >= 10  # Pierre(3) + Marie(4) + Jean(6) = 13
        
        print(f"✅ Network status: {data['active_vehicles']} vehicles, {data['total_available_seats']} seats")


class TestHelpCenter:
    """Test help center chatbot endpoint"""
    
    def test_chatbot_endpoint_exists(self):
        """Test that chatbot endpoint exists (requires auth)"""
        response = requests.post(
            f"{BASE_URL}/api/help/chat",
            json={"message": "Comment fonctionne l'abonnement?"}
        )
        # Should require auth or return response
        assert response.status_code in [200, 401, 422]
        print(f"✅ Help chatbot endpoint: status {response.status_code}")


class TestInternationalization:
    """Test i18n support"""
    
    def test_frontend_loads_with_french(self):
        """Test frontend loads with French language"""
        response = requests.get(
            BASE_URL,
            headers={"Accept-Language": "fr-FR"}
        )
        assert response.status_code == 200
        print("✅ Frontend loads with French language header")
    
    def test_frontend_loads_with_english(self):
        """Test frontend loads with English language"""
        response = requests.get(
            BASE_URL,
            headers={"Accept-Language": "en-US"}
        )
        assert response.status_code == 200
        print("✅ Frontend loads with English language header")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
