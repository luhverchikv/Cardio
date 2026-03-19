# utils/metrics/history_db.py

import sqlite3
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger
from typing import Dict, List, Optional

# Путь к базе данных
DB_PATH = Path("utils/metrics/history_db.db")


def init_db():
    """Инициализирует базу данных и создаёт таблицы"""
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # 📊 Таблица ежедневных снимков метрик
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE NOT NULL,
                
                -- Пользователи
                total_users INTEGER DEFAULT 0,
                new_users INTEGER DEFAULT 0,
                
                -- Активность
                dau INTEGER DEFAULT 0,
                wau INTEGER DEFAULT 0,
                mau INTEGER DEFAULT 0,
                dau_percent REAL DEFAULT 0.0,
                wau_percent REAL DEFAULT 0.0,
                mau_percent REAL DEFAULT 0.0,
                
                -- Отток
                churned_users INTEGER DEFAULT 0,
                churn_rate REAL DEFAULT 0.0,
                retention_rate REAL DEFAULT 0.0,
                
                -- Записи давления
                bp_entries_yesterday INTEGER DEFAULT 0,
                bp_per_active REAL DEFAULT 0.0,
                
                -- Иерархия
                total_admins INTEGER DEFAULT 0,
                total_specialists INTEGER DEFAULT 0,
                total_smart_users INTEGER DEFAULT 0,
                
                -- Технические
                elapsed_seconds REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 📈 Таблица еженедельных агрегатов (для быстрых отчётов)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weekly_aggregates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                week_start TEXT UNIQUE NOT NULL,
                week_end TEXT NOT NULL,
                
                avg_dau REAL DEFAULT 0.0,
                avg_wau REAL DEFAULT 0.0,
                avg_mau REAL DEFAULT 0.0,
                total_new_users INTEGER DEFAULT 0,
                total_bp_entries INTEGER DEFAULT 0,
                avg_churn_rate REAL DEFAULT 0.0,
                avg_retention_rate REAL DEFAULT 0.0,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 📅 Таблица ежемесячных агрегатов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monthly_aggregates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT UNIQUE NOT NULL,
                
                avg_dau REAL DEFAULT 0.0,
                avg_wau REAL DEFAULT 0.0,
                avg_mau REAL DEFAULT 0.0,
                total_new_users INTEGER DEFAULT 0,
                total_bp_entries INTEGER DEFAULT 0,
                avg_churn_rate REAL DEFAULT 0.0,
                avg_retention_rate REAL DEFAULT 0.0,
                month_start_users INTEGER DEFAULT 0,
                month_end_users INTEGER DEFAULT 0,
                growth_rate REAL DEFAULT 0.0,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Индексы для ускорения запросов
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_date ON daily_snapshots(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_weekly_start ON weekly_aggregates(week_start)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_monthly_month ON monthly_aggregates(month)")
        
        conn.commit()
        conn.close()
        
        logger.bind(user_id="system", event_type="analytics_db").info(
            f"✅ База данных аналитики инициализирована: {DB_PATH}"
        )
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_db_error").exception(
            f"❌ Ошибка инициализации БД: {e}"
        )


