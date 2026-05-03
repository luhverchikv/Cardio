# Cardio – Telegram‑бот для мониторинга артериального давления

## Описание
`Cardio` — это асинхронный Telegram‑бот, написанный на **aiogram 3.x**. Он помогает пользователям фиксировать измерения давления и пульса, получать аналитические отчёты (circadian‑profile, adherence), а также взаимодействовать с ботом голосом. Данные сохраняются в **MongoDB**, а конфиденциальные поля шифруются с помощью **Fernet**.

## Основные возможности
- Регистрация/аутентификация пользователей через Telegram‑ID.
- Запись давления и пульса (текстовый ввод и голосовые сообщения).
- Ежедневные/еженедельные/ежемесячные напоминания о необходимости измерения.
- Генерация отчётов: среднее давление, pulse‑pressure, circadian‑профиль и т.п.
- Административный UI (добавление/редактирование специалистов, рассылка).
- Полный набор unit‑тестов (конфигурация, шифрование, Mongo‑операции).

## Структура проекта
```
Cardio-main/
├─ admin/               # Админ‑панель и UI
├─ menu/                # Меню для обычных пользователей
├─ logic/               # Бизнес‑логика, аналитика, отчёты
│   └─ analytics/       # circadian, adherence и пр.
├─ voice_engine/        # Обработка голосовых сообщений (ffmpeg, vosk)
├─ utils/               # Middleware, reminders, metrics, encryption
├─ mongo.py             # Асинхронный клиент MongoDB
├─ config.py            # Загрузка переменных окружения (environs)
├─ main.py              # Точка входа, подключение роутеров и scheduler
├─ run_tests.sh         # Скрипт для локального запуска тестов
└─ requirements.txt     # Список зависимостей (Python)
```

## Требования
- **Python 3.11** (или выше)
- **Docker** (рекомендовано для production)
- **MongoDB** (можно запустить в Docker)
- Системные пакеты: `ffmpeg`, `libopus0`, `libsndfile1` (для `voice_engine`).

## Быстрый старт (локально)
```bash
# 1. Клонировать репозиторий (уже сделано в workspace)
cd Cardio_repo/Cardio-main

# 2. Создать виртуальное окружение и установить зависимости
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Скопировать пример файла окружения и задать переменные
cp example.env .env
# отредактируйте .env: BOT_TOKEN, OWNER_ID, MONGO_*, FERNET_KEY и пр.

# 4. Запустить Mongo (Docker‑композ)
 docker run -d --name cardio-mongo -p 27017:27017 mongo:6

# 5. Запустить бота
python main.py
```
Bot будет работать в режиме **polling**. Для production рекомендуется использовать webhook (см. ниже).

## Запуск в Docker
```bash
# Собрать образ
docker build -t cardio-bot .

# Запустить контейнер, передав переменные окружения из .env
docker run -d \
  --name cardio \
  --restart unless-stopped \
  --env-file .env \
  cardio-bot
```
Образ включает все системные зависимости (ffmpeg, libsndfile, git) и Python‑пакеты.

## Конфигурация (`.env`)
| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен бота от BotFather |
| `OWNER_ID`  | Telegram‑ID владельца (int) |
| `MONGO_USER`, `MONGO_PASS`, `MONGO_HOST`, `MONGO_PORT`, `MONGO_DB` | Параметры подключения к MongoDB |
| `FERNET_KEY` | 44‑символьный ключ Fernet для шифрования |
| `USE_WEBHOOK` (opt) | `True` – включить webhook, `False` – polling |
| `WEBHOOK_URL` (opt) | URL, куда Telegram будет отправлять обновления |

## Webhook (production)
1. Установите переменные `USE_WEBHOOK=True` и `WEBHOOK_URL=https://your.domain/bot` в `.env`.
2. Убедитесь, что у вас есть действительный SSL‑сертификат (Telegram требует HTTPS).
3. При старте бота автоматически вызовется `setup_webhook()`.

## Тесты
```bash
# Запуск всех тестов
pytest -vv
# Запуск только тестов конфигурации
pytest tests/test_config.py
```
Тестовый набор покрывает загрузку конфигурации, проверку Fernet‑ключа и работу с Mongo‑моками.

## Лицензия
Этот проект распространяется под лицензией **MIT** – см. файл `LICENSE` в корне репозитория.

---
*Создано автоматически Hermes‑Agent на основе текущего состояния репозитория.*