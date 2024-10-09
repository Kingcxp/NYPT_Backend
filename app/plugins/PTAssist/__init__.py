import os

from fastapi import APIRouter
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from .database import database, crud
from .config import Config
from ...manager import console


@asynccontextmanager
async def init_db(_: APIRouter) -> AsyncGenerator[None, None]:
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    if os.path.exists(Config.CONFIG_PATH):
        try:
            crud.server_config = crud.ServerConfigReader(Config.CONFIG_PATH)
            async with database.Session() as session:
                await crud.create_all_rooms(session, crud.server_config.room_total)
        except Exception:
            console.print_exception(show_locals=True)
            crud.server_config = None
    yield


router = APIRouter(
    prefix="/assist",
    tags=["assist"],
    lifespan=init_db
)
__router__ = router

from . import assistance
