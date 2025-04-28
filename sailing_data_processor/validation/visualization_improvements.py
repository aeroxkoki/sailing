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
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.quality_metrics_integration import EnhancedQualityMetricsCalculator


class EnhancedValidationVisualization:
    """
    データ検証結果の拡張視覚化クラス
    
    Parameters
    ----------
    quality_metrics : EnhancedQualityMetricsCalculator
        強化されたデータ品質メトリクス計算クラス
    data : pd.DataFrame
        検証されたデータフレーム
    """
    
    def __init__(self, quality_metrics: EnhancedQualityMetricsCalculator, data: pd.DataFrame):
        """
        初期化
        
        Parameters
        ----------
        quality_metrics : EnhancedQualityMetricsCalculator
            強化されたデータ品質メトリクス計算クラス
        data : pd.DataFrame
            検証されたデータフレーム
        """
        self.quality_metrics = quality_metrics
        self.data = data
    
    def generate_quality_score_visualization(self) -> Tuple[go.Figure, go.Figure]:
        """
        品質スコアのゲージチャートとカテゴリ別バーチャートを生成。
        
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
        
        # カテゴリ別バーチャートを生成
        categories = ["completeness", "accuracy", "consistency"]
        values = [quality_scores[cat] for cat in categories]
        
        # カテゴリ名の日本語対応
        category_names = {
            "completeness": "完全性",
            "accuracy": "正確性",
            "consistency": "一貫性"
        }
        
        # カテゴリ別の色設定
        bar_colors = [
            self._get_score_color(values[0]),
            self._get_score_color(values[1]),
            self._get_score_color(values[2])
        ]
        
        display_categories = [category_names[cat] for cat in categories]
        
        bar_chart = go.Figure(data=[
            go.Bar(
                x=display_categories,
                y=values,
                marker_color=bar_colors,
                text=[f"{v:.1f}" for v in values],
                textposition="auto",
                hoverinfo="text",
                hovertext=[
                    f"完全性スコア: {values[0]:.1f}<br>欠損値や必須項目の充足度",
                    f"正確性スコア: {values[1]:.1f}<br>値の範囲や形式の正確さ",
                    f"一貫性スコア: {values[2]:.1f}<br>時間的・空間的な整合性"
                ]
            )
        ])
        
        # 目標ラインの追加（品質目標：90点）
        bar_chart.add_shape(
            type="line",
            x0=-0.5, y0=90, x1=2.5, y1=90,
            line=dict(color="green", width=2, dash="dash"),
            name="品質目標"
        )
        
        bar_chart.update_layout(
            title={
                "text": "カテゴリ別品質スコア",
                "y": 0.9,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
            },
            yaxis={
                "title": "品質スコア",
                "range": [0, 105],
                "tickvals": [0, 25, 50, 75, 90, 100],
                "ticktext": ["0", "25", "50", "75", "90", "100"],
                "gridcolor": "lightgray"
            },
            height=350,
            margin=dict(t=60, b=30, l=40, r=40),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font={"family": "Arial", "size": 12},
            showlegend=False
        )
        
        return gauge_chart, bar_chart
    
    def generate_spatial_quality_map(self) -> go.Figure:
        """
        空間的な品質分布のマップを生成。
        
        Returns
        -------
        go.Figure
            品質マップの図
        """
        # 空間品質スコアを取得
        spatial_scores = self.quality_metrics.calculate_spatial_quality_scores()
        
        if not spatial_scores:
            # データがない場合は空のマップを返す
            fig = go.Figure()
            fig.update_layout(
                title="空間的な品質分布マップ (データなし)",
                height=500,
                margin=dict(t=50, b=0, l=0, r=0)
            )
            return fig
        
        # マップの中心座標を計算
        all_lats = []
        all_lons = []
        for grid in spatial_scores:
            center = grid["center"]
            all_lats.append(center[0])
            all_lons.append(center[1])
        
        center_lat = sum(all_lats) / len(all_lats) if all_lats else 0
        center_lon = sum(all_lons) / len(all_lons) if all_lons else 0
        
        # マップの作成
        fig = go.Figure()
        
        # 各グリッドのマーカーを追加
        for grid in spatial_scores:
            quality_score = grid["quality_score"]
            
            # マーカーの色を品質スコアから決定
            color = self._get_score_color(quality_score)
            
            # ホバーテキストを作成
            hover_text = (
                f"グリッドID: {grid['grid_id']}<br>" +
                f"品質スコア: {quality_score:.1f}<br>" +
                f"問題数: {grid['problem_count']}<br>" +
                f"総レコード数: {grid['total_count']}<br>" +
                f"問題率: {(grid['problem_count'] / grid['total_count'] * 100):.1f}%"
            )
            
            # 問題タイプの内訳があれば追加
            if "problem_distribution" in grid:
                problem_type_text = "<br>問題タイプ内訳:<br>"
                for problem_type, count in grid["problem_distribution"].items():
                    if count > 0:
                        type_name = {
                            "missing_data": "欠損値",
                            "out_of_range": "範囲外の値",
                            "duplicates": "重複データ",
                            "spatial_anomalies": "空間的異常",
                            "temporal_anomalies": "時間的異常"
                        }.get(problem_type, problem_type)
                        problem_type_text += f" - {type_name}: {count}件<br>"
                hover_text += problem_type_text
            
            # グリッドの中心にマーカーを追加
            fig.add_trace(go.Scattermapbox(
                lat=[grid["center"][0]],
                lon=[grid["center"][1]],
                mode="markers+text",
                marker=dict(
                    size=20,
                    color=color,
                    opacity=0.7
                ),
                text=[f"{quality_score:.0f}"],
                textfont=dict(size=10, color="white"),
                hoverinfo="text",
                hovertext=[hover_text]
            ))
            
            # グリッドの境界を描画
            bounds = grid["bounds"]
            lats = [
                bounds["min_lat"], bounds["max_lat"],
                bounds["max_lat"], bounds["min_lat"],
                bounds["min_lat"]
            ]
            lons = [
                bounds["min_lon"], bounds["min_lon"],
                bounds["max_lon"], bounds["max_lon"],
                bounds["min_lon"]
            ]
            
            fig.add_trace(go.Scattermapbox(
                lat=lats,
                lon=lons,
                mode="lines",
                line=dict(width=1, color=color),
                hoverinfo="none"
            ))
        
        # マップレイアウトの設定
        fig.update_layout(
            title="空間的な品質分布マップ",
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=12
            ),
            height=500,
            margin=dict(t=50, b=0, l=0, r=0),
            showlegend=False
        )
        
        # 凡例として、品質スコアレンジの説明をアノテーションとして追加
        fig.add_annotation(
            x=0.02, y=0.02,
            xref="paper", yref="paper",
            text=(
                "品質スコア<br>" +
                "<span style='color:#E74C3C'>■</span> 0-50: 低品質<br>" +
                "<span style='color:#F1C40F'>■</span> 50-75: 中程度<br>" +
                "<span style='color:#2ECC71'>■</span> 75-90: 良好<br>" +
                "<span style='color:#27AE60'>■</span> 90-100: 優良"
            ),
            showarrow=False,
            align="left",
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="gray",
            borderwidth=1,
            borderpad=4,
            font=dict(size=10)
        )
        
        return fig
    
    def generate_temporal_quality_chart(self) -> go.Figure:
        """
        時間帯別の品質分布チャートを生成。
        
        Returns
        -------
        go.Figure
            時間帯別品質チャート
        """
        # 時間的品質スコアを取得
        temporal_scores = self.quality_metrics.calculate_temporal_quality_scores()
        
        if not temporal_scores:
            # データがない場合は空のチャートを返す
            fig = go.Figure()
            fig.update_layout(
                title="時間帯別の品質スコア (データなし)",
                height=400,
                margin=dict(t=50, b=50, l=40, r=40)
            )
            return fig
        
        # サブプロットの作成（2行1列）
        fig = make_subplots(
            rows=2, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("時間帯別品質スコア", "時間帯別データ量と問題数")
        )
        
        # 時間帯の表示順序を設定
        period_order = {"早朝": 1, "午前": 2, "午後": 3, "夕方": 4, "夜間": 5, "深夜": 6}
        temporal_scores.sort(key=lambda x: period_order.get(x["period"], 99))
        
        # 時間帯と品質スコアの抽出
        periods = [score["period"] for score in temporal_scores]
        quality_scores = [score["quality_score"] for score in temporal_scores]
        total_counts = [score["total_count"] for score in temporal_scores]
        problem_counts = [score["problem_count"] for score in temporal_scores]
        
        # 品質スコアのバーチャート（上の図）
        fig.add_trace(
            go.Bar(
                x=periods,
                y=quality_scores,
                marker_color=[self._get_score_color(score) for score in quality_scores],
                text=[f"{score:.1f}" for score in quality_scores],
                textposition="auto",
                name="品質スコア"
            ),
            row=1, col=1
        )
        
        # 目標ラインの追加（品質目標：90点）
        fig.add_shape(
            type="line",
            x0=-0.5, y0=90, 
            x1=len(periods) - 0.5, y1=90,
            line=dict(color="green", width=2, dash="dash"),
            row=1, col=1
        )
        
        # データ量のバーチャート（下の図）
        fig.add_trace(
            go.Bar(
                x=periods,
                y=total_counts,
                marker_color="rgba(0, 0, 255, 0.7)",
                name="データ量"
            ),
            row=2, col=1
        )
        
        # 問題数のバーチャート（下の図に重ねて表示）
        fig.add_trace(
            go.Bar(
                x=periods,
                y=problem_counts,
                marker_color="rgba(255, 0, 0, 0.7)",
                name="問題数"
            ),
            row=2, col=1
        )
        
        # レイアウト設定
        fig.update_layout(
            height=600,
            barmode="group",
            margin=dict(t=70, b=50, l=50, r=50),
            paper_bgcolor="white",
            plot_bgcolor="white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="closest"
        )
        
        # Y軸の設定
        fig.update_yaxes(
            title_text="品質スコア",
            range=[0, 105],
            tickvals=[0, 25, 50, 75, 90, 100],
            gridcolor="lightgray",
            row=1, col=1
        )
        
        fig.update_yaxes(
            title_text="レコード数",
            gridcolor="lightgray",
            row=2, col=1
        )
        
        return fig
    
    def generate_quality_score_dashboard(self) -> Dict[str, go.Figure]:
        """
        品質スコアダッシュボードを生成
        
        各種品質スコアの視覚的表現を含むダッシュボード要素を生成します。
        
        Returns
        -------
        Dict[str, go.Figure]
            ダッシュボード要素の辞書
        """
        # 総合スコアとカテゴリ別スコアのチャートを生成
        gauge_chart, bar_chart = self.generate_quality_score_visualization()
        
        # 時間的品質チャートを生成
        temporal_chart = self.generate_temporal_quality_chart()
        
        # 空間的品質マップを生成
        spatial_map = self.generate_spatial_quality_map()
        
        # ダッシュボード要素を辞書で返す
        return {
            "gauge_chart": gauge_chart,
            "category_bar_chart": bar_chart,
            "temporal_quality_chart": temporal_chart,
            "spatial_quality_map": spatial_map
        }
    
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