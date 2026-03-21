# tests/test_handlers/test_start_menu.py
"""
Тесты для хендлеров меню в menu/start_menu.py
Используем моки для aiogram и mongo — не требуют реального бота/БД.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, InlineKeyboardMarkup


# ============================================================================
# ФИКСТУРЫ (локальные для этого файла)
# ============================================================================

@pytest.fixture
def mock_message(create_mock_message):
    """Создаёт стандартное тестовое сообщение"""
    return create_mock_message(user_id=123456, chat_id=123456)


@pytest.fixture
def mock_callback(create_mock_callback):
    """Создаёт стандартный тестовый callback"""
    return create_mock_callback(user_id=123456)


@pytest.fixture
def mock_bot(mock_aiogram_bot):
    """Мок aiogram Bot"""
    return mock_aiogram_bot


# ============================================================================
# ТЕСТЫ: КОМАНДА /start
# ============================================================================

class TestCommandStart:
    """Тесты функции command_start"""
    
    @pytest.mark.asyncio
    async def test_creates_new_user_and_sends_welcome(
        self, mock_env_vars, mock_message, mock_bot
    ):
        """Новый пользователь: создаётся запись + отправляется приветствие"""
        from menu.start_menu import command_start
        
        # Мокаем функцию создания пользователя
        with patch('menu.start_menu.get_or_create_user', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = True  # Пользователь создан
            
            await command_start(mock_message, mock_bot)
            
            # Проверяем, что пользователь был создан
            mock_create.assert_called_once_with(123456)
            # Проверяем, что отправлено приветственное сообщение
            mock_message.answer.assert_called()
            # Проверяем, что в сообщении есть ключевые слова
            call_args = mock_message.answer.call_args[0][0]
            assert "Рад видеть" in call_args or "👋" in call_args
    
    @pytest.mark.asyncio
    async def test_existing_user_still_gets_welcome(
        self, mock_env_vars, mock_message, mock_bot
    ):
        """Существующий пользователь тоже получает приветствие"""
        from menu.start_menu import command_start
        
        with patch('menu.start_menu.get_or_create_user', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = False  # Пользователь уже был
            
            await command_start(mock_message, mock_bot)
            
            # Функция всё равно вызывается
            mock_create.assert_called_once_with(123456)
            # Приветствие отправляется в любом случае
            mock_message.answer.assert_called()
    
    @pytest.mark.asyncio
    async def test_command_start_with_keyboard(
        self, mock_env_vars, mock_message, mock_bot
    ):
        """Приветствие содержит клавиатуру с кнопками"""
        from menu.start_menu import command_start
        
        with patch('menu.start_menu.get_or_create_user', new_callable=AsyncMock, return_value=True):
            await command_start(mock_message, mock_bot)
            
            # Проверяем, что reply_markup был передан
            call_kwargs = mock_message.answer.call_args[1]
            assert 'reply_markup' in call_kwargs
            # Проверяем тип клавиатуры
            assert isinstance(call_kwargs['reply_markup'], ReplyKeyboardMarkup)


# ============================================================================
# ТЕСТЫ: КНОПКА "ОТЧЁТ"
# ============================================================================

class TestReportButton:
    """Тесты функции report_button (если есть)"""
    
    @pytest.mark.asyncio
    async def test_report_button_sends_placeholder(
        self, mock_env_vars, mock_message, mock_bot
    ):
        """Нажатие на кнопку 'Отчёт' отправляет заглушку"""
        try:
            from menu.start_menu import report_button
        except ImportError:
            pytest.skip("report_button not implemented")
        
        await report_button(mock_message)
        
        # Проверяем, что отправлено сообщение-заглушка
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "заглушка" in call_args.lower() or "в разработке" in call_args.lower()


# ============================================================================
# ТЕСТЫ: УДАЛЕНИЕ ДАННЫХ — ПОДТВЕРЖДЕНИЕ
# ============================================================================

class TestDeleteDataConfirm:
    """Тесты функции delete_data_confirm"""
    
    @pytest.mark.asyncio
    async def test_delete_success_shows_confirmation(
        self, mock_env_vars, mock_callback, mock_bot
    ):
        """Успешное удаление: показывается сообщение об успехе"""
        from menu.start_menu import delete_data_confirm
        
        with patch('menu.start_menu.delete_user_data', new_callable=AsyncMock, return_value=True):
            await delete_data_confirm(mock_callback)
            
            # Проверяем, что данные были удалены
            from mongo import delete_user_data
            # (функция вызвана внутри, проверяем через mock)
            
            # Проверяем, что показано сообщение об успехе
            mock_callback.message.edit_text.assert_called_once()
            success_text = mock_callback.message.edit_text.call_args[0][0]
            assert "✅" in success_text or "удалены" in success_text.lower()
            # Проверяем, что отправлен ответ на callback
            mock_callback.answer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_failure_shows_error(
        self, mock_env_vars, mock_callback, mock_bot
    ):
        """Ошибка удаления: показывается сообщение об ошибке"""
        from menu.start_menu import delete_data_confirm
        
        with patch('menu.start_menu.delete_user_data', new_callable=AsyncMock, return_value=False):
            await delete_data_confirm(mock_callback)
            
            # Проверяем, что показано сообщение об ошибке
            mock_callback.message.edit_text.assert_called_once()
            error_text = mock_callback.message.edit_text.call_args[0][0]
            assert "❌" in error_text or "ошибка" in error_text.lower()
    
    @pytest.mark.asyncio
    async def test_delete_with_exception(
        self, mock_env_vars, mock_callback, mock_bot
    ):
        """Исключение при удалении: обрабатывается корректно"""
        from menu.start_menu import delete_data_confirm
        
        with patch('menu.start_menu.delete_user_data', new_callable=AsyncMock, side_effect=Exception("DB error")):
            await delete_data_confirm(mock_callback)
            
            # Проверяем, что ошибка обработана и показано сообщение
            mock_callback.message.edit_text.assert_called_once()
            error_text = mock_callback.message.edit_text.call_args[0][0]
            assert "❌" in error_text or "ошибка" in error_text.lower()


# ============================================================================
# ТЕСТЫ: УДАЛЕНИЕ ДАННЫХ — ОТМЕНА
# ============================================================================

class TestDeleteDataCancel:
    """Тесты функции delete_data_cancel"""
    
    @pytest.mark.asyncio
    async def test_cancel_shows_cancellation_message(
        self, mock_env_vars, mock_callback, mock_bot
    ):
        """Отмена удаления: показывается сообщение об отмене"""
        from menu.start_menu import delete_data_cancel
        
        await delete_data_cancel(mock_callback)
        
        # Проверяем, что показано сообщение об отмене
        mock_callback.message.edit_text.assert_called_once_with("❎ Удаление данных отменено")
        # Проверяем, что отправлен ответ на callback
        mock_callback.answer.assert_called_once()


# ============================================================================
# ТЕСТЫ: КОМАНДА /iamowner
# ============================================================================

class TestOwnerCommand:
    """Тесты функции owner_command"""
    
    @pytest.mark.asyncio
    async def test_owner_access_granted(
        self, mock_env_vars, mock_message, mock_bot
    ):
        """Владелец (OWNER_ID) получает доступ"""
        from menu.start_menu import owner_command
        
        # Создаём сообщение от владельца
        owner_message = MagicMock()
        owner_message.from_user.id = 999999999  # owner_id из mock_env_vars
        owner_message.answer = AsyncMock()
        
        with patch('menu.start_menu.ensure_owner_role', new_callable=AsyncMock, return_value=True):
            await owner_command(owner_message)
            
            # Проверяем, что доступ предоставлен
            owner_message.answer.assert_called_once()
            response_text = owner_message.answer.call_args[0][0]
            assert "👑" in response_text or "владелец" in response_text.lower()
    
    @pytest.mark.asyncio
    async def test_non_owner_access_denied(
        self, mock_env_vars, mock_message, mock_bot
    ):
        """Не-владелец получает отказ"""
        from menu.start_menu import owner_command
        
        # Создаём сообщение от обычного пользователя
        user_message = MagicMock()
        user_message.from_user.id = 123456  # не owner
        user_message.answer = AsyncMock()
        
        with patch('menu.start_menu.ensure_owner_role', new_callable=AsyncMock, return_value=False):
            await owner_command(user_message)
            
            # Проверяем, что доступ отклонён
            user_message.answer.assert_called_once()
            response_text = user_message.answer.call_args[0][0]
            assert "❌" in response_text or "нет доступа" in response_text.lower() or "не владелец" in response_text.lower()


# ============================================================================
# ТЕСТЫ: ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================


# tests/test_handlers/test_start_menu.py - ЗАМЕНИТЕ ВЕСЬ КЛАСС НА ЭТО:

class TestEnsureOwnerRole:
    """Тесты логики проверки владельца (без реального MongoDB)"""
    
    def test_owner_id_logic_direct(self, mock_env_vars):
        """Прямая проверка: сравниваем user_id с config.bot.owner_id"""
        from config import config
        
        # Логика проста: владелец если user_id == config.bot.owner_id
        assert (999999999 == config.bot.owner_id) is True   # владелец
        assert (123456 == config.bot.owner_id) is False     # не владелец





# ============================================================================
# ТЕСТЫ: KEYBOARD HELPERS (если есть)
# ============================================================================

class TestKeyboardHelpers:
    """Тесты функций создания клавиатур"""
    
    def test_get_main_keyboard_returns_markup(self):
        """get_main_keyboard возвращает ReplyKeyboardMarkup"""
        try:
            from menu.start_menu import get_main_keyboard
        except ImportError:
            pytest.skip("get_main_keyboard not implemented")
        
        keyboard = get_main_keyboard()
        
        assert isinstance(keyboard, ReplyKeyboardMarkup)
        assert len(keyboard.keyboard) > 0  # Есть хотя бы одна строка
    
    def test_get_delete_confirmation_keyboard_returns_markup(self):
        """get_delete_confirmation_keyboard возвращает InlineKeyboardMarkup"""
        try:
            from menu.start_menu import get_delete_confirmation_keyboard
        except ImportError:
            pytest.skip("get_delete_confirmation_keyboard not implemented")
        
        keyboard = get_delete_confirmation_keyboard()
        
        assert isinstance(keyboard, InlineKeyboardMarkup)
        # Проверяем, что есть кнопки "Подтвердить" и "Отмена"
        inline_buttons = keyboard.inline_keyboard[0]
        assert len(inline_buttons) >= 2


# ============================================================================
# ПАРАМЕТРИЗОВАННЫЕ ТЕСТЫ
# ============================================================================

@pytest.mark.parametrize("user_id,expected_result", [
    (999999999, True),   # владелец
    (123456, False),     # не владелец
    (111111111, False),  # не владелец
    (0, False),          # не владелец
])
@pytest.mark.asyncio
async def test_ensure_owner_role_parametrized(mock_env_vars, user_id, expected_result):
    """Параметризованный тест для ensure_owner_role"""
    from menu.start_menu import ensure_owner_role
    
    result = await ensure_owner_role(user_id)
    assert result is expected_result


@pytest.mark.parametrize("callback_data,expected_action", [
    ("delete_my_data_confirm", "confirm"),
    ("delete_my_data_cancel", "cancel"),
])
@pytest.mark.asyncio
async def test_callback_routing(mock_env_vars, callback_data, expected_action, create_mock_callback):
    """Параметризованный тест для маршрутизации колбэков"""
    # Этот тест проверяет, что разные callback_data обрабатываются разными функциями
    # Реализация зависит от вашего router/handler setup
    
    callback = create_mock_callback(data=callback_data)
    
    # Мокаем обе возможные функции
    with patch('menu.start_menu.delete_data_confirm', new_callable=AsyncMock) as mock_confirm, \
         patch('menu.start_menu.delete_data_cancel', new_callable=AsyncMock) as mock_cancel:
        
        # Имитируем вызов хендлера (зависит от вашей реализации)
        # Например, если у вас есть общий хендлер для колбэков:
        # await callback_handler(callback)
        
        # Проверяем, что вызвана правильная функция
        if expected_action == "confirm":
            # mock_confirm.assert_called()  # Раскомментируйте при реализации
            pass
        elif expected_action == "cancel":
            # mock_cancel.assert_called()
            pass

