"""
Ticket panel view with dropdown
"""

import discord
from typing import Dict, Any, List, Optional
import logging
import re

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
        else:
            logger.warning("No dropdown options found in configuration")
    
    def _create_dropdown_options(self) -> List[discord.SelectOption]:
        """Create dropdown options from config"""
        options = []
        try:
            ticket_options = self.bot.config.get_ticket_options()
            
            if not ticket_options:
                logger.warning("No ticket options found in dropdownoption.json")
                return options
            
            for ticket_option in ticket_options:
                try:
                    # Validate required fields
                    if 'name' not in ticket_option or 'id' not in ticket_option:
                        logger.warning(f"Missing required fields in option: {ticket_option}")
                        continue
                    
                    # Handle emoji properly
                    emoji = self._parse_emoji(ticket_option.get('emoji'))
                    
                    # Create SelectOption
                    option = discord.SelectOption(
                        label=str(ticket_option['name'])[:100],
                        value=str(ticket_option['id']),
                        description=str(ticket_option.get('description', ''))[:100] if ticket_option.get('description') else None,
                        emoji=emoji
                    )
                    options.append(option)
                    
                    logger.info(f"Added option: {ticket_option['name']} (ID: {ticket_option['id']})")
                    
                except Exception as e:
                    logger.error(f"Error creating option for {ticket_option}: {e}")
                    # Try without emoji
                    try:
                        option = discord.SelectOption(
                            label=str(ticket_option['name'])[:100],
                            value=str(ticket_option['id']),
                            description=str(ticket_option.get('description', ''))[:100] if ticket_option.get('description') else None
                        )
                        options.append(option)
                        logger.info(f"Added option without emoji: {ticket_option['name']}")
                    except Exception as e2:
                        logger.error(f"Failed to create option without emoji: {e2}")
                        continue
                    
        except Exception as e:
            logger.error(f"Error creating dropdown options: {e}", exc_info=True)
        
        return options
    
    def _parse_emoji(self, emoji_str: Optional[str]) -> Optional[discord.PartialEmoji]:
        """Parse emoji string to discord emoji object"""
        if not emoji_str:
            return None
        
        try:
            # Check if it's a custom emoji (format: <:name:id> or <a:name:id>)
            custom_emoji_pattern = r'<(a?):(\w+):(\d+)>'
            match = re.match(custom_emoji_pattern, emoji_str.strip())
            
            if match:
                animated = bool(match.group(1))
                name = match.group(2)
                emoji_id = int(match.group(3))
                return discord.PartialEmoji(name=name, id=emoji_id, animated=animated)
            
            # Check if it's a unicode emoji
            # Discord supports unicode emojis directly
            if emoji_str.strip():
                # Try to create a PartialEmoji from unicode
                # This will work for standard unicode emojis
                return discord.PartialEmoji(name=emoji_str.strip())
            
        except Exception as e:
            logger.warning(f"Failed to parse emoji '{emoji_str}': {e}")
        
        return None


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
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
