"""
Regression tests for Métro-Taxi application - Iteration 9
Tests API endpoints and core functionality after audio button bug fix
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasicEndpoints:
    """Test basic health and public endpoints"""
    
    def test_regions_endpoint(self):
        """Test that /api/regions returns the 3 regions"""
        response = requests.get(f"{BASE_URL}/api/regions")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3, f"Expected 3 regions, got {len(data)}"
        
        # Verify region IDs
        region_ids = [r['id'] for r in data]
        assert 'paris' in region_ids, "Paris region missing"
        assert 'lyon' in region_ids, "Lyon region missing"
        assert 'london' in region_ids, "London region missing"
        
        # Verify Paris is active
        paris = next(r for r in data if r['id'] == 'paris')
        assert paris['is_active'] == True, "Paris should be active"
        
        print(f"✅ Regions endpoint: {len(data)} regions returned")
        print(f"   Region IDs: {region_ids}")
    
    def test_active_regions_endpoint(self):
        """Test that /api/regions/active returns only active regions"""
        response = requests.get(f"{BASE_URL}/api/regions/active")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # All returned regions should be active
        for region in data:
            assert region['is_active'] == True, f"Region {region['id']} should be active"
        
        print(f"✅ Active regions endpoint: {len(data)} active regions")
    
    def test_subscription_plans_endpoint(self):
        """Test that /api/subscriptions/plans returns the plans"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        
        data = response.json()
        assert 'plans' in data
        
        plans = data['plans']
        assert '24h' in plans, "24h plan missing"
        assert '1week' in plans, "1week plan missing"
        assert '1month' in plans, "1month plan missing"
        
        # Verify plan prices
        assert plans['24h']['price'] == 6.99
        assert plans['1week']['price'] == 16.99
        assert plans['1month']['price'] == 53.99
        
        print(f"✅ Subscription plans endpoint: {len(plans)} plans returned")
        print(f"   Plans: {list(plans.keys())}")


class TestRegionDetails:
    """Test region-specific endpoints"""
    
    def test_get_paris_region(self):
        """Test getting Paris region details"""
        response = requests.get(f"{BASE_URL}/api/regions/paris")
        assert response.status_code == 200
        
        data = response.json()
        assert data['id'] == 'paris'
        assert data['name'] == 'Île-de-France'
        assert data['country'] == 'FR'
        assert data['currency'] == 'EUR'
        assert data['language'] == 'fr'
        assert 'bounds' in data
        
        print(f"✅ Paris region details: {data['name']}")
    
    def test_get_nonexistent_region(self):
        """Test getting a non-existent region returns 404"""
        response = requests.get(f"{BASE_URL}/api/regions/nonexistent")
        assert response.status_code == 404
        print("✅ Non-existent region returns 404")


class TestAudioEndpoints:
    """Test audio file endpoints (voiceover)"""
    
    def test_french_voiceover_exists(self):
        """Test that French voiceover audio file is accessible"""
        response = requests.head(f"{BASE_URL}/audio/voiceover/voiceover_fr.mp3")
        assert response.status_code == 200, f"French voiceover not found: {response.status_code}"
        print("✅ French voiceover audio accessible")
    
    def test_english_voiceover_exists(self):
        """Test that English voiceover audio file is accessible"""
        response = requests.head(f"{BASE_URL}/audio/voiceover/voiceover_en.mp3")
        assert response.status_code == 200, f"English voiceover not found: {response.status_code}"
        print("✅ English voiceover audio accessible")


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_login_with_invalid_credentials(self):
        """Test login with invalid credentials returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        print("✅ Invalid login returns 401")
    
    def test_login_with_admin_credentials(self):
        """Test login with admin credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@metrotaxi.fr", "password": "admin123"}
        )
        # Admin might exist or not, just check it doesn't crash
        assert response.status_code in [200, 401]
        print(f"✅ Admin login endpoint: {response.status_code}")


class TestDriverEndpoints:
    """Test driver-related endpoints"""
    
    def test_available_drivers_requires_auth(self):
        """Test that available drivers endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/drivers/available")
        # This endpoint requires authentication
        assert response.status_code == 401
        print("✅ Available drivers endpoint requires auth (401)")


class TestStaticAssets:
    """Test static asset endpoints"""
    
    def test_frontend_loads(self):
        """Test that frontend loads correctly"""
        response = requests.get(BASE_URL)
        assert response.status_code == 200
        assert 'text/html' in response.headers.get('content-type', '')
        print("✅ Frontend loads correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
