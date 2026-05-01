from collections.abc import AsyncGenerator

from sqlalchemy import inspect
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    def as_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self.__class__).columns}


DATABASE_URL = URL.create(
    "postgresql+asyncpg",
    username=settings.PG_USERNAME,
    password=settings.PG_PASSWORD,
    database=settings.PG_DATABASE,
    host=settings.PG_HOST,
    port=settings.PG_PORT,
)

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
