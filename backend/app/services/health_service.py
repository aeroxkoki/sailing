"""
ヘルスチェックサービス

システムの健全性をチェックする機能を提供
"""

import logging
from typing import Dict, Any
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.db.session import get_async_db

logger = logging.getLogger(__name__)

async def check_database() -> Dict[str, Any]:
    """
    データベース接続の状態をチェック
    
    戻り値:
    - status: 接続状態 ("ok" または "error")
    - message: 詳細メッセージ
    - latency_ms: 応答時間（ミリ秒）
    """
    import time
    
    try:
        # セッションを取得
        session = await anext(get_async_db())
        
        # 開始時間を記録
        start_time = time.time()
        
        # 単純なクエリを実行
        result = await session.execute(text("SELECT 1"))
        row = result.scalar()
        
        # 終了時間を記録し、レイテンシを計算
        end_time = time.time()
        latency_ms = round((end_time - start_time) * 1000, 2)
        
        if row == 1:
            return {
                "status": "ok",
                "message": "データベース接続正常",
                "latency_ms": latency_ms
            }
        else:
            return {
                "status": "error",
                "message": "データベースから予期しない応答",
                "latency_ms": latency_ms
            }
            
    except Exception as e:
        logger.error(f"データベース接続エラー: {str(e)}")
        return {
            "status": "error",
            "message": f"データベース接続エラー: {str(e)}",
            "latency_ms": None
        }

async def check_api_services() -> Dict[str, Any]:
    """
    外部APIサービスの状態をチェック
    
    戻り値:
    - status: 全体の状態 ("ok" または "error")
    - services: 各サービスの状態
    """
    # 本番では実際の外部APIをチェックする
    # このサンプル実装ではダミーの結果を返す
    
    return {
        "status": "ok",
        "services": {
            "supabase": {
                "status": "ok",
                "message": "Supabase接続正常"
            },
            "file_storage": {
                "status": "ok",
                "message": "ファイルストレージ接続正常"
            }
        }
    }
