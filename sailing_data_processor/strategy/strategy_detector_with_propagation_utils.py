# -*- coding: utf-8 -*-
"""
Strategy Detector With Propagation Utilities

風向予測を考慮した戦略検出器のユーティリティ関数
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime

from sailing_data_processor.strategy.points import WindShiftPoint, TackPoint, LaylinePoint
from sailing_data_processor.strategy.strategy_detector_utils import (
    normalize_to_timestamp, get_time_difference_seconds, 
    angle_difference, calculate_distance
)

def get_wind_at_position(lat: float, lon: float, 
                         time_point: datetime, 
                         wind_field: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    指定位置での風情報を取得
    
    Parameters:
    -----------
    lat : float
        緯度
    lon : float
        経度
    time_point : datetime
        時刻
    wind_field : Dict[str, Any]
        風場データ
        
    Returns:
    --------
    Optional[Dict[str, Any]]
        風情報（方向、速度など）
    """
    # 風場データのフォーマットに応じた取得処理
    if 'get_wind_at_position' in wind_field and callable(wind_field['get_wind_at_position']):
        # 関数が提供されている場合はそれを使用
        return wind_field['get_wind_at_position'](lat, lon, time_point)
    
    elif 'lat_grid' in wind_field and 'lon_grid' in wind_field:
        # グリッドデータからの補間
        try:
            lat_grid = wind_field['lat_grid']
            lon_grid = wind_field['lon_grid']
            
            # 最も近いグリッド点を探索
            lat_idx = np.abs(lat_grid - lat).argmin()
            lon_idx = np.abs(lon_grid - lon).argmin()
            
            # 風向風速取得
            if 'wind_direction' in wind_field and isinstance(wind_field['wind_direction'], np.ndarray):
                direction = wind_field['wind_direction'][lat_idx, lon_idx]
                speed = wind_field.get('wind_speed', np.zeros_like(wind_field['wind_direction']))[lat_idx, lon_idx]
                
                # 信頼度情報（存在すれば）
                confidence = 0.8  # デフォルト値
                if 'confidence' in wind_field and isinstance(wind_field['confidence'], np.ndarray):
                    confidence = wind_field['confidence'][lat_idx, lon_idx]
                
                # 変動性情報（存在すれば）
                variability = 0.2  # デフォルト値
                if 'variability' in wind_field and isinstance(wind_field['variability'], np.ndarray):
                    variability = wind_field['variability'][lat_idx, lon_idx]
                
                return {
                    'direction': float(direction),
                    'speed': float(speed),
                    'confidence': float(confidence),
                    'variability': float(variability)
                }
        except (IndexError, KeyError, ValueError) as e:
            # エラー発生時はNoneを返す
            return None
    
    elif 'direction' in wind_field and 'speed' in wind_field:
        # 単一の風情報しかない場合
        return {
            'direction': float(wind_field['direction']),
            'speed': float(wind_field['speed']),
            'confidence': float(wind_field.get('confidence', 0.8)),
            'variability': float(wind_field.get('variability', 0.2))
        }
    
    # 対応するフォーマットがない場合はNoneを返す
    return None

def calculate_strategic_score(maneuver_type: str, 
                            before_tack_type: str, 
                            after_tack_type: str,
                            position: Tuple[float, float], 
                            time_point, 
                            wind_field: Dict[str, Any],
                            config: Dict[str, Any]) -> Tuple[float, str]:
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
    config : Dict[str, Any]
        設定パラメータ
        
    Returns:
    --------
    Tuple[float, str]
        (戦略スコア（0-1）, 評価メモ)
    """
    score = 0.5  # デフォルト値
    note = "標準的な戦略判断"
    
    # 風場取得
    wind = get_wind_at_position(position[0], position[1], time_point, wind_field)
    
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

def determine_tack_type(bearing: float, wind_direction: float) -> str:
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

def filter_duplicate_shift_points(shift_points: List[WindShiftPoint]) -> List[WindShiftPoint]:
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

def filter_duplicate_tack_points(tack_points: List[TackPoint]) -> List[TackPoint]:
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
    # 基本的に filter_duplicate_shift_points と同様
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

def filter_duplicate_laylines(layline_points: List[LaylinePoint]) -> List[LaylinePoint]:
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
    # 基本的に filter_duplicate_shift_points と同様
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