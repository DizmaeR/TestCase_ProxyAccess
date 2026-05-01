from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.virtual_machine import VirtualMachine


class VirtualMachineRepository:
    @staticmethod
    async def get_by_id(db: AsyncSession, vm_id: int) -> VirtualMachine | None:
        result = await db.execute(
            select(VirtualMachine).where(VirtualMachine.id == vm_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_free(db: AsyncSession) -> VirtualMachine | None:
        result = await db.execute(
            select(VirtualMachine).where(
                VirtualMachine.current_user_id.is_(None),
                VirtualMachine.is_active.is_(True),
            )
        )
        return result.scalars().first()

    @staticmethod
    async def assign_user(
        db: AsyncSession, vm: VirtualMachine, user_id: int
    ) -> VirtualMachine:
        from datetime import datetime, timezone

        vm.current_user_id = user_id
        vm.last_used_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(vm)
        return vm

    @staticmethod
    async def release(db: AsyncSession, vm: VirtualMachine) -> VirtualMachine:
        vm.current_user_id = None
        await db.commit()
        await db.refresh(vm)
        return vm
