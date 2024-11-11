"""
Telegram Bot Main Module for GaDL (Gamdl)

This module handles the core Telegram bot functionality for Apple Music downloads.
"""

import os
import telebot
import logging
from typing import Dict, Any

# Local imports
from . import (
    initialize_telegram_bot, 
    validate_apple_music_url, 
    GaDLTelegramException
)

# Configure logging
logger = logging.getLogger(__name__)

class AppleMusicDownloaderBot:
    def __init__(self, config_path: str = None):
        """
        Initialize the Telegram Bot for Apple Music Downloads
        
        :param config_path: Path to configuration file
        """
        try:
            # Initialize bot components
            self.bot_components = initialize_telegram_bot(config_path)
            
            # Extract components
            self.bot = self.bot_components['bot']
            self.downloader = self.bot_components['downloader']
            self.apple_music_api = self.bot_components['apple_music_api']
            self.config = self.bot_components['config']
            
            # Setup bot handlers
            self.setup_message_handlers()
            self.setup_callback_handlers()
            
        except Exception as e:
            logger.critical(f"Bot initialization failed: {e}")
            raise

    def setup_message_handlers(self):
        """
        Setup message handlers for different bot commands
        """
        @self.bot.message_handler(commands=['start', 'help'])
        def send_welcome(message):
            """
            Handle /start and /help commands
            """
            welcome_text = (
                "🎵 Welcome to Apple Music Downloader Bot! 🎶\n\n"
                "Send me an Apple Music URL and I'll download it for you.\n\n"
                "Supported Links:\n"
                "• Songs\n"
                "• Albums\n"
                "• Playlists\n"
                "• Music Videos\n\n"
                "Need help? Contact @YourSupportUsername"
            )
            self.bot.reply_to(message, welcome_text)

        @self.bot.message_handler(func=lambda message: True)
        def handle_download_request(message):
            """
            Handle download requests for Apple Music URLs
            """
            try:
                # Check user authorization
                if not self.is_user_authorized(message.from_user.id):
                    self.bot.reply_to(message, "❌ You are not authorized to use this bot.")
                    return

                url = message.text.strip()
                
                # Validate Apple Music URL
                if not validate_apple_music_url(url):
                    self.bot.reply_to(message, "❌ Invalid Apple Music URL. Please send a valid link.")
                    return

                # Send processing message
                processing_msg = self.bot.reply_to(message, "🔄 Processing your request...")

                # Download the content
                download_result = self.download_content(url)

                # Send downloaded file
                self.send_download_result(message, download_result, processing_msg)

            except GaDLTelegramException as e:
                self.bot.reply_to(message, f"❌ Download Error: {e.message}")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.bot.reply_to(message, "❌ An unexpected error occurred. Please try again later.")

    def setup_callback_handlers(self):
        """
        Setup inline keyboard callback handlers
        """
        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_query(call):
            """
            Handle inline keyboard callbacks
            """
            try:
                if call.data.startswith('download_'):
                    # Handle specific download options
                    self.handle_download_selection(call)
            except Exception as e:
                logger.error(f"Callback handler error: {e}")

    def is_user_authorized(self, user_id: int) -> bool:
        """
        Check if a user is authorized to use the bot
        
        :param user_id: Telegram User ID
        :return: Boolean indicating authorization status
        """
        allowed_users = self.config.get('allowed_users', [])
        return user_id in allowed_users or not allowed_users

    def download_content(self, url: str) -> Dict[str, Any]:
        """
        Download Apple Music content
        
        :param url: Apple Music URL
        :return: Download result dictionary
        """
        try:
            # Use GaDL downloader to fetch content
            download_result = self.downloader.download(url)
            
            if not download_result:
                raise GaDLTelegramException("Failed to download content")
            
            return download_result
        
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise GaDLTelegramException(f"Download failed: {str(e)}")

    def send_download_result(self, message, download_result, processing_msg):
        """
        Send downloaded content to user
        
        :param message: Original message
        :param download_result: Download result dictionary
        :param processing_msg: Processing message to edit
        """
        try:
            # Determine file type and send accordingly
            file_path = download_result.get('file_path')
            
            if not file_path or not os.path.exists(file_path):
                raise GaDLTelegramException("File not found")

            # Send file based on type
            with open(file_path, 'rb') as file:
                if file_path.endswith('.m4a'):  # Audio
                    self.bot.send_audio(message.chat.id, file)
                elif file_path.endswith(('.mp4', '.m4v')):  # Video
                    self.bot.send_video(message.chat.id, file)
                else:
                    self.bot.send_document(message.chat.id, file)

            # Edit processing message
            self.bot.edit_message_text(
                chat_id=processing_msg.chat.id,
                message_id=processing_msg.message_id,
                text="✅ Download Completed Successfully!"
            )

        except Exception as e:
            logger.error(f"Sending file failed: {e}")
            self.bot.edit_message_text(
                chat_id=processing_msg.chat.id,
                message_id=processing_msg.message_id,
                text=f"❌ Failed to send file: {str(e)}"
            )

    def handle_download_selection(self, call):
        """
        Handle specific download selections from inline keyboard
        
        :param call: Callback query
        """
        # Implement additional download options if needed
        pass

    def start_bot(self):
        """
        Start the Telegram Bot
        """
        try:
            logger.info("🤖 Apple Music Downloader Bot Started")
            self.bot.polling(none_stop=True)
        except Exception as e:
            logger.critical(f"Bot polling failed: {e}")

def main():
    """
    Main entry point for the Telegram Bot
    """
    try:
        bot = AppleMusicDownloaderBot()
        bot.start_bot()
    except Exception as e:
        logger.critical(f"Bot initialization failed: {e}")

if __name__ == '__main__':
    main()
