import os

from fastapi import APIRouter
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from .database import database, crud
from .config import Config
from ...manager import console


server_config = None


@asynccontextmanager
async def init_db(_: APIRouter) -> AsyncGenerator[None, None]:
    global server_config
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    if os.path.exists(Config.CONFIG_PATH):
        try:
            server_config = crud.ServerConfigReader(Config.CONFIG_PATH)
            async with database.Session() as session:
                await crud.create_all_rooms(session, server_config.room_total)
        except Exception:
            console.print_exception(show_locals=True)
            server_config = None
    yield


router = APIRouter(
    prefix="/assist",
    tags=["assist"],
    lifespan=init_db
)
__router__ = router

from . import assistance
