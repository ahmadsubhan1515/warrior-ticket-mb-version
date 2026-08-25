"""
Ticket management service
"""

import discord
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json

from database.base import DatabaseManager
from utils.permissions import PermissionChecker
from utils.embeds import EmbedBuilder
from services.duration_service import DurationService

logger = logging.getLogger(__name__)

class TicketService:
    """Ticket management service"""
    
    def __init__(self, bot: discord.Client, db: DatabaseManager):
        self.bot = bot
        self.db = db
        self.duration_service = DurationService()
        self.auto_close_timers = {}
    
    async def create_ticket(
        self,
        guild: discord.Guild,
        user: discord.Member,
        option_id: int,
        interaction: Optional[discord.Interaction] = None
    ) -> Tuple[bool, Optional[discord.TextChannel], str]:
        """
        Create a new ticket
        Returns (success, channel, message)
        """
        try:
            # Check user's active tickets
            max_tickets = self.bot.config.get('ticket_settings.max_open_tickets_per_user', 1)
            active_tickets = await self.db.get_active_tickets_by_user(user.id, guild.id)
            
            if len(active_tickets) >= max_tickets:
                # Check if ticket channel still exists
                for ticket in active_tickets:
                    channel = guild.get_channel(ticket['channel_id'])
                    if channel:
                        return False, channel, f"You already have an active ticket: {channel.mention}"
                
                # Clean up stale tickets
                for ticket in active_tickets:
                    await self.db.update_ticket(ticket['ticket_id'], {'status': 'stale'})
            
            # Get option config
            option = self.bot.config.get_option_by_id(option_id)
            if not option:
                return False, None, "Invalid ticket option selected."
            
            # Get category
            try:
                category_id = int(option['category_id'])
                category = guild.get_channel(category_id)
                if not category or not isinstance(category, discord.CategoryChannel):
                    return False, None, f"Category not found for this ticket type. Please contact an administrator."
            except (ValueError, TypeError):
                return False, None, "Invalid category configuration."
            
            # Generate ticket ID and number
            ticket_number = await self.db.get_next_ticket_number()
            ticket_id = f"TICKET-{ticket_number:06d}"
            
            # Create channel name
            channel_name = f"ticket-{user.name.lower().replace(' ', '-')[:20]}-{ticket_number}"
            if len(channel_name) > 32:
                channel_name = f"ticket-{ticket_number}"
            
            # Create ticket channel
            channel = await category.create_text_channel(
                name=channel_name,
                topic=f"Ticket {ticket_id} | User: {user.name} | Type: {option['name']}"
            )
            
            # Setup permissions
            await PermissionChecker.setup_ticket_permissions(
                channel,
                user,
                option_id,
                self.bot.config.get_access(),
                self.bot
            )
            
            # Prepare ticket data
            now = datetime.utcnow()
            ticket_data = {
                'ticket_id': ticket_id,
                'ticket_number': ticket_number,
                'guild_id': guild.id,
                'channel_id': channel.id,
                'user_id': user.id,
                'option_id': option_id,
                'ticket_type': option['name'],
                'category_id': category.id,
                'created_at': now.isoformat(),
                'closed_at': None,
                'closed_by': None,
                'status': 'open',
                'auto_close_at': None,
                'close_reason': None,
                'added_users': [],
                'transcript_path': None,
                'metadata': {
                    'ticket_type_emoji': option.get('emoji', '🎫'),
                    'support_roles': option.get('support_roles', [])
                }
            }
            
            # Set auto close if configured
            if self.bot.config.get('ticket_settings.auto_close_enabled', False):
                hours = self.bot.config.get('ticket_settings.default_auto_close_hours', 48)
                auto_close_at = now + timedelta(hours=hours)
                ticket_data['auto_close_at'] = auto_close_at.isoformat()
                
                # Schedule auto close
                self.schedule_auto_close(ticket_id, channel.id, hours * 3600)
            
            # Save to database
            await self.db.create_ticket(ticket_data)
            
            # Send ticket interface
            ticket_embed = EmbedBuilder.create_ticket_embed(ticket_data, user)
            
            from views.ticket_controls import TicketControlsView
            view = TicketControlsView(self.bot, ticket_id)
            
            await channel.send(
                content=f"{user.mention} Your ticket has been created!",
                embed=ticket_embed,
                view=view
            )
            
            # Send opening log
            await self.send_opening_log(ticket_data, user)
            
            logger.info(f"Ticket created: {ticket_id} for user {user.id} in channel {channel.id}")
            
            return True, channel, f"Ticket created successfully: {channel.mention}"
            
        except discord.Forbidden:
            logger.error("Bot missing permissions to create ticket channel")
            return False, None, "I don't have permission to create channels. Please check my permissions."
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}", exc_info=True)
            return False, None, "An error occurred while creating your ticket. Please try again later."
    
    async def close_ticket(
        self,
        ticket_id: str,
        closed_by: discord.Member,
        reason: str = "Manual close",
        send_dm: bool = True
    ) -> Tuple[bool, str]:
        """
        Close a ticket
        Returns (success, message)
        """
        try:
            # Get ticket data
            ticket_data = await self.db.get_ticket(ticket_id)
            if not ticket_data:
                return False, "Ticket not found in database."
            
            if ticket_data['status'] != 'open':
                return False, "This ticket is already closed."
            
            # Update status to prevent duplicate close
            await self.db.update_ticket(ticket_id, {'status': 'closing'})
            
            # Cancel auto close timer if exists
            if ticket_id in self.auto_close_timers:
                self.auto_close_timers[ticket_id].cancel()
                del self.auto_close_timers[ticket_id]
            
            # Get channel
            channel = self.bot.get_channel(ticket_data['channel_id'])
            if not channel:
                guild = self.bot.get_guild(ticket_data['guild_id'])
                if guild:
                    channel = guild.get_channel(ticket_data['channel_id'])
            
            # Generate transcript
            transcript_path = None
            if channel and self.bot.config.get('transcript.enabled', True):
                transcript_path = await self.bot.transcript_service.generate_transcript(
                    channel,
                    ticket_data
                )
            
            # Update ticket data
            now = datetime.utcnow()
            created_at = datetime.fromisoformat(ticket_data['created_at'])
            duration = now - created_at
            
            updates = {
                'closed_at': now.isoformat(),
                'closed_by': closed_by.id,
                'status': 'closed',
                'close_reason': reason,
                'auto_close_at': None,
                'transcript_path': transcript_path,
                'metadata': {
                    **(ticket_data.get('metadata', {})),
                    'duration': str(duration)
                }
            }
            
            await self.db.update_ticket(ticket_id, updates)
            
            # Send close log
            await self.send_closing_log(ticket_data, closed_by, reason, transcript_path)
            
            # Send DM to user
            if send_dm and self.bot.config.get('dm_settings.enabled', True):
                await self.send_close_dm(ticket_data, transcript_path)
            
            # Delete or archive channel
            if channel:
                if self.bot.config.get('ticket_settings.delete_on_close', False):
                    await channel.delete()
                else:
                    archive_category_id = self.bot.config.get('ticket_settings.archive_category_id')
                    if archive_category_id:
                        archive_category = channel.guild.get_channel(archive_category_id)
                        if archive_category and isinstance(archive_category, discord.CategoryChannel):
                            await channel.edit(category=archive_category)
                            await channel.set_permissions(channel.guild.default_role, read_messages=False)
            
            logger.info(f"Ticket closed: {ticket_id} by {closed_by.id}")
            return True, "Ticket closed successfully."
            
        except Exception as e:
            logger.error(f"Failed to close ticket {ticket_id}: {e}", exc_info=True)
            # Revert status if close failed
            try:
                await self.db.update_ticket(ticket_id, {'status': 'open'})
            except:
                pass
            return False, "An error occurred while closing the ticket."
    
    async def send_opening_log(self, ticket_data: Dict[str, Any], user: discord.Member) -> None:
        """Send ticket opening log"""
        try:
            channel_id = self.bot.config.get_log_channel('ticket_open')
            if not channel_id:
                return
            
            channel = self.bot.get_channel(channel_id)
            if not channel:
                guild = self.bot.get_guild(ticket_data['guild_id'])
                if guild:
                    channel = guild.get_channel(channel_id)
            
            if channel:
                embed = EmbedBuilder.create_ticket_log(ticket_data, user, "open")
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send opening log: {e}")
    
    async def send_closing_log(
        self,
        ticket_data: Dict[str, Any],
        closed_by: discord.Member,
        reason: str,
        transcript_path: Optional[str]
    ) -> None:
        """Send ticket closing log"""
        try:
            channel_id = self.bot.config.get_log_channel('ticket_close')
            if not channel_id:
                return
            
            channel = self.bot.get_channel(channel_id)
            if not channel:
                guild = self.bot.get_guild(ticket_data['guild_id'])
                if guild:
                    channel = guild.get_channel(channel_id)
            
            if channel:
                # Get user
                user = self.bot.get_user(ticket_data['user_id'])
                if not user:
                    guild = self.bot.get_guild(ticket_data['guild_id'])
                    if guild:
                        user = guild.get_member(ticket_data['user_id'])
                        if not user:
                            user = await self.bot.fetch_user(ticket_data['user_id'])
                
                ticket_data['closed_by'] = closed_by.id
                ticket_data['close_reason'] = reason
                ticket_data['duration'] = ticket_data.get('metadata', {}).get('duration', 'Unknown')
                
                embed = EmbedBuilder.create_ticket_log(ticket_data, user, "close")
                
                # Send with transcript
                if transcript_path and self.bot.config.get('transcript.send_to_logs', True):
                    try:
                        file = discord.File(transcript_path, filename=f"{ticket_data['ticket_id']}.html")
                        await channel.send(embed=embed, file=file)
                        return
                    except Exception as e:
                        logger.error(f"Failed to send transcript: {e}")
                
                await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send closing log: {e}")
    
    async def send_close_dm(
        self,
        ticket_data: Dict[str, Any],
        transcript_path: Optional[str]
    ) -> None:
        """Send close notification to user DM"""
        try:
            user = self.bot.get_user(ticket_data['user_id'])
            if not user:
                try:
                    user = await self.bot.fetch_user(ticket_data['user_id'])
                except:
                    logger.warning(f"Could not fetch user {ticket_data['user_id']}")
                    return
            
            embed = EmbedBuilder.create_dm_embed(ticket_data)
            
            try:
                if transcript_path and self.bot.config.get('dm_settings.send_transcript', True):
                    try:
                        file = discord.File(transcript_path, filename=f"{ticket_data['ticket_id']}.html")
                        await user.send(embed=embed, file=file)
                        return
                    except Exception as e:
                        logger.error(f"Failed to send transcript in DM: {e}")
                
                await user.send(embed=embed)
            except discord.Forbidden:
                logger.info(f"User {user.id} has DMs disabled")
            except Exception as e:
                logger.error(f"Failed to send DM to {user.id}: {e}")
                
        except Exception as e:
            logger.error(f"Failed to send close DM: {e}")
    
    def schedule_auto_close(self, ticket_id: str, channel_id: int, seconds: int) -> None:
        """Schedule auto close timer"""
        async def auto_close():
            await asyncio.sleep(seconds)
            try:
                # Get guild and channel
                ticket_data = await self.db.get_ticket(ticket_id)
                if not ticket_data or ticket_data['status'] != 'open':
                    return
                
                guild = self.bot.get_guild(ticket_data['guild_id'])
                if not guild:
                    return
                
                # Get bot as closer
                closer = guild.me
                
                await self.close_ticket(ticket_id, closer, "Auto close timeout", send_dm=True)
                
            except Exception as e:
                logger.error(f"Auto close failed for {ticket_id}: {e}")
            finally:
                if ticket_id in self.auto_close_timers:
                    del self.auto_close_timers[ticket_id]
        
        task = asyncio.create_task(auto_close())
        self.auto_close_timers[ticket_id] = task
    
    async def cancel_all_timers(self) -> None:
        """Cancel all auto close timers"""
        for ticket_id, task in self.auto_close_timers.items():
            if not task.done():
                task.cancel()
                logger.info(f"Cancelled timer for {ticket_id}")
        self.auto_close_timers.clear()
    
    async def add_user_to_ticket(
        self,
        ticket_id: str,
        user: discord.Member,
        added_by: discord.Member
    ) -> Tuple[bool, str]:
        """Add user to ticket"""
        try:
            ticket_data = await self.db.get_ticket(ticket_id)
            if not ticket_data:
                return False, "Ticket not found."
            
            channel = user.guild.get_channel(ticket_data['channel_id'])
            if not channel:
                return False, "Ticket channel not found."
            
            # Add to database
            await self.db.add_ticket_user(ticket_id, user.id)
            
            # Add to channel permissions
            await PermissionChecker.add_user_to_ticket(channel, user)
            
            # Notify in channel
            embed = discord.Embed(
                title="👤 User Added",
                description=f"{user.mention} has been added to the ticket by {added_by.mention}",
                color=discord.Color.green()
            )
            await channel.send(embed=embed)
            
            logger.info(f"User {user.id} added to ticket {ticket_id} by {added_by.id}")
            return True, f"{user.mention} has been added to the ticket."
            
        except Exception as e:
            logger.error(f"Failed to add user to ticket: {e}")
            return False, "Failed to add user to ticket."
    
    async def remove_user_from_ticket(
        self,
        ticket_id: str,
        user: discord.Member,
        removed_by: discord.Member
    ) -> Tuple[bool, str]:
        """Remove user from ticket"""
        try:
            ticket_data = await self.db.get_ticket(ticket_id)
            if not ticket_data:
                return False, "Ticket not found."
            
            channel = user.guild.get_channel(ticket_data['channel_id'])
            if not channel:
                return False, "Ticket channel not found."
            
            # Remove from database
            await self.db.remove_ticket_user(ticket_id, user.id)
            
            # Remove from channel permissions
            await PermissionChecker.remove_user_from_ticket(channel, user)
            
            # Notify in channel
            embed = discord.Embed(
                title="👤 User Removed",
                description=f"{user.mention} has been removed from the ticket by {removed_by.mention}",
                color=discord.Color.red()
            )
            await channel.send(embed=embed)
            
            logger.info(f"User {user.id} removed from ticket {ticket_id} by {removed_by.id}")
            return True, f"{user.mention} has been removed from the ticket."
            
        except Exception as e:
            logger.error(f"Failed to remove user from ticket: {e}")
            return False, "Failed to remove user from ticket."
