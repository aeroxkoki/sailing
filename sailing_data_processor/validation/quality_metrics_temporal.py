# -*- coding: utf-8 -*-
"""
Module for quality metrics temporal analysis.
This module provides temporal analysis functions for quality metrics.
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

class QualityMetricsTemporal:
    """
    品質メトリクスの時間的分析クラス
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
    
    def generate_temporal_quality_chart(self):
        """
        時間帯別の品質分布チャートを生成。
        
        時間帯ごとの品質スコアをグラフ化し、時間的な品質の変動を視覚化します。
        各時間帯のデータ量と問題発生率も表示します。
        
        Returns
        -------
        Object
            時間帯別品質チャート（Plotly Figureまたはダミーオブジェクト）
        """
        # Plotlyが利用可能かチェック
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotlyが利用できないため、時間帯別チャートを生成できません")
            # ダミーオブジェクトを返す（エラー防止用）
            class DummyFigure:
                def update_layout(self, *args, **kwargs): pass
                def add_trace(self, *args, **kwargs): pass
                def add_shape(self, *args, **kwargs): pass
                def update_yaxes(self, *args, **kwargs): pass
                def update_xaxes(self, *args, **kwargs): pass
            return DummyFigure()
        
        # 時間的品質スコアを取得
        temporal_scores = self.metrics_calculator.calculate_temporal_quality_scores()
        
        if not temporal_scores:
            # データがない場合は空のチャートを返す
            fig = go.Figure()
            fig.update_layout(
                title="時間帯別の品質スコア (データなし)",
                height=400,
                margin=dict(t=50, b=50, l=40, r=40)
            )
            return fig
        
        # 時間順にソート
        temporal_scores.sort(key=lambda x: x["start_time"])
        
        # チャートデータの準備
        labels = [score["label"] for score in temporal_scores]
        quality_scores = [score["quality_score"] for score in temporal_scores]
        problem_counts = [score["problem_count"] for score in temporal_scores]
        total_counts = [score["total_count"] for score in temporal_scores]
        problem_percentages = [score["problem_percentage"] for score in temporal_scores]
        
        # 問題タイプごとのデータを抽出（存在する場合）
        problem_types_data = {}
        if "problem_types" in temporal_scores[0]:
            # 問題タイプのキーを取得
            problem_type_keys = temporal_scores[0]["problem_types"].keys()
            
            for key in problem_type_keys:
                problem_types_data[key] = [score["problem_types"].get(key, 0) for score in temporal_scores]
        
        # サブプロットの数を決定
        if problem_types_data:
            subplot_rows = 3  # 品質スコア、データ量と問題率、問題タイプ分布
        else:
            subplot_rows = 2  # 品質スコア、データ量と問題率のみ
        
        # グラフの作成（サブプロット）
        fig = make_subplots(
            rows=subplot_rows, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(
                ["時間帯別品質スコア", "時間帯別データ量と問題率"] + 
                (["問題タイプ別分布"] if problem_types_data else [])
            ),
            specs=[
                [{"type": "bar"}],
                [{"type": "scatter"}]
            ] + ([{"type": "bar"}] if problem_types_data else [])
        )
        
        # 品質スコアのバーチャート
        bar_colors = [self.metrics_calculator._get_score_color(score) for score in quality_scores]
        
        # 品質スコアのバーチャート（上の図）
        fig.add_trace(
            go.Bar(
                x=labels,
                y=quality_scores,
                marker_color=bar_colors,
                text=[f"{score:.1f}" for score in quality_scores],
                textposition="auto",
                hoverinfo="text",
                hovertext=[
                    (f"時間帯: {labels[i]}<br>" +
                     f"品質スコア: {quality_scores[i]:.1f}<br>" +
                     f"データ量: {total_counts[i]}<br>" +
                     f"問題数: {problem_counts[i]}")
                    for i in range(len(labels))
                ],
                name="品質スコア"
            ),
            row=1, col=1
        )
        
        # 目標ラインの追加（品質目標：90点）
        fig.add_shape(
            type="line",
            x0=-0.5, y0=90, 
            x1=len(labels) - 0.5, y1=90,
            line=dict(color="green", width=2, dash="dash"),
            row=1, col=1
        )
        
        # データ量のラインチャート（下の図）
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=total_counts,
                mode="lines+markers",
                name="データ量",
                line=dict(color="blue", width=2),
                marker=dict(size=8, color="blue"),
                hoverinfo="text",
                hovertext=[f"時間帯: {labels[i]}<br>データ量: {total_counts[i]}" for i in range(len(labels))]
            ),
            row=2, col=1
        )
        
        # 問題率のラインチャート（2次Y軸）
        fig.add_trace(
            go.Scatter(
                x=labels,
                y=problem_percentages,
                mode="lines+markers",
                name="問題率 (%)",
                line=dict(color="red", width=2, dash="dot"),
                marker=dict(size=8, color="red"),
                hoverinfo="text",
                hovertext=[f"時間帯: {labels[i]}<br>問題率: {problem_percentages[i]:.1f}%" for i in range(len(labels))],
                yaxis="y3"
            ),
            row=2, col=1
        )
        
        # 問題タイプの内訳がある場合、それも表示
        if problem_types_data:
            # 問題タイプごとの色を設定
            type_colors = {
                "missing_data": "blue",
                "out_of_range": "red",
                "duplicates": "green",
                "spatial_anomalies": "purple",
                "temporal_anomalies": "orange"
            }
            # 問題タイプごとの表示名
            type_names = {
                "missing_data": "欠損値",
                "out_of_range": "範囲外の値",
                "duplicates": "重複データ",
                "spatial_anomalies": "空間的異常",
                "temporal_anomalies": "時間的異常"
            }
            # 積み上げバーチャートのデータ準備
            bar_data = []
            for key in problem_types_data:
                if sum(problem_types_data[key]) > 0:
                    bar_data.append({
                        "name": type_names.get(key, key),
                        "values": problem_types_data[key],
                        "color": type_colors.get(key, "gray")
                    })
            
            # 積み上げバーチャートを追加
            for data in bar_data:
                fig.add_trace(
                    go.Bar(
                        x=labels,
                        y=data["values"],
                        name=data["name"],
                        marker_color=data["color"],
                        hoverinfo="text",
                        hovertext=[
                            f"時間帯: {labels[i]}<br>{data['name']}: {data['values'][i]}件"
                            for i in range(len(labels))
                        ]
                    ),
                    row=3, col=1
                )
        
        # レイアウト設定
        fig.update_layout(
            height=600 if problem_types_data else 500,
            margin=dict(t=70, b=50, l=50, r=50),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(family="Arial", size=12),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="closest",
            barmode="stack" if problem_types_data else None
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
            title_text="データ量",
            range=[0, max(total_counts) * 1.1],
            gridcolor="lightgray",
            row=2, col=1,
            title_standoff=0
        )
        
        # 2次Y軸（問題率）の追加
        fig.update_layout(
            yaxis3=dict(
                title="問題率 (%)",
                titlefont=dict(color="red"),
                tickfont=dict(color="red"),
                anchor="x",
                overlaying="y2",
                side="right",
                range=[0, max(problem_percentages) * 1.1 if problem_percentages else 10],
                showgrid=False
            )
        )
        
        # 問題タイプの内訳グラフのY軸設定
        if problem_types_data:
            fig.update_yaxes(
                title_text="問題数",
                gridcolor="lightgray",
                row=3, col=1
            )
        
        # X軸の設定（斜めに表示）
        fig.update_xaxes(
            tickangle=-45,
            row=subplot_rows, col=1
        )
        
        return fig
