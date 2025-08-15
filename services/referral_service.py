import logging
from typing import Optional, Dict, Any, Tuple
from models.user import User
from services.user_service import UserService
from services.point_service import PointService
from config.database import database
from config.settings import settings

logger = logging.getLogger(__name__)

class ReferralService:
    def __init__(self):
        self.users_collection = None
        self.user_service = UserService()
        self.point_service = PointService()
    
    async def initialize(self):
        """Initialize the referral service"""
        self.users_collection = database.get_collection(settings.USERS_COLLECTION)
        await self.user_service.initialize()
        await self.point_service.initialize()
    
    async def process_referral(self, new_user_id: int, referral_code: str) -> Tuple[bool, str]:
        """Process a referral when new user joins"""
        try:
            # Get the referrer by referral code
            referrer = await self.user_service.get_user_by_referral_code(referral_code)
            if not referrer:
                return False, "Kode referral tidak valid."
            
            # Check if user is trying to refer themselves
            if referrer.user_id == new_user_id:
                return False, "Anda tidak bisa menggunakan kode referral sendiri."
            
            # Check if new user already exists and has been referred
            new_user = await self.user_service.get_user(new_user_id)
            if new_user and new_user.referred_by:
                return False, "Anda sudah menggunakan kode referral sebelumnya."
            
            # Update new user with referral info
            if new_user:
                new_user.referred_by = referrer.user_id
                new_user.referral_points += settings.REFERRAL_POINTS
                await self.user_service.update_user(new_user)
            else:
                # This shouldn't happen normally, but handle it
                return False, "User baru belum terdaftar."
            
            # Update referrer
            referrer.referral_count += 1
            referrer.referral_points += settings.REFERRAL_POINTS
            await self.user_service.update_user(referrer)
            
            logger.info(f"Referral processed: {referrer.user_id} referred {new_user_id}")
            
            return True, f"Berhasil! Anda dan yang mengundang masing-masing mendapat {settings.REFERRAL_POINTS} poin."
            
        except Exception as e:
            logger.error(f"Error processing referral: {e}")
            return False, "Terjadi kesalahan saat memproses referral."
    
    async def get_referral_info(self, user: User) -> Dict[str, Any]:
        """Get referral information for a user"""
        try:
            # Get referrer info if user was referred
            referrer_info = None
            if user.referred_by:
                referrer = await self.user_service.get_user(user.referred_by)
                if referrer:
                    referrer_info = {
                        "user_id": referrer.user_id,
                        "first_name": referrer.first_name,
                        "username": referrer.username
                    }
            
            # Get list of users referred by this user
            referred_users = []
            if user.referral_count > 0:
                referred_cursor = self.users_collection.find(
                    {"referred_by": user.user_id},
                    {
                        "user_id": 1,
                        "first_name": 1,
                        "username": 1,
                        "join_date": 1
                    }
                ).limit(50)  # Limit to avoid too much data
                
                async for referred_user in referred_cursor:
                    referred_users.append(referred_user)
            
            return {
                "referral_code": user.referral_code,
                "referral_count": user.referral_count,
                "referral_points": user.referral_points,
                "referred_by": referrer_info,
                "referred_users": referred_users,
                "total_points_earned": user.referral_count * settings.REFERRAL_POINTS
            }
            
        except Exception as e:
            logger.error(f"Error getting referral info for user {user.user_id}: {e}")
            return {}
    
    async def get_referral_leaderboard(self, limit: int = 10) -> list:
        """Get referral leaderboard"""
        try:
            cursor = self.users_collection.find(
                {
                    "referral_count": {"$gt": 0},
                    "is_banned": {"$ne": True}
                },
                {
                    "user_id": 1,
                    "first_name": 1,
                    "username": 1,
                    "referral_count": 1,
                    "referral_points": 1
                }
            ).sort("referral_count", -1).limit(limit)
            
            leaderboard = []
            rank = 1
            
            async for user_data in cursor:
                user_data["rank"] = rank
                leaderboard.append(user_data)
                rank += 1
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting referral leaderboard: {e}")
            return []
    
    async def get_referral_statistics(self) -> Dict[str, Any]:
        """Get global referral statistics"""
        try:
            # Total referrals and referral points
            pipeline = [
                {"$group": {
                    "_id": None,
                    "total_referrals": {"$sum": "$referral_count"},
                    "total_referral_points": {"$sum": "$referral_points"},
                    "users_with_referrals": {
                        "$sum": {"$cond": [{"$gt": ["$referral_count", 0]}, 1, 0]}
                    },
                    "referred_users": {
                        "$sum": {"$cond": [{"$ne": ["$referred_by", None]}, 1, 0]}
                    }
                }}
            ]
            
            result = await self.users_collection.aggregate(pipeline).to_list(1)
            
            if result:
                stats = result[0]
                
                # Calculate average referrals per active user
                users_with_referrals = stats.get("users_with_referrals", 0)
                total_referrals = stats.get("total_referrals", 0)
                avg_referrals = round(total_referrals / users_with_referrals, 2) if users_with_referrals > 0 else 0
                
                return {
                    "total_referrals": total_referrals,
                    "total_referral_points": stats.get("total_referral_points", 0),
                    "users_with_referrals": users_with_referrals,
                    "referred_users": stats.get("referred_users", 0),
                    "average_referrals_per_user": avg_referrals
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting referral statistics: {e}")
            return {}
    
    async def validate_referral_code(self, referral_code: str) -> Tuple[bool, str]:
        """Validate a referral code"""
        try:
            if not referral_code or len(referral_code) != 8:
                return False, "Kode referral harus 8 karakter."
            
            user = await self.user_service.get_user_by_referral_code(referral_code)
            if not user:
                return False, "Kode referral tidak ditemukan."
            
            if user.is_banned:
                return False, "Kode referral tidak valid."
            
            return True, "Kode referral valid."
            
        except Exception as e:
            logger.error(f"Error validating referral code {referral_code}: {e}")
            return False, "Terjadi kesalahan saat validasi."
    
    async def generate_referral_link(self, user: User, bot_username: str) -> str:
        """Generate referral link for a user"""
        try:
            base_url = f"https://t.me/{bot_username}"
            referral_link = f"{base_url}?start=ref_{user.referral_code}"
            return referral_link
        except Exception as e:
            logger.error(f"Error generating referral link for user {user.user_id}: {e}")
            return ""
    
    async def get_referral_rewards_info(self) -> str:
        """Get information about referral rewards"""
        return f"""
🎁 **Sistem Referral**

💰 **Reward:**
• Anda: +{settings.REFERRAL_POINTS} poin referral
• Teman yang diundang: +{settings.REFERRAL_POINTS} poin referral

✨ **Keuntungan Poin Referral:**
• Tidak pernah expire
• Digunakan sebelum poin harian
• Bisa dikumpulkan tanpa batas

📋 **Cara Kerja:**
1. Bagikan link referral Anda
2. Teman klik link dan mulai chat dengan bot
3. Teman ketik kode referral saat diminta
4. Anda berdua langsung dapat poin!

🏆 **Tips:**
• Semakin banyak mengundang, semakin banyak poin
• Ajak teman aktif agar mereka terus menggunakan bot
• Gunakan poin untuk membuat gambar dengan AI

💡 Gunakan `/referral` untuk melihat statistik referral Anda!
        """.strip()
    
    async def reset_user_referral_stats(self, user_id: int) -> bool:
        """Reset user's referral statistics (admin function)"""
        try:
            result = await self.users_collection.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "referral_count": 0,
                        "referral_points": 0,
                        "referred_by": None
                    }
                }
            )
            
            # Also reset any users referred by this user
            await self.users_collection.update_many(
                {"referred_by": user_id},
                {"$unset": {"referred_by": ""}}
            )
            
            logger.info(f"Referral stats reset for user {user_id}")
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error resetting referral stats for user {user_id}: {e}")
            return False
