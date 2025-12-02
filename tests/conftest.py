"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from typing import Generator

import pytest
from aiogram.types import User, Chat, Message
from openpyxl import Workbook

from src.core.config import Settings


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_excel_file(temp_dir: Path) -> Path:
    """Create a temporary Excel file with expected headers."""
    excel_path = temp_dir / "test_plavka.xlsx"
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Journal"
    worksheet.append([
        "timestamp",
        "user_id", 
        "username",
        "chat_id",
        "message_id",
        "text",
    ])
    workbook.save(excel_path)
    workbook.close()
    return excel_path


@pytest.fixture
def mock_settings(temp_dir: Path) -> Settings:
    """Mock settings for testing with temporary directory."""
    return Settings(
        bot_token="test_token",
        xlsx_path=temp_dir / "test_plavka.xlsx",
        locale="ru"
    )


@pytest.fixture
def mock_user() -> User:
    """Create a mock Telegram user."""
    return User(
        id=12345,
        is_bot=False,
        first_name="Test",
        username="testuser",
        language_code="ru"
    )


@pytest.fixture
def mock_chat() -> Chat:
    """Create a mock Telegram chat."""
    return Chat(
        id=67890,
        type="private"
    )


@pytest.fixture
def mock_message(mock_user: User, mock_chat: Chat) -> Message:
    """Create a mock Telegram message."""
    return Message(
        message_id=999,
        date="2024-01-01T12:00:00",
        chat=mock_chat,
        from_user=mock_user,
        content_type="text",
        options={}
    )


@pytest.fixture
def sample_shift_message() -> str:
    """Sample shift report message for testing parsing."""
    return """Смена: 1
Дата: 15.11.2024
Время: 08:00-20:00
Длительность: 12 ч
Старший: Иванов И.И.
Всего плавок: 5
Участники: Петров П.П., Сидоров С.С.

ДЕТАЛИ ПЛАВОК:
✅ 1 РК-001 кластер-1 отливка-123 литник-456 опоки-789 t=1250°C 14:30 Создана
🔄 2 РК-002 кластер-2 отливка-124 литник-457 опоки-790 t=1260°C 14:45 Создана
✅ 3 РК-003 кластер-1 отливка-125 литник-458 опоки-791 t=1245°C 15:00 Создана"""


@pytest.fixture
def mock_telegram_bot():
    """Create a mock Telegram bot instance."""
    bot = MagicMock()
    bot.token = "test_token"
    return bot


@pytest.fixture
def mock_state():
    """Create a mock FSM state."""
    state = AsyncMock()
    state.get_state = AsyncMock(return_value=None)
    state.set_state = AsyncMock()
    state.clear = AsyncMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    return state


@pytest.fixture
def mock_callback_query(mock_message: Message):
    """Create a mock callback query."""
    callback = MagicMock()
    callback.message = mock_message
    callback.answer = AsyncMock()
    callback.data = "test_callback"
    return callback