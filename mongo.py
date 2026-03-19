from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple, Literal
from motor.motor_asyncio import AsyncIOMotorClient

from config import config
from utils.encryption import encrypt_text

# Инициализация клиента
# Рекомендуется оборачивать в lifecycle события приложения (startup/shutdown)
client = AsyncIOMotorClient(config.db.url)
db = client[config.db.name]
users_collection = db["users"]

# Константы для ролей и статусов
VALID_ROLES = {"user", "admin", "specialist", "owner"}
REMINDER_STATUS_OFF = 0
REMINDER_STATUS_MORNING = 1
REMINDER_STATUS_EVENING = 2
REMINDER_STATUS_BOTH = 3


def _get_utc_now() -> datetime:
    """Хелпер для получения текущего времени в UTC (замена устаревшему utcnow)"""
    return datetime.now(timezone.utc)


async def get_or_create_user(user_id: int) -> bool:
    """
    Создает пользователя, если он не существует.
    Возвращает True, если пользователь был создан, False если уже существовал.
    """
    # Используем upsert для атомарности и избежания race condition
    default_data = {
        "user_id": user_id,
        "registered_at": _get_utc_now(),
        "reminders": REMINDER_STATUS_OFF,

        "roles": ["user"],
        "bp_targets": {
            "systolic": 130,
            "diastolic": 85,
            "heart_rate_min": 55,
            "heart_rate_max": 70 
        },
        "blood_pressure_entries": []
    }
    
    result = await users_collection.update_one(
        {"user_id": user_id},
        {"$setOnInsert": default_data},
        upsert=True
    )
    # upserted_id будет не None, только если документ был создан
    return result.upserted_id is not None


async def add_blood_pressure_entry(
    user_id: int,
    systolic: Optional[int],
    diastolic: Optional[int],
    pulse: Optional[int],
    arrhythmic: bool,
) -> bool:
    """Добавляет запись артериального давления и пульса пользователю"""
    entry = {
        "timestamp": _get_utc_now(),
        "systolic": systolic,
        "diastolic": diastolic,
        "pulse": pulse,
        "arrhythmic": arrhythmic,
    }

    result = await users_collection.update_one(
        {"user_id": user_id},
        {"$push": {"blood_pressure_entries": entry}}
    )
    return result.modified_count == 1


async def delete_user_data(user_id: int) -> bool:
    """Удаляет все данные пользователя из базы данных"""
    result = await users_collection.delete_one({"user_id": user_id})
    return result.deleted_count > 0


async def get_my_data(user_id: int) -> Optional[Dict[str, Any]]:
    """Возвращает ВСЕ данные пользователя по user_id (для отладки)"""
    return await users_collection.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    
async def get_users_count() -> int:
    return await users_collection.count_documents({})


async def get_last_bp_timestamp(user_id: int) -> Optional[datetime]:
    user = await users_collection.find_one(
        {"user_id": user_id},
        {"blood_pressure_entries": {"$slice": -1}, "_id": 0}
    )

    if not user:
        return None

    entries = user.get("blood_pressure_entries", [])
    if not entries:
        return None

    # $slice возвращает список, берем первый элемент
    return entries[0].get("timestamp")


async def get_bp_entries_last_days(user_id: int, days: int = 30) -> Tuple[List[Dict], Dict]:
    """
    Возвращает записи за последние N дней и целевые показатели.
    Оптимизировано: фильтрация происходит на стороне MongoDB.
    """
    since = _get_utc_now() - timedelta(days=days)

    # Используем агрегацию для фильтрации массива на стороне БД
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$project": {
            "bp_targets": 1,
            "blood_pressure_entries": {
                "$filter": {
                    "input": "$blood_pressure_entries",
                    "as": "entry",
                    "cond": {"$gte": ["$$entry.timestamp", since]}
                }
            }
        }}
    ]
    
    cursor = users_collection.aggregate(pipeline)
    doc = await cursor.to_list(length=1)
    
    if not doc:
        return [], {}
        
    user_data = doc[0]
    return user_data.get("blood_pressure_entries", []), user_data.get("bp_targets", {})


# ========= Работа с уведомлениями =========
async def set_reminders_status(user_id: int, value: int):
    """
    Запись в базу уведомлений.
    0 - отключены, 1 - утро, 2 - вечер, 3 - оба.
    """
    # Валидация значения (опционально, но желательно)
    if value not in {0, 1, 2, 3}:
        raise ValueError("Invalid reminder status value")
        
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"reminders": value}}
    )


