"""
API��������
"""

from fastapi import APIRouter

from app.core.config import settings
from app.api.endpoints import (
    wind_estimation,
    strategy_detection,
    data_import,
    projects,
    sessions,
    users,
)


# API����n\
api_router = APIRouter()

# ���ݤ��n�����������k{2
api_router.include_router(
    wind_estimation.router,
    prefix="/wind-estimation",
    tags=["wind estimation"]
)

api_router.include_router(
    strategy_detection.router,
    prefix="/strategy-detection",
    tags=["strategy detection"]
)

api_router.include_router(
    data_import.router,
    prefix="/data-import",
    tags=["data import"]
)

api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

api_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["sessions"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)
