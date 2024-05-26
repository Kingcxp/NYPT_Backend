from . import main, get_sysinfo


@main.route("/sysinfo")
def sysinfo():
    return get_sysinfo()
