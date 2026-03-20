# tests/test_handlers/test_start_menu.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_command_start_creates_user(
    mock_env_vars,
    create_mock_message,
    mock_aiogram_bot
):
    """Тест команды /start: создание пользователя"""
    # Импортируем после моков
    from menu.start_menu import command_start
    
    message = create_mock_message()
    
    # Мокаем функцию из mongo
    with patch('menu.start_menu.get_or_create_user', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = True
        
        await command_start(message, mock_aiogram_bot)
        
        mock_get.assert_called_once_with(message.from_user.id)
        message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_delete_data_confirm_success(
    mock_env_vars,
    create_mock_callback
):
    """Тест подтверждения удаления данных"""
    from menu.start_menu import delete_data_confirm
    
    callback = create_mock_callback(data="delete_my_data_confirm")
    
    with patch('menu.start_menu.delete_user_data', new_callable=AsyncMock, return_value=True):
        await delete_data_confirm(callback)
        
        callback.message.edit_text.assert_called_once()
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
    
    callback.message.edit_text.assert_called_once()
    callback.answer.assert_called_once()

