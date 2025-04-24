# -*- coding: utf-8 -*-
"""
sailing_data_processor.validation.visualization_improvements

"""データ検証結果の視覚化機能の強化実装"""
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
"""データ検証結果の拡張視覚化クラス"""
    
    Parameters
    ----------
    quality_metrics : EnhancedQualityMetricsCalculator
"""強化されたデータ品質メトリクス計算クラス"""
    data : pd.DataFrame
"""検証されたデータフレーム"""
    """
    
    def __init__(self, quality_metrics: EnhancedQualityMetricsCalculator, data: pd.DataFrame):
        """
"""初期化"""
        
        Parameters
        ----------
        quality_metrics : EnhancedQualityMetricsCalculator
"""強化されたデータ品質メトリクス計算クラス"""
        data : pd.DataFrame
"""検証されたデータフレーム"""
        """
        self.quality_metrics = quality_metrics
        self.data = data
    
    def generate_quality_score_visualization(self) -> Tuple[go.Figure, go.Figure]:
        """
"""品質スコアのゲージチャートとカテゴリ別バーチャートを生成。"""
        
        Returns
        -------
        Tuple[go.Figure, go.Figure]
"""ゲージチャートとバーチャート"""
        """
        # 品質スコアを取得
        quality_scores = self.quality_metrics.calculate_quality_scores()
        
        # ゲージチャートを生成（総合スコア用）
        gauge_chart = go.Figure(go.Indicator(
            mode="gauge+number",
            value=quality_scores["total"],
"""            title={"text": "データ品質スコア", "font": {"size": 24}},"""
            number={"font": {"size": 32, "color": self._get_score_color(quality_scores["total"])}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkblue"},
                "bar": {"color": self._get_score_color(quality_scores["total"])},
                "bgcolor": "white",
                "borderwidth": 2,
                "bordercolor": "gray",
                "steps": [
"""                    {"range": [0, 50], "color": "#FFCCCC"},  # 赤系 - 低品質"""
"""                    {"range": [50, 75], "color": "#FFEEAA"},  # 黄系 - 中品質"""
"""                    {"range": [75, 90], "color": "#CCFFCC"},  # 緑系 - 高品質"""
"""                    {"range": [90, 100], "color": "#AAFFAA"}  # 濃い緑系 - 非常に高品質"""
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": quality_scores["total"]
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
"""            "completeness": "完全性","""
"""            "accuracy": "正確性","""
"""            "consistency": "一貫性""""
        
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
"""                    f"完全性スコア: {values[0]:.1f}<br>欠損値や必須項目の充足度","""
"""                    f"正確性スコア: {values[1]:.1f}<br>値の範囲や形式の正確さ","""
"""                    f"一貫性スコア: {values[2]:.1f}<br>時間的・空間的な整合性""""
                ]
            )
        ])
        
        # 目標ラインの追加（品質目標：90点）
        bar_chart.add_shape(
            type="line",
            x0=-0.5, y0=90, x1=2.5, y1=90,
            line=dict(color="green", width=2, dash="dash"),
"""            name="品質目標""""
        )
        
        bar_chart.update_layout(
            title={
"""                "text": "カテゴリ別品質スコア","""
                "y": 0.9,
                "x": 0.5,
                "xanchor": "center",
                "yanchor": "top"
            },
            yaxis={
"""                "title": "品質スコア","""
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
"""空間的な品質分布のマップを生成。"""
        
        Returns
        -------
        go.Figure
"""品質マップの図"""
        """
        # 空間品質スコアを取得
        spatial_scores = self.quality_metrics.calculate_spatial_quality_scores()
        
        if not spatial_scores:
            # データがない場合は空のマップを返す
            fig = go.Figure()
            fig.update_layout(
"""                title="空間的な品質分布マップ (データなし)","""
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
"""                f"グリッドID: {grid['grid_id']}<br>" +"""
"""                f"品質スコア: {quality_score:.1f}<br>" +"""
"""                f"問題数: {grid['problem_count']}<br>" +"""
"""                f"総レコード数: {grid['total_count']}<br>" +"""
"""                f"問題率: {(grid['problem_count'] / grid['total_count'] * 100):.1f}%""""
            )
            
            # 問題タイプの内訳があれば追加
            if "problem_distribution" in grid:
"""                problem_type_text = "<br>問題タイプ内訳:<br>""""
                for problem_type, count in grid["problem_distribution"].items():
                    if count > 0:
                        type_name = {
"""                            "missing_data": "欠損値","""
"""                            "out_of_range": "範囲外の値","""
"""                            "duplicates": "重複データ","""
"""                            "spatial_anomalies": "空間的異常","""
"""                            "temporal_anomalies": "時間的異常""""
                        }.get(problem_type, problem_type)
"""                        problem_type_text += f" - {type_name}: {count}件<br>""""
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
"""            title="空間的な品質分布マップ","""
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
"""                "品質スコア<br>" +"""
"""                "<span style='color:#E74C3C'>■</span> 0-50: 低品質<br>" +"""
"""                "<span style='color:#F1C40F'>■</span> 50-75: 中程度<br>" +"""
"""                "<span style='color:#2ECC71'>■</span> 75-90: 良好<br>" +"""
"""                "<span style='color:#27AE60'>■</span> 90-100: 優良""""
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
"""時間帯別の品質分布チャートを生成。"""
        
        Returns
        -------
        go.Figure
"""時間帯別品質チャート"""
        """
        # 時間的品質スコアを取得
        temporal_scores = self.quality_metrics.calculate_temporal_quality_scores()
        
        if not temporal_scores:
            # データがない場合は空のチャートを返す
            fig = go.Figure()
            fig.update_layout(
"""                title="時間帯別の品質スコア (データなし)","""
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
"""            subplot_titles=("時間帯別品質スコア", "時間帯別データ量と問題数")"""
        )
        
        # 時間帯の表示順序を設定
"""        period_order = {"早朝": 1, "午前": 2, "午後": 3, "夕方": 4, "夜間": 5, "深夜": 6}"""
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
"""                name="品質スコア""""
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
"""                name="データ量""""
            ),
            row=2, col=1
        )
        
        # 問題数のバーチャート（下の図に重ねて表示）
        fig.add_trace(
            go.Bar(
                x=periods,
                y=problem_counts,
                marker_color="rgba(255, 0, 0, 0.7)",
"""                name="問題数""""
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
"""            title_text="品質スコア","""
# # #             range=[0, 105],
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
# # #             tickvals=[0, 25, 50, 75, 90, 100],
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
            gridcolor="lightgray",
            row=1, col=1
        )
        
        fig.update_yaxes(
"""            title_text="レコード数","""
            gridcolor="lightgray",
            row=2, col=1
        )
        
        return fig
    
    def generate_quality_score_dashboard(self) -> Dict[str, go.Figure]:
        """
"""品質スコアダッシュボードを生成"""
        
"""各種品質スコアの視覚的表現を含むダッシュボード要素を生成します。"""
        
        Returns
        -------
        Dict[str, go.Figure]
"""ダッシュボード要素の辞書"""
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
        
    def _get_score_color(self, score: float) -> str:
        """
"""スコアに応じた色を返す"""
        
        Parameters
        ----------
        score : float
"""品質スコア（0-100）"""
            
        Returns
        -------
        str
"""対応する色のHEXコード"""
        """
        if score >= 90:
"""            return "#27AE60"  # 濃い緑"""
        elif score >= 75:
"""            return "#2ECC71"  # 緑"""
        elif score >= 50:
"""            return "#F1C40F"  # 黄色"""
        elif score >= 25:
"""            return "#E67E22"  # オレンジ"""
        else:
"""            return "#E74C3C"  # 赤"""

"""        各種品質スコアの視覚的表現を含むダッシュボード要素を生成します。"""

        Returns
        -------
        Dict[str, go.Figure]
"""            ダッシュボード要素の辞書"""
        """
        # 品質スコアと関連チャートを生成
        gauge_chart, bar_chart = self.quality_metrics.generate_quality_score_visualization()
        
        # 時間的品質チャートを生成
        temporal_chart = self.quality_metrics.generate_temporal_quality_chart()
        
        # 空間的品質マップを生成
        spatial_map = self.quality_metrics.generate_spatial_quality_map()
        
        # ダッシュボード要素を辞書で返す
        return {
            "gauge_chart": gauge_chart,
            "category_bar_chart": bar_chart,
            "temporal_quality_chart": temporal_chart,
            "spatial_quality_map": spatial_map
    
    def generate_problem_distribution_visualization(self) -> Dict[str, go.Figure]:
        """
"""        問題分布の視覚化を生成"""

"""        問題の時間的・空間的分布を視覚化します。"""

        Returns
        -------
        Dict[str, go.Figure]
"""            問題分布の視覚化の辞書"""
        """
        # 時間的分布の視覚化
        temporal_scores = self.quality_metrics.calculate_temporal_quality_scores()
        temporal_chart = self._generate_temporal_problem_distribution(temporal_scores)
        
        # 空間的分布の視覚化
        spatial_scores = self.quality_metrics.calculate_spatial_quality_scores()
        spatial_heatmap = self._generate_spatial_problem_heatmap(spatial_scores)
        
        # 問題タイプ別の分布パイチャート
        problem_pie = self._generate_problem_type_pie_chart()
        
        # 時間帯別の問題タイプ積み上げバーチャート
        problem_stacked = self._generate_problem_type_stacked_bar(temporal_scores)
        
        return {
            "temporal_distribution": temporal_chart,
            "spatial_heatmap": spatial_heatmap,
            "problem_type_pie": problem_pie,
            "problem_type_stacked": problem_stacked
    
    def _generate_temporal_problem_distribution(self, temporal_scores: List[Dict[str, Any]]) -> go.Figure:
        """
"""        時間帯別の問題分布チャートを生成"""

        Parameters
        ----------
        temporal_scores : List[Dict[str, Any]]
"""            時間帯別のスコア情報"""

        Returns
        -------
        go.Figure
"""            時間帯別問題分布チャート"""
        """
        if not temporal_scores:
            fig = go.Figure()
            fig.update_layout(
"""title="時間帯別の問題分布 (データなし)","""
                height=400
            )
            return fig
        
        # 時間順にソート
        temporal_scores.sort(key=lambda x: x["start_time"])
        
        # データ準備
        labels = [score["label"] for score in temporal_scores]
        problem_counts = [score["problem_count"] for score in temporal_scores]
        problem_percentages = [score["problem_percentage"] for score in temporal_scores]
        
        # チャート作成
        fig = go.Figure([
            go.Bar(
                x=labels,
                y=problem_counts,
"""name="問題数","""
                marker_color="indianred"
            ),
            go.Scatter(
                x=labels,
                y=problem_percentages,
"""name="問題率 (%)","""
                marker=dict(color="royalblue"),
                mode="lines+markers",
                yaxis="y2"
            )
        ])
        
        # レイアウト設定
        fig.update_layout(
"""title="時間帯別の問題分布","""
"""xaxis=dict(title="時間帯"),"""
            yaxis=dict(
"""title="問題数","""
                side="left"
            ),
            yaxis2=dict(
"""title="問題率 (%)","""
                side="right",
                overlaying="y",
                tickformat=".1f",
# # #                 range=[0, max(problem_percentages) * 1.1] if problem_percentages else [0, 100]
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
            ),
            legend=dict(x=0.01, y=0.99),
            height=400,
            margin=dict(t=50, b=50, l=50, r=50),
            hovermode="x unified"
        )
        
        # X軸ラベルを斜めに表示
        fig.update_xaxes(tickangle=-45)
        
        return fig
    
    def _generate_spatial_problem_heatmap(self, spatial_scores: List[Dict[str, Any]]) -> go.Figure:
        """
"""        空間的な問題分布のヒートマップを生成"""

        Parameters
        ----------
        spatial_scores : List[Dict[str, Any]]
"""            空間グリッド別のスコア情報"""

        Returns
        -------
        go.Figure
"""            空間的問題分布ヒートマップ"""
        """
        if not spatial_scores:
            fig = go.Figure()
            fig.update_layout(
"""title="空間的な問題分布 (データなし)","""
                height=500
            )
            return fig
        
        # データフレームに変換
        grid_data = []
        for grid in spatial_scores:
            center_lat, center_lon = grid["center"]
            grid_data.append({
                "lat": center_lat,
                "lon": center_lon,
                "problem_count": grid["problem_count"],
                "problem_percentage": grid["problem_percentage"],
                "total_count": grid["total_count"]
            })
        
        df = pd.DataFrame(grid_data)
        
        # ヒートマップ作成
        fig = px.density_mapbox(
            df,
            lat="lat",
            lon="lon",
            z="problem_percentage",
            radius=20,
            center={"lat": df["lat"].mean(), "lon": df["lon"].mean()},
            zoom=11,
            mapbox_style="open-street-map",
            color_continuous_scale=[
                [0, "green"],
                [0.5, "yellow"],
                [1, "red"]
            ],
"""labels={"problem_percentage": "問題率 (%)"},"""
            hover_name=None,
            hover_data={
                "lat": False,
                "lon": False,
                "problem_count": True,
                "total_count": True,
                "problem_percentage": ":.1f"
        )
        
        # レイアウト設定
        fig.update_layout(
"""title="空間的な問題分布ヒートマップ","""
            height=500,
            margin=dict(t=50, b=0, l=0, r=0),
            coloraxis_colorbar=dict(
"""title="問題率 (%)","""
                ticksuffix="%"
            )
        )
        
        return fig
    
    def _generate_problem_type_pie_chart(self) -> go.Figure:
        """
"""        問題タイプ別の円グラフを生成"""

        Returns
        -------
        go.Figure
"""            問題タイプ別円グラフ"""
        """
        # 問題タイプごとの件数
        problem_counts = {
            "missing_data": len(self.quality_metrics.problematic_indices["missing_data"]),
            "out_of_range": len(self.quality_metrics.problematic_indices["out_of_range"]),
            "duplicates": len(self.quality_metrics.problematic_indices["duplicates"]),
            "spatial_anomalies": len(self.quality_metrics.problematic_indices["spatial_anomalies"]),
            "temporal_anomalies": len(self.quality_metrics.problematic_indices["temporal_anomalies"])
        
        # 問題タイプの日本語名
        problem_type_names = {
""""missing_data": "欠損値","""
""""out_of_range": "範囲外の値","""
""""duplicates": "重複データ","""
""""spatial_anomalies": "空間的異常","""
""""temporal_anomalies": "時間的異常""""
        
        # 色の設定
        colors = {
            "missing_data": "blue",
            "out_of_range": "red",
            "duplicates": "green",
            "spatial_anomalies": "purple",
            "temporal_anomalies": "orange"
        
        # データ準備
        labels = []
        values = []
        color_list = []
        
        for problem_type, count in problem_counts.items():
            if count > 0:
                labels.append(problem_type_names[problem_type])
                values.append(count)
                color_list.append(colors[problem_type])
        
        if not values:
            # 問題がない場合
            fig = go.Figure()
            fig.update_layout(
"""title="問題タイプの分布 (問題なし)","""
                height=400
            )
            return fig
        
        # 円グラフ作成
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=color_list,
            textinfo="label+percent",
            hoverinfo="label+value+percent",
            textposition="outside",
            insidetextorientation="radial"
        )])
        
        # レイアウト設定
        fig.update_layout(
"""title="問題タイプの分布","""
            height=400,
            margin=dict(t=50, b=50, l=20, r=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=0,
                xanchor="center",
                x=0.5
            )
        )
        
        return fig
    
    def _generate_problem_type_stacked_bar(self, temporal_scores: List[Dict[str, Any]]) -> go.Figure:
        """
"""        時間帯別の問題タイプ積み上げバーチャートを生成"""

        Parameters
        ----------
        temporal_scores : List[Dict[str, Any]]
"""            時間帯別のスコア情報"""

        Returns
        -------
        go.Figure
"""            問題タイプ別積み上げバーチャート"""
        """
        if not temporal_scores or "problem_types" not in temporal_scores[0]:
            fig = go.Figure()
            fig.update_layout(
"""title="時間帯別の問題タイプ (データなし)","""
                height=400
            )
            return fig
        
        # 時間順にソート
        temporal_scores.sort(key=lambda x: x["start_time"])
        
        # データ準備
        labels = [score["label"] for score in temporal_scores]
        
        # 問題タイプのキーを取得
        problem_type_keys = temporal_scores[0]["problem_types"].keys()
        
        # 問題タイプごとのデータを抽出
        problem_types_data = {}
        for key in problem_type_keys:
            problem_types_data[key] = [score["problem_types"].get(key, 0) for score in temporal_scores]
        
        # 問題タイプの日本語名と色
        problem_type_names = {
""""missing_data": "欠損値","""
""""out_of_range": "範囲外の値","""
""""duplicates": "重複データ","""
""""spatial_anomalies": "空間的異常","""
""""temporal_anomalies": "時間的異常""""
        
        colors = {
            "missing_data": "blue",
            "out_of_range": "red",
            "duplicates": "green",
            "spatial_anomalies": "purple",
            "temporal_anomalies": "orange"
        
        # チャート作成
        fig = go.Figure()
        
        # 各問題タイプのデータを追加
        for key in problem_type_keys:
            if sum(problem_types_data[key]) > 0:
                fig.add_trace(go.Bar(
                    x=labels,
                    y=problem_types_data[key],
# # #                     name=problem_type_names.get(key, key),
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
                    marker_color=colors.get(key, "gray"),
                    hoverinfo="text",
                    hovertext=[
"""f"時間帯: {labels[i]}<br>{problem_type_names.get(key, key)}: {problem_types_data[key][i]}件""""
                        for i in range(len(labels))
                    ]
                ))
        
        # レイアウト設定
        fig.update_layout(
"""title="時間帯別の問題タイプ分布","""
"""xaxis=dict(title="時間帯"),"""
"""yaxis=dict(title="問題数"),"""
            barmode="stack",
            height=400,
            margin=dict(t=50, b=50, l=50, r=20),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="x unified"
        )
        
        # X軸ラベルを斜めに表示
        fig.update_xaxes(tickangle=-45)
        
        return fig
    
    def generate_quality_score_card(self) -> Dict[str, Any]:
        """
"""        品質スコアのカード形式表示データを生成"""

        Returns
        -------
        Dict[str, Any]
"""            カード表示用のデータ"""
        """
        # 品質スコアを取得
        quality_scores = self.quality_metrics.calculate_quality_scores()
        
        # カテゴリ別スコアを取得
        category_scores = self.quality_metrics.calculate_category_quality_scores()
        
        # カテゴリの日本語名
        category_names = {
""""completeness": "完全性","""
""""accuracy": "正確性","""
""""consistency": "一貫性""""
        
        # カード形式のデータを構築
        cards = [{
""""title": "総合品質スコア","""
            "value": quality_scores["total"],
""""description": "データ全体の品質評価","""
            "color": self._get_score_color(quality_scores["total"]),
            "impact_level": self._get_impact_level_name(self._determine_impact_level(quality_scores["total"]))
        }]
        
        # カテゴリ別のカード
        for category, score in quality_scores.items():
            if category != "total":
# # #                 cat_details = category_scores.get(category, {})
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
 # AUTO-COMMENTED: キーワード引数の後に位置引数があります
                cards.append({
""""title": f"{category_names.get(category, category)}スコア","""
                    "value": score,
                    "description": self._get_category_description(category),
                    "color": self._get_score_color(score),
                    "impact_level": self._get_impact_level_name(cat_details.get("impact_level", "low")),
                    "issues": cat_details.get("issues", 0),
                    "details": cat_details.get("details", {})
                })
        
        return {
            "total_score": quality_scores["total"],
            "cards": cards
    
    def _get_score_color(self, score: float) -> str:
        """
"""        スコアに応じた色を返す"""

        Parameters
        ----------
        score : float
"""            品質スコア（0-100）"""

        Returns
        -------
        str
"""            対応する色のHEXコード"""
        """
        if score >= 90:
"""return "#27AE60"  # 濃い緑"""
        elif score >= 75:
"""return "#2ECC71"  # 緑"""
        elif score >= 50:
"""return "#F1C40F"  # 黄色"""
        elif score >= 25:
"""return "#E67E22"  # オレンジ"""
        else:
"""return "#E74C3C"  # 赤"""
    
    def _determine_impact_level(self, score: float) -> str:
        """
"""        品質スコアから影響レベルを決定する"""

        Parameters
        ----------
        score : float
"""            品質スコア (0-100)"""

        Returns
        -------
        str
"""            影響レベル"""
        """
        if score >= 90:
"""return "low"       # 低影響"""
        elif score >= 75:
"""return "medium"    # 中程度の影響"""
        elif score >= 50:
"""return "high"      # 高影響"""
        else:
"""return "critical"  # 重大な影響"""
    
    def _get_impact_level_name(self, impact_level: str) -> str:
        """
"""        影響レベルの日本語名を取得"""

        Parameters
        ----------
        impact_level : str
"""            影響レベル"""

        Returns
        -------
        str
"""            日本語の影響レベル名"""
        """
        impact_names = {
""""low": "低影響","""
""""medium": "中程度の影響","""
""""high": "高影響","""
""""critical": "重大な影響""""
        return impact_names.get(impact_level, impact_level)
    
    def _get_category_description(self, category: str) -> str:
        """
"""        カテゴリの説明を取得"""

        Parameters
        ----------
        category : str
"""            カテゴリ名"""

        Returns
        -------
        str
"""            カテゴリの説明"""
        """
        descriptions = {
""""completeness": "欠損値や必須項目の充足度","""
""""accuracy": "値の範囲や形式の正確さ","""
""""consistency": "時間的・空間的な整合性""""
        return descriptions.get(category, "")

"""