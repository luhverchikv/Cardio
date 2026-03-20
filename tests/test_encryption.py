# tests/test_encryption.py
"""
Тесты для модуля utils/encryption.py
Все тесты используют моки — не требуют реальных внешних сервисов.
"""
import pytest
from cryptography.fernet import Fernet, InvalidToken
from unittest.mock import patch, MagicMock


# ============================================================================
# ТЕСТЫ
# ============================================================================

class TestEncryptText:
    """Тесты функции encrypt_text"""
    
    def test_encrypts_string(self, mock_env_vars):
        """Шифрование строки возвращает зашифрованный текст"""
        from utils.encryption import encrypt_text
        
        original = "Hello World"
        encrypted = encrypt_text(original)
        
        # Результат — строка (не bytes)
        assert isinstance(encrypted, str)
        # Зашифрованный текст отличается от оригинала
        assert encrypted != original
        # Fernet создаёт токены определённого формата (содержат '.')
        assert "." in encrypted
    
    def test_encrypt_empty_string(self, mock_env_vars):
        """Шифрование пустой строки"""
        from utils.encryption import encrypt_text
        
        encrypted = encrypt_text("")
        
        assert isinstance(encrypted, str)
        assert encrypted != ""  # Пустая строка тоже шифруется
    
    def test_encrypt_special_characters(self, mock_env_vars):
        """Шифрование строк со спецсимволами"""
        from utils.encryption import encrypt_text
        
        special = "Привет! @#$%^&*() 123\n\t"
        encrypted = encrypt_text(special)
        
        assert isinstance(encrypted, str)
        # Расшифровка должна вернуть оригинал
        from utils.encryption import decrypt_text
        assert decrypt_text(encrypted) == special
    
    def test_encrypt_same_input_different_output(self, mock_env_vars):
        """Одинаковый вход → разный выход (из-за случайного nonce в Fernet)"""
        from utils.encryption import encrypt_text
        
        text = "Same message"
        encrypted1 = encrypt_text(text)
        encrypted2 = encrypt_text(text)
        
        # Fernet использует случайный nonce, поэтому результаты разные
        assert encrypted1 != encrypted2
        
        # Но оба расшифровываются в одно и то же
        from utils.encryption import decrypt_text
        assert decrypt_text(encrypted1) == text
        assert decrypt_text(encrypted2) == text
    
    def test_encrypt_long_text(self, mock_env_vars):
        """Шифрование длинного текста"""
        from utils.encryption import encrypt_text, decrypt_text
        
        long_text = "A" * 10000  # 10KB текста
        encrypted = encrypt_text(long_text)
        decrypted = decrypt_text(encrypted)
        
        assert decrypted == long_text


class TestDecryptText:
    """Тесты функции decrypt_text"""
    
    def test_decrypts_valid_token(self, mock_env_vars):
        """Расшифровка валидного токена"""
        from utils.encryption import encrypt_text, decrypt_text
        
        original = "Secret health data: BP 120/80"
        encrypted = encrypt_text(original)
        decrypted = decrypt_text(encrypted)
        
        assert decrypted == original
    
    def test_decrypt_invalid_token_raises(self, mock_env_vars):
        """Расшифровка невалидного токена вызывает InvalidToken"""
        from utils.encryption import decrypt_text
        
        invalid_tokens = [
            "not.a.valid.token",
            "",
            "random_string",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # JWT-подобный
        ]
        
        for token in invalid_tokens:
            with pytest.raises(InvalidToken):
                decrypt_text(token)
    
    def test_decrypt_tampered_token_raises(self, mock_env_vars):
        """Расшифровка изменённого токена вызывает InvalidToken"""
        from utils.encryption import encrypt_text, decrypt_text
        
        original = "Sensitive data"
        encrypted = encrypt_text(original)
        
        # "Портим" токен — меняем несколько символов
        tampered = encrypted[:-5] + "XXXXX"
        
        with pytest.raises(InvalidToken):
            decrypt_text(tampered)
    
    def test_decrypt_unicode_text(self, mock_env_vars):
        """Расшифровка текста с Unicode (кириллица, эмодзи)"""
        from utils.encryption import encrypt_text, decrypt_text
        
        unicode_texts = [
            "Привет мир",  # Кириллица
            "Hello 世界",  # Китайские иероглифы
            "Health ❤️ Care",  # Эмодзи
            "Давление: 120/80 мм рт.ст.",  # Смешанный текст
        ]
        
        for text in unicode_texts:
            encrypted = encrypt_text(text)
            decrypted = decrypt_text(encrypted)
            assert decrypted == text


