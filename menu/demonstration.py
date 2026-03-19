# menu/demonstration.py
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from menu.keyboard import menu_kb
from locales.loader import LocalizedTranslator

demo_router = Router()

@demo_router.callback_query(F.data == "start_demo")
async def show_demo_sequence(call: CallbackQuery, bot: Bot, translator: LocalizedTranslator):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    # Отправляем первое сообщение с фото
    photo1 = FSInputFile("menu/IMG_0116.jpeg")
    await bot.send_photo(
        photo=photo1,
        chat_id=chat_id,
        caption=translator.get("demo-help-caption"),
    )
    
    # Небольшая пауза перед следующим сообщением
    await asyncio.sleep(5)
    
    # Отправляем второе сообщение с фото
    photo2 = FSInputFile("menu/IMG_0363.jpeg")
    await bot.send_photo(
        photo=photo2,
        chat_id=chat_id,
        caption=translator.get("demo-report-caption"),
    )
    
    # Пауза перед видео
    await asyncio.sleep(5)
    
    # Отправляем видео
    video = FSInputFile("menu/5972954607000541907.mov")
    await bot.send_video(
        video=video,
        chat_id=chat_id,
        caption=translator.get("demo-video-caption"),
    )
    
    # Пауза перед финальным сообщением
    await asyncio.sleep(1)
    
    # Отправляем финальное сообщение с клавиатурой меню
    await bot.send_message(
        chat_id=chat_id,
        text=translator.get("demo-finish"),
        reply_markup=menu_kb(translator)
    )
    
    # Удаляем колбэк, чтобы кнопка не "крутилась"
    await call.answer()