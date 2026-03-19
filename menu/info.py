# menu/info.py

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from config import config

info_router = Router()


# ========== КЛАВИАТУРЫ ==========

def get_info_keyboard():
    """Главная клавиатура раздела Информация"""
    builder = InlineKeyboardBuilder()
    
    builder.row(
        InlineKeyboardButton(
            text="📝 Как записывать давление",
            callback_data="info_how_to_log_bp"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📊 Как читать графики",
            callback_data="info_how_to_read_charts"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔔 Напоминания",
            callback_data="info_reminders"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="👥 Иерархия пользователей",
            callback_data="info_hierarchy"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📋 Политика конфиденциальности",
            callback_data="info_privacy"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="📞 Связь с нами",
            callback_data="info_contact"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="❓ FAQ",
            callback_data="info_faq"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад в меню",
            callback_data="main_menu"
        )
    )
    
    return builder.as_markup()


def get_back_to_info_keyboard():
    """Кнопка назад в раздел Информация"""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="info_main"
        )
    )
    return builder.as_markup()


# ========== ХЕНДЛЕРЫ ==========

@info_router.message(Command("info"))
async def info_main_handler(message: Message):
    """Главная страница раздела Информация"""
    text = (
        f"ℹ️ <b>Информация о боте</b>\n\n"
        f"👋 Приветствуем вас в CardioControl!\n\n"
        f"Этот бот поможет вам:\n"
        f"• 📝 Вести учёт артериального давления\n"
        f"• 📊 Анализировать показатели здоровья\n"
        f"• 🔔 Получать своевременные напоминания\n"
        f"• 👨‍⚕️ Делиться данными с врачом\n\n"
        f"Выберите раздел, чтобы узнать больше:"
    )
    
    await message.answer(text, reply_markup=get_info_keyboard(), parse_mode="HTML")


@info_router.callback_query(F.data == "info_main")
async def info_main_callback_handler(call: CallbackQuery):
    """Возврат к главному меню информации"""
    text = (
        f"ℹ️ <b>Информация о боте</b>\n\n"
        f"👋 Приветствуем вас в CardioControl!\n\n"
        f"Этот бот поможет вам:\n"
        f"• 📝 Вести учёт артериального давления\n"
        f"• 📊 Анализировать показатели здоровья\n"
        f"• 🔔 Получать своевременные напоминания\n"
        f"• 👨‍⚕️ Делиться данными с врачом\n\n"
        f"Выберите раздел, чтобы узнать больше:"
    )
    
    await call.message.edit_text(text, reply_markup=get_info_keyboard(), parse_mode="HTML")
    await call.answer()


@info_router.callback_query(F.data == "info_how_to_log_bp")
async def info_how_to_log_bp_handler(call: CallbackQuery):
    """Как записывать давление"""
    text = (
        f"📝 <b>Как записывать давление</b>\n\n"
        f"Есть несколько способов:\n\n"
        
        f"<b>1️⃣ Текстовый формат:</b>\n"
        f"Отправьте сообщение в формате:\n"
        f"<code>120/80 65</code>\n"
        f"где:\n"
        f"• 120 — систолическое (верхнее)\n"
        f"• 80 — диастолическое (нижнее)\n"
        f"• 65 — пульс\n\n"
        
        f"<b>2️⃣ Голосовой ввод:</b>\n"
        f"Отправьте голосовое сообщение:\n"
        f"<i>«Давление 120 на 80, пульс 65»</i>\n"
        f"Бот распознает и запишет данные.\n\n"
        
        f"<b>3️⃣ Через кнопку:</b>\n"
        f"Нажмите «📝 Записать давление» в главном меню\n"
        f"и следуйте инструкциям бота.\n\n"
        
        f"<b>💡 Советы:</b>\n"
        f"• Записывайте давление в одно и то же время\n"
        f"• Отдыхайте 5 минут перед измерением\n"
        f"• Не разговаривайте во время измерения"
    )
    
    await call.message.edit_text(text, reply_markup=get_back_to_info_keyboard(), parse_mode="HTML")
    await call.answer()


