# -*- coding: utf-8 -*-
"""
戦略検出サービス

セッションのGPSデータと風向風速データから戦略ポイントを検出
"""

import uuid
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from app.models.strategy_point import StrategyPoint as ModelStrategyPoint, StrategyDetectionResult as ModelStrategyDetectionResult
from app.schemas.strategy_detection import StrategyDetectionInput, StrategyDetectionResult, StrategyPoint, PerformanceMetrics, StrategyRecommendation, StrategyType
from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
from sailing_data_processor.strategy.points import WindShiftPoint, TackPoint, LaylinePoint

from fastapi import HTTPException, status

def detect_strategies(
    params: StrategyDetectionInput,
    user_id: UUID,
    db: Session
) -> StrategyDetectionResult:
    """
    戦略ポイントを検出
    
    Parameters:
    -----------
    params : StrategyDetectionInput
        戦略検出パラメータ
    user_id : UUID
        ユーザーID
    db : Session
        データベースセッション
        
    Returns:
    --------
    StrategyDetectionResult
        戦略検出結果
    """
    try:
        # TODO: セッションIDからGPSデータと風向データを取得
        # デモ用のサンプルデータを使用
        course_data = _get_demo_course_data()
        wind_field = _get_demo_wind_field()
        
        # 戦略検出のインスタンス作成
        detector = StrategyDetectorWithPropagation()
        
        # 戦略ポイントの検出
        # 風向変化の検出
        wind_shifts = detector.detect_wind_shifts_with_propagation(
            course_data=course_data,
            wind_field=wind_field
        )
        
        # 最適タックポイント検出
        tack_points = detector.detect_optimal_tacks(
            course_data=course_data,
            wind_field=wind_field
        )
        
        # レイラインポイント検出
        layline_points = detector.detect_laylines(
            course_data=course_data,
            wind_field=wind_field
        )
        
        # 結果の変換
        strategy_points = _convert_to_strategy_points(
            wind_shifts=wind_shifts,
            tack_points=tack_points,
            layline_points=layline_points
        )
        
        # 検出感度による絞り込み
        filtered_points = _filter_by_sensitivity(
            strategy_points=strategy_points,
            sensitivity=params.detection_sensitivity
        )
        
        # 結果の作成
        result = _create_strategy_detection_result(
            strategy_points=filtered_points,
            session_id=str(params.session_id)
        )
        
        # TODO: 結果をデータベースに保存
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"戦略検出エラー: {str(e)}"
        )

def _get_demo_course_data() -> Dict[str, Any]:
    """
    デモ用のコースデータを生成
    
    Returns:
    --------
    Dict[str, Any]
        コースデータ
    """
    # 仮想データ
    return {
        "start_time": datetime.now(),
        "legs": [
            {
                "path": {
                    "path_points": [
                        {"lat": 35.0, "lon": 139.0},
                        {"lat": 35.1, "lon": 139.1}
                    ]
                }
            }
        ]
    }

def _get_demo_wind_field() -> Dict[str, Any]:
    """
    デモ用の風場データを生成
    
    Returns:
    --------
    Dict[str, Any]
        風場データ
    """
    import numpy as np
    
    # 仮想データ
    lat_grid, lon_grid = np.meshgrid(
        np.linspace(34.9, 35.2, 10),
        np.linspace(138.9, 139.2, 10)
    )
    
    return {
        "time": datetime.now(),
        "lat_grid": lat_grid,
        "lon_grid": lon_grid,
        "wind_direction": np.ones_like(lat_grid) * 270.0,  # 西風
        "wind_speed": np.ones_like(lat_grid) * 10.0,  # 10ノット
        "confidence": np.ones_like(lat_grid) * 0.8  # 信頼度80%
    }

def _convert_to_strategy_points(
    wind_shifts: List,
    tack_points: List,
    layline_points: List
) -> List[StrategyPoint]:
    """
    検出された各ポイントを共通フォーマットに変換
    
    Parameters:
    -----------
    wind_shifts : List
        風向変化ポイントリスト
    tack_points : List
        タックポイントリスト
    layline_points : List
        レイラインポイントリスト
        
    Returns:
    --------
    List[StrategyPoint]
        共通フォーマットの戦略ポイント
    """
    strategy_points = []
    
    # 風向変化ポイントの変換
    for point in wind_shifts:
        strategy_points.append(StrategyPoint(
            id=uuid.uuid4(),
            timestamp=point.time_estimate.isoformat(),
            latitude=point.position[0],
            longitude=point.position[1],
            strategy_type=StrategyType.WIND_SHIFT,
            confidence=point.shift_probability,
            details={
                "shift_angle": point.shift_angle,
                "before_direction": point.before_direction,
                "after_direction": point.after_direction,
                "strategic_score": point.strategic_score
            }
        ))
    
    # タックポイントの変換
    for point in tack_points:
        strategy_points.append(StrategyPoint(
            id=uuid.uuid4(),
            timestamp=point.time_estimate.isoformat(),
            latitude=point.position[0],
            longitude=point.position[1],
            strategy_type=StrategyType.TACK,
            confidence=0.8,  # 固定値
            details={
                "vmg_gain": point.vmg_gain if hasattr(point, 'vmg_gain') else 0.0,
                "strategic_score": point.strategic_score if hasattr(point, 'strategic_score') else 0.0
            }
        ))
    
    # レイラインポイントの変換
    for point in layline_points:
        strategy_points.append(StrategyPoint(
            id=uuid.uuid4(),
            timestamp=point.time_estimate.isoformat(),
            latitude=point.position[0],
            longitude=point.position[1],
            strategy_type=StrategyType.LAYLINE,
            confidence=point.confidence if hasattr(point, 'confidence') else 0.8,
            details={
                "mark_id": point.mark_id if hasattr(point, 'mark_id') else "",
                "strategic_score": point.strategic_score if hasattr(point, 'strategic_score') else 0.0
            }
        ))
    
    return strategy_points

