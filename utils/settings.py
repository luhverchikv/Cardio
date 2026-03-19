# utils/settings.py
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from mongo import get_reminders_status, set_reminders_status
from aiogram.filters import Command

settings_router = Router()

def settings_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎯 Целевые показатели", callback_data="custom_targets")],
            [InlineKeyboardButton(text="🔔 Напоминания", callback_data="open_reminders")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close_callback")],
        ]
    )

def reminders_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔕 Отключить", callback_data="reminder_0")],
            [InlineKeyboardButton(text="🔔 Только утром", callback_data="reminder_1")],
            [InlineKeyboardButton(text="🔔 Только вечером", callback_data="reminder_2")],
            [InlineKeyboardButton(text="🔔 Утром и вечером", callback_data="reminder_3")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_settings")],
        ]
    )

def reminder_status_text(value: int):
    mapping = {
        0: "🔕 Напоминания отключены",
        1: "🌅 Напоминания утром включены",
        2: "🌙 Напоминания вечером включены",
        3: "🌅 + 🌙 Напоминания утром и вечером включены",
    }
    return mapping.get(value, "")

@settings_router.message(Command("settings"))
@settings_router.message(F.text.startswith('⚙️'))
async def cmd_settings(message: Message):
    await message.answer(
        "⚙️ Настройки Выберите нужный раздел:",
        reply_markup=settings_keyboard()
    )
    await message.delete()

@settings_router.callback_query(F.data == "open_reminders")
async def process_reminder(call: CallbackQuery):
    user_id = call.from_user.id
    value = await get_reminders_status(user_id)
    await call.message.edit_text(
        f"{reminder_status_text(value)}\n\nВы можете изменить настройку:",
        reply_markup=reminders_keyboard()
    )
    await call.answer()

@settings_router.callback_query(F.data == "back_to_settings")
async def back_to_settings(call: CallbackQuery):
    await call.message.edit_text(
        "⚙️ Настройки Выберите нужный раздел:",
        reply_markup=settings_keyboard()
    )
    await call.answer()

@settings_router.callback_query(F.data.startswith("reminder_"))
async def process_reminder_setting(call: CallbackQuery):
    value = int(call.data.split("_")[1])
    await set_reminders_status(call.from_user.id, value)
    await call.message.edit_text(
        f"{reminder_status_text(value)}\n\nВы можете изменить настройку снова:",
        reply_markup=reminders_keyboard()
    )
    await call.answer()

