from typing import Tuple

from . import main
from .config import Config
from ...manager import suc, err, escape_tag


@main.route("/notice/total", methods=['GET'])
def notice_total() -> Tuple[str, int]:
    tot: int = 0
    for i in range(1, 100):
        try:
            f = open(Config.file_path + f"notice{i}.html", "r")
        except:
            break
        f.close()
        tot += 1
    suc("GET", "/notice/total", f"200 OK")
    return str(tot), 200


@main.route("/notice/<int:page>", methods=['GET'])
def notice(page: int) -> Tuple[str, int]:
    page_path = Config.file_path + f"notice{page}.html"
    try:
        f = open(page_path, "r")
    except:
        err("GET", f"/notice/{escape_tag('<int:page>')}", f"404 Not Found: Notice not found.")
        return "", 404
    lines = f.readlines()
    f.close()
    suc("GET", f"/notice/{escape_tag('<int:page>')}", f"200 OK")
    return "\n".join(lines), 200
