"""
Test suite for Métro-Taxi Central Matching Algorithm
Tests the following features:
1. /api/matching/optimal-route - Calculate optimal route with segments
2. /api/matching/network-status - Real-time network status
3. /api/matching/transfers - Transfer suggestions
4. /api/matching/find-drivers - Intelligent driver matching
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@metrotaxi.fr"
ADMIN_PASSWORD = "admin123"
TEST_USER_EMAIL = "marie.test@example.com"
TEST_USER_PASSWORD = "test123"

# Paris coordinates for testing
PARIS_CENTER = {"lat": 48.8566, "lng": 2.3522}
PARIS_NORTH = {"lat": 48.8800, "lng": 2.3400}  # ~3km north
PARIS_SOUTH = {"lat": 48.8300, "lng": 2.3600}  # ~3km south
PARIS_EAST = {"lat": 48.8566, "lng": 2.4000}   # ~3km east


class TestAuthSetup:
    """Authentication setup tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    @pytest.fixture(scope="class")
    def user_token(self):
        """Get or create test user and return token"""
        # Try to login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        
        # Create new user if login fails
        unique_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        response = requests.post(f"{BASE_URL}/api/auth/register/user", json={
            "first_name": "Test",
            "last_name": "User",
            "email": unique_email,
            "phone": "+33612345678",
            "password": "test123"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("User authentication failed")
    
    def test_admin_login(self):
        """Test admin login works"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "admin" in data


class TestMatchingOptimalRoute:
    """Tests for /api/matching/optimal-route endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for tests"""
        # Try user login first
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        
        # Try admin login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_optimal_route_short_distance(self, auth_token):
        """Test optimal route calculation for short distance (< 3km)"""
        response = requests.post(
            f"{BASE_URL}/api/matching/optimal-route",
            json={
                "user_lat": PARIS_CENTER["lat"],
                "user_lng": PARIS_CENTER["lng"],
                "dest_lat": PARIS_CENTER["lat"] + 0.01,  # ~1km
                "dest_lng": PARIS_CENTER["lng"] + 0.01
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "route" in data
        route = data["route"]
        assert "total_distance_km" in route
        assert "segments" in route
        assert "transfer_points" in route
        assert "total_transfers" in route
        assert "estimated_total_time_minutes" in route
        assert "route_efficiency" in route
        
        # Verify algorithm config is returned
        assert "algorithm_config" in data
        config = data["algorithm_config"]
        assert config["segment_min_km"] == 1.5
        assert config["segment_max_km"] == 3.0
        assert config["max_transfers"] == 2
        
        print(f"Short route: {route['total_distance_km']}km, {route['total_transfers']} transfers")
    
    def test_optimal_route_medium_distance(self, auth_token):
        """Test optimal route calculation for medium distance (3-6km)"""
        response = requests.post(
            f"{BASE_URL}/api/matching/optimal-route",
            json={
                "user_lat": PARIS_CENTER["lat"],
                "user_lng": PARIS_CENTER["lng"],
                "dest_lat": PARIS_NORTH["lat"],
                "dest_lng": PARIS_NORTH["lng"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        route = data["route"]
        
        # For medium distance, may need 1-2 transfers
        assert route["total_transfers"] <= 2
        assert route["total_distance_km"] > 0
        assert len(route["segments"]) >= 1
        
        print(f"Medium route: {route['total_distance_km']}km, {route['total_transfers']} transfers, {len(route['segments'])} segments")
    
    def test_optimal_route_long_distance(self, auth_token):
        """Test optimal route calculation for long distance (>6km)"""
        response = requests.post(
            f"{BASE_URL}/api/matching/optimal-route",
            json={
                "user_lat": PARIS_SOUTH["lat"],
                "user_lng": PARIS_SOUTH["lng"],
                "dest_lat": PARIS_NORTH["lat"],
                "dest_lng": PARIS_NORTH["lng"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        route = data["route"]
        
        # Long distance should have segments
        assert len(route["segments"]) >= 1
        assert route["total_transfers"] <= 2  # Max 2 transfers
        
        # Verify segment structure
        for segment in route["segments"]:
            assert "index" in segment
            assert "start" in segment
            assert "end" in segment
            assert "distance_km" in segment
            assert "eta_minutes" in segment
        
        print(f"Long route: {route['total_distance_km']}km, {route['total_transfers']} transfers, efficiency: {route['route_efficiency']}%")
    
    def test_optimal_route_unauthorized(self):
        """Test optimal route requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/matching/optimal-route",
            json={
                "user_lat": PARIS_CENTER["lat"],
                "user_lng": PARIS_CENTER["lng"],
                "dest_lat": PARIS_NORTH["lat"],
                "dest_lng": PARIS_NORTH["lng"]
            }
        )
        assert response.status_code == 401


class TestMatchingNetworkStatus:
    """Tests for /api/matching/network-status endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_network_status_structure(self, auth_token):
        """Test network status returns correct structure"""
        response = requests.get(
            f"{BASE_URL}/api/matching/network-status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields
        assert "network_status" in data
        assert data["network_status"] in ["active", "limited"]
        assert "active_vehicles" in data
        assert isinstance(data["active_vehicles"], int)
        assert "total_available_seats" in data
        assert isinstance(data["total_available_seats"], int)
        assert "active_rides" in data
        assert "pending_requests" in data
        assert "vehicles" in data
        assert isinstance(data["vehicles"], list)
        
        print(f"Network: {data['network_status']}, {data['active_vehicles']} vehicles, {data['total_available_seats']} seats")
    
    def test_network_status_vehicle_details(self, auth_token):
        """Test vehicle details in network status"""
        response = requests.get(
            f"{BASE_URL}/api/matching/network-status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # If there are vehicles, verify their structure
        if data["vehicles"]:
            vehicle = data["vehicles"][0]
            assert "id" in vehicle
            assert "location" in vehicle
            assert "vehicle_type" in vehicle
            assert "available_seats" in vehicle
            # direction_bearing may be None if no destination
            assert "direction_bearing" in vehicle
            
            print(f"Sample vehicle: {vehicle['vehicle_type']}, {vehicle['available_seats']} seats")
    
    def test_network_status_unauthorized(self):
        """Test network status requires authentication"""
        response = requests.get(f"{BASE_URL}/api/matching/network-status")
        assert response.status_code == 401


class TestMatchingTransfers:
    """Tests for /api/matching/transfers endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_transfers_endpoint_structure(self, auth_token):
        """Test transfers endpoint returns correct structure"""
        response = requests.post(
            f"{BASE_URL}/api/matching/transfers",
            json={
                "user_lat": PARIS_CENTER["lat"],
                "user_lng": PARIS_CENTER["lng"],
                "dest_lat": PARIS_NORTH["lat"],
                "dest_lng": PARIS_NORTH["lng"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "transfers" in data
        assert "count" in data
        assert isinstance(data["transfers"], list)
        assert isinstance(data["count"], int)
        
        print(f"Found {data['count']} transfer options")
    
    def test_transfers_option_structure(self, auth_token):
        """Test transfer option structure when available"""
        response = requests.post(
            f"{BASE_URL}/api/matching/transfers",
            json={
                "user_lat": PARIS_CENTER["lat"],
                "user_lng": PARIS_CENTER["lng"],
                "dest_lat": PARIS_NORTH["lat"],
                "dest_lng": PARIS_NORTH["lng"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # If transfers are available, verify structure
        if data["transfers"]:
            transfer = data["transfers"][0]
            assert "type" in transfer
            assert "first_driver" in transfer
            assert "second_driver" in transfer
            assert "transfer_point" in transfer
            assert "first_segment_km" in transfer
            assert "second_segment_km" in transfer
            assert "efficiency_percent" in transfer
            
            # Verify driver info
            assert "id" in transfer["first_driver"]
            assert "name" in transfer["first_driver"]
            assert "vehicle" in transfer["first_driver"]
            
            print(f"Transfer: {transfer['first_segment_km']}km + {transfer['second_segment_km']}km, efficiency: {transfer['efficiency_percent']}%")
    
    def test_transfers_unauthorized(self):
        """Test transfers requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/matching/transfers",
            json={
                "user_lat": PARIS_CENTER["lat"],
                "user_lng": PARIS_CENTER["lng"],
                "dest_lat": PARIS_NORTH["lat"],
                "dest_lng": PARIS_NORTH["lng"]
            }
        )
        assert response.status_code == 401


class TestMatchingFindDrivers:
    """Tests for /api/matching/find-drivers endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_find_drivers_structure(self, auth_token):
        """Test find-drivers returns correct structure"""
        response = requests.post(
            f"{BASE_URL}/api/matching/find-drivers",
            json={
                "user_lat": PARIS_CENTER["lat"],
                "user_lng": PARIS_CENTER["lng"],
                "dest_lat": PARIS_NORTH["lat"],
                "dest_lng": PARIS_NORTH["lng"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "drivers" in data
        assert isinstance(data["drivers"], list)
        
        print(f"Found {len(data['drivers'])} matching drivers")
    
    def test_find_drivers_matching_info(self, auth_token):
        """Test driver matching info structure"""
        response = requests.post(
            f"{BASE_URL}/api/matching/find-drivers",
            json={
                "user_lat": PARIS_CENTER["lat"],
                "user_lng": PARIS_CENTER["lng"],
                "dest_lat": PARIS_NORTH["lat"],
                "dest_lng": PARIS_NORTH["lng"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # If drivers are available, verify matching info
        if data["drivers"]:
            driver = data["drivers"][0]
            assert "matching" in driver
            matching = driver["matching"]
            
            # Verify matching score components
            assert "score" in matching
            assert "distance_km" in matching
            assert "direction_score" in matching
            assert "eta_minutes" in matching
            assert "seats_score" in matching
            
            # Score should be positive
            assert matching["score"] > 0
            
            print(f"Best match: score={matching['score']}, distance={matching['distance_km']}km, direction={matching['direction_score']}%")
    
    def test_find_drivers_sorted_by_score(self, auth_token):
        """Test drivers are sorted by matching score (descending)"""
        response = requests.post(
            f"{BASE_URL}/api/matching/find-drivers",
            json={
                "user_lat": PARIS_CENTER["lat"],
                "user_lng": PARIS_CENTER["lng"],
                "dest_lat": PARIS_NORTH["lat"],
                "dest_lng": PARIS_NORTH["lng"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        if len(data["drivers"]) > 1:
            scores = [d["matching"]["score"] for d in data["drivers"]]
            assert scores == sorted(scores, reverse=True), "Drivers should be sorted by score descending"
    
    def test_find_drivers_unauthorized(self):
        """Test find-drivers requires authentication"""
        response = requests.post(
            f"{BASE_URL}/api/matching/find-drivers",
            json={
                "user_lat": PARIS_CENTER["lat"],
                "user_lng": PARIS_CENTER["lng"],
                "dest_lat": PARIS_NORTH["lat"],
                "dest_lng": PARIS_NORTH["lng"]
            }
        )
        assert response.status_code == 401


class TestDriverPassengers:
    """Tests for /api/matching/driver-passengers endpoint"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Admin authentication failed")
    
    def test_driver_passengers_structure(self, admin_token):
        """Test driver-passengers endpoint structure"""
        # First get a driver ID
        response = requests.get(
            f"{BASE_URL}/api/admin/drivers",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code != 200 or not response.json().get("drivers"):
            pytest.skip("No drivers available for testing")
        
        driver_id = response.json()["drivers"][0]["id"]
        
        # Test the endpoint
        response = requests.get(
            f"{BASE_URL}/api/matching/driver-passengers/{driver_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "passengers" in data
        assert "count" in data
        assert "auto_match_enabled" in data
        assert isinstance(data["passengers"], list)
        
        print(f"Found {data['count']} compatible passengers for driver")


class TestRideSuggestions:
    """Tests for /api/matching/suggestions endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_suggestions_endpoint(self, auth_token):
        """Test ride suggestions endpoint"""
        # Get a user ID first
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code != 200 or not response.json().get("users"):
            pytest.skip("No users available for testing")
        
        user_id = response.json()["users"][0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/matching/suggestions/{user_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)
        
        print(f"Found {len(data['suggestions'])} ride suggestions")


class TestAvailableDrivers:
    """Tests for /api/drivers/available endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Authentication failed")
    
    def test_available_drivers_structure(self, auth_token):
        """Test available drivers endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/drivers/available",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "drivers" in data
        assert isinstance(data["drivers"], list)
        
        # If drivers exist, verify structure
        if data["drivers"]:
            driver = data["drivers"][0]
            assert "id" in driver
            assert "first_name" in driver
            assert "vehicle_plate" in driver
            assert "vehicle_type" in driver
            assert "location" in driver
            assert "available_seats" in driver
            
            print(f"Found {len(data['drivers'])} available drivers")
        else:
            print("No available drivers currently")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
