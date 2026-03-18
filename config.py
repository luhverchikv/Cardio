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
    forum_topics: list


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


topics_raw = env("FORUM_TOPICS", "")

forum_topics = []
if topics_raw:
    for item in topics_raw.split(","):
        key, name = item.split(":")
        forum_topics.append({"key": key.strip(), "name": name.strip()})
        

# Создаем конфиг
config = Config(
    bot=TgBot(
        token=env('BOT_TOKEN'),
        owner_id=env.int('OWNER_ID'),
        forum_topics=forum_topics
    ),
    db=DatabaseConfig(
        url=mongo_url,
        name=mongo_db
    ),
    encryption=EncryptionConfig(
        fernet_key=env('FERNET_KEY')
    ),
)