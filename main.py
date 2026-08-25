"""
Advanced Discord Ticket Bot - Main Entry Point
"""

import asyncio
import os
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.config import Config
from utils.logger import setup_logger
from database.base import DatabaseManager
from services.recovery_service import RecoveryService

# Setup logging
logger = setup_logger()

class TicketBot(commands.Bot):
    """Main bot class"""
    
    def __init__(self):
        self.config = Config()
        
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix=self.config.get_prefix(),
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.db = None
        self.recovery_service = None
        self.ticket_service = None
        self.duration_service = None
        self.transcript_service = None
        
    async def setup_hook(self):
        """Setup hook called before bot starts"""
        logger.info("Setting up bot...")
        
        # Initialize database
        db_type = self.config.get_database_type()
        logger.info(f"Initializing {db_type} database...")
        
        if db_type == "mongodb":
            from database.mongodb import MongoDB
            mongo_uri = os.getenv("MONGO_URI")
            if not mongo_uri:
                logger.error("MONGO_URI not found in environment variables")
                raise ValueError("MONGO_URI is required for MongoDB")
            self.db = MongoDB(mongo_uri, "discord_ticket_bot")
        else:
            from database.sqlite import SQLiteDB
            self.db = SQLiteDB("data/tickets.db")
        
        await self.db.initialize()
        logger.info(f"Database initialized successfully")
        
        # Initialize services
        from services.ticket_service import TicketService
        from services.transcript_service import TranscriptService
        from services.duration_service import DurationService
        
        self.duration_service = DurationService()
        self.transcript_service = TranscriptService(self)
        self.ticket_service = TicketService(self, self.db)
        self.recovery_service = RecoveryService(self, self.db)
        
        # Load cogs
        logger.info("Loading cogs...")
        await self.load_extension("cogs.ticket_commands")
        await self.load_extension("cogs.events")
        logger.info("Cogs loaded successfully")
        
        # Register persistent views
        from views.ticket_panel import TicketPanelView
        from views.ticket_controls import TicketControlsView
        
        self.add_view(TicketPanelView(self))
        self.add_view(TicketControlsView(self, "dummy"))
        logger.info("Persistent views registered")
        
        # Run recovery process
        logger.info("Running startup recovery...")
        await self.recovery_service.recover_all()
        logger.info("Recovery process completed")
        
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Bot is ready! Serving {len(self.guilds)} guilds")
        
        # Set bot status
        activity_type = self.config.get("bot.activity_type", "watching")
        activity_text = self.config.get("bot.activity_text", "tickets")
        
        if activity_type == "playing":
            activity = discord.Game(name=activity_text)
        elif activity_type == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=activity_text)
        elif activity_type == "streaming":
            activity = discord.Streaming(name=activity_text, url="https://twitch.tv/discord")
        else:
            activity = discord.Activity(type=discord.ActivityType.watching, name=activity_text)
        
        await self.change_presence(activity=activity)
        
    async def close(self):
        """Graceful shutdown"""
        logger.info("Shutting down bot...")
        
        # Cancel pending tasks
        if self.ticket_service:
            await self.ticket_service.cancel_all_timers()
        
        # Close database connection
        if self.db:
            await self.db.close()
            logger.info("Database connection closed")
        
        # Close Discord connection
        await super().close()
        logger.info("Bot shutdown complete")

async def main():
    """Main entry point"""
    try:
        # Get token from environment
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            logger.error("DISCORD_TOKEN not found in .env file")
            print("Error: DISCORD_TOKEN not found in .env file")
            print("Please copy .env.example to .env and add your bot token")
            sys.exit(1)
        
        # Create and run bot
        bot = TicketBot()
        
        try:
            await bot.start(token)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            await bot.close()
        except discord.LoginFailure:
            logger.error("Invalid Discord token provided")
            print("Error: Invalid Discord token. Please check your .env file")
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
            print(f"Bot crashed: {e}")
            
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        print(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
