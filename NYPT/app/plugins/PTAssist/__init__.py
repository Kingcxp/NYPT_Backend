import os

from flask import Blueprint
from enum import Enum
from typing import Optional

from ..utils.database.database import Interface


interface = Interface(os.path.dirname(os.path.abspath(__file__)), "rooms")

"""
表: ROOMS

字段:
ROOMID: 会场编号
TOKEN: 会场密码
"""
interface.create_table("ROOMS", {
    "ROOMID": int,
    "TOKEN": str
})

class Index(Enum):
    ROOMID   = 0
    TOKEN    = 1


def next_room_id() -> int:
    """获得数据库中下一个未被占用过的 roomid

    Returns:
        int: 下一个未被占用过的 roomid
    """
    room_now: Optional[int] = interface.select_scalar("ROOMS", order_by="ROOMID", is_desc=True)
    if room_now is None:
        room_now = 0
    return room_now + 1


main = Blueprint('main', __name__)
__blueprint__ = main
__commands__ = []


from . import assistance