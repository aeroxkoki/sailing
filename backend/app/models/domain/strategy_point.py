# -*- coding: utf-8 -*-
"""
戦略ポイントモデル
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class StrategyPoint(BaseModel):
    """戦略ポイント"""
    timestamp: datetime = Field(..., description="タイムスタンプ")
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="経度")
    strategy_type: str = Field(..., description="戦略タイプ")
    confidence: float = Field(1.0, description="信頼度（0-1）")
    metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータ")


class StrategyDetectionResult(BaseModel):
    """戦略検出結果"""
    strategy_points: List[StrategyPoint] = Field(..., description="戦略ポイント")
    created_at: datetime = Field(..., description="作成日時")
    session_id: Optional[str] = Field(None, description="セッションID")
    track_length: Optional[float] = Field(None, description="航跡の長さ（メートル）")
    total_tacks: Optional[int] = Field(None, description="タックの総数")
    total_jibes: Optional[int] = Field(None, description="ジャイブの総数")
    upwind_percentage: Optional[float] = Field(None, description="アップウィンド割合（%）")
    downwind_percentage: Optional[float] = Field(None, description="ダウンウィンド割合（%）")
    reaching_percentage: Optional[float] = Field(None, description="リーチング割合（%）")
    performance_score: Optional[float] = Field(None, description="パフォーマンススコア（0-100）")
    recommendations: Optional[List[str]] = Field(None, description="推奨事項")


class StrategyDetectionInput(BaseModel):
    """戦略検出入力"""
    session_id: UUID = Field(..., description="セッションID")
    wind_estimation_id: Optional[UUID] = Field(None, description="風推定ID")
    detection_sensitivity: Optional[float] = Field(0.5, description="検出感度（0-1）")
    min_tack_angle: Optional[float] = Field(45.0, description="最小タック角度（度）")
    min_jibe_angle: Optional[float] = Field(45.0, description="最小ジャイブ角度（度）")
