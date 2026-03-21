# tests/test_config.py
"""
Тесты для модуля config.py — соответствуют реальной реализации.
"""
import pytest
import sys
from unittest.mock import patch


# ============================================================================
# ТЕСТЫ УСПЕШНОЙ ЗАГРУЗКИ
# ============================================================================

class TestConfigLoad:
    """Тесты успешной загрузки конфигурации"""
    
    def test_loads_with_valid_env(self, mock_env_vars):
        """Конфигурация загружается с валидными переменными окружения"""
        # Очищаем кэш модулей перед импортом
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        # Проверяем базовые поля бота
        assert config.bot.token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        assert config.bot.owner_id == 999999999
        assert isinstance(config.bot.owner_id, int)
        
        # Проверяем поля базы данных (только url и name!)
        assert config.db.name == "test_cardio"
        assert "mongodb://testuser:testpass@localhost:27017/test_cardio" in config.db.url
        assert "authSource=test_cardio" in config.db.url
        
        # Проверяем шифрование
        assert config.encryption.fernet_key is not None
        assert len(config.encryption.fernet_key) == 44  # Длина Fernet-ключа
    
    def test_mongo_url_contains_auth_source(self, mock_env_vars):
        """MongoDB URL содержит authSource параметр"""
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        assert "authSource=" in config.db.url
    
    def test_owner_id_is_integer(self, mock_env_vars):
        """OWNER_ID корректно преобразуется в int через env.int()"""
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        assert isinstance(config.bot.owner_id, int)


# ============================================================================
# ТЕСТЫ MONGO URL ФОРМИРОВАНИЯ
# ============================================================================

class TestMongoUrlFormation:
    """Тесты формирования MongoDB connection URL"""
    
    def test_mongo_url_basic_format(self, mock_env_vars):
        """Базовый формат MongoDB URL"""
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        url = config.db.url
        assert url.startswith("mongodb://")
        assert "testuser:testpass@" in url
        assert "localhost:27017" in url
        assert "/test_cardio" in url
    
    def test_mongo_url_with_custom_host(self, mock_fernet_key, monkeypatch):
        """MongoDB URL с кастомным хостом"""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "999999999")
        monkeypatch.setenv("MONGO_USER", "admin")
        monkeypatch.setenv("MONGO_PASS", "secret")
        monkeypatch.setenv("MONGO_HOST", "cluster0.mongodb.net")
        monkeypatch.setenv("MONGO_PORT", "27017")
        monkeypatch.setenv("MONGO_DB", "production_db")
        monkeypatch.setenv("FERNET_KEY", mock_fernet_key)
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        assert "admin:secret@cluster0.mongodb.net" in config.db.url
        assert "/production_db" in config.db.url
        assert "authSource=production_db" in config.db.url
    
    def test_mongo_url_with_custom_port(self, mock_fernet_key, monkeypatch):
        """MongoDB URL с кастомным портом"""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "999999999")
        monkeypatch.setenv("MONGO_USER", "test")
        monkeypatch.setenv("MONGO_PASS", "test")
        monkeypatch.setenv("MONGO_HOST", "localhost")
        monkeypatch.setenv("MONGO_PORT", "27018")
        monkeypatch.setenv("MONGO_DB", "test_db")
        monkeypatch.setenv("FERNET_KEY", mock_fernet_key)
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        assert ":27018" in config.db.url
    
    def test_mongo_url_default_host_port(self, mock_fernet_key, monkeypatch):
        """MongoDB URL использует дефолтные host/port если не заданы"""
        # Не устанавливаем MONGO_HOST и MONGO_PORT
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "999999999")
        monkeypatch.setenv("MONGO_USER", "test")
        monkeypatch.setenv("MONGO_PASS", "test")
        # MONGO_HOST и MONGO_PORT не заданы — должны быть дефолты
        monkeypatch.setenv("MONGO_DB", "test_db")
        monkeypatch.setenv("FERNET_KEY", mock_fernet_key)
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        # Проверяем, что дефолты подставились
        assert "localhost:27017" in config.db.url


# ============================================================================
# ТЕСТЫ FERNET KEY
# ============================================================================

