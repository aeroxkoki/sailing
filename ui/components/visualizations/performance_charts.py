"""
ui.components.visualizations.performance_charts

パフォーマンス分析チャートコンポーネント - 速度、風向などのデータをチャート表示するためのコンポーネント
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
from sailing_data_processor.data_model.container import GPSDataContainer, WindDataContainer
from ui.data_binding import DataBindingManager, UIStateManager

class PerformanceChartsComponent:
    """
    パフォーマンスチャート用のコンポーネント
    
    セーリングデータを時系列グラフとして表示するためのコンポーネントです。
    """
    
    def __init__(self, data_binding: DataBindingManager, ui_state: UIStateManager):
        """
        初期化
        
        Parameters
        ----------
        data_binding : DataBindingManager
            データバインディング管理オブジェクト
        ui_state : UIStateManager
            UI状態管理オブジェクト
        """
        self.data_binding = data_binding
        self.ui_state = ui_state
        
        # カラーパレット
        self.color_palette = px.colors.qualitative.Safe
        
        # チャートキャッシュ
        self._chart_cache = {}
    
    def create_time_series_chart(self, 
                                container: GPSDataContainer, 
                                y_columns: List[str],
                                title: str = 'パフォーマンスチャート',
                                height: int = 400,
                                width: int = 800) -> go.Figure:
        """
        時系列チャートを作成
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        y_columns : List[str]
            Y軸に表示する列のリスト
        title : str, optional
            チャートのタイトル
        height : int, optional
            チャートの高さ
        width : int, optional
            チャートの幅
            
        Returns
        -------
        go.Figure
            作成されたPlotlyのFigureオブジェクト
        """
        # データフレームの取得
        df = container.data
        
        # 指定された列が存在するか確認
        available_columns = [col for col in y_columns if col in df.columns]
        
        if not available_columns:
            # 適切な列がない場合はエラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{title} - データなし",
                height=height,
                width=width,
                annotations=[
                    dict(
                        text="指定された列がデータに含まれていません",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5
                    )
                ]
            )
            return fig
        
        # チャートの作成
        fig = go.Figure()
        
        # 各列のデータを追加
        for i, column in enumerate(available_columns):
            color_idx = i % len(self.color_palette)
            
            # Y軸のデータ型に応じた表示書式を設定
            hover_template = f"%{{x|%Y-%m-%d %H:%M:%S}}<br>{column}: %{{y:.2f}}<extra></extra>"
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df[column],
                    mode='lines',
                    name=column,
                    line=dict(color=self.color_palette[color_idx], width=2),
                    hovertemplate=hover_template
                )
            )
        
        # レイアウトの設定
        fig.update_layout(
            title=title,
            xaxis=dict(
                title='時間',
                tickformat='%H:%M:%S',
                showgrid=True,
                gridcolor='rgba(220, 220, 220, 0.25)'
            ),
            yaxis=dict(
                title=available_columns[0] if len(available_columns) == 1 else 'Value',
                showgrid=True,
                gridcolor='rgba(220, 220, 220, 0.25)'
            ),
            hovermode='closest',
            height=height,
            width=width,
            margin=dict(l=40, r=40, t=50, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template="plotly_white"
        )
        
        # 選択ツールを有効化
        fig.update_layout(
            dragmode='select',
            selectdirection='h',
            # モバイル対応の調整
            autosize=True
        )
        
        return fig
    
    def create_multi_metric_chart(self, container: GPSDataContainer, 
                                  metrics: List[str] = ['speed', 'course'],
                                  title: str = 'パフォーマンス多変量チャート',
                                  height: int = 500,
                                  width: int = 800) -> go.Figure:
        """
        複数メトリクスを表示するサブプロット形式のチャートを作成
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        metrics : List[str], optional
            表示するメトリクスのリスト
        title : str, optional
            チャートのタイトル
        height : int, optional
            チャートの高さ
        width : int, optional
            チャートの幅
            
        Returns
        -------
        go.Figure
            作成されたサブプロットのFigureオブジェクト
        """
        # データフレームの取得
        df = container.data
        
        # 利用可能なメトリクスを取得
        available_metrics = [metric for metric in metrics if metric in df.columns]
        
        if not available_metrics:
            # 適切なメトリクスがない場合はエラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{title} - データなし",
                height=height,
                width=width,
                annotations=[
                    dict(
                        text="指定されたメトリクスがデータに含まれていません",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5
                    )
                ]
            )
            return fig
        
        # サブプロットの作成
        rows = len(available_metrics)
        fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.02,
                           subplot_titles=available_metrics)
        
        # 各メトリクスのトレースを追加
        for i, metric in enumerate(available_metrics):
            row = i + 1
            color_idx = i % len(self.color_palette)
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df[metric],
                    mode='lines',
                    name=metric,
                    line=dict(color=self.color_palette[color_idx], width=2),
                    hovertemplate=f"%{{x|%Y-%m-%d %H:%M:%S}}<br>{metric}: %{{y:.2f}}<extra></extra>"
                ),
                row=row, col=1
            )
        
        # レイアウトの設定
        fig.update_layout(
            title=title,
            height=height,
            width=width,
            margin=dict(l=40, r=40, t=50, b=40),
            showlegend=False,
            template="plotly_white"
        )
        
        # 各サブプロットのX軸とY軸の設定
        for i in range(rows):
            fig.update_xaxes(
                showgrid=True,
                gridcolor='rgba(220, 220, 220, 0.25)',
                row=i+1, col=1
            )
            
            fig.update_yaxes(
                title_text=available_metrics[i],
                showgrid=True,
                gridcolor='rgba(220, 220, 220, 0.25)',
                row=i+1, col=1
            )
        
        # 最下部サブプロットのX軸ラベルを設定
        fig.update_xaxes(
            title_text="時間",
            tickformat='%H:%M:%S',
            row=rows, col=1
        )
        
        # ホバーモードを設定
        fig.update_layout(hovermode='x unified')
        
        return fig
    
    def create_polar_chart(self, container: GPSDataContainer, 
                          value_column: str = 'speed', 
                          angle_column: str = 'course',
                          title: str = '極座標パフォーマンスチャート',
                          height: int = 500,
                          width: int = 500) -> go.Figure:
        """
        極座標チャートを作成 (例: 風向別の速度)
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        value_column : str, optional
            値を示す列名 (半径方向に表示)
        angle_column : str, optional
            角度を示す列名 (角度方向に表示)
        title : str, optional
            チャートのタイトル
        height : int, optional
            チャートの高さ
        width : int, optional
            チャートの幅
            
        Returns
        -------
        go.Figure
            作成された極座標チャートのFigureオブジェクト
        """
        # データフレームの取得
        df = container.data
        
        # 指定された列が存在するか確認
        if value_column not in df.columns or angle_column not in df.columns:
            # 適切な列がない場合はエラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{title} - データなし",
                height=height,
                width=width,
                annotations=[
                    dict(
                        text=f"必要な列がデータに含まれていません ({value_column}, {angle_column})",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5
                    )
                ]
            )
            return fig
        
        # 方向を角度（ラジアン）に変換
        theta = np.radians(df[angle_column])
        
        # 値の取得
        r = df[value_column]
        
        # 極座標チャートの作成
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatterpolar(
                r=r,
                theta=theta,
                mode='markers',
                marker=dict(
                    color=r,
                    size=5,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(
                        title=value_column
                    )
                ),
                name=value_column,
                hovertemplate=f"{angle_column}: %{{theta}}<br>{value_column}: %{{r:.2f}}<extra></extra>"
            )
        )
        
        # レイアウトの設定
        fig.update_layout(
            title=title,
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(r) * 1.1]
                ),
                angularaxis=dict(
                    tickmode='array',
                    tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                    ticktext=['0°', '45°', '90°', '135°', '180°', '225°', '270°', '315°']
                )
            ),
            height=height,
            width=width,
            template="plotly_white"
        )
        
        return fig
    
    def create_comparison_chart(self, 
                               containers: List[GPSDataContainer],
                               metric: str = 'speed',
                               names: Optional[List[str]] = None,
                               title: str = '比較チャート',
                               height: int = 400,
                               width: int = 800) -> go.Figure:
        """
        複数のデータセット間の比較チャートを作成
        
        Parameters
        ----------
        containers : List[GPSDataContainer]
            比較するGPSデータコンテナのリスト
        metric : str, optional
            比較する指標の列名
        names : Optional[List[str]], optional
            データセットの名前リスト（省略時はコンテナIDを使用）
        title : str, optional
            チャートのタイトル
        height : int, optional
            チャートの高さ
        width : int, optional
            チャートの幅
            
        Returns
        -------
        go.Figure
            作成された比較チャートのFigureオブジェクト
        """
        # コンテナが空の場合
        if not containers:
            fig = go.Figure()
            fig.update_layout(
                title=f"{title} - データなし",
                height=height,
                width=width,
                annotations=[
                    dict(
                        text="比較するデータセットがありません",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5
                    )
                ]
            )
            return fig
        
        # 名前リストの確認
        if names is None:
            names = [f"データセット {i+1}" for i in range(len(containers))]
        elif len(names) < len(containers):
            # 名前が足りない場合は自動生成して補完
            names = names + [f"データセット {i+1}" for i in range(len(names), len(containers))]
        
        # チャートの作成
        fig = go.Figure()
        
        # 各コンテナのデータを追加
        for i, container in enumerate(containers):
            df = container.data
            
            # 指定された列が存在するか確認
            if metric not in df.columns:
                continue
            
            color_idx = i % len(self.color_palette)
            
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df[metric],
                    mode='lines',
                    name=names[i],
                    line=dict(color=self.color_palette[color_idx], width=2),
                    hovertemplate=f"{names[i]}<br>%{{x|%Y-%m-%d %H:%M:%S}}<br>{metric}: %{{y:.2f}}<extra></extra>"
                )
            )
        
        # レイアウトの設定
        fig.update_layout(
            title=title,
            xaxis=dict(
                title='時間',
                tickformat='%H:%M:%S',
                showgrid=True,
                gridcolor='rgba(220, 220, 220, 0.25)'
            ),
            yaxis=dict(
                title=metric,
                showgrid=True,
                gridcolor='rgba(220, 220, 220, 0.25)'
            ),
            hovermode='closest',
            height=height,
            width=width,
            margin=dict(l=40, r=40, t=50, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            template="plotly_white"
        )
        
        return fig
    
    def create_histogram_chart(self, 
                              container: GPSDataContainer,
                              column: str = 'speed',
                              title: str = 'ヒストグラム',
                              height: int = 400,
                              width: int = 600,
                              nbins: int = 20) -> go.Figure:
        """
        ヒストグラムチャートを作成
        
        Parameters
        ----------
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        column : str, optional
            ヒストグラムを作成する列名
        title : str, optional
            チャートのタイトル
        height : int, optional
            チャートの高さ
        width : int, optional
            チャートの幅
        nbins : int, optional
            ビンの数
            
        Returns
        -------
        go.Figure
            作成されたヒストグラムのFigureオブジェクト
        """
        # データフレームの取得
        df = container.data
        
        # 指定された列が存在するか確認
        if column not in df.columns:
            # 適切な列がない場合はエラーメッセージを表示
            fig = go.Figure()
            fig.update_layout(
                title=f"{title} - データなし",
                height=height,
                width=width,
                annotations=[
                    dict(
                        text=f"指定された列がデータに含まれていません ({column})",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.5,
                        y=0.5
                    )
                ]
            )
            return fig
        
        # ヒストグラムの作成
        fig = go.Figure()
        
        fig.add_trace(
            go.Histogram(
                x=df[column],
                nbinsx=nbins,
                marker_color=self.color_palette[0],
                opacity=0.7,
                hovertemplate=f"{column}: %{{x}}<br>頻度: %{{y}}<extra></extra>"
            )
        )
        
        # 統計情報の計算
        mean_val = df[column].mean()
        median_val = df[column].median()
        max_val = df[column].max()
        
        # 統計線の追加
        fig.add_vline(x=mean_val, line_width=2, line_dash="dash", line_color="red",
                     annotation_text=f"平均: {mean_val:.2f}", annotation_position="top left")
        fig.add_vline(x=median_val, line_width=2, line_dash="dash", line_color="green",
                     annotation_text=f"中央値: {median_val:.2f}", annotation_position="top right")
        
        # レイアウトの設定
        fig.update_layout(
            title=title,
            xaxis=dict(
                title=column,
                showgrid=True,
                gridcolor='rgba(220, 220, 220, 0.25)'
            ),
            yaxis=dict(
                title='頻度',
                showgrid=True,
                gridcolor='rgba(220, 220, 220, 0.25)'
            ),
            height=height,
            width=width,
            margin=dict(l=40, r=40, t=50, b=40),
            template="plotly_white"
        )
        
        return fig
    
    def render_time_series(self, 
                          container_id: str,
                          y_columns: List[str],
                          title: Optional[str] = None,
                          height: int = 400,
                          width: Optional[int] = None,
                          key: Optional[str] = None) -> bool:
        """
        時系列チャートをStreamlitに表示
        
        Parameters
        ----------
        container_id : str
            データコンテナのID
        y_columns : List[str]
            Y軸に表示する列のリスト
        title : Optional[str], optional
            チャートのタイトル（Noneの場合はコンテナIDを使用）
        height : int, optional
            チャートの高さ
        width : Optional[int], optional
            チャートの幅（Noneの場合は自動調整）
        key : Optional[str], optional
            Streamlitコンポーネントのキー
            
        Returns
        -------
        bool
            表示成功時はTrue、失敗時はFalse
        """
        # コンテナの取得
        container = self.data_binding.get_container(container_id)
        
        if container is None or not isinstance(container, GPSDataContainer):
            st.error(f"有効なGPSデータコンテナが見つかりません: {container_id}")
            return False
        
        # タイトルの設定
        if title is None:
            title = f"{container_id} パフォーマンスチャート"
        
        # キャッシュキーの生成
        cache_key = f"time_series_{container_id}_{'-'.join(y_columns)}_{height}_{width}"
        
        # キャッシュに存在する場合はそれを使用
        if cache_key in self._chart_cache:
            fig = self._chart_cache[cache_key]
        else:
            # 新規に作成
            fig = self.create_time_series_chart(
                container=container,
                y_columns=y_columns,
                title=title,
                height=height,
                width=width or 800
            )
            # キャッシュに保存
            self._chart_cache[cache_key] = fig
        
        # Streamlitに表示
        st.plotly_chart(fig, use_container_width=width is None, key=key)
        
        return True
    
    def render_multi_metric(self, 
                           container_id: str,
                           metrics: List[str] = ['speed', 'course'],
                           title: Optional[str] = None,
                           height: int = 500,
                           width: Optional[int] = None,
                           key: Optional[str] = None) -> bool:
        """
        複数メトリクスのサブプロットチャートをStreamlitに表示
        
        Parameters
        ----------
        container_id : str
            データコンテナのID
        metrics : List[str], optional
            表示するメトリクスのリスト
        title : Optional[str], optional
            チャートのタイトル（Noneの場合はコンテナIDを使用）
        height : int, optional
            チャートの高さ
        width : Optional[int], optional
            チャートの幅（Noneの場合は自動調整）
        key : Optional[str], optional
            Streamlitコンポーネントのキー
            
        Returns
        -------
        bool
            表示成功時はTrue、失敗時はFalse
        """
        # コンテナの取得
        container = self.data_binding.get_container(container_id)
        
        if container is None or not isinstance(container, GPSDataContainer):
            st.error(f"有効なGPSデータコンテナが見つかりません: {container_id}")
            return False
        
        # タイトルの設定
        if title is None:
            title = f"{container_id} 多変量パフォーマンス"
        
        # キャッシュキーの生成
        cache_key = f"multi_metric_{container_id}_{'-'.join(metrics)}_{height}_{width}"
        
        # キャッシュに存在する場合はそれを使用
        if cache_key in self._chart_cache:
            fig = self._chart_cache[cache_key]
        else:
            # 新規に作成
            fig = self.create_multi_metric_chart(
                container=container,
                metrics=metrics,
                title=title,
                height=height,
                width=width or 800
            )
            # キャッシュに保存
            self._chart_cache[cache_key] = fig
        
        # Streamlitに表示
        st.plotly_chart(fig, use_container_width=width is None, key=key)
        
        return True
    
    def render_comparison(self, 
                         container_ids: List[str],
                         metric: str = 'speed',
                         title: Optional[str] = None,
                         height: int = 400,
                         width: Optional[int] = None,
                         key: Optional[str] = None) -> bool:
        """
        複数データセットの比較チャートをStreamlitに表示
        
        Parameters
        ----------
        container_ids : List[str]
            比較するデータコンテナのIDリスト
        metric : str, optional
            比較する指標の列名
        title : Optional[str], optional
            チャートのタイトル
        height : int, optional
            チャートの高さ
        width : Optional[int], optional
            チャートの幅（Noneの場合は自動調整）
        key : Optional[str], optional
            Streamlitコンポーネントのキー
            
        Returns
        -------
        bool
            表示成功時はTrue、失敗時はFalse
        """
        # コンテナの取得
        containers = []
        names = []
        
        for container_id in container_ids:
            container = self.data_binding.get_container(container_id)
            if container is not None and isinstance(container, GPSDataContainer):
                containers.append(container)
                names.append(container_id)
        
        if not containers:
            st.error("有効なGPSデータコンテナが見つかりません")
            return False
        
        # タイトルの設定
        if title is None:
            title = f"{metric} 比較"
        
        # キャッシュキーの生成
        cache_key = f"comparison_{'_'.join(container_ids)}_{metric}_{height}_{width}"
        
        # キャッシュに存在する場合はそれを使用
        if cache_key in self._chart_cache:
            fig = self._chart_cache[cache_key]
        else:
            # 新規に作成
            fig = self.create_comparison_chart(
                containers=containers,
                metric=metric,
                names=names,
                title=title,
                height=height,
                width=width or 800
            )
            # キャッシュに保存
            self._chart_cache[cache_key] = fig
        
        # Streamlitに表示
        st.plotly_chart(fig, use_container_width=width is None, key=key)
        
        return True
    
    def invalidate_cache(self) -> None:
        """キャッシュを無効化"""
        self._chart_cache = {}
