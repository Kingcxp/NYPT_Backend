import os
import hashlib

from flask import Blueprint

from ..utils.database.database import Interface


interface = Interface(os.path.dirname(os.path.abspath(__file__)), "user_database")
interface.create_table("USER", {
    "UID": int,
    "NAME": str,
    "TOKEN": str,
    "TAGS": str,
    "IDENTITY": str,
    "BANNED": bool
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
]


from . import auth

