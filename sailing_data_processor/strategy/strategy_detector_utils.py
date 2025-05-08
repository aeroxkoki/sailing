# -*- coding: utf-8 -*-
"""
戦略検出ユーティリティモジュール

戦略ポイント検出に使用される各種ユーティリティ関数を提供します
"""

import math
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta

# ロガー設定
logger = logging.getLogger(__name__)

def normalize_to_timestamp(t) -> float:
    """
    時間値をUNIXタイムスタンプに変換
    
    Parameters:
    -----------
    t : any
        時間値（datetime, timedelta, int, float等）
        
    Returns:
    --------
    float
        UNIXタイムスタンプ（秒数）
    """
    if isinstance(t, datetime):
        # datetimeをUNIXタイムスタンプに変換
        return t.timestamp()
    elif isinstance(t, timedelta):
        # timedeltalを変換
        return t.total_seconds()
    elif isinstance(t, (int, float)):
        # 数値はそのままfloatで返す
        return float(t)
    elif isinstance(t, dict):
        # 辞書の場合
        if 'timestamp' in t:
            # timestampキーがある場合
            return float(t['timestamp'])
        else:
            # timestampがない場合は無限大を返す
            return float('inf')
    elif isinstance(t, str):
        try:
            # 数値文字列なら数値に変換
            return float(t)
        except ValueError:
            try:
                # ISO形式の時間文字列
                dt = datetime.fromisoformat(t.replace('Z', '+00:00'))
                return dt.timestamp()
            except ValueError:
                # 変換できない場合は無限大
                return float('inf')
    else:
        # その他の型は文字列に変換して数値化
        try:
            return float(str(t))
        except ValueError:
            # 変換できない場合は無限大を返す
            return float('inf')

def get_time_difference_seconds(time1, time2) -> float:
    """
    二つの時間値の差分を秒数で取得
    
    Parameters:
    -----------
    time1, time2 : any
        時間値（datetime, timedelta, int, float, etc）
        
    Returns:
    --------
    float
        時間差（秒）。変換できない場合は無限大
    """
    # 両方の時間をタイムスタンプに変換
    try:
        ts1 = normalize_to_timestamp(time1)
        ts2 = normalize_to_timestamp(time2)
        
        # どちらかが無限大なら無限大を返す
        if ts1 == float('inf') or ts2 == float('inf'):
            return float('inf')
            
        return abs(ts1 - ts2)
    except Exception as e:
        logger.error(f"時間差の計算エラー: {e}")
        # エラーが発生した場合は無限大を返す
        return float('inf')

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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

def angle_difference(a: float, b: float) -> float:
    """
    2つの角度の差を計算（-180～180度の範囲）
    
    Parameters:
    -----------
    a, b : float
        角度（度）
        
    Returns:
    --------
    float
        角度差（-180～180）
    """
    diff = (a - b + 180) % 360 - 180
    return diff

def determine_tack_type(bearing: float, wind_direction: float) -> str:
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
    # 方位の正規化
    bearing_norm = bearing % 360
    wind_norm = wind_direction % 360
    
    # 艇の進行方向に対して風がどちらから来るかを判定する
    # 風向と船が向いている方向の相対角度を計算
    
    # 風向と艇の向きの相対角度を計算
    # 風が右から来るならスターボード、左から来るならポート
    relative_angle = (wind_norm - bearing_norm) % 360
    
    # 0-180度なら右舷から風（スターボードタック）
    # 180-360度なら左舷から風（ポートタック）
    if 0 <= relative_angle <= 180:
        return 'starboard'  # 風が右から来る場合
    else:
        return 'port'       # 風が左から来る場合（180-360度より大きい）