class TestFernetKey:
    """Тесты Fernet-ключа в конфигурации"""
    
    def test_fernet_key_length(self, mock_env_vars):
        """Fernet-ключ имеет правильную длину (44 символа)"""
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        assert len(config.encryption.fernet_key) == 44
    
    def test_fernet_key_from_env(self, mock_fernet_key, monkeypatch):
        """Fernet-ключ читается из переменной окружения"""
        custom_key = "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB="
        
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "999999999")
        monkeypatch.setenv("MONGO_USER", "test")
        monkeypatch.setenv("MONGO_PASS", "test")
        monkeypatch.setenv("MONGO_HOST", "localhost")
        monkeypatch.setenv("MONGO_PORT", "27017")
        monkeypatch.setenv("MONGO_DB", "test_db")
        monkeypatch.setenv("FERNET_KEY", custom_key)
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        assert config.encryption.fernet_key == custom_key


# ============================================================================
# ТЕСТЫ КЭШИРОВАНИЯ МОДУЛЯ
# ============================================================================

class TestConfigCaching:
    """Тесты кэширования модуля конфигурации"""
    
    def test_config_is_singleton(self, mock_env_vars):
        """Конфигурация — синглтон (один экземпляр при импорте)"""
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config as config1
        from config import config as config2
        
        assert config1 is config2
    
    def test_config_reloads_after_cache_clear(self, mock_env_vars):
        """Конфигурация перезагружается после очистки кэша"""
        # Первая загрузка
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config as config1
        token1 = config1.bot.token
        
        # Меняем переменную окружения
        import os
        os.environ["BOT_TOKEN"] = "NEW_TOKEN:123456"
        
        # Очищаем кэш и загружаем снова
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config as config2
        token2 = config2.bot.token
        
        assert token1 != token2
        
        # Возвращаем оригинальное значение
        os.environ["BOT_TOKEN"] = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


# ============================================================================
# ТЕСТЫ ОШИБОК (только для BOT_TOKEN и FERNET_KEY — они обязательные)
# ============================================================================

# tests/test_config.py - ИСПРАВЛЕННЫЙ КЛАСС TestConfigErrors

