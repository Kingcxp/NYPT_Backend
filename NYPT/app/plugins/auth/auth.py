import time

from math import ceil
from flask import request, session
from typing import Dict, Any, Tuple, Optional, List
from random import randint
from functools import reduce

from . import main, interface, encrypter, Index, next_rid, str_decode, str_encode
from .config import Config
from ...manager import warn, suc, err
from ..utils.email.email import send_mail


@main.route("/auth/id", methods=["GET"])
async def require_id() -> Tuple[Dict[str, Any], int]:
    """返回 session 中储存的用户标识

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回用户标识，状态码 200(OK)，否则返回 400(Bad Request)
    """
    if session.get("user_id") is not None:
        suc("GET", "/auth/id", "200 OK")
        return {
            "user_id": session.get("user_id")
        }, 200
    warn("GET", "/auth/id", "400 Bad Request: 用户未登录！")
    return {
        "msg": "您尚未登录！"
    }, 400


@main.route("/auth/verify", methods=["POST"])
async def verify_email() -> Tuple[Dict[str, Any], int]:
    """生成验证码并通过邮件发送到指定邮箱
    将验证码存储在session中

    POST 表单信息:
    {
        "email": str(邮箱地址)
    }

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回 200(OK)，否则(控制同一个session间隔30秒才能发一次)返回 400(Bad Request)，若失败返回 500(Internal Server Error)
    """
    timeout: float = 30.0

    email = request.json["email"]
    captcha = reduce(lambda x, y: x + y, [str(randint(0, 9)) for i in range(6)])
    if (last_time := session.get("last_captcha_time")) is not None and (time_left := timeout - (time.time() - last_time)) > 0.0:
        warn("POST", "/auth/verify", f"400 Bad Request: 请在 {time_left} 秒后再发送验证码！")
        return {
            "time_left": ceil(time_left),
            "msg": f"请在 {ceil(time_left)} 秒后再发送验证码！"
        }, 400
    if await send_mail(
        target=email, sender_name="NYPT",
        title="验证邮件", msg=Config.verify_msg % captcha
    ):
        session["captcha"] = captcha
        session["last_captcha_time"] = time.time()
        session["email"] = email
        suc("POST", "/auth/verify", "200 OK")
        return {}, 200
    else:
        err("POST", "auth/verify", "500 Internal Server Error: 邮件发送失败！")
        return {
            "msg": "发送失败！请检查邮箱是否输入正确！"
        }, 500
    

@main.route("/auth/deprecate", methods=["GET"])
async def deprecate() -> Tuple[Dict[str, Any], int]:
    """立即销毁session中的验证码

    Returns:
        Tuple[Dict[str, Any], int]: 均返回 200(OK)，因为一定会成功
    """
    if session.get("captcha") != None:
        session.pop("captcha")
        session.pop("email")
        session.pop("last_captcha_time")
    suc("GET", "/auth/deprecate", "200 OK")
    return {}, 200
    

@main.route("/auth/logout", methods=["GET"])
async def logout() -> Tuple[Dict[str, Any], int]:
    """登出，清空 session 中的登录信息

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回状态码 200(OK)，否则返回 400(Bad Request)
    """
    if session.get("user_id") is not None:
        session.pop("user_id")
        if session.get("captcha") != None:
            session.pop("captcha")
            session.pop("email")
            session.pop("last_captcha_time")
        suc("GET", "/auth/logout", "200 OK")
        return {}, 200
    warn("GET", "/auth/logout", "400 Bad Request: 用户未登录！")
    return {
        "msg": "您并未登录！"
    }, 400


@main.route("/auth/login", methods=["POST"])
async def login() -> Tuple[Dict[str, Any], int]:
    """登录，在 session 中保存登录信息

    POST 表单信息:
    {
        "name": str(对应数据表中的 REALNAME)
        "token": str(双层加密后的密码)
        "salt": str(加密密码中加的盐)
    }

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回状态码 200(OK)，否则返回 400(Bad Request)
    """
    user_name: str = request.json["name"]
    user_token: str = request.json["token"]
    user_salt: str = request.json["salt"]
    try_fetch = interface.select_first("USER", where={"REALNAME": ("==", user_name)})
    fetch_result = None
    if try_fetch is not None:
        fetch_result = try_fetch[Index.TOKEN.value]
    if fetch_result is None:
        warn("POST", "/auth/login", f"400 Bad Request: 未找到名为 {user_name} 的用户！")
        return {
            "msg": "用户名不存在！"
        }, 400
    if encrypter(fetch_result, user_salt) != user_token:
        warn("POST", "/auth/login", "400 Bad Request: 密码错误！")
        return {
            "msg": "密码错误！"
        }, 400
    session["user_id"] = try_fetch[Index.UID.value]
    suc("POST", "/auth/login", "200 OK")
    return {}, 200


