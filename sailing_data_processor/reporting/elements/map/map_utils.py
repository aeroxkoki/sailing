# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map.map_utils

マップ関連のユーティリティ関数を提供するモジュールです。
GPSデータの処理やマップ表示のためのヘルパー関数を含みます。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import math
import uuid
import datetime
import statistics
from collections import defaultdict

import numpy as np
from geopy.distance import geodesic


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の距離を計算（メートル単位）
    
    Parameters
    ----------
    lat1 : float
        緯度1
    lon1 : float
        経度1
    lat2 : float
        緯度2
    lon2 : float
        経度2
        
    Returns
    -------
    float
        距離（メートル単位）
    """
    return geodesic((lat1, lon1), (lat2, lon2)).meters


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の方位角を計算（度単位、北=0度、時計回り）
    
    Parameters
    ----------
    lat1 : float
        緯度1
    lon1 : float
        経度1
    lat2 : float
        緯度2
    lon2 : float
        経度2
        
    Returns
    -------
    float
        方位角（0-360度）
    """
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    bearing = math.atan2(y, x)
    
    bearing_deg = math.degrees(bearing)
    return (bearing_deg + 360) % 360


def create_color_scale(values: List[float], color_map: str = "viridis") -> Dict[float, str]:
    """
    数値リストからカラースケールを作成
    
    Parameters
    ----------
    values : List[float]
        値のリスト
    color_map : str, optional
        カラーマップ名, by default "viridis"
        
    Returns
    -------
    Dict[float, str]
        値と色のマッピング辞書（0-1の間に正規化）
    """
    import matplotlib.cm as cm
    import matplotlib.colors as mcolors
    
    if not values:
        return {}
    
    # 値の正規化
    min_val = min(values)
    max_val = max(values)
    
    if min_val == max_val:
        return {0: "rgba(0, 0, 255, 0.8)", 1: "rgba(0, 0, 255, 0.8)"}
    
    # カラーマップの取得
    cmap = cm.get_cmap(color_map)
    
    # カラースケールの作成
    scale = {}
    for i in range(11):
        norm_val = i / 10
        val = min_val + norm_val * (max_val - min_val)
        
        # RGBAカラーを取得
        rgba = cmap(norm_val)
        rgba_str = f"rgba({int(rgba[0]*255)}, {int(rgba[1]*255)}, {int(rgba[2]*255)}, {rgba[3]})"
        
        scale[norm_val] = rgba_str
    
    return scale


