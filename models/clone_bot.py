from datetime import datetime
from typing import Dict, Any, Optional
import pytz
from config.settings import settings

class CloneBot:
    def __init__(self, **kwargs):
        self.bot_token = kwargs.get('bot_token')
        self.creator_id = kwargs.get('creator_id')
        self.admin_id = kwargs.get('admin_id')
        self.bot_username = kwargs.get('bot_username')
        self.bot_name = kwargs.get('bot_name')
        self.is_active = kwargs.get('is_active', True)
        self.created_at = kwargs.get('created_at', self._get_current_time())
        self.last_activity = kwargs.get('last_activity', self._get_current_time())
        
        # Statistics
        self.total_users = kwargs.get('total_users', 0)
        self.total_messages = kwargs.get('total_messages', 0)
        self.total_images = kwargs.get('total_images', 0)
        
        # Settings specific to clone bot
        self.custom_welcome = kwargs.get('custom_welcome')
        self.custom_help = kwargs.get('custom_help')
        self.settings = kwargs.get('settings', {})
    
    def _get_current_time(self):
        """Get current time in WIB timezone"""
        tz = pytz.timezone(settings.TIMEZONE)
        return datetime.now(tz)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert clone bot to dictionary"""
        return {
            'bot_token': self.bot_token,
            'creator_id': self.creator_id,
            'admin_id': self.admin_id,
            'bot_username': self.bot_username,
            'bot_name': self.bot_name,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'last_activity': self.last_activity,
            'total_users': self.total_users,
            'total_messages': self.total_messages,
            'total_images': self.total_images,
            'custom_welcome': self.custom_welcome,
            'custom_help': self.custom_help,
            'settings': self.settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CloneBot':
        """Create clone bot from dictionary"""
        return cls(**data)
    
    def update_activity(self):
        """Update last activity time"""
        self.last_activity = self._get_current_time()
    
    def increment_stats(self, stat_type: str):
        """Increment statistics"""
        if stat_type == "users":
            self.total_users += 1
        elif stat_type == "messages":
            self.total_messages += 1
        elif stat_type == "images":
            self.total_images += 1
        
        self.update_activity()
    
    def deactivate(self):
        """Deactivate the clone bot"""
        self.is_active = False
        self.update_activity()
    
    def activate(self):
        """Activate the clone bot"""
        self.is_active = True
        self.update_activity()
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update bot settings"""
        self.settings.update(new_settings)
        self.update_activity()
    
    def get_stats_summary(self) -> str:
        """Get formatted statistics summary"""
        return f"""
📊 **Statistik Bot Clone**

👥 Total Users: {self.total_users:,}
💬 Total Messages: {self.total_messages:,}
🖼 Total Images: {self.total_images:,}

📅 Dibuat: {self.created_at.strftime('%d/%m/%Y %H:%M')}
🕐 Aktivitas Terakhir: {self.last_activity.strftime('%d/%m/%Y %H:%M')}
📱 Status: {'Aktif' if self.is_active else 'Nonaktif'}
        """.strip()
