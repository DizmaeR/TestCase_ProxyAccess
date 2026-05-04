from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.virtual_machine import VirtualMachineRepository
from app.schemas.virtual_machine import VirtualMachineResponse
from app.websocket.manager import manager


class ProxyService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.vm_repo = VirtualMachineRepository(db)

    async def activate_key(self, key: str) -> VirtualMachineResponse:
        user = await self.user_repo.get_by_activation_key(key)
        if not user:
            raise HTTPException(status_code=400, detail="Неверный ключ")
        await self.user_repo.update_activation_key(user, None)  # обнуляем ключ
        # Освобождаем старые VM пользователя (если приложение закрыли без disconnect)
        for old_vm in await self.vm_repo.get_all_by_user_id(user.id):
            await self.vm_repo.release(old_vm)
        vm = await self.vm_repo.get_free()
        if not vm:
            await manager.send_status(user.id, "no_free_vms")
            raise HTTPException(status_code=503, detail="Все прокси заняты")
        await self.vm_repo.assign_user(vm, user.id)
        await manager.send_status(user.id, "connected")
        return VirtualMachineResponse.model_validate(vm)

    async def disconnect(self, user: User) -> dict:
        vms = await self.vm_repo.get_all_by_user_id(user.id)
        if not vms:
            raise HTTPException(status_code=400, detail="Нет активного подключения")
        for vm in vms:
            await self.vm_repo.release(vm)
        await manager.send_status(user.id, "disconnected")
        return {"message": "Отключено"}
