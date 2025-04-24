# -*- coding: utf-8 -*-
"""
visualization.chart_components

チャートとグラフの可視化コンポーネントを提供するモジュールです。
時系列グラフ、散布図、ヒストグラム、極座標グラフなどのデータ可視化を行います。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
import colorsys
import json
import math

class ChartBase:
    """
    チャートの基底クラス
    
    すべてのチャートコンポーネントはこのクラスを継承します。
    """
    
    def __init__(self, chart_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートの一意ID
        name : str, optional
            チャートの表示名
        """
        self.chart_id = chart_id
        self.name = name or chart_id
        self._properties = {}
        
        # データ保持用
        self._data = None
        
        # キャッシュ
        self._fig_cache = None
        self._cache_key = None
    
    def set_property(self, name: str, value: Any) -> None:
        """
        プロパティを設定
        
        Parameters
        ----------
        name : str
            プロパティ名
        value : Any
            プロパティ値
        """
        self._properties[name] = value
        self._cache_key = None  # キャッシュを無効化
    
    def get_property(self, name: str, default: Any = None) -> Any:
        """
        プロパティを取得
        
        Parameters
        ----------
        name : str
            プロパティ名
        default : Any, optional
            プロパティが存在しない場合のデフォルト値
            
        Returns
        -------
        Any
            プロパティ値
        """
        return self._properties.get(name, default)
    
    def set_data(self, data: Any) -> None:
        """
        チャートデータを設定
        
        Parameters
        ----------
        data : Any
            チャートデータ
        """
        self._data = data
        self._cache_key = None  # キャッシュを無効化
    
    def get_data(self) -> Any:
        """
        チャートデータを取得
        
        Returns
        -------
        Any
            チャートデータ
        """
        return self._data
    
    def create_figure(self) -> go.Figure:
        """
        Plotlyのfigureを作成（オーバーライド用）
        
        Returns
        -------
        go.Figure
            作成されたfigureオブジェクト
        """
        fig = go.Figure()
        fig.update_layout(
            title=self.name,
            template="plotly_white"
        )
        return fig
    
    def render(self, width: Optional[int] = None, height: int = 400, key: Optional[str] = None) -> None:
        """
        チャートをStreamlitに表示
        
        Parameters
        ----------
        width : Optional[int], optional
            表示幅（Noneの場合は自動調整）
        height : int, optional
            表示高さ
        key : Optional[str], optional
            Streamlitコンポーネントのキー
        """
        # キャッシュの利用
        cache_key = f"{self.chart_id}-{width}-{height}-{str(self._properties)}"
        
        # データがない場合や変更された場合は図を再作成
        if self._data is None:
            st.info(f"{self.name}: データがありません")
            return
        
        if self._fig_cache is None or self._cache_key != cache_key:
            # 図を作成
            fig = self.create_figure()
            
            # キャッシュを更新
            self._fig_cache = fig
            self._cache_key = cache_key
        else:
            # キャッシュから取得
            fig = self._fig_cache
        
        # Streamlitに表示
        st.plotly_chart(fig, use_container_width=width is None, key=key)
    
    def to_dict(self) -> Dict:
        """
        現在の設定を辞書として出力
        
        Returns
        -------
        Dict
            現在の設定を含む辞書
        """
        return {
            "chart_id": self.chart_id,
            "name": self.name,
            "properties": self._properties
        }
    
    def from_dict(self, config: Dict) -> None:
        """
        辞書から設定を読み込み
        
        Parameters
        ----------
        config : Dict
            設定を含む辞書
        """
        if "name" in config:
            self.name = config["name"]
        if "properties" in config:
            self._properties = config["properties"]
        
        # キャッシュを無効化
        self._cache_key = None