class TestConfigErrors:
    """Тесты обработки ошибок — только для действительно обязательных полей"""
    
    def test_missing_bot_token_raises(self, monkeypatch):
        """Отсутствие BOT_TOKEN вызывает ошибку"""
        # Очищаем все переменные
        for key in ["BOT_TOKEN", "OWNER_ID", "MONGO_USER", "MONGO_PASS", "MONGO_DB", "FERNET_KEY"]:
            monkeypatch.delenv(key, raising=False)
        
        # Очищаем кэш модулей
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        # environs должен выбросить ошибку для обязательного поля
        from environs import EnvValidationError
        
        with pytest.raises((EnvValidationError, Exception)):
            from config import config  # noqa: F841
    
    def test_missing_fernet_key_raises(self, monkeypatch):
        """Отсутствие FERNET_KEY вызывает ошибку"""
        # Очищаем только FERNET_KEY
        monkeypatch.delenv("FERNET_KEY", raising=False)
        
        # Устанавливаем остальные переменные
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "999999999")
        monkeypatch.setenv("MONGO_USER", "test")
        monkeypatch.setenv("MONGO_PASS", "test")
        # MONGO_HOST и MONGO_PORT не устанавливаем — у них есть дефолты
        monkeypatch.setenv("MONGO_DB", "test_cardio")
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from environs import EnvValidationError
        
        with pytest.raises((EnvValidationError, Exception)):
            from config import config  # noqa: F841
    
    def test_missing_mongo_db_raises(self, monkeypatch):
        """Отсутствие MONGO_DB вызывает ошибку"""
        monkeypatch.delenv("MONGO_DB", raising=False)
        
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "999999999")
        monkeypatch.setenv("MONGO_USER", "test")
        monkeypatch.setenv("MONGO_PASS", "test")
        monkeypatch.setenv("MONGO_HOST", "localhost")
        monkeypatch.setenv("MONGO_PORT", "27017")
        monkeypatch.setenv("FERNET_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from environs import EnvValidationError
        
        with pytest.raises((EnvValidationError, Exception)):
            from config import config  # noqa: F841
    
    def test_missing_mongo_user_raises(self, monkeypatch):
        """Отсутствие MONGO_USER вызывает ошибку"""
        monkeypatch.delenv("MONGO_USER", raising=False)

        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "999999999")
        monkeypatch.setenv("MONGO_PASS", "test")
        monkeypatch.setenv("MONGO_HOST", "localhost")
        monkeypatch.setenv("MONGO_PORT", "27017")
        monkeypatch.setenv("MONGO_DB", "test_cardio")
        monkeypatch.setenv("FERNET_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")

        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]

        from environs import EnvValidationError

        with pytest.raises((EnvValidationError, Exception)):
            from config import config  # noqa: F841

    def test_missing_mongo_pass_raises(self, monkeypatch):
        """Отсутствие MONGO_PASS вызывает ошибку"""
        monkeypatch.delenv("MONGO_PASS", raising=False)

        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "999999999")
        monkeypatch.setenv("MONGO_USER", "test")
        monkeypatch.setenv("MONGO_HOST", "localhost")
        monkeypatch.setenv("MONGO_PORT", "27017")
        monkeypatch.setenv("MONGO_DB", "test_cardio")
        monkeypatch.setenv("FERNET_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")

        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]

        from environs import EnvValidationError

        with pytest.raises((EnvValidationError, Exception)):
            from config import config  # noqa: F841
    
    def test_missing_owner_id_raises(self, monkeypatch):
        """Отсутствие OWNER_ID вызывает ошибку"""
        monkeypatch.delenv("OWNER_ID", raising=False)
        
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("MONGO_USER", "test")
        monkeypatch.setenv("MONGO_PASS", "test")
        monkeypatch.setenv("MONGO_HOST", "localhost")
        monkeypatch.setenv("MONGO_PORT", "27017")
        monkeypatch.setenv("MONGO_DB", "test_cardio")
        monkeypatch.setenv("FERNET_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from environs import EnvValidationError
        
        with pytest.raises((EnvValidationError, Exception)):
            from config import config  # noqa: F841


# ============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ
# ============================================================================

@pytest.mark.parametrize("test_token,expected_token", [
    ("123456:ABC-DEF", "123456:ABC-DEF"),
    ("test_bot_token_123", "test_bot_token_123"),
])
def test_bot_token_variations(mock_fernet_key, monkeypatch, test_token, expected_token):
    """Параметризованный тест для разных значений BOT_TOKEN"""
    monkeypatch.setenv("BOT_TOKEN", test_token)
    monkeypatch.setenv("OWNER_ID", "999999999")
    monkeypatch.setenv("MONGO_USER", "test")
    monkeypatch.setenv("MONGO_PASS", "test")
    monkeypatch.setenv("MONGO_HOST", "localhost")
    monkeypatch.setenv("MONGO_PORT", "27017")
    monkeypatch.setenv("MONGO_DB", "test_db")
    monkeypatch.setenv("FERNET_KEY", mock_fernet_key)
    
    for mod in list(sys.modules.keys()):
        if mod in ('config', 'environs'):
            del sys.modules[mod]
    
    from config import config
    
    assert config.bot.token == expected_token


@pytest.mark.parametrize("test_owner_id,expected_id", [
    ("123456", 123456),
    ("999999999", 999999999),
    ("1", 1),
])
def test_owner_id_conversions(mock_fernet_key, monkeypatch, test_owner_id, expected_id):
    """Параметризованный тест для преобразования OWNER_ID в int"""
    monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
    monkeypatch.setenv("OWNER_ID", test_owner_id)
    monkeypatch.setenv("MONGO_USER", "test")
    monkeypatch.setenv("MONGO_PASS", "test")
    monkeypatch.setenv("MONGO_HOST", "localhost")
    monkeypatch.setenv("MONGO_PORT", "27017")
    monkeypatch.setenv("MONGO_DB", "test_db")
    monkeypatch.setenv("FERNET_KEY", mock_fernet_key)
    
    for mod in list(sys.modules.keys()):
        if mod in ('config', 'environs'):
            del sys.modules[mod]
    
    from config import config
    
    assert config.bot.owner_id == expected_id
    assert isinstance(config.bot.owner_id, int)
