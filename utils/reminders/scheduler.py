# utils/reminders/scheduler.py
import zoneinfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from utils.analytics.history_db import calculate_weekly_aggregates, calculate_monthly_aggregates
from utils.analytics.daily_report import send_daily_report
from utils.reminders.reminders_run import send_admin_stats, send_monthly_charts_to_specialists
from utils.reminders.bp_reminders import run_bp_reminders
from config import config


def setup_scheduler(bot):
    minsk_tz = zoneinfo.ZoneInfo("Europe/Minsk")

    scheduler = AsyncIOScheduler(timezone=minsk_tz)
    
    # 📊 ЕЖЕДНЕВНЫЙ отчёт владельцу (6:00) ← Изменили время!
    scheduler.add_job(
        send_daily_report,
        CronTrigger(hour=6, minute=0),  # ✅ 6 утра
        args=[bot, config.bot.owner_id],
        id="daily_report",
        replace_existing=True
    )
    
    # 📈 ЕЖЕНЕДЕЛЬНЫЕ агрегаты (понедельник 7:00)
    scheduler.add_job(
        calculate_weekly_aggregates,
        CronTrigger(day_of_week="mon", hour=7, minute=0),
        id="weekly_aggregates",
        replace_existing=True
    )
    
    # 📅 ЕЖЕМЕСЯЧНЫЕ агрегаты (1-е число 7:00)
    scheduler.add_job(
        calculate_monthly_aggregates,
        CronTrigger(day=1, hour=7, minute=0),
        id="monthly_aggregates",
        replace_existing=True
    )
    
    # 🕢 Ежедневная рассылка статистики администраторам в 7:30
    scheduler.add_job(
        send_admin_stats,
        CronTrigger(hour=7, minute=30),
        args=[bot],
        id="admin_stats",
        replace_existing=True
    )
    
    # 📊 ЕЖЕМЕСЯЧНАЯ рассылка графиков специалистам (1-е число в 10:00)
    scheduler.add_job(
        send_monthly_charts_to_specialists,
        CronTrigger(day=1, hour=10, minute=0),  # ✅ 1-е число каждого месяца в 10:00
        args=[bot],
        id="monthly_charts_specialists",
        replace_existing=True
    )
    
    # 🌅 Утреннее напоминание (09:00)
    scheduler.add_job(
        run_bp_reminders,
        CronTrigger(hour=9, minute=0),
        args=[bot, 1, 3],
        id="bp_reminders_morning",
        replace_existing=True
    )

    # 🌙 Вечернее напоминание (21:00)
    scheduler.add_job(
        run_bp_reminders,
        CronTrigger(hour=21, minute=0),
        args=[bot, 2, 3],
        id="bp_reminders_evening",
        replace_existing=True
    )
    
    scheduler.start()

    return scheduler