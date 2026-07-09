from fastapi import FastAPI

from app.api.v1.injuries import router as injuries_router

app = FastAPI(title="FootballIQ")

app.include_router(injuries_router, prefix="/api/v1")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "ok", "service": "FootballIQ"}