class TimeSeriesChart(ChartBase):
    """
    時系列データのグラフ表示コンポーネント
    """
    
    def __init__(self, chart_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートの一意ID
        name : str, optional
            チャートの表示名
        """
        super().__init__(chart_id, name or "時系列グラフ")
        
        # デフォルト設定
        self.set_property("time_key", "timestamp")
        self.set_property("value_keys", ["value"])
        self.set_property("x_title", "時間")
        self.set_property("y_title", "値")
        self.set_property("show_legend", True)
        self.set_property("line_mode", "lines")  # "lines", "markers", "lines+markers"
        self.set_property("color_scheme", "Safe")  # Plotly color scheme
        self.set_property("range_selector", True)  # 時間範囲セレクターを表示
        self.set_property("moving_average", False)  # 移動平均を表示
        self.set_property("moving_average_window", 5)  # 移動平均のウィンドウサイズ
        
        # 選択ポイント
        self._selected_point = None
        self._selected_range = None
    
    def set_selected_point(self, point_index: int) -> None:
        """
        選択ポイントを設定
        
        Parameters
        ----------
        point_index : int
            選択されたポイントのインデックス
        """
        self._selected_point = point_index
        self._cache_key = None  # キャッシュを無効化
    
    def set_selected_range(self, range_indices: Tuple[int, int]) -> None:
        """
        選択範囲を設定
        
        Parameters
        ----------
        range_indices : Tuple[int, int]
            選択範囲の開始・終了インデックス
        """
        self._selected_range = range_indices
        self._cache_key = None  # キャッシュを無効化
    
    def create_figure(self) -> go.Figure:
        """
        時系列グラフのfigureを作成
        
        Returns
        -------
        go.Figure
            作成されたfigureオブジェクト
        """
        # データが設定されていない場合
        if self._data is None:
            # 空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title=self.name,
                template="plotly_white",
                xaxis=dict(title=self.get_property("x_title", "時間")),
                yaxis=dict(title=self.get_property("y_title", "値"))
            )
            return fig
        
        # プロパティの取得
        time_key = self.get_property("time_key", "timestamp")
        value_keys = self.get_property("value_keys", ["value"])
        x_title = self.get_property("x_title", "時間")
        y_title = self.get_property("y_title", "値")
        show_legend = self.get_property("show_legend", True)
        line_mode = self.get_property("line_mode", "lines")
        color_scheme = self.get_property("color_scheme", "Safe")
        range_selector = self.get_property("range_selector", True)
        moving_average = self.get_property("moving_average", False)
        moving_average_window = self.get_property("moving_average_window", 5)
        
        # データをDataFrameに変換
        df = self._data
        if not isinstance(df, pd.DataFrame):
            if isinstance(df, dict):
                df = pd.DataFrame(df)
            elif isinstance(df, list):
                df = pd.DataFrame(df)
            else:
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データ形式エラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="データ形式がサポートされていません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        
        # 必要なカラムの存在確認
        if time_key not in df.columns:
            # タイムスタンプカラムが存在しない場合、インデックスを時間として使用
            time_values = df.index
        else:
            time_values = df[time_key]
        
        # 表示する値カラムを絞り込み
        available_value_keys = [key for key in value_keys if key in df.columns]
        
        if not available_value_keys:
            # 値のカラムが存在しない場合、数値カラムを自動選択
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                available_value_keys = numeric_cols[:3].tolist()  # 最初の3つを選択
            else:
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データエラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="表示する数値カラムがありません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        
        # カラーパレットの取得
        try:
            colors = getattr(px.colors.qualitative, color_scheme)
        except AttributeError:
            colors = px.colors.qualitative.Safe
        
        # グラフの作成
        fig = go.Figure()
        
        # 各カラムのプロット
        for i, column in enumerate(available_value_keys):
            color_idx = i % len(colors)
            color = colors[color_idx]
            
            # 元データのプロット
            fig.add_trace(go.Scatter(
                x=time_values,
                y=df[column],
                mode=line_mode,
                name=column,
                line=dict(color=color, width=2)
            ))
            
            # 移動平均の追加
            if moving_average and len(df) > moving_average_window:
                # 移動平均の計算
                ma_values = df[column].rolling(window=moving_average_window, center=True).mean()
                
                # 移動平均のプロット
                fig.add_trace(go.Scatter(
                    x=time_values,
                    y=ma_values,
                    mode="lines",
                    name=f"{column} (移動平均)",
                    line=dict(color=color, width=1, dash="dash")
                ))
        
        # 選択ポイントの追加
        if self._selected_point is not None and 0 <= self._selected_point < len(df):
            point_time = time_values.iloc[self._selected_point] if hasattr(time_values, 'iloc') else time_values[self._selected_point]
            
            # 各カラムの値を取得してアノテーション表示
            for i, column in enumerate(available_value_keys):
                point_value = df[column].iloc[self._selected_point]
                color_idx = i % len(colors)
                color = colors[color_idx]
                
                # 選択ポイントをマーカーで強調
                fig.add_trace(go.Scatter(
                    x=[point_time],
                    y=[point_value],
                    mode="markers",
                    marker=dict(color=color, size=10, line=dict(color="black", width=2)),
                    name=f"選択: {column}",
                    showlegend=False
                ))
        
        # 選択範囲の追加
        if self._selected_range is not None and len(self._selected_range) == 2:
            start_idx, end_idx = self._selected_range
            if 0 <= start_idx < len(df) and 0 <= end_idx < len(df):
                # 範囲のハイライト
                for i, column in enumerate(available_value_keys):
                    # 色はやや透明に
                    color_idx = i % len(colors)
                    color_rgb = px.colors.unlabel_rgb(colors[color_idx])
                    light_color = f"rgba({color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}, 0.3)"
                    
                    # 範囲を塗りつぶし
                    x_range = time_values.iloc[start_idx:end_idx+1] if hasattr(time_values, 'iloc') else time_values[start_idx:end_idx+1]
                    y_range = df[column].iloc[start_idx:end_idx+1]
                    
                    # ハイライト領域を追加
                    fig.add_trace(go.Scatter(
                        x=x_range,
                        y=y_range,
                        mode="none",
                        fill="tozeroy",
                        fillcolor=light_color,
                        name=f"選択範囲: {column}",
                        showlegend=False
                    ))
        
        # レイアウトの設定
        fig.update_layout(
            title=self.name,
            template="plotly_white",
            xaxis=dict(
                title=x_title,
                showgrid=True,
                gridcolor="rgba(220, 220, 220, 0.25)"
            ),
            yaxis=dict(
                title=y_title,
                showgrid=True,
                gridcolor="rgba(220, 220, 220, 0.25)"
            ),
            hovermode="closest",
            showlegend=show_legend,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        # 時間範囲セレクターの追加
        if range_selector and isinstance(time_values.iloc[0] if hasattr(time_values, 'iloc') else time_values[0], datetime):
            fig.update_layout(
                xaxis=dict(
                    rangeselector=dict(
                        buttons=list([
                            dict(count=1, label="1時間", step="hour", stepmode="backward"),
                            dict(count=6, label="6時間", step="hour", stepmode="backward"),
                            dict(count=12, label="12時間", step="hour", stepmode="backward"),
                            dict(count=1, label="1日", step="day", stepmode="backward"),
                            dict(step="all", label="全期間")
                        ]),
                        font=dict(size=10),
                        x=0, y=1.01,
                    ),
                    rangeslider=dict(visible=True, thickness=0.05),
                    type="date"
                )
            )
        
        return fig


class MultiMetricChart(ChartBase):
    """
    複数メトリクスを表示するサブプロット形式のチャートコンポーネント
    """
    
    def __init__(self, chart_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートの一意ID
        name : str, optional
            チャートの表示名
        """
        super().__init__(chart_id, name or "複数メトリクスチャート")
        
        # デフォルト設定
        self.set_property("time_key", "timestamp")
        self.set_property("metrics", ["value"])
        self.set_property("x_title", "時間")
        self.set_property("color_scheme", "Safe")
        self.set_property("shared_xaxes", True)
        self.set_property("shared_yaxes", False)
        self.set_property("row_heights", None)  # 行の高さの比率（等分する場合はNone）
        
        # 選択ポイント
        self._selected_point = None
    
    def set_selected_point(self, point_index: int) -> None:
        """
        選択ポイントを設定
        
        Parameters
        ----------
        point_index : int
            選択されたポイントのインデックス
        """
        self._selected_point = point_index
        self._cache_key = None  # キャッシュを無効化
    
    def create_figure(self) -> go.Figure:
        """
        複数メトリクスのサブプロットfigureを作成
        
        Returns
        -------
        go.Figure
            作成されたfigureオブジェクト
        """
        # データが設定されていない場合
        if self._data is None:
            # 空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title=self.name,
                template="plotly_white"
            )
            return fig
        
        # プロパティの取得
        time_key = self.get_property("time_key", "timestamp")
        metrics = self.get_property("metrics", ["value"])
        x_title = self.get_property("x_title", "時間")
        color_scheme = self.get_property("color_scheme", "Safe")
        shared_xaxes = self.get_property("shared_xaxes", True)
        shared_yaxes = self.get_property("shared_yaxes", False)
        row_heights = self.get_property("row_heights", None)
        
        # データをDataFrameに変換
        df = self._data
        if not isinstance(df, pd.DataFrame):
            if isinstance(df, dict):
                df = pd.DataFrame(df)
            elif isinstance(df, list):
                df = pd.DataFrame(df)
            else:
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データ形式エラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="データ形式がサポートされていません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        
        # 時間カラムの存在確認
        if time_key not in df.columns:
            # タイムスタンプカラムが存在しない場合、インデックスを時間として使用
            time_values = df.index
        else:
            time_values = df[time_key]
        
        # 表示するメトリクスを絞り込み
        available_metrics = [metric for metric in metrics if metric in df.columns]
        
        if not available_metrics:
            # メトリクスが存在しない場合、数値カラムを自動選択
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                available_metrics = numeric_cols[:5].tolist()  # 最初の5つを選択
            else:
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データエラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="表示するメトリクスがありません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        
        # カラーパレットの取得
        try:
            colors = getattr(px.colors.qualitative, color_scheme)
        except AttributeError:
            colors = px.colors.qualitative.Safe
        
        # サブプロットの作成
        rows = len(available_metrics)
        
        # 行の高さを設定
        if row_heights is None:
            # 等分する場合
            row_heights = [1] * rows
        elif len(row_heights) != rows:
            # 行数と高さのリスト長が異なる場合は等分
            row_heights = [1] * rows
        
        fig = make_subplots(
            rows=rows, 
            cols=1, 
            shared_xaxes=shared_xaxes, 
            shared_yaxes=shared_yaxes,
            vertical_spacing=0.02,
            row_heights=row_heights,
            subplot_titles=available_metrics
        )
        
        # 各メトリクスのプロット
        for i, metric in enumerate(available_metrics):
            row = i + 1
            color_idx = i % len(colors)
            color = colors[color_idx]
            
            # データのプロット
            fig.add_trace(
                go.Scatter(
                    x=time_values,
                    y=df[metric],
                    mode="lines",
                    name=metric,
                    line=dict(color=color, width=2)
                ),
                row=row, col=1
            )
            
            # 選択ポイントの追加
            if self._selected_point is not None and 0 <= self._selected_point < len(df):
                point_time = time_values.iloc[self._selected_point] if hasattr(time_values, 'iloc') else time_values[self._selected_point]
                point_value = df[metric].iloc[self._selected_point]
                
                # 選択ポイントをマーカーで強調
                fig.add_trace(
                    go.Scatter(
                        x=[point_time],
                        y=[point_value],
                        mode="markers",
                        marker=dict(color=color, size=10, line=dict(color="black", width=2)),
                        name=f"選択: {metric}",
                        showlegend=False
                    ),
                    row=row, col=1
                )
        
        # レイアウトの設定
        fig.update_layout(
            title=self.name,
            template="plotly_white",
            height=150 * rows,  # 行数に応じて高さを調整
            showlegend=False,
            margin=dict(l=50, r=50, t=50 + 20 * rows, b=50)  # 行数に応じてマージンを調整
        )
        
        # X軸のタイトル（最下部のサブプロットにのみ表示）
        fig.update_xaxes(title_text=x_title, row=rows, col=1)
        
        # 各行のY軸設定
        for i, metric in enumerate(available_metrics):
            fig.update_yaxes(title_text=metric, row=i+1, col=1)
            
            # グリッドラインの設定
            fig.update_xaxes(
                showgrid=True,
                gridcolor="rgba(220, 220, 220, 0.25)",
                row=i+1, col=1
            )
            fig.update_yaxes(
                showgrid=True,
                gridcolor="rgba(220, 220, 220, 0.25)",
                row=i+1, col=1
            )
        
        # ホバーモードの設定
        fig.update_layout(hovermode="x unified")
        
        return fig


