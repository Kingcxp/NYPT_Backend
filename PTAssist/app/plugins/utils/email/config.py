import os


class Config:
    # ! TODO 更改发送者邮箱地址和token
    # 发送者邮箱地址
    sender = "jt_hub@163.com"
    # SMTP token
    sender_pass = "IJDWLLYQUVGQBBYO"
    # Host of SMTP
    mail_host = "smtp.163.com"
    # Plugin directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
