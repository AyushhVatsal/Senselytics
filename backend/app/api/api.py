from fastapi import APIRouter

from app.api.routes import (
    auth,
    datasets,
    health,
    users,
    queries
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(datasets.router)
api_router.include_router(queries.router)