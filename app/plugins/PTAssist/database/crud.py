import xlrd
import xlwt

from functools import reduce
from sqlalchemy import select
from random import randint, shuffle
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Iterable, Optional, List, Any, Callable

from . import models, schemas
from .. import server_config
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


class ServerConfigReader:
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
        judge_info_sheet = workbook.sheet_by_name(Config.REFEREE_INFO_SHEET_NAME)
        team_question_bank_sheet = workbook.sheet_by_name(Config.TEAM_QUESTION_BANK_SHEET_NAME)

        self.match_rule = str(software_config_sheet.cell_value(1, 1))
        self.match_type = str(software_config_sheet.cell_value(2, 1))
        self.judge_num_per_match = int(software_config_sheet.cell_value(3, 1))
        self.room_total = int(software_config_sheet.cell_value(4, 1))
        self.round_num = int(software_config_sheet.cell_value(5, 1))
        self.positive_weight = float(software_config_sheet.cell_value(6, 1))
        self.negative_weight = float(software_config_sheet.cell_value(7, 1))
        self.judge_weight = float(software_config_sheet.cell_value(8, 1))

        problem_set = problem_set_sheet.col_values(1)
        self.problem_set = {
            str(i): str(problem_set[i])
            for i in range(1, len(problem_set) + 1)
        }

        self.teams = []
        for i in range(1, team_info_sheet.nrows + 1):
            team = team_info_sheet.row_values(i)
            self.teams.append({
                "school": str(team[0]),
                "name": str(team[1]),
                "members": [{
                    "name": str(team[member]),
                    "gender": str(team[member + 1])
                } for member in range(2, len(team), 2)]
            })

        self.judges = {}
        for i in range(1, judge_info_sheet.nrows + 1):
            school_judges = judge_info_sheet.row_values(i)
            self.judges[str(school_judges[0])] = str(school_judges[1:])

        self.question_banks = []
        for i in range(1, team_question_bank_sheet.nrows + 1):
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


class CounterpartTableWriter:
    """
    用来将对局信息写入到 Excel 文件中，已经存在的文件会被覆盖
    """
    def __init__(self, path: str) -> None:
        self.path = path

    def __enter__(self) -> "CounterpartTableWriter":
        with open(self.path, "w"):
            pass

        self.workbook: xlwt.Workbook = xlwt.Workbook(encoding="utf-8")

        self.sheet_without_judge = self.workbook.add_sheet("对阵表（无裁判）")
        self.sheet_with_judge = self.workbook.add_sheet("对阵表")
        self.sheet_with_judge_and_school = self.workbook.add_sheet("对阵表含学校")

        return self

    def __exit__(self, *_) -> None:
        self.workbook.save(self.path)

    def render_table(
        self,
        sheet: xlwt.Worksheet,
        offset_row: int,
        offset_col: int,
        table: List[List[Any]],
        getter: Callable[[Any], str]
    ) -> None:
        """
        绘制一轮比赛的对局表， Any 类型的数据会作为 str 类型输出

        Args:
            sheet (xlwt.Worksheet): 工作表
            offset_row (int): 表格左上角坐标
            offset_col (int): 表格左上角坐标
            table (List[List[Any]]): 表格具体数值
            getter (Callable[[Any], str]): 如何表示表格中的数据，作为转换函数传入
        """
        if server_config is None:
            return
        sheet.write(offset_row, offset_col + 1, "正方")
        sheet.write(offset_row, offset_col + 2, "反方")
        sheet.write(offset_row, offset_col + 3, "评方")
        sheet.write(offset_row, offset_col + 4, "观方")
        for i in range(server_config.room_total):
            sheet.write(offset_row + i + 1, offset_col, f"会场{i + 1}")
        offset_row, offset_col = offset_row + 1, offset_col + 1
        for i in range(len(table)):
            for j in range(len(table[i])):
                sheet.write(offset_row + j, offset_col + i, getter(table[i][j]))


async def generate_counterpart_table(reader: ServerConfigReader) -> bool:
    """
    生成对阵表，返回是否成功
    """
    if server_config is None:
        return False

    teams = [(team.get("name"), team.get("school")) for team in server_config.teams]
    cur_row, cur_col = 0, 0
    with CounterpartTableWriter(Config.COUNTERPART_TABLE_PATH) as writer:
        for r in range(server_config.round_num):
            table: List[List[Any]] = [[], [], [], []]
            round_id = r + 1
            writer.sheet_without_judge.write(cur_row, cur_col, f"第{round_id}轮对阵表")
            writer.sheet_with_judge.write(cur_row, cur_col, f"第{round_id}轮对阵表")
            writer.sheet_with_judge_and_school.write(cur_row, cur_col, f"第{round_id}轮对阵表")
            cur_row += 1
            #? 装填
            for side in range(4):
                for i in range(server_config.room_total):
                    try:
                        table[side].append(teams[side * server_config.room_total + i])
                    except IndexError:
                        table[side].append("None")
                shuffle(table[side])
            #? 保存
            writer.render_table(writer.sheet_without_judge, cur_row, cur_col, table, lambda x: x[0])
            writer.render_table(writer.sheet_with_judge, cur_row, cur_col, table, lambda x: x[0])
            writer.render_table(writer.sheet_with_judge_and_school, cur_row, cur_col, table, lambda x: x)
            cur_row += server_config.room_total + 2
            #? 轮转队伍
            teams = teams[server_config.room_total + 1:] + teams[:server_config.room_total + 1]

    return True
