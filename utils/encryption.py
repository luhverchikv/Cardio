# utils/encryption.py
from cryptography.fernet import Fernet
from config import config


# Используем ключ из конфига
fernet = Fernet(config.encryption.fernet_key.encode())


def encrypt_text(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()


def decrypt_text(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()

# Генерация нового ключа
#key = Fernet.generate_key()
#print("Ваш ключ:", key.decode())