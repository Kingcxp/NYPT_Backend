import os
import xlwt
import tkinter as tk

from base64 import b64encode, b64decode
from typing import List, Dict, Any, Union, Optional
from random import randint
from functools import reduce
from rich.table import Table
from tkinter import filedialog

from . import interface, next_uid, Index, next_team, next_volunteer, str_decode
from .config import Config
from ..utils.email.email import send_mail_sync
from ...manager import CommandInterface, console, console


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


def img_encode(src: str) -> str:
    with open(src, "rb") as img:
        img_base64 = b64encode(img.read())
    img_type = "error"
    if src.endswith("png"):
        img_type = "png"
    if src.endswith("jpg") or src.endswith("jpeg"):
        img_type = "jpeg"
        
    if img_type == "error":
        raise TypeError("图片格式不支持！")

    return f"data:image/{img_type};base64," + img_base64.decode()


class NewUser(CommandInterface):
    @property
    def command(self) -> str:
        return "new-user"
    
    @property
    def description(self) -> str:
        return "创建一个新用户"
    
    @property
    def usage(self) -> str:
        return "new-user <realname> <email> <password> [-identity=<identity>]"

    def execute(self, args: List[str]) -> bool:
        if (len(args) != 3 and len(args) != 4) or \
            (len(args) == 4 and not args[3].startswith("-identity=")):
            return False
        realname = args[0]
        email = args[1]
        password = args[2]
        identity = "Team"
        if len(args) == 4:
            identity = args[3].split("-identity=")[1]
        query_user = interface.select_first("USER", where={"REALNAME": ("==", realname)})
        if query_user is not None:
            console.info(f"[red]用户名 [yellow]{realname}[/yellow] 已经存在！[/red]")
            return True
        query_user = interface.select_first("USER", where={"EMAIL": ("==", email)})
        if query_user is not None:
            console.info(f"[red]邮箱 [yellow]{email}[/yellow] 已经存在！[/red]")
            return True
        console.info(f"[green]正在创建用户 [yellow]{realname}[/yellow] ...[/green]")
        user_id = next_uid()
        interface.insert("USER",
            UID=user_id,
            NAME=realname,
            REALNAME=realname,
            EMAIL=email,
            TOKEN=b64encode(password.encode('utf-8')).decode('utf-8'),
            TAGS="",
            IDENTITY=identity,
            CONTACT="",
            LEADER="",
            MEMBER="",
            AWARD=""
        )
        console.info(f"[green]新用户 [yellow]{realname}[/yellow] 创建成功！[/green]")
        return True
    

class DeleteUser(CommandInterface):
    @property
    def command(self) -> str:
        return "delete-user"
    
    @property
    def description(self) -> str:
        return "删除一个已存在的用户"
    
    @property
    def usage(self) -> str:
        return "delete-user -id=<uid> 或者 delete-user -realname=<realname> 或者 delete-user -email=<email>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 1:
            return False
        key: str = ""
        value: Union[str, int] = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", int(args[0].split("-id=")[1]), "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        elif args[0].startswith("-email="):
            key, value, value_name = "EMAIL", args[0].split("-email=")[1], "email"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            console.info(f"[red]删除用户 {value_name}=[yellow]{value}[/yellow] 失败：用户不存在！[/red]")
            return True
        console.info(f"[red]正在删除用户 {value_name}=[yellow]{value}[/yellow] ...[/red]")
        interface.delete("USER", where={key: ("==", value)})
        console.info(f"[red]用户 {value_name}=[yellow]{value}[/yellow] 删除成功！[/red]")
        return True
    

