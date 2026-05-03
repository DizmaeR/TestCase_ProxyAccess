from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_activation_key,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserUpdate
from app.tasks.email import send_activation_email


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)

    async def register(self, user_data: UserCreate) -> dict:
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email уже занят")
        hashed = hash_password(user_data.password)
        activation_key = generate_activation_key()
        user = await self.user_repository.create(user_data, hashed, activation_key)
        await self.user_repository.activate(user)
        send_activation_email.delay(user_data.email, activation_key)
        return {"message": "Письмо с ключом отправлено на почту"}

    async def login(self, login_data: LoginRequest) -> TokenResponse:
        user = await self.user_repository.get_by_email(login_data.email)
        if not user:
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        if not verify_password(login_data.password, user.password):
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        token = create_access_token(user.id)
        return TokenResponse(access_token=token)

    async def change_password(self, user: User, data: UserUpdate) -> dict:
        if not verify_password(data.old_password, user.password):
            raise HTTPException(status_code=400, detail="Неверный старый пароль")

        hashed = hash_password(data.new_password)
        await self.user_repository.update(user, hashed)
        return {"message": "Пароль успешно изменён"}

    async def refresh_activation_key(self, user: User) -> dict:
        activation_key = generate_activation_key()
        await self.user_repository.update_activation_key(user, activation_key)
        return {"message": "Новый ключ отправлен на почту"}
