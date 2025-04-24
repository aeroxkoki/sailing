# -*- coding: utf-8 -*-
"""
プロジェクトスキーマ定義
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """プロジェクトベースモデル"""
    name: str = Field(..., description="プロジェクト名")
    description: Optional[str] = Field(None, description="プロジェクト説明")


class ProjectCreate(ProjectBase):
    """プロジェクト作成モデル"""
    pass


class ProjectUpdate(ProjectBase):
    """プロジェクト更新モデル"""
    name: Optional[str] = Field(None, description="プロジェクト名")


class Project(ProjectBase):
    """プロジェクトモデル"""
    id: UUID = Field(..., description="プロジェクトID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    user_id: UUID = Field(..., description="ユーザーID")
    
    class Config:
        from_attributes = True