class AddTag(CommandInterface):
    @property
    def command(self) -> str:
        return "add-tag"
    
    @property
    def description(self) -> str:
        return "为指定用户添加一个标签"
    
    @property
    def usage(self) -> str:
        return "add-tag -id=<uid> <tag> 或者 add-tag -realname=<realname> <tag> 或者 add-tag -email=<email> <tag>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: Union[str, int] = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", int(args[0].split("-id=")[1]), "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        elif args[0].startswith("-email="):
            key, value, value_name = "EMAIL", args[0].split("-email=")[1], "email"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            console.info(f"[red]为 {value_name}=[yellow]{value}[/yellow] 的用户添加 tag 失败：用户不存在！[/red]")
            return True
        tags: str = query_user[Index.TAGS.value]
        if args[1] in tags:
            console.info(f"[bold]为 {value_name}=[yellow]{value}[/yellow] 的用户添加 tag 失败：用户已经拥有该标签！[/bold]")
        console.info(f"[green]正在为 {value_name}=[yellow]{value}[/yellow] 的用户添加 tag ...[/green]")
        if tags == "":
            tags = args[1]
        else:
            tags = tags + "|" + args[1]
        interface.update("USER", where={key: ("==", value)}, TAGS=tags)
        console.info(f"[green]为 {value_name}=[yellow]{value}[/yellow] 的用户添加 tag 成功！[/green]")
        return True
    

class RemoveTag(CommandInterface):
    @property
    def command(self) -> str:
        return "remove-tag"
    
    @property
    def description(self) -> str:
        return "为指定用户移除一个标签"
    
    @property
    def usage(self) -> str:
        return "remove-tag -id=<uid> <tag> 或者 remove-tag -realname=<realname> <tag> 或者 remove-tag -email=<email> <tag>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: Union[str, int] = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", int(args[0].split("-id=")[1]), "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        elif args[0].startswith("-email="):
            key, value, value_name = "EMAIL", args[0].split("-email=")[1], "email"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            console.info(f"[red]为 {value_name}=[yellow]{value}[/yellow] 的用户移除 tag 失败：用户不存在！[/red]")
            return True
        tags: str = query_user[Index.TAGS.value]
        if args[1] not in tags:
            console.info(f"[bold]为 {value_name}=[yellow]{value}[/yellow] 的用户移除 tag 失败：用户未拥有该标签！[/bold]")
        console.info(f"[green]正在为 {value_name}=[yellow]{value}[/yellow] 的用户移除 tag ...[/green]")
        if tags.startswith(args[1]):
            if "|" in tags:
                tags = tags.replace(args[1] + "|", "")
            else:
                tags = tags.replace(args[1], "")
        else:
            tags = tags.replace("|" + args[1], "")
        interface.update("USER", where={key: ("==", value)}, TAGS=tags)
        console.info(f"[green]为 {value_name}=[yellow]{value}[/yellow] 的用户移除 tag 成功！[/green]")
        return True
    

class SetIdentity(CommandInterface):
    @property
    def command(self) -> str:
        return "set-identity"
    
    @property
    def description(self) -> str:
        return "更改用户的身份组"
    
    @property
    def usage(self) -> str:
        return "set-identity -id=<uid> <identity> 或者 set-identity -realname=<realname> <identity> 或者 set-identity -email=<email> <identity>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: Union[str, int] = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", int(args[0].split("-id=")[1]), "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        elif args[0].startswith("-email="):
            key, value, value_name = "EMAIL", args[0].split("-email=")[1], "email"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            console.info(f"[red]为 {value_name}=[yellow]{value}[/yellow] 的用户更改 identity 失败：用户不存在！[/red]")
            return True
        console.info(f"[green]正在为 {value_name}=[yellow]{value}[/yellow] 的用户更改 identity ...[/green]")
        interface.update("USER", where={key: ("==", value)}, IDENTITY=args[1])
        console.info(f"[green]为 {value_name}=[yellow]{value}[/yellow] 的用户更改 identity 成功！[/green]")
        return True


class SetPassword(CommandInterface):
    @property
    def command(self) -> str:
        return "set-password"
    
    @property
    def description(self) -> str:
        return "更改用户的密码"
    
    @property
    def usage(self) -> str:
        return "set-password -id=<uid> <password> 或者 set-password -realname=<realname> <password> 或者 set-password -email=<email> <password>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: Union[str, int] = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", int(args[0].split("-id=")[1]), "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        elif args[0].startswith("-email="):
            key, value, value_name = "EMAIL", args[0].split("-email=")[1], "email"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            console.info(f"[red]为 {value_name}=[yellow]{value}[/yellow] 的用户更改 password 失败：用户不存在！[/red]")
            return True
        console.info(f"[green]正在为 {value_name}=[yellow]{value}[/yellow] 的用户更改 password ...[/green]")
        interface.update("USER", where={key: ("==", value)}, TOKEN=b64encode(args[1].encode('utf-8')).decode('utf-8'))
        console.info(f"[green]为 {value_name}=[yellow]{value}[/yellow] 的用户更改 password 成功！[/green]")
        return True
    

