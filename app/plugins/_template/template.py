from fastapi import status
from fastapi.responses import PlainTextResponse

from . import router


@router.get("/")
async def template():
    return PlainTextResponse("This is a template plugin.", status.HTTP_200_OK)
