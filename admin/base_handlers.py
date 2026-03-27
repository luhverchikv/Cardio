# admin/base_handlers.py

import asyncio
from aiogram import F, Bot
from aiogram.types import Message, Contact, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from datetime import datetime
from admin.connection_keyboard import get_paginated_keyboard, get_entity_card_keyboard, get_broadcast_keyboard
from admin.entity_config import EntityConfig
from admin.broadcast import send_broadcast_message
from mongo import users_collection, update_user_roles_and_connections, update_entity_alias, delete_entity_from_db
from logic.report.blood_pressure_chart import generate_blood_pressure_chart
from utils.encryption import decrypt_text
from logic.analytics import generate_smart_user_analytics

class BaseEntityStates(StatesGroup):
    """Базовые состояния (для общих функций)"""
    waiting_for_broadcast_recipients = State()
    waiting_for_broadcast_content = State()


# ✅ ОТДЕЛЬНЫЕ СОСТОЯНИЯ ДЛЯ КАЖДОЙ РОЛИ
class OwnerStates(StatesGroup):
    """Состояния для Владельца"""
    waiting_for_contact = State()
    waiting_for_alias = State()
    editing_entity_alias = State()


class AdminStates(StatesGroup):
    """Состояния для Админа"""
    waiting_for_contact = State()
    waiting_for_alias = State()
    editing_entity_alias = State()


class SpecialistStates(StatesGroup):
    """Состояния для Специалиста"""
    waiting_for_contact = State()
    waiting_for_alias = State()
    editing_entity_alias = State()


class BroadcastStates(StatesGroup):
    """Состояния для рассылки"""
    waiting_for_broadcast_recipients = State()
    waiting_for_broadcast_content = State()


def format_analytics_text(analytics: dict, alias: str) -> str:
    text = f"📊 **Аналитика: {alias}**\n"
    text += f"📅 Период: {analytics.get('period', 'N/A')}\n"
    text += "━" * 20 + "\n\n"
    
    # Основные метрики
    text += "**📈 Средние значения:**\n"
    if analytics.get('avg_systolic'):
        text += f"  • Систолическое (верхнее): {analytics['avg_systolic']} мм рт.ст.\n"
    if analytics.get('avg_diastolic'):
        text += f"  • Диастолическое (нижнее): {analytics['avg_diastolic']} мм рт.ст.\n"
    if analytics.get('avg_pulse'):
        text += f"  • Пульс: {analytics['avg_pulse']} уд/мин\n"
    
    text += "\n"
    
    # Целевые показатели
    targets = analytics.get('targets', {})
    if targets:
        text += "**🎯 Целевые значения:**\n"
        text += f"  • САД: {targets.get('systolic', 'не задано')} мм рт.ст.\n"
        text += f"  • ДАД: {targets.get('diastolic', 'не задано')} мм рт.ст.\n"
        text += "\n"
    
    # Приверженность и контроль
    text += "**📋 Приверженность лечению:**\n"
    adherence = analytics.get('adherence', 0)
    text += f"  • Измерения: {adherence:.0f}% дней\n"
    dtir = analytics.get('dtir', 0)
    text += f"  • Дни в целевом диапазоне: {dtir:.0f}%\n"
    text += f"  • Всего записей: {analytics.get('records_count', 0)}\n"
    
    text += "\n"
    
    # Тренд
    trend = analytics.get('trend', '➡️ Стабильно')
    text += f"**{trend}** Тренд артериального давления\n"
    
    # Предупреждения
    alerts = analytics.get('alerts', [])
    if alerts:
        text += "\n**⚠️ Рекомендации:**\n"
        for alert in alerts:
            text += f"  {alert}\n"
    
    return text


# ========== ОБЩИЕ ХЕНДЛЕРЫ ==========

