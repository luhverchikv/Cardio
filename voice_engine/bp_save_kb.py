# voice_engine/bp_save_kb.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def build_bp_keyboard(
    systolic: int | None,
    diastolic: int | None,
    pulse: int | None,
    arrhythmic: bool,
    can_save: bool = True
) -> InlineKeyboardMarkup:
    if not can_save:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ Данные недопустимы",
                        callback_data="bp|cancel",
                        style='danger',
                    )
                ]
            ]
        )
    if systolic is None or diastolic is None:
        
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="❌ АД не распознано",
                        callback_data="bp|cancel",
                         style='danger',
                    )
                ]
            ]
        )

        
    a = 1 if arrhythmic else 0

    callback = f"bp|s={systolic}|d={diastolic}|p={pulse}|a={a}"
    print(callback)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💾 Сохранить показатели",
                    callback_data=callback,
                    style='success'
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="bp|cancel",
                    style='danger'
                )
            ]
        ]
    )


