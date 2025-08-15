from pyrogram import Client
from pyrogram.types import User as PyrogramUser
import logging
from typing import Dict, Any, Optional
from config.settings import settings
from config.database import database
from core.gemini_client import GeminiClient
from services.user_service import UserService
from services.memory_service import MemoryService
from services.point_service import PointService
from services.referral_service import ReferralService

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, 
                 bot_token: str = None, 
                 api_id: int = None, 
                 api_hash: str = None,
                 is_clone: bool = False,
                 clone_admin_id: int = None):
        
        # Use provided credentials or default from settings
        self.bot_token = bot_token or settings.BOT_TOKEN
        self.api_id = api_id or settings.API_ID
        self.api_hash = api_hash or settings.API_HASH
        
        # Bot properties
        self.is_clone = is_clone
        self.clone_admin_id = clone_admin_id
        self.bot_info = None
        
        # Initialize client
        self.client = Client(
            name=f"bot_{self.bot_token.split(':')[0]}" if self.bot_token else "main_bot",
            bot_token=self.bot_token,
            api_id=self.api_id,
            api_hash=self.api_hash
        )
        
        # Initialize services
        self.gemini_client = GeminiClient()
        self.user_service = UserService()
        self.memory_service = MemoryService()
        self.point_service = PointService()
        self.referral_service = ReferralService()
        
        # Bot statistics
        self.stats = {
            'total_users': 0,
            'total_messages': 0,
            'total_images': 0,
            'uptime_start': None
        }
    
    async def initialize(self):
        """Initialize bot and services"""
        try:
            # Connect to database
            await database.connect()
            
            # Start the client
            await self.client.start()
            
            # Get bot info
            self.bot_info = await self.client.get_me()
            logger.info(f"Bot started: @{self.bot_info.username}")
            
            # Initialize services
            await self.user_service.initialize()
            await self.memory_service.initialize()
            await self.point_service.initialize()
            await self.referral_service.initialize()
            
            # Load statistics
            await self._load_stats()
            
            # Register handlers
            await self._register_handlers()
            
            from datetime import datetime
            self.stats['uptime_start'] = datetime.now()
            
            logger.info("Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            raise
    
    async def _load_stats(self):
        """Load bot statistics"""
        try:
            # Count total users
            users_collection = database.get_collection(settings.USERS_COLLECTION)
            self.stats['total_users'] = await users_collection.count_documents({})
            
            # Count total messages (you might want to implement this differently)
            conversations_collection = database.get_collection(settings.CONVERSATIONS_COLLECTION)
            async for conversation in conversations_collection.find({}):
                self.stats['total_messages'] += len(conversation.get('messages', []))
            
            logger.info(f"Stats loaded: {self.stats}")
            
        except Exception as e:
            logger.error(f"Failed to load stats: {e}")
    
    async def _register_handlers(self):
        """Register message handlers"""
        from handlers.user_handlers import UserHandlers
        from handlers.admin_handlers import AdminHandlers
        from handlers.clone_handlers import CloneHandlers
        from handlers.callback_handlers import CallbackHandlers
        
        # Initialize handlers
        user_handlers = UserHandlers(self)
        admin_handlers = AdminHandlers(self)
        clone_handlers = CloneHandlers(self)
        callback_handlers = CallbackHandlers(self)
        
        # Register handlers with the client
        user_handlers.register_handlers()
        admin_handlers.register_handlers()
        callback_handlers.register_handlers()
        
        # Only register clone handlers for main bot (not clone bots)
        if not self.is_clone:
            clone_handlers.register_handlers()
    
    async def stop(self):
        """Stop the bot"""
        try:
            await self.client.stop()
            await database.close()
            logger.info("Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    def is_owner(self, user_id: int) -> bool:
        """Check if user is the owner"""
        return user_id == settings.OWNER_ID
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        if self.is_owner(user_id):
            return True
        
        # For clone bots, check if user is the clone admin
        if self.is_clone and user_id == self.clone_admin_id:
            return True
        
        # Check database for admin status
        # This will be implemented in user_service
        return False
    
    async def get_user_info(self, user_id: int) -> Optional[PyrogramUser]:
        """Get user information from Telegram"""
        try:
            return await self.client.get_users(user_id)
        except Exception as e:
            logger.error(f"Failed to get user info for {user_id}: {e}")
            return None
    
    async def send_message_safe(self, chat_id: int, text: str, **kwargs):
        """Send message with error handling"""
        try:
            # Split long messages
            if len(text) > settings.MAX_MESSAGE_LENGTH:
                messages = self._split_message(text)
                for msg in messages:
                    await self.client.send_message(chat_id, msg, **kwargs)
            else:
                await self.client.send_message(chat_id, text, **kwargs)
                
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
    
    def _split_message(self, text: str) -> list:
        """Split long message into smaller parts"""
        messages = []
        while len(text) > settings.MAX_MESSAGE_LENGTH:
            # Find last newline before limit
            split_pos = text.rfind('\n', 0, settings.MAX_MESSAGE_LENGTH)
            if split_pos == -1:
                split_pos = settings.MAX_MESSAGE_LENGTH
            
            messages.append(text[:split_pos])
            text = text[split_pos:].lstrip('\n')
        
        if text:
            messages.append(text)
        
        return messages
    
    async def update_stats(self, stat_type: str):
        """Update bot statistics"""
        if stat_type == "users":
            self.stats['total_users'] += 1
        elif stat_type == "messages":
            self.stats['total_messages'] += 1
        elif stat_type == "images":
            self.stats['total_images'] += 1
    
    def get_bot_info_text(self) -> str:
        """Get formatted bot information"""
        uptime = ""
        if self.stats['uptime_start']:
            from datetime import datetime
            uptime_delta = datetime.now() - self.stats['uptime_start']
            hours, remainder = divmod(int(uptime_delta.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            uptime = f"{hours}h {minutes}m"
        
        return f"""
🤖 **Informasi Bot**

📱 Username: @{self.bot_info.username}
👤 Nama: {self.bot_info.first_name}
🆔 ID: {self.bot_info.id}

📊 **Statistik**
👥 Total Users: {self.stats['total_users']:,}
💬 Total Messages: {self.stats['total_messages']:,}
🖼 Total Images: {self.stats['total_images']:,}
⏰ Uptime: {uptime}

🌟 Powered by Gemini AI 2.5
        """.strip()
