# -*- coding: utf-8 -*-
"""
sailing_data_processor.improved_features モジュール

WindEstimatorクラスに追加する改良機能の実装
"""

import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

def determine_sailing_state(self, course: float, wind_direction: float) -> str:
    """
    コースと風向から艇の帆走状態を詳細に判定（改善版）
    
    Parameters:
    -----------
    course : float
        艇の進行方向（度、0-360）
    wind_direction : float
        風向（度、0-360）
        
    Returns:
    --------
    str
        帆走状態
        - 'upwind_port': 風上 ポートタック
        - 'upwind_starboard': 風上 スターボードタック
        - 'downwind_port': 風下 ポートタック
        - 'downwind_starboard': 風下 スターボードタック
        - 'reaching_port': リーチング ポートタック
        - 'reaching_starboard': リーチング スターボードタック
    """
    # 風向に対する相対角度（-180〜180度）
    rel_angle = self._calculate_angle_difference(course, wind_direction)
    
    # タック判定（風向に対する相対位置）
    # 0〜180度の範囲にある場合はポートタック、-180〜0度の範囲にある場合はスターボードタック
    tack = 'port' if rel_angle >= 0 else 'starboard'
    
    # 風上/風下判定のしきい値
    upwind_threshold = self.params["upwind_threshold"]
    downwind_threshold = self.params["downwind_threshold"]
    
    # 風に対する状態を判定
    abs_rel_angle = abs(rel_angle)
    
    if abs_rel_angle <= upwind_threshold:
        state = f'upwind_{tack}'
    elif abs_rel_angle >= downwind_threshold:
        state = f'downwind_{tack}'
    else:
        state = f'reaching_{tack}'
    
    return state

def identify_maneuver_type(self, before_bearing: float, after_bearing: float, 
                         wind_direction: float, speed_before: float, speed_after: float,
                         abs_angle_change: float, before_state: str, after_state: str) -> Tuple[str, float]:
    """
    マニューバータイプを識別し、信頼度を計算
    
    Parameters:
    -----------
    before_bearing : float
        マニューバー前の進行方向
    after_bearing : float
        マニューバー後の進行方向
    wind_direction : float
        風向
    speed_before : float
        マニューバー前の速度
    speed_after : float
        マニューバー後の速度
    abs_angle_change : float
        角度変化の絶対値
    before_state : str
        マニューバー前の帆走状態
    after_state : str
        マニューバー後の帆走状態
        
    Returns:
    --------
    Tuple[str, float]
        (マニューバータイプ, 信頼度)
    """
    # 状態の解析
    before_tack = before_state.split('_')[-1]  # 'port' または 'starboard'
    after_tack = after_state.split('_')[-1]
    before_point = before_state.split('_')[0]  # 'upwind', 'downwind', 'reaching'
    after_point = after_state.split('_')[0]
    
    # 同じタックのままなら明らかにタックやジャイブではない
    if before_tack == after_tack:
        return "course_change", 0.6
    
    # タックの識別（風上または風上付近での操船、風位置が大きく変わる）
    tack_conditions = [
        # タックの必要条件：タックの変更
        before_tack \!= after_tack,
        
        # どちらも風上またはリーチングの状態（より正確に）
        ('upwind' in before_state or 'reaching' in before_state) and 
        ('upwind' in after_state or 'reaching' in after_state),
        
        # 方位変化が60〜150度（タックの典型的な範囲）
        60 <= abs_angle_change <= 150,
        
        # 典型的には操船で速度が落ちる
        speed_after < speed_before * 0.9
    ]
    
    # ジャイブの識別（風下または風下付近での操船、風位置が大きく変わる）
    jibe_conditions = [
        # ジャイブの必要条件：タックの変更
        before_tack \!= after_tack,
        
        # どちらも風下またはリーチングの状態
        ('downwind' in before_state or 'reaching' in before_state) and 
        ('downwind' in after_state or 'reaching' in after_state),
        
        # 方位変化が60〜150度（ジャイブの典型的な範囲）
        60 <= abs_angle_change <= 150
    ]
    
    # 条件が満たされているかカウント
    tack_score = sum(1 for cond in tack_conditions if cond) / len(tack_conditions)
    jibe_score = sum(1 for cond in jibe_conditions if cond) / len(jibe_conditions)
    
    # より高いスコアに基づいて分類
    if tack_score > jibe_score and tack_score > 0.5:
        # タックのスコアに基づいて信頼度を計算
        return "tack", min(1.0, tack_score * 1.2)
    elif jibe_score > 0.5:
        return "jibe", min(1.0, jibe_score * 1.2)
    elif before_point == 'upwind' and after_point \!= 'upwind':
        # 風上から風下/リーチングへの転換 (ベアウェイ)
        return "bear_away", 0.8
    elif before_point \!= 'upwind' and after_point == 'upwind':
        # 風下/リーチングから風上への転換 (ヘッドアップ)
        return "head_up", 0.8
    else:
        # 判断できない場合
        return "unknown", 0.5

