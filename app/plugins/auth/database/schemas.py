from pydantic import BaseModel


class UserBase(BaseModel):
    """
    用户信息基础单元
    """
    name: str
    identity: str
    token: str


class UserCreate(UserBase):
    """
    创建用户信息时需要提供的内容
    """
    pass


class User(UserBase):
    uid: int
    email: str
    contact: str
    leaders: str
    members: str
    award: str

    class Config:
        orm_mode = True
