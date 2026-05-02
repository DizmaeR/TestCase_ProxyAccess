from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.repositories.user import UserRepository
from backend.app.repositories.virtual_machine import VirtualMachineRepository


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_vm_repository(
    db: AsyncSession = Depends(get_db),
) -> VirtualMachineRepository:
    return VirtualMachineRepository(db)
