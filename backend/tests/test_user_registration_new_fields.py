"""
Test suite for user registration with new mandatory fields:
- street_address (rue)
- postal_code (code postal)
- city (ville)
- date_of_birth (date de naissance)

These fields are required for INPI/security compliance.
"""

import pytest
import requests
import os
import time

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestUserRegistrationNewFields:
    """Test user registration with new mandatory fields"""
    
    def test_successful_registration_with_all_fields(self):
        """Test that registration succeeds with all required fields"""
        timestamp = int(time.time())
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"test_reg_success_{timestamp}@test.com",
            "phone": "0612345678",
            "password": "Test123!",
            "street_address": "12 rue de la Paix",
            "postal_code": "75001",
            "city": "Paris",
            "date_of_birth": "1990-01-15"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload)
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Data assertions
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        
        user = data["user"]
        assert user["first_name"] == payload["first_name"]
        assert user["last_name"] == payload["last_name"]
        assert user["email"] == payload["email"]
        assert user["phone"] == payload["phone"]
        assert user["street_address"] == payload["street_address"]
        assert user["postal_code"] == payload["postal_code"]
        assert user["city"] == payload["city"]
        assert user["date_of_birth"] == payload["date_of_birth"]
        assert user["role"] == "user"
        assert user["subscription_active"] == False
        
        print(f"✓ Registration successful with all new fields for {payload['email']}")
    
    def test_registration_missing_street_address(self):
        """Test that registration fails when street_address is missing"""
        timestamp = int(time.time())
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"test_missing_street_{timestamp}@test.com",
            "phone": "0612345678",
            "password": "Test123!",
            # street_address is missing
            "postal_code": "75001",
            "city": "Paris",
            "date_of_birth": "1990-01-15"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload)
        
        # Should return 422 Unprocessable Entity
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        
        # Check error message mentions street_address
        data = response.json()
        assert "detail" in data
        error_fields = [err.get("loc", [])[-1] for err in data["detail"]]
        assert "street_address" in error_fields, "Error should mention street_address"
        
        print("✓ Registration correctly rejected when street_address is missing")
    
    def test_registration_missing_postal_code(self):
        """Test that registration fails when postal_code is missing"""
        timestamp = int(time.time())
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"test_missing_postal_{timestamp}@test.com",
            "phone": "0612345678",
            "password": "Test123!",
            "street_address": "12 rue de la Paix",
            # postal_code is missing
            "city": "Paris",
            "date_of_birth": "1990-01-15"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        
        data = response.json()
        error_fields = [err.get("loc", [])[-1] for err in data["detail"]]
        assert "postal_code" in error_fields, "Error should mention postal_code"
        
        print("✓ Registration correctly rejected when postal_code is missing")
    
    def test_registration_missing_city(self):
        """Test that registration fails when city is missing"""
        timestamp = int(time.time())
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"test_missing_city_{timestamp}@test.com",
            "phone": "0612345678",
            "password": "Test123!",
            "street_address": "12 rue de la Paix",
            "postal_code": "75001",
            # city is missing
            "date_of_birth": "1990-01-15"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        
        data = response.json()
        error_fields = [err.get("loc", [])[-1] for err in data["detail"]]
        assert "city" in error_fields, "Error should mention city"
        
        print("✓ Registration correctly rejected when city is missing")
    
    def test_registration_missing_date_of_birth(self):
        """Test that registration fails when date_of_birth is missing"""
        timestamp = int(time.time())
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"test_missing_dob_{timestamp}@test.com",
            "phone": "0612345678",
            "password": "Test123!",
            "street_address": "12 rue de la Paix",
            "postal_code": "75001",
            "city": "Paris"
            # date_of_birth is missing
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        
        data = response.json()
        error_fields = [err.get("loc", [])[-1] for err in data["detail"]]
        assert "date_of_birth" in error_fields, "Error should mention date_of_birth"
        
        print("✓ Registration correctly rejected when date_of_birth is missing")
    
    def test_registration_missing_all_new_fields(self):
        """Test that registration fails when all new fields are missing"""
        timestamp = int(time.time())
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"test_missing_all_{timestamp}@test.com",
            "phone": "0612345678",
            "password": "Test123!"
            # All new fields missing: street_address, postal_code, city, date_of_birth
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload)
        
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        
        data = response.json()
        error_fields = [err.get("loc", [])[-1] for err in data["detail"]]
        
        # All 4 new fields should be mentioned in errors
        assert "street_address" in error_fields, "Error should mention street_address"
        assert "postal_code" in error_fields, "Error should mention postal_code"
        assert "city" in error_fields, "Error should mention city"
        assert "date_of_birth" in error_fields, "Error should mention date_of_birth"
        
        print("✓ Registration correctly rejected when all new fields are missing")
    
    def test_duplicate_email_rejected(self):
        """Test that duplicate email registration is rejected"""
        timestamp = int(time.time())
        email = f"test_duplicate_{timestamp}@test.com"
        
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "phone": "0612345678",
            "password": "Test123!",
            "street_address": "12 rue de la Paix",
            "postal_code": "75001",
            "city": "Paris",
            "date_of_birth": "1990-01-15"
        }
        
        # First registration should succeed
        response1 = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload)
        assert response1.status_code == 200, f"First registration should succeed: {response1.text}"
        
        # Second registration with same email should fail
        response2 = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload)
        assert response2.status_code == 400, f"Expected 400 for duplicate email, got {response2.status_code}"
        
        data = response2.json()
        assert "déjà utilisé" in data.get("detail", "").lower() or "already" in data.get("detail", "").lower()
        
        print("✓ Duplicate email registration correctly rejected")


class TestUserDataPersistence:
    """Test that new fields are correctly persisted and retrieved"""
    
    def test_user_data_persisted_after_registration(self):
        """Test that user data with new fields is persisted in database"""
        timestamp = int(time.time())
        payload = {
            "first_name": "Persistence",
            "last_name": "Test",
            "email": f"test_persist_{timestamp}@test.com",
            "phone": "0698765432",
            "password": "Test123!",
            "street_address": "25 avenue des Champs-Élysées",
            "postal_code": "75008",
            "city": "Paris",
            "date_of_birth": "1985-06-20"
        }
        
        # Register user
        response = requests.post(f"{BASE_URL}/api/auth/register/user", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        token = data["token"]
        
        # Get user profile using token
        headers = {"Authorization": f"Bearer {token}"}
        me_response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        assert me_response.status_code == 200, f"Failed to get user profile: {me_response.text}"
        
        me_data = me_response.json()
        user = me_data.get("user", {})
        
        # Verify all new fields are present
        assert user.get("street_address") == payload["street_address"], f"street_address not persisted: got {user.get('street_address')}"
        assert user.get("postal_code") == payload["postal_code"], f"postal_code not persisted: got {user.get('postal_code')}"
        assert user.get("city") == payload["city"], f"city not persisted: got {user.get('city')}"
        assert user.get("date_of_birth") == payload["date_of_birth"], f"date_of_birth not persisted: got {user.get('date_of_birth')}"
        
        print("✓ All new fields correctly persisted and retrieved")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
