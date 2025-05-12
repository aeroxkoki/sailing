# -*- coding: utf-8 -*-
"""
パフォーマンス分析モジュール

セーリングデータからパフォーマンス変化や影響度の
分析機能を提供します。
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

from sailing_data_processor.analysis.analysis_utils import find_nearest_time

# ロギング設定
logger = logging.getLogger(__name__)

def extract_performance_metrics(track_data: pd.DataFrame, wind_data: pd.DataFrame, window_size: int) -> Dict[str, pd.Series]:
    """
    パフォーマンス指標を抽出する
    
    Parameters
    ----------
    track_data : pd.DataFrame
        セーリングトラックデータ
    wind_data : pd.DataFrame
        風向風速データ
    window_size : int
        移動平均のウィンドウサイズ
        
    Returns
    -------
    Dict[str, pd.Series]
        各種パフォーマンス指標
    """
    metrics = {}
    
    if track_data.empty:
        return metrics
    
    # 速度指標
    metrics["speed"] = track_data["speed"]
    
    # VMG指標（既に計算されている場合）
    if "vmg" in track_data.columns:
        metrics["vmg"] = track_data["vmg"]
    
    # 速度の変化率
    metrics["speed_change"] = track_data["speed"].pct_change()
    
    # 移動平均速度
    metrics["avg_speed"] = track_data["speed"].rolling(window=window_size, center=True).mean()
    
    # 風向相対値（風データがある場合）
    if not wind_data.empty:
        # 各トラックポイントの時刻に最も近い風データを見つける
        wind_relative_angles = []
        
        from sailing_data_processor.analysis.analysis_utils import angle_difference
        
        for idx, row in track_data.iterrows():
            track_time = row["timestamp"]
            wind_idx = find_nearest_time(wind_data, track_time)
            
            if wind_idx is not None:
                wind_dir = wind_data.loc[wind_idx, "wind_direction"]
                heading = row["heading"]
                
                # 風向とヘディングの相対角度
                rel_angle = angle_difference(heading, wind_dir)
                wind_relative_angles.append(abs(rel_angle))
            else:
                wind_relative_angles.append(None)
        
        metrics["wind_angle"] = pd.Series(wind_relative_angles, index=track_data.index)
    
    return metrics

def detect_performance_changes(
    track_data: pd.DataFrame, 
    performance_metrics: Dict[str, pd.Series],
    vmg_change_threshold: float,
    speed_change_threshold: float
) -> List[Dict[str, Any]]:
    """
    パフォーマンス変化ポイントを検出する
    
    Parameters
    ----------
    track_data : pd.DataFrame
        セーリングトラックデータ
    performance_metrics : Dict[str, pd.Series]
        パフォーマンス指標
    vmg_change_threshold : float
        VMG変化の閾値
    speed_change_threshold : float
        速度変化の閾値
        
    Returns
    -------
    List[Dict[str, Any]]
        パフォーマンス変化ポイントのリスト
    """
    performance_points = []
    
    if track_data.empty or not performance_metrics:
        return performance_points
    
    # VMG変化の検出
    if "vmg" in performance_metrics:
        vmg = performance_metrics["vmg"]
        # ウィンドウサイズはすでに計算済みの平均に基づいているため再計算不要
        avg_vmg = vmg.rolling(window=5, center=True).mean()
        vmg_change = avg_vmg.diff()
        
        # 大きなVMG変化のインデックスを取得
        vmg_improvements = vmg_change[vmg_change > vmg_change_threshold].index
        vmg_deteriorations = vmg_change[vmg_change < -vmg_change_threshold].index
        
        # VMG向上ポイント
        for idx in vmg_improvements:
            if idx in track_data.index:
                point_time = track_data.loc[idx, "timestamp"]
                point_lat = track_data.loc[idx, "latitude"]
                point_lon = track_data.loc[idx, "longitude"]
                
                performance_points.append({
                    "type": "vmg_improvement",
                    "time": point_time,
                    "position": (point_lat, point_lon),
                    "change_magnitude": float(vmg_change.loc[idx]),
                    "description": f"VMG improved by {vmg_change.loc[idx]:.2f} knots"
                })
        
        # VMG低下ポイント
        for idx in vmg_deteriorations:
            if idx in track_data.index:
                point_time = track_data.loc[idx, "timestamp"]
                point_lat = track_data.loc[idx, "latitude"]
                point_lon = track_data.loc[idx, "longitude"]
                
                performance_points.append({
                    "type": "vmg_deterioration",
                    "time": point_time,
                    "position": (point_lat, point_lon),
                    "change_magnitude": float(vmg_change.loc[idx]),
                    "description": f"VMG decreased by {abs(vmg_change.loc[idx]):.2f} knots"
                })
    
    # 速度変化の検出
    speed = performance_metrics["speed"]
    avg_speed = speed.rolling(window=5, center=True).mean()
    speed_change = avg_speed.diff()
    
    # 大きな速度変化のインデックスを取得
    speed_improvements = speed_change[speed_change > speed_change_threshold].index
    speed_deteriorations = speed_change[speed_change < -speed_change_threshold].index
    
    # 速度向上ポイント
    for idx in speed_improvements:
        if idx in track_data.index:
            point_time = track_data.loc[idx, "timestamp"]
            point_lat = track_data.loc[idx, "latitude"]
            point_lon = track_data.loc[idx, "longitude"]
            
            performance_points.append({
                "type": "speed_improvement",
                "time": point_time,
                "position": (point_lat, point_lon),
                "change_magnitude": float(speed_change.loc[idx]),
                "description": f"Speed improved by {speed_change.loc[idx]:.2f} knots"
            })
    
    # 速度低下ポイント
    for idx in speed_deteriorations:
        if idx in track_data.index:
            point_time = track_data.loc[idx, "timestamp"]
            point_lat = track_data.loc[idx, "latitude"]
            point_lon = track_data.loc[idx, "longitude"]
            
            performance_points.append({
                "type": "speed_deterioration",
                "time": point_time,
                "position": (point_lat, point_lon),
                "change_magnitude": float(speed_change.loc[idx]),
                "description": f"Speed decreased by {abs(speed_change.loc[idx]):.2f} knots"
            })
    
    return performance_points

def calculate_impact_scores(points: List[Dict[str, Any]], 
                         track_data: pd.DataFrame, 
                         wind_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    各ポイントのインパクトスコアを計算する
    
    Parameters
    ----------
    points : List[Dict[str, Any]]
        評価対象のポイントリスト
    track_data : pd.DataFrame
        セーリングトラックデータ
    wind_data : pd.DataFrame
        風向風速データ
        
    Returns
    -------
    List[Dict[str, Any]]
        インパクトスコア付きのポイントリスト
    """
    scored_points = []
    
    for point in points:
        point_type = point["type"]
        impact_score = 5.0  # デフォルトスコア
        
        # ポイントタイプに基づく基本スコア
        if point_type in ["tack", "jibe"]:
            # タックとジャイブのスコア調整
            base_score = 7.0
            
            # 実行の質でスコア調整
            if "execution_quality" in point:
                # 実行品質が悪いほど重要なポイントになる（改善の余地）
                quality_factor = 1.5 - point["execution_quality"]
                impact_score = base_score * (1.0 + quality_factor)
            else:
                impact_score = base_score
                
        elif point_type in ["bear_away", "head_up"]:
            # コース変更のスコア
            impact_score = 5.0
            
        elif point_type in ["vmg_improvement", "vmg_deterioration"]:
            # VMG変化のスコア
            base_score = 6.0
            
            # 変化の大きさでスコア調整
            if "change_magnitude" in point:
                magnitude_factor = min(2.0, abs(point["change_magnitude"]) * 3)
                impact_score = base_score * magnitude_factor
            else:
                impact_score = base_score
                
        elif point_type in ["speed_improvement", "speed_deterioration"]:
            # 速度変化のスコア
            base_score = 4.0
            
            # 変化の大きさでスコア調整
            if "change_magnitude" in point:
                magnitude_factor = min(2.0, abs(point["change_magnitude"]) * 2)
                impact_score = base_score * magnitude_factor
            else:
                impact_score = base_score
        
        # 風向との関係でスコア調整（風データがある場合）
        if not wind_data.empty and "time" in point:
            point_time = point["time"]
            wind_idx = find_nearest_time(wind_data, point_time)
            
            if wind_idx is not None:
                wind_speed = wind_data.loc[wind_idx, "wind_speed"]
                
                # 風が強いほど重要なポイントになる
                wind_factor = min(1.5, wind_speed / 10.0)
                impact_score *= wind_factor
        
        # スコアを0-10の範囲に正規化
        impact_score = max(0, min(10, impact_score))
        
        # ポイントにスコアを設定
        scored_point = point.copy()
        scored_point["impact_score"] = impact_score
        
        scored_points.append(scored_point)
    
    return scored_points

def remove_duplicate_points(points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    重複ポイントを除外する
    
    Parameters
    ----------
    points : List[Dict[str, Any]]
        ポイントリスト
        
    Returns
    -------
    List[Dict[str, Any]]
        重複除去後のポイントリスト
    """
    if not points:
        return []
    
    # 重複判定の時間閾値（秒）
    time_threshold = 10
    
    # 結果リスト
    unique_points = []
    
    # 各ポイントをチェック
    for point in points:
        # 既に追加したポイントと重複しないかチェック
        is_duplicate = False
        
        for unique_point in unique_points:
            # 時間が近いか
            if abs((point["time"] - unique_point["time"]).total_seconds()) < time_threshold:
                # 同じタイプか、または互いに関連するタイプか
                if point["type"] == unique_point["type"] or \
                   (point["type"].endswith("improvement") and unique_point["type"].endswith("improvement")) or \
                   (point["type"].endswith("deterioration") and unique_point["type"].endswith("deterioration")):
                    
                    is_duplicate = True
                    
                    # 既存ポイントとスコアを比較し、より重要なほうを残す
                    if "impact_score" in point and "impact_score" in unique_point:
                        if point["impact_score"] > unique_point["impact_score"]:
                            # 新しいポイントのほうが重要なら置き換え
                            unique_points.remove(unique_point)
                            is_duplicate = False
                    
                    break
        
        # 重複でなければ追加
        if not is_duplicate:
            unique_points.append(point)
    
    return unique_points

def generate_analysis_summary(high_impact_points: List[Dict[str, Any]],
                           strategic_points: List[Dict[str, Any]],
                           performance_points: List[Dict[str, Any]],
                           cross_points: List[Dict[str, Any]],
                           missed_points: List[Dict[str, Any]]) -> str:
    """
    分析サマリーを生成する
    
    Parameters
    ----------
    high_impact_points : List[Dict[str, Any]]
        高インパクトポイントリスト
    strategic_points : List[Dict[str, Any]]
        戦略的ポイントリスト
    performance_points : List[Dict[str, Any]]
        パフォーマンスポイントリスト
    cross_points : List[Dict[str, Any]]
        クロスポイントリスト
    missed_points : List[Dict[str, Any]]
        機会損失ポイントリスト
        
    Returns
    -------
    str
        分析サマリーテキスト
    """
    summary = "分析サマリー:\n"
    
    # データ量の確認
    if not high_impact_points and not strategic_points and not performance_points:
        return "重要なポイントは検出されませんでした。"
    
    # 高インパクトポイントのサマリー
    if high_impact_points:
        summary += f"\n重要ポイント: {len(high_impact_points)}個のポイントが特定されました。\n"
        
        # 最も重要なポイントを抽出
        top_points = sorted(high_impact_points, key=lambda x: x.get("impact_score", 0), reverse=True)[:3]
        
        for i, point in enumerate(top_points):
            impact = point.get("impact_score", 0)
            desc = point.get("description", "不明な操作")
            time_str = point["time"].strftime("%H:%M:%S") if "time" in point else "不明"
            
            summary += f" {i+1}. {time_str} - {desc} (重要度: {impact:.1f}/10)\n"
    
    # 戦略的ポイントのサマリー
    tack_count = sum(1 for p in strategic_points if p["type"] == "tack")
    jibe_count = sum(1 for p in strategic_points if p["type"] == "jibe")
    bear_away_count = sum(1 for p in strategic_points if p["type"] == "bear_away")
    head_up_count = sum(1 for p in strategic_points if p["type"] == "head_up")
    
    summary += f"\n操船転換: タック {tack_count}回、ジャイブ {jibe_count}回"
    if bear_away_count or head_up_count:
        summary += f", ベアアウェイ {bear_away_count}回, ヘッドアップ {head_up_count}回"
    summary += "\n"
    
    # パフォーマンスポイントのサマリー
    vmg_improvement_count = sum(1 for p in performance_points if p["type"] == "vmg_improvement")
    vmg_deterioration_count = sum(1 for p in performance_points if p["type"] == "vmg_deterioration")
    speed_improvement_count = sum(1 for p in performance_points if p["type"] == "speed_improvement")
    speed_deterioration_count = sum(1 for p in performance_points if p["type"] == "speed_deterioration")
    
    summary += f"\nパフォーマンス変化: VMG向上 {vmg_improvement_count}回, VMG低下 {vmg_deterioration_count}回"
    summary += f", 速度向上 {speed_improvement_count}回, 速度低下 {speed_deterioration_count}回\n"
    
    # 機会損失のサマリー
    if missed_points:
        summary += f"\n機会損失: {len(missed_points)}個のポイントで改善機会があります。\n"
        
        wind_shift_missed = sum(1 for p in missed_points if p["type"] == "wind_shift_response")
        if wind_shift_missed:
            summary += f" - {wind_shift_missed}回の風向変化に対する対応が不足しています。\n"
    
    # 競合艇との関係
    if cross_points:
        ahead_count = sum(1 for p in cross_points if p.get("is_ahead", False))
        behind_count = len(cross_points) - ahead_count
        
        summary += f"\n競合艇との交差: {len(cross_points)}回 (前方: {ahead_count}回, 後方: {behind_count}回)\n"
    
    return summary
