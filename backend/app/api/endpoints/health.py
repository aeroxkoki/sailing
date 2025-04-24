# -*- coding: utf-8 -*-
"""
ヘルスチェックAPI
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.health_service import check_database, check_api_services

router = APIRouter()

@router.get(
    "/",
    response_class=JSONResponse,
    summary="システム状態を確認",
    description="APIサーバーの状態を確認します",
)
async def health_check():
    """
    システムの健全性をチェックします
    
    戻り値:
    - status: システム状態
    - version: APIバージョン
    - services: 各サービスのステータス
    """
    # データベース接続チェック
    db_status = await check_database()
    
    # 外部APIサービスチェック
    api_status = await check_api_services()
    
    return {
        "status": "ok",
        "version": settings.API_VERSION,
        "services": {
            "database": db_status,
            "api_services": api_status
        }
    }

@router.get(
    "/ping",
    response_class=JSONResponse,
    summary="簡易接続チェック",
    description="APIサーバーへの簡易接続チェック",
)
async def ping():
    """
    シンプルな接続チェック
    
    戻り値:
    - ping: "pong"
    """
    return {
        "ping": "pong"
    }
