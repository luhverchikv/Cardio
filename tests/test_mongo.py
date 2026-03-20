# tests/test_mongo.py
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_get_or_create_user_new(mock_env_vars, patch_users_collection):
    """Тест создания нового пользователя"""
    # Импортируем функцию ПОСЛЕ патчинга коллекции
    from mongo import get_or_create_user
    
    # Настраиваем mock: upserted_id != None означает, что пользователь создан
    patch_users_collection.update_one.return_value = MagicMock(upserted_id=123)
    
    result = await get_or_create_user(999999)
    
    assert result is True
    patch_users_collection.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_add_blood_pressure_entry(mock_env_vars, patch_users_collection):
    """Тест добавления записи о давлении"""
    from mongo import add_blood_pressure_entry
    
    # Настраиваем mock: modified_count=1 означает успешное обновление
    patch_users_collection.update_one.return_value = MagicMock(modified_count=1)
    
    result = await add_blood_pressure_entry(
        user_id=123456,
        systolic=120,
        diastolic=80,
        pulse=72,
        arrhythmic=False
    )
    
    assert result is True
    
    # Проверяем аргументы вызова
    call_args = patch_users_collection.update_one.call_args
    assert call_args is not None
    
    filter_arg, update_arg = call_args[0]
    assert filter_arg["user_id"] == 123456
    assert "$push" in update_arg
    assert "blood_pressure_entries" in update_arg["$push"]
    
    entry = update_arg["$push"]["blood_pressure_entries"]
    assert entry["systolic"] == 120
    assert entry["diastolic"] == 80
    assert entry["pulse"] == 72
    assert "timestamp" in entry


@pytest.mark.asyncio
async def test_set_reminders_status_valid(mock_env_vars, patch_users_collection):
    """Тест установки статуса уведомлений (валидные значения)"""
    from mongo import set_reminders_status
    
    patch_users_collection.update_one.return_value = MagicMock(modified_count=1)
    
    for status in [0, 1, 2, 3]:
        await set_reminders_status(123456, status)
        
        call_args = patch_users_collection.update_one.call_args
        filter_arg, update_arg = call_args[0]
        
        assert filter_arg == {"user_id": 123456}
        assert update_arg == {"$set": {"reminders": status}}


@pytest.mark.asyncio
async def test_set_reminders_status_invalid(mock_env_vars):
    """Тест установки невалидного статуса уведомлений"""
    from mongo import set_reminders_status
    
    with pytest.raises(ValueError, match="Invalid reminder status"):
        await set_reminders_status(123456, 99)


@pytest.mark.asyncio
async def test_get_bp_entries_last_days(mock_env_vars, patch_users_collection):
    """Тест получения записей за последние N дней"""
    from mongo import get_bp_entries_last_days
    
    # Настраиваем мок для aggregate
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[{
        "blood_pressure_entries": [
            {"timestamp": datetime.now(timezone.utc), "systolic": 120, "diastolic": 80}
        ],
        "bp_targets": {"systolic": 130, "diastolic": 85}
    }])
    patch_users_collection.aggregate.return_value = mock_cursor
    
    entries, targets = await get_bp_entries_last_days(123456, days=7)
    
    assert isinstance(entries, list)
    assert isinstance(targets, dict)
    assert targets.get("systolic") == 130

