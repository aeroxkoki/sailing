# -*- coding: utf-8 -*-
"""
分析ユーティリティモジュール

重要ポイント検出・分析に使用される一般的な
ユーティリティ関数を提供します。
"""

import math
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

def find_nearest_time(df: pd.DataFrame, target_time: datetime) -> Optional[Any]:
    """
    データフレーム内で指定時刻に最も近い時刻のインデックスを取得
    
    Parameters
    ----------
    df : pd.DataFrame
        対象データフレーム
    target_time : datetime
        検索する時刻
        
    Returns
    -------
    Any or None
        最も近い時刻のインデックス、または見つからない場合はNone
    """
    if df.empty or "timestamp" not in df.columns:
        return None
    
    # 各時刻との差分を計算
    time_diffs = [(idx, abs((row["timestamp"] - target_time).total_seconds()))
                 for idx, row in df.iterrows()]
    
    # 最小の差分を持つインデックスを返す
    min_diff_idx = min(time_diffs, key=lambda x: x[1])[0]
    
    return min_diff_idx

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の距離を計算する（メートル）
    
    Parameters
    ----------
    lat1, lon1 : float
        地点1の緯度・経度
    lat2, lon2 : float
        地点2の緯度・経度
        
    Returns
    -------
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
    
    # Haversine formula
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間の方位角を計算する（度）
    
    Parameters
    ----------
    lat1, lon1 : float
        地点1の緯度・経度
    lat2, lon2 : float
        地点2の緯度・経度
        
    Returns
    -------
    float
        方位角（度、0-360）
    """
    # 緯度経度をラジアンに変換
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 方位角計算
    dlon = lon2_rad - lon1_rad
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
    
    # 0-360度に正規化
    bearing_deg = (bearing_deg + 360) % 360
    
    return bearing_deg

def angle_difference(angle1: float, angle2: float) -> float:
    """
    2つの角度間の最小差分を計算する（-180〜180度）
    
    Parameters
    ----------
    angle1, angle2 : float
        角度（度）
        
    Returns
    -------
    float
        最小差分（度、-180〜180）
    """
    diff = (angle1 - angle2) % 360
    if diff > 180:
        diff -= 360
        
    return diff
