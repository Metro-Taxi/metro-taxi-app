"""
Modèles Pydantic pour l'application Métro-Taxi
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any


# ============================================
# AUTH MODELS
# ============================================
class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str


class DriverRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str
    vehicle_plate: str
    vehicle_type: str
    seats: int
    vtc_license: str
    iban: Optional[str] = None
    bic: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmailVerificationRequest(BaseModel):
    token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    role: str
    subscription_active: bool = False
    subscription_expires: Optional[str] = None
    created_at: str


class DriverResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    first_name: str
    last_name: str
    email: str
    phone: str
    vehicle_plate: str
    vehicle_type: str
    seats: int
    vtc_license: str
    is_active: bool
    is_validated: bool
    role: str
    created_at: str
    iban: Optional[str] = None
    bic: Optional[str] = None


# ============================================
# LOCATION & RIDES MODELS
# ============================================
class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    available_seats: Optional[int] = None


class RideRequestCreate(BaseModel):
    driver_id: str
    pickup_lat: float
    pickup_lng: float
    destination_lat: float
    destination_lng: float


class RideRequestResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    user_name: str
    driver_id: str
    pickup_lat: float
    pickup_lng: float
    destination_lat: float
    destination_lng: float
    status: str
    created_at: str


class RideProgressUpdate(BaseModel):
    ride_id: str
    status: str  # "pickup", "in_progress", "near_destination", "completed"
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None


class RideHistoryFilter(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = None
    page: int = 1
    limit: int = 20


# ============================================
# MATCHING MODELS
# ============================================
class MatchingRequest(BaseModel):
    user_lat: float
    user_lng: float
    dest_lat: float
    dest_lng: float


# ============================================
# PAYMENT MODELS
# ============================================
class CheckoutRequest(BaseModel):
    plan_id: str
    origin_url: str


class CheckoutRequestWithRegion(BaseModel):
    plan_id: str
    region_id: str
    origin_url: str


class SepaCheckoutRequest(BaseModel):
    plan_id: str
    region_id: str
    iban: str
    account_holder_name: str
    email: str
    origin_url: str


# ============================================
# ADMIN MODELS
# ============================================
class AdminStats(BaseModel):
    total_users: int
    total_drivers: int
    active_subscriptions: int
    active_rides: int


class BankInfoUpdate(BaseModel):
    iban: str
    bic: str


# ============================================
# PUSH NOTIFICATIONS MODELS
# ============================================
class PushSubscription(BaseModel):
    endpoint: str
    keys: Dict[str, str]
    user_id: Optional[str] = None
    user_type: str = "user"  # "user" or "driver"


class NotificationPayload(BaseModel):
    title: str
    body: str
    icon: Optional[str] = "/icons/icon-192x192.png"
    badge: Optional[str] = "/icons/icon-72x72.png"
    data: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, str]]] = None


# ============================================
# RATING SYSTEM MODELS
# ============================================
class RatingCreate(BaseModel):
    ride_id: str
    driver_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class RatingResponse(BaseModel):
    id: str
    ride_id: str
    user_id: str
    driver_id: str
    rating: int
    comment: Optional[str]
    created_at: str


# ============================================
# CHAT SYSTEM MODELS
# ============================================
class ChatMessage(BaseModel):
    ride_id: str
    content: str


class ChatMessageResponse(BaseModel):
    id: str
    ride_id: str
    sender_id: str
    sender_type: str  # "user" or "driver"
    sender_name: str
    content: str
    created_at: str
    read: bool = False


# ============================================
# REGION SYSTEM MODELS
# ============================================
class RegionBounds(BaseModel):
    north: float  # Max latitude
    south: float  # Min latitude
    east: float   # Max longitude
    west: float   # Min longitude


class RegionCreate(BaseModel):
    id: str  # e.g., "paris", "lyon", "london"
    name: str  # Display name e.g., "Île-de-France"
    country: str  # ISO country code e.g., "FR", "GB"
    currency: str  # e.g., "EUR", "GBP"
    language: str  # Default language e.g., "fr", "en"
    timezone: str = "Europe/Paris"
    bounds: RegionBounds
    is_active: bool = False


class RegionResponse(BaseModel):
    id: str
    name: str
    country: str
    currency: str
    language: str
    timezone: str
    bounds: dict
    is_active: bool
    launch_date: Optional[str] = None
    created_at: str
    driver_count: int = 0
    user_count: int = 0


class RegionSubscription(BaseModel):
    region_id: str
    plan_id: str  # "24h", "1week", "1month"
    expires_at: str
    is_active: bool = True


class UserRegisterWithRegion(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str
    region_id: Optional[str] = None  # Optional, can be detected by geolocation


class DriverRegisterWithRegion(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str
    vehicle_plate: str
    vehicle_type: str
    seats: int
    vtc_license: str
    region_id: str  # Required for drivers
    iban: Optional[str] = None
    bic: Optional[str] = None
