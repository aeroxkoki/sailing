# -*- coding: utf-8 -*-
"""
ui.integrated.pages.chart_view

セーリング戦略分析システムの統計チャートビューページ
時系列分析、ボックスプロット、ヒートマップなど様々なチャートを表示します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import json
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# チャートコンポーネントのインポート
from ui.integrated.components.charts.speed_profile_chart import SpeedProfileChart
from ui.integrated.components.charts.wind_angle_chart import WindAngleChart
from ui.integrated.components.charts.vmg_analysis_chart import VMGAnalysisChart

def render_page():
    """統計チャートビューページをレンダリングする関数"""
    
    st.title("統計チャート分析")
    
    # セッション状態の初期化
    if 'selected_chart_session' not in st.session_state:
        st.session_state.selected_chart_session = None
    
    if 'selected_chart_type' not in st.session_state:
        st.session_state.selected_chart_type = "speed_profile"
    
    # サイドバーのセッション選択
    with st.sidebar:
        st.subheader("セッション選択")
        # 実際にはプロジェクト管理システムからセッションを取得する
        # サンプルとしてダミーデータを使用
        sessions = ["2025/03/27 レース練習", "2025/03/25 風向変化トレーニング", "2025/03/20 スピードテスト"]
        selected_session = st.selectbox("分析するセッションを選択", sessions)
        
        if selected_session != st.session_state.selected_chart_session:
            st.session_state.selected_chart_session = selected_session
            # セッションが変更されたら関連データを読み込む処理をここに追加
            # st.experimental_rerun()
        
        # チャートタイプの選択
        st.subheader("チャートタイプ")
        chart_types = {
            "speed_profile": "速度プロファイル",
            "wind_angle": "風向角度効率",
            "vmg_analysis": "VMG分析",
            "height_analysis": "ヒール角分析",
            "tack_analysis": "タック分析"
        }
        
        selected_chart_type = st.radio(
            "チャートタイプを選択",
            list(chart_types.keys()),
            format_func=lambda x: chart_types[x],
            index=list(chart_types.keys()).index(st.session_state.selected_chart_type)
        )
        
        if selected_chart_type != st.session_state.selected_chart_type:
            st.session_state.selected_chart_type = selected_chart_type
            st.experimental_rerun()
    
    # 選択されたセッションに関する情報を表示
    if st.session_state.selected_chart_session:
        st.markdown(f"## セッション: {st.session_state.selected_chart_session}")
        
        # 選択されたチャートタイプの表示
        chart_type = st.session_state.selected_chart_type
        
        # テスト用にサンプルデータを生成
        sample_data = generate_sample_data()
        
        # チャートタイプに応じたコンテンツの表示
        if chart_type == "speed_profile":
            render_speed_profile(sample_data)
        elif chart_type == "wind_angle":
            render_wind_angle_chart(sample_data)
        elif chart_type == "vmg_analysis":
            render_vmg_analysis(sample_data)
        elif chart_type == "height_analysis":
            render_height_analysis(sample_data)
        elif chart_type == "tack_analysis":
            render_tack_analysis(sample_data)
        
        # エクスポートオプション
        st.divider()
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            if st.button("画像としてエクスポート（PNG）", use_container_width=True):
                st.info("画像エクスポート機能は開発中です。")
        
        with export_col2:
            if st.button("データとしてエクスポート（CSV）", use_container_width=True):
                st.info("データエクスポート機能は開発中です。")
        
        with export_col3:
            if st.button("レポートに追加", use_container_width=True):
                st.info("レポート追加機能は開発中です。")
    
    else:
        # セッションが選択されていない場合
        st.info("分析するセッションを左側のサイドバーから選択してください。")


def render_speed_profile(data):
    """
    速度プロファイルチャートの表示
    
    Parameters
    ----------
    data : dict
        チャート表示用のデータ
    """
    # チャートコンポーネントのインスタンス化
    speed_chart = SpeedProfileChart(title="セーリング速度プロファイル")
    
    # チャートの説明
    st.markdown("""
    ### 速度プロファイル分析
    
    このチャートでは時間経過による船速の変化を表示します。移動平均や目標速度の表示、注釈の表示/非表示などを設定できます。
    """)
    
    # チャート設定用のエクスパンダー
    with st.expander("チャート設定", expanded=False):
        # チャートコントロールの表示
        updated_options = speed_chart.render_controls()
        
        # オプションの更新
        speed_chart.update_options(updated_options)
    
    # イベントデータの作成（サンプル）
    events = []
    for i in range(5):
        event_time = data["speed_data"]["timestamp"].iloc[20 * (i + 1)]
        event_type = ["tack", "gybe", "mark_rounding"][i % 3]
        
        events.append({
            "timestamp": event_time,
            "type": event_type,
            "description": f"{event_type.capitalize()} at {event_time.strftime('%H:%M:%S')}"
        })
    
    # チャートの描画
    speed_chart.render(data["speed_data"], events)


def render_wind_angle_chart(data):
    """
    風向角度効率チャートの表示
    
    Parameters
    ----------
    data : dict
        チャート表示用のデータ
    """
    # チャートコンポーネントのインスタンス化
    wind_angle_chart = WindAngleChart(title="風向角度効率分析")
    
    # チャートの説明
    st.markdown("""
    ### 風向角度効率分析
    
    このチャートでは異なる風向角度における船速とVMG（Velocity Made Good）を極座標で表示します。
    最適な風向角度やパフォーマンス特性を分析できます。
    """)
    
    # チャート設定用のエクスパンダー
    with st.expander("チャート設定", expanded=False):
        # チャートコントロールの表示
        updated_options = wind_angle_chart.render_controls()
        
        # オプションの更新
        wind_angle_chart.update_options(updated_options)
    
    # 極図データ（理想曲線用）
    polar_data = {
        "angles": list(range(0, 181, 5)),
        "speeds": [0] + [3 + 5 * np.sin(np.radians(a)) for a in range(5, 176, 5)] + [0]
    }
    
    # チャートの描画
    wind_angle_chart.render(data["angle_data"], polar_data)


def render_vmg_analysis(data):
    """
    VMG分析チャートの表示
    
    Parameters
    ----------
    data : dict
        チャート表示用のデータ
    """
    # チャートコンポーネントのインスタンス化
    vmg_chart = VMGAnalysisChart(title="VMG（Velocity Made Good）分析")
    
    # チャートの説明
    st.markdown("""
    ### VMG（対風速度）分析
    
    このチャートでは風上および風下における対風速度（VMG）を分析します。
    風上/風下セグメントのVMG分布、時系列変化、風向角度との関係などを視覚化します。
    """)
    
    # チャート設定用のエクスパンダー
    with st.expander("チャート設定", expanded=False):
        # チャートコントロールの表示
        updated_options = vmg_chart.render_controls()
        
        # オプションの更新
        vmg_chart.update_options(updated_options)
    
    # 目標VMG値
    target_vmg = {
        "upwind": 3.5,  # 風上目標VMG
        "downwind": -4.2  # 風下目標VMG
    }
    
    # チャートの描画
    vmg_chart.render(data["vmg_data"], target_vmg)


def render_height_analysis(data):
    """
    ヒール角分析チャートの表示（プレースホルダ）
    
    Parameters
    ----------
    data : dict
        チャート表示用のデータ
    """
    st.markdown("""
    ### ヒール角分析
    
    このチャートではヒール角（船体の傾き）とそのパフォーマンスへの影響を分析します。
    """)
    
    # プレースホルダとしてまだ実装されていないことを表示
    st.info("ヒール角分析機能は現在開発中です。次回のアップデートで追加される予定です。")
    
    # サンプルグラフを表示
    heel_data = data["heel_data"]
    
    # 基本的な散布図を表示
    fig = px.scatter(
        heel_data,
        x="heel_angle",
        y="boat_speed",
        color="wind_speed",
        labels={
            "heel_angle": "ヒール角 (度)",
            "boat_speed": "船速 (ノット)",
            "wind_speed": "風速 (ノット)"
        },
        title="ヒール角と船速の関係"
    )
    
    # 回帰曲線の追加
    heel_range = np.linspace(heel_data["heel_angle"].min(), heel_data["heel_angle"].max(), 100)
    poly_coeffs = np.polyfit(heel_data["heel_angle"], heel_data["boat_speed"], 2)
    poly_fn = np.poly1d(poly_coeffs)
    fitted_speed = poly_fn(heel_range)
    
    fig.add_trace(
        go.Scatter(
            x=heel_range,
            y=fitted_speed,
            mode="lines",
            line=dict(color="red", width=2),
            name="傾向曲線"
        )
    )
    
    # 最適ヒール角の検出
    optimal_idx = np.argmax(fitted_speed)
    optimal_heel = heel_range[optimal_idx]
    optimal_speed = fitted_speed[optimal_idx]
    
    fig.add_trace(
        go.Scatter(
            x=[optimal_heel],
            y=[optimal_speed],
            mode="markers+text",
            marker=dict(size=12, color="green", symbol="star"),
            text=f"最適: {optimal_heel:.1f}°",
            textposition="top center",
            name=f"最適ヒール角: {optimal_heel:.1f}°"
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ヒール角の統計情報
    heel_mean = heel_data["heel_angle"].mean()
    heel_std = heel_data["heel_angle"].std()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("平均ヒール角", f"{heel_mean:.1f}°")
    
    with col2:
        st.metric("最適ヒール角", f"{optimal_heel:.1f}°")
    
    with col3:
        st.metric("ヒール角偏差", f"±{heel_std:.1f}°")


def render_tack_analysis(data):
    """
    タック分析チャートの表示（プレースホルダ）
    
    Parameters
    ----------
    data : dict
        チャート表示用のデータ
    """
    st.markdown("""
    ### タック分析
    
    このチャートではタックの性能と効率を分析します。タック所要時間、速度損失、角度変化などを視覚化します。
    """)
    
    # プレースホルダとしてまだ実装されていないことを表示
    st.info("タック分析機能は現在開発中です。次回のアップデートで追加される予定です。")
    
    # サンプルデータの表示
    tack_data = pd.DataFrame({
        "タック番号": list(range(1, 11)),
        "所要時間(秒)": [8.2, 7.5, 9.1, 7.8, 6.9, 8.4, 7.7, 8.0, 7.6, 6.8],
        "速度損失(ノット)": [1.2, 0.8, 1.5, 0.9, 0.7, 1.0, 0.8, 1.1, 0.9, 0.6],
        "最終角度(度)": [85, 88, 82, 87, 90, 86, 89, 87, 88, 91]
    })
    
    # タック分析のサンプルグラフ
    fig1 = px.bar(
        tack_data,
        x="タック番号",
        y="所要時間(秒)",
        title="タック所要時間分析"
    )
    
    fig1.update_layout(
        height=300,
        yaxis=dict(title="所要時間 (秒)"),
        xaxis=dict(title="タック番号")
    )
    
    st.plotly_chart(fig1, use_container_width=True)
    
    # 2列レイアウトで残りのグラフを表示
    col1, col2 = st.columns(2)
    
    with col1:
        fig2 = px.scatter(
            tack_data,
            x="所要時間(秒)",
            y="速度損失(ノット)",
            size="最終角度(度)",
            color="タック番号",
            title="タック効率分析"
        )
        
        fig2.update_layout(
            height=350,
            xaxis=dict(title="所要時間 (秒)"),
            yaxis=dict(title="速度損失 (ノット)")
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    with col2:
        # タックパフォーマンスのレーダーチャート
        # いくつかのタックパフォーマンス指標を作成
        performance_data = pd.DataFrame({
            "指標": ["速度維持", "角度精度", "実行時間", "風の利用", "軌跡効率"],
            "値": [85, 90, 75, 80, 85]  # パーセント値
        })
        
        # レーダーチャートの作成
        fig3 = go.Figure()
        
        fig3.add_trace(go.Scatterpolar(
            r=performance_data["値"],
            theta=performance_data["指標"],
            fill='toself',
            name='実績'
        ))
        
        # 目標値
        fig3.add_trace(go.Scatterpolar(
            r=[90, 90, 90, 90, 90],
            theta=performance_data["指標"],
            fill='toself',
            name='目標',
            opacity=0.5
        ))
        
        fig3.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="タックパフォーマンスレーダー",
            height=350
        )
        
        st.plotly_chart(fig3, use_container_width=True)


def generate_sample_data():
    """
    テスト用のサンプルデータを生成する関数
    
    Returns
    -------
    dict
        チャート表示用のデータ辞書
    """
    # 時間の設定
    start_time = datetime.now() - timedelta(hours=2)
    times = pd.date_range(start=start_time, periods=100, freq="1min")
    
    # 船速データ
    speed_data = pd.DataFrame({
        "timestamp": times,
        "boat_speed": np.random.normal(6, 1, len(times)) + np.sin(np.linspace(0, 8, len(times))),
        "vmg": np.random.normal(3, 1.5, len(times)) + np.sin(np.linspace(0, 6, len(times))) * 0.8,
        "wind_speed": np.random.normal(12, 2, len(times)) + np.sin(np.linspace(0, 4, len(times)))
    })
    
    # 風向角度データ
    angles = np.linspace(0, 180, 200)
    angle_data = pd.DataFrame({
        "wind_angle": angles,
        "boat_speed": 5 + 2 * np.sin(np.radians(angles)),
        "vmg": 3.5 * np.cos(np.radians(angles)),
        "apparent_wind": 10 + 2 * np.sin(np.radians(angles))
    })
    
    # VMG分析用データ
    vmg_data = pd.DataFrame({
        "timestamp": times,
        "wind_angle": np.abs((np.cumsum(np.random.normal(0, 3, len(times))) % 360) - 180),
        "boat_speed": np.random.normal(6, 1, len(times)) + np.sin(np.linspace(0, 8, len(times))),
        "vmg": np.random.normal(2, 2, len(times)) * np.cos(np.linspace(0, 6, len(times))),
        "wind_speed": np.random.normal(12, 2, len(times))
    })
    
    # ヒール角分析用データ
    heel_data = pd.DataFrame({
        "timestamp": times,
        "heel_angle": np.random.normal(15, 5, len(times)),
        "boat_speed": np.random.normal(6, 1, len(times)),
        "wind_speed": np.random.normal(12, 2, len(times))
    })
    
    # データの相関を持たせる（ヒール角と速度の関係）
    # 適度なヒール角は速度に好影響、過度なヒール角は悪影響というモデル
    optimal_heel = 18  # 最適なヒール角
    for i in range(len(heel_data)):
        heel = heel_data.loc[i, "heel_angle"]
        heel_effect = -0.02 * (heel - optimal_heel) ** 2  # 最適値からの二次関数で効果を表現
        heel_data.loc[i, "boat_speed"] += heel_effect
    
    return {
        "speed_data": speed_data,
        "angle_data": angle_data,
        "vmg_data": vmg_data,
        "heel_data": heel_data
    }


if __name__ == "__main__":
    render_page()
