from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.virtual_machine import VirtualMachine


class VirtualMachineRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, vm_id: int) -> VirtualMachine | None:
        result = await self.session.execute(
            select(VirtualMachine).where(VirtualMachine.id == vm_id)
        )
        return result.scalar_one_or_none()

    async def get_free(self) -> VirtualMachine | None:
        result = await self.session.execute(
            select(VirtualMachine).where(
                VirtualMachine.current_user_id.is_(None),
                VirtualMachine.is_active.is_(True),
            )
        )
        return result.scalars().first()

    async def assign_user(self, vm: VirtualMachine, user_id: int) -> VirtualMachine:
        vm.current_user_id = user_id
        vm.last_used_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(vm)
        return vm

    async def release(self, vm: VirtualMachine) -> VirtualMachine:
        vm.current_user_id = None
        await self.session.commit()
        await self.session.refresh(vm)
        return vm
