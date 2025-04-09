"""
ui.integrated.pages.timeline_view

セーリング戦略分析システムのタイムラインビューページ
時間経過に沿ったイベントやデータパラメータの変化を視覚化します。
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

# タイムラインコンポーネントのインポート
from ui.integrated.components.timeline.timeline_view_component import TimelineViewComponent

def render_page():
    """タイムラインビューページをレンダリングする関数"""
    
    st.title("タイムライン分析")
    
    # セッション状態の初期化
    if 'selected_timeline_session' not in st.session_state:
        st.session_state.selected_timeline_session = None
    
    # サイドバーのセッション選択
    with st.sidebar:
        st.subheader("セッション選択")
        # 実際にはプロジェクト管理システムからセッションを取得する
        # サンプルとしてダミーデータを使用
        sessions = ["2025/03/27 レース練習", "2025/03/25 風向変化トレーニング", "2025/03/20 スピードテスト"]
        selected_session = st.selectbox("分析するセッションを選択", sessions)
        
        if selected_session != st.session_state.selected_timeline_session:
            st.session_state.selected_timeline_session = selected_session
            # セッションが変更されたら関連データを読み込む処理をここに追加
            # st.experimental_rerun()
        
        # 追加のフィルタリングオプション
        st.subheader("フィルタリングオプション")
        
        # イベントタイプフィルター
        event_types = ["タック", "ジャイブ", "マーク", "風向シフト", "戦略判断"]
        selected_event_types = st.multiselect(
            "イベントタイプ",
            options=event_types,
            default=event_types
        )
        
        # パラメータ選択
        available_parameters = ["船速", "風速", "風向", "ヒール角", "VMG", "方位"]
        selected_parameters = st.multiselect(
            "表示パラメータ",
            options=available_parameters,
            default=["船速", "風速", "VMG"]
        )
        
        # 時間範囲選択
        st.subheader("時間範囲")
        time_range = st.slider(
            "表示時間範囲",
            min_value=0,
            max_value=100,
            value=(0, 100)
        )
    
    # 選択されたセッションに関する情報を表示
    if st.session_state.selected_timeline_session:
        st.markdown(f"## セッション: {st.session_state.selected_timeline_session}")
        
        # テスト用にサンプルデータを生成
        sample_data = generate_sample_data()
        
        # イベントタイプでフィルタリング
        event_data = sample_data["events"]
        if selected_event_types:
            event_data = event_data[event_data["type"].isin(selected_event_types)]
        
        # タイムラインコンポーネントを使用
        timeline_component = TimelineViewComponent(title="航行タイムライン分析")
        
        # オプションの設定
        timeline_options = {
            "parameter_count": len(selected_parameters),
            "height": 400
        }
        
        # オプションを更新
        timeline_component.update_options(timeline_options)
        
        # タイムラインコンポーネントの描画
        timeline_component.render(sample_data["time_series"], event_data)
        
        # フェーズ分析セクション
        st.markdown("## フェーズ分析")
        
        # フェーズ分析のタブ
        tab1, tab2, tab3 = st.tabs(["レグ分析", "マニューバー分析", "風向変化分析"])
        
        with tab1:
            render_leg_analysis(sample_data)
        
        with tab2:
            render_maneuver_analysis(sample_data)
        
        with tab3:
            render_wind_shift_analysis(sample_data)
        
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


def render_leg_analysis(data):
    """
    レグ分析を表示
    
    Parameters
    ----------
    data : dict
        分析用データ
    """
    st.markdown("### レグ（コースの区間）分析")
    
    # レグデータのサンプル
    leg_data = pd.DataFrame({
        "レグ番号": [1, 2, 3, 4, 5],
        "種類": ["風上", "風下", "風上", "リーチ", "風上"],
        "所要時間(分)": [12.5, 8.2, 11.8, 5.4, 10.2],
        "平均速度(kt)": [5.8, 6.7, 6.1, 7.2, 5.9],
        "平均VMG(kt)": [3.5, 4.1, 3.7, 5.3, 3.6],
        "風向変化(度)": [12, 5, 8, 3, 10]
    })
    
    # レグデータのテーブル表示
    st.dataframe(leg_data, use_container_width=True)
    
    # グラフ表示
    col1, col2 = st.columns(2)
    
    with col1:
        # レグ所要時間グラフ
        fig1 = px.bar(
            leg_data,
            x="レグ番号",
            y="所要時間(分)",
            color="種類",
            title="レグ別所要時間"
        )
        
        # レイアウト調整
        fig1.update_layout(
            height=350,
            xaxis_title="レグ番号",
            yaxis_title="所要時間 (分)"
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # レグ速度比較グラフ
        fig2 = go.Figure()
        
        # 速度データの追加
        fig2.add_trace(
            go.Bar(
                name="平均速度",
                x=leg_data["レグ番号"],
                y=leg_data["平均速度(kt)"],
                marker_color='blue'
            )
        )
        
        # VMGデータの追加
        fig2.add_trace(
            go.Bar(
                name="平均VMG",
                x=leg_data["レグ番号"],
                y=leg_data["平均VMG(kt)"],
                marker_color='green'
            )
        )
        
        # グラフの更新
        fig2.update_layout(
            title="レグ別速度・VMG比較",
            height=350,
            barmode='group',
            xaxis_title="レグ番号",
            yaxis_title="速度 (ノット)"
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # レグ分析のサマリー
    st.markdown("#### レグ分析サマリー")
    
    # 3列で統計情報を表示
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("最速レグ", "レグ4 (リーチ)", delta="+1.1 kt")
    
    with summary_col2:
        st.metric("最高VMG", "レグ4 (リーチ)", delta="+1.7 kt")
    
    with summary_col3:
        st.metric("風向変化最大", "レグ1 (風上)", delta="12°")


def render_maneuver_analysis(data):
    """
    マニューバー分析を表示
    
    Parameters
    ----------
    data : dict
        分析用データ
    """
    st.markdown("### マニューバー（タック・ジャイブ）分析")
    
    # マニューバーデータのサンプル
    maneuver_data = pd.DataFrame({
        "ID": [1, 2, 3, 4, 5, 6, 7, 8],
        "タイプ": ["タック", "タック", "ジャイブ", "タック", "ジャイブ", "タック", "タック", "ジャイブ"],
        "時刻": ["13:05:23", "13:18:45", "13:32:12", "13:47:30", "14:02:15", "14:15:40", "14:28:55", "14:42:20"],
        "所要時間(秒)": [8.2, 7.5, 12.1, 8.4, 11.8, 7.2, 9.3, 13.0],
        "速度損失(kt)": [1.2, 0.9, 1.5, 1.1, 1.4, 0.8, 1.3, 1.7],
        "角度変化(度)": [85, 88, 95, 87, 92, 90, 86, 93]
    })
    
    # マニューバーデータのテーブル表示
    st.dataframe(maneuver_data, use_container_width=True)
    
    # グラフ表示
    col1, col2 = st.columns(2)
    
    with col1:
        # マニューバー所要時間グラフ
        fig1 = px.box(
            maneuver_data,
            x="タイプ",
            y="所要時間(秒)",
            color="タイプ",
            points="all",
            title="マニューバー種類別所要時間"
        )
        
        # レイアウト調整
        fig1.update_layout(
            height=350,
            xaxis_title="マニューバータイプ",
            yaxis_title="所要時間 (秒)"
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # マニューバー効率散布図
        fig2 = px.scatter(
            maneuver_data,
            x="所要時間(秒)",
            y="速度損失(kt)",
            color="タイプ",
            size="角度変化(度)",
            hover_data=["ID", "時刻"],
            title="マニューバー効率分析"
        )
        
        # レイアウト調整
        fig2.update_layout(
            height=350,
            xaxis_title="所要時間 (秒)",
            yaxis_title="速度損失 (ノット)"
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # マニューバー分析のサマリー
    st.markdown("#### マニューバー分析サマリー")
    
    # マニューバータイプごとの平均値を計算
    tack_data = maneuver_data[maneuver_data["タイプ"] == "タック"]
    jibe_data = maneuver_data[maneuver_data["タイプ"] == "ジャイブ"]
    
    tack_time = tack_data["所要時間(秒)"].mean()
    jibe_time = jibe_data["所要時間(秒)"].mean()
    
    tack_loss = tack_data["速度損失(kt)"].mean()
    jibe_loss = jibe_data["速度損失(kt)"].mean()
    
    # 3列で統計情報を表示
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("平均タック時間", f"{tack_time:.1f} 秒")
    
    with summary_col2:
        st.metric("平均ジャイブ時間", f"{jibe_time:.1f} 秒")
    
    with summary_col3:
        st.metric("最適マニューバー", "タック #6", delta="-0.4 秒")


def render_wind_shift_analysis(data):
    """
    風向変化分析を表示
    
    Parameters
    ----------
    data : dict
        分析用データ
    """
    st.markdown("### 風向変化分析")
    
    # 風向変化データのサンプル
    shift_data = pd.DataFrame({
        "ID": [1, 2, 3, 4, 5],
        "時刻": ["13:10:15", "13:25:40", "13:52:30", "14:15:20", "14:38:45"],
        "変化量(度)": [12, -8, 15, -10, 7],
        "変化速度(度/分)": [2.4, 1.6, 3.0, 2.0, 1.4],
        "持続時間(分)": [5, 3, 8, 4, 6],
        "対応": ["タック", "様子見", "コース調整", "タック", "様子見"]
    })
    
    # 符号に基づいて方向列を追加
    shift_data["方向"] = shift_data["変化量(度)"].apply(lambda x: "右シフト" if x > 0 else "左シフト")
    
    # 風向変化データのテーブル表示
    st.dataframe(shift_data, use_container_width=True)
    
    # グラフ表示
    col1, col2 = st.columns(2)
    
    with col1:
        # 風向変化量グラフ
        fig1 = px.bar(
            shift_data,
            x="ID",
            y="変化量(度)",
            color="方向",
            text="変化量(度)",
            title="風向シフト分析"
        )
        
        # テキスト表示の書式設定
        fig1.update_traces(
            texttemplate='%{text:.0f}°',
            textposition='outside'
        )
        
        # レイアウト調整
        fig1.update_layout(
            height=350,
            xaxis_title="シフトID",
            yaxis_title="変化量 (度)"
        )
        
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # 風向変化の散布図
        fig2 = px.scatter(
            shift_data,
            x="持続時間(分)",
            y="変化速度(度/分)",
            color="方向",
            size=abs(shift_data["変化量(度)"]),
            hover_data=["ID", "時刻", "対応"],
            title="風向シフト特性"
        )
        
        # レイアウト調整
        fig2.update_layout(
            height=350,
            xaxis_title="持続時間 (分)",
            yaxis_title="変化速度 (度/分)"
        )
        
        st.plotly_chart(fig2, use_container_width=True)
    
    # 風向変化分析のサマリー
    st.markdown("#### 風向変化サマリー")
    
    # 風向変化の統計
    right_shifts = shift_data[shift_data["変化量(度)"] > 0]
    left_shifts = shift_data[shift_data["変化量(度)"] < 0]
    
    avg_right = right_shifts["変化量(度)"].mean() if not right_shifts.empty else 0
    avg_left = abs(left_shifts["変化量(度)"].mean()) if not left_shifts.empty else 0
    
    # 3列で統計情報を表示
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("平均右シフト", f"{avg_right:.1f}°")
    
    with summary_col2:
        st.metric("平均左シフト", f"{avg_left:.1f}°")
    
    with summary_col3:
        # 風のパターン判定（単純な例）
        if len(right_shifts) > len(left_shifts):
            pattern = "右回りトレンド"
        elif len(right_shifts) < len(left_shifts):
            pattern = "左回りトレンド"
        else:
            pattern = "振動パターン"
            
        st.metric("風パターン", pattern)
    
    # パターン解説
    st.markdown(f"""
    **パターン分析**: {pattern}

    このセッションでは、風向の変化に{pattern}が見られます。
    右シフトが{len(right_shifts)}回、左シフトが{len(left_shifts)}回発生しています。
    最大の風向変化は{shift_data['変化量(度)'].abs().max()}度で、ID {shift_data.loc[shift_data['変化量(度)'].abs().idxmax(), 'ID']}のシフトで発生しました。
    """)


def generate_sample_data():
    """
    テスト用のサンプルデータを生成する関数
    
    Returns
    -------
    dict
        タイムライン表示用のデータ辞書
    """
    # 時間の設定
    start_time = datetime.now() - timedelta(hours=2)
    times = pd.date_range(start=start_time, periods=100, freq="1min")
    
    # 時系列データ
    time_series = pd.DataFrame({
        "timestamp": times,
        "船速": np.random.normal(6, 1, len(times)) + np.sin(np.linspace(0, 8, len(times))),
        "風速": np.random.normal(12, 2, len(times)) + np.sin(np.linspace(0, 4, len(times))),
        "風向": np.cumsum(np.random.normal(0, 1, len(times))) % 360 + 180,
        "ヒール角": np.random.normal(15, 5, len(times)) + np.sin(np.linspace(0, 6, len(times))) * 2,
        "VMG": np.random.normal(3, 1.5, len(times)) + np.sin(np.linspace(0, 6, len(times))) * 0.8
    })
    
    # イベントデータの生成
    events_data = []
    
    # タックイベント
    for i in range(5):
        idx = 10 + i * 20  # 均等に配置
        events_data.append({
            "timestamp": times[idx],
            "type": "タック",
            "description": f"タック #{i+1} - 風向シフトに対応"
        })
    
    # ジャイブイベント
    for i in range(3):
        idx = 15 + i * 30  # 均等に配置
        events_data.append({
            "timestamp": times[idx],
            "type": "ジャイブ",
            "description": f"ジャイブ #{i+1} - 風下への方向転換"
        })
    
    # マークイベント
    marks = ["スタート", "風上マーク1", "風下マーク", "風上マーク2", "フィニッシュ"]
    for i, mark in enumerate(marks):
        idx = 5 + i * 20  # 均等に配置
        events_data.append({
            "timestamp": times[idx],
            "type": "マーク",
            "description": f"{mark}通過"
        })
    
    # 風向シフトイベント
    for i in range(4):
        idx = 8 + i * 25  # 均等に配置
        direction = "右" if i % 2 == 0 else "左"
        amount = np.random.randint(8, 20)
        events_data.append({
            "timestamp": times[idx],
            "type": "風向シフト",
            "description": f"{direction}に{amount}°シフト"
        })
    
    # 戦略判断イベント
    strategies = [
        "風上へのレイヤー選択",
        "他艇との交差判断",
        "プレスアップ戦術",
        "風の変化に備えた位置取り"
    ]
    for i, strategy in enumerate(strategies):
        idx = 12 + i * 22  # 均等に配置
        events_data.append({
            "timestamp": times[idx],
            "type": "戦略判断",
            "description": strategy
        })
    
    # DataFrameに変換
    events = pd.DataFrame(events_data)
    
    return {
        "time_series": time_series,
        "events": events
    }


if __name__ == "__main__":
    render_page()