async def list_entities_handler(
    message: Message,
    config: EntityConfig,
    required_role: str,
    broadcast_callback: str = "start_broadcast"  # ✅ Уникальный callback
):
    """Универсальный список сущностей"""
    user_id = message.from_user.id
    user_doc = await users_collection.find_one({"user_id": user_id})
    entities = user_doc.get(config.connection_field, [])
    
    if not entities:
        from admin.connection_keyboard import get_add_admin_keyboard, get_add_specialist_keyboard, get_add_smart_user_keyboard
        keyboard_map = {
            "admin": lambda: get_add_admin_keyboard(broadcast_callback),
            "specialist": lambda: get_add_specialist_keyboard(broadcast_callback),
            "smart_user": lambda: get_add_smart_user_keyboard(broadcast_callback)
        }
        keyboard_func = keyboard_map.get(config.role)
        reply_markup = keyboard_func() if keyboard_func else None
        await message.answer(config.empty_message, reply_markup=reply_markup)
        return

    total = len(entities)
    keyboard = get_paginated_keyboard(
        entities=entities,
        page=0,
        entity_prefix=config.role,
        id_field=config.id_field,
        broadcast_callback=broadcast_callback  # ✅ Передаём уникальный callback
    )

    text = f"👥 Всего {config.display_name.replace('ом', 'ов') if config.display_name.endswith('ом') else config.display_name}: <b>{total}</b>\n\nВыберите:"
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


async def add_entity_callback_handler(
    callback: CallbackQuery,
    state: FSMContext,
    config: EntityConfig
):
    """Универсальный запрос контакта с выбором состояния по роли"""
    
    # ✅ Выбираем состояние в зависимости от роли
    state_map = {
        "admin": OwnerStates.waiting_for_contact,      # Owner добавляет admin
        "specialist": AdminStates.waiting_for_contact,  # Admin добавляет specialist
        "smart_user": SpecialistStates.waiting_for_contact  # Specialist добавляет smart_user
    }
    
    target_state = state_map.get(config.role)
    if not target_state:
        await callback.answer("❌ Ошибка: неизвестная роль", show_alert=True)
        return
    
    await callback.message.answer(
        f"Пожалуйста, отправьте контакт пользователя, которого вы хотите сделать {config.display_name}."
    )
    await state.set_state(target_state)
    await state.update_data(entity_role=config.role)
    await callback.answer()


async def process_entity_contact(
    message: Message,
    state: FSMContext,
    config: EntityConfig
):
    """Универсальная обработка контакта с проверкой на дубликаты"""
    contact: Contact = message.contact
    target_id = contact.user_id
    requester_id = message.from_user.id
    
    # 1️⃣ Проверяем, зарегистрирован ли пользователь в боте
    user_exists = await users_collection.find_one({"user_id": target_id})
    if not user_exists:
        await message.answer("❌ Этот пользователь не зарегистрирован в боте.")
        await state.clear()
        return

    # 2️⃣ ✅ ПРОВЕРКА НА ДУБЛИКАТЫ: Получаем документ владельца
    requester_doc = await users_collection.find_one({"user_id": requester_id})
    if not requester_doc:
        await message.answer("❌ Ошибка: ваш профиль не найден.")
        await state.clear()
        return

    # 3️⃣ ✅ Проверяем, нет ли уже этой сущности в связях владельца
    existing_entities = requester_doc.get(config.connection_field, [])
    for entity in existing_entities:
        if entity.get(config.id_field) == target_id:
            # ✅ Нашли дубликат!
            raw_alias = entity.get("alias", "")
            try:
                alias = decrypt_text(raw_alias)
            except Exception:
                alias = "Неизвестно"
            
            await message.answer(
                f"❌ Этот пользователь уже добавлен как {config.display_name}!\n\n"
                f"👤 Псевдоним: <b>{alias}</b>\n"
                f"Используйте редактирование, если хотите изменить псевдоним.",
                parse_mode="HTML",
            )
            await state.clear()
            return

    # 4️⃣ Если дубликатов нет — отправляем запрос на подтверждение
    builder = InlineKeyboardBuilder()
    builder.button(
        text="✅ Подтвердить",
        callback_data=f"confirm_{config.role}:{target_id}:{requester_id}"
    )
    
    try:
        await message.bot.send_message(
            chat_id=target_id,
            text=f"Здравствуйте! Вам предложили роль {config.display_name}. Вы согласны?",
            reply_markup=builder.as_markup()
        )
        await message.answer(f"✅ Запрос на назначение {config.display_name} отправлен. Дождитесь подтверждения.")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить сообщение пользователю. Ошибка: {e}")
    
    await state.clear()


