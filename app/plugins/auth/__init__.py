from fastapi import APIRouter

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)
__router__ = router
