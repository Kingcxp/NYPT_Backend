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
from app.manager import console, CommandInterface
 
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
            console.info('[yellow]帮助：[/yellow]')
            console.info('[cyan]输入[/cyan] [yellow]help[/yellow] 来展示这段信息')
            console.info('[cyan]输入[/cyan] [yellow]info[/yellow] 展示运行环境信息')
            console.info('[cyan]输入[/cyan] [yellow]list-commands[/yellow] 查看所有的命令信息')
            console.info('[cyan]输入[/cyan] [yellow]quit[/yellow], [yellow]stop[/yellow] 或者 [yellow]exit[/yellow] 来终止服务')
            console.info('[blue]提示：[/blue] 你可以在 [yellow]help[/yellow] 命令之后，加上 [cyan]若干条[/cyan] 命令名称来查看 [green]这些命令的详细信息[/green]！')
        else:
            for arg in args:
                command = command_manager.commands.get(arg)
                print()
                if command is None:
                    console.error(
                        f'"[yellow]{arg}[/yellow]" : [red]未找到[/red] 命令！'
                    )
                else:
                    console.info(
                        f'命令的 [magenta]简介[/magenta] 和 [cyan]用法[/cyan] 如下：'
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
        console.info('[cyan]当前运行路径:[/cyan] [yellow]' + os.getcwd() + '[/yellow]')
        console.info('[cyan]python 版本:[/cyan] ' + sys.version)
        repo = git.Repo(os.path.dirname(os.path.abspath(__file__)) + '/..')
        console.info("[cyan]当前提交 ID:[/cyan] " + str(repo.commit()))
        console.info('[cyan]版本日期:[/cyan] ' + str(repo.commit().committed_datetime))
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
    console.info("[red]A[/red][yellow]p[/yellow][green]p[/green][blue]l[/blue][cyan]i[/cyan][magenta]c[/magenta][white]a[/white][red]t[/red][yellow]i[/yellow][green]o[/green][blue]n[/blue] [cyan]c[/cyan][magenta]l[/magenta][white]o[/white][red]s[/red][yellow]e[/yellow][green]d[/green][blue].[/blue]")


def main() -> None:
    global app, command_manager, server, thread
    app, command_manager = create_app(Path(os.path.dirname(os.path.abspath(__file__))).resolve())
    command_manager.register_command(HelpCommand())
    command_manager.register_command(InfoCommand())
    command_manager.register_command(ListCommands())
    server = create_server(app, host='0.0.0.0', port=8081)
    thread = Thread(target=server.run)
    thread.start()
    console.info("[red]A[/red][yellow]p[/yellow][green]p[/green][blue]l[/blue][cyan]i[/cyan][magenta]c[/magenta][white]a[/white][red]t[/red][yellow]i[/yellow][green]o[/green][blue]n[/blue] [cyan]s[/cyan][magenta]t[/magenta][white]a[/white][red]r[/red][yellow]t[/yellow][green]e[/green][blue]d[/blue][cyan].[/cyan]")
    original_stdout = sys.stdout
    sys.stdout = sys.stderr
    console.info("输入 [yellow]help[/yellow] 查看帮助")
    sys.stdout = original_stdout

    while True:
        try:
            command = input().strip()
        except KeyboardInterrupt:
            console.critical("[red]使用了 CTRL+C! 这是不允许的，请使用正常命令终止服务![/red]")
            continue
        except:
            continue
        if command == "":
            continue
        else:
            to_quit: bool = False
            commands = command.replace("\x00", "").split("&&")
            for _command in commands:
                command_line = [c.strip() for c in _command.split()]
                try:
                    if command_line[0] == 'exit' or command_line[0] == 'quit' or command_line[0] == 'stop':
                        close_server()
                        to_quit = True
                        break
                except:
                    # Unknown Error
                    continue
                command_manager.parse_command(command_line[0], command_line[1:])
            if to_quit:
                break


if __name__ == "__main__":
    __name__ = "Flask"
    main()
