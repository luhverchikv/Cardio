# tests/conftest.py
import os
import sys
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from cryptography.fernet import Fernet

pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_fernet_key():
    return Fernet.generate_key().decode()


@pytest.fixture
def mock_env_vars(mock_fernet_key, monkeypatch):
    """Мокируем env vars И удаляем кэшированные модули"""
    # Сначала мокаем переменные
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.setenv("OWNER_ID", "999999999")
    monkeypatch.setenv("MONGO_USER", "testuser")
    monkeypatch.setenv("MONGO_PASS", "testpass")
    monkeypatch.setenv("MONGO_HOST", "localhost")
    monkeypatch.setenv("MONGO_PORT", "27017")
    monkeypatch.setenv("MONGO_DB", "test_cardio")
    monkeypatch.setenv("FERNET_KEY", mock_fernet_key)
    
    # Удаляем кэшированные модули, чтобы они перечитали новые env vars
    for mod in list(sys.modules.keys()):
        if mod in ('config', 'mongo', 'utils.encryption') or mod.startswith('utils.'):
            del sys.modules[mod]


@pytest_asyncio.fixture
async def mock_collection():
    """Чистый MagicMock для коллекции — без попыток использовать mongomock_motor"""
    collection = MagicMock()
    collection.update_one = AsyncMock()
    collection.find_one = AsyncMock()
    collection.delete_one = AsyncMock()
    
    # Для aggregate: возвращаем мок-курсор
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    collection.aggregate = MagicMock(return_value=mock_cursor)
    
    return collection


@pytest.fixture
def patch_users_collection(mock_collection):
    """Патчим users_collection в mongo модуле ПЕРЕД импортом функций"""
    with patch('mongo.users_collection', mock_collection):
        yield mock_collection


@pytest.fixture
def mock_aiogram_bot():
    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.delete_message = AsyncMock()
    return bot


@pytest.fixture
def create_mock_message(mock_aiogram_bot):
    def _factory(text: str = "", user_id: int = 123456, chat_id: int = 123456):
        message = MagicMock()
        message.text = text
        message.from_user = MagicMock(id=user_id)
        message.chat = MagicMock(id=chat_id)
        message.answer = AsyncMock()
        message.delete = AsyncMock()
        message.bot = mock_aiogram_bot
        return message
    return _factory


@pytest.fixture
def create_mock_callback():
    def _factory(data: str = "", user_id: int = 123456):
        callback = MagicMock()
        callback.data = data
        callback.from_user = MagicMock(id=user_id)
        callback.message = MagicMock()
        callback.message.edit_text = AsyncMock()
        callback.answer = AsyncMock()
        return callback
    return _factory

