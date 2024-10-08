import xlrd
import xlwt

from math import exp
from functools import reduce
from sqlalchemy import select
from random import randint, shuffle, random
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Iterable, Optional, List, Any, Callable, Set, Tuple, Dict

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
        self.judge_num_per_room = int(software_config_sheet.cell_value(3, 1))
        self.room_total = int(software_config_sheet.cell_value(4, 1))
        self.round_num = int(software_config_sheet.cell_value(5, 1))
        self.positive_weight = float(software_config_sheet.cell_value(6, 1))
        self.negative_weight = float(software_config_sheet.cell_value(7, 1))
        self.judge_weight = float(software_config_sheet.cell_value(8, 1))

        problem_set = problem_set_sheet.col_values(1)
        self.problem_set: Dict[str, str] = {
            str(i): str(problem_set[i])
            for i in range(1, len(problem_set) + 1)
        }

        self.teams: List[Dict[str, Any]] = []
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

        self.judges: Dict[str, str] = {}
        for i in range(1, judge_info_sheet.nrows + 1):
            school_judges = judge_info_sheet.row_values(i)
            self.judges[str(school_judges[0])] = str(school_judges[1:])

        self.question_banks: List[Dict[str, Any]] = []
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
    # 存取 server_config
    server_config: Optional[ServerConfigReader] = None

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
        if self.server_config is None:
            return
        sheet.write(offset_row, offset_col + 1, "正方")
        sheet.write(offset_row, offset_col + 2, "反方")
        sheet.write(offset_row, offset_col + 3, "评方")
        sheet.write(offset_row, offset_col + 4, "观方")
        for i in range(self.server_config.room_total):
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
        if self.server_config is None:
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
            row += self.server_config.room_total + 1



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


