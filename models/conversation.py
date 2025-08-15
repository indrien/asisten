from datetime import datetime
from typing import List, Dict, Any, Optional
import pytz
from config.settings import settings

class Message:
    def __init__(self, role: str, content: str, message_type: str = "text", **kwargs):
        self.role = role  # "user" or "assistant"
        self.content = content
        self.message_type = message_type  # "text", "image", "audio"
        self.timestamp = kwargs.get('timestamp', self._get_current_time())
        self.metadata = kwargs.get('metadata', {})
    
    def _get_current_time(self):
        """Get current time in WIB timezone"""
        tz = pytz.timezone(settings.TIMEZONE)
        return datetime.now(tz)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'role': self.role,
            'content': self.content,
            'message_type': self.message_type,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(**data)

class Conversation:
    def __init__(self, user_id: int, **kwargs):
        self.user_id = user_id
        self.messages: List[Message] = kwargs.get('messages', [])
        self.created_at = kwargs.get('created_at', self._get_current_time())
        self.updated_at = kwargs.get('updated_at', self._get_current_time())
        self.context = kwargs.get('context', {})
        
        # Load messages from dict if provided
        if 'messages' in kwargs and isinstance(kwargs['messages'][0] if kwargs['messages'] else None, dict):
            self.messages = [Message.from_dict(msg) for msg in kwargs['messages']]
    
    def _get_current_time(self):
        """Get current time in WIB timezone"""
        tz = pytz.timezone(settings.TIMEZONE)
        return datetime.now(tz)
    
    def add_message(self, role: str, content: str, message_type: str = "text", **kwargs):
        """Add a message to the conversation"""
        message = Message(role, content, message_type, **kwargs)
        self.messages.append(message)
        self.updated_at = self._get_current_time()
        
        # Keep only the last MAX_MEMORY_MESSAGES messages
        if len(self.messages) > settings.MAX_MEMORY_MESSAGES:
            self.messages = self.messages[-settings.MAX_MEMORY_MESSAGES:]
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get recent messages for context"""
        return self.messages[-limit:] if limit > 0 else self.messages
    
    def get_gemini_format(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get messages in Gemini API format"""
        recent_messages = self.get_recent_messages(limit)
        formatted_messages = []
        
        for msg in recent_messages:
            if msg.message_type == "text":
                formatted_messages.append({
                    "role": "user" if msg.role == "user" else "model",
                    "parts": [{"text": msg.content}]
                })
        
        return formatted_messages
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.messages = []
        self.updated_at = self._get_current_time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary"""
        return {
            'user_id': self.user_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create conversation from dictionary"""
        return cls(**data)
    
    def get_stats(self) -> Dict[str, int]:
        """Get conversation statistics"""
        user_messages = sum(1 for msg in self.messages if msg.role == "user")
        assistant_messages = sum(1 for msg in self.messages if msg.role == "assistant")
        image_messages = sum(1 for msg in self.messages if msg.message_type == "image")
        audio_messages = sum(1 for msg in self.messages if msg.message_type == "audio")
        
        return {
            'total_messages': len(self.messages),
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'image_messages': image_messages,
            'audio_messages': audio_messages
        }
