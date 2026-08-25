"""
MongoDB database implementation
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from .base import DatabaseManager

logger = logging.getLogger(__name__)

class MongoDB(DatabaseManager):
    """MongoDB database manager"""
    
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db: AsyncIOMotorDatabase = self.client[db_name]
        self.tickets = self.db['tickets']
        self.counters = self.db['counters']
    
    async def initialize(self):
        """Initialize MongoDB database"""
        # Create indexes
        await self.tickets.create_index('ticket_id', unique=True)
        await self.tickets.create_index('channel_id', unique=True)
        await self.tickets.create_index([('user_id', 1), ('guild_id', 1), ('status', 1)])
        await self.tickets.create_index('status')
        await self.tickets.create_index('auto_close_at')
        
        # Initialize counter if not exists
        counter = await self.counters.find_one({'_id': 'ticket_number'})
        if not counter:
            await self.counters.insert_one({'_id': 'ticket_number', 'seq': 0})
        
        logger.info("MongoDB database initialized")
    
    async def close(self):
        """Close database connection"""
        self.client.close()
        logger.info("MongoDB connection closed")
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ticket"""
        await self.tickets.insert_one(ticket_data)
        return ticket_data
    
    async def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID"""
        ticket = await self.tickets.find_one({'ticket_id': ticket_id})
        if ticket:
            ticket.pop('_id', None)
        return ticket
    
    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Get ticket by channel ID"""
        ticket = await self.tickets.find_one({'channel_id': channel_id})
        if ticket:
            ticket.pop('_id', None)
        return ticket
    
    async def get_active_tickets_by_user(self, user_id: int, guild_id: int) -> List[Dict[str, Any]]:
        """Get active tickets by user"""
        cursor = self.tickets.find({
            'user_id': user_id,
            'guild_id': guild_id,
            'status': 'open'
        })
        tickets = []
        async for ticket in cursor:
            ticket.pop('_id', None)
            tickets.append(ticket)
        return tickets
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update ticket"""
        result = await self.tickets.update_one(
            {'ticket_id': ticket_id},
            {'$set': updates}
        )
        return result.modified_count > 0 or result.matched_count > 0
    
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete ticket"""
        result = await self.tickets.delete_one({'ticket_id': ticket_id})
        return result.deleted_count > 0
    
    async def get_all_active_tickets(self) -> List[Dict[str, Any]]:
        """Get all active tickets"""
        cursor = self.tickets.find({'status': 'open'})
        tickets = []
        async for ticket in cursor:
            ticket.pop('_id', None)
            tickets.append(ticket)
        return tickets
    
    async def get_ticket_count(self, user_id: int, guild_id: int) -> int:
        """Get active ticket count for user"""
        return await self.tickets.count_documents({
            'user_id': user_id,
            'guild_id': guild_id,
            'status': 'open'
        })
    
    async def get_next_ticket_number(self) -> int:
        """Get next ticket number"""
        result = await self.counters.find_one_and_update(
            {'_id': 'ticket_number'},
            {'$inc': {'seq': 1}},
            return_document=True
        )
        return result['seq'] if result else 1
    
    async def add_ticket_user(self, ticket_id: str, user_id: int) -> bool:
        """Add user to ticket"""
        result = await self.tickets.update_one(
            {'ticket_id': ticket_id},
            {'$addToSet': {'added_users': user_id}}
        )
        return result.modified_count > 0 or result.matched_count > 0
    
    async def remove_ticket_user(self, ticket_id: str, user_id: int) -> bool:
        """Remove user from ticket"""
        result = await self.tickets.update_one(
            {'ticket_id': ticket_id},
            {'$pull': {'added_users': user_id}}
        )
        return result.modified_count > 0 or result.matched_count > 0
    
    async def get_ticket_users(self, ticket_id: str) -> List[int]:
        """Get users added to ticket"""
        ticket = await self.get_ticket(ticket_id)
        return ticket.get('added_users', []) if ticket else []
