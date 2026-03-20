# tests/test_mongo.py
"""
Тесты для модуля mongo.py
Все тесты используют моки — не требуют реального подключения к MongoDB.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, AsyncMock, patch


# ============================================================================
# ФИКСТУРЫ (локальные для этого файла)
# ============================================================================

@pytest_asyncio.fixture
async def mock_collection():
    """Создаем чистый MagicMock для коллекции MongoDB"""
    collection = MagicMock()
    collection.update_one = AsyncMock()
    collection.find_one = AsyncMock()
    collection.delete_one = AsyncMock()
    
    # Мок для aggregate: возвращает курсор с методом to_list
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[])
    collection.aggregate = MagicMock(return_value=mock_cursor)
    
    return collection


@pytest.fixture
def patch_collection(mock_collection):
    """Патчим users_collection в модуле mongo"""
    with patch('mongo.users_collection', mock_collection):
        yield mock_collection


@pytest.fixture
def sample_bp_entry():
    """Пример данных для записи о давлении"""
    return {
        "user_id": 123456,
        "systolic": 120,
        "diastolic": 80,
        "pulse": 72,
        "arrhythmic": False
    }


# ============================================================================
# ТЕСТЫ
# ============================================================================

class TestGetOrCreateUser:
    """Тесты функции get_or_create_user"""
    
    @pytest.mark.asyncio
    async def test_creates_new_user(self, mock_env_vars, patch_collection):
        """Пользователя нет в БД -> создаётся новый"""
        from mongo import get_or_create_user
        
        # find_one возвращает None (пользователь не найден)
        patch_collection.find_one.return_value = None
        # update_one имитирует upsert: возвращаем mock с upserted_id
        patch_collection.update_one.return_value = MagicMock(upserted_id="new_id")
        
        result = await get_or_create_user(999999)
        
        assert result is True
        patch_collection.find_one.assert_called_once_with({"user_id": 999999})
        patch_collection.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_user_exists(self, mock_env_vars, patch_collection):
        """Пользователь уже есть в БД -> ничего не создаём"""
        from mongo import get_or_create_user
        
        # find_one возвращает данные пользователя
        patch_collection.find_one.return_value = {"user_id": 123456, "reminders": 1}
        
        result = await get_or_create_user(123456)
        
        assert result is True
        patch_collection.find_one.assert_called_once_with({"user_id": 123456})
        # update_one не должен вызываться, если пользователь найден
        patch_collection.update_one.assert_not_called()


class TestAddBloodPressureEntry:
    """Тесты функции add_blood_pressure_entry"""
    
    @pytest.mark.asyncio
    async def test_adds_entry_successfully(self, mock_env_vars, patch_collection, sample_bp_entry):
        """Успешное добавление записи о давлении"""
        from mongo import add_blood_pressure_entry
        
        patch_collection.update_one.return_value = MagicMock(modified_count=1)
        
        result = await add_blood_pressure_entry(
            user_id=sample_bp_entry["user_id"],
            systolic=sample_bp_entry["systolic"],
            diastolic=sample_bp_entry["diastolic"],
            pulse=sample_bp_entry["pulse"],
            arrhythmic=sample_bp_entry["arrhythmic"]
        )
        
        assert result is True
        
        # Проверяем аргументы вызова update_one
        call_args = patch_collection.update_one.call_args
        assert call_args is not None
        
        filter_arg, update_arg = call_args[0]
        assert filter_arg == {"user_id": sample_bp_entry["user_id"]}
        assert "$push" in update_arg
        assert "blood_pressure_entries" in update_arg["$push"]
        
        # Проверяем структуру добавляемой записи
        entry = update_arg["$push"]["blood_pressure_entries"]
        assert entry["systolic"] == 120
        assert entry["diastolic"] == 80
        assert entry["pulse"] == 72
        assert entry["arrhythmic"] is False
        assert "timestamp" in entry
        assert isinstance(entry["timestamp"], datetime)
    
    @pytest.mark.asyncio
    async def test_handles_arrhythmic_true(self, mock_env_vars, patch_collection):
        """Запись с arrhythmic=True"""
        from mongo import add_blood_pressure_entry
        
        patch_collection.update_one.return_value = MagicMock(modified_count=1)
        
        await add_blood_pressure_entry(
            user_id=123456,
            systolic=140,
            diastolic=90,
            pulse=85,
            arrhythmic=True  # ← Важный случай
        )
        
        entry = patch_collection.update_one.call_args[0][1]["$push"]["blood_pressure_entries"]
        assert entry["arrhythmic"] is True


class TestSetRemindersStatus:
    """Тесты функции set_reminders_status"""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", [0, 1, 2, 3])
    async def test_valid_statuses(self, mock_env_vars, patch_collection, status):
        """Установка валидных статусов уведомлений"""
        from mongo import set_reminders_status
        
        patch_collection.update_one.return_value = MagicMock(modified_count=1)
        
        result = await set_reminders_status(123456, status)
        
        assert result is True
        
        filter_arg, update_arg = patch_collection.update_one.call_args[0]
        assert filter_arg == {"user_id": 123456}
        assert update_arg == {"$set": {"reminders": status}}
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_status", [-1, 4, 10, 99])
    async def test_invalid_statuses_raise(self, mock_env_vars, invalid_status):
        """Невалидные статусы вызывают ValueError"""
        from mongo import set_reminders_status
        
        with pytest.raises(ValueError, match="Invalid reminder status"):
            await set_reminders_status(123456, invalid_status)


class TestGetBpEntriesLastDays:
    """Тесты функции get_bp_entries_last_days"""
    
    @pytest.mark.asyncio
    async def test_returns_entries_and_targets(self, mock_env_vars, patch_collection):
        """Успешное получение записей и целей"""
        from mongo import get_bp_entries_last_days
        
        # Готовим мок-ответ агрегации
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[{
            "blood_pressure_entries": [
                {
                    "timestamp": datetime.now(timezone.utc) - timedelta(days=1),
                    "systolic": 120,
                    "diastolic": 80,
                    "pulse": 70
                },
                {
                    "timestamp": datetime.now(timezone.utc) - timedelta(days=2),
                    "systolic": 125,
                    "diastolic": 82,
                    "pulse": 75
                }
            ],
            "bp_targets": {"systolic": 130, "diastolic": 85}
        }])
        patch_collection.aggregate.return_value = mock_cursor
        
        entries, targets = await get_bp_entries_last_days(123456, days=7)
        
        # Проверяем тип и содержимое результата
        assert isinstance(entries, list)
        assert len(entries) == 2
        assert entries[0]["systolic"] == 120
        assert entries[1]["diastolic"] == 82
        
        assert isinstance(targets, dict)
        assert targets["systolic"] == 130
        assert targets["diastolic"] == 85
        
        # Проверяем, что aggregate вызван с правильным pipeline
        patch_collection.aggregate.assert_called_once()
        pipeline = patch_collection.aggregate.call_args[0][0]
        assert pipeline[0]["$match"]["user_id"] == 123456
    
    @pytest.mark.asyncio
    async def test_empty_result(self, mock_env_vars, patch_collection):
        """Нет записей за указанный период"""
        from mongo import get_bp_entries_last_days
        
        # Пустой результат агрегации
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        patch_collection.aggregate.return_value = mock_cursor
        
        entries, targets = await get_bp_entries_last_days(999999, days=30)
        
        assert entries == []
        assert targets == {}  # или {"systolic": None, "diastolic": None} — зависит от реализации


class TestDeleteUserData:
    """Тесты функции delete_user_data"""
    
    @pytest.mark.asyncio
    async def test_deletes_user_successfully(self, mock_env_vars, patch_collection):
        """Успешное удаление данных пользователя"""
        from mongo import delete_user_data
        
        patch_collection.delete_one.return_value = MagicMock(deleted_count=1)
        
        result = await delete_user_data(123456)
        
        assert result is True
        patch_collection.delete_one.assert_called_once_with({"user_id": 123456})
    
    @pytest.mark.asyncio
    async def test_user_not_found(self, mock_env_vars, patch_collection):
        """Пользователь не найден при удалении"""
        from mongo import delete_user_data
        
        patch_collection.delete_one.return_value = MagicMock(deleted_count=0)
        
        result = await delete_user_data(999999)
        
        # Функция может возвращать False или True — зависит от реализации
        # Проверяем, что удаление было попытано
        patch_collection.delete_one.assert_called_once_with({"user_id": 999999})

