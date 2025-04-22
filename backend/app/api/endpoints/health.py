"""
ヘルスチェックエンドポイント
"""

from fastapi import APIRouter, Depends, Request
from datetime import datetime
import os
import sys

from app.db.database import check_db_connection

router = APIRouter()

@router.get("/", summary="APIヘルスチェック")
async def api_health_check():
    """
    APIの健全性チェックエンドポイント。
    システムの状態、バージョン、DBの接続状態などを返します。
    """
    health_data = {
        "status": "healthy",
        "api_version": "v1",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("APP_ENV", "development"),
        "python_version": sys.version,
    }
    
    # データベース接続チェック
    try:
        db_status = await check_db_connection()
        health_data["database"] = db_status
    except Exception as e:
        health_data["database"] = {
            "status": "error", 
            "message": str(e)
        }
    
    return health_data

@router.get("/check", summary="簡易ヘルスチェック")
async def simple_health_check():
    """
    単純なヘルスチェックエンドポイント。
    監視システムからの呼び出し用に最小限の情報のみを返します。
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }
