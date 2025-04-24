# -*- coding: utf-8 -*-
"""
データベース接続設定
"""

import os
import logging
from datetime import datetime
from typing import Any, Dict, Optional, List
from supabase import create_client, Client
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.utils.encoding_utils import normalize_japanese_text
from app.utils.error_handling import safe_external_call, SupabaseError

# ロガーの設定
logger = logging.getLogger(__name__)

# SQLAlchemy接続設定
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# テキストエンコーディングを明示的に指定
connection_args = {
    "client_encoding": "utf8",
    "connect_timeout": 30,
    "pool_size": 10,
    "max_overflow": 20
}

# データベースエンジン
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args=connection_args,
    echo=settings.DEBUG
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 非同期データベースエンジン (非同期APIのサポート)
async_database_url = SQLALCHEMY_DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
async_engine = create_async_engine(
    async_database_url,
    echo=settings.DEBUG,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
AsyncSessionLocal = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)

# モデルベース
Base = declarative_base()
metadata = MetaData()

# Supabaseクライアントインスタンス
supabase: Optional[Client] = None


@safe_external_call(
    error_message="Supabaseクライアントの初期化に失敗しました",
    service_name="supabase",
    raise_error=False
)
def _create_supabase_client(
    url: str, 
    key: str, 
    use_options: bool = True
) -> Optional[Client]:
    """
    Supabaseクライアントを作成する内部関数
    
    Args:
        url: SupabaseのURL
        key: Supabaseのアクセスキー
        use_options: オプションオブジェクトを使用するかどうか
        
    Returns:
        Client: Supabaseクライアントインスタンス
    """
    if use_options:
        try:
            from supabase.lib.client_options import SyncClientOptions
            options = SyncClientOptions()
            return create_client(
                supabase_url=url,
                supabase_key=key,
                options=options
            )
        except ImportError:
            # ライブラリのバージョンが古い場合は通常の方法で作成を試みる
            logger.warning("SyncClientOptions not found, trying without options")
            return create_client(url, key)
    else:
        # 基本的なパラメータのみで初期化
        return create_client(url, key)


def init_supabase() -> Optional[Client]:
    """
    Supabaseクライアントの初期化を行い、失敗した場合は代替方法を試みる
    
    Returns:
        Optional[Client]: 初期化されたSupabaseクライアントまたはNone
    """
    global supabase
    
    if supabase is not None:
        return supabase
    
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning("Supabase settings are not configured")
        return None
    
    # 初期化戦略のリスト（優先順位順）
    strategies = [
        # 戦略1: オプションオブジェクトを使用した初期化
        lambda: _create_supabase_client(settings.SUPABASE_URL, settings.SUPABASE_KEY, use_options=True),
        # 戦略2: 基本的なパラメータのみで初期化
        lambda: _create_supabase_client(settings.SUPABASE_URL, settings.SUPABASE_KEY, use_options=False),
    ]
    
    # 各戦略を順番に試す
    for strategy_index, strategy in enumerate(strategies):
        try:
            client = strategy()
            if client:
                logger.info(f"Supabase client initialized using strategy {strategy_index + 1}")
                supabase = client
                return supabase
        except Exception as e:
            logger.warning(f"Supabase initialization strategy {strategy_index + 1} failed: {str(e)}")
    
    logger.error("All Supabase initialization strategies failed")
    return None


def get_supabase() -> Optional[Client]:
    """
    Supabaseクライアントの取得。未初期化の場合は初期化を試みる
    
    Returns:
        Optional[Client]: Supabaseクライアントまたはnone
    """
    if supabase is None:
        return init_supabase()
    return supabase


def get_db():
    """データベースセッションの取得"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """非同期データベースセッションの取得"""
    async with AsyncSessionLocal() as session:
        yield session


# 文字列正規化関数
def normalize_db_strings(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    データベースから取得した辞書内の文字列を正規化
    
    Args:
        data: データベースから取得した辞書データ
        
    Returns:
        正規化された辞書データ
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = normalize_japanese_text(value)
        elif isinstance(value, dict):
            result[key] = normalize_db_strings(value)
        elif isinstance(value, list):
            result[key] = [
                normalize_db_strings(item) if isinstance(item, dict) 
                else normalize_japanese_text(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            result[key] = value
    return result


# データベース接続チェック関数
async def check_db_connection() -> Dict[str, Any]:
    """
    データベースとSupabase接続の状態をチェック
    
    Returns:
        接続状態を含む辞書
    """
    result = {
        "status": "error",
        "message": "接続チェックできませんでした",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("APP_ENV", "development"),
        "database_url": SQLALCHEMY_DATABASE_URL.replace(
            # 機密情報を隠す
            SQLALCHEMY_DATABASE_URL.split("@")[0] if "@" in SQLALCHEMY_DATABASE_URL else "",
            "***"
        ) if SQLALCHEMY_DATABASE_URL else "未設定"
    }
    
    # SQLAlchemy接続チェック
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            result["status"] = "connected"
            result["message"] = "データベース接続成功"
            
            # テーブル情報の取得を試みる
            try:
                tables_result = await session.execute("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'public'")
                tables = [row[0] for row in tables_result.fetchall()]
                result["tables_count"] = len(tables)
            except Exception:
                # テーブル情報取得失敗は重大ではない
                pass
    except Exception as e:
        result["status"] = "error"
        result["message"] = f"データベース接続エラー: {str(e)}"
        return result
    
    # Supabase接続チェック
    try:
        sb_client = get_supabase()
        if sb_client:
            # 単純なクエリでSupabase接続をテスト
            try:
                health_check = sb_client.table('health_check').select('*').limit(1).execute()
                result["supabase"] = {
                    "status": "connected",
                    "message": "Supabase接続成功"
                }
            except Exception as e:
                # テーブルが存在しなくてもエラーになるので、別のアプローチを試みる
                try:
                    # 認証状態をチェック
                    auth_check = sb_client.auth.get_user()
                    result["supabase"] = {
                        "status": "connected",
                        "message": "Supabase認証接続成功"
                    }
                except Exception as inner_e:
                    result["supabase"] = {
                        "status": "partial",
                        "message": f"Supabase部分接続: {str(inner_e)}"
                    }
        else:
            result["supabase"] = {
                "status": "not_configured",
                "message": "Supabase未設定"
            }
    except Exception as e:
        result["supabase"] = {
            "status": "error",
            "message": f"Supabase接続エラー: {str(e)}"
        }
    
    return result

# Supabaseクライアントの初期化
init_supabase()
