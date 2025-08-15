import re
import hashlib
import secrets
import string
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import pytz
from config.settings import settings

logger = logging.getLogger(__name__)

def validate_bot_token(token: str) -> bool:
    """Validate Telegram bot token format"""
    try:
        if not token or ':' not in token:
            return False
        
        parts = token.split(':')
        if len(parts) != 2:
            return False
        
        bot_id, hash_part = parts
        
        # Bot ID should be numeric and at least 8 digits
        if not bot_id.isdigit() or len(bot_id) < 8:
            return False
        
        # Hash part should be alphanumeric and 35 characters
        if len(hash_part) != 35 or not re.match(r'^[A-Za-z0-9_-]+$', hash_part):
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating bot token: {e}")
        return False

def validate_user_id(user_id: Union[str, int]) -> bool:
    """Validate Telegram user ID"""
    try:
        if isinstance(user_id, str):
            if not user_id.isdigit():
                return False
            user_id = int(user_id)
        
        # Telegram user IDs are typically 9-10 digits
        return 100000000 <= user_id <= 9999999999
        
    except Exception:
        return False

def format_number(number: int) -> str:
    """Format number with thousand separators"""
    try:
        return f"{number:,}"
    except Exception:
        return str(number)

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    try:
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        elif seconds < 86400:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            return f"{hours}h {remaining_minutes}m"
        else:
            days = seconds // 86400
            remaining_hours = (seconds % 86400) // 3600
            return f"{days}d {remaining_hours}h"
    except Exception:
        return "Unknown"

def get_current_time_wib() -> datetime:
    """Get current time in WIB timezone"""
    try:
        tz = pytz.timezone(settings.TIMEZONE)
        return datetime.now(tz)
    except Exception:
        return datetime.now()

def format_datetime(dt: datetime, format_str: str = "%d/%m/%Y %H:%M") -> str:
    """Format datetime to string"""
    try:
        if dt.tzinfo is None:
            tz = pytz.timezone(settings.TIMEZONE)
            dt = tz.localize(dt)
        return dt.strftime(format_str)
    except Exception:
        return "Unknown"

def time_until_midnight_wib() -> dict:
    """Get time remaining until midnight WIB"""
    try:
        tz = pytz.timezone(settings.TIMEZONE)
        now = datetime.now(tz)
        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        time_until = tomorrow - now
        
        hours = int(time_until.total_seconds() // 3600)
        minutes = int((time_until.total_seconds() % 3600) // 60)
        seconds = int(time_until.total_seconds() % 60)
        
        return {
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "total_seconds": int(time_until.total_seconds()),
            "text": f"{hours}h {minutes}m"
        }
    except Exception:
        return {"hours": 0, "minutes": 0, "seconds": 0, "total_seconds": 0, "text": "Unknown"}

def generate_referral_code(length: int = 8) -> str:
    """Generate random referral code"""
    try:
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    except Exception:
        return ''.join(secrets.choice(string.ascii_uppercase) for _ in range(length))

def hash_string(text: str, salt: str = "") -> str:
    """Hash string with optional salt"""
    try:
        combined = f"{text}{salt}"
        return hashlib.sha256(combined.encode()).hexdigest()
    except Exception:
        return hashlib.md5(text.encode()).hexdigest()

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length"""
    try:
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    except Exception:
        return str(text)

def clean_html(text: str) -> str:
    """Remove HTML tags from text"""
    try:
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    except Exception:
        return text

def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    try:
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text
    except Exception:
        return text

def parse_command_args(text: str) -> List[str]:
    """Parse command arguments from text"""
    try:
        # Split by spaces but keep quoted strings together
        import shlex
        return shlex.split(text)
    except Exception:
        # Fallback to simple split
        return text.split()

def is_valid_username(username: str) -> bool:
    """Validate Telegram username format"""
    try:
        if not username:
            return False
        
        # Remove @ if present
        username = username.lstrip('@')
        
        # Username should be 5-32 characters, start with letter, contain only letters, digits, underscores
        pattern = r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$'
        return bool(re.match(pattern, username))
        
    except Exception:
        return False

def extract_user_mention(text: str) -> Optional[int]:
    """Extract user ID from mention or text"""
    try:
        # Check for user ID in text
        user_id_match = re.search(r'\b(\d{8,10})\b', text)
        if user_id_match:
            user_id = int(user_id_match.group(1))
            if validate_user_id(user_id):
                return user_id
        
        return None
        
    except Exception:
        return None

def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format"""
    try:
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"
    except Exception:
        return f"{size_bytes} B"

def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """Create a progress bar"""
    try:
        if total == 0:
            return "█" * length
        
        progress = current / total
        filled_length = int(length * progress)
        
        bar = "█" * filled_length + "░" * (length - filled_length)
        percentage = round(progress * 100, 1)
        
        return f"{bar} {percentage}%"
    except Exception:
        return "█" * length

def generate_unique_id(prefix: str = "") -> str:
    """Generate unique ID with optional prefix"""
    try:
        import uuid
        unique_id = str(uuid.uuid4()).replace('-', '')[:8]
        return f"{prefix}{unique_id}" if prefix else unique_id
    except Exception:
        import time
        import random
        return f"{prefix}{int(time.time())}{random.randint(100, 999)}"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    try:
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            max_name_length = 255 - len(ext) - 1
            filename = f"{name[:max_name_length]}.{ext}" if ext else name[:255]
        
        return filename
    except Exception:
        return "file"

def calculate_percentage(part: int, total: int) -> float:
    """Calculate percentage with safe division"""
    try:
        if total == 0:
            return 0.0
        return round((part / total) * 100, 2)
    except Exception:
        return 0.0

def split_text_by_length(text: str, max_length: int = 4096) -> List[str]:
    """Split text into chunks by maximum length"""
    try:
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        while len(text) > max_length:
            # Find last newline before max_length
            split_pos = text.rfind('\n', 0, max_length)
            if split_pos == -1:
                split_pos = max_length
            
            chunks.append(text[:split_pos])
            text = text[split_pos:].lstrip('\n')
        
        if text:
            chunks.append(text)
        
        return chunks
    except Exception:
        return [text]

def get_emoji_flag(country_code: str) -> str:
    """Get emoji flag for country code"""
    try:
        # Convert country code to flag emoji
        country_code = country_code.upper()
        flag = ''.join(chr(0x1F1E6 + ord(c) - ord('A')) for c in country_code)
        return flag
    except Exception:
        return "🏳️"

def validate_url(url: str) -> bool:
    """Validate URL format"""
    try:
        import re
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    except Exception:
        return False
