# utils/middlewares/logging_middleware.py

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, Update
from typing import Callable, Dict, Any, Awaitable
from loguru import logger


class LoggingMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:

        user_id = None
        event_type = None
        message_text = None

        # --- MESSAGE ---
        if isinstance(event, Message):
            user_id = event.from_user.id

            if event.text:
                if event.text.startswith("/"):
                    event_type = "command"
                    message_text = f"COMMAND: {event.text}"
                else:
                    event_type = "message"
                    message_text = f"TEXT: {event.text}"

            elif event.voice:
                event_type = "voice"
                message_text = "VOICE MESSAGE"

            elif event.photo:
                event_type = "photo"
                message_text = "PHOTO"

            else:
                event_type = "other_message"
                message_text = "OTHER MESSAGE TYPE"

        # --- CALLBACK ---
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            event_type = "callback"
            message_text = f"CALLBACK: {event.data}"

        # --- Логирование ---
        if user_id:
            logger.bind(
                user_id=user_id,
                event_type=event_type
            ).info(message_text)

        # Передаём управление дальше
        return await handler(event, data)