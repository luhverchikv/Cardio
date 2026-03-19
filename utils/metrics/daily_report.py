# utils/metrics/daily_report.py

from mongo import users_collection
from datetime import datetime, timedelta
from loguru import logger
from typing import Dict, List, Tuple
import asyncio
from utils.metrics.history_db import save_daily_snapshot, init_db


async def get_all_active_users() -> Dict[int, int]:
    """
    Получает DAU, WAU, MAU за ОДИН запрос.
    Возвращает словарь: {days: count}
    """
    try:
        now = datetime.utcnow()
        thresholds = {
            1: now - timedelta(days=1),
            7: now - timedelta(days=7),
            30: now - timedelta(days=30)
        }
        
        pipeline = [
            {"$unwind": "$blood_pressure_entries"},
            {"$group": {
                "_id": "$user_id",
                "last_entry": {"$max": "$blood_pressure_entries.timestamp"}
            }},
            {"$project": {
                "_id": 0,
                "user_id": "$_id",
                "last_entry": 1,
                "is_dau": {"$cond": [{"$gte": ["$last_entry", thresholds[1]]}, 1, 0]},
                "is_wau": {"$cond": [{"$gte": ["$last_entry", thresholds[7]]}, 1, 0]},
                "is_mau": {"$cond": [{"$gte": ["$last_entry", thresholds[30]]}, 1, 0]}
            }},
            {"$group": {
                "_id": None,
                "dau": {"$sum": "$is_dau"},
                "wau": {"$sum": "$is_wau"},
                "mau": {"$sum": "$is_mau"}
            }}
        ]
        
        result = await users_collection.aggregate(pipeline).to_list(length=1)
        
        if result:
            return {
                1: result[0]["dau"],
                7: result[0]["wau"],
                30: result[0]["mau"]
            }
        
        return {1: 0, 7: 0, 30: 0}
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_error").error(f"get_all_active_users: {e}")
        return {1: 0, 7: 0, 30: 0}


async def get_user_counts() -> Dict:
    """
    Получает total_users и new_users за ОДИН запрос.
    """
    try:
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        pipeline = [
            {"$facet": {
                "total": [{"$count": "count"}],
                "new": [
                    {"$match": {"registered_at": {"$gte": yesterday}}},
                    {"$count": "count"}
                ]
            }}
        ]
        
        result = await users_collection.aggregate(pipeline).to_list(length=1)
        
        if result:
            return {
                "total": result[0]["total"][0]["count"] if result[0]["total"] else 0,
                "new": result[0]["new"][0]["count"] if result[0]["new"] else 0
            }
        
        return {"total": 0, "new": 0}
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_error").error(f"get_user_counts: {e}")
        return {"total": 0, "new": 0}


async def get_churn_stats() -> Dict:
    """
    Получает churned_users и churn_rate за ОДИН запрос.
    """
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        pipeline = [
            {"$match": {"registered_at": {"$lt": thirty_days_ago}}},
            {"$addFields": {
                "last_entry": {"$arrayElemAt": ["$blood_pressure_entries", -1]}
            }},
            {"$facet": {
                "cohort": [{"$count": "count"}],
                "churned": [
                    {"$match": {
                        "$or": [
                            {"blood_pressure_entries": {"$size": 0}},
                            {"blood_pressure_entries": {"$exists": False}},
                            {"last_entry.timestamp": {"$lt": thirty_days_ago}},
                            {"last_entry": None}
                        ]
                    }},
                    {"$count": "count"}
                ]
            }}
        ]
        
        result = await users_collection.aggregate(pipeline).to_list(length=1)
        
        if result:
            cohort_count = result[0]["cohort"][0]["count"] if result[0]["cohort"] else 0
            churned_count = result[0]["churned"][0]["count"] if result[0]["churned"] else 0
            
            churn_rate = (churned_count / cohort_count * 100) if cohort_count > 0 else 0.0
            
            return {
                "churned": churned_count,
                "churn_rate": churn_rate,
                "cohort": cohort_count
            }
        
        return {"churned": 0, "churn_rate": 0.0, "cohort": 0}
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_error").error(f"get_churn_stats: {e}")
        return {"churned": 0, "churn_rate": 0.0, "cohort": 0}