async def save_daily_snapshot(metrics: Dict) -> bool:
    """
    Сохраняет ежедневный снимок метрик в SQLite.
    
    Args:
        metrics: Словарь с метриками из generate_daily_report()
    
    Returns:
        bool: True если успешно, False если ошибка
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Проверяем, есть ли уже запись за сегодня
        cursor.execute(
            "SELECT id FROM daily_snapshots WHERE date = ?",
            (today,)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Обновляем существующую запись
            cursor.execute("""
                UPDATE daily_snapshots SET
                    total_users = ?,
                    new_users = ?,
                    dau = ?,
                    wau = ?,
                    mau = ?,
                    dau_percent = ?,
                    wau_percent = ?,
                    mau_percent = ?,
                    churned_users = ?,
                    churn_rate = ?,
                    retention_rate = ?,
                    bp_entries_yesterday = ?,
                    bp_per_active = ?,
                    total_admins = ?,
                    total_specialists = ?,
                    total_smart_users = ?,
                    elapsed_seconds = ?,
                    created_at = CURRENT_TIMESTAMP
                WHERE date = ?
            """, (
                metrics.get("total", 0),
                metrics.get("new", 0),
                metrics.get("dau", 0),
                metrics.get("wau", 0),
                metrics.get("mau", 0),
                metrics.get("dau_percent", 0.0),
                metrics.get("wau_percent", 0.0),
                metrics.get("mau_percent", 0.0),
                metrics.get("churned", 0),
                metrics.get("churn_rate", 0.0),
                metrics.get("retention_rate", 0.0),
                metrics.get("bp_entries_yesterday", 0),
                metrics.get("bp_per_active", 0.0),
                metrics.get("hierarchy", {}).get("total_admins", 0),
                metrics.get("hierarchy", {}).get("total_specialists", 0),
                metrics.get("hierarchy", {}).get("total_smart_users", 0),
                metrics.get("elapsed_seconds", 0.0),
                today
            ))
            
            logger.bind(user_id="system", event_type="analytics_db").info(
                f"📊 Обновлён снимок за {today}"
            )
        else:
            # Создаём новую запись
            cursor.execute("""
                INSERT INTO daily_snapshots (
                    date, total_users, new_users, dau, wau, mau,
                    dau_percent, wau_percent, mau_percent,
                    churned_users, churn_rate, retention_rate,
                    bp_entries_yesterday, bp_per_active,
                    total_admins, total_specialists, total_smart_users,
                    elapsed_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                today,
                metrics.get("total", 0),
                metrics.get("new", 0),
                metrics.get("dau", 0),
                metrics.get("wau", 0),
                metrics.get("mau", 0),
                metrics.get("dau_percent", 0.0),
                metrics.get("wau_percent", 0.0),
                metrics.get("mau_percent", 0.0),
                metrics.get("churned", 0),
                metrics.get("churn_rate", 0.0),
                metrics.get("retention_rate", 0.0),
                metrics.get("bp_entries_yesterday", 0),
                metrics.get("bp_per_active", 0.0),
                metrics.get("hierarchy", {}).get("total_admins", 0),
                metrics.get("hierarchy", {}).get("total_specialists", 0),
                metrics.get("hierarchy", {}).get("total_smart_users", 0),
                metrics.get("elapsed_seconds", 0.0)
            ))
            
            logger.bind(user_id="system", event_type="analytics_db").info(
                f"📊 Создан снимок за {today}"
            )
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_db_error").exception(
            f"❌ Ошибка сохранения снимка: {e}"
        )
        return False


async def get_historical_data(days: int = 30) -> List[Dict]:
    """
    Получает исторические данные за N дней.
    
    Args:
        days: Количество дней для выборки
    
    Returns:
        List[Dict]: Список записей с метриками
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row  # Возвращает строки как словари
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM daily_snapshots
            WHERE date >= date('now', ?)
            ORDER BY date DESC
        """, (f"-{days} days",))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_db_error").exception(
            f"❌ Ошибка получения истории: {e}"
        )
        return []


async def get_growth_trend(days: int = 30) -> Dict:
    """
    Анализирует тренд роста за N дней.
    
    Returns:
        Dict: Статистика тренда
    """
    try:
        data = await get_historical_data(days)
        
        if len(data) < 2:
            return {
                "trend": "insufficient_data",
                "message": "Недостаточно данных для анализа"
            }
        
        # Считаем изменения
        first = data[-1]  # Самый старый
        last = data[0]    # Самый новый
        
        total_growth = last["total_users"] - first["total_users"]
        total_growth_percent = (total_growth / first["total_users"] * 100) if first["total_users"] > 0 else 0
        
        dau_growth = last["dau"] - first["dau"]
        dau_growth_percent = (dau_growth / first["dau"] * 100) if first["dau"] > 0 else 0
        
        # Средние значения
        avg_dau = sum(d["dau"] for d in data) / len(data)
        avg_new_users = sum(d["new_users"] for d in data) / len(data)
        
        # Определяем тренд
        if total_growth_percent > 10:
            trend = "growing"
        elif total_growth_percent < -10:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "total_growth": total_growth,
            "total_growth_percent": total_growth_percent,
            "dau_growth": dau_growth,
            "dau_growth_percent": dau_growth_percent,
            "avg_dau": avg_dau,
            "avg_new_users": avg_new_users,
            "days_analyzed": len(data),
            "period": f"{first['date']} → {last['date']}"
        }
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_db_error").exception(
            f"❌ Ошибка анализа тренда: {e}"
        )
        return {"trend": "error", "message": str(e)}


