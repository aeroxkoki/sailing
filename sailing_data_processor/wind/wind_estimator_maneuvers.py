# -*- coding: utf-8 -*-
"""
sailing_data_processor.wind.wind_estimator_maneuvers モジュール

マニューバー（タック・ジャイブ）検出機能を提供します。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Union, Any
import warnings

from sailing_data_processor.wind.wind_estimator_utils import normalize_angle, calculate_angle_change

def determine_point_state(relative_angle: float, 
                        upwind_range: float = 45.0, 
                        downwind_range: float = 120.0) -> str:
    """
    風に対する艇の状態を判定する
    
    Parameters:
    -----------
    relative_angle : float
        風に対する相対角度（度）
    upwind_range : float, optional
        風上判定の閾値
    downwind_range : float, optional
        風下判定の閾値
        
    Returns:
    --------
    str
        状態（'upwind', 'downwind', 'reaching'）
    """
    # 0-360度の範囲に正規化
    rel_angle = normalize_angle(relative_angle)
    
    # 絶対値で計算（0または180度からの距離）
    abs_angle = rel_angle
    if abs_angle > 180:
        abs_angle = 360 - abs_angle
    
    # 風上状態（0度付近）
    if abs_angle < upwind_range:
        return 'upwind'
    
    # 風下状態（180度付近）
    if abs_angle > 180 - downwind_range/2:
        return 'downwind'
    
    # それ以外はリーチング
    return 'reaching'

def detect_tacks(data: pd.DataFrame, min_tack_angle: float = 60.0) -> pd.DataFrame:
    """
    タックを検出する
    
    Parameters:
    -----------
    data : pd.DataFrame
        GPSデータ（heading/course列を含む）
    min_tack_angle : float, optional
        タック検出の最小角度変化（度）
        
    Returns:
    --------
    pd.DataFrame
        検出されたタックのデータフレーム
    """
    if data.empty or len(data) < 3:
        return pd.DataFrame()
    
    heading_col = 'heading' if 'heading' in data.columns else 'course'
    if heading_col not in data.columns:
        return pd.DataFrame()
    
    tacks = []
    for i in range(1, len(data)-1):
        heading_prev = data.iloc[i-1][heading_col]
        heading_current = data.iloc[i][heading_col]
        heading_next = data.iloc[i+1][heading_col]
        
        # ヘディングの変化を計算（180度をまたぐ場合の処理を含む）
        angle_change = calculate_angle_change(heading_prev, heading_next)
        
        # タック判定（角度が急激に変化）
        if abs(angle_change) > min_tack_angle:
            tacks.append({
                'timestamp': data.iloc[i]['timestamp'] if 'timestamp' in data.columns else i,
                'angle_change': abs(angle_change),
                'heading_before': heading_prev,
                'heading_after': heading_next,
                'index': i
            })
    
    return pd.DataFrame(tacks)

def detect_gybes(data: pd.DataFrame, min_gybe_angle: float = 60.0) -> pd.DataFrame:
    """
    ジャイブを検出する
    
    Parameters:
    -----------
    data : pd.DataFrame
        GPSデータ（heading/course列を含む）
    min_gybe_angle : float, optional
        ジャイブ検出の最小角度変化（度）
        
    Returns:
    --------
    pd.DataFrame
        検出されたジャイブのデータフレーム
    """
    if data.empty or len(data) < 3:
        return pd.DataFrame()
    
    heading_col = 'heading' if 'heading' in data.columns else 'course'
    if heading_col not in data.columns:
        return pd.DataFrame()
    
    gybes = []
    for i in range(1, len(data)-1):
        heading_prev = data.iloc[i-1][heading_col]
        heading_current = data.iloc[i][heading_col]
        heading_next = data.iloc[i+1][heading_col]
        
        # ヘディングの変化を計算
        angle_change = calculate_angle_change(heading_prev, heading_next)
        
        # ジャイブ判定（右旋回）
        if angle_change > min_gybe_angle:
            gybes.append({
                'timestamp': data.iloc[i]['timestamp'] if 'timestamp' in data.columns else i,
                'angle_change': abs(angle_change),
                'heading_before': heading_prev,
                'heading_after': heading_next,
                'index': i
            })
    
    return pd.DataFrame(gybes)

def detect_maneuvers(data: pd.DataFrame, wind_direction=None, 
                    min_tack_angle: float = 60.0) -> pd.DataFrame:
    """
    マニューバー（タック/ジャイブ）を検出する
    
    Parameters:
    -----------
    data : pd.DataFrame
        GPSデータ
    wind_direction : float, optional
        風向（度）。指定された場合、マニューバーの種類を風向に基づいて判定
    min_tack_angle : float, optional
        タック/ジャイブ検出の最小角度変化（度）
        
    Returns:
    --------
    pd.DataFrame
        検出されたマニューバーのデータフレーム
    """
    # まずタックとジャイブを検出
    tacks = detect_tacks(data, min_tack_angle)
    gybes = detect_gybes(data, min_tack_angle)
    
    maneuvers_list = []
    
    # タックのデータを追加
    if not tacks.empty:
        for _, tack in tacks.iterrows():
            maneuver_data = {
                'timestamp': tack['timestamp'],
                'maneuver_type': 'tack',
                'angle_change': tack['angle_change'],
                'before_bearing': tack['heading_before'],
                'after_bearing': tack['heading_after'],
                'maneuver_confidence': 0.8,  # デフォルトの信頼度
                'before_state': 'unknown',
                'after_state': 'unknown'
            }
            
            # 風向が指定されている場合は状態を判定
            if wind_direction is not None:
                maneuver_data['before_state'] = determine_point_state(
                    tack['heading_before'] - wind_direction)
                maneuver_data['after_state'] = determine_point_state(
                    tack['heading_after'] - wind_direction)
            
            maneuvers_list.append(maneuver_data)
    
    # ジャイブのデータを追加
    if not gybes.empty:
        for _, gybe in gybes.iterrows():
            maneuver_data = {
                'timestamp': gybe['timestamp'],
                'maneuver_type': 'jibe',
                'angle_change': gybe['angle_change'],
                'before_bearing': gybe['heading_before'],
                'after_bearing': gybe['heading_after'],
                'maneuver_confidence': 0.8,  # デフォルトの信頼度
                'before_state': 'unknown',
                'after_state': 'unknown'
            }
            
            # 風向が指定されている場合は状態を判定
            if wind_direction is not None:
                maneuver_data['before_state'] = determine_point_state(
                    gybe['heading_before'] - wind_direction)
                maneuver_data['after_state'] = determine_point_state(
                    gybe['heading_after'] - wind_direction)
            
            maneuvers_list.append(maneuver_data)
    
    # タイムスタンプでソート
    maneuvers_df = pd.DataFrame(maneuvers_list)
    if not maneuvers_df.empty and 'timestamp' in maneuvers_df.columns:
        maneuvers_df = maneuvers_df.sort_values('timestamp')
        
    return maneuvers_df

def categorize_maneuver(before_bearing: float, after_bearing: float, 
                      wind_direction: float, 
                      upwind_threshold: float = 45.0,
                      downwind_threshold: float = 120.0) -> Dict[str, Any]:
    """
    マニューバーの種類を分類する
    
    Parameters:
    -----------
    before_bearing : float
        マニューバー前の方向（度）
    after_bearing : float
        マニューバー後の方向（度）
    wind_direction : float
        風向（度）
    upwind_threshold : float, optional
        風上判定の閾値
    downwind_threshold : float, optional
        風下判定の閾値
        
    Returns:
    --------
    Dict[str, Any]
        マニューバーの分類結果
    """
    # 風に対する相対角度
    rel_before = normalize_angle(before_bearing - wind_direction)
    rel_after = normalize_angle(after_bearing - wind_direction)
    
    # 角度変化
    angle_change = calculate_angle_change(before_bearing, after_bearing)
    abs_change = abs(angle_change)
    
    # 風に対する状態
    before_state = determine_point_state(rel_before, upwind_threshold, downwind_threshold)
    after_state = determine_point_state(rel_after, upwind_threshold, downwind_threshold)
    
    # マニューバー分類
    maneuver_type = "unknown"
    confidence = 0.5
    
    # タック／ジャイブの判定
    if abs_change > 60:
        if before_state == 'upwind' and after_state == 'upwind':
            maneuver_type = "tack"
            confidence = 0.9
        elif before_state == 'downwind' and after_state == 'downwind':
            maneuver_type = "jibe"
            confidence = 0.9
        else:
            # 大きな角度変化があるが、状態変化が不明確な場合
            if abs_change > 120:
                maneuver_type = "jibe"
                confidence = 0.7
            else:
                maneuver_type = "tack"
                confidence = 0.7
    else:
        # より小さな角度変化の場合
        if before_state != after_state:
            if after_state == 'downwind':
                maneuver_type = "bear_away"
                confidence = 0.8
            else:
                maneuver_type = "head_up"
                confidence = 0.8
        else:
            # コース修正
            maneuver_type = "course_correction"
            confidence = 0.6
    
    return {
        "maneuver_type": maneuver_type,
        "confidence": confidence,
        "angle_change": abs_change,
        "before_state": before_state,
        "after_state": after_state
    }