async def get_bp_entries_yesterday() -> int:
    """Количество записей давления за вчера"""
    try:
        now = datetime.utcnow()
        yesterday_start = now - timedelta(days=1)
        yesterday_end = now
        
        pipeline = [
            {"$unwind": "$blood_pressure_entries"},
            {"$match": {
                "blood_pressure_entries.timestamp": {
                    "$gte": yesterday_start,
                    "$lt": yesterday_end
                }
            }},
            {"$count": "count"}
        ]
        
        result = await users_collection.aggregate(pipeline).to_list(length=1)
        return result[0]["count"] if result else 0
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_error").error(f"get_bp_entries_yesterday: {e}")
        return 0


async def get_retention_rate() -> float:
    """Retention Rate на 7 день"""
    try:
        now = datetime.utcnow()
        registration_date = now - timedelta(days=7)
        registration_date_end = registration_date + timedelta(days=1)
        today_start = now - timedelta(days=1)
        
        pipeline = [
            {"$match": {
                "registered_at": {
                    "$gte": registration_date,
                    "$lt": registration_date_end
                }
            }},
            {"$lookup": {
                "from": "users",
                "let": {"user_id": "$user_id"},
                "pipeline": [
                    {"$match": {
                        "$expr": {"$eq": ["$user_id", "$$user_id"]},
                        "blood_pressure_entries.timestamp": {"$gte": today_start}
                    }},
                    {"$limit": 1}
                ],
                "as": "active"
            }},
            {"$facet": {
                "cohort": [{"$count": "count"}],
                "active": [
                    {"$match": {"active": {"$gt": []}}},
                    {"$count": "count"}
                ]
            }}
        ]
        
        # Упрощённая версия (быстрее)
        cohort_pipeline = [
            {"$match": {
                "registered_at": {
                    "$gte": registration_date,
                    "$lt": registration_date_end
                }
            }},
            {"$count": "count"}
        ]
        
        active_pipeline = [
            {"$match": {
                "registered_at": {
                    "$gte": registration_date,
                    "$lt": registration_date_end
                }
            }},
            {"$unwind": "$blood_pressure_entries"},
            {"$match": {"blood_pressure_entries.timestamp": {"$gte": today_start}}},
            {"$group": {"_id": "$user_id"}},
            {"$count": "count"}
        ]
        
        cohort_result, active_result = await asyncio.gather(
            users_collection.aggregate(cohort_pipeline).to_list(length=1),
            users_collection.aggregate(active_pipeline).to_list(length=1)
        )
        
        cohort_count = cohort_result[0]["count"] if cohort_result else 0
        active_count = active_result[0]["count"] if active_result else 0
        
        return (active_count / cohort_count * 100) if cohort_count > 0 else 0.0
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_error").error(f"get_retention_rate: {e}")
        return 0.0


async def get_hierarchy_stats() -> Dict:
    """Статистика иерархии пользователей"""
    try:
        pipeline = [
            {"$match": {"roles": {"$exists": True, "$type": "array"}}},
            {"$group": {
                "_id": None,
                "total_admins": {"$sum": {"$cond": [{"$in": ["admin", "$roles"]}, 1, 0]}},
                "total_specialists": {"$sum": {"$cond": [{"$in": ["specialist", "$roles"]}, 1, 0]}},
                "total_smart_users": {"$sum": {"$cond": [{"$in": ["smart_user", "$roles"]}, 1, 0]}}
            }}
        ]
        
        result = await users_collection.aggregate(pipeline).to_list(length=1)
        return result[0] if result else {
            "total_admins": 0,
            "total_specialists": 0,
            "total_smart_users": 0
        }
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_error").error(f"get_hierarchy_stats: {e}")
        return {
            "total_admins": 0,
            "total_specialists": 0,
            "total_smart_users": 0
        }


