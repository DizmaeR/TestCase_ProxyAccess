import pytest
from app.models.user import User
from app.models.virtual_machine import VirtualMachine
from app.repositories.virtual_machine import VirtualMachineRepository
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import TestSessionLocal

pytestmark = pytest.mark.asyncio


async def test_activate_key_success(
    client: AsyncClient,
    registered_user: tuple[User, str],
    test_vm: VirtualMachine,
) -> None:
    user, activation_key = registered_user
    response = await client.post(f"/api/v1/proxy/activate-key?key={activation_key}")
    assert response.status_code == 200
    data = response.json()
    assert data["host"] == test_vm.host
    assert data["port"] == test_vm.port
    assert data["protocol"] == test_vm.protocol

    # Verify VM is now assigned to the user
    async with TestSessionLocal() as session:
        vm = await VirtualMachineRepository(session).get_by_id(test_vm.id)
        assert vm is not None
        assert vm.current_user_id == user.id


async def test_activate_key_invalid(
    client: AsyncClient,
    test_vm: VirtualMachine,
) -> None:
    response = await client.post("/api/v1/proxy/activate-key?key=invalidkey000")
    assert response.status_code == 400
    assert response.json()["detail"] == "Неверный ключ"


async def test_activate_key_no_free_vms(
    client: AsyncClient,
    registered_user: tuple[User, str],
    test_vm: VirtualMachine,
    db_session: AsyncSession,
) -> None:
    user, activation_key = registered_user
    # Occupy the only available VM with a different user
    test_vm.current_user_id = 9999
    await db_session.commit()

    response = await client.post(f"/api/v1/proxy/activate-key?key={activation_key}")
    assert response.status_code == 503
    assert response.json()["detail"] == "Все прокси заняты"


async def test_activate_key_releases_previous_vm(
    client: AsyncClient,
    registered_user: tuple[User, str],
    db_session: AsyncSession,
) -> None:
    """Second activation releases the previously assigned VM automatically."""
    user, first_key = registered_user

    # Create two VMs so the second activation can succeed
    vm1 = VirtualMachine(
        name="vm1", host="10.0.0.1", port=1080, protocol="socks5", is_active=True
    )
    vm2 = VirtualMachine(
        name="vm2", host="10.0.0.2", port=1080, protocol="socks5", is_active=True
    )
    db_session.add_all([vm1, vm2])
    await db_session.commit()

    # First activation
    response = await client.post(f"/api/v1/proxy/activate-key?key={first_key}")
    assert response.status_code == 200

    # Give the user a second activation key
    from app.core.security import generate_activation_key

    second_key = generate_activation_key()
    user.activation_key = second_key
    await db_session.commit()

    # Second activation — old VM should be released automatically
    response = await client.post(f"/api/v1/proxy/activate-key?key={second_key}")
    assert response.status_code == 200

    async with TestSessionLocal() as session:
        repo = VirtualMachineRepository(session)
        occupied = await repo.get_all_by_user_id(user.id)
        assert len(occupied) == 1  # only one VM assigned at a time


async def test_disconnect_success(
    client: AsyncClient,
    registered_user: tuple[User, str],
    test_vm: VirtualMachine,
    auth_headers: dict[str, str],
    db_session: AsyncSession,
) -> None:
    user, _ = registered_user
    # Manually assign the VM to simulate an existing connection
    test_vm.current_user_id = user.id
    await db_session.commit()

    response = await client.post("/api/v1/proxy/disconnect", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Отключено"

    # Verify the VM is freed
    async with TestSessionLocal() as session:
        vm = await VirtualMachineRepository(session).get_by_id(test_vm.id)
        assert vm is not None
        assert vm.current_user_id is None


async def test_disconnect_no_active_connection(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post("/api/v1/proxy/disconnect", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Нет активного подключения"


async def test_disconnect_unauthorized(client: AsyncClient) -> None:
    response = await client.post("/api/v1/proxy/disconnect")
    assert response.status_code == 401
