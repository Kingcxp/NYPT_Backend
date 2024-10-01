import os


class Config:
    #! 服务器配置文件路径
    config_path: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "server_config.xlsx"
    )

    #! 服务器文件路径
    #? 临时数据存储路径
    temp_folder: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        ".temp/"
    )
    #? 比赛数据文件路径
    main_folder: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "match/"
    )
    #? 轮次文件夹路径名，跟在主文件夹之后，请使用 {id} 在字符串中标识轮次号
    round_folder_name: str = "Round{id}/"
    #? 会场文件路径名，跟在轮次文件夹之后，请使用 {id} 在字符串中标识房间号
    room_file_name: str = "Room{id}.json"
    #? 接收到的临时文件名，请使用 {round_id} 标识轮次号，{room_id} 标识房间号，{time_stamp} 标识时间戳
    temp_file_name: str = "Round{round_id}-Room{room_id}-{timestamp}.json"