async def generate_daily_report() -> Dict:
    """
    Генерирует полный ежедневный отчёт.
    ОПТИМИЗИРОВАНО: запросы выполняются параллельно.
    """
    try:
        logger.bind(user_id="system", event_type="analytics_start").info("🚀 Начало генерации отчёта...")
        start_time = datetime.utcnow()
        
        # 🚀 ГРУППА 1: Базовые метрики (выполняются параллельно)
        user_counts, active_users = await asyncio.gather(
            get_user_counts(),
            get_all_active_users()
        )
        
        # 🚀 ГРУППА 2: Отток и удержание (выполняются параллельно)
        churn_stats, retention = await asyncio.gather(
            get_churn_stats(),
            get_retention_rate()
        )
        
        # 🚀 ГРУППА 3: Остальные метрики (выполняются параллельно)
        bp_entries, hierarchy = await asyncio.gather(
            get_bp_entries_yesterday(),
            get_hierarchy_stats()
        )
        
        # 📊 Сборка отчёта
        total = user_counts["total"]
        new = user_counts["new"]
        dau = active_users[1]
        wau = active_users[7]
        mau = active_users[30]
        churned = churn_stats["churned"]
        churn_rate = churn_stats["churn_rate"]
        bp_entries_yesterday = bp_entries
        bp_per_active = bp_entries_yesterday / dau if dau > 0 else 0
        
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        
        logger.bind(user_id="system", event_type="analytics_complete").info(
            f"✅ Генерация отчёта завершена за {elapsed:.2f}с"
        )
        
        return {
            "total": total,
            "new": new,
            "dau": dau,
            "wau": wau,
            "mau": mau,
            "churned": churned,
            "churn_rate": churn_rate,
            "retention_rate": retention,
            "bp_entries_yesterday": bp_entries_yesterday,
            "bp_per_active": bp_per_active,
            "hierarchy": hierarchy,
            "success": True,
            "elapsed_seconds": elapsed
        }
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_error").exception(
            f"❌ Критическая ошибка в generate_daily_report: {e}"
        )
        return {"success": False, "error": str(e)}


async def send_daily_report(bot, owner_id: int):
    """Отправляет ежедневный отчёт владельцу."""
    try:
        # ✅ Инициализируем БД при первом запуске
        init_db()
        logger.bind(user_id=owner_id, event_type="report_send").info(f"📩 Отправка отчёта пользователю {owner_id}")
        
        report = await generate_daily_report()
        
        if not report.get("success"):
            logger.bind(user_id=owner_id, event_type="report_error").error(
                f"Отчёт не сгенерирован: {report.get('error')}"
            )
            await bot.send_message(
                owner_id,
                f"❌ Ошибка генерации отчёта: {report.get('error')}"
            )
            return
        # ✅ Сохраняем снимок в SQLite
        await save_daily_snapshot(report)
        
        today = datetime.now().strftime("%d.%m.%Y")
        
        # ✅ Извлекаем все данные из отчёта
        total = report["total"]
        new = report["new"]
        dau = report["dau"]
        wau = report["wau"]
        mau = report["mau"]
        churned = report["churned"]          # ✅ ДОБАВЛЕНО!
        churn_rate = report["churn_rate"]
        retention_rate = report["retention_rate"]
        bp_entries = report["bp_entries_yesterday"]
        bp_per_active = report["bp_per_active"]
        hierarchy = report["hierarchy"]
        elapsed = report.get("elapsed_seconds", 0)
        
        dau_percent = (dau / total * 100) if total > 0 else 0
        wau_percent = (wau / total * 100) if total > 0 else 0
        mau_percent = (mau / total * 100) if total > 0 else 0
        
        text = (
            f"📊 <b>Ежедневный отчёт</b>\n"
            f"📅 {today}\n"
            f"⏱️ Время генерации: {elapsed:.2f}с\n\n"
            
            f"<b>👥 Пользователи:</b>\n"
            f"Всего: {total}\n"
            f"➕ Новые: {new}\n\n"
            
            f"<b>📈 Активность:</b>\n"
            f"DAU: {dau} ({dau_percent:.1f}%)\n"
            f"WAU: {wau} ({wau_percent:.1f}%)\n"
            f"MAU: {mau} ({mau_percent:.1f}%)\n\n"
            
            f"<b>📉 Метрики оттока:</b>\n"
            f"Churn Rate: {churn_rate:.2f}%\n"
            f"В оттоке: {churned}\n"              # ✅ Теперь переменная определена
            f"Retention Rate (7 дней): {retention_rate:.2f}%\n\n"
            
            f"<b>📝 Записи давления:</b>\n"
            f"За вчера: {bp_entries}\n"
            f"На активного пользователя: {bp_per_active:.2f}\n\n"
            
            f"<b>🏗️ Иерархия:</b>\n"
            f"👥 Админы: {hierarchy.get('total_admins', 0)}\n"
            f"👨‍⚕️ Специалисты: {hierarchy.get('total_specialists', 0)}\n"
            f"📱 Smart-пользователи: {hierarchy.get('total_smart_users', 0)}"
        )
        
        await bot.send_message(owner_id, text, parse_mode="HTML")
        logger.bind(user_id=owner_id, event_type="report_success").info(f"✅ Отчёт успешно отправлен")
        
    except Exception as e:
        logger.bind(user_id=owner_id, event_type="report_error").exception(
            f"❌ Ошибка в send_daily_report: {e}"
        )
        await bot.send_message(owner_id, f"❌ Ошибка отправки отчёта: {e}")