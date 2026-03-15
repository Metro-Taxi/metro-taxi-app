"""
Test suite for Iteration 6 features:
- Driver earnings API (GET /api/drivers/earnings)
- Admin driver earnings API (GET /api/admin/driver-earnings)
- Admin process payouts API (POST /api/admin/process-payouts)
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@metrotaxi.fr"
ADMIN_PASSWORD = "admin123"
DRIVER_EMAIL = "jean.dupont.test@example.com"
DRIVER_PASSWORD = "test123456"


class TestDriverEarningsAPI:
    """Test driver earnings endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def get_driver_token(self):
        """Get driver authentication token - create driver if needed"""
        # First try to login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": DRIVER_EMAIL,
            "password": DRIVER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        
        # If login fails, create a new test driver
        test_driver_email = f"TEST_driver_{uuid.uuid4().hex[:8]}@example.com"
        register_response = self.session.post(f"{BASE_URL}/api/auth/register/driver", json={
            "first_name": "Test",
            "last_name": "Driver",
            "email": test_driver_email,
            "phone": "+33612345678",
            "password": "test123456",
            "vehicle_plate": "AB-123-CD",
            "vehicle_type": "berline",
            "seats": 4,
            "vtc_license": "VTC-12345",
            "iban": "FR7612345678901234567890123",
            "bic": "BNPAFRPP"
        })
        if register_response.status_code == 200:
            return register_response.json().get("token")
        return None
    
    def test_driver_earnings_endpoint_exists(self):
        """Test that GET /api/drivers/earnings endpoint exists"""
        token = self.get_driver_token()
        if not token:
            pytest.skip("Could not get driver token")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/drivers/earnings")
        
        # Should return 200 (success) or 403 (forbidden for non-drivers)
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            # Verify response structure
            assert "current_month" in data, "Missing 'current_month' in response"
            assert "totals" in data, "Missing 'totals' in response"
            assert "rate_per_km" in data, "Missing 'rate_per_km' in response"
            assert "payout_day" in data, "Missing 'payout_day' in response"
            
            # Verify rate_per_km is 1.50
            assert data["rate_per_km"] == 1.50, f"Expected rate_per_km=1.50, got {data['rate_per_km']}"
            
            # Verify payout_day is 10
            assert data["payout_day"] == 10, f"Expected payout_day=10, got {data['payout_day']}"
            
            print(f"SUCCESS: Driver earnings endpoint returns correct structure")
            print(f"  - rate_per_km: {data['rate_per_km']}€")
            print(f"  - payout_day: {data['payout_day']}")
    
    def test_driver_earnings_unauthorized(self):
        """Test that GET /api/drivers/earnings requires authentication"""
        response = self.session.get(f"{BASE_URL}/api/drivers/earnings")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Driver earnings endpoint requires authentication")
    
    def test_driver_earnings_response_structure(self):
        """Test driver earnings response has correct structure"""
        token = self.get_driver_token()
        if not token:
            pytest.skip("Could not get driver token")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/drivers/earnings")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check current_month structure
            current_month = data.get("current_month", {})
            assert "month" in current_month, "Missing 'month' in current_month"
            assert "total_km" in current_month, "Missing 'total_km' in current_month"
            assert "total_revenue" in current_month, "Missing 'total_revenue' in current_month"
            assert "rides_count" in current_month, "Missing 'rides_count' in current_month"
            
            # Check totals structure
            totals = data.get("totals", {})
            assert "total_km" in totals, "Missing 'total_km' in totals"
            assert "total_revenue" in totals, "Missing 'total_revenue' in totals"
            assert "total_rides" in totals, "Missing 'total_rides' in totals"
            
            print("SUCCESS: Driver earnings response has correct structure")
            print(f"  - Current month: {current_month.get('month')}")
            print(f"  - Total km: {totals.get('total_km')}")
            print(f"  - Total revenue: {totals.get('total_revenue')}€")


