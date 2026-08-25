"""
Event handlers
"""

import discord
from discord.ext import commands
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Events(commands.Cog):
    """Event handlers"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Handle member leaving server"""
        try:
            guild_id = self.bot.config.get_guild_id()
            if guild_id and member.guild.id != guild_id:
                return
            
            # Get user's active tickets
            active_tickets = await self.bot.db.get_active_tickets_by_user(member.id, member.guild.id)
            
            if not active_tickets:
                return
            
            logger.info(f"User {member.id} left server with {len(active_tickets)} active tickets")
            
            for ticket in active_tickets:
                try:
                    # Close ticket
                    await self.bot.ticket_service.close_ticket(
                        ticket['ticket_id'],
                        member.guild.me,
                        "User left server",
                        send_dm=False  # Don't DM since user left
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to close ticket {ticket['ticket_id']} for departed user: {e}")
                    
        except Exception as e:
            logger.error(f"Member remove handler error: {e}", exc_info=True)
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Handle channel deletion"""
        try:
            if not isinstance(channel, discord.TextChannel):
                return
            
            # Check if it's a ticket channel
            ticket_data = await self.bot.db.get_ticket_by_channel(channel.id)
            
            if not ticket_data:
                return
            
            logger.info(f"Ticket channel {channel.id} deleted for ticket {ticket_data['ticket_id']}")
            
            # Update ticket status
            if ticket_data['status'] == 'open':
                await self.bot.db.update_ticket(ticket_data['ticket_id'], {
                    'status': 'deleted',
                    'closed_at': datetime.utcnow().isoformat(),
                    'close_reason': 'Channel deleted'
                })
                
        except Exception as e:
            logger.error(f"Channel delete handler error: {e}", exc_info=True)
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        """Global command error handler"""
        from utils.errors import ErrorHandler
        await ErrorHandler.handle_command_error(ctx, error)


# IMPORTANT: This setup function is required for the cog to load
async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(Events(bot))
