"""
ui.integrated.components.dashboard.widgets.wind_summary_widget

風向風速データのサマリーを表示するダッシュボードウィジェット
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

class WindSummaryWidget:
    """風向風速サマリーウィジェット"""
    
    def __init__(self):
        """初期化"""
        self.title = "風向風速サマリー"
    
    def render(self, wind_data):
        """
        風向風速サマリーウィジェットの描画
        
        Parameters
        ----------
        wind_data : pandas.DataFrame
            風向風速データを含むDataFrame
            timestamp, wind_direction, wind_speedカラムが必要
        """
        # カードのスタイル設定
        with st.container():
            st.write(f"### {self.title}")
            
            # 風向風速の基本統計量
            wind_speed_mean = wind_data['wind_speed'].mean()
            wind_speed_std = wind_data['wind_speed'].std()
            wind_speed_min = wind_data['wind_speed'].min()
            wind_speed_max = wind_data['wind_speed'].max()
            
            # 風向の基本統計量（円環データのため単純な平均は使えない）
            # 代わりに最も頻度の高い方向（最頻値）を使用
            wind_direction_mean = self._calculate_circular_mean(wind_data['wind_direction'])
            wind_direction_range = self._calculate_direction_range(wind_data['wind_direction'])
            
            # レイアウト: 基本情報を上部に表示
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("平均風速", f"{wind_speed_mean:.1f} kt")
            
            with col2:
                st.metric("風向", f"{wind_direction_mean:.0f}°")
            
            with col3:
                st.metric("風速範囲", f"{wind_speed_min:.1f}-{wind_speed_max:.1f} kt")
            
            # 時系列グラフ
            self._render_time_series(wind_data)
            
            # 極座標図（風配図）
            self._render_wind_rose(wind_data)
            
            # インサイトと注釈
            if len(wind_data) > 0:
                self._render_insights(wind_data)
    
    def _render_time_series(self, wind_data):
        """
        風向風速の時系列グラフを描画
        
        Parameters
        ----------
        wind_data : pandas.DataFrame
            風向風速データを含むDataFrame
        """
        # 時系列グラフ（双軸）
        fig = go.Figure()
        
        # 風速グラフ
        fig.add_trace(
            go.Scatter(
                x=wind_data['timestamp'],
                y=wind_data['wind_speed'],
                name="風速 (kt)",
                line=dict(color='blue', width=2),
                mode='lines'
            )
        )
        
        # 風向グラフ（第二軸）
        fig.add_trace(
            go.Scatter(
                x=wind_data['timestamp'],
                y=wind_data['wind_direction'],
                name="風向 (°)",
                line=dict(color='red', width=2, dash='dot'),
                mode='lines',
                yaxis="y2"
            )
        )
        
        # レイアウト設定
        fig.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
            yaxis=dict(title="風速 (kt)"),
            yaxis2=dict(
                title="風向 (°)",
                overlaying="y",
                side="right",
                range=[0, 360]
            ),
            xaxis=dict(title="時間")
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    def _render_wind_rose(self, wind_data):
        """
        風配図（極座標図）を描画
        
        Parameters
        ----------
        wind_data : pandas.DataFrame
            風向風速データを含むDataFrame
        """
        # 風向データをビン（区間）に分ける
        direction_bins = list(range(0, 361, 15))
        bin_labels = [f"{d}°" for d in range(0, 360, 15)]
        
        # 風向をビンに分類
        wind_data['direction_bin'] = pd.cut(
            wind_data['wind_direction'],
            bins=direction_bins,
            labels=bin_labels,
            include_lowest=True
        )
        
        # 風速の範囲でグループ化
        wind_data['speed_category'] = pd.cut(
            wind_data['wind_speed'],
            bins=[0, 5, 10, 15, 20, 25, 30],
            labels=['0-5 kt', '5-10 kt', '10-15 kt', '15-20 kt', '20-25 kt', '25-30 kt'],
            include_lowest=True
        )
        
        # 各方向ビンと風速カテゴリーでデータをまとめる
        direction_speed_counts = wind_data.groupby(['direction_bin', 'speed_category']).size().reset_index(name='count')
        
        # 方向ごとに風速カテゴリーの合計を計算
        direction_counts = direction_speed_counts.groupby('direction_bin')['count'].sum().reset_index()
        
        # 極座標チャートを作成
        fig = go.Figure()
        
        # 各風速カテゴリーに対して異なる色で追加
        colors = ['lightblue', 'blue', 'royalblue', 'darkblue', 'navy', 'midnightblue']
        speed_categories = ['0-5 kt', '5-10 kt', '10-15 kt', '15-20 kt', '20-25 kt', '25-30 kt']
        
        # 風速カテゴリーごとにバーを追加
        for i, speed_cat in enumerate(speed_categories):
            # このカテゴリーのデータを抽出
            cat_data = direction_speed_counts[direction_speed_counts['speed_category'] == speed_cat]
            
            if not cat_data.empty:
                fig.add_trace(go.Barpolar(
                    r=cat_data['count'],
                    theta=cat_data['direction_bin'],
                    name=speed_cat,
                    marker_color=colors[i]
                ))
        
        # レイアウト設定
        fig.update_layout(
            height=300,
            polar=dict(
                radialaxis=dict(showticklabels=False, ticks=''),
                angularaxis=dict(
                    tickmode='array',
                    tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                    ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                    direction='clockwise'
                )
            ),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=0, xanchor="center", x=0.5),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    def _render_insights(self, wind_data):
        """
        風向風速データからのインサイトを描画
        
        Parameters
        ----------
        wind_data : pandas.DataFrame
            風向風速データを含むDataFrame
        """
        # シフトとトレンドの検出
        wind_shifts = self._detect_wind_shifts(wind_data)
        
        with st.expander("風向風速の分析インサイト", expanded=False):
            # シフト情報を表示
            if wind_shifts:
                st.write("**検出された主要な風向シフト:**")
                for shift in wind_shifts[:3]:  # 最大3つまで表示
                    st.write(f"- {shift['time'].strftime('%H:%M:%S')}: {shift['description']}")
            
            # トレンド情報
            st.write("**風向風速トレンド:**")
            
            # 風速トレンド
            if wind_data['wind_speed'].iloc[-1] > wind_data['wind_speed'].iloc[0]:
                speed_trend = "増加傾向"
            elif wind_data['wind_speed'].iloc[-1] < wind_data['wind_speed'].iloc[0]:
                speed_trend = "減少傾向"
            else:
                speed_trend = "安定"
            
            # 風向の安定性
            direction_std = np.std(wind_data['wind_direction'])
            if direction_std < 10:
                direction_stability = "非常に安定"
            elif direction_std < 20:
                direction_stability = "安定"
            elif direction_std < 40:
                direction_stability = "やや変動あり"
            else:
                direction_stability = "不安定"
            
            st.write(f"- 風速: {speed_trend} (平均変動: ±{wind_data['wind_speed'].std():.1f} kt)")
            st.write(f"- 風向: {direction_stability} (標準偏差: {direction_std:.1f}°)")
    
    def _calculate_circular_mean(self, directions):
        """
        円環データ（風向）の平均を計算
        
        Parameters
        ----------
        directions : array-like
            風向のデータ (0-360度)
            
        Returns
        -------
        float
            平均風向 (0-360度)
        """
        # 角度をラジアンに変換
        rad = np.deg2rad(directions)
        
        # 平均の計算（複素数を使用）
        sin_mean = np.mean(np.sin(rad))
        cos_mean = np.mean(np.cos(rad))
        
        # ラジアンから度に戻す
        circular_mean = np.rad2deg(np.arctan2(sin_mean, cos_mean))
        
        # 角度を0-360の範囲に調整
        if circular_mean < 0:
            circular_mean += 360
            
        return circular_mean
    
    def _calculate_direction_range(self, directions):
        """
        風向の変動範囲を計算
        
        Parameters
        ----------
        directions : array-like
            風向のデータ (0-360度)
            
        Returns
        -------
        tuple
            (最小風向, 最大風向)
        """
        # 単純な最小値と最大値では、北（0度と360度）をまたぐ場合に問題がある
        # より洗練された方法は円環統計を使用するが、簡易版として次のように実装
        
        # 四分位範囲を使用して範囲を計算
        q1 = np.percentile(directions, 25)
        q3 = np.percentile(directions, 75)
        
        return (q1, q3)
    
    def _detect_wind_shifts(self, wind_data):
        """
        風向シフトを検出
        
        Parameters
        ----------
        wind_data : pandas.DataFrame
            風向風速データを含むDataFrame
            
        Returns
        -------
        list
            検出された風向シフトのリスト
        """
        shifts = []
        window_size = 5  # 移動平均のウィンドウサイズ
        
        if len(wind_data) <= window_size:
            return shifts
        
        # 移動平均を計算して風向の急激な変化を検出
        wind_data['direction_ma'] = wind_data['wind_direction'].rolling(window=window_size).mean()
        
        # NaNを含まない部分だけを処理
        clean_data = wind_data.dropna()
        
        # 隣接する移動平均の差
        clean_data['direction_diff'] = clean_data['direction_ma'].diff()
        
        # 北をまたぐケース（例：355度から5度への変化）を処理
        # 通常、差は-350度になるが、実際は+10度の変化
        clean_data.loc[clean_data['direction_diff'] < -180, 'direction_diff'] += 360
        clean_data.loc[clean_data['direction_diff'] > 180, 'direction_diff'] -= 360
        
        # シフトの閾値
        threshold = 10.0  # 10度以上の変化をシフトとみなす
        
        # シフトを検出
        shift_times = clean_data[abs(clean_data['direction_diff']) > threshold].index
        
        for i, time_idx in enumerate(shift_times):
            if i > 0 and (time_idx - shift_times[i-1]).total_seconds() < 300:  # 5分以内のシフトはスキップ
                continue
                
            direction_diff = clean_data.loc[time_idx, 'direction_diff']
            shift_type = "右" if direction_diff > 0 else "左"
            
            shifts.append({
                'time': wind_data['timestamp'].loc[time_idx],
                'magnitude': abs(direction_diff),
                'type': shift_type,
                'description': f"{shift_type}に{abs(direction_diff):.1f}°シフト"
            })
        
        return shifts