@main.route("/auth/register", methods=["POST"])
async def register() -> Tuple[Dict[str, Any], int]:
    """注册，收到注册请求并加入 PENDING_REQUEST

    POST 表单信息：
    {
        "school": str(学校名称)
        "name": str(队伍名称或志愿者名称)
        "email": str(邮箱地址)
        "tel": str(电话号码)
        "identity": str(用户身份)
        "captcha": str(验证码)
        "contact": str(联系人姓名，identity为Team时才有效)
    }

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回状态码 200(OK)，否则返回 400(Bad Request)
    """
    school: str = request.json["school"]
    name: str = request.json["name"]
    email: str = request.json["email"]
    tel: str = request.json["tel"]
    identity: str = request.json["identity"]
    captcha: str = request.json["captcha"]
    contact: str = ""
    if identity == "Team":
        contact = request.json["contact"]
    session_captcha: Optional[str] = session.get("captcha")
    session_email: Optional[str] = session.get("email")
    if session_captcha is None:
        warn("POST", "/auth/register", "400 Bad Request: 未找到验证码！")
        return {
            "msg": "未进行邮箱验证！"
        }, 400
    session.pop("captcha")
    session.pop("last_captcha_time")
    session.pop("email")
    if captcha != session_captcha:
        warn("POST", "/auth/register", "400 Bad Request: 验证码错误！")
        return {
            "msg": "验证码错误！"
        }, 400
    if email != session_email:
        warn("POST", "/auth/register", "400 Bad Request: 邮箱和验证邮箱不相符！")
        return {
            "msg": "邮箱和验证邮箱不相符！"
        }, 400
    email_result = interface.select_all("USER", where={"EMAIL": ("==", email)})
    if email_result is not None and len(email_result) > 0:
        warn("POST", "/auth/register", "400 Bad Request: 该邮箱已经存在！")
        return {
            "msg": "该邮箱已经被注册过！"
        }, 400
    rid: int = next_rid()
    interface.insert("PENDING_REQUEST",
        RID=rid,
        NAME=name,
        SCHOOL=school,
        EMAIL=email,
        TEL=tel,
        IDENTITY=identity,
        CONTACT=contact
    )
    suc("POST", "/auth/register", "200 OK")
    return {}, 200


@main.route("/auth/teaminfo/fetch", methods=["GET"])
async def team_info_fetch() -> Tuple[Dict[str, Any], int]:
    """Team 用户获取队伍成员信息

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回状态码 200(OK)，失败返回 400(Bad Request) 或 500(Internal Server Error)
        返回字典和 save 的 POST 表单一致
    """
    if (user_id := session.get("user_id")) is None:
        warn("GET", "/auth/teaminfo/fetch", "400 Bad Request: 用户未登录！")
        return {
            "msg": "您尚未登录！"
        }, 400
    fetch_result = interface.select_first("USER", where={"UID": ("==", user_id)})
    if fetch_result is None:
        warn("GET", "/auth/teaminfo/fetch", "500 Internal Server Error: 用户不存在！")
        err("GET", "/auth/teaminfo/fetch", "注意！这是重大错误，正常操作不可能出现这种情况！")
        return {
            "msg": "用户不存在！"
        }, 500
    suc("POST", "/auth/teaminfo/fetch", "200 OK")
    return {
        "leaders": str_decode(fetch_result[Index.LEADER.value]),
        "members": str_decode(fetch_result[Index.MEMBER.value]),
        "contact": fetch_result[Index.CONTACT.value],
    }, 200


