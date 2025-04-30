# -*- coding: utf-8 -*-
"""
Module for data quality metrics improvements.
This module provides functions for quality metrics calculation and visualization.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Core functionality imports
from sailing_data_processor.validation.quality_metrics_improvements_core import QualityMetricsCalculatorExtension
from sailing_data_processor.validation.quality_metrics_visualization import QualityMetricsVisualization
from sailing_data_processor.validation.quality_metrics_temporal import QualityMetricsTemporal

# Create a combined class for backward compatibility
class QualityMetricsCalculator(QualityMetricsCalculatorExtension):
    """
    データ品質メトリクスの計算クラス
    
    データ検証結果に基づいてデータ品質を評価し、様々なメトリクスを計算します。
    また、品質スコアの視覚化機能も提供します。
    """
    
    def __init__(self, validation_results=None, data=None):
        """
        初期化
        
        Parameters
        ----------
        validation_results : List[Dict[str, Any]], optional
            DataValidatorから得られた検証結果
        data : pd.DataFrame, optional
            検証されたデータフレーム
        """
        # 親クラスの初期化
        super().__init__(validation_results, data)
        
        # 視覚化クラスの初期化
        self.visualizer = QualityMetricsVisualization(self)
        self.temporal_analyzer = QualityMetricsTemporal(self)
        
    def generate_quality_score_visualization(self) -> Tuple:
        """
        品質スコアのゲージチャートとカテゴリ別バーチャートを生成
        
        Returns
        -------
        Tuple
            ゲージチャートとバーチャート
        """
        return self.visualizer.generate_quality_score_visualization()
    
    def generate_spatial_quality_map(self):
        """
        空間的な品質分布のマップを生成
        
        Returns
        -------
        Object
            品質マップの図
        """
        return self.visualizer.generate_spatial_quality_map()
        
    def generate_temporal_quality_chart(self):
        """
        時間帯別の品質分布チャートを生成
        
        Returns
        -------
        Object
            時間帯別品質チャート
        """
        return self.temporal_analyzer.generate_temporal_quality_chart()

    def calculate_temporal_quality_scores(self) -> List[Dict[str, Any]]:
        """
        時間帯別の品質スコアを計算。
        
        データを時間帯ごとに分析し、それぞれの時間帯の品質スコアと問題情報を計算します。
        これにより、時間的な品質変動を特定できます。
        
        Returns
        -------
        List[Dict[str, Any]]
            各時間帯の品質情報
        """
        # タイムスタンプカラムがない場合
        if "timestamp" not in self.data.columns:
            return []
        
        try:
            # 有効なタイムスタンプのみを抽出
            valid_data = self.data.dropna(subset=["timestamp"])
            
            if len(valid_data) < 2:
                return []
            
            # 問題のあるすべてのレコードのインデックス
            all_problem_indices = self.problematic_indices["all"]
            
            # 時間範囲を決定
            min_time = valid_data["timestamp"].min()
            max_time = valid_data["timestamp"].max()
            time_range = max_time - min_time
            
            # 時間を12個の区間に分割
            hours_bins = 12
            time_step = time_range / hours_bins
            
            # 時間帯ごとのスコアを計算
            temporal_scores = []
            
            for i in range(hours_bins):
                bin_start = min_time + time_step * i
                bin_end = min_time + time_step * (i + 1)
                
                # 時間帯内のレコードを抽出
                bin_mask = (valid_data["timestamp"] >= bin_start) & (valid_data["timestamp"] < bin_end)
                bin_indices = valid_data.index[bin_mask].tolist()
                
                if bin_indices:
                    # 時間帯内の問題レコード数
                    problem_indices_in_bin = set(bin_indices).intersection(set(all_problem_indices))
                    problem_count = len(problem_indices_in_bin)
                    total_count = len(bin_indices)
                    
                    # 問題の割合に基づく品質スコア
                    problem_percentage = problem_count / total_count * 100 if total_count > 0 else 0
                    quality_score = max(0, 100 - problem_percentage)
                    
                    # 人間が読みやすい時間帯ラベルを作成
                    label = f"{bin_start.strftime('%H:%M')}-{bin_end.strftime('%H:%M')}"
                    
                    # 問題タイプごとの分布も計算
                    problem_type_distribution = self._calculate_problem_type_distribution_for_period(bin_indices)
                    
                    # 品質スコアを保存
                    temporal_scores.append({
                        "period": f"期間{i+1}",
                        "start_time": bin_start.isoformat(),
                        "end_time": bin_end.isoformat(),
                        "label": label,
                        "quality_score": quality_score,
                        "problem_count": problem_count,
                        "total_count": total_count,
                        "problem_percentage": problem_percentage,
                        "impact_level": self._determine_impact_level(quality_score),
                        "problem_types": problem_type_distribution
                    })
            
            return temporal_scores
            
        except Exception as e:
            # エラーが発生した場合は空のリストを返す
            print(f"時間帯別の品質スコア計算中にエラー: {e}")
            return []
            
    def calculate_spatial_quality_scores(self) -> List[Dict[str, Any]]:
        """
        空間グリッド別の品質スコアを計算。
        
        データを空間的なグリッドに分割し、各グリッドの品質スコアと問題情報を計算します。
        これにより、空間的な品質変動を視覚的に把握できます。
        
        Returns
        -------
        List[Dict[str, Any]]
            各グリッドの品質情報
        """
        # 位置情報カラムがない場合
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            return []
            
        try:
            # 有効な位置情報を持つレコードのみを抽出
            valid_data = self.data.dropna(subset=["latitude", "longitude"])
            
            if len(valid_data) < 5:  # 最低5ポイント必要
                return []
                
            # 問題のあるすべてのレコードのインデックス
            all_problem_indices = self.problematic_indices["all"]
            
            # 位置の範囲を取得
            min_lat = valid_data["latitude"].min()
            max_lat = valid_data["latitude"].max()
            min_lon = valid_data["longitude"].min()
            max_lon = valid_data["longitude"].max()
            
            # 適切なグリッドサイズを決定（5x5グリッド）
            lat_bins = 5
            lon_bins = 5
            
            # 範囲が狭すぎる場合は調整
            if max_lat - min_lat < 0.001:
                center_lat = (max_lat + min_lat) / 2
                min_lat = center_lat - 0.005
                max_lat = center_lat + 0.005
                
            if max_lon - min_lon < 0.001:
                center_lon = (max_lon + min_lon) / 2
                min_lon = center_lon - 0.005
                max_lon = center_lon + 0.005
                
            lat_step = (max_lat - min_lat) / lat_bins
            lon_step = (max_lon - min_lon) / lon_bins
            
            # グリッドごとの品質スコアを計算
            spatial_scores = []
            
            for i in range(lat_bins):
                lat_start = min_lat + lat_step * i
                lat_end = min_lat + lat_step * (i + 1)
                
                for j in range(lon_bins):
                    lon_start = min_lon + lon_step * j
                    lon_end = min_lon + lon_step * (j + 1)
                    
                    # グリッド内のレコードを抽出
                    grid_mask = ((valid_data["latitude"] >= lat_start) & 
                                (valid_data["latitude"] < lat_end) & 
                                (valid_data["longitude"] >= lon_start) & 
                                (valid_data["longitude"] < lon_end))
                    grid_indices = valid_data.index[grid_mask].tolist()
                    
                    if grid_indices:  # グリッド内にデータがある場合
                        # グリッド内の問題レコード数
                        problem_indices_in_grid = set(grid_indices).intersection(set(all_problem_indices))
                        problem_count = len(problem_indices_in_grid)
                        total_count = len(grid_indices)
                        
                        # 問題の割合に基づく品質スコア
                        problem_percentage = problem_count / total_count * 100 if total_count > 0 else 0
                        quality_score = max(0, 100 - problem_percentage)
                        
                        # グリッドの中心座標
                        center_lat = (lat_start + lat_end) / 2
                        center_lon = (lon_start + lon_end) / 2
                        
                        # グリッドIDを生成
                        grid_id = f"grid_{i}_{j}"
                        
                        # 問題タイプごとの分布も計算
                        problem_type_distribution = self._calculate_problem_type_distribution_for_period(grid_indices)
                        
                        # 品質スコアを保存
                        spatial_scores.append({
                            "grid_id": grid_id,
                            "lat_range": (lat_start, lat_end),
                            "lon_range": (lon_start, lon_end),
                            "center": (center_lat, center_lon),
                            "quality_score": quality_score,
                            "problem_count": problem_count,
                            "total_count": total_count,
                            "problem_percentage": problem_percentage,
                            "impact_level": self._determine_impact_level(quality_score),
                            "problem_types": problem_type_distribution
                        })
            
            return spatial_scores
            
        except Exception as e:
            # エラーが発生した場合は空のリストを返す
            print(f"空間的な品質スコア計算中にエラー: {e}")
            return []
