# admin/entity_config.py

from dataclasses import dataclass
from typing import Dict


@dataclass
class EntityConfig:
    """Конфигурация для каждого типа сущности"""
    role: str                    # Роль в системе
    display_name: str            # Отображаемое имя
    connection_field: str        # Поле в БД
    id_field: str                # Ключ ID в массиве
    add_command: str             # Команда для добавления
    list_command: str            # Команда для списка
    empty_message: str           # Сообщение если пусто
    confirm_message: str         # Сообщение при подтверждении
    alias_prompt: str            # Запрос псевдонима
    alias_saved: str             # Подтверждение сохранения
    delete_message: str          # Сообщение при удалении
    broadcast_target: str        # Для рассылок


# Конфигурация всех сущностей
ENTITY_CONFIGS: Dict[str, EntityConfig] = {
    "admin": EntityConfig(
        role="admin",
        display_name="администратором",
        connection_field="connected_admins",
        id_field="admin_id",
        add_command="add_admin",
        list_command="owner",
        empty_message="👥 У вас пока нет администраторов.",
        confirm_message="Вы подтвердили роль администратора. Поздравляю! 🎉",
        alias_prompt="Теперь введите псевдоним для нового администратора.",
        alias_saved="Псевдоним '{alias}' для администратора сохранен.",
        delete_message="❌ Администратор удалён и теперь является обычным пользователем.",
        broadcast_target="admins"
    ),
    "specialist": EntityConfig(
        role="specialist",
        display_name="специалистом",
        connection_field="connected_specialists",
        id_field="specialist_id",
        add_command="add_specialist",
        list_command="admin",
        empty_message="👥 У вас пока нет специалистов.",
        confirm_message="Вы подтвердили роль специалиста. Поздравляю! 🎉",
        alias_prompt="Теперь введите псевдоним для нового специалиста.",
        alias_saved="Псевдоним '{alias}' для специалиста сохранен.",
        delete_message="❌ Специалист удалён и теперь является обычным пользователем.",
        broadcast_target="specialists"
    ),
    "smart_user": EntityConfig(
        role="smart_user",
        display_name="Smart-пользователем",
        connection_field="connected_smart_users",
        id_field="smart_user_id",
        add_command="add_smart_user",
        list_command="specialist",
        empty_message="👥 У вас пока нет Smart-пользователей.",
        confirm_message="Вы подтвердили роль Smart-пользователя. Поздравляю! 🎉",
        alias_prompt="Теперь введите псевдоним для нового Smart-пользователя.",
        alias_saved="Псевдоним '{alias}' для Smart-пользователя сохранен.",
        delete_message="❌ Smart-пользователь удалён и теперь является обычным пользователем.",
        broadcast_target="smart_users"
    ),
}
