#utils/middlewares/auth_middleware.py

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery # Добавляем CallbackQuery
from mongo import users_collection 


class UserAuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        
        # Получаем user_id из события
        # TelegramObject - это базовый класс для всех событий
        user_id = event.from_user.id
        
        user_exists = await users_collection.find_one({"user_id": user_id})
        
        # Если пользователь не найден в базе данных
        if not user_exists:
            
            # Проверяем тип события и его данные
            is_start_command = False
            if isinstance(event, Message) and event.text and event.text.strip().lower() == "/start":
                is_start_command = True
            
            # Разрешаем обработку только для команды /start
            if is_start_command:
                return await handler(event, data)
            else:
                # Для всех остальных команд, сообщений и callback-запросов
                if isinstance(event, CallbackQuery):
                    await event.answer("Пожалуйста, нажмите /start, чтобы начать работу с ботом.", show_alert=True)
                else:
                    await event.answer("Пожалуйста, нажмите /start, чтобы начать работу с ботом.")
                
                # Очищаем состояние пользователя, если оно есть
                if 'state' in data:
                    await data['state'].clear()
                return 
                
        # Если пользователь найден, пропускаем его к хендлеру
        return await handler(event, data)