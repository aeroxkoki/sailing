# -*- coding: utf-8 -*-
"""
重要決断ポイント分析器

レースデータから戦略的に重要な決断ポイントやパフォーマンス変化点を検出するモジュールです。
特に重要な判断ポイントの特定、影響度評価、代替戦略シナリオの生成などの機能を提供します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
import logging
import json
from collections import defaultdict

# ロガーの設定
logger = logging.getLogger(__name__)

class DecisionPointsAnalyzer:
    """
    重要決断ポイント分析器
    
    レースデータから戦略的に重要な決断ポイントや
    パフォーマンス変化点を検出します。
    """
    
    def __init__(self, sensitivity=0.7, analysis_level="advanced"):
        """
        初期化
        
        Parameters
        ----------
        sensitivity : float, optional
            検出感度 (0.0-1.0), by default 0.7
        analysis_level : str, optional
            分析レベル, by default "advanced"
        """
        self.sensitivity = sensitivity
        self.analysis_level = analysis_level
        
        # 検出アルゴリズムの設定
        self._configure_detection_algorithms()
        
        logger.info(f"DecisionPointsAnalyzer initialized with sensitivity {sensitivity} and level {analysis_level}")
    
    def _configure_detection_algorithms(self):
        """検出アルゴリズムの設定"""
        # 分析レベルに応じたパラメータ設定
        if self.analysis_level == "basic":
            self.detection_params = {
                "strategic_decision_threshold": 0.5,
                "performance_change_threshold": 0.2,
                "window_size": 10,
                "min_impact_score": 3.0,
                "max_points": 10
            }
        elif self.analysis_level == "intermediate":
            self.detection_params = {
                "strategic_decision_threshold": 0.4,
                "performance_change_threshold": 0.15,
                "window_size": 8,
                "min_impact_score": 2.5,
                "max_points": 15
            }
        elif self.analysis_level == "professional":
            self.detection_params = {
                "strategic_decision_threshold": 0.2,
                "performance_change_threshold": 0.05,
                "window_size": 5,
                "min_impact_score": 1.5,
                "max_points": 30
            }
        else:  # "advanced" (default)
            self.detection_params = {
                "strategic_decision_threshold": 0.3,
                "performance_change_threshold": 0.1,
                "window_size": 6,
                "min_impact_score": 2.0,
                "max_points": 20
            }
        
        # 感度に応じた閾値の調整
        self.detection_params["strategic_decision_threshold"] *= (2 - self.sensitivity)
        self.detection_params["performance_change_threshold"] *= (2 - self.sensitivity)
        self.detection_params["min_impact_score"] *= (2 - self.sensitivity)
        
        logger.debug(f"Detection parameters configured: {self.detection_params}")
    
    def identify_key_points(self, track_data, wind_data, strategy_evaluation=None, course_data=None):
        """
        重要ポイントの特定
        
        Parameters
        ----------
        track_data : DataFrame
            GPSトラックデータ
        wind_data : DataFrame
            風データ
        strategy_evaluation : dict, optional
            戦略評価結果, by default None
        course_data : dict, optional
            コース情報, by default None
            
        Returns
        -------
        dict
            特定された重要ポイント
        """
        logger.info("Starting identification of key decision points")
        
        # データの検証
        if track_data.empty:
            logger.warning("Empty track data provided")
            return {"error": "トラックデータがありません。"}
        
        try:
            # 1. 戦略的決断ポイントの検出
            logger.info("Detecting strategic decision points")
            strategic_points = self.detect_strategic_decisions(track_data, wind_data)
            
            # 2. パフォーマンス変化点の検出
            logger.info("Detecting performance change points")
            performance_metrics = self._extract_performance_metrics(track_data, wind_data)
            performance_points = self.detect_performance_changes(track_data, performance_metrics)
            
            # 3. クロスポイントの分析（競合艇データがあれば）
            cross_points = []
            if "competitor_data" in strategy_evaluation and strategy_evaluation["competitor_data"] is not None:
                logger.info("Analyzing cross points with competitors")
                cross_points = self.analyze_cross_points(track_data, strategy_evaluation["competitor_data"])
            
            # 4. マーク回航の分析（コースデータがあれば）
            mark_points = []
            if course_data and "marks" in course_data:
                logger.info("Analyzing mark roundings")
                mark_points = self.analyze_mark_roundings(track_data, course_data)
            
            # 5. 機会損失ポイントの検出
            logger.info("Detecting missed opportunities")
            competitor_data = strategy_evaluation.get("competitor_data") if strategy_evaluation else None
            missed_points = self.detect_missed_opportunities(track_data, wind_data, competitor_data)
            
            # 6. 影響度スコアの計算と重要ポイントの選定
            logger.info("Calculating impact scores and selecting key points")
            all_points = strategic_points + performance_points + cross_points + mark_points + missed_points
            
            # 影響度スコアでソート
            all_points_with_impact = self.calculate_impact_scores(all_points, track_data, wind_data)
            all_points_with_impact.sort(key=lambda x: x.get("impact_score", 0), reverse=True)
            
            # 高影響ポイントの選定（スコアとポイント数で制限）
            high_impact_points = [
                p for p in all_points_with_impact 
                if p.get("impact_score", 0) >= self.detection_params["min_impact_score"]
            ][:self.detection_params["max_points"]]
            
            # 7. What-ifシナリオの生成
            logger.info("Generating what-if scenarios for high impact points")
            for point in high_impact_points:
                point["alternatives"] = self.generate_what_if_scenarios(
                    point, track_data, wind_data, course_data
                )
            
            # 8. 分析サマリーの生成
            logger.info("Generating analysis summary")
            summary = self._generate_analysis_summary(
                high_impact_points, strategic_points, performance_points, cross_points, missed_points
            )
            
            # 重要ポイント検出結果をまとめる
            result = {
                "high_impact_points": high_impact_points,
                "strategic_points_count": len(strategic_points),
                "performance_points_count": len(performance_points),
                "cross_points_count": len(cross_points),
                "mark_points_count": len(mark_points),
                "missed_opportunities_count": len(missed_points),
                "total_points_detected": len(all_points),
                "summary": summary
            }
            
            logger.info(f"Identified {len(high_impact_points)} high impact points from {len(all_points)} total detected points")
            return result
            
        except Exception as e:
            logger.error(f"Error in decision points identification: {str(e)}", exc_info=True)
            return {"error": f"重要ポイント特定中にエラーが発生しました: {str(e)}"}
    
    def detect_strategic_decisions(self, track_data, wind_data):
        """
        戦略的決断ポイントの検出
        
        Parameters
        ----------
        track_data : DataFrame
            GPSトラックデータ
        wind_data : DataFrame
            風データ
            
        Returns
        -------
        list
            検出された戦略的決断ポイント
        """
        logger.info("Detecting strategic decisions")
        strategic_points = []
        
        # 必要なカラムの存在確認
        required_cols = ["timestamp", "latitude", "longitude", "heading"]
        if not all(col in track_data.columns for col in required_cols):
            logger.warning(f"Missing required columns for strategic decisions detection: {required_cols}")
            return strategic_points
        
        try:
            # 1. 方向変化の検出（タック、ジャイブなど）
            direction_points = self._detect_direction_changes(track_data)
            strategic_points.extend(direction_points)
            
            # 2. レイラインポイントの検出（コース情報がある場合）
            # 注: 実際の実装では、コース情報からレイラインを計算する必要がある
            layline_points = self._detect_layline_approaches(track_data, wind_data)
            strategic_points.extend(layline_points)
            
            # 3. 風向変化への対応ポイントの検出
            if wind_data is not None and not wind_data.empty:
                wind_shift_points = self._detect_wind_shift_responses(track_data, wind_data)
                strategic_points.extend(wind_shift_points)
            
            # 4. 戦術的位置取りの変更ポイントの検出
            positioning_points = self._detect_tactical_positioning_changes(track_data)
            strategic_points.extend(positioning_points)
            
            # 5. リスク/リワード判断ポイントの検出
            risk_reward_points = self._detect_risk_reward_decisions(track_data)
            strategic_points.extend(risk_reward_points)
            
            logger.info(f"Detected {len(strategic_points)} strategic decision points")
            return strategic_points
            
        except Exception as e:
            logger.error(f"Error detecting strategic decisions: {str(e)}", exc_info=True)
            return []
    
    def detect_performance_changes(self, track_data, performance_metrics):
        """
        パフォーマンス変化点の検出
        
        Parameters
        ----------
        track_data : DataFrame
            GPSトラックデータ
        performance_metrics : dict
            パフォーマンス指標
            
        Returns
        -------
        list
            検出されたパフォーマンス変化点
        """
        logger.info("Detecting performance changes")
        performance_points = []
        
        # 必要なカラムの存在確認
        required_cols = ["timestamp", "speed"]
        if not all(col in track_data.columns for col in required_cols):
            logger.warning(f"Missing required columns for performance changes detection: {required_cols}")
            return performance_points
        
        try:
            # 1. 速度変化点の検出
            speed_change_points = self._detect_by_speed(track_data)
            performance_points.extend(speed_change_points)
            
            # 2. VMG変化点の検出（VMGカラムがある場合）
            if "vmg" in track_data.columns:
                vmg_change_points = self._detect_by_vmg(track_data)
                performance_points.extend(vmg_change_points)
            
            # 3. 効率変化点の検出
            if "efficiency" in performance_metrics:
                efficiency_change_points = self._detect_by_efficiency(track_data, performance_metrics["efficiency"])
                performance_points.extend(efficiency_change_points)
            
            # 4. アングル最適化ポイントの検出
            angle_points = self._detect_angle_optimization(track_data, performance_metrics)
            performance_points.extend(angle_points)
            
            logger.info(f"Detected {len(performance_points)} performance change points")
            return performance_points
            
        except Exception as e:
            logger.error(f"Error detecting performance changes: {str(e)}", exc_info=True)
            return []
    
    def analyze_cross_points(self, track_data, competitor_data):
        """
        クロスポイントの分析
        
        Parameters
        ----------
        track_data : DataFrame
            GPSトラックデータ
        competitor_data : DataFrame
            競合艇データ
            
        Returns
        -------
        list
            分析されたクロスポイント
        """
        logger.info("Analyzing cross points")
        cross_points = []
        
        # 必要なカラムの存在確認
        required_cols = ["timestamp", "latitude", "longitude"]
        if not all(col in track_data.columns for col in required_cols) or \
           not all(col in competitor_data.columns for col in required_cols):
            logger.warning(f"Missing required columns for cross points analysis: {required_cols}")
            return cross_points
        
        try:
            # 1. クロスポイントの検出
            # 注: 実際の実装では、時空間的な近接性を計算してクロスを検出する必要がある
            unique_competitors = competitor_data["boat_id"].unique() if "boat_id" in competitor_data.columns else [1]
            
            for boat_id in unique_competitors:
                boat_data = competitor_data[competitor_data["boat_id"] == boat_id] if "boat_id" in competitor_data.columns else competitor_data
                
                # 時間的に近いポイントを探索
                for i in range(len(track_data) - 1):
                    current_time = track_data.iloc[i]["timestamp"]
                    
                    # 競合艇の近い時間のデータを取得
                    competitor_at_time = boat_data[(boat_data["timestamp"] >= current_time - timedelta(seconds=10)) & 
                                                  (boat_data["timestamp"] <= current_time + timedelta(seconds=10))]
                    
                    if competitor_at_time.empty:
                        continue
                    
                    # 空間的な近さを計算
                    for _, comp_row in competitor_at_time.iterrows():
                        distance = self._calculate_distance(
                            track_data.iloc[i]["latitude"], track_data.iloc[i]["longitude"],
                            comp_row["latitude"], comp_row["longitude"]
                        )
                        
                        # 距離が閾値以下の場合クロスポイントとして検出
                        if distance < 100:  # 100m以内
                            cross_point = {
                                "type": "cross_point",
                                "time": track_data.iloc[i]["timestamp"],
                                "position": {
                                    "latitude": track_data.iloc[i]["latitude"],
                                    "longitude": track_data.iloc[i]["longitude"]
                                },
                                "boat_id": boat_id,
                                "distance": distance,
                                "relative_bearing": self._calculate_relative_bearing(
                                    track_data.iloc[i], comp_row
                                ) if "heading" in track_data.columns and "heading" in comp_row else None,
                                "description": f"競合艇 {boat_id} とのクロスポイント。距離: {distance:.1f}m"
                            }
                            
                            cross_points.append(cross_point)
            
            # 2. クロスポイントの重複を除去
            # 同じ競合艇との近い時間のクロスは統合
            unique_cross_points = []
            for point in cross_points:
                is_duplicate = False
                for unique_point in unique_cross_points:
                    if point["boat_id"] == unique_point["boat_id"] and \
                       abs((point["time"] - unique_point["time"]).total_seconds()) < 30:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    unique_cross_points.append(point)
            
            logger.info(f"Analyzed {len(unique_cross_points)} cross points")
            return unique_cross_points
            
        except Exception as e:
            logger.error(f"Error analyzing cross points: {str(e)}", exc_info=True)
            return []
    
    def analyze_mark_roundings(self, track_data, course_data):
        """
        マーク回航の分析
        
        Parameters
        ----------
        track_data : DataFrame
            GPSトラックデータ
        course_data : dict
            コース情報
            
        Returns
        -------
        list
            分析されたマーク回航ポイント
        """
        logger.info("Analyzing mark roundings")
        mark_points = []
        
        # 必要なカラムの存在確認
        required_cols = ["timestamp", "latitude", "longitude"]
        if not all(col in track_data.columns for col in required_cols) or "marks" not in course_data:
            logger.warning("Missing required data for mark rounding analysis")
            return mark_points
        
        try:
            # マークごとに回航ポイントを検出
            for i, mark in enumerate(course_data["marks"]):
                # マーク位置の取得
                mark_lat = mark.get("latitude")
                mark_lon = mark.get("longitude")
                mark_type = mark.get("type", "unknown")
                
                if mark_lat is None or mark_lon is None:
                    continue
                
                # トラックデータからマーク近辺のポイントを特定
                closest_distance = float('inf')
                closest_idx = -1
                
                for j, row in track_data.iterrows():
                    distance = self._calculate_distance(
                        row["latitude"], row["longitude"],
                        mark_lat, mark_lon
                    )
                    
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_idx = j
                
                # 閾値内にマークに接近したポイントがある場合
                if closest_distance < 50:  # 50m以内
                    # 回航前後のデータを取得
                    approach_start_idx = max(0, closest_idx - 30)
                    exit_end_idx = min(len(track_data) - 1, closest_idx + 30)
                    
                    approach_data = track_data.iloc[approach_start_idx:closest_idx+1]
                    exit_data = track_data.iloc[closest_idx:exit_end_idx+1]
                    
                    # 回航の品質を評価
                    rounding_quality = self._evaluate_rounding_quality(approach_data, exit_data)
                    
                    # マーク回航ポイントの作成
                    mark_point = {
                        "type": "mark_rounding",
                        "mark_type": mark_type,
                        "mark_number": i + 1,
                        "time": track_data.iloc[closest_idx]["timestamp"],
                        "position": {
                            "latitude": track_data.iloc[closest_idx]["latitude"],
                            "longitude": track_data.iloc[closest_idx]["longitude"]
                        },
                        "distance_to_mark": closest_distance,
                        "rounding_quality": rounding_quality,
                        "approach_speed": approach_data["speed"].mean() if "speed" in approach_data.columns else None,
                        "exit_speed": exit_data["speed"].mean() if "speed" in exit_data.columns else None,
                        "description": f"マーク{i+1}({mark_type})の回航ポイント。品質: {rounding_quality:.1f}/10"
                    }
                    
                    # 回航の問題点があれば追加
                    if rounding_quality < 6:
                        issues = self._identify_rounding_issues(approach_data, exit_data)
                        mark_point["issues"] = issues
                        mark_point["description"] += f" 課題: {', '.join(issues)}"
                    
                    mark_points.append(mark_point)
            
            logger.info(f"Analyzed {len(mark_points)} mark rounding points")
            return mark_points
            
        except Exception as e:
            logger.error(f"Error analyzing mark roundings: {str(e)}", exc_info=True)
            return []
    
    def detect_missed_opportunities(self, track_data, wind_data, competitor_data=None):
        """
        機会損失ポイントの検出
        
        Parameters
        ----------
        track_data : DataFrame
            GPSトラックデータ
        wind_data : DataFrame
            風データ
        competitor_data : DataFrame, optional
            競合艇データ, by default None
            
        Returns
        -------
        list
            検出された機会損失ポイント
        """
        logger.info("Detecting missed opportunities")
        missed_points = []
        
        try:
            # 1. 風向変化への対応遅れの検出
            if wind_data is not None and not wind_data.empty:
                wind_shift_misses = self._detect_missed_wind_shifts(track_data, wind_data)
                missed_points.extend(wind_shift_misses)
            
            # 2. レイラインアプローチの問題検出
            layline_misses = self._detect_layline_issues(track_data, wind_data)
            missed_points.extend(layline_misses)
            
            # 3. 競合艇比較による機会損失の検出
            if competitor_data is not None:
                competitor_misses = self._detect_competitor_advantage_points(track_data, competitor_data)
                missed_points.extend(competitor_misses)
            
            # 4. 非効率な操船の検出
            inefficiency_points = self._detect_inefficient_sailing(track_data)
            missed_points.extend(inefficiency_points)
            
            logger.info(f"Detected {len(missed_points)} missed opportunity points")
            return missed_points
            
        except Exception as e:
            logger.error(f"Error detecting missed opportunities: {str(e)}", exc_info=True)
            return []
    
    def calculate_impact_scores(self, decision_points, track_data, wind_data):
        """
        決断ポイントの影響度スコア計算
        
        Parameters
        ----------
        decision_points : list
            決断ポイントのリスト
        track_data : DataFrame
            GPSトラックデータ
        wind_data : DataFrame
            風データ
            
        Returns
        -------
        list
            影響度スコア付きの決断ポイント
        """
        logger.info("Calculating impact scores for decision points")
        
        try:
            # 各ポイントに影響度スコアを付与
            for point in decision_points:
                # 基本スコア（ポイントタイプによる）
                base_score = self._get_base_impact_score(point["type"])
                
                # スコア修飾要因
                modifiers = {}
                
                # 1. タイミング修飾（レース全体における位置）
                if "time" in point and "timestamp" in track_data.columns:
                    race_start = track_data["timestamp"].min()
                    race_end = track_data["timestamp"].max()
                    race_duration = (race_end - race_start).total_seconds()
                    
                    if race_duration > 0:
                        point_time_ratio = (point["time"] - race_start).total_seconds() / race_duration
                        
                        # レース序盤と終盤のポイントはより重要
                        if point_time_ratio < 0.2 or point_time_ratio > 0.8:
                            modifiers["timing"] = 1.2
                        else:
                            modifiers["timing"] = 1.0
                
                # 2. 風の状況による修飾
                if wind_data is not None and not wind_data.empty and "time" in point:
                    # ポイント時点の風データを取得
                    wind_at_time = wind_data[wind_data["timestamp"] <= point["time"]].iloc[-1] if "timestamp" in wind_data.columns else None
                    
                    if wind_at_time is not None:
                        # 風が強いまたは変動しているときのポイントはより重要
                        if "wind_speed" in wind_at_time and wind_at_time["wind_speed"] > 15:
                            modifiers["wind_condition"] = 1.3
                        else:
                            modifiers["wind_condition"] = 1.0
                
                # 3. ポイント特有の修飾要因
                if point["type"] == "mark_rounding":
                    # マーク回航の品質が低い場合、より重要
                    if "rounding_quality" in point and point["rounding_quality"] < 5:
                        modifiers["quality_impact"] = 1.5
                    else:
                        modifiers["quality_impact"] = 1.0
                
                elif point["type"] == "cross_point":
                    # 距離が近いクロスポイントはより重要
                    if "distance" in point:
                        distance_factor = max(0.5, min(1.5, 100 / max(10, point["distance"])))
                        modifiers["proximity"] = distance_factor
                
                elif point["type"] in ["tack", "gybe"]:
                    # マニューバーの効率が低い場合、より重要
                    if "efficiency" in point:
                        efficiency_factor = max(0.8, min(1.5, 2 - point["efficiency"]))
                        modifiers["efficiency_impact"] = efficiency_factor
                
                # 修飾要因の適用
                impact_score = base_score
                for modifier in modifiers.values():
                    impact_score *= modifier
                
                # ポイントに影響度スコアを設定（0-10のスケールに正規化）
                point["impact_score"] = min(10, max(0, impact_score))
                
                # 影響要因も記録
                point["impact_factors"] = modifiers
            
            logger.info("Impact scores calculated for all decision points")
            return decision_points
            
        except Exception as e:
            logger.error(f"Error calculating impact scores: {str(e)}", exc_info=True)
            
            # エラー時は基本スコアのみを設定
            for point in decision_points:
                if "impact_score" not in point:
                    point["impact_score"] = self._get_base_impact_score(point["type"])
            
            return decision_points
    
    def generate_what_if_scenarios(self, decision_point, track_data, wind_data, course_data=None):
        """
        What-ifシナリオの生成
        
        Parameters
        ----------
        decision_point : dict
            決断ポイント
        track_data : DataFrame
            GPSトラックデータ
        wind_data : DataFrame
            風データ
        course_data : dict, optional
            コース情報, by default None
            
        Returns
        -------
        list
            生成された代替シナリオ
        """
        logger.info(f"Generating what-if scenarios for point type: {decision_point.get('type', 'unknown')}")
        
        try:
            # ポイントタイプに応じたシナリオ生成
            point_type = decision_point.get("type", "unknown")
            
            if point_type == "tack":
                return self._generate_tack_scenarios(decision_point, track_data, wind_data)
            
            elif point_type == "gybe":
                return self._generate_gybe_scenarios(decision_point, track_data, wind_data)
            
            elif point_type == "layline":
                return self._generate_layline_scenarios(decision_point, track_data, wind_data, course_data)
            
            elif point_type == "wind_shift":
                return self._generate_wind_shift_scenarios(decision_point, track_data, wind_data)
            
            elif point_type == "mark_rounding":
                return self._generate_mark_rounding_scenarios(decision_point, track_data)
            
            elif point_type == "cross_point":
                return self._generate_cross_point_scenarios(decision_point, track_data)
            
            elif "missed" in point_type:
                return self._generate_missed_opportunity_scenarios(decision_point, track_data, wind_data)
            
            else:
                # 一般的なシナリオ
                return self._generate_generic_scenarios(decision_point, track_data, wind_data)
            
        except Exception as e:
            logger.error(f"Error generating what-if scenarios: {str(e)}", exc_info=True)
            
            # エラー時はシンプルなシナリオを返す
            return [{
                "scenario": "代替戦略",
                "outcome": "異なる結果が得られる可能性がありますが、詳細を計算できませんでした。",
                "impact": 0.5
            }]
    
    def _extract_performance_metrics(self, track_data, wind_data):
        """パフォーマンス指標の抽出"""
        metrics = {}
        
        # 速度統計
        if "speed" in track_data.columns:
            metrics["avg_speed"] = track_data["speed"].mean()
            metrics["max_speed"] = track_data["speed"].max()
            metrics["speed_variability"] = track_data["speed"].std() / metrics["avg_speed"] if metrics["avg_speed"] > 0 else 0
        
        # VMG統計（ある場合）
        if "vmg" in track_data.columns:
            metrics["avg_vmg"] = track_data["vmg"].mean()
            metrics["max_vmg"] = track_data["vmg"].max()
        
        # 効率の計算（速度とVMGの比率など）
        if "speed" in track_data.columns and "vmg" in track_data.columns:
            efficiency = track_data["vmg"] / track_data["speed"]
            metrics["efficiency"] = efficiency
            metrics["avg_efficiency"] = efficiency.mean()
        
        return metrics
    
    def _detect_direction_changes(self, track_data):
        """方向変化の検出"""
        direction_points = []
        
        # 必要なカラムの確認
        if "heading" not in track_data.columns:
            return direction_points
        
        window_size = self.detection_params["window_size"]
        
        # 一定のウィンドウでヘディングの変化を検出
        for i in range(window_size, len(track_data) - window_size):
            # 前後のウィンドウでの平均ヘディング
            pre_heading = track_data.iloc[i-window_size:i]["heading"].mean()
            post_heading = track_data.iloc[i:i+window_size]["heading"].mean()
            
            # ヘディング差の計算（角度の特殊性を考慮）
            heading_diff = abs((post_heading - pre_heading + 180) % 360 - 180)
            
            # 大きな方向変化を検出
            if heading_diff > 60:  # 60度以上の変化
                # タックかジャイブかを判定
                if 60 < heading_diff < 160:
                    point_type = "tack"
                    efficiency = self._calculate_tack_efficiency(track_data, i, window_size)
                    description = f"タックポイント。方向変化: {heading_diff:.1f}度, 効率: {efficiency:.2f}"
                else:
                    point_type = "gybe"
                    efficiency = self._calculate_gybe_efficiency(track_data, i, window_size)
                    description = f"ジャイブポイント。方向変化: {heading_diff:.1f}度, 効率: {efficiency:.2f}"
                
                # ポイントの作成
                direction_point = {
                    "type": point_type,
                    "time": track_data.iloc[i]["timestamp"],
                    "position": {
                        "latitude": track_data.iloc[i]["latitude"],
                        "longitude": track_data.iloc[i]["longitude"]
                    },
                    "heading_change": heading_diff,
                    "pre_heading": pre_heading,
                    "post_heading": post_heading,
                    "efficiency": efficiency,
                    "description": description
                }
                
                direction_points.append(direction_point)
        
        # 近接ポイントの除去（重複を防ぐ）
        filtered_points = []
        if direction_points:
            filtered_points.append(direction_points[0])
            
            for point in direction_points[1:]:
                # 前のポイントとの時間差
                time_diff = (point["time"] - filtered_points[-1]["time"]).total_seconds()
                
                # 30秒以上離れている場合のみ追加
                if time_diff > 30:
                    filtered_points.append(point)
        
        return filtered_points
    
    def _detect_layline_approaches(self, track_data, wind_data):
        """レイラインアプローチの検出"""
        layline_points = []
        
        # 注: 実際の実装では、風向データとコース情報から
        # レイラインの位置を計算する必要がある
        
        # シンプルな実装としては、一定の時間間隔で
        # 艇の方向が風向に近い（風上マーク）または風向と逆（風下マーク）の
        # 場合にレイラインに近いと仮定
        
        if "heading" not in track_data.columns or wind_data is None or wind_data.empty:
            return layline_points
        
        # 風向の取得
        if "wind_direction" in wind_data.columns:
            # 風向の平均値を使用
            avg_wind_dir = wind_data["wind_direction"].mean()
            
            # 30秒ごとにチェック
            for i in range(0, len(track_data), 30):
                if i >= len(track_data):
                    break
                
                # 艇の向きと風向の角度差
                heading = track_data.iloc[i]["heading"]
                angle_to_wind = abs((heading - avg_wind_dir + 180) % 360 - 180)
                
                # 風向に対して45度前後（風上レイライン）または135度前後（風下レイライン）
                is_upwind_layline = 35 < angle_to_wind < 55
                is_downwind_layline = 125 < angle_to_wind < 145
                
                if is_upwind_layline or is_downwind_layline:
                    layline_type = "upwind_layline" if is_upwind_layline else "downwind_layline"
                    
                    # レイラインポイントの作成
                    layline_point = {
                        "type": "layline",
                        "layline_type": layline_type,
                        "time": track_data.iloc[i]["timestamp"],
                        "position": {
                            "latitude": track_data.iloc[i]["latitude"],
                            "longitude": track_data.iloc[i]["longitude"]
                        },
                        "angle_to_wind": angle_to_wind,
                        "description": f"{'風上' if is_upwind_layline else '風下'}レイラインアプローチ。風向との角度: {angle_to_wind:.1f}度"
                    }
                    
                    layline_points.append(layline_point)
        
        return layline_points
    
    def _detect_wind_shift_responses(self, track_data, wind_data):
        """風向変化への対応の検出"""
        wind_shift_points = []
        
        # 必要なカラムの確認
        if "wind_direction" not in wind_data.columns or "timestamp" not in wind_data.columns:
            return wind_shift_points
        
        # 風向変化の検出
        window_size = 5  # 5ポイントの移動ウィンドウ
        
        for i in range(window_size, len(wind_data) - window_size):
            # 前後のウィンドウでの平均風向
            pre_wind_dir = wind_data.iloc[i-window_size:i]["wind_direction"].mean()
            post_wind_dir = wind_data.iloc[i:i+window_size]["wind_direction"].mean()
            
            # 風向差の計算（角度の特殊性を考慮）
            wind_shift = abs((post_wind_dir - pre_wind_dir + 180) % 360 - 180)
            
            # 一定以上の風向変化を検出
            if wind_shift > 10:  # 10度以上の変化
                wind_shift_time = wind_data.iloc[i]["timestamp"]
                
                # 風向変化後の艇の対応を検出
                response_window = 60  # 60秒以内の対応を検索
                
                # 風向変化後の近いトラックデータを探す
                response_data = track_data[
                    (track_data["timestamp"] >= wind_shift_time) & 
                    (track_data["timestamp"] <= wind_shift_time + timedelta(seconds=response_window))
                ]
                
                if not response_data.empty and "heading" in response_data.columns:
                    # 対応の前後で方向変化があるか確認
                    if len(response_data) > 2:
                        initial_heading = response_data.iloc[0]["heading"]
                        final_heading = response_data.iloc[-1]["heading"]
                        
                        # 方向変化の計算
                        heading_change = abs((final_heading - initial_heading + 180) % 360 - 180)
                        
                        # 有意な方向変化があれば風向変化対応ポイントとして検出
                        if heading_change > 5:
                            shift_direction = "left" if ((post_wind_dir - pre_wind_dir + 180) % 360 - 180) < 0 else "right"
                            response_type = self._determine_wind_shift_response_type(
                                shift_direction, initial_heading, final_heading
                            )
                            
                            # 風向変化対応ポイントの作成
                            response_point = {
                                "type": "wind_shift_response",
                                "time": response_data.iloc[0]["timestamp"],
                                "position": {
                                    "latitude": response_data.iloc[0]["latitude"],
                                    "longitude": response_data.iloc[0]["longitude"]
                                },
                                "wind_shift_magnitude": wind_shift,
                                "wind_shift_direction": shift_direction,
                                "response_type": response_type,
                                "heading_change": heading_change,
                                "description": f"風向変化({wind_shift:.1f}度, {shift_direction})への対応。反応タイプ: {response_type}"
                            }
                            
                            wind_shift_points.append(response_point)
        
        return wind_shift_points
    
    def _detect_tactical_positioning_changes(self, track_data):
        """戦術的位置取りの変更の検出"""
        # 簡易実装のため、空のリストを返す
        # 実際の実装では、コース情報や競合艇の位置を考慮して
        # 戦術的な位置取りの変更を検出する必要がある
        return []
    
    def _detect_risk_reward_decisions(self, track_data):
        """リスク/リワード判断の検出"""
        # 簡易実装のため、空のリストを返す
        # 実際の実装では、コース情報やリスクモデルを利用して
        # 高リスク/高リワードの判断を検出する必要がある
        return []
    
    def _detect_by_speed(self, track_data):
        """速度変化による検出"""
        speed_points = []
        
        # 必要なカラムの確認
        if "speed" not in track_data.columns:
            return speed_points
        
        # 移動平均の計算（ノイズ除去）
        window_size = self.detection_params["window_size"]
        track_data['speed_ma'] = track_data['speed'].rolling(window=window_size, center=True).mean()
        
        # NaNを除去
        speed_data = track_data.dropna(subset=['speed_ma'])
        
        if len(speed_data) < window_size * 2:
            return speed_points
        
        # 速度変化の検出
        threshold = self.detection_params["performance_change_threshold"] * speed_data["speed_ma"].mean()
        
        for i in range(window_size, len(speed_data) - window_size):
            # 前後の速度差
            pre_speed = speed_data.iloc[i-window_size:i]["speed_ma"].mean()
            post_speed = speed_data.iloc[i:i+window_size]["speed_ma"].mean()
            speed_diff = post_speed - pre_speed
            
            # 変化率
            change_ratio = abs(speed_diff / pre_speed) if pre_speed > 0 else 0
            
            # 閾値以上の変化を検出
            if change_ratio > threshold:
                point_type = "speed_improvement" if speed_diff > 0 else "speed_deterioration"
                
                # 速度変化ポイントの作成
                speed_point = {
                    "type": point_type,
                    "time": speed_data.iloc[i]["timestamp"],
                    "position": {
                        "latitude": speed_data.iloc[i]["latitude"],
                        "longitude": speed_data.iloc[i]["longitude"]
                    },
                    "pre_speed": pre_speed,
                    "post_speed": post_speed,
                    "speed_change": speed_diff,
                    "change_ratio": change_ratio,
                    "description": f"速度{'向上' if speed_diff > 0 else '低下'}ポイント。変化: {speed_diff:.2f}ノット({change_ratio*100:.1f}%)"
                }
                
                speed_points.append(speed_point)
        
        # 近接ポイントの除去
        filtered_points = []
        if speed_points:
            filtered_points.append(speed_points[0])
            
            for point in speed_points[1:]:
                # 前のポイントとの時間差
                time_diff = (point["time"] - filtered_points[-1]["time"]).total_seconds()
                
                # 30秒以上離れている場合のみ追加
                if time_diff > 30:
                    filtered_points.append(point)
        
        return filtered_points
    
    def _detect_by_vmg(self, track_data):
        """VMG変化による検出"""
        vmg_points = []
        
        # 必要なカラムの確認
        if "vmg" not in track_data.columns:
            return vmg_points
        
        # 移動平均の計算（ノイズ除去）
        window_size = self.detection_params["window_size"]
        track_data['vmg_ma'] = track_data['vmg'].rolling(window=window_size, center=True).mean()
        
        # NaNを除去
        vmg_data = track_data.dropna(subset=['vmg_ma'])
        
        if len(vmg_data) < window_size * 2:
            return vmg_points
        
        # VMG変化の検出
        threshold = self.detection_params["performance_change_threshold"] * abs(vmg_data["vmg_ma"].mean())
        
        for i in range(window_size, len(vmg_data) - window_size):
            # 前後のVMG差
            pre_vmg = vmg_data.iloc[i-window_size:i]["vmg_ma"].mean()
            post_vmg = vmg_data.iloc[i:i+window_size]["vmg_ma"].mean()
            vmg_diff = post_vmg - pre_vmg
            
            # 変化率
            change_ratio = abs(vmg_diff / pre_vmg) if abs(pre_vmg) > 0.1 else 0
            
            # 閾値以上の変化を検出
            if change_ratio > threshold:
                point_type = "vmg_improvement" if vmg_diff > 0 else "vmg_deterioration"
                
                # VMG変化ポイントの作成
                vmg_point = {
                    "type": point_type,
                    "time": vmg_data.iloc[i]["timestamp"],
                    "position": {
                        "latitude": vmg_data.iloc[i]["latitude"],
                        "longitude": vmg_data.iloc[i]["longitude"]
                    },
                    "pre_vmg": pre_vmg,
                    "post_vmg": post_vmg,
                    "vmg_change": vmg_diff,
                    "change_ratio": change_ratio,
                    "description": f"VMG{'向上' if vmg_diff > 0 else '低下'}ポイント。変化: {vmg_diff:.2f}ノット({change_ratio*100:.1f}%)"
                }
                
                vmg_points.append(vmg_point)
        
        # 近接ポイントの除去
        filtered_points = []
        if vmg_points:
            filtered_points.append(vmg_points[0])
            
            for point in vmg_points[1:]:
                # 前のポイントとの時間差
                time_diff = (point["time"] - filtered_points[-1]["time"]).total_seconds()
                
                # 30秒以上離れている場合のみ追加
                if time_diff > 30:
                    filtered_points.append(point)
        
        return filtered_points
    
    def _detect_by_efficiency(self, track_data, efficiency_data):
        """効率変化による検出"""
        efficiency_points = []
        
        # 効率データが提供されていない場合
        if efficiency_data is None:
            return efficiency_points
        
        # 移動平均の計算（ノイズ除去）
        window_size = self.detection_params["window_size"]
        efficiency_ma = efficiency_data.rolling(window=window_size, center=True).mean()
        
        # NaNを除去
        valid_indices = ~efficiency_ma.isna()
        efficiency_ma = efficiency_ma[valid_indices]
        
        if len(efficiency_ma) < window_size * 2:
            return efficiency_points
        
        # インデックスを合わせる
        valid_track_data = track_data.loc[valid_indices]
        
        # 効率変化の検出
        threshold = self.detection_params["performance_change_threshold"]
        
        for i in range(window_size, len(efficiency_ma) - window_size):
            # 前後の効率差
            pre_efficiency = efficiency_ma.iloc[i-window_size:i].mean()
            post_efficiency = efficiency_ma.iloc[i:i+window_size].mean()
            efficiency_diff = post_efficiency - pre_efficiency
            
            # 変化率
            change_ratio = abs(efficiency_diff / pre_efficiency) if pre_efficiency > 0.1 else 0
            
            # 閾値以上の変化を検出
            if change_ratio > threshold:
                point_type = "efficiency_improvement" if efficiency_diff > 0 else "efficiency_deterioration"
                
                # 効率変化ポイントの作成
                efficiency_point = {
                    "type": point_type,
                    "time": valid_track_data.iloc[i]["timestamp"],
                    "position": {
                        "latitude": valid_track_data.iloc[i]["latitude"],
                        "longitude": valid_track_data.iloc[i]["longitude"]
                    },
                    "pre_efficiency": pre_efficiency,
                    "post_efficiency": post_efficiency,
                    "efficiency_change": efficiency_diff,
                    "change_ratio": change_ratio,
                    "description": f"効率{'向上' if efficiency_diff > 0 else '低下'}ポイント。変化: {efficiency_diff:.2f}({change_ratio*100:.1f}%)"
                }
                
                efficiency_points.append(efficiency_point)
        
        # 近接ポイントの除去
        filtered_points = []
        if efficiency_points:
            filtered_points.append(efficiency_points[0])
            
            for point in efficiency_points[1:]:
                # 前のポイントとの時間差
                time_diff = (point["time"] - filtered_points[-1]["time"]).total_seconds()
                
                # 30秒以上離れている場合のみ追加
                if time_diff > 30:
                    filtered_points.append(point)
        
        return filtered_points
    
    def _detect_angle_optimization(self, track_data, performance_metrics):
        """角度最適化ポイントの検出"""
        # 簡易実装のため、空のリストを返す
        # 実際の実装では、VMGや速度と艇の向きの関係から
        # 角度の最適化ポイントを検出する必要がある
        return []
    
    def _calculate_tack_efficiency(self, track_data, tack_index, window_size):
        """タック効率の計算"""
        # 速度損失ベースのタック効率計算
        if "speed" not in track_data.columns:
            return 0.8  # デフォルト値
        
        # タック前後の速度
        pre_tack_speed = track_data.iloc[tack_index-window_size:tack_index]["speed"].mean()
        post_tack_speed = track_data.iloc[tack_index:tack_index+window_size]["speed"].mean()
        
        # 速度維持率を効率として計算
        if pre_tack_speed > 0:
            efficiency = post_tack_speed / pre_tack_speed
            return min(1.0, max(0.0, efficiency))
        else:
            return 0.8  # デフォルト値
    
    def _calculate_gybe_efficiency(self, track_data, gybe_index, window_size):
        """ジャイブ効率の計算"""
        # 速度損失ベースのジャイブ効率計算
        if "speed" not in track_data.columns:
            return 0.85  # デフォルト値
        
        # ジャイブ前後の速度
        pre_gybe_speed = track_data.iloc[gybe_index-window_size:gybe_index]["speed"].mean()
        post_gybe_speed = track_data.iloc[gybe_index:gybe_index+window_size]["speed"].mean()
        
        # 速度維持率を効率として計算
        if pre_gybe_speed > 0:
            efficiency = post_gybe_speed / pre_gybe_speed
            return min(1.0, max(0.0, efficiency))
        else:
            return 0.85  # デフォルト値
    
    def _determine_wind_shift_response_type(self, shift_direction, initial_heading, final_heading):
        """風向変化対応タイプの判定"""
        # ヘディング変化の計算
        heading_change = (final_heading - initial_heading + 180) % 360 - 180
        
        # 対応タイプの判定
        if abs(heading_change) < 10:
            return "minimal_adjustment"
        elif abs(heading_change) > 80:
            return "tack_or_gybe"
        elif (shift_direction == "left" and heading_change > 0) or (shift_direction == "right" and heading_change < 0):
            return "favorable_adjustment"
        else:
            return "unfavorable_adjustment"
    
    def _evaluate_rounding_quality(self, approach_data, exit_data):
        """マーク回航品質の評価"""
        # 回航の滑らかさと効率をベースにした品質評価
        
        quality_score = 7.0  # デフォルト値
        factors = []
        
        # 速度維持の評価
        if "speed" in approach_data.columns and "speed" in exit_data.columns:
            approach_speed = approach_data["speed"].mean()
            exit_speed = exit_data["speed"].mean()
            
            if approach_speed > 0:
                speed_ratio = exit_speed / approach_speed
                speed_factor = min(1.2, max(0.5, speed_ratio))
                factors.append(speed_factor)
        
        # 方向変化の滑らかさ評価
        if "heading" in approach_data.columns and "heading" in exit_data.columns:
            # 方向変化の滑らかさを評価（標準偏差が小さいほど滑らか）
            combined_headings = list(approach_data["heading"]) + list(exit_data["heading"])
            
            # 角度データの特殊性を考慮
            # 方位角の標準偏差計算（サイン・コサイン法）
            headings_rad = np.radians(combined_headings)
            sin_mean = np.mean(np.sin(headings_rad))
            cos_mean = np.mean(np.cos(headings_rad))
            
            # 角度の分散を計算
            r = np.sqrt(sin_mean**2 + cos_mean**2)
            heading_std = np.sqrt(-2 * np.log(r))
            
            # 標準偏差が小さいほど高スコア
            smoothness_factor = max(0.5, min(1.5, 1.5 - heading_std / 30))
            factors.append(smoothness_factor)
        
        # 各要素を評価に反映
        for factor in factors:
            quality_score *= factor
        
        # スコアを0-10の範囲に正規化
        return min(10, max(0, quality_score))
    
    def _identify_rounding_issues(self, approach_data, exit_data):
        """マーク回航の問題点を特定"""
        issues = []
        
        # 速度問題の特定
        if "speed" in approach_data.columns and "speed" in exit_data.columns:
            approach_speed = approach_data["speed"].mean()
            exit_speed = exit_data["speed"].mean()
            min_speed = min(min(approach_data["speed"]), min(exit_data["speed"]))
            
            if approach_speed > 0 and exit_speed / approach_speed < 0.8:
                issues.append("回航での大きな速度損失")
            
            if min_speed < approach_speed * 0.6:
                issues.append("回航中の極端な減速")
        
        # 角度問題の特定
        if "heading" in approach_data.columns and "heading" in exit_data.columns:
            # ヘディング変化の急峻さをチェック
            combined_headings = list(approach_data["heading"]) + list(exit_data["heading"])
            
            if len(combined_headings) > 3:
                heading_changes = []
                for i in range(1, len(combined_headings)):
                    change = abs((combined_headings[i] - combined_headings[i-1] + 180) % 360 - 180)
                    heading_changes.append(change)
                
                max_change = max(heading_changes)
                if max_change > 30:
                    issues.append("急激な方向変化")
        
        # 特定の問題がなければ一般的なコメント
        if not issues:
            issues.append("効率改善の余地あり")
        
        return issues
    
    def _detect_missed_wind_shifts(self, track_data, wind_data):
        """風向変化への対応遅れの検出"""
        missed_points = []
        
        # 必要なカラムの確認
        if "wind_direction" not in wind_data.columns or "timestamp" not in wind_data.columns or "heading" not in track_data.columns:
            return missed_points
        
        window_size = 5  # 5ポイントの移動ウィンドウ
        response_window = 120  # 120秒以内の対応を期待
        
        # 風向の変化を検出
        for i in range(window_size, len(wind_data) - window_size):
            # 前後のウィンドウでの平均風向
            pre_wind_dir = wind_data.iloc[i-window_size:i]["wind_direction"].mean()
            post_wind_dir = wind_data.iloc[i:i+window_size]["wind_direction"].mean()
            
            # 風向差の計算（角度の特殊性を考慮）
            wind_shift = abs((post_wind_dir - pre_wind_dir + 180) % 360 - 180)
            
            # 一定以上の風向変化を検出
            if wind_shift > 10:  # 10度以上の変化
                wind_shift_time = wind_data.iloc[i]["timestamp"]
                
                # 風向変化後のボートの対応をチェック
                response_data = track_data[
                    (track_data["timestamp"] >= wind_shift_time) & 
                    (track_data["timestamp"] <= wind_shift_time + timedelta(seconds=response_window))
                ]
                
                if not response_data.empty:
                    # ヘディングの変化をチェック
                    initial_heading = response_data.iloc[0]["heading"]
                    final_heading = response_data.iloc[-1]["heading"]
                    heading_change = abs((final_heading - initial_heading + 180) % 360 - 180)
                    
                    # 風向変化に対してヘディング変化が少ない場合は対応遅れと判断
                    if heading_change < wind_shift * 0.3:  # 風向変化の30%未満の対応は遅れと判断
                        shift_direction = "left" if ((post_wind_dir - pre_wind_dir + 180) % 360 - 180) < 0 else "right"
                        
                        # 対応遅れポイントの作成
                        missed_point = {
                            "type": "missed_wind_shift",
                            "time": wind_shift_time + timedelta(seconds=response_window/2),  # 応答ウィンドウの中間点
                            "position": {
                                "latitude": response_data.iloc[len(response_data)//2]["latitude"],
                                "longitude": response_data.iloc[len(response_data)//2]["longitude"]
                            },
                            "wind_shift_magnitude": wind_shift,
                            "wind_shift_direction": shift_direction,
                            "heading_change": heading_change,
                            "expected_change": wind_shift * 0.5,  # 期待されるヘディング変化
                            "description": f"風向変化({wind_shift:.1f}度, {shift_direction})への対応遅れ。実際の対応: {heading_change:.1f}度"
                        }
                        
                        missed_points.append(missed_point)
        
        return missed_points
    
    def _detect_layline_issues(self, track_data, wind_data):
        """レイラインアプローチの問題検出"""
        # 簡易実装のため、空のリストを返す
        # 実際の実装では、コース情報と風向データを利用して
        # レイラインアプローチの問題（早すぎる、遅すぎる、非効率など）を
        # 検出する必要がある
        return []
    
    def _detect_competitor_advantage_points(self, track_data, competitor_data):
        """競合艇優位性ポイントの検出"""
        advantage_points = []
        
        # 必要なカラムの確認
        if "speed" not in track_data.columns or "timestamp" not in track_data.columns or \
           "speed" not in competitor_data.columns or "timestamp" not in competitor_data.columns:
            return advantage_points
        
        # 30秒ごとにチェック
        sample_interval = 30
        for i in range(0, len(track_data), sample_interval):
            if i >= len(track_data):
                break
            
            current_time = track_data.iloc[i]["timestamp"]
            
            # 自艇データの取得
            own_speed = track_data.iloc[i]["speed"]
            
            # 競合艇の近い時間のデータを検索
            competitor_at_time = competitor_data[
                (competitor_data["timestamp"] >= current_time - timedelta(seconds=15)) & 
                (competitor_data["timestamp"] <= current_time + timedelta(seconds=15))
            ]
            
            if not competitor_at_time.empty:
                # 競合艇の平均速度
                competitor_speed = competitor_at_time["speed"].mean()
                
                # 競合艇が明らかに速い場合、優位性ポイントとして検出
                if competitor_speed > own_speed * 1.15:  # 15%以上速い
                    advantage_point = {
                        "type": "competitor_advantage",
                        "time": current_time,
                        "position": {
                            "latitude": track_data.iloc[i]["latitude"],
                            "longitude": track_data.iloc[i]["longitude"]
                        },
                        "own_speed": own_speed,
                        "competitor_speed": competitor_speed,
                        "speed_advantage": competitor_speed - own_speed,
                        "advantage_ratio": competitor_speed / own_speed,
                        "description": f"競合艇優位ポイント。速度差: {competitor_speed - own_speed:.2f}ノット({competitor_speed/own_speed*100-100:.1f}%速い)"
                    }
                    
                    advantage_points.append(advantage_point)
        
        # 近接ポイントの除去
        filtered_points = []
        if advantage_points:
            filtered_points.append(advantage_points[0])
            
            for point in advantage_points[1:]:
                # 前のポイントとの時間差
                time_diff = (point["time"] - filtered_points[-1]["time"]).total_seconds()
                
                # 60秒以上離れている場合のみ追加
                if time_diff > 60:
                    filtered_points.append(point)
        
        return filtered_points
    
    def _detect_inefficient_sailing(self, track_data):
        """非効率な操船の検出"""
        # 簡易実装のため、空のリストを返す
        # 実際の実装では、VMGや速度、角度などから
        # 非効率な操船を検出する必要がある
        return []
    
    def _get_base_impact_score(self, point_type):
        """ポイントタイプに基づく基本影響度スコアの取得"""
        impact_scores = {
            "tack": 6.0,
            "gybe": 6.0,
            "layline": 7.0,
            "wind_shift_response": 7.5,
            "missed_wind_shift": 8.0,
            "mark_rounding": 7.0,
            "cross_point": 5.5,
            "speed_improvement": 6.0,
            "speed_deterioration": 6.0,
            "vmg_improvement": 6.5,
            "vmg_deterioration": 6.5,
            "efficiency_improvement": 6.0,
            "efficiency_deterioration": 6.0,
            "competitor_advantage": 7.0
        }
        
        return impact_scores.get(point_type, 5.0)
    
    def _calculate_relative_bearing(self, own_position, competitor_position):
        """相対方位の計算"""
        if "heading" not in own_position:
            return None
        
        # 自艇から競合艇への方位を計算
        bearing = self._calculate_bearing(
            own_position["latitude"], own_position["longitude"],
            competitor_position["latitude"], competitor_position["longitude"]
        )
        
        # 自艇のヘディングとの相対方位
        relative_bearing = (bearing - own_position["heading"] + 180) % 360 - 180
        
        return relative_bearing
    
    def _generate_tack_scenarios(self, point, track_data, wind_data):
        """タックのシナリオ生成"""
        scenarios = []
        
        # 1. タイミングの異なるシナリオ
        scenarios.append({
            "scenario": "10秒早くタック",
            "outcome": "風向が変わる前にタックすることで、より有利なレイラインに乗れる可能性があります。",
            "impact": 0.8
        })
        
        scenarios.append({
            "scenario": "10秒遅くタック",
            "outcome": "風向の変化を待ってからタックすることで、よりリフトに乗れる可能性があります。",
            "impact": 0.7
        })
        
        # 2. 実行効率の異なるシナリオ
        if "efficiency" in point:
            efficiency = point["efficiency"]
            if efficiency < 0.8:
                scenarios.append({
                    "scenario": "より効率的なタック実行",
                    "outcome": f"タック効率の改善により速度損失を減らし、VMGを向上できます。現在の効率: {efficiency:.2f}",
                    "impact": 0.9
                })
        
        # 3. 位置の異なるシナリオ
        scenarios.append({
            "scenario": "異なる位置でタック",
            "outcome": "風向や水流の違う位置でタックすることで、より有利なコンディションを得られる可能性があります。",
            "impact": 0.6
        })
        
        return scenarios
    
    def _generate_gybe_scenarios(self, point, track_data, wind_data):
        """ジャイブのシナリオ生成"""
        scenarios = []
        
        # 1. タイミングの異なるシナリオ
        scenarios.append({
            "scenario": "10秒早くジャイブ",
            "outcome": "風下マークへのアプローチが変わり、より良いラインを取れる可能性があります。",
            "impact": 0.7
        })
        
        scenarios.append({
            "scenario": "10秒遅くジャイブ",
            "outcome": "風向の変化を待ってからジャイブすることで、より効率的なラインを取れる可能性があります。",
            "impact": 0.7
        })
        
        # 2. 実行効率の異なるシナリオ
        if "efficiency" in point:
            efficiency = point["efficiency"]
            if efficiency < 0.85:
                scenarios.append({
                    "scenario": "より効率的なジャイブ実行",
                    "outcome": f"ジャイブ効率の改善により速度損失を減らし、パフォーマンスを向上できます。現在の効率: {efficiency:.2f}",
                    "impact": 0.8
                })
        
        # 3. 風のパフを利用するシナリオ
        scenarios.append({
            "scenario": "パフを待ってからジャイブ",
            "outcome": "風のパフが来たタイミングでジャイブすることで、加速と方向転換を同時に行えます。",
            "impact": 0.6
        })
        
        return scenarios
    
    def _generate_layline_scenarios(self, point, track_data, wind_data, course_data):
        """レイラインのシナリオ生成"""
        scenarios = []
        
        # ポイントに問題の記載があれば利用
        issue = point.get("description", "")
        
        # 早すぎるレイラインアプローチの場合
        if "早すぎる" in issue:
            # 早すぎる場合のシナリオ
            scenarios.append({
                "scenario": "より遅くレイラインに乗る",
                "outcome": "距離は増加するが、より正確なレイラインアプローチが可能になります。",
                "impact": 0.7
            })
            
            scenarios.append({
                "scenario": "現在のアプローチを維持",
                "outcome": "時間的余裕はあるが、風向変化があると遠回りになるリスクがあります。",
                "impact": 0.5
            })
            
        elif "遅すぎる" in issue:
            # 遅すぎる場合のシナリオ
            scenarios.append({
                "scenario": "より早くレイラインに乗る",
                "outcome": "マークへの到達が確実になり、混雑リスクを減らせる可能性があります。",
                "impact": 0.8
            })
            
            scenarios.append({
                "scenario": "現在のアプローチを維持",
                "outcome": "距離は短くなるが、マークに到達できないリスクがあります。",
                "impact": 0.7
            })
            
            scenarios.append({
                "scenario": "少し広めに回り込む",
                "outcome": "マーク回航をスムーズにできるが、距離は増加します。",
                "impact": 0.6
            })
            
        else:
            # 非効率なアプローチの場合のシナリオ
            scenarios.append({
                "scenario": "より直線的なアプローチを取る",
                "outcome": "距離を短縮できるが、風向や他艇の影響を受けやすくなります。",
                "impact": 0.7
            })
            
            scenarios.append({
                "scenario": "現在のアプローチを少し修正",
                "outcome": "過剰な遠回りを避けつつ、安全なアプローチを維持できます。",
                "impact": 0.6
            })
            
            scenarios.append({
                "scenario": "他艇との関係を考慮したアプローチに変更",
                "outcome": "戦術的な位置取りが改善する可能性がありますが、距離は増加します。",
                "impact": 0.5
            })
        
        return scenarios
    
    def _generate_wind_shift_scenarios(self, point, track_data, wind_data):
        """風向変化対応のシナリオ生成"""
        scenarios = []
        
        shift_direction = point.get("wind_shift_direction", "")
        response_type = point.get("response_type", "")
        
        if response_type == "minimal_adjustment":
            # 最小調整の場合のシナリオ
            scenarios.append({
                "scenario": "積極的なタック/ジャイブで対応",
                "outcome": "風向変化を最大限活用できるが、マニューバーのコストが発生します。",
                "impact": 0.8
            })
            
            scenarios.append({
                "scenario": "より大きな方向調整",
                "outcome": "風向変化の一部を活用しつつ、マニューバーなしで対応します。",
                "impact": 0.7
            })
            
        elif response_type == "tack_or_gybe":
            # タック/ジャイブ対応の場合のシナリオ
            scenarios.append({
                "scenario": "タック/ジャイブを遅らせる",
                "outcome": "風向変化が安定してから方向転換することで、より確実な判断が可能になります。",
                "impact": 0.7
            })
            
            scenarios.append({
                "scenario": "方向転換せずに調整",
                "outcome": "マニューバーせずに進路調整のみで対応し、速度を維持します。",
                "impact": 0.6
            })
            
        else:
            # その他の対応の場合のシナリオ
            scenarios.append({
                "scenario": "より積極的な風向変化対応",
                "outcome": "風向変化をより早く検出し、適切な対応をとることで有利を得られます。",
                "impact": 0.8
            })
            
            scenarios.append({
                "scenario": "異なる風向予測に基づく対応",
                "outcome": "風の傾向をより長期的に分析し、戦略的な対応を取ります。",
                "impact": 0.7
            })
        
        return scenarios
    
    def _generate_mark_rounding_scenarios(self, point, track_data):
        """マーク回航のシナリオ生成"""
        scenarios = []
        
        # マーク回航の品質に応じたシナリオ
        rounding_quality = point.get("rounding_quality", 7.0)
        issues = point.get("issues", [])
        
        if rounding_quality < 6.0:
            # 品質が低い場合のシナリオ
            scenarios.append({
                "scenario": "より広く滑らかなターン",
                "outcome": "速度をより維持し、安定した回航が可能になりますが、距離が増加します。",
                "impact": 0.8
            })
            
            if any("速度" in issue for issue in issues):
                scenarios.append({
                    "scenario": "速度重視の回航",
                    "outcome": "回航前の減速を最小化し、回航後の加速を早めることで総合的な時間を短縮します。",
                    "impact": 0.9
                })
            
            if any("方向変化" in issue for issue in issues):
                scenarios.append({
                    "scenario": "より滑らかな舵角",
                    "outcome": "急激な舵角を避け、滑らかな回航軌跡を取ることで速度損失を減らします。",
                    "impact": 0.8
                })
        else:
            # 品質が良い場合のシナリオ
            scenarios.append({
                "scenario": "より攻撃的な回航",
                "outcome": "マークにより近づくことで距離を短縮できますが、速度損失のリスクが増加します。",
                "impact": 0.7
            })
            
            scenarios.append({
                "scenario": "戦術的なポジショニング重視",
                "outcome": "回航後の位置取りを優先し、後続の競合艇に対して有利な位置を確保します。",
                "impact": 0.7
            })
        
        # マークタイプに応じたシナリオ
        mark_type = point.get("mark_type", "unknown")
        
        if mark_type == "windward":
            scenarios.append({
                "scenario": "風上マークでの内側回航",
                "outcome": "内側からの回航で距離を短縮できますが、他艇との接触リスクが増加します。",
                "impact": 0.7
            })
        elif mark_type == "leeward":
            scenarios.append({
                "scenario": "風下マークでの広めの回航",
                "outcome": "風下での加速を優先し、回航後のスピードアドバンテージを確保します。",
                "impact": 0.7
            })
        
        return scenarios
    
    def _generate_cross_point_scenarios(self, point, track_data):
        """クロスポイントのシナリオ生成"""
        scenarios = []
        
        # 距離に応じたシナリオ
        distance = point.get("distance", 50)
        
        if distance < 30:
            # 近接クロスの場合のシナリオ
            scenarios.append({
                "scenario": "先行権の確保",
                "outcome": "より積極的に位置取りを行い、先行権を確保することで優位に立ちます。",
                "impact": 0.8
            })
            
            scenarios.append({
                "scenario": "回避行動の早期開始",
                "outcome": "十分な余裕を持って回避行動を取り、安全を確保しつつ最小限の距離ロスに抑えます。",
                "impact": 0.7
            })
        else:
            # 余裕のあるクロスの場合のシナリオ
            scenarios.append({
                "scenario": "戦術的位置取りの改善",
                "outcome": "クロス後の位置関係を意識し、風上/有利サイドを確保します。",
                "impact": 0.7
            })
            
            scenarios.append({
                "scenario": "競合艇のカバーに入る",
                "outcome": "競合艇の風を塞ぐ位置に移動し、相対的な優位性を高めます。",
                "impact": 0.8
            })
        
        # 相対方位に応じたシナリオ
        relative_bearing = point.get("relative_bearing")
        
        if relative_bearing is not None:
            if abs(relative_bearing) < 30:
                # ほぼ同一方向の場合
                scenarios.append({
                    "scenario": "並走優位の確保",
                    "outcome": "わずかな速度アドバンテージを活かして徐々に前に出ることで、風上位置を確保します。",
                    "impact": 0.7
                })
            elif abs(relative_bearing) > 150:
                # ほぼ反対方向の場合
                scenarios.append({
                    "scenario": "逆方向での有利コース選択",
                    "outcome": "異なるコースを選択することで、風の強い/シフトのある有利なエリアを狙います。",
                    "impact": 0.6
                })
        
        return scenarios
    
    def _generate_missed_opportunity_scenarios(self, point, track_data, wind_data):
        """機会損失のシナリオ生成"""
        scenarios = []
        
        point_type = point.get("type", "")
        
        if "wind_shift" in point_type:
            # 風向変化の見逃しの場合のシナリオ
            scenarios.append({
                "scenario": "風向変化への迅速な対応",
                "outcome": "風向変化を早期に検出し、すぐに適切な対応を取ることで有利を得られます。",
                "impact": 0.9
            })
            
            scenarios.append({
                "scenario": "風上側へのポジショニング",
                "outcome": "風向変化が予想される場合に風上側にポジショニングすることで、シフトの恩恵を最大化します。",
                "impact": 0.8
            })
            
        elif "competitor_advantage" in point_type:
            # 競合艇優位の場合のシナリオ
            scenarios.append({
                "scenario": "艇速の最適化",
                "outcome": "セールトリムと艇の姿勢を最適化し、競合艇と同等以上の速度を維持します。",
                "impact": 0.8
            })
            
            scenarios.append({
                "scenario": "異なるコースの選択",
                "outcome": "競合艇と異なるコースを選択し、有利な風や潮流条件を見つけることで差を埋めます。",
                "impact": 0.7
            })
            
        else:
            # その他の機会損失の場合のシナリオ
            scenarios.append({
                "scenario": "状況認識の向上",
                "outcome": "風、競合艇、コースコンディションをより注意深く観察し、早期に好機を捉えます。",
                "impact": 0.8
            })
            
            scenarios.append({
                "scenario": "積極的な戦略の採用",
                "outcome": "リスクを適切に評価した上で、より積極的な戦略判断を行い、好機を逃さないようにします。",
                "impact": 0.7
            })
        
        return scenarios
    
    def _generate_generic_scenarios(self, point, track_data, wind_data):
        """一般的なシナリオ生成"""
        scenarios = []
        point_type = point.get("type", "unknown")
        
        # 標準的なシナリオ
        scenarios.append({
            "scenario": "現在の判断とは異なる選択をする",
            "outcome": "異なる結果が得られる可能性がありますが、状況によって有利・不利は変わります。",
            "impact": 0.6
        })
        
        # ポイントタイプに応じた追加シナリオ
        if "speed_change" in point_type:
            scenarios.append({
                "scenario": "速度変化の原因に早めに対応",
                "outcome": "パフォーマンス変化を最小限に抑えられる可能性があります。",
                "impact": 0.7
            })
            
        elif "vmg" in point_type:
            scenarios.append({
                "scenario": "VMG最適化に重点を置いた判断",
                "outcome": "短期的なVMG向上が期待できますが、長期的な戦略との兼ね合いが重要です。",
                "impact": 0.7
            })
            
        elif "cross_point" in point_type:
            scenarios.append({
                "scenario": "他艇との関係性を重視した判断",
                "outcome": "戦術的な位置取りが改善しますが、VMGが最適でなくなる可能性があります。",
                "impact": 0.7
            })
        
        # 一般的な追加シナリオ
        scenarios.append({
            "scenario": "より慎重な判断",
            "outcome": "リスクは減少しますが、機会損失の可能性があります。",
            "impact": 0.5
        })
        
        return scenarios
    
    def _generate_analysis_summary(self, high_impact_points, strategic_points, performance_points, cross_points, missed_points):
        """分析サマリーの生成"""
        # ポイント数の集計
        point_counts = {
            "total": len(high_impact_points),
            "strategic": len(strategic_points),
            "performance": len(performance_points),
            "cross": len(cross_points),
            "missed": len(missed_points)
        }
        
        # 高影響ポイントのタイプ集計
        high_impact_types = {}
        for point in high_impact_points:
            point_type = point.get("type", "unknown")
            high_impact_types[point_type] = high_impact_types.get(point_type, 0) + 1
        
        # 最も多いタイプを特定
        most_common_type = max(high_impact_types.items(), key=lambda x: x[1])[0] if high_impact_types else "unknown"
        
        # 最も影響度が高いポイントを特定
        top_point = high_impact_points[0] if high_impact_points else None
        top_point_desc = ""
        if top_point:
            top_point_desc = f"最も影響度が高かったポイントは{top_point.get('time').strftime('%H:%M:%S')}の{top_point.get('type')}で、{top_point.get('description')}です。"
        
        # 分析概要の生成
        summary = [
            f"レース中に{point_counts['total']}個の重要ポイントを特定しました。",
            f"内訳は戦略的判断が{point_counts['strategic']}個、パフォーマンス変化が{point_counts['performance']}個、"
            f"クロスポイントが{point_counts['cross']}個、機会損失が{point_counts['missed']}個です。",
            top_point_desc
        ]
        
        # 特筆すべき傾向
        if point_counts['missed'] > point_counts['total'] * 0.3:
            summary.append("機会損失ポイントが多く、風向変化や状況変化への対応に改善の余地があります。")
        
        if most_common_type == "tack" or most_common_type == "gybe":
            summary.append("マニューバーの判断が多く、その効率と適切なタイミングが重要でした。")
        
        elif most_common_type in ["vmg_improvement", "vmg_deterioration"]:
            summary.append("VMGの変動が顕著で、風向変化と艇速のバランスが特に重要でした。")
        
        elif most_common_type == "mark_rounding" or most_common_type == "mark_approach":
            summary.append("マーク回航の影響が大きく、効率的なアプローチと回航が成績を左右しました。")
        
        # 総合評価
        summary.append("これらのポイントを分析し、次回のレースではより効果的な判断が可能になります。")
        
        return " ".join(summary)
    
    def _calculate_bearing(self, lat1, lon1, lat2, lon2):
        """2点間の方位角を計算（度、北=0）"""
        # ラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 方位角の計算
        y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) -
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad))
        bearing = math.atan2(y, x)
        
        # 度に変換し、0-360度に正規化
        bearing_deg = (math.degrees(bearing) + 360) % 360
        
        return bearing_deg
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """2点間の距離を計算（メートル）"""
        # 地球の半径（メートル）
        R = 6371000
        
        # ラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 緯度経度の差分
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # ハーバーサイン公式
        a = (math.sin(dlat/2)**2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        # 距離の計算
        distance = R * c
        
        return distance
