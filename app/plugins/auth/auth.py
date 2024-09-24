import time

from math import ceil
from pydantic import BaseModel
from fastapi import Request, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Optional, List
from random import randint
from functools import reduce

from . import router
from .config import Config
from .database import *
from ..utils.email import send_mail


@router.get("/id")
async def require_id(request: Request) -> JSONResponse:
    """
    返回 session 中存储的用户标识
    """
    uid = request.session.get("user_id")
    if uid is not None:
        return JSONResponse(content={
            "user_id": uid
        }, status_code=status.HTTP_200_OK)
    return JSONResponse(content={
        "msg": "您尚未登录！"
    }, status_code=status.HTTP_200_OK)


class VerifyItem(BaseModel):
    # 邮箱地址
    email: str


@router.post("/verify")
async def verify_email(item: VerifyItem, request: Request) -> JSONResponse:
    """
    生成验证码并发送到指定邮箱
    将验证码存储在 session 中
    """
    timeout: float = 30.0
    captcha: str = reduce(lambda x, y: x + y, [str(randint(0, 9)) for i in range(6)])
    if (last_time := request.session.get("last_captcha_time")) is not None and (time_left := timeout - (time.time() - last_time)) > 0.0:
        return JSONResponse(content={
            "time_left": ceil(time_left),
            "msg": f"请在 {ceil(time_left)} 秒后再发送验证码！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    if await send_mail(
        target=item.email, sender_name="NYPT",
        title="NYPT 验证码", msg=Config.verify_msg % captcha
    ):
        request.session["captcha"] = captcha
        request.session["last_captcha_time"] = time.time()
        request.session["email"] = item.email
        return JSONResponse(content={}, status_code=status.HTTP_200_OK)
    return JSONResponse(content={
        "msg": "发送失败！请检查邮箱是否输入正确！"
    }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/deprecate")
async def deprecate(request: Request) -> JSONResponse:
    """
    立即销毁 session 中的验证码
    """
    try:
        request.session.pop("captcha")
        request.session.pop("last_captcha_time")
        request.session.pop("email")
    except:
        pass
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


@router.get("/logout")
async def logout(request: Request) -> JSONResponse:
    """
    登出，清空 session 中的信息
    """
    user_id = request.session.get("user_id")
    if user_id is None:
        return JSONResponse(content={
            "msg": "您并未登录！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    request.session.clear()
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


class LoginItem(BaseModel):
    name: str
    token: str
    salt: str


@router.post("/login")
async def login(item: LoginItem, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    登录，在 session 中保存登录信息

    POST 表单信息：
    {
        "name": str(对应数据表中的name)
        "token": str(双层加密后的密码)
        "salt": str(双层加密时加入的盐)
    }
    """
    try_fetch = await get_user_by_name(db, item.name)
    fetch_token = None
    if try_fetch is not None:
        fetch_token = try_fetch.token
    else:
        return JSONResponse(content={
            "msg": "用户名不存在！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    if encrypter(str(fetch_token), item.salt) != item.token:
        return JSONResponse(content={
            "msg": "密码错误！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    request.session["user_id"] = try_fetch.uid
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


@router.get("/teaminfo/fetch")
async def team_info_fetch(request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    Team 用户获取队伍成员信息

    返回字典和 /teaminfo/save 的表单字典一致
    """
    if (user_id := request.session.get("user_id")) is None:
        return JSONResponse(content={
            "msg": "您并未登录！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    fetch_result = await get_user(db, user_id)
    if fetch_result is None:
        return JSONResponse({
            "msg": "用户不存在！"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content={
        "leaders": fetch_result.leaders,
        "members": fetch_result.members,
        "contact": fetch_result.contact
    }, status_code=status.HTTP_200_OK)


class TeaminfoSaveItem(BaseModel):
    leaders: List[Dict[str, str]]
    members: List[Dict[str, str]]
    contact: str


@router.post("/teaminfo/save")
async def team_info_save(item: TeaminfoSaveItem, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    Team 用户保存队伍成员信息

    POST 表单信息：
    {
        "leaders": str(队长信息)
        "members": str(队员信息)
        "contact": str(联系方式)
    }
    """
    if (user_id := request.session.get("user_id")) is None:
        return JSONResponse(content={
            "msg": "您尚未登录！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    fetch_result = await get_user(db, user_id)
    if fetch_result is None:
        return JSONResponse({
            "msg": "用户不存在！"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    await update_teaminfo(db, user_id, str_encode(item.leaders), str_encode(item.members), item.contact)
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


@router.get("/userdata/which")
async def fetch_userdata(which: str, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    获取已登录用户的信息

    通过路由传入字符串，表示需要获取的内容名称，总共有如下几种：
    user_id:    uid
    real_name:  name
    email:      email
    identity:   itentity
    contact:    contact
    leader:     leaders
    member:     members
    award:      award
    all:        除 token 和 award 外全部字段
    """
    if (user_id := request.session.get("user_id")) is None:
        return JSONResponse(content={
            "msg": "您尚未登录！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    fetch_result = await get_user(db, user_id)
    if fetch_result is None:
        return JSONResponse({
            "msg": "用户不存在！"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    match which:
        case "user_id":
            return JSONResponse(content={
                "user_id": fetch_result.uid
            }, status_code=status.HTTP_200_OK)
        case "real_name":
            return JSONResponse(content={
                "real_name": fetch_result.name
            }, status_code=status.HTTP_200_OK)
        case "email":
            return JSONResponse(content={
                "email": fetch_result.email
            }, status_code=status.HTTP_200_OK)
        case "identity":
            return JSONResponse(content={
                "identity": fetch_result.identity
            }, status_code=status.HTTP_200_OK)
        case "contact":
            return JSONResponse(content={
                "contact": fetch_result.contact
            }, status_code=status.HTTP_200_OK)
        case "leader":
            return JSONResponse(content={
                "leader": fetch_result.leaders
            }, status_code=status.HTTP_200_OK)
        case "member":
            return JSONResponse(content={
                "member": fetch_result.members
            }, status_code=status.HTTP_200_OK)
        case "award":
            return JSONResponse(content={
                "award": fetch_result.award
            }, status_code=status.HTTP_200_OK)
        case "all":
            return JSONResponse(content={
                "user_id": fetch_result.uid,
                "real_name": fetch_result.name,
                "email": fetch_result.email,
                "identity": fetch_result.identity,
                "contact": fetch_result.contact,
                "leader": fetch_result.leaders,
                "member": fetch_result.members
            }, status_code=status.HTTP_200_OK)
        case _:
            return JSONResponse(content={
                "msg": "未找到该存储字段！"
            }, status_code=status.HTTP_400_BAD_REQUEST)
