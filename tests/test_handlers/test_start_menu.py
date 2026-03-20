# tests/test_handlers/test_start_menu.py
import pytest
from unittest.mock import patch, AsyncMock
from aiogram.types import Message, CallbackQuery


@pytest.mark.asyncio
async def test_command_start_creates_user(
    mock_env_vars, 
    create_mock_message, 
    mock_aiogram_bot
):
    """Тест команды /start: создание пользователя и отправка приветствия"""
    from menu.start_menu import command_start
    
    message = create_mock_message()
    
    with patch('menu.start_menu.get_or_create_user', new_callable=AsyncMock) as mock_get_user:
        await command_start(message, mock_aiogram_bot)
        
        # Проверяем, что пользователь был создан
        mock_get_user.assert_called_once_with(message.from_user.id)
        # Проверяем отправку приветственного сообщения
        message.answer.assert_called()


@pytest.mark.asyncio
async def test_delete_data_confirm_success(
    mock_env_vars,
    create_mock_callback
):
    """Тест подтверждения удаления данных (успешный сценарий)"""
    from menu.start_menu import delete_data_confirm
    
    callback = create_mock_callback(data="delete_my_data_confirm")
    
    with patch('menu.start_menu.delete_user_data', new_callable=AsyncMock, return_value=True):
        await delete_data_confirm(callback)
        
        callback.message.edit_text.assert_called_once()
        assert "✅" in callback.message.edit_text.call_args[0][0]
        callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_delete_data_cancel(
    mock_env_vars,
    create_mock_callback
):
    """Тест отмены удаления данных"""
    from menu.start_menu import delete_data_cancel
    
    callback = create_mock_callback(data="delete_my_data_cancel")
    
    await delete_data_cancel(callback)
    
    callback.message.edit_text.assert_called_once_with("❎ Удаление данных отменено")
    callback.answer.assert_called_once()


@pytest.mark.asyncio
async def test_owner_command_success(
    mock_env_vars,
    create_mock_message
):
    """Тест команды /iamowner для владельца"""
    from menu.start_menu import owner_command
    
    message = create_mock_message(user_id=999999999)  # owner_id из моков
    
    with patch('menu.start_menu.ensure_owner_role', new_callable=AsyncMock, return_value=True):
        await owner_command(message)
        
        message.answer.assert_called_once()
        assert "👑" in message.answer.call_args[0][0]