async def confirm_entity_role(
    call: CallbackQuery,
    state: FSMContext,
    config: EntityConfig
):
    """Универсальное подтверждение роли"""
    parts = call.data.split(":")
    target_id = int(parts[1])
    requester_id = int(parts[2])
    
    await call.message.edit_text(config.confirm_message)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="Продолжить", callback_data=f"set_{config.role}_alias:{target_id}")
    
    await call.message.bot.send_message(
        chat_id=requester_id,
        text="Пользователь согласился.",
        reply_markup=builder.as_markup()
    )


async def start_alias_input(
    call: CallbackQuery,
    state: FSMContext,
    config: EntityConfig
):
    """Универсальный запрос псевдонима с выбором состояния по роли"""
    
    # ✅ Выбираем состояние в зависимости от роли
    state_map = {
        "admin": OwnerStates.waiting_for_alias,
        "specialist": AdminStates.waiting_for_alias,
        "smart_user": SpecialistStates.waiting_for_alias
    }
    
    target_state = state_map.get(config.role)
    if not target_state:
        await call.answer("❌ Ошибка: неизвестная роль", show_alert=True)
        return
    
    target_id = int(call.data.split(":")[1])
    requester_id = call.from_user.id
    
    await call.message.edit_text(config.alias_prompt)
    await state.set_state(target_state)  # ✅ Устанавливаем правильное состояние
    await state.update_data(
        current_entity_id=target_id,
        requester_id=requester_id,
        entity_role=config.role
    )


async def process_entity_alias(
    message: Message,
    state: FSMContext,
    config: EntityConfig
):
    """Универсальное сохранение псевдонима"""
    alias = message.text
    data = await state.get_data()
    target_id = data.get("current_entity_id")
    requester_id = data.get("requester_id")

    await update_user_roles_and_connections(
        requester_id=requester_id,
        target_id=target_id,
        target_role=config.role,
        alias=alias,
        connection_field=config.connection_field
    )
    
    await message.answer(config.alias_saved.format(alias=alias))
    await state.clear()


async def paginate_entities_handler(
    call: CallbackQuery,
    config: EntityConfig
):
    """Универсальная пагинация"""
    parts = call.data.split(":")
    page = int(parts[1])
    user_id = call.from_user.id

    user_doc = await users_collection.find_one({"user_id": user_id})
    entities = user_doc.get(config.connection_field, [])

    keyboard = get_paginated_keyboard(
        entities=entities,
        page=page,
        entity_prefix=config.role,
        id_field=config.id_field
    )

    total = len(entities)
    text = f"👥 Всего {config.display_name.replace('ом', 'ов') if config.display_name.endswith('ом') else config.display_name}: <b>{total}</b>\n\nВыберите:"

    await call.message.edit_text(text, reply_markup=keyboard)


async def show_entity_card(
    call: CallbackQuery,
    config: EntityConfig,
    show_broadcast: bool = False,  # ✅ Передаём параметры
    show_chart: bool = False,
    show_close: bool = True
):
    """Универсальная карточка сущности"""
    entity_id = int(call.data.split(":")[1])
    owner_id = call.from_user.id
    
    # 1️⃣ Получаем документ владельца
    owner_doc = await users_collection.find_one({"user_id": owner_id})
    if not owner_doc:
        await call.answer("Владелец не найден", show_alert=True)
        return

    # 2️⃣ Ищем сущность в массиве подключений владельца
    entity_data = None
    for entity in owner_doc.get(config.connection_field, []):
        if entity.get(config.id_field) == entity_id:
            entity_data = entity
            break
    
    if not entity_data:
        await call.answer("Сущность не найдена в ваших связях", show_alert=True)
        return

    # 3️⃣ Получаем alias из связи владельца
    raw_alias = entity_data.get("alias", "Не указан")
    try:
        alias = decrypt_text(raw_alias)
    except Exception:
        alias = raw_alias

    # 4️⃣ Получаем документ сущности
    entity_doc = await users_collection.find_one({"user_id": entity_id})
    if not entity_doc:
        await call.answer("Сущность не найдена", show_alert=True)
        return

    # 5️⃣ Формируем текст с дополнительной информацией
    text = f"👤 <b>{alias}</b>\n"
    
    
    # Можно добавить дату назначения, если есть
    created_info = entity_doc.get("created_by", {})
    connected_at = created_info.get("connected_at")
    if connected_at:
        if isinstance(connected_at, str):
            connected_at = datetime.fromisoformat(connected_at)
        text += f"📅 Дата назначения: {connected_at.strftime('%d.%m.%Y')}\n"

    # 6️⃣ Получаем клавиатуру с нужными кнопками
    _, keyboard = get_entity_card_keyboard(
        entity_doc,
        config.role,
        config.id_field,
        show_broadcast=show_broadcast,
        show_chart=show_chart,
        show_close=show_close
    )

    await call.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


