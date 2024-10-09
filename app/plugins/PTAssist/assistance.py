import os
import aiofiles

from json import loads
from pydantic import BaseModel
from fastapi import Request, Depends, Response, status, File
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from . import router
from .config import Config, data_folder
from .database import get_db, crud
from ...manager import console


@router.get("/total/room")
async def get_total_room() -> JSONResponse:
    """
    获取会场总数
    """
    if crud.server_config is None:
        return JSONResponse(content={
            "msg": "配置文件尚未准备好！请联系管理员完成配置再试！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(content={
        "rooms": crud.server_config.room_total,
        "offset": 1
    }, status_code=status.HTTP_200_OK)


@router.get("/total/round")
async def get_total_round() -> JSONResponse:
    """
    获取轮次总数
    """
    if crud.server_config is None:
        return JSONResponse(content={
            "msg": "配置文件尚未准备好！请联系管理员完成配置再试！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(content={
        "rounds": crud.server_config.round_num,
        "offset": 1
    }, status_code=status.HTTP_200_OK)


class GetRoomdataItem(BaseModel):
    # 会场编号
    roomID: int
    # 比赛轮次
    round: int
    # 会场令牌
    token: str


@router.post("/roomdata")
async def get_roomdata(item: GetRoomdataItem, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    获取指定会场的数据
    """
    if crud.server_config is None:
        return JSONResponse(content={
            "msg": "配置文件尚未准备好！请联系管理员完成配置再试！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    try_fetch = await crud.get_room(db, item.roomID)
    if try_fetch is None:
        return JSONResponse(content={
            "msg": "会场不存在！"
        }, status_code=status.HTTP_404_NOT_FOUND)
    if str(try_fetch.token) != item.token:
        return JSONResponse(content={
            "msg": "会场令牌不正确！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    file_path = os.path.join(
        Config.MAIN_FOLDER,
        Config.ROUND_FOLDER_NAME.format(id=item.round),
        Config.ROOM_FILE_NAME.format(id=item.roomID)
    )
    if not os.path.exists(file_path):
        return JSONResponse(content={
            "msg": "会场数据文件不存在！"
        }, status_code=status.HTTP_404_NOT_FOUND)
    try:
        async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
            file_json = loads("".join(await file.readlines()))
    except Exception:
        console.print_exception(show_locals=True)
        return JSONResponse(content={
            "msg": "会场数据文件解析失败！"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content={
        "data": file_json,
        "rule": crud.server_config.match_rule,
        "match_type": crud.server_config.match_type
    }, status_code=status.HTTP_200_OK)


#####################
# 用户信息后台管理 Api
#####################


@router.get("/manage/counterpart/generate")
async def generate_counterpart_table(request: Request) -> Response:
    """
    生成对阵表
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code= status.HTTP_403_FORBIDDEN)
    if not await crud.generate_counterpart_table():
        return JSONResponse(content={
            "msg": "生成失败！"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return FileResponse(
        path=Config.COUNTERPART_TABLE_PATH,
        filename="counterpart_table.xls",
        status_code=status.HTTP_200_OK
    )


@router.get("/manage/rooms/clear")
async def clear_rooms(request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    清空所有会场数据并重新生成
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code= status.HTTP_403_FORBIDDEN)
    await crud.delete_all_rooms(db)
    if crud.server_config is not None:
        await crud.create_all_rooms(db, crud.server_config.room_total)
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


@router.get("/manage/rooms/info")
async def get_rooms_info(request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    获取所有会场数据
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code= status.HTTP_403_FORBIDDEN)
    rooms = await crud.get_all_rooms(db)
    return JSONResponse(content={
        "rooms": [{
            "room_id": room.room_id,
            "token": room.token
        } for room in rooms]
    }, status_code=status.HTTP_200_OK)


@router.post("/manage/config/upload")
async def upload_config(request: Request, file: bytes = File()) -> JSONResponse:
    """
    上传配置文件到服务器
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code= status.HTTP_403_FORBIDDEN)
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    async with aiofiles.open(Config.CONFIG_PATH, "wb") as config:
        await config.write(file)
    if crud.server_config is None:
        crud.server_config = crud.ServerConfigReader(Config.CONFIG_PATH)
    try:
        crud.server_config.update()
    except Exception:
        console.print_exception(show_locals=True)
        return JSONResponse(content={
            "msg": "配置文件解析失败！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


@router.get("/manage/config/download")
async def download_config(request: Request) -> Response:
    """
    下载配置文件到客户端
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code= status.HTTP_403_FORBIDDEN)
    if not os.path.exists(Config.CONFIG_PATH):
        return JSONResponse(content={
            "msg": "配置文件不存在！"
        }, status_code=status.HTTP_404_NOT_FOUND)
    return FileResponse(
        path=Config.CONFIG_PATH,
        filename="server_config.xls",
        status_code=status.HTTP_200_OK
    )
