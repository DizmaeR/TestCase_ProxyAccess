from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: UserCreate, activation_key: str) -> User:
        new_user = User(
            email=user_data.email,
            password=user_data.password,
            activation_key=activation_key,
        )
        self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return new_user

    async def update(self, user: User, data: UserUpdate) -> User:
        user.password = data.new_password
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_activation_key(self, user: User, activation_key: str) -> User:
        user.activation_key = activation_key
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def activate(self, user: User) -> User:
        user.is_active = True
        user.activation_key = None
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_activation_key(self, activation_key: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.activation_key == activation_key)
        )
        return result.scalar_one_or_none()
