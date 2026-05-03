from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, get_proxy_service
from app.models.user import User
from app.schemas.virtual_machine import VirtualMachineResponse
from app.services.proxy import ProxyService

router = APIRouter(prefix="/proxy", tags=["Proxy"])


@router.post("/activate-key")
async def activate_key(
    key: str,
    proxy_service: ProxyService = Depends(get_proxy_service),
) -> VirtualMachineResponse:
    return await proxy_service.activate_key(key)


@router.post("/disconnect")
async def disconnect(
    current_user: User = Depends(get_current_user),
    proxy_service: ProxyService = Depends(get_proxy_service),
) -> dict:
    return await proxy_service.disconnect(current_user)
