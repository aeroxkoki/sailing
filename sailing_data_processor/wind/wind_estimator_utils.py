# -*- coding: utf-8 -*-
"""
sailing_data_processor.wind.wind_estimator_utils モジュール

風向風速推定のためのユーティリティ関数を提供します。
"""

import math
from typing import Tuple, Dict, Any

def normalize_angle(angle: float) -> float:
    """
    角度を0-360度の範囲に正規化する
    
    Parameters:
    -----------
    angle : float
        角度（度）
        
    Returns:
    --------
    float
        正規化された角度（0-360度）
    """
    # まず360で割った余りを計算
    normalized = angle % 360
    
    # 負の値の場合は360を足す
    if normalized < 0:
        normalized += 360
        
    return normalized

def calculate_angle_change(angle1: float, angle2: float) -> float:
    """
    2つの角度の変化を計算する（-180〜180度）
    
    Parameters:
    -----------
    angle1, angle2 : float
        角度（度）
        
    Returns:
    --------
    float
        角度変化（度）
    """
    diff = angle2 - angle1
    
    # -180〜180度の範囲に正規化
    while diff > 180:
        diff -= 360
    while diff < -180:
        diff += 360
        
    return diff

def calculate_bearing(point1: Tuple[float, float], 
                     point2: Tuple[float, float]) -> float:
    """
    2点間のベアリングを計算する
    
    Parameters:
    -----------
    point1, point2 : Tuple[float, float]
        位置（緯度、経度）
        
    Returns:
    --------
    float
        ベアリング（度）
    """
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # ラジアンに変換
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # ベアリング計算
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    
    bearing = math.degrees(math.atan2(x, y))
    
    # 0-360度の範囲に正規化
    return normalize_angle(bearing)

def calculate_distance(point1: Tuple[float, float], 
                      point2: Tuple[float, float]) -> float:
    """
    2点間の距離を計算する（海里）
    
    Parameters:
    -----------
    point1, point2 : Tuple[float, float]
        位置（緯度、経度）
        
    Returns:
    --------
    float
        距離（海里）
    """
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    # ラジアンに変換
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # 地球の半径（海里）
    r = 3440.065
    
    return c * r

def calculate_endpoint(start_point: Tuple[float, float], 
                      bearing: float, distance: float) -> Tuple[float, float]:
    """
    始点からある方向と距離にある終点を計算する
    
    Parameters:
    -----------
    start_point : Tuple[float, float]
        始点（緯度、経度）
    bearing : float
        方位（度）
    distance : float
        距離（海里）
        
    Returns:
    --------
    Tuple[float, float]
        終点（緯度、経度）
    """
    lat1, lon1 = start_point
    
    # ラジアンに変換
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    bearing = math.radians(bearing)
    
    # 地球の半径（海里）
    r = 3440.065
    
    # 角距離
    angular_distance = distance / r
    
    # 終点の計算
    lat2 = math.asin(math.sin(lat1) * math.cos(angular_distance) +
                    math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing))
    
    lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
                            math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2))
    
    # 度に変換
    lat2 = math.degrees(lat2)
    lon2 = math.degrees(lon2)
    
    return (lat2, lon2)

def convert_angle_to_wind_vector(angle: float, speed: float = 1.0) -> Tuple[float, float]:
    """
    風向角度を風向ベクトルに変換する
    
    Parameters:
    -----------
    angle : float
        風向（度）
    speed : float, optional
        風速（ノット）
        
    Returns:
    --------
    Tuple[float, float]
        風向ベクトル（x, y成分）
    """
    # 北を0度として時計回りの角度から、数学的な角度（東が0度、反時計回り）に変換
    math_angle = 90 - angle
    
    x = speed * math.cos(math.radians(math_angle))
    y = speed * math.sin(math.radians(math_angle))
    
    return (x, y)

def convert_wind_vector_to_angle(vector: Tuple[float, float]) -> float:
    """
    風向ベクトルを風向角度に変換する
    
    Parameters:
    -----------
    vector : Tuple[float, float]
        風向ベクトル（x, y成分）
        
    Returns:
    --------
    float
        風向（度）
    """
    x, y = vector
    
    # ベクトルが原点の場合は0度を返す
    if abs(x) < 1e-10 and abs(y) < 1e-10:
        return 0.0
        
    # 数学的な角度（東が0度、反時計回り）を計算
    math_angle = math.degrees(math.atan2(y, x))
    
    # 北を0度として時計回りの角度に変換
    wind_angle = normalize_angle(90 - math_angle)
    
    # 風ベクトルは風が吹いてくる方向を表すため、180度回転させる
    wind_angle = normalize_angle(wind_angle + 180)
    
    return wind_angle

def create_wind_result(direction: float, speed: float, 
                     confidence: float, method: str, 
                     timestamp: Any = None) -> Dict[str, Any]:
    """
    風向風速推定結果を作成する
    
    Parameters:
    -----------
    direction : float
        風向（度）
    speed : float  
        風速（ノット）
    confidence : float
        信頼度（0-1）
    method : str
        推定方法
    timestamp : Any, optional
        タイムスタンプ
        
    Returns:
    --------
    Dict[str, Any]
        風向風速推定結果
    """
    return {
        "direction": direction,
        "speed": speed,
        "confidence": confidence,
        "method": method,
        "timestamp": timestamp
    }

def get_conversion_functions(latitude: float) -> Tuple[callable, callable]:
    """
    指定された緯度における度とメートルの変換関数を返す
    
    Parameters:
    -----------
    latitude : float
        緯度
        
    Returns:
    --------
    Tuple[callable, callable]
        (緯度変換関数, 経度変換関数)のタプル
    """
    # 球体近似による1度あたりの距離（メートル）
    earth_radius = 6371000  # 地球の平均半径（メートル）
    
    # 緯度1度あたりのメートル距離（ほぼ一定）
    meters_per_lat = earth_radius * math.pi / 180
    
    # 経度1度あたりのメートル距離（緯度によって変化）
    meters_per_lon = meters_per_lat * math.cos(math.radians(latitude))
    
    # 緯度変換関数
    def lat_to_meters(lat_diff):
        return lat_diff * meters_per_lat
    
    # 経度変換関数
    def lon_to_meters(lon_diff):
        return lon_diff * meters_per_lon
    
    return lat_to_meters, lon_to_meters
