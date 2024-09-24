from fastapi import APIRouter


router = APIRouter(
    prefix="/sysinfo",
    tags=["sysinfo"],
)
__router__ = router


from . import sysinfo
