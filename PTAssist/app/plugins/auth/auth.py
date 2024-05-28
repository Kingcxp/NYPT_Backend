from flask import request, session
from typing import Dict, List, Any, Tuple, Optional
from random import randint
from functools import reduce

from . import main, interface, next_uid, encrypter
from ...manager import warn, suc, err


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


@main.route("/auth/login", methods=["POST"])
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
        fetch_result = try_fetch[3]
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
    session["user_id"] = try_fetch[0]
    suc("POST", "/auth/login", "200 OK")
    return {}, 200


@main.route("/auth/userdata/<str:which>", methods=['GET'])
def fetch_userdata(which: str) -> Tuple[Dict[str, Any], int]:
    """获得已登录用户的信息

    通过路由传入：
    字符串，需要获取的内容名称，总共有如下几种：
    user_id: UID
    user_name: NAME
    real_name: REALNAME
    tags: TAGS
    identity: IDENTITY
    leader: LEADER
    member: MEMBER
    award: AWARD
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
                "user_id": fetch_result[0]
            }, 200
        case "user_name":
            return {
                "user_name": fetch_result[1]
            }, 200
        case "real_name":
            return {
                "real_name": fetch_result[2]
            }, 200
        case "tags":
            return {
                "tags": fetch_result[4]
            }, 200
        case "identity":
            return {
                "identity": fetch_result[5]
            }, 200
        case "leader":
            return {
                "leader": fetch_result[6]
            }, 200
        case "member":
            return {
                "member": fetch_result[7]
            }, 200
        case "award":
            return {
                "award": fetch_result[8]
            }, 200
        case "all":
            return {
                "user_id": fetch_result[0],
                "user_name": fetch_result[1],
                "real_name": fetch_result[2],
                "tags": fetch_result[4],
                "identity": fetch_result[5],
                "leader": fetch_result[6],
                "member": fetch_result[7],
            }, 200
        case _:
            return {
                "msg": "未找到该存储字段！"
            }, 404
