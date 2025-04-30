# -*- coding: utf-8 -*-
"""
Module for quality metrics visualization.
This module provides visualization functions for quality metrics.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# ロギング設定
logger = logging.getLogger(__name__)

# 必要なモジュールを遅延インポートするための準備
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    logger.warning("plotly モジュールをインポートできませんでした。視覚化機能は利用できません。")
    PLOTLY_AVAILABLE = False
    # モックオブジェクトを作成して他のコードが動作できるようにする
    class MockGo:
        def __init__(self):
            self.Figure = MockFigure
        def __getattr__(self, name):
            return MockClass()
    
    class MockFigure:
        def __init__(self, *args, **kwargs):
            pass
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    
    class MockClass:
        def __init__(self, *args, **kwargs):
            pass
        def __call__(self, *args, **kwargs):
            return MockFigure()
    
    go = MockGo()

# 自作モジュールのインポート
from sailing_data_processor.validation.quality_metrics_improvements_core import QualityMetricsCalculatorExtension

class QualityMetricsVisualization:
    """
    品質メトリクスの視覚化クラス
    """
    
    def __init__(self, metrics_calculator: QualityMetricsCalculatorExtension):
        """
        初期化メソッド
        
        Parameters
        ----------
        metrics_calculator : QualityMetricsCalculatorExtension
            品質メトリクス計算オブジェクト
        """
        self.metrics_calculator = metrics_calculator
    
    def generate_quality_score_visualization(self) -> Tuple:
        """
        品質スコアのゲージチャートとカテゴリ別バーチャートを生成。
        
        品質スコアの視覚的表現として、総合スコアを円形ゲージで、
        カテゴリ別スコア（完全性、正確性、一貫性）を棒グラフで表示します。
        
        Returns
        -------
        Tuple
            ゲージチャートとバーチャート
        """
        # Plotlyが利用可能かチェック
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotlyが利用できないため、視覚化を生成できません")
            # ダミーオブジェクトを返す（エラー防止用）
            class DummyFigure:
                def update_layout(self, *args, **kwargs): pass
                def add_annotation(self, *args, **kwargs): pass
                def add_shape(self, *args, **kwargs): pass
            return DummyFigure(), DummyFigure()
        
        # 品質スコアを取得
        quality_scores = self.metrics_calculator.calculate_quality_scores()
        
        # ゲージチャートを生成（総合スコア用）
        gauge_chart = go.Figure(go.Indicator(
            mode="gauge+number",
            value=quality_scores["total"],
            title={"text": "データ品質スコア", "font": {"size": 24}},
            number={"font": {"size": 32}, "color": self.metrics_calculator._get_score_color(quality_scores["total"])},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": self.metrics_calculator._get_score_color(quality_scores["total"])},
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
            self.metrics_calculator._get_score_color(values[0]),
            self.metrics_calculator._get_score_color(values[1]),
            self.metrics_calculator._get_score_color(values[2])
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

    def generate_spatial_quality_map(self):
        """
        空間的な品質分布のマップを生成。
        
        GPSデータの空間的な品質分布を地図上に視覚化します。
        各エリアは品質スコアによって色分けされ、品質の空間的な変動を把握できます。
        
        Returns
        -------
        Object
            品質マップの図（Plotly Figureまたはダミーオブジェクト）
        """
        # Plotlyが利用可能かチェック
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotlyが利用できないため、空間マップを生成できません")
            # ダミーオブジェクトを返す（エラー防止用）
            class DummyFigure:
                def update_layout(self, *args, **kwargs): pass
                def add_annotation(self, *args, **kwargs): pass
                def add_trace(self, *args, **kwargs): pass
            return DummyFigure()
        
        # 空間品質スコアを取得
        spatial_scores = self.metrics_calculator.calculate_spatial_quality_scores()
        
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
            color = self.metrics_calculator._get_score_color(quality_score)
            
            # ホバーテキストを作成
            hover_text = (
                f"品質スコア: {quality_score:.1f}<br>" +
                f"問題数: {grid['problem_count']}<br>" +
                f"総レコード数: {grid['total_count']}<br>" +
                f"問題率: {(grid['problem_count'] / grid['total_count'] * 100):.1f}%"
            )
            
            # 問題タイプの内訳があれば追加
            if "problem_types" in grid:
                problem_type_text = "<br>問題タイプ内訳:<br>"
                for problem_type, count in grid["problem_types"].items():
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
