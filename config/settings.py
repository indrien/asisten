import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram Bot Configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    
    # Gemini AI Configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # MongoDB Configuration
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "telegram_assistant")
    
    # Owner/Developer
    OWNER_ID = int(os.getenv("OWNER_ID", 0))
    
    # Bot Settings
    BOT_NAME = os.getenv("BOT_NAME", "AsistenAI")
    DAILY_POINTS = int(os.getenv("DAILY_POINTS", 3))
    REFERRAL_POINTS = int(os.getenv("REFERRAL_POINTS", 3))
    
    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "Asia/Jakarta")
    
    # Collections
    USERS_COLLECTION = "users"
    CONVERSATIONS_COLLECTION = "conversations"
    CLONE_BOTS_COLLECTION = "clone_bots"
    
    # Bot Features
    MAX_MESSAGE_LENGTH = 4096
    MAX_MEMORY_MESSAGES = 50
    
    @classmethod
    def validate(cls):
        """Validate required environment variables"""
        required = [
            "BOT_TOKEN", "API_ID", "API_HASH", 
            "GEMINI_API_KEY", "OWNER_ID"
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        return True

settings = Settings()
