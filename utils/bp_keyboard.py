# utils/bk_keyboard.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def bp_target_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🩺 Изменить целевое АД",
                    callback_data="edit_bp_target_pressure"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❤️ Изменить целевой пульс",
                    callback_data="edit_bp_target_pulse"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data="back_to_settings"
                )
            ],
        ]
    )
    

def format_pressure(digits: str) -> tuple[str, bool]:
    """
    Возвращает:
    - текст для отображения
    - валидно ли АД
    """

    if not digits:
        return "АД: — / — мм рт.ст.", False

    # ещё вводим
    if len(digits) < 4:
        return f"АД: {digits}/ — мм рт.ст.", False

    sad = int(digits[:3])
    dad = int(digits[3:])

    valid = (
        100 <= sad <= 280 and
        60 <= dad <= 150 and
        sad > dad
    )

    status = "✅" if valid else "❌"
    return f"АД: {sad}/{dad} мм рт.ст. {status}", valid
    

def pressure_builder(digits: str | None = None):
    digits = digits or ""

    kb = InlineKeyboardBuilder()

    display_text, is_valid = format_pressure(digits)

    # дисплей
    kb.button(text=display_text, callback_data="noop")

    # цифры
    for i in range(1, 10):
        kb.button(
            text=str(i),
            callback_data=f"pressure_add_{digits}{i}"
        )

    kb.button(
        text="0",
        callback_data=f"pressure_add_{digits}0"
    )

    # управление
    kb.button(
        text="❌",
        callback_data=f"pressure_del_{digits[:-1]}"
    )

    kb.button(
        text="Отменить",
        callback_data="cancel_pressure"
    )

    if is_valid:
        kb.button(
            text="✅ Подтвердить",
            callback_data=f"pressure_confirm_{digits}"
        )

    kb.adjust(1, 3, 3, 3, 2)
    return kb.as_markup()



def old_pressure_builder(digits: list[str] | None = None):
    digits = digits or []

    kb = InlineKeyboardBuilder()

    # --- Отображаемое значение ---
    display_text, is_valid = format_pressure(digits)

    kb.button(
        text=display_text,
        callback_data="noop"
    )

    # --- Цифры ---
    for i in range(1, 10):
        kb.button(text=str(i), callback_data=f"pressure_add_{i}")

    kb.button(text="0", callback_data="pressure_add_0")

    # --- Управление ---
    kb.button(text="❌", callback_data="pressure_del")
    kb.button(text="Отменить", callback_data="cancel_pressure")

    if is_valid:
        kb.button(text="✅ Подтвердить", callback_data="pressure_confirm")

    kb.adjust(1, 3, 3, 3, 2)
    return kb.as_markup()


def pulse_keyboard(digits: str = ""):
    kb = InlineKeyboardBuilder()

    display = digits if digits else "—"
    kb.button(text=f"Пульс: {display}", callback_data="noop")

    for i in range(1, 10):
        kb.button(text=str(i), callback_data=f"pulse_add_{digits}{i}")

    kb.button(text="0", callback_data=f"pulse_add_{digits}0")

    kb.button(text="⌫", callback_data=f"pulse_del_{digits[:-1]}")
    kb.button(text="Отмена", callback_data="cancel_pulse")

    if digits and 30 <= int(digits) <= 220:
        kb.button(text="✅ Подтвердить", callback_data=f"pulse_confirm_{digits}")

    kb.adjust(1, 3, 3, 3, 2)
    return kb.as_markup()