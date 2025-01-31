from sqlalchemy import Column, String, Integer

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


class Lottery(database.Base):
    """
    表: lotteries

    字段:
        team_name: 队伍名称
        lottery_id: 抽奖唯一标识
    """
    __tablename__ = "lotteries"

    team_name = Column(String(1024), primary_key=True)
    lottery_id = Column(Integer, unique=True)
