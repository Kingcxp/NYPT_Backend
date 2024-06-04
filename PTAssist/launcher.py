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
        return 'help'
    
    def execute(self, args: List[str]) -> bool:
        logger.opt(colors=True).info('<y>Shortcuts</y>')
        logger.opt(colors=True).info('<c>Enter</c> <y>help</y> to show this help.')
        logger.opt(colors=True).info('<c>Enter</c> <y>info</y> to show info.')
        logger.opt(colors=True).info('<c>Enter</c> <y>list-commands</y> to show all the available commands.')
        logger.opt(colors=True).info('<c>Enter</c> <y>quit</y>, <y>stop</y> or <y>exit</y> to stop the server.')
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
        logger.opt(colors=True).info('<c>Current working directory:</c> <y>' + os.getcwd() + '</y>')
        logger.opt(colors=True).info('<c>Python version:</c> ' + sys.version)
        repo = git.Repo(os.path.dirname(os.path.abspath(__file__)) + '/..')
        logger.opt(colors=True).info("<c>Commit ID:</c> " + str(repo.commit()))
        logger.opt(colors=True).info('<c>Version date:</c> ' + str(repo.commit().committed_datetime))
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
    

def close_server():
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
    logger.opt(colors=True).info("Enter <y>help</y> to show help.")

    while True:
        try:
            command = input()
        except KeyboardInterrupt:
            logger.opt(colors=True).info("\r<r>DETECTED CTRL+C! PLEASE USE QUIT OR EXIT TO STOP THE SERVER!</r>")
            continue
        if command == 'quit' or command == "exit" or command == "stop":
            close_server()
            break
        if command == "":
            continue
        else:
            command_line = [c.strip() for c in command.split()]
            command_manager.parse_command(command_line[0], command_line[1:])
