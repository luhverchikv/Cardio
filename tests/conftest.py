# tests/conftest.py
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from cryptography.fernet import Fernet

# Настройка pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для async тестов"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_fernet_key():
    """Генерация тестового Fernet-ключа"""
    return Fernet.generate_key().decode()


@pytest.fixture
def mock_env_vars(mock_fernet_key, monkeypatch):
    """Мокирование переменных окружения для тестов"""
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.setenv("OWNER_ID", "999999999")
    monkeypatch.setenv("MONGO_USER", "testuser")
    monkeypatch.setenv("MONGO_PASS", "testpass")
    monkeypatch.setenv("MONGO_HOST", "localhost")
    monkeypatch.setenv("MONGO_PORT", "27017")
    monkeypatch.setenv("MONGO_DB", "test_cardio")
    monkeypatch.setenv("FERNET_KEY", mock_fernet_key)


@pytest_asyncio.fixture
async def mock_mongo_collection():
    """Мок MongoDB коллекции с использованием mongomock"""
    try:
        from mongomock_motor import AsyncMongoMockClient
        
        client = AsyncMongoMockClient()
        db = client["test_cardio"]
        collection = db["users"]
        yield collection
    except ImportError:
        # Fallback: простой MagicMock, если mongomock_motor не установлен
        mock_collection = AsyncMock()
        mock_collection.update_one = AsyncMock()
        mock_collection.find_one = AsyncMock()
        mock_collection.delete_one = AsyncMock()
        mock_collection.aggregate = AsyncMock(return_value=AsyncMock())
        yield mock_collection


@pytest.fixture
def mock_aiogram_bot():
    """Мок aiogram Bot для тестов хендлеров"""
    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.delete_message = AsyncMock()
    return bot


@pytest.fixture
def create_mock_message(mock_aiogram_bot):
    """Фабрика моков сообщений Telegram"""
    def _factory(text: str = "", user_id: int = 123456, chat_id: int = 123456):
        message = MagicMock()
        message.text = text
        message.from_user.id = user_id
        message.chat.id = chat_id
        message.answer = AsyncMock()
        message.delete = AsyncMock()
        message.bot = mock_aiogram_bot
        return message
    return _factory


@pytest.fixture
def create_mock_callback():
    """Фабрика моков callback-запросов"""
    def _factory( str = "", user_id: int = 123456):
        callback = MagicMock()
        callback.data = data
        callback.from_user.id = user_id
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        return callback
    return _factory

