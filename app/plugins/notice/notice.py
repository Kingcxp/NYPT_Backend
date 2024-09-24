import os
import aiofiles

from fastapi import status
from fastapi.responses import PlainTextResponse

from . import router


@router.get("/total")
async def notice_total() -> PlainTextResponse:
    """获取公告总数

    Returns:
        PlainTextResponse: 转为字符串的数字，表示一共有多少个公告，状态码: 200 OK
    """
    tot: int = 0
    for i in range(0, 100):
        if not os.path.exists(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                f"notice{i}.html"
            )
        ):
            break
        tot += 1
    return PlainTextResponse(str(tot), status_code=status.HTTP_200_OK)


@router.get("/{page}")
async def notice(page: int) -> PlainTextResponse:
    """
    获取指定编号的公告

    Args:
        page (int): 公告编号

    Returns:
        PlainTextResponse: 公告内容，状态码: 200 OK 或 404 Not Found(未找到公告)
    """
    page_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"notice{page}.html"
    )
    if not os.path.exists(page_path):
        return PlainTextResponse(
            "",
            status_code=status.HTTP_404_NOT_FOUND
        )
    async with aiofiles.open(page_path, "r", encoding="utf-8") as f:
        content = await f.read()
    return PlainTextResponse(content, status_code=status.HTTP_200_OK)
