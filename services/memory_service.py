import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, time, timezone
import pytz
from models.conversation import Conversation, Message
from config.database import database
from config.settings import settings

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self):
        self.conversations_collection = None
    
    async def initialize(self):
        """Initialize the memory service"""
        self.conversations_collection = database.get_collection(settings.CONVERSATIONS_COLLECTION)
    
    async def get_conversation(self, user_id: int) -> Optional[Conversation]:
        """Get user's conversation"""
        try:
            conversation_data = await self.conversations_collection.find_one({"user_id": user_id})
            if conversation_data:
                return Conversation.from_dict(conversation_data)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation for user {user_id}: {e}")
            return None
    
    async def create_conversation(self, user_id: int) -> Conversation:
        """Create a new conversation"""
        try:
            conversation = Conversation(user_id=user_id)
            
            # Insert to database
            await self.conversations_collection.insert_one(conversation.to_dict())
            
            logger.info(f"New conversation created for user: {user_id}")
            return conversation
            
        except Exception as e:
            logger.error(f"Error creating conversation for user {user_id}: {e}")
            raise
    
    async def get_or_create_conversation(self, user_id: int) -> Conversation:
        """Get existing conversation or create new one"""
        conversation = await self.get_conversation(user_id)
        if not conversation:
            conversation = await self.create_conversation(user_id)
        return conversation
    
    async def add_message(self, 
                         user_id: int, 
                         role: str, 
                         content: str, 
                         message_type: str = "text",
                         **kwargs) -> bool:
        """Add a message to user's conversation"""
        try:
            conversation = await self.get_or_create_conversation(user_id)
            conversation.add_message(role, content, message_type, **kwargs)
            
            # Update in database
            result = await self.conversations_collection.update_one(
                {"user_id": user_id},
                {"$set": conversation.to_dict()},
                upsert=True
            )
            
            return result.modified_count > 0 or result.upserted_id is not None
            
        except Exception as e:
            logger.error(f"Error adding message for user {user_id}: {e}")
            return False
    
    async def get_conversation_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history in Gemini format"""
        try:
            conversation = await self.get_conversation(user_id)
            if conversation:
                return conversation.get_gemini_format(limit)
            return []
        except Exception as e:
            logger.error(f"Error getting conversation history for user {user_id}: {e}")
            return []
    
    async def clear_conversation(self, user_id: int) -> bool:
        """Clear user's conversation memory"""
        try:
            conversation = await self.get_conversation(user_id)
            if conversation:
                conversation.clear_memory()
                
                result = await self.conversations_collection.update_one(
                    {"user_id": user_id},
                    {"$set": conversation.to_dict()}
                )
                
                logger.info(f"Conversation cleared for user: {user_id}")
                return result.modified_count > 0
            return True
            
        except Exception as e:
            logger.error(f"Error clearing conversation for user {user_id}: {e}")
            return False
    
    async def get_conversation_stats(self, user_id: int) -> Optional[Dict[str, int]]:
        """Get conversation statistics for a user"""
        try:
            conversation = await self.get_conversation(user_id)
            if conversation:
                return conversation.get_stats()
            return None
        except Exception as e:
            logger.error(f"Error getting conversation stats for user {user_id}: {e}")
            return None
    
    async def get_recent_messages(self, user_id: int, limit: int = 5) -> List[Message]:
        """Get recent messages for a user"""
        try:
            conversation = await self.get_conversation(user_id)
            if conversation:
                return conversation.get_recent_messages(limit)
            return []
        except Exception as e:
            logger.error(f"Error getting recent messages for user {user_id}: {e}")
            return []
    
    async def search_messages(self, 
                            user_id: int, 
                            query: str, 
                            limit: int = 20) -> List[Message]:
        """Search messages in user's conversation"""
        try:
            conversation = await self.get_conversation(user_id)
            if not conversation:
                return []
            
            matching_messages = []
            for message in conversation.messages:
                if query.lower() in message.content.lower():
                    matching_messages.append(message)
                    if len(matching_messages) >= limit:
                        break
            
            return matching_messages
            
        except Exception as e:
            logger.error(f"Error searching messages for user {user_id}: {e}")
            return []
    
    async def get_global_memory_stats(self) -> Dict[str, Any]:
        """Get global memory statistics"""
        try:
            total_conversations = await self.conversations_collection.count_documents({})
            
            # Count total messages
            pipeline = [
                {"$project": {"message_count": {"$size": "$messages"}}},
                {"$group": {"_id": None, "total_messages": {"$sum": "$message_count"}}}
            ]
            
            result = await self.conversations_collection.aggregate(pipeline).to_list(1)
            total_messages = result[0]["total_messages"] if result else 0
            
            # Get active conversations (last 24 hours)
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(days=1)
            active_conversations = await self.conversations_collection.count_documents({
                "updated_at": {"$gte": yesterday}
            })
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "active_conversations": active_conversations,
                "avg_messages_per_conversation": round(total_messages / total_conversations, 2) if total_conversations > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting global memory stats: {e}")
            return {}
    
    async def backup_conversation(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Backup user's conversation"""
        try:
            conversation = await self.get_conversation(user_id)
            if conversation:
                return conversation.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error backing up conversation for user {user_id}: {e}")
            return None
    
    async def restore_conversation(self, user_id: int, backup_data: Dict[str, Any]) -> bool:
        """Restore user's conversation from backup"""
        try:
            conversation = Conversation.from_dict(backup_data)
            conversation.user_id = user_id  # Ensure correct user_id
            
            result = await self.conversations_collection.update_one(
                {"user_id": user_id},
                {"$set": conversation.to_dict()},
                upsert=True
            )
            
            logger.info(f"Conversation restored for user: {user_id}")
            return result.modified_count > 0 or result.upserted_id is not None
            
        except Exception as e:
            logger.error(f"Error restoring conversation for user {user_id}: {e}")
            return False
    
    async def cleanup_old_conversations(self, days: int = 90) -> int:
        """Clean up old conversations (maintenance function)"""
        try:
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Delete conversations older than cutoff_date with minimal activity
            result = await self.conversations_collection.delete_many({
                "updated_at": {"$lt": cutoff_date},
                "$expr": {"$lt": [{"$size": "$messages"}, 10]}  # Less than 10 messages
            })
            
            logger.info(f"Cleaned up {result.deleted_count} old conversations")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old conversations: {e}")
            return 0
    
    async def optimize_memory_usage(self, user_id: int) -> bool:
        """Optimize memory usage for a user by summarizing old messages"""
        try:
            conversation = await self.get_conversation(user_id)
            if not conversation or len(conversation.messages) <= settings.MAX_MEMORY_MESSAGES:
                return True
            
            # Keep recent messages and summarize the rest
            recent_messages = conversation.messages[-settings.MAX_MEMORY_MESSAGES//2:]
            old_messages = conversation.messages[:-settings.MAX_MEMORY_MESSAGES//2]
            
            if old_messages:
                # Create a summary message
                summary_text = f"Ringkasan percakapan sebelumnya: {len(old_messages)} pesan telah diringkas untuk mengoptimalkan memori."
                
                # Create new conversation with summary + recent messages
                conversation.messages = [
                    Message("assistant", summary_text, "text", metadata={"type": "summary"})
                ] + recent_messages
                
                # Update in database
                result = await self.conversations_collection.update_one(
                    {"user_id": user_id},
                    {"$set": conversation.to_dict()}
                )
                
                logger.info(f"Memory optimized for user {user_id}: {len(old_messages)} messages summarized")
                return result.modified_count > 0
            
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing memory for user {user_id}: {e}")
            return False
