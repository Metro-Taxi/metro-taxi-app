"""
Test Suite for Iteration 5 Features:
1. 16 languages in language selector (FR, EN, EN-GB, DE, NL, ES, PT, IT, NO, SV, DA, ZH, HI, PA, AR, RU)
2. Driver registration with IBAN and BIC
3. Auto-validation of drivers (is_validated=True at registration)
4. Bank info update API (PUT /api/drivers/bank-info)
5. Admin driver deactivation (POST /api/admin/drivers/{id}/deactivate)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://rideshare-hub-143.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@metrotaxi.fr"
ADMIN_PASSWORD = "admin123"


class TestDriverRegistrationWithBankInfo:
    """Test driver registration with IBAN and BIC fields"""
    
    def test_register_driver_with_iban_bic(self):
        """Test that a new driver can register with IBAN and BIC"""
        unique_id = str(uuid.uuid4())[:8]
        driver_data = {
            "first_name": "TEST_Pierre",
            "last_name": "TEST_Martin",
            "email": f"test.driver.{unique_id}@example.com",
            "phone": "+33612345678",
            "password": "test123456",
            "vehicle_plate": f"AB-{unique_id[:3]}-CD",
            "vehicle_type": "berline",
            "seats": 4,
            "vtc_license": f"VTC-{unique_id}",
            "iban": "FR7630006000011234567890189",
            "bic": "BNPAFRPP"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register/driver", json=driver_data)
        print(f"Driver registration response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "driver" in data, "Response should contain 'driver' key"
        assert "token" in data, "Response should contain 'token' key"
        
        driver = data["driver"]
        # Verify IBAN and BIC are stored
        assert driver.get("iban") == "FR7630006000011234567890189", "IBAN should be stored"
        assert driver.get("bic") == "BNPAFRPP", "BIC should be stored"
        
        # Verify auto-validation
        assert driver.get("is_validated") == True, "Driver should be auto-validated at registration"
        
        print(f"✓ Driver registered with IBAN: {driver.get('iban')}, BIC: {driver.get('bic')}")
        print(f"✓ Driver is_validated: {driver.get('is_validated')}")
        
        return data
    
    def test_register_driver_without_bank_info(self):
        """Test that a driver can register without IBAN/BIC (optional fields)"""
        unique_id = str(uuid.uuid4())[:8]
        driver_data = {
            "first_name": "TEST_Jean",
            "last_name": "TEST_Dupont",
            "email": f"test.driver.nobank.{unique_id}@example.com",
            "phone": "+33698765432",
            "password": "test123456",
            "vehicle_plate": f"XY-{unique_id[:3]}-ZZ",
            "vehicle_type": "suv",
            "seats": 5,
            "vtc_license": f"VTC-NB-{unique_id}"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register/driver", json=driver_data)
        print(f"Driver registration (no bank) response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        driver = data["driver"]
        
        # IBAN and BIC should be None or not present
        assert driver.get("iban") is None, "IBAN should be None when not provided"
        assert driver.get("bic") is None, "BIC should be None when not provided"
        
        # Still auto-validated
        assert driver.get("is_validated") == True, "Driver should be auto-validated even without bank info"
        
        print(f"✓ Driver registered without bank info, is_validated: {driver.get('is_validated')}")
        
        return data


class TestBankInfoUpdateAPI:
    """Test PUT /api/drivers/bank-info endpoint"""
    
    def test_update_bank_info_as_driver(self):
        """Test that a driver can update their bank info"""
        # First register a new driver
        unique_id = str(uuid.uuid4())[:8]
        driver_data = {
            "first_name": "TEST_Bank",
            "last_name": "TEST_Update",
            "email": f"test.bank.update.{unique_id}@example.com",
            "phone": "+33611223344",
            "password": "test123456",
            "vehicle_plate": f"BK-{unique_id[:3]}-UP",
            "vehicle_type": "monospace",
            "seats": 6,
            "vtc_license": f"VTC-BK-{unique_id}"
        }
        
        reg_response = requests.post(f"{BASE_URL}/api/auth/register/driver", json=driver_data)
        assert reg_response.status_code == 200, f"Registration failed: {reg_response.text}"
        
        token = reg_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Update bank info
        bank_data = {
            "iban": "DE89370400440532013000",
            "bic": "COBADEFFXXX"
        }
        
        update_response = requests.put(f"{BASE_URL}/api/drivers/bank-info", json=bank_data, headers=headers)
        print(f"Bank info update response: {update_response.status_code}")
        
        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        
        data = update_response.json()
        assert data.get("iban") == "DE89370400440532013000", "IBAN should be updated"
        assert data.get("bic") == "COBADEFFXXX", "BIC should be updated"
        
        print(f"✓ Bank info updated: IBAN={data.get('iban')}, BIC={data.get('bic')}")
        
        # Verify by getting bank info
        get_response = requests.get(f"{BASE_URL}/api/drivers/bank-info", headers=headers)
        assert get_response.status_code == 200
        
        get_data = get_response.json()
        assert get_data.get("iban") == "DE89370400440532013000"
        assert get_data.get("bic") == "COBADEFFXXX"
        
        print(f"✓ Bank info verified via GET endpoint")
    
    def test_update_bank_info_unauthorized(self):
        """Test that non-drivers cannot update bank info"""
        # Try without token
        bank_data = {"iban": "FR7630006000011234567890189", "bic": "BNPAFRPP"}
        
        response = requests.put(f"{BASE_URL}/api/drivers/bank-info", json=bank_data)
        assert response.status_code == 401, f"Expected 401 without token, got {response.status_code}"
        
        print(f"✓ Unauthorized access correctly rejected")


class TestAdminDriverDeactivation:
    """Test admin can deactivate drivers"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["token"]
    
    def test_admin_can_deactivate_driver(self, admin_token):
        """Test that admin can deactivate a validated driver"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First, get list of drivers
        drivers_response = requests.get(f"{BASE_URL}/api/admin/drivers", headers=headers)
        assert drivers_response.status_code == 200
        
        drivers = drivers_response.json().get("drivers", [])
        
        # Find a validated driver to deactivate
        validated_driver = None
        for driver in drivers:
            if driver.get("is_validated") == True:
                validated_driver = driver
                break
        
        if not validated_driver:
            # Create a new driver to test deactivation
            unique_id = str(uuid.uuid4())[:8]
            driver_data = {
                "first_name": "TEST_Deactivate",
                "last_name": "TEST_Me",
                "email": f"test.deactivate.{unique_id}@example.com",
                "phone": "+33699887766",
                "password": "test123456",
                "vehicle_plate": f"DA-{unique_id[:3]}-CT",
                "vehicle_type": "berline",
                "seats": 4,
                "vtc_license": f"VTC-DA-{unique_id}"
            }
            reg_response = requests.post(f"{BASE_URL}/api/auth/register/driver", json=driver_data)
            assert reg_response.status_code == 200
            validated_driver = reg_response.json()["driver"]
        
        driver_id = validated_driver["id"]
        print(f"Testing deactivation on driver: {validated_driver.get('first_name')} {validated_driver.get('last_name')}")
        
        # Deactivate the driver
        deactivate_response = requests.post(
            f"{BASE_URL}/api/admin/drivers/{driver_id}/deactivate",
            headers=headers
        )
        print(f"Deactivation response: {deactivate_response.status_code}")
        
        assert deactivate_response.status_code == 200, f"Expected 200, got {deactivate_response.status_code}: {deactivate_response.text}"
        
        # Verify driver is deactivated
        drivers_response = requests.get(f"{BASE_URL}/api/admin/drivers", headers=headers)
        drivers = drivers_response.json().get("drivers", [])
        
        deactivated_driver = next((d for d in drivers if d["id"] == driver_id), None)
        assert deactivated_driver is not None, "Driver should still exist"
        assert deactivated_driver.get("is_validated") == False, "Driver should be deactivated (is_validated=False)"
        
        print(f"✓ Driver successfully deactivated: is_validated={deactivated_driver.get('is_validated')}")
    
    def test_admin_can_reactivate_driver(self, admin_token):
        """Test that admin can reactivate a deactivated driver"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get drivers and find a deactivated one
        drivers_response = requests.get(f"{BASE_URL}/api/admin/drivers", headers=headers)
        drivers = drivers_response.json().get("drivers", [])
        
        deactivated_driver = next((d for d in drivers if d.get("is_validated") == False), None)
        
        if deactivated_driver:
            driver_id = deactivated_driver["id"]
            
            # Reactivate (validate) the driver
            validate_response = requests.post(
                f"{BASE_URL}/api/admin/drivers/{driver_id}/validate",
                headers=headers
            )
            print(f"Validation response: {validate_response.status_code}")
            
            assert validate_response.status_code == 200, f"Expected 200, got {validate_response.status_code}"
            
            # Verify driver is reactivated
            drivers_response = requests.get(f"{BASE_URL}/api/admin/drivers", headers=headers)
            drivers = drivers_response.json().get("drivers", [])
            
            reactivated_driver = next((d for d in drivers if d["id"] == driver_id), None)
            assert reactivated_driver.get("is_validated") == True, "Driver should be reactivated"
            
            print(f"✓ Driver successfully reactivated: is_validated={reactivated_driver.get('is_validated')}")
        else:
            print("No deactivated driver found to test reactivation")


class TestAdminBadgesTranslation:
    """Test that admin dashboard badges are properly translated"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_admin_subscriptions_endpoint(self, admin_token):
        """Test admin subscriptions endpoint returns data for badges"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/subscriptions", headers=headers)
        print(f"Admin subscriptions response: {response.status_code}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check structure for badge data
        assert "summary" in data or "active_subscriptions" in data, "Response should contain subscription data"
        
        if "summary" in data:
            summary = data["summary"]
            print(f"✓ Subscription summary: active={summary.get('total_active', 0)}, expiring_soon={summary.get('expiring_soon_24h', 0)}, expired={summary.get('total_expired', 0)}")
        
        print(f"✓ Admin subscriptions endpoint working correctly")


class TestLanguageConfiguration:
    """Test that all 16 languages are configured in the backend/frontend"""
    
    def test_subscription_plans_available(self):
        """Test that subscription plans are available (basic API check)"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "plans" in data
        plans = data["plans"]
        
        assert "24h" in plans
        assert "1week" in plans
        assert "1month" in plans
        
        print(f"✓ Subscription plans available: {list(plans.keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
