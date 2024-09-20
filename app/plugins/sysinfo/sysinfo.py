import psutil

from . import router


@router.get("/")
def sysinfo():
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
