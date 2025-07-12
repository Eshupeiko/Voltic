"""
Main entry point for the Telegram Employee Knowledge Bot.
This bot answers employee questions using a Google Sheets knowledge base.
"""

import os
import asyncio
import logging
from bot.telegram_bot import TelegramBot
from bot.config import Config
from utils.logger import setup_logging
from utils.keep_alive import keep_alive

def main():
    """Main function to start the Telegram bot."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = Config()
        logger.info("Configuration loaded successfully")
        
        # Start keep-alive server for Replit
        keep_alive()
        
        # Create and start the Telegram bot
        bot = TelegramBot(config)
        logger.info("Starting Telegram bot...")
        
        # Run the bot
        asyncio.run(bot.run())
        
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        raise

if __name__ == "__main__":
    main()
