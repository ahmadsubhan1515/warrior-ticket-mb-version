"""
Ticket panel view with dropdown
"""

import discord
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class TicketPanelView(discord.ui.View):
    """Persistent view for ticket panel"""
    
    def __init__(self, bot: discord.Client):
        super().__init__(timeout=None)
        self.bot = bot
        
        # Add dropdown
        options = self._create_dropdown_options()
        if options:
            self.add_item(TicketTypeDropdown(self.bot, options))
    
    def _create_dropdown_options(self) -> List[discord.SelectOption]:
        """Create dropdown options from config"""
        options = []
        for ticket_option in self.bot.config.get_ticket_options():
            option = discord.SelectOption(
                label=ticket_option['name'][:100],
                value=str(ticket_option['id']),
                description=ticket_option.get('description', '')[:100],
                emoji=ticket_option.get('emoji') if ticket_option.get('emoji') else None
            )
            options.append(option)
        return options


class TicketTypeDropdown(discord.ui.Select):
    """Dropdown for selecting ticket type"""
    
    def __init__(self, bot: discord.Client, options: List[discord.SelectOption]):
        self.bot = bot
        
        # Get dropdown config
        dropdown_config = bot.config.get_panelbox().get('dropdown', {})
        
        super().__init__(
            placeholder=dropdown_config.get('placeholder', 'Select a ticket type...'),
            min_values=dropdown_config.get('min_values', 1),
            max_values=dropdown_config.get('max_values', 1),
            options=options,
            custom_id="ticket_type_dropdown",
            disabled=dropdown_config.get('disabled', False)
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle dropdown selection"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Get selected option ID
            option_id = int(self.values[0])
            
            # Get user and guild
            user = interaction.user
            guild = interaction.guild
            
            if not guild:
                await interaction.followup.send("This action can only be used in a server.", ephemeral=True)
                return
            
            # Check if user is a member
            if not isinstance(user, discord.Member):
                member = guild.get_member(user.id)
                if not member:
                    await interaction.followup.send("Could not find you in this server.", ephemeral=True)
                    return
                user = member
            
            # Create ticket
            success, channel, message = await self.bot.ticket_service.create_ticket(
                guild,
                user,
                option_id,
                interaction
            )
            
            if success:
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.followup.send(message, ephemeral=True)
                
        except ValueError:
            await interaction.followup.send("Invalid ticket option selected.", ephemeral=True)
        except Exception as e:
            logger.error(f"Dropdown callback error: {e}", exc_info=True)
            await interaction.followup.send("An error occurred while creating your ticket.", ephemeral=True)
