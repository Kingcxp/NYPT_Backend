from . import main, get_sysinfo


@main.route("/sysinfo")
async def sysinfo():
    return get_sysinfo()
