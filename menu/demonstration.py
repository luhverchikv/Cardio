# menu/demonstration.py
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from menu.keyboard import menu_kb

demo_router = Router()

@demo_router.callback_query(F.data == "start_demo")
async def show_demo_sequence(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    photo1 = FSInputFile("menu/IMG_0514.jpeg")
    await bot.send_photo(
        photo=photo1,
        chat_id=chat_id,
        caption="🎙 Ввод занимает меньше 5 секунд. Просто нажмите и удерживайте значок микрофона и скажите, например: «Артериальное давление сто двадцать на семьдесят, пульс шестьдесят пять» Бот всё распознает автоматически."
    )
    await asyncio.sleep(5)

    photo2 = FSInputFile("menu/IMG_0515.jpeg")
    await bot.send_photo(
        photo=photo2,
        chat_id=chat_id,
        caption="📊 После нескольких измерений вы увидите наглядный график. Это помогает: • заметить тенденции • понять, работает ли терапия • показать данные врачу Регулярность — это уже забота о себе"
    )
    await asyncio.sleep(5)

    video = FSInputFile("menu/7027506647285554585.mp4")
    await bot.send_video(
        video=video,
        chat_id=chat_id,
        caption="Теперь посмотрите короткое видео-демонстрацию. Нажмите и удерживайте значок микрофона и произнесите фразу, как показано в примере."
    )
    await asyncio.sleep(1)

    await bot.send_message(
        chat_id=chat_id,
        text="🎉 Теперь вы знаете, как пользоваться ботом. Вы можете: • добавить измерение • посмотреть отчёт • настроить цели Начнём?",
        reply_markup=menu_kb()
    )
    await call.answer()