def _filter_by_sensitivity(
    strategy_points: List[StrategyPoint],
    sensitivity: float
) -> List[StrategyPoint]:
    """
    検出感度による戦略ポイントのフィルタリング
    
    Parameters:
    -----------
    strategy_points : List[StrategyPoint]
        戦略ポイントリスト
    sensitivity : float
        検出感度（0-1）
        
    Returns:
    --------
    List[StrategyPoint]
        フィルタリングされた戦略ポイント
    """
    # 検出感度に基づく信頼度の閾値計算
    # 感度が高いほど低い信頼度のポイントも検出される
    confidence_threshold = 1.0 - sensitivity
    
    filtered_points = [
        point for point in strategy_points
        if point.confidence >= confidence_threshold
    ]
    
    return filtered_points

def _create_strategy_detection_result(
    strategy_points: List[StrategyPoint],
    session_id: str
) -> StrategyDetectionResult:
    """
    戦略検出結果をAPIレスポンス形式に変換
    
    Parameters:
    -----------
    strategy_points : List[StrategyPoint]
        検出された戦略ポイント
    session_id : str
        セッションID
        
    Returns:
    --------
    StrategyDetectionResult
        APIレスポンス形式の戦略検出結果
    """
    # 各種ポイントの集計
    tack_count = sum(1 for p in strategy_points if p.strategy_type == StrategyType.TACK)
    jibe_count = sum(1 for p in strategy_points if p.strategy_type == StrategyType.JIBE)
    wind_shift_count = sum(1 for p in strategy_points if p.strategy_type == StrategyType.WIND_SHIFT)
    layline_count = sum(1 for p in strategy_points if p.strategy_type == StrategyType.LAYLINE)
    
    # 推奨事項の生成
    recommendations = _generate_recommendations(strategy_points)
    
    # パフォーマンスメトリクスの仮作成
    performance_metrics = PerformanceMetrics(
        overall_score=0.75,  # TODO: 実際の計算を実装
        maneuver_efficiency=0.8,
        wind_shift_response=0.7,
        layline_accuracy=0.85,
        details={
            "tack_count": tack_count,
            "jibe_count": jibe_count,
            "wind_shift_count": wind_shift_count
        }
    )
    
    # サマリー作成
    summary = {
        "total_points": len(strategy_points),
        "strategy_types": {
            "tack": tack_count,
            "jibe": jibe_count,
            "wind_shift": wind_shift_count,
            "layline": layline_count
        }
    }
    
    # 結果作成
    result = StrategyDetectionResult(
        session_id=UUID(session_id),
        strategy_points=strategy_points,
        performance_metrics=performance_metrics,
        recommendations=recommendations,
        summary=summary,
        created_at=datetime.now().isoformat()
    )
    
    return result

def _generate_recommendations(strategy_points: List[StrategyPoint]) -> List[StrategyRecommendation]:
    """
    戦略ポイントに基づく推奨事項を生成
    
    Parameters:
    -----------
    strategy_points : List[StrategyPoint]
        戦略ポイント
        
    Returns:
    --------
    List[StrategyRecommendation]
        推奨事項のリスト
    """
    recommendations = []
    
    # 風向変化の分析に基づく推奨
    wind_shifts = [p for p in strategy_points if p.strategy_type == StrategyType.WIND_SHIFT]
    if len(wind_shifts) > 0:
        recommendations.append(StrategyRecommendation(
            title="風向変化への対応",
            description=f"{len(wind_shifts)}回の風向変化が検出されました。風の変化に早く対応するようタックタイミングを最適化しましょう。",
            priority="high",
            category="wind_analysis"
        ))
    
    # タック数に基づく推奨
    tack_points = [p for p in strategy_points if p.strategy_type == StrategyType.TACK]
    if len(tack_points) > 5:
        recommendations.append(StrategyRecommendation(
            title="タック数の最適化",
            description="タック数が多めです。風の変化を正確に読んでタック回数を減らしましょう。",
            priority="medium",
            category="maneuver"
        ))
    elif len(tack_points) < 2 and len(strategy_points) > 0:
        recommendations.append(StrategyRecommendation(
            title="タック回数不足",
            description="タック数が少ないです。風の振れに合わせたタックでVMGを向上させる機会があるかもしれません。",
            priority="medium",
            category="maneuver"
        ))
    
    # レイラインに基づく推奨
    layline_points = [p for p in strategy_points if p.strategy_type == StrategyType.LAYLINE]
    if len(layline_points) > 0:
        recommendations.append(StrategyRecommendation(
            title="レイライン戦略",
            description="レイラインに到達しています。風の変化に注意してタックのタイミングを調整する機会があります。",
            priority="low",
            category="tactics"
        ))
    
    return recommendations
