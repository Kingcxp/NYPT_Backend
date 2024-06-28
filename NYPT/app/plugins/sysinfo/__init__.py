import psutil

from flask import Blueprint
from typing import Dict, Any


def get_sysinfo() -> Dict[str, Any]:
    cpu_usage: float = psutil.cpu_percent()
    cpu_cores: int = psutil.cpu_count()
    cpu_freq: psutil.scpufreq = psutil.cpu_freq()
    memory_usage: float = psutil.virtual_memory().percent
    memory_total: float = float(psutil.virtual_memory().total) / float(10000)
    return {
        "cpu_usage": cpu_usage,
        "cpu_counts": cpu_cores,
        "cpu_freq": cpu_freq,
        "mem_total": memory_total,
        "mem_usage": memory_usage
    }


from .commands import *


main = Blueprint('sysinfo', __name__)
__blueprint__ = main
__commands__ = [
    SystemInfo()
]


from . import sysinfo
