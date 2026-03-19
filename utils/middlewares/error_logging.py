# utils/middlewares/error_logging.py

from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Dict, Any, Awaitable
from loguru import logger


class ErrorLoggingMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
        event: Update,
        data: Dict[str, Any]
    ) -> Any:

        try:
            return await handler(event, data)

        except Exception:
            user_id = None
            chat_id = None
            event_type = None

            # --- MESSAGE ---
            if event.message:
                user_id = event.message.from_user.id
                chat_id = event.message.chat.id
                event_type = "message"

            # --- CALLBACK ---
            elif event.callback_query:
                user_id = event.callback_query.from_user.id
                chat_id = event.callback_query.message.chat.id
                event_type = "callback"

            # --- INLINE QUERY ---
            elif event.inline_query:
                user_id = event.inline_query.from_user.id
                event_type = "inline_query"

            else:
                event_type = "unknown_update"

            logger.bind(
                user_id=user_id,
                event_type=event_type
            ).exception("Unhandled exception in handler")

            raise  # обязательно пробрасываем дальше