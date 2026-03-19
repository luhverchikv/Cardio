# utils/settings.py

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from locales.loader import LocalizedTranslator
from mongo import get_reminders_status, set_reminders_status
from aiogram.filters import Command

settings_router = Router()


def settings_keyboard(translator: LocalizedTranslator):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=translator.get("settings-targets"),
                callback_data="custom_targets"
            )],
            [InlineKeyboardButton(
                text=translator.get("settings-reminders"),
                callback_data="open_reminders"
            )],
            [InlineKeyboardButton(
                text=translator.get("settings-close"),
                callback_data="close_callback"
            )],
        ]
    )


def reminders_keyboard(translator: LocalizedTranslator):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=translator.get("reminder-off"),
                callback_data="reminder_0"
            )],
            [InlineKeyboardButton(
                text=translator.get("reminder-morning"),
                callback_data="reminder_1"
            )],
            [InlineKeyboardButton(
                text=translator.get("reminder-evening"),
                callback_data="reminder_2"
            )],
            [InlineKeyboardButton(
                text=translator.get("reminder-both"),
                callback_data="reminder_3"
            )],
            [InlineKeyboardButton(
                text=translator.get("back-button"),
                callback_data="back_to_settings"
            )],
        ]
    )


def reminder_status_text(value: int, translator: LocalizedTranslator):
    mapping = {
        0: translator.get("reminders-disabled"),
        1: translator.get("reminders-morning"),
        2: translator.get("reminders-evening"),
        3: translator.get("reminders-both"),
    }
    return mapping.get(value, "")

@settings_router.message(Command("settings"))
@settings_router.message(F.text.startswith('⚙️'))
async def cmd_settings(message: Message, translator: LocalizedTranslator):
    await message.answer(
        translator.get("settings-title"),
        reply_markup=settings_keyboard(translator)
    )
    await message.delete()


@settings_router.callback_query(F.data == "open_reminders")
async def process_reminder(call: CallbackQuery, translator: LocalizedTranslator):
    user_id = call.from_user.id
    value = await get_reminders_status(user_id)

    await call.message.edit_text(
        f"{reminder_status_text(value, translator)}\n\n"
        f"{translator.get('reminders-change')}",
        reply_markup=reminders_keyboard(translator)
    )
    await call.answer()


@settings_router.callback_query(F.data == "back_to_settings")
async def back_to_settings(call: CallbackQuery, translator: LocalizedTranslator):
    await call.message.edit_text(
        translator.get("settings-title"),
        reply_markup=settings_keyboard(translator)
    )
    await call.answer()


@settings_router.callback_query(F.data.startswith("reminder_"))
async def process_reminder_setting(call: CallbackQuery, translator: LocalizedTranslator):
    value = int(call.data.split("_")[1])
    await set_reminders_status(call.from_user.id, value)

    await call.message.edit_text(
        f"{reminder_status_text(value, translator)}\n\n"
        f"{translator.get('reminders-change-again')}",
        reply_markup=reminders_keyboard(translator)
    )
    await call.answer()