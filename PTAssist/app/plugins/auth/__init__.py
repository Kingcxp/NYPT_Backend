import os
import hashlib

from flask import Blueprint

from ..utils.database.database import Interface, Article


interface = Interface(os.path.dirname(os.path.abspath(__file__)), "user_database")
"""
表: USER

字段: 
UID: 用户唯一标识
NAME: 用户名
REALNAME: 真实用户名，由后台确定，用户无法更改，登录标识，必须保证唯一，为避免输入麻烦尽量不使用中文
TOKEN: 用户密码(base64编码)
TAGS: 用户标签
IDENTITY: 用户身份
TEAMNAME: 队伍名称(身份非队伍无效)
LEADER: 领队信息(身份非队伍无效)格式：姓名 - 性别 - 手机号 - 身份证号 - 学院 - 专业 - QQ - 邮箱
MEMBER: 队员信息(身份非队伍无效)格式同领队信息，每个队员用 ' | ' 隔开
AWARD: 奖项信息(身份非队伍无效)
"""
interface.create_table("USER", {
    "UID": int,
    "NAME": str,
    "REALNAME": str,
    "TOKEN": str,
    "TAGS": str,
    "IDENTITY": str,
    "LEADER": str,
    "MEMBER": str,
    "AWARD": Article
})


def encrypter(victim: str, salt: str) -> str:
    """返回将 victim 和 salt 连接后使用 sha256 加密出的字符串

    Args:
        victim (str): 主字符串
        salt (str): 字符串加盐

    Returns:
        str: 加密结果
    """
    encrypted = hashlib.sha256(victim.encode('utf-8'))
    encrypted.update(salt.encode('utf-8'))
    return encrypted.hexdigest()


def next_uid() -> int:
    """获得数据库中下一个未被占用过的 uid

    Returns:
        int: 下一个未被占用过的 uid
    """
    uid_now: int = interface.select_scalar("USER", order_by="UID", is_desc=True)
    if uid_now == None:
        uid_now = 10000
    return uid_now + 1


from .commands import *


main = Blueprint('auth', __name__)
__blueprint__ = main
__commands__ = [
    NewUser(),
    DeleteUser(),
    AddTag(),
    RemoveTag(),
    SetIdentity(),
    SetPassword(),
    SetRealname(),
    SetName(),
    ListTeams(),
    ListVolunteers(),
    ListAll()
]


from . import auth

