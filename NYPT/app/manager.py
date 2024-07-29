import sys
import inspect
import pkgutil
import datetime
import importlib

from rich.console import Console
from traceback import print_exc
from abc import abstractmethod, ABCMeta
from flask import Flask
from pathlib import Path
from typing import Iterable, Optional, Set, Dict, List, Literal


console: Console = Console()

def get_caller_name():
    current_frame = inspect.currentframe()
    try:
        caller_frame = inspect.getouterframes(current_frame, 2)[1]
        caller_module = inspect.getmodule(caller_frame[0])
        return caller_module.__name__
    finally:
        del current_frame


def warning(message: str):
    console.print(
        f"[green]{datetime.datetime.now().strftime('%m-%d %H:%M:%S')}[/green] "
        f"[[bold][yellow]WARNING[/yellow][/bold]] "
        f"[cyan]{get_caller_name()}[/cyan] | "
        f"{message}"
    )


def success(message: str):
    console.print(
        f"[green]{datetime.datetime.now().strftime('%m-%d %H:%M:%S')}[/green] "
        f"[[bold][green]SUCCESS[/green][/bold]] "
        f"[cyan]{get_caller_name()}[/cyan] | "
        f"{message}"
    )


def error(message: str):
    console.print(
        f"[green]{datetime.datetime.now().strftime('%m-%d %H:%M:%S')}[/green] "
        f"[[bold][red]ERROR[/red][/bold]] "
        f"[cyan]{get_caller_name()}[/cyan] | "
        f"{message}"
    )


def info(message: str):
    console.print(
        f"[green]{datetime.datetime.now().strftime('%m-%d %H:%M:%S')}[/green] "
        f"[[bold][white]INFO[/white][/bold]] "
        f"[cyan]{get_caller_name()}[/cyan] | "
        f"{message}"
    )


def critical(message: str):
    console.print(
        f"[green]{datetime.datetime.now().strftime('%m-%d %H:%M:%S')}[/green] "
        f"[[bold][black][on red]CRITICAL[/on red][/black][/bold]] "
        f"[cyan]{get_caller_name()}[/cyan] | "
        f"{message}"
    )


console.warning = warning
console.error = error
console.success = success
console.info = info
console.critical = critical


def warn(method: Literal["GET", "POST"], router: str, msg: str):
    console.warning(f"[yellow]{method}[/yellow] '{router}' [magenta]{msg}[/magenta]")


def suc(method: Literal["GET", "POST"], router: str, msg: str):
    console.success(f"[yellow]{method}[/yellow] '{router}' [green]{msg}[/green]")


def err(method: Literal["GET", "POST"], router: str, msg: str):
    console.error(f"[yellow]{method}[/yellow] '{router}' [red]{msg}[/red]")


class CommandInterface(metaclass=ABCMeta):
    
    @property
    @abstractmethod
    def command(self) -> str:
        """Get name of the command

        Returns:
            str: name of the command
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Get description of the command

        Returns:
            str: description of the command
        """
        pass

    @property
    @abstractmethod
    def usage(self) -> str:
        """Get usage of the command

        Returns:
            str: usage of the command
        """
        pass
    
    @abstractmethod
    def execute(self, args: List[str]) -> bool:
        """Execute the command by processing the args.

        Args:
            args (List[str]): arguments of the command

        Returns:
            bool: whether the execution is successful, True if successful
        """
        pass


class CommandManager:

    def __init__(self) -> None:
        """
        Initialize CommandManager
        """
        self.commands = {}
        self.commands_descriptions_and_usages = {}

    def parse_command(self, command: str, args: List[str]) -> None:
        """Parse the command line.

        Args:
            command (str): name of the command
            args (List[str]): arguments of the command
        """
        original_stdout = sys.stdout
        sys.stdout = sys.stderr
        command = command.replace("\x00", "")
        executor = self.commands.get(command)
        if executor is None:
            console.error(
                f'"[yellow]{command}[/yellow]" : [red]未找到[/red] 命令！'
            )
            return
        try:
            execute_result = executor(args)
            if not execute_result:
                console.warning(
                    f'"[yellow]{command}[/yellow]": 指令运行 [red]失败[/red], [yellow]可能是[/yellow] 因为使用了 [bold]错误的参数[/bold]'
                )
                console.info(
                    f'命令的 [magenta]简介[/magenta] 和 [cyan]用法[/cyan] 如下：'
                )
                console.print(f'命令名称: "{command}"')
                console.print(f'命令简介: {self.commands_descriptions_and_usages[command][0]}')
                console.print(f'命令用法: {self.commands_descriptions_and_usages[command][1]}')
                return
        except:
            print_exc()
            console.critical(
                f'"[yellow]{command}[/yellow]": 命令在运行过程中 [red]出现错误[/red]！'
            )
            return
        console.success(
            f'"[yellow]{command}[/yellow]": 命令 [green]运行成功[/green]！'
        )
        sys.stdout = original_stdout

    def register_command(self, command: CommandInterface, force_register: bool = False) -> bool:
        """Register one command to CommandManager.

        Args:
            command (CommandInterface): a command, extending CommandInterface.
            force_register (bool): whether to overwrite the exist command.

        Returns:
            bool: whether the command is registered successfully, False if the command has been registered.
        """
        original_stdout = sys.stdout
        sys.stdout = sys.stderr
        if force_register == False and self.commands.get(command.command) is not None:
            console.error(
                f'命令已经存在: "[yellow]{command.command}[/yellow]"! 可能的话，请修改你的命令名称。'
                f'"[yellow]{command.command}[/yellow]": 命令 [magenta]已经存在[/magenta]！'
            )
            return False
        self.commands[command.command] = command.execute
        self.commands_descriptions_and_usages[command.command] = (command.description, command.usage)
        console.success(
            f'[green]成功注册[/green] 命令 "[yellow]{command.command}[/yellow]"！'
        )
        sys.stdout = original_stdout
        return True


