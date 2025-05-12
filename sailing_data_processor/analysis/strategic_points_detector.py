# -*- coding: utf-8 -*-
"""
戦略的ポイント検出モジュール

セーリングデータから戦略的に重要なポイントを特定する
機能を提供します。
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from sailing_data_processor.analysis.analysis_utils import (
    find_nearest_time, calculate_distance, calculate_bearing, angle_difference
)

# ロギング設定
logger = logging.getLogger(__name__)

def detect_strategic_decisions(track_data: pd.DataFrame, wind_data: pd.DataFrame, sensitivity: float) -> List[Dict[str, Any]]:
    """
    戦略的決断ポイントを検出する
    
    Parameters
    ----------
    track_data : pd.DataFrame
        セーリングトラックデータ
    wind_data : pd.DataFrame
        風向風速データ
    sensitivity : float
        検出感度
        
    Returns
    -------
    List[Dict[str, Any]]
        戦略的決断ポイントのリスト
    """
    strategic_points = []
    
    if track_data.empty:
        return strategic_points
    
    # ヘディングの変化を検出
    heading_diff = track_data["heading"].diff().abs()
    
    # 大きなヘディング変化のインデックスを取得
    heading_threshold = 45 * sensitivity  # 45度以上の変化を検出
    heading_changes = heading_diff[heading_diff > heading_threshold].index
    
    # 各ヘディング変化ポイントを分析
    for idx in heading_changes:
        point_idx = track_data.index.get_loc(idx)
        
        # インデックスが範囲外にならないように確認
        if point_idx < 2 or point_idx >= len(track_data) - 2:
            continue
            
        # 変化前後のデータを取得
        before_idx = track_data.index[point_idx - 2]
        after_idx = track_data.index[point_idx + 2]
        
        # 変化前後のヘディングと速度
        before_heading = track_data.loc[before_idx, "heading"]
        after_heading = track_data.loc[after_idx, "heading"]
        before_speed = track_data.loc[before_idx, "speed"]
        after_speed = track_data.loc[after_idx, "speed"]
        
        # 該当時刻の情報
        point_time = track_data.loc[idx, "timestamp"]
        point_lat = track_data.loc[idx, "latitude"]
        point_lon = track_data.loc[idx, "longitude"]
        
        # ポイントタイプの決定（タックかジャイブか）
        heading_change = angle_difference(before_heading, after_heading)
        
        # 風向に対する変化の方向を計算
        wind_idx = find_nearest_time(wind_data, point_time)
        if wind_idx is not None:
            wind_direction = wind_data.loc[wind_idx, "wind_direction"]
            
            # ヘディングと風向の相対角度
            before_to_wind = angle_difference(before_heading, wind_direction)
            after_to_wind = angle_difference(after_heading, wind_direction)
            
            # 風上から風下への変化か、風下から風上への変化かを判定
            is_upwind_before = abs(before_to_wind) < 90
            is_upwind_after = abs(after_to_wind) < 90
            
            # 相対的な風向の変化を判定
            if is_upwind_before and is_upwind_after:
                # 両方とも風上 → タック
                maneuver_type = "tack"
            elif not is_upwind_before and not is_upwind_after:
                # 両方とも風下 → ジャイブ
                maneuver_type = "jibe"
            elif is_upwind_before and not is_upwind_after:
                # 風上から風下へ → ベアアウェイ
                maneuver_type = "bear_away"
            else:
                # 風下から風上へ → ヘッドアップ
                maneuver_type = "head_up"
        else:
            # 風データがない場合は単純にヘディング変化から判定
            if abs(heading_change) > 90:
                maneuver_type = "tack" if abs(heading_change) > 150 else "jibe"
            else:
                maneuver_type = "course_change"
        
        # 実行の質を評価
        execution_quality = 1.0 - min(1.0, (before_speed - after_speed) / before_speed if before_speed > 0 else 0)
        
        # 戦略的決断情報を作成
        strategic_point = {
            "type": maneuver_type,
            "time": point_time,
            "position": (point_lat, point_lon),
            "heading_change": heading_change,
            "speed_before": before_speed,
            "speed_after": after_speed,
            "execution_quality": execution_quality,
            "description": f"{maneuver_type.capitalize()} with {abs(heading_change):.1f}° change"
        }
        
        strategic_points.append(strategic_point)
    
    return strategic_points

def analyze_cross_points(track_data: pd.DataFrame, competitor_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    競合艇とのクロスポイントを分析する
    
    Parameters
    ----------
    track_data : pd.DataFrame
        セーリングトラックデータ
    competitor_data : pd.DataFrame
        競合艇のトラックデータ
        
    Returns
    -------
    List[Dict[str, Any]]
        クロスポイント情報のリスト
    """
    cross_points = []
    
    if track_data.empty or competitor_data.empty:
        return cross_points
    
    # 自艇と競合艇の位置を時間でリサンプリング（共通の時間軸で比較するため）
    # この実装ではシンプルにするため、競合艇のデータが同じ時間間隔であると仮定
    
    # 距離の閾値（メートル）
    distance_threshold = 50
    
    # 各時点での距離を計算
    for idx, row in track_data.iterrows():
        # 最も近い時間の競合艇データを検索
        comp_idx = find_nearest_time(competitor_data, row["timestamp"])
        
        if comp_idx is None:
            continue
            
        # 自艇と競合艇の位置
        own_lat = row["latitude"]
        own_lon = row["longitude"]
        comp_lat = competitor_data.loc[comp_idx, "latitude"]
        comp_lon = competitor_data.loc[comp_idx, "longitude"]
        
        # 距離を計算
        distance = calculate_distance(own_lat, own_lon, comp_lat, comp_lon)
        
        # 閾値以下の距離ならクロスポイントとして記録
        if distance < distance_threshold:
            # 相対位置（前後関係）を計算
            own_heading = row["heading"]
            relative_bearing = calculate_bearing(own_lat, own_lon, comp_lat, comp_lon)
            bearing_diff = angle_difference(own_heading, relative_bearing)
            
            # -90〜+90度ならば前方、それ以外なら後方
            is_ahead = abs(bearing_diff) < 90
            
            # 相対速度
            own_speed = row["speed"]
            comp_speed = competitor_data.loc[comp_idx, "speed"] if "speed" in competitor_data.columns else 0
            
            cross_points.append({
                "time": row["timestamp"],
                "position": (own_lat, own_lon),
                "distance": distance,
                "is_ahead": is_ahead,
                "relative_speed": own_speed - comp_speed,
                "description": f"Cross with competitor at {distance:.1f}m {'ahead' if is_ahead else 'behind'}"
            })
    
    return cross_points

