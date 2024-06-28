from typing import List
from . import get_sysinfo
from ...manager import CommandInterface, logger


class SystemInfo(CommandInterface):
    @property
    def command(self) -> str:
        return "sysinfo"
    
    @property
    def description(self) -> str:
        return "获取系统信息"
    
    @property
    def usage(self) -> str:
        return "sysinfo"
    
    def execute(self, args: List[str]) -> bool:
        info = get_sysinfo()
        logger.opt(colors=True).info(f"<g>CPU Usage:</g> <y>{info['cpu_usage']}</y>")
        logger.opt(colors=True).info(f"<g>CPU Counts:</g> <y>{info['cpu_counts']}</y>")
        logger.opt(colors=True).info(f"<g>CPU Frequency:</g> <y>{info['cpu_freq']}</y>")
        logger.opt(colors=True).info(f"<g>Memory Total:</g> <y>{info['mem_total']}</y>")
        logger.opt(colors=True).info(f"<g>Memory Usage:</g> <y>{info['mem_usage']}</y>")
        return True
