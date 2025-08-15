import motor.motor_asyncio
from pymongo import MongoClient
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URI)
            self.db = self.client[settings.DATABASE_NAME]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Create indexes
            await self.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Users collection indexes
            await self.db[settings.USERS_COLLECTION].create_index("user_id", unique=True)
            await self.db[settings.USERS_COLLECTION].create_index("referral_code", unique=True, sparse=True)
            
            # Conversations collection indexes
            await self.db[settings.CONVERSATIONS_COLLECTION].create_index([("user_id", 1), ("timestamp", -1)])
            
            # Clone bots collection indexes
            await self.db[settings.CLONE_BOTS_COLLECTION].create_index("bot_token", unique=True)
            await self.db[settings.CLONE_BOTS_COLLECTION].create_index("creator_id")
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create indexes: {e}")
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    def get_collection(self, collection_name):
        """Get a collection from the database"""
        return self.db[collection_name]

# Global database instance
database = Database()