class PolarChart(ChartBase):
    """
    極座標（レーダーチャート、風配図など）表示コンポーネント
    """
    
    def __init__(self, chart_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートの一意ID
        name : str, optional
            チャートの表示名
        """
        super().__init__(chart_id, name or "極座標チャート")
        
        # デフォルト設定
        self.set_property("value_key", "value")
        self.set_property("angle_key", "angle")
        self.set_property("angle_unit", "degrees")  # "degrees" or "radians"
        self.set_property("color_by", None)  # 色分けする列
        self.set_property("chart_type", "scatter")  # "scatter", "line", "bar"
        self.set_property("start_angle", 0)  # 開始角度 (度)
        self.set_property("direction", "clockwise")  # "clockwise" or "counterclockwise"
        self.set_property("closed", True)  # ラインチャートを閉じるか
        self.set_property("fill", "none")  # "none", "toself", "tozeroy"
    
    def create_figure(self) -> go.Figure:
        """
        極座標グラフのfigureを作成
        
        Returns
        -------
        go.Figure
            作成されたfigureオブジェクト
        """
        # データが設定されていない場合
        if self._data is None:
            # 空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title=self.name,
                template="plotly_white"
            )
            return fig
        
        # プロパティの取得
        value_key = self.get_property("value_key", "value")
        angle_key = self.get_property("angle_key", "angle")
        angle_unit = self.get_property("angle_unit", "degrees")
        color_by = self.get_property("color_by", None)
        chart_type = self.get_property("chart_type", "scatter")
        start_angle = self.get_property("start_angle", 0)
        direction = self.get_property("direction", "clockwise")
        closed = self.get_property("closed", True)
        fill = self.get_property("fill", "none")
        
        # データをDataFrameに変換
        df = self._data
        if not isinstance(df, pd.DataFrame):
            if isinstance(df, dict):
                df = pd.DataFrame(df)
            elif isinstance(df, list):
                df = pd.DataFrame(df)
            else:
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データ形式エラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="データ形式がサポートされていません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        
        # 必要なカラムの存在確認
        if value_key not in df.columns:
            # 値カラムが存在しない場合、エラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.name} - データエラー",
                template="plotly_white",
                annotations=[dict(
                    text=f"値カラム '{value_key}' がありません",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5
                )]
            )
            return fig
            
        if angle_key not in df.columns:
            # 角度カラムが存在しない場合、エラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.name} - データエラー",
                template="plotly_white",
                annotations=[dict(
                    text=f"角度カラム '{angle_key}' がありません",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5
                )]
            )
            return fig
        
        # 角度の単位変換
        theta = df[angle_key]
        if angle_unit == "degrees":
            # ラジアンに変換
            theta = theta * np.pi / 180
        
        # 角度の基準点と方向の調整
        if direction == "clockwise":
            # 時計回り（標準的な方位表現。北が0度、東が90度など）
            theta = start_angle * np.pi / 180 - theta
        else:
            # 反時計回り（数学的な標準表現）
            theta = start_angle * np.pi / 180 + theta
        
        # 値の取得
        r = df[value_key]
        
        # 極座標グラフの作成
        fig = go.Figure()
        
        # カラー分けの処理
        if color_by is not None and color_by in df.columns:
            # カラー分けあり - グループごとにプロット
            groups = df[color_by].unique()
            
            for group in groups:
                group_df = df[df[color_by] == group]
                group_theta = theta[df[color_by] == group]
                group_r = group_df[value_key]
                
                # 閉じたラインチャートのため、最初のポイントを最後に追加
                if chart_type == "line" and closed:
                    group_theta = pd.concat([group_theta, group_theta.iloc[[0]]])
                    group_r = pd.concat([group_r, group_r.iloc[[0]]])
                
                # チャートタイプに応じたプロット
                if chart_type == "scatter":
                    fig.add_trace(go.Scatterpolar(
                        r=group_r,
                        theta=group_theta,
                        mode="markers",
                        name=str(group),
                        fill=fill
                    ))
                elif chart_type == "line":
                    fig.add_trace(go.Scatterpolar(
                        r=group_r,
                        theta=group_theta,
                        mode="lines",
                        name=str(group),
                        fill=fill
                    ))
                elif chart_type == "bar":
                    fig.add_trace(go.Barpolar(
                        r=group_r,
                        theta=group_theta,
                        name=str(group)
                    ))
        else:
            # カラー分けなし - 単一のプロット
            
            # 閉じたラインチャートのため、最初のポイントを最後に追加
            if chart_type == "line" and closed:
                theta = pd.concat([theta, theta.iloc[[0]]])
                r = pd.concat([r, r.iloc[[0]]])
            
            # チャートタイプに応じたプロット
            if chart_type == "scatter":
                fig.add_trace(go.Scatterpolar(
                    r=r,
                    theta=theta,
                    mode="markers",
                    fill=fill
                ))
            elif chart_type == "line":
                fig.add_trace(go.Scatterpolar(
                    r=r,
                    theta=theta,
                    mode="lines",
                    fill=fill
                ))
            elif chart_type == "bar":
                fig.add_trace(go.Barpolar(
                    r=r,
                    theta=theta
                ))
        
        # レイアウトの設定
        fig.update_layout(
            title=self.name,
            template="plotly_white",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(r) * 1.1]
                ),
                angularaxis=dict(
                    direction=direction,
                    rotation=start_angle
                )
            )
        )
        
        return fig


class WindRoseChart(ChartBase):
    """
    風配図（風向頻度分布）表示コンポーネント
    """
    
    def __init__(self, chart_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートの一意ID
        name : str, optional
            チャートの表示名
        """
        super().__init__(chart_id, name or "風配図")
        
        # デフォルト設定
        self.set_property("direction_key", "direction")
        self.set_property("value_key", "frequency")
        self.set_property("speed_key", None)  # 風速による色分け用（Noneの場合は色分けなし）
        self.set_property("n_directions", 16)  # 方位の数（8: 主要8方位、16: 16方位、36: 10度間隔など）
        self.set_property("direction_names", None)  # 方位の名前（Noneの場合は自動生成）
        self.set_property("show_direction_labels", True)  # 方位ラベルを表示するか
        self.set_property("max_value", None)  # 最大値（Noneの場合は自動計算）
        self.set_property("chart_type", "bar")  # "bar", "line", "area"
        self.set_property("color_scheme", "Viridis")  # Plotly color scheme
    
    def create_figure(self) -> go.Figure:
        """
        風配図のfigureを作成
        
        Returns
        -------
        go.Figure
            作成されたfigureオブジェクト
        """
        # データが設定されていない場合
        if self._data is None:
            # 空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title=self.name,
                template="plotly_white"
            )
            return fig
        
        # プロパティの取得
        direction_key = self.get_property("direction_key", "direction")
        value_key = self.get_property("value_key", "frequency")
        speed_key = self.get_property("speed_key", None)
        n_directions = self.get_property("n_directions", 16)
        direction_names = self.get_property("direction_names", None)
        show_direction_labels = self.get_property("show_direction_labels", True)
        max_value = self.get_property("max_value", None)
        chart_type = self.get_property("chart_type", "bar")
        color_scheme = self.get_property("color_scheme", "Viridis")
        
        # データをDataFrameに変換
        df = self._data
        if not isinstance(df, pd.DataFrame):
            if isinstance(df, dict):
                df = pd.DataFrame(df)
            elif isinstance(df, list):
                df = pd.DataFrame(df)
            else:
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データ形式エラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="データ形式がサポートされていません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        
        # 必要なカラムの存在確認
        if direction_key not in df.columns:
            # 方位カラムが存在しない場合、エラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.name} - データエラー",
                template="plotly_white",
                annotations=[dict(
                    text=f"方位カラム '{direction_key}' がありません",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5
                )]
            )
            return fig
            
        if value_key not in df.columns:
            # 値カラムが存在しない場合、エラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.name} - データエラー",
                template="plotly_white",
                annotations=[dict(
                    text=f"値カラム '{value_key}' がありません",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5
                )]
            )
            return fig
        
        # 方位ビンを作成
        bin_size = 360 / n_directions
        direction_bins = np.arange(0, 360, bin_size)
        df['direction_bin'] = pd.cut(df[direction_key] % 360, bins=np.append(direction_bins, 360), labels=direction_bins, include_lowest=True)
        
        # 方位名の生成
        if direction_names is None:
            if n_directions == 4:
                direction_names = ["北", "東", "南", "西"]
            elif n_directions == 8:
                direction_names = ["北", "北東", "東", "南東", "南", "南西", "西", "北西"]
            elif n_directions == 16:
                direction_names = ["北", "北北東", "北東", "東北東", "東", "東南東", "南東", "南南東", 
                                  "南", "南南西", "南西", "西南西", "西", "西北西", "北西", "北北西"]
            else:
                # 角度の値をそのまま使用
                direction_names = [f"{d:.0f}°" for d in direction_bins]
        
        # 方位ごとに集計
        if speed_key is not None and speed_key in df.columns:
            # 風速別に集計
            # 風速をビンに区分
            wind_bins = [0, 2, 4, 6, 8, 10, 12, 14, 17, 20, float('inf')]
            wind_labels = ["0-2", "2-4", "4-6", "6-8", "8-10", "10-12", "12-14", "14-17", "17-20", "20+"]
            df['speed_bin'] = pd.cut(df[speed_key], bins=wind_bins, labels=wind_labels, include_lowest=True)
            
            # 方位×風速ビンでの集計
            direction_speed_values = df.groupby(['direction_bin', 'speed_bin'])[value_key].sum().unstack(fill_value=0)
            
            # 欠損方位を補完
            for direction in direction_bins:
                if direction not in direction_speed_values.index:
                    direction_speed_values.loc[direction] = [0] * len(wind_labels)
            
            # インデックスを並べ替え
            direction_speed_values = direction_speed_values.sort_index()
            
            # 極座標グラフの作成
            fig = go.Figure()
            
            # カラースケールの設定
            try:
                colors = getattr(px.colors.sequential, color_scheme)
            except AttributeError:
                colors = px.colors.sequential.Viridis
            
            # 各風速ビンについてプロット
            for i, speed_bin in enumerate(wind_labels):
                if speed_bin in direction_speed_values.columns:
                    values = direction_speed_values[speed_bin].values
                    color_idx = i * len(colors) // len(wind_labels)
                    color = colors[color_idx] if color_idx < len(colors) else colors[-1]
                    
                    # 閉じたグラフにするために最初の要素を最後に追加
                    theta = np.append(direction_bins, direction_bins[0]) * np.pi / 180
                    r = np.append(values, values[0])
                    
                    # チャートタイプに応じたプロット
                    if chart_type == "bar":
                        fig.add_trace(go.Barpolar(
                            r=values,
                            theta=direction_bins,
                            name=f"{speed_bin} kt",
                            marker_color=color
                        ))
                    elif chart_type in ["line", "area"]:
                        fig.add_trace(go.Scatterpolar(
                            r=r,
                            theta=theta,
                            mode="lines",
                            name=f"{speed_bin} kt",
                            line=dict(color=color),
                            fill="toself" if chart_type == "area" else "none"
                        ))
        else:
            # 風速区分なしの単純集計
            direction_values = df.groupby('direction_bin')[value_key].sum()
            
            # 欠損方位を補完
            for direction in direction_bins:
                if direction not in direction_values.index:
                    direction_values.loc[direction] = 0
            
            # インデックスを並べ替え
            direction_values = direction_values.sort_index()
            
            # 極座標グラフの作成
            fig = go.Figure()
            
            # 閉じたグラフにするために最初の要素を最後に追加
            if chart_type in ["line", "area"]:
                theta = np.append(direction_bins, direction_bins[0]) * np.pi / 180
                r = np.append(direction_values.values, direction_values.values[0])
                
                fig.add_trace(go.Scatterpolar(
                    r=r,
                    theta=theta,
                    mode="lines",
                    line=dict(color="royalblue", width=3),
                    fill="toself" if chart_type == "area" else "none"
                ))
            else:
                fig.add_trace(go.Barpolar(
                    r=direction_values.values,
                    theta=direction_bins,
                    marker_color="royalblue"
                ))
        
        # レイアウトの設定
        fig.update_layout(
            title=self.name,
            template="plotly_white",
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max_value] if max_value is not None else None
                ),
                angularaxis=dict(
                    direction="clockwise",
                    rotation=90,  # 北を上に
                    tickmode="array" if show_direction_labels else "auto",
                    tickvals=direction_bins,
                    ticktext=direction_names,
                    tickfont=dict(size=10)
                )
            )
        )
        
        return fig


