from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    @staticmethod
    async def create(
        db: AsyncSession, user_data: UserCreate, activation_key: str
    ) -> User:
        new_user = User(
            email=user_data.email,
            password=user_data.password,
            activation_key=activation_key,
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user

    @staticmethod
    async def update(db: AsyncSession, user: User, data: UserUpdate) -> User:
        user.password = data.new_password
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_activation_key(
        db: AsyncSession, user: User, activation_key: str
    ) -> User:
        user.activation_key = activation_key
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def activate(db: AsyncSession, user: User) -> User:
        user.is_active = True
        user.activation_key = None
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_activation_key(
        db: AsyncSession, activation_key: str
    ) -> User | None:
        result = await db.execute(
            select(User).where(User.activation_key == activation_key)
        )
        return result.scalar_one_or_none()
