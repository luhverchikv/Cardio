# tests/test_config.py
"""
Тесты для модуля config.py
Проверяют загрузку конфигурации из переменных окружения.
"""
import pytest
import sys
from unittest.mock import patch


# ============================================================================
# ТЕСТЫ ЗАГРУЗКИ КОНФИГУРАЦИИ
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
        
        # Проверяем базовые поля
        assert config.bot.token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        assert config.bot.owner_id == 999999999
        
        # Проверяем поля базы данных
        assert config.db.user == "testuser"
        assert config.db.password == "testpass"
        assert config.db.host == "localhost"
        assert config.db.port == "27017"
        assert config.db.name == "test_cardio"
        
        # Проверяем, что URL собирается корректно
        assert "mongodb://testuser:testpass@localhost:27017/test_cardio" in config.db.url
        
        # Проверяем шифрование
        assert config.encryption.fernet_key is not None
        assert len(config.encryption.fernet_key) == 44  # Длина Fernet-ключа
    
    def test_owner_id_is_int(self, mock_env_vars):
        """OWNER_ID корректно преобразуется в int"""
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        assert isinstance(config.bot.owner_id, int)
        assert config.bot.owner_id == 999999999
    
    def test_mongo_port_is_string(self, mock_env_vars):
        """MONGO_PORT остаётся строкой (для подключения)"""
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        assert isinstance(config.db.port, str)
        assert config.db.port == "27017"


# ============================================================================
# ТЕСТЫ ОШИБОК ПРИ ЗАГРУЗКЕ
# ============================================================================

class TestConfigErrors:
    """Тесты обработки ошибок при загрузке конфигурации"""
    
    def test_missing_bot_token(self, monkeypatch):
        """Отсутствие BOT_TOKEN вызывает ошибку"""
        # Очищаем окружение
        for key in ["BOT_TOKEN", "OWNER_ID", "MONGO_USER", "MONGO_PASS", "MONGO_DB", "FERNET_KEY"]:
            monkeypatch.delenv(key, raising=False)
        
        # Очищаем кэш модулей
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from environs import EnvValidationError
        
        with pytest.raises((EnvValidationError, Exception)):
            from config import config  # noqa: F841
    
    def test_missing_owner_id(self, monkeypatch):
        """Отсутствие OWNER_ID вызывает ошибку"""
        for key in ["OWNER_ID"]:
            monkeypatch.delenv(key, raising=False)
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        with pytest.raises((Exception,)):
            from config import config  # noqa: F841
    
    def test_missing_mongo_credentials(self, monkeypatch):
        """Отсутствие MongoDB credentials вызывает ошибку"""
        for key in ["MONGO_USER", "MONGO_PASS"]:
            monkeypatch.delenv(key, raising=False)
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        with pytest.raises((Exception,)):
            from config import config  # noqa: F841
    
    def test_missing_mongo_db_name(self, monkeypatch):
        """Отсутствие MONGO_DB вызывает ошибку"""
        monkeypatch.delenv("MONGO_DB", raising=False)
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        with pytest.raises((Exception,)):
            from config import config  # noqa: F841
    
    def test_missing_fernet_key(self, monkeypatch):
        """Отсутствие FERNET_KEY вызывает ошибку"""
        monkeypatch.delenv("FERNET_KEY", raising=False)
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        with pytest.raises((Exception,)):
            from config import config  # noqa: F841
    
    def test_invalid_owner_id_not_number(self, monkeypatch):
        """OWNER_ID не является числом —environs должен отклонить"""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "not_a_number")  # ← Невалидное значение
        monkeypatch.setenv("MONGO_USER", "test")
        monkeypatch.setenv("MONGO_PASS", "test")
        monkeypatch.setenv("MONGO_HOST", "localhost")
        monkeypatch.setenv("MONGO_PORT", "27017")
        monkeypatch.setenv("MONGO_DB", "test_db")
        monkeypatch.setenv("FERNET_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        with pytest.raises((Exception,)):
            from config import config  # noqa: F841


# ============================================================================
# ТЕСТЫ MONGO URL
# ============================================================================

class TestMongoUrl:
    """Тесты формирования MongoDB connection URL"""
    
    def test_mongo_url_format(self, mock_env_vars):
        """MongoDB URL имеет правильный формат"""
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        # Проверяем структуру URL
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
    
    def test_mongo_url_with_custom_port(self, mock_fernet_key, monkeypatch):
        """MongoDB URL с кастомным портом"""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "999999999")
        monkeypatch.setenv("MONGO_USER", "test")
        monkeypatch.setenv("MONGO_PASS", "test")
        monkeypatch.setenv("MONGO_HOST", "localhost")
        monkeypatch.setenv("MONGO_PORT", "27018")  # ← Нестандартный порт
        monkeypatch.setenv("MONGO_DB", "test_db")
        monkeypatch.setenv("FERNET_KEY", mock_fernet_key)
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        assert ":27018" in config.db.url


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
    
    def test_fernet_key_is_valid_base64(self, mock_env_vars):
        """Fernet-ключ является валидным base64"""
        import base64
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        from config import config
        
        # Fernet-ключи используют URL-safe base64
        try:
            # Пробуем декодировать (добавляем паддинг если нужно)
            key = config.encryption.fernet_key
            padding = 4 - (len(key) % 4)
            if padding != 4:
                key += '=' * padding
            base64.urlsafe_b64decode(key)
        except Exception:
            pytest.fail("Fernet-ключ не является валидным base64")
    
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
        
        # Это один и тот же объект
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
        
        # Токен должен измениться
        assert token1 != token2
        
        # Возвращаем оригинальное значение
        os.environ["BOT_TOKEN"] = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"


# ============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ
# ============================================================================

@pytest.mark.parametrize("missing_var", [
    "BOT_TOKEN",
    "OWNER_ID",
    "MONGO_USER",
    "MONGO_PASS",
    "MONGO_DB",
    "FERNET_KEY",
])
def test_missing_required_env_var(monkeypatch, missing_var):
    """Параметризованный тест: отсутствие каждой обязательной переменной"""
    # Очищаем все переменные
    for key in ["BOT_TOKEN", "OWNER_ID", "MONGO_USER", "MONGO_PASS", "MONGO_DB", "FERNET_KEY"]:
        monkeypatch.delenv(key, raising=False)
    
    # Устанавливаем все кроме той, которую тестируем
    if missing_var != "BOT_TOKEN":
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
    if missing_var != "OWNER_ID":
        monkeypatch.setenv("OWNER_ID", "999999999")
    if missing_var != "MONGO_USER":
        monkeypatch.setenv("MONGO_USER", "test")
    if missing_var != "MONGO_PASS":
        monkeypatch.setenv("MONGO_PASS", "test")
    if missing_var != "MONGO_HOST":
        monkeypatch.setenv("MONGO_HOST", "localhost")
    if missing_var != "MONGO_PORT":
        monkeypatch.setenv("MONGO_PORT", "27017")
    if missing_var != "MONGO_DB":
        monkeypatch.setenv("MONGO_DB", "test_db")
    if missing_var != "FERNET_KEY":
        monkeypatch.setenv("FERNET_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    
    # Очищаем кэш модулей
    for mod in list(sys.modules.keys()):
        if mod in ('config', 'environs'):
            del sys.modules[mod]
    
    with pytest.raises((Exception,)):
        from config import config  # noqa: F841

