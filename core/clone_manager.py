import asyncio
import logging
from typing import Dict, List, Optional
from core.bot import TelegramBot
from models.clone_bot import CloneBot
from config.database import database
from config.settings import settings

logger = logging.getLogger(__name__)

class CloneManager:
    def __init__(self):
        self.active_clones: Dict[str, TelegramBot] = {}
        self.clone_tasks: Dict[str, asyncio.Task] = {}
    
    async def create_clone_bot(self, 
                             bot_token: str, 
                             creator_id: int, 
                             admin_id: int) -> Optional[CloneBot]:
        """Create a new clone bot"""
        try:
            # Validate bot token by creating a temporary client
            test_bot = TelegramBot(
                bot_token=bot_token,
                api_id=settings.API_ID,
                api_hash=settings.API_HASH,
                is_clone=True,
                clone_admin_id=admin_id
            )
            
            await test_bot.initialize()
            bot_info = test_bot.bot_info
            await test_bot.stop()
            
            # Check if clone already exists
            clone_collection = database.get_collection(settings.CLONE_BOTS_COLLECTION)
            existing = await clone_collection.find_one({"bot_token": bot_token})
            if existing:
                raise ValueError("Bot token sudah digunakan")
            
            # Check if user already has a clone bot
            user_clone = await clone_collection.find_one({"creator_id": creator_id})
            if user_clone:
                raise ValueError("Anda sudah memiliki bot clone")
            
            # Create clone bot record
            clone_bot = CloneBot(
                bot_token=bot_token,
                creator_id=creator_id,
                admin_id=admin_id,
                bot_username=bot_info.username,
                bot_name=bot_info.first_name
            )
            
            # Save to database
            await clone_collection.insert_one(clone_bot.to_dict())
            
            # Update user record
            users_collection = database.get_collection(settings.USERS_COLLECTION)
            await users_collection.update_one(
                {"user_id": creator_id},
                {
                    "$set": {
                        "has_clone_bot": True,
                        "clone_bot_id": bot_info.id
                    }
                }
            )
            
            logger.info(f"Clone bot created: @{bot_info.username} by user {creator_id}")
            return clone_bot
            
        except Exception as e:
            logger.error(f"Failed to create clone bot: {e}")
            raise
    
    async def start_clone_bot(self, bot_token: str) -> bool:
        """Start a clone bot"""
        try:
            if bot_token in self.active_clones:
                return True  # Already running
            
            # Get clone bot info from database
            clone_collection = database.get_collection(settings.CLONE_BOTS_COLLECTION)
            clone_data = await clone_collection.find_one({"bot_token": bot_token})
            
            if not clone_data or not clone_data.get('is_active', True):
                return False
            
            # Create and initialize clone bot
            clone_bot = TelegramBot(
                bot_token=bot_token,
                api_id=settings.API_ID,
                api_hash=settings.API_HASH,
                is_clone=True,
                clone_admin_id=clone_data['admin_id']
            )
            
            await clone_bot.initialize()
            
            # Store active clone
            self.active_clones[bot_token] = clone_bot
            
            # Create a task to run the clone bot
            task = asyncio.create_task(self._run_clone_bot(clone_bot))
            self.clone_tasks[bot_token] = task
            
            logger.info(f"Clone bot started: {clone_data['bot_username']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start clone bot {bot_token}: {e}")
            return False
    
    async def stop_clone_bot(self, bot_token: str) -> bool:
        """Stop a clone bot"""
        try:
            if bot_token not in self.active_clones:
                return True  # Not running
            
            # Stop the bot
            clone_bot = self.active_clones[bot_token]
            await clone_bot.stop()
            
            # Cancel the task
            if bot_token in self.clone_tasks:
                task = self.clone_tasks[bot_token]
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                del self.clone_tasks[bot_token]
            
            # Remove from active clones
            del self.active_clones[bot_token]
            
            logger.info(f"Clone bot stopped: {bot_token}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop clone bot {bot_token}: {e}")
            return False
    
    async def _run_clone_bot(self, clone_bot: TelegramBot):
        """Run a clone bot (this keeps it alive)"""
        try:
            # The bot is already started, this just keeps the task alive
            while True:
                await asyncio.sleep(60)  # Check every minute
                
                # You can add health checks here
                if not clone_bot.client.is_connected:
                    logger.warning(f"Clone bot disconnected: {clone_bot.bot_info.username}")
                    break
                    
        except asyncio.CancelledError:
            logger.info(f"Clone bot task cancelled: {clone_bot.bot_info.username}")
        except Exception as e:
            logger.error(f"Error in clone bot task: {e}")
    
    async def start_all_clone_bots(self):
        """Start all active clone bots from database"""
        try:
            clone_collection = database.get_collection(settings.CLONE_BOTS_COLLECTION)
            active_clones = clone_collection.find({"is_active": True})
            
            started_count = 0
            async for clone_data in active_clones:
                try:
                    success = await self.start_clone_bot(clone_data['bot_token'])
                    if success:
                        started_count += 1
                except Exception as e:
                    logger.error(f"Failed to start clone bot {clone_data['bot_username']}: {e}")
            
            logger.info(f"Started {started_count} clone bots")
            
        except Exception as e:
            logger.error(f"Failed to start clone bots: {e}")
    
    async def stop_all_clone_bots(self):
        """Stop all running clone bots"""
        try:
            tasks = []
            for bot_token in list(self.active_clones.keys()):
                tasks.append(self.stop_clone_bot(bot_token))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("All clone bots stopped")
            
        except Exception as e:
            logger.error(f"Failed to stop clone bots: {e}")
    
    async def get_clone_bot_stats(self, creator_id: int) -> Optional[Dict]:
        """Get clone bot statistics for a user"""
        try:
            clone_collection = database.get_collection(settings.CLONE_BOTS_COLLECTION)
            clone_data = await clone_collection.find_one({"creator_id": creator_id})
            
            if not clone_data:
                return None
            
            clone_bot = CloneBot.from_dict(clone_data)
            is_running = clone_data['bot_token'] in self.active_clones
            
            return {
                'clone_bot': clone_bot,
                'is_running': is_running,
                'stats': clone_bot.get_stats_summary()
            }
            
        except Exception as e:
            logger.error(f"Failed to get clone bot stats: {e}")
            return None
    
    async def delete_clone_bot(self, creator_id: int) -> bool:
        """Delete a clone bot"""
        try:
            clone_collection = database.get_collection(settings.CLONE_BOTS_COLLECTION)
            clone_data = await clone_collection.find_one({"creator_id": creator_id})
            
            if not clone_data:
                return False
            
            # Stop the bot if it's running
            await self.stop_clone_bot(clone_data['bot_token'])
            
            # Delete from database
            await clone_collection.delete_one({"creator_id": creator_id})
            
            # Update user record
            users_collection = database.get_collection(settings.USERS_COLLECTION)
            await users_collection.update_one(
                {"user_id": creator_id},
                {
                    "$set": {
                        "has_clone_bot": False,
                        "clone_bot_id": None
                    }
                }
            )
            
            logger.info(f"Clone bot deleted for user {creator_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete clone bot: {e}")
            return False
    
    def get_running_clones_count(self) -> int:
        """Get number of running clone bots"""
        return len(self.active_clones)
    
    async def get_all_clone_stats(self) -> Dict:
        """Get statistics for all clone bots"""
        try:
            clone_collection = database.get_collection(settings.CLONE_BOTS_COLLECTION)
            
            total_clones = await clone_collection.count_documents({})
            active_clones = await clone_collection.count_documents({"is_active": True})
            running_clones = self.get_running_clones_count()
            
            return {
                'total_clones': total_clones,
                'active_clones': active_clones,
                'running_clones': running_clones
            }
            
        except Exception as e:
            logger.error(f"Failed to get clone stats: {e}")
            return {}

# Global clone manager instance
clone_manager = CloneManager()
