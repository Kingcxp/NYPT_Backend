from pydantic import BaseModel


class Room(BaseModel):
    """
    会场信息
    """
    token: str
