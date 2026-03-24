# menu/start_menu.py
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from menu.keyboard import start_kb, delete_data_keyboard, menu_kb
from mongo import get_or_create_user, delete_user_data, ensure_owner_role


menu_router = Router()


@menu_router.message(CommandStart())
async def command_start(message: Message, bot: Bot):
    await get_or_create_user(message.from_user.id)
    await message.answer(
        "👋 Рад видеть Вас здесь. \n\nКонтроль давления — это не про строгие цифры. \nЭто про спокойствие. \nПро уверенность. \nПро ещё один день рядом с теми, кто важен ❤️",
        reply_markup=menu_kb()
    )
    await message.answer(
        "Давайте я покажу, как всё работает.",
        reply_markup=start_kb()
    )
    await message.delete()

@menu_router.message(Command("delete_my_data"))
async def delete_data_command(message: Message):
    await message.delete()
    await message.answer(
        "⚠️ <b>Внимание!</b> Это действие <b>полностью удалит</b> все ваши данные из базы. Отменить это будет невозможно. Вы уверены, что хотите продолжить?",
        reply_markup=delete_data_keyboard(),
        parse_mode="HTML"
    )

@menu_router.callback_query(F.data == "delete_my_data_confirm")
async def delete_data_confirm(callback: CallbackQuery):
    deleted = await delete_user_data(callback.from_user.id)
    text = "✅ Ваши данные были полностью удалены." if deleted else "ℹ Данные не найдены или уже были удалены."
    await callback.message.edit_text(text)
    await callback.answer()

@menu_router.callback_query(F.data == "delete_my_data_cancel")
async def delete_data_cancel(callback: CallbackQuery):
    await callback.message.edit_text("❎ Удаление данных отменено")
    await callback.answer()

@menu_router.callback_query(F.data == "close_callback")
async def close_settings(call: CallbackQuery):
    await call.message.delete()

@menu_router.message(Command("iamowner"))
async def owner_command(message: Message):
    updated = await ensure_owner_role(message.from_user.id)
    if updated:
        await message.answer("👑 Роль владельца подтверждена")
    else:
        await message.answer("❌ У вас нет прав владельца")