class TestGenerateFernetKey:
    """Тесты функции generate_fernet_key (если есть)"""
    
    def test_generates_valid_key(self, mock_env_vars):
        """Генерация валидного Fernet-ключа"""
        try:
            from utils.encryption import generate_fernet_key
            
            key = generate_fernet_key()
            
            # Ключ — строка
            assert isinstance(key, str)
            # Fernet-ключи имеют определённую длину (44 символа в base64)
            assert len(key) == 44
            # Ключ можно использовать для создания Fernet
            fernet = Fernet(key.encode())
            assert fernet is not None
        except ImportError:
            # Если функции нет в модуле — пропускаем тест
            pytest.skip("generate_fernet_key not implemented")


class TestEncryptionIntegration:
    """Интеграционные тесты шифрования"""
    
    def test_encrypt_decrypt_roundtrip_multiple_times(self, mock_env_vars):
        """Многократное шифрование-расшифрование одного текста"""
        from utils.encryption import encrypt_text, decrypt_text
        
        original = "Health data"
        
        for i in range(10):
            encrypted = encrypt_text(original)
            decrypted = decrypt_text(encrypted)
            assert decrypted == original
    
    def test_encrypt_decrypt_health_data_formats(self, mock_env_vars):
        """Шифрование различных форматов медицинских данных"""
        from utils.encryption import encrypt_text, decrypt_text
        
        health_data_samples = [
            "BP: 120/80, Pulse: 72",
            "User ID: 123456, Arrhythmic: False",
            "Measurement: 2024-01-15 10:30:00",
            '{"systolic": 120, "diastolic": 80, "pulse": 72}',
            "Нормальное давление",
        ]
        
        for data in health_data_samples:
            encrypted = encrypt_text(data)
            decrypted = decrypt_text(encrypted)
            assert decrypted == data
    
    def test_encryption_is_reversible(self, mock_env_vars):
        """Шифрование обратимо для любых строк"""
        from utils.encryption import encrypt_text, decrypt_text
        import string
        
        # Тестируем на всех printable символах
        all_printable = string.printable
        encrypted = encrypt_text(all_printable)
        decrypted = decrypt_text(encrypted)
        
        assert decrypted == all_printable


class TestEncryptionEdgeCases:
    """Тесты граничных случаев"""
    
    def test_encrypt_none_raises(self, mock_env_vars):
        """Попытка зашифровать None вызывает ошибку"""
        from utils.encryption import encrypt_text
        
        with pytest.raises((TypeError, AttributeError)):
            encrypt_text(None)
    
    def test_encrypt_int_raises(self, mock_env_vars):
        """Попытка зашифровать число вызывает ошибку"""
        from utils.encryption import encrypt_text
        
        with pytest.raises((TypeError, AttributeError)):
            encrypt_text(12345)
    
    def test_encrypt_bytes_raises(self, mock_env_vars):
        """Попытка зашифровать bytes вызывает ошибку (если функция ожидает str)"""
        from utils.encryption import encrypt_text
        
        with pytest.raises((TypeError, AttributeError)):
            encrypt_text(b"bytes data")
    
    def test_decrypt_whitespace_token_raises(self, mock_env_vars):
        """Расшифровка токена с пробелами вызывает ошибку"""
        from utils.encryption import decrypt_text
        
        with pytest.raises(InvalidToken):
            decrypt_text("  token  ")
    
    def test_decrypt_newline_token_raises(self, mock_env_vars):
        """Расшифровка токена с переносами строк вызывает ошибку"""
        from utils.encryption import decrypt_text
        
        with pytest.raises(InvalidToken):
            decrypt_text("token\nwith\nnewlines")


# ============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ (для компактности)
# ============================================================================

@pytest.mark.parametrize("test_input", [
    "Simple text",
    "Текст на русском",
    "Text with numbers 12345",
    "Special chars: !@#$%^&*()",
    "Mixed: Привет 123 @#$",
    "Very long text " + "x" * 1000,
    "Whitespace:   spaces   ",
    "Newlines: \n line1 \n line2",
    "Tabs: \t tab \t tab",
])
def test_encrypt_decrypt_various_inputs(mock_env_vars, test_input):
    """Параметризованный тест для различных входных данных"""
    from utils.encryption import encrypt_text, decrypt_text
    
    encrypted = encrypt_text(test_input)
    decrypted = decrypt_text(encrypted)
    
    assert decrypted == test_input


@pytest.mark.parametrize("invalid_token", [
    "",
    " ",
    "not_valid",
    "not.valid.token",
    "eyJhbGciOiJIUzI1NiJ9",
    "a" * 100,
    None,  # Этот тест может потребовать отдельной обработки
])
def test_decrypt_invalid_tokens(mock_env_vars, invalid_token):
    """Параметризованный тест для невалидных токенов"""
    from utils.encryption import decrypt_text
    
    if invalid_token is None:
        with pytest.raises((TypeError, AttributeError)):
            decrypt_text(invalid_token)
    else:
        with pytest.raises(InvalidToken):
            decrypt_text(invalid_token)

