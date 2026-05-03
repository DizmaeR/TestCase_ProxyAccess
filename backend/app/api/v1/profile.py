from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service, get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth import AuthService

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


@router.put("/password")
async def change_password(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    return await auth_service.change_password(current_user, data)


@router.post("/refresh-key")
async def refresh_activation_key(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    return await auth_service.refresh_activation_key(current_user)
