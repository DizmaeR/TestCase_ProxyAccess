import pytest
from app.core.security import verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from httpx import AsyncClient

from tests.conftest import TestSessionLocal

pytestmark = pytest.mark.asyncio


async def test_get_profile(
    client: AsyncClient,
    registered_user: tuple[User, str],
    auth_headers: dict[str, str],
) -> None:
    user, _ = registered_user
    response = await client.get("/api/v1/profile/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user.email
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data


async def test_get_profile_unauthorized(client: AsyncClient) -> None:
    response = await client.get("/api/v1/profile/")
    assert response.status_code == 401


async def test_change_password(
    client: AsyncClient,
    registered_user: tuple[User, str],
    auth_headers: dict[str, str],
) -> None:
    user, _ = registered_user
    response = await client.put(
        "/api/v1/profile/password",
        headers=auth_headers,
        json={
            "old_password": "testpassword123",
            "new_password": "newpassword456",
            "new_password_confirm": "newpassword456",
        },
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Пароль успешно изменён"

    # Verify the password was actually updated in the DB
    async with TestSessionLocal() as session:
        updated = await UserRepository(session).get_by_id(user.id)
        assert updated is not None
        assert verify_password("newpassword456", updated.password)
        assert not verify_password("testpassword123", updated.password)


async def test_change_password_wrong_old(
    client: AsyncClient,
    registered_user: tuple[User, str],
    auth_headers: dict[str, str],
) -> None:
    response = await client.put(
        "/api/v1/profile/password",
        headers=auth_headers,
        json={
            "old_password": "wrongpassword",
            "new_password": "newpassword456",
            "new_password_confirm": "newpassword456",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Неверный старый пароль"


async def test_refresh_key(
    client: AsyncClient,
    registered_user: tuple[User, str],
    auth_headers: dict[str, str],
) -> None:
    user, old_key = registered_user
    response = await client.post("/api/v1/profile/refresh-key", headers=auth_headers)
    assert response.status_code == 200
    assert "message" in response.json()

    # Verify the key changed in the DB
    async with TestSessionLocal() as session:
        updated = await UserRepository(session).get_by_id(user.id)
        assert updated is not None
        assert updated.activation_key != old_key
        assert updated.activation_key is not None
