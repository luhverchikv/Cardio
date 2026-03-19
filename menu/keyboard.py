# menu/keyboard.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def start_kb() -> ReplyKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=Знакомство с ботом",
                    callback_data="start_demo"
                )
            ],
    
        ]
    )


def menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=⚙️ Настройки")],
            [KeyboardButton(text=📋 Отчет", style='primary')],
        ],
        resize_keyboard=True
    )
    
    
def delete_data_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, удалить мои данные",
                    callback_data="delete_my_data_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="delete_my_data_cancel"
                )
            ]
        ]
    )