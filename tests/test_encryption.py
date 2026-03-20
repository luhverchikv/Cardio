# tests/test_encryption.py
import pytest
from cryptography.fernet import InvalidToken


def test_encrypt_decrypt_roundtrip(mock_env_vars):
    """Тест: зашифровать -> расшифровать = исходный текст"""
    from utils.encryption import encrypt_text, decrypt_text
    
    original = "Sensitive health  BP 120/80"
    encrypted = encrypt_text(original)
    decrypted = decrypt_text(encrypted)
    
    assert decrypted == original
    assert encrypted != original  # Убедимся, что шифрование произошло


def test_decrypt_invalid_token(mock_env_vars):
    """Тест обработки невалидного токена"""
    from utils.encryption import decrypt_text
    
    with pytest.raises(InvalidToken):
        decrypt_text("invalid.encrypted.token.here")


def test_encrypt_different_outputs(mock_env_vars):
    """Тест: одно и то же сообщение шифруется по-разному (из-за случайного IV)"""
    from utils.encryption import encrypt_text
    
    text = "Same message"
    enc1 = encrypt_text(text)
    enc2 = encrypt_text(text)
    
    assert enc1 != enc2  # Fernet использует случайный nonce

