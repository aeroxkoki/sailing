# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization_modules.visualizer_part2 import ValidationVisualizerPart2


class ValidationVisualizer:
    """
    データ検証結果の視覚化クラス
    
    Parameters
    ----------
    quality_metrics : QualityMetricsCalculator
        データ品質メトリクス計算クラス
    data : pd.DataFrame
        検証されたデータフレーム
    """
    
    def __init__(self, quality_metrics: QualityMetricsCalculator, data: pd.DataFrame):
        """
        初期化
        
        Parameters
        ----------
        quality_metrics : QualityMetricsCalculator
            データ品質メトリクス計算クラス
        data : pd.DataFrame
            検証されたデータフレーム
        """
        self.quality_metrics = quality_metrics
        self.data = data
        self.part2 = ValidationVisualizerPart2(quality_metrics, data)
        
    def generate_quality_score_visualization(self) -> Tuple[go.Figure, go.Figure]:
        """
        品質スコアのゲージチャートとカテゴリ別バーチャートを生成。
        
        品質スコアの視覚的表現として、総合スコアを円形ゲージで、
        カテゴリ別スコア（完全性、正確性、一貫性）を棒グラフで表示します。
        
        Returns
        -------
        Tuple[go.Figure, go.Figure]
            ゲージチャートとバーチャート
        """
        # 品質スコアを取得
        quality_scores = self.quality_metrics.calculate_quality_scores()
        
        # ゲージチャートを生成（総合スコア用）
        gauge_chart = go.Figure(go.Indicator(
            mode="gauge+number",
            value=quality_scores["total"],
            title={"text": "データ品質スコア", "font": {"size": 24}},
            number={"font": {"size": 32, "color": self._get_score_color(quality_scores["total"])}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": self._get_score_color(quality_scores["total"])},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
                    {"range": [0, 50], "color": "#FFCCCC"},  # 赤系 - 低品質
                    {"range": [50, 75], "color": "#FFEEAA"},  # 黄系 - 中品質
                    {"range": [75, 90], "color": "#CCFFCC"},  # 緑系 - 高品質
                    {"range": [90, 100], "color": "#AAFFAA"}  # 濃い緑系 - 非常に高品質
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": quality_scores["total"]
                }
            }
        ))
        
        # レイアウト設定
        gauge_chart.update_layout(
            height=300,
            margin=dict(t=40, b=0, l=40, r=40),
            paper_bgcolor="white",
            font={"family": "Arial", "size": 12}
        )
        
        # ベストプラクティスの追加
        if quality_scores["total"] >= 90:
            gauge_chart.add_annotation(
                x=0.5, y=0.7,
                text="高品質",
                showarrow=False,
                font={"size": 16, "color": "green"},
                align="center"
            )
        elif quality_scores["total"] < 50:
            gauge_chart.add_annotation(
                x=0.5, y=0.7,
                text="要改善",
                showarrow=False,
                font={"size": 16, "color": "red"},
                align="center"
            )
        
        # カテゴリ別バーチャートは次のクラスに委譲
        bar_chart = self.part2.generate_category_scores_chart(quality_scores)
        
        return gauge_chart, bar_chart
    
    def _get_score_color(self, score: float) -> str:
        """
        スコアに応じた色を返す
        
        Parameters
        ----------
        score : float
            品質スコア（0-100）
            
        Returns
        -------
        str
            対応する色のHEXコード
        """
        if score >= 90:
            return "#27AE60"  # 濃い緑
        elif score >= 75:
            return "#2ECC71"  # 緑
        elif score >= 50:
            return "#F1C40F"  # 黄色
        elif score >= 25:
            return "#E67E22"  # オレンジ
        else:
            return "#E74C3C"  # 赤
    
    # 他のメソッドはすべてPart2クラスに委譲
    def generate_spatial_quality_map(self) -> go.Figure:
        return self.part2.generate_spatial_quality_map()
    
    def generate_temporal_quality_chart(self) -> go.Figure:
        return self.part2.generate_temporal_quality_chart()
    
    def generate_heatmap_data(self) -> Dict[str, Any]:
        return self.part2.generate_heatmap_data()
    
    def generate_distribution_charts(self) -> Dict[str, Any]:
        return self.part2.generate_distribution_charts()
    
    def generate_timeline_markers(self) -> Dict[str, Any]:
        return self.part2.generate_timeline_markers()
    
    def generate_detailed_report(self) -> Dict[str, Any]:
        return self.part2.generate_detailed_report()
    
    def generate_quality_score_chart(self) -> go.Figure:
        return self.part2.generate_quality_score_chart()
    
    def generate_category_scores_chart(self) -> go.Figure:
        return self.part2.generate_category_scores_chart()
    
    def generate_problem_distribution_chart(self) -> go.Figure:
        return self.part2.generate_problem_distribution_chart()
    
    def generate_problem_heatmap(self) -> go.Figure:
        return self.part2.generate_problem_heatmap()
    
    def generate_timeline_chart(self) -> go.Figure:
        return self.part2.generate_timeline_chart()
    
    def generate_all_visualizations(self) -> Dict[str, go.Figure]:
        return self.part2.generate_all_visualizations()
