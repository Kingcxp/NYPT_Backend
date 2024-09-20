from fastapi import APIRouter
from typing import Dict, Any


router = APIRouter(
    prefix="/sysinfo",
    tags=["sysinfo"],
    responses={ 404: {"description": "Not Found"} }
)
__router__ = router


from . import sysinfo
