# tests/test_mongo.py
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta


@pytest_asyncio.fixture
async def mock_mongo_collection():
    """Создаем правильный mock для коллекции MongoDB"""
    collection = MagicMock()
    collection.update_one = AsyncMock()
    collection.find_one = AsyncMock()
    collection.delete_one = AsyncMock()
    collection.aggregate = MagicMock(return_value=AsyncMock())
    return collection


@pytest_asyncio.fixture
async def mock_mongo_module(mock_mongo_collection, monkeypatch):
    """Подменяем mongo.py моками"""
    # Создаем мок для всего модуля mongo
    with patch('mongo.client'), \
         patch('mongo.db'), \
         patch('mongo.users_collection', mock_mongo_collection):
        
        # Перезагружаем модуль mongo чтобы он использовал моки
        import importlib
        import mongo
        importlib.reload(mongo)
        
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
    # Настраиваем mock для find_one (пользователь не найден)
    mock_mongo_collection.find_one.return_value = None
    
    result = await mock_mongo_module.get_or_create_user(999999)
    
    assert result is True
    # Проверяем, что update_one был вызван
    assert mock_mongo_collection.update_one.called


@pytest.mark.asyncio
async def test_add_blood_pressure_entry(mock_mongo_module, mock_mongo_collection, sample_user_data):
    """Тест добавления записи о давлении"""
    # Настраиваем mock для успешного добавления
    mock_mongo_collection.update_one.return_value = MagicMock(modified_count=1)
    
    result = await mock_mongo_module.add_blood_pressure_entry(
        user_id=sample_user_data["user_id"],
        systolic=sample_user_data["systolic"],
        diastolic=sample_user_data["diastolic"],
        pulse=sample_user_data["pulse"],
        arrhythmic=sample_user_data["arrhythmic"]
    )
    
    assert result is True
    
    # Проверяем, что update_one был вызван с правильными аргументами
    call_args = mock_mongo_collection.update_one.call_args
    assert call_args is not None
    
    # Проверяем структуру данных
    filter_arg = call_args[0][0]
    update_arg = call_args[0][1]
    
    assert filter_arg["user_id"] == sample_user_data["user_id"]
    assert "$push" in update_arg
    assert "blood_pressure_entries" in update_arg["$push"]
    
    entry = update_arg["$push"]["blood_pressure_entries"]
    assert entry["systolic"] == 120
    assert entry["diastolic"] == 80
    assert entry["pulse"] == 72


@pytest.mark.asyncio
async def test_set_reminders_status_valid(mock_mongo_module, mock_mongo_collection):
    """Тест установки статуса уведомлений (валидные значения)"""
    mock_mongo_collection.update_one.return_value = MagicMock(modified_count=1)
    
    for status in [0, 1, 2, 3]:
        await mock_mongo_module.set_reminders_status(123456, status)
        
        # Проверяем последний вызов
        call_args = mock_mongo_collection.update_one.call_args
        filter_arg = call_args[0][0]
        update_arg = call_args[0][1]
        
        assert filter_arg == {"user_id": 123456}
        assert update_arg == {"$set": {"reminders": status}}


@pytest.mark.asyncio
async def test_set_reminders_status_invalid(mock_mongo_module):
    """Тест установки невалидного статуса уведомлений"""
    with pytest.raises(ValueError, match="Invalid reminder status"):
        await mock_mongo_module.set_reminders_status(123456, 99)


@pytest.mark.asyncio
async def test_get_bp_entries_last_days(mock_mongo_module, mock_mongo_collection):
    """Тест получения записей за последние N дней"""
    # Создаем мок для курсора агрегации
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[{
        "blood_pressure_entries": [
            {"timestamp": datetime.now(timezone.utc), "systolic": 120, "diastolic": 80}
        ],
        "bp_targets": {"systolic": 130, "diastolic": 85}
    }])
    
    # Настраиваем aggregate возвращать курсор
    mock_mongo_collection.aggregate = MagicMock(return_value=mock_cursor)
    
    entries, targets = await mock_mongo_module.get_bp_entries_last_days(123456, days=7)
    
    assert isinstance(entries, list)
    assert isinstance(targets, dict)
    assert "systolic" in targets

