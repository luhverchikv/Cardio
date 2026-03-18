# config.py
from dataclasses import dataclass
from environs import Env


@dataclass
class DatabaseConfig:
    url: str
    name: str


@dataclass
class TgBot:
    token: str
    owner_id: int


@dataclass
class EncryptionConfig:
    fernet_key: str


@dataclass
class Config:
    bot: TgBot
    db: DatabaseConfig
    encryption: EncryptionConfig


# Инициализация Env
env = Env()
env.read_env()  # Читаем из .env файла в корне проекта

# Формируем URL подключения
mongo_user = env("MONGO_USER")
mongo_pass = env("MONGO_PASS")
mongo_host = env("MONGO_HOST", "localhost")
mongo_port = env("MONGO_PORT", "27017")
mongo_db = env("MONGO_DB")

mongo_url = (
    f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/"
    f"{mongo_db}?authSource={mongo_db}"
)


# Создаем конфиг
config = Config(
    bot=TgBot(
        token=env('BOT_TOKEN'),
        owner_id=env.int('OWNER_ID')
    ),
    db=DatabaseConfig(
        url=mongo_url,
        name=mongo_db
    ),
    encryption=EncryptionConfig(
        fernet_key=env('FERNET_KEY')
    ),
)