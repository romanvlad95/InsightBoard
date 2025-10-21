from fastapi import APIRouter

from app.api.v1.endpoints import metrics, websocket
from app.api.v1.routers import auth, dashboards

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["dashboards"])
api_router.include_router(websocket.router, tags=["websocket"])
