import os

from enum import Enum


class WorkMode(Enum):
    OFFLINE = 0
    ONLINE = 1


class Config:
    # !服务器地址
    mode: WorkMode = WorkMode.ONLINE

    # !ONLINE 设置
    # ?服务器地址
    server_url: str = "127.0.0.1"
    # ?服务器端口
    server_port: int = 1145

    # !OFFLINE 设置
    # ?数据主文件夹路径
    main_folder: str = os.path.split(os.path.realpath(__file__))[0] + '/match/'
    # ?轮次文件夹路径名，跟在主文件夹之后，请用 {id} 标识轮次号
    round_folder_name: str = "Round{id}/"
    # ?会场文件夹路径名，跟在轮次文件夹之后，请用 {id} 标识房间号
    room_file_name: str = "Room{id}"

    # !赛场规则配置
    # ?比赛规则
    rule: str = "CUPT"
    # ?比赛类型
    match_type: str = "NORMAL"

    # !总轮次
    round_count: int = 3
