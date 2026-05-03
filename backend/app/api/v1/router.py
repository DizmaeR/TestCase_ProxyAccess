from fastapi import APIRouter

from app.api.v1 import auth, profile, proxy

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(profile.router)
router.include_router(proxy.router)
