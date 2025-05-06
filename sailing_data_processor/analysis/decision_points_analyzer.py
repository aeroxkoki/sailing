# -*- coding: utf-8 -*-
"""
重要ポイント特定エンジン

セーリングデータから戦略的に重要なポイントを特定し、
分析するモジュールです。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
import logging
import json
from collections import defaultdict

# ロギング設定
logger = logging.getLogger(__name__)

class DecisionPointsAnalyzer:
    """
    重要ポイント特定エンジン
    
    セーリングデータから戦略的に重要なポイントを特定し、
    分析します。
    """
    
    def __init__(self, sensitivity=0.7, analysis_level="advanced"):
        """
        初期化
        
        Parameters
        ----------
        sensitivity : float, optional
            感度 (0.0-1.0), by default 0.7
        analysis_level : str, optional
            分析レベル, by default "advanced"
        """
        self.sensitivity = sensitivity
        self.analysis_level = analysis_level
        
        # 検出設定の初期化
        self._configure_detection_algorithms()
        
        logger.info(f"DecisionPointsAnalyzer initialized with sensitivity {sensitivity} and level {analysis_level}")
    
    def _configure_detection_algorithms(self):
        """検出アルゴリズムの設定"""
        # 分析レベルに応じて検出パラメータを設定
        if self.analysis_level == "basic":
            self.detection_params = {
                "strategic_decision_threshold": 0.5,
                "performance_change_threshold": 0.2,
                "window_size": 10,
                "min_impact_score": 3.0,
                "max_points": 10,
                "vmg_change_threshold": 0.3,
                "speed_change_threshold": 0.25,
                "wind_shift_threshold": 10.0
            }
        elif self.analysis_level == "intermediate":
            self.detection_params = {
                "strategic_decision_threshold": 0.4,
                "performance_change_threshold": 0.15,
                "window_size": 8,
                "min_impact_score": 2.5,
                "max_points": 15,
                "vmg_change_threshold": 0.2,
                "speed_change_threshold": 0.2,
                "wind_shift_threshold": 8.0
            }
        elif self.analysis_level == "professional":
            self.detection_params = {
                "strategic_decision_threshold": 0.2,
                "performance_change_threshold": 0.05,
                "window_size": 5,
                "min_impact_score": 1.5,
                "max_points": 30,
                "vmg_change_threshold": 0.1,
                "speed_change_threshold": 0.1,
                "wind_shift_threshold": 5.0
            }
        else:  # "advanced" (default)
            self.detection_params = {
                "strategic_decision_threshold": 0.3,
                "performance_change_threshold": 0.1,
                "window_size": 6,
                "min_impact_score": 2.0,
                "max_points": 20,
                "vmg_change_threshold": 0.15,
                "speed_change_threshold": 0.15,
                "wind_shift_threshold": 7.0
            }
    
    def identify_key_points(self, track_data: pd.DataFrame, wind_data: pd.DataFrame) -> Dict[str, Any]:
        """
        重要な決断ポイントを特定する
        
        Parameters
        ----------
        track_data : pd.DataFrame
            セーリングトラックデータ
        wind_data : pd.DataFrame
            風向風速データ
            
        Returns
        -------
        Dict[str, Any]
            重要ポイント情報の辞書
        """
        try:
            if track_data.empty:
                return {
                    "high_impact_points": [],
                    "strategic_points": [],
                    "performance_points": [],
                    "summary": "データがありません"
                }
            
            # 戦略的決断ポイントの検出
            strategic_points = self.detect_strategic_decisions(track_data, wind_data)
            
            # 性能変化ポイントの検出
            performance_metrics = self._extract_performance_metrics(track_data, wind_data)
            performance_points = self.detect_performance_changes(track_data, performance_metrics)
            
            # 全ポイントの重複除去
            all_points = strategic_points + performance_points
            # 重複ポイントの除去
            unique_points = self._remove_duplicate_points(all_points)
            
            # 各ポイントのインパクトスコア計算
            scored_points = self.calculate_impact_scores(unique_points, track_data, wind_data)
            
            # スコア順に並び替えて上位を抽出
            high_impact_points = sorted(scored_points, key=lambda x: x["impact_score"], reverse=True)
            
            # 最大表示数の制限
            max_points = self.detection_params["max_points"]
            if len(high_impact_points) > max_points:
                high_impact_points = high_impact_points[:max_points]
            
            # 競合艇とのクロスポイント分析（オプション）
            cross_points = []
            competitor_data = track_data.get("competitor_data", None)
            if competitor_data is not None:
                cross_points = self.analyze_cross_points(track_data, competitor_data)
            
            # 機会損失分析
            missed_points = self.detect_missed_opportunities(track_data, wind_data, competitor_data)
            
            # 分析サマリー作成
            summary = self._generate_analysis_summary(
                high_impact_points, strategic_points, performance_points,
                cross_points, missed_points
            )
            
            # 結果を返す
            return {
                "high_impact_points": high_impact_points,
                "strategic_points": strategic_points,
                "performance_points": performance_points,
                "cross_points": cross_points if cross_points else [],
                "missed_points": missed_points,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"重要ポイント特定中にエラーが発生しました: {e}")
            return {"error": f"重要ポイント特定中にエラーが発生しました: {e}"}
    
    def detect_strategic_decisions(self, track_data: pd.DataFrame, wind_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        戦略的決断ポイントを検出する
        
        Parameters
        ----------
        track_data : pd.DataFrame
            セーリングトラックデータ
        wind_data : pd.DataFrame
            風向風速データ
            
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
        heading_threshold = 45 * self.sensitivity  # 45度以上の変化を検出
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
            heading_change = self._angle_difference(before_heading, after_heading)
            
            # 風向に対する変化の方向を計算
            wind_idx = self._find_nearest_time(wind_data, point_time)
            if wind_idx is not None:
                wind_direction = wind_data.loc[wind_idx, "wind_direction"]
                
                # ヘディングと風向の相対角度
                before_to_wind = self._angle_difference(before_heading, wind_direction)
                after_to_wind = self._angle_difference(after_heading, wind_direction)
                
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
    
    def _extract_performance_metrics(self, track_data: pd.DataFrame, wind_data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        パフォーマンス指標を抽出する
        
        Parameters
        ----------
        track_data : pd.DataFrame
            セーリングトラックデータ
        wind_data : pd.DataFrame
            風向風速データ
            
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
        window_size = self.detection_params["window_size"]
        metrics["avg_speed"] = track_data["speed"].rolling(window=window_size, center=True).mean()
        
        # 風向相対値（風データがある場合）
        if not wind_data.empty:
            # 各トラックポイントの時刻に最も近い風データを見つける
            wind_relative_angles = []
            
            for idx, row in track_data.iterrows():
                track_time = row["timestamp"]
                wind_idx = self._find_nearest_time(wind_data, track_time)
                
                if wind_idx is not None:
                    wind_dir = wind_data.loc[wind_idx, "wind_direction"]
                    heading = row["heading"]
                    
                    # 風向とヘディングの相対角度
                    rel_angle = self._angle_difference(heading, wind_dir)
                    wind_relative_angles.append(abs(rel_angle))
                else:
                    wind_relative_angles.append(None)
            
            metrics["wind_angle"] = pd.Series(wind_relative_angles, index=track_data.index)
        
        return metrics
    
    def detect_performance_changes(self, track_data: pd.DataFrame, performance_metrics: Dict[str, pd.Series]) -> List[Dict[str, Any]]:
        """
        パフォーマンス変化ポイントを検出する
        
        Parameters
        ----------
        track_data : pd.DataFrame
            セーリングトラックデータ
        performance_metrics : Dict[str, pd.Series]
            パフォーマンス指標
            
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
            avg_vmg = vmg.rolling(window=self.detection_params["window_size"], center=True).mean()
            vmg_change = avg_vmg.diff()
            
            # 大きなVMG変化のインデックスを取得
            vmg_threshold = self.detection_params["vmg_change_threshold"]
            vmg_improvements = vmg_change[vmg_change > vmg_threshold].index
            vmg_deteriorations = vmg_change[vmg_change < -vmg_threshold].index
            
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
        avg_speed = speed.rolling(window=self.detection_params["window_size"], center=True).mean()
        speed_change = avg_speed.diff()
        
        # 大きな速度変化のインデックスを取得
        speed_threshold = self.detection_params["speed_change_threshold"]
        speed_improvements = speed_change[speed_change > speed_threshold].index
        speed_deteriorations = speed_change[speed_change < -speed_threshold].index
        
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
    
    def calculate_impact_scores(self, points: List[Dict[str, Any]], 
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
                wind_idx = self._find_nearest_time(wind_data, point_time)
                
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
    
    def generate_what_if_scenarios(self, point: Dict[str, Any], 
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
            wind_idx = self._find_nearest_time(wind_data, point_time)
            
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
    
    def analyze_cross_points(self, track_data: pd.DataFrame, 
                         competitor_data: pd.DataFrame) -> List[Dict[str, Any]]:
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
            comp_idx = self._find_nearest_time(competitor_data, row["timestamp"])
            
            if comp_idx is None:
                continue
                
            # 自艇と競合艇の位置
            own_lat = row["latitude"]
            own_lon = row["longitude"]
            comp_lat = competitor_data.loc[comp_idx, "latitude"]
            comp_lon = competitor_data.loc[comp_idx, "longitude"]
            
            # 距離を計算
            distance = self._calculate_distance(own_lat, own_lon, comp_lat, comp_lon)
            
            # 閾値以下の距離ならクロスポイントとして記録
            if distance < distance_threshold:
                # 相対位置（前後関係）を計算
                own_heading = row["heading"]
                relative_bearing = self._calculate_bearing(own_lat, own_lon, comp_lat, comp_lon)
                bearing_diff = self._angle_difference(own_heading, relative_bearing)
                
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
    
    def analyze_mark_roundings(self, track_data: pd.DataFrame, 
                           marks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                distance = self._calculate_distance(boat_lat, boat_lon, mark_lat, mark_lon)
                
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
                    heading_change = self._angle_difference(before_heading, after_heading)
                    
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
    
    def detect_missed_opportunities(self, track_data: pd.DataFrame, 
                                wind_data: pd.DataFrame,
                                competitor_data: pd.DataFrame = None) -> List[Dict[str, Any]]:
        """
        機会損失ポイントを検出する
        
        Parameters
        ----------
        track_data : pd.DataFrame
            セーリングトラックデータ
        wind_data : pd.DataFrame
            風向風速データ
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
            wind_shift_threshold = self.detection_params["wind_shift_threshold"]
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
                heading_threshold = 45 * self.sensitivity
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
                    track_idx = self._find_nearest_time(track_data, shift_time)
                    
                    if track_idx is not None:
                        # シフトの方向（有利/不利）を評価
                        shift_direction = wind_shifts.loc[shift_idx]
                        boat_heading = track_data.loc[track_idx, "heading"]
                        wind_before = wind_data.loc[shift_idx, "wind_direction"] - shift_direction
                        wind_after = wind_data.loc[shift_idx, "wind_direction"]
                        
                        # 風向とヘディングの相対角度
                        before_rel_angle = self._angle_difference(boat_heading, wind_before)
                        after_rel_angle = self._angle_difference(boat_heading, wind_after)
                        
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
    
    def _remove_duplicate_points(self, points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
    
    def _generate_analysis_summary(self, high_impact_points: List[Dict[str, Any]],
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
    
    def _find_nearest_time(self, df: pd.DataFrame, target_time: datetime) -> Optional[Any]:
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
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
    
    def _angle_difference(self, angle1: float, angle2: float) -> float:
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
