"""
Recovery service for handling bot restarts
"""

import discord
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from database.base import DatabaseManager

logger = logging.getLogger(__name__)

class RecoveryService:
    """Recovery service for restoring ticket state after restart"""
    
    def __init__(self, bot: discord.Client, db: DatabaseManager):
        self.bot = bot
        self.db = db
    
    async def recover_all(self) -> None:
        """Recover all active tickets after restart"""
        try:
            active_tickets = await self.db.get_all_active_tickets()
            logger.info(f"Found {len(active_tickets)} active tickets to recover")
            
            recovered = 0
            failed = 0
            
            for ticket_data in active_tickets:
                try:
                    success = await self.recover_ticket(ticket_data)
                    if success:
                        recovered += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to recover ticket {ticket_data.get('ticket_id', 'unknown')}: {e}")
            
            logger.info(f"Recovery complete: {recovered} recovered, {failed} failed")
            
        except Exception as e:
            logger.error(f"Recovery process failed: {e}", exc_info=True)
    
    async def recover_ticket(self, ticket_data: Dict[str, Any]) -> bool:
        """Recover individual ticket"""
        ticket_id = ticket_data.get('ticket_id')
        channel_id = ticket_data.get('channel_id')
        guild_id = ticket_data.get('guild_id')
        
        if not ticket_id or not channel_id or not guild_id:
            logger.error(f"Invalid ticket data: missing required fields")
            return False
        
        try:
            # Get guild
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logger.warning(f"Guild {guild_id} not found for ticket {ticket_id}")
                await self.mark_ticket_stale(ticket_id, "Guild not found")
                return False
            
            # Get channel
            channel = guild.get_channel(channel_id)
            if not channel:
                logger.warning(f"Channel {channel_id} not found for ticket {ticket_id}")
                await self.mark_ticket_stale(ticket_id, "Channel not found")
                return False
            
            # Check if user still exists
            user_id = ticket_data.get('user_id')
            if user_id:
                try:
                    member = guild.get_member(user_id)
                    if not member:
                        # Try to fetch member
                        try:
                            member = await guild.fetch_member(user_id)
                        except:
                            # User left the server
                            logger.info(f"User {user_id} left the server for ticket {ticket_id}")
                            await self.close_abandoned_ticket(ticket_data, "User left server")
                            return True
                except Exception as e:
                    logger.warning(f"Failed to check user {user_id} for ticket {ticket_id}: {e}")
            
            # Check auto close timer
            auto_close_at = ticket_data.get('auto_close_at')
            if auto_close_at:
                try:
                    auto_close_time = datetime.fromisoformat(auto_close_at)
                    now = datetime.utcnow()
                    
                    if auto_close_time <= now:
                        # Auto close time has passed
                        logger.info(f"Auto close time passed for ticket {ticket_id}")
                        if guild.me:
                            await self.bot.ticket_service.close_ticket(
                                ticket_id,
                                guild.me,
                                "Auto close timeout (recovered)",
                                send_dm=True
                            )
                            return True
                    else:
                        # Schedule remaining time
                        remaining_seconds = int((auto_close_time - now).total_seconds())
                        logger.info(f"Scheduling auto close for {ticket_id} in {remaining_seconds}s")
                        self.bot.ticket_service.schedule_auto_close(
                            ticket_id,
                            channel_id,
                            remaining_seconds
                        )
                except Exception as e:
                    logger.warning(f"Failed to restore auto close for {ticket_id}: {e}")
            
            # Re-register view on channel
            try:
                from views.ticket_controls import TicketControlsView
                view = TicketControlsView(self.bot, ticket_id)
                
                # Find existing bot message with view
                async for message in channel.history(limit=50):
                    if message.author == self.bot.user:
                        # Re-add view
                        try:
                            await message.edit(view=view)
                            break
                        except:
                            continue
            except Exception as e:
                logger.warning(f"Failed to re-register view for {ticket_id}: {e}")
            
            logger.info(f"Successfully recovered ticket {ticket_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to recover ticket {ticket_id}: {e}", exc_info=True)
            return False
    
    async def mark_ticket_stale(self, ticket_id: str, reason: str) -> None:
        """Mark ticket as stale"""
        try:
            await self.db.update_ticket(ticket_id, {
                'status': 'stale',
                'close_reason': reason,
                'closed_at': datetime.utcnow().isoformat()
            })
            logger.info(f"Marked ticket {ticket_id} as stale: {reason}")
        except Exception as e:
            logger.error(f"Failed to mark ticket {ticket_id} as stale: {e}")
    
    async def close_abandoned_ticket(self, ticket_data: Dict[str, Any], reason: str) -> None:
        """Close ticket abandoned by user"""
        try:
            guild = self.bot.get_guild(ticket_data['guild_id'])
            if not guild or not guild.me:
                return
            
            await self.bot.ticket_service.close_ticket(
                ticket_data['ticket_id'],
                guild.me,
                reason,
                send_dm=False  # Don't DM since user left
            )
        except Exception as e:
            logger.error(f"Failed to close abandoned ticket {ticket_data.get('ticket_id')}: {e}")
