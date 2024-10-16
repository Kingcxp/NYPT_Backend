import os
import xlrd
import xlwt
import aiofiles

from math import exp
from json import dumps
from shutil import rmtree
from functools import reduce
from sqlalchemy import select, delete, table
from random import randint, shuffle, random
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Iterable, Optional, List, Any, Callable, Set, Tuple, Dict

from . import models, schemas
from ..config import Config
from ....manager import console


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


async def delete_all_rooms(db: AsyncSession) -> None:
    """
    删除所有会场
    """
    await db.execute(delete(models.Room))
    await db.commit()
    await db.flush()


class ServerConfigReader:
    """
    读入 server_config.xls 并解析服务器配置到缓存
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

        self.match_rule = str(software_config_sheet.cell_value(0, 1))
        self.match_type = str(software_config_sheet.cell_value(1, 1))
        self.judge_num_per_room = int(software_config_sheet.cell_value(2, 1))
        self.room_total = int(software_config_sheet.cell_value(3, 1))
        self.round_num = int(software_config_sheet.cell_value(4, 1))
        self.positive_weight = float(software_config_sheet.cell_value(5, 1))
        self.negative_weight = float(software_config_sheet.cell_value(6, 1))
        self.judge_weight = float(software_config_sheet.cell_value(7, 1))

        problem_set = problem_set_sheet.col_values(1)
        self.problem_set: Dict[str, str] = {
            str(i): str(problem_set[i - 1])
            for i in range(1, len(problem_set) + 1)
        }

        self.teams: List[Dict[str, Any]] = []
        self.team_by_school: Dict[str, Dict[str, Any]] = {}
        for i in range(1, team_info_sheet.nrows):
            team = team_info_sheet.row_values(i)
            members = [{
                "name": str(team[member]),
                "gender": str(team[member + 1])
            } for member in range(2, len(team), 2)]
            self.teams.append({
                "school": str(team[0]),
                "name": str(team[1]),
                "members": members
            })
            self.team_by_school[str(team[0])] = {
                "name": str(team[1]),
                "members": members
            }

        self.judges: Dict[str, List[str]] = {}
        for i in range(1, judge_info_sheet.nrows):
            school_judges = judge_info_sheet.row_values(i)
            self.judges[str(school_judges[0])] = [str(judge) for judge in school_judges[1:] if str(judge).strip() != ""]

        self.question_banks: Dict[str, Dict[str, Any]] = {}
        for i in range(1, team_question_bank_sheet.nrows):
            question_bank = team_question_bank_sheet.row_values(i)
            self.question_banks[str(question_bank[1])] = {
                "school": str(question_bank[0]),
                "bank": [
                    question.strip() for question in
                    str(question_bank[2]).replace("，", ",").strip().split(",")
                ]
            }

        workbook.release_resources()


server_config: Optional[ServerConfigReader] = None


class CounterpartTableWriter:
    """
    用来将对局信息写入到 Excel 文件中，已经存在的文件会被覆盖
    """
    def __init__(self, path: str) -> None:
        self.path = path
        with open(self.path, "w"):
            pass

        self.workbook: xlwt.Workbook = xlwt.Workbook(encoding="utf-8")

        self.sheet_without_judge: xlwt.Worksheet = self.workbook.add_sheet("对阵表（无裁判）")
        self.sheet_with_judge: xlwt.Worksheet = self.workbook.add_sheet("对阵表")
        self.sheet_with_judge_and_school: xlwt.Worksheet = self.workbook.add_sheet("对阵表含学校")

    def on_exit(self) -> None:
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

    def render_judges(
        self,
        judge_tables: List[List[List[Tuple[str, str]]]],
    ) -> None:
        """
        绘制裁判信息

        Args:
            judge_tables (List[List[List[Tuple[str, str]]]]): 裁判信息
        """
        if server_config is None:
            return
        row = 1
        for table in judge_tables:
            self.sheet_with_judge.write(row, 5, "裁判们")
            self.sheet_with_judge_and_school.write(row, 5, "裁判们")
            row += 1
            for i in range(len(table)):
                for j in range(len(table[i])):
                    self.sheet_with_judge.write(row + i, 5 + j, str(table[i][j][0]))
                    self.sheet_with_judge_and_school.write(row + i, 5 + j, str(table[i][j]))
            row += server_config.room_total + 2



def select_one(count_list: List[int]) -> int:
    """
    输入权重列表，返回抽签得到的值的索引
    """
    probability_list: List[float] = [
        exp(-float(count)) for count in count_list
    ]
    s: float = sum(probability_list)
    probability_list = [p / s for p in probability_list]

    val: float = random()
    tot = 0
    for index in range(len(probability_list)):
        if tot >= val:
            return index
        else:
            tot += probability_list[index]
    return len(probability_list) - 1


def try_generate_judges(
    tables: List[List[List[Tuple[str, str]]]],
    times: int = 1000
) -> Tuple[List[List[List[Tuple[str, str]]]], bool]:
    """
    尝试生成裁判表，返回是否成功
    """
    if server_config is None:
        return [], False

    # 来个 time 次先试试
    for _ in range(times):
        do_continue = False
        # 总轮次裁判序号: 已上场次数的字典，用于均衡全部轮次各裁判的上场次数
        judge_used_map: Dict[str, int] = {}
        for school in server_config.judges:
            for judge in server_config.judges[school]:
                judge_used_map[judge] = 0
        # 本次所有生成的裁判表
        judge_tables: List[List[List[Tuple[str, str]]]] = []
        for round_id in range(server_config.round_num):
            team_table = tables[round_id]
            # 该轮生成的裁判表
            judge_table: List[List[Tuple[str, str]]] = []
            # 本轮次已上场裁判，用于避免一个老师在一轮中在多个会场出现
            judge_used_list: List[str] = []
            # 本轮次已使用学校
            school_used_list: List[str] = []
            for room in range(server_config.room_total):
                # 储存本会场所用裁判
                judge_table_room: List[Tuple[str, str]] = []
                # 参赛队伍学校名称列表
                team_school_names: Set = set()
                for side in range(4):
                    if team_table[side][room][1] != "None":
                        team_school_names.add(team_table[side][room][1])
                # 可用裁判的选择规则是 不与参赛队员学校相同，且未当过本轮裁判
                avail_judge_list: List[Tuple[str, str]] = reduce(
                    lambda x, y: x + y, [
                        list(filter(
                            lambda x: x[1] not in team_school_names and x[0] not in judge_used_list,
                            [(j, school) for j in server_config.judges[school]]
                        )) for school in server_config.judges.keys()
                    ]
                )
                if len(avail_judge_list) < server_config.judge_num_per_room:
                    do_continue = True
                    break
                for _ in range(server_config.judge_num_per_room):
                    # 若之前选过同学校的老师，则人为地将其下次被选中的概率降低
                    selected_index = select_one([
                        judge_used_map[j] if s not in school_used_list else judge_used_map[j] + 5
                        for j, s in avail_judge_list
                    ])
                    judge_table_room.append(avail_judge_list[selected_index])
                    judge_used_list.append(avail_judge_list[selected_index][0])
                    school_used_list.append(avail_judge_list[selected_index][1])
                    judge_used_map[avail_judge_list[selected_index][0]] += 1
                    avail_judge_list.pop(selected_index)
                judge_table.append(judge_table_room)
            if do_continue:
                break
            judge_tables.append(judge_table)
        if not do_continue:
            return judge_tables, True
    return [], False


def try_generate_judges_allow_school(
    tables: List[List[List[Tuple[str, str]]]]
) -> Tuple[List[List[List[Tuple[str, str]]]], bool]:
    """
    生成裁判表并允许同校裁判，返回是否成功
    """
    if server_config is None:
        return [], False

    damm_it = False
    judge_tables: List[List[List[Tuple[str, str]]]] = []
    judge_used_map: Dict[str, int] = {}
    for school in server_config.judges:
        for judge in server_config.judges[school]:
            judge_used_map[judge] = 0
    for round_id in range(server_config.round_num):
        team_table = tables[round_id]
        # 该轮生成的裁判表
        judge_table: List[List[Tuple[str, str]]] = []
        # 本轮次已上场裁判，用于避免一个老师在一轮中在多个会场出现
        judge_used_list: List[str] = []
        # 本轮次已使用学校
        school_used_list: List[str] = []
        for room in range(server_config.room_total):
            # 储存本会场所用裁判
            judge_table_room: List[Tuple[str, str]] = []
            # 参赛队伍学校名称列表
            team_school_names: Set = set()
            for side in range(4):
                if team_table[side][room][1] != "None":
                    team_school_names.add(team_table[side][room][1])
            # 可用裁判的选择规则是 未当过本轮裁判
            avail_judge_list: List[Tuple[str, str]] = reduce(
                lambda x, y: x + y,
                filter(
                    lambda x: x[0] not in judge_used_list, [
                        [(j, school) for j in server_config.judges[school]]
                        for school in server_config.judges.keys()
                    ]
                )
            )
            if len(avail_judge_list) < server_config.judge_num_per_room:
                damm_it = True
                break
            for _ in range(server_config.judge_num_per_room):
                # 若之前选过同学校的老师，则人为地将其下次被选中的概率降低
                selected_index = select_one([
                    judge_used_map[j] if s not in school_used_list else judge_used_map[j] + 5
                    for j, s in avail_judge_list
                ])
                judge_table_room.append(avail_judge_list[selected_index])
                judge_used_list.append(avail_judge_list[selected_index][0])
                school_used_list.append(avail_judge_list[selected_index][1])
                judge_used_map[avail_judge_list[selected_index][0]] += 1
                avail_judge_list.pop(selected_index)
            judge_table.append(judge_table_room)
        if damm_it:
            break
        judge_tables.append(judge_table)
    return judge_tables, not damm_it


def generate_judges(
    tables: List[List[List[Tuple[str, str]]]]
) -> List[List[List[Tuple[str, str]]]]:
    """
    生成裁判表，允许同学校和不同会场重复裁判
    """
    if server_config is None:
        return []

    judge_tables: List[List[List[Tuple[str, str]]]] = []
    judge_used_map: Dict[str, int] = {}
    for school in server_config.judges:
        for judge in server_config.judges[school]:
            judge_used_map[judge] = 0
    for round_id in range(server_config.round_num):
        team_table = tables[round_id]
        # 该轮生成的裁判表
        judge_table: List[List[Tuple[str, str]]] = []
        # 本轮次已上场裁判，用于避免一个老师在一轮中在多个会场出现
        judge_used_list: List[str] = []
        # 本轮次已使用学校
        school_used_list: List[str] = []
        for room in range(server_config.room_total):
            # 储存本会场所用裁判
            judge_table_room: List[Tuple[str, str]] = []
            # 参赛队伍学校名称列表
            team_school_names: Set = set()
            for side in range(4):
                if team_table[side][room][1] != "None":
                    team_school_names.add(team_table[side][room][1])
            # 可用裁判的选择规则是 是裁判就行
            avail_judge_list: List[Tuple[str, str]] = reduce(
                lambda x, y: x + y, [
                    [(j, school) for j in server_config.judges[school]]
                    for school in server_config.judges.keys()
                ]
            )
            for _ in range(server_config.judge_num_per_room):
                # 若之前选过同学校的老师，则人为地将其下次被选中的概率降低
                selected_index = select_one([
                    judge_used_map[j] if s not in school_used_list else judge_used_map[j] + 5
                    for j, s in avail_judge_list
                ])
                judge_table_room.append(avail_judge_list[selected_index])
                judge_used_list.append(avail_judge_list[selected_index][0])
                school_used_list.append(avail_judge_list[selected_index][1])
                judge_used_map[avail_judge_list[selected_index][0]] += 1
                avail_judge_list.pop(selected_index)
            judge_table.append(judge_table_room)
        judge_tables.append(judge_table)
    return judge_tables


async def save_json(
    dic: Dict[str, Any],
    path: str
) -> bool:
    """
    将字典保存为文件，返回是否成功
    """
    try:
        async with aiofiles.open(path, "w", encoding="utf-8") as file:
            await file.write(dumps(dic))
        return True
    except Exception:
        console.print_exception(show_locals=True)
        return False


async def generate_room_data(tables: List[List[List[Tuple[str, str]]]]) -> bool:
    """
    生成房间数据，返回是否成功
    """
    if server_config is None:
        return False

    try:
        if not os.path.exists(Config.MAIN_FOLDER):
            os.mkdir(Config.MAIN_FOLDER)
        for r in range(server_config.round_num):
            # 创建轮次文件夹
            folder = os.path.join(Config.MAIN_FOLDER, Config.ROUND_FOLDER_NAME.format(id=r+1))
            if os.path.exists(folder):
                rmtree(folder)
            os.mkdir(folder)

            for room in range(server_config.room_total):
                room_json: Dict[str, Any] = {
                    "teamDataList": [],
                    "questionMap": []
                }
                for side in range(4):
                    room_json["teamDataList"].append({
                        "name": tables[r][side][room][0],
                        "school": tables[r][side][room][1],
                        "playerDataList": [],
                        "recordDataList": []
                    })
                    for player in server_config.team_by_school[tables[r][side][room][1]]["members"]:
                        room_json["teamDataList"]["playerDataList"].append(player)
                    for question in server_config.problem_set.keys():
                        if question in server_config.question_banks[tables[r][side][room][0]]["bank"]:
                            continue
                        room_json["teamDataList"][side]["recordDataList"].append({
                            "round": 0,
                            "phase": 0,
                            "roomID": 0,
                            "questionID": question,
                            "masterID": 0,
                            "role": "B",
                            "score": 0.0,
                            "weight": 0.0
                        })
                await save_json(room_json, os.path.join(folder, Config.ROOM_FILE_NAME.format(id=room+1)))
        return True
    except Exception:
        console.print_exception(show_locals=True)
        return False


async def generate_counterpart_table() -> bool:
    """
    生成对阵表，返回是否成功
    """
    if server_config is None:
        return False

    teams: List[Tuple[str, str]] = [(str(team.get("name")), str(team.get("school"))) for team in server_config.teams]
    shuffle(teams)
    cur_row, cur_col = 0, 0
    writer = CounterpartTableWriter(Config.COUNTERPART_TABLE_PATH)
    tables: List[List[List[Tuple[str, str]]]] = []
    for r in range(server_config.round_num):
        table: List[List[Tuple[str, str]]] = [[], [], [], []]
        writer.sheet_without_judge.write(cur_row, cur_col, f"第{r + 1}轮对阵表")
        writer.sheet_with_judge.write(cur_row, cur_col, f"第{r + 1}轮对阵表")
        writer.sheet_with_judge_and_school.write(cur_row, cur_col, f"第{r + 1}轮对阵表")
        cur_row += 1
        #? 装填
        for side in range(4):
            for i in range(server_config.room_total):
                try:
                    table[side].append(teams[side * server_config.room_total + i])
                except IndexError:
                    table[side].append(("None", "None"))
            shuffle(table[side])
        #? 保存
        writer.render_table(writer.sheet_without_judge, cur_row, cur_col, table, lambda x: x[0])
        writer.render_table(writer.sheet_with_judge, cur_row, cur_col, table, lambda x: x[0])
        writer.render_table(writer.sheet_with_judge_and_school, cur_row, cur_col, table, lambda x: str(x))
        cur_row += server_config.room_total + 2
        tables.append(table)
        #? 轮转队伍
        teams = teams[server_config.room_total + 1:] + teams[:server_config.room_total + 1]
    #! 生成会场裁判（完全照抄 PTAssist_Server）
    judge_tables, is_success = try_generate_judges(tables, Config.JUDGE_GENERATE_TRY_TIMES)
    if not is_success:
        #? 循环 time 次都找不到合适的结果！那就可以使用同校裁判
        judge_tables, is_success = try_generate_judges_allow_school(tables)
        if not is_success:
            #? 裁判根本不够！允许不同会场可以重复裁判
            judge_tables = generate_judges(tables)
    writer.render_judges(judge_tables)
    writer.on_exit()
    return True


async def export_rooms(db: AsyncSession) -> bool:
    """
    导出会场令牌表格，返回是否成功
    """
    rooms = await get_all_rooms(db)
    workbook = xlwt.Workbook(encoding="utf-8")

    sheet = workbook.add_sheet("会场 & 令牌")
    sheet.write(0, 0, "会场编号")
    sheet.write(0, 1, "会场令牌")
    row = 1
    for room in rooms:
        sheet.write(row, 0, str(room.room_id))
        sheet.write(row, 1, str(room.token))
        row += 1

    workbook.save(Config.TOKEN_TABLE_PATH)
    return True