def estimate_wind_from_maneuvers_improved(self, maneuvers: dict, full_df: dict) -> Dict[str, Any]:
    """
    マニューバー（タック/ジャイブ）から風向風速を推定（改善版）
    
    Parameters:
    -----------
    maneuvers : pd.DataFrame
        検出されたマニューバーのデータフレーム
    full_df : pd.DataFrame
        完全なGPSデータフレーム
        
    Returns:
    --------
    Dict[str, Any]
        風向風速推定結果
    """
    if maneuvers.empty or len(maneuvers) < 2:
        return None
    
    # 最新のタイムスタンプ
    latest_timestamp = full_df['timestamp'].max()
    
    # タックのみを抽出（より信頼性が高い）
    tack_maneuvers = maneuvers[maneuvers['maneuver_type'] == 'tack']
    
    # タックが不足している場合は全マニューバー使用
    if len(tack_maneuvers) < 2:
        tack_maneuvers = maneuvers
    
    # 風向計算（各マニューバーから推定）
    wind_directions = []
    confidences = []
    timestamps = []
    
    for _, maneuver in tack_maneuvers.iterrows():
        before_bearing = maneuver['before_bearing']
        after_bearing = maneuver['after_bearing']
        timestamp = maneuver['timestamp']
        
        # 改善：タックの場合の風向推定をより正確に行う
        # 艇は風から約45度開けて帆走するため、風向は艇の進行方向から約45度風上側にある
        
        # 前後の艇の進行方向の風向からの最大開き角度（約45度）
        typical_angle = 42.0  # 一般的な風上帆走角度
        
        # 風向を推定（2つの方法）
        # 方法1: 2つの進行方向の平均
        avg_direction = (before_bearing + after_bearing) / 2
        wind_dir1 = (avg_direction + 180) % 360  # 平均方向の反対
        
        # 方法2: 2つの進行方向から風上に修正角度分開けたベクトルの平均
        # 前の進行方向からtypical_angle度開けた方向
        before_vector_angle = (before_bearing + typical_angle) % 360
        # 後の進行方向からtypical_angle度開けた方向
        after_vector_angle = (after_bearing + typical_angle) % 360
        
        # ベクトル平均のために角度をラジアンに変換
        before_rad = np.radians(before_vector_angle)
        after_rad = np.radians(after_vector_angle)
        
        # ベクトル平均
        avg_x = (np.cos(before_rad) + np.cos(after_rad)) / 2
        avg_y = (np.sin(before_rad) + np.sin(after_rad)) / 2
        wind_dir2 = np.degrees(np.arctan2(avg_y, avg_x)) % 360
        
        # 両方の推定値の重みづけ平均
        wind_direction = (wind_dir1 * 0.4 + wind_dir2 * 0.6) % 360
        
        # 信頼度の計算要素
        # 1. マニューバー自体の信頼度
        maneuver_confidence = maneuver.get('maneuver_confidence', 0.8)
        
        # 2. 速度変化（一般にタック中は減速する）
        speed_ratio = maneuver.get('speed_ratio', 1.0)
        speed_confidence = 1.0 - min(1.0, abs(speed_ratio - 0.7) / 0.5)
        
        # 3. 角度変化（一般的なタック角度は90度付近）
        angle_change = abs(maneuver.get('bearing_change', 90.0))
        angle_confidence = 1.0 - min(1.0, abs(angle_change - 90) / 45)
        
        # 総合信頼度
        confidence = (maneuver_confidence * 0.5 + speed_confidence * 0.2 + angle_confidence * 0.3)
        
        # 結果に追加
        wind_directions.append(wind_direction)
        confidences.append(confidence)
        timestamps.append(timestamp)
    
    # 時間重みも考慮（最新のデータほど高い重み）
    time_weights = np.linspace(0.7, 1.0, len(timestamps))
    
    # 信頼度と時間重みを掛け合わせた総合重み
    combined_weights = np.array(confidences) * time_weights
    
    # 角度の加重平均（円環統計）
    sin_values = np.sin(np.radians(wind_directions))
    cos_values = np.cos(np.radians(wind_directions))
    
    weighted_sin = np.average(sin_values, weights=combined_weights)
    weighted_cos = np.average(cos_values, weights=combined_weights)
    
    avg_wind_dir = np.degrees(np.arctan2(weighted_sin, weighted_cos)) % 360
    avg_confidence = np.average(confidences, weights=time_weights)
    
    # 風速の推定
    wind_speed = self._estimate_wind_speed_from_maneuvers(maneuvers, full_df)
    
    return self._create_wind_result(
        float(avg_wind_dir), wind_speed, float(avg_confidence),
        "maneuver_analysis", latest_timestamp
    )
