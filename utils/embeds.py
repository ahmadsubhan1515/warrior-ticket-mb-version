"""
Embed creation utilities
"""

import discord
from typing import Optional, List, Dict, Any
from datetime import datetime

class EmbedBuilder:
    """Embed builder utility"""
    
    @staticmethod
    def get_color(config: Dict[str, Any], default: str = "#5865F2") -> discord.Color:
        """Get embed color from config"""
        color = config.get('color', default)
        try:
            if isinstance(color, str):
                color = color.replace('#', '')
                return discord.Color(int(color, 16))
            elif isinstance(color, int):
                return discord.Color(color)
        except (ValueError, TypeError):
            pass
        return discord.Color(int(default.replace('#', ''), 16))
    
    @staticmethod
    def create_ticket_panel(config: Dict[str, Any]) -> discord.Embed:
        """Create ticket panel embed"""
        color = EmbedBuilder.get_color(config)
        embed = discord.Embed(
            title=config.get('title', 'Support Center'),
            description=config.get('description', 'Select a ticket type below'),
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
        if footer:
            embed.set_footer(
                text=footer.get('text', ''),
                icon_url=footer.get('icon_url')
            )
        
        # Set author
        author = config.get('author', {})
        if author:
            embed.set_author(
                name=author.get('name', ''),
                icon_url=author.get('icon_url'),
                url=author.get('url')
            )
        
        # Add fields
        fields = config.get('fields', [])
        for field in fields:
            embed.add_field(
                name=field.get('name', ''),
                value=field.get('value', ''),
                inline=field.get('inline', False)
            )
        
        return embed
    
    @staticmethod
    def create_ticket_embed(ticket_data: Dict[str, Any], user: discord.User) -> discord.Embed:
        """Create ticket interface embed"""
        embed = discord.Embed(
            title=f"🎫 Ticket {ticket_data['ticket_id']}",
            description=f"Welcome {user.mention}! Support will be with you shortly.",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="👤 Opened By", value=f"{user.mention}\n`{user.id}`", inline=True)
        embed.add_field(name="📋 Ticket Type", value=ticket_data['ticket_type'], inline=True)
        embed.add_field(name="🔢 Option ID", value=str(ticket_data['option_id']), inline=True)
        embed.add_field(name="📅 Created At", value=f"<t:{int(datetime.fromisoformat(ticket_data['created_at']).timestamp())}:F>", inline=True)
        embed.add_field(name="📊 Status", value="🟢 Open", inline=True)
        embed.add_field(name="💬 Channel", value=f"<#{ticket_data['channel_id']}>", inline=True)
        
        embed.set_footer(text="Ticket System • Use buttons below to manage")
        
        return embed
    
    @staticmethod
    def create_ticket_log(ticket_data: Dict[str, Any], user: discord.User, log_type: str) -> discord.Embed:
        """Create ticket log embed"""
        if log_type == "open":
            embed = discord.Embed(
                title="🎫 Ticket Opened",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
        else:
            embed = discord.Embed(
                title="🔒 Ticket Closed",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
        
        embed.add_field(name="Ticket ID", value=ticket_data['ticket_id'], inline=True)
        embed.add_field(name="User", value=f"{user.mention}\n`{user.id}`", inline=True)
        embed.add_field(name="Type", value=ticket_data['ticket_type'], inline=True)
        embed.add_field(name="Channel", value=f"<#{ticket_data['channel_id']}>", inline=True)
        
        if log_type == "close":
            embed.add_field(name="Closed By", value=f"<@{ticket_data.get('closed_by', 'Unknown')}>", inline=True)
            embed.add_field(name="Duration", value=ticket_data.get('duration', 'Unknown'), inline=True)
            embed.add_field(name="Reason", value=ticket_data.get('close_reason', 'Manual close'), inline=True)
        
        return embed
    
    @staticmethod
    def create_dm_embed(ticket_data: Dict[str, Any]) -> discord.Embed:
        """Create DM notification embed"""
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description="Your ticket has been closed.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(name="Ticket ID", value=ticket_data['ticket_id'], inline=True)
        embed.add_field(name="Type", value=ticket_data['ticket_type'], inline=True)
        embed.add_field(name="Opened At", value=f"<t:{int(datetime.fromisoformat(ticket_data['created_at']).timestamp())}:F>", inline=True)
        embed.add_field(name="Closed At", value=f"<t:{int(datetime.fromisoformat(ticket_data['closed_at']).timestamp())}:F>", inline=True)
        
        if ticket_data.get('duration'):
            embed.add_field(name="Duration", value=ticket_data['duration'], inline=True)
        
        embed.set_footer(text="Thank you for using our support system!")
        
        return embed
