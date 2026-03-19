# utils/bp_target.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from utils.states import PulseTargetState
from mongo import get_bp_target, set_bp_target
from utils.bp_keyboard import bp_target_keyboard, pressure_builder, pulse_keyboard

target_router = Router()


@target_router.callback_query(F.data == "custom_targets")
async def show_bp_targets(call: CallbackQuery):
    user_id = call.from_user.id
    targets = await get_bp_target(user_id)

    if not targets:
        text = "⚠️ Целевые показатели не заданы."
    else:
        text = (
            "🎯 <b>Ваши целевые показатели:</b>\n\n"
            f"🩺 Давление: <b>{targets['systolic']}/{targets['diastolic']}</b> мм рт.ст.\n"
            f"❤️ Пульс: <b>{targets['heart_rate_min']}–{targets['heart_rate_max']}</b> уд/мин"
        )

    await call.message.edit_text(
        text,
        reply_markup=bp_target_keyboard(),
        parse_mode="HTML"
    )


@target_router.callback_query(F.data == "edit_bp_target_pressure")
async def edit_bp_target_pressure(call: CallbackQuery):
    await call.message.edit_text(
        "✏️ <b>Введите целевое давление</b>",
        reply_markup=pressure_builder(),
        parse_mode="HTML"
    )


@target_router.callback_query(F.data.startswith("pressure_add_"))
async def pressure_add(call: CallbackQuery):
    digits = call.data.replace("pressure_add_", "")

    await call.message.edit_reply_markup(
        reply_markup=pressure_builder(digits)
    )
    
    
@target_router.callback_query(F.data.startswith("pressure_del_"))
async def pressure_del(call: CallbackQuery):
    digits = call.data.replace("pressure_del_", "")

    await call.message.edit_reply_markup(
        reply_markup=pressure_builder(digits)
    )
    

@target_router.callback_query(F.data.startswith("pressure_confirm_"))
async def pressure_confirm(call: CallbackQuery):
    digits = call.data.replace("pressure_confirm_", "")

    sad = int(digits[:3])
    dad = int(digits[3:])

    await set_bp_target(
        call.from_user.id,
        {
            "systolic": sad,
            "diastolic": dad,
        }
    )

    await call.answer("✅ Целевое давление сохранено", show_alert=True)
    
    
@target_router.callback_query(F.data == "edit_bp_target_pulse")
async def start_pulse_edit(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(PulseTargetState.min)

    await call.message.edit_text(
        "❤️ Введите <b>минимальный</b> целевой пульс:",
        reply_markup=pulse_keyboard(),
        parse_mode="HTML"
    )
    
    
@target_router.callback_query(F.data.startswith("pulse_add_"))
async def pulse_add(call: CallbackQuery, state: FSMContext):
    digits = call.data.replace("pulse_add_", "")

    await call.message.edit_reply_markup(
        reply_markup=pulse_keyboard(digits)
    )
    
    
@target_router.callback_query(F.data.startswith("pulse_del_"))
async def pulse_del(call: CallbackQuery):
    digits = call.data.replace("pulse_del_", "")

    await call.message.edit_reply_markup(
        reply_markup=pulse_keyboard(digits)
    )
    
    
@target_router.callback_query(F.data.startswith("pulse_confirm_"))
async def pulse_confirm(call: CallbackQuery, state: FSMContext):
    value = int(call.data.replace("pulse_confirm_", ""))
    current_state = await state.get_state()

    if current_state == PulseTargetState.min.state:
        await state.update_data(min=value)
        await state.set_state(PulseTargetState.max)

        await call.message.edit_text(
            "❤️ Введите <b>максимальный</b> целевой пульс:",
            reply_markup=pulse_keyboard(),
            parse_mode="HTML"
        )

    elif current_state == PulseTargetState.max.state:
        data = await state.get_data()
        min_hr = data["min"]

        if value <= min_hr:
            await call.answer(
                "Максимальный пульс должен быть выше минимального",
                show_alert=True
            )
            return

        await set_bp_target(
            call.from_user.id,
            {
                "heart_rate_min": min_hr,
                "heart_rate_max": value,
            }
        )

        await state.clear()
        await call.answer("✅ Целевой пульс сохранён", show_alert=True)

        await show_bp_targets(call)
        
        
@target_router.callback_query(F.data == "cancel_pulse")
async def cancel_pulse(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_bp_targets(call)