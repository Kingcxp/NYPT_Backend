from fastapi import APIRouter


router = APIRouter(
    prefix="/notice",
    tags=["notice"],
)
__router__ = router