class ShowPassword(CommandInterface):
    @property
    def command(self) -> str:
        return "show-password"
    
    @property
    def description(self) -> str:
        return "展示解密后的密码"
    
    @property
    def usage(self) -> str:
        return "show-password -id=<uid> 或者 show-password -realname=<realname> 或者 show-password -email=<email>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 1:
            return False
        key: str = ""
        value: Union[str, int] = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", int(args[0].split("-id=")[1]), "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        elif args[0].startswith("-email="):
            key, value, value_name = "EMAIL", args[0].split("-email=")[1], "email"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            console.info(f"[red]为 {value_name}=[yellow]{value}[/yellow] 的用户查找 password 失败：用户不存在！[/red]")
            return True
        console.print(b64decode(query_user[Index.TOKEN.value].encode("utf-8")).decode("utf-8"), style="bold green")
        return True
    

class SetRealname(CommandInterface):
    @property
    def command(self) -> str:
        return "set-realname"
    
    @property
    def description(self) -> str:
        return "更改用户的真实用户名"
    
    @property
    def usage(self) -> str:
        return "set-realname -id=<uid> <realname> 或者 set-realname -realname=<old_realname> <new_realname> 或者set-realname -email=<email> <realname>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: Union[str, int] = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", int(args[0].split("-id=")[1]), "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        elif args[0].startswith("-email="):
            key, value, value_name = "EMAIL", args[0].split("-email=")[1], "email"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            console.info(f"[red]为 {value_name}=[yellow]{value}[/yellow] 的用户更改 realname 失败：用户不存在！[/red]")
            return True
        console.info(f"[green]正在为 {value_name}=[yellow]{value}[/yellow] 的用户更改 realname ...[/green]")
        interface.update("USER", where={key: ("==", value)}, REALNAME=args[1])
        console.info(f"[green]为 {value_name}=[yellow]{value}[/yellow] 的用户更改 realname 成功！[/green]")
        return True
    

class SetName(CommandInterface):
    @property
    def command(self) -> str:
        return "set-name"
    
    @property
    def description(self) -> str:
        return "更改用户的用户名"
    
    @property
    def usage(self) -> str:
        return "set-name -id=<uid> <name> 或者 set-name -realname=<realname> <name> 或者 set-name -email=<email> <name>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: Union[str, int] = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", int(args[0].split("-id=")[1]), "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        elif args[0].startswith("-email="):
            key, value, value_name = "EMAIL", args[0].split("-email=")[1], "email"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            console.info(f"[red]为 {value_name}=[yellow]{value}[/yellow] 的用户更改 name 失败：用户不存在！[/red]")
            return True
        console.info(f"[green]正在为 {value_name}=[yellow]{value}[/yellow] 的用户更改 name ...[/green]")
        interface.update("USER", where={key: ("==", value)}, NAME=args[1])
        console.info(f"[green]为 {value_name}=[yellow]{value}[/yellow] 的用户更改 name 成功！[/green]")
        return True
    

class SetAward(CommandInterface):
    @property
    def command(self) -> str:
        return "set-award"
    
    @property
    def description(self) -> str:
        return "为用户设置奖项图片"
    
    @property
    def usage(self) -> str:
        return "set-award -id=<uid> 或者 set-award -realname=<realname> 或者 set-award -email=<email>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 1:
            return False
        key: str = ""
        value: Union[str, int] = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", int(args[0].split("-id=")[1]), "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        elif args[0].startswith("-email="):
            key, value, value_name = "EMAIL", args[0].split("-email=")[1], "email"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            console.info(f"[red]为 {value_name}=[yellow]{value}[/yellow] 的用户添加奖项失败：用户不存在！[/red]")
            return True
        console.info(f"[green]正在为 {value_name}=[yellow]{value}[/yellow] 的用户添加奖项...[/green]")

        root = tk.Tk()
        root.withdraw()
        filepath = filedialog.askopenfilename()
        interface.update("USER", where={key: ("==", value)}, AWARD=img_encode(filepath))

        console.info(f"[green]为 {value_name}=[yellow]{value}[/yellow] 的用户添加奖项成功！[/green]")
        return True
    

