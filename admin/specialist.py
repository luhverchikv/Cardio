# admin/specialist.py

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.filters.role_filter import RoleFilter
from admin.base_handlers import (
    BaseEntityStates,
    BroadcastStates,
    SpecialistStates,
    list_entities_handler,
    add_entity_callback_handler,
    process_entity_contact,
    confirm_entity_role,
    start_alias_input,
    process_entity_alias,
    paginate_entities_handler,
    show_entity_card,
    start_edit_entity_alias,
    process_edit_entity_alias as process_edit_entity_alias_base,
    delete_entity_handler,
    start_broadcast_handler,
    get_broadcast_recipients,
    process_broadcast_content,
    broadcast_to_entity_handler,
    view_chart_handler,
    view_analytics_handler,
    close_callback_handler,
)
from admin.entity_config import ENTITY_CONFIGS
from mongo import users_collection


specialist_router = Router()
specialist_router.message.filter(RoleFilter("specialist"))
specialist_router.callback_query.filter(RoleFilter("specialist"))

# Получаем конфигурацию для специалиста
CONFIG = ENTITY_CONFIGS["smart_user"]
SPECIALIST_CONFIG = ENTITY_CONFIGS["smart_user"]
SPECIALIST_BROADCAST_TARGETS = [
    "smart_users",      # ✅ Только свои connected_smart_users
    "debug"             # ✅ Себе
]


@specialist_router.message(Command(CONFIG.list_command))
async def list_specialists_handler(message: Message):
    await list_entities_handler(message, CONFIG, "specialist", broadcast_callback="start_broadcast_specialist")


@specialist_router.callback_query(F.data == CONFIG.add_command)
async def add_specialist_callback_handler(callback: CallbackQuery, state: FSMContext):
    await add_entity_callback_handler(callback, state, CONFIG)


@specialist_router.message(F.contact, SpecialistStates.waiting_for_contact)
async def process_specialist_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("entity_role") == "smart_user":
        await process_entity_contact(message, state, CONFIG)


@specialist_router.callback_query(F.data.startswith(f"confirm_{CONFIG.role}:"))
async def confirm_specialist(call: CallbackQuery, state: FSMContext):
    await confirm_entity_role(call, state, CONFIG)


@specialist_router.callback_query(F.data.startswith(f"set_{CONFIG.role}_alias:"))
async def start_specialist_alias_input(call: CallbackQuery, state: FSMContext):
    await start_alias_input(call, state, CONFIG)


@specialist_router.message(SpecialistStates.waiting_for_alias)
async def process_specialist_alias(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("entity_role") == "smart_user":
        await process_entity_alias(message, state, CONFIG)


@specialist_router.callback_query(F.data.startswith(f"page_{CONFIG.role}:"))
async def paginate_specialists_handler(call: CallbackQuery):
    await paginate_entities_handler(call, CONFIG)


@specialist_router.callback_query(F.data.startswith(f"{CONFIG.role}:"))
async def show_smart_user_card(call: CallbackQuery):
    await show_entity_card(
        call,
        CONFIG,
        show_broadcast=True,  # ✅ Специалист может рассылать smart-пользователю
        show_chart=True,      # ✅ Может смотреть график
        show_close=True       # ✅ Может закрыть
    )


@specialist_router.callback_query(F.data.startswith(f"edit_{CONFIG.role}:"))
async def start_edit_specialist_alias(call: CallbackQuery, state: FSMContext):
    await start_edit_entity_alias(call, state, CONFIG)


@specialist_router.message(SpecialistStates.editing_entity_alias)
async def process_edit_smart_user_alias(message: Message, state: FSMContext):  # ✅ Уникальное имя!
    """Обработчик редактирования для Smart-пользователей"""
    data = await state.get_data()
    
    if data.get("entity_type") == CONFIG.role:  # ✅ "smart_user"
        await process_edit_entity_alias_base(message, state, CONFIG)  # ✅ Вызываем импорт!
    else:
        await message.answer("❌ Ошибка редактирования. Попробуйте снова.")
        await state.clear()


@specialist_router.callback_query(F.data.startswith(f"delete_{CONFIG.role}:"))
async def delete_specialist_handler(call: CallbackQuery):
    await delete_entity_handler(call, CONFIG)


# --- РАССЫЛКА (остаётся уникальной) ---
@specialist_router.callback_query(F.data == "start_broadcast_specialist")
async def specialist_start_broadcast_handler(call: CallbackQuery, state: FSMContext):
    await start_broadcast_handler(call, state, SPECIALIST_CONFIG, SPECIALIST_BROADCAST_TARGETS)


@specialist_router.callback_query(F.data.startswith("broadcast_to:"), BroadcastStates.waiting_for_broadcast_recipients)
async def specialist_get_broadcast_recipients(call: CallbackQuery, state: FSMContext):
    await get_broadcast_recipients(call, state, SPECIALIST_CONFIG)


@specialist_router.message(BroadcastStates.waiting_for_broadcast_content)
async def specialist_process_broadcast_content(message: Message, state: FSMContext, bot: Bot):
    await process_broadcast_content(message, state, bot)


# ✅ Рассылка конкретному smart-пользователю
@specialist_router.callback_query(F.data.startswith("broadcast_to_entity:"))
async def broadcast_to_smart_user_handler(call: CallbackQuery, state: FSMContext):
    await broadcast_to_entity_handler(call, state, CONFIG)
    
    
# ✅ Просмотр графика smart-пользователя
@specialist_router.callback_query(F.data.startswith("view_chart:"))
async def view_smart_user_chart(call: CallbackQuery, bot: Bot):
    await view_chart_handler(call, CONFIG, bot)
    await view_analytics_handler(call, CONFIG, bot)