class ScatterChart(ChartBase):
    """
    散布図表示コンポーネント
    """
    
    def __init__(self, chart_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートの一意ID
        name : str, optional
            チャートの表示名
        """
        super().__init__(chart_id, name or "散布図")
        
        # デフォルト設定
        self.set_property("x_key", "x")
        self.set_property("y_key", "y")
        self.set_property("x_title", "X")
        self.set_property("y_title", "Y")
        self.set_property("color_by", None)  # 色分けする列
        self.set_property("size_by", None)  # サイズを変える列
        self.set_property("hover_data", None)  # ホバー表示する列のリスト
        self.set_property("color_scheme", "Viridis")  # Plotly color scheme
        self.set_property("show_trendline", False)  # トレンドラインを表示するか
        self.set_property("trendline_type", "ols")  # "ols", "lowess"
        self.set_property("marker_size", 8)  # マーカーサイズ
        self.set_property("opacity", 0.7)  # マーカーの透明度
    
    def create_figure(self) -> go.Figure:
        """
        散布図のfigureを作成
        
        Returns
        -------
        go.Figure
            作成されたfigureオブジェクト
        """
        # データが設定されていない場合
        if self._data is None:
            # 空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title=self.name,
                template="plotly_white"
            )
            return fig
        
        # プロパティの取得
        x_key = self.get_property("x_key", "x")
        y_key = self.get_property("y_key", "y")
        x_title = self.get_property("x_title", "X")
        y_title = self.get_property("y_title", "Y")
        color_by = self.get_property("color_by", None)
        size_by = self.get_property("size_by", None)
        hover_data = self.get_property("hover_data", None)
        color_scheme = self.get_property("color_scheme", "Viridis")
        show_trendline = self.get_property("show_trendline", False)
        trendline_type = self.get_property("trendline_type", "ols")
        marker_size = self.get_property("marker_size", 8)
        opacity = self.get_property("opacity", 0.7)
        
        # データをDataFrameに変換
        df = self._data
        if not isinstance(df, pd.DataFrame):
            if isinstance(df, dict):
                df = pd.DataFrame(df)
            elif isinstance(df, list):
                df = pd.DataFrame(df)
            else:
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データ形式エラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="データ形式がサポートされていません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        
        # 必要なカラムの存在確認
        if x_key not in df.columns:
            # X軸カラムが存在しない場合、エラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.name} - データエラー",
                template="plotly_white",
                annotations=[dict(
                    text=f"X軸カラム '{x_key}' がありません",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5
                )]
            )
            return fig
            
        if y_key not in df.columns:
            # Y軸カラムが存在しない場合、エラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.name} - データエラー",
                template="plotly_white",
                annotations=[dict(
                    text=f"Y軸カラム '{y_key}' がありません",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5
                )]
            )
            return fig
        
        # ホバーデータの列を確認
        if hover_data is not None:
            hover_data = [col for col in hover_data if col in df.columns]
        
        # プロットの作成
        if color_by is not None and color_by in df.columns:
            # カラーマッピングあり
            if size_by is not None and size_by in df.columns:
                # サイズマッピングあり
                fig = px.scatter(
                    df, x=x_key, y=y_key, 
                    color=color_by, size=size_by,
                    hover_data=hover_data,
                    color_continuous_scale=color_scheme,
                    opacity=opacity,
                    trendline=trendline_type if show_trendline else None,
                    title=self.name
                )
            else:
                # サイズマッピングなし
                fig = px.scatter(
                    df, x=x_key, y=y_key, 
                    color=color_by,
                    hover_data=hover_data,
                    color_continuous_scale=color_scheme,
                    opacity=opacity,
                    trendline=trendline_type if show_trendline else None,
                    title=self.name
                )
                # マーカーサイズを設定
                fig.update_traces(marker=dict(size=marker_size))
        else:
            # カラーマッピングなし
            if size_by is not None and size_by in df.columns:
                # サイズマッピングあり
                fig = px.scatter(
                    df, x=x_key, y=y_key, 
                    size=size_by,
                    hover_data=hover_data,
                    opacity=opacity,
                    trendline=trendline_type if show_trendline else None,
                    title=self.name
                )
            else:
                # サイズマッピングなし
                fig = px.scatter(
                    df, x=x_key, y=y_key,
                    hover_data=hover_data,
                    opacity=opacity,
                    trendline=trendline_type if show_trendline else None,
                    title=self.name
                )
                # マーカーサイズを設定
                fig.update_traces(marker=dict(size=marker_size))
        
        # 軸ラベルの設定
        fig.update_layout(
            xaxis_title=x_title,
            yaxis_title=y_title,
            template="plotly_white"
        )
        
        return fig


class HistogramChart(ChartBase):
    """
    ヒストグラム表示コンポーネント
    """
    
    def __init__(self, chart_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートの一意ID
        name : str, optional
            チャートの表示名
        """
        super().__init__(chart_id, name or "ヒストグラム")
        
        # デフォルト設定
        self.set_property("value_key", "value")
        self.set_property("x_title", "値")
        self.set_property("y_title", "頻度")
        self.set_property("color", "#3366CC")
        self.set_property("nbins", 20)  # ビンの数
        self.set_property("opacity", 0.7)  # バーの透明度
        self.set_property("show_stats", True)  # 統計情報を表示するか
        self.set_property("show_kde", False)  # カーネル密度推定を表示するか
        self.set_property("color_by", None)  # 色分けする列
        self.set_property("color_scheme", "Viridis")  # Plotly color scheme
    
    def create_figure(self) -> go.Figure:
        """
        ヒストグラムのfigureを作成
        
        Returns
        -------
        go.Figure
            作成されたfigureオブジェクト
        """
        # データが設定されていない場合
        if self._data is None:
            # 空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title=self.name,
                template="plotly_white"
            )
            return fig
        
        # プロパティの取得
        value_key = self.get_property("value_key", "value")
        x_title = self.get_property("x_title", "値")
        y_title = self.get_property("y_title", "頻度")
        color = self.get_property("color", "#3366CC")
        nbins = self.get_property("nbins", 20)
        opacity = self.get_property("opacity", 0.7)
        show_stats = self.get_property("show_stats", True)
        show_kde = self.get_property("show_kde", False)
        color_by = self.get_property("color_by", None)
        color_scheme = self.get_property("color_scheme", "Viridis")
        
        # データをDataFrameに変換
        df = self._data
        if not isinstance(df, pd.DataFrame):
            if isinstance(df, dict):
                df = pd.DataFrame(df)
            elif isinstance(df, list):
                df = pd.DataFrame(df)
            else:
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データ形式エラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="データ形式がサポートされていません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        
        # 必要なカラムの存在確認
        if value_key not in df.columns:
            # 値カラムが存在しない場合、エラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.name} - データエラー",
                template="plotly_white",
                annotations=[dict(
                    text=f"値カラム '{value_key}' がありません",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5
                )]
            )
            return fig
        
        # プロットの作成
        if color_by is not None and color_by in df.columns:
            # カラー分けあり
            fig = px.histogram(
                df, x=value_key,
                color=color_by,
                nbins=nbins,
                opacity=opacity,
                color_discrete_sequence=[color] if isinstance(color, str) else None,
                title=self.name
            )
            
            # カーネル密度推定の追加
            if show_kde:
                groups = df[color_by].unique()
                for i, group in enumerate(groups):
                    group_df = df[df[color_by] == group]
                    values = group_df[value_key].dropna()
                    
                    if len(values) > 1:
                        kde_x = np.linspace(values.min(), values.max(), 100)
                        kde_y = self._compute_kde(values, kde_x)
                        
                        # スケーリング
                        # ヒストグラムの最大頻度を推定
                        hist, bin_edges = np.histogram(values, bins=nbins)
                        max_count = hist.max()
                        
                        # KDEを最大頻度に合わせてスケーリング
                        kde_y_scaled = kde_y * max_count / kde_y.max() if kde_y.max() > 0 else kde_y
                        
                        fig.add_trace(go.Scatter(
                            x=kde_x,
                            y=kde_y_scaled,
                            mode='lines',
                            line=dict(width=2, dash='solid'),
                            name=f'KDE {group}'
                        ))
        else:
            # カラー分けなし
            fig = px.histogram(
                df, x=value_key,
                nbins=nbins,
                opacity=opacity,
                color_discrete_sequence=[color] if isinstance(color, str) else None,
                title=self.name
            )
            
            # カーネル密度推定の追加
            if show_kde:
                values = df[value_key].dropna()
                
                if len(values) > 1:
                    kde_x = np.linspace(values.min(), values.max(), 100)
                    kde_y = self._compute_kde(values, kde_x)
                    
                    # スケーリング
                    hist, bin_edges = np.histogram(values, bins=nbins)
                    max_count = hist.max()
                    
                    # KDEを最大頻度に合わせてスケーリング
                    kde_y_scaled = kde_y * max_count / kde_y.max() if kde_y.max() > 0 else kde_y
                    
                    fig.add_trace(go.Scatter(
                        x=kde_x,
                        y=kde_y_scaled,
                        mode='lines',
                        line=dict(width=2, color='red', dash='solid'),
                        name='KDE'
                    ))
        
        # 統計情報の追加
        if show_stats:
            values = df[value_key].dropna()
            
            if len(values) > 0:
                mean_val = values.mean()
                median_val = values.median()
                std_val = values.std()
                
                # 平均線
                fig.add_vline(
                    x=mean_val,
                    line_width=2,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"平均: {mean_val:.2f}",
                    annotation_position="top left"
                )
                
                # 中央値線
                fig.add_vline(
                    x=median_val,
                    line_width=2,
                    line_dash="dash",
                    line_color="green",
                    annotation_text=f"中央値: {median_val:.2f}",
                    annotation_position="top right"
                )
                
                # 標準偏差の範囲
                fig.add_vrect(
                    x0=mean_val - std_val,
                    x1=mean_val + std_val,
                    fillcolor="gray",
                    opacity=0.2,
                    line_width=0,
                    annotation_text="±1σ",
                    annotation_position="bottom right"
                )
        
        # 軸ラベルの設定
        fig.update_layout(
            xaxis_title=x_title,
            yaxis_title=y_title,
            template="plotly_white",
            bargap=0.1  # バー間のギャップ
        )
        
        return fig
    
    def _compute_kde(self, data: pd.Series, x_grid: np.ndarray) -> np.ndarray:
        """
        カーネル密度推定を計算
        
        Parameters
        ----------
        data : pd.Series
            入力データ
        x_grid : np.ndarray
            計算するx座標のグリッド
            
        Returns
        -------
        np.ndarray
            KDE値
        """
        n = len(data)
        if n < 2:
            return np.zeros_like(x_grid)
        
        # バンド幅の計算（Scott's rule）
        h = 1.06 * np.std(data) * n**(-1/5)
        if h == 0:
            h = 1.0  # ゼロ分散の場合のフォールバック
        
        # カーネル密度推定
        kde = np.zeros_like(x_grid, dtype=float)
        
        for i in range(n):
            # ガウスカーネル
            kde += np.exp(-0.5 * ((x_grid - data.iloc[i]) / h)**2) / (h * np.sqrt(2 * np.pi))
        
        return kde / n


