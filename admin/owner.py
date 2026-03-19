# admin/owner.py

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.reminders.reminders_run import send_monthly_charts_to_specialists
from utils.filters.role_filter import RoleFilter
from utils.analytics.daily_report import send_daily_report
from admin.base_handlers import (
    BaseEntityStates,
    BroadcastStates,
    OwnerStates,
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

owner_router = Router()
owner_router.message.filter(RoleFilter("owner"))
owner_router.callback_query.filter(RoleFilter("owner"))

# ✅ Владелец управляет администраторами
CONFIG = ENTITY_CONFIGS["admin"]
OWNER_CONFIG = ENTITY_CONFIGS["admin"]
OWNER_BROADCAST_TARGETS = [
    "admins",           # ✅ Свои админы
    "all_specialists",  # ✅ ВСЕ специалисты в базе
    "all_smart_users",  # ✅ ВСЕ smart-пользователи в базе
    "users",            # ✅ ВСЕ пользователи в базе
    "debug"             # ✅ Себе
]

@owner_router.message(Command(CONFIG.list_command))  # Команда: /owner
async def list_admins_handler(message: Message):
    await list_entities_handler(message, CONFIG, "owner", broadcast_callback="start_broadcast_owner")


@owner_router.callback_query(F.data == CONFIG.add_command)  # add_admin
async def add_admin_callback_handler(callback: CallbackQuery, state: FSMContext):
    await add_entity_callback_handler(callback, state, CONFIG)


@owner_router.message(F.contact, OwnerStates.waiting_for_contact)
async def process_admin_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("entity_role") == "admin":  # ✅ Проверяем роль
        await process_entity_contact(message, state, CONFIG)
    else:
        #await message.answer(f"{data.get("entity_role")}\n❌ Ошибка: неверный тип сущности (admin). Начните заново.")
        await state.clear()

@owner_router.callback_query(F.data.startswith(f"confirm_{CONFIG.role}:"))
async def confirm_admin(call: CallbackQuery, state: FSMContext):
    await confirm_entity_role(call, state, CONFIG)


@owner_router.callback_query(F.data.startswith(f"set_{CONFIG.role}_alias:"))
async def start_admin_alias_input(call: CallbackQuery, state: FSMContext):
    await start_alias_input(call, state, CONFIG)


@owner_router.message(OwnerStates.waiting_for_alias)
async def process_admin_alias(message: Message, state: FSMContext):
    data = await state.get_data()
    if data.get("entity_role") == "admin":
        await process_entity_alias(message, state, CONFIG)


@owner_router.callback_query(F.data.startswith(f"page_{CONFIG.role}:"))
async def paginate_admins_handler(call: CallbackQuery):
    await paginate_entities_handler(call, CONFIG)


@owner_router.callback_query(F.data.startswith(f"{CONFIG.role}:"))
async def show_admin_card(call: CallbackQuery):
    await show_entity_card(
        call,
        CONFIG,
        show_broadcast=True,  # ❌ Обычно владелец не рассылает админам индивидуально
        show_chart=False,      # ❌ График админа не нужен
        show_close=True
    )


@owner_router.callback_query(F.data.startswith(f"edit_{CONFIG.role}:"))
async def start_edit_admin_alias(call: CallbackQuery, state: FSMContext):
    await start_edit_entity_alias(call, state, CONFIG)


@owner_router.message(OwnerStates.editing_entity_alias)
async def process_edit_admin_alias(message: Message, state: FSMContext):
    """Обработчик редактирования для Администраторов"""
    data = await state.get_data()
    
    if data.get("entity_type") == CONFIG.role:  # ✅ "admin"
        await process_edit_entity_alias_base(message, state, CONFIG)
    else:
        await message.answer("❌ Ошибка редактирования. Попробуйте снова.")
        await state.clear()


@owner_router.callback_query(F.data.startswith(f"delete_{CONFIG.role}:"))
async def delete_admin_handler(call: CallbackQuery):
    await delete_entity_handler(call, CONFIG)


# --- РАССЫЛКА (Владелец имеет доступ ко всем группам) ---
@owner_router.callback_query(F.data == "start_broadcast_owner")
async def owner_start_broadcast_handler(call: CallbackQuery, state: FSMContext):
    await start_broadcast_handler(call, state, OWNER_CONFIG, OWNER_BROADCAST_TARGETS)

@owner_router.callback_query(F.data.startswith("broadcast_to:"), BroadcastStates.waiting_for_broadcast_recipients)
async def owner_get_broadcast_recipients(call: CallbackQuery, state: FSMContext):
    await get_broadcast_recipients(call, state, OWNER_CONFIG)


@owner_router.message(BroadcastStates.waiting_for_broadcast_content)
async def owner_process_broadcast_content(message: Message, state: FSMContext, bot: Bot):
    await process_broadcast_content(message, state, bot)


# ✅ Рассылка конкретному администратору
@owner_router.callback_query(F.data.startswith("broadcast_to_entity:"))
async def broadcast_to_admin_handler(call: CallbackQuery, state: FSMContext):
    await broadcast_to_entity_handler(call, state, CONFIG)
    
    
# ✅ Просмотр графика администратора (если нужно)
@owner_router.callback_query(F.data.startswith("view_chart:"))
async def view_admin_chart(call: CallbackQuery, bot: Bot):
    await view_chart_handler(call, CONFIG, bot)


# ✅ Закрытие карточки
@owner_router.callback_query(F.data == "close_callback")
async def close_admin_card(call: CallbackQuery):
    await close_callback_handler(call)
    

@owner_router.message(Command("test_monthly_charts"))
async def test_monthly_charts_handler(message: Message, bot: Bot):
    """Тестовый запуск ежемесячной рассылки (только для владельца)"""
    
    await message.answer("🚀 Запускаю тестовую рассылку графиков...")
    await send_monthly_charts_to_specialists(bot)
    await message.answer("✅ Тестовая рассылка завершена!")


@owner_router.message(Command("daily_report"))
async def test_daily_report_handler(message: Message, bot: Bot):
    """Тестовый запуск ежедневного отчёта (только для владельца)"""
    await message.answer("🚀 Генерирую ежедневный отчёт...")
    await send_daily_report(bot, message.from_user.id)