from typing import Optional
from pydantic import BaseModel


class UserBase(BaseModel):
    """
    用户信息基础单元
    """
    name: str
    identity: str
    token: str
    email: Optional[str]


class UserCreate(UserBase):
    """
    创建用户信息时需要提供的内容
    """
    pass


class User(UserBase):
    user_id: int
    teamname: Optional[str]
    contact: Optional[str]
    leaders: Optional[str]
    members: Optional[str]
    award: Optional[str]

    class Config:
        from_attributes = True
