from base64 import b64encode, b64decode
from typing import List, Any
from rich.table import Table

from . import interface, next_uid
from ...manager import CommandInterface, logger, console


class NewUser(CommandInterface):
    @property
    def command(self) -> str:
        return "new-user"
    
    @property
    def description(self) -> str:
        return "创建一个新用户"
    
    @property
    def usage(self) -> str:
        return "new-user <realname> <password> [-identity=<identity>]"

    def execute(self, args: List[str]) -> bool:
        if (len(args) != 2 and len(args) != 3) or \
            (len(args) == 3 and not args[2].startswith("-identity=")):
            return False
        realname = args[0]
        password = args[1]
        identity = "Team"
        if len(args) == 3:
            identity = args[2].split("-identity=")[1]
        query_user = interface.select_first("USER", where={"REALNAME": ("==", realname)})
        if query_user is not None:
            logger.opt(colors=True).info(f"<r>用户名 <y>{realname}</y> 已经存在！</r>")
            return True
        logger.opt(colors=True).info(f"<g>正在创建用户 <y>{realname}</y> ...</g>")
        user_id = next_uid()
        interface.insert("USER",
            UID=user_id,
            NAME=realname,
            REALNAME=realname,
            TOKEN=b64encode(password.encode('utf-8')).decode('utf-8'),
            TAGS="",
            IDENTITY=identity,
            TEAMNAME="",
            LEADER="",
            MEMBER="",
            AWARD=""
        )
        logger.opt(colors=True).info(f"<g>新用户 <y>{realname}</y> 创建成功！</g>")
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
        return "delete-user -id=<uid> 或者 delete-user -realname=<realname>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 1:
            return False
        key: str = ""
        value: str = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", args[0].split("-id=")[1], "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            logger.opt(colors=True).info(f"<r>删除用户 {value_name}=<y>{value}</y> 失败：用户不存在！</r>")
            return True
        logger.opt(colors=True).info(f"<r>正在删除用户 {value_name}=<y>{value}</y> ...</r>")
        interface.delete("USER", where={key: ("==", value)})
        logger.opt(colors=True).info(f"<r>用户 {value_name}=<y>{value}</y> 删除成功！</r>")
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
        return "add-tag -id=<uid> <tag> 或者 add-tag -realname=<realname> <tag>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: str = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", args[0].split("-id=")[1], "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            logger.opt(colors=True).info(f"<r>为 {value_name}=<y>{value}</y> 的用户添加 tag 失败：用户不存在！</r>")
            return True
        tags: str = query_user[4]
        if args[1] in tags:
            logger.opt(colors=True).info(f"<b>为 {value_name}=<y>{value}</y> 的用户添加 tag 失败：用户已经拥有该标签！</b>")
        logger.opt(colors=True).info(f"<g>正在为 {value_name}=<y>{value}</y> 的用户添加 tag ...</g>")
        if tags == "":
            tags = args[1]
        else:
            tags = tags + "|" + args[1]
        interface.update("USER", where={key: ("==", value)}, TAGS=tags)
        logger.opt(colors=True).info(f"<g>为 {value_name}=<y>{value}</y> 的用户添加 tag 成功！</g>")
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
        return "remove-tag -id=<uid> <tag> 或者 remove-tag -realname=<realname> <tag>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: str = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", args[0].split("-id=")[1], "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            logger.opt(colors=True).info(f"<r>为 {value_name}=<y>{value}</y> 的用户移除 tag 失败：用户不存在！</r>")
            return True
        tags: str = query_user[4]
        if args[1] not in tags:
            logger.opt(colors=True).info(f"<b>为 {value_name}=<y>{value}</y> 的用户移除 tag 失败：用户未拥有该标签！</b>")
        logger.opt(colors=True).info(f"<g>正在为 {value_name}=<y>{value}</y> 的用户移除 tag ...</g>")
        if tags.startswith(args[1]):
            if "|" in tags:
                tags = tags.replace(args[1] + "|", "")
            else:
                tags = tags.replace(args[1], "")
        else:
            tags = tags.replace("|" + args[1], "")
        interface.update("USER", where={key: ("==", value)}, TAGS=tags)
        logger.opt(colors=True).info(f"<g>为 {value_name}=<y>{value}</y> 的用户移除 tag 成功！</g>")
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
        return "set-identity -id=<uid> <identity> 或者 set-identity -realname=<realname> <identity>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: str = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", args[0].split("-id=")[1], "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            logger.opt(colors=True).info(f"<r>为 {value_name}=<y>{value}</y> 的用户更改 identity 失败：用户不存在！</r>")
            return True
        logger.opt(colors=True).info(f"<g>正在为 {value_name}=<y>{value}</y> 的用户更改 identity ...</g>")
        interface.update("USER", where={key: ("==", value)}, IDENTITY=args[1])
        logger.opt(colors=True).info(f"<g>为 {value_name}=<y>{value}</y> 的用户更改 identity 成功！</g>")
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
        return "set-password -id=<uid> <password> 或者 set-password -realname=<realname> <password>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: str = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", args[0].split("-id=")[1], "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            logger.opt(colors=True).info(f"<r>为 {value_name}=<y>{value}</y> 的用户更改 password 失败：用户不存在！</r>")
            return True
        logger.opt(colors=True).info(f"<g>正在为 {value_name}=<y>{value}</y> 的用户更改 password ...</g>")
        interface.update("USER", where={key: ("==", value)}, TOKEN=b64encode(args[1].encode('utf-8')).decode('utf-8'))
        logger.opt(colors=True).info(f"<g>为 {value_name}=<y>{value}</y> 的用户更改 password 成功！</g>")
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
        return "set-realname -id=<uid> <new_realname> 或者 set-realname -realname=<old_realname> <new_realname>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: str = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", args[0].split("-id=")[1], "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            logger.opt(colors=True).info(f"<r>为 {value_name}=<y>{value}</y> 的用户更改 realname 失败：用户不存在！</r>")
            return True
        logger.opt(colors=True).info(f"<g>正在为 {value_name}=<y>{value}</y> 的用户更改 realname ...</g>")
        interface.update("USER", where={key: ("==", value)}, REALNAME=args[1])
        logger.opt(colors=True).info(f"<g>为 {value_name}=<y>{value}</y> 的用户更改 realname 成功！</g>")
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
        return "set-name -id=<uid> <name> 或者 set-name -realname=<realname> <name>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 2:
            return False
        key: str = ""
        value: str = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", args[0].split("-id=")[1], "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            logger.opt(colors=True).info(f"<r>为 {value_name}=<y>{value}</y> 的用户更改 name 失败：用户不存在！</r>")
            return True
        logger.opt(colors=True).info(f"<g>正在为 {value_name}=<y>{value}</y> 的用户更改 name ...</g>")
        interface.update("USER", where={key: ("==", value)}, NAME=args[1])
        logger.opt(colors=True).info(f"<g>为 {value_name}=<y>{value}</y> 的用户更改 name 成功！</g>")
        return True
    

