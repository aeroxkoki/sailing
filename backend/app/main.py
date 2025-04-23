"""
FastAPI メインアプリケーション
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.v1.api import api_router
from app.core.config import settings

# FastAPIアプリケーション作成
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.API_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS設定
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Gzip圧縮
app.add_middleware(GZipMiddleware, minimum_size=1000)

# APIルータ登録
app.include_router(api_router, prefix=settings.API_V1_STR)

# ルートパス
@app.get("/")
async def root():
    """
    ルートパスへのアクセス
    """
    return {
        "message": "セーリング戦略分析システム API",
        "version": settings.API_VERSION,
        "docs": "/docs",
    }
