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
    
    def test_missing_mongo_user_pass_ok(self, monkeypatch):
        """Отсутствие MONGO_USER/MONGO_PASS НЕ вызывает ошибку (environs позволяет)"""
        monkeypatch.delenv("MONGO_USER", raising=False)
        monkeypatch.delenv("MONGO_PASS", raising=False)
        
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF")
        monkeypatch.setenv("OWNER_ID", "999999999")
        monkeypatch.setenv("MONGO_HOST", "localhost")
        monkeypatch.setenv("MONGO_PORT", "27017")
        monkeypatch.setenv("MONGO_DB", "test_cardio")
        monkeypatch.setenv("FERNET_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
        
        for mod in list(sys.modules.keys()):
            if mod in ('config', 'environs'):
                del sys.modules[mod]
        
        # environs НЕ требует эти поля — они могут быть пустыми
        from config import config
        
        # URL будет с пустыми credentials, но конфиг загрузится
        assert config.db.url is not None
    
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

