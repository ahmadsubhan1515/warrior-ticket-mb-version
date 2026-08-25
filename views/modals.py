"""
Modal views for ticket actions
"""

import discord
from typing import Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AddUserModal(discord.ui.Modal):
    """Modal for adding user to ticket"""
    
    def __init__(self, bot: discord.Client, ticket_id: str):
        super().__init__(title="Add User to Ticket")
        self.bot = bot
        self.ticket_id = ticket_id
        
        self.user_input = discord.ui.TextInput(
            label="User ID or Mention",
            placeholder="Enter user ID or @mention",
            required=True,
            min_length=1,
            max_length=100
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            if not interaction.guild:
                await interaction.followup.send("This action can only be used in a server.", ephemeral=True)
                return
            
            # Parse user input
            user_input = self.user_input.value.strip()
            user_id = None
            
            # Try to extract user ID from mention
            if user_input.startswith('<@') and user_input.endswith('>'):
                user_input = user_input.strip('<@!>')
            
            try:
                user_id = int(user_input)
            except ValueError:
                await interaction.followup.send("Invalid user ID or mention.", ephemeral=True)
                return
            
            # Get member
            member = interaction.guild.get_member(user_id)
            if not member:
                try:
                    member = await interaction.guild.fetch_member(user_id)
                except:
                    await interaction.followup.send("User not found in this server.", ephemeral=True)
                    return
            
            # Add user to ticket
            success, message = await self.bot.ticket_service.add_user_to_ticket(
                self.ticket_id,
                member,
                interaction.user
            )
            
            await interaction.followup.send(message, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Add user modal error: {e}", exc_info=True)
            try:
                await interaction.followup.send("An error occurred.", ephemeral=True)
            except:
                pass


class RemoveUserModal(discord.ui.Modal):
    """Modal for removing user from ticket"""
    
    def __init__(self, bot: discord.Client, ticket_id: str):
        super().__init__(title="Remove User from Ticket")
        self.bot = bot
        self.ticket_id = ticket_id
        
        self.user_input = discord.ui.TextInput(
            label="User ID or Mention",
            placeholder="Enter user ID or @mention",
            required=True,
            min_length=1,
            max_length=100
        )
        self.add_item(self.user_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            if not interaction.guild:
                await interaction.followup.send("This action can only be used in a server.", ephemeral=True)
                return
            
            # Parse user input
            user_input = self.user_input.value.strip()
            user_id = None
            
            # Try to extract user ID from mention
            if user_input.startswith('<@') and user_input.endswith('>'):
                user_input = user_input.strip('<@!>')
            
            try:
                user_id = int(user_input)
            except ValueError:
                await interaction.followup.send("Invalid user ID or mention.", ephemeral=True)
                return
            
            # Get member
            member = interaction.guild.get_member(user_id)
            if not member:
                await interaction.followup.send("User not found in this server.", ephemeral=True)
                return
            
            # Remove user from ticket
            success, message = await self.bot.ticket_service.remove_user_from_ticket(
                self.ticket_id,
                member,
                interaction.user
            )
            
            await interaction.followup.send(message, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Remove user modal error: {e}", exc_info=True)
            try:
                await interaction.followup.send("An error occurred.", ephemeral=True)
            except:
                pass


class CloseTimeModal(discord.ui.Modal):
    """Modal for setting auto-close time"""
    
    def __init__(self, bot: discord.Client, ticket_id: str):
        super().__init__(title="Set Auto-Close Time")
        self.bot = bot
        self.ticket_id = ticket_id
        
        self.duration_input = discord.ui.TextInput(
            label="Duration",
            placeholder="Examples: 1m, 30m, 1h, 2h, 12h, 1d, 1w",
            required=True,
            min_length=2,
            max_length=20
        )
        self.add_item(self.duration_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Parse duration
            duration_str = self.duration_input.value.strip()
            is_valid, error_message = self.bot.duration_service.validate_duration(duration_str)
            
            if not is_valid:
                await interaction.followup.send(error_message, ephemeral=True)
                return
            
            # Get auto close time
            seconds = self.bot.duration_service.parse_duration(duration_str)
            auto_close_at = datetime.utcnow() + timedelta(seconds=seconds)
            
            # Update database
            await self.bot.db.update_ticket(self.ticket_id, {
                'auto_close_at': auto_close_at.isoformat()
            })
            
            # Schedule auto close
            self.bot.ticket_service.schedule_auto_close(
                self.ticket_id,
                interaction.channel_id,
                seconds
            )
            
            # Send confirmation
            formatted_duration = self.bot.duration_service.format_duration(seconds)
            await interaction.followup.send(
                f"Ticket will auto-close in {formatted_duration}.",
                ephemeral=True
            )
            
            # Send message in channel
            if interaction.channel:
                embed = discord.Embed(
                    title="⏰ Auto-Close Scheduled",
                    description=f"This ticket will automatically close in **{formatted_duration}**.",
                    color=discord.Color.orange()
                )
                embed.set_footer(text=f"Set by {interaction.user.name}")
                await interaction.channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Close time modal error: {e}", exc_info=True)
            try:
                await interaction.followup.send("An error occurred.", ephemeral=True)
            except:
                pass
