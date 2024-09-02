import os
import struct
import asyncio
import aiofiles

from datetime import datetime
from json import dumps, loads
from typing import Tuple, Dict, Any, Optional
from flask import request

from . import main, interface, Index, next_room_id
from .config import Config, WorkMode
from ...manager import suc, warn, err


async def request_data(data: Optional[Any] = None) -> Optional[Dict[str, Any]]:
    """向 PTAssist 原版服务端请求数据

    Args:
        data (Optional[Any], optional): 请求数据

    Returns:
        Dict[str, Any]: 服务端返回数据，若请求失败，返回 None
    """
    try:
        reader, writer = await asyncio.open_connection(Config.server_url, Config.server_port)
        json_data = dumps(data).encode("utf-8")
        writer.write(struct.pack('>H', len(json_data)) + json_data)
        await writer.drain()
        length_bytes = await reader.readexactly(2)
        length = struct.unpack('>H', length_bytes)[0]
        recv_data = loads((await reader.readexactly(length)).decode('utf-8'))
    except Exception as e:
        print(e)
        recv_data = None
    finally:
        writer.close()
        await writer.wait_closed()

    return recv_data


@main.route("/assist/total/room", methods=["GET"])
async def get_room_total() -> Tuple[Dict[str, Any], int]:
    """获取分会场总数

    Returns:
        Tuple[str, int]: 200 OK
    """
    suc("GET", "/assist/total/room", f"200 OK")
    return {
        "rooms": next_room_id() - 1,
        "offset": Config.room_offset
    }, 200


@main.route("/assist/total/round", methods=["GET"])
async def get_round_total() -> Tuple[str, int]:
    """获取轮次总数

    Returns:
        Tuple[str, int]: 200 OK
    """
    suc("GET", "/assist/total/round", f"200 OK")
    return {
        "rounds": Config.round_count,
        "offset": Config.round_offset
    }, 200


@main.route("/assist/roomdata", methods=["POST"])
async def roomdata() -> Tuple[Dict[str, Any], int]:
    """获取指定会场的数据

    POST 表单信息:
    {
        "roomID": int(会场编号)
        "round": int(比赛轮次)
        "token": str(会场令牌)
    }

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回 200(OK)，失败返回 400(Bad Request) 或者 404(Not Found) 或者 500(Internal Server Error)
    """
    room_id: int = int(request.json["roomID"])
    round_id: int = int(request.json["round"])
    token: str = request.json.get("token")

    try_fetch = interface.select_first("ROOMS", where={"ROOMID": ("==", room_id)})
    if try_fetch is None:
        warn("POST", "/assist/roomdata", "会场 ID 不存在！")
        return {
            "msg": "会场 ID 不存在！"
        }, 404
    fetch_result = try_fetch[Index.TOKEN.value]
    if token is not None and fetch_result != token:
        warn("POST", "/assist/roomdata", "会场密钥不匹配！")
        return {
            "msg": "会场令牌不匹配！"
        }, 400
    
    if Config.mode == WorkMode.OFFLINE:
        file_path = os.path.join(
            Config.main_folder,
            Config.round_folder_name.format(id=round_id),
            Config.room_file_name.format(id=room_id)
        )
        if not os.path.exists(file_path):
            warn("POST", "/assist/roomdata", f"[OFFLINE]: [blue]{file_path}[/blue] 未找到！")
            return {
                "msg": "服务器配置为离线模式，本地数据未找到！"
            }, 404
        else:
            try:
                suc("POST", "/assist/roomdata", f"[OFFLINE]: 读取[blue]{file_path}[/blue]...")
                async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
                    file_json = loads("".join(await file.readlines()))
            except Exception as e:
                print(e)
                err("POST", "/assist/roomdata", "本地数据读取失败！")
                return {
                    "msg": "本地数据读取失败！"
                }, 500
            suc("POST", "/assist/roomdata", "本地数据获取成功！")
            return {
                "data": file_json,
                "rule": Config.rule,
                "match_type": Config.match_type
            }, 200
    else:
        data = request_data({
            "roomID": room_id,
            "round": round_id,
            "data": None
        })
        if data is None:
            err("POST", "/assist/roomdata", "[ONLINE]: 向服务端发送请求失败！请检查配置或网络连接！")
            return {
                "msg": "服务端网络或配置异常！无法连接到 PTAssist 服务端！"
            }, 500
        suc("POST", "/assist/roomdata", "[ONLINE]: 服务器数据获取成功！")
        return {
            "data": data,
            "rule": Config.rule,
            "match_type": Config.match_type
        }, 200


@main.route("/assist/upload", methods=["POST"])
async def upload():
    """上传指定会场的数据
    
    POST 表单信息:
    {
        "roomID": int(会场编号)
        "round": int(比赛轮次)
        "token": str(会场令牌)
        "roomdata": dict(会场数据)
    }

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回 200(OK)，失败返回 400(Bad Request) 或者 404(Not Found) 或者 500(Internal Server Error)
    """
    room_id: int = int(request.json["roomID"])
    round_id: int = int(request.json["round"])
    token: str = request.json["token"]
    new_data: Dict[str, Any] = request.json["roomdata"]

    try_fetch = interface.select_first("ROOMS", where={"ROOMID": ("==", room_id)})
    if try_fetch is None:
        warn("POST", "/assist/upload", "会场 ID 不存在！")
        return {
            "msg": "会场 ID 不存在！"
        }, 404
    fetch_result = try_fetch[Index.TOKEN.value]
    if fetch_result != token:
        warn("POST", "/assist/upload", "会场密钥不匹配！")
        return {
            "msg": "会场令牌不匹配！"
        }, 400

    if Config.mode == WorkMode.OFFLINE:
        file_path = os.path.join(
            Config.temp_folder,
            Config.temp_file_name.format(
                room_id=room_id,
                round_id=round_id,
                time_stamp=datetime.now().strftime(r"%Y-%m-%d-%H-%M-%S-%f")
            )
        )
        try:
            async with aiofiles.open(file_path, "w", encoding="utf-8") as file:
                await file.write(dumps(new_data))
            suc("POST", "/assist/upload", f"[OFFLINE]: [blue]{file_path}[/blue] 保存成功！")
            return {}, 200
        except Exception as e:
            print(e)
            err("POST", "/assist/upload", f"[OFFLINE]: [blue]{file_path}[/blue] 保存失败！")
            return {
                "msg": "本地数据保存失败！"
            }, 500
    else:
        data = request_data({
            "roomID": room_id,
            "round": round_id,
            "data": new_data
        })
        if data is None:
            err("POST", "/assist/upload", "[ONLINE]: 向服务端发送请求失败！请检查配置或网络连接！")
            return {
                "msg": "服务端网络或配置异常！无法连接到 PTAssist 服务端！"
            }, 500
        suc("POST", "/assist/upload", "[ONLINE]: 服务器数据上传成功！")
        return {}, 200
