import os


data_folder = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "data/"
)


class Config:
    #! 生成裁判表的尝试次数
    JUDGE_GENERATE_TRY_TIMES = 1000

    #! 服务器配置文件路径
    CONFIG_PATH: str = os.path.join(
        data_folder,
        "server_config.xls"
    )

    #! 对阵表文件路径
    COUNTERPART_TABLE_PATH: str = os.path.join(
        data_folder,
        "counterpart_table.xls"
    )
    LOTTERY_COUNTERPART_TABLE_PATH: str = os.path.join(
        data_folder,
        "counterpart_table_lottery.xls"
    )

    #! 会场令牌表格文件路径
    TOKEN_TABLE_PATH: str = os.path.join(
        data_folder,
        "rooms.xls"
    )

    #! 服务器文件路径
    #? 临时数据存储路径
    TEMP_FOLDER: str = os.path.join(
        data_folder,
        ".temp/"
    )
    #? 比赛数据文件路径
    MAIN_FOLDER: str = os.path.join(
        data_folder,
        "match/"
    )
    #? 轮次文件夹路径名，跟在主文件夹之后，请使用 {id} 在字符串中标识轮次号
    ROUND_FOLDER_NAME: str = "Round{id}/"
    #? 会场文件路径名，跟在轮次文件夹之后，请使用 {id} 在字符串中标识房间号
    ROOM_FILE_NAME: str = "Room{id}.json"
    #? 接收到的临时文件名，请使用 {round_id} 标识轮次号，{room_id} 标识房间号，{time_stamp} 标识时间戳
    TEMP_FILE_NAME: str = "{room_id}-{round_id}-{time_info}.json"

    #! 配置表名
    SOFTWARE_CONFIG_SHEET_NAME = "软件配置"
    PROBLEM_SET_SHEET_NAME = "赛题信息"
    TEAM_INFO_SHEET_NAME = "队伍信息"
    REFEREE_INFO_SHEET_NAME = "裁判信息"
    TEAM_QUESTION_BANK_SHEET_NAME = "队伍题库"
