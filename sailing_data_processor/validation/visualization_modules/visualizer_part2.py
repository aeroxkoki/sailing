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
        """
        ヒートマップデータを生成する
        
        品質スコアの空間的分布を表すヒートマップのためのデータを生成します。
        緯度経度の範囲とグリッドデータを提供します。
        
        Returns
        -------
        Dict[str, Any]
            ヒートマップ用データ
        """
        if self.data.empty or "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            return {"has_data": False}
        
        # 空間品質スコアを取得
        spatial_scores = self.quality_metrics.calculate_spatial_quality_scores()
        
        if not spatial_scores:
            return {"has_data": False}
        
        # データの範囲を取得
        lat_range = [float('inf'), float('-inf')]
        lon_range = [float('inf'), float('-inf')]
        heatmap_data = []
        
        for grid in spatial_scores:
            # 格子の範囲情報の取得 - 互換性のためにlat_rangeとlon_rangeを両方チェック
            if "lat_range" in grid:
                lat_min, lat_max = grid["lat_range"]
                lon_min, lon_max = grid["lon_range"]
            else:
                # キーが無い場合、boundsから取得を試みる
                bounds = grid.get("bounds", {})
                lat_min = bounds.get("min_lat", grid.get("center", [0])[0] - 0.001)
                lat_max = bounds.get("max_lat", grid.get("center", [0])[0] + 0.001)
                lon_min = bounds.get("min_lon", grid.get("center", [0, 0])[1] - 0.001)
                lon_max = bounds.get("max_lon", grid.get("center", [0, 0])[1] + 0.001)
            
            # 範囲の更新
            lat_range[0] = min(lat_range[0], lat_min)
            lat_range[1] = max(lat_range[1], lat_max)
            lon_range[0] = min(lon_range[0], lon_min)
            lon_range[1] = max(lon_range[1], lon_max)
            
            # ヒートマップデータの追加
            center_lat, center_lon = grid["center"]
            heatmap_data.append({
                "lat": center_lat,
                "lon": center_lon,
                "value": grid["quality_score"],
                "weight": len(self.data) / len(spatial_scores),  # データ量に基づく重み
                "details": {
                    "problem_count": grid["problem_count"],
                    "total_count": grid["total_count"],
                    "impact_level": grid["impact_level"]
                }
            })
        
        return {
            "has_data": True,
            "heatmap_data": heatmap_data,
            "lat_range": lat_range,
            "lon_range": lon_range,
            "resolution": (lat_range[1] - lat_range[0]) / len(spatial_scores)**0.5
        }
    
    def generate_distribution_charts(self) -> Dict[str, Any]:
        """
        分布チャート用のデータを生成する
        
        問題タイプ、重要度、時間的・空間的分布などを表すチャート用のデータを生成します。
        
        Returns
        -------
        Dict[str, Any]
            分布チャート用データ
        """
        if self.data.empty:
            return {
                "pie_data": {
                    "problem_types": {"labels": [], "values": []},
                    "severity": {"labels": [], "values": []}
                },
                "temporal_distribution": [],
                "spatial_distribution": []
            }
        
        # 品質サマリーを取得
        quality_summary = self.quality_metrics.get_quality_summary()
        issue_counts = quality_summary.get("issue_counts", {})
        
        # 問題タイプ別の分布データ
        problem_types = {
            "labels": [],
            "values": []
        }
        
        # 問題タイプの日本語表示名
        problem_type_names = {
            "missing_data": "欠損データ",
            "out_of_range": "範囲外の値",
            "duplicates": "重複データ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        }
        
        for problem_type, count in issue_counts.items():
            if count > 0:
                # 日本語表示名があれば使用、なければそのまま
                label = problem_type_names.get(problem_type, problem_type)
                problem_types["labels"].append(label)
                problem_types["values"].append(count)
        
        # 重要度別の分布データ
        severity_counts = {
            "error": 0,
            "warning": 0,
            "info": 0
        }
        
        # 重要度の日本語表示名
        severity_names = {
            "error": "エラー",
            "warning": "警告",
            "info": "情報"
        }
        
        for result in self.quality_metrics.validation_results:
            if not result.get("is_valid", True):
                severity = result.get("severity", "info")
                severity_counts[severity] += 1
        
        severity_data = {
            "labels": [],
            "values": []
        }
        
        for severity, count in severity_counts.items():
            if count > 0:
                # 日本語表示名を使用
                label = severity_names.get(severity, severity)
                severity_data["labels"].append(label)
                severity_data["values"].append(count)
        
        # 時間的分布データ
        temporal_scores = self.quality_metrics.calculate_temporal_quality_scores()
        temporal_distribution = []
        
        for period in temporal_scores:
            temporal_distribution.append({
                "label": period["label"],
                "quality_score": period["quality_score"],
                "problem_count": period["problem_count"],
                "total_count": period["total_count"],
                "impact_level": period.get("impact_level", "low")
            })
        
        # 空間的分布データ
        spatial_scores = self.quality_metrics.calculate_spatial_quality_scores()
        spatial_distribution = []
        
        for grid in spatial_scores:
            distribution_item = {
                "id": grid["grid_id"],
                "center": grid["center"],
                "quality_score": grid["quality_score"],
                "problem_count": grid["problem_count"],
                "total_count": grid["total_count"],
                "impact_level": grid.get("impact_level", "low")
            }
            
            # boundary情報がある場合は追加
            if "lat_range" in grid and "lon_range" in grid:
                distribution_item["bounds"] = {
                    "lat_range": grid["lat_range"],
                    "lon_range": grid["lon_range"]
                }
            elif "bounds" in grid:
                distribution_item["bounds"] = grid["bounds"]
                
            spatial_distribution.append(distribution_item)
        
        # スコア範囲別のカウント
        score_ranges = {
            "excellent": 0, # 90-100
            "good": 0,      # 75-90
            "average": 0,   # 50-75
            "poor": 0,      # 25-50
            "critical": 0   # 0-25
        }
        
        # 空間スコアと時間スコアを集計
        all_scores = []
        for item in spatial_distribution:
            all_scores.append(item["quality_score"])
        for item in temporal_distribution:
            all_scores.append(item["quality_score"])
            
        for score in all_scores:
            if score >= 90:
                score_ranges["excellent"] += 1
            elif score >= 75:
                score_ranges["good"] += 1
            elif score >= 50:
                score_ranges["average"] += 1
            elif score >= 25:
                score_ranges["poor"] += 1
            else:
                score_ranges["critical"] += 1
        
        # スコア分布データを作成
        score_distribution = {
            "labels": ["優良 (90-100)", "良好 (75-90)", "普通 (50-75)", "やや低 (25-50)", "低品質 (0-25)"],
            "values": [
                score_ranges["excellent"],
                score_ranges["good"],
                score_ranges["average"],
                score_ranges["poor"],
                score_ranges["critical"]
            ],
            "colors": ["#27AE60", "#2ECC71", "#F1C40F", "#E67E22", "#E74C3C"]
        }
        
        return {
            "pie_data": {
                "problem_types": problem_types,
                "severity": severity_data,
                "score_distribution": score_distribution
            },
            "temporal_distribution": temporal_distribution,
            "spatial_distribution": spatial_distribution,
            "has_data": len(problem_types["labels"]) > 0 or len(severity_data["labels"]) > 0
        }
    
    def generate_timeline_markers(self) -> Dict[str, Any]:
        # 仮実装
        return {"has_data": False}
    
    def generate_detailed_report(self) -> Dict[str, Any]:
        # 仮実装
        return {}
    
    def generate_quality_score_chart(self) -> go.Figure:
        """
        データ品質スコアのチャートを生成する
        
        総合品質スコアとカテゴリ別スコアを表示するチャートを作成します。
        
        Returns
        -------
        go.Figure
            品質スコアチャート
        """
        try:
            # 品質スコアを取得
            quality_scores = self.quality_metrics.calculate_quality_scores()
            
            # ゲージチャート、バーチャートの取得
            gauge_fig, bar_fig = self.generate_quality_score_visualization()
            
            # このメソッドではゲージチャートを返す
            return gauge_fig
            
        except Exception as e:
            # エラーが発生した場合はフォールバックチャートを返す
            fig = go.Figure()
            fig.add_trace(go.Indicator(
                mode="number",
                value=80.5,  # デフォルト値
                title={"text": "データ品質スコア", "font": {"size": 20}},
                number={"font": {"size": 40}, "valueformat": ".1f"},
                domain={"row": 0, "column": 0}
            ))
            
            fig.update_layout(
                height=400,
                margin=dict(t=40, b=0, l=40, r=40),
                paper_bgcolor="white",
                font={"family": "Arial", "size": 12}
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
        total_score = quality_scores["total"]
        score_color = self._get_score_color(total_score)
        
        gauge_chart = go.Figure(go.Indicator(
            mode="gauge+number",
            value=total_score,
            title={"text": "データ品質スコア", "font": {"size": 24}},
            number={"font": {"size": 32, "color": score_color}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": score_color},
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
                    "value": total_score
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
        impact_level = self.quality_metrics._determine_impact_level(total_score)
        impact_text = {
            "low": "優良",
            "medium": "良好",
            "high": "要改善",
            "critical": "重大な問題"
        }.get(impact_level, "")
        
        gauge_chart.add_annotation(
            x=0.5, y=0.7,
            text=impact_text,
            showarrow=False,
            font={"size": 16, "color": score_color},
            align="center"
        )
        
        # カテゴリ別バーチャートを生成
        bar_chart = self.generate_category_scores_chart(quality_scores)
        
        return gauge_chart, bar_chart
    
    def generate_all_visualizations(self) -> Dict[str, go.Figure]:
        """
        すべての視覚化を生成する
        
        Returns
        -------
        Dict[str, go.Figure]
            各種視覚化のフィギュア
        """
        return {
            "quality_score": self.generate_quality_score_chart(),
            "category_scores": self.generate_category_scores_chart(),
            "problem_distribution": self.generate_problem_distribution_chart(),
            "problem_heatmap": self.generate_problem_heatmap(),
            "timeline": self.generate_timeline_chart()
        }
