import time

from math import ceil
from base64 import b64decode
from pydantic import BaseModel
from fastapi import Request, Depends, status
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Union
from random import randint
from functools import reduce

from . import router
from .config import Config
from .database import get_db, crud, schemas
from ..utils.email import send_mail


@router.get("/id")
async def require_id(request: Request) -> JSONResponse:
    """
    返回 session 中存储的用户标识
    """
    user_id = request.session.get("user_id")
    if user_id is not None:
        return JSONResponse(content={
            "user_id": user_id
        }, status_code=status.HTTP_200_OK)
    return JSONResponse(content={
        "msg": "您尚未登录！"
    }, status_code=status.HTTP_400_BAD_REQUEST)


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
    captcha: str = reduce(lambda x, y: x + y, [str(randint(0, 9)) for _ in range(6)])
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
    # 对应数据表中的name
    name: str
    # 双层加密后的密码
    token: str
    # 双层加密时加入的盐
    salt: str


@router.post("/login")
async def login(item: LoginItem, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    登录，在 session 中保存登录信息
    """
    try_fetch = await crud.get_user_by_name(db, item.name)
    fetch_token = None
    if try_fetch is not None:
        fetch_token = try_fetch.token
    else:
        return JSONResponse(content={
            "msg": "用户名不存在！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    if crud.encrypter(str(fetch_token), item.salt) != item.token:
        return JSONResponse(content={
            "msg": "密码错误！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    request.session["user_id"] = try_fetch.user_id
    request.session["identity"] = try_fetch.identity
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
    fetch_result = await crud.get_user(db, user_id)
    if fetch_result is None:
        return JSONResponse({
            "msg": "用户不存在！"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(content={
        "leaders": crud.str_decode(str(fetch_result.leaders)),
        "members": crud.str_decode(str(fetch_result.members)),
        "contact": "" if fetch_result.contact is None else fetch_result.contact
    }, status_code=status.HTTP_200_OK)


class TeaminfoSaveItem(BaseModel):
    # 队长信息
    leaders: List[Dict[str, str]]
    # 队员信息
    members: List[Dict[str, str]]
    # 联系方式
    contact: str


@router.post("/teaminfo/save")
async def team_info_save(item: TeaminfoSaveItem, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    Team 用户保存队伍成员信息
    """
    if (user_id := request.session.get("user_id")) is None:
        return JSONResponse(content={
            "msg": "您尚未登录！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    fetch_result = await crud.get_user(db, user_id)
    if fetch_result is None:
        return JSONResponse({
            "msg": "用户不存在！"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    await crud.update_teaminfo(db, user_id, crud.str_encode(item.leaders), crud.str_encode(item.members), item.contact)
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


@router.get("/userdata/{which}")
async def fetch_userdata(which: str, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    获取已登录用户的信息

    通过路由传入字符串，表示需要获取的内容名称，总共有如下几种：
    user_id:    user_id
    name:       name
    email:      email
    identity:   itentity
    teamname:   teamname
    contact:    contact
    leaders:    leaders
    members:    members
    award:      award
    all:        除 token 和 award 外全部字段
    """
    if (user_id := request.session.get("user_id")) is None:
        return JSONResponse(content={
            "msg": "您尚未登录！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    fetch_result = await crud.get_user(db, user_id)
    if fetch_result is None:
        return JSONResponse({
            "msg": "用户不存在！"
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    match which:
        case "user_id":
            return JSONResponse(content={
                "user_id": fetch_result.user_id
            }, status_code=status.HTTP_200_OK)
        case "name":
            return JSONResponse(content={
                "name": fetch_result.name
            }, status_code=status.HTTP_200_OK)
        case "email":
            return JSONResponse(content={
                "email": fetch_result.email
            }, status_code=status.HTTP_200_OK)
        case "identity":
            return JSONResponse(content={
                "identity": fetch_result.identity
            }, status_code=status.HTTP_200_OK)
        case "teamname":
            return JSONResponse(content={
                "teamname": fetch_result.teamname
            }, status_code=status.HTTP_200_OK)
        case "contact":
            return JSONResponse(content={
                "contact": fetch_result.contact
            }, status_code=status.HTTP_200_OK)
        case "leaders":
            return JSONResponse(content={
                "leaders": fetch_result.leaders
            }, status_code=status.HTTP_200_OK)
        case "members":
            return JSONResponse(content={
                "members": fetch_result.members
            }, status_code=status.HTTP_200_OK)
        case "award":
            return JSONResponse(content={
                "award": fetch_result.award
            }, status_code=status.HTTP_200_OK)
        case "all":
            return JSONResponse(content={
                "user_id": fetch_result.user_id,
                "real_name": fetch_result.name,
                "email": fetch_result.email,
                "identity": fetch_result.identity,
                "teamname": fetch_result.teamname,
                "contact": fetch_result.contact,
                "leader": fetch_result.leaders,
                "member": fetch_result.members
            }, status_code=status.HTTP_200_OK)
        case _:
            return JSONResponse(content={
                "msg": "未找到该存储字段！"
            }, status_code=status.HTTP_400_BAD_REQUEST)


#####################
# 用户信息后台管理 Api
#####################


@router.post("/manage/user/create")
async def user_create(user: schemas.UserCreate, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    创建一个用户
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code=status.HTTP_403_FORBIDDEN)
    new_user = await crud.create_user(db, user)
    if not new_user:
        return JSONResponse(content={
            "msg": "创建用户失败：用户已经存在！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    if user.email is not None:
        await send_mail(
            target=user.email, sender_name="NYPT",
            title="NYPT 用户信息", msg=Config.msg_create % (user.name, b64decode(user.token).decode('utf-8'))
        )
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


class UserCreateAllItem(BaseModel):
    # 起始编号
    begin: int
    # 终止编号
    end: int
    # 身份类型
    identity: str
    # 密码串长度
    length: int



@router.post("/manage/user/createall")
async def user_createall(item: UserCreateAllItem, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    批量创建用户，并返回用户总数
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code=status.HTTP_403_FORBIDDEN)
    for i in range(item.begin, item.end + 1):
        await crud.create_user(db, schemas.UserCreate(
            name="%s%03d" % (item.identity, i),
            identity=item.identity,
            token=crud.generate_password(item.length),
            email=None
        ))
    users = await crud.get_all_users(db)
    return JSONResponse(content={
        "total": len([user for user in users])
    }, status_code=status.HTTP_200_OK)


@router.get("/manage/user/delete/{id}")
async def user_delete(id: int, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code=status.HTTP_403_FORBIDDEN)
    stat = await crud.delete_user(db, id)
    if not stat:
        return JSONResponse(content={
            "msg": "删除用户失败：用户不存在！"
        }, status_code=status.HTTP_400_BAD_REQUEST)
    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


def identify(identity: str) -> str:
    """
    将用户类型转换为中文
    """
    if identity == "Administrator":
        return "管理员"
    elif identity == "Team":
        return "比赛队伍"
    elif identity == "VolunteerA":
        return "志愿者记分员"
    elif identity == "VolunteerB":
        return "志愿者计时员"
    return "未知身份？"


@router.get("/manage/user/getall/{page}/{limit}")
async def user_getall(page: int, limit: int, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    获取指定范围的用户信息
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code=status.HTTP_403_FORBIDDEN)
    users = await crud.get_all_users(db, (page - 1) * limit, limit)
    return JSONResponse(content={
        "users": [{
            "name": user.name,
            "user_id": user.user_id,
            "token": user.token,
            "email": user.email if user.email is not None else "未提供邮箱",
            "teamname": user.teamname,
            "leaders": user.leaders,
            "members": user.members,
            "contact": user.contact,
            "identity": identify(str(user.identity)),
            "view_token": False
        } for user in users]
    })


@router.get("/manage/user/total")
async def user_total(request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    获取用户总数，最大值 25565
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code=status.HTTP_403_FORBIDDEN)
    users = await crud.get_all_users(db)
    return JSONResponse(content={
        "total": len([user for user in users])
    }, status_code=status.HTTP_200_OK)


@router.get("/manage/user/search/{id}")
async def user_search_id(id: str, request: Request, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """
    根据用户 name 查询用户并返回
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code=status.HTTP_403_FORBIDDEN)
    user_found = await crud.get_user_by_name(db, id)
    if user_found is None:
        return JSONResponse(content={
            "msg": "未找到用户！"
        }, status_code=status.HTTP_404_NOT_FOUND)
    return JSONResponse(content={
        "name": user_found.name,
        "user_id": user_found.user_id,
        "token": user_found.token,
        "email": user_found.email if user_found.email is not None else "未提供邮箱",
        "teamname": user_found.teamname,
        "leaders": user_found.leaders,
        "members": user_found.members,
        "contact": user_found.contact,
        "identity": identify(str(user_found.identity)),
    })


@router.get("/manage/config/template")
async def get_config_template(request: Request, db: AsyncSession = Depends(get_db)) -> Union[JSONResponse, FileResponse]:
    """
    获取服务器配置模板
    """
    if request.session.get("identity") != "Administrator":
        return JSONResponse(content={
            "msg": "权限不足！"
        }, status_code=status.HTTP_403_FORBIDDEN)
    # TODO: 生成模板
    return FileResponse(
        path=Config.config_template_path,
        status_code=status.HTTP_200_OK,
    )
