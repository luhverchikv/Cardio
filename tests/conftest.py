# tests/conftest.py
"""
Общие фикстуры для тестов Cardio.
Используются в: test_mongo.py, test_config.py, test_encryption.py
"""
import sys
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from cryptography.fernet import Fernet

# Регистрация плагина pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для async-тестов"""
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
    """
    Мокирует переменные окружения и очищает кэш модулей.
    
    Используется в тестах, которые импортируют config/mongo/encryption.
    Автоматически очищает sys.modules, чтобы модули перечитали новые env vars.
    """
    # Мокаем переменные окружения
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
    monkeypatch.setenv("OWNER_ID", "999999999")
    monkeypatch.setenv("MONGO_USER", "testuser")
    monkeypatch.setenv("MONGO_PASS", "testpass")
    monkeypatch.setenv("MONGO_HOST", "localhost")
    monkeypatch.setenv("MONGO_PORT", "27017")
    monkeypatch.setenv("MONGO_DB", "test_cardio")
    monkeypatch.setenv("FERNET_KEY", mock_fernet_key)
    
    # Очищаем кэш модулей, чтобы они перечитали env vars
    modules_to_clear = ['config', 'mongo', 'environs']
    for mod in list(sys.modules.keys()):
        if mod in modules_to_clear or mod.startswith('utils.'):
            del sys.modules[mod]

