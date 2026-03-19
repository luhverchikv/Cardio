# utils/logging_config.py

from loguru import logger
import sys


def setup_logging():
    logger.remove()  # Убираем стандартный stderr sink

    logger.add(
        "logs/errors.log",
        level="ERROR",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | "
            "user_id={extra[user_id]!s} | "
            "event={extra[event_type]!s}"
        ),
        rotation="1 month",
        compression="zip",
    )

    logger.add(
        "logs/info.log",
        level="INFO",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message} | "
            "user_id={extra[user_id]!s} | "
            "event={extra[event_type]!s}"
        ),
        filter=lambda record: (
            record["level"].no < 40  # ниже ERROR
            and record["extra"].get("module") != "voice"
        ),
        rotation="1 month",
        compression="zip",
    )
    # 🎙 Голос отдельно
    logger.add(
        "logs/voice_recognition.log",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | USER={extra[user_id]!s} | {message}",
        filter=lambda record: record["extra"].get("module") == "voice",
        rotation="1 month",
        compression="zip",
    )

    return logger