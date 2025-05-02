# -*- coding: utf-8 -*-
"""
StrategyDetectorWithPropagation

風向予測を考慮した戦略検出器
"""

import numpy as np
import math
import warnings
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
from functools import lru_cache

# 戦略検出関連モジュール - 親クラスと戦略ポイント定義
from sailing_data_processor.strategy.detector import StrategyDetector
from sailing_data_processor.strategy.points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint
# 共通ユーティリティ関数をインポート
from sailing_data_processor.strategy.strategy_detector_utils import (
    normalize_to_timestamp, get_time_difference_seconds, 
    angle_difference, calculate_distance
)

# ロガー設定
logger = logging.getLogger(__name__)

class StrategyDetectorWithPropagation(StrategyDetector):
    """
    風向予測を考慮した戦略検出器
    
    StrategyDetectorの機能を拡張して風向
    変化予測を組み込む
    """
    
    def __init__(self, vmg_calculator=None, wind_fusion_system=None):
        """
        初期化
        
        Parameters:
        -----------
        vmg_calculator : OptimalVMGCalculator, optional
            VMG計算機
        wind_fusion_system : WindFieldFusionSystem, optional
            風場融合器
        """
        # 親クラス初期化
        super().__init__(vmg_calculator)
        
        # 風場融合器設定
        self.wind_fusion_system = wind_fusion_system
        
        # 予測設定
        self.propagation_config = {
            'wind_shift_prediction_horizon': 1800,  # 予測最大時間（秒）
            'prediction_time_step': 300,           # 予測ステップ（秒）
            'wind_shift_confidence_threshold': 0.7, # 予測確信度閾値
            'min_propagation_distance': 1000,      # 最小伝播距離（m）
            'prediction_confidence_decay': 0.1,    # 予測の時間減衰パラメータ
            'use_historical_data': True            # 履歴データ使用
        }
    
    def detect_wind_shifts_with_propagation(self, course_data: Dict[str, Any], 
                                         wind_field: Dict[str, Any]) -> List[WindShiftPoint]:
        """
        風向予測を考慮した風向変化検出
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コースデータ
        wind_field : Dict[str, Any]
            風場データ
            
        Returns:
        --------
        List[WindShiftPoint]
            検出した風向変化点
        """
        if not wind_field or 'wind_direction' not in wind_field:
            return []
        
        # 風場融合器を用いた予測風向変化検出
        predicted_shifts = []
        
        if self.wind_fusion_system and hasattr(self.wind_fusion_system, 'predict_wind_field'):
            try:
                # 基準時刻
                reference_time = None
                if 'time' in wind_field:
                    reference_time = wind_field['time']
                elif 'start_time' in course_data:
                    reference_time = course_data['start_time']
                
                if reference_time:
                    # 予測時間設定
                    horizon = self.propagation_config['wind_shift_prediction_horizon']
                    time_step = self.propagation_config['prediction_time_step']
                    
                    # 各予測時間の風向変化検出
                    for t in range(time_step, horizon + 1, time_step):
                        target_time = reference_time + timedelta(seconds=t)
                        
                        # 風場予測
                        predicted_field = self.wind_fusion_system.predict_wind_field(
                            target_time=target_time,
                            current_wind_field=wind_field
                        )
                        
                        if predicted_field:
                            # 予測時点の風場での風向変化検出
                            leg_shifts = self._detect_wind_shifts_in_legs(
                                course_data, predicted_field, target_time
                            )
                            
                            # 予測時間に基づく確信度減衰
                            for shift in leg_shifts:
                                decay_factor = 1.0 - (t / horizon) * self.propagation_config['prediction_confidence_decay']
                                shift.shift_probability *= decay_factor
                            
                            predicted_shifts.extend(leg_shifts)
            
            except Exception as e:
                logger.error(f"予測時間処理中にエラーが発生しました: {e}")
        
        # 現在の風場での風向変化検出（親メソッド使用）
        current_shifts = super().detect_wind_shifts(course_data, wind_field)
        
        # 現在と予測の風向変化統合
        all_shifts = current_shifts + predicted_shifts
        
        # 重複する風向変化点フィルタリング
        filtered_shifts = self._filter_duplicate_shift_points(all_shifts)
        
        # 信頼度フィルタリング
        threshold = self.propagation_config['wind_shift_confidence_threshold']
        final_shifts = [shift for shift in filtered_shifts 
                      if shift.shift_probability >= threshold]
        
        return final_shifts
    
    def _detect_wind_shifts_in_legs(self, course_data: Dict[str, Any], 
                                 wind_field: Dict[str, Any],
                                 target_time: datetime) -> List[WindShiftPoint]:
        """
        各レグでの風向変化検出
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コースデータ
        wind_field : Dict[str, Any]
            風場データ
        target_time : datetime
            対象時刻
            
        Returns:
        --------
        List[WindShiftPoint]
            検出した風向変化点
        """
        # レグ情報確認
        if 'legs' not in course_data:
            return []
        
        shift_points = []
        
        # 各レグを処理
        for leg in course_data['legs']:
            # パス情報確認
            if 'path' not in leg or 'path_points' not in leg['path']:
                continue
            
            path_points = leg['path']['path_points']
            
            # パス点数確認
            if len(path_points) < 2:
                continue
            
            # 前の地点での風場
            prev_wind = None
            
            # 各パス地点を処理
            for i, point in enumerate(path_points):
                # パス情報確認
                if 'lat' not in point or 'lon' not in point:
                    continue
                
                lat, lon = point['lat'], point['lon']
                
                # 風場取得
                wind = self._get_wind_at_position(lat, lon, target_time, wind_field)
                
                # 風場情報が無い場合はスキップ
                if not wind:
                    continue
                
                # 前の地点での風場と比較して風向変化検出
                if prev_wind:
                    # 風向の差
                    dir_diff = angle_difference(
                        wind['direction'], prev_wind['direction']
                    )
                    
                    # 最小風向変化判定
                    min_shift = self.config['min_wind_shift_angle']
                    if abs(dir_diff) >= min_shift:
                        # 風向変化の前後の中間地点
                        midlat = (lat + path_points[i-1]['lat']) / 2
                        midlon = (lon + path_points[i-1]['lon']) / 2
                        
                        # 前後の風場の信頼度の最小値
                        confidence = min(
                            wind.get('confidence', 0.8),
                            prev_wind.get('confidence', 0.8)
                        )
                        
                        # 前後の風場の変動性の最大値
                        variability = max(
                            wind.get('variability', 0.2),
                            prev_wind.get('variability', 0.2)
                        )
                        
                        # 風向変化ポイント作成
                        shift_point = WindShiftPoint(
                            position=(midlat, midlon),
                            time_estimate=target_time
                        )
                        
                        # 風向情報設定
                        shift_point.shift_angle = dir_diff
                        shift_point.before_direction = prev_wind['direction']
                        shift_point.after_direction = wind['direction']
                        shift_point.wind_speed = (prev_wind['speed'] + wind['speed']) / 2
                        
                        # 確信度
                        raw_probability = confidence * (1.0 - variability)
                        
                        # 風向差が大きいほど重要度が上がる
                        # 特に大きな風向変化ほど重要
                        angle_weight = min(1.0, abs(dir_diff) / 45.0)
                        shift_point.shift_probability = raw_probability * (0.5 + 0.5 * angle_weight)
                        
                        # 戦略スコア
                        strategic_score, note = self._calculate_strategic_score(
                            "wind_shift", "", "",
                            (midlat, midlon), target_time, wind_field
                        )
                        
                        shift_point.strategic_score = strategic_score
                        shift_point.note = note
                        
                        # 追加
                        shift_points.append(shift_point)
                
                # 現在の風場を記録
                prev_wind = wind
        
        return shift_points
    
    def _filter_duplicate_shift_points(self, shift_points: List[WindShiftPoint]) -> List[WindShiftPoint]:
        """
        重複する風向変化ポイントのフィルタリング
        
        Parameters:
        -----------
        shift_points : List[WindShiftPoint]
            変化ポイントリスト
            
        Returns:
        --------
        List[WindShiftPoint]
            フィルタリング後の変化ポイント
        """
        if len(shift_points) <= 1:
            return shift_points
        
        filtered_points = []
        sorted_points = sorted(shift_points, 
                              key=lambda p: normalize_to_timestamp(p.time_estimate))
        
        for point in sorted_points:
            is_duplicate = False
            
            for existing in filtered_points:
                # 位置が近い（300m以内）
                position_close = calculate_distance(
                    point.position[0], point.position[1],
                    existing.position[0], existing.position[1]
                ) < 300
                
                # 時間が近い（5分以内）
                time_diff = get_time_difference_seconds(
                    point.time_estimate, existing.time_estimate
                )
                time_close = time_diff < 300
                
                # 角度が類似（15度以内）
                angle_similar = abs(angle_difference(
                    point.shift_angle, existing.shift_angle
                )) < 15
                
                # 重複判定
                if position_close and time_close and angle_similar:
                    # 確信度が高い方を優先
                    if point.shift_probability > existing.shift_probability:
                        # 既の変化ポイントの置き換え
                        filtered_points.remove(existing)
                        filtered_points.append(point)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_points.append(point)
        
        return filtered_points
    
    def _calculate_strategic_score(self, maneuver_type: str, 
                                 before_tack_type: str, 
                                 after_tack_type: str,
                                 position: Tuple[float, float], 
                                 time_point, 
                                 wind_field: Dict[str, Any]) -> Tuple[float, str]:
        """
        戦略的重要度の計算
        
        Parameters:
        -----------
        maneuver_type : str
            操作の種別 ('tack', 'gybe', 'wind_shift'等)
        before_tack_type : str
            操作前のタック種別 ('port'または'starboard')
        after_tack_type : str
            操作後のタック種別 ('port'または'starboard')
        position : Tuple[float, float]
            操作の位置（緯度, 経度）
        time_point : any
            操作の時刻
        wind_field : Dict[str, Any]
            風場データ
            
        Returns:
        --------
        Tuple[float, str]
            (戦略スコア（0-1）, 評価メモ)
        """
        score = 0.5  # デフォルト値
        note = "標準的な戦略判断"
        
        # 風場取得
        wind = self._get_wind_at_position(position[0], position[1], time_point, wind_field)
        
        if not wind:
            return score, note
        
        # 操作タイプに応じた評価
        if maneuver_type == 'tack':
            # タックの場合
            wind_shift_probability = wind.get('variability', 0.2)
            
            # タック種別
            if before_tack_type != after_tack_type:
                # タックが風向変化に合わせている場合
                if wind_shift_probability > 0.6:
                    # 変動性の高い中での適切なタック
                    score = 0.8
                    note = "風の変動に合わせた適切なタック"
                elif wind.get('confidence', 0.5) < 0.4:
                    # 風の不確実性が高い中でのタック
                    score = 0.3
                    note = "風の予測が不確実な中でのタック（リスク）"
                else:
                    # 標準的なタック
                    score = 0.5
                    note = "標準的なタック"
            
        elif maneuver_type == 'wind_shift':
            # 風向変化の場合
            shift_angle = abs(angle_difference(
                wind.get('direction', 0), 
                wind.get('before_direction', wind.get('direction', 0))
            ))
            
            if shift_angle > 20:
                # 大きな風向変化
                score = 0.9
                note = "大きな風向変化ポイント"
            elif shift_angle > 10:
                # 中程度の風向変化
                score = 0.7
                note = "中程度の風向変化"
            else:
                # 小さな風向変化
                score = 0.5
                note = "小さな風向変化"
            
            # 風速の変化も考慮
            if 'before_speed' in wind and 'speed' in wind:
                speed_change = abs(wind['speed'] - wind['before_speed'])
                if speed_change > 5:
                    score += 0.1
                    note += "（風速も大きく変化）"
        
        # 後の非線形評価は別途具現化が必要な場合は実施
        if 'lat_grid' in wind_field and 'lon_grid' in wind_field:
            # 将来的な拡張
            pass
        
        return min(1.0, score), note
    
    def detect_optimal_tacks(self, course_data: Dict[str, Any], 
                          wind_field: Dict[str, Any]) -> List[TackPoint]:
        """
        最適タックポイント検出
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コースデータ
        wind_field : Dict[str, Any]
            風場データ
            
        Returns:
        --------
        List[TackPoint]
            検出した最適タックポイント
        """
        # VMG計算機がない場合は検出不可
        if not self.vmg_calculator:
            logger.warning("VMGCalculatorが設定されていないため、最適タックポイントの検出ができません")
            return []
        
        # 基本機能を利用（予測機能は将来拡張）
        return super().detect_optimal_tacks(course_data, wind_field)
    
    def detect_laylines(self, course_data: Dict[str, Any], 
                      wind_field: Dict[str, Any]) -> List[LaylinePoint]:
        """
        レイラインポイント検出
        
        Parameters:
        -----------
        course_data : Dict[str, Any]
            コースデータ
        wind_field : Dict[str, Any]
            風場データ
            
        Returns:
        --------
        List[LaylinePoint]
            検出したレイラインポイント
        """
        # VMG計算機がない場合は検出不可
        if not self.vmg_calculator:
            logger.warning("VMGCalculatorが設定されていないため、レイラインポイントの検出ができません")
            return []
        
        # 基本機能を利用（予測機能は将来拡張）
        return super().detect_laylines(course_data, wind_field)
    
    def _determine_tack_type(self, bearing: float, wind_direction: float) -> str:
        """
        タック種別判定
        
        Parameters:
        -----------
        bearing : float
            艇の進行方向（度）
        wind_direction : float
            風向（度、真北から時計回り）
            
        Returns:
        --------
        str
            タック種別 ('port'または'starboard')
        """
        # 艇と風の相対角度
        relative_angle = angle_difference(bearing, wind_direction)
        
        # 角度から判定（負の角度はポートタック、正の角度はスターボードタック）
        return 'port' if relative_angle < 0 else 'starboard'
    
    def _filter_duplicate_tack_points(self, tack_points: List[TackPoint]) -> List[TackPoint]:
        """
        重複するタックポイントのフィルタリング
        
        Parameters:
        -----------
        tack_points : List[TackPoint]
            タックポイントリスト
            
        Returns:
        --------
        List[TackPoint]
            フィルタリング後のタックポイント
        """
        # 基本的に _filter_duplicate_shift_points と同様
        if len(tack_points) <= 1:
            return tack_points
        
        filtered_points = []
        for point in tack_points:
            is_duplicate = False
            
            for existing in filtered_points:
                # 位置が近い
                position_close = calculate_distance(
                    point.position[0], point.position[1],
                    existing.position[0], existing.position[1]
                ) < 200  # タックはより詳細に
                
                # VMG利得が類似している
                vmg_similar = abs(point.vmg_gain - existing.vmg_gain) < 0.05
                
                if position_close and vmg_similar:
                    # VMG利得が大きい方を優先
                    if point.vmg_gain > existing.vmg_gain:
                        filtered_points.remove(existing)
                        filtered_points.append(point)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_points.append(point)
        
        return filtered_points
    
    def _filter_duplicate_laylines(self, layline_points: List[LaylinePoint]) -> List[LaylinePoint]:
        """
        重複するレイラインポイントのフィルタリング
        
        Parameters:
        -----------
        layline_points : List[LaylinePoint]
            レイラインポイントリスト
            
        Returns:
        --------
        List[LaylinePoint]
            フィルタリング後のレイラインポイント
        """
        # 基本的に _filter_duplicate_shift_points と同様
        if len(layline_points) <= 1:
            return layline_points
        
        filtered_points = []
        for point in layline_points:
            is_duplicate = False
            
            for existing in filtered_points:
                # 同じマーク向け
                same_mark = point.mark_id == existing.mark_id
                
                # 位置が近い
                position_close = calculate_distance(
                    point.position[0], point.position[1],
                    existing.position[0], existing.position[1]
                ) < 300
                
                if same_mark and position_close:
                    # 確信度が高い方を優先
                    if point.confidence > existing.confidence:
                        filtered_points.remove(existing)
                        filtered_points.append(point)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_points.append(point)
        
        return filtered_points