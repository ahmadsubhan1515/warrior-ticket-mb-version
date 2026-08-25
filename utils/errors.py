"""
Custom error handling
"""

import discord
from discord.ext import commands
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class TicketError(Exception):
    """Base ticket error"""
    pass

class TicketNotFoundError(TicketError):
    """Ticket not found in database"""
    pass

class TicketAlreadyExistsError(TicketError):
    """Ticket already exists"""
    pass

class TicketLimitReachedError(TicketError):
    """User has reached maximum tickets"""
    pass

class InvalidOptionError(TicketError):
    """Invalid ticket option"""
    pass

class InvalidDurationError(TicketError):
    """Invalid duration format"""
    pass

class CategoryNotFoundError(TicketError):
    """Category not found"""
    pass

class PermissionDeniedError(TicketError):
    """Permission denied"""
    pass

class DatabaseError(TicketError):
    """Database error"""
    pass

class TranscriptError(TicketError):
    """Transcript generation error"""
    pass

class ErrorHandler:
    """Error handler utility"""
    
    @staticmethod
    async def send_error(
        ctx: commands.Context,
        error: Exception,
        title: str = "Error"
    ) -> None:
        """Send error message to user"""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=str(error),
            color=discord.Color.red()
        )
        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            try:
                await ctx.send(embed=embed)
            except:
                pass
    
    @staticmethod
    async def handle_command_error(
        ctx: commands.Context,
        error: Exception
    ) -> None:
        """Handle command errors"""
        if isinstance(error, commands.MissingPermissions):
            await ErrorHandler.send_error(ctx, "You don't have permission to use this command.", "Permission Denied")
        elif isinstance(error, commands.BotMissingPermissions):
            await ErrorHandler.send_error(ctx, f"I'm missing required permissions: {', '.join(error.missing_permissions)}", "Bot Missing Permissions")
        elif isinstance(error, commands.CommandNotFound):
            return  # Ignore command not found
        elif isinstance(error, commands.MissingRequiredArgument):
            await ErrorHandler.send_error(ctx, f"Missing required argument: {error.param.name}", "Invalid Usage")
        elif isinstance(error, commands.BadArgument):
            await ErrorHandler.send_error(ctx, "Invalid argument provided.", "Invalid Argument")
        elif isinstance(error, commands.CommandOnCooldown):
            await ErrorHandler.send_error(ctx, f"This command is on cooldown. Try again in {error.retry_after:.1f}s.", "Cooldown")
        elif isinstance(error, TicketError):
            await ErrorHandler.send_error(ctx, str(error), "Ticket Error")
        else:
            logger.error(f"Unhandled error in command {ctx.command}: {error}", exc_info=True)
            await ErrorHandler.send_error(ctx, "An unexpected error occurred. Please try again later.", "Unexpected Error")
