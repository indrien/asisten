from datetime import datetime, timezone
from typing import Optional, Dict, Any
import pytz
from config.settings import settings

class User:
    def __init__(self, user_id: int, **kwargs):
        self.user_id = user_id
        self.username = kwargs.get('username')
        self.first_name = kwargs.get('first_name')
        self.last_name = kwargs.get('last_name')
        self.is_banned = kwargs.get('is_banned', False)
        self.is_admin = kwargs.get('is_admin', False)
        
        # Points system
        self.daily_points = kwargs.get('daily_points', settings.DAILY_POINTS)
        self.total_points_used = kwargs.get('total_points_used', 0)
        self.last_reset = kwargs.get('last_reset', self._get_current_time())
        
        # Referral system
        self.referral_code = kwargs.get('referral_code')
        self.referred_by = kwargs.get('referred_by')
        self.referral_count = kwargs.get('referral_count', 0)
        self.referral_points = kwargs.get('referral_points', 0)
        
        # Bot usage
        self.join_date = kwargs.get('join_date', self._get_current_time())
        self.last_activity = kwargs.get('last_activity', self._get_current_time())
        self.message_count = kwargs.get('message_count', 0)
        self.image_generated = kwargs.get('image_generated', 0)
        
        # Clone bot
        self.has_clone_bot = kwargs.get('has_clone_bot', False)
        self.clone_bot_id = kwargs.get('clone_bot_id')
    
    def _get_current_time(self):
        """Get current time in WIB timezone"""
        tz = pytz.timezone(settings.TIMEZONE)
        return datetime.now(tz)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_banned': self.is_banned,
            'is_admin': self.is_admin,
            'daily_points': self.daily_points,
            'total_points_used': self.total_points_used,
            'last_reset': self.last_reset,
            'referral_code': self.referral_code,
            'referred_by': self.referred_by,
            'referral_count': self.referral_count,
            'referral_points': self.referral_points,
            'join_date': self.join_date,
            'last_activity': self.last_activity,
            'message_count': self.message_count,
            'image_generated': self.image_generated,
            'has_clone_bot': self.has_clone_bot,
            'clone_bot_id': self.clone_bot_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """Create user object from dictionary"""
        return cls(**data)
    
    def can_generate_image(self) -> bool:
        """Check if user can generate image"""
        if self.is_banned:
            return False
        
        # Check if points need to be reset (daily reset at midnight WIB)
        self._check_daily_reset()
        
        return (self.daily_points + self.referral_points) > 0
    
    def use_point(self, point_type: str = 'daily') -> bool:
        """Use a point for image generation"""
        if not self.can_generate_image():
            return False
        
        if point_type == 'referral' and self.referral_points > 0:
            self.referral_points -= 1
        elif self.daily_points > 0:
            self.daily_points -= 1
        else:
            return False
        
        self.total_points_used += 1
        self.image_generated += 1
        return True
    
    def _check_daily_reset(self):
        """Check if daily points need to be reset"""
        tz = pytz.timezone(settings.TIMEZONE)
        now = datetime.now(tz)
        
        # Convert last_reset to WIB timezone if it's not already
        if self.last_reset.tzinfo is None:
            last_reset = tz.localize(self.last_reset)
        else:
            last_reset = self.last_reset.astimezone(tz)
        
        # Check if it's a new day (after midnight)
        if now.date() > last_reset.date():
            self.daily_points = settings.DAILY_POINTS
            self.last_reset = now
    
    def add_referral_points(self, points: int):
        """Add referral points"""
        self.referral_points += points
    
    def update_activity(self):
        """Update last activity time and increment message count"""
        self.last_activity = self._get_current_time()
        self.message_count += 1
