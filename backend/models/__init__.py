"""
Modèles Pydantic pour Métro-Taxi
"""
from .schemas import (
    # Auth
    UserRegister,
    DriverRegister,
    LoginRequest,
    EmailVerificationRequest,
    UserResponse,
    DriverResponse,
    # Location & Rides
    LocationUpdate,
    RideRequestCreate,
    RideRequestResponse,
    RideProgressUpdate,
    RideHistoryFilter,
    # Matching
    MatchingRequest,
    # Payments
    CheckoutRequest,
    CheckoutRequestWithRegion,
    SepaCheckoutRequest,
    # Admin
    AdminStats,
    BankInfoUpdate,
    # Notifications
    PushSubscription,
    NotificationPayload,
    # Ratings
    RatingCreate,
    RatingResponse,
    # Chat
    ChatMessage,
    ChatMessageResponse,
    # Regions
    RegionBounds,
    RegionCreate,
    RegionResponse,
    RegionSubscription,
    UserRegisterWithRegion,
    DriverRegisterWithRegion,
)
