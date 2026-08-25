"""
Duration parsing service
"""

import re
from typing import Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DurationService:
    """Duration parser and manager"""
    
    # Supported time units (in seconds)
    UNITS = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    def __init__(self):
        self.pattern = re.compile(r'(\d+)([smhdw])')
    
    def parse_duration(self, duration_str: str) -> Optional[int]:
        """
        Parse duration string to seconds
        Examples: 30m, 1h, 2d, 1w, 1d2h, 2h30m
        
        Returns total seconds or None if invalid
        """
        if not duration_str or len(duration_str) > 100:
            return None
        
        duration_str = duration_str.lower().strip()
        matches = self.pattern.findall(duration_str)
        
        if not matches:
            return None
        
        # Check if the entire string was matched
        reconstructed = ''.join(f"{num}{unit}" for num, unit in matches)
        if reconstructed != duration_str:
            return None
        
        total_seconds = 0
        for value, unit in matches:
            value_int = int(value)
            unit_seconds = self.UNITS.get(unit, 0)
            
            if unit_seconds == 0:
                return None
            
            total_seconds += value_int * unit_seconds
        
        # Limit maximum duration (30 days)
        max_seconds = 30 * 24 * 3600
        if total_seconds > max_seconds:
            return None
        
        return total_seconds if total_seconds > 0 else None
    
    def format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human readable string"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m"
        elif seconds < 86400:
            return f"{seconds // 3600}h"
        elif seconds < 604800:
            return f"{seconds // 86400}d"
        else:
            return f"{seconds // 604800}w"
    
    def get_auto_close_time(self, duration_str: str) -> Optional[datetime]:
        """Get auto close datetime from duration string"""
        seconds = self.parse_duration(duration_str)
        if seconds is None:
            return None
        return datetime.utcnow() + timedelta(seconds=seconds)
    
    def get_remaining_seconds(self, target_time: datetime) -> int:
        """Get remaining seconds until target time"""
        if not target_time:
            return 0
        
        now = datetime.utcnow()
        if target_time <= now:
            return 0
        
        delta = target_time - now
        return int(delta.total_seconds())
    
    def validate_duration(self, duration_str: str) -> Tuple[bool, str]:
        """
        Validate duration string
        Returns (is_valid, error_message)
        """
        seconds = self.parse_duration(duration_str)
        
        if seconds is None:
            return False, "Invalid duration format. Use formats like: 1m, 30m, 1h, 2h, 12h, 1d, 7d, 1w"
        
        if seconds > 30 * 24 * 3600:
            return False, "Duration cannot exceed 30 days"
        
        return True, ""
