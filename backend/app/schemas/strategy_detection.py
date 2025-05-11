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


class StrategyPoint(BaseModel):
    """戦略ポイント"""
    id: UUID = Field(..., description="ID")
    timestamp: str = Field(..., description="タイムスタンプ")
    latitude: float = Field(..., description="緯度")
    longitude: float = Field(..., description="経度")
    strategy_type: StrategyType = Field(..., description="戦略タイプ")
    confidence: float = Field(..., description="信頼度（0-1）")
    details: dict = Field({}, description="詳細情報")
    
    class Config:
        use_enum_values = True


class PerformanceMetrics(BaseModel):
    """パフォーマンスメトリクス"""
    overall_score: float = Field(..., description="総合スコア（0-1）")
    maneuver_efficiency: float = Field(..., description="マニューバー効率（0-1）")
    wind_shift_response: float = Field(..., description="風向シフト対応（0-1）")
    layline_accuracy: float = Field(..., description="レイライン精度（0-1）")
    details: dict = Field({}, description="詳細情報")


class StrategyRecommendation(BaseModel):
    """戦略推奨事項"""
    title: str = Field(..., description="タイトル")
    description: str = Field(..., description="説明")
    priority: str = Field(..., description="優先度（high/medium/low）")
    category: str = Field(..., description="カテゴリ")


class StrategyDetectionResult(BaseModel):
    """戦略検出結果"""
    session_id: UUID = Field(..., description="セッションID")
    strategy_points: List[StrategyPoint] = Field([], description="戦略ポイントリスト")
    performance_metrics: Optional[PerformanceMetrics] = Field(None, description="パフォーマンスメトリクス")
    recommendations: List[StrategyRecommendation] = Field([], description="推奨事項リスト")
    summary: dict = Field({}, description="サマリー情報")
    created_at: str = Field(..., description="作成日時")
