import hashlib

from base64 import b64encode
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Iterable, List, Dict, Optional

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


async def get_user(db: AsyncSession, user_id: int) -> Optional[models.User]:
    """
    通过用户名 id 获取用户信息
    """
    return (await db.execute(select(models.User).where(models.User.user_id == user_id))).scalars().first()


async def get_user_by_name(db: AsyncSession, name: str) -> Optional[models.User]:
    """
    通过用户名获取用户信息
    """
    return (await db.execute(select(models.User).where(models.User.name == name))).scalars().first()


async def get_user_by_identity(db: AsyncSession, identity: str) -> Optional[models.User]:
    """
    获取第一个身份为 identity 的用户（用来查找是否存在指定身份的用户）
    """
    return (await db.execute(select(models.User).where(models.User.identity == identity))).scalars().first()


async def get_last_user(db: AsyncSession) -> Optional[models.User]:
    """
    获取编号最大的那个用户信息
    """
    return (await db.execute(select(models.User).order_by(models.User.user_id.desc()))).scalars().first()


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 25565) -> Iterable[models.User]:
    """
    获取所有的用户信息
    """
    return (await db.execute(select(models.User).offset(skip).limit(limit))).scalars().all()


async def create_user(db: AsyncSession, user: schemas.UserCreate) -> Optional[models.User]:
    """
    创建一个用户信息，提供的密码会自动加密，如果无法创建，返回错误信息
    """
    if await get_user_by_name(db, user.name):
        return None
    user.token = b64encode(user.token.encode('utf-8')).decode('utf-8')
    new_user = models.User(**user.model_dump())
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    """
    删除一个用户信息，返回是否成功
    """
    if user := await get_user(db, user_id):
        return False
    await db.delete(user)
    await db.flush()
    return True


async def update_user(db: AsyncSession, user: schemas.User) -> bool:
    """
    更新一个用户信息，返回是否成功
    """
    if await get_user(db, user.user_id):
        return False
    await db.execute(update(models.User).where(models.User.user_id == user.user_id).values({
        models.User.__dict__[key]: value for key, value in user.model_dump().items() if key != 'user_id'
    }))
    return True


async def update_teaminfo(db: AsyncSession, user_id: int, leaders: str, members: str, contact: str) -> None:
    """
    更新用户团队信息
    """
    await db.execute(update(models.User).where(models.User.user_id == user_id).values({
        models.User.leaders: leaders,
        models.User.members: members,
        models.User.contact: contact
    }))
