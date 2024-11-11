"""
Telegram Bot Test Suite

This test module covers various Telegram bot functionality:
- Command handling
- Message processing
- User interaction
- Error handling
- Webhook integration
"""

import pytest
from unittest.mock import MagicMock, patch
from telegram import Update, Message, User as TelegramUser
from telegram.ext import CallbackContext

from app.services.telegram_bot import TelegramBotService
from app.exceptions import (
    TelegramBotError,
    InvalidCommandError,
    UserNotAuthorizedError
)

class TestTelegramBot:
    @pytest.fixture
    def telegram_bot_service(self):
        """
        Fixture to create a TelegramBotService instance for testing
        """
        return TelegramBotService()

    def create_mock_update_and_context(
        self, 
        text="/start", 
        user_id=123456, 
        username="testuser"
    ):
        """
        Helper method to create mock Telegram update and context
        """
        mock_user = MagicMock(spec=TelegramUser)
        mock_user.id = user_id
        mock_user.username = username

        mock_message = MagicMock(spec=Message)
        mock_message.text = text
        mock_message.from_user = mock_user
        mock_message.chat_id = user_id

        mock_update = MagicMock(spec=Update)
        mock_update.message = mock_message

        mock_context = MagicMock(spec=CallbackContext)
        mock_context.bot = MagicMock()

        return mock_update, mock_context

    def test_start_command(self, telegram_bot_service):
        """
        Test /start command handler
        """
        mock_update, mock_context = self.create_mock_update_and_context(text="/start")

        # Execute start command
        telegram_bot_service.start_command(mock_update, mock_context)

        # Assert bot sent welcome message
        mock_context.bot.send_message.assert_called_once()
        args = mock_context.bot.send_message.call_args[1]
        assert "Welcome" in args['text']

    def test_help_command(self, telegram_bot_service):
        """
        Test /help command handler
        """
        mock_update, mock_context = self.create_mock_update_and_context(text="/help")

        # Execute help command
        telegram_bot_service.help_command(mock_update, mock_context)

        # Assert bot sent help message
        mock_context.bot.send_message.assert_called_once()
        args = mock_context.bot.send_message.call_args[1]
        assert "Available commands" in args['text']

    def test_unauthorized_user_access(self, telegram_bot_service):
        """
        Test handling of unauthorized user attempting to use bot
        """
        # Mock unauthorized user
        mock_update, mock_context = self.create_mock_update_and_context(
            text="/admin", 
            user_id=999999, 
            username="unauthorized_user"
        )

        # Configure authorization check to raise exception
        with patch.object(
            telegram_bot_service, 
            'is_user_authorized', 
            return_value=False
        ):
            with pytest.raises(UserNotAuthorizedError):
                telegram_bot_service.admin_command(mock_update, mock_context)

    def test_invalid_command_handling(self, telegram_bot_service):
        """
        Test handling of invalid commands
        """
        mock_update, mock_context = self.create_mock_update_and_context(
            text="/invalidcommand"
        )

        with pytest.raises(InvalidCommandError):
            telegram_bot_service.handle_unknown_command(mock_update, mock_context)

    @patch('app.services.telegram_bot.requests.post')
    def test_webhook_integration(self, mock_post, telegram_bot_service):
        """
        Test Telegram webhook setup and integration
        """
        # Mock successful webhook setup response
        mock_post.return_value.json.return_value = {
            'ok': True,
            'description': 'Webhook was set successfully'
        }
        mock_post.return_value.status_code = 200

        # Webhook configuration
        webhook_url = "https://example.com/webhook"
        bot_token = "test_token"

        # Setup webhook
        result = telegram_bot_service.set_webhook(webhook_url, bot_token)

        # Assertions
        assert result is True
        mock_post.assert_called_once()

    def test_message_processing(self, telegram_bot_service):
        """
        Test message processing workflow
        """
        mock_update, mock_context = self.create_mock_update_and_context(
            text="Hello, bot!"
        )

        # Process message
        response = telegram_bot_service.process_message(mock_update, mock_context)

        # Assert message was processed
        assert response is not None
        mock_context.bot.send_message.assert_called_once()

    @patch('app.services.telegram_bot.TelegramBotService.send_error_log')
    def test_error_handling(self, mock_send_error_log, telegram_bot_service):
        """
        Test bot error handling and logging
        """
        # Simulate an error scenario
        error = Exception("Test error")
        mock_update, mock_context = self.create_mock_update_and_context()

        # Handle error
        telegram_bot_service.error_handler(mock_update, mock_context, error)

        # Assert error was logged
        mock_send_error_log.assert_called_once()

    def test_rate_limiting(self, telegram_bot_service):
        """
        Test bot rate limiting functionality
        """
        # Create multiple mock updates in quick succession
        updates = [
            self.create_mock_update_and_context(text=f"/command{i}")[0] 
            for i in range(10)
        ]

        # Track processed updates
        processed_updates = []

        # Process updates with rate limiting
        for update in updates:
            try:
                result = telegram_bot_service.process_update_with_rate_limit(update)
                processed_updates.append(result)
            except TelegramBotError:
                # Some updates should be rate-limited
                pass

        # Assert not all updates were processed
        assert len(processed_updates) < len(updates)

    def test_user_interaction_workflow(self, telegram_bot_service):
        """
        Test complete user interaction workflow
        """
        # Simulate a user interaction sequence
        interactions = [
            ("/start", "Welcome message"),
            ("Hello", "User greeting"),
            ("/help", "Help information"),
        ]

        conversation_history = []

        for command, expected_response in interactions:
            mock_update, mock_context = self.create_mock_update_and_context(
                text=command
            )

            # Process interaction
            response = telegram_bot_service.process_message(mock_update, mock_context)
            
            conversation_history.append({
                'command': command,
                'response': response
            })

        # Validate conversation flow
        assert len(conversation_history) == len(interactions)
        assert all(
            'command' in interaction and 'response' in interaction 
            for interaction in conversation_history
      )
