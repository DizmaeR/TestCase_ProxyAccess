from sqlalchemy.ext.asyncio import AsyncSession

from app.models.virtual_machine import VirtualMachine


async def create_fixtures(db: AsyncSession) -> None:
    vms = [
        VirtualMachine(
            name="proxy-1",
            host="192.168.1.1",
            port=1080,
            protocol="socks5",
            is_active=True,
        ),
        VirtualMachine(
            name="proxy-2",
            host="192.168.1.2",
            port=1080,
            protocol="socks5",
            is_active=True,
        ),
        VirtualMachine(
            name="proxy-3",
            host="192.168.1.3",
            port=8080,
            protocol="http",
            is_active=True,
        ),
    ]
    db.add_all(vms)
    await db.commit()
