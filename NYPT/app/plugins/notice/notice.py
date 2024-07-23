import os
import aiofiles

from typing import Tuple

from . import main
from .config import Config
from ...manager import suc, err, escape_tag


@main.route("/notice/total", methods=['GET'])
async def notice_total() -> Tuple[str, int]:
    """获取公告总数

    Returns:
        Tuple[str, int]: 200 OK
    """
    tot: int = 0
    for i in range(1, 100):
        if not os.path.exists(Config.file_path + f"notice{i}.html"):
            break
        tot += 1
    suc("GET", "/notice/total", f"200 OK")
    return str(tot), 200


@main.route("/notice/<int:page>", methods=['GET'])
async def notice(page: int) -> Tuple[str, int]:
    """获取指定编号的公告

    Args:
        page (int): 公告编号

    Returns:
        Tuple[str, int]: 找到文件返回 200(OK)，否则返回 404(Not Found)
    """
    page_path = Config.file_path + f"notice{page}.html"
    if not os.path.exists(page_path):
        err("GET", f"/notice/{escape_tag('<int:page>')}", f"404 Not Found: Notice not found.")
        return "", 404
    async with aiofiles.open(page_path, "r", encoding="utf-8") as f:
        content = await f.read()
    suc("GET", f"/notice/{escape_tag('<int:page>')}", f"200 OK")
    return content, 200
