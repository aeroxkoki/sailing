"""
ui.components.visualizations.wind_field_view

風の場可視化コンポーネント - 風向風速データを地図上に表示するためのコンポーネント
"""

import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
import colorsys
from sailing_data_processor.data_model.container import GPSDataContainer, WindDataContainer
from ui.data_binding import DataBindingManager, UIStateManager
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class WindFieldViewComponent:
    """
    風の場可視化用のコンポーネント
    
    風向風速データを地図上に可視化するためのコンポーネントです。
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
        
        # カラーマップ
        self.colorscales = {
            'wind_speed': 'Blues',
            'wind_direction': 'HSV',
            'wind_shift': 'RdBu',
            'wind_gust': 'YlOrRd'
        }
    
    def create_wind_field_map(self, 
                           wind_data: Dict[str, Any],
                           center: Optional[Tuple[float, float]] = None,
                           zoom_start: int = 13,
                           tile: str = 'CartoDB positron') -> folium.Map:
        """
        風の場を表示するマップを作成
        
        Parameters
        ----------
        wind_data : Dict[str, Any]
            風の場データ
            {'positions': [(lat, lon), ...], 'directions': [dir, ...], 'speeds': [speed, ...]}
        center : Optional[Tuple[float, float]], optional
            地図の中心座標 (緯度, 経度)
        zoom_start : int, optional
            初期ズームレベル
        tile : str, optional
            地図タイル名
            
        Returns
        -------
        folium.Map
            作成されたマップオブジェクト
        """
        # 風データから中心座標を計算（もし指定がなければ）
        if center is None:
            positions = wind_data.get('positions', [])
            if positions:
                lats = [pos[0] for pos in positions]
                lons = [pos[1] for pos in positions]
                center = (np.mean(lats), np.mean(lons))
            else:
                center = (35.45, 139.65)  # デフォルト: 東京湾
        
        # マップオブジェクトの作成
        m = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles=tile,
            control_scale=True
        )
        
        # 風の格子データを取得
        positions = wind_data.get('positions', [])
        directions = wind_data.get('directions', [])
        speeds = wind_data.get('speeds', [])
        
        # データ数の確認
        n_points = min(len(positions), len(directions), len(speeds))
        
        if n_points == 0:
            # 風データがない場合
            folium.Marker(
                location=center,
                popup="風データがありません",
                icon=folium.Icon(icon="exclamation-sign", color="red")
            ).add_to(m)
            return m
        
        # 風速の最大値と最小値
        max_speed = max(speeds) if speeds else 1.0
        min_speed = min(speeds) if speeds else 0.0
        
        # 凡例の作成
        legend_html = self._create_wind_legend(min_speed, max_speed)
        
        # 凡例をマップに追加
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 風矢印レイヤーの作成
        wind_layer = folium.FeatureGroup(name="風の場")
        
        # 風矢印を各格子点に配置
        for i in range(n_points):
            lat, lon = positions[i]
            direction = directions[i]
            speed = speeds[i]
            
            # 風速に応じた色の調整
            intensity = (speed - min_speed) / (max_speed - min_speed) if max_speed > min_speed else 0.5
            rgb = colorsys.hsv_to_rgb(0.6, 0.8, 0.5 + 0.5 * intensity)  # 青から水色へのグラデーション
            arrow_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            
            # 矢印の向きを計算
            arrow_angle = (90 - direction) % 360
            
            # 矢印の長さを風速に比例させる
            length = 3 + 7 * intensity  # 3〜10の範囲でスケール
            
            # 矢印を追加
            folium.RegularPolygonMarker(
                location=[lat, lon],
                number_of_sides=3,
                rotation=arrow_angle,
                radius=length,
                color=arrow_color,
                fill_color=arrow_color,
                fill_opacity=0.7,
                popup=f"風向: {direction}°, 風速: {speed}ノット"
            ).add_to(wind_layer)
        
        # レイヤーをマップに追加
        wind_layer.add_to(m)
        
        return m
    
    def create_wind_trend_chart(self, 
                              wind_container: WindDataContainer,
                              time_range: Optional[Tuple[datetime, datetime]] = None) -> go.Figure:
        """
        風向風速の時間変化チャートを作成
        
        Parameters
        ----------
        wind_container : WindDataContainer
            風データを含むコンテナ
        time_range : Optional[Tuple[datetime, datetime]], optional
            表示する時間範囲
            
        Returns
        -------
        go.Figure
            作成されたグラフオブジェクト
        """
        # 風データを取得
        wind_data = wind_container.data
        
        # 時系列データフレームの作成
        if isinstance(wind_data, dict) and 'timestamp' in wind_data:
            # 単一の風データポイント
            df = pd.DataFrame({
                'timestamp': [wind_data['timestamp']],
                'direction': [wind_data['direction']],
                'speed': [wind_data['speed']]
            })
        elif isinstance(wind_data, pd.DataFrame):
            # 複数の風データポイント
            df = wind_data
        else:
            # 対応していないフォーマット
            fig = go.Figure()
            fig.add_annotation(
                text="対応していない風データフォーマットです",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # 時間範囲でフィルタリング（もし指定があれば）
        if time_range and 'timestamp' in df.columns:
            start_time, end_time = time_range
            df = df[(df['timestamp'] >= start_time) & (df['timestamp'] <= end_time)]
        
        # データが空の場合
        if len(df) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="指定された時間範囲に風データがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # サブプロットの作成（2行1列：上が風向、下が風速）
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=("風向の時間変化", "風速の時間変化")
        )
        
        # 風向のプロット
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['direction'],
                mode='lines+markers',
                name='風向',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        # 風速のプロット
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['speed'],
                mode='lines+markers',
                name='風速',
                line=dict(color='red', width=2)
            ),
            row=2, col=1
        )
        
        # レイアウトの設定
        fig.update_layout(
            height=500,
            margin=dict(l=0, r=0, t=50, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            hovermode="x unified"
        )
        
        # 軸の設定
        fig.update_yaxes(title_text="風向 (度)", range=[0, 360], row=1, col=1)
        fig.update_yaxes(title_text="風速 (ノット)", row=2, col=1)
        fig.update_xaxes(title_text="時間", row=2, col=1)
        
        return fig
    
    def create_wind_rose(self, wind_container: WindDataContainer) -> go.Figure:
        """
        風配図（ウィンドローズ）を作成
        
        Parameters
        ----------
        wind_container : WindDataContainer
            風データを含むコンテナ
            
        Returns
        -------
        go.Figure
            作成されたグラフオブジェクト
        """
        # 風データを取得
        wind_data = wind_container.data
        
        # データフレームの作成
        if isinstance(wind_data, dict) and 'direction' in wind_data:
            # 単一の風データポイント - 風配図は意味がない
            fig = go.Figure()
            fig.add_annotation(
                text="風配図の作成には複数の風データポイントが必要です",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=16)
            )
            return fig
        elif isinstance(wind_data, pd.DataFrame):
            # 複数の風データポイント
            df = wind_data
        else:
            # 対応していないフォーマット
            fig = go.Figure()
            fig.add_annotation(
                text="対応していない風データフォーマットです",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # 必要な列があるか確認
        if 'direction' not in df.columns or 'speed' not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="風向または風速データがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # 風向を16方位に分類
        bin_size = 360 / 16
        direction_bins = np.arange(0, 360 + bin_size, bin_size)
        direction_labels = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                          'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
        
        # 風速を分類（0-5, 5-10, 10-15, 15-20, 20+）
        speed_bins = [0, 5, 10, 15, 20, np.inf]
        speed_labels = ['0-5', '5-10', '10-15', '15-20', '20+']
        
        # 風向を16方位に変換
        df['direction_cat'] = pd.cut(
            df['direction'] % 360, 
            bins=direction_bins, 
            labels=direction_labels,
            include_lowest=True
        )
        
        # 風速をカテゴリに変換
        df['speed_cat'] = pd.cut(
            df['speed'],
            bins=speed_bins,
            labels=speed_labels,
            include_lowest=True
        )
        
        # 風向と風速のクロス集計
        wind_rose_data = pd.crosstab(
            df['direction_cat'],
            df['speed_cat'],
            normalize='index'
        ).reset_index()
        
        # 風配図の作成
        fig = go.Figure()
        
        # 各風速カテゴリの色を設定
        colors = px.colors.sequential.Blues[1:]  # 青のグラデーション
        
        # 最も遅い風速から順にプロット（積み重ね棒グラフ）
        for i, speed_cat in enumerate(speed_labels):
            fig.add_trace(go.Barpolar(
                r=wind_rose_data[speed_cat],
                theta=wind_rose_data['direction_cat'],
                name=f'{speed_cat} ノット',
                marker_color=colors[i],
                hovertemplate='%{theta}: %{r:.1%}<br>%{fullData.name}<extra></extra>'
            ))
        
        # レイアウトの設定
        fig.update_layout(
            title='風配図',
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    tickformat='%'
                ),
                angularaxis=dict(
                    direction='clockwise',
                    rotation=90,  # 北が上になるように回転
                    categoryorder='array',
                    categoryarray=direction_labels
                )
            ),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
            height=500,
            width=500
        )
        
        return fig
    
    def create_wind_shift_heatmap(self, 
                                wind_data: pd.DataFrame, 
                                time_resolution: str = '1H',
                                direction_bins: int = 8) -> go.Figure:
        """
        風向シフトのヒートマップを作成
        
        Parameters
        ----------
        wind_data : pd.DataFrame
            風データを含むデータフレーム
        time_resolution : str, optional
            時間方向の解像度
        direction_bins : int, optional
            風向を何分割するか
            
        Returns
        -------
        go.Figure
            作成されたグラフオブジェクト
        """
        # 必要な列があるか確認
        if 'timestamp' not in wind_data.columns or 'direction' not in wind_data.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="タイムスタンプまたは風向データがありません",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            return fig
        
        # 時間でリサンプリング
        df = wind_data.copy()
        df.set_index('timestamp', inplace=True)
        
        # 風向を指定されたビン数に分類
        bin_size = 360 / direction_bins
        bins = np.arange(0, 360 + bin_size, bin_size)
        
        # 各時間帯での風向頻度をカウント
        freq_df = pd.DataFrame()
        
        # 各ビンの度数分布を計算
        for i in range(len(bins) - 1):
            bin_label = f"{bins[i]:.0f}°-{bins[i+1]:.0f}°"
            mask = (df['direction'] >= bins[i]) & (df['direction'] < bins[i+1])
            freq_df[bin_label] = mask.resample(time_resolution).mean()
        
        # NaNを0に置換
        freq_df.fillna(0, inplace=True)
        
        # ヒートマップの作成
        fig = go.Figure(data=go.Heatmap(
            z=freq_df.values,
            x=freq_df.columns,
            y=freq_df.index.strftime('%Y-%m-%d %H:%M'),
            colorscale='Blues',
            colorbar=dict(title='頻度'),
            hoverongaps=False,
            hovertemplate='時間: %{y}<br>風向: %{x}<br>頻度: %{z:.2f}<extra></extra>'
        ))
        
        # レイアウトの設定
        fig.update_layout(
            title='風向シフトのヒートマップ',
            xaxis_title='風向',
            yaxis_title='時間',
            xaxis=dict(
                tickangle=-45,
                tickmode='array',
                tickvals=list(range(len(freq_df.columns))),
                ticktext=freq_df.columns
            ),
            height=500,
            margin=dict(l=0, r=0, t=50, b=0)
        )
        
        return fig
    
    def create_wind_interpolation_map(self, 
                                    gps_data: pd.DataFrame,
                                    wind_grid: Dict[str, Any],
                                    center: Optional[Tuple[float, float]] = None,
                                    zoom_start: int = 13) -> folium.Map:
        """
        GPSトラックと風補間マップを作成
        
        Parameters
        ----------
        gps_data : pd.DataFrame
            GPSトラックデータ
        wind_grid : Dict[str, Any]
            風の格子データ
        center : Optional[Tuple[float, float]], optional
            地図の中心座標
        zoom_start : int, optional
            初期ズームレベル
            
        Returns
        -------
        folium.Map
            作成されたマップオブジェクト
        """
        # 中心座標の計算（指定がなければ）
        if center is None:
            if 'latitude' in gps_data.columns and 'longitude' in gps_data.columns:
                center = (gps_data['latitude'].mean(), gps_data['longitude'].mean())
            else:
                positions = wind_grid.get('positions', [])
                if positions:
                    lats = [pos[0] for pos in positions]
                    lons = [pos[1] for pos in positions]
                    center = (np.mean(lats), np.mean(lons))
                else:
                    center = (35.45, 139.65)  # デフォルト: 東京湾
        
        # マップオブジェクトの作成
        m = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles='CartoDB positron',  # 海図風の明るい背景
            control_scale=True
        )
        
        # GPSトラックレイヤー
        track_layer = folium.FeatureGroup(name="GPSトラック")
        
        # GPSトラックを追加（もしデータがあれば）
        if 'latitude' in gps_data.columns and 'longitude' in gps_data.columns:
            track_points = list(zip(gps_data['latitude'], gps_data['longitude']))
            
            # トラックラインを追加
            folium.PolyLine(
                track_points,
                color='red',
                weight=3,
                opacity=0.7,
                tooltip="GPSトラック"
            ).add_to(track_layer)
            
            # 始点と終点のマーカー
            if track_points:
                # スタートマーカー
                folium.Marker(
                    track_points[0],
                    tooltip="スタート",
                    icon=folium.Icon(color='green', icon='play', prefix='fa')
                ).add_to(track_layer)
                
                # ゴールマーカー
                folium.Marker(
                    track_points[-1],
                    tooltip="ゴール",
                    icon=folium.Icon(color='red', icon='stop', prefix='fa')
                ).add_to(track_layer)
        
        # トラックレイヤーをマップに追加
        track_layer.add_to(m)
        
        # 風の格子データレイヤー
        wind_layer = folium.FeatureGroup(name="風の場")
        
        # 風の格子データを取得
        positions = wind_grid.get('positions', [])
        directions = wind_grid.get('directions', [])
        speeds = wind_grid.get('speeds', [])
        
        # データ数の確認
        n_points = min(len(positions), len(directions), len(speeds))
        
        if n_points > 0:
            # 風速の最大値と最小値
            max_speed = max(speeds)
            min_speed = min(speeds)
            
            # 風矢印を各格子点に配置
            for i in range(n_points):
                lat, lon = positions[i]
                direction = directions[i]
                speed = speeds[i]
                
                # 風速に応じた色の調整
                intensity = (speed - min_speed) / (max_speed - min_speed) if max_speed > min_speed else 0.5
                rgb = colorsys.hsv_to_rgb(0.6, 0.8, 0.5 + 0.5 * intensity)  # 青から水色へのグラデーション
                arrow_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
                
                # 矢印の向きを計算
                arrow_angle = (90 - direction) % 360
                
                # 矢印の長さを風速に比例させる
                length = 3 + 7 * intensity  # 3〜10の範囲でスケール
                
                # 矢印を追加
                folium.RegularPolygonMarker(
                    location=[lat, lon],
                    number_of_sides=3,
                    rotation=arrow_angle,
                    radius=length,
                    color=arrow_color,
                    fill_color=arrow_color,
                    fill_opacity=0.7,
                    popup=f"風向: {direction}°, 風速: {speed}ノット"
                ).add_to(wind_layer)
            
            # 凡例の作成
            legend_html = self._create_wind_legend(min_speed, max_speed)
            
            # 凡例をマップに追加
            m.get_root().html.add_child(folium.Element(legend_html))
        
        # 風レイヤーをマップに追加
        wind_layer.add_to(m)
        
        # レイヤーコントロールを追加
        folium.LayerControl().add_to(m)
        
        return m
    
    def create_wind_comparison_chart(self, 
                                   wind_data1: pd.DataFrame, 
                                   wind_data2: pd.DataFrame,
                                   name1: str = 'データ1',
                                   name2: str = 'データ2') -> go.Figure:
        """
        2つの風データを比較するチャートを作成
        
        Parameters
        ----------
        wind_data1 : pd.DataFrame
            1つ目の風データ
        wind_data2 : pd.DataFrame
            2つ目の風データ
        name1 : str, optional
            1つ目のデータの名前
        name2 : str, optional
            2つ目のデータの名前
            
        Returns
        -------
        go.Figure
            作成されたグラフオブジェクト
        """
        # 必要な列があるか確認
        required_cols = ['timestamp', 'direction', 'speed']
        
        for col in required_cols:
            if col not in wind_data1.columns or col not in wind_data2.columns:
                fig = go.Figure()
                fig.add_annotation(
                    text=f"必要なカラム '{col}' がデータにありません",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=20)
                )
                return fig
        
        # サブプロットの作成（2行1列）
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            subplot_titles=("風向の比較", "風速の比較")
        )
        
        # 風向の比較
        fig.add_trace(
            go.Scatter(
                x=wind_data1['timestamp'],
                y=wind_data1['direction'],
                mode='lines',
                name=f'{name1} (風向)',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=wind_data2['timestamp'],
                y=wind_data2['direction'],
                mode='lines',
                name=f'{name2} (風向)',
                line=dict(color='red')
            ),
            row=1, col=1
        )
        
        # 風速の比較
        fig.add_trace(
            go.Scatter(
                x=wind_data1['timestamp'],
                y=wind_data1['speed'],
                mode='lines',
                name=f'{name1} (風速)',
                line=dict(color='blue')
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=wind_data2['timestamp'],
                y=wind_data2['speed'],
                mode='lines',
                name=f'{name2} (風速)',
                line=dict(color='red')
            ),
            row=2, col=1
        )
        
        # レイアウトの設定
        fig.update_layout(
            height=600,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            hovermode="x unified"
        )
        
        # 軸の設定
        fig.update_yaxes(title_text="風向 (度)", range=[0, 360], row=1, col=1)
        fig.update_yaxes(title_text="風速 (ノット)", row=2, col=1)
        fig.update_xaxes(title_text="時間", row=2, col=1)
        
        return fig
    
    def render_wind_field_map(self, wind_container: WindDataContainer, width: int = 800, height: int = 600) -> None:
        """
        風の場マップをStreamlitに表示
        
        Parameters
        ----------
        wind_container : WindDataContainer
            風データを含むコンテナ
        width : int, optional
            表示幅
        height : int, optional
            表示高さ
        """
        # 風データからグリッドデータを作成
        wind_grid = self._create_wind_grid_from_container(wind_container)
        
        # マップを作成
        map_obj = self.create_wind_field_map(wind_grid)
        
        # マップを表示
        folium_static(map_obj, width=width, height=height)
    
    def render_wind_dashboard(self, wind_container: WindDataContainer) -> None:
        """
        風データダッシュボードをStreamlitに表示
        
        Parameters
        ----------
        wind_container : WindDataContainer
            風データを含むコンテナ
        """
        # 風データを取得
        wind_data = wind_container.data
        
        # 風データをデータフレームに変換
        if isinstance(wind_data, dict):
            df = pd.DataFrame([wind_data])
        elif isinstance(wind_data, pd.DataFrame):
            df = wind_data
        else:
            st.error("対応していない風データフォーマットです")
            return
        
        # ダッシュボードのレイアウト
        st.subheader("風データダッシュボード")
        
        # メトリクス概要を表示
        self._render_wind_metrics(df)
        
        # 風の場と風配図を2列で表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("風の場")
            wind_grid = self._create_wind_grid_from_dataframe(df)
            map_obj = self.create_wind_field_map(wind_grid)
            folium_static(map_obj, width=400, height=400)
        
        with col2:
            st.subheader("風配図")
            fig = self.create_wind_rose(wind_container)
            st.plotly_chart(fig, use_container_width=True)
        
        # 時系列チャートを表示
        st.subheader("風向風速の時間変化")
        fig = self.create_wind_trend_chart(wind_container)
        st.plotly_chart(fig, use_container_width=True)
        
        # 風向シフトのヒートマップを表示
        st.subheader("風向シフトの分析")
        if len(df) > 10:  # データが十分にある場合のみ
            fig = self.create_wind_shift_heatmap(df)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("風向シフト分析にはより多くのデータポイントが必要です")
    
    def _create_wind_grid_from_container(self, wind_container: WindDataContainer) -> Dict[str, Any]:
        """
        WindDataContainerから風の格子データを作成
        
        Parameters
        ----------
        wind_container : WindDataContainer
            風データを含むコンテナ
            
        Returns
        -------
        Dict[str, Any]
            風の格子データ
        """
        wind_data = wind_container.data
        
        if isinstance(wind_data, dict):
            # 単一の風データポイント
            if 'position' in wind_data:
                lat = wind_data['position'].get('latitude', 0.0)
                lon = wind_data['position'].get('longitude', 0.0)
            else:
                # 位置情報がない場合
                st.warning("風データに位置情報がありません。デフォルトの位置を使用します。")
                lat, lon = 35.45, 139.65
            
            # 方向と速度を抽出
            direction = wind_data.get('direction', 0.0)
            speed = wind_data.get('speed', 0.0)
            
            return {
                'positions': [(lat, lon)],
                'directions': [direction],
                'speeds': [speed]
            }
        
        elif isinstance(wind_data, pd.DataFrame):
            return self._create_wind_grid_from_dataframe(wind_data)
        
        else:
            # 対応していないフォーマット
            st.warning("対応していない風データフォーマットです")
            return {'positions': [], 'directions': [], 'speeds': []}
    
    def _create_wind_grid_from_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        データフレームから風の格子データを作成
        
        Parameters
        ----------
        df : pd.DataFrame
            風データを含むデータフレーム
            
        Returns
        -------
        Dict[str, Any]
            風の格子データ
        """
        # 必要な列があるか確認
        if 'direction' not in df.columns or 'speed' not in df.columns:
            st.warning("風データに方向または速度の情報がありません")
            return {'positions': [], 'directions': [], 'speeds': []}
        
        # 位置情報の確認
        has_position = 'latitude' in df.columns and 'longitude' in df.columns
        
        if not has_position:
            # 位置情報がない場合はデフォルト位置を使用
            st.warning("風データに位置情報がありません。デフォルトの位置を使用します。")
            positions = [(35.45, 139.65)] * len(df)
        else:
            positions = list(zip(df['latitude'], df['longitude']))
        
        # 方向と速度を抽出
        directions = df['direction'].tolist()
        speeds = df['speed'].tolist()
        
        return {
            'positions': positions,
            'directions': directions,
            'speeds': speeds
        }
    
    def _create_wind_legend(self, min_speed: float, max_speed: float) -> str:
        """
        風速の凡例HTMLを作成
        
        Parameters
        ----------
        min_speed : float
            最小風速
        max_speed : float
            最大風速
            
        Returns
        -------
        str
            凡例のHTML文字列
        """
        # 風速の範囲を5分割
        steps = 5
        speed_range = np.linspace(min_speed, max_speed, steps)
        
        # 色のグラデーションを生成
        colors = []
        for i in range(steps):
            intensity = i / (steps - 1)
            rgb = colorsys.hsv_to_rgb(0.6, 0.8, 0.5 + 0.5 * intensity)
            color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            colors.append(color)
        
        # 凡例HTML
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 150px; height: 160px; 
                    border:2px solid grey; z-index:9999; font-size:12px;
                    background-color: white; padding: 10px; border-radius: 5px;">
            <div style="text-align: center; margin-bottom: 5px;">
                <span style="font-weight: bold;">風速 (ノット)</span>
            </div>
        '''
        
        # 色のグラデーションと対応する風速を表示
        for i in range(steps - 1, -1, -1):
            legend_html += f'''
            <div style="display: flex; align-items: center; margin-bottom: 5px;">
                <div style="background-color: {colors[i]}; width: 20px; height: 20px; margin-right: 5px;"></div>
                <span>{speed_range[i]:.1f}</span>
            </div>
            '''
        
        legend_html += '</div>'
        
        return legend_html
    
    def _render_wind_metrics(self, df: pd.DataFrame) -> None:
        """
        風のメトリクス情報を表示
        
        Parameters
        ----------
        df : pd.DataFrame
            風データを含むデータフレーム
        """
        # 必要な列があるか確認
        if 'direction' not in df.columns or 'speed' not in df.columns:
            st.warning("風データに方向または速度の情報がありません")
            return
        
        # 風向に関するメトリクス
        direction_values = df['direction']
        avg_direction = self._circular_mean(direction_values)
        std_direction = self._circular_std(direction_values)
        
        # 風速に関するメトリクス
        speed_values = df['speed']
        avg_speed = speed_values.mean()
        max_speed = speed_values.max()
        min_speed = speed_values.min()
        std_speed = speed_values.std()
        
        # データポイント数
        n_points = len(df)
        
        # 時間範囲（タイムスタンプがある場合）
        time_range = ""
        if 'timestamp' in df.columns:
            start_time = df['timestamp'].min()
            end_time = df['timestamp'].max()
            duration_sec = (end_time - start_time).total_seconds()
            
            if duration_sec < 60:
                time_range = f"{duration_sec:.0f}秒間"
            elif duration_sec < 3600:
                time_range = f"{duration_sec/60:.1f}分間"
            else:
                time_range = f"{duration_sec/3600:.1f}時間"
        
        # メトリクスを3列で表示
        col1, col2, col3 = st.columns(3)
        
        # 風向メトリクス
        with col1:
            st.metric("平均風向", f"{avg_direction:.1f}°", f"変動: ±{std_direction:.1f}°")
        
        # 風速メトリクス
        with col2:
            st.metric("平均風速", f"{avg_speed:.1f}ノット", f"最大: {max_speed:.1f}ノット")
        
        # データ情報
        with col3:
            st.metric("データポイント数", f"{n_points}", time_range)
    
    def _circular_mean(self, angles: pd.Series) -> float:
        """
        角度の円周平均を計算
        
        Parameters
        ----------
        angles : pd.Series
            角度データの系列（度数法）
            
        Returns
        -------
        float
            平均角度（度数法）
        """
        # ラジアンに変換
        rad = np.radians(angles)
        
        # 複素数表現で平均を計算
        x = np.mean(np.cos(rad))
        y = np.mean(np.sin(rad))
        
        # 平均角度を計算
        mean_rad = np.arctan2(y, x)
        
        # 度数法に戻して0-360の範囲に調整
        mean_deg = (np.degrees(mean_rad) + 360) % 360
        
        return mean_deg
    
    def _circular_std(self, angles: pd.Series) -> float:
        """
        角度の円周標準偏差を計算
        
        Parameters
        ----------
        angles : pd.Series
            角度データの系列（度数法）
            
        Returns
        -------
        float
            標準偏差（度数法）
        """
        # ラジアンに変換
        rad = np.radians(angles)
        
        # 複素数表現で分散を計算
        x = np.mean(np.cos(rad))
        y = np.mean(np.sin(rad))
        r = np.sqrt(x**2 + y**2)
        
        # 円周分散から標準偏差を計算
        std_rad = np.sqrt(-2 * np.log(r))
        
        # 度数法に変換
        std_deg = np.degrees(std_rad)
        
        return std_deg