def get_wind_at_position(lat: float, lon: float, time_point, wind_field: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """
    指定位置の風の情報を取得
    
    Parameters:
    -----------
    lat : float
        緯度
    lon : float
        経度
    time_point : any
        時間
    wind_field : Dict[str, Any]
        風の場データ
        
    Returns:
    --------
    Optional[Dict[str, float]]
        風情報（direction, speed, confidence）
    """
    if not wind_field:
        return None
    
    if 'lat_grid' not in wind_field or 'lon_grid' not in wind_field:
        return None
    
    # 緯度経度グリッド取得
    lat_grid = wind_field['lat_grid']
    lon_grid = wind_field['lon_grid']
    
    if lat_grid.size == 0 or lon_grid.size == 0:
        return None
    
    # 最も近いグリッドポイントを検索
    distances = (lat_grid - lat)**2 + (lon_grid - lon)**2
    closest_idx = distances.argmin()
    closest_i, closest_j = divmod(closest_idx, lat_grid.shape[1])
    
    # 最も近いポイントの風情報取得
    wind_dir = wind_field['wind_direction'][closest_i, closest_j]
    wind_speed = wind_field['wind_speed'][closest_i, closest_j]
    
    # 信頼度情報取得
    confidence = 0.8  # デフォルト値
    if 'confidence' in wind_field:
        confidence = wind_field['confidence'][closest_i, closest_j]
    
    # 変動性情報取得
    variability = 0.2  # デフォルト値
    if 'variability' in wind_field:
        variability = wind_field['variability'][closest_i, closest_j]
    
    # 風情報返す
    return {
        'direction': wind_dir,
        'speed': wind_speed,
        'confidence': confidence,
        'variability': variability
    }

def calculate_strategic_score(maneuver_type: str, 
                             before_tack_type: str, 
                             after_tack_type: str,
                             position: Tuple[float, float], 
                             time_point, 
                             wind_field: Dict[str, Any]) -> Tuple[float, str]:
    """
    戦略判断の評価点を計算
    
    Parameters:
    -----------
    maneuver_type : str
        操作の種類 ('tack', 'gybe', 'wind_shift'等)
    before_tack_type : str
        操作前のタック ('port'または'starboard')
    after_tack_type : str
        操作後のタック ('port'または'starboard')
    position : Tuple[float, float]
        操作位置の（緯度, 経度）
    time_point : any
        操作の時間
    wind_field : Dict[str, Any]
        風の場データ
        
    Returns:
    --------
    Tuple[float, str]
        (戦略評価点（0-1）, 評価コメント)
    """
    score = 0.5  # デフォルト値
    note = "標準的な戦略判断"
    
    # 風情報取得
    wind = get_wind_at_position(position[0], position[1], time_point, wind_field)
    
    if not wind:
        return score, note
    
    # 操作タイプに応じた評価
    if maneuver_type == 'tack':
        # タックの場合
        wind_shift_probability = wind.get('variability', 0.2)
        
        # タック種類が変わっていることを確認
        if before_tack_type != after_tack_type:
            # タックが風向変化に合致するか確認
            if wind_shift_probability > 0.6:
                # 変動の大きい風での適切なタック
                score = 0.8
                note = "風の変化に応じた適切なタック"
            elif wind.get('confidence', 0.5) < 0.4:
                # 風の不確実さに起因するタック
                score = 0.3
                note = "風の予測が不確かでのタック（慎重に）"
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
            note = "大きな風向変化を検出"
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
    
    # 位置の最適性なども追加要素として考慮可能
    if 'lat_grid' in wind_field and 'lon_grid' in wind_field:
        # 更に詳細に分析
        pass
    
    return min(1.0, score), note

def filter_duplicate_shift_points(shift_points):
    """
    重複する風向変化ポイントを除去
    
    Parameters:
    -----------
    shift_points : List
        風向変化ポイントリスト
        
    Returns:
    --------
    List
        重複を除去した風向変化ポイント
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
            
            # 角度が類似している（15度以内）
            angle_similar = abs(angle_difference(
                point.shift_angle, existing.shift_angle
            )) < 15
            
            # 重複と判定
            if position_close and time_close and angle_similar:
                # 確率が高いほうを選択
                if point.shift_probability > existing.shift_probability:
                    # 古い風向変化ポイントの代わり
                    filtered_points.remove(existing)
                    filtered_points.append(point)
                
                is_duplicate = True
                break
        
        if not is_duplicate:
            filtered_points.append(point)
    
    return filtered_points

def filter_duplicate_tack_points(tack_points):
    """
    重複するタックポイントを除去
    
    Parameters:
    -----------
    tack_points : List
        タックポイントリスト
        
    Returns:
    --------
    List
        重複を除去したタックポイント
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
            ) < 200  # タックはより厳密に設定
            
            # VMG利得が類似している
            vmg_similar = abs(point.vmg_gain - existing.vmg_gain) < 0.05
            
            if position_close and vmg_similar:
                # VMG利得が大きいほうを選択
                if point.vmg_gain > existing.vmg_gain:
                    filtered_points.remove(existing)
                    filtered_points.append(point)
                
                is_duplicate = True
                break
        
        if not is_duplicate:
            filtered_points.append(point)
    
    return filtered_points

def filter_duplicate_laylines(layline_points):
    """
    重複するレイラインポイントを除去
    
    Parameters:
    -----------
    layline_points : List
        レイラインポイントリスト
        
    Returns:
    --------
    List
        重複を除去したレイラインポイント
    """
    # 基本的に filter_duplicate_shift_points と同様
    if len(layline_points) <= 1:
        return layline_points
    
    filtered_points = []
    for point in layline_points:
        is_duplicate = False
        
        for existing in filtered_points:
            # 同じマーク対象
            same_mark = point.mark_id == existing.mark_id
            
            # 位置が近い
            position_close = calculate_distance(
                point.position[0], point.position[1],
                existing.position[0], existing.position[1]
            ) < 300
            
            if same_mark and position_close:
                # 確率が高いほうを選択
                if point.confidence > existing.confidence:
                    filtered_points.remove(existing)
                    filtered_points.append(point)
                
                is_duplicate = True
                break
        
        if not is_duplicate:
            filtered_points.append(point)
    
    return filtered_points