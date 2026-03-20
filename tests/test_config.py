# tests/test_config.py
import pytest


def test_config_loads_with_valid_env(mock_env_vars):
    """Тест загрузки конфигурации с валидными переменными окружения"""
    # Импортируем ПОСЛЕ mock_env_vars, который очистил кэш модулей
    from config import config
    
    assert config.bot.token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    assert config.bot.owner_id == 999999999
    assert config.db.name == "test_cardio"
    assert "mongodb://testuser:testpass@localhost:27017/test_cardio" in config.db.url
    assert config.encryption.fernet_key is not None


def test_config_missing_env_var(monkeypatch):
    """Тест поведения при отсутствии обязательной переменной окружения"""
    # Очищаем окружение
    for key in ["BOT_TOKEN", "OWNER_ID", "MONGO_USER", "MONGO_PASS", "MONGO_DB", "FERNET_KEY"]:
        monkeypatch.delenv(key, raising=False)
    
    # Очищаем кэш модулей
    import sys
    for mod in list(sys.modules.keys()):
        if mod in ('config', 'environs'):
            del sys.modules[mod]
    
    # environs выбрасывает EnvValidationError
    with pytest.raises(Exception):  # Ловим любой вариант ошибки
        from config import config  # noqa: F841