@info_router.callback_query(F.data == "info_how_to_read_charts")
async def info_how_to_read_charts_handler(call: CallbackQuery):
    """Как читать графики"""
    text = (
        f"📊 <b>Как читать графики</b>\n\n"
        
        f"<b>📈 График давления:</b>\n"
        f"• 🟩 Зелёный столбец — норма\n"
        f"• 🟨 Жёлтый столбец — пограничное\n"
        f"• 🟥 Красный столбец — выше нормы\n"
        f"• ⬛ Чёрный — диастолическое выше нормы\n"
        f"• 🔺 Красный треугольник — аритмия\n\n"
        
        f"<b>📉 График пульса:</b>\n"
        f"• 🟩 Зелёная зона — 55-70 уд/мин\n"
        f"• 🟨 Жёлтая зона — 70-90 уд/мин\n"
        f"• 🟥 Красная зона — выше 90 уд/мин\n"
        f"• 🔢 Красные цифры — выход за пределы\n\n"
        
        f"<b>📅 Периоды:</b>\n"
        f"• График строится за последние 30 дней\n"
        f"• Каждый столбец — максимальное значение за день\n"
        f"• Пунктирные линии — ваши целевые показатели\n\n"
        
        f"<b>💡 Как получить график:</b>\n"
        f"• Нажмите «📊 Мой график» в меню\n"
        f"• Или попросите врача через админ-панель"
    )
    
    await call.message.edit_text(text, reply_markup=get_back_to_info_keyboard(), parse_mode="HTML")
    await call.answer()


@info_router.callback_query(F.data == "info_reminders")
async def info_reminders_handler(call: CallbackQuery):
    """О напоминаниях"""
    text = (
        f"🔔 <b>Напоминания</b>\n\n"
        
        f"<b>Виды напоминаний:</b>\n"
        f"• 🌅 Утреннее — в 09:00\n"
        f"• 🌙 Вечернее — в 21:00\n"
        f"• 🔕 Можно отключить в настройках\n\n"
        
        f"<b>Как настроить:</b>\n"
        f"1. Нажмите «⚙️ Настройки»\n"
        f"2. Выберите «🔔 Напоминания»\n"
        f"3. Выберите удобное время\n\n"
        
        f"<b>Важно:</b>\n"
        f"• Напоминания приходят по вашему часовому поясу\n"
        f"• Можно настроить для себя или через врача\n"
        f"• Рекомендуется измерять 2 раза в день"
    )
    
    await call.message.edit_text(text, reply_markup=get_back_to_info_keyboard(), parse_mode="HTML")
    await call.answer()


@info_router.callback_query(F.data == "info_hierarchy")
async def info_hierarchy_handler(call: CallbackQuery):
    """Об иерархии пользователей"""
    text = (
        f"👥 <b>Иерархия пользователей</b>\n\n"
        
        f"<b>👑 Владелец (Owner):</b>\n"
        f"• Управляет администраторами\n"
        f"• Доступ ко всем функциям\n"
        f"• Может рассылать всем пользователям\n\n"
        
        f"<b>👥 Администратор (Admin):</b>\n"
        f"• Управляет специалистами\n"
        f"• Может добавлять врачей\n"
        f"• Рассылка своим специалистам\n\n"
        
        f"<b>👨‍⚕️ Специалист (Specialist):</b>\n"
        f"• Управляет Smart-пользователями\n"
        f"• Получает ежемесячные отчёты\n"
        f"• Видит графики пациентов\n\n"
        
        f"<b>📱 Smart-пользователь:</b>\n"
        f"• Обычный пользователь бота\n"
        f"• Может записывать давление\n"
        f"• Получает напоминания\n\n"
        
        f"<b>📊 Иерархия:</b>\n"
        f"Владелец → Админ → Специалист → Smart-пользователь"
    )
    
    await call.message.edit_text(text, reply_markup=get_back_to_info_keyboard(), parse_mode="HTML")
    await call.answer()


