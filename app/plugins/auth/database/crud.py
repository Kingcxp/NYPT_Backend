import xlwt
import hashlib

from random import randint
from base64 import b64encode
from functools import reduce
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Iterable, List, Dict, Optional

from . import models, schemas
from ..config import Config


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
    if members_str == "None" or members_str == "":
        return []
    members = members_str.split(' | ')
    return [from_str(member) for member in members]


def generate_password(length: int, keyring: str = "1234567890qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM") -> str:
    """生成一个随机密码

    Args:
        length (int): 密码长度
        keyring (str): 密码字符的所有备选项

    Returns:
        str: 生成的密码
    """
    return reduce(
        lambda x, y: x + y,
        [keyring[randint(0, len(keyring) - 1)] for _ in range(length)]
    )


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


async def get_all_users_by_identity(db: AsyncSession, identity: str) -> Iterable[models.User]:
    """
    获取所有身份为 identity 的用户
    """
    return (await db.execute(select(models.User).where(models.User.identity == identity))).scalars().all()


async def get_last_user(db: AsyncSession) -> Optional[models.User]:
    """
    获取编号最大的那个用户信息
    """
    return (await db.execute(select(models.User).order_by(models.User.user_id.desc()))).scalars().first()


async def get_all_users(db: AsyncSession, skip: int = 0, limit: int = 25565) -> Iterable[models.User]:
    """
    获取所有的用户信息
    """
    return (await db.execute(select(models.User).offset(skip).limit(limit).order_by(models.User.user_id))).scalars().all()


async def get_user_lottery(db: AsyncSession, user_id: int) -> int:
    """
    获取用户的抽签号
    """
    return (await db.execute(select(models.User.lottery).where(models.User.user_id == user_id))).scalars().first()


async def get_lotteries(db: AsyncSession) -> List[int, int]:
    """
    获取所有抽签号不为 -1 的用户的用户 id 和抽签号
    """
    return (await db.execute(select(models.User.user_id, models.User.lottery).where(models.User.lottery != -1))).scalars().all()


async def update_user_lottery(db: AsyncSession, user_id: int, lottery: int) -> None:
    """
    更新用户的抽签号
    """
    await db.execute(update(models.User).where(models.User.user_id == user_id).values({
        models.User.lottery: lottery
    }))
    await db.commit()
    await db.flush()


async def create_user(db: AsyncSession, user: schemas.UserCreate) -> Optional[models.User]:
    """
    创建一个用户信息，提供的密码会自动加密，如果无法创建，返回 None
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
    if (user := await get_user(db, user_id)) is None:
        return False
    await db.delete(user)
    await db.commit()
    await db.flush()
    return True


async def update_teaminfo(db: AsyncSession, user_id: int, leaders: str, members: str, school: str, contact: str, tel: str) -> None:
    """
    更新用户团队信息
    """
    await db.execute(update(models.User).where(models.User.user_id == user_id).values({
        models.User.leaders: leaders,
        models.User.members: members,
        models.User.school: school,
        models.User.contact: contact,
        models.User.tel: tel
    }))
    await db.commit()
    await db.flush()


async def generate_config_template(db: AsyncSession) -> bool:
    """
    生成配置文件模板，返回是否成功
    """
    try:
        workbook: xlwt.Workbook = xlwt.Workbook(encoding="utf-8")
        team_infos = await get_all_users_by_identity(db, "Team")
        team_infos = sorted(team_infos, key=lambda x: str(x.school))

        #? 配置表
        sheet_config: xlwt.Worksheet = workbook.add_sheet("软件配置")
        index: int = -1
        for key, value in Config.CONFIG_DEFAULT.items():
            index += 1
            sheet_config.write(index, 0, key)
            sheet_config.write(index, 1, value)

        #? 赛题信息
        sheet_info: xlwt.Worksheet = workbook.add_sheet("赛题信息")
        sheet_info.write(0, 0, "题号")
        sheet_info.write(0, 1, "题名")

        #? 队伍信息
        sheet_team: xlwt.Worksheet = workbook.add_sheet("队伍信息")
        index = -1
        for header in Config.TEAMINFO_HEADERS:
            index += 1
            sheet_team.write(0, index, header)
        index = 0
        for team in team_infos:
            index += 1
            sheet_team.write(index, 0, str(team.school))
            sheet_team.write(index, 1, str(team.name))
            members: List[Dict[str, str]] = str_decode(str(team.members))
            i = 0
            for member in members:
                i += 1
                sheet_team.write(index, i * 2, f"{i}号选手")
                sheet_team.write(index, 1 + i * 2, member["gender"])

        #? 裁判信息
        sheet_judge: xlwt.Worksheet = workbook.add_sheet("裁判信息")
        sheet_judge.write(0, 0, "学校名")
        sheet_judge.write(0, 1, "裁判们（一空一个，请不要全部放在一个单元格中）")

        #? 队伍题库
        sheet_problem_set: xlwt.Worksheet = workbook.add_sheet("队伍题库")
        sheet_problem_set.write(0, 0, "学校名")
        sheet_problem_set.write(0, 1, "队伍名")
        sheet_problem_set.write(0, 2, "题库")
        sheet_problem_set.write(0, 3, "注：此表单为队伍的题库表单，用于不采用拒题而选择直接给出题库的比赛规则。若不需要此功能则不需要填写任何内容，也不要删除此表单。题库输入规则为题号用逗号隔开，例如：1,2,10 此处逗号半角圆角都可以")
        index = 0
        for team in team_infos:
            index += 1
            sheet_problem_set.write(index, 0, str(team.school))
            sheet_problem_set.write(index, 1, str(team.name))

        workbook.save(Config.CONFIG_TEMPLATE_PATH)

        return True
    finally:
        return False
