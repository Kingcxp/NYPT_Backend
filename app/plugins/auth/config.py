import os

from typing import Dict, List


class Config:
    VERIFY_MSG = \
"""
【NYPT】验证码：%s，用于 PT 比赛平台邮箱验证，请勿转发。如非本人操作，请忽略本短信。
"""
    CREATE_MSG = \
"""
尊敬的用户：
    请查收您在 NYPT 平台的新帐号！
    用户名：%s
    密码：%s
    本平台不提供任何自行找回帐号的途径，请勿随意删除此邮件，以防帐号和密码信息丢失！
    祝您在之后的比赛中收获愉快！
    （这是一封自动发送的邮件，请不要回复！）
"""
    #! 配置模板存放位置
    CONFIG_TEMPLATE_PATH: str = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config_template.xlsx"
    )

    #! 定义配置
    CONFIG_DEFAULT: Dict[str, str] = {
        "比赛规则(CUPT/JSYPT)": "CUPT",
        "比赛类型(NORMAL/SPECIAL)": "NORMAL",
        "每场比赛裁判个数": "5",
        "会场总个数": "10",
        "比赛轮数": "3",
        "正方分数权重": "3",
        "反方分数权重": "2",
        "评方分数权重": "1",
    }

    #! 队伍信息表头
    TEAMINFO_HEADERS: List[str] = [
        "学校名",
        "队伍名",
        "抽签号",
        "队员姓名",
        "队员性别（男/女）",
        "队员姓名",
        "队员性别（男/女）",
        "队员姓名",
        "队员性别（男/女）",
        "队员姓名",
        "队员性别（男/女）",
        "队员姓名",
        "队员性别（男/女）",
    ]
