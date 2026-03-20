# tests/test_config.py
import pytest
from unittest.mock import patch


def test_config_loads_with_valid_env(mock_env_vars):
    """Тест загрузки конфигурации с валидными переменными окружения"""
    # Импортируем после моков, чтобы config.py прочитал мокированные env
    from config import config
    
    assert config.bot.token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    assert config.bot.owner_id == 999999999
    assert config.db.name == "test_cardio"
    assert "mongodb://testuser:testpass@localhost:27017/test_cardio" in config.db.url
    assert config.encryption.fernet_key is not None


def test_config_missing_env_var(monkeypatch):
    """Тест поведения при отсутствии обязательной переменной окружения"""
    # Очищаем окружение для чистого теста
    for key in ["BOT_TOKEN", "OWNER_ID", "MONGO_USER", "MONGO_PASS", "MONGO_DB", "FERNET_KEY"]:
        monkeypatch.delenv(key, raising=False)
    
    with pytest.raises(Exception):  # environs выбросит ошибку
        # Пересоздаём модуль config для теста
        import sys
        if 'config' in sys.modules:
            del sys.modules['config']
        from config import config  # noqa: F841

