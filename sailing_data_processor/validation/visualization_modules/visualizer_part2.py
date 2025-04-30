# -*- coding: utf-8 -*-
"""
ValidationVisualizer クラスの続き - Part2
このクラスは visualization.py を複数ファイルに分割するために作成されました
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json

from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator


class ValidationVisualizerPart2:
    """
    ValidationVisualizer クラスの続き - Part2
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
    
    def generate_category_scores_chart(self, quality_scores=None) -> go.Figure:
        """
        カテゴリ別バーチャートを生成
        
        Parameters
        ----------
        quality_scores : Dict, optional
            品質スコア辞書。Noneの場合は計算する。
            
        Returns
        -------
        go.Figure
            カテゴリ別バーチャート
        """
        # 品質スコアがない場合は計算
        if quality_scores is None:
            quality_scores = self.quality_metrics.calculate_quality_scores()
        
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
        
        return bar_chart
    
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
    
    def generate_spatial_quality_map(self) -> go.Figure:
        """
        空間的な品質分布のマップを生成。
        
        GPSデータの空間的な品質分布を地図上に視覚化します。
        各エリアは品質スコアによって色分けされ、品質の空間的な変動を把握できます。
        
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
        
        # 各グリッドのポリゴンを追加
        for grid in spatial_scores:
            lat_range = grid["lat_range"]
            lon_range = grid["lon_range"]
            quality_score = grid["quality_score"]
            
            # グリッドの四隅の座標
            lats = [lat_range[0], lat_range[1], lat_range[1], lat_range[0]]
            lons = [lon_range[0], lon_range[0], lon_range[1], lon_range[1]]
            
            # ポリゴンの色を品質スコアから決定
            color = self._get_score_color(quality_score)
            
            # ホバーテキストを作成
            hover_text = (
                f"品質スコア: {quality_score:.1f}<br>" +
                f"問題数: {grid['problem_count']}<br>" +
                f"総レコード数: {grid['total_count']}<br>" +
                f"問題率: {(grid['problem_count'] / grid['total_count'] * 100):.1f}%"
            )
            
            # 各グリッドのポリゴンを追加
            fig.add_trace(go.Scattermapbox(
                lat=lats + [lats[0]],  # 閉じたポリゴンにするため最初の点を追加
                lon=lons + [lons[0]],
                mode="lines",
                line=dict(width=1, color=color),
                fill="toself",
                fillcolor=color,
                opacity=0.6,
                text=hover_text,
                hoverinfo="text",
                name=f"グリッド（スコア: {quality_score:.1f}）"
            ))
            
            # グリッドの中心にスコアを表示するマーカーを追加
            fig.add_trace(go.Scattermapbox(
                lat=[grid["center"][0]],
                lon=[grid["center"][1]],
                mode="markers+text",
                marker=dict(size=10, color="white", opacity=0.7),
                text=[f"{quality_score:.0f}"],
                textfont=dict(size=10, color="black"),
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
                "<span style='color:#E74C3C'>■</span> 0-25: 重大な問題<br>" +
                "<span style='color:#E67E22'>■</span> 25-50: 多数の問題<br>" +
                "<span style='color:#F1C40F'>■</span> 50-75: 一部に問題<br>" +
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
        # 仮実装
        fig = go.Figure()
        fig.update_layout(
            title="時間帯別の品質スコア (実装中)",
            height=400
        )
        return fig
    
    def generate_heatmap_data(self) -> Dict[str, Any]:
        # 仮実装
        return {"has_data": False}
    
    def generate_distribution_charts(self) -> Dict[str, Any]:
        # 仮実装
        return {}
    
    def generate_timeline_markers(self) -> Dict[str, Any]:
        # 仮実装
        return {"has_data": False}
    
    def generate_detailed_report(self) -> Dict[str, Any]:
        # 仮実装
        return {}
    
    def generate_quality_score_chart(self) -> go.Figure:
        # 仮実装
        fig = go.Figure()
        fig.update_layout(
            title="データ品質スコア (実装中)",
            height=300
        )
        return fig
    
    def generate_problem_distribution_chart(self) -> go.Figure:
        # 仮実装
        fig = go.Figure()
        fig.update_layout(
            title="問題タイプの分布 (実装中)",
            height=350
        )
        return fig
    
    def generate_problem_heatmap(self) -> go.Figure:
        # 仮実装
        fig = go.Figure()
        fig.update_layout(
            title="問題密度ヒートマップ (実装中)",
            height=400
        )
        return fig
    
    def generate_timeline_chart(self) -> go.Figure:
        # 仮実装
        fig = go.Figure()
        fig.update_layout(
            title="問題のタイムライン (実装中)",
            height=300
        )
        return fig
    
    def generate_all_visualizations(self) -> Dict[str, go.Figure]:
        # 仮実装
        return {
            "quality_score": self.generate_quality_score_chart(),
            "category_scores": self.generate_category_scores_chart(),
            "problem_distribution": self.generate_problem_distribution_chart(),
            "problem_heatmap": self.generate_problem_heatmap(),
            "timeline": self.generate_timeline_chart()
        }
