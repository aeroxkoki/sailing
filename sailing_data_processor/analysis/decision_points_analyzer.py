# -*- coding: utf-8 -*-
"""
重要ポイント特定エンジン

セーリングデータから戦略的に重要なポイントを特定し、
分析するモジュールです。
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
import logging

# モジュールのインポート
from sailing_data_processor.analysis.performance_analyzer import (
    extract_performance_metrics, detect_performance_changes,
    calculate_impact_scores, remove_duplicate_points, generate_analysis_summary
)
from sailing_data_processor.analysis.strategic_points_detector import (
    detect_strategic_decisions, analyze_cross_points, 
    analyze_mark_roundings, detect_missed_opportunities,
    generate_what_if_scenarios
)

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
            strategic_points = detect_strategic_decisions(track_data, wind_data, self.sensitivity)
            
            # 性能変化ポイントの検出
            performance_metrics = extract_performance_metrics(
                track_data, wind_data, self.detection_params["window_size"]
            )
            performance_points = detect_performance_changes(
                track_data, 
                performance_metrics, 
                self.detection_params["vmg_change_threshold"],
                self.detection_params["speed_change_threshold"]
            )
            
            # 全ポイントの重複除去
            all_points = strategic_points + performance_points
            # 重複ポイントの除去
            unique_points = remove_duplicate_points(all_points)
            
            # 各ポイントのインパクトスコア計算
            scored_points = calculate_impact_scores(unique_points, track_data, wind_data)
            
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
                cross_points = analyze_cross_points(track_data, competitor_data)
            
            # 機会損失分析
            missed_points = detect_missed_opportunities(
                track_data, 
                wind_data, 
                self.detection_params["wind_shift_threshold"],
                competitor_data
            )
            
            # 分析サマリー作成
            summary = generate_analysis_summary(
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
        # 互換性のために残している。実際の実装は extract_performance_metrics を使用
        return extract_performance_metrics(track_data, wind_data, self.detection_params["window_size"])
    
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
        # 互換性のために残している。実際の実装は remove_duplicate_points を使用
        return remove_duplicate_points(points)
    
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
        # 互換性のために残している。実際の実装は generate_analysis_summary を使用
        return generate_analysis_summary(
            high_impact_points, strategic_points, performance_points,
            cross_points, missed_points
        )
    
    # 以下のメソッドは別モジュールに移動したが、後方互換性のために呼び出しを提供
    
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
        return detect_strategic_decisions(track_data, wind_data, self.sensitivity)
    
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
        return detect_performance_changes(
            track_data, 
            performance_metrics, 
            self.detection_params["vmg_change_threshold"],
            self.detection_params["speed_change_threshold"]
        )
    
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
        return calculate_impact_scores(points, track_data, wind_data)
    
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
        return generate_what_if_scenarios(point, track_data, wind_data)
    
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
        return analyze_cross_points(track_data, competitor_data)
    
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
        return analyze_mark_roundings(track_data, marks)
    
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
        return detect_missed_opportunities(
            track_data, 
            wind_data, 
            self.detection_params["wind_shift_threshold"],
            competitor_data
        )
