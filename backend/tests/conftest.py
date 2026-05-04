from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from app.core.security import (
    create_access_token,
    generate_activation_key,
    hash_password,
)
from app.database.connection import Base, get_db
from app.main import app
from app.models.user import User
from app.models.virtual_machine import VirtualMachine
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Test database — SQLite in-memory, shared connection via StaticPool
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Replace production lifespan (connects to PostgreSQL) with a no-op
@asynccontextmanager
async def _noop_lifespan(application):
    yield


app.router.lifespan_context = _noop_lifespan

# ---------------------------------------------------------------------------
# Autouse fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def _db_tables():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def _override_dependencies():
    """Redirect every get_db call to the in-memory test DB."""
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _mock_celery(monkeypatch):
    """Prevent Celery tasks from connecting to Redis or sending real emails."""
    mock = MagicMock()
    monkeypatch.setattr("app.services.auth.send_activation_email", mock)
    return mock


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(db_session: AsyncSession) -> tuple[User, str]:
    """A pre-created, active user with a valid activation key."""
    activation_key = generate_activation_key()
    user = User(
        email="testuser@example.com",
        password=hash_password("testpassword123"),
        is_active=True,
        activation_key=activation_key,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user, activation_key


@pytest_asyncio.fixture
async def auth_headers(registered_user: tuple[User, str]) -> dict[str, str]:
    user, _ = registered_user
    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def test_vm(db_session: AsyncSession) -> VirtualMachine:
    """A free, active virtual machine."""
    vm = VirtualMachine(
        name="test-proxy",
        host="192.168.1.100",
        port=1080,
        protocol="socks5",
        is_active=True,
    )
    db_session.add(vm)
    await db_session.commit()
    await db_session.refresh(vm)
    return vm