def load_all_plugins(
        app: Flask,
        manager: CommandManager,
        launcher_path: Path,
        module_path: Optional[Iterable[str]] = None,
        plugin_dir: Optional[Iterable[str]] = None
) -> None:
    """
    Load all the plugins from the list of module_path
    and the plugins under the folder of each plugin_dir in the list.
    Ignoring plugins that starts with `_`

    Params:
        app: the flask application that need to load plugins
        launcher_path: resolved path to the folder of launcher.py
        module_path: list of plugins
        plugin_dir: list of path that contains plugins
    """
    PluginManager(app, manager, launcher_path, module_path, plugin_dir).load_all_plugins()


def path_to_module_name(launcher_path: Path, path: Path) -> str:
    rel_path = path.resolve().relative_to(launcher_path)
    if rel_path.stem == "__init__":
        return ".".join(rel_path.parts[:-1])
    else:
        return ".".join(rel_path.parts[:-1] + (rel_path.stem,))


def _module_name_to_plugin_name(module_name: str) -> str:
    return module_name.rsplit(".", 1)[-1]


class PluginManager:
    """
    Plugin Manager for the flask application.
    written according to module nonebot.plugin.manager.PluginManager

    Params:
        app: the flask application
        manager: command manager of the application
        launcher_path: resolved path to the folder of launcher.py
        plugins: set of the plugins
        search_path: set of the path that contains plugins.
    """

    def __init__(
            self,
            app: Flask,
            manager: CommandManager,
            launcher_path: Path,
            plugins: Optional[Iterable[str]] = None,
            search_path: Optional[Iterable[str]] = None
    ) -> None:
        self.app: Flask = app
        self.manager: CommandManager = manager
        self.launcher_path = launcher_path
        self.plugins: Set[str] = set(plugins or [])
        self.search_path: Set[str] = set(search_path or [])

        self._third_party_plugin_names: Dict[str, str] = {}
        self._searched_plugin_names: Dict[str, Path] = {}
        self.prepare_plugins()

    def __repr__(self) -> str:
        return f"PluginManager(plugins={self.plugins}, search_path={self.search_path})"

    @property
    def third_party_plugins(self) -> Set[str]:
        return set(self._third_party_plugin_names.keys())

    @property
    def searched_plugins(self) -> Set[str]:
        return set(self._searched_plugin_names.keys())

    @property
    def available_plugins(self) -> Set[str]:
        return self.third_party_plugins | self.searched_plugins

    def prepare_plugins(self) -> Set[str]:
        """
        search all the possible plugins and store them.
        """
        searched_plugins: Dict[str, Path] = {}
        third_party_plugins: Dict[str, str] = {}

        for plugin in self.plugins:
            name = _module_name_to_plugin_name(plugin)
            if name in third_party_plugins:
                raise RuntimeError(
                    f"插件已经存在: {name}! 请检查你的插件名称！"
                )
            third_party_plugins[name] = plugin

        self._third_party_plugin_names = third_party_plugins

        for module_info in pkgutil.iter_modules(self.search_path):
            if module_info.name.startswith('_'):
                console.info(
                    f'[magenta]忽略了[/magenta] 模块 "[yellow]{module_info.name}[/yellow]"'
                )
                continue
            if (
                    module_info.name in searched_plugins
                    or module_info.name in third_party_plugins
            ):
                raise RuntimeError(
                    f'插件已经存在: {module_info.name}! 请检查你的插件名称！'
                )

            if not (
                    module_spec := module_info.module_finder.find_spec(
                        module_info.name, None
                    )
            ):
                continue
            if not (module_path := module_spec.origin):
                continue
            searched_plugins[module_info.name] = Path(module_path).resolve()

        self._searched_plugin_names = searched_plugins

        return self.available_plugins

    def load_plugin(self, name: str) -> str:
        """
        load the plugin decided by name.

        Param:
            name: name of the plugin
        """
        try:
            if name in self.plugins:
                module = importlib.import_module(name)
            elif name in self._third_party_plugin_names:
                module = importlib.import_module(self._third_party_plugin_names[name])
            elif name in self._searched_plugin_names:
                module = importlib.import_module(
                    path_to_module_name(self.launcher_path, self._searched_plugin_names[name])
                )
            else:
                raise RuntimeError(f"插件未找到: {name}! 请检查你的插件名称！")

            if (blueprint := getattr(module, "__blueprint__", None)) is None:
                raise RuntimeError(
                    f"模块 {module.__name__} 未正确作为插件加载! "
                    "请确认 `__blueprint__` 变量的值是否正确."
                )
            self.app.register_blueprint(blueprint)
            console.success(
                f'[green]成功加载[/green] 插件 "[yellow]{name}[/yellow]"'
            )
            if (commands := getattr(module, "__commands__", None)) is not None:
                for command in commands:
                    self.manager.register_command(command)
        except Exception as e:
            console.error(
                f'[red][on #F8BBD0]插件 "{name}" 加载失败！[/on #F8BBD0][/red]'
            )
            exit(e)

    def load_all_plugins(self):
        for name in self.available_plugins:
            self.load_plugin(name)
