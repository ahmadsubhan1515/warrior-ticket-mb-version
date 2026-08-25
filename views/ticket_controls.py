"""
Ticket control buttons view
"""

import discord
from typing import Optional
import logging

from views.modals import AddUserModal, RemoveUserModal, CloseTimeModal

logger = logging.getLogger(__name__)

class TicketControlsView(discord.ui.View):
    """Persistent view for ticket controls"""
    
    def __init__(self, bot: discord.Client, ticket_id: str):
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_id = ticket_id
    
    @discord.ui.button(
        label="Close",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_close",
        emoji="🔒",
        row=0
    )
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close ticket button"""
        await self.handle_close(interaction)
    
    @discord.ui.button(
        label="Transcript",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_transcript",
        emoji="📝",
        row=0
    )
    async def transcript_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Generate transcript button"""
        await self.handle_transcript(interaction)
    
    @discord.ui.button(
        label="Add User",
        style=discord.ButtonStyle.primary,
        custom_id="ticket_add_user",
        emoji="➕",
        row=0
    )
    async def add_user_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Add user button"""
        await self.handle_add_user(interaction)
    
    @discord.ui.button(
        label="Remove User",
        style=discord.ButtonStyle.primary,
        custom_id="ticket_remove_user",
        emoji="➖",
        row=0
    )
    async def remove_user_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Remove user button"""
        await self.handle_remove_user(interaction)
    
    @discord.ui.button(
        label="Close With Time",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_close_time",
        emoji="⏰",
        row=1
    )
    async def close_time_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Close with time button"""
        await self.handle_close_time(interaction)
    
    async def check_permissions(self, interaction: discord.Interaction) -> bool:
        """Check if user has permission to manage ticket"""
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return False
        
        # Get ticket data
        ticket_data = await self.bot.db.get_ticket(self.ticket_id)
        if not ticket_data:
            return False
        
        # Check permissions
        from utils.permissions import PermissionChecker
        return PermissionChecker.can_manage_ticket(
            interaction.user,
            ticket_data,
            self.bot.config.get_access()
        )
    
    async def handle_close(self, interaction: discord.Interaction):
        """Handle close button"""
        try:
            # Check permissions
            if not await self.check_permissions(interaction):
                await interaction.response.send_message("You don't have permission to close this ticket.", ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True)
            
            # Close ticket
            success, message = await self.bot.ticket_service.close_ticket(
                self.ticket_id,
                interaction.user,
                "Manual close",
                send_dm=True
            )
            
            if success:
                await interaction.followup.send("Ticket closed successfully.", ephemeral=True)
            else:
                await interaction.followup.send(message, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Close button error: {e}", exc_info=True)
            try:
                await interaction.followup.send("An error occurred while closing the ticket.", ephemeral=True)
            except:
                pass
    
    async def handle_transcript(self, interaction: discord.Interaction):
        """Handle transcript button"""
        try:
            # Check permissions
            if not await self.check_permissions(interaction):
                await interaction.response.send_message("You don't have permission to generate transcript.", ephemeral=True)
                return
            
            await interaction.response.defer(ephemeral=True)
            
            # Get ticket data
            ticket_data = await self.bot.db.get_ticket(self.ticket_id)
            if not ticket_data:
                await interaction.followup.send("Ticket not found.", ephemeral=True)
                return
            
            # Generate transcript
            channel = interaction.guild.get_channel(ticket_data['channel_id']) if interaction.guild else None
            if not channel:
                await interaction.followup.send("Ticket channel not found.", ephemeral=True)
                return
            
            transcript_path = await self.bot.transcript_service.generate_transcript(channel, ticket_data)
            
            if transcript_path:
                file = discord.File(transcript_path, filename=f"{self.ticket_id}.html")
                await interaction.followup.send(
                    content=f"Transcript for {self.ticket_id}:",
                    file=file,
                    ephemeral=True
                )
            else:
                await interaction.followup.send("Failed to generate transcript.", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Transcript button error: {e}", exc_info=True)
            try:
                await interaction.followup.send("An error occurred while generating transcript.", ephemeral=True)
            except:
                pass
    
    async def handle_add_user(self, interaction: discord.Interaction):
        """Handle add user button"""
        try:
            # Check permissions
            if not await self.check_permissions(interaction):
                await interaction.response.send_message("You don't have permission to add users.", ephemeral=True)
                return
            
            # Show modal
            modal = AddUserModal(self.bot, self.ticket_id)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Add user button error: {e}", exc_info=True)
            try:
                await interaction.response.send_message("An error occurred.", ephemeral=True)
            except:
                pass
    
    async def handle_remove_user(self, interaction: discord.Interaction):
        """Handle remove user button"""
        try:
            # Check permissions
            if not await self.check_permissions(interaction):
                await interaction.response.send_message("You don't have permission to remove users.", ephemeral=True)
                return
            
            # Show modal
            modal = RemoveUserModal(self.bot, self.ticket_id)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Remove user button error: {e}", exc_info=True)
            try:
                await interaction.response.send_message("An error occurred.", ephemeral=True)
            except:
                pass
    
    async def handle_close_time(self, interaction: discord.Interaction):
        """Handle close with time button"""
        try:
            # Check permissions
            if not await self.check_permissions(interaction):
                await interaction.response.send_message("You don't have permission to set auto-close.", ephemeral=True)
                return
            
            # Show modal
            modal = CloseTimeModal(self.bot, self.ticket_id)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Close time button error: {e}", exc_info=True)
            try:
                await interaction.response.send_message("An error occurred.", ephemeral=True)
            except:
                pass
