# main.py

import asyncio
from aiogram import Bot, Dispatcher
from config import config
from utils.logging_config import setup_logging
from utils.reminders.scheduler import setup_scheduler

from logic.report.report import report_router
from voice_engine.handler import voice_router

from menu.start_menu import menu_router
from menu.demonstration import demo_router
from utils.language_menu import language_router
from utils.settings import settings_router
from utils.bp_target import target_router
from admin.owner import owner_router
from admin.admin import admin_router
from admin.specialist import specialist_router

from utils.middlewares.logging_middleware import LoggingMiddleware
from utils.middlewares.auth_middleware import UserAuthMiddleware
from utils.middlewares.error_logging import ErrorLoggingMiddleware


logger = setup_logging().bind(
    user_id=None,
    event_type=None,
    module=None
)


async def main():
    bot = Bot(config.bot.token)
    dp = Dispatcher()
    
    dp.message.middleware(UserAuthMiddleware())
    dp.callback_query.middleware(UserAuthMiddleware())
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.update.middleware(ErrorLoggingMiddleware())

    dp.include_router(menu_router)
    dp.include_router(demo_router)
    dp.include_router(language_router)
    dp.include_router(settings_router)
    dp.include_router(voice_router)
    dp.include_router(report_router)
    dp.include_router(target_router)
    dp.include_routers(owner_router, admin_router, specialist_router)
    
    setup_scheduler(bot)
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())