class UserInfo(CommandInterface):
    @staticmethod
    def print_user(user: List[Any]) -> None:
        console.print("UID: ", style="bold blue", end="")
        console.print(f"{user[0]}", style="yellow")
        console.print(f"NAME: ", style="bold blue", end="")
        console.print(f"{user[1]}", style="yellow")
        console.print(f"REALNAME: ", style="bold blue", end="")
        console.print(f"{user[2]}", style="yellow")
        console.print(f"TOKEN: ", style="bold blue", end="")
        console.print(f"{user[3]}", style="yellow")
        console.print(f"TAGS: ", style="bold blue", end="")
        console.print(f"{user[4]}", style="yellow")
        console.print(f"IDENTITY: ", style="bold blue", end="")
        console.print(f"{user[5]}", style="yellow")
        if user[5] == "Team":
            console.print(f"LEADER: ", style="bold blue", end="")
            console.print(f"{user[6]}", style="yellow")
            console.print(f"MEMBER: ", style="bold blue", end="")
            console.print(f"{user[7]}", style="yellow")

    @property
    def command(self) -> str:
        return "user-info"
    
    @property
    def description(self) -> str:
        return "获取指定用户的信息"
    
    @property
    def usage(self) -> str:
        return "user-info -id=<uid> 或者 user-info -realname=<realname>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 1:
            return False
        key: str = ""
        value: str = ""
        value_name: str = ""
        if args[0].startswith("-id="):
            key, value, value_name = "UID", args[0].split("-id=")[1], "id"
        elif args[0].startswith("-realname="):
            key, value, value_name = "REALNAME", args[0].split("-realname=")[1], "realname"
        else:
            return False
        query_user = interface.select_first("USER", where={key: ("==", value)})
        if query_user is None:
            logger.opt(colors=True).info(f"<r>获取用户 {value_name}=<y>{value}</y> 的信息失败：用户不存在！</r>")
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
        table.add_column("UID", justify="left")
        table.add_column("NAME", justify="left")
        table.add_column("REALNAME", justify="left")
        table.add_column("TAGS", justify="left")
        table.add_column("IDENTITY", justify="left")
        for team in teams:
            table.add_row(team[0], team[1], team[2], team[4], team[5])
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
        volunteers = interface.select_all("USER", where={"IDENTITY": ("==", "Volunteer" + args[0].split("-type=")[1])})
        table: Table = Table(show_header=True, header_style="bold green")
        table.add_column("UID", justify="left")
        table.add_column("NAME", justify="left")
        table.add_column("REALNAME", justify="left")
        table.add_column("TAGS", justify="left")
        table.add_column("IDENTITY", justify="left")
        for volunteer in volunteers:
            table.add_row(volunteer[0], volunteer[1], volunteer[2], volunteer[4], volunteer[5])
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
        table.add_column("UID", justify="left")
        table.add_column("NAME", justify="left")
        table.add_column("REALNAME", justify="left")
        table.add_column("TAGS", justify="left")
        table.add_column("IDENTITY", justify="left")
        for user in all:
            table.add_row(user[0], user[1], user[2], user[4], user[5])
        console.print(table)
        return True
