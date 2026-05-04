import pytest
from app.models.user import User
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    assert "message" in response.json()


async def test_register_duplicate_email(
    client: AsyncClient, registered_user: tuple[User, str]
) -> None:
    user, _ = registered_user
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": user.email, "password": "anotherpassword"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email уже занят"


async def test_login_success(
    client: AsyncClient, registered_user: tuple[User, str]
) -> None:
    user, _ = registered_user
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(
    client: AsyncClient, registered_user: tuple[User, str]
) -> None:
    user, _ = registered_user
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный email или пароль"


async def test_login_wrong_email(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный email или пароль"