async def calculate_weekly_aggregates():
    """
    Рассчитывает и сохраняет еженедельные агрегаты.
    Запускается раз в неделю (например, в понедельник в 7:00).
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Получаем последнюю полную неделю
        today = datetime.utcnow()
        last_monday = today - timedelta(days=today.weekday(), weeks=1)
        next_sunday = last_monday + timedelta(days=6)
        
        week_start = last_monday.strftime("%Y-%m-%d")
        week_end = next_sunday.strftime("%Y-%m-%d")
        
        # Проверяем, есть ли уже агрегат
        cursor.execute(
            "SELECT id FROM weekly_aggregates WHERE week_start = ?",
            (week_start,)
        )
        
        if cursor.fetchone():
            logger.bind(user_id="system", event_type="analytics_db").info(
                f"⏭️ Агрегат за неделю {week_start} уже существует"
            )
            conn.close()
            return
        
        # Считаем агрегаты
        cursor.execute("""
            SELECT
                AVG(dau) as avg_dau,
                AVG(wau) as avg_wau,
                AVG(mau) as avg_mau,
                SUM(new_users) as total_new_users,
                SUM(bp_entries_yesterday) as total_bp_entries,
                AVG(churn_rate) as avg_churn_rate,
                AVG(retention_rate) as avg_retention_rate
            FROM daily_snapshots
            WHERE date BETWEEN ? AND ?
        """, (week_start, week_end))
        
        row = cursor.fetchone()
        
        if row and row[0] is not None:
            cursor.execute("""
                INSERT INTO weekly_aggregates (
                    week_start, week_end,
                    avg_dau, avg_wau, avg_mau,
                    total_new_users, total_bp_entries,
                    avg_churn_rate, avg_retention_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                week_start, week_end,
                row[0], row[1], row[2],
                row[3], row[4],
                row[5], row[6]
            ))
            
            conn.commit()
            logger.bind(user_id="system", event_type="analytics_db").info(
                f"✅ Создан недельный агрегат: {week_start} → {week_end}"
            )
        
        conn.close()
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_db_error").exception(
            f"❌ Ошибка расчёта недельных агрегатов: {e}"
        )


async def calculate_monthly_aggregates():
    """
    Рассчитывает и сохраняет ежемесячные агрегаты.
    Запускается 1-го числа каждого месяца в 7:00.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Получаем предыдущий месяц
        today = datetime.utcnow()
        first_day_last_month = today.replace(day=1) - timedelta(days=1)
        first_day_last_month = first_day_last_month.replace(day=1)
        last_day_last_month = today.replace(day=1) - timedelta(days=1)
        
        month_start = first_day_last_month.strftime("%Y-%m-%d")
        month_end = last_day_last_month.strftime("%Y-%m-%d")
        month_key = first_day_last_month.strftime("%Y-%m")
        
        # Проверяем, есть ли уже агрегат
        cursor.execute(
            "SELECT id FROM monthly_aggregates WHERE month = ?",
            (month_key,)
        )
        
        if cursor.fetchone():
            logger.bind(user_id="system", event_type="analytics_db").info(
                f"⏭️ Агрегат за месяц {month_key} уже существует"
            )
            conn.close()
            return
        
        # Считаем агрегаты
        cursor.execute("""
            SELECT
                AVG(dau) as avg_dau,
                AVG(wau) as avg_wau,
                AVG(mau) as avg_mau,
                SUM(new_users) as total_new_users,
                SUM(bp_entries_yesterday) as total_bp_entries,
                AVG(churn_rate) as avg_churn_rate,
                AVG(retention_rate) as avg_retention_rate,
                MIN(total_users) as month_start_users,
                MAX(total_users) as month_end_users
            FROM daily_snapshots
            WHERE date BETWEEN ? AND ?
        """, (month_start, month_end))
        
        row = cursor.fetchone()
        
        if row and row[0] is not None:
            growth_rate = ((row[8] - row[7]) / row[7] * 100) if row[7] > 0 else 0
            
            cursor.execute("""
                INSERT INTO monthly_aggregates (
                    month,
                    avg_dau, avg_wau, avg_mau,
                    total_new_users, total_bp_entries,
                    avg_churn_rate, avg_retention_rate,
                    month_start_users, month_end_users, growth_rate
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                month_key,
                row[0], row[1], row[2],
                row[3], row[4],
                row[5], row[6],
                row[7], row[8], growth_rate
            ))
            
            conn.commit()
            logger.bind(user_id="system", event_type="analytics_db").info(
                f"✅ Создан месячный агрегат: {month_key}"
            )
        
        conn.close()
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_db_error").exception(
            f"❌ Ошибка расчёта месячных агрегатов: {e}"
        )


async def export_to_csv(days: int = 30, filename: str = "analytics_export.csv") -> str:
    """
    Экспортирует исторические данные в CSV.
    
    Returns:
        str: Путь к файлу
    """
    try:
        import csv
        
        data = await get_historical_data(days)
        
        if not data:
            return "No data"
        
        filepath = Path("data") / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        logger.bind(user_id="system", event_type="analytics_db").info(
            f"📁 Экспорт в CSV: {filepath} ({len(data)} записей)"
        )
        
        return str(filepath)
        
    except Exception as e:
        logger.bind(user_id="system", event_type="analytics_db_error").exception(
            f"❌ Ошибка экспорта в CSV: {e}"
        )
        return "Error"
