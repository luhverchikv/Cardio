# utils/filters/role_filter.py
from aiogram.filters import Filter
from aiogram.types import Message
from mongo import users_collection

class RoleFilter(Filter):
    def __init__(self, role: str | list):
        # Если роль одна, превращаем ее в список
        self.roles = [role] if isinstance(role, str) else role

    async def __call__(self, message: Message):
        user_id = message.from_user.id
        user = await users_collection.find_one({"user_id": user_id})

        # Проверяем, существует ли пользователь и есть ли у него хотя бы одна из разрешенных ролей
        # 💡 ИСПРАВЛЕНИЕ: roles — это массив, а не отдельное поле role
        if not user:
            return False
            
        user_roles = user.get("roles", [])
        # Проверяем, есть ли пересечение между ролями пользователя и требуемыми ролями
        return any(role in user_roles for role in self.roles)