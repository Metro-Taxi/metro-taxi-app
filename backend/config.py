"""
Configuration centralisée pour l'application Métro-Taxi
"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'metro-taxi-secret')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Stripe Configuration
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

# Resend Configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')

# Subscription Plans (prices in cents to avoid floating point issues)
SUBSCRIPTION_PLANS = {
    "24h": {"name": "24 heures", "price": 6.99, "price_cents": 699, "duration_hours": 24},
    "1week": {"name": "1 semaine", "price": 16.99, "price_cents": 1699, "duration_hours": 168},
    "1month": {"name": "1 mois", "price": 53.99, "price_cents": 5399, "duration_hours": 720}
}

# Driver Revenue Configuration
DRIVER_RATE_PER_KM = 1.50  # €1.50 per kilometer
PAYOUT_DAY = 10  # Day of month for automatic payouts

# Algorithm Constants
SEGMENT_MIN_KM = 1.5  # Minimum segment distance
SEGMENT_MAX_KM = 3.0  # Maximum segment distance (suggest transfer after)
MAX_PICKUP_DISTANCE_KM = 2.0  # Maximum pickup distance
MAX_TRANSFERS = 2  # Maximum number of transfers allowed
DIRECTION_THRESHOLD = 60  # Minimum direction score for compatibility (0-100)

# WebPush VAPID Keys
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY')
VAPID_CLAIMS = {"sub": "mailto:contact@metro-taxi.com"}

# OpenAI/Emergent Key
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