class TestAdminDriverEarningsAPI:
    """Test admin driver earnings endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_admin_driver_earnings_endpoint_exists(self):
        """Test that GET /api/admin/driver-earnings endpoint exists"""
        token = self.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/admin/driver-earnings")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify response structure (actual API response)
        assert "current_month" in data, "Missing 'current_month' in response"
        assert "payout_day" in data, "Missing 'payout_day' in response"
        assert "rate_per_km" in data, "Missing 'rate_per_km' in response"
        assert "total_pending" in data, "Missing 'total_pending' in response"
        assert "drivers_count" in data, "Missing 'drivers_count' in response"
        assert "earnings" in data, "Missing 'earnings' in response"
        
        # Verify rate_per_km is 1.50
        assert data["rate_per_km"] == 1.50, f"Expected rate_per_km=1.50, got {data['rate_per_km']}"
        
        # Verify payout_day is 10
        assert data["payout_day"] == 10, f"Expected payout_day=10, got {data['payout_day']}"
        
        print("SUCCESS: Admin driver earnings endpoint returns correct structure")
        print(f"  - Current month: {data.get('current_month')}")
        print(f"  - Total pending: {data.get('total_pending')}€")
        print(f"  - Drivers count: {data.get('drivers_count')}")
    
    def test_admin_driver_earnings_unauthorized(self):
        """Test that GET /api/admin/driver-earnings requires admin authentication"""
        response = self.session.get(f"{BASE_URL}/api/admin/driver-earnings")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Admin driver earnings endpoint requires authentication")
    
    def test_admin_driver_earnings_non_admin_forbidden(self):
        """Test that non-admin users cannot access admin driver earnings"""
        # Create a test driver
        test_email = f"TEST_driver_{uuid.uuid4().hex[:8]}@example.com"
        register_response = self.session.post(f"{BASE_URL}/api/auth/register/driver", json={
            "first_name": "Test",
            "last_name": "Driver",
            "email": test_email,
            "phone": "+33612345678",
            "password": "test123456",
            "vehicle_plate": "AB-123-CD",
            "vehicle_type": "berline",
            "seats": 4,
            "vtc_license": "VTC-12345"
        })
        
        if register_response.status_code == 200:
            driver_token = register_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {driver_token}"})
            response = self.session.get(f"{BASE_URL}/api/admin/driver-earnings")
            assert response.status_code == 403, f"Expected 403, got {response.status_code}"
            print("SUCCESS: Non-admin users cannot access admin driver earnings")
        else:
            pytest.skip("Could not create test driver")


class TestAdminProcessPayoutsAPI:
    """Test admin process payouts endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_admin_process_payouts_endpoint_exists(self):
        """Test that POST /api/admin/process-payouts endpoint exists"""
        token = self.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.post(f"{BASE_URL}/api/admin/process-payouts")
        
        # Should return 200 (success)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        # Verify response structure (actual API response)
        assert "processed_count" in data, "Missing 'processed_count' in response"
        assert "errors_count" in data, "Missing 'errors_count' in response"
        assert "total_amount" in data, "Missing 'total_amount' in response"
        assert "processed" in data, "Missing 'processed' in response"
        assert "errors" in data, "Missing 'errors' in response"
        
        print("SUCCESS: Admin process payouts endpoint returns correct structure")
        print(f"  - Processed count: {data.get('processed_count')}")
        print(f"  - Errors count: {data.get('errors_count')}")
        print(f"  - Total amount: {data.get('total_amount')}€")
    
    def test_admin_process_payouts_unauthorized(self):
        """Test that POST /api/admin/process-payouts requires admin authentication"""
        response = self.session.post(f"{BASE_URL}/api/admin/process-payouts")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Admin process payouts endpoint requires authentication")
    
    def test_admin_process_payouts_non_admin_forbidden(self):
        """Test that non-admin users cannot process payouts"""
        # Create a test driver
        test_email = f"TEST_driver_{uuid.uuid4().hex[:8]}@example.com"
        register_response = self.session.post(f"{BASE_URL}/api/auth/register/driver", json={
            "first_name": "Test",
            "last_name": "Driver",
            "email": test_email,
            "phone": "+33612345678",
            "password": "test123456",
            "vehicle_plate": "AB-123-CD",
            "vehicle_type": "berline",
            "seats": 4,
            "vtc_license": "VTC-12345"
        })
        
        if register_response.status_code == 200:
            driver_token = register_response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {driver_token}"})
            response = self.session.post(f"{BASE_URL}/api/admin/process-payouts")
            assert response.status_code == 403, f"Expected 403, got {response.status_code}"
            print("SUCCESS: Non-admin users cannot process payouts")
        else:
            pytest.skip("Could not create test driver")


class TestDriverRateConfiguration:
    """Test driver rate configuration (1.50€/km)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_admin_token(self):
        """Get admin authentication token"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_driver_rate_is_1_50_per_km(self):
        """Verify driver rate is configured at 1.50€/km"""
        token = self.get_admin_token()
        if not token:
            pytest.skip("Could not get admin token")
        
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        response = self.session.get(f"{BASE_URL}/api/admin/driver-earnings")
        
        if response.status_code == 200:
            data = response.json()
            rate = data.get("rate_per_km")
            assert rate == 1.50, f"Expected rate_per_km=1.50, got {rate}"
            print(f"SUCCESS: Driver rate is correctly configured at {rate}€/km")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
