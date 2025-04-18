"""
データベース接続設定
"""

import os
from typing import Any, Dict, Optional, List
from supabase import create_client, Client
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.utils.encoding_utils import normalize_japanese_text


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


def init_supabase() -> Client:
    """Supabaseクライアントの初期化"""
    global supabase
    
    if supabase is None and settings.SUPABASE_URL and settings.SUPABASE_KEY:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    return supabase


def get_supabase() -> Client:
    """Supabaseクライアントの取得"""
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


# Supabaseクライアントの初期化
init_supabase()
