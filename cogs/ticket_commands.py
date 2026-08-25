"""
Ticket management commands
"""

import discord
from discord.ext import commands
import logging
from typing import Optional

from utils.permissions import PermissionChecker
from utils.embeds import EmbedBuilder
from utils.errors import TicketError

logger = logging.getLogger(__name__)

class TicketCommands(commands.Cog):
    """Ticket management commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def cog_check(self, ctx: commands.Context) -> bool:
        """Check if command is used in configured guild"""
        guild_id = self.bot.config.get_guild_id()
        if guild_id and ctx.guild and ctx.guild.id != guild_id:
            await ctx.send(f"This bot is configured for guild ID {guild_id}, but this guild is {ctx.guild.id}")
            return False
        return True
    
    @commands.command(name="ticketpanel", aliases=["ticket"])
    @commands.has_permissions(manage_channels=True)
    async def ticket_panel(self, ctx: commands.Context):
        """Send the ticket panel to the current channel"""
        try:
            # Debug: Check if config is loaded
            if not self.bot.config:
                await ctx.send("❌ Configuration not loaded!")
                return
            
            # Debug: Check panel config
            panel_config = self.bot.config.get_panelbox()
            if not panel_config:
                await ctx.send("❌ Panel configuration is empty!")
                return
            
            # Debug: Print panel config
            logger.info(f"Panel config: {panel_config}")
            
            # Create embed
            embed = EmbedBuilder.create_ticket_panel(panel_config)
            
            # Create view
            from views.ticket_panel import TicketPanelView
            view = TicketPanelView(self.bot)
            
            # Send panel
            await ctx.send(embed=embed, view=view)
            
            # Delete command message if possible
            try:
                await ctx.message.delete()
            except:
                pass
            
            logger.info(f"Ticket panel sent by {ctx.author.id} in channel {ctx.channel.id}")
            
        except Exception as e:
            logger.error(f"Failed to send ticket panel: {e}", exc_info=True)
            # Send detailed error for debugging
            error_msg = f"❌ Failed to send ticket panel.\n**Error:** {str(e)}\n"
            error_msg += "**Possible issues:**\n"
            error_msg += "• Check if panelbox.json is valid\n"
            error_msg += "• Check if dropdownoption.json has valid options\n"
            error_msg += "• Check if category IDs are correct\n"
            await ctx.send(error_msg)
