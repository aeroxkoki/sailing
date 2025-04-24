# -*- coding: utf-8 -*-
"""
APIルータ設定
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    projects,
    sessions,
    users,
    data_import,
    wind_estimation,
    strategy_detection,
)

api_router = APIRouter()

# ヘルスチェック
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

# プロジェクト管理
api_router.include_router(
    projects.router,
    prefix="/projects",
    tags=["projects"]
)

# セッション管理
api_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["sessions"]
)

# ユーザー管理
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

# データインポート
api_router.include_router(
    data_import.router,
    prefix="/data-import",
    tags=["data-import"]
)

# 風速推定
api_router.include_router(
    wind_estimation.router,
    prefix="/wind-estimation",
    tags=["wind-estimation"]
)

# 戦略検出
api_router.include_router(
    strategy_detection.router,
    prefix="/strategy-detection",
    tags=["strategy-detection"]
)
