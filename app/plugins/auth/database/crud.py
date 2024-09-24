import hashlib

from base64 import b64encode
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from . import models, schemas


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


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """
    通过用户名 id 获取用户信息
    """
    return db.query(models.User).filter(
        models.User.uid == user_id
    ).first()


def get_user_by_name(db: Session, name: str) -> Optional[models.User]:
    """
    通过用户名获取用户信息
    """
    return db.query(models.User).filter(
        models.User.name == name
    ).first()

def get_last_user(db: Session) -> Optional[models.User]:
    """
    获取编号最大的那个用户信息
    """
    return db.query(models.User).order_by(models.User.uid.desc()).first()


def get_all_users(db: Session, skip: int = 0, limit: int = 25565) -> List[models.User]:
    """
    获取所有的用户信息
    """
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    创建一个用户信息，提供的密码会自动加密
    """
    user.token = b64encode(user.token.encode('utf-8')).decode('utf-8')
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
