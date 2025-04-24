# -*- coding: utf-8 -*-
"""
GPS関連ユーティリティ
"""

from typing import List, Tuple, Dict, Any, Optional
import math
import gpxpy
import numpy as np
from geopy.distance import geodesic

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の距離を計算（メートル単位）
    """
    return geodesic((lat1, lon1), (lat2, lon2)).meters

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の方位角を計算（度単位）
    """
    # ラジアンへ変換
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 方位角計算
    y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    bearing = math.atan2(y, x)
    
    # 度に変換し、0-360度に正規化
    bearing_deg = math.degrees(bearing)
    return (bearing_deg + 360) % 360

def calculate_speed(distance: float, time_diff: float) -> float:
    """
    距離と時間差から速度を計算（ノット単位）
    """
    if time_diff <= 0:
        return 0.0
    
    # メートル/秒 からノットへ変換
    speed_ms = distance / time_diff
    speed_knots = speed_ms * 1.94384
    
    return speed_knots

def parse_gpx(gpx_content: str) -> List[Dict[str, Any]]:
    """
    GPXファイルの内容を解析しポイントのリストを返す
    """
    try:
        gpx = gpxpy.parse(gpx_content)
        points = []
        
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    points.append({
                        'latitude': point.latitude,
                        'longitude': point.longitude,
                        'elevation': point.elevation,
                        'time': point.time,
                        'speed': getattr(point, 'speed', None),
                        'course': getattr(point, 'course', None)
                    })
        
        return points
    except Exception as e:
        raise ValueError(f"GPXデータの解析エラー: {str(e)}")

def interpolate_points(points: List[Dict[str, Any]], interval_seconds: int = 1) -> List[Dict[str, Any]]:
    """
    GPSポイントを指定間隔で補間する
    """
    if not points or len(points) < 2:
        return points
    
    # 時間情報がない場合は補間できない
    if 'time' not in points[0] or points[0]['time'] is None:
        return points
    
    interpolated = []
    for i in range(len(points) - 1):
        current = points[i]
        next_point = points[i + 1]
        
        # 現在のポイントを追加
        interpolated.append(current)
        
        # 時間差（秒）を計算
        time_diff = (next_point['time'] - current['time']).total_seconds()
        
        # 補間が必要な場合のみ処理
        if time_diff > interval_seconds:
            # 補間するポイント数
            num_points = int(time_diff / interval_seconds)
            
            for j in range(1, num_points):
                # 補間係数
                ratio = j / num_points
                
                # 位置の線形補間
                lat = current['latitude'] + ratio * (next_point['latitude'] - current['latitude'])
                lon = current['longitude'] + ratio * (next_point['longitude'] - current['longitude'])
                
                # 時間の補間
                time = current['time'] + (next_point['time'] - current['time']) * ratio
                
                # 速度と方位も補間
                speed = None
                course = None
                if current.get('speed') is not None and next_point.get('speed') is not None:
                    speed = current['speed'] + ratio * (next_point['speed'] - current['speed'])
                if current.get('course') is not None and next_point.get('course') is not None:
                    course = current['course'] + ratio * (next_point['course'] - current['course'])
                
                interpolated.append({
                    'latitude': lat,
                    'longitude': lon,
                    'elevation': current['elevation'] + ratio * (next_point['elevation'] - current['elevation']) if (current['elevation'] is not None and next_point['elevation'] is not None) else None,
                    'time': time,
                    'speed': speed,
                    'course': course,
                    'interpolated': True
                })
    
    # 最後のポイントを追加
    interpolated.append(points[-1])
    
    return interpolated
