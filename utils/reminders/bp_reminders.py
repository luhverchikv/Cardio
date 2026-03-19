from datetime import datetime, timedelta
from loguru import logger

from mongo import (
    get_users_with_reminders,
    get_last_bp_timestamp
)
#from logic.reminders.keyboard import edit_reminders_keyboard


async def run_bp_reminders(bot, *allowed_states: int):
    """
    bot – экземпляр Bot
    allowed_states – допустимые значения reminders (например 1, 3)
    """
    now = datetime.now()
    threshold = now - timedelta(hours=6)

    users = await get_users_with_reminders()

    for user in users:
        user_id = user["user_id"]
        reminders = user.get("reminders", 0)

        if reminders not in allowed_states:
            continue

        last_ts = await get_last_bp_timestamp(user_id)

        # Если измерений вообще не было — считаем, что напоминание нужно
        if not last_ts:
            should_notify = True
        else:
            try:
                should_notify = last_ts < threshold
            except Exception as e:
                logger.error(
                    f"Ошибка сравнения времени у пользователя {user_id}: {e}"
                )
                should_notify = True

        if not should_notify:
            continue

        try:
            await bot.send_message(
                chat_id=user_id,
                text=(
                    "⏰ Пора измерить артериальное давление.\n\n"
                    "Регулярный контроль помогает вовремя заметить изменения "
                    "и скорректировать лечение 💙"
                ),
                #reply_markup=edit_reminders_keyboard()
            )
        except Exception as e:
            logger.error(
                f"Ошибка отправки напоминания пользователю {user_id}: {e}"
            )