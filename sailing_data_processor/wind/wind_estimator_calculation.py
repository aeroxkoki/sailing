# -*- coding: utf-8 -*-
"""
sailing_data_processor.wind.wind_estimator_calculation モジュール

風向風速の計算・推定機能を提供します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
import warnings

from sailing_data_processor.wind.wind_estimator_utils import normalize_angle, create_wind_result

def calculate_vmg(boat_speed: float, boat_course: float, 
                 wind_direction: float) -> float:
    """
    VMG（Velocity Made Good）を計算する
    
    Parameters:
    -----------
    boat_speed : float
        艇速（ノット）
    boat_course : float
        艇の進行方向（度）
    wind_direction : float
        風向（度）
        
    Returns:
    --------
    float
        VMG（ノット）
    """
    import math
    
    # 風向に対する相対角度
    relative_angle = normalize_angle(boat_course - wind_direction)
    
    # VMG計算（風に対する速度成分）
    vmg = boat_speed * math.cos(math.radians(relative_angle))
    
    return vmg

def estimate_wind_from_maneuvers(maneuvers: pd.DataFrame, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    マニューバーから風向風速を推定する
    
    Parameters:
    -----------
    maneuvers : pd.DataFrame
        検出されたマニューバー
    data : pd.DataFrame
        GPSデータ
        
    Returns:
    --------
    Optional[Dict[str, Any]]
        推定結果
    """
    # マニューバーが空かどうかを確認
    if maneuvers.empty or len(maneuvers) < 2:
        return None
    
    # タックを抽出
    tacks = maneuvers[maneuvers['maneuver_type'] == 'tack']
    if tacks.empty:
        return None
    
    # タックの前後の方向から風向を推定
    wind_directions = []
    for _, tack in tacks.iterrows():
        before = tack['before_bearing']
        after = tack['after_bearing']
        
        # タックの前後の方向の平均が風向に対して約90度
        avg_heading = (before + after) / 2
        wind_dir = normalize_angle(avg_heading + 90)
        wind_directions.append(wind_dir)
    
    # 風向がない場合は終了
    if not wind_directions:
        return None
    
    # 平均風向
    mean_wind_direction = np.mean(wind_directions)
    
    # 風速は速度から推定（簡略化）
    speed_col = 'sog' if 'sog' in data.columns else 'speed'
    if speed_col in data.columns:
        wind_speed = data[speed_col].mean() * 0.8
    else:
        wind_speed = 12.0  # デフォルト値
    
    return create_wind_result(
        direction=mean_wind_direction,
        speed=wind_speed,
        confidence=0.7,
        method='maneuvers',
        timestamp=data.iloc[-1]['timestamp'] if 'timestamp' in data.columns else None
    )

def estimate_wind_from_course_speed(data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    コースと速度の変化から風向風速を推定する
    
    Parameters:
    -----------
    data : pd.DataFrame
        GPSデータ
        
    Returns:
    --------
    Optional[Dict[str, Any]]
        推定結果
    """
    if data.empty or len(data) < 10:
        return None
    
    # 簡単な実装：平均的な方向から推定
    heading_col = 'heading' if 'heading' in data.columns else 'course'
    if heading_col not in data.columns:
        return None
    
    # 平均的な向きから風向を推定（簡略化）
    mean_heading = data[heading_col].mean()
    wind_direction = normalize_angle(mean_heading + 180)
    
    # 速度から風速を推定（簡略化）
    speed_col = 'sog' if 'sog' in data.columns else 'speed'
    if speed_col in data.columns:
        mean_speed = data[speed_col].mean()
        wind_speed = mean_speed * 0.7  # 簡単な推定
    else:
        wind_speed = 10.0  # デフォルト値
    
    return create_wind_result(
        direction=wind_direction,
        speed=wind_speed,
        confidence=0.5,
        method='course_speed',
        timestamp=data.iloc[-1]['timestamp'] if 'timestamp' in data.columns else None
    )

def preprocess_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    データの前処理を行う
    
    Parameters:
    -----------
    data : pd.DataFrame
        生のGPSデータ
        
    Returns:
    --------
    pd.DataFrame
        前処理されたデータ
    """
    df = data.copy()
    
    # タイムスタンプの確認
    if 'timestamp' not in df.columns:
        df['timestamp'] = pd.to_datetime(df.index)
    
    # 速度の確認
    if 'sog' not in df.columns and 'speed' not in df.columns:
        # 位置から速度を計算する必要がある場合
        pass
    
    # ヘディングの確認
    if 'heading' not in df.columns and 'course' not in df.columns:
        # コースから計算する必要がある場合
        if 'course' in df.columns:
            df['heading'] = df['course']
        elif 'bearing' in df.columns:
            df['heading'] = df['bearing']
    
    return df
