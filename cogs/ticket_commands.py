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
            return False
        return True
    
    async def is_admin(self, ctx: commands.Context) -> bool:
        """Check if user is admin"""
        admin_role_id = self.bot.config.get_ticket_admin_role()
        return PermissionChecker.is_admin(ctx.author, admin_role_id)
    
    @commands.command(name="ticketpanel", aliases=["ticket"])
    @commands.has_permissions(manage_channels=True)
    async def ticket_panel(self, ctx: commands.Context):
        """Send the ticket panel to the current channel"""
        try:
            # Get panel config
            panel_config = self.bot.config.get_panelbox()
            
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
            await ctx.send(f"Failed to send ticket panel. Error: {str(e)}")
    
    @commands.command(name="ticketsetup")
    @commands.has_permissions(administrator=True)
    async def ticket_setup(self, ctx: commands.Context):
        """Setup ticket system"""
        try:
            embed = discord.Embed(
                title="🎫 Ticket System Setup",
                description="Ticket system is ready!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="📋 Configuration",
                value="• Config files loaded\n• Database connected\n• Views registered",
                inline=False
            )
            
            embed.add_field(
                name="🎯 Commands",
                value=f"• `{self.bot.config.get_prefix()}ticketpanel` - Send ticket panel\n"
                      f"• `{self.bot.config.get_prefix()}tickets` - View your tickets",
                inline=False
            )
            
            # Get ticket options
            options = self.bot.config.get_ticket_options()
            if options:
                option_list = "\n".join([
                    f"• **{opt['name']}** (ID: {opt['id']})" for opt in options
                ])
                embed.add_field(
                    name="📝 Ticket Types",
                    value=option_list,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Ticket setup error: {e}", exc_info=True)
            await ctx.send("Failed to setup ticket system.")
    
    @commands.command(name="tickets", aliases=["mytickets"])
    async def list_tickets(self, ctx: commands.Context):
        """List your active tickets"""
        try:
            if not ctx.guild:
                await ctx.send("This command can only be used in a server.")
                return
            
            # Get user's active tickets
            tickets = await self.bot.db.get_active_tickets_by_user(ctx.author.id, ctx.guild.id)
            
            if not tickets:
                await ctx.send("You don't have any active tickets.")
                return
            
            embed = discord.Embed(
                title="🎫 Your Active Tickets",
                color=discord.Color.blue()
            )
            
            for ticket in tickets:
                channel = ctx.guild.get_channel(ticket['channel_id'])
                channel_mention = channel.mention if channel else f"<#{ticket['channel_id']}>"
                
                created_at = discord.utils.parse_time(ticket['created_at'])
                timestamp = f"<t:{int(created_at.timestamp())}:R>"
                
                embed.add_field(
                    name=f"Ticket {ticket['ticket_id']}",
                    value=f"**Type:** {ticket['ticket_type']}\n"
                          f"**Channel:** {channel_mention}\n"
                          f"**Created:** {timestamp}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"List tickets error: {e}", exc_info=True)
            await ctx.send("Failed to list tickets.")
    
    @commands.command(name="ticketadd", aliases=["adduser"])
    @commands.has_permissions(manage_channels=True)
    async def ticket_add(self, ctx: commands.Context, user: discord.Member, ticket_id: Optional[str] = None):
        """Add a user to a ticket"""
        try:
            # Determine ticket
            if ticket_id:
                ticket_data = await self.bot.db.get_ticket(ticket_id)
            else:
                # Use current channel
                ticket_data = await self.bot.db.get_ticket_by_channel(ctx.channel.id)
            
            if not ticket_data:
                await ctx.send("Ticket not found.")
                return
            
            # Check permissions
            if not PermissionChecker.can_manage_ticket(ctx.author, ticket_data, self.bot.config.get_access()):
                await ctx.send("You don't have permission to manage this ticket.")
                return
            
            # Add user
            success, message = await self.bot.ticket_service.add_user_to_ticket(
                ticket_data['ticket_id'],
                user,
                ctx.author
            )
            
            await ctx.send(message)
            
        except Exception as e:
            logger.error(f"Ticket add error: {e}", exc_info=True)
            await ctx.send("Failed to add user to ticket.")
    
    @commands.command(name="ticketremove", aliases=["removeuser"])
    @commands.has_permissions(manage_channels=True)
    async def ticket_remove(self, ctx: commands.Context, user: discord.Member, ticket_id: Optional[str] = None):
        """Remove a user from a ticket"""
        try:
            # Determine ticket
            if ticket_id:
                ticket_data = await self.bot.db.get_ticket(ticket_id)
            else:
                # Use current channel
                ticket_data = await self.bot.db.get_ticket_by_channel(ctx.channel.id)
            
            if not ticket_data:
                await ctx.send("Ticket not found.")
                return
            
            # Check permissions
            if not PermissionChecker.can_manage_ticket(ctx.author, ticket_data, self.bot.config.get_access()):
                await ctx.send("You don't have permission to manage this ticket.")
                return
            
            # Remove user
            success, message = await self.bot.ticket_service.remove_user_from_ticket(
                ticket_data['ticket_id'],
                user,
                ctx.author
            )
            
            await ctx.send(message)
            
        except Exception as e:
            logger.error(f"Ticket remove error: {e}", exc_info=True)
            await ctx.send("Failed to remove user from ticket.")
    
    @commands.command(name="ticketclose", aliases=["close"])
    @commands.has_permissions(manage_channels=True)
    async def ticket_close(self, ctx: commands.Context, *, reason: Optional[str] = "Manual close"):
        """Close a ticket"""
        try:
            # Get ticket from current channel
            ticket_data = await self.bot.db.get_ticket_by_channel(ctx.channel.id)
            
            if not ticket_data:
                await ctx.send("This is not a ticket channel.")
                return
            
            # Check permissions
            if not PermissionChecker.can_manage_ticket(ctx.author, ticket_data, self.bot.config.get_access()):
                await ctx.send("You don't have permission to close this ticket.")
                return
            
            # Close ticket
            success, message = await self.bot.ticket_service.close_ticket(
                ticket_data['ticket_id'],
                ctx.author,
                reason,
                send_dm=True
            )
            
            if success:
                await ctx.send("Ticket closed successfully.")
            else:
                await ctx.send(message)
            
        except Exception as e:
            logger.error(f"Ticket close error: {e}", exc_info=True)
            await ctx.send("Failed to close ticket.")
    
    @ticket_panel.error
    @ticket_setup.error
    @ticket_add.error
    @ticket_remove.error
    @ticket_close.error
    async def command_error(self, ctx: commands.Context, error):
        """Handle command errors"""
        from utils.errors import ErrorHandler
        await ErrorHandler.handle_command_error(ctx, error)


# IMPORTANT: This setup function is required for the cog to load
async def setup(bot):
    """Setup function for loading the cog"""
    await bot.add_cog(TicketCommands(bot))
