import logging
import schedule
import asyncio
from datetime import datetime, time
import pytz
from typing import Dict, Any
from models.user import User
from config.database import database
from config.settings import settings

logger = logging.getLogger(__name__)

class PointService:
    def __init__(self):
        self.users_collection = None
        self.reset_scheduler_running = False
    
    async def initialize(self):
        """Initialize the point service"""
        self.users_collection = database.get_collection(settings.USERS_COLLECTION)
        
        # Start the point reset scheduler
        await self.start_point_reset_scheduler()
    
    async def can_user_generate_image(self, user: User) -> bool:
        """Check if user can generate image"""
        # Check if user is banned
        if user.is_banned:
            return False
        
        # Check and reset daily points if needed
        user._check_daily_reset()
        
        # User can generate if they have daily points or referral points
        return (user.daily_points + user.referral_points) > 0
    
    async def use_point_for_image(self, user: User, point_type: str = "auto") -> bool:
        """Use a point for image generation"""
        try:
            if not await self.can_user_generate_image(user):
                return False
            
            # Auto mode: use referral points first, then daily points
            if point_type == "auto":
                if user.referral_points > 0:
                    point_type = "referral"
                else:
                    point_type = "daily"
            
            # Use the specified point type
            success = user.use_point(point_type)
            
            if success:
                # Update user in database
                await self.users_collection.update_one(
                    {"user_id": user.user_id},
                    {"$set": user.to_dict()}
                )
                
                logger.info(f"Point used for image generation - User: {user.user_id}, Type: {point_type}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error using point for user {user.user_id}: {e}")
            return False
    
    async def get_user_points_info(self, user: User) -> Dict[str, Any]:
        """Get detailed points information for user"""
        try:
            # Ensure points are up to date
            user._check_daily_reset()
            
            # Calculate time until next reset (midnight WIB)
            tz = pytz.timezone(settings.TIMEZONE)
            now = datetime.now(tz)
            tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + pytz.timedelta(days=1)
            time_until_reset = tomorrow - now
            
            hours_until_reset = int(time_until_reset.total_seconds() // 3600)
            minutes_until_reset = int((time_until_reset.total_seconds() % 3600) // 60)
            
            return {
                "daily_points": user.daily_points,
                "referral_points": user.referral_points,
                "total_points": user.daily_points + user.referral_points,
                "total_points_used": user.total_points_used,
                "images_generated": user.image_generated,
                "can_generate": await self.can_user_generate_image(user),
                "time_until_reset": {
                    "hours": hours_until_reset,
                    "minutes": minutes_until_reset,
                    "text": f"{hours_until_reset}h {minutes_until_reset}m"
                },
                "last_reset": user.last_reset.strftime("%d/%m/%Y %H:%M") if user.last_reset else "Never"
            }
            
        except Exception as e:
            logger.error(f"Error getting points info for user {user.user_id}: {e}")
            return {}
    
    async def reset_daily_points(self, user_id: int = None) -> int:
        """Reset daily points for user(s)"""
        try:
            tz = pytz.timezone(settings.TIMEZONE)
            now = datetime.now(tz)
            
            if user_id:
                # Reset for specific user
                result = await self.users_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "daily_points": settings.DAILY_POINTS,
                            "last_reset": now
                        }
                    }
                )
                return result.modified_count
            else:
                # Reset for all users (daily reset)
                result = await self.users_collection.update_many(
                    {},  # All users
                    {
                        "$set": {
                            "daily_points": settings.DAILY_POINTS,
                            "last_reset": now
                        }
                    }
                )
                
                logger.info(f"Daily points reset for {result.modified_count} users")
                return result.modified_count
                
        except Exception as e:
            logger.error(f"Error resetting daily points: {e}")
            return 0
    
    async def add_referral_points(self, user_id: int, points: int) -> bool:
        """Add referral points to user"""
        try:
            result = await self.users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {"referral_points": points}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Added {points} referral points to user {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error adding referral points to user {user_id}: {e}")
            return False
    
    async def get_points_statistics(self) -> Dict[str, Any]:
        """Get global points statistics"""
        try:
            # Total points used
            pipeline = [
                {"$group": {
                    "_id": None,
                    "total_points_used": {"$sum": "$total_points_used"},
                    "total_images_generated": {"$sum": "$image_generated"},
                    "total_referral_points": {"$sum": "$referral_points"},
                    "active_users_with_points": {
                        "$sum": {
                            "$cond": [
                                {"$gt": [{"$add": ["$daily_points", "$referral_points"]}, 0]},
                                1, 0
                            ]
                        }
                    }
                }}
            ]
            
            result = await self.users_collection.aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                return {
                    "total_points_used": stats.get("total_points_used", 0),
                    "total_images_generated": stats.get("total_images_generated", 0),
                    "total_referral_points": stats.get("total_referral_points", 0),
                    "active_users_with_points": stats.get("active_users_with_points", 0)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting points statistics: {e}")
            return {}
    
    async def get_top_point_users(self, limit: int = 10) -> list:
        """Get top users by points used"""
        try:
            cursor = self.users_collection.find(
                {"is_banned": {"$ne": True}},
                {
                    "user_id": 1,
                    "first_name": 1,
                    "username": 1,
                    "total_points_used": 1,
                    "image_generated": 1,
                    "referral_points": 1
                }
            ).sort("total_points_used", -1).limit(limit)
            
            users = []
            async for user_data in cursor:
                users.append(user_data)
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting top point users: {e}")
            return []
    
    async def start_point_reset_scheduler(self):
        """Start the daily point reset scheduler"""
        if self.reset_scheduler_running:
            return
        
        try:
            # Schedule daily reset at midnight WIB
            schedule.every().day.at("00:00").do(self._schedule_daily_reset)
            
            # Start scheduler loop
            self.reset_scheduler_running = True
            asyncio.create_task(self._scheduler_loop())
            
            logger.info("Point reset scheduler started")
            
        except Exception as e:
            logger.error(f"Error starting point reset scheduler: {e}")
    
    async def _scheduler_loop(self):
        """Run the scheduler loop"""
        while self.reset_scheduler_running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
    
    def _schedule_daily_reset(self):
        """Schedule the daily reset (called by schedule)"""
        asyncio.create_task(self.reset_daily_points())
    
    async def stop_scheduler(self):
        """Stop the point reset scheduler"""
        self.reset_scheduler_running = False
        schedule.clear()
        logger.info("Point reset scheduler stopped")
    
    async def manual_reset_user_points(self, user_id: int) -> bool:
        """Manually reset a user's daily points (admin function)"""
        try:
            count = await self.reset_daily_points(user_id)
            return count > 0
        except Exception as e:
            logger.error(f"Error manually resetting points for user {user_id}: {e}")
            return False
    
    async def grant_bonus_points(self, user_id: int, points: int, point_type: str = "referral") -> bool:
        """Grant bonus points to a user (admin function)"""
        try:
            field = "referral_points" if point_type == "referral" else "daily_points"
            
            result = await self.users_collection.update_one(
                {"user_id": user_id},
                {"$inc": {field: points}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Granted {points} {point_type} points to user {user_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error granting bonus points to user {user_id}: {e}")
            return False
    
    def get_points_help_text(self) -> str:
        """Get help text about the points system"""
        return f"""
🎯 **Sistem Poin untuk Generasi Gambar**

📊 **Poin Harian:**
• Setiap user mendapat {settings.DAILY_POINTS} poin per hari
• Reset otomatis setiap jam 12 malam WIB
• Gunakan untuk membuat gambar dengan AI

🎁 **Poin Referral:**
• Dapatkan {settings.REFERRAL_POINTS} poin dengan mengundang teman
• Teman yang diundang juga dapat {settings.REFERRAL_POINTS} poin
• Poin referral tidak expire

⚡ **Cara Kerja:**
• 1 poin = 1 gambar yang bisa dibuat
• Poin referral digunakan terlebih dahulu
• Jika poin habis, tunggu reset harian

📋 **Perintah:**
• `/points` - Cek poin Anda
• `/referral` - Lihat kode referral
• `/invite` - Undang teman dan dapatkan poin

💡 **Tips:** Ajak teman untuk mendapat poin tambahan!
        """.strip()
