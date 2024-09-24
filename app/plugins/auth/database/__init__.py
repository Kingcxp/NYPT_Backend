import os

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from ...utils.database import Database


database: Database = Database(
    "sqlite+aiosqlite:///",
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "auth_database.sqlite"
    )
)

async def get_db() -> AsyncGenerator[AsyncSession]:
    async with database.Session() as db:
        yield db


from .models import *
from .schemas import *
from .crud import *