@info_router.callback_query(F.data == "info_privacy")
async def info_privacy_handler(call: CallbackQuery):
    """Политика конфиденциальности"""
    text = (
        f"📋 <b>Политика конфиденциальности</b>\n\n"
        
        f"<b>🔒 Защита данных:</b>\n"
        f"• Все данные хранятся в зашифрованном виде\n"
        f"• Доступ только у вас и вашего врача\n"
        f"• Мы не передаём данные третьим лицам\n\n"
        
        f"<b>📁 Какие данные собираем:</b>\n"
        f"• ID пользователя Telegram\n"
        f"• Измерения давления и пульса\n"
        f"• Настройки напоминаний\n"
        f"• Целевые показатели здоровья\n\n"
        
        f"<b>🗑️ Удаление данных:</b>\n"
        f"• Вы можете удалить все данные в любой момент\n"
        f"• Команда: /delete_data\n"
        f"• Данные удаляются безвозвратно\n\n"
        
        f"<b>📞 Вопросы:</b>\n"
        f"По вопросам конфиденциальности пишите:\n"
        f"@{config.bot.support_username or 'support'}"
    )
    
    await call.message.edit_text(text, reply_markup=get_back_to_info_keyboard(), parse_mode="HTML")
    await call.answer()


@info_router.callback_query(F.data == "info_contact")
async def info_contact_handler(call: CallbackQuery):
    """Связь с нами"""
    text = (
        f"📞 <b>Связь с нами</b>\n\n"
        
        f"<b>💬 Поддержка:</b>\n"
        f"Telegram: @{config.bot.support_username or 'support'}\n"
        f"Email: {config.bot.support_email or 'support@cardiocontrol.com'}\n\n"
        
        f"<b>🕒 Время работы:</b>\n"
        f"Пн-Пт: 09:00 - 18:00 (MSK)\n"
        f"Сб-Вс: Выходной\n\n"
        
        f"<b>📱 Социальные сети:</b>\n"
        f"• Telegram канал: @{config.bot.channel_username or 'cardiocontrol'}\n"
        f"• Website: {config.bot.website or 'https://cardiocontrol.com'}\n\n"
        
        f"<b>🐛 Сообщить об ошибке:</b>\n"
        f"Отправьте описание проблемы в поддержку\n"
        f"или используйте команду /bug_report"
    )
    
    await call.message.edit_text(text, reply_markup=get_back_to_info_keyboard(), parse_mode="HTML")
    await call.answer()


@info_router.callback_query(F.data == "info_faq")
async def info_faq_handler(call: CallbackQuery):
    """Частые вопросы"""
    text = (
        f"❓ <b>Частые вопросы (FAQ)</b>\n\n"
        
        f"<b>В: Как изменить целевые показатели?</b>\n"
        f"О: Настройки → Целевые показатели → Изменить\n\n"
        
        f"<b>В: Можно ли экспортировать данные?</b>\n"
        f"О: Да, команда /export_data отправит CSV файл\n\n"
        
        f"<b>В: Как отключить напоминания?</b>\n"
        f"О: Настройки → Напоминания → Отключить\n\n"
        
        f"<b>В: Сколько измерений нужно в день?</b>\n"
        f"О: Рекомендуется 2 раза: утром и вечером\n\n"
        
 f"<b>В: Можно ли добавить несколько врачей?</b>\n"
        f"О: Да, через админ-панель владельца\n\n"
        
        f"<b>В: Как удалить аккаунт?</b>\n"
        f"О: Команда /delete_data удалит все данные\n\n"
        
        f"<b>Ещё вопросы?</b>\n"
        f"Пишите в поддержку: @{config.bot.support_username or 'support'}"
    )
    
    await call.message.edit_text(text, reply_markup=get_back_to_info_keyboard(), parse_mode="HTML")
    await call.answer()