class ListRequests(CommandInterface):
    @property
    def command(self) -> str:
        return "list-requests"
    
    @property
    def description(self) -> str:
        return "列出所有的注册请求"
    
    @property
    def usage(self) -> str:
        return "list-requests"
    
    def execute(self, args: List[str]) -> bool:
        all = interface.select_all("PENDING_REQUEST")
        table: Table = Table(show_header=True, header_style="bold green")
        table.add_column("编号", justify="left", style="bold yellow")
        table.add_column("名称", justify="left")
        table.add_column("学校", justify="left", style="blue")
        table.add_column("邮箱", justify="left", style="green")
        table.add_column("电话", justify="left", style="yellow")
        table.add_column("身份", justify="left", style="green")
        table.add_column("联系人", justify="left", style="bold blue")
        for request in all:
            table.add_row(
                str(request[Index.RID.value]),
                str(request[Index.NAME.value]),
                str(request[Index.SCHOOL.value]),
                str(request[Index.EMAIL.value]),
                str(request[Index.TEL.value]),
                str(request[Index.IDENTITY.value]),
                str(request[Index.CONTACT.value])
            )
        console.print(table)
        return True
    

class AcceptRequest(CommandInterface):
    @property
    def command(self) -> str:
        return "accept-request"
    
    @property
    def description(self) -> str:
        return "通过一个注册请求，自动创建一个账号并通过邮件告知用户"
    
    @property
    def usage(self) -> str:
        return "accept-request -id=<rid>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 1 or not args[0].startswith("-id="):
            return False
        rid: int = int(args[0].split("-id=")[1])
        request = interface.select_first("PENDING_REQUEST", where={"RID": ("==", rid)})
        if request is None:
            console.info(f"[red]获取 [yellow]id={rid}[/yellow] 的请求信息失败：请求不存在！[/red]")
            return True
        email = request[Index.EMAIL.value]
        email_query = interface.select_first("USER", where={"EMAIL": ("==", email)})
        if email_query is not None:
            console.info(f"[red][yellow]email={email}[/yellow] 的用户已经存在！[/red]")
        realname: Optional[str] = None
        password: Optional[str] = None
        match request[Index.IDENTITY.value]:
            case "Team":
                realname = next_team()
                password = generate_password(Config.team_pwd_len)
            case "VolunteerA":
                realname = next_volunteer("A")
                password = generate_password(Config.volunteer_a_pwd_len)
            case "VolunteerB":
                realname = next_volunteer("B")
                password = generate_password(Config.volunteer_b_pwd_len)
            case _:
                console.info(f"[red]这是什么身份？不应该有这种身份！你只能拒绝它！[/red]")
                return True
        interface.insert("USER",
            UID=next_uid(),
            NAME=request[Index.NAME.value],
            REALNAME=realname,
            EMAIL=email,
            TOKEN=b64encode(password.encode("utf-8")).decode("utf-8"),
            IDENTITY=request[Index.IDENTITY.value],
            TAGS="",
            CONTACT=request[Index.CONTACT.value],
            LEADER="",
            MEMBER="",
            AWARD=""
        )
        if not send_mail_sync(
            target=email, sender_name="NYPT",
            title="您的注册申请已经通过！", msg=Config.accepted_msg % (realname, password)
        ):
            console.info(f"[red]发送邮件发生错误！请尝试重新通过申请！[/red]")
            return True
        interface.delete("PENDING_REQUEST", where={"RID": ("==", rid)})
        console.info(f"[green]已经通过该注册请求！[/green]")
        return True


class RejectRequest(CommandInterface):
    @property
    def command(self) -> str:
        return "reject-request"
    
    @property
    def description(self) -> str:
        return "拒绝一个注册请求，通过邮件告知用户"
    
    @property
    def usage(self) -> str:
        return "reject-request -id=<rid> [拒绝理由]"
    
    def execute(self, args: List[str]) -> bool:
        if len(args != 1) or not args[0].startswith("-id="):
            return False
        rid: int = int(args[0].split("-id=")[1])
        args = args[1:]
        request = interface.select_first("PENDING_REQUEST", where={"RID": ("==", rid)})
        if request is None:
            console.info(f"[red]获取 [yellow]id={rid}[/yellow] 的请求信息失败：请求不存在！[/red]")
            return True
        email = request[Index.EMAIL.value]
        if not send_mail_sync(
            target=email, sender_name="NYPT",
            title="您的注册请求被拒绝！", msg=Config.rejected_msg % ("".join(args))
        ):
            console.info(f"[red]发送邮件发生错误！请尝试重新拒绝申请！[/red]")
            return True
        interface.delete("PENDING_REQUEST", where={"RID": ("==", rid)})
        console.info(f"[green]已经拒绝该注册请求！[/green]")
        return True
    

