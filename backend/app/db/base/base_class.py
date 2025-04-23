"""
ベースSQLAlchemyモデル
"""

from typing import Any
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


@as_declarative()
class Base:
    """
    SQLAlchemyベースクラス
    """
    id: Any
    __name__: str
    
    # テーブル名をクラス名から自動生成
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"
    
    # 共通カラム
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
