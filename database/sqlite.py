"""
SQLite database implementation
"""

import aiosqlite
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from .base import DatabaseManager

logger = logging.getLogger(__name__)

class SQLiteDB(DatabaseManager):
    """SQLite database manager"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    async def initialize(self):
        """Initialize SQLite database"""
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        
        await self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                ticket_number INTEGER UNIQUE,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER UNIQUE,
                user_id INTEGER NOT NULL,
                option_id INTEGER NOT NULL,
                ticket_type TEXT NOT NULL,
                category_id INTEGER,
                created_at TEXT NOT NULL,
                closed_at TEXT,
                closed_by INTEGER,
                status TEXT DEFAULT 'open',
                auto_close_at TEXT,
                close_reason TEXT,
                added_users TEXT DEFAULT '[]',
                transcript_path TEXT,
                metadata TEXT DEFAULT '{}'
            );
            
            CREATE INDEX IF NOT EXISTS idx_tickets_user ON tickets(user_id, guild_id, status);
            CREATE INDEX IF NOT EXISTS idx_tickets_channel ON tickets(channel_id);
            CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
            CREATE INDEX IF NOT EXISTS idx_tickets_auto_close ON tickets(auto_close_at);
        """)
        
        await self.conn.commit()
        logger.info("SQLite database initialized")
    
    async def close(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            logger.info("SQLite database connection closed")
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ticket"""
        async with self.conn.execute("""
            INSERT INTO tickets (
                ticket_id, ticket_number, guild_id, channel_id, user_id,
                option_id, ticket_type, category_id, created_at, status,
                auto_close_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticket_data['ticket_id'],
            ticket_data.get('ticket_number'),
            ticket_data['guild_id'],
            ticket_data['channel_id'],
            ticket_data['user_id'],
            ticket_data['option_id'],
            ticket_data['ticket_type'],
            ticket_data.get('category_id'),
            ticket_data['created_at'],
            ticket_data.get('status', 'open'),
            ticket_data.get('auto_close_at'),
            json.dumps(ticket_data.get('metadata', {}))
        ):
            await self.conn.commit()
            return ticket_data
    
    async def get_ticket(self, ticket_id: str) -> Optional[Dict[str, Any]]:
        """Get ticket by ID"""
        async with self.conn.execute(
            "SELECT * FROM tickets WHERE ticket_id = ?", (ticket_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def get_ticket_by_channel(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """Get ticket by channel ID"""
        async with self.conn.execute(
            "SELECT * FROM tickets WHERE channel_id = ?", (channel_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                data['added_users'] = json.loads(data.get('added_users', '[]'))
                data['metadata'] = json.loads(data.get('metadata', '{}'))
                return data
            return None
    
    async def get_active_tickets_by_user(self, user_id: int, guild_id: int) -> List[Dict[str, Any]]:
        """Get active tickets by user"""
        async with self.conn.execute(
            "SELECT * FROM tickets WHERE user_id = ? AND guild_id = ? AND status = 'open'",
            (user_id, guild_id)
        ) as cursor:
            rows = await cursor.fetchall()
            tickets = []
            for row in rows:
                data = dict(row)
                data['added_users'] = json.loads(data.get('added_users', '[]'))
                data['metadata'] = json.loads(data.get('metadata', '{}'))
                tickets.append(data)
            return tickets
    
    async def update_ticket(self, ticket_id: str, updates: Dict[str, Any]) -> bool:
        """Update ticket"""
        if 'added_users' in updates:
            updates['added_users'] = json.dumps(updates['added_users'])
        if 'metadata' in updates:
            updates['metadata'] = json.dumps(updates['metadata'])
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [ticket_id]
        
        async with self.conn.execute(
            f"UPDATE tickets SET {set_clause} WHERE ticket_id = ?",
            values
        ):
            await self.conn.commit()
            return True
    
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete ticket"""
        async with self.conn.execute(
            "DELETE FROM tickets WHERE ticket_id = ?", (ticket_id,)
        ):
            await self.conn.commit()
            return True
    
    async def get_all_active_tickets(self) -> List[Dict[str, Any]]:
        """Get all active tickets"""
        async with self.conn.execute(
            "SELECT * FROM tickets WHERE status = 'open'"
        ) as cursor:
            rows = await cursor.fetchall()
            tickets = []
            for row in rows:
                data = dict(row)
                data['added_users'] = json.loads(data.get('added_users', '[]'))
                data['metadata'] = json.loads(data.get('metadata', '{}'))
                tickets.append(data)
            return tickets
    
    async def get_ticket_count(self, user_id: int, guild_id: int) -> int:
        """Get active ticket count for user"""
        async with self.conn.execute(
            "SELECT COUNT(*) as count FROM tickets WHERE user_id = ? AND guild_id = ? AND status = 'open'",
            (user_id, guild_id)
        ) as cursor:
            row = await cursor.fetchone()
            return row['count'] if row else 0
    
    async def get_next_ticket_number(self) -> int:
        """Get next ticket number"""
        async with self.conn.execute(
            "SELECT COALESCE(MAX(ticket_number), 0) + 1 as next_num FROM tickets"
        ) as cursor:
            row = await cursor.fetchone()
            return row['next_num'] if row else 1
    
    async def add_ticket_user(self, ticket_id: str, user_id: int) -> bool:
        """Add user to ticket"""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return False
        
        users = json.loads(ticket.get('added_users', '[]'))
        if user_id not in users:
            users.append(user_id)
            await self.update_ticket(ticket_id, {'added_users': users})
        return True
    
    async def remove_ticket_user(self, ticket_id: str, user_id: int) -> bool:
        """Remove user from ticket"""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return False
        
        users = json.loads(ticket.get('added_users', '[]'))
        if user_id in users:
            users.remove(user_id)
            await self.update_ticket(ticket_id, {'added_users': users})
        return True
    
    async def get_ticket_users(self, ticket_id: str) -> List[int]:
        """Get users added to ticket"""
        ticket = await self.get_ticket(ticket_id)
        if not ticket:
            return []
        return json.loads(ticket.get('added_users', '[]'))
