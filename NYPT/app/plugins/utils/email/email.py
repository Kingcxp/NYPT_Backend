import smtplib
# import aiosmtplib
import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from .config import Config


def send_mail(target: str, sender_name: str, title: str, msg: str) -> bool:
    """
    发送纯文本邮件

    Args:
        target (str): 目标邮箱地址
        sender_name (str): 发送者名称
        title (str): 邮件标题
        msg (str): 邮件正文

    Return:
        bool: 发送邮件时候成功，成功为True，否则为False
    """
    message = MIMEMultipart()
    time = datetime.datetime.today().strftime("%m-%d %H: %M")

    message["From"] = formataddr(pair=(sender_name, Config.sender))
    message["To"] = target
    message["Subject"] = title + " -- {}".format(time)

    message.attach(MIMEText(msg, "plain", "utf-8"))

    try:
        # async with aiosmtplib.SMTP(Config.mail_host) as server:
        #     await server.login(Config.sender, Config.sender_pass)
        #     await server.sendmail(Config.sender, target, message.as_string())
        server = smtplib.SMTP(Config.mail_host)
        server.login(Config.sender, Config.sender_pass)
        server.sendmail(Config.sender, target, message.as_string())
        server.quit()
        return True
    except Exception as err:
        print(err)
        return False
