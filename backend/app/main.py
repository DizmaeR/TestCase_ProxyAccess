from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.api.v1.router import router
from app.database.connection import SessionLocal
from app.database.fixtures import create_fixtures
from app.models.virtual_machine import VirtualMachine
from app.websocket.router import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with SessionLocal() as db:
        result = await db.execute(select(VirtualMachine))
        vms = result.scalars().all()
        if not vms:
            await create_fixtures(db)
    yield


app = FastAPI(
    title="Proxy Access API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(ws_router)


@app.get("/", include_in_schema=False)
async def root() -> RedirectResponse:
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
