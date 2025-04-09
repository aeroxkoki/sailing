"""
ui.integrated.pages.statistical_view

セーリング戦略分析システムの統計チャートページ
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# 比較分析ツールのインポート
from ui.integrated.components.visualization.comparison_tool import ComparisonTool

def render_page():
    """統計チャートページをレンダリングする関数"""
    
    st.title('統計チャート分析')
    
    # セッション状態の初期化
    if 'stats_initialized' not in st.session_state:
        st.session_state.stats_initialized = True
        st.session_state.selected_stats_session = None
        st.session_state.chart_type = "velocity"
        st.session_state.comparison_mode = False
        st.session_state.comparison_sessions = []
        st.session_state.chart_settings = {}
    
    # サイドバーのセッション選択
    with st.sidebar:
        st.subheader("セッション選択")
        # 実際にはプロジェクト管理システムからセッションを取得する
        # サンプルとしてダミーデータを使用
        sessions = ["2025/03/27 レース練習", "2025/03/25 風向変化トレーニング", "2025/03/20 スピードテスト"]
        selected_session = st.selectbox("分析するセッションを選択", sessions)
        
        if selected_session != st.session_state.selected_stats_session:
            st.session_state.selected_stats_session = selected_session
            # セッションが変更されたら関連データを読み込む処理をここに追加
            st.experimental_rerun()
    
    # 選択されたセッションの表示
    if st.session_state.selected_stats_session:
        st.markdown(f"## セッション: {st.session_state.selected_stats_session}")
        
        # 比較モードの選択
        with st.sidebar:
            st.markdown("---")
            st.subheader("比較分析")
            
            comparison_mode = st.checkbox("比較モードを有効にする", value=st.session_state.comparison_mode)
            
            if comparison_mode != st.session_state.comparison_mode:
                st.session_state.comparison_mode = comparison_mode
                st.experimental_rerun()
            
            if st.session_state.comparison_mode:
                # 比較するセッションの選択
                comparison_sessions = st.multiselect(
                    "比較するセッションを選択",
                    [s for s in sessions if s != st.session_state.selected_stats_session],
                    default=st.session_state.comparison_sessions
                )
                
                if comparison_sessions != st.session_state.comparison_sessions:
                    st.session_state.comparison_sessions = comparison_sessions
                    st.experimental_rerun()
        
        # タブを使用して異なるチャートビューを提供
        tab1, tab2, tab3, tab4 = st.tabs(["速度分析", "風向分析", "VMG分析", "戦略分析"])
        
        with tab1:
            render_velocity_tab()
        
        with tab2:
            render_wind_tab()
        
        with tab3:
            render_vmg_tab()
        
        with tab4:
            render_strategy_tab()
        
        # チャート設定
        with st.sidebar:
            st.markdown("---")
            st.subheader("チャート設定")
            
            # 現在のタブに応じた設定を表示
            if st.session_state.chart_type == "velocity":
                render_velocity_settings()
            elif st.session_state.chart_type == "wind":
                render_wind_settings()
            elif st.session_state.chart_type == "vmg":
                render_vmg_settings()
            elif st.session_state.chart_type == "strategy":
                render_strategy_settings()
        
        # エクスポートオプション
        with st.sidebar:
            st.markdown("---")
            st.subheader("エクスポート")
            
            export_format = st.selectbox(
                "フォーマット",
                ["PNG", "SVG", "HTML", "CSV", "Excel"]
            )
            
            if st.button("現在のチャートをエクスポート"):
                # 実際の実装では、エクスポート機能を呼び出す
                st.success(f"チャートを {export_format} 形式でエクスポートしました。")
            
            if st.button("すべてのチャートをエクスポート"):
                # 実際の実装では、すべてのチャートをエクスポートする
                st.success(f"すべてのチャートを {export_format} 形式でエクスポートしました。")
            
            if st.button("レポートに追加"):
                # 実際の実装では、レポート生成機能と連携
                st.success("選択されたチャートをレポートに追加しました。")
    else:
        st.info("分析するセッションを選択してください。")

def render_velocity_tab():
    """速度分析タブの表示"""
    st.session_state.chart_type = "velocity"
    
    st.subheader("速度分析")
    
    # 速度分布ヒストグラム
    st.markdown("### 速度分布")
    
    # サンプルデータの生成
    np.random.seed(42)  # 再現性のために乱数シードを設定
    speed_data = np.random.normal(6.2, 1.2, 500)  # 平均6.2ノット、標準偏差1.2のデータ
    speed_df = pd.DataFrame({'速度 (kt)': speed_data})
    
    if st.session_state.comparison_mode and st.session_state.comparison_sessions:
        # 比較データの生成（実際の実装では、セッションからデータを取得）
        compare_data = []
        
        for session in st.session_state.comparison_sessions:
            # セッションごとに少し異なる分布のデータを生成
            session_seed = hash(session) % 1000  # セッション名からシード値を生成
            np.random.seed(session_seed)
            
            # 少しずつ異なる平均と標準偏差を持つデータ
            session_data = np.random.normal(5.8 + session_seed * 0.01, 1.0 + session_seed * 0.01, 500)
            
            temp_df = pd.DataFrame({
                '速度 (kt)': session_data,
                'セッション': session
            })
            compare_data.append(temp_df)
        
        # 現在のセッションデータに名前を付ける
        speed_df['セッション'] = st.session_state.selected_stats_session
        
        # すべてのデータを結合
        all_data = pd.concat([speed_df] + compare_data, ignore_index=True)
        
        # Plotlyでヒストグラムを作成（複数セッションの比較）
        fig = px.histogram(
            all_data, 
            x='速度 (kt)', 
            color='セッション',
            barmode='overlay',
            opacity=0.7,
            nbins=20,
            histnorm='percent',
            marginal='box',
            title='セッション間の速度分布比較'
        )
        
        # レイアウトの調整
        fig.update_layout(
            xaxis_title='速度 (kt)',
            yaxis_title='割合 (%)',
            legend_title='セッション',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 統計情報の表示
        st.markdown("### 速度統計比較")
        
        stats_data = []
        for session_name in [st.session_state.selected_stats_session] + st.session_state.comparison_sessions:
            session_data = all_data[all_data['セッション'] == session_name]['速度 (kt)']
            stats_data.append({
                'セッション': session_name,
                '平均速度 (kt)': session_data.mean().round(2),
                '最高速度 (kt)': session_data.max().round(2),
                '最低速度 (kt)': session_data.min().round(2),
                '標準偏差': session_data.std().round(2),
                '中央値 (kt)': session_data.median().round(2)
            })
        
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True)
        
    else:
        # 単一セッションの速度分布ヒストグラム
        fig = px.histogram(
            speed_df, 
            x='速度 (kt)', 
            nbins=20, 
            marginal='box',
            histnorm='percent',
            title='速度分布'
        )
        
        # レイアウトの調整
        fig.update_layout(
            xaxis_title='速度 (kt)',
            yaxis_title='割合 (%)',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 統計情報の表示
        st.markdown("### 速度統計")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("平均速度", f"{speed_df['速度 (kt)'].mean():.2f} kt")
        
        with col2:
            st.metric("最高速度", f"{speed_df['速度 (kt)'].max():.2f} kt")
        
        with col3:
            st.metric("標準偏差", f"{speed_df['速度 (kt)'].std():.2f}")
        
        with col4:
            st.metric("中央値", f"{speed_df['速度 (kt)'].median():.2f} kt")
    
    # 速度の時系列分析
    st.markdown("### 速度の時間変化")
    
    # 時系列データの生成
    time_range = pd.date_range(start="2025-03-27 13:00:00", periods=100, freq="1min")
    
    # トレンド成分（徐々に上昇して後半で下降）
    trend = np.concatenate([
        np.linspace(5.5, 7.0, 60),  # 上昇トレンド
        np.linspace(7.0, 6.0, 40)   # 下降トレンド
    ])
    
    # サイクル成分（風上/風下の繰り返し）
    cycles = np.sin(np.linspace(0, 4*np.pi, 100)) * 1.2
    
    # ノイズ成分
    np.random.seed(42)
    noise = np.random.normal(0, 0.3, 100)
    
    # 速度データの生成
    speed_time_data = trend + cycles + noise
    
    # データフレーム作成
    time_df = pd.DataFrame({
        '時間': time_range,
        '速度 (kt)': speed_time_data
    })
    
    if st.session_state.comparison_mode and st.session_state.comparison_sessions:
        # 比較用の時系列データ生成
        compare_time_data = []
        
        for session in st.session_state.comparison_sessions:
            # セッションごとに少し異なる時系列データを生成
            session_seed = hash(session) % 1000
            np.random.seed(session_seed)
            
            # トレンド、サイクル、ノイズを少し変えたデータ
            session_trend = trend * (0.9 + session_seed * 0.0002)
            session_cycles = cycles * (0.95 + session_seed * 0.0001)
            session_noise = np.random.normal(0, 0.3, 100)
            
            session_speed = session_trend + session_cycles + session_noise
            
            temp_df = pd.DataFrame({
                '時間': time_range,
                '速度 (kt)': session_speed,
                'セッション': session
            })
            
            compare_time_data.append(temp_df)
        
        # 現在のセッションデータに名前を付ける
        time_df['セッション'] = st.session_state.selected_stats_session
        
        # すべてのデータを結合
        all_time_data = pd.concat([time_df] + compare_time_data, ignore_index=True)
        
        # 比較時系列グラフの作成
        fig = px.line(
            all_time_data,
            x='時間',
            y='速度 (kt)',
            color='セッション',
            title='セッション間の速度時系列比較'
        )
        
        # レイアウトの調整
        fig.update_layout(
            xaxis_title='時間',
            yaxis_title='速度 (kt)',
            legend_title='セッション',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # 単一セッションの時系列グラフ
        fig = px.line(
            time_df,
            x='時間',
            y='速度 (kt)',
            title='速度の時間変化'
        )
        
        # レイアウトの調整
        fig.update_layout(
            xaxis_title='時間',
            yaxis_title='速度 (kt)',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 風向別速度分布（ポーラープロット）
    st.markdown("### 風向別速度分布")
    
    # 風向と速度のサンプルデータ生成
    n_points = 200
    np.random.seed(42)
    
    # 風向データ（0-360度）
    wind_angles = np.random.uniform(0, 360, n_points)
    
    # 風向に応じた速度モデリング
    # 風上（0度付近）と風下（180度付近）で遅く、横風（90度、270度付近）で速い
    base_speed = 5.0
    angle_factor = 2.5 * np.sin(np.deg2rad(wind_angles) * 2) + 0.5
    
    # バイアスとノイズを追加
    speed_variations = base_speed + angle_factor + np.random.normal(0, 0.8, n_points)
    
    # 極座標プロット用のデータ準備
    polar_df = pd.DataFrame({
        '風向 (度)': wind_angles,
        '速度 (kt)': speed_variations
    })
    
    if st.session_state.comparison_mode and st.session_state.comparison_sessions:
        # 比較モードでは複数セッションのプロットを表示
        fig = go.Figure()
        
        # 現在のセッションデータを追加
        fig.add_trace(go.Scatterpolar(
            r=polar_df['速度 (kt)'],
            theta=polar_df['風向 (度)'],
            mode='markers',
            name=st.session_state.selected_stats_session,
            marker=dict(size=7, opacity=0.7)
        ))
        
        # 比較セッションのデータを追加
        for i, session in enumerate(st.session_state.comparison_sessions):
            # セッションごとに少し異なる極座標データを生成
            session_seed = hash(session) % 1000
            np.random.seed(session_seed)
            
            # 風向データ
            session_angles = np.random.uniform(0, 360, n_points)
            
            # 風向に応じた速度
            session_base = base_speed * (0.9 + session_seed * 0.0003)
            session_factor = angle_factor * (0.95 + session_seed * 0.0002)
            session_speed = session_base + session_factor + np.random.normal(0, 0.8, n_points)
            
            # プロットに追加
            fig.add_trace(go.Scatterpolar(
                r=session_speed,
                theta=session_angles,
                mode='markers',
                name=session,
                marker=dict(size=7, opacity=0.7)
            ))
        
        # レイアウトの設定
        fig.update_layout(
            title='セッション間の風向別速度比較',
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            showlegend=True,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # 単一セッションの極座標プロット
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=polar_df['速度 (kt)'],
            theta=polar_df['風向 (度)'],
            mode='markers',
            marker=dict(size=8, color=polar_df['速度 (kt)'], colorscale='Viridis', 
                        showscale=True, colorbar=dict(title='速度 (kt)'))
        ))
        
        # レイアウトの設定
        fig.update_layout(
            title='風向別の速度分布',
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )
            ),
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # マニューバー（タック/ジャイブ）効率分析
    st.markdown("### マニューバー効率分析")
    
    # マニューバーデータの生成
    maneuver_data = {
        'マニューバー': ['タック1', 'タック2', 'タック3', 'タック4', 'タック5', 'ジャイブ1', 'ジャイブ2', 'ジャイブ3'],
        '所要時間(秒)': [8, 6, 9, 7, 8, 10, 9, 11],
        '速度損失(kt)': [0.8, 0.5, 1.2, 0.7, 0.6, 1.3, 1.0, 1.5],
        '効率(%)': [92, 95, 85, 93, 94, 86, 90, 82],
        'タイプ': ['タック', 'タック', 'タック', 'タック', 'タック', 'ジャイブ', 'ジャイブ', 'ジャイブ']
    }
    
    maneuver_df = pd.DataFrame(maneuver_data)
    
    if st.session_state.comparison_mode and st.session_state.comparison_sessions:
        # 比較モードでは複数セッションのマニューバーデータを集計表示
        
        # 比較用のデータ生成
        compare_maneuver_data = []
        
        for session in st.session_state.comparison_sessions:
            # セッションごとの集計データを作成
            session_data = {
                'セッション': session,
                'タック平均所要時間': np.random.uniform(6.5, 9.0),
                'タック平均速度損失': np.random.uniform(0.6, 1.1),
                'タック平均効率': np.random.uniform(85, 95),
                'ジャイブ平均所要時間': np.random.uniform(8.5, 11.5),
                'ジャイブ平均速度損失': np.random.uniform(0.9, 1.4),
                'ジャイブ平均効率': np.random.uniform(80, 90)
            }
            compare_maneuver_data.append(session_data)
        
        # 現在のセッションの集計データ
        current_session_data = {
            'セッション': st.session_state.selected_stats_session,
            'タック平均所要時間': maneuver_df[maneuver_df['タイプ'] == 'タック']['所要時間(秒)'].mean(),
            'タック平均速度損失': maneuver_df[maneuver_df['タイプ'] == 'タック']['速度損失(kt)'].mean(),
            'タック平均効率': maneuver_df[maneuver_df['タイプ'] == 'タック']['効率(%)'].mean(),
            'ジャイブ平均所要時間': maneuver_df[maneuver_df['タイプ'] == 'ジャイブ']['所要時間(秒)'].mean(),
            'ジャイブ平均速度損失': maneuver_df[maneuver_df['タイプ'] == 'ジャイブ']['速度損失(kt)'].mean(),
            'ジャイブ平均効率': maneuver_df[maneuver_df['タイプ'] == 'ジャイブ']['効率(%)'].mean()
        }
        
        # すべてのデータを結合
        all_maneuver_data = pd.DataFrame([current_session_data] + compare_maneuver_data)
        
        # 集計データの表示
        st.dataframe(all_maneuver_data.round(2), use_container_width=True)
        
        # 比較グラフの作成（例：効率の比較）
        fig = px.bar(
            all_maneuver_data,
            x='セッション',
            y=['タック平均効率', 'ジャイブ平均効率'],
            barmode='group',
            title='セッション間のマニューバー効率比較',
            labels={'value': '効率 (%)', 'variable': 'マニューバータイプ'}
        )
        
        # レイアウトの調整
        fig.update_layout(
            xaxis_title='セッション',
            yaxis_title='効率 (%)',
            legend_title='マニューバータイプ',
            template='plotly_white',
            yaxis=dict(range=[75, 100])  # Y軸の範囲を調整
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # 単一セッションのマニューバー効率分析
        
        # タック/ジャイブ別の所要時間と速度損失プロット
        fig = px.scatter(
            maneuver_df,
            x='所要時間(秒)',
            y='速度損失(kt)',
            color='タイプ',
            size='効率(%)',
            hover_name='マニューバー',
            title='マニューバー効率分析'
        )
        
        # レイアウトの調整
        fig.update_layout(
            xaxis_title='所要時間 (秒)',
            yaxis_title='速度損失 (kt)',
            legend_title='マニューバータイプ',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # マニューバーデータの表示
        st.dataframe(maneuver_df, use_container_width=True)

def render_wind_tab():
    """風向分析タブの表示"""
    st.session_state.chart_type = "wind"
    
    st.subheader("風向風速分析")
    
    # 風向の時系列分析
    st.markdown("### 風向の時間変化")
    
    # 時系列データの生成
    time_range = pd.date_range(start="2025-03-27 13:00:00", periods=100, freq="1min")
    
    # 風向データを生成（徐々に変化する傾向と短期的な変動を含む）
    # 基本的な傾向 - 時間とともに右に振れる
    trend = np.linspace(180, 220, 100)
    
    # 短期的な変動
    np.random.seed(42)
    oscillations = np.cumsum(np.random.normal(0, 1, 100))  # ランダムウォークで変動を模倣
    oscillations = oscillations * 3 / np.max(np.abs(oscillations))  # 変動幅を調整
    
    # 風向データ
    wind_dir_data = (trend + oscillations) % 360
    
    # データフレーム作成
    wind_dir_df = pd.DataFrame({
        '時間': time_range,
        '風向 (度)': wind_dir_data
    })
    
    # 風速データを生成
    base_wind_speed = 12.0
    wind_speed_trend = np.concatenate([
        np.linspace(base_wind_speed, base_wind_speed + 3, 40),  # 徐々に強くなる
        np.linspace(base_wind_speed + 3, base_wind_speed - 1, 60)  # 徐々に弱くなる
    ])
    
    wind_speed_oscillations = np.sin(np.linspace(0, 5*np.pi, 100)) * 1.2  # 周期的な変動
    wind_speed_noise = np.random.normal(0, 0.5, 100)  # ランダムな変動
    
    wind_speed_data = wind_speed_trend + wind_speed_oscillations + wind_speed_noise
    wind_speed_data = np.maximum(wind_speed_data, 0)  # 負の風速を除外
    
    # 風速データをデータフレームに追加
    wind_dir_df['風速 (kt)'] = wind_speed_data
    
    if st.session_state.comparison_mode and st.session_state.comparison_sessions:
        # 比較用の風向データ生成
        compare_wind_data = []
        
        for session in st.session_state.comparison_sessions:
            # セッションごとに少し異なる風向データを生成
            session_seed = hash(session) % 1000
            np.random.seed(session_seed)
            
            # 基本トレンドは共通だが、変動パターンを変える
            session_oscillations = np.cumsum(np.random.normal(0, 1, 100))
            session_oscillations = session_oscillations * 3 / np.max(np.abs(session_oscillations))
            
            session_wind_dir = (trend + session_oscillations) % 360
            
            # 風速も少し変える
            session_wind_speed_oscillations = np.sin(np.linspace(0, 5*np.pi, 100) + session_seed * 0.01) * 1.2
            session_wind_speed_noise = np.random.normal(0, 0.5, 100)
            session_wind_speed = wind_speed_trend + session_wind_speed_oscillations + session_wind_speed_noise
            session_wind_speed = np.maximum(session_wind_speed, 0)
            
            temp_df = pd.DataFrame({
                '時間': time_range,
                '風向 (度)': session_wind_dir,
                '風速 (kt)': session_wind_speed,
                'セッション': session
            })
            
            compare_wind_data.append(temp_df)
        
        # 現在のセッションデータに名前を付ける
        wind_dir_df['セッション'] = st.session_state.selected_stats_session
        
        # すべてのデータを結合
        all_wind_data = pd.concat([wind_dir_df] + compare_wind_data, ignore_index=True)
        
        # 風向の比較グラフ
        fig_dir = px.line(
            all_wind_data,
            x='時間',
            y='風向 (度)',
            color='セッション',
            title='セッション間の風向変化比較'
        )
        
        # レイアウトの調整
        fig_dir.update_layout(
            xaxis_title='時間',
            yaxis_title='風向 (度)',
            legend_title='セッション',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_dir, use_container_width=True)
        
        # 風速の比較グラフ
        fig_speed = px.line(
            all_wind_data,
            x='時間',
            y='風速 (kt)',
            color='セッション',
            title='セッション間の風速変化比較'
        )
        
        # レイアウトの調整
        fig_speed.update_layout(
            xaxis_title='時間',
            yaxis_title='風速 (kt)',
            legend_title='セッション',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_speed, use_container_width=True)
        
    else:
        # 風向の時系列グラフ
        fig_dir = px.line(
            wind_dir_df,
            x='時間',
            y='風向 (度)',
            title='風向の時間変化'
        )
        
        # レイアウトの調整
        fig_dir.update_layout(
            xaxis_title='時間',
            yaxis_title='風向 (度)',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_dir, use_container_width=True)
        
        # 風速の時系列グラフ
        fig_speed = px.line(
            wind_dir_df,
            x='時間',
            y='風速 (kt)',
            title='風速の時間変化'
        )
        
        # レイアウトの調整
        fig_speed.update_layout(
            xaxis_title='時間',
            yaxis_title='風速 (kt)',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_speed, use_container_width=True)
    
    # 風向シフト分析
    st.markdown("### 風向シフト分析")
    
    # 風向シフトデータの生成
    shift_data = {
        '時刻': ['13:15', '13:42', '14:10', '14:35', '15:05'],
        'シフト量': [15, -12, 8, 20, -10],  # 正は右シフト、負は左シフト
        'シフト速度 (度/分)': [1.2, 2.4, 0.8, 1.5, 2.0],
        '検出遅延 (秒)': [8, 4, 12, 20, 5],
        '対応品質': ['良好', '優良', '遅延', '見逃し', '良好']
    }
    
    shift_df = pd.DataFrame(shift_data)
    
    # 対応品質を数値化（可視化用）
    quality_map = {'優良': 4, '良好': 3, '遅延': 2, '見逃し': 1}
    shift_df['品質スコア'] = shift_df['対応品質'].map(quality_map)
    
    # シフト量と品質の散布図
    fig_shift = px.scatter(
        shift_df,
        x='シフト量',
        y='シフト速度 (度/分)',
        size='検出遅延 (秒)',
        color='対応品質',
        hover_name='時刻',
        size_max=15,
        title='風向シフトの特性と対応品質'
    )
    
    # レイアウトの調整
    fig_shift.update_layout(
        xaxis_title='シフト量 (度、正=右シフト、負=左シフト)',
        yaxis_title='シフト速度 (度/分)',
        legend_title='対応品質',
        template='plotly_white'
    )
    
    st.plotly_chart(fig_shift, use_container_width=True)
    
    # シフトデータの詳細表示
    st.dataframe(shift_df.drop(columns=['品質スコア']), use_container_width=True)
    
    # 風配図（風向風速の極座標表示）
    st.markdown("### 風配図（風向風速分布）")
    
    # 風向風速データの生成
    n_points = 300
    np.random.seed(42)
    
    # 主風向周辺に集中する風向データ
    main_direction = 200  # 主風向（度）
    wind_dir_points = main_direction + np.random.normal(0, 25, n_points)
    wind_dir_points = wind_dir_points % 360
    
    # 風速データ（平均12ノット周辺）
    wind_speed_points = np.random.gamma(shape=4, scale=3, size=n_points)
    
    # データフレーム作成
    wind_dist_df = pd.DataFrame({
        '風向 (度)': wind_dir_points,
        '風速 (kt)': wind_speed_points
    })
    
    if st.session_state.comparison_mode and st.session_state.comparison_sessions:
        # 比較モードでは複数セッションのデータを表示
        fig = go.Figure()
        
        # 現在のセッションデータを追加
        fig.add_trace(go.Scatterpolar(
            r=wind_dist_df['風速 (kt)'],
            theta=wind_dist_df['風向 (度)'],
            mode='markers',
            name=st.session_state.selected_stats_session,
            marker=dict(size=7, opacity=0.7)
        ))
        
        # 比較セッションのデータを追加
        for i, session in enumerate(st.session_state.comparison_sessions):
            # セッションごとに少し異なる風向風速データを生成
            session_seed = hash(session) % 1000
            np.random.seed(session_seed)
            
            # 異なる主風向で生成
            session_main_dir = (main_direction + session_seed % 30 - 15) % 360
            session_dir = session_main_dir + np.random.normal(0, 25, n_points)
            session_dir = session_dir % 360
            
            # 風速も少し変える
            session_speed = np.random.gamma(shape=4, scale=3 * (0.9 + session_seed * 0.0002), size=n_points)
            
            # プロットに追加
            fig.add_trace(go.Scatterpolar(
                r=session_speed,
                theta=session_dir,
                mode='markers',
                name=session,
                marker=dict(size=7, opacity=0.7)
            ))
        
        # レイアウトの設定
        fig.update_layout(
            title='セッション間の風向風速分布比較',
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 25]
                )
            ),
            showlegend=True,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        # 単一セッションの風配図
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=wind_dist_df['風速 (kt)'],
            theta=wind_dist_df['風向 (度)'],
            mode='markers',
            marker=dict(
                size=8,
                color=wind_dist_df['風速 (kt)'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='風速 (kt)')
            )
        ))
        
        # レイアウトの設定
        fig.update_layout(
            title='風配図（風向風速分布）',
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 25]
                )
            ),
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 風向と風速の分布ヒストグラム
        fig_hist = make_subplots(rows=1, cols=2, subplot_titles=('風向分布', '風速分布'))
        
        fig_hist.add_trace(
            go.Histogram(x=wind_dist_df['風向 (度)'], nbinsx=36, name='風向'),
            row=1, col=1
        )
        
        fig_hist.add_trace(
            go.Histogram(x=wind_dist_df['風速 (kt)'], nbinsx=20, name='風速'),
            row=1, col=2
        )
        
        # レイアウトの調整
        fig_hist.update_layout(
            title='風向風速の分布',
            showlegend=False,
            template='plotly_white'
        )
        
        fig_hist.update_xaxes(title_text='風向 (度)', row=1, col=1)
        fig_hist.update_xaxes(title_text='風速 (kt)', row=1, col=2)
        fig_hist.update_yaxes(title_text='頻度', row=1, col=1)
        fig_hist.update_yaxes(title_text='頻度', row=1, col=2)
        
        st.plotly_chart(fig_hist, use_container_width=True)

def render_vmg_tab():
    """VMG分析タブの表示"""
    st.session_state.chart_type = "vmg"
    
    st.subheader("VMG (Velocity Made Good) 分析")
    
    # VMGの時系列分析
    st.markdown("### VMGの時間変化")
    
    # 時系列データの生成
    time_range = pd.date_range(start="2025-03-27 13:00:00", periods=100, freq="1min")
    
    # 風上と風下を交互に走るようなパターンを模倣
    stages = [
        {'start': 0, 'end': 20, 'type': '風上', 'base_vmg': 3.2},
        {'start': 20, 'end': 40, 'type': '風下', 'base_vmg': 4.5},
        {'start': 40, 'end': 60, 'type': '風上', 'base_vmg': 3.4},
        {'start': 60, 'end': 80, 'type': '風下', 'base_vmg': 4.7},
        {'start': 80, 'end': 100, 'type': '風上', 'base_vmg': 3.3}
    ]
    
    # VMGデータの生成
    vmg_values = []
    leg_types = []
    
    for stage in stages:
        length = stage['end'] - stage['start']
        # 各レグ内でパフォーマンスが向上するトレンド
        trend = np.linspace(stage['base_vmg']-0.2, stage['base_vmg']+0.3, length)
        
        # ノイズを追加
        np.random.seed(42 + stage['start'])
        noise = np.random.normal(0, 0.2, length)
        
        # タックやジャイブでの一時的な落ち込み
        if length > 10:
            indices = np.random.choice(range(3, length-3), 2, replace=False)
            for idx in indices:
                noise[idx-2:idx+3] -= np.array([0.4, 0.8, 1.2, 0.8, 0.4])
        
        stage_vmg = trend + noise
        vmg_values.extend(stage_vmg)
        leg_types.extend([stage['type']] * length)
    
    # データフレーム作成
    vmg_df = pd.DataFrame({
        '時間': time_range,
        'VMG (kt)': vmg_values,
        'レグタイプ': leg_types
    })
    
    if st.session_state.comparison_mode and st.session_state.comparison_sessions:
        # 比較用のVMGデータ生成
        compare_vmg_data = []
        
        for session in st.session_state.comparison_sessions:
            # セッションごとに少し異なるVMGデータを生成
            session_seed = hash(session) % 1000
            np.random.seed(session_seed)
            
            session_vmg = []
            session_leg_types = []
            
            for stage in stages:
                length = stage['end'] - stage['start']
                # 各セッションで基準VMGを少し変える
                base_vmg_factor = 0.95 + (session_seed % 100) * 0.001
                session_base_vmg = stage['base_vmg'] * base_vmg_factor
                
                # 同様のトレンドとノイズパターンで生成
                trend = np.linspace(session_base_vmg-0.2, session_base_vmg+0.3, length)
                noise = np.random.normal(0, 0.2, length)
                
                if length > 10:
                    indices = np.random.choice(range(3, length-3), 2, replace=False)
                    for idx in indices:
                        noise[idx-2:idx+3] -= np.array([0.4, 0.8, 1.2, 0.8, 0.4])
                
                stage_vmg = trend + noise
                session_vmg.extend(stage_vmg)
                session_leg_types.extend([stage['type']] * length)
            
            temp_df = pd.DataFrame({
                '時間': time_range,
                'VMG (kt)': session_vmg,
                'レグタイプ': session_leg_types,
                'セッション': session
            })
            
            compare_vmg_data.append(temp_df)
        
        # 現在のセッションデータに名前を付ける
        vmg_df['セッション'] = st.session_state.selected_stats_session
        
        # すべてのデータを結合
        all_vmg_data = pd.concat([vmg_df] + compare_vmg_data, ignore_index=True)
        
        # セッション間のVMG比較（レグタイプで色分け）
        fig = px.line(
            all_vmg_data,
            x='時間',
            y='VMG (kt)',
            color='セッション',
            line_dash='レグタイプ',
            title='セッション間のVMG比較',
            labels={'VMG (kt)': 'VMG (kt)', 'time': '時間'}
        )
        
        # レイアウトの調整
        fig.update_layout(
            xaxis_title='時間',
            yaxis_title='VMG (kt)',
            legend_title='セッション / レグタイプ',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 風上と風下のVMG比較
        st.markdown("### レグタイプ別VMG比較")
        
        # 各セッションのレグタイプ別平均VMGを計算
        upwind_stats = []
        downwind_stats = []
        
        for session in [st.session_state.selected_stats_session] + st.session_state.comparison_sessions:
            session_data = all_vmg_data[all_vmg_data['セッション'] == session]
            
            upwind_data = session_data[session_data['レグタイプ'] == '風上']['VMG (kt)']
            downwind_data = session_data[session_data['レグタイプ'] == '風下']['VMG (kt)']
            
            upwind_stats.append({
                'セッション': session,
                'レグタイプ': '風上',
                '平均VMG': upwind_data.mean(),
                '最大VMG': upwind_data.max(),
                '標準偏差': upwind_data.std()
            })
            
            downwind_stats.append({
                'セッション': session,
                'レグタイプ': '風下',
                '平均VMG': downwind_data.mean(),
                '最大VMG': downwind_data.max(),
                '標準偏差': downwind_data.std()
            })
        
        # 統計データをデータフレームに変換
        vmg_stats_df = pd.DataFrame(upwind_stats + downwind_stats)
        
        # レグタイプ別VMG比較グラフ
        fig_stats = px.bar(
            vmg_stats_df,
            x='セッション',
            y='平均VMG',
            color='レグタイプ',
            barmode='group',
            error_y='標準偏差',
            title='セッション間のレグタイプ別平均VMG比較'
        )
        
        # レイアウトの調整
        fig_stats.update_layout(
            xaxis_title='セッション',
            yaxis_title='平均VMG (kt)',
            legend_title='レグタイプ',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_stats, use_container_width=True)
        
        # 統計データの表示
        st.dataframe(vmg_stats_df.round(2), use_container_width=True)
        
    else:
        # 単一セッションのVMG時系列グラフ（レグタイプで色分け）
        fig = px.line(
            vmg_df,
            x='時間',
            y='VMG (kt)',
            color='レグタイプ',
            title='VMGの時間変化',
            labels={'VMG (kt)': 'VMG (kt)', 'time': '時間'}
        )
        
        # レイアウトの調整
        fig.update_layout(
            xaxis_title='時間',
            yaxis_title='VMG (kt)',
            legend_title='レグタイプ',
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 風上と風下のVMG分布
        st.markdown("### レグタイプ別VMG分布")
        
        fig_dist = px.histogram(
            vmg_df,
            x='VMG (kt)',
            color='レグタイプ',
            barmode='overlay',
            opacity=0.7,
            histnorm='percent',
            title='レグタイプ別VMG分布'
        )
        
        # レイアウトの調整
        fig_dist.update_layout(
            xaxis_title='VMG (kt)',
            yaxis_title='割合 (%)',
            legend_title='レグタイプ',
            template='plotly_white'
        )
        
        st.plotly_chart(fig_dist, use_container_width=True)
    
    # VMGのヒートマップ分析
    st.markdown("### VMGのヒートマップ分析")
    
    # VMGのヒートマップ用データの説明
    st.info("実際のアプリケーションでは、GPSトラックと風データからマップ上のVMGヒートマップが生成されます。MVPでは、サンプル画像で表現します。")
    
    # サンプルヒートマップ画像
    st.image("https://via.placeholder.com/800x400?text=VMG+Heatmap+Example", use_container_width=True)
    
    # 風向角度とVMGの関係分析
    st.markdown("### 風向角度とVMGの関係")
    
    # 風向角度とVMGのデータ生成
    n_points = 200
    np.random.seed(42)
    
    # 風向角度（0-180度、0が真正面から、180が真後ろから）
    angles = np.random.uniform(0, 180, n_points)
    
    # 風向角度に応じたVMGモデリング（45度と135度付近で最大）
    base_vmg = 3.0
    angle_factor = 2.0 * np.sin(np.deg2rad(angles) * 2 - np.pi/2) + 2.0
    
    # ノイズを追加
    vmg_by_angle = base_vmg + angle_factor + np.random.normal(0, 0.5, n_points)
    vmg_by_angle = np.maximum(vmg_by_angle, 0)  # 負のVMGを除外
    
    # データフレーム作成
    angle_vmg_df = pd.DataFrame({
        '風向角度 (度)': angles,
        'VMG (kt)': vmg_by_angle
    })
    
    # 風向角度とVMGの散布図
    fig_angle = px.scatter(
        angle_vmg_df,
        x='風向角度 (度)',
        y='VMG (kt)',
        opacity=0.7,
        title='風向角度とVMGの関係'
    )
    
    # 傾向線の追加
    fig_angle.add_trace(
        go.Scatter(
            x=np.linspace(0, 180, 100),
            y=base_vmg + 2.0 * np.sin(np.deg2rad(np.linspace(0, 180, 100)) * 2 - np.pi/2) + 2.0,
            mode='lines',
            name='傾向線',
            line=dict(color='red', width=2)
        )
    )
    
    # レイアウトの調整
    fig_angle.update_layout(
        xaxis_title='風向角度 (度)',
        yaxis_title='VMG (kt)',
        template='plotly_white',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # 最適な風向角度を示す垂直線
    fig_angle.add_vline(x=45, line_width=1, line_dash="dash", line_color="green")
    fig_angle.add_annotation(x=45, y=0, text="最適風上角度", showarrow=False, yshift=10)
    
    fig_angle.add_vline(x=135, line_width=1, line_dash="dash", line_color="green")
    fig_angle.add_annotation(x=135, y=0, text="最適風下角度", showarrow=False, yshift=10)
    
    st.plotly_chart(fig_angle, use_container_width=True)
    
    # 最適VMG分析
    st.markdown("### 最適VMG分析")
    
    # 最適VMGの説明
    st.info("理論的な最適VMGと実際のパフォーマンスを比較します。実際のアプリケーションでは、ボートの極図（polar diagram）と計測データから計算されます。")
    
    # 最適VMGに対するパフォーマンス評価データ
    vmg_performance = {
        '風速範囲 (kt)': ['0-5', '5-10', '10-15', '15-20', '20+'],
        '風上最適VMG (kt)': [2.1, 3.4, 3.8, 3.5, 3.0],
        '風上実際VMG (kt)': [1.9, 3.2, 3.5, 3.1, 2.5],
        '風上効率 (%)': [90, 94, 92, 89, 83],
        '風下最適VMG (kt)': [2.8, 4.2, 4.8, 5.1, 5.5],
        '風下実際VMG (kt)': [2.5, 4.0, 4.5, 4.7, 4.9],
        '風下効率 (%)': [89, 95, 94, 92, 89]
    }
    
    vmg_perf_df = pd.DataFrame(vmg_performance)
    
    # 効率の棒グラフ
    fig_eff = px.bar(
        vmg_perf_df,
        x='風速範囲 (kt)',
        y=['風上効率 (%)', '風下効率 (%)'],
        barmode='group',
        title='風速範囲別VMG効率'
    )
    
    # レイアウトの調整
    fig_eff.update_layout(
        xaxis_title='風速範囲 (kt)',
        yaxis_title='効率 (%)',
        legend_title='効率タイプ',
        template='plotly_white'
    )
    
    st.plotly_chart(fig_eff, use_container_width=True)
    
    # 詳細データの表示
    st.dataframe(vmg_perf_df, use_container_width=True)

def render_strategy_tab():
    """戦略分析タブの表示"""
    st.session_state.chart_type = "strategy"
    
    st.subheader("戦略分析")
    
    # 戦略ポイント一覧
    st.markdown("### 検出された戦略ポイント")
    
    # 戦略ポイントのサンプルデータ
    strategy_data = {
        '時刻': ['13:10', '13:38', '14:05', '14:32', '15:00', '15:15', '15:30', '15:42'],
        'タイプ': ['風向シフト対応', 'レイライン接近', '風向シフト対応', '障害物回避', 'コース変更', 'タック', 'レイライン接近', '風向シフト対応'],
        '判断': ['シフト前にタック', 'レイラインでタック', '様子見', '早めの回避行動', '風上へのコース変更', '早めのタック', 'レイラインでタック', 'シフト後にタック'],
        '結果': ['レグ短縮', 'オーバースタンド', '不利なレイヤー', 'ロス最小化', '有利なレイヤー獲得', '風速域改善', 'コース短縮', '方位角改善'],
        '重要度': ['高', '中', '高', '低', '中', '中', '高', '高'],
        '評価': ['最適', '改善必要', '不適切', '適切', '最適', '適切', '最適', '改善必要']
    }
    
    strategy_df = pd.DataFrame(strategy_data)
    
    # 評価と重要度を数値化（可視化用）
    eval_map = {'最適': 4, '適切': 3, '改善必要': 2, '不適切': 1}
    importance_map = {'高': 3, '中': 2, '低': 1}
    
    strategy_df['評価スコア'] = strategy_df['評価'].map(eval_map)
    strategy_df['重要度スコア'] = strategy_df['重要度'].map(importance_map)
    
    # 戦略ポイントの時系列表示
    fig_timeline = px.scatter(
        strategy_df,
        x='時刻',
        y='タイプ',
        size='重要度スコア',
        color='評価',
        hover_name='判断',
        hover_data=['結果'],
        title='戦略ポイントのタイムライン'
    )
    
    # レイアウトの調整
    fig_timeline.update_layout(
        xaxis_title='時刻',
        yaxis_title='戦略ポイントタイプ',
        legend_title='評価',
        template='plotly_white'
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # 戦略ポイントのテーブル表示
    st.dataframe(strategy_df.drop(columns=['評価スコア', '重要度スコア']), use_container_width=True)
    
    # 戦略的判断の分布
    st.markdown("### 戦略的判断の分布と評価")
    
    # タイプ別の評価分布
    evaluation_count = pd.crosstab(strategy_df['タイプ'], strategy_df['評価'])
    
    fig_eval = px.bar(
        evaluation_count,
        title='タイプ別の評価分布'
    )
    
    # レイアウトの調整
    fig_eval.update_layout(
        xaxis_title='戦略ポイントタイプ',
        yaxis_title='件数',
        legend_title='評価',
        template='plotly_white'
    )
    
    st.plotly_chart(fig_eval, use_container_width=True)
    
    # レース結果への影響分析
    st.markdown("### 戦略判断のレース結果への影響")
    
    # 判断と結果の影響のサンプルデータ
    impact_data = {
        '戦略判断': ['最適な風向シフト対応', '的確なレイライン判断', '良好なスタート位置', '効率的なタック実行', '優れた見張り', '適切なセールトリム'],
        '推定利得 (秒)': [45, 30, 25, 20, 15, 10],
        '確信度 (%)': [90, 85, 80, 95, 70, 75]
    }
    
    impact_df = pd.DataFrame(impact_data)
    
    # 利得の横棒グラフ
    fig_impact = px.bar(
        impact_df,
        x='推定利得 (秒)',
        y='戦略判断',
        error_x=impact_df['推定利得 (秒)'] * (1 - impact_df['確信度 (%)'] / 100),  # 確信度に基づくエラーバー
        orientation='h',
        title='戦略判断の利得推定'
    )
    
    # レイアウトの調整
    fig_impact.update_layout(
        xaxis_title='推定利得 (秒)',
        yaxis_title='戦略判断',
        template='plotly_white'
    )
    
    st.plotly_chart(fig_impact, use_container_width=True)
    
    # 戦略的判断の空間分布
    st.markdown("### 戦略的判断の空間分布")
    
    # 空間分布の説明
    st.info("実際のアプリケーションでは、GPSトラック上に戦略ポイントをマッピングし、空間的な分布を表示します。MVPでは、サンプル画像で表現します。")
    
    # サンプル戦略マップ
    st.image("https://via.placeholder.com/800x400?text=Strategy+Points+Map", use_container_width=True)
    
    # 各戦略ポイントでの風と速度の状況
    st.markdown("### 各戦略ポイントでの環境条件")
    
    # 環境条件のサンプルデータ
    conditions_data = {
        '時刻': ['13:10', '13:38', '14:05', '14:32', '15:00', '15:15', '15:30', '15:42'],
        '風向 (度)': [210, 225, 215, 220, 235, 240, 230, 220],
        '風速 (kt)': [12.5, 13.2, 11.8, 12.0, 14.5, 15.0, 14.2, 13.5],
        '艇速 (kt)': [6.2, 5.8, 6.0, 6.5, 7.2, 6.8, 7.0, 6.5],
        'VMG (kt)': [3.4, 3.2, 3.3, 3.5, 4.8, 3.6, 3.8, 3.5],
        '波高 (m)': [0.5, 0.6, 0.5, 0.6, 0.8, 0.9, 0.8, 0.7],
        '潮流 (kt)': [0.2, 0.3, 0.2, 0.2, 0.4, 0.4, 0.3, 0.3]
    }
    
    conditions_df = pd.DataFrame(conditions_data)
    
    # 各戦略ポイントでの条件を可視化
    fig_cond = make_subplots(rows=2, cols=2, 
                             subplot_titles=('風向', '風速', '艇速', 'VMG'),
                             shared_xaxes=True)
    
    fig_cond.add_trace(
        go.Scatter(x=conditions_df['時刻'], y=conditions_df['風向 (度)'], mode='lines+markers'),
        row=1, col=1
    )
    
    fig_cond.add_trace(
        go.Scatter(x=conditions_df['時刻'], y=conditions_df['風速 (kt)'], mode='lines+markers'),
        row=1, col=2
    )
    
    fig_cond.add_trace(
        go.Scatter(x=conditions_df['時刻'], y=conditions_df['艇速 (kt)'], mode='lines+markers'),
        row=2, col=1
    )
    
    fig_cond.add_trace(
        go.Scatter(x=conditions_df['時刻'], y=conditions_df['VMG (kt)'], mode='lines+markers'),
        row=2, col=2
    )
    
    # レイアウトの調整
    fig_cond.update_layout(
        title='戦略ポイントでの環境条件',
        showlegend=False,
        template='plotly_white',
        height=500
    )
    
    st.plotly_chart(fig_cond, use_container_width=True)
    
    # 環境条件データの表示
    st.dataframe(conditions_df, use_container_width=True)
    
    # フィードバックと改善提案
    st.markdown("### 戦略的改善提案")
    
    improvement_points = [
        "**風向シフトの検出と対応**: 右シフトのパターンをより早く認識し、事前対応することでレグタイムを約30秒短縮できます。",
        "**レイラインの判断**: レイラインへの接近時に2回のオーバースタンドが観測されました。最終アプローチでの位置把握を改善してください。",
        "**タック/ジャイブのタイミング**: 風向変化の直前ではなく、安定した風を得られるタイミングでのマニューバーを心がけてください。",
        "**周囲艇との位置関係**: 特に混雑したマーク回航では、早めのポジショニングが重要です。他艇の影響を最小化できます。",
        "**コース選択のバランス**: 極端な端のコースよりも、中央寄りでオプションを保ちながら風の変化に対応できる位置を維持することを推奨します。"
    ]
    
    for i, point in enumerate(improvement_points):
        st.markdown(f"{i+1}. {point}")

def render_velocity_settings():
    """速度分析設定の表示"""
    st.markdown("#### 速度チャート設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bin_count = st.slider("ヒストグラムのビン数", 5, 30, 20)
    
    with col2:
        smoothing = st.slider("時系列グラフの平滑化", 0.0, 1.0, 0.0)
    
    show_statistics = st.checkbox("統計情報を表示", True)
    show_distribution = st.checkbox("分布を表示", True)
    
    st.markdown("#### 風向別速度設定")
    
    polar_resolution = st.select_slider(
        "解像度",
        options=["低", "中", "高"],
        value="中"
    )
    
    polar_color_scale = st.selectbox(
        "カラースケール",
        ["Viridis", "Plasma", "Cividis", "Turbo", "RdBu"]
    )

def render_wind_settings():
    """風向分析設定の表示"""
    st.markdown("#### 風向チャート設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        time_interval = st.select_slider(
            "時間間隔",
            options=["1秒", "5秒", "10秒", "30秒", "1分"],
            value="1分"
        )
    
    with col2:
        smoothing = st.slider("時系列グラフの平滑化", 0.0, 1.0, 0.2)
    
    # 風配図設定
    st.markdown("#### 風配図設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        resolution = st.select_slider(
            "解像度",
            options=["低", "中", "高"],
            value="中"
        )
    
    with col2:
        plot_type = st.selectbox(
            "プロットタイプ",
            ["散布図", "ヒートマップ", "コンター"]
        )
    
    # シフト検出設定
    st.markdown("#### シフト検出設定")
    
    min_shift = st.slider("最小シフト量 (度)", 5, 30, 8)
    detection_window = st.slider("検出ウィンドウ (秒)", 10, 120, 60)

def render_vmg_settings():
    """VMG分析設定の表示"""
    st.markdown("#### VMGチャート設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        time_interval = st.select_slider(
            "時間間隔",
            options=["1秒", "5秒", "10秒", "30秒", "1分"],
            value="1分"
        )
    
    with col2:
        smoothing = st.slider("時系列グラフの平滑化", 0.0, 1.0, 0.2)
    
    show_trend_line = st.checkbox("トレンドラインを表示", True)
    highlight_optimal = st.checkbox("最適値をハイライト", True)
    
    # VMG分析設定
    st.markdown("#### VMG分析設定")
    
    wind_angle_resolution = st.slider("風向角度解像度 (度)", 1, 10, 5)
    velocity_source = st.selectbox(
        "速度データソース",
        ["GPS", "船速計", "推定値"]
    )
    polar_reference = st.checkbox("理論極図と比較", True)

def render_strategy_settings():
    """戦略分析設定の表示"""
    st.markdown("#### 戦略ポイント設定")
    
    col1, col2 = st.columns(2)
    
    with col1:
        min_importance = st.select_slider(
            "最小重要度",
            options=["すべて", "低", "中", "高"],
            value="すべて"
        )
    
    with col2:
        point_types = st.multiselect(
            "表示するポイントタイプ",
            ["風向シフト対応", "レイライン接近", "障害物回避", "コース変更", "タック", "ジャイブ"],
            ["風向シフト対応", "レイライン接近", "コース変更", "タック"]
        )
    
    show_timeline = st.checkbox("タイムラインを表示", True)
    show_map = st.checkbox("マップ上に表示", True)
    
    # 分析設定
    st.markdown("#### 分析設定")
    
    analysis_detail = st.select_slider(
        "分析詳細度",
        options=["低", "中", "高"],
        value="中"
    )
    
    show_recommendations = st.checkbox("改善提案を表示", True)
    comparison_reference = st.selectbox(
        "比較基準",
        ["理論最適値", "過去最高パフォーマンス", "フリート平均", "なし"]
    )

def make_subplots(rows=1, cols=1, subplot_titles=None, shared_xaxes=False):
    """Plotlyのmake_subplotsの簡易実装"""
    from plotly.subplots import make_subplots as plotly_make_subplots
    return plotly_make_subplots(rows=rows, cols=cols, subplot_titles=subplot_titles, shared_xaxes=shared_xaxes)

if __name__ == "__main__":
    render_page()
