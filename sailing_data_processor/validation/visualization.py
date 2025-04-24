"""
sailing_data_processor.validation.visualization

データ検証結果の視覚化を行うモジュール
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
        """
        時間帯別の品質分布チャートを生成。
        
        時間帯ごとの品質スコアをグラフ化し、時間的な品質の変動を視覚化します。
        各時間帯のデータ量と問題発生率も表示します。
        
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
        
        # 時間順にソート
        temporal_scores.sort(key=lambda x: x["start_time"])
        
        # チャートデータの準備
        labels = [score["label"] for score in temporal_scores]
        quality_scores = [score["quality_score"] for score in temporal_scores]
        problem_counts = [score["problem_count"] for score in temporal_scores]
        total_counts = [score["total_count"] for score in temporal_scores]
        problem_percentages = [score["problem_percentage"] for score in temporal_scores]
        
        # グラフの作成（サブプロット2つ）
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=("時間帯別品質スコア", "時間帯別データ量とエラー率"),
            specs=[
                [{"type": "bar"}],
                [{"type": "scatter"}]
            ]
        )
        
        # 品質スコアのバーチャート
        bar_colors = [self._get_score_color(score) for score in quality_scores]
        
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
        
        # レイアウト設定
        fig.update_layout(
            height=600,
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
        
        # X軸の設定（斜めに表示）
        fig.update_xaxes(
            tickangle=-45,
            row=2, col=1
        )
        
        return fig
        
    def generate_heatmap_data(self) -> Dict[str, Any]:
        """
        ヒートマップデータの生成
        
        Returns
        -------
        Dict[str, Any]
            ヒートマップ用のデータ
        """
        # 問題のあるレコードのインデックス
        problem_indices = self.quality_metrics.problematic_indices["all"]
        
        # データが少ない場合や問題がない場合はスキップ
        if len(self.data) < 10 or not problem_indices:
            return {"has_data": False}
        
        # 位置情報カラムがない場合もスキップ
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            return {"has_data": False}
        
        try:
            # 位置の範囲を取得
            min_lat = self.data["latitude"].min()
            max_lat = self.data["latitude"].max()
            min_lon = self.data["longitude"].min()
            max_lon = self.data["longitude"].max()
            
            if (pd.isna(min_lat) or pd.isna(max_lat) or 
                pd.isna(min_lon) or pd.isna(max_lon)):
                return {"has_data": False}
            
            # グリッドの解像度を設定（より細かく）
            lat_bins = 20
            lon_bins = 20
            
            # 範囲が狭すぎる場合はデフォルトの範囲を設定
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
            
            # グリッドデータを初期化
            lat_centers = [min_lat + lat_step * (i + 0.5) for i in range(lat_bins)]
            lon_centers = [min_lon + lon_step * (i + 0.5) for i in range(lon_bins)]
            
            # ヒートマップデータを準備
            problem_density = np.zeros((lat_bins, lon_bins))
            record_counts = np.zeros((lat_bins, lon_bins))
            
            # データポイントをグリッドに割り当て
            for idx, row in self.data.iterrows():
                lat, lon = row["latitude"], row["longitude"]
                
                # 範囲外のポイントはスキップ
                if (lat < min_lat or lat > max_lat or lon < min_lon or lon > max_lon):
                    continue
                
                # グリッドインデックスを計算
                lat_idx = min(lat_bins - 1, int((lat - min_lat) / lat_step))
                lon_idx = min(lon_bins - 1, int((lon - min_lon) / lon_step))
                
                # レコードカウントを増やす
                record_counts[lat_idx, lon_idx] += 1
                
                # 問題のあるレコードなら問題カウントも増やす
                if idx in problem_indices:
                    problem_density[lat_idx, lon_idx] += 1
            
            # 問題率を計算
            problem_rate = np.zeros((lat_bins, lon_bins))
            for i in range(lat_bins):
                for j in range(lon_bins):
                    if record_counts[i, j] > 0:
                        problem_rate[i, j] = problem_density[i, j] / record_counts[i, j]
            
            # ヒートマップデータを構築
            heatmap_data = []
            for i in range(lat_bins):
                for j in range(lon_bins):
                    if record_counts[i, j] > 0:
                        heatmap_data.append({
                            "lat": lat_centers[i],
                            "lon": lon_centers[j],
                            "problem_count": int(problem_density[i, j]),
                            "record_count": int(record_counts[i, j]),
                            "problem_rate": float(problem_rate[i, j])
                        })
            
            return {
                "has_data": True,
                "heatmap_data": heatmap_data,
                "lat_range": (min_lat, max_lat),
                "lon_range": (min_lon, max_lon)
        
        except Exception as e:
            return {
                "has_data": False,
                "error": str(e)
    
    def generate_distribution_charts(self) -> Dict[str, Any]:
        """
        分布チャートデータの生成
        
        Returns
        -------
        Dict[str, Any]
            分布チャート用のデータ
        """
        # 問題カテゴリとその日本語名
        categories = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        
        # 問題タイプ別の件数
        problem_counts = {
            cat_name: len(self.quality_metrics.problematic_indices[cat_key])
            for cat_key, cat_name in categories.items()
        
        # 重要度別の件数
        severity_counts = self.quality_metrics.get_problem_severity_distribution()
        
        # 円グラフデータを準備
        pie_data = {
            "problem_types": {
                "labels": list(problem_counts.keys()),
                "values": list(problem_counts.values())
            },
            "severity": {
                "labels": ["エラー", "警告", "情報"],
                "values": [severity_counts["error"], severity_counts["warning"], severity_counts["info"]]
        
        # 問題の分布（時間的）
        temporal_distribution = self.quality_metrics.problem_distribution["temporal"]
        
        # 問題の分布（空間的）
        spatial_distribution = self.quality_metrics.problem_distribution["spatial"]
        
        return {
            "pie_data": pie_data,
            "temporal_distribution": temporal_distribution,
            "spatial_distribution": spatial_distribution
    
    def generate_timeline_markers(self) -> Dict[str, Any]:
        """
        タイムラインマーカーデータの生成
        
        Returns
        -------
        Dict[str, Any]
            タイムライン用のマーカーデータ
        """
        # タイムスタンプカラムがない場合はスキップ
        if "timestamp" not in self.data.columns:
            return {"has_data": False}
        
        problem_indices = self.quality_metrics.problematic_indices["all"]
        
        if not problem_indices:
            return {"has_data": False}
        
        try:
            # 問題タイプごとのマーカーを作成
            markers = []
            
            # 問題タイプとマーカー情報のマッピング
            problem_types = {
                "missing_data": {"color": "blue", "symbol": "circle", "name": "欠損値"},
                "out_of_range": {"color": "red", "symbol": "triangle-up", "name": "範囲外の値"},
                "duplicates": {"color": "green", "symbol": "square", "name": "重複"},
                "spatial_anomalies": {"color": "purple", "symbol": "diamond", "name": "空間的異常"},
                "temporal_anomalies": {"color": "orange", "symbol": "star", "name": "時間的異常"}
            
            # 各問題タイプのマーカーを収集
            for problem_type, info in problem_types.items():
                indices = self.quality_metrics.problematic_indices[problem_type]
                if not indices:
                    continue
                
                # 問題タイプのマーカーを作成
                for idx in indices:
                    if idx < len(self.data):
                        row = self.data.iloc[idx]
                        
                        if pd.notna(row.get("timestamp")):
                            markers.append({
                                "timestamp": row["timestamp"],
                                "type": problem_type,
                                "type_name": info["name"],
                                "color": info["color"],
                                "symbol": info["symbol"],
                                "index": idx
                            })
            
            # 時間順にソート
            markers.sort(key=lambda x: x["timestamp"])
            
            return {
                "has_data": True,
                "markers": markers,
                "problem_types": problem_types
        
        except Exception as e:
            return {
                "has_data": False,
                "error": str(e)
    
    def generate_detailed_report(self) -> Dict[str, Any]:
        """
        詳細レポートの生成
        
        Returns
        -------
        Dict[str, Any]
            詳細レポートデータ
        """
        quality_summary = self.quality_metrics.get_quality_summary()
        
        # 問題のあるレコードの詳細
        problem_records = []
        
        for problem_type, indices in self.quality_metrics.problematic_indices.items():
            if problem_type != "all" and indices:
                for idx in indices[:100]:  # 最初の100個まで
                    if idx < len(self.data):
                        row = self.data.iloc[idx]
                        
                        record = {
                            "index": idx,
                            "problem_type": problem_type,
                            "timestamp": row.get("timestamp", None),
                            "latitude": row.get("latitude", None),
                            "longitude": row.get("longitude", None)
                        
                        problem_records.append(record)
        
        # 問題のあるカラムの詳細
        problematic_columns = self.quality_metrics.get_problematic_columns()
        
        # 修正可能性の評価
        fixability = quality_summary["fixable_counts"]
        
        # レポートデータの構築
        return {
            "quality_scores": self.quality_metrics.quality_scores,
            "category_scores": self.quality_metrics.category_scores,
            "issue_counts": quality_summary["issue_counts"],
            "severity_counts": quality_summary["severity_counts"],
            "fixability": fixability,
            "problem_records": problem_records,
            "problematic_columns": problematic_columns,
            "generated_at": datetime.now().isoformat()
    
    def generate_quality_score_chart(self) -> go.Figure:
        """
        品質スコアのゲージチャートを生成
        
        Returns
        -------
        go.Figure
            Plotlyのゲージチャート
        """
        # 総合スコアのゲージチャート
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=self.quality_metrics.quality_scores["total"],
            title={"text": "データ品質スコア"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 50], "color": "red"},
                    {"range": [50, 75], "color": "orange"},
                    {"range": [75, 90], "color": "yellow"},
                    {"range": [90, 100], "color": "green"}
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": self.quality_metrics.quality_scores["total"]
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(t=30, b=30, l=30, r=30)
        )
        
        return fig
    
    def generate_category_scores_chart(self) -> go.Figure:
        """
        カテゴリ別スコアのバーチャートを生成
        
        Returns
        -------
        go.Figure
            Plotlyのバーチャート
        """
        # カテゴリ別スコアのバーチャート
        categories = ["completeness", "accuracy", "consistency"]
        values = [self.quality_metrics.quality_scores[cat] for cat in categories]
        
        # カテゴリ名の日本語対応
        category_names = {
            "completeness": "完全性",
            "accuracy": "正確性",
            "consistency": "一貫性"
        
        display_categories = [category_names[cat] for cat in categories]
        
        fig = go.Figure(data=[
            go.Bar(
                x=display_categories,
                y=values,
                marker_color=['#1f77b4', '#ff7f0e', '#2ca02c']
            )
        ])
        
        fig.update_layout(
            title="カテゴリ別スコア",
            yaxis_range=[0, 100],
            height=250,
            margin=dict(t=50, b=30, l=30, r=30),
        )
        
        # 注釈の追加
        annotations = []
        for i, cat in enumerate(categories):
            annotations.append(dict(
                x=i,
                y=values[i] + 5,  # スコアの上に表示
                text=f"{values[i]:.1f}",
                showarrow=False,
                font=dict(size=12)
            ))
        
        fig.update_layout(annotations=annotations)
        
        return fig
    
    def generate_problem_distribution_chart(self) -> go.Figure:
        """
        問題分布の円グラフを生成
        
        Returns
        -------
        go.Figure
            Plotlyの円グラフ
        """
        # 問題タイプ別の件数
        problem_counts = {
            "欠損値": len(self.quality_metrics.problematic_indices["missing_data"]),
            "範囲外の値": len(self.quality_metrics.problematic_indices["out_of_range"]),
            "重複": len(self.quality_metrics.problematic_indices["duplicates"]),
            "空間的異常": len(self.quality_metrics.problematic_indices["spatial_anomalies"]),
            "時間的異常": len(self.quality_metrics.problematic_indices["temporal_anomalies"])
        
        # 値が0のカテゴリを除外
        problem_counts = {k: v for k, v in problem_counts.items() if v > 0}
        
        if not problem_counts:
            # 問題がない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="問題タイプの分布 (問題なし)",
                height=300,
                margin=dict(t=50, b=30, l=30, r=30)
            )
            return fig
        
        # 問題タイプの円グラフ
        fig = go.Figure(data=[
            go.Pie(
                labels=list(problem_counts.keys()),
                values=list(problem_counts.values()),
                hole=.4,
                marker_colors=['blue', 'red', 'green', 'purple', 'orange']
            )
        ])
        
        fig.update_layout(
            title="問題タイプの分布",
            height=300,
            margin=dict(t=50, b=30, l=30, r=30)
        )
        
        return fig
    
    def generate_problem_heatmap(self) -> go.Figure:
        """
        問題の密度ヒートマップを生成
        
        Returns
        -------
        go.Figure
            Plotlyのヒートマップ
        """
        heatmap_data = self.generate_heatmap_data()
        
        if not heatmap_data["has_data"]:
            # データがない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="問題密度ヒートマップ (データなし)",
                height=400,
                margin=dict(t=50, b=30, l=30, r=30)
            )
            return fig
        
        # マップ作成
        heatmap_points = heatmap_data["heatmap_data"]
        
        fig = px.density_mapbox(
            pd.DataFrame(heatmap_points),
            lat="lat",
            lon="lon",
            z="problem_rate",
            radius=10,
            center={"lat": (heatmap_data["lat_range"][0] + heatmap_data["lat_range"][1]) / 2,
                   "lon": (heatmap_data["lon_range"][0] + heatmap_data["lon_range"][1]) / 2},
            zoom=10,
            mapbox_style="open-street-map",
            color_continuous_scale="Viridis",
            opacity=0.7,
            hover_data=["problem_count", "record_count", "problem_rate"]
        )
        
        fig.update_layout(
            title="問題密度ヒートマップ",
            height=400,
            margin=dict(t=50, b=0, l=0, r=0),
            coloraxis_colorbar=dict(
                title="問題率",
                tickformat=".0%"
            )
        )
        
        return fig
    
    def generate_timeline_chart(self) -> go.Figure:
        """
        問題のタイムラインチャートを生成
        
        Returns
        -------
        go.Figure
            Plotlyのタイムラインチャート
        """
        timeline_data = self.generate_timeline_markers()
        
        if not timeline_data["has_data"]:
            # データがない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="問題のタイムライン (データなし)",
                height=300,
                margin=dict(t=50, b=30, l=30, r=30)
            )
            return fig
        
        markers = timeline_data["markers"]
        problem_types = timeline_data["problem_types"]
        
        # 時間順にソート
        markers.sort(key=lambda x: x["timestamp"])
        
        # 問題タイプごとにグループ化
        grouped_markers = {}
        for marker in markers:
            problem_type = marker["type"]
            if problem_type not in grouped_markers:
                grouped_markers[problem_type] = []
            grouped_markers[problem_type].append(marker)
        
        # タイムラインチャートの作成
        fig = go.Figure()
        
        # 各問題タイプのマーカーを追加
        for problem_type, type_markers in grouped_markers.items():
            info = problem_types[problem_type]
            timestamps = [m["timestamp"] for m in type_markers]
            y_values = [1] * len(timestamps)  # 同じ高さにプロット
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=y_values,
                mode="markers",
                name=info["name"],
                marker=dict(
                    color=info["color"],
                    symbol=info["symbol"],
                    size=10
                ),
                hoverinfo="x+text",
                hovertext=[f"インデックス: {m['index']}, 種類: {m['type_name']}" for m in type_markers]
            ))
        
        # レイアウトの設定
        fig.update_layout(
            title="問題のタイムライン",
            xaxis_title="時間",
            yaxis_visible=False,
            showlegend=True,
            height=300,
            margin=dict(t=50, b=30, l=30, r=30)
        )
        
        return fig
    
    def generate_all_visualizations(self) -> Dict[str, go.Figure]:
        """
        全ての視覚化を生成
        
        Returns
        -------
        Dict[str, go.Figure]
            視覚化の辞書（キーは視覚化の種類）
        """
        visualizations = {
            "quality_score": self.generate_quality_score_chart(),
            "category_scores": self.generate_category_scores_chart(),
            "problem_distribution": self.generate_problem_distribution_chart(),
            "problem_heatmap": self.generate_problem_heatmap(),
            "timeline": self.generate_timeline_chart(),
            "problem_type_detail": self.generate_problem_type_detail_chart(),
            "problem_severity_chart": self.generate_problem_severity_chart(),
            "data_quality_map": self.generate_data_quality_map(),
            "hourly_quality_chart": self.generate_hourly_quality_chart(),
            "spatial_quality_grid": self.generate_spatial_quality_grid(),
            "track_quality_chart": self.generate_track_quality_chart(),
            "speed_profile_chart": self.generate_speed_profile_chart()
        
        return visualizations
        
    def generate_track_quality_chart(self) -> go.Figure:
        """
        トラック品質の視覚化チャートを生成
        
        Returns
        -------
        go.Figure
            トラック品質のチャート
        """
        # 拡張空間メトリクスを取得
        extended_metrics = self.quality_metrics.get_extended_spatial_metrics()
        
        if not extended_metrics.get("has_data", False) or "track_quality" not in extended_metrics:
            # データがない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="トラック品質分析 (データなし)",
                height=400,
                margin=dict(t=50, b=30, l=30, r=30)
            )
            return fig
            
        track_quality = extended_metrics["track_quality"]
        
        if not track_quality.get("has_data", False):
            # トラック品質データがない場合も空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title=f"トラック品質分析 ({track_quality.get('reason', 'データなし')})",
                height=400,
                margin=dict(t=50, b=30, l=30, r=30)
            )
            return fig
        
        # トラック品質スコアのゲージチャート
        track_stats = track_quality.get("track_stats", {})
        track_quality_score = track_quality.get("track_quality_score", 0)
        
        # スピードと方向の一貫性を示すゲージチャートを作成
        fig = go.Figure()
        
        # 総合品質スコアのゲージ
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=track_quality_score,
            title={"text": "トラック総合品質"},
            domain={"row": 0, "column": 0},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "darkblue"},
                "steps": [
                    {"range": [0, 50], "color": "red"},
                    {"range": [50, 75], "color": "orange"},
                    {"range": [75, 90], "color": "yellow"},
                    {"range": [90, 100], "color": "green"}
                ],
                "threshold": {
                    "line": {"color": "black", "width": 4},
                    "thickness": 0.75,
                    "value": track_quality_score
        ))
        
        # 速度の一貫性スコアを追加
        if "speed" in track_stats and "consistency" in track_stats["speed"]:
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=track_stats["speed"]["consistency"],
                title={"text": "速度一貫性"},
                domain={"row": 0, "column": 1},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 50], "color": "red"},
                        {"range": [50, 75], "color": "orange"},
                        {"range": [75, 90], "color": "yellow"},
                        {"range": [90, 100], "color": "green"}
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 4},
                        "thickness": 0.75,
                        "value": track_stats["speed"]["consistency"]
            ))
        
        # 進行方向の一貫性スコアを追加
        if "turn_rate" in track_stats and "consistency" in track_stats["turn_rate"]:
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=track_stats["turn_rate"]["consistency"],
                title={"text": "方向一貫性"},
                domain={"row": 0, "column": 2},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 50], "color": "red"},
                        {"range": [50, 75], "color": "orange"},
                        {"range": [75, 90], "color": "yellow"},
                        {"range": [90, 100], "color": "green"}
                    ],
                    "threshold": {
                        "line": {"color": "black", "width": 4},
                        "thickness": 0.75,
                        "value": track_stats["turn_rate"]["consistency"]
            ))
        
        # レイアウト設定
        fig.update_layout(
            title="トラック品質分析",
            grid={"rows": 1, "columns": 3, "pattern": "independent"},
            height=250,
            margin=dict(t=50, b=30, l=30, r=30)
        )
        
        return fig
    
    def generate_speed_profile_chart(self) -> go.Figure:
        """
        速度プロファイルの視覚化チャートを生成
        
        Returns
        -------
        go.Figure
            速度プロファイルのチャート
        """
        # 拡張空間メトリクスを取得
        extended_metrics = self.quality_metrics.get_extended_spatial_metrics()
        
        if not extended_metrics.get("has_data", False) or "track_quality" not in extended_metrics:
            # データがない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="速度プロファイル分析 (データなし)",
                height=400,
                margin=dict(t=50, b=30, l=30, r=30)
            )
            return fig
            
        track_quality = extended_metrics["track_quality"]
        
        if not track_quality.get("has_data", False) or "track_segments" not in track_quality:
            # トラックセグメントがない場合も空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="速度プロファイル分析 (セグメントデータなし)",
                height=400,
                margin=dict(t=50, b=30, l=30, r=30)
            )
            return fig
        
        # トラックセグメントデータを取得
        segments = track_quality["track_segments"]
        track_stats = track_quality.get("track_stats", {})
        
        if not segments:
            fig = go.Figure()
            fig.update_layout(title="速度プロファイル (データなし)")
            return fig
        
        # セグメントデータをDataFrameに変換
        import pandas as pd
        segments_df = pd.DataFrame(segments)
        
        # シーケンス番号の追加
        segments_df["sequence"] = range(len(segments_df))
        
        # サブプロットで速度と方向のプロファイルを作成
        from plotly.subplots import make_subplots
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("速度プロファイル", "進行方向変化"),
            shared_xaxes=True,
            vertical_spacing=0.1
        )
        
        # 速度チャート
        fig.add_trace(
            go.Scatter(
                x=segments_df["sequence"],
                y=segments_df["speed_knots"],
                mode="lines+markers",
                name="速度 (ノット)",
                line=dict(color="blue"),
                hovertemplate="セグメント: %{x}<br>速度: %{y:.2f} ノット<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 問題のあるセグメントをハイライト
        if "problematic_segments" in track_stats:
            problem_segments = track_stats["problematic_segments"]
            
            for segment in problem_segments:
                if "segment_idx" in segment and segment["segment_idx"] < len(segments_df):
                    idx = segment["segment_idx"]
                    issues = segment.get("issues", [])
                    issue_text = ", ".join(issues)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=[idx],
                            y=[segments_df.iloc[idx]["speed_knots"]],
                            mode="markers",
                            marker=dict(
                                size=12,
                                color="red",
                                symbol="triangle-up"
                            ),
                            name=f"問題: {issue_text}",
                            hoverinfo="text",
                            hovertext=f"問題: {issue_text}",
                            showlegend=False
                        ),
                        row=1, col=1
                    )
        
        # 速度基本統計線
        if "speed" in track_stats:
            speed_stats = track_stats["speed"]
            mean_speed = speed_stats.get("mean")
            std_speed = speed_stats.get("std")
            
            if mean_speed is not None:
                fig.add_hline(
                    y=mean_speed,
                    line=dict(color="green", dash="dash"),
                    annotation_text="平均速度",
                    annotation_position="bottom right",
                    row=1, col=1
                )
            
            if mean_speed is not None and std_speed is not None:
                fig.add_hline(
                    y=mean_speed + std_speed,
                    line=dict(color="orange", dash="dot"),
                    annotation_text="+1σ",
                    annotation_position="bottom right",
                    row=1, col=1
                )
                
                fig.add_hline(
                    y=max(0, mean_speed - std_speed),
                    line=dict(color="orange", dash="dot"),
                    annotation_text="-1σ",
                    annotation_position="top right",
                    row=1, col=1
                )
        
        # 進行方向チャート
        if "bearing_deg" in segments_df.columns:
            fig.add_trace(
                go.Scatter(
                    x=segments_df["sequence"],
                    y=segments_df["bearing_deg"],
                    mode="lines+markers",
                    name="進行方向 (度)",
                    line=dict(color="purple"),
                    hovertemplate="セグメント: %{x}<br>方向: %{y:.1f}°<extra></extra>"
                ),
                row=2, col=1
            )
        
        # 旋回率チャート（2次Yとして）
        if "turn_rate" in segments_df.columns:
            # NaNではない値のみを抽出
            turn_rate_df = segments_df[segments_df["turn_rate"].notna()]
            
            fig.add_trace(
                go.Scatter(
                    x=turn_rate_df["sequence"],
                    y=turn_rate_df["turn_rate"],
                    mode="lines",
                    name="旋回率 (度/秒)",
                    line=dict(color="red", width=1),
                    hovertemplate="セグメント: %{x}<br>旋回率: %{y:.2f}°/秒<extra></extra>",
                    yaxis="y3"
                ),
                row=2, col=1
            )
            
            # 旋回率の2次Y軸を追加
            fig.update_layout(
                yaxis3=dict(
                    title="旋回率 (度/秒)",
                    titlefont=dict(color="red"),
                    tickfont=dict(color="red"),
                    anchor="x",
                    overlaying="y2",
                    side="right"
                )
            )
        
        # レイアウト設定
        fig.update_layout(
            title="速度・方向プロファイル分析",
            xaxis_title="トラックセグメント",
            xaxis2_title="トラックセグメント",
            yaxis_title="速度 (ノット)",
            yaxis2_title="進行方向 (度)",
            height=500,
            margin=dict(t=50, b=50, l=50, r=50),
            hovermode="closest"
        )
        
        # Y軸設定
        fig.update_yaxes(title_text="速度 (ノット)", row=1, col=1)
        fig.update_yaxes(title_text="進行方向 (度)", range=[0, 360], row=2, col=1)
        
        return fig
        
    def generate_hourly_quality_chart(self) -> go.Figure:
        """
        時間帯別の品質スコアチャートを生成
        
        Returns
        -------
        go.Figure
            時間帯別の品質スコアチャート
        """
        # 拡張された時間的メトリクスを取得
        extended_metrics = self.quality_metrics.get_extended_temporal_metrics()
        
        if not extended_metrics.get("has_data", False):
            # データがない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="時間帯別の品質スコア (データなし)",
                height=350,
                margin=dict(t=50, b=50, l=30, r=30)
            )
            return fig
        
        # 時間帯別の品質スコアを取得
        time_quality_scores = extended_metrics.get("time_quality_scores", [])
        
        if not time_quality_scores:
            # スコアデータがない場合も空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="時間帯別の品質スコア (スコアデータなし)",
                height=350,
                margin=dict(t=50, b=50, l=30, r=30)
            )
            return fig
        
        # 時間帯と品質スコアを抽出
        labels = [score["label"] for score in time_quality_scores]
        quality_scores = [score["quality_score"] for score in time_quality_scores]
        problem_counts = [score["problem_count"] for score in time_quality_scores]
        total_counts = [score["total_count"] for score in time_quality_scores]
        
        # 品質スコアに基づいて色を決定
        colors = []
        for score in quality_scores:
            if score >= 90:
                colors.append('green')
            elif score >= 75:
                colors.append('yellowgreen')
            elif score >= 50:
                colors.append('orange')
            else:
                colors.append('red')
        
        # ホバーテキストを作成
        hover_texts = []
        for i in range(len(labels)):
            hover_texts.append(
                f"時間帯: {labels[i]}<br>" +
                f"品質スコア: {quality_scores[i]:.1f}<br>" +
                f"問題数: {problem_counts[i]}<br>" +
                f"レコード数: {total_counts[i]}<br>" +
                f"問題率: {(problem_counts[i] / total_counts[i] * 100):.1f}%"
            )
        
        # チャートの作成
        fig = go.Figure()
        
        # 品質スコアのバーチャート
        fig.add_trace(go.Bar(
            x=labels,
            y=quality_scores,
            marker_color=colors,
            text=[f"{score:.1f}" for score in quality_scores],
            textposition="auto",
            hovertext=hover_texts,
            hoverinfo="text",
            name="品質スコア"
        ))
        
        # レイアウトの設定
        fig.update_layout(
            title="時間帯別の品質スコア",
            xaxis_title="時間帯",
            yaxis_title="品質スコア (0-100)",
            yaxis_range=[0, 105],  # スケールを0-100+少し余裕を持たせる
            height=350,
            margin=dict(t=50, b=50, l=30, r=30)
        )
        
        return fig
    
    def generate_spatial_quality_grid(self) -> go.Figure:
        """
        空間的な品質スコアグリッドを生成
        
        Returns
        -------
        go.Figure
            空間的な品質スコアのヒートマップ
        """
        # 拡張された空間的メトリクスを取得
        extended_metrics = self.quality_metrics.get_extended_spatial_metrics()
        
        if not extended_metrics.get("has_data", False):
            # データがない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="空間的な品質スコアマップ (データなし)",
                height=400,
                margin=dict(t=50, b=0, l=0, r=0)
            )
            return fig
        
        # グリッド品質スコアを取得
        grid_quality_scores = extended_metrics.get("grid_quality_scores", [])
        
        if not grid_quality_scores:
            # スコアデータがない場合も空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="空間的な品質スコアマップ (スコアデータなし)",
                height=400,
                margin=dict(t=50, b=0, l=0, r=0)
            )
            return fig
        
        # グリッドデータをDataFrameに変換
        grid_df = pd.DataFrame(grid_quality_scores)
        
        # 位置情報の範囲を取得
        spatial_bounds = extended_metrics.get("spatial_bounds", {})
        center_lat = (spatial_bounds.get("min_lat", 0) + spatial_bounds.get("max_lat", 0)) / 2
        center_lon = (spatial_bounds.get("min_lon", 0) + spatial_bounds.get("max_lon", 0)) / 2
        
        # ホバーテキストを作成
        hover_texts = []
        for _, row in grid_df.iterrows():
            center = row["center"]
            hover_texts.append(
                f"中心座標: ({center[0]:.6f}, {center[1]:.6f})<br>" +
                f"品質スコア: {row['quality_score']:.1f}<br>" +
                f"問題数: {row['problem_count']}<br>" +
                f"レコード数: {row['total_count']}<br>" +
                f"問題率: {(row['problem_count'] / row['total_count'] * 100):.1f}%"
            )
        
        # カラースケールの設定
        colorscale = [
            [0, "red"],       # 低品質
            [0.25, "orange"],
            [0.5, "yellow"],
            [0.75, "lightgreen"],
            [1.0, "green"]    # 高品質
        ]
        
        # ヒートマップの作成
        fig = go.Figure()
        
        # 品質スコアのヒートマップレイヤー
        fig.add_trace(go.Scattermapbox(
            lat=[center[0] for center in grid_df["center"]],
            lon=[center[1] for center in grid_df["center"]],
            mode="markers",
            marker=dict(
                size=15,
                color=grid_df["quality_score"],
                colorscale=colorscale,
                cmin=0,
                cmax=100,
                colorbar=dict(
                    title="品質スコア",
                    thickness=15,
                    len=0.8,
                    x=0.95
                ),
                opacity=0.7
            ),
            text=hover_texts,
            hoverinfo="text",
            name="品質スコア"
        ))
        
        # マップのレイアウト設定
        fig.update_layout(
            title="空間的な品質スコアマップ",
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=11
            ),
            height=400,
            margin=dict(t=50, b=0, l=0, r=0)
        )
        
        return fig
    
    def generate_time_of_day_distribution(self) -> go.Figure:
        """
        時間帯別の問題分布チャートを生成
        
        Returns
        -------
        go.Figure
            時間帯別の問題分布のチャート
        """
        # 拡張された時間的メトリクスを取得
        extended_metrics = self.quality_metrics.get_extended_temporal_metrics()
        
        if not extended_metrics.get("has_data", False):
            # データがない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="時間帯別の問題分布 (データなし)",
                height=350,
                margin=dict(t=50, b=50, l=30, r=30)
            )
            return fig
        
        # 問題タイプ別の時間分布を取得
        problem_type_temporal = extended_metrics.get("problem_type_temporal", {})
        
        if not problem_type_temporal:
            # 問題データがない場合も空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="時間帯別の問題分布 (問題データなし)",
                height=350,
                margin=dict(t=50, b=50, l=30, r=30)
            )
            return fig
        
        # 問題タイプごとの時間帯分布
        fig = go.Figure()
        
        # 問題タイプとカラーマッピング
        type_colors = {
            "missing_data": "blue",
            "out_of_range": "red",
            "duplicates": "green",
            "spatial_anomalies": "purple",
            "temporal_anomalies": "orange"
        
        # 問題タイプ名のマッピング
        type_names = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        
        # 各問題タイプの時間帯分布を追加
        for problem_type, distribution in problem_type_temporal.items():
            tod_distribution = distribution.get("time_of_day_distribution", {})
            
            if not tod_distribution.get("periods", []) or not tod_distribution.get("counts", {}):
                continue
            
            # 時間帯と件数を抽出
            periods = [period["name"] for period in tod_distribution["periods"]]
            counts = [tod_distribution["counts"][period] for period in periods]
            
            # 棒グラフを追加
            fig.add_trace(go.Bar(
                x=periods,
                y=counts,
                name=type_names.get(problem_type, problem_type),
                marker_color=type_colors.get(problem_type, "gray")
            ))
        
        # 時間帯の並び順を調整
        period_order = ["早朝", "午前", "午後", "夕方", "夜間", "深夜"]
        
        # レイアウトの設定
        fig.update_layout(
            title="時間帯別の問題分布",
            xaxis_title="時間帯",
            yaxis_title="問題数",
            xaxis=dict(
                categoryorder="array",
                categoryarray=period_order
            ),
            barmode="group",
            height=350,
            margin=dict(t=50, b=50, l=30, r=30)
        )
        
        return fig
        
    def generate_problem_severity_chart(self) -> go.Figure:
        """
        問題の重要度に基づいた円グラフを生成
        
        Returns
        -------
        go.Figure
            問題の重要度分布を示す円グラフ
        """
        # 重要度別の問題数を取得
        severity_counts = self.metrics_calculator.get_problem_severity_distribution()
        labels = ["エラー", "警告", "情報"]
        values = [severity_counts["error"], severity_counts["warning"], severity_counts["info"]]
        colors = ["red", "orange", "blue"]
        
        # 値が0のものを除外
        non_zero = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
        
        if not non_zero:
            # データがない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="重要度別の問題数 (問題なし)",
                height=300
            )
            return fig
        
        # 円グラフの作成
        labels, values, colors = zip(*non_zero)
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=colors
        )])
        
        fig.update_layout(
            title="重要度別の問題数",
            height=300
        )
        
        return fig
    
    def generate_data_quality_map(self) -> go.Figure:
        """
        データ品質の地理的分布マップを生成
        
        Returns
        -------
        go.Figure
            データ品質マップ
        """
        # 位置情報カラムがない場合はスキップ
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            fig = go.Figure()
            fig.update_layout(
                title="データ品質マップ (位置情報なし)",
                height=400
            )
            return fig
        
        try:
            # 各レコードの品質スコアを計算
            record_scores = []
            for i in range(len(self.data)):
                quality_score = self.metrics_calculator.get_record_quality_score(i)
                
                record = self.data.iloc[i]
                lat = record.get("latitude")
                lon = record.get("longitude")
                
                if pd.notna(lat) and pd.notna(lon):
                    record_scores.append({
                        "latitude": lat,
                        "longitude": lon,
                        "score": quality_score["total"],
                        "completeness": quality_score["completeness"],
                        "accuracy": quality_score["accuracy"],
                        "consistency": quality_score["consistency"],
                        "index": i
                    })
            
            if not record_scores:
                fig = go.Figure()
                fig.update_layout(
                    title="データ品質マップ (有効な位置情報なし)",
                    height=400
                )
                return fig
            
            # スコアデータをDataFrameに変換
            df = pd.DataFrame(record_scores)
            
            # カラースケールの設定
            color_scale = [
                [0, "red"],      # 低品質
                [0.4, "orange"],
                [0.7, "yellow"],
                [1.0, "green"]   # 高品質
            ]
            
            # マップの作成
            fig = px.scatter_mapbox(
                df,
                lat="latitude",
                lon="longitude",
                color="score",
                color_continuous_scale=color_scale,
                range_color=[0, 100],
                opacity=0.8,
                zoom=11,
                hover_data={
                    "index": True,
                    "score": ":.1f",
                    "completeness": ":.1f",
                    "accuracy": ":.1f",
                    "consistency": ":.1f"
                },
                labels={
                    "score": "品質スコア",
                    "completeness": "完全性",
                    "accuracy": "正確性",
                    "consistency": "一貫性"
                },
                title="データ品質マップ"
            )
            
            fig.update_layout(
                mapbox_style="open-street-map",
                margin=dict(t=50, b=0, l=0, r=0),
                coloraxis_colorbar=dict(
                    title="品質スコア",
                    ticksuffix="%"
                ),
                height=400
            )
            
            return fig
            
        except Exception as e:
            # エラーが発生した場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title=f"データ品質マップ (エラー: {str(e)})",
                height=400
            )
            return fig
    
    def generate_hierarchy_scores_chart(self) -> go.Figure:
        """
        階層的な品質スコアの可視化チャートを生成
        
        Returns
        -------
        go.Figure
            階層的品質スコアのチャート
        """
        # 階層的品質スコアを取得
        hierarchy_scores = self.quality_metrics.calculate_hierarchical_quality_scores()
        categories = hierarchy_scores["categories"]
        
        # サンバーストチャート用のデータを準備
        labels = ["データ品質"]  # ルートノード
        parents = [""]  # ルートノードの親は空文字
        values = [hierarchy_scores["overall_score"]]  # ルートノードの値は総合スコア
        colors = ["#1f77b4"]  # ルートノードの色
        
        # カテゴリごとのデータを追加
        category_colors = {
            "organizational": "#ff7f0e",  # オレンジ
            "statistical": "#2ca02c",     # 緑
            "structural": "#d62728",      # 赤
            "semantic": "#9467bd"         # 紫
        
        # カテゴリを追加
        for cat_key, category in categories.items():
            cat_name = category["name"]
            cat_score = category["score"]
            
            labels.append(cat_name)
            parents.append("データ品質")
            values.append(cat_score)
            colors.append(category_colors.get(cat_key, "#1f77b4"))
            
            # サブカテゴリを追加
            for subcat_key, subcat in category["subcategories"].items():
                subcat_name = subcat["name"]
                subcat_score = subcat["score"]
                
                labels.append(subcat_name)
                parents.append(cat_name)
                values.append(subcat_score)
                
                # サブカテゴリは同系色の薄い色を使う
                base_color = category_colors.get(cat_key, "#1f77b4")
                colors.append(self._lighten_color(base_color, 0.3))
        
        # サンバーストチャートの作成
        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total",
            marker=dict(
                colors=colors
            ),
            hovertemplate='<b>%{label}</b><br>スコア: %{value:.1f}<br><extra></extra>',
            maxdepth=2  # 最大2階層まで表示
        ))
        
        # レイアウト設定
        fig.update_layout(
            title="階層的データ品質スコア",
            margin=dict(t=50, b=10, l=10, r=10),
            height=500,
            width=700
        )
        
        return fig
    
    def _lighten_color(self, color: str, factor: float = 0.3) -> str:
        """
        色を明るくする関数
        
        Parameters
        ----------
        color : str
            色コード (#rrggbb)
        factor : float, optional
            明るくする係数 (0-1), by default 0.3
            
        Returns
        -------
        str
            明るくした色コード
        """
        # 色コードから RGB 値を取得
        color = color.lstrip('#')
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
        
        # RGB 値を明るくする
        r = min(255, r + int((255 - r) * factor))
        g = min(255, g + int((255 - g) * factor))
        b = min(255, b + int((255 - b) * factor))
        
        # RGB 値を色コードに変換
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def generate_quality_patterns_chart(self) -> go.Figure:
        """
        データ品質パターンの可視化チャートを生成
        
        Returns
        -------
        go.Figure
            データ品質パターンのチャート
        """
        # データ品質パターンを取得
        patterns = self.quality_metrics.get_data_quality_patterns()
        
        # パターンがない場合は空のチャートを返す
        if patterns["pattern_count"] == 0:
            fig = go.Figure()
            fig.update_layout(
                title="データ品質パターン (検出されたパターンなし)",
                height=400
            )
            return fig
        
        # パターン一覧の表を作成
        pattern_rows = []
        for i, pattern in enumerate(patterns["patterns"]):
            pattern_rows.append([
                i + 1,
                pattern["name"],
                pattern["description"],
                pattern["severity"]
            ])
        
        # テーブル用の色設定
        colors = {
            "error": "rgba(220, 20, 60, 0.2)",   # 赤 (薄い)
            "warning": "rgba(255, 165, 0, 0.2)",  # オレンジ (薄い)
            "info": "rgba(65, 105, 225, 0.2)"     # 青 (薄い)
        
        # セルの背景色を設定
        cell_colors = []
        for row in pattern_rows:
            severity = row[3]
            cell_colors.append([
                "white",  # インデックス
                "white",  # パターン名
                "white",  # 説明
                colors.get(severity, "white")  # 重要度
            ])
        
        # テーブルの作成
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=["#", "パターン", "説明", "重要度"],
                fill_color="paleturquoise",
                align="left",
                font=dict(size=14)
            ),
            cells=dict(
                values=[
                    [row[0] for row in pattern_rows],
                    [row[1] for row in pattern_rows],
                    [row[2] for row in pattern_rows],
                    [row[3] for row in pattern_rows]
                ],
                fill_color=cell_colors,
                align="left",
                font=dict(size=13),
                height=30
            )
        )])
        
        # レイアウト設定
        fig.update_layout(
            title="検出されたデータ品質パターン",
            margin=dict(l=10, r=10, t=50, b=10),
            height=max(150 + 40 * len(pattern_rows), 400)
        )
        
        return fig
    
    def generate_data_quality_summary_grid(self) -> Dict[str, go.Figure]:
        """
        データ品質サマリーのグリッド表示用チャートセットを生成
        
        Returns
        -------
        Dict[str, go.Figure]
            グリッド表示用のチャートセット
        """
        charts = {
            "quality_score": self.generate_quality_score_chart(),
            "category_scores": self.generate_category_scores_chart(),
            "problem_distribution": self.generate_problem_distribution_chart(),
            "hierarchy_scores": self.generate_hierarchy_scores_chart(),
            "quality_patterns": self.generate_quality_patterns_chart(),
            "data_quality_map": self.generate_data_quality_map()
        
        return charts
    
    def generate_validation_dashboard_data(self) -> Dict[str, Any]:
        """
        検証ダッシュボード用のデータを生成
        
        Returns
        -------
        Dict[str, Any]
            ダッシュボード用のデータ
        """
        # 品質スコア
        quality_scores = self.quality_metrics.quality_scores
        
        # 問題概要
        problem_summary = {
            "total_records": len(self.data),
            "problematic_records": len(self.quality_metrics.problematic_indices["all"]),
            "problem_percentage": round(len(self.quality_metrics.problematic_indices["all"]) / len(self.data) * 100, 1) if len(self.data) > 0 else 0,
            "problem_counts": {
                "missing_data": len(self.quality_metrics.problematic_indices["missing_data"]),
                "out_of_range": len(self.quality_metrics.problematic_indices["out_of_range"]),
                "duplicates": len(self.quality_metrics.problematic_indices["duplicates"]),
                "spatial_anomalies": len(self.quality_metrics.problematic_indices["spatial_anomalies"]),
                "temporal_anomalies": len(self.quality_metrics.problematic_indices["temporal_anomalies"])
            },
            "severity_counts": self.quality_metrics.get_problem_severity_distribution()
        
        # チャート
        charts = self.generate_data_quality_summary_grid()
        
        # 問題詳細
        problem_details = {
            "by_column": self.quality_metrics.get_problematic_columns(),
            "by_record": self.quality_metrics.get_record_issues()
        
        # 修正推奨
        fix_recommendations = self.quality_metrics.get_fix_recommendations()
        
        # 品質パターン
        quality_patterns = self.quality_metrics.get_data_quality_patterns()
        
        # 拡張メトリクス
        extended_metrics = {
            "temporal": self.quality_metrics.get_extended_temporal_metrics(),
            "spatial": self.quality_metrics.get_extended_spatial_metrics(),
            "hierarchy": self.quality_metrics.calculate_hierarchical_quality_scores()
        
        return {
            "quality_scores": quality_scores,
            "problem_summary": problem_summary,
            "charts": charts,
            "problem_details": problem_details,
            "fix_recommendations": fix_recommendations,
            "quality_patterns": quality_patterns,
            "extended_metrics": extended_metrics,
            "generated_at": datetime.now().isoformat()
        
    def generate_problem_type_detail_chart(self) -> go.Figure:
        """
        問題タイプの詳細チャートを生成
        
        Returns
        -------
        go.Figure
            問題タイプ詳細のチャート
        """
        # 問題タイプの詳細情報を取得
        problem_type_distribution = self.metrics_calculator.problem_distribution.get("problem_type", {})
        
        if not problem_type_distribution.get("has_data", False):
            # データがない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="問題タイプの詳細 (データなし)",
                height=400,
                margin=dict(t=50, b=30, l=30, r=30)
            )
            return fig
        
        # 問題タイプごとの件数
        problem_counts = problem_type_distribution.get("problem_counts", {})
        
        # 日本語の表示名
        type_names = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        
        # 色の定義
        colors = {
            "missing_data": "blue",
            "out_of_range": "red",
            "duplicates": "green",
            "spatial_anomalies": "purple",
            "temporal_anomalies": "orange"
        
        # 表示するデータを準備
        data = []
        for problem_type, count in problem_counts.items():
            if count > 0:
                data.append({
                    "problem_type": type_names.get(problem_type, problem_type),
                    "count": count,
                    "color": colors.get(problem_type, "gray")
                })
        
        if not data:
            # データがない場合は空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title="問題タイプの詳細 (問題なし)",
                height=400,
                margin=dict(t=50, b=30, l=30, r=30)
            )
            return fig
        
        # データフレームに変換
        df = pd.DataFrame(data)
        
        # 棒グラフの作成
        fig = go.Figure()
        
        for i, row in df.iterrows():
            fig.add_trace(go.Bar(
                x=[row["problem_type"]],
                y=[row["count"]],
                name=row["problem_type"],
                marker_color=row["color"],
                text=[row["count"]],
                textposition="auto"
            ))
        
        # 詳細情報のホバーテキスト用データを準備
        problem_details = problem_type_distribution.get("problem_details", {})
        hover_info = []
        
        for problem_type, type_name in type_names.items():
            if problem_type in problem_details:
                detail = problem_details[problem_type]
                hover_text = f"{type_name}<br>"
                
                if "affected_columns" in detail:
                    hover_text += "影響カラム：<br>"
                    for col, info in detail["affected_columns"].items():
                        if isinstance(info, dict) and "count" in info:
                            hover_text += f" - {col}: {info['count']}件<br>"
                        else:
                            hover_text += f" - {col}: {info}件<br>"
                
                if "affected_attributes" in detail:
                    hover_text += "影響属性：<br>"
                    for attr, info in detail["affected_attributes"].items():
                        if isinstance(info, dict):
                            for key, val in info.items():
                                hover_text += f" - {attr}.{key}: {val}<br>"
                        else:
                            hover_text += f" - {attr}: {info}<br>"
                
                hover_info.append(hover_text)
        
        # レイアウト設定
        fig.update_layout(
            title="問題タイプ別の件数",
            xaxis_title="問題タイプ",
            yaxis_title="問題数",
            height=400,
            margin=dict(t=50, b=50, l=30, r=30),
            showlegend=False
        )
        
        # Y軸の最大値を調整
        max_count = max(problem_counts.values()) if problem_counts else 0
        fig.update_yaxes(range=[0, max_count * 1.1])
        
        return fig


class ValidationDashboard:
    """
    検証ダッシュボードクラス
    
    Parameters
    ----------
    validation_results : List[Dict[str, Any]]
        DataValidatorから得られた検証結果
    data : pd.DataFrame
        検証されたデータフレーム
    """
    
    def __init__(self, validation_results: List[Dict[str, Any]], data: pd.DataFrame):
        """
        初期化
        
        Parameters
        ----------
        validation_results : List[Dict[str, Any]]
            DataValidatorから得られた検証結果
        data : pd.DataFrame
            検証されたデータフレーム
        """
        self.validation_results = validation_results
        self.data = data
        
        # メトリクス計算とビジュアライザーを初期化
        self.metrics_calculator = QualityMetricsCalculator(validation_results, data)
        self.visualizer = ValidationVisualizer(self.metrics_calculator, data)
        
        # フィルタリング状態を初期化
        self.active_filters = {
            "problem_types": ["missing_data", "out_of_range", "duplicates", 
                           "spatial_anomalies", "temporal_anomalies"],
            "severity": ["error", "warning", "info"],
            "time_range": None,
            "position": None
    
    def render_overview_section(self) -> Dict[str, Any]:
        """
        概要セクションのレンダリング
        
        Returns
        -------
        Dict[str, Any]
            概要セクションのデータ
        """
        # 品質スコアの概要
        quality_summary = self.metrics_calculator.get_quality_summary()
        
        # 視覚化の取得
        quality_score_chart = self.visualizer.generate_quality_score_chart()
        category_scores_chart = self.visualizer.generate_category_scores_chart()
        
        return {
            "quality_summary": quality_summary,
            "charts": {
                "quality_score": quality_score_chart,
                "category_scores": category_scores_chart
    
    def render_details_section(self) -> Dict[str, Any]:
        """
        詳細セクションのレンダリング
        
        Returns
        -------
        Dict[str, Any]
            詳細セクションのデータ
        """
        # 問題分布の視覚化
        problem_distribution_chart = self.visualizer.generate_problem_distribution_chart()
        problem_heatmap = self.visualizer.generate_problem_heatmap()
        timeline_chart = self.visualizer.generate_timeline_chart()
        
        # 詳細レポートの取得
        detailed_report = self.visualizer.generate_detailed_report()
        
        # 問題レコードの表形式データ
        problem_records_df = pd.DataFrame(detailed_report["problem_records"])
        
        return {
            "charts": {
                "problem_distribution": problem_distribution_chart,
                "problem_heatmap": problem_heatmap,
                "timeline": timeline_chart
            },
            "detailed_report": detailed_report,
            "problem_records_df": problem_records_df if not problem_records_df.empty else None
    
    def render_action_section(self) -> Dict[str, Any]:
        """
        アクションセクションのレンダリング
        
        Returns
        -------
        Dict[str, Any]
            アクションセクションのデータ
        """
        # 問題タイプごとの修正オプション
        fix_options = {}
        
        # 欠損値の修正オプション
        if len(self.metrics_calculator.problematic_indices["missing_data"]) > 0:
            fix_options["missing_data"] = {
                "name": "欠損値の処理",
                "description": "欠損値を線形補間、前後の値、または定数で埋めることができます",
                "methods": [
                    {"id": "interpolate", "name": "線形補間", "description": "前後の値から補間"},
                    {"id": "ffill", "name": "前の値で埋める", "description": "直前の有効な値で欠損値を埋める"},
                    {"id": "bfill", "name": "後の値で埋める", "description": "直後の有効な値で欠損値を埋める"},
                    {"id": "value", "name": "定数で埋める", "description": "指定した値で欠損値を埋める"},
                    {"id": "drop", "name": "行を削除", "description": "欠損値を含む行を削除"}
                ]
        
        # 範囲外の値の修正オプション
        if len(self.metrics_calculator.problematic_indices["out_of_range"]) > 0:
            fix_options["out_of_range"] = {
                "name": "範囲外の値の処理",
                "description": "範囲外の値をクリップ、削除、または補間することができます",
                "methods": [
                    {"id": "clip", "name": "値をクリップ", "description": "範囲内に収まるよう値を切り詰める"},
                    {"id": "remove", "name": "値をNULLにする", "description": "範囲外の値をNULLに置き換え"},
                    {"id": "drop", "name": "行を削除", "description": "範囲外の値を含む行を削除"}
                ]
        
        # 重複の修正オプション
        if len(self.metrics_calculator.problematic_indices["duplicates"]) > 0:
            fix_options["duplicates"] = {
                "name": "重複の処理",
                "description": "重複するタイムスタンプをずらすか、重複行を削除することができます",
                "methods": [
                    {"id": "offset", "name": "時間をずらす", "description": "重複するタイムスタンプを少しずつずらす"},
                    {"id": "drop", "name": "重複を削除", "description": "重複する2番目以降の行を削除"}
                ]
        
        # 空間的異常の修正オプション
        if len(self.metrics_calculator.problematic_indices["spatial_anomalies"]) > 0:
            fix_options["spatial_anomalies"] = {
                "name": "空間的異常の処理",
                "description": "異常な位置や速度を示すポイントを処理できます",
                "methods": [
                    {"id": "remove", "name": "異常を削除", "description": "異常なポイントを削除"},
                    {"id": "interpolate", "name": "位置を補間", "description": "前後のポイントから位置を補間"}
                ]
        
        # 時間的異常の修正オプション
        if len(self.metrics_calculator.problematic_indices["temporal_anomalies"]) > 0:
            fix_options["temporal_anomalies"] = {
                "name": "時間的異常の処理",
                "description": "時間ギャップや逆行を処理できます",
                "methods": [
                    {"id": "remove_reverse", "name": "逆行を削除", "description": "時間が逆行している行を削除"},
                    {"id": "split", "name": "セッション分割", "description": "大きなギャップで別セッションに分割"}
                ]
        
        # 自動修正可能な問題の抽出
        auto_fixable_issues = []
        
        for result in self.validation_results:
            if not result["is_valid"]:
                rule_name = result["rule_name"]
                severity = result["severity"]
                
                # 自動修正可能な問題の判定
                if "No Duplicate Timestamps" in rule_name:
                    auto_fixable_issues.append({
                        "rule_name": rule_name,
                        "severity": severity,
                        "fix_type": "duplicates",
                        "fix_method": "offset"
                    })
                elif "Temporal Consistency" in rule_name and "reverse_indices" in result["details"]:
                    auto_fixable_issues.append({
                        "rule_name": rule_name,
                        "severity": severity,
                        "fix_type": "temporal_anomalies",
                        "fix_method": "remove_reverse"
                    })
        
        return {
            "fix_options": fix_options,
            "auto_fixable_issues": auto_fixable_issues
    
    def handle_filter_change(self, new_filters: Dict[str, Any]) -> None:
        """
        フィルター変更の処理
        
        Parameters
        ----------
        new_filters : Dict[str, Any]
            新しいフィルター設定
        """
        # フィルター状態を更新
        self.active_filters.update(new_filters)
        
        # フィルターに基づいて問題インデックスをフィルタリング
        filtered_indices = self._filter_problem_indices()
        
        # フィルタリングされた問題インデックスを使用して視覚化を更新
        # 実際の実装では、これらのインデックスを使って表示内容を更新
        return filtered_indices
    
    def _filter_problem_indices(self) -> Dict[str, List[int]]:
        """
        フィルターに基づいて問題インデックスをフィルタリング
        
        Returns
        -------
        Dict[str, List[int]]
            フィルタリングされた問題インデックス
        """
        # 元の問題インデックス
        indices = self.metrics_calculator.problematic_indices.copy()
        
        # 問題タイプでフィルタリング
        if self.active_filters["problem_types"] != ["missing_data", "out_of_range", "duplicates", 
                                                  "spatial_anomalies", "temporal_anomalies"]:
            # 選択されていない問題タイプは空のリストにする
            for problem_type in ["missing_data", "out_of_range", "duplicates", 
                               "spatial_anomalies", "temporal_anomalies"]:
                if problem_type not in self.active_filters["problem_types"]:
                    indices[problem_type] = []
        
        # 重要度でフィルタリング
        if self.active_filters["severity"] != ["error", "warning", "info"]:
            # 選択されていない重要度の問題を除外
            severity_filtered_indices = []
            
            for result in self.validation_results:
                if not result["is_valid"] and result["severity"] in self.active_filters["severity"]:
                    details = result["details"]
                    
                    # 問題タイプごとのインデックスを収集
                    if "null_indices" in details:
                        for col, col_indices in details["null_indices"].items():
                            severity_filtered_indices.extend(col_indices)
                    
                    if "out_of_range_indices" in details:
                        severity_filtered_indices.extend(details["out_of_range_indices"])
                    
                    if "duplicate_indices" in details:
                        for ts, dup_indices in details["duplicate_indices"].items():
                            severity_filtered_indices.extend(dup_indices)
                    
                    if "anomaly_indices" in details:
                        severity_filtered_indices.extend(details["anomaly_indices"])
                    
                    if "gap_indices" in details:
                        severity_filtered_indices.extend(details["gap_indices"])
                    
                    if "reverse_indices" in details:
                        severity_filtered_indices.extend(details["reverse_indices"])
            
            # 全体の問題インデックスを更新
            indices["all"] = list(set(indices["all"]) & set(severity_filtered_indices))
            
            # 各問題タイプの交差
            for problem_type in ["missing_data", "out_of_range", "duplicates", 
                               "spatial_anomalies", "temporal_anomalies"]:
                indices[problem_type] = list(set(indices[problem_type]) & set(severity_filtered_indices))
        
        # 時間範囲でフィルタリング
        if self.active_filters["time_range"] is not None:
            time_min, time_max = self.active_filters["time_range"]
            
            # タイムスタンプカラムがある場合のみ
            if "timestamp" in self.data.columns:
                # 時間範囲内のインデックスを特定
                time_mask = ((self.data["timestamp"] >= time_min) & 
                            (self.data["timestamp"] <= time_max))
                time_indices = self.data.index[time_mask].tolist()
                
                # 全体の問題インデックスとの交差
                indices["all"] = list(set(indices["all"]) & set(time_indices))
                
                # 各問題タイプの交差
                for problem_type in ["missing_data", "out_of_range", "duplicates", 
                                   "spatial_anomalies", "temporal_anomalies"]:
                    indices[problem_type] = list(set(indices[problem_type]) & set(time_indices))
        
        # 位置でフィルタリング
        if self.active_filters["position"] is not None:
            lat_min, lat_max, lon_min, lon_max = self.active_filters["position"]
            
            # 位置カラムがある場合のみ
            if "latitude" in self.data.columns and "longitude" in self.data.columns:
                # 位置範囲内のインデックスを特定
                position_mask = ((self.data["latitude"] >= lat_min) & 
                                (self.data["latitude"] <= lat_max) & 
                                (self.data["longitude"] >= lon_min) & 
                                (self.data["longitude"] <= lon_max))
                position_indices = self.data.index[position_mask].tolist()
                
                # 全体の問題インデックスとの交差
                indices["all"] = list(set(indices["all"]) & set(position_indices))
                
                # 各問題タイプの交差
                for problem_type in ["missing_data", "out_of_range", "duplicates", 
                                   "spatial_anomalies", "temporal_anomalies"]:
                    indices[problem_type] = list(set(indices[problem_type]) & set(position_indices))
        
        return indices
    
    def get_filtered_visualizations(self) -> Dict[str, go.Figure]:
        """
        フィルター適用後の視覚化を取得
        
        Returns
        -------
        Dict[str, go.Figure]
            フィルタリングされた視覚化
        """
        # TODO: フィルタリングされた問題インデックスに基づいて視覚化を更新する機能を実装
        # 現在はフィルタリングを無視して通常の視覚化を返す
        return self.visualizer.generate_all_visualizations()


# 既存のValidationVisualizationクラスとの互換性のため、ラッパークラスを定義
class ValidationVisualization:
    """
    既存のValidationVisualizationクラスとの互換性のためのラッパークラス
    
    Parameters
    ----------
    validator : DataValidator
        データ検証器
    container : GPSDataContainer
        GPSデータコンテナ
    """
    
    def __init__(self, validator: DataValidator, container: GPSDataContainer):
        """
        初期化
        
        Parameters
        ----------
        validator : DataValidator
            データ検証器
        container : GPSDataContainer
            GPSデータコンテナ
        """
        self.validator = validator
        self.container = container
        self.data = container.data
        
        # 検証が実行されていない場合は実行
        if not validator.validation_results:
            validator.validate(container)
        
        self.validation_results = validator.validation_results
        
        # 新しいクラスを使用
        self.metrics_calculator = QualityMetricsCalculator(validator.validation_results, container.data)
        self.visualizer = ValidationVisualizer(self.metrics_calculator, container.data)
        self.dashboard = ValidationDashboard(validator.validation_results, container.data)
        
        # データ品質スコアの計算
        self.quality_score = self.metrics_calculator.quality_scores
        
        # 問題のあるレコードのインデックスを収集
        self.problematic_indices = self.metrics_calculator.problematic_indices
        
        # レコードごとの問題集計を計算（互換性のため）
        self.record_issues = self._calculate_record_issues()
        
        # データクオリティサマリー
        self.quality_summary = self.metrics_calculator.get_quality_summary()
    
    def _calculate_record_issues(self) -> Dict[int, Dict[str, Any]]:
        """
        レコードごとの問題集計を計算（互換性のためのメソッド）
        
        Returns
        -------
        Dict[int, Dict[str, Any]]
            インデックスごとの問題詳細
        """
        record_issues = {}
        
        # 問題カテゴリとその説明
        issue_categories = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複タイムスタンプ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        
        # 各問題タイプで、問題のあるレコードに問題情報を追加
        for category, indices in self.problematic_indices.items():
            if category != "all":
                for idx in indices:
                    if idx not in record_issues:
                        record_issues[idx] = {
                            "issues": [],
                            "issue_count": 0,
                            "severity": "info"
                    
                    # 問題がまだ追加されていなければ追加
                    if issue_categories[category] not in record_issues[idx]["issues"]:
                        record_issues[idx]["issues"].append(issue_categories[category])
                        record_issues[idx]["issue_count"] += 1
        
        # 問題の重要度を設定
        for result in self.validation_results:
            if not result["is_valid"]:
                severity = result["severity"]
                details = result["details"]
                
                # 重要度を設定する対象のインデックスを抽出
                target_indices = []
                
                if "null_indices" in details:
                    for col, indices in details["null_indices"].items():
                        target_indices.extend(indices)
                if "out_of_range_indices" in details:
                    target_indices.extend(details["out_of_range_indices"])
                if "duplicate_indices" in details:
                    for ts, indices in details["duplicate_indices"].items():
                        target_indices.extend(indices)
                if "anomaly_indices" in details:
                    target_indices.extend(details["anomaly_indices"])
                if "gap_indices" in details:
                    target_indices.extend(details["gap_indices"])
                if "reverse_indices" in details:
                    target_indices.extend(details["reverse_indices"])
                
                # 対象インデックスの重要度を更新
                for idx in target_indices:
                    if idx in record_issues:
                        # 最も重要な重要度を設定（error > warning > info）
                        if severity == "error" or record_issues[idx]["severity"] == "error":
                            record_issues[idx]["severity"] = "error"
                        elif severity == "warning" or record_issues[idx]["severity"] == "warning":
                            record_issues[idx]["severity"] = "warning"
        
        # 各レコードに具体的な問題情報を追加
        for idx, issue_data in record_issues.items():
            # データの一部を保存
            if idx < len(self.data):
                row = self.data.iloc[idx]
                issue_data["timestamp"] = row.get("timestamp", None)
                issue_data["latitude"] = row.get("latitude", None)
                issue_data["longitude"] = row.get("longitude", None)
                
                # 問題の詳細説明を生成
                issue_data["description"] = f"{issue_data['issue_count']}個の問題: " + ", ".join(issue_data["issues"])
        
        return record_issues
    
    # 元のクラスのメソッドを新しいクラスのメソッドに委譲
    def get_quality_score_visualization(self) -> Tuple[go.Figure, go.Figure]:
        """
        データ品質スコアの視覚化（互換性のためのメソッド）
        """
        return (
            self.visualizer.generate_quality_score_chart(),
            self.visualizer.generate_category_scores_chart()
        )
    
    def get_issues_summary_visualization(self) -> Tuple[go.Figure, go.Figure, pd.DataFrame]:
        """
        検出された問題の概要視覚化（互換性のためのメソッド）
        """
        # 問題の重要度別カウント
        severity_counts = self.metrics_calculator.get_problem_severity_distribution()
        
        # 重要度別の棒グラフ
        severity_fig = go.Figure()
        colors = {"error": "red", "warning": "orange", "info": "blue"}
        
        for severity, count in severity_counts.items():
            if count > 0:
                severity_fig.add_trace(go.Bar(
                    x=[severity.capitalize()],
                    y=[count],
                    name=severity.capitalize(),
                    marker_color=colors[severity]
                ))
        
        severity_fig.update_layout(
            title="重要度別の問題数",
            xaxis_title="重要度",
            yaxis_title="問題数",
            height=350,
            margin=dict(t=50, b=50, l=30, r=30)
        )
        
        # 問題タイプ別の棒グラフ
        type_fig = self.visualizer.generate_problem_distribution_chart()
        
        # サマリーテーブル
        summary_data = {
            "カテゴリ": ["総レコード数", "問題のあるレコード数", "問題のあるレコード割合",
                     "エラー", "警告", "情報"],
            "値": [
                len(self.data),
                len(self.problematic_indices["all"]),
                f"{(len(self.problematic_indices['all']) / len(self.data) * 100):.2f}%" if len(self.data) > 0 else "0.00%",
                severity_counts["error"],
                severity_counts["warning"],
                severity_counts["info"]
            ]
        
        summary_df = pd.DataFrame(summary_data)
        
        return severity_fig, type_fig, summary_df
    
    def get_spatial_issues_map(self) -> go.Figure:
        """
        空間的な問題の地図表示（互換性のためのメソッド）
        """
        return self.visualizer.generate_problem_heatmap()
    
    def get_temporal_issues_visualization(self) -> go.Figure:
        """
        時間的な問題の視覚化（互換性のためのメソッド）
        """
        return self.visualizer.generate_timeline_chart()
    
    def get_data_distribution_visualization(self) -> Tuple[go.Figure, go.Figure]:
        """
        データ分布の視覚化（互換性のためのメソッド）
        """
        # 数値カラムを抽出
        numeric_cols = self.data.select_dtypes(include=np.number).columns.tolist()
        
        if not numeric_cols:
            # 数値カラムがない場合は空のグラフを返す
            fig1 = go.Figure()
            fig1.update_layout(
                title="数値カラムのヒストグラム (数値カラムがありません)",
                height=400
            )
            
            fig2 = go.Figure()
            fig2.update_layout(
                title="異常値を含む箱ひげ図 (数値カラムがありません)",
                height=400
            )
            
            return fig1, fig2
        
        # ヒストグラム
        hist_fig = go.Figure()
        
        for col in numeric_cols[:3]:  # 最初の3つのカラムのみ表示
            hist_fig.add_trace(go.Histogram(
                x=self.data[col],
                name=col,
                opacity=0.7,
                nbinsx=30
            ))
        
        hist_fig.update_layout(
            title="数値カラムのヒストグラム",
            xaxis_title="値",
            yaxis_title="頻度",
            barmode="overlay",
            height=400,
            margin=dict(t=50, b=50, l=30, r=30)
        )
        
        # 箱ひげ図
        box_fig = go.Figure()
        
        all_problem_indices = self.problematic_indices["all"]
        
        for col in numeric_cols[:3]:  # 最初の3つのカラムのみ表示
            # 正常データと問題データを分ける
            normal_mask = ~self.data.index.isin(all_problem_indices)
            problem_mask = self.data.index.isin(all_problem_indices)
            
            box_fig.add_trace(go.Box(
                y=self.data.loc[normal_mask, col],
                name=f"{col} (正常)",
                boxmean=True,
                marker_color="blue"
            ))
            
            if any(problem_mask):
                box_fig.add_trace(go.Box(
                    y=self.data.loc[problem_mask, col],
                    name=f"{col} (問題)",
                    boxmean=True,
                    marker_color="red"
                ))
        
        box_fig.update_layout(
            title="正常値と異常値の分布比較",
            yaxis_title="値",
            height=400,
            margin=dict(t=50, b=50, l=30, r=30)
        )
        
        return hist_fig, box_fig
    
    def get_validation_details_table(self) -> pd.DataFrame:
        """
        検証結果の詳細テーブル（互換性のためのメソッド）
        """
        rows = []
        
        for result in self.validation_results:
            rule_name = result["rule_name"]
            is_valid = result["is_valid"]
            severity = result["severity"]
            details = result["details"]
            
            # 詳細情報の要約
            summary = ""
            if not is_valid:
                if "missing_columns" in details:
                    summary = f"欠落カラム: {', '.join(details['missing_columns'])}"
                elif "out_of_range_count" in details:
                    summary = f"範囲外の値: {details['out_of_range_count']}件"
                    if "actual_min" in details and "actual_max" in details:
                        summary += f" (範囲: {details['actual_min']} - {details['actual_max']})"
                elif "total_null_count" in details:
                    summary = f"欠損値: {details['total_null_count']}件"
                elif "duplicate_count" in details:
                    summary = f"重複: {details['duplicate_count']}件"
                elif "anomaly_count" in details:
                    summary = f"異常値: {details['anomaly_count']}件"
                    if "max_calculated_speed" in details:
                        summary += f" (最大速度: {details['max_calculated_speed']:.1f}ノット)"
                elif "gap_count" in details:
                    summary = f"時間ギャップ: {details['gap_count']}件, "
                    summary += f"時間逆行: {details['reverse_count']}件"
                else:
                    summary = "詳細情報なし"
            else:
                summary = "検証成功"
            
            rows.append({
                "ルール": rule_name,
                "結果": "成功" if is_valid else "失敗",
                "重要度": severity,
                "詳細": summary,
                "対応可能": self._is_fixable(rule_name, details) if not is_valid else "該当なし"
            })
        
        return pd.DataFrame(rows)
    
    def _is_fixable(self, rule_name: str, details: Dict[str, Any]) -> str:
        """
        問題が自動修正可能かを判定（互換性のためのメソッド）
        """
        # 欠落カラムは修正不可
        if "missing_columns" in details:
            return "いいえ"
        
        # その他の問題は基本的に修正可能
        if any(key in details for key in ["out_of_range_count", "total_null_count", 
                                         "duplicate_count", "anomaly_count", 
                                         "gap_count", "reverse_count"]):
            return "はい"
        
        return "いいえ"
    
    def get_problem_records_table(self) -> pd.DataFrame:
        """
        問題のあるレコードのテーブル（互換性のためのメソッド）
        """
        if not self.record_issues:
            return pd.DataFrame()
        
        # 問題のあるレコードの情報を抽出
        problem_records = []
        
        for idx, issue_data in self.record_issues.items():
            record = {
                "インデックス": idx,
                "タイムスタンプ": issue_data.get("timestamp"),
                "緯度": issue_data.get("latitude"),
                "経度": issue_data.get("longitude"),
                "問題数": issue_data.get("issue_count", 0),
                "重要度": issue_data.get("severity", "info"),
                "問題タイプ": ", ".join(issue_data.get("issues", [])),
                "説明": issue_data.get("description", "")
            problem_records.append(record)
        
        # DataFrameに変換
        df = pd.DataFrame(problem_records)
        
        # 重要度でソート
        severity_order = {"error": 0, "warning": 1, "info": 2}
        if not df.empty and "重要度" in df.columns:
            df["severity_order"] = df["重要度"].map(severity_order)
            df = df.sort_values(["severity_order", "問題数"], ascending=[True, False])
            df = df.drop(columns=["severity_order"])
        
        return df
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """
        データ品質レポートの生成（互換性のためのメソッド）
        """
        return self.visualizer.generate_detailed_report()
    
    def generate_fix_recommendations(self) -> List[Dict[str, Any]]:
        """
        問題に対する修正推奨の生成（互換性のためのメソッド）
        """
        recommendations = []
        
        # 既存の実装を再利用
        quality_summary = self.quality_summary
        
        # 各検証結果に対する推奨事項
        for result in self.validation_results:
            if not result["is_valid"]:
                rule_name = result["rule_name"]
                severity = result["severity"]
                details = result["details"]
                
                # 欠落カラムの問題
                if "missing_columns" in details and details["missing_columns"]:
                    for col in details["missing_columns"]:
                        recommendations.append({
                            "rule": rule_name,
                            "severity": severity,
                            "issue": f"必須カラム '{col}' が欠落しています",
                            "recommendation": "データインポート時にこのカラムをマッピングしてください",
                            "automatic_fix": False,  # 自動修正不可
                            "action_type": "import_mapping",
                            "affected_count": 0,
                            "affected_percentage": 0
                        })
                
                # 欠損値の問題
                elif "total_null_count" in details and details["total_null_count"] > 0:
                    null_counts = details.get("null_counts", {})
                    for col, count in null_counts.items():
                        if count > 0:
                            percentage = (count / len(self.data) * 100) if len(self.data) > 0 else 0
                            recommendations.append({
                                "rule": rule_name,
                                "severity": severity,
                                "issue": f"カラム '{col}' に {count}個の欠損値があります",
                                "recommendation": "線形補間で欠損値を埋めるか、欠損値を持つ行を削除してください",
                                "automatic_fix": True,  # 自動修正可能
                                "action_type": "fill_nulls",
                                "column": col,
                                "method": "interpolate",
                                "affected_count": count,
                                "affected_percentage": percentage
                            })
                
                # 範囲外の値
                elif "out_of_range_count" in details and details["out_of_range_count"] > 0:
                    col = details.get("column", "")
                    min_val = details.get("min_value", None)
                    max_val = details.get("max_value", None)
                    
                    range_str = ""
                    if min_val is not None and max_val is not None:
                        range_str = f"{min_val}から{max_val}の範囲内"
                    elif min_val is not None:
                        range_str = f"{min_val}以上"
                    elif max_val is not None:
                        range_str = f"{max_val}以下"
                    
                    percentage = (details["out_of_range_count"] / len(self.data) * 100) if len(self.data) > 0 else 0
                    recommendations.append({
                        "rule": rule_name,
                        "severity": severity,
                        "issue": f"カラム '{col}' に {details['out_of_range_count']}個の範囲外の値があります",
                        "recommendation": f"値を{range_str}にクリップするか、異常値を持つ行を削除してください",
                        "automatic_fix": True,  # 自動修正可能
                        "action_type": "clip_values",
                        "column": col,
                        "min_value": min_val,
                        "max_value": max_val,
                        "affected_count": details["out_of_range_count"],
                        "affected_percentage": percentage
                    })
                
                # その他の問題も同様に処理
                # ...
        
        # 推奨の優先度ソート
        recommendations.sort(key=lambda x: (
            0 if x["severity"] == "error" else (1 if x["severity"] == "warning" else 2),
            -x.get("affected_percentage", 0)
        ))
        
        return recommendations
    
    def get_interactive_data_cleaning_view(self) -> Dict[str, Any]:
        """
        インタラクティブなデータクリーニングビューの生成（互換性のためのメソッド）
        """
        # ダッシュボードのアクションセクションを活用
        action_section = self.dashboard.render_action_section()
        
        # 問題レコードの取得
        problem_records_df = self.get_problem_records_table()
        
        # 修正推奨の取得
        recommendations = self.generate_fix_recommendations()
        
        return {
            "fix_options": action_section["fix_options"],
            "recommendations": recommendations,
            "problem_records": problem_records_df,
            "auto_fixable_issues": action_section["auto_fixable_issues"],
            "problematic_indices": self.problematic_indices,
            "quality_scores": self.quality_score,
            "quality_summary": self.quality_summary