async def get_reminders_status(user_id: int) -> int:
    user = await users_collection.find_one({"user_id": user_id}, {"reminders": 1, "_id": 0})
    return int(user.get("reminders", 0)) if user else 0
    
    
async def get_users_with_reminders(limit: int = 1000):
    """
    Возвращает курсор или список пользователей с активными уведомлениями.
    Добавлен limit для предотвращения переполнения памяти.
    """
    cursor = users_collection.find({"reminders": {"$gt": 0}}, {"_id": 0})
    return await cursor.to_list(length=limit)

# ======Работа с целевыми показателями=====
async def get_bp_target(user_id: int) -> Optional[Dict]:
    user = await users_collection.find_one(
        {"user_id": user_id},
        {"_id": 0, "bp_targets": 1}
    )
    return user.get("bp_targets") if user else None


async def set_bp_target(user_id: int, new_values: dict) -> bool:
    # Получаем текущие значения, чтобы не затереть отсутствующие ключи
    current = await get_bp_target(user_id) or {}

    merged = {
        "systolic": current.get("systolic"),
        "diastolic": current.get("diastolic"),
        "heart_rate_min": current.get("heart_rate_min"),
        "heart_rate_max": current.get("heart_rate_max"),
        **new_values,
    }
    # Убираем None значения, которые могли прийти из current, если их там не было
    # (Опционально: зависит от желаемой логики хранения)
    merged = {k: v for k, v in merged.items() if v is not None}

    result = await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"bp_targets": merged}}
    )
    return result.modified_count == 1

# ============ Работа с ролями ============
async def update_user_roles_and_connections(
    requester_id: int,
    target_id: int,
    target_role: str,
    alias: str,
    connection_field: Optional[str] = None
):
    # Валидация роли для безопасности (защита от инъекций в имя поля)
    if target_role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {target_role}")

    if connection_field is None:
        connection_field = f"connected_{target_role}s"
    
    id_key = f"{target_role}_id"
    encrypted_alias = encrypt_text(alias)

    # 1. Обновляем роль target_id
    # Убрали upsert=True, чтобы не создавать пустых пользователей случайно
    await users_collection.update_one(
        {"user_id": target_id},
        {
            "$addToSet": {"roles": target_role},
            "$set": {
                "created_by": {
                    "user_id": requester_id,
                    "connected_at": _get_utc_now()
                }
            }
        }
    )

    # 2. Добавляем зашифрованный alias в связи requester_id
    await users_collection.update_one(
        {"user_id": requester_id},
        {
            "$addToSet": {
                connection_field: {
                    id_key: target_id,
                    "alias": encrypted_alias
                }
            }
        }
    )
    

async def update_entity_alias(owner_id: int, entity_id: int, new_alias: str, connection_field: str):
    """Обновляет псевдоним сущности в документе владельца."""
    # Санитизация имени поля (базовая)
    if not connection_field.startswith("connected_"):
        raise ValueError("Invalid connection field format")
        
    encrypted_alias = encrypt_text(new_alias)
    entity_type = connection_field.replace("connected_", "").rstrip("s")
    id_key = f"{entity_type}_id"

    await users_collection.update_one(
        {"user_id": owner_id, f"{connection_field}.{id_key}": entity_id},
        {"$set": {f"{connection_field}.$.alias": encrypted_alias}}
    )


async def delete_entity_from_db(owner_id: int, entity_id: int, target_role: str, connection_field: str):
    if target_role not in VALID_ROLES:
        raise ValueError(f"Invalid role: {target_role}")

    id_key = f"{target_role}_id"

    # 1️⃣ Удаляем роль из массива ролей сущности
    await users_collection.update_one(
        {"user_id": entity_id},
        {
            "$pull": {"roles": target_role},
            "$unset": {"created_by": 1, "alias": 1} # Значение для $unset игнорируется, обычно ставят 1
        }
    )

    # 2️⃣ Удаляем связь у владельца
    await users_collection.update_one(
        {"user_id": owner_id},
        {"$pull": {connection_field: {id_key: entity_id}}}
    )


async def ensure_owner_role(user_id: int) -> bool:
    if user_id != config.bot.owner_id:
        return False

    result = await users_collection.update_one(
        {"user_id": user_id},
        {"$addToSet": {"roles": "owner"}}
    )
    return result.modified_count == 1
