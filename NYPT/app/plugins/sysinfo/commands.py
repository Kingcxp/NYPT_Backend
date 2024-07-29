from typing import List
from . import get_sysinfo
from ...manager import CommandInterface, console


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
        console.info(f"[green]CPU Usage:[/green] [yellow]{info['cpu_usage']}[/yellow]")
        console.info(f"[green]CPU Counts:[/green] [yellow]{info['cpu_counts']}[/yellow]")
        console.info(f"[green]CPU Frequency:[/green] [yellow]{info['cpu_freq']}[/yellow]")
        console.info(f"[green]Memory Total:[/green] [yellow]{info['mem_total']}[/yellow]")
        console.info(f"[green]Memory Usage:[/green] [yellow]{info['mem_usage']}[/yellow]")
        return True