class HeatMapChart(ChartBase):
    """
    ヒートマップ表示コンポーネント
    """
    
    def __init__(self, chart_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートの一意ID
        name : str, optional
            チャートの表示名
        """
        super().__init__(chart_id, name or "ヒートマップ")
        
        # デフォルト設定
        self.set_property("x_key", "x")
        self.set_property("y_key", "y")
        self.set_property("value_key", "value")
        self.set_property("x_title", "X")
        self.set_property("y_title", "Y")
        self.set_property("color_scheme", "Viridis")  # Plotly color scheme
        self.set_property("show_values", False)  # 値のテキストを表示するか
        self.set_property("show_scale", True)  # カラースケールを表示するか
        self.set_property("scale_title", "値")  # カラースケールのタイトル
        self.set_property("transpose", False)  # 転置するか
    
    def create_figure(self) -> go.Figure:
        """
        ヒートマップのfigureを作成
        
        Returns
        -------
        go.Figure
            作成されたfigureオブジェクト
        """
        # データが設定されていない場合
        if self._data is None:
            # 空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title=self.name,
                template="plotly_white"
            )
            return fig
        
        # プロパティの取得
        x_key = self.get_property("x_key", "x")
        y_key = self.get_property("y_key", "y")
        value_key = self.get_property("value_key", "value")
        x_title = self.get_property("x_title", "X")
        y_title = self.get_property("y_title", "Y")
        color_scheme = self.get_property("color_scheme", "Viridis")
        show_values = self.get_property("show_values", False)
        show_scale = self.get_property("show_scale", True)
        scale_title = self.get_property("scale_title", "値")
        transpose = self.get_property("transpose", False)
        
        # データ形式の判断とピボット処理
        if isinstance(self._data, pd.DataFrame):
            df = self._data
            
            # データ形式の判断
            if x_key in df.columns and y_key in df.columns and value_key in df.columns:
                # 座標形式のデータをピボットテーブルに変換
                matrix = df.pivot_table(index=y_key, columns=x_key, values=value_key, aggfunc='mean')
            elif df.index.name == y_key and all(col for col in df.columns):
                # すでにマトリックス形式のデータ
                matrix = df.copy()
            else:
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データエラー",
                    template="plotly_white",
                    annotations=[dict(
                        text=f"必要なカラム '{x_key}', '{y_key}', '{value_key}' がないか、マトリックス形式ではありません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        elif isinstance(self._data, dict):
            # 辞書形式の場合（matrix, x_labels, y_labelsの形式を想定）
            if 'matrix' in self._data:
                matrix_data = self._data['matrix']
                x_labels = self._data.get('x_labels', list(range(len(matrix_data[0]))) if matrix_data else [])
                y_labels = self._data.get('y_labels', list(range(len(matrix_data))) if matrix_data else [])
                
                matrix = pd.DataFrame(matrix_data, index=y_labels, columns=x_labels)
            else:
                # マトリックス形式でない辞書の場合
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データ形式エラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="データ形式がサポートされていません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        elif isinstance(self._data, (list, np.ndarray)):
            # リスト/配列の場合：単純な2次元配列と仮定
            if all(isinstance(row, (list, np.ndarray)) for row in self._data):
                # 2次元配列
                matrix_data = self._data
                x_labels = list(range(len(matrix_data[0]))) if matrix_data else []
                y_labels = list(range(len(matrix_data)))
                
                matrix = pd.DataFrame(matrix_data, index=y_labels, columns=x_labels)
            else:
                # 1次元配列または不均一な配列
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データ形式エラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="データ形式がサポートされていません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        else:
            # サポートされていないデータ形式
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.name} - データ形式エラー",
                template="plotly_white",
                annotations=[dict(
                    text="データ形式がサポートされていません",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5
                )]
            )
            return fig
        
        # 必要に応じて転置
        if transpose:
            matrix = matrix.T
        
        # カラースケールの取得
        try:
            colorscale = getattr(px.colors.sequential, color_scheme)
        except AttributeError:
            colorscale = px.colors.sequential.Viridis
        
        # ヒートマップの作成
        fig = go.Figure(data=go.Heatmap(
            z=matrix.values,
            x=matrix.columns,
            y=matrix.index,
            colorscale=colorscale,
            showscale=show_scale,
            colorbar=dict(title=scale_title),
            text=matrix.values if show_values else None,
            hovertemplate='%{y}, %{x}: %{z}<extra></extra>' if not show_values else '%{text}<extra></extra>'
        ))
        
        # 値のテキスト表示
        if show_values:
            annotations = []
            for i, row in enumerate(matrix.index):
                for j, col in enumerate(matrix.columns):
                    value = matrix.iloc[i, j]
                    text_color = 'white' if matrix.values[i, j] > (matrix.values.max() + matrix.values.min()) / 2 else 'black'
                    
                    annotations.append(dict(
                        x=col,
                        y=row,
                        text=f"{value:.1f}",
                        showarrow=False,
                        font=dict(color=text_color)
                    ))
            
            fig.update_layout(annotations=annotations)
        
        # レイアウトの設定
        fig.update_layout(
            title=self.name,
            xaxis_title=x_title,
            yaxis_title=y_title,
            template="plotly_white"
        )
        
        return fig


class BoxPlotChart(ChartBase):
    """
    ボックスプロット表示コンポーネント
    """
    
    def __init__(self, chart_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        chart_id : str
            チャートの一意ID
        name : str, optional
            チャートの表示名
        """
        super().__init__(chart_id, name or "ボックスプロット")
        
        # デフォルト設定
        self.set_property("value_key", "value")
        self.set_property("group_key", "group")
        self.set_property("x_title", "グループ")
        self.set_property("y_title", "値")
        self.set_property("color_by", None)  # 色分けする列
        self.set_property("color_scheme", "Viridis")  # Plotly color scheme
        self.set_property("show_points", True)  # データポイントを表示するか
        self.set_property("show_notch", False)  # ノッチを表示するか
        self.set_property("orientation", "vertical")  # "vertical" or "horizontal"
        self.set_property("sort_groups", False)  # グループをソートするか
    
    def create_figure(self) -> go.Figure:
        """
        ボックスプロットのfigureを作成
        
        Returns
        -------
        go.Figure
            作成されたfigureオブジェクト
        """
        # データが設定されていない場合
        if self._data is None:
            # 空のグラフを返す
            fig = go.Figure()
            fig.update_layout(
                title=self.name,
                template="plotly_white"
            )
            return fig
        
        # プロパティの取得
        value_key = self.get_property("value_key", "value")
        group_key = self.get_property("group_key", "group")
        x_title = self.get_property("x_title", "グループ")
        y_title = self.get_property("y_title", "値")
        color_by = self.get_property("color_by", None)
        color_scheme = self.get_property("color_scheme", "Viridis")
        show_points = self.get_property("show_points", True)
        show_notch = self.get_property("show_notch", False)
        orientation = self.get_property("orientation", "vertical")
        sort_groups = self.get_property("sort_groups", False)
        
        # データをDataFrameに変換
        df = self._data
        if not isinstance(df, pd.DataFrame):
            if isinstance(df, dict):
                df = pd.DataFrame(df)
            elif isinstance(df, list):
                df = pd.DataFrame(df)
            else:
                # エラーメッセージを表示する空のグラフ
                fig = go.Figure()
                fig.update_layout(
                    title=f"{self.name} - データ形式エラー",
                    template="plotly_white",
                    annotations=[dict(
                        text="データ形式がサポートされていません",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.5, y=0.5
                    )]
                )
                return fig
        
        # 必要なカラムの存在確認
        if value_key not in df.columns:
            # 値カラムが存在しない場合、エラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.name} - データエラー",
                template="plotly_white",
                annotations=[dict(
                    text=f"値カラム '{value_key}' がありません",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5
                )]
            )
            return fig
        
        # グループカラムのチェック
        if group_key is not None and group_key not in df.columns:
            # グループカラムが指定されているが存在しない場合
            fig = go.Figure()
            fig.update_layout(
                title=f"{self.name} - データエラー",
                template="plotly_white",
                annotations=[dict(
                    text=f"グループカラム '{group_key}' がありません",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=0.5
                )]
            )
            return fig
        
        # プロット設定
        plot_kwargs = {
            'y' if orientation == 'vertical' else 'x': value_key,
            'notched': show_notch,
            'points': 'all' if show_points else False,
            'title': self.name,
            'labels': {value_key: y_title}
        }
        
        # グループとカラー設定
        if group_key is not None:
            plot_kwargs['x' if orientation == 'vertical' else 'y'] = group_key
            plot_kwargs['labels'][group_key] = x_title
            
            # グループのソート
            if sort_groups:
                groups = sorted(df[group_key].unique())
                df[group_key] = pd.Categorical(df[group_key], categories=groups, ordered=True)
        
        # カラー設定
        if color_by is not None and color_by in df.columns:
            plot_kwargs['color'] = color_by
            plot_kwargs['color_discrete_sequence'] = getattr(px.colors.qualitative, color_scheme, px.colors.qualitative.Safe)
        
        # 向き設定
        if orientation == 'horizontal':
            plot_kwargs['orientation'] = 'h'
        
        # ボックスプロットの作成
        fig = px.box(df, **plot_kwargs)
        
        # レイアウトの設定
        fig.update_layout(
            template="plotly_white",
            boxmode="group"  # グループ化モード
        )
        
        return fig


