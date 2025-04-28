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
        filtered_shifts = self._filter_duplicate_shift_points(all_shifts)
        
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
                    dir_diff = self._angle_difference(
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
                        strategic_score, note = self._calculate_strategic_score(
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
    
    def _filter_duplicate_shift_points(self, shift_points: List[WindShiftPoint]) -> List[WindShiftPoint]:
        """
        重複する風向シフトポイントをフィルタリング
        
        Parameters:
        -----------
        shift_points : List[WindShiftPoint]
            シフトポイントリスト
            
        Returns:
        --------
        List[WindShiftPoint]
            フィルタリングされたシフトポイント
        """
        if len(shift_points) <= 1:
            return shift_points
        
        filtered_points = []
        sorted_points = sorted(shift_points, 
                              key=lambda p: self._normalize_to_timestamp(p.time_estimate))
        
        for point in sorted_points:
            is_duplicate = False
            
            for existing in filtered_points:
                # 位置が近い（300m以内）
                position_close = self._calculate_distance(
                    point.position[0], point.position[1],
                    existing.position[0], existing.position[1]
                ) < 300
                
                # 時間が近い（5分以内）
                time_diff = self._get_time_difference_seconds(
                    point.time_estimate, existing.time_estimate
                )
                time_close = time_diff < 300
                
                # 角度が類似している（15度以内）
                angle_similar = abs(self._angle_difference(
                    point.shift_angle, existing.shift_angle
                )) < 15
                
                # 重複と判断
                if position_close and time_close and angle_similar:
                    # 確率が高い方を優先
                    if point.shift_probability > existing.shift_probability:
                        # 既存のシフトポイントを置き換え
                        filtered_points.remove(existing)
                        filtered_points.append(point)
                    
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered_points.append(point)
        
        return filtered_points
    
    def _normalize_to_timestamp(self, t) -> float:
        """
        様々な時間表現から統一したUNIXタイムスタンプを作成
        
        Parameters:
        -----------
        t : any
            様々な時間表現(datetime, timedelta, int, float等)
            
        Returns:
        --------
        float
            UNIXタイムスタンプ形式の値
        """
        if isinstance(t, datetime):
            # datetimeをUNIXタイムスタンプに変換
            return t.timestamp()
        elif isinstance(t, timedelta):
            # timedeltaを秒に変換
            return t.total_seconds()
        elif isinstance(t, (int, float)):
            # 数値はそのままfloatで返す
            return float(t)
        elif isinstance(t, dict):
            # 辞書型の場合
            if 'timestamp' in t:
                # timestampキーを持つ辞書の場合
                return float(t['timestamp'])
            else:
                # timestampキーがない辞書の場合はエラー防止のため無限大を返す
                return float('inf')
        elif isinstance(t, str):
            try:
                # 数値文字列の場合は数値に変換
                return float(t)
            except ValueError:
                try:
                    # ISO形式の日時文字列
                    dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
                    return dt.timestamp()
                except ValueError:
                    # 変換できない場合は無限大
                    return float('inf')
        else:
            # その他の型は文字列に変換してから数値化
            try:
                return float(str(t))
            except ValueError:
                # 変換できない場合は無限大（対応する順序）
                return float('inf')
    def _get_time_difference_seconds(self, time1, time2) -> float:
        """
        二つの時間表現の差分を秒単位で計算
        
        Parameters:
        -----------
        time1, time2 : any
            様々な時間表現（datetime, timedelta, int, float, etc）
            
        Returns:
        --------
        float
            時間差（秒）、計算できない場合は無限大
        """
        # どちらの時間も正規化してから差分計算
        try:
            ts1 = self._normalize_to_timestamp(time1)
            ts2 = self._normalize_to_timestamp(time2)
            
            # どちらかが無効な場合は無限大を返す
            if ts1 == float('inf') or ts2 == float('inf'):
                return float('inf')
                
            return abs(ts1 - ts2)
        except Exception as e:
            logger.error(f"時間差計算エラー: {e}")
            # エラーが発生した場合は無限大を返す
            return float('inf')
    
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
    
    def _determine_tack_type(self, bearing: float, wind_direction: float) -> str:
        """
        タック種類を判定
        
        Parameters:
        -----------
        bearing : float
            進行方向角度（度）
        wind_direction : float
            風向角度（度、北を0として時計回り）
            
        Returns:
        --------
        str
            タック ('port'または'starboard')
        """
        # 風と進行方向の角度差
        relative_angle = self._angle_difference(bearing, wind_direction)
        
        # 角度から判定（負ならポート、正ならスターボードタック）
        return 'port' if relative_angle < 0 else 'starboard'
    
    def _calculate_strategic_score(self, maneuver_type: str, 
                                 before_tack_type: str, 
                                 after_tack_type: str,
                                 position: Tuple[float, float], 
                                 time_point, 
                                 wind_field: Dict[str, Any]) -> Tuple[float, str]:
        """
        戦略的重要度のスコア計算
        
        Parameters:
        -----------
        maneuver_type : str
            操作の種類 ('tack', 'gybe', 'wind_shift'等)
        before_tack_type : str
            操作前のタック ('port'または'starboard')
        after_tack_type : str
            操作後のタック ('port'または'starboard')
        position : Tuple[float, float]
            操作の位置（緯度, 経度）
        time_point : any
            操作の時間
        wind_field : Dict[str, Any]
            風の場データ
            
        Returns:
        --------
        Tuple[float, str]
            (戦略的スコア（0-1）, コメント)
        """
        score = 0.5  # デフォルト値
        note = "通常の戦略的変更"
        
        # 風情報取得
        wind = self._get_wind_at_position(position[0], position[1], time_point, wind_field)
        
        if not wind:
            return score, note
        
        # タイプごとに異なる計算
        if maneuver_type == 'tack':
            # タックの場合
            wind_shift_probability = wind.get('variability', 0.2)
            
            # タック変更
            if before_tack_type != after_tack_type:
                # タックが風向変化に関連する場合
                if wind_shift_probability > 0.6:
                    # 変動性の高い風での適切なタック
                    score = 0.8
                    note = "風の変動に対応した適切なタック"
                elif wind.get('confidence', 0.5) < 0.4:
                    # 確信度の低い予測に基づくタック
                    score = 0.3
                    note = "風の確信度が低い中でのタック（慎重に）"
                else:
                    # 通常のタック
                    score = 0.5
                    note = "通常のタック"
            
        elif maneuver_type == 'wind_shift':
            # 風向シフトの場合
            shift_angle = abs(self._angle_difference(
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
        
        # 位置の風の重要性などさらに詳細な評価を行う場合
        if 'lat_grid' in wind_field and 'lon_grid' in wind_field:
            # 将来的に拡張
            pass
        
        return min(1.0, score), note
    
    def _filter_duplicate_tack_points(self, tack_points: List[TackPoint]) -> List[TackPoint]:
        """
        重複するタックポイントをフィルタリング
        
        Parameters:
        -----------
        tack_points : List[TackPoint]
            タックポイントリスト
            
        Returns:
        --------
        List[TackPoint]
            フィルタリングされたタックポイント
        """
        # 基本的に _filter_duplicate_shift_points と同様
        if len(tack_points) <= 1:
            return tack_points
        
        filtered_points = []
        for point in tack_points:
            is_duplicate = False
            
            for existing in filtered_points:
                # 位置が近い
                position_close = self._calculate_distance(
                    point.position[0], point.position[1],
                    existing.position[0], existing.position[1]
                ) < 200  # タックはより厳密に判定
                
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
        重複するレイラインポイントをフィルタリング
        
        Parameters:
        -----------
        layline_points : List[LaylinePoint]
            レイラインポイントリスト
            
        Returns:
        --------
        List[LaylinePoint]
            フィルタリングされたレイラインポイント
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
                position_close = self._calculate_distance(
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
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        2点間の距離を計算
        
        Parameters:
        -----------
        lat1, lon1 : float
            始点の緯度経度
        lat2, lon2 : float
            終点の緯度経度
            
        Returns:
        --------
        float
            距離（メートル）
        """
        # 地球の半径（メートル）
        R = 6371000
        
        # 緯度経度をラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 差分
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversineの公式
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance