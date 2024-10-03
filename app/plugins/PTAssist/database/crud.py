import xlrd

from random import randint
from functools import reduce
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Iterable, Optional

from . import models, schemas
from ..config import Config


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


async def get_room(db: AsyncSession, room_id: int) -> Optional[models.Room]:
    """
    通过会场 ID 获取会场信息
    """
    return (await db.execute(select(models.Room).where(models.Room.room_id == room_id))).scalars().first()


async def get_all_rooms(db: AsyncSession, skip: int = 0, limit: int = 100) -> Iterable[models.Room]:
    """
    获取所有的房间信息
    """
    return (await db.execute(select(models.Room).offset(skip).limit(limit).order_by(models.Room.room_id))).scalars().all()


async def create_room(db: AsyncSession, room: schemas.Room) -> Optional[models.Room]:
    """
    创建一个会场
    """
    new_room = models.Room(**room.model_dump())
    db.add(new_room)
    await db.commit()
    await db.refresh(new_room)
    return new_room


async def create_all_rooms(db: AsyncSession, room_count: int) -> None:
    """
    创建指定数量的房间，已经创建过的房间会被忽略
    """
    for room_id in range(1, room_count + 1):
        if (await get_room(db, room_id)) is None:
            await create_room(db, schemas.Room(token=generate_password(8)))


async def delete_room(db: AsyncSession, room_id: int) -> bool:
    """
    删除一个会场，返回是否成功
    """
    if (room := await get_room(db, room_id)) is None:
        return False
    await db.delete(room)
    await db.commit()
    await db.flush()
    return True


class WorkbookReader:
    """
    读入 server_config.xlsx 并解析服务器配置到缓存
    """
    def __init__(self, path: str) -> None:
        self.path = path
        self.update(path)

    def update(self, path: Optional[str] = None) -> None:
        if path is None:
            path = self.path
        workbook = xlrd.open_workbook(filename=path)

        software_config_sheet = workbook.sheet_by_name(Config.SOFTWARE_CONFIG_SHEET_NAME)
        problem_set_sheet = workbook.sheet_by_name(Config.PROBLEM_SET_SHEET_NAME)
        team_info_sheet = workbook.sheet_by_name(Config.TEAM_INFO_SHEET_NAME)
        referee_info_sheet = workbook.sheet_by_name(Config.REFEREE_INFO_SHEET_NAME)
        team_question_bank_sheet = workbook.sheet_by_name(Config.TEAM_QUESTION_BANK_SHEET_NAME)

        self.match_rule = str(software_config_sheet.cell_value(1, 1))
        self.match_type = str(software_config_sheet.cell_value(2, 1))
        self.referee_num_per_match = int(software_config_sheet.cell_value(3, 1))
        self.room_total = int(software_config_sheet.cell_value(4, 1))
        self.round_num = int(software_config_sheet.cell_value(5, 1))
        self.positive_weight = float(software_config_sheet.cell_value(6, 1))
        self.negative_weight = float(software_config_sheet.cell_value(7, 1))
        self.referee_weight = float(software_config_sheet.cell_value(8, 1))

        problem_set = problem_set_sheet.col_values(1)
        self.problem_set = {
            str(i): str(problem_set[i])
            for i in range(1, len(problem_set))
        }

        self.teams = []
        for i in range(1, team_info_sheet.nrows):
            team = team_info_sheet.row_values(i)
            self.teams.append({
                "school": str(team[0]),
                "name": str(team[1]),
                **{
                    str(team[member]): str(team[member + 1])
                    for member in range(2, len(team), 2)
                }
            })

        self.referees = {}
        for i in range(1, referee_info_sheet.nrows):
            school_referees = referee_info_sheet.row_values(i)
            self.referees[str(school_referees[0])] = str(school_referees[1:])

        self.question_banks = []
        for i in range(1, team_question_bank_sheet.nrows):
            question_bank = team_question_bank_sheet.row_values(i)
            self.question_banks.append({
                "school": str(question_bank[0]),
                "name": str(question_bank[1]),
                "bank": [
                    int(question) for question in
                    str(question_bank[2]).replace("，", ",").strip().split(",")
                ]
            })

        workbook.release_resources()
