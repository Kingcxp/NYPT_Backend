from pydantic import BaseModel


class Room(BaseModel):
    """
    会场信息
    """
    token: str


class Lottery(BaseModel):
    """
    抽奖信息
    """
    team_name: str
    lottery_id: int