class UserInfo(CommandInterface):
    @staticmethod
    def print_user(user: List[Any]) -> None:
        table: Table = Table(show_header=True, header_style="bold green")
        table.add_column("字段", justify="left", style="bold green")
        table.add_column("值", justify="left", style="yellow")
        table.add_row("编号", str(user[Index.UID.value]))
        table.add_row("名称", str(user[Index.NAME.value]))
        table.add_row("标识", str(user[Index.REALNAME.value]))
        table.add_row("邮箱", str(user[Index.EMAIL.value]))
        table.add_row("密码(加密)", str(user[Index.TOKEN.value]))
        table.add_row("标签", str(user[Index.TAGS.value]))
        table.add_row("身份", str(user[Index.IDENTITY.value]))
        if user[Index.IDENTITY.value] == "Team":
            table.add_row("联系人", str(user[Index.CONTACT.value]))
            table.add_row("领队", str(user[Index.LEADER.value]))
            table.add_row("队员", str(user[Index.MEMBER.value]))
        console.print(table)

    @property
    def command(self) -> str:
        return "user-info"
    
    @property
    def description(self) -> str:
        return "获取指定用户的信息"
    
    @property
    def usage(self) -> str:
        return "user-info -id=<uid> 或者 user-info -realname=<realname> 或者 user-info -email=<email>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 1:
            return False
        key: str = ""
        value: Union[str, int] = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", int(args[0].split("-id=")[1]), "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        elif args[0].startswith("-email="):
            key, value, value_name = "EMAIL", args[0].split("-email=")[1], "email"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            console.info(f"[red]获取用户 {value_name}=[yellow]{value}[/yellow] 的信息失败：用户不存在！[/red]")
            return True
        self.print_user(query_user)
        return True
    

class ListTeams(CommandInterface):
    @property
    def command(self) -> str:
        return "list-teams"
    
    @property
    def description(self) -> str:
        return "列出所有的队伍"
    
    @property
    def usage(self) -> str:
        return "list-teams"
    
    def execute(self, args: List[str]) -> bool:
        teams = interface.select_all("USER", where={"IDENTITY": ("==", "Team")})
        table: Table = Table(show_header=True, header_style="bold green")
        table.add_column("编号", justify="left", style="bold yellow")
        table.add_column("队名", justify="left")
        table.add_column("标识", justify="left", style="blue")
        table.add_column("邮箱地址", justify="left", style="green")
        table.add_column("标签", justify="left", style="yellow")
        table.add_column("联系人", justify="left", style="green")
        for team in teams:
            table.add_row(
                str(team[Index.UID.value]),
                str(team[Index.NAME.value]),
                str(team[Index.REALNAME.value]),
                str(team[Index.EMAIL.value]),
                str(team[Index.TAGS.value]),
                str(team[Index.CONTACT.value])
            )
        console.print(table)
        return True
    

class ListVolunteers(CommandInterface):
    @property
    def command(self) -> str:
        return "list-volunteers"
    
    @property
    def description(self) -> str:
        return "列出所有的指定类型志愿者，分 A 和 B 两种"
    
    @property
    def usage(self) -> str:
        return "list-volunteers -type=<type>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 1 or not args[0].startswith("-type="):
            return False
        volunteers = interface.select_all("USER", where={"IDENTITY": ("==", "Volunteer" + args[0].split("-type=")[1].upper())})
        table: Table = Table(show_header=True, header_style="bold green")
        table.add_column("编号", justify="left", style="bold yellow")
        table.add_column("名称", justify="left")
        table.add_column("标识", justify="left", style="blue")
        table.add_column("邮箱地址", justify="left", style="green")
        table.add_column("标签", justify="left", style="yellow")
        table.add_column("身份", justify="left", style="green")
        for volunteer in volunteers:
            table.add_row(
                str(volunteer[Index.UID.value]),
                str(volunteer[Index.NAME.value]),
                str(volunteer[Index.REALNAME.value]),
                str(volunteer[Index.EMAIL.value]),
                str(volunteer[Index.TAGS.value]),
                str(volunteer[Index.IDENTITY.value])
            )
        console.print(table)
        return True
    

