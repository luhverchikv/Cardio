# menu/keyboard.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from locales.loader import LocalizedTranslator


def start_kb(translator: LocalizedTranslator) -> ReplyKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=translator.get("start-demo"),
                    callback_data="start_demo"
                )
            ],
    
        ]
    )


def menu_kb(translator: LocalizedTranslator) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            #[KeyboardButton(text=translator.get("start-button-bp"))],
            [KeyboardButton(text=translator.get("start-button-settings"))],
            [KeyboardButton(text=translator.get("start-button-report"), style='primary')],
        ],
        resize_keyboard=True
    )
    
    
def delete_data_keyboard(translator: LocalizedTranslator):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=translator.get("delete-confirm"),
                    callback_data="delete_my_data_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    text=translator.get("delete-cancel"),
                    callback_data="delete_my_data_cancel"
                )
            ]
        ]
    )