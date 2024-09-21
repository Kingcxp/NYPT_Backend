import os
import pkgutil
import importlib

from rich.console import Console
from fastapi import FastAPI
from typing import Optional, Iterable, Set, Dict
from pathlib import Path


console: Console = Console()


def load_all_routers(
    app: FastAPI,
    plugins: Optional[Iterable[str]] = None,
    plugin_dirs: Optional[Iterable[str]] = None
) -> None:
    """为 FastAPI 加载所有的路由

    Args:
        app (FastAPI): FastAPI 实例
        plugins (Optional[Iterable[str]]): 独立插件路径列表
        plugin_dirs (Optional[Iterable[str]]): 插件文件夹列表
    """
    PluginManager(app, plugins, plugin_dirs).load_all_plugins()


def path_to_module_name(path: Path):
    rel_path = path.resolve().relative_to(Path(
        os.path.dirname(os.path.abspath(__file__))
    ))
    if rel_path.stem == "__init__":
        return ".".join(rel_path.parts[:-1])
    return ".".join(rel_path.parts[:-1] + (rel_path.stem,))


def _module_name_to_plugin_name(module_name: str) -> str:
    return module_name.split(".", 1)[-1]


class PluginManager:
    """
    为 FastAPI 应用编写的插件管理器
    参考 nonebot.plugin.manager.PluginManager

    Params:
        app (FastAPI): FastAPI 实例
        plugins (Optional[Iterable[str]]): 独立插件路径列表
        search_path (Optional[Iterable[str]]): 插件文件夹列表
    """
    def __init__(
        self,
        app: FastAPI,
        plugins: Optional[Iterable[str]] = None,
        search_path: Optional[Iterable[str]] = None
    ) -> None:
        self.app = app
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
        搜索插件并加载
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
                    "." + path_to_module_name(self._searched_plugin_names[name]),
                    package=__package__
                )
            else:
                raise RuntimeError(f"插件未找到: {name}! 请检查你的插件名称！")

            if (router := getattr(module, "__router__", None)) is None:
                raise RuntimeError(
                    f"模块 {module.__name__} 未正确作为插件加载! "
                    "请确认 `__blueprint__` 变量的值是否正确."
                )
            self.app.include_router(router=router)
            console.log(
                f'[green]成功加载[/green] 插件 "[yellow]{name}[/yellow]"'
            )
        except Exception:
            console.log(
                f'[red][on #F8BBD0]插件 "{name}" 加载失败！[/on #F8BBD0][/red]'
            )
            console.print_exception(show_locals=True)
            exit()

    def load_all_plugins(self):
        for name in self.available_plugins:
            self.load_plugin(name)