@main.route("/auth/teaminfo/save", methods=["POST"])
async def team_info_save() -> Tuple[Dict[str, Any], int]:
    """Team 用户保存队伍成员信息

    POST 表单信息：
    {
        "leaders": List[Dict[str, str]](领队列表)
        "members": List[Dict[str, str]](队员列表)
        "contact": str(联系人名称)
    }

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回状态码 200(OK)，失败返回 400(Bad Request) 或 500(Internal Server Error)
    """
    leaders: List[Dict[str, str]] = request.json["leaders"]
    members: List[Dict[str, str]] = request.json["members"]
    contact: str = request.json["contact"]
    if (user_id := session.get("user_id")) is None:
        warn("POST", "/auth/teaminfo/save", "400 Bad Request: 用户未登录！")
        return {
            "msg": "您尚未登录！"
        }, 400
    fetch_result = interface.select_first("USER", where={"UID": ("==", user_id)})
    if fetch_result is None:
        warn("POST", "/auth/teaminfo/save", "500 Internal Server Error: 用户不存在！")
        err("POST", "/auth/teaminfo/save", "注意！这是重大错误，正常操作不可能出现这种情况！")
        return {
            "msg": "用户不存在！"
        }, 500
    suc("POST", "/auth/teaminfo/save", "200 OK")
    interface.update("USER", where={"UID": ("==", user_id)}, LEADER=str_encode(leaders), MEMBER=str_encode(members), CONTACT=contact)
    return {}, 200


@main.route("/auth/userdata/<string:which>", methods=["GET"])
async def fetch_userdata(which: str) -> Tuple[Dict[str, Any], int]:
    """获得已登录用户的信息

    通过路由传入：
    字符串，需要获取的内容名称，总共有如下几种：
    user_id:    UID
    user_name:  NAME
    real_name:  REALNAME
    email:      EMAIL
    tags:       TAGS
    identity:   IDENTITY
    contact:    CONTACT
    leader:     LEADER
    member:     MEMBER
    award:      AWARD
    all:        除 TOKEN 和 AWARD 外全部字段

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回用户信息及状态码 200(OK)，否则返回 400(Bad Request) 或 404(Not Found) 或 500(Internal Server Error)，视情况而定
    """
    if (user_id := session.get("user_id")) is None:
        warn("GET", "/auth/userdata", "400 Bad Request: 用户未登录！")
        return {
            "msg": "您尚未登录！"
        }, 400
    fetch_result = interface.select_first("USER", where={"UID": ("==", user_id)})
    if fetch_result is None:
        warn("GET", "/auth/userdata", "500 Internal Server Error: 用户不存在！")
        err("GET", "/auth/userdata", "注意！这是重大错误，正常操作不可能出现这种情况！")
        return {
            "msg": "用户不存在！"
        }, 500
    suc("GET", "/auth/userdata", "200 OK")
    match which:
        case "user_id":
            return {
                "user_id": fetch_result[Index.UID.value]
            }, 200
        case "user_name":
            return {
                "user_name": fetch_result[Index.NAME.value]
            }, 200
        case "real_name":
            return {
                "real_name": fetch_result[Index.REALNAME.value]
            }, 200
        case "email":
            return {
                "email": fetch_result[Index.EMAIL.value]
            }, 200
        case "tags":
            return {
                "tags": fetch_result[Index.TAGS.value]
            }, 200
        case "identity":
            return {
                "identity": fetch_result[Index.IDENTITY.value]
            }, 200
        case "contact":
            return {
                "contact": fetch_result[Index.CONTACT.value]
            }, 200
        case "leader":
            return {
                "leader": fetch_result[Index.LEADER.value]
            }, 200
        case "member":
            return {
                "member": fetch_result[Index.MEMBER.value]
            }, 200
        case "award":
            return {
                "award": fetch_result[Index.AWARD.value]
            }, 200
        case "all":
            return {
                "user_id": fetch_result[Index.UID.value],
                "user_name": fetch_result[Index.NAME.value],
                "real_name": fetch_result[Index.REALNAME.value],
                "email": fetch_result[Index.EMAIL.value],
                "tags": fetch_result[Index.TAGS.value],
                "identity": fetch_result[Index.IDENTITY.value],
                "contact": fetch_result[Index.CONTACT.value],
                "leader": fetch_result[Index.LEADER.value],
                "member": fetch_result[Index.MEMBER.value],
            }, 200
        case _:
            return {
                "msg": "未找到该存储字段！"
            }, 404
