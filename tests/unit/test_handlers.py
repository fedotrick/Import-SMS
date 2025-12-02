"""Unit tests for Telegram bot handlers."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.bot.handlers import start, add_record, menu
from src.bot.services.excel import ExcelServiceError, ExcelValidationError


class TestStartHandler:
    """Test cases for start handler."""

    @pytest.mark.asyncio
    async def test_handle_start_command(self, mock_message):
        """Test handling /start command."""
        await start.handle_start(mock_message)
        
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "Привет! Это журнал смен" in call_args[0][0]
        
        # Should include main menu keyboard
        assert call_args[1]["reply_markup"] is not None


class TestAddRecordHandler:
    """Test cases for add record handler."""

    @pytest.mark.asyncio
    async def test_cancel_add_record(self, mock_message, mock_state):
        """Test canceling add record operation."""
        mock_message.text = "/cancel"
        
        await add_record.cancel_add_record(mock_message, mock_state)
        
        mock_state.clear.assert_called_once()
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "Добавление записи отменено" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_process_add_record_success(self, mock_message, mock_state):
        """Test successful record addition."""
        mock_message.text = "Test message content"
        mock_message.from_user.id = 12345
        mock_message.from_user.username = "testuser"
        mock_message.chat.id = 67890
        mock_message.message_id = 999
        
        with patch('src.bot.handlers.add_record.append_message_row') as mock_append:
            await add_record.process_add_record(mock_message, mock_state)
            
            mock_append.assert_called_once_with(
                user_id=12345,
                username="testuser",
                chat_id=67890,
                message_id=999,
                text="Test message content"
            )
            
            mock_state.clear.assert_called_once()
            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            assert "✅ Запись сохранена" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_process_add_record_with_full_name(self, mock_message, mock_state):
        """Test record addition with full name when username is None."""
        mock_message.text = "Test message"
        mock_message.from_user.id = 12345
        mock_message.from_user.username = None
        mock_message.from_user.full_name = "Test User"
        mock_message.chat.id = 67890
        mock_message.message_id = 999
        
        with patch('src.bot.handlers.add_record.append_message_row') as mock_append:
            await add_record.process_add_record(mock_message, mock_state)
            
            mock_append.assert_called_once_with(
                user_id=12345,
                username="Test User",
                chat_id=67890,
                message_id=999,
                text="Test message"
            )

    @pytest.mark.asyncio
    async def test_process_add_record_empty_message(self, mock_message, mock_state):
        """Test handling empty message in add record."""
        mock_message.text = ""
        
        await add_record.process_add_record(mock_message, mock_state)
        
        mock_message.answer.assert_called_once_with(
            "Пожалуйста, отправьте текстовое сообщение для записи в журнал."
        )
        mock_state.clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_add_record_whitespace_only_message(self, mock_message, mock_state):
        """Test handling whitespace-only message."""
        mock_message.text = "   \n\t   "
        
        await add_record.process_add_record(mock_message, mock_state)
        
        mock_message.answer.assert_called_once_with(
            "Пожалуйста, отправьте текстовое сообщение для записи в журнал."
        )
        mock_state.clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_add_record_no_sender(self, mock_message, mock_state):
        """Test handling message without sender information."""
        mock_message.text = "Test message"
        mock_message.from_user = None
        
        await add_record.process_add_record(mock_message, mock_state)
        
        mock_message.answer.assert_called_once_with(
            "Не удалось определить отправителя сообщения."
        )
        mock_state.clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_add_record_excel_validation_error(self, mock_message, mock_state):
        """Test handling Excel validation error."""
        mock_message.text = "Test message"
        mock_message.from_user.id = 12345
        mock_message.from_user.username = "testuser"
        mock_message.chat.id = 67890
        mock_message.message_id = 999
        
        with patch('src.bot.handlers.add_record.append_message_row') as mock_append:
            mock_append.side_effect = ExcelValidationError("Test validation error")
            
            await add_record.process_add_record(mock_message, mock_state)
            
            mock_message.answer.assert_called_once()
            call_args = mock_message.answer.call_args
            assert "⚠️ Не удалось сохранить запись" in call_args[0][0]
            assert "структура plavka.xlsx отличается от ожидаемой" in call_args[0][0]
            mock_state.clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_add_record_excel_service_error(self, mock_message, mock_state):
        """Test handling Excel service error."""
        mock_message.text = "Test message"
        mock_message.from_user.id = 12345
        mock_message.from_user.username = "testuser"
        mock_message.chat.id = 67890
        mock_message.message_id = 999
        
        with patch('src.bot.handlers.add_record.append_message_row') as mock_append:
            mock_append.side_effect = ExcelServiceError("File is locked")
            
            await add_record.process_add_record(mock_message, mock_state)
            
            mock_message.answer.assert_called_once_with("File is locked")
            mock_state.clear.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_add_record_unexpected_error(self, mock_message, mock_state):
        """Test handling unexpected error."""
        mock_message.text = "Test message"
        mock_message.from_user.id = 12345
        mock_message.from_user.username = "testuser"
        mock_message.chat.id = 67890
        mock_message.message_id = 999
        
        with patch('src.bot.handlers.add_record.append_message_row') as mock_append:
            mock_append.side_effect = Exception("Unexpected error")
            
            await add_record.process_add_record(mock_message, mock_state)
            
            mock_message.answer.assert_called_once_with(
                "Произошла непредвиденная ошибка. Попробуйте позже."
            )
            mock_state.clear.assert_not_called()


class TestMenuHandler:
    """Test cases for menu handler."""

    @pytest.mark.asyncio
    async def test_menu_add_record(self, mock_callback_query, mock_state):
        """Test add record menu callback."""
        await menu.menu_add_record(mock_callback_query, mock_state)
        
        mock_callback_query.answer.assert_called_once()
        mock_state.set_state.assert_called_once_with(add_record.AddRecordState.waiting_for_text)
        mock_callback_query.message.answer.assert_called_once()
        call_args = mock_callback_query.message.answer.call_args
        assert "Отправьте текст сообщения" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_menu_add_record_no_message(self, mock_callback_query, mock_state):
        """Test add record menu callback with no message."""
        mock_callback_query.message = None
        
        await menu.menu_add_record(mock_callback_query, mock_state)
        
        mock_callback_query.answer.assert_called_once_with(
            "Сообщение недоступно.", show_alert=True
        )
        mock_state.set_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_menu_last_records_success(self, mock_callback_query):
        """Test last records menu callback with data."""
        test_rows = [
            ["2024-01-01T12:00:00", 123, "user1", 456, 789, "First message"],
            ["2024-01-01T13:00:00", 124, "user2", 457, 790, "Second message"],
        ]
        
        with patch('src.bot.handlers.menu.get_last_rows') as mock_get_rows:
            mock_get_rows.return_value = test_rows
            
            await menu.menu_last_records(mock_callback_query)
            
            mock_callback_query.answer.assert_called_once()
            mock_callback_query.message.answer.assert_called_once()
            
            # Check that formatted rows are included in response
            call_args = mock_callback_query.message.answer.call_args
            response_text = call_args[0][0]
            assert "First message" in response_text
            assert "Second message" in response_text
            assert "ID сообщения: 789" in response_text
            assert "Автор: user1" in response_text

    @pytest.mark.asyncio
    async def test_menu_last_records_no_data(self, mock_callback_query):
        """Test last records menu callback with no data."""
        with patch('src.bot.handlers.menu.get_last_rows') as mock_get_rows:
            mock_get_rows.return_value = []
            
            await menu.menu_last_records(mock_callback_query)
            
            mock_callback_query.answer.assert_called_once()
            call_args = mock_callback_query.message.answer.call_args
            assert "Записей пока нет" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_menu_last_records_validation_error(self, mock_callback_query):
        """Test last records menu callback with validation error."""
        with patch('src.bot.handlers.menu.get_last_rows') as mock_get_rows:
            mock_get_rows.side_effect = ExcelValidationError("Invalid structure")
            
            await menu.menu_last_records(mock_callback_query)
            
            mock_callback_query.answer.assert_called_once()
            call_args = mock_callback_query.message.answer.call_args
            assert "⚠️ Не удалось прочитать plavka.xlsx" in call_args[0][0]
            assert "структура файла отличается от ожидаемой" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_menu_last_records_service_error(self, mock_callback_query):
        """Test last records menu callback with service error."""
        with patch('src.bot.handlers.menu.get_last_rows') as mock_get_rows:
            mock_get_rows.side_effect = ExcelServiceError("File is locked")
            
            await menu.menu_last_records(mock_callback_query)
            
            mock_callback_query.answer.assert_called_once()
            mock_callback_query.message.answer.assert_called_once_with("File is locked")

    @pytest.mark.asyncio
    async def test_menu_last_records_unexpected_error(self, mock_callback_query):
        """Test last records menu callback with unexpected error."""
        with patch('src.bot.handlers.menu.get_last_rows') as mock_get_rows:
            mock_get_rows.side_effect = Exception("Unexpected error")
            
            await menu.menu_last_records(mock_callback_query)
            
            mock_callback_query.answer.assert_called_once()
            call_args = mock_callback_query.message.answer.call_args
            assert "Произошла непредвиденная ошибка" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_menu_last_records_no_message(self, mock_callback_query):
        """Test last records menu callback with no message."""
        mock_callback_query.message = None
        
        await menu.menu_last_records(mock_callback_query)
        
        mock_callback_query.answer.assert_called_once_with(
            "Сообщение недоступно.", show_alert=True
        )

    @pytest.mark.asyncio
    async def test_menu_download_file_exists(self, mock_callback_query, temp_dir):
        """Test download menu callback when file exists."""
        excel_path = temp_dir / "plavka.xlsx"
        excel_path.touch()  # Create empty file
        
        with patch('src.bot.handlers.menu.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.xlsx_path = excel_path
            mock_get_settings.return_value = mock_settings
            
            await menu.menu_download(mock_callback_query)
            
            mock_callback_query.answer.assert_called_once()
            mock_callback_query.message.answer_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_menu_download_file_not_exists(self, mock_callback_query):
        """Test download menu callback when file doesn't exist."""
        with patch('src.bot.handlers.menu.get_settings') as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.xlsx_path = MagicMock()
            mock_settings.xlsx_path.exists.return_value = False
            mock_get_settings.return_value = mock_settings
            
            await menu.menu_download(mock_callback_query)
            
            mock_callback_query.answer.assert_called_once()
            call_args = mock_callback_query.message.answer.call_args
            assert "Файл plavka.xlsx пока не создан" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_menu_download_no_message(self, mock_callback_query):
        """Test download menu callback with no message."""
        mock_callback_query.message = None
        
        await menu.menu_download(mock_callback_query)
        
        mock_callback_query.answer.assert_called_once_with(
            "Сообщение недоступно.", show_alert=True
        )

    @pytest.mark.asyncio
    async def test_menu_help(self, mock_callback_query):
        """Test help menu callback."""
        await menu.menu_help(mock_callback_query)
        
        mock_callback_query.answer.assert_called_once()
        mock_callback_query.message.answer.assert_called_once()
        
        call_args = mock_callback_query.message.answer.call_args
        response_text = call_args[0][0]
        assert "ℹ️ Журнал смен" in response_text
        assert "Добавить запись" in response_text
        assert "Последние записи" in response_text
        assert "Скачать plavka.xlsx" in response_text

    @pytest.mark.asyncio
    async def test_menu_help_no_message(self, mock_callback_query):
        """Test help menu callback with no message."""
        mock_callback_query.message = None
        
        await menu.menu_help(mock_callback_query)
        
        mock_callback_query.answer.assert_called_once_with(
            "Сообщение недоступно.", show_alert=True
        )

    def test_format_last_rows_empty(self):
        """Test formatting empty last rows."""
        result = menu._format_last_rows([])
        assert result == "Записей пока нет."

    def test_format_last_rows_with_data(self):
        """Test formatting rows with data."""
        rows = [
            ["2024-01-01T12:00:00", 123, "user1", 456, 789, "First message"],
            ["2024-01-01T13:00:00", 124, None, 457, 790, "Second message"],
        ]
        
        result = menu._format_last_rows(rows)
        
        assert "First message" in result
        assert "Second message" in result
        assert "ID сообщения: 789" in result
        assert "ID сообщения: 790" in result
        assert "Автор: user1" in result
        assert "Автор: —" in result  # None username becomes "—"
        assert "2024-01-01T12:00:00" in result
        assert "2024-01-01T13:00:00" in result