def analyze_mark_roundings(track_data: pd.DataFrame, marks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    マーク回航を分析する
    
    Parameters
    ----------
    track_data : pd.DataFrame
        セーリングトラックデータ
    marks : List[Dict[str, Any]]
        マーク情報のリスト
        
    Returns
    -------
    List[Dict[str, Any]]
        マーク回航ポイント情報のリスト
    """
    mark_points = []
    
    if track_data.empty or not marks:
        return mark_points
    
    # 各マークについて
    for mark in marks:
        mark_lat = mark["latitude"]
        mark_lon = mark["longitude"]
        mark_type = mark.get("type", "unknown")
        
        # マーク周辺を通過したか検出
        closest_distance = float('inf')
        closest_idx = None
        
        for idx, row in track_data.iterrows():
            boat_lat = row["latitude"]
            boat_lon = row["longitude"]
            
            # マークとの距離を計算
            distance = calculate_distance(boat_lat, boat_lon, mark_lat, mark_lon)
            
            # 最短距離を更新
            if distance < closest_distance:
                closest_distance = distance
                closest_idx = idx
        
        # マークに十分近づいたか
        mark_radius = 20  # マーク半径（メートル）
        if closest_distance <= mark_radius * 2 and closest_idx is not None:
            # マーク通過前後のデータを取得
            idx_loc = track_data.index.get_loc(closest_idx)
            
            # インデックスが範囲外にならないように確認
            before_idx = max(0, idx_loc - 5)
            after_idx = min(len(track_data) - 1, idx_loc + 5)
            
            # 回航前後の方位変化を計算
            if before_idx < idx_loc < after_idx:
                before_heading = track_data.iloc[before_idx]["heading"]
                after_heading = track_data.iloc[after_idx]["heading"]
                heading_change = angle_difference(before_heading, after_heading)
                
                # 回航方向（時計回りまたは反時計回り）
                is_clockwise = heading_change > 0
                
                # マーク回航情報を作成
                mark_points.append({
                    "type": "mark_rounding",
                    "mark_type": mark_type,
                    "time": track_data.loc[closest_idx, "timestamp"],
                    "position": (track_data.loc[closest_idx, "latitude"], 
                               track_data.loc[closest_idx, "longitude"]),
                    "closest_distance": closest_distance,
                    "heading_change": heading_change,
                    "is_clockwise": is_clockwise,
                    "description": f"{mark_type.capitalize()} mark rounding {'clockwise' if is_clockwise else 'counter-clockwise'}"
                })
    
    return mark_points

def detect_missed_opportunities(
    track_data: pd.DataFrame, 
    wind_data: pd.DataFrame,
    wind_shift_threshold: float,
    competitor_data: pd.DataFrame = None
) -> List[Dict[str, Any]]:
    """
    機会損失ポイントを検出する
    
    Parameters
    ----------
    track_data : pd.DataFrame
        セーリングトラックデータ
    wind_data : pd.DataFrame
        風向風速データ
    wind_shift_threshold : float
        風向変化の閾値
    competitor_data : pd.DataFrame, optional
        競合艇のトラックデータ
        
    Returns
    -------
    List[Dict[str, Any]]
        機会損失ポイント情報のリスト
    """
    missed_points = []
    
    if track_data.empty:
        return missed_points
    
    # シンプルな風シフト機会損失検出
    if not wind_data.empty:
        # 風向の変化を計算
        wind_shifts = wind_data["wind_direction"].diff()
        
        # 大きな風向変化のインデックスを取得
        significant_shifts = wind_shifts[abs(wind_shifts) > wind_shift_threshold].index
        
        # 風向変化に対する対応を検出（変化後に近いタックがあるか）
        for shift_idx in significant_shifts:
            shift_time = wind_data.loc[shift_idx, "timestamp"]
            
            # シフト後の適切な対応時間（15秒〜3分以内）
            min_response_time = shift_time + timedelta(seconds=15)
            max_response_time = shift_time + timedelta(minutes=3)
            
            # その時間範囲内のタックを検索
            response_found = False
            
            # タックを検出
            heading_diff = track_data["heading"].diff().abs()
            heading_threshold = 45
            heading_changes = heading_diff[heading_diff > heading_threshold].index
            
            for change_idx in heading_changes:
                change_time = track_data.loc[change_idx, "timestamp"]
                
                # シフト後の適切な時間内にタックがあるか
                if min_response_time <= change_time <= max_response_time:
                    response_found = True
                    break
            
            # 適切な対応がなかった場合は機会損失として記録
            if not response_found:
                # シフト時に最も近いトラックデータの位置を取得
                track_idx = find_nearest_time(track_data, shift_time)
                
                if track_idx is not None:
                    # シフトの方向（有利/不利）を評価
                    shift_direction = wind_shifts.loc[shift_idx]
                    boat_heading = track_data.loc[track_idx, "heading"]
                    wind_before = wind_data.loc[shift_idx, "wind_direction"] - shift_direction
                    wind_after = wind_data.loc[shift_idx, "wind_direction"]
                    
                    # 風向とヘディングの相対角度
                    before_rel_angle = angle_difference(boat_heading, wind_before)
                    after_rel_angle = angle_difference(boat_heading, wind_after)
                    
                    # シフトによる相対角度の変化が大きいか（有利/不利の判断）
                    angle_change = after_rel_angle - before_rel_angle
                    
                    # シフトによる利益/損失を評価
                    is_favorable = (abs(after_rel_angle) < abs(before_rel_angle))
                    
                    # 機会損失を記録
                    missed_points.append({
                        "type": "wind_shift_response",
                        "time": shift_time,
                        "position": (track_data.loc[track_idx, "latitude"], 
                                   track_data.loc[track_idx, "longitude"]),
                        "shift_magnitude": float(shift_direction),
                        "is_favorable": is_favorable,
                        "description": f"Missed response to {abs(shift_direction):.1f}° {'favorable' if is_favorable else 'unfavorable'} wind shift"
                    })
    
    # 競合艇データがある場合の競合艇と比較した機会損失
    if competitor_data is not None and not competitor_data.empty:
        # 今回は簡単な処理のみ実装
        # 実際には競合艇と自艇の差分から様々な機会損失を検出可能
        pass
    
    return missed_points

def generate_what_if_scenarios(point: Dict[str, Any], 
                           track_data: pd.DataFrame, 
                           wind_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    特定のポイントに対するWhat-ifシナリオを生成する
    
    Parameters
    ----------
    point : Dict[str, Any]
        分析対象ポイント
    track_data : pd.DataFrame
        セーリングトラックデータ
    wind_data : pd.DataFrame
        風向風速データ
        
    Returns
    -------
    List[Dict[str, Any]]
        代替シナリオのリスト
    """
    scenarios = []
    
    # ポイントタイプに基づくシナリオ生成
    point_type = point.get("type")
    
    if point_type in ["tack", "jibe"]:
        # タック/ジャイブの代替シナリオ
        
        # 1. 継続シナリオ（タック/ジャイブをしなかった場合）
        if "old_heading" in point and "new_heading" in point:
            old_heading = point["old_heading"]
            
            scenarios.append({
                "scenario": "no_maneuver",
                "description": f"Continue on {old_heading}° without {point_type}",
                "outcome": "Potentially better VMG but may miss tactical advantage",
                "impact": "Medium"
            })
        
        # 2. 遅延シナリオ（数秒後にタック/ジャイブした場合）
        scenarios.append({
            "scenario": "delayed_maneuver",
            "description": f"Delay {point_type} by 10-20 seconds",
            "outcome": "Potentially different wind condition or better position",
            "impact": "Medium to High"
        })
        
        # 3. 実行品質改善シナリオ
        if "execution_quality" in point and point["execution_quality"] < 0.9:
            scenarios.append({
                "scenario": "improved_execution",
                "description": f"Better execution of {point_type} (less speed loss)",
                "outcome": "Faster transition, less distance lost",
                "impact": "High"
            })
    
    elif point_type in ["vmg_deterioration", "speed_deterioration"]:
        # パフォーマンス低下の代替シナリオ
        
        # 1. 早期修正シナリオ
        scenarios.append({
            "scenario": "early_correction",
            "description": "Earlier recognition and correction of performance issue",
            "outcome": "Less overall performance loss",
            "impact": "High"
        })
        
        # 2. 代替設定シナリオ
        scenarios.append({
            "scenario": "alternative_settings",
            "description": "Different sail trim or helm adjustment",
            "outcome": "Maintaining better performance in changing conditions",
            "impact": "Medium to High"
        })
    
    # 共通シナリオ（風の変化への対応）
    if not wind_data.empty and "time" in point:
        point_time = point["time"]
        wind_idx = find_nearest_time(wind_data, point_time)
        
        if wind_idx is not None:
            wind_direction = wind_data.loc[wind_idx, "wind_direction"]
            
            # 風の変化を予測したシナリオ
            scenarios.append({
                "scenario": "wind_anticipation",
                "description": f"Anticipate wind shift from {wind_direction}°",
                "outcome": "Better positioning for upcoming wind conditions",
                "impact": "High"
            })
    
    return scenarios
