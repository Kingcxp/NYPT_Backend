import os
import smtplib
import aiosmtplib
import datetime

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from ....manager import console


async def send_mail_async(target: str, sender_name: str, title: str, msg: str) -> bool:
    """异步发送纯文本邮件

    Args:
        target (str): 目标邮箱地址
        sender_name (str): 发送者名称
        title (str): 邮件标题
        msg (str): 邮件正文

    Returns:
        bool: 发送邮件是否成功，成功为 True，否则为 False
    """
    message = MIMEMultipart()
    time = datetime.datetime.today().strftime("%m-%d %H: %M")
    email = os.getenv("EMAIL")
    email_passkey = os.getenv("EMAIL_PASSKEY")
    email_host = os.getenv("EMAIL_HOST")
    if email is None or \
       email_passkey is None or \
       email_host is None:
        console.log("[red][on #F8BBD0]未配置邮箱信息，请检查环境(EMAIL, EMAIL_PASSKEY, EMAIL_HOST)变量是否设置！[/on #F8BBD0][/red]")
        return False

    message["From"] = formataddr(pair=(sender_name, email))
    message["To"] = target
    message["Subject"] = title + " -- {}".format(time)

    message.attach(MIMEText(msg, "plain", "utf-8"))

    try:
        async with aiosmtplib.SMTP(hostname=email_host) as server:
            await server.login(email, email_passkey)
            await server.sendmail(email, target, message.as_string())
        return True
    except Exception:
        console.print_exception(show_locals=True)
        return False

def send_mail(target: str, sender_name: str, title: str, msg: str) -> bool:
    """同步发送纯文本邮件

    Args:
        target (str): 目标邮箱地址
        sender_name (str): 发送者名称
        title (str): 邮件标题
        msg (str): 邮件正文

    Returns:
        bool: 发送邮件是否成功，成功为 True，否则为 False
    """
    message = MIMEMultipart()
    time = datetime.datetime.today().strftime("%m-%d %H: %M")
    email = os.getenv("EMAIL")
    email_passkey = os.getenv("EMAIL_PASSKEY")
    email_host = os.getenv("EMAIL_HOST")
    if email is None or \
       email_passkey is None or \
       email_host is None:
        console.log("[red][on #F8BBD0]未配置邮箱信息，请检查环境(EMAIL, EMAIL_PASSKEY, EMAIL_HOST)变量是否设置！[/on #F8BBD0][/red]")
        return False

    message["From"] = formataddr(pair=(sender_name, email))
    message["To"] = target
    message["Subject"] = title + " -- {}".format(time)

    message.attach(MIMEText(msg, "plain", "utf-8"))

    try:
        with smtplib.SMTP(host=email_host) as server:
            server.login(email, email_passkey)
            server.sendmail(email, target, message.as_string())
        return True
    except Exception:
        console.print_exception(show_locals=True)
        return False
