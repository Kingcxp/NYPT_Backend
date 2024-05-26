from typing import List
from . import get_sysinfo
from ...manager import CommandInterface, logger


class SystemInfo(CommandInterface):
    @property
    def command(self) -> str:
        return "sysinfo"
    
    @property
    def description(self) -> str:
        return "Get system information"
    
    @property
    def usage(self) -> str:
        return "sysinfo"
    
    def execute(self, args: List[str]) -> bool:
        info = get_sysinfo()
        logger.opt(colors=True).info(f"<g>CPU Usage:</g> <r>{info['cpu_usage']}</r>")
        logger.opt(colors=True).info(f"<g>CPU Counts:</g> <r>{info['cpu_counts']}</r>")
        logger.opt(colors=True).info(f"<g>CPU Frequency:</g> <r>{info['cpu_freq']}</r>")
        logger.opt(colors=True).info(f"<g>Memory Total:</g> <r>{info['mem_total']}</r>")
        logger.opt(colors=True).info(f"<g>Memory Usage:</g> <r>{info['mem_usage']}</r>")
        return True
