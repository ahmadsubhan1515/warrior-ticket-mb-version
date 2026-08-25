"""
Permission checking utilities
"""

import discord
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class PermissionChecker:
    """Permission checker utility"""
    
    @staticmethod
    def is_admin(member: discord.Member, admin_role_id: int) -> bool:
        """Check if member has admin role or administrator permission"""
        if member.guild_permissions.administrator:
            return True
        
        if admin_role_id and any(role.id == admin_role_id for role in member.roles):
            return True
        
        return False
    
    @staticmethod
    def is_support(member: discord.Member, option_id: int, access_config: dict) -> bool:
        """Check if member has support role for specific option"""
        if PermissionChecker.is_admin(member, int(access_config.get('ticket_admin_role', 0))):
            return True
        
        support_roles = access_config.get('support_roles', {})
        for role_id, options in support_roles.items():
            if option_id in options and any(role.id == int(role_id) for role in member.roles):
                return True
        
        return False
    
    @staticmethod
    def can_manage_ticket(member: discord.Member, ticket_data: dict, access_config: dict) -> bool:
        """Check if member can manage specific ticket"""
        return PermissionChecker.is_support(
            member, 
            ticket_data['option_id'], 
            access_config
        )
    
    @staticmethod
    async def setup_ticket_permissions(
        channel: discord.TextChannel,
        opener: discord.Member,
        option_id: int,
        access_config: dict,
        bot: discord.Client
    ) -> None:
        """Setup ticket channel permissions"""
        guild = channel.guild
        
        # Create permission overwrites
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            opener: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_permissions=True,
                read_message_history=True
            )
        }
        
        # Add admin role permissions
        admin_role_id = int(access_config.get('ticket_admin_role', 0))
        if admin_role_id:
            admin_role = guild.get_role(admin_role_id)
            if admin_role:
                overwrites[admin_role] = discord.PermissionOverwrite(
                    read_messages=True,
                    send_messages=True,
                    read_message_history=True
                )
        
        # Add support role permissions
        support_roles = access_config.get('support_roles', {})
        for role_id, options in support_roles.items():
            if option_id in options:
                role = guild.get_role(int(role_id))
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True,
                        read_message_history=True
                    )
        
        # Apply permissions
        await channel.edit(overwrites=overwrites)
    
    @staticmethod
    async def add_user_to_ticket(
        channel: discord.TextChannel,
        user: discord.Member
    ) -> None:
        """Add user to ticket channel"""
        await channel.set_permissions(
            user,
            read_messages=True,
            send_messages=True,
            read_message_history=True
        )
    
    @staticmethod
    async def remove_user_from_ticket(
        channel: discord.TextChannel,
        user: discord.Member
    ) -> None:
        """Remove user from ticket channel"""
        await channel.set_permissions(user, overwrite=None)