def simplify_track(track_data: List[Dict[str, Any]], tolerance: float = 5.0, 
                 max_points: int = 1000, lat_key: str = "lat", lng_key: str = "lng") -> List[Dict[str, Any]]:
    """
    GPSトラックデータを簡略化（間引き）
    
    Parameters
    ----------
    track_data : List[Dict[str, Any]]
        トラックデータポイントのリスト
    tolerance : float, optional
        簡略化の許容誤差（メートル）, by default 5.0
    max_points : int, optional
        最大点数, by default 1000
    lat_key : str, optional
        緯度のキー, by default "lat"
    lng_key : str, optional
        経度のキー, by default "lng"
        
    Returns
    -------
    List[Dict[str, Any]]
        簡略化されたトラックデータ
    """
    if not track_data or len(track_data) <= 2:
        return track_data
    
    # 簡略化が必要ない場合はそのまま返す
    if len(track_data) <= max_points:
        return track_data
    
    # 簡略化アルゴリズム（Douglas-Peucker法の簡易版）
    def distance_point_to_line(p, line_start, line_end):
        if line_start == line_end:
            return calculate_distance(p[0], p[1], line_start[0], line_start[1])
        
        # ライン上の最も近い点を計算
        x1, y1 = line_start
        x2, y2 = line_end
        x3, y3 = p
        
        dx = x2 - x1
        dy = y2 - y1
        
        # 線分の長さの二乗
        line_length_sq = dx*dx + dy*dy
        
        if line_length_sq == 0:
            return calculate_distance(p[0], p[1], line_start[0], line_start[1])
        
        # 線分上の最も近い点のパラメータ（0-1の範囲）
        t = max(0, min(1, ((x3-x1)*dx + (y3-y1)*dy) / line_length_sq))
        
        # 最も近い点の座標
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        # 距離を計算
        return calculate_distance(p[0], p[1], closest_x, closest_y)
    
    # 再帰的に簡略化
    def _simplify(points, start_idx, end_idx, result_indices):
        if end_idx - start_idx <= 1:
            return
        
        # 始点と終点
        p_start = (points[start_idx][lat_key], points[start_idx][lng_key])
        p_end = (points[end_idx][lat_key], points[end_idx][lng_key])
        
        # 最大距離とそのインデックスを探す
        max_dist = -1
        max_idx = start_idx
        
        for i in range(start_idx + 1, end_idx):
            p = (points[i][lat_key], points[i][lng_key])
            dist = distance_point_to_line(p, p_start, p_end)
            
            if dist > max_dist:
                max_dist = dist
                max_idx = i
        
        # 許容誤差より大きい場合は分割して再帰
        if max_dist > tolerance:
            result_indices.add(max_idx)
            _simplify(points, start_idx, max_idx, result_indices)
            _simplify(points, max_idx, end_idx, result_indices)
    
    # 結果のインデックスセット（始点と終点は常に含む）
    result_indices = {0, len(track_data) - 1}
    
    # 簡略化処理
    _simplify(track_data, 0, len(track_data) - 1, result_indices)
    
    # 結果のインデックスを順にソート
    result_indices = sorted(result_indices)
    
    # 点数の調整（max_points以下になるように間引く）
    if len(result_indices) > max_points:
        # 均等に間引く
        step = len(result_indices) / max_points
        new_indices = {0, len(track_data) - 1}  # 始点と終点は保持
        
        }
        idx = 1
        while len(new_indices) < max_points - 1 and idx < len(result_indices) - 1:
            new_indices.add(result_indices[idx])
            idx = int(idx + step)
        
        result_indices = sorted(new_indices)
    
    # 結果の構築
    return [track_data[i] for i in result_indices]


