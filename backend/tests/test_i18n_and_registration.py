"""
Test suite for Métro-Taxi i18n and Registration with Email Verification
Tests:
- User registration API with email verification
- Driver registration API with email verification
- Admin login
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestUserRegistration:
    """Test user registration with email verification"""
    
    def test_user_registration_success(self):
        """Test successful user registration returns verification URL"""
        unique_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register/user", json={
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "phone": "0612345678",
            "password": "test123"
        }, headers={
            "Content-Type": "application/json",
            "Accept-Language": "fr"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        assert "verification_url" in data, "Response should contain verification_url"
        assert "message" in data, "Response should contain message"
        
        # Verify user data
        user = data["user"]
        assert user["email"] == unique_email
        assert user["first_name"] == "Test"
        assert user["last_name"] == "User"
        assert user["role"] == "user"
        assert user["email_verified"] == False
        
        print(f"SUCCESS: User registered with verification URL: {data['verification_url'][:50]}...")
    
    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email fails"""
        unique_email = f"test_dup_{uuid.uuid4().hex[:8]}@example.com"
        
        # First registration
        response1 = requests.post(f"{BASE_URL}/api/auth/register/user", json={
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "phone": "0612345678",
            "password": "test123"
        })
        assert response1.status_code == 200
        
        # Second registration with same email
        response2 = requests.post(f"{BASE_URL}/api/auth/register/user", json={
            "first_name": "Test2",
            "last_name": "User2",
            "email": unique_email,
            "phone": "0612345679",
            "password": "test456"
        })
        
        assert response2.status_code == 400, f"Expected 400 for duplicate email, got {response2.status_code}"
        print("SUCCESS: Duplicate email registration rejected")


class TestDriverRegistration:
    """Test driver registration with email verification"""
    
    def test_driver_registration_success(self):
        """Test successful driver registration returns verification URL"""
        unique_email = f"test_driver_{uuid.uuid4().hex[:8]}@example.com"
        
        response = requests.post(f"{BASE_URL}/api/auth/register/driver", json={
            "first_name": "Test",
            "last_name": "Driver",
            "email": unique_email,
            "phone": "0687654321",
            "password": "driver123",
            "vehicle_plate": f"AB-{uuid.uuid4().hex[:3].upper()}-CD",
            "vehicle_type": "berline",
            "seats": 4,
            "vtc_license": f"VTC-{uuid.uuid4().hex[:6].upper()}"
        }, headers={
            "Content-Type": "application/json",
            "Accept-Language": "en"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "driver" in data, "Response should contain driver"
        assert "verification_url" in data, "Response should contain verification_url"
        assert "message" in data, "Response should contain message"
        
        # Verify driver data
        driver = data["driver"]
        assert driver["email"] == unique_email
        assert driver["first_name"] == "Test"
        assert driver["last_name"] == "Driver"
        assert driver["role"] == "driver"
        assert driver["email_verified"] == False
        assert driver["is_validated"] == False  # Needs admin validation
        
        print(f"SUCCESS: Driver registered with verification URL: {data['verification_url'][:50]}...")


class TestAdminLogin:
    """Test admin login functionality"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@metrotaxi.fr",
            "password": "admin123"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "admin" in data, "Response should contain admin"
        
        admin = data["admin"]
        assert admin["email"] == "admin@metrotaxi.fr"
        assert admin["role"] == "admin"
        
        print("SUCCESS: Admin login successful")
        return data["token"]
    
    def test_admin_login_wrong_password(self):
        """Test admin login with wrong password fails"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@metrotaxi.fr",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("SUCCESS: Wrong password rejected")


class TestAdminEndpoints:
    """Test admin dashboard endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated requests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@metrotaxi.fr",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin login failed")
    
    def test_admin_stats(self, admin_token):
        """Test admin stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total_users" in data
        assert "total_drivers" in data
        assert "active_subscriptions" in data
        assert "active_rides" in data
        
        print(f"SUCCESS: Admin stats - Users: {data['total_users']}, Drivers: {data['total_drivers']}")
    
    def test_admin_drivers_list(self, admin_token):
        """Test admin drivers list endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/drivers", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "drivers" in data
        print(f"SUCCESS: Admin drivers list - {len(data['drivers'])} drivers")
    
    def test_admin_users_list(self, admin_token):
        """Test admin users list endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "users" in data
        print(f"SUCCESS: Admin users list - {len(data['users'])} users")
    
    def test_admin_subscriptions(self, admin_token):
        """Test admin subscriptions endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/subscriptions", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "active" in data or "expired" in data or "expiring_soon" in data
        print("SUCCESS: Admin subscriptions endpoint working")
    
    def test_admin_cards(self, admin_token):
        """Test admin virtual cards endpoint"""
        response = requests.get(f"{BASE_URL}/api/admin/cards", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "cards" in data
        print(f"SUCCESS: Admin cards list - {len(data['cards'])} cards")


class TestSubscriptionPlans:
    """Test subscription plans endpoint"""
    
    def test_get_subscription_plans(self):
        """Test getting subscription plans"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "plans" in data
        
        plans = data["plans"]
        # Plan IDs are: 24h, 1week, 1month
        assert "24h" in plans
        assert "1week" in plans
        assert "1month" in plans
        
        # Verify plan structure
        for plan_id, plan in plans.items():
            assert "name" in plan
            assert "price" in plan
            assert "duration_hours" in plan
        
        print(f"SUCCESS: Subscription plans - 24h: {plans['24h']['price']}€, 1week: {plans['1week']['price']}€, 1month: {plans['1month']['price']}€")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
