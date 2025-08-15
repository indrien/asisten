import asyncio
import logging
from functools import wraps
from typing import Callable, Any
from pyrogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)

def admin_required(func: Callable) -> Callable:
    """Decorator to check if user is admin"""
    @wraps(func)
    async def wrapper(self, message_or_query, *args, **kwargs):
        try:
            if isinstance(message_or_query, Message):
                user_id = message_or_query.from_user.id
                chat_id = message_or_query.chat.id
            elif isinstance(message_or_query, CallbackQuery):
                user_id = message_or_query.from_user.id
                chat_id = message_or_query.message.chat.id
            else:
                return
            
            # Check if user is admin
            if not self.bot.is_admin(user_id):
                if isinstance(message_or_query, Message):
                    await self.bot.send_message_safe(
                        chat_id,
                        "❌ Anda tidak memiliki akses admin."
                    )
                elif isinstance(message_or_query, CallbackQuery):
                    await message_or_query.answer(
                        "❌ Anda tidak memiliki akses admin.",
                        show_alert=True
                    )
                return
            
            return await func(self, message_or_query, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in admin_required decorator: {e}")
            
    return wrapper

def owner_required(func: Callable) -> Callable:
    """Decorator to check if user is owner"""
    @wraps(func)
    async def wrapper(self, message_or_query, *args, **kwargs):
        try:
            if isinstance(message_or_query, Message):
                user_id = message_or_query.from_user.id
                chat_id = message_or_query.chat.id
            elif isinstance(message_or_query, CallbackQuery):
                user_id = message_or_query.from_user.id
                chat_id = message_or_query.message.chat.id
            else:
                return
            
            # Check if user is owner
            if not self.bot.is_owner(user_id):
                if isinstance(message_or_query, Message):
                    await self.bot.send_message_safe(
                        chat_id,
                        "❌ Anda tidak memiliki akses owner."
                    )
                elif isinstance(message_or_query, CallbackQuery):
                    await message_or_query.answer(
                        "❌ Anda tidak memiliki akses owner.",
                        show_alert=True
                    )
                return
            
            return await func(self, message_or_query, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in owner_required decorator: {e}")
            
    return wrapper

def rate_limit(calls: int = 5, period: int = 60):
    """Simple rate limiting decorator"""
    def decorator(func: Callable) -> Callable:
        # Store call times for each user
        call_times = {}
        
        @wraps(func)
        async def wrapper(self, message_or_query, *args, **kwargs):
            try:
                if isinstance(message_or_query, Message):
                    user_id = message_or_query.from_user.id
                    chat_id = message_or_query.chat.id
                elif isinstance(message_or_query, CallbackQuery):
                    user_id = message_or_query.from_user.id
                    chat_id = message_or_query.message.chat.id
                else:
                    return
                
                import time
                current_time = time.time()
                
                # Clean old entries
                if user_id in call_times:
                    call_times[user_id] = [
                        call_time for call_time in call_times[user_id]
                        if current_time - call_time < period
                    ]
                else:
                    call_times[user_id] = []
                
                # Check rate limit
                if len(call_times[user_id]) >= calls:
                    if isinstance(message_or_query, Message):
                        await self.bot.send_message_safe(
                            chat_id,
                            f"⏳ Rate limit exceeded. Tunggu {period} detik."
                        )
                    elif isinstance(message_or_query, CallbackQuery):
                        await message_or_query.answer(
                            f"⏳ Rate limit exceeded. Tunggu {period} detik.",
                            show_alert=True
                        )
                    return
                
                # Add current call
                call_times[user_id].append(current_time)
                
                return await func(self, message_or_query, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in rate_limit decorator: {e}")
                
        return wrapper
    return decorator

def error_handler(func: Callable) -> Callable:
    """Decorator to handle and log errors"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            
            # Try to send error message to user if possible
            try:
                if len(args) >= 2:
                    message_or_query = args[1]
                    if isinstance(message_or_query, Message):
                        await args[0].bot.send_message_safe(
                            message_or_query.chat.id,
                            "❌ Terjadi kesalahan. Silakan coba lagi nanti."
                        )
                    elif isinstance(message_or_query, CallbackQuery):
                        await message_or_query.answer(
                            "❌ Terjadi kesalahan. Silakan coba lagi nanti.",
                            show_alert=True
                        )
            except:
                pass
                
    return wrapper

def typing_action(func: Callable) -> Callable:
    """Decorator to send typing action before executing function"""
    @wraps(func)
    async def wrapper(self, message, *args, **kwargs):
        try:
            if isinstance(message, Message):
                # Send typing action
                asyncio.create_task(
                    self.bot.client.send_chat_action(message.chat.id, "typing")
                )
            
            return await func(self, message, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in typing_action decorator: {e}")
            return await func(self, message, *args, **kwargs)
            
    return wrapper

def log_user_action(action: str):
    """Decorator to log user actions"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, message_or_query, *args, **kwargs):
            try:
                if isinstance(message_or_query, Message):
                    user_id = message_or_query.from_user.id
                    username = message_or_query.from_user.username
                elif isinstance(message_or_query, CallbackQuery):
                    user_id = message_or_query.from_user.id
                    username = message_or_query.from_user.username
                else:
                    user_id = "unknown"
                    username = "unknown"
                
                logger.info(f"User action: {action} by {user_id} (@{username})")
                
                return await func(self, message_or_query, *args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in log_user_action decorator: {e}")
                return await func(self, message_or_query, *args, **kwargs)
                
        return wrapper
    return decorator

def banned_check(func: Callable) -> Callable:
    """Decorator to check if user is banned"""
    @wraps(func)
    async def wrapper(self, message_or_query, *args, **kwargs):
        try:
            if isinstance(message_or_query, Message):
                user_id = message_or_query.from_user.id
                chat_id = message_or_query.chat.id
            elif isinstance(message_or_query, CallbackQuery):
                user_id = message_or_query.from_user.id
                chat_id = message_or_query.message.chat.id
            else:
                return
            
            # Get user and check ban status
            user = await self.bot.user_service.get_user(user_id)
            if user and user.is_banned:
                if isinstance(message_or_query, Message):
                    await self.bot.send_message_safe(
                        chat_id,
                        "❌ Anda telah dibanned dari menggunakan bot ini."
                    )
                elif isinstance(message_or_query, CallbackQuery):
                    await message_or_query.answer(
                        "❌ Anda telah dibanned dari menggunakan bot ini.",
                        show_alert=True
                    )
                return
            
            return await func(self, message_or_query, *args, **kwargs)
            
        except Exception as e:
            logger.error(f"Error in banned_check decorator: {e}")
            
    return wrapper
