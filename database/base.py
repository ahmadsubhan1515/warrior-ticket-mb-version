"""
Database abstraction layer
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager(ABC):
    """Abstract database manager"""
    
    @abstractmethod
    async def initialize(self):
        """Initialize database"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close database connection"""
        pass
    
    @abstractmethod
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ticket"""
        pass
    
    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID"""
        pass
    
    @abstractmethod
    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Get ticket by channel ID"""
        pass
    
    @abstractmethod
    async def get_active_tickets_by_user(self, user_id: int, guild_id: int) -> List[Dict[str, Any]]:
        """Get active tickets by user"""
        pass
    
    @abstractmethod
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update ticket"""
        pass
    
    @abstractmethod
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete ticket"""
        pass
    
    @abstractmethod
    async def get_all_active_tickets(self) -> List[Dict[str, Any]]:
        """Get all active tickets"""
        pass
    
    @abstractmethod
    async def get_ticket_count(self, user_id: int, guild_id: int) -> int:
        """Get active ticket count for user"""
        pass
    
    @abstractmethod
    async def get_next_ticket_number(self) -> int:
        """Get next ticket number"""
        pass
    
    @abstractmethod
    async def add_ticket_user(self, ticket_id: str, user_id: int) -> bool:
        """Add user to ticket"""
        pass
    
    @abstractmethod
    async def remove_ticket_user(self, ticket_id: str, user_id: int) -> bool:
        """Remove user from ticket"""
        pass
    
    @abstractmethod
    async def get_ticket_users(self, ticket_id: str) -> List[int]:
        """Get users added to ticket"""
        pass
