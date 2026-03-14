import requests
import sys
from datetime import datetime
import json

class MetroTaxiAPITester:
    def __init__(self, base_url="https://transit-match-7.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.driver_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.driver_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")

            return success, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_subscription_plans(self):
        """Test subscription plans endpoint"""
        success, response = self.run_test(
            "Get Subscription Plans",
            "GET",
            "subscriptions/plans",
            200
        )
        if success and 'plans' in response:
            plans = response['plans']
            if '24h' in plans and '1week' in plans and '1month' in plans:
                print(f"   Found {len(plans)} subscription plans")
                return True
        return False

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"testuser{timestamp}@example.com",
            "phone": "0612345678",
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register/user",
            200,
            data=user_data
        )
        
        if success and 'token' in response and 'user' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            print(f"   User registered with ID: {self.user_id[:8]}")
            return True
        return False

    def test_driver_registration(self):
        """Test driver registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        driver_data = {
            "first_name": "Test",
            "last_name": "Driver",
            "email": f"testdriver{timestamp}@example.com",
            "phone": "0687654321",
            "password": "testpass123",
            "vehicle_plate": f"AB-{timestamp[-3:]}-CD",
            "vehicle_type": "berline",
            "seats": 4,
            "vtc_license": f"VTC-{timestamp}"
        }
        
        success, response = self.run_test(
            "Driver Registration",
            "POST",
            "auth/register/driver",
            200,
            data=driver_data
        )
        
        if success and 'token' in response and 'driver' in response:
            self.driver_token = response['token']
            self.driver_id = response['driver']['id']
            print(f"   Driver registered with ID: {self.driver_id[:8]}")
            return True
        return False

    def test_admin_login(self):
        """Test admin login"""
        login_data = {
            "email": "admin@metrotaxi.fr",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response and 'admin' in response:
            self.admin_token = response['token']
            print(f"   Admin logged in successfully")
            return True
        return False

    def test_user_login(self):
        """Test user login with registered user"""
        if not self.user_id:
            return False
            
        # We need to get the email from registration, let's use a test email
        timestamp = datetime.now().strftime('%H%M%S')
        login_data = {
            "email": f"testuser{timestamp}@example.com",
            "password": "testpass123"
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        return success

    def test_auth_me(self):
        """Test get current user info"""
        if not self.token:
            return False
            
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200,
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        if success and 'user' in response:
            print(f"   User info retrieved: {response['user']['first_name']}")
            return True
        return False

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        if not self.admin_token:
            return False
            
        success, response = self.run_test(
            "Admin Stats",
            "GET",
            "admin/stats",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and all(key in response for key in ['total_users', 'total_drivers', 'active_subscriptions', 'active_rides']):
            print(f"   Stats: {response['total_users']} users, {response['total_drivers']} drivers")
            return True
        return False

    def test_admin_drivers(self):
        """Test admin get all drivers"""
        if not self.admin_token:
            return False
            
        success, response = self.run_test(
            "Admin Get Drivers",
            "GET",
            "admin/drivers",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and 'drivers' in response:
            print(f"   Found {len(response['drivers'])} drivers")
            return True
        return False

    def test_validate_driver(self):
        """Test admin validate driver"""
        if not self.admin_token or not self.driver_id:
            return False
            
        success, response = self.run_test(
            "Admin Validate Driver",
            "POST",
            f"admin/drivers/{self.driver_id}/validate",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and response.get('status') == 'validated':
            print(f"   Driver {self.driver_id[:8]} validated")
            return True
        return False

    def test_available_drivers(self):
        """Test get available drivers"""
        if not self.token:
            return False
            
        success, response = self.run_test(
            "Get Available Drivers",
            "GET",
            "drivers/available",
            200,
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        if success and 'drivers' in response:
            print(f"   Found {len(response['drivers'])} available drivers")
            return True
        return False

    def test_user_virtual_card(self):
        """Test user virtual card endpoint"""
        if not self.token or not self.user_id:
            return False
            
        success, response = self.run_test(
            "Get User Virtual Card",
            "GET",
            f"users/{self.user_id}/card",
            200,
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        if success and 'card' in response:
            card = response['card']
            print(f"   Virtual card for: {card.get('name', 'Unknown')}")
            return True
        return False

    def test_email_verification_status(self):
        """Test email verification status endpoint"""
        if not self.token:
            return False
            
        success, response = self.run_test(
            "Get Email Verification Status",
            "GET",
            "auth/verification-status",
            200,
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        if success and 'email_verified' in response:
            print(f"   Email verified: {response['email_verified']}")
            return True
        return False

    def test_matching_find_drivers(self):
        """Test intelligent matching algorithm"""
        if not self.token:
            return False
            
        matching_data = {
            "user_lat": 48.8566,
            "user_lng": 2.3522,
            "dest_lat": 48.8606,
            "dest_lng": 2.3376
        }
        
        success, response = self.run_test(
            "Find Matching Drivers",
            "POST",
            "matching/find-drivers",
            200,
            data=matching_data,
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        if success and 'drivers' in response:
            drivers = response['drivers']
            print(f"   Found {len(drivers)} matched drivers")
            if drivers:
                # Check if matching scores are present
                first_driver = drivers[0]
                if 'matching' in first_driver:
                    matching = first_driver['matching']
                    print(f"   Best match score: {matching.get('score', 0)}")
                    return True
            return True  # Empty result is also valid
        return False

    def test_matching_transfers(self):
        """Test transfer suggestions endpoint"""
        if not self.token:
            return False
            
        transfer_data = {
            "user_lat": 48.8566,
            "user_lng": 2.3522,
            "dest_lat": 48.8606,
            "dest_lng": 2.3376
        }
        
        success, response = self.run_test(
            "Find Transfer Routes",
            "POST",
            "matching/transfers",
            200,
            data=transfer_data,
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        if success and 'transfers' in response and 'count' in response:
            transfers = response['transfers']
            count = response['count']
            print(f"   Found {count} transfer options")
            return True
        return False

    def test_admin_virtual_cards(self):
        """Test admin virtual cards endpoint"""
        if not self.admin_token:
            return False
            
        success, response = self.run_test(
            "Admin Get Virtual Cards",
            "GET",
            "admin/cards",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and 'cards' in response and 'total' in response:
            cards = response['cards']
            total = response['total']
            print(f"   Found {total} virtual cards")
            return True
        return False

    def test_admin_user_card_detail(self):
        """Test admin get specific user card"""
        if not self.admin_token or not self.user_id:
            return False
            
        success, response = self.run_test(
            "Admin Get User Card Detail",
            "GET",
            f"admin/cards/{self.user_id}",
            200,
            headers={'Authorization': f'Bearer {self.admin_token}'}
        )
        
        if success and 'card' in response:
            card = response['card']
            print(f"   Card details for: {card.get('name', 'Unknown')}")
            print(f"   Card number: {card.get('card_number', 'N/A')}")
            return True
        return False

    def test_ride_request_and_progress(self):
        """Test ride request and progress tracking"""
        if not self.token or not self.driver_token:
            return False
            
        # First, update driver location to make them available
        location_data = {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "available_seats": 3
        }
        
        location_success, _ = self.run_test(
            "Update Driver Location",
            "POST",
            "drivers/location",
            200,
            data=location_data,
            headers={'Authorization': f'Bearer {self.driver_token}'}
        )
        
        if not location_success:
            print("   Failed to update driver location")
            return False
            
        # Toggle driver active
        active_success, _ = self.run_test(
            "Toggle Driver Active",
            "POST",
            "drivers/toggle-active",
            200,
            headers={'Authorization': f'Bearer {self.driver_token}'}
        )
        
        if not active_success:
            print("   Failed to activate driver")
            return False
            
        # Create ride request
        ride_data = {
            "driver_id": self.driver_id,
            "pickup_lat": 48.8566,
            "pickup_lng": 2.3522,
            "destination_lat": 48.8606,
            "destination_lng": 2.3376
        }
        
        ride_success, ride_response = self.run_test(
            "Create Ride Request",
            "POST",
            "rides/request",
            200,
            data=ride_data,
            headers={'Authorization': f'Bearer {self.token}'}
        )
        
        if not ride_success or 'ride' not in ride_response:
            print("   Failed to create ride request")
            return False
            
        ride_id = ride_response['ride']['id']
        print(f"   Created ride: {ride_id[:8]}")
        
        # Test ride progress update
        progress_data = {
            "ride_id": ride_id,
            "status": "pickup",
            "current_lat": 48.8566,
            "current_lng": 2.3522
        }
        
        progress_success, progress_response = self.run_test(
            "Update Ride Progress",
            "POST",
            f"rides/{ride_id}/progress",
            200,
            data=progress_data,
            headers={'Authorization': f'Bearer {self.driver_token}'}
        )
        
        if progress_success and 'status' in progress_response:
            print(f"   Progress updated to: {progress_response['status']}")
            
            # Test ride tracking
            tracking_success, tracking_response = self.run_test(
                "Get Ride Tracking",
                "GET",
                f"rides/{ride_id}/tracking",
                200,
                headers={'Authorization': f'Bearer {self.token}'}
            )
            
            if tracking_success and 'ride' in tracking_response and 'progress' in tracking_response:
                progress = tracking_response['progress']
                print(f"   Tracking progress: {progress.get('percent', 0)}%")
                return True
                
        return False

def main():
    print("🚀 Starting Métro-Taxi API Tests")
    print("=" * 50)
    
    tester = MetroTaxiAPITester()
    
    # Test sequence
    tests = [
        ("Subscription Plans", tester.test_subscription_plans),
        ("User Registration", tester.test_user_registration),
        ("Driver Registration", tester.test_driver_registration),
        ("Admin Login", tester.test_admin_login),
        ("Auth Me", tester.test_auth_me),
        ("Email Verification Status", tester.test_email_verification_status),
        ("Admin Stats", tester.test_admin_stats),
        ("Admin Drivers", tester.test_admin_drivers),
        ("Validate Driver", tester.test_validate_driver),
        ("Available Drivers", tester.test_available_drivers),
        ("Matching Find Drivers", tester.test_matching_find_drivers),
        ("Matching Transfers", tester.test_matching_transfers),
        ("Admin Virtual Cards", tester.test_admin_virtual_cards),
        ("Admin User Card Detail", tester.test_admin_user_card_detail),
        ("User Virtual Card", tester.test_user_virtual_card),
        ("Ride Request and Progress", tester.test_ride_request_and_progress),
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} - Exception: {str(e)}")
            failed_tests.append(test_name)
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for test in failed_tests:
            print(f"   - {test}")
    else:
        print("\n✅ All tests passed!")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"\n📈 Success rate: {success_rate:.1f}%")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())