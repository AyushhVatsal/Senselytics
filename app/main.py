from fastapi import FastAPI

from app.api.api import api_router
from app.core.config import settings
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}"
    }