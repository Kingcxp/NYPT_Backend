from sqlalchemy import Column, String, Integer, true

from . import database


class Room(database.Base):
    """
    表: rooms

    字段:
        room_id: 会场唯一标识
        token: 会场令牌
    """
    __tablename__ = "rooms"

    room_id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(1024))
