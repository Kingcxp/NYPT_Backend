import os
import sys
import git
import ctypes
import inspect

from typing import List
from rich.table import Table
from waitress import create_server
from pathlib import Path
from threading import Thread

from app import create_app
from app.manager import logger, console, CommandInterface
 
def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
 
 
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


app = None
command_manager = None
server = None
thread = None


class HelpCommand(CommandInterface):

    @property
    def command(self) -> str:
        return 'help'
    
    @property
    def description(self) -> str:
        return '展示帮助信息'
    
    @property
    def usage(self) -> str:
        return 'help 或者 help <command>'
    
    def execute(self, args: List[str]) -> bool:
        if len(args) == 0:
            logger.opt(colors=True).info('<y>帮助：</y>')
            logger.opt(colors=True).info('<c>输入</c> <y>help</y> 来展示这段信息')
            logger.opt(colors=True).info('<c>输入</c> <y>info</y> 展示运行环境信息')
            logger.opt(colors=True).info('<c>输入</c> <y>clear</y> 清空控制台缓冲区')
            logger.opt(colors=True).info('<c>输入</c> <y>list-commands</y> 查看所有的命令信息')
            logger.opt(colors=True).info('<c>输入</c> <y>quit</y>, <y>stop</y> 或者 <y>exit</y> 来终止服务')
            logger.opt(colors=True).info('<e>提示：</e> 你可以在 <y>help</y> 命令之后，加上 <c>若干条</c> 命令名称来查看 <g>这些命令的详细信息</g>！')
        else:
            for arg in args:
                command = command_manager.commands.get(arg)
                print()
                if command is None:
                    logger.opt(colors=True).error(
                        f'"<y>{arg}</y>" : <r>未找到</r> 命令！'
                    )
                else:
                    logger.opt(colors=True).info(
                        f'命令的 <m>简介</m> 和 <c>用法</c> 如下：'
                    )
                    console.print(f'命令名称: "{arg}"')
                    console.print(f'命令简介: {command_manager.commands_descriptions_and_usages[arg][0]}')
                    console.print(f'命令用法: {command_manager.commands_descriptions_and_usages[arg][1]}')
        return True
    

class InfoCommand(CommandInterface):

    @property
    def command(self) -> str:
        return 'info'
    
    @property
    def description(self) -> str:
        return '展示系统和版本信息'
    
    @property
    def usage(self) -> str:
        return 'info'
    
    def execute(self, args: List[str]) -> bool:
        logger.opt(colors=True).info('<c>当前运行路径:</c> <y>' + os.getcwd() + '</y>')
        logger.opt(colors=True).info('<c>python 版本:</c> ' + sys.version)
        repo = git.Repo(os.path.dirname(os.path.abspath(__file__)) + '/..')
        logger.opt(colors=True).info("<c>当前提交 ID:</c> " + str(repo.commit()))
        logger.opt(colors=True).info('<c>版本日期:</c> ' + str(repo.commit().committed_datetime))
        return True
    

class ClearCommand(CommandInterface):

    @property
    def command(self) -> str:
        return 'clear'
    
    @property
    def description(self) -> str:
        return '清除屏幕缓冲区'
    
    @property
    def usage(self) -> str:
        return 'clear'
    
    def execute(self, args: List[str]) -> bool:
        os.system('cls' if os.name == 'nt' else 'clear')
        return True
    

class ListCommands(CommandInterface):
    @property
    def command(self) -> str:
        return "list-commands"
    
    @property
    def description(self) -> str:
        return "列出所有的命令及其详细介绍"
    
    @property
    def usage(self) -> str:
        return "list-commands"
    
    def execute(self, args: List[str]) -> bool:
        table: Table = Table(show_header=True, header_style="bold green")
        table.add_column("command", justify="left", style="bold yellow")
        table.add_column("description", justify="left", style="bold blue")
        for command in command_manager.commands.keys():
            table.add_row(command, command_manager.commands_descriptions_and_usages[command][0])
        console.print(table)
        return True
    

def close_server() -> None:
    server.close()
    try:
        stop_thread(thread)
    except:
        thread.join()
    logger.opt(colors=True).info("<r>A</r><y>p</y><g>p</g><e>l</e><c>i</c><m>c</m><w>a</w><r>t</r><y>i</y><g>o</g><e>n</e> <c>c</c><m>l</m><w>o</w><r>s</r><y>e</y><g>d</g><e>.</e>")


if __name__ == "__main__":
    __name__ = "Flask"
    app, command_manager = create_app(Path(os.path.dirname(os.path.abspath(__file__))).resolve())
    command_manager.register_command(HelpCommand())
    command_manager.register_command(InfoCommand())
    command_manager.register_command(ClearCommand())
    command_manager.register_command(ListCommands())
    server = create_server(app, host='0.0.0.0', port=8081)
    thread = Thread(target=server.run)
    thread.start()
    logger.opt(colors=True).info("<r>A</r><y>p</y><g>p</g><e>l</e><c>i</c><m>c</m><w>a</w><r>t</r><y>i</y><g>o</g><e>n</e> <c>s</c><m>t</m><w>a</w><r>r</r><y>t</y><g>e</g><e>d</e><c>.</c>")
    logger.opt(colors=True).info("输入 <y>help</y> 查看帮助")

    while True:
        try:
            command = input().strip()
        except KeyboardInterrupt:
            logger.opt(colors=True).critical("\r<r>使用了 CTRL+C! 这是不允许的，请使用正常命令终止服务!</r>")
            continue
        if command == "":
            continue
        else:
            to_quit: bool = False
            commands = command.split("&&")
            for _command in commands:
                command_line = [c.strip() for c in _command.split()]
                if command_line[0] == 'exit' or command_line[0] == 'quit' or command_line[0] == 'stop':
                    close_server()
                    to_quit = True
                    break
                command_manager.parse_command(command_line[0], command_line[1:])
            if to_quit:
                break