class ListAll(CommandInterface):
    @property
    def command(self) -> str:
        return "list-all"
    
    @property
    def description(self) -> str:
        return "列出所有的用户"
    
    @property
    def usage(self) -> str:
        return "list-all"
    
    def execute(self, args: List[str]) -> bool:
        all = interface.select_all("USER")
        table: Table = Table(show_header=True, header_style="bold green")
        table.add_column("编号", justify="left", style="bold yellow")
        table.add_column("名称", justify="left")
        table.add_column("标识", justify="left", style="blue")
        table.add_column("邮箱", justify="left", style="green")
        table.add_column("标签", justify="left", style="yellow")
        table.add_column("身份", justify="left", style="green")
        for user in all:
            table.add_row(
                str(user[Index.UID.value]),
                str(user[Index.NAME.value]),
                str(user[Index.REALNAME.value]),
                str(user[Index.EMAIL.value]),
                str(user[Index.TAGS.value]),
                str(user[Index.IDENTITY.value])
            )
        console.print(table)
        return True
    

class ExportConfig(CommandInterface):
    @property
    def command(self) -> str:
        return "export-config"
    
    @property
    def description(self) -> str:
        return "导出为 PTAssist 使用的配置文件"
    
    @property
    def usage(self) -> str:
        return "export-config"
    
    def execute(self, args: List[str]) -> bool:
        workbook = xlwt.Workbook(encoding='utf-8')
        team_infos = interface.select_all("USER", where={"IDENTITY": ("==", "Team")})
        team_infos = sorted(team_infos, key=lambda x: x[Index.SCHOOL.value])

        #? 配置表
        sheet_config = workbook.add_sheet("软件配置")
        index: int = -1
        for key, value in Config.config_default.items():
            index += 1
            sheet_config.write(index, 0, key)
            sheet_config.write(index, 1, value)

        #? 赛题信息
        sheet_info = workbook.add_sheet("赛题信息")
        sheet_info.write(0, 0, "题号")
        sheet_info.write(0, 1, "题名")
        index = 0
        for problem in Config.problem_set:
            index += 1
            sheet_info.write(index, 0, str(index))
            sheet_info.write(index, 1, problem)
        
        #? 队伍信息
        sheet_team = workbook.add_sheet("队伍信息")
        index = -1
        for header in Config.team_info_headers:
            index += 1
            sheet_team.write(0, index, header)
        index = 0
        for team in team_infos:
            index += 1
            sheet_team.write(index, 0, team[Index.SCHOOL.value])
            sheet_team.write(index, 1, team[Index.REALNAME.value])
            # TODO ? 抽签号 ?
            sheet_team.write(index, 2, str(index))
            members: List[Dict[str, str]] = str_decode(team[Index.MEMBER.value])
            i = 0
            for member in members:
                i += 1
                sheet_team.write(index, 1 + i * 2, f"{i}号选手")
                sheet_team.write(index, 2 + i * 2, member["gender"])

        #? 裁判信息
        # TODO 无法生成？
        sheet_referee = workbook.add_sheet("裁判信息")
        sheet_referee.write(0, 0, "学校名")
        sheet_referee.write(0, 1, "裁判们")

        #? 队伍题库
        sheet_problem_set = workbook.add_sheet("队伍题库")
        sheet_problem_set.write(0, 0, "学校名")
        sheet_problem_set.write(0, 1, "队伍名")
        sheet_problem_set.write(0, 2, "题库")
        index = 0
        for team in team_infos:
            index += 1
            sheet_problem_set.write(index, 0, team[Index.SCHOOL.value])
            sheet_problem_set.write(index, 1, team[Index.REALNAME.value])
        
        workbook.save(os.path.dirname(os.path.abspath(__file__)) + "/server_config.xlsx")
        console.info(f"[green]配置文件导出成功！[/green]")
        return True
