# -*- coding: utf-8 -*-
"""
戦略検出スキーマ

戦略検出APIで使用するスキーマを定義
"""

from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class StrategyType(str, Enum):
    """戦略タイプ"""
    WIND_SHIFT = "wind_shift"  # 風向シフト
    TACK = "tack"              # タック
    JIBE = "jibe"              # ジャイブ
    LAYLINE = "layline"        # レイライン
    START = "start"            # スタート
    FINISH = "finish"          # フィニッシュ
    MARK_ROUNDING = "mark_rounding"  # マーク回航


class StrategyDetectionInput(BaseModel):
    """戦略検出入力パラメータ"""
    session_id: UUID = Field(..., description="セッションID")
    wind_estimation_id: Optional[UUID] = Field(None, description="風推定ID")
    detection_sensitivity: float = Field(0.5, description="検出感度（0-1）")
    min_tack_angle: float = Field(45.0, description="最小タック角度（度）")
    min_jibe_angle: float = Field(45.0, description="最小ジャイブ角度（度）")
    strategy_types: Optional[List[StrategyType]] = Field(
        None, 
        description="検出する戦略タイプ（指定がない場合はすべて）"
    )

    class Config:
        use_enum_values = True


class StrategyAnalysisOptions(BaseModel):
    """戦略分析オプション"""
    compare_with_optimal: bool = Field(False, description="最適航路と比較するかどうか")
    calculate_performance_score: bool = Field(True, description="パフォーマンススコアを計算するかどうか")
    generate_recommendations: bool = Field(True, description="推奨事項を生成するかどうか")
    detailed_analysis: bool = Field(False, description="詳細分析を行うかどうか")