def extract_track_segments(track_data: List[Dict[str, Any]], 
                          segment_key: Optional[str] = None, 
                          time_gap_threshold: Optional[int] = None,
                          distance_gap_threshold: Optional[float] = None,
                          lat_key: str = "lat", 
                          lng_key: str = "lng",
                          time_key: str = "timestamp") -> List[List[Dict[str, Any]]]:
    """
    GPSトラックデータをセグメントに分割
    
    Parameters
    ----------
    track_data : List[Dict[str, Any]]
        トラックデータポイントのリスト
    segment_key : Optional[str], optional
        セグメントを識別するキー, by default None
    time_gap_threshold : Optional[int], optional
        セグメント分割の時間ギャップ閾値（秒）, by default None
    distance_gap_threshold : Optional[float], optional
        セグメント分割の距離ギャップ閾値（メートル）, by default None
    lat_key : str, optional
        緯度のキー, by default "lat"
    lng_key : str, optional
        経度のキー, by default "lng"
    time_key : str, optional
        時間のキー, by default "timestamp"
        
    Returns
    -------
    List[List[Dict[str, Any]]]
        セグメントのリスト
    """
    if not track_data:
        return []
    
    # セグメントキーが指定されている場合
    if segment_key is not None:
        segments = defaultdict(list)
        for point in track_data:
            if segment_key in point:
                segments[point[segment_key]].append(point)
        
        return list(segments.values())
    
    # 時間ギャップによる分割
    if time_gap_threshold is not None:
        segments = []
        current_segment = [track_data[0]]
        
        for i in range(1, len(track_data)):
            prev_point = track_data[i-1]
            curr_point = track_data[i]
            
            # 時間の抽出と比較
            prev_time = prev_point.get(time_key)
            curr_time = curr_point.get(time_key)
            
            if prev_time is not None and curr_time is not None:
                # 文字列の場合はdatetimeに変換
                if isinstance(prev_time, str):
                    try:
                        prev_time = datetime.datetime.fromisoformat(prev_time.replace('Z', '+00:00'))
                    except ValueError:
                        try:
                            prev_time = datetime.datetime.strptime(prev_time, "%Y-%m-%dT%H:%M:%S")
                        except ValueError:
                            prev_time = None
                
                if isinstance(curr_time, str):
                    try:
                        curr_time = datetime.datetime.fromisoformat(curr_time.replace('Z', '+00:00'))
                    except ValueError:
                        try:
                            curr_time = datetime.datetime.strptime(curr_time, "%Y-%m-%dT%H:%M:%S")
                        except ValueError:
                            curr_time = None
                
                # 数値の場合はUnixタイムスタンプと仮定
                if isinstance(prev_time, (int, float)) and isinstance(curr_time, (int, float)):
                    time_diff = curr_time - prev_time
                    if time_diff > time_gap_threshold:
                        segments.append(current_segment)
                        current_segment = [curr_point]
                        continue
                
                # datetime同士の場合は秒数で比較
                if isinstance(prev_time, datetime.datetime) and isinstance(curr_time, datetime.datetime):
                    time_diff = (curr_time - prev_time).total_seconds()
                    if time_diff > time_gap_threshold:
                        segments.append(current_segment)
                        current_segment = [curr_point]
                        continue
            
            current_segment.append(curr_point)
        
        # 最後のセグメントを追加
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    # 距離ギャップによる分割
    if distance_gap_threshold is not None:
        segments = []
        current_segment = [track_data[0]]
        
        for i in range(1, len(track_data)):
            prev_point = track_data[i-1]
            curr_point = track_data[i]
            
            # 距離の計算と比較
            if lat_key in prev_point and lng_key in prev_point and lat_key in curr_point and lng_key in curr_point:
                distance = calculate_distance(
                    prev_point[lat_key], prev_point[lng_key],
                    curr_point[lat_key], curr_point[lng_key]
                )
                
                if distance > distance_gap_threshold:
                    segments.append(current_segment)
                    current_segment = [curr_point]
                    continue
            
            current_segment.append(curr_point)
        
        # 最後のセグメントを追加
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    # デフォルトは1つのセグメント
    return [track_data]


