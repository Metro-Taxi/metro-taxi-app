"""
Test Stripe Checkout Session Creation - Iteration 7
Tests for the rounding bug fix: prices should be passed in cents directly to Stripe SDK

Features tested:
1. User login via POST /api/auth/login
2. Stripe Checkout session creation for 1week plan (16.99€ = 1699 centimes)
3. Stripe Checkout session creation for 24h plan (6.99€ = 699 centimes)
4. Verification that Stripe URL is returned with valid session_id
5. GET /api/regions endpoint returns active regions
"""

import pytest
import requests
import os

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testuser@metro-taxi.com"
TEST_USER_PASSWORD = "test123456"

# Expected prices in cents (to verify rounding bug is fixed)
EXPECTED_PRICES = {
    "24h": {"price": 6.99, "price_cents": 699},
    "1week": {"price": 16.99, "price_cents": 1699},
    "1month": {"price": 53.99, "price_cents": 5399}
}


class TestHealthAndBasics:
    """Basic health checks before testing Stripe"""
    
    def test_api_health(self):
        """Test that API is accessible via subscriptions/plans endpoint"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200, f"API health check failed: {response.status_code}"
        print(f"✅ API health check passed - subscriptions/plans endpoint accessible")
    
    def test_subscription_plans_endpoint(self):
        """Test that subscription plans are correctly configured with cents"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200, f"Plans endpoint failed: {response.status_code}"
        
        data = response.json()
        assert "plans" in data, "Response should contain 'plans' key"
        
        plans = data["plans"]
        
        # Verify each plan has price_cents field
        for plan_id, expected in EXPECTED_PRICES.items():
            assert plan_id in plans, f"Plan {plan_id} should exist"
            plan = plans[plan_id]
            
            assert "price_cents" in plan, f"Plan {plan_id} should have price_cents field"
            assert plan["price_cents"] == expected["price_cents"], \
                f"Plan {plan_id} price_cents should be {expected['price_cents']}, got {plan['price_cents']}"
            assert plan["price"] == expected["price"], \
                f"Plan {plan_id} price should be {expected['price']}, got {plan['price']}"
            
            print(f"✅ Plan {plan_id}: price={plan['price']}€, price_cents={plan['price_cents']}")
        
        print("✅ All subscription plans correctly configured with price_cents")


class TestRegions:
    """Test regions endpoint"""
    
    def test_get_regions(self):
        """Test GET /api/regions returns regions"""
        response = requests.get(f"{BASE_URL}/api/regions")
        assert response.status_code == 200, f"Regions endpoint failed: {response.status_code}"
        
        regions = response.json()
        assert isinstance(regions, list), "Regions should be a list"
        print(f"✅ GET /api/regions returned {len(regions)} regions")
        
        if len(regions) > 0:
            for region in regions:
                print(f"   - Region: {region.get('id')} ({region.get('name')}) - Active: {region.get('is_active')}")
        
        return regions
    
    def test_get_active_regions(self):
        """Test GET /api/regions/active returns only active regions"""
        response = requests.get(f"{BASE_URL}/api/regions/active")
        assert response.status_code == 200, f"Active regions endpoint failed: {response.status_code}"
        
        regions = response.json()
        assert isinstance(regions, list), "Active regions should be a list"
        
        # All returned regions should be active
        for region in regions:
            assert region.get("is_active") == True, f"Region {region.get('id')} should be active"
        
        print(f"✅ GET /api/regions/active returned {len(regions)} active regions")
        return regions


class TestUserAuthentication:
    """Test user login functionality"""
    
    def test_login_with_invalid_credentials(self):
        """Test login fails with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401 for invalid credentials, got {response.status_code}"
        print("✅ Login correctly rejects invalid credentials")
    
    def test_login_with_test_user(self):
        """Test login with test user credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        # If test user doesn't exist, we need to create it first
        if response.status_code == 401:
            print(f"⚠️ Test user {TEST_USER_EMAIL} doesn't exist, creating...")
            # Register the test user
            register_response = requests.post(f"{BASE_URL}/api/auth/register/user", json={
                "first_name": "Test",
                "last_name": "User",
                "email": TEST_USER_EMAIL,
                "phone": "+33612345678",
                "password": TEST_USER_PASSWORD
            })
            
            if register_response.status_code == 200:
                print(f"✅ Test user created successfully")
                data = register_response.json()
                assert "token" in data, "Registration should return token"
                return data["token"]
            elif register_response.status_code == 400 and "déjà utilisé" in register_response.text:
                # User exists but password might be different
                pytest.skip(f"Test user exists but login failed - check credentials")
            else:
                pytest.fail(f"Failed to create test user: {register_response.status_code} - {register_response.text}")
        
        assert response.status_code == 200, f"Login failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "token" in data, "Login response should contain token"
        assert "user" in data, "Login response should contain user data"
        
        print(f"✅ Login successful for {TEST_USER_EMAIL}")
        print(f"   User ID: {data['user'].get('id')}")
        
        return data["token"]


