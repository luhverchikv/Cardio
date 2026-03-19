# menu/start_menu.py
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from menu.keyboard import start_kb, delete_data_keyboard, menu_kb
from mongo import get_or_create_user, delete_user_data, ensure_owner_role
from locales.loader import LocalizedTranslator
from logic.topic import ensure_user_topics

menu_router = Router()


@menu_router.message(CommandStart())
async def command_start(message: Message, bot: Bot, translator:LocalizedTranslator):
    tg_lang = message.from_user.language_code or ru

    await get_or_create_user(message.from_user.id, tg_lang)
    #await ensure_user_topics(bot, message.chat.id, message.from_user.id)
    await message.answer(
        f"{translator.get('start-greeting')}",
        reply_markup=menu_kb(translator)
    )
    await message.answer(
        f"{translator.get('start-description')}",
        reply_markup=start_kb(translator)
    )
    await message.delete()


@menu_router.message(Command("delete_my_data"))
async def delete_data_command(
    message: Message,
    translator: LocalizedTranslator
):
    await message.delete()

    await message.answer(
        translator.get("delete-warning"),
        reply_markup=delete_data_keyboard(translator),
        parse_mode="HTML"
    )

    
@menu_router.callback_query(F.data == "delete_my_data_confirm")
async def delete_data_confirm(
    callback: CallbackQuery,
    translator: LocalizedTranslator
):
    deleted = await delete_user_data(callback.from_user.id)

    text = (
        translator.get("delete-success")
        if deleted
        else translator.get("delete-not-found")
    )

    await callback.message.edit_text(text)
    await callback.answer()


@menu_router.callback_query(F.data == "delete_my_data_cancel")
async def delete_data_cancel(
    callback: CallbackQuery,
    translator: LocalizedTranslator
):
    await callback.message.edit_text(
        translator.get("delete-cancelled")
    )
    await callback.answer()


@menu_router.callback_query(F.data == "close_callback")
async def close_settings(call: CallbackQuery):
    await call.message.delete()
    

# ПЕРЕРАБОТАТЬ!!!!!
@menu_router.message(Command("iamowner"))
async def owner_command(message: Message):
    updated = await ensure_owner_role(message.from_user.id)
    if updated:
        await message.answer("👑 Роль владельца подтверждена")
    else:
        await message.answer("❌ У вас нет прав владельца")
        