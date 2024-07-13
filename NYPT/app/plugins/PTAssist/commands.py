from base64 import b64encode, b64decode
from rich.table import Table

from typing import List
from . import interface, next_room_id, Index
from ...manager import CommandInterface, logger, console


class CreateRoom(CommandInterface):
    @property
    def command(self) -> str:
        return "create-room"
    
    @property
    def description(self) -> str:
        return "创建一个新会场数据，含密码(可以为空)"
    
    @property
    def usage(self) -> str:
        return "create-room [-pwd=<password>]"
    
    def execute(self, args: List[str]) -> bool:
        if (len(args) != 0 and len(args) != 1) or \
            (len(args) == 1 and not args[0].startswith("-pwd=")):
            return False
        password: str = ""
        if len(args) == 2:
            password = args[0].split("-pwd=")[1]
        room_id = next_room_id()
        interface.insert("ROOMS",
            ROOMID=room_id,
            TOKEN=b64encode(password.encode('utf-8')).decode('utf-8')
        )
        logger.opt(colors=True).info(f"<g>新会场创建成功！ <b>id</b> 为 <y>{room_id}</y>(当前总会场数)</g>")
        return True
    

class RemoveRoom(CommandInterface):
    @property
    def command(self) -> str:
        return "remove-room"
    
    @property
    def description(self) -> str:
        return "删除一个会场数据， id 大于该会场 id 的会场 id 将自动减一"
    
    @property
    def usage(self) -> str:
        return "remove-room <room_id>"
    
    def execute(self, args: List[str]) -> bool:
        if len(args) != 1 or not args[0].isnumeric():
            return False
        room_id: int = int(args[0])
        query_room = interface.select_first("ROOMS", where={"ROOMID": ("==", room_id)})
        if query_room is None:
            logger.opt(colors=True).error(f"<r>会场 id=<y>{room_id}</y> 不存在！</r>")
            return True
        logger.opt(colors=True).info(f"<g>正在删除会场 id=<y>{room_id}</y> ...</g>")
        room_total = next_room_id()
        interface.delete("ROOMS", where={"ROOMID": ("==", room_id)})
        for i in range(room_id + 1, room_total):
            interface.update("ROOMS", where={"ROOMID": ("==", i)}, ROOMID=i-1)
        logger.opt(colors=True).info(f"<g>会场 id=<y>{room_id}</y> 删除成功！</g>")
        return True
    

class SetRoompass(CommandInterface):
    @property
    def command(self) -> str:
        return "set-roompass"
    
    @property
    def description(self) -> str:
        return "设置一个会场的密码(可以为空)"
    
    @property
    def usage(self) -> str:
        return "set-roompass <room_id> [-pwd=<password>]"
    
    def execute(self, args: List[str]) -> bool:
        if (len(args) != 1 and len(args) != 2) or \
            (len(args) == 2 and not args[1].startswith("-pwd=")) or \
            (not args[0].isnumeric()):
            return False
        room_id: int = int(args[0])
        password: str = ""
        if len(args) == 2:
            password = args[1].split("-pwd=")[1]
        query_room = interface.select_first("ROOMS", where={"ROOMID": ("==", room_id)})
        if query_room is None:
            logger.opt(colors=True).error(f"<r>会场 id=<y>{room_id}</y> 不存在！</r>")
            return True
        interface.update("ROOMS", where={"ROOMID": ("==", room_id)}, TOKEN=b64encode(password.encode('utf-8')).decode('utf-8'))
        logger.opt(colors=True).info(f"<g>会场 id=<y>{room_id}</y> 密码设置成功！</g>")
        return True
    

class ListRooms(CommandInterface):
    @property
    def command(self) -> str:
        return "list-rooms"

    @property
    def description(self) -> str:
        return "列出所有会场的信息"
    
    @property
    def usage(self) -> str:
        return "list-rooms"
    
    def execute(self, args: List[str]) -> bool:
        all = interface.select_all("ROOMS")
        table: Table = Table(show_header=True, header_style="bold green")
        table.add_column("会场号", style="bold yellow", no_wrap=True)
        table.add_column("密码", style="blue", no_wrap=True)
        for room in all:
            table.add_row(
                str(room[Index.ROOMID.value]),
                str(room[Index.TOKEN.value])
            )
        console.print(table)
        return True