class TestStripeCheckout:
    """Test Stripe Checkout session creation - LIVE MODE (no actual payments)"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for test user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if response.status_code == 401:
            # Create test user if doesn't exist
            register_response = requests.post(f"{BASE_URL}/api/auth/register/user", json={
                "first_name": "Test",
                "last_name": "User",
                "email": TEST_USER_EMAIL,
                "phone": "+33612345678",
                "password": TEST_USER_PASSWORD
            })
            if register_response.status_code == 200:
                return register_response.json()["token"]
            pytest.skip("Could not authenticate test user")
        
        return response.json()["token"]
    
    @pytest.fixture
    def active_region_id(self):
        """Get an active region ID for testing"""
        response = requests.get(f"{BASE_URL}/api/regions/active")
        if response.status_code == 200:
            regions = response.json()
            if len(regions) > 0:
                return regions[0]["id"]
        
        # If no active region, try to get any region
        response = requests.get(f"{BASE_URL}/api/regions")
        if response.status_code == 200:
            regions = response.json()
            if len(regions) > 0:
                return regions[0]["id"]
        
        pytest.skip("No regions available for testing")
    
    def test_checkout_requires_authentication(self, active_region_id):
        """Test that checkout endpoint requires authentication"""
        response = requests.post(f"{BASE_URL}/api/payments/checkout/region", json={
            "plan_id": "1week",
            "region_id": active_region_id,
            "origin_url": "https://metro-taxi-demo.preview.emergentagent.com"
        })
        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print("✅ Checkout endpoint correctly requires authentication")
    
    def test_checkout_1week_plan(self, auth_token, active_region_id):
        """
        Test Stripe Checkout for 1week plan (16.99€ = 1699 centimes)
        This is the main test for the rounding bug fix
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/region",
            headers=headers,
            json={
                "plan_id": "1week",
                "region_id": active_region_id,
                "origin_url": "https://metro-taxi-demo.preview.emergentagent.com"
            }
        )
        
        assert response.status_code == 200, f"Checkout failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "url" in data, "Response should contain 'url'"
        assert "session_id" in data, "Response should contain 'session_id'"
        
        # Verify Stripe URL format
        stripe_url = data["url"]
        assert stripe_url.startswith("https://checkout.stripe.com/"), \
            f"URL should be a Stripe checkout URL, got: {stripe_url[:50]}..."
        
        # Verify session_id format (Stripe session IDs start with 'cs_')
        session_id = data["session_id"]
        assert session_id.startswith("cs_"), \
            f"Session ID should start with 'cs_', got: {session_id[:20]}..."
        
        print(f"✅ 1week plan checkout session created successfully")
        print(f"   Session ID: {session_id[:30]}...")
        print(f"   Stripe URL: {stripe_url[:60]}...")
        print(f"   Expected amount: 1699 centimes (16.99€)")
        print(f"   ⚠️ LIVE MODE - Do not complete payment!")
    
    def test_checkout_24h_plan(self, auth_token, active_region_id):
        """
        Test Stripe Checkout for 24h plan (6.99€ = 699 centimes)
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/region",
            headers=headers,
            json={
                "plan_id": "24h",
                "region_id": active_region_id,
                "origin_url": "https://metro-taxi-demo.preview.emergentagent.com"
            }
        )
        
        assert response.status_code == 200, f"Checkout failed: {response.status_code} - {response.text}"
        
        data = response.json()
        
        # Verify response structure
        assert "url" in data, "Response should contain 'url'"
        assert "session_id" in data, "Response should contain 'session_id'"
        
        # Verify Stripe URL format
        stripe_url = data["url"]
        assert stripe_url.startswith("https://checkout.stripe.com/"), \
            f"URL should be a Stripe checkout URL, got: {stripe_url[:50]}..."
        
        # Verify session_id format
        session_id = data["session_id"]
        assert session_id.startswith("cs_"), \
            f"Session ID should start with 'cs_', got: {session_id[:20]}..."
        
        print(f"✅ 24h plan checkout session created successfully")
        print(f"   Session ID: {session_id[:30]}...")
        print(f"   Stripe URL: {stripe_url[:60]}...")
        print(f"   Expected amount: 699 centimes (6.99€)")
        print(f"   ⚠️ LIVE MODE - Do not complete payment!")
    
    def test_checkout_invalid_plan(self, auth_token, active_region_id):
        """Test checkout fails with invalid plan ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/region",
            headers=headers,
            json={
                "plan_id": "invalid_plan",
                "region_id": active_region_id,
                "origin_url": "https://metro-taxi-demo.preview.emergentagent.com"
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid plan, got {response.status_code}"
        print("✅ Checkout correctly rejects invalid plan ID")
    
    def test_checkout_invalid_region(self, auth_token):
        """Test checkout fails with invalid region ID"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/region",
            headers=headers,
            json={
                "plan_id": "1week",
                "region_id": "invalid_region_xyz",
                "origin_url": "https://metro-taxi-demo.preview.emergentagent.com"
            }
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid region, got {response.status_code}"
        print("✅ Checkout correctly rejects invalid region ID")


class TestStripeWebhook:
    """Test Stripe webhook endpoint (signature validation only - cannot test full flow)"""
    
    def test_webhook_rejects_invalid_signature(self):
        """Test that webhook rejects requests without valid Stripe signature"""
        # Send a fake webhook payload without valid signature
        response = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "invalid_signature"
            },
            json={
                "type": "checkout.session.completed",
                "data": {"object": {"id": "cs_test_fake"}}
            }
        )
        
        # Webhook should return error status (not crash)
        # The endpoint returns {"status": "error"} for invalid signatures
        data = response.json()
        assert data.get("status") == "error" or response.status_code != 200, \
            "Webhook should reject invalid signature"
        
        print("✅ Webhook correctly rejects invalid Stripe signature")
        print("   Note: Full webhook testing requires valid Stripe signature")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
