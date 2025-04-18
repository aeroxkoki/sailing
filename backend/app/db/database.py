"""
Çü¿Ùü¹¥šâ¸åüë
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


# SQLAlchemy(-š
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# ¨ó¸ó
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ^¨ó¸ó (^æLÅj4)
async_database_url = SQLALCHEMY_DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
async_engine = create_async_engine(async_database_url)
AsyncSessionLocal = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)

# Ùü¹âÇë
Base = declarative_base()
metadata = MetaData()

# Supabase¥š¯é¤¢óÈ
supabase: Optional[Client] = None


def init_supabase() -> Client:
    """Supabase¯é¤¢óÈ’Y‹"""
    global supabase
    
    if supabase is None and settings.SUPABASE_URL and settings.SUPABASE_KEY:
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    
    return supabase


def get_supabase() -> Client:
    """Supabase¯é¤¢óÈ’Ö—Y‹"""
    if supabase is None:
        return init_supabase()
    return supabase


def get_db():
    """Çü¿Ùü¹»Ã·çó’Ö—Y‹"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db():
    """^Çü¿Ùü¹»Ã·çó’Ö—Y‹"""
    async with AsyncSessionLocal() as session:
        yield session


# Supabase¯é¤¢óÈn
init_supabase()