async def generate_counterpart_table() -> bool:
    """
    生成对阵表，返回是否成功
    """
    if CounterpartTableWriter.server_config is None:
        return False

    teams: List[Tuple[str, str]] = [(str(team.get("name")), str(team.get("school"))) for team in CounterpartTableWriter.server_config.teams]
    cur_row, cur_col = 0, 0
    writer = CounterpartTableWriter(Config.COUNTERPART_TABLE_PATH)
    tables: List[List[List[Tuple[str, str]]]] = []
    for r in range(CounterpartTableWriter.server_config.round_num):
        table: List[List[Tuple[str, str]]] = [[], [], [], []]
        round_id = r + 1
        writer.sheet_without_judge.write(cur_row, cur_col, f"第{round_id}轮对阵表")
        writer.sheet_with_judge.write(cur_row, cur_col, f"第{round_id}轮对阵表")
        writer.sheet_with_judge_and_school.write(cur_row, cur_col, f"第{round_id}轮对阵表")
        cur_row += 1
        #? 装填
        for side in range(4):
            for i in range(CounterpartTableWriter.server_config.room_total):
                try:
                    table[side].append(teams[side * CounterpartTableWriter.server_config.room_total + i])
                except IndexError:
                    table[side].append(("None", "None"))
            shuffle(table[side])
        #? 保存
        writer.render_table(writer.sheet_without_judge, cur_row, cur_col, table, lambda x: x[0])
        writer.render_table(writer.sheet_with_judge, cur_row, cur_col, table, lambda x: x[0])
        writer.render_table(writer.sheet_with_judge_and_school, cur_row, cur_col, table, lambda x: x)
        cur_row += CounterpartTableWriter.server_config.room_total + 2
        tables.append(table)
        #? 轮转队伍
        teams = teams[CounterpartTableWriter.server_config.room_total + 1:] + teams[:CounterpartTableWriter.server_config.room_total + 1]
    #! 生成会场裁判（完全照抄 PTAssist_Server）真的一看就很耗内存💢
    # 来个 1000 次先试试
    for i in range(1000):
        do_continue = False
        # 总轮次裁判序号: 已上场次数的字典，用于均衡全部轮次各裁判的上场次数
        judge_used_map: Dict[str, int] = {}
        for school in CounterpartTableWriter.server_config.judges:
            for judge in CounterpartTableWriter.server_config.judges[school]:
                judge_used_map[judge] = 0
        # 本次所有生成的裁判表
        judge_tables: List[List[List[Tuple[str, str]]]] = []
        for round_id in range(CounterpartTableWriter.server_config.round_num):
            team_table = tables[round_id]
            # 该轮生成的裁判表
            judge_table: List[List[Tuple[str, str]]] = []
            # 本轮次已上场裁判，用于避免一个老师在一轮中在多个会场出现
            judge_used_list: List[str] = []
            # 本轮次已使用学校
            school_used_list: List[str] = []
            for room in range(CounterpartTableWriter.server_config.room_total):
                # 储存本会场所用裁判
                judge_table_room: List[Tuple[str, str]] = []
                # 参赛队伍学校名称列表
                team_school_names: Set = set()
                for side in range(4):
                    if team_table[side][room][1] != "None":
                        team_school_names.add(team_table[side][room][1])
                # 可用裁判的选择规则是 不与参赛队员学校相同，且未当过本轮裁判
                avail_judge_list: List[Tuple[str, str]] = reduce(
                    lambda x, y: x + y,
                    filter(
                        lambda x: x[1] not in team_school_names and x[0] not in judge_used_list, [
                            [(j, school) for j in CounterpartTableWriter.server_config.judges[school]]
                            for school in CounterpartTableWriter.server_config.judges.keys()
                        ]
                    )
                )
                if len(avail_judge_list) < CounterpartTableWriter.server_config.judge_num_per_room:
                    do_continue = True
                    break
                for _ in range(CounterpartTableWriter.server_config.judge_num_per_room):
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
            writer.render_judges(judge_tables)
            writer.on_exit()
            return True
    #? 循环 1000 次都找不到合适的结果！那就可以使用同校裁判
    damm_it = False
    judge_tables: List[List[List[Tuple[str, str]]]] = []
    judge_used_map: Dict[str, int] = {}
    for round_id in range(CounterpartTableWriter.server_config.round_num):
        team_table = tables[round_id]
        # 该轮生成的裁判表
        judge_table: List[List[Tuple[str, str]]] = []
        # 本轮次已上场裁判，用于避免一个老师在一轮中在多个会场出现
        judge_used_list: List[str] = []
        # 本轮次已使用学校
        school_used_list: List[str] = []
        for room in range(CounterpartTableWriter.server_config.room_total):
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
                        [(j, school) for j in CounterpartTableWriter.server_config.judges[school]]
                        for school in CounterpartTableWriter.server_config.judges.keys()
                    ]
                )
            )
            if len(avail_judge_list) < CounterpartTableWriter.server_config.judge_num_per_room:
                damm_it = True
                break
            for _ in range(CounterpartTableWriter.server_config.judge_num_per_room):
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
    if not damm_it:
        writer.render_judges(judge_tables)
        writer.on_exit()
        return True

    #? 裁判根本不够！允许不同会场可以重复裁判
    judge_tables: List[List[List[Tuple[str, str]]]] = []
    judge_used_map: Dict[str, int] = {}
    for round_id in range(CounterpartTableWriter.server_config.round_num):
        team_table = tables[round_id]
        # 该轮生成的裁判表
        judge_table: List[List[Tuple[str, str]]] = []
        # 本轮次已上场裁判，用于避免一个老师在一轮中在多个会场出现
        judge_used_list: List[str] = []
        # 本轮次已使用学校
        school_used_list: List[str] = []
        for room in range(CounterpartTableWriter.server_config.room_total):
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
                    [(j, school) for j in CounterpartTableWriter.server_config.judges[school]]
                    for school in CounterpartTableWriter.server_config.judges.keys()
                ]
            )
            for _ in range(CounterpartTableWriter.server_config.judge_num_per_room):
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
        writer.render_judges(judge_tables)
        writer.on_exit()
        return True

    #! 卧槽？
    return False
