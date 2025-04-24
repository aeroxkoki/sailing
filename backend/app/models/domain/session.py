# -*- coding: utf-8 -*-
"""
セッションモデル
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class SessionBase(BaseModel):
    """セッションベースモデル"""
    name: str = Field(..., description="セッション名")
    description: Optional[str] = Field(None, description="セッション説明")
    date: datetime = Field(..., description="セッション日時")
    location: Optional[str] = Field(None, description="場所")
    weather_conditions: Optional[Dict[str, Any]] = Field(None, description="気象条件")


class SessionCreate(SessionBase):
    """セッション作成モデル"""
    project_id: UUID = Field(..., description="プロジェクトID")
    gps_data_file: Optional[str] = Field(None, description="GPSデータファイル")


class SessionUpdate(BaseModel):
    """セッション更新モデル"""
    name: Optional[str] = Field(None, description="セッション名")
    description: Optional[str] = Field(None, description="セッション説明")
    date: Optional[datetime] = Field(None, description="セッション日時")
    location: Optional[str] = Field(None, description="場所")
    weather_conditions: Optional[Dict[str, Any]] = Field(None, description="気象条件")
    wind_estimation_id: Optional[UUID] = Field(None, description="風推定ID")
    strategy_detection_id: Optional[UUID] = Field(None, description="戦略検出ID")


class Session(SessionBase):
    """セッションモデル"""
    id: UUID = Field(..., description="セッションID")
    project_id: UUID = Field(..., description="プロジェクトID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    user_id: UUID = Field(..., description="ユーザーID")
    gps_data_file: Optional[str] = Field(None, description="GPSデータファイル")
    wind_estimation_id: Optional[UUID] = Field(None, description="風推定ID")
    strategy_detection_id: Optional[UUID] = Field(None, description="戦略検出ID")
    
    class Config:
        from_attributes = True
