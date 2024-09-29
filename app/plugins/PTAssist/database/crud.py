from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Iterable, Optional

from . import models, schemas


async def get_room(db: AsyncSession, room_id: int) -> Optional[models.Room]:
    """
    通过会场 ID 获取会场信息
    """
    return (await db.execute(select(models.Room).where(models.Room.room_id == room_id))).scalars().first()


async def get_all_rooms(db: AsyncSession, skip: int = 0, limit: int = 100) -> Iterable[models.Room]:
    """
    获取所有的房间信息
    """
    return (await db.execute(select(models.Room).offset(skip).limit(limit).order_by(models.Room.room_id))).scalars().all()


async def create_room(db: AsyncSession, room: schemas.Room) -> Optional[models.Room]:
    """
    创建一个会场
    """
    new_room = models.Room(**room.model_dump())
    db.add(new_room)
    await db.commit()
    await db.refresh(new_room)
    return new_room


async def delete_room(db: AsyncSession, room_id: int) -> bool:
    """
    删除一个会场，返回是否成功
    """
    if (room := await get_room(db, room_id)) is None:
        return False
    await db.delete(room)
    await db.commit()
    await db.flush()
    return True
