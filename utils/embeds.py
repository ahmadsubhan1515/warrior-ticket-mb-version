"""
Embed creation utilities
"""

import discord
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmbedBuilder:
    """Embed builder utility"""
    
    @staticmethod
    def get_color(config: Dict[str, Any], default: str = "#5865F2") -> discord.Color:
        """Get embed color from config"""
        try:
            color = config.get('color', default)
            if isinstance(color, str):
                color = color.replace('#', '')
                return discord.Color(int(color, 16))
            elif isinstance(color, int):
                return discord.Color(color)
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid color value: {color}, using default")
        return discord.Color(int(default.replace('#', ''), 16))
    
    @staticmethod
    def create_ticket_panel(config: Dict[str, Any]) -> discord.Embed:
        """Create ticket panel embed"""
        try:
            # Get basic config with defaults
            title = config.get('title', 'Support Center')
            description = config.get('description', 'Select a ticket type below')
            color = EmbedBuilder.get_color(config)
            
            # Create embed
            embed = discord.Embed(
                title=title,
                description=description,
                color=color
            )
            
            # Set image
            if config.get('image'):
                embed.set_image(url=config['image'])
            
            # Set thumbnail
            if config.get('thumbnail'):
                embed.set_thumbnail(url=config['thumbnail'])
            
            # Set footer
            footer = config.get('footer', {})
            if footer and isinstance(footer, dict):
                footer_text = footer.get('text', '')
                footer_icon = footer.get('icon_url')
                if footer_text or footer_icon:
                    embed.set_footer(text=footer_text or '', icon_url=footer_icon)
            
            # Set author
            author = config.get('author', {})
            if author and isinstance(author, dict):
                author_name = author.get('name', '')
                if author_name:
                    embed.set_author(
                        name=author_name,
                        icon_url=author.get('icon_url'),
                        url=author.get('url')
                    )
            
            # Add fields
            fields = config.get('fields', [])
            if isinstance(fields, list):
                for field in fields:
                    if isinstance(field, dict):
                        embed.add_field(
                            name=field.get('name', ''),
                            value=field.get('value', ''),
                            inline=field.get('inline', False)
                        )
            
            return embed
            
        except Exception as e:
            logger.error(f"Error creating panel embed: {e}", exc_info=True)
            # Return a basic embed on error
            return discord.Embed(
                title="Support Center",
                description="Select a ticket type below",
                color=discord.Color.blue()
            )