async def start_edit_entity_alias(
    call: CallbackQuery,
    state: FSMContext,
    config: EntityConfig
):
    """Универсальное начало редактирования с выбором состояния по роли"""
    
    # ✅ Выбираем состояние в зависимости от роли
    state_map = {
        "admin": OwnerStates.editing_entity_alias,
        "specialist": AdminStates.editing_entity_alias,
        "smart_user": SpecialistStates.editing_entity_alias
    }
    
    target_state = state_map.get(config.role)
    if not target_state:
        await call.answer("❌ Ошибка: неизвестная роль", show_alert=True)
        return
    
    entity_id = int(call.data.split(":")[1])
    
    await call.message.edit_text(f"✏️ Введите новый никнейм для {config.display_name}:")
    await state.set_state(target_state)  # ✅ Устанавливаем правильное состояние
    await state.update_data(
        editing_entity_id=entity_id,
        entity_type=config.role
    )


async def process_edit_entity_alias(
    message: Message,
    state: FSMContext,
    config: EntityConfig
):
    """Универсальное сохранение редактирования"""
    alias = message.text.strip()
    data = await state.get_data()
    entity_id = data.get("editing_entity_id")
    requester_id = message.from_user.id

    await update_entity_alias(requester_id, entity_id, alias, config.connection_field)

    await message.answer(f"✅ Никнейм обновлён: <b>{alias}</b>")
    await state.clear()


async def delete_entity_handler(
    call: CallbackQuery,
    config: EntityConfig
):
    """Универсальное удаление"""
    entity_id = int(call.data.split(":")[1])
    requester_id = call.from_user.id
    
    await delete_entity_from_db(
        requester_id,
        entity_id,
        config.role,
        config.connection_field
    )

    await call.message.edit_text(config.delete_message)


# ========= Функция рассылки ===========

