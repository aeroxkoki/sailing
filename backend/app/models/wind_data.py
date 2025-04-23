"""
風データモデル
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class WindDataPoint(BaseModel):
    """風データポイント"""
    timestamp: datetime = Field(..., description="タイムスタンプ")
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="経度")
    speed: float = Field(..., description="風速（ノット）")
    direction: float = Field(..., description="風向（度）")
    confidence: float = Field(1.0, description="信頼度（0-1）")


class WindEstimationResult(BaseModel):
    """風推定結果"""
    wind_data: List[WindDataPoint] = Field(..., description="風データポイント")
    average_speed: float = Field(..., description="平均風速（ノット）")
    average_direction: float = Field(..., description="平均風向（度）")
    created_at: datetime = Field(..., description="作成日時")
    session_id: Optional[str] = Field(None, description="セッションID")


class WindPattern(BaseModel):
    """風のパターン"""
    pattern_type: str = Field(..., description="パターンタイプ")
    start_time: datetime = Field(..., description="開始時間")
    end_time: datetime = Field(..., description="終了時間")
    average_speed: float = Field(..., description="平均風速（ノット）")
    average_direction: float = Field(..., description="平均風向（度）")
    variation: float = Field(..., description="変動幅（度）")
    description: Optional[str] = Field(None, description="説明")
