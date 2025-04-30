# -*- coding: utf-8 -*-
"""
StrategyDetectorWithPropagation 

風の場の移動予測を考慮した戦略検出器モジュール
"""

import numpy as np
import math
import warnings
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
from functools import lru_cache

# 内部モジュールのインポート
from sailing_data_processor.strategy.detector import StrategyDetector
from sailing_data_processor.strategy.points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint
from sailing_data_processor.strategy.strategy_detector_utils import (
    calculate_distance, get_time_difference_seconds, normalize_to_timestamp,
    filter_duplicate_shift_points, filter_duplicate_tack_points, filter_duplicate_laylines,
    calculate_strategic_score, determine_tack_type, angle_difference
)

# ロガー設定
logger = logging.getLogger(__name__)

class StrategyDetectorWithPropagation(StrategyDetector):
    """
    風の場の移動予測を考慮した戦略検出器
    
    StrategyDetectorの機能に加えて、風の場の
    将来的な移動を考慮します。
    """
    
    def __init__(self, vmg_calculator=None, wind_fusion_system=None):
        """
        初期化
        
        Parameters:
        -----------
        vmg_calculator : OptimalVMGCalculator, optional
            VMG計算器
        wind_fusion_system : WindFieldFusionSystem, optional
            風統合システム
        """
        # 親クラス初期化
        super().__init__(vmg_calculator)
        
        # 風統合システム設定
        self.wind_fusion_system = wind_fusion_system
        
        # 移動予測設定
        self.propagation_config = {
            'wind_shift_prediction_horizon': 1800,  # 風向変化予測時間（秒）
            'prediction_time_step': 300,           # 予測ステップ（秒）
            'wind_shift_confidence_threshold': 0.7, # 風向シフト確信度
            'min_propagation_distance': 1000,      # 最小移動距離（m）
            'prediction_confidence_decay': 0.1,    # 予測確信度の時間による減衰率
            'use_historical_data': True            # 過去データ使用
        }
    
    def detect_wind_shifts_with_propagation(self, course_data: Dict[str, Any], 
                                         wind_field: Dict[str, Any]) -> List[WindShiftPoint]:
        """
        風の場の移動予測を考慮した風向シフト検出
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コースデータ
        wind_field : Dict[str, Any]
            風の場データ
            
        Returns:
        --------
        List[WindShiftPoint]
            検出された風向シフト
        """
        if not wind_field or 'wind_direction' not in wind_field:
            return []
        
        # 風統合システムがあれば、予測風向シフトを取得
        predicted_shifts = []
        
        if self.wind_fusion_system and hasattr(self.wind_fusion_system, 'predict_wind_field'):
            try:
                # 基準時間
                reference_time = None
                if 'time' in wind_field:
                    reference_time = wind_field['time']
                elif 'start_time' in course_data:
                    reference_time = course_data['start_time']
                
                if reference_time:
                    # 予測時間範囲設定
                    horizon = self.propagation_config['wind_shift_prediction_horizon']
                    time_step = self.propagation_config['prediction_time_step']
                    
                    # 各予測時間での風向シフト検出
                    for t in range(time_step, horizon + 1, time_step):
                        target_time = reference_time + timedelta(seconds=t)
                        
                        # 風の場の予測
                        predicted_field = self.wind_fusion_system.predict_wind_field(
                            target_time=target_time,
                            current_wind_field=wind_field
                        )
                        
                        if predicted_field:
                            # 予測された風の場での風向シフト検出
                            leg_shifts = self._detect_wind_shifts_in_legs(
                                course_data, predicted_field, target_time
                            )
                            
                            # 予測時間に応じて確信度を減衰
                            for shift in leg_shifts:
                                decay_factor = 1.0 - (t / horizon) * self.propagation_config['prediction_confidence_decay']
                                shift.shift_probability *= decay_factor
                            
                            predicted_shifts.extend(leg_shifts)
            
            except Exception as e:
                logger.error(f"風向変化予測中にエラーが発生しました: {e}")
        
        # 現在の風の場での風向シフト検出（親クラスのメソッド）
        current_shifts = super().detect_wind_shifts(course_data, wind_field)
        
        # 現在と予測の風向シフトを結合
        all_shifts = current_shifts + predicted_shifts
        
        # 重複する風向シフトをフィルタリング
        filtered_shifts = filter_duplicate_shift_points(all_shifts)
        
        # 確信度でフィルタリング
        threshold = self.propagation_config['wind_shift_confidence_threshold']
        final_shifts = [shift for shift in filtered_shifts 
                      if shift.shift_probability >= threshold]
        
        return final_shifts
    
    def _detect_wind_shifts_in_legs(self, course_data: Dict[str, Any], 
                                 wind_field: Dict[str, Any],
                                 target_time: datetime) -> List[WindShiftPoint]:
        """
        各レグ内での風向シフト検出
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コースデータ
        wind_field : Dict[str, Any]
            風の場データ
        target_time : datetime
            対象時間
            
        Returns:
        --------
        List[WindShiftPoint]
            検出された風向シフト
        """
        # レグ情報がない場合は空のリストを返す
        if 'legs' not in course_data:
            return []
        
        shift_points = []
        
        # 各レグについて処理
        for leg in course_data['legs']:
            # パス情報がない場合はスキップ
            if 'path' not in leg or 'path_points' not in leg['path']:
                continue
            
            path_points = leg['path']['path_points']
            
            # パス情報が少なすぎる場合はスキップ
            if len(path_points) < 2:
                continue
            
            # 前のポイントでの風情報
            prev_wind = None
            
            # 各パスポイントについて処理
            for i, point in enumerate(path_points):
                # 位置情報がない場合はスキップ
                if 'lat' not in point or 'lon' not in point:
                    continue
                
                lat, lon = point['lat'], point['lon']
                
                # 風情報取得
                wind = self._get_wind_at_position(lat, lon, target_time, wind_field)
                
                # 風情報が取得できない場合はスキップ
                if not wind:
                    continue
                
                # 前のポイントでの風情報がある場合、風向シフト検出
                if prev_wind:
                    # 風向の差分
                    dir_diff = angle_difference(
                        wind['direction'], prev_wind['direction']
                    )
                    
                    # 最小風向シフト閾値
                    min_shift = self.config['min_wind_shift_angle']
                    if abs(dir_diff) >= min_shift:
                        # 風向シフトの位置（前後の中間点）
                        midlat = (lat + path_points[i-1]['lat']) / 2
                        midlon = (lon + path_points[i-1]['lon']) / 2
                        
                        # 確信度（前後の風情報の確信度の最小値）
                        confidence = min(
                            wind.get('confidence', 0.8),
                            prev_wind.get('confidence', 0.8)
                        )
                        
                        # 変動性（前後の風情報の変動性の最大値）
                        variability = max(
                            wind.get('variability', 0.2),
                            prev_wind.get('variability', 0.2)
                        )
                        
                        # 風向シフトポイント作成
                        shift_point = WindShiftPoint(
                            position=(midlat, midlon),
                            time_estimate=target_time
                        )
                        
                        # 風向情報設定
                        shift_point.shift_angle = dir_diff
                        shift_point.before_direction = prev_wind['direction']
                        shift_point.after_direction = wind['direction']
                        shift_point.wind_speed = (prev_wind['speed'] + wind['speed']) / 2
                        
                        # 確率計算
                        raw_probability = confidence * (1.0 - variability)
                        
                        # 風向差が大きいほど重要度が高い
                        # 大きな風向変化ほど確率を高く
                        angle_weight = min(1.0, abs(dir_diff) / 45.0)
                        shift_point.shift_probability = raw_probability * (0.5 + 0.5 * angle_weight)
                        
                        # 戦略的評価
                        strategic_score, note = calculate_strategic_score(
                            "wind_shift", "", "",
                            (midlat, midlon), target_time, wind_field
                        )
                        
                        shift_point.strategic_score = strategic_score
                        shift_point.note = note
                        
                        # リストに追加
                        shift_points.append(shift_point)
                
                # 現在の風情報を保存
                prev_wind = wind
        
        return shift_points
    
    def detect_optimal_tacks(self, course_data: Dict[str, Any], 
                          wind_field: Dict[str, Any]) -> List[TackPoint]:
        """
        最適タックポイントを検出
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コースデータ
        wind_field : Dict[str, Any]
            風の場データ
            
        Returns:
        --------
        List[TackPoint]
            検出された最適タックポイント
        """
        # VMG計算器がない場合はリストを返す
        if not self.vmg_calculator:
            logger.warning("VMGCalculatorが設定されていないため、最適タックポイントの検出ができません")
            return []
        
        # 親クラスの実装を呼び出す（基本実装を使用）
        return super().detect_optimal_tacks(course_data, wind_field)
    
    def detect_laylines(self, course_data: Dict[str, Any], 
                      wind_field: Dict[str, Any]) -> List[LaylinePoint]:
        """
        レイラインポイントを検出
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コースデータ
        wind_field : Dict[str, Any]
            風の場データ
            
        Returns:
        --------
        List[LaylinePoint]
            検出されたレイラインポイント
        """
        # VMG計算器がない場合はリストを返す
        if not self.vmg_calculator:
            logger.warning("VMGCalculatorが設定されていないため、レイラインポイントの検出ができません")
            return []
        
        # 親クラスの実装を呼び出す（基本実装を使用）
        return super().detect_laylines(course_data, wind_field)
