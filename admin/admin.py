# admin/admin.py

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton 
from utils.filters.role_filter import RoleFilter
from admin.base_handlers import (
    BaseEntityStates,
    BroadcastStates,
    AdminStates,
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
    close_callback_handler,
)
from admin.entity_config import ENTITY_CONFIGS
from mongo import users_collection

admin_router = Router()
admin_router.message.filter(RoleFilter("admin"))
admin_router.callback_query.filter(RoleFilter("admin"))

# ✅ Админ управляет специалистами (не smart_user!)
CONFIG = ENTITY_CONFIGS["specialist"]
ADMIN_CONFIG = ENTITY_CONFIGS["specialist"]
ADMIN_BROADCAST_TARGETS = [
    "specialists",      # ✅ Только свои connected_specialists
    "debug"             # ✅ Себе
]


@admin_router.message(Command(CONFIG.list_command))  # Команда: /admin
async def list_specialists_handler(message: Message):
    await list_entities_handler(message, CONFIG, "admin", broadcast_callback="start_broadcast_admin")


@admin_router.callback_query(F.data == CONFIG.add_command)  # add_specialist
async def add_specialist_callback_handler(callback: CallbackQuery, state: FSMContext):
    await add_entity_callback_handler(callback, state, CONFIG)


@admin_router.message(F.contact, AdminStates.waiting_for_contact)
async def process_specialist_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("entity_role") == "specialist":  # ✅ Проверяем роль
        await process_entity_contact(message, state, CONFIG)
    else:
        await message.answer(f"{data.get("entity_role")}\n❌ Ошибка: неверный тип сущности. Начните заново.")
        await state.clear()

@admin_router.callback_query(F.data.startswith(f"confirm_{CONFIG.role}:"))
async def confirm_specialist(call: CallbackQuery, state: FSMContext):
    await confirm_entity_role(call, state, CONFIG)


@admin_router.callback_query(F.data.startswith(f"set_{CONFIG.role}_alias:"))
async def start_specialist_alias_input(call: CallbackQuery, state: FSMContext):
    await start_alias_input(call, state, CONFIG)


@admin_router.message(AdminStates.waiting_for_alias)
async def process_specialist_alias(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("entity_role") == "specialist":
        await process_entity_alias(message, state, CONFIG)


@admin_router.callback_query(F.data.startswith(f"page_{CONFIG.role}:"))
async def paginate_specialists_handler(call: CallbackQuery):
    await paginate_entities_handler(call, CONFIG)


@admin_router.callback_query(F.data.startswith(f"{CONFIG.role}:"))
async def show_specialist_card(call: CallbackQuery):
    await show_entity_card(
        call,
        CONFIG,
        show_broadcast=True,   # ✅ Админ может рассылать специалисту
        show_chart=False,      # ❌ График специалиста обычно не нужен
        show_close=True
    )


@admin_router.callback_query(F.data.startswith(f"edit_{CONFIG.role}:"))
async def start_edit_specialist_alias(call: CallbackQuery, state: FSMContext):
    await start_edit_entity_alias(call, state, CONFIG)


@admin_router.message(AdminStates.editing_entity_alias)
async def process_edit_specialist_alias(message: Message, state: FSMContext):
    """Обработчик редактирования для Специалистов"""
    data = await state.get_data()
    
    if data.get("entity_type") == CONFIG.role:  # ✅ "specialist"
        await process_edit_entity_alias_base(message, state, CONFIG)
    else:
        await message.answer("❌ Ошибка редактирования. Попробуйте снова.")
        await state.clear()


@admin_router.callback_query(F.data.startswith(f"delete_{CONFIG.role}:"))
async def delete_specialist_handler(call: CallbackQuery):
    await delete_entity_handler(call, CONFIG)


# --- РАССЫЛКА ---
@admin_router.callback_query(F.data == "start_broadcast_admin")
async def admin_start_broadcast_handler(call: CallbackQuery, state: FSMContext):
    await start_broadcast_handler(call, state, ADMIN_CONFIG, ADMIN_BROADCAST_TARGETS)


@admin_router.callback_query(F.data.startswith("broadcast_to:"), BroadcastStates.waiting_for_broadcast_recipients)
async def admin_get_broadcast_recipients(call: CallbackQuery, state: FSMContext):
    await get_broadcast_recipients(call, state, ADMIN_CONFIG)


@admin_router.message(BroadcastStates.waiting_for_broadcast_content)
async def admin_process_broadcast_content(message: Message, state: FSMContext, bot: Bot):
    await process_broadcast_content(message, state, bot)


# ✅ Рассылка конкретному специалисту
@admin_router.callback_query(F.data.startswith("broadcast_to_entity:"))
async def broadcast_to_specialist_handler(call: CallbackQuery, state: FSMContext):
    await broadcast_to_entity_handler(call, state, CONFIG)
    
    
# ✅ Просмотр графика специалиста (если нужно)
@admin_router.callback_query(F.data.startswith("view_chart:"))
async def view_specialist_chart(call: CallbackQuery, bot: Bot):
    await view_chart_handler(call, CONFIG, bot)


# ✅ Закрытие карточки
@admin_router.callback_query(F.data == "close_callback")
async def close_specialist_card(call: CallbackQuery):
    await close_callback_handler(call)