class ChartManager:
    """
    チャートコンポーネントの管理クラス
    
    複数のチャートを管理し、連携させるための機能を提供します。
    """
    
    def __init__(self):
        """初期化"""
        self.name = "チャート管理"
        
        # チャート管理
        self._charts = {}
        self._chart_order = []
        
        # 共有データコンテキスト
        self._data_context = {}
        
        # 選択状態の共有
        self._selection_context = {
            "selected_point": None,
            "selected_range": None,
            "selected_category": None
        }
    
    def add_chart(self, chart: ChartBase) -> None:
        """
        チャートを追加
        
        Parameters
        ----------
        chart : ChartBase
            追加するチャート
        """
        if chart.chart_id not in self._charts:
            self._charts[chart.chart_id] = chart
            self._chart_order.append(chart.chart_id)
    
    def remove_chart(self, chart_id: str) -> bool:
        """
        チャートを削除
        
        Parameters
        ----------
        chart_id : str
            削除するチャートのID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if chart_id in self._charts:
            del self._charts[chart_id]
            self._chart_order.remove(chart_id)
            return True
        return False
    
    def get_chart(self, chart_id: str) -> Optional[ChartBase]:
        """
        チャートを取得
        
        Parameters
        ----------
        chart_id : str
            取得するチャートのID
            
        Returns
        -------
        Optional[ChartBase]
            チャートオブジェクト、なければNone
        """
        return self._charts.get(chart_id)
    
    def get_all_charts(self) -> Dict[str, ChartBase]:
        """
        すべてのチャートを取得
        
        Returns
        -------
        Dict[str, ChartBase]
            チャートID: チャートオブジェクトの辞書
        """
        return self._charts
    
    def set_chart_order(self, chart_order: List[str]) -> None:
        """
        チャートの表示順序を設定
        
        Parameters
        ----------
        chart_order : List[str]
            チャートIDのリスト（上から順）
        """
        # 有効なチャートIDのみで順序を更新
        valid_ids = [chart_id for chart_id in chart_order if chart_id in self._charts]
        
        # 順序に含まれていないチャートを追加
        for chart_id in self._charts.keys():
            if chart_id not in valid_ids:
                valid_ids.append(chart_id)
        
        self._chart_order = valid_ids
    
    def set_data_context(self, data_key: str, data: Any) -> None:
        """
        共有データコンテキストにデータを設定
        
        Parameters
        ----------
        data_key : str
            データのキー
        data : Any
            データ値
        """
        self._data_context[data_key] = data
    
    def get_data_context(self, data_key: str) -> Optional[Any]:
        """
        共有データコンテキストからデータを取得
        
        Parameters
        ----------
        data_key : str
            取得するデータのキー
            
        Returns
        -------
        Optional[Any]
            データ値、キーが存在しない場合はNone
        """
        return self._data_context.get(data_key)
    
    def set_selected_point(self, point_index: int) -> None:
        """
        選択ポイントを設定し、連携チャートに伝播
        
        Parameters
        ----------
        point_index : int
            選択されたポイントのインデックス
        """
        self._selection_context["selected_point"] = point_index
        
        # 全チャートに選択を伝播
        for chart_id, chart in self._charts.items():
            if hasattr(chart, "set_selected_point"):
                chart.set_selected_point(point_index)
    
    def set_selected_range(self, range_indices: Tuple[int, int]) -> None:
        """
        選択範囲を設定し、連携チャートに伝播
        
        Parameters
        ----------
        range_indices : Tuple[int, int]
            選択範囲の開始・終了インデックス
        """
        self._selection_context["selected_range"] = range_indices
        
        # 全チャートに選択を伝播
        for chart_id, chart in self._charts.items():
            if hasattr(chart, "set_selected_range"):
                chart.set_selected_range(range_indices)
    
    def set_selected_category(self, category: str) -> None:
        """
        選択カテゴリを設定し、連携チャートに伝播
        
        Parameters
        ----------
        category : str
            選択されたカテゴリ
        """
        self._selection_context["selected_category"] = category
        
        # TODO: カテゴリの選択をチャートに伝播する処理
    
    def render_charts(self, columns: int = 1, width: Optional[int] = None, height: int = 400) -> None:
        """
        すべてのチャートをStreamlitに表示
        
        Parameters
        ----------
        columns : int, optional
            表示列数
        width : Optional[int], optional
            表示幅（Noneの場合は自動調整）
        height : int, optional
            表示高さ
        """
        if not self._charts:
            st.info("表示するチャートがありません")
            return
        
        # チャートをcolumns列に分けて表示
        chart_chunks = [self._chart_order[i:i+columns] for i in range(0, len(self._chart_order), columns)]
        
        for chunk in chart_chunks:
            cols = st.columns(len(chunk))
            
            for i, chart_id in enumerate(chunk):
                chart = self._charts.get(chart_id)
                if chart:
                    with cols[i]:
                        st.subheader(chart.name)
                        chart.render(width=width, height=height, key=chart_id)
    
    def to_dict(self) -> Dict:
        """
        現在の設定を辞書として出力
        
        Returns
        -------
        Dict
            現在の設定を含む辞書
        """
        chart_configs = {}
        for chart_id, chart in self._charts.items():
            chart_configs[chart_id] = chart.to_dict()
        
        return {
            "chart_order": self._chart_order,
            "chart_configs": chart_configs
        }
    
    def from_dict(self, config: Dict) -> None:
        """
        辞書から設定を読み込み
        
        Parameters
        ----------
        config : Dict
            設定を含む辞書
        """
        if "chart_order" in config:
            # 有効なチャートIDのみを使用
            valid_ids = [chart_id for chart_id in config["chart_order"] if chart_id in self._charts]
            # 順序に含まれていないチャートを追加
            for chart_id in self._charts.keys():
                if chart_id not in valid_ids:
                    valid_ids.append(chart_id)
            self._chart_order = valid_ids
        
        if "chart_configs" in config:
            for chart_id, chart_config in config["chart_configs"].items():
                if chart_id in self._charts:
                    self._charts[chart_id].from_dict(chart_config)
