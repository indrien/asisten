#!/usr/bin/env python3
"""
Telegram Bot Asisten dengan Gemini AI 2.5
Main entry point untuk menjalankan bot.
"""

import asyncio
import logging
import sys
import signal
from typing import Optional

from config.settings import settings
from config.database import database
from core.bot import TelegramBot
from core.clone_manager import clone_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class BotManager:
    def __init__(self):
        self.main_bot: Optional[TelegramBot] = None
        self.is_running = False
        self.shutdown_event = asyncio.Event()
    
    async def start(self):
        """Start the bot system"""
        try:
            logger.info("🚀 Starting Telegram Bot Asisten...")
            
            # Validate settings
            settings.validate()
            logger.info("✅ Settings validated")
            
            # Initialize main bot
            self.main_bot = TelegramBot()
            await self.main_bot.initialize()
            logger.info("✅ Main bot initialized")
            
            # Start all clone bots
            logger.info("🤖 Starting clone bots...")
            await clone_manager.start_all_clone_bots()
            logger.info("✅ Clone bots started")
            
            # Set running flag
            self.is_running = True
            
            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()
            
            logger.info("🎉 Bot system started successfully!")
            logger.info(f"👤 Bot: @{self.main_bot.bot_info.username}")
            logger.info(f"👥 Total users: {self.main_bot.stats['total_users']}")
            logger.info(f"🤖 Clone bots running: {clone_manager.get_running_clones_count()}")
            
            # Keep the bot running
            await self.shutdown_event.wait()
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot system: {e}")
            raise
    
    async def stop(self):
        """Stop the bot system"""
        try:
            logger.info("🛑 Stopping bot system...")
            
            self.is_running = False
            
            # Stop clone bots
            if clone_manager:
                logger.info("🛑 Stopping clone bots...")
                await clone_manager.stop_all_clone_bots()
                logger.info("✅ Clone bots stopped")
            
            # Stop main bot
            if self.main_bot:
                logger.info("🛑 Stopping main bot...")
                await self.main_bot.stop()
                logger.info("✅ Main bot stopped")
            
            # Signal shutdown complete
            self.shutdown_event.set()
            
            logger.info("✅ Bot system stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping bot system: {e}")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}")
            asyncio.create_task(self.stop())
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
        signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
        
        if sys.platform != 'win32':
            signal.signal(signal.SIGHUP, signal_handler)   # Hangup signal

async def health_check():
    """Health check function for monitoring"""
    try:
        # Check database connection
        await database.client.admin.command('ping')
        
        # Add more health checks as needed
        logger.debug("🔍 Health check passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return False

async def startup_checks():
    """Perform startup checks"""
    try:
        logger.info("🔍 Performing startup checks...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            raise RuntimeError("Python 3.8+ required")
        logger.info("✅ Python version check passed")
        
        # Test database connection
        await database.connect()
        await database.close()
        logger.info("✅ Database connection test passed")
        
        # Check required environment variables
        required_vars = ['BOT_TOKEN', 'API_ID', 'API_HASH', 'GEMINI_API_KEY', 'OWNER_ID']
        missing_vars = []
        
        for var in required_vars:
            if not getattr(settings, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("✅ Environment variables check passed")
        
        logger.info("✅ All startup checks passed")
        
    except Exception as e:
        logger.error(f"❌ Startup check failed: {e}")
        raise

def display_banner():
    """Display startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           🤖 Telegram Bot Asisten dengan Gemini AI          ║
    ║                                                              ║
    ║  ✨ Features:                                                ║
    ║     • Unlimited chat dengan AI                              ║
    ║     • Generasi gambar dengan sistem poin                    ║
    ║     • Sistem referral dan memory percakapan                 ║
    ║     • Fitur admin dan clone bot                             ║
    ║                                                              ║
    ║  🚀 Powered by Gemini AI 2.5 & Pyrogram                    ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

async def main():
    """Main function"""
    try:
        # Display banner
        display_banner()
        
        # Perform startup checks
        await startup_checks()
        
        # Create and start bot manager
        bot_manager = BotManager()
        await bot_manager.start()
        
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Check if we're in an existing event loop
        try:
            loop = asyncio.get_running_loop()
            logger.warning("⚠️  Running in existing event loop")
            # If we're already in a loop, create a task
            task = loop.create_task(main())
            # For Jupyter/Colab environments
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, main())
                future.result()
        except RuntimeError:
            # No event loop running, start normally
            asyncio.run(main())
            
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