def analyze_track_statistics(track_data: List[Dict[str, Any]], 
                           lat_key: str = "lat", 
                           lng_key: str = "lng",
                           speed_key: str = "speed",
                           time_key: str = "timestamp") -> Dict[str, Any]:
    """
    GPSトラックデータの統計情報を計算
    
    Parameters
    ----------
    track_data : List[Dict[str, Any]]
        トラックデータポイントのリスト
    lat_key : str, optional
        緯度のキー, by default "lat"
    lng_key : str, optional
        経度のキー, by default "lng"
    speed_key : str, optional
        速度のキー, by default "speed"
    time_key : str, optional
        時間のキー, by default "timestamp"
        
    Returns
    -------
    Dict[str, Any]
        統計情報を含む辞書
    """
    if not track_data:
        return {
            "distance": 0,
            "duration": 0,
            "avg_speed": 0,
            "max_speed": 0,
            "min_speed": 0,
            "median_speed": 0,
            "speed_variance": 0,
            "bounding_box": "min_lat": 0, "min_lng": 0, "max_lat": 0, "max_lng": 0}
 {
            "distance": 0,
            "duration": 0,
            "avg_speed": 0,
            "max_speed": 0,
            "min_speed": 0,
            "median_speed": 0,
            "speed_variance": 0,
            "bounding_box": "min_lat": 0, "min_lng": 0, "max_lat": 0, "max_lng": 0}}
        return {
            "distance": 0,
            "duration": 0,
            "avg_speed": 0,
            "max_speed": 0,
            "min_speed": 0,
            "median_speed": 0,
            "speed_variance": 0,
            "bounding_box": "min_lat": 0, "min_lng": 0, "max_lat": 0, "max_lng": 0}}
 {
            "distance": 0,
            "duration": 0,
            "avg_speed": 0,
            "max_speed": 0,
            "min_speed": 0,
            "median_speed": 0,
            "speed_variance": 0,
            "bounding_box": "min_lat": 0, "min_lng": 0, "max_lat": 0, "max_lng": 0}}}
    
    # データポイント数
    num_points = len(track_data)
    
    # 初期値
    total_distance = 0
    speeds = []
    start_time = None
    end_time = None
    min_lat = float('inf')
    min_lng = float('inf')
    max_lat = float('-inf')
    max_lng = float('-inf')
    
    # 距離と速度の計算
    for i in range(num_points):
        point = track_data[i]
        
        # バウンディングボックスの更新
        if lat_key in point and lng_key in point:
            lat = float(point[lat_key])
            lng = float(point[lng_key])
            min_lat = min(min_lat, lat)
            min_lng = min(min_lng, lng)
            max_lat = max(max_lat, lat)
            max_lng = max(max_lng, lng)
        
        # 速度の抽出
        if speed_key in point:
            speeds.append(float(point[speed_key]))
        
        # 時間の抽出
        if time_key in point:
            time_value = point[time_key]
            
            # 文字列の場合はdatetimeに変換
            if isinstance(time_value, str):
                try:
                    time_value = datetime.datetime.fromisoformat(time_value.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        time_value = datetime.datetime.strptime(time_value, "%Y-%m-%dT%H:%M:%S")
                    except ValueError:
                        time_value = None
            
            # 開始・終了時間の更新
            if time_value is not None:
                if start_time is None or time_value < start_time:
                    start_time = time_value
                if end_time is None or time_value > end_time:
                    end_time = time_value
        
        # 距離の計算（2点間）
        if i > 0 and lat_key in point and lng_key in point and lat_key in track_data[i-1] and lng_key in track_data[i-1]:
            prev_point = track_data[i-1]
            distance = calculate_distance(
                prev_point[lat_key], prev_point[lng_key],
                point[lat_key], point[lng_key]
            )
            total_distance += distance
    
    # 統計計算
    avg_speed = 0
    max_speed = 0
    min_speed = 0
    median_speed = 0
    speed_variance = 0
    
    if speeds:
        avg_speed = sum(speeds) / len(speeds)
        max_speed = max(speeds)
        min_speed = min(speeds)
        median_speed = statistics.median(speeds)
        speed_variance = statistics.variance(speeds) if len(speeds) > 1 else 0
    
    # 所要時間の計算
    duration = 0
    if start_time is not None and end_time is not None:
        if isinstance(start_time, datetime.datetime) and isinstance(end_time, datetime.datetime):
            duration = (end_time - start_time).total_seconds()
        elif isinstance(start_time, (int, float)) and isinstance(end_time, (int, float)):
            duration = end_time - start_time
    
    # 結果の辞書
    return {
        "distance": total_distance,
        "duration": duration,
        "avg_speed": avg_speed,
        "max_speed": max_speed,
        "min_speed": min_speed,
        "median_speed": median_speed,
        "speed_variance": speed_variance,
        "bounding_box": {
            "min_lat": min_lat if min_lat != float('inf') else 0,
            "min_lng": min_lng if min_lng != float('inf') else 0,
            "max_lat": max_lat if max_lat != float('-inf') else 0,
        }
 {
        "distance": total_distance,
        "duration": duration,
        "avg_speed": avg_speed,
        "max_speed": max_speed,
        "min_speed": min_speed,
        "median_speed": median_speed,
        "speed_variance": speed_variance,
        "bounding_box": "min_lat": min_lat if min_lat != float('inf') else 0,
            "min_lng": min_lng if min_lng != float('inf') else 0,
            "max_lat": max_lat if max_lat != float('-inf') else 0,}
            "max_lng": max_lng if max_lng != float('-inf') else 0


def detect_significant_points(track_data: List[Dict[str, Any]], 
                            min_angle: float = 30.0,
                            min_distance: float = 50.0,
                            max_points: int = 20,
                            lat_key: str = "lat", 
                            lng_key: str = "lng") -> List[Dict[str, Any]]:
    """
    GPSトラックデータから重要なポイントを検出（方向変化が大きい点など）
    
    Parameters
    ----------
    track_data : List[Dict[str, Any]]
        トラックデータポイントのリスト
    min_angle : float, optional
        重要と判断する最小の角度変化（度）, by default 30.0
    min_distance : float, optional
        重要ポイント間の最小距離（メートル）, by default 50.0
    max_points : int, optional
        最大検出ポイント数, by default 20
    lat_key : str, optional
        緯度のキー, by default "lat"
    lng_key : str, optional
        経度のキー, by default "lng"
        
    Returns
    -------
    List[Dict[str, Any]]
        重要ポイントのリスト（元のデータポイントに情報を追加）
    """
    if not track_data or len(track_data) < 3:
        return []
    
    significant_points = []
    last_significant_idx = 0
    
    # 進行方向の変化を計算
    for i in range(1, len(track_data) - 1):
        # 3点を取得
        p1 = track_data[i-1]
        p2 = track_data[i]
        p3 = track_data[i+1]
        
        # 緯度・経度の確認
        if (lat_key not in p1 or lng_key not in p1 or
            lat_key not in p2 or lng_key not in p2 or
            lat_key not in p3 or lng_key not in p3):
            continue
        
        # 2つの方位角を計算
        bearing1 = calculate_bearing(
            p1[lat_key], p1[lng_key],
            p2[lat_key], p2[lng_key]
        )
        
        bearing2 = calculate_bearing(
            p2[lat_key], p2[lng_key],
            p3[lat_key], p3[lng_key]
        )
        
        # 角度の差を計算（0-180度の範囲）
        angle_diff = abs(((bearing2 - bearing1 + 180) % 360) - 180)
        
        # 前回の重要ポイントからの距離を計算
        distance_from_last = 0
        if significant_points:
            last_point = track_data[last_significant_idx]
            distance_from_last = calculate_distance(
                last_point[lat_key], last_point[lng_key],
                p2[lat_key], p2[lng_key]
            )
        
        # 最小角度と最小距離の条件を満たす場合
        if angle_diff >= min_angle and (not significant_points or distance_from_last >= min_distance):
            # 元のデータポイントに情報を追加
            point_data = p2.copy()
            point_data["angle_change"] = angle_diff
            point_data["is_significant"] = True
            significant_points.append(point_data)
            last_significant_idx = i
            
            # 最大数に達したら終了
            if len(significant_points) >= max_points:
                break
    
    return significant_points


def find_nearest_point(track_data: List[Dict[str, Any]], 
                     lat: float, 
                     lng: float, 
                     lat_key: str = "lat", 
                     lng_key: str = "lng") -> Optional[Dict[str, Any]]:
    """
    指定された位置に最も近いトラックポイントを見つける
    
    Parameters
    ----------
    track_data : List[Dict[str, Any]]
        トラックデータポイントのリスト
    lat : float
        検索位置の緯度
    lng : float
        検索位置の経度
    lat_key : str, optional
        緯度のキー, by default "lat"
    lng_key : str, optional
        経度のキー, by default "lng"
        
    Returns
    -------
    Optional[Dict[str, Any]]
        最も近いポイント（見つからない場合はNone）
    """
    if not track_data:
        return None
    
    min_distance = float('inf')
    nearest_point = None
    
    for point in track_data:
        if lat_key in point and lng_key in point:
            distance = calculate_distance(
                lat, lng,
                point[lat_key], point[lng_key]
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_point = point
    
    return nearest_point
