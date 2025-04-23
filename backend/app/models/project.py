"""
プロジェクトSQLAlchemyモデル
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base.base_class import Base


class Project(Base):
    """プロジェクトテーブルモデル"""
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    def __repr__(self):
        return f"<Project(id={self.id}, name={self.name})>"