async def start_broadcast_handler(
    call: CallbackQuery,
    state: FSMContext,
    config: EntityConfig,
    available_targets: list[str]
):
    """Универсальный старт рассылки с клавиатурой из connection_keyboard"""
    
    keyboard = get_broadcast_keyboard(available_targets)
    
    await call.message.edit_text(
        "📢 <b>Кому отправить рассылку?</b>\n\n"
        "Выберите целевую группу:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_for_broadcast_recipients)
    await state.update_data(broadcast_config=config)
    await call.answer()


async def get_broadcast_recipients(
    call: CallbackQuery,
    state: FSMContext,
    config: EntityConfig
):
    """Получение списка получателей с учётом иерархии ролей"""
    target_group = call.data.split(":")[1]
    user_id = call.from_user.id
    
    user_ids = []
    
    # ✅ DEBUG — всем доступен (только себе)
    if target_group == "debug":
        user_ids = [user_id]
    
    # ✅ ВСЕ ПОЛЬЗОВАТЕЛИ — только Owner
    elif target_group == "users":
        cursor = users_collection.find({}, {"user_id": 1})
        all_users = await cursor.to_list(length=None)
        user_ids = [u["user_id"] for u in all_users]
    
    # ✅ ВСЕ СПЕЦИАЛИСТЫ — только Owner (ищет по всей базе)
    elif target_group == "all_specialists":
        cursor = users_collection.find(
            {"roles": "specialist"},
            {"user_id": 1}
        )
        all_specialists = await cursor.to_list(length=None)
        user_ids = [s["user_id"] for s in all_specialists]
        #user_ids = [s["user_id"] for s in all_specialists if s["user_id"] != user_id]
    
    # ✅ ВСЕ SMART-ПОЛЬЗОВАТЕЛИ — только Owner (ищет по всей базе)
    elif target_group == "all_smart_users":
        cursor = users_collection.find(
            {"roles": "smart_user"},
            {"user_id": 1}
        )
        all_smart_users = await cursor.to_list(length=None)
        user_ids = [s["user_id"] for s in all_smart_users]
    
    # ✅ АДМИНЫ — только Owner (из connected_admins)
    elif target_group == "admins":
        owner_doc = await users_collection.find_one({"user_id": user_id})
        if owner_doc:
            admins = owner_doc.get("connected_admins", [])
            user_ids = [a.get("admin_id") for a in admins if a.get("admin_id")]
    
    # ✅ СПЕЦИАЛИСТЫ — Owner (все из базы) или Admin (только свои connected)
    elif target_group == "specialists":
        user_doc = await users_collection.find_one({"user_id": user_id})
        if user_doc:
            # Проверяем роль пользователя
            user_roles = user_doc.get("roles", [])
            if "admin" in user_roles:
                # Admin получает только СВОИХ connected_specialists
                specialists = user_doc.get("connected_specialists", [])
                user_ids = [s.get("specialist_id") for s in specialists if s.get("specialist_id")]
    
    # ✅ SMART-ПОЛЬЗОВАТЕЛИ — Admin/Specialist (только свои connected)
    elif target_group == "smart_users":
        user_doc = await users_collection.find_one({"user_id": user_id})
        if user_doc:
            smart_users = user_doc.get("connected_smart_users", [])
            user_ids = [s.get("smart_user_id") for s in smart_users if s.get("smart_user_id")]
    
    # ✅ Удаляем дубликаты
    recipients_set = set(user_ids)
    recipients_list = list(recipients_set)
    
    if not recipients_list:
        await call.message.edit_text("❌ Нет получателей для этой группы.")
        await state.clear()
        return
    
    await state.update_data(
        broadcast_recipients=recipients_list,
        broadcast_target=target_group
    )
    
    await call.message.edit_text(
        f"✅ Выбрано получателей: <b>{len(recipients_list)}</b>\n\n"
        "📝 Теперь отправьте сообщение для рассылки.\n"
        "Можно отправить: текст, фото, видео или документ.\n\n"
        "🔗 Для URL-кнопки используйте формат:\n"
        "`[Текст кнопки](URL)` в конце текста.",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_for_broadcast_content)
    await call.answer()


async def process_broadcast_content(
    message: Message,
    state: FSMContext,
    bot: Bot
):
    """Отправка рассылки (групповой или одиночной)"""
    data = await state.get_data()
    recipients = data.get("broadcast_recipients", [])
    target = data.get("broadcast_target", "unknown")
    
    if not recipients:
        await message.answer("❌ Нет получателей для рассылки.")
        await state.clear()
        return

    text = message.caption or message.text
    photo_id = message.photo[-1].file_id if message.photo else None
    video_id = message.video.file_id if message.video else None
    document_id = message.document.file_id if message.document else None
    url = None
    url_text = "Перейти"

    # Парсинг URL-кнопки из текста
    if text and text.count('](') == 1 and text.endswith(')'):
        try:
            url_text = text[text.rfind('[')+1:text.rfind(']')]
            url = text[text.rfind('(')+1:text.rfind(')')]
            text = text[:text.rfind('[')].strip()
        except Exception:
            pass

    # ✅ Для одиночной рассылки — упрощённая логика
    if target == "single_entity":
        success = await send_broadcast_message(
            bot, recipients[0], text, photo_id, video_id, document_id, url, url_text
        )
        
        if success:
            await message.answer(f"✅ Сообщение отправлено пользователю!")
        else:
            await message.answer(f"❌ Не удалось отправить сообщение.")
        
        await state.clear()
        return

    # ✅ Для групповой рассылки — полная логика с прогрессом
    await message.answer(f"🚀 Начинаю рассылку...")
    
    success_count = 0
    fail_count = 0
    
    for i, user_id in enumerate(recipients):
        if await send_broadcast_message(
            bot, user_id, text, photo_id, video_id, document_id, url, url_text
        ):
            success_count += 1
        else:
            fail_count += 1
        
        # Небольшая задержка для избежания лимитов
        await asyncio.sleep(0.5)
        
        # Прогресс каждые 10 сообщений
        if (i + 1) % 10 == 0:
            await message.answer(f"📊 Прогресс: {i + 1}/{len(recipients)}")

    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📬 Всего: {len(recipients)}\n"
        f"✅ Успешно: {success_count}\n"
        f"❌ Ошибок: {fail_count}", 
        parse_mode="HTML"
    )
    await state.clear()


