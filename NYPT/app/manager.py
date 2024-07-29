import re
import sys
import pkgutil
import importlib

from rich.console import Console
from traceback import print_exc
from abc import abstractmethod, ABCMeta
from flask import Flask
from pathlib import Path
from loguru import logger
from typing import Iterable, Optional, Set, Dict, List, Literal


def log_handler(message) -> None:
    print(message, end="")

logger.remove()
logger.add(
    log_handler,
    level=0,
    colorize=True,
    diagnose=False,
    format=str(
        "\r<g>{time:MM-DD HH:mm:ss}</g> "
        "[<lvl>{level}</lvl>] "
        "<c>{name}</c> | "
        # "<c>{function}:{line}</c>| "
        "{message}\r"
    ),
)

console: Console = Console()


def warn(method: Literal["GET", "POST"], router: str, msg: str):
    logger.opt(colors=True).warning(f"<y>{method}</y> '{router}' <m>{msg}</m>")


def suc(method: Literal["GET", "POST"], router: str, msg: str):
    logger.opt(colors=True).success(f"<y>{method}</y> '{router}' <g>{msg}</g>")


def err(method: Literal["GET", "POST"], router: str, msg: str):
    logger.opt(colors=True).error(f"<y>{method}</y> '{router}' <r>{msg}</r>")


def escape_tag(s: str) -> str:
    """用于记录带颜色日志时转义 `<tag>` 类型特殊标签

    参考: [loguru color 标签](https://loguru.readthedocs.io/en/stable/api/logger.html#color)

    参数:
        s: 需要转义的字符串
    """
    return re.sub(r"</?((?:[fb]g\s)?[^<>\s]*)>", r"\\\g<0>", s)


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
        executor = self.commands.get(command)
        if executor is None:
            logger.opt(colors=True).error(
                f'"<y>{command}</y>" : <r>未找到</r> 命令！'
            )
            return
        try:
            execute_result = executor(args)
            if not execute_result:
                logger.opt(colors=True).warning(
                    f'"<y>{command}</y>": 指令运行 <r>失败</r>, <y>可能是</y> 因为使用了 <b>错误的参数</b>'
                )
                logger.opt(colors=True).info(
                    f'命令的 <m>简介</m> 和 <c>用法</c> 如下：'
                )
                console.print(f'命令名称: "{command}"')
                console.print(f'命令简介: {self.commands_descriptions_and_usages[command][0]}')
                console.print(f'命令用法: {self.commands_descriptions_and_usages[command][1]}')
                return
        except:
            print_exc()
            logger.opt(colors=True).critical(
                f'"<y>{command}</y>": 命令在运行过程中 <r>出现错误</r>！'
            )
            return
        logger.opt(colors=True).success(
            f'"<y>{command}</y>": 命令 <g>运行成功</g>！'
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
            logger.opt(colors=True).error(
                f'命令已经存在: "<y>{command.command}</y>"! 可能的话，请修改你的命令名称。'
                f'"<y>{command.command}</y>": 命令 <m>已经存在</m>！'
            )
            return False
        self.commands[command.command] = command.execute
        self.commands_descriptions_and_usages[command.command] = (command.description, command.usage)
        logger.opt(colors=True).success(
            f'<g>成功注册</g> 命令 "<y>{command.command}</y>"！'
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
                logger.opt(colors=True).info(
                    f'<m>忽略了</m> 模块 "<y>{escape_tag(module_info.name)}</y>"'
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
            logger.opt(colors=True).success(
                f'<g>成功加载</g> 插件 "<y>{escape_tag(name)}</y>"'
            )
            if (commands := getattr(module, "__commands__", None)) is not None:
                for command in commands:
                    self.manager.register_command(command)
        except Exception as e:
            logger.opt(colors=True, exception=e).error(
                f'<r><bg #f8bbd0>插件 "{escape_tag(name)}" 加载失败！</bg #f8bbd0></r>'
            )
            exit(e)

    def load_all_plugins(self):
        for name in self.available_plugins:
            self.load_plugin(name)
