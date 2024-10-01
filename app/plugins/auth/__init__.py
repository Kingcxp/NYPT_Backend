from fastapi import APIRouter
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from .database import database, crud, schemas


@asynccontextmanager
async def init_db(_: APIRouter) -> AsyncGenerator[None, None]:
    async with database.engine.begin() as conn:
        await conn.run_sync(database.Base.metadata.create_all)
    async with database.Session() as db:
        admin = await crud.get_user_by_identity(db, "Administrator")
        if not admin:
            # 创建默认的管理员
            await crud.create_user(db, schemas.UserCreate(
                name="Admin",
                identity="Administrator",
                token="adminpass",
                email=None
            ))
    yield


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    lifespan=init_db
)
__router__ = router


from . import auth