async def broadcast_to_entity_handler(
    call: CallbackQuery,
    state: FSMContext,
    config: EntityConfig
):
    """Рассылка конкретному пользователю"""
    entity_id = int(call.data.split(":")[2])
    
    await state.update_data(
        broadcast_recipients=[entity_id],
        broadcast_target="single_entity"
    )
    
    await call.message.edit_text(
        f"📢 Рассылка пользователю\n\n"
        "Отправьте сообщение (текст, фото, видео или документ):\n"
        "Для URL-кнопки: `[Текст](URL)` в конце текста."
    )
    await state.set_state(BroadcastStates.waiting_for_broadcast_content)
    await call.answer()


async def close_callback_handler(call: CallbackQuery):
    """Закрытие карточки"""
    await call.message.delete()
    await call.answer()


# ======= График пользователя ========

async def view_chart_handler(
    call: CallbackQuery,
    config: EntityConfig,
    bot: Bot
):
    """Просмотр графика пользователя с отображением alias"""
    entity_id = int(call.data.split(":")[2])
    owner_id = call.from_user.id
    
    # 1️⃣ Получаем документ владельца для поиска alias
    owner_doc = await users_collection.find_one({"user_id": owner_id})
    if not owner_doc:
        await call.answer("❌ Владелец не найден", show_alert=True)
        return

    # 2️⃣ Ищем сущность в связях владельца и получаем alias
    entity_data = None
    for entity in owner_doc.get(config.connection_field, []):
        if entity.get(config.id_field) == entity_id:
            entity_data = entity
            break
    
    if not entity_data:
        await call.answer("❌ Сущность не найдена в ваших связях", show_alert=True)
        return

    # 3️⃣ Расшифровываем alias
    raw_alias = entity_data.get("alias", "Не указан")
    try:
        alias = decrypt_text(raw_alias)
    except Exception:
        alias = raw_alias

    # 4️⃣ Генерируем график для smart-пользователя
    chart_buf = await generate_blood_pressure_chart(entity_id)
    
    if chart_buf:
        photo = BufferedInputFile(
            chart_buf.getvalue(),
            filename=f"bp_chart_{entity_id}.png"
        )
        
        # ✅ Отправляем график с alias вместо ID
        await bot.send_photo(
            chat_id=call.from_user.id,
            photo=photo,
            caption=f"📊 График пользователя: <b>{alias}</b>\n\n"
                    
                    f"📅 За последние 30 дней",
            parse_mode="HTML",
        )
        
        # ✅ Показываем уведомление, что график отправлен
        await call.answer("📊 График отправлен!", show_alert=False)
    else:
        # ✅ Если нет данных
        await call.answer(
            f"❌ У пользователя <b>{alias}</b> нет данных за последние 30 дней",
            show_alert=True
        )
        

#======= Аналитика пользователя (новая функция) ========
async def view_analytics_handler(
    call: CallbackQuery,
    config: EntityConfig,
    bot: Bot
    ):
    entity_id = int(call.data.split(":")[2])
    owner_id = call.from_user.id
    # 1️⃣ Получаем документ владельца для поиска alias
    owner_doc = await users_collection.find_one({"user_id": owner_id})
    if not owner_doc:
        await call.answer("❌ Владелец не найден", show_alert=True)
        return

    # 2️⃣ Ищем сущность в связях владельца и получаем alias
    entity_data = None
    for entity in owner_doc.get(config.connection_field, []):
        if entity.get(config.id_field) == entity_id:
            entity_data = entity
            break
    
    if not entity_data:
        await call.answer("❌ Сущность не найдена в ваших связях", show_alert=True)
        return
    
    # 3️⃣ Расшифровываем alias
    raw_alias = entity_data.get("alias", "Не указан")
    try:
        alias = decrypt_text(raw_alias)
    except Exception:
        alias = raw_alias
    
    # 4️⃣ Получаем аналитику
    analytics = await generate_smart_user_analytics(entity_id)
    
    if analytics:
        # Отправляем аналитику текстом
        analytics_text = format_analytics_text(analytics, alias)
        await bot.send_message(
            chat_id=call.from_user.id,
            text=analytics_text,
            parse_mode="Markdown"
        )
        await call.answer("📊 Аналитика отправлена!", show_alert=False)
    else:
        await call.answer(
            f"⚠️ У пользователя **{alias}** недостаточно данных для аналитики.\n"
            f"Необходимо минимум 1 измерение за последние 30 дней.",
            show_alert=True
        )