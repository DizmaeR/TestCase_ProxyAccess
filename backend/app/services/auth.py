from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    generate_activation_key,
    hash_password,
    verify_password,
)
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)

    async def register(self, user_data: UserCreate) -> dict:
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email уже занят")

        hashed = hash_password(user_data.password)
        activation_key = generate_activation_key()
        user_data.password = hashed
        await self.user_repository.create(user_data, activation_key)

        return {"message": "Письмо с ключом отправлено на почту"}

    async def login(self, login_data: LoginRequest) -> TokenResponse:
        user = await self.user_repository.get_by_email(login_data.email)
        if not user:
            raise HTTPException(status_code=401, detail="Неверный email или пароль")

        if not verify_password(login_data.password, user.password):
            raise HTTPException(status_code=401, detail="Неверный email или пароль")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Аккаунт не активирован")

        token = create_access_token(user.id)
        return TokenResponse(access_token=token)
