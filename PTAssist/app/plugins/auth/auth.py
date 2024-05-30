import time

from flask import request, session
from typing import Dict, List, Any, Tuple, Optional
from random import randint
from functools import reduce

from . import main, interface, encrypter, Index
from ...manager import warn, suc, err
from ..utils.email.email import send_mail


@main.route("/auth/id", methods=["GET"])
def require_id() -> Tuple[Dict[str, Any], int]:
    """返回 session 中储存的用户标识

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回用户标识，状态码 200(OK)，否则返回 400(Bad Request)
    """
    if session.get("user_id") is not None:
        suc("GET", "/auth/id", "200 OK")
        return {
            "user_id": session.get('user_id')
        }, 200
    warn("GET", "/auth/id", "400 Bad Request: 用户未登录！")
    return {
        "msg": "您尚未登录！"
    }, 400


@main.route("/auth/verify", methods=["POST"])
def verify_email() -> Tuple[Dict[str, Any], int]:
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
    email_msg = f"尊敬的用户，您好：\n\n\t您正在通过 PTAssist 平台进行邮箱验证操作，本次验证码为 {captcha} (为了保证您的账户安全性，请您尽快完成验证！)\n为了保证账户安全，请勿泄露此验证码。\n祝在之后的比赛中收获愉快！\n(这是一封自动发送的邮件，请不要回复！)\n"
    if (last_time := session.get("last_captcha_time")) is not None and (time_left := timeout - (time.time() - last_time)) > 0.0:
        warn("POST", "/auth/verify", f"400 Bad Request: 请在 {time_left} 秒后再发送验证码！")
        return {
            "time_left": {time_left},
            "msg": f"请在 {time_left} 秒后再发送验证码！"
        }, 400
    if send_mail(
        target=email, sender_name="PTAssist",
        title="验证邮件", msg=email_msg
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
def deprecate() -> Tuple[Dict[str, Any], int]:
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
def logout() -> Tuple[Dict[str, Any], int]:
    """登出，清空 session 中的登录信息

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回状态码 200(OK)，否则返回 400(Bad Request)
    """
    if session.get("user_id") is not None:
        suc("GET", "/auth/logout", "200 OK")
        return {}, 200
    warn("GET", "/auth/logout", "400 Bad Request: 用户未登录！")
    return {
        "msg": "您并未登录！"
    }, 400


@main.route("/auth/login/userpass", methods=["POST"])
def login() -> Tuple[Dict[str, Any], int]:
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
        fetch_result = try_fetch[Index.TOKEN]
    if fetch_result is None:
        warn("POST", "/auth/login/userpass", f"400 Bad Request: 未找到名为 {user_name} 的用户！")
        return {
            "msg": "用户名不存在！"
        }, 400
    if encrypter(fetch_result, user_salt) != user_token:
        warn("POST", "/auth/login/userpass", "400 Bad Request: 密码错误！")
        return {
            "msg": "密码错误！"
        }, 400
    session["user_id"] = try_fetch[Index.UID]
    suc("POST", "/auth/login/userpass", "200 OK")
    return {}, 200


@main.route("/auth/userdata/<string:which>", methods=['GET'])
def fetch_userdata(which: str) -> Tuple[Dict[str, Any], int]:
    """获得已登录用户的信息

    通过路由传入：
    字符串，需要获取的内容名称，总共有如下几种：
    user_id:    UID
    user_name:  NAME
    real_name:  REALNAME
    email:      EMAIL
    tags:       TAGS
    identity:   IDENTITY
    leader:     LEADER
    member:     MEMBER
    award:      AWARD
    all: 除 TOKEN 和 AWARD 外全部字段

    Returns:
        Tuple[Dict[str, Any], int]: 成功返回用户信息及状态码 200(OK)，否则返回 400(Bad Request) 或 404(Not Found) 或 500(Internal Server Error)，视情况而定
    """
    if user_id := session.get("user_id") is None:
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
                "user_id": fetch_result[Index.UID]
            }, 200
        case "user_name":
            return {
                "user_name": fetch_result[Index.NAME]
            }, 200
        case "real_name":
            return {
                "real_name": fetch_result[Index.REALNAME]
            }, 200
        case "email":
            return {
                "email": fetch_result[Index.EMAIL]
            }, 200
        case "tags":
            return {
                "tags": fetch_result[Index.TAGS]
            }, 200
        case "identity":
            return {
                "identity": fetch_result[Index.IDENTITY]
            }, 200
        case "leader":
            return {
                "leader": fetch_result[Index.LEADER]
            }, 200
        case "member":
            return {
                "member": fetch_result[Index.MEMBER]
            }, 200
        case "award":
            return {
                "award": fetch_result[Index.AWARD]
            }, 200
        case "all":
            return {
                "user_id": fetch_result[Index.UID],
                "user_name": fetch_result[Index.NAME],
                "real_name": fetch_result[Index.REALNAME],
                "email": fetch_result[Index.EMAIL],
                "tags": fetch_result[Index.TAGS],
                "identity": fetch_result[Index.IDENTITY],
                "leader": fetch_result[Index.LEADER],
                "member": fetch_result[Index.MEMBER],
            }, 200
        case _:
            return {
                "msg": "未找到该存储字段！"
            }, 404
