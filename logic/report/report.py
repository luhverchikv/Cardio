# logic/report/report.py
from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from logic.report.blood_pressure_chart import generate_blood_pressure_chart
from logic.analytics.report_builder import build_bp_report
from logic.analytics.formatter import format_bp_report
from mongo import get_bp_entries_last_days
import asyncio
from menu.keyboard import menu_kb
from aiogram.filters import Command


report_router = Router()


def report_details_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Подробнее", callback_data="report_details")
    return kb.as_markup()


@report_router.message(Command("report"))
@report_router.message(F.text.startswith('📋'))
async def start_report(message: Message, bot: Bot):
    user_id = message.from_user.id

    # 1️⃣ Получаем данные
    entries, targets = await get_bp_entries_last_days(user_id)

    if not entries:
        await message.answer("❗️Данных за последние 30 дней не найдено. Добавьте хотя бы одно измерение артериального давления.")
        return

    # 2️⃣ Строим аналитику
    #pressure, adherence, flags, circadian, dipping_status = build_bp_report(entries, targets)

    #report_text = format_bp_report(
    #pressure=pressure,
    #adherence=adherence,
    #flags=flags,
    #circadian=circadian,
    #dipping_status=dipping_status
#)

    # 3️⃣ Генерируем график
    chart_buf = await generate_blood_pressure_chart(user_id)

    if chart_buf:
        photo = BufferedInputFile(
            chart_buf.getvalue(),
            filename="blood_pressure_chart.png"
        )
        chat_id = message.chat.id

        await bot.send_photo(
            photo=photo,
            chat_id=chat_id,
            caption="📈 График артериального давления за последние 30 дней"
            #reply_markup=menu_kb()
        )
    else:
        await message.answer("❗️Данных за последние 30 дней не найдено. Добавьте хотя бы одно измерение артериального давления.")
    await message.delete()