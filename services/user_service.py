import string
import random
import logging
from typing import Optional, List, Dict, Any
from models.user import User
from config.database import database
from config.settings import settings

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.users_collection = None
    
    async def initialize(self):
        """Initialize the user service"""
        self.users_collection = database.get_collection(settings.USERS_COLLECTION)
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by user_id"""
        try:
            user_data = await self.users_collection.find_one({"user_id": user_id})
            if user_data:
                return User.from_dict(user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None
    
    async def create_user(self, user_id: int, **kwargs) -> User:
        """Create a new user"""
        try:
            # Generate unique referral code
            referral_code = await self._generate_unique_referral_code()
            
            user = User(
                user_id=user_id,
                referral_code=referral_code,
                **kwargs
            )
            
            # Insert to database
            await self.users_collection.insert_one(user.to_dict())
            
            logger.info(f"New user created: {user_id}")
            return user
            
        except Exception as e:
            logger.error(f"Error creating user {user_id}: {e}")
            raise
    
    async def update_user(self, user: User) -> bool:
        """Update user in database"""
        try:
            result = await self.users_collection.update_one(
                {"user_id": user.user_id},
                {"$set": user.to_dict()}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating user {user.user_id}: {e}")
            return False
    
    async def get_or_create_user(self, user_id: int, **kwargs) -> User:
        """Get existing user or create new one"""
        user = await self.get_user(user_id)
        if not user:
            user = await self.create_user(user_id, **kwargs)
        else:
            # Update activity
            user.update_activity()
            await self.update_user(user)
        return user
    
    async def ban_user(self, user_id: int) -> bool:
        """Ban a user"""
        try:
            result = await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"is_banned": True}}
            )
            logger.info(f"User banned: {user_id}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error banning user {user_id}: {e}")
            return False
    
    async def unban_user(self, user_id: int) -> bool:
        """Unban a user"""
        try:
            result = await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"is_banned": False}}
            )
            logger.info(f"User unbanned: {user_id}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error unbanning user {user_id}: {e}")
            return False
    
    async def set_admin(self, user_id: int, is_admin: bool = True) -> bool:
        """Set admin status for user"""
        try:
            result = await self.users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"is_admin": is_admin}}
            )
            logger.info(f"User admin status changed: {user_id} -> {is_admin}")
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error setting admin status for user {user_id}: {e}")
            return False
    
    async def get_user_by_referral_code(self, referral_code: str) -> Optional[User]:
        """Get user by referral code"""
        try:
            user_data = await self.users_collection.find_one({"referral_code": referral_code})
            if user_data:
                return User.from_dict(user_data)
            return None
        except Exception as e:
            logger.error(f"Error getting user by referral code {referral_code}: {e}")
            return None
    
    async def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            total_users = await self.users_collection.count_documents({})
            banned_users = await self.users_collection.count_documents({"is_banned": True})
            admin_users = await self.users_collection.count_documents({"is_admin": True})
            clone_bot_users = await self.users_collection.count_documents({"has_clone_bot": True})
            
            # Get active users (last 24 hours)
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(days=1)
            active_users = await self.users_collection.count_documents({
                "last_activity": {"$gte": yesterday}
            })
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "banned_users": banned_users,
                "admin_users": admin_users,
                "clone_bot_users": clone_bot_users
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}
    
    async def get_top_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top users by message count"""
        try:
            cursor = self.users_collection.find(
                {"is_banned": {"$ne": True}},
                {
                    "user_id": 1,
                    "first_name": 1,
                    "username": 1,
                    "message_count": 1,
                    "image_generated": 1,
                    "referral_count": 1
                }
            ).sort("message_count", -1).limit(limit)
            
            users = []
            async for user_data in cursor:
                users.append(user_data)
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting top users: {e}")
            return []
    
    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by username or first name"""
        try:
            # Create search filter
            search_filter = {
                "$or": [
                    {"username": {"$regex": query, "$options": "i"}},
                    {"first_name": {"$regex": query, "$options": "i"}},
                ]
            }
            
            # Try to convert query to int for user_id search
            try:
                user_id = int(query)
                search_filter["$or"].append({"user_id": user_id})
            except ValueError:
                pass
            
            cursor = self.users_collection.find(search_filter).limit(limit)
            users = []
            
            async for user_data in cursor:
                users.append(User.from_dict(user_data))
            
            return users
            
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []
    
    async def _generate_unique_referral_code(self) -> str:
        """Generate unique referral code"""
        while True:
            # Generate random 8-character code
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Check if code already exists
            existing = await self.users_collection.find_one({"referral_code": code})
            if not existing:
                return code
    
    async def get_users_for_broadcast(self, exclude_banned: bool = True) -> List[int]:
        """Get all user IDs for broadcasting"""
        try:
            filter_query = {}
            if exclude_banned:
                filter_query["is_banned"] = {"$ne": True}
            
            cursor = self.users_collection.find(filter_query, {"user_id": 1})
            user_ids = []
            
            async for user_data in cursor:
                user_ids.append(user_data["user_id"])
            
            return user_ids
            
        except Exception as e:
            logger.error(f"Error getting users for broadcast: {e}")
            return []
    
    async def cleanup_inactive_users(self, days: int = 90) -> int:
        """Clean up inactive users (optional maintenance function)"""
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Find inactive users
            result = await self.users_collection.delete_many({
                "last_activity": {"$lt": cutoff_date},
                "message_count": {"$lt": 5},  # Less than 5 messages
                "is_admin": {"$ne": True}  # Don't delete admins
            })
            
            logger.info(f"Cleaned up {result.deleted_count} inactive users")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive users: {e}")
            return 0
