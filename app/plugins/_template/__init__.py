from fastapi import APIRouter


router = APIRouter(
    prefix="/template",
    tags=["template"],
)
__router__ = router
