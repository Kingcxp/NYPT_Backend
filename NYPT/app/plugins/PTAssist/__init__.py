import os

from flask import Blueprint

from ..utils.database.database import Interface


interface = Interface(os.path.dirname(os.path.abspath(__file__)), "rooms")

"""
表: ROOMS

字段:
ROOMID: 会场编号
ROOMNAME: 会场名称
TOKEN: 会场密码
"""
interface.create_table("ROOMS", {
    "ROOMID": int,
    "ROOMNAME": str,
    "TOKEN": str
})

main = Blueprint('main', __name__)
__blueprint__ = main
__commands__ = []


from . import assistance