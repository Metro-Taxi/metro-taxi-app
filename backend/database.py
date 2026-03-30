"""
Configuration de la base de données MongoDB
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
db = client[os.environ['DB_NAME']]

async def verify_connection():
    """Verify MongoDB connection is working"""
    try:
        await client.admin.command('ping')
        return True
    except Exception as e:
        return False
