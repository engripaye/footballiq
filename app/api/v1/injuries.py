from fastapi import APIRouter
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    pass


router = APIRouter(prefix="/injuries", tags=["injuries"])


@router.get("/")
def list_injuries() -> dict[str, list[dict[str, str]]]:
    return {"injuries": []}
