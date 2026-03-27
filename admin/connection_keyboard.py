# admin/connection_keyboard.py
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from math import ceil
from utils.encryption import decrypt_text


def get_add_admin_keyboard(broadcast_callback: str = "start_broadcast_owner"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Пригласить администратора", callback_data="add_admin")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data=broadcast_callback)]
    ])


def get_add_specialist_keyboard(broadcast_callback: str = "start_broadcast_admin"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Пригласить специалиста", callback_data="add_specialist")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data=broadcast_callback)]
    ])
    

def get_add_smart_user_keyboard(broadcast_callback: str = "start_broadcast_specialist"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Пригласить Smart-пользователя", callback_data="add_smart_user")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data=broadcast_callback)]
    ])
    

def get_paginated_keyboard(
    entities: list[dict], 
    page: int, 
    per_page: int = 10, 
    entity_prefix: str = "entity", 
    id_field: str = "user_id",
    broadcast_callback: str = "start_broadcast"
):
    """
    Создаёт клавиатуру со списком сущностей с пагинацией.
    
    entity_prefix теперь соответствует config.role:
    - "admin" → владелец добавляет админов
    - "specialist" → админ добавляет специалистов
    - "smart_user" → специалист добавляет smart-пользователей
    """
    
    # ✅ Исправленная логика: entity_prefix = config.role
    if entity_prefix == "admin":
        add_role = "add_admin"
        invite_text = "➕ Пригласить администратора"
    elif entity_prefix == "specialist":
        add_role = "add_specialist"
        invite_text = "➕ Пригласить специалиста"
    elif entity_prefix == "smart_user":
        add_role = "add_smart_user"
        invite_text = "➕ Пригласить Smart-пользователя"
    else:
        add_role = "ignore"
        invite_text = "➕ Пригласить"
    
    builder = InlineKeyboardBuilder()
    
    # Кнопка добавления (только если не ignore)
    if add_role != "ignore":
        builder.row(InlineKeyboardButton(text=invite_text, callback_data=add_role))
    
    # Кнопка рассылки (можно оставить для всех или убрать для некоторых ролей)
    builder.row(InlineKeyboardButton(text="📢 Сделать рассылку", callback_data=broadcast_callback))

    # Выбираем нужную страницу
    start_index = page * per_page
    end_index = start_index + per_page
    paginated_entities = entities[start_index:end_index]

    # Создаём кнопки для никнеймов
    for entity in paginated_entities:
        raw_alias = entity.get("alias")
        alias = decrypt_text(raw_alias) if raw_alias else "Без имени"
        
        entity_id = entity.get(id_field)
        if entity_id:
            button = InlineKeyboardButton(
                text=alias, 
                callback_data=f"{entity_prefix}:{entity_id}"
            )
            builder.row(button)

    # Если сущностей нет, добавим подсказку
    if not paginated_entities:
        builder.row(InlineKeyboardButton(text="📭 Список пуст", callback_data="ignore"))

    # Пагинация
    total_pages = ceil(len(entities) / per_page) if entities else 1

    pagination_row = []
    if page > 0:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{entity_prefix}:{page - 1}")
        )
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    pagination_row.append(
        InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="ignore")
    )

    if page < total_pages - 1:
        pagination_row.append(
            InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"page_{entity_prefix}:{page + 1}")
        )
    else:
        pagination_row.append(InlineKeyboardButton(text=" ", callback_data="ignore"))

    builder.row(*pagination_row)

    return builder.as_markup()


def get_entity_card_keyboard(
    entity: dict,
    entity_prefix: str = "entity",
    id_field: str = "user_id",
    show_broadcast: bool = False,
    show_chart: bool = False,
    show_analytics: bool = False,
    show_close: bool = True
    ):
    entity_id = entity.get("user_id")
    builder = InlineKeyboardBuilder()
    # ✅ Первый ряд: Редактировать
    builder.row(
        InlineKeyboardButton(
            text="✍️ Редактировать",
            callback_data=f"edit_{entity_prefix}:{entity_id}"
        )
    )
    
    # ✅ Второй ряд: Удалить
    builder.row(
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"delete_{entity_prefix}:{entity_id}"
        )
    )
    
    # ✅ Третий ряд: Рассылка (если включена)
    if show_broadcast:
        builder.row(
            InlineKeyboardButton(
                text="✉️ Отправить сообщение",
                callback_data=f"broadcast_to_entity:{entity_prefix}:{entity_id}"
            )
        )
    
    # ✅ Четвёртый ряд: График и Аналитика (если включены) - в одном ряду
    chart_and_analytics_buttons = []
    
    if show_chart:
        chart_and_analytics_buttons.append(
            InlineKeyboardButton(
                text="📊 График",
                callback_data=f"view_chart:{entity_prefix}:{entity_id}"
            )
        )
    
    if show_analytics:
        chart_and_analytics_buttons.append(
            InlineKeyboardButton(
                text="📋 Аналитика",
                callback_data=f"view_analytics:{entity_prefix}:{entity_id}"
            )
        )
    
    if chart_and_analytics_buttons:
        builder.row(*chart_and_analytics_buttons)
    
    # ✅ Последний ряд: Закрыть (если включено)
    if show_close:
        builder.row(
            InlineKeyboardButton(
                text="❌ Закрыть",
                callback_data="close_callback"
            )
        )
    
    return "", builder.as_markup()
    

def get_broadcast_keyboard(available_targets: list[str]):
    """
    Создаёт клавиатуру выбора группы для рассылки.
    
    Args:
        available_targets: Список доступных целей для рассылки
                          (например: ["smart_users", "debug"])
    
    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками групп
    """
    builder = InlineKeyboardBuilder()
    
    # ✅ Понятные названия для каждой группы
    target_labels = {
        "admins": "👥 Администраторам",
        "specialists": "👥 Специалистам (моим)",
        "all_specialists": "🌍 Всем специалистам",
        "smart_users": "👥 Smart-пользователям (моим)",
        "all_smart_users": "🌍 Всем Smart-пользователям",
        "users": "🌍 Всем пользователям",
        "debug": "🛠️ Отладочная (себе)"
    }
    
    for target in available_targets:
        builder.row(
            InlineKeyboardButton(
                text=target_labels.get(target, target),
                callback_data=f"broadcast_to:{target}"
            )
        )
    
    return builder.as_markup()