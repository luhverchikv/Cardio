# tests/test_mongo.py
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone, timedelta


@pytest_asyncio.fixture
async def mock_mongo_module(mock_mongo_collection, monkeypatch):
    """Подмена реального mongo.py на тестовый с моком коллекции"""
    # Мокируем инициализацию клиента в mongo.py
    with patch('mongo.client'):
        with patch('mongo.db'):
            with patch('mongo.users_collection', mock_mongo_collection):
                import mongo
                yield mongo


@pytest_asyncio.fixture
async def sample_user_data():
    """Пример данных пользователя для тестов"""
    return {
        "user_id": 123456,
        "systolic": 120,
        "diastolic": 80,
        "pulse": 72,
        "arrhythmic": False
    }


@pytest.mark.asyncio
async def test_get_or_create_user_new(mock_mongo_module, mock_mongo_collection):
    """Тест создания нового пользователя"""
    result = await mock_mongo_module.get_or_create_user(999999)
    
    assert result is True  # Пользователь был создан
    # Проверяем, что update_one был вызван с upsert
    mock_mongo_collection.update_one.assert_called_once()


@pytest.mark.asyncio
async def test_add_blood_pressure_entry(mock_mongo_module, mock_mongo_collection, sample_user_data):
    """Тест добавления записи о давлении"""
    result = await mock_mongo_module.add_blood_pressure_entry(
        user_id=sample_user_data["user_id"],
        systolic=sample_user_data["systolic"],
        diastolic=sample_user_data["diastolic"],
        pulse=sample_user_data["pulse"],
        arrhythmic=sample_user_data["arrhythmic"]
    )
    
    assert result is True
    # Проверяем структуру добавляемой записи
    call_args = mock_mongo_collection.update_one.call_args
    push_data = call_args[0][1]["$push"]["blood_pressure_entries"]
    
    assert push_data["systolic"] == 120
    assert "timestamp" in push_data
    assert isinstance(push_data["timestamp"], datetime)


@pytest.mark.asyncio
async def test_set_reminders_status_valid(mock_mongo_module, mock_mongo_collection):
    """Тест установки статуса уведомлений (валидные значения)"""
    for status in [0, 1, 2, 3]:
        await mock_mongo_module.set_reminders_status(123456, status)
        mock_mongo_collection.update_one.assert_called_with(
            {"user_id": 123456},
            {"$set": {"reminders": status}}
        )


@pytest.mark.asyncio
async def test_set_reminders_status_invalid(mock_mongo_module):
    """Тест установки невалидного статуса уведомлений"""
    with pytest.raises(ValueError, match="Invalid reminder status"):
        await mock_mongo_module.set_reminders_status(123456, 99)


@pytest.mark.asyncio
async def test_get_bp_entries_last_days(mock_mongo_module, mock_mongo_collection):
    """Тест получения записей за последние N дней"""
    # Мокируем ответ агрегации
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[{
        "blood_pressure_entries": [{"timestamp": datetime.now(timezone.utc), "systolic": 120}],
        "bp_targets": {"systolic": 130, "diastolic": 85}
    }])
    mock_mongo_collection.aggregate.return_value = mock_cursor
    
    entries, targets = await mock_mongo_module.get_bp_entries_last_days(123456, days=7)
    
    assert isinstance(entries, list)
    assert "systolic" in targets

