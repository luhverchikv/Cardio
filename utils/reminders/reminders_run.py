# utils/reminders/reminders_run.py

from aiogram import Bot
from aiogram.types import BufferedInputFile
import datetime
from loguru import logger
from config import config
from mongo import get_users_count, users_collection
from utils.encryption import decrypt_text
from logic.report.blood_pressure_chart import generate_blood_pressure_chart


async def send_monthly_charts_to_specialists(bot: Bot):
    """
    Ежемесячная рассылка графиков Smart-пользователей специалистам.
    Запускается 1-го числа каждого месяца в 10:00.
    """
    try:
        today = datetime.datetime.now().strftime("%d.%m.%Y")
        
        # 1️⃣ Получаем всех специалистов из базы
        cursor = users_collection.find(
            {"roles": "specialist"},
            {"user_id": 1, "connected_smart_users": 1}
        )
        specialists = await cursor.to_list(length=None)
        if not specialists:
            logger.info("❌ Нет специалистов для рассылки")
            return
        
        total_charts_sent = 0
        total_specialists_received = 0
        
        # 2️⃣ Проходим по каждому специалисту
        for specialist_doc in specialists:
            specialist_id = specialist_doc.get("user_id")
            smart_users = specialist_doc.get("connected_smart_users", [])
            
            if not smart_users:
                logger.info(f"⚠️ Специалист {specialist_id} не имеет Smart-пользователей")
                continue
            
            try:
                # 3️⃣ Отправляем приветственное сообщение специалисту
                await bot.send_message(
                    chat_id=specialist_id,
                    text=(
                        f"📊 <b>Ежемесячный отчёт</b>\n\n"
                        f"📅 Дата: {today}\n"
                        f"👥 Smart-пользователей: {len(smart_users)}\n\n"
                        f"Ниже будут отправлены графики за последние 30 дней."
                    ),
                    parse_mode="HTML"
                )
                
                charts_sent_for_specialist = 0
                
                # 4️⃣ Проходим по каждому Smart-пользователю
                for smart_user in smart_users:
                    smart_user_id = smart_user.get("smart_user_id")
                    raw_alias = smart_user.get("alias", "")
                    
                    # Расшифровываем alias
                    try:
                        alias = decrypt_text(raw_alias) if raw_alias else "Без имени"
                    except Exception:
                        alias = "Без имени"
                    
                    # 5️⃣ Генерируем график
                    chart_buf = await generate_blood_pressure_chart(smart_user_id)
                    
                    if chart_buf:
                        photo = BufferedInputFile(
                            chart_buf.getvalue(),
                            filename=f"bp_chart_{smart_user_id}.png"
                        )
                        
                        # 6️⃣ Отправляем график специалисту
                        await bot.send_photo(
                            chat_id=specialist_id,
                            photo=photo,
                            caption=(
                                f"📊 <b>График: {alias}</b>\n\n"
                                f"🆔 ID: <code>{smart_user_id}</code>\n"
                                f"📅 За последние 30 дней"
                            ),
                            parse_mode="HTML"
                        )
                        
                        charts_sent_for_specialist += 1
                        total_charts_sent += 1
                        
                        # Небольшая задержка для избежания лимитов
                        import asyncio
                        await asyncio.sleep(0.5)
                    else:
                        logger.info(f"⚠️ Нет данных для Smart-пользователя {smart_user_id}")
                
                if charts_sent_for_specialist > 0:
                    total_specialists_received += 1
                    
                
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке специалисту {specialist_id}: {e}")
                continue
        
        
    except Exception:
        logger.exception("❌ Критическая ошибка в send_monthly_charts_to_specialists")






async def send_admin_stats(bot: Bot):
    """
    Отправляет администраторам ежедневную статистику
    """
    try:
        count_users = await get_users_count()
        today = datetime.datetime.now().strftime("%d.%m.%Y")

        text = (
            f"📅 Сегодня: {today}\n"
            f"👥 Всего пользователей: {count_users}"
        )

        # если один владелец
        await bot.send_message(config.bot.owner_id, text)

        # если администраторов несколько — на будущее
        # for admin_id in config.admins:
        #     await bot.send_message(admin_id, text)

    except Exception:
        logger.exception("Ошибка при отправке admin stats")