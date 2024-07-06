import os
import socket
import struct

from json import dumps, loads
from typing import Tuple, Dict, Any, Optional
from flask import request

from . import main
from .config import Config, WorkMode
from ...manager import suc, warn, err


def request_data(data: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """向 PTAssist 原版服务端请求数据

    Args:
        data (Optional[Any], optional): 请求数据

    Returns:
        Dict[str, Any]: 服务端返回数据，若请求失败，返回 None
    """
    client = socket.socket()
    try:
        client.connect((Config.server_url, Config.server_port))
        json_data = dumps(data).encode("utf-8")
        client.send(struct.pack('>H', len(json_data)) + json_data)
        length_bytes = client.recv(2)
        length = struct.unpack('>H', length_bytes)[0]
        recv_data = loads(client.recv(length).decode('utf-8'))
    except:
        recv_data = None
    finally:
        client.close()

    return recv_data


@main.route("/assist/roomdata", methods=["POST"])
def roomdata() -> Tuple[Dict[str, Any], int]:
    """获取指定会场的数据

    POST 表单信息:
    {
        "roomID": int(会场 ID)
        "round": int(轮次 ID)
        "token": str(会场 token)
    }

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回 200(OK)，失败返回 400(Bad Request) 或者 404(Not Found) 或者 500(Internal Server Error)
    """
    room_id: int = request.json["roomID"]
    round_id: int = request.json["round"]
    token: str = request.json["token"]

    # TODO: 验证会场 token，失败返回 400 Bad Request
    
    if Config.mode == WorkMode.OFFLINE:
        file_path = \
            Config.main_folder + \
            Config.round_folder_name.format(id=round_id) + \
            Config.room_file_name.format(id=room_id)
        if os.path.exists(file_path):
            warn("POST", "/assist/roomdata", "当前模式：OFFLINE，本地数据未找到！")
            return {
                "msg": "服务器配置为离线模式，本地数据未找到！"
            }, 404
        else:
            try:
                with open(file_path, "r") as file:
                    file_json = loads("".join(file.readlines()))
            except:
                err("POST", "/assist/roomdata", "本地数据读取失败！")
                return {
                    "msg": "本地数据读取失败！"
                }, 500
            suc("POST", "/assist/roomdata", "本地数据获取成功！")
            return {
                "data": file_json
            }, 200
    else:
        data = request_data({
            "roomID": room_id,
            "round": round_id,
            "data": None
        })
        if data is None:
            err("POST", "/assist/roomdata", "向服务端发送请求失败！请检查配置或网络连接！")
            return {
                "msg": "服务端网络或配置异常！无法连接到 PTAssist！"
            }, 500
        else:
            suc("POST", "/assist/roomdata", "服务器数据获取成功！")
            return {
                "data": data
            }, 200
