import os
import hashlib

from enum import Enum
from flask import Blueprint
from typing import List, Dict

from ..utils.database.database import Interface, Article


interface = Interface(os.path.dirname(os.path.abspath(__file__)), "auth_database")

"""
表: USER

字段: 
UID: 用户唯一标识
NAME: 用户名
REALNAME: 真实用户名，由后台确定，用户无法更改，登录标识，必须保证唯一，为避免输入麻烦尽量不使用中文
EMAIL: 联系人邮箱，唯一标识
TOKEN: 用户密码(base64编码)
TAGS: 用户标签
IDENTITY: 用户身份
CONTACT: 联系人名称(身份非队伍无效)
LEADER: 领队信息(身份非队伍无效)格式：姓名 - 性别 - 手机号 - 身份证号 - 学院 - 专业 - QQ - 邮箱
MEMBER: 队员信息(身份非队伍无效)格式同领队信息，每个队员用 ' | ' 隔开
AWARD: 奖项信息(身份非队伍无效)

表: PENDING_REQUEST

字段: 
RID: 请求编号，唯一标识
NAME: 队伍名
SCHOOL: 学校名称
EMAIL: 联系人邮箱，唯一标识
TEL: 电话号码
IDENTITY: 用户身份
"""
interface.create_table("USER", {
    "UID": int,
    "NAME": str,
    "REALNAME": str,
    "EMAIL": str,
    "TOKEN": str,
    "IDENTITY": str,
    "CONTACT": str,
    "TAGS": str,
    "LEADER": str,
    "MEMBER": str,
    "AWARD": Article
})
interface.create_table("PENDING_REQUEST", {
    "RID": int,
    "NAME": str,
    "SCHOOL": str,
    "EMAIL": str,
    "TEL": str,
    "IDENTITY": str,
    "CONTACT": str
})

class Index(Enum):
    UID         = 0
    NAME        = 1
    REALNAME    = 2
    EMAIL       = 3
    TOKEN       = 4
    IDENTITY    = 5
    CONTACT     = 6
    TAGS        = 7
    LEADER      = 8
    MEMBER      = 9
    AWARD       = 10

    RID         = 0
    SCHOOL      = 2
    TEL         = 4


def encrypter(victim: str, salt: str) -> str:
    """返回将 victim 和 salt 连接后使用 sha256 加密出的字符串

    Args:
        victim (str): 主字符串
        salt (str): 字符串加盐

    Returns:
        str: 加密结果
    """
    encrypted = hashlib.sha256(victim.encode('utf-8'))
    encrypted.update(salt.encode('utf-8'))
    return encrypted.hexdigest()


def next_uid() -> int:
    """获得数据库中下一个未被占用过的 uid

    Returns:
        int: 下一个未被占用过的 uid
    """
    uid_now: int = interface.select_scalar("USER", order_by="UID", is_desc=True)
    if uid_now is None:
        uid_now = 0
    return uid_now + 1


def next_team() -> str:
    """获得数据库中下一个 team 编号

    Returns:
        int: 下一个 team 编号
    """
    team_now: Optional[List[Any]] = interface.select_first("USER", where={"IDENTITY": ("==", "Team")}, order_by="REALNAME", is_desc=True)
    team_name: str = ""
    if team_now is None:
        team_name = "team001"
    else:
        team_id: int = int(team_now[Index.REALNAME].split("team")[1]) + 1
        team_name = ("team%03d" % team_id)
    return team_name


def next_volunteer(type: str) -> str:
    """获得数据库中下一个 volunteer 编号

    Args:
        type (str): 志愿者类型

    Returns:
        int: 下一个 volunteer 编号
    """
    volunteer_now: Optional[List[Any]] = interface.select_first("USER", where={"IDENTITY": ("==", f"Volunteer{type.upper()}")}, order_by="REALNAME", is_desc=True)
    volunteer_name: str = ""
    if volunteer_now is None:
        volunteer_name = f"volunteer-{type.lower()}001"
    else:
        volunteer_id: int = int(volunteer_now[Index.REALNAME].split(f"volunteer-{type.lower()}")[1]) + 1
        volunteer_name = (f"volunteer-{type.lower()}" + "%03d" % volunteer_id)
    return volunteer_name

def next_rid() -> int:
    """获得数据库中下一个未被占用过的 rid

    Returns:
        int: 下一个未被占用过的 rid
    """
    rid_now: Optional[int] = interface.select_scalar("PENDING_REQUEST", order_by="RID", is_desc=True)
    if rid_now is None:
        rid_now = 0
    return rid_now + 1


def str_encode(members: List[Dict[str, str]]) -> str:
    """将成员列表转换为字符串

    Args:
        members (List[Dict[str, str]]): 成员列表

    Returns:
        str: 转换成的字符串，字段之间用 ' - ' 隔开，成员之间用 ' | ' 隔开
    """
    def to_str(member: Dict[str, str]) -> str:
        return f"{member['name']} - {member['gender']} - {member['mobile']} - {member['identity']} - {member['academy']} - {member['profession']} - {member['qq']} - {member['email']}"
    return " | ".join([to_str(member) for member in members])


def str_decode(members_str: str) -> List[Dict[str, str]]:
    """将字符串转换为成员列表

    Args:
        members_str (str): 成员列表字符串

    Returns:
        List[Dict[str, str]]: 转换出的成员列表
    """
    def from_str(member: str) -> Dict[str, str]:
        values = member.split(' - ')
        return {
            "name": values[0],
            "gender": values[1],
            "mobile": values[2],
            "identity": values[3],
            "academy": values[4],
            "profession": values[5],
            "qq": values[6],
            "email": values[7]
        }
    if members_str == '':
        return []
    members = members_str.split(' | ')
    return [from_str(member) for member in members]


from .commands import *


main = Blueprint('auth', __name__)
__blueprint__ = main
__commands__ = [
    NewUser(),
    DeleteUser(),
    AddTag(),
    RemoveTag(),
    SetIdentity(),
    SetPassword(),
    ShowPassword(),
    SetRealname(),
    SetName(),
    ListRequests(),
    AcceptRequest(),
    RejectRequest(),
    UserInfo(),
    ListTeams(),
    ListVolunteers(),
    ListAll()
]


from . import auth

