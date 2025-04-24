# -*- coding: utf-8 -*-
"""
ui.integrated.components.dashboard.widgets.performance_widget

パフォーマンス指標データのサマリーを表示するダッシュボードウィジェット
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

class PerformanceWidget:
    """パフォーマンス指標サマリーウィジェット"""
    
    def __init__(self):
        """初期化"""
        self.title = "パフォーマンス指標"
    
    def render(self, speed_data):
        """
        パフォーマンス指標サマリーウィジェットの描画
        
        Parameters
        ----------
        speed_data : pandas.DataFrame
            速度データを含むDataFrame
            timestamp, boat_speed, vmg, heel_angle カラムが必要
        """
        # カードのスタイル設定
        with st.container():
            st.write(f"### {self.title}")
            
            # 基本統計量
            boat_speed_mean = speed_data['boat_speed'].mean()
            vmg_mean = speed_data['vmg'].mean()
            heel_angle_mean = speed_data['heel_angle'].mean()
            
            # レイアウト: 基本情報を上部に表示
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("平均速度", f"{boat_speed_mean:.1f} kt")
            
            with col2:
                st.metric("平均VMG", f"{vmg_mean:.1f} kt")
            
            with col3:
                st.metric("平均ヒール角", f"{heel_angle_mean:.1f}°")
            
            # 時系列グラフ
            self._render_time_series(speed_data)
            
            # 散布図
            self._render_scatter(speed_data)
    
    def _render_time_series(self, speed_data):
        """
        速度関連指標の時系列グラフを描画
        
        Parameters
        ----------
        speed_data : pandas.DataFrame
            速度データを含むDataFrame
        """
        # 時系列グラフ（複数指標を並べて表示）
        fig = go.Figure()
        
        # ボート速度のグラフ
        fig.add_trace(
            go.Scatter(
                x=speed_data['timestamp'],
                y=speed_data['boat_speed'],
                name="速度 (kt)",
                line=dict(color='blue', width=2),
                mode='lines'
            )
        )
        
        # VMGのグラフ
        fig.add_trace(
            go.Scatter(
                x=speed_data['timestamp'],
                y=speed_data['vmg'],
                name="VMG (kt)",
                line=dict(color='green', width=2),
                mode='lines'
            )
        )
        
        # レイアウト設定
        fig.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1, xanchor="right", x=1),
            yaxis=dict(title="速度 (kt)"),
            xaxis=dict(title="時間")
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    def _render_scatter(self, speed_data):
        """
        ヒール角と速度の関係を散布図で表示
        
        Parameters
        ----------
        speed_data : pandas.DataFrame
            速度データを含むDataFrame
        """
        # ヒール角と速度の関係を示す散布図
        fig = px.scatter(
            speed_data, 
            x='heel_angle', 
            y='boat_speed',
            color='vmg',
            color_continuous_scale='Viridis',
            title="ヒール角と速度の関係",
            labels={
                'heel_angle': 'ヒール角 (°)',
                'boat_speed': '速度 (kt)',
                'vmg': 'VMG (kt)'
            }
        )
        
        # トレンドラインの追加
        fig.add_trace(
            go.Scatter(
                x=speed_data['heel_angle'],
                y=np.poly1d(np.polyfit(speed_data['heel_angle'], speed_data['boat_speed'], 1))(speed_data['heel_angle']),
                mode='lines',
                name='トレンドライン',
                line=dict(color='red', dash='dash')
            )
        )
        
        # レイアウト設定
        fig.update_layout(
            height=240,
            margin=dict(l=0, r=0, t=40, b=0),
            coloraxis_colorbar=dict(title="VMG (kt)")
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # 分析インサイト
        with st.expander("パフォーマンス分析", expanded=False):
            # 最適ヒール角の計算（単純化のため、速度が最大となるヒール角を使用）
            optimal_heel = speed_data.loc[speed_data['boat_speed'].idxmax(), 'heel_angle']
            
            # VMGが最大となるヒール角と速度
            max_vmg_idx = speed_data['vmg'].idxmax()
            max_vmg_heel = speed_data.loc[max_vmg_idx, 'heel_angle']
            max_vmg_speed = speed_data.loc[max_vmg_idx, 'boat_speed']
            
            # 相関係数
            corr_heel_speed = speed_data['heel_angle'].corr(speed_data['boat_speed'])
            corr_heel_vmg = speed_data['heel_angle'].corr(speed_data['vmg'])
            
            st.markdown("**パフォーマンスインサイト:**")
            st.markdown(f"- 最適ヒール角（最高速度）: **{optimal_heel:.1f}°**")
            st.markdown(f"- 最適ヒール角（最高VMG）: **{max_vmg_heel:.1f}°**")
            st.markdown(f"- ヒール角と速度の相関: **{corr_heel_speed:.2f}**")
            st.markdown(f"- ヒール角とVMGの相関: **{corr_heel_vmg:.2f}**")
            
            # パフォーマンス向上のためのアドバイス
            if abs(corr_heel_speed) > 0.5:
                if corr_heel_speed > 0:
                    st.markdown("- ヒール角を大きくすることで速度が向上する可能性があります")
                else:
                    st.markdown("- ヒール角を小さくすることで速度が向上する可能性があります")
