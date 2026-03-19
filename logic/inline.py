# blood_pressure/inline.py

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_numeric_keyboard(current: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    
    kb.button(text=f"Текущее: {current or '—'}", callback_data="noop")
    kb.add(
        InlineKeyboardButton(text="1", callback_data="digit_1"),
        InlineKeyboardButton(text="2", callback_data="digit_2"),
        InlineKeyboardButton(text="3", callback_data="digit_3"),
        InlineKeyboardButton(text="4", callback_data="digit_4"),
        InlineKeyboardButton(text="5", callback_data="digit_5"),
        InlineKeyboardButton(text="6", callback_data="digit_6"),
        InlineKeyboardButton(text="7", callback_data="digit_7"),
        InlineKeyboardButton(text="8", callback_data="digit_8"),
        InlineKeyboardButton(text="9", callback_data="digit_9"),
        InlineKeyboardButton(text="0", callback_data="digit_0"),
    )
    kb.add(
        InlineKeyboardButton(text="/", callback_data="slash"),
        InlineKeyboardButton(text="-", callback_data="hyphen"),
        InlineKeyboardButton(text="⌫", callback_data="backspace"),
    )
    kb.add(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_input"),
        InlineKeyboardButton(text="✅ Сохранить", callback_data="confirm_input")
    )
    kb.adjust(1, 3, 3, 3, 1, 3, 2)
    return kb.as_markup()