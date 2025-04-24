# -*- coding: utf-8 -*-
"""
戦略検出モジュールページ

このモジュールは戦略的判断ポイントの検出と表示を行うためのStreamlitページを提供します。
風のシフト、タックポイント、レイラインなどの重要な戦略判断ポイントを検出・可視化します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional

from sailing_data_processor.analysis.analysis_parameters import ParametersManager, ParameterNamespace
from sailing_data_processor.analysis.integrated_strategy_detector import IntegratedStrategyDetector
from sailing_data_processor.analysis.integrated_wind_estimator import IntegratedWindEstimator
from sailing_data_processor.analysis.analysis_cache import AnalysisCache
from ui.components.workflow_components import parameter_adjustment_panel
from ui.integrated.controllers.workflow_controller import IntegratedWorkflowController


# ロガーの設定
logger = logging.getLogger(__name__)


def display_strategy_points_map(df: pd.DataFrame, strategy_points: List[Dict[str, Any]]) -> None:
    """
    戦略ポイントを地図上に表示
    
    Parameters:
    -----------
    df : pd.DataFrame
        GPSデータを含むデータフレーム
    strategy_points : List[Dict[str, Any]]
        検出された戦略ポイントのリスト
    """
    if df is None or df.empty:
        st.warning("GPSデータがありません。")
        return
    
    if not strategy_points:
        st.info("表示する戦略ポイントがありません。")
        return
    
    # 中心位置の計算
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()
    
    # 地図の作成
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
    
    # GPSトラックの描画
    track_coords = [[row["latitude"], row["longitude"]] for _, row in df.iterrows()]
    folium.PolyLine(
        track_coords,
        color="blue",
        weight=3,
        opacity=0.7,
        tooltip="航路"
    ).add_to(m)
    
    # 開始点と終了点のマーカー
    folium.Marker(
        [df["latitude"].iloc[0], df["longitude"].iloc[0]],
        popup="開始",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(m)
    
    folium.Marker(
        [df["latitude"].iloc[-1], df["longitude"].iloc[-1]],
        popup="終了",
        icon=folium.Icon(color="red", icon="stop")
    ).add_to(m)
    
    # 戦略ポイント用のマーカークラスタ
    marker_cluster = MarkerCluster().add_to(m)
    
    # 戦略ポイントの追加
    for point in strategy_points:
        # 位置情報の確認
        lat = point.get("latitude")
        lon = point.get("longitude")
        
        if lat is None or lon is None:
            continue
        
        # ポイントのタイプと重要度
        point_type = point.get("type", "Unknown")
        score = point.get("strategic_score", 0)
        
        # タイプに応じたアイコン設定
        icon_settings = {
            "WindShiftPoint": {
                "color": "red",
                "icon": "arrows",
                "prefix": "fa"
            },
            "TackPoint": {
                "color": "green",
                "icon": "exchange",
                "prefix": "fa"
            },
            "LaylinePoint": {
                "color": "orange",
                "icon": "anchor",
                "prefix": "fa"
            },
            "MarkRoundingPoint": {
                "color": "blue",
                "icon": "flag",
                "prefix": "fa"
            }
        }
        
        # デフォルト設定
        settings = icon_settings.get(point_type, {
            "color": "purple",
            "icon": "question",
            "prefix": "fa"
        })
        
        # ポップアップテキストの作成
        popup_text = f"<strong>{point_type}</strong> (重要度: {score:.2f})<br>"
        
        # タイプ別の詳細情報
        if point_type == "WindShiftPoint":
            popup_text += f"シフト角度: {point.get('shift_angle', 0):.1f}°<br>"
            popup_text += f"シフト前風向: {point.get('before_direction', 0):.1f}°<br>"
            popup_text += f"シフト後風向: {point.get('after_direction', 0):.1f}°<br>"
            popup_text += f"風速: {point.get('wind_speed', 0):.1f}ノット<br>"
        
        elif point_type == "TackPoint":
            popup_text += f"タックタイプ: {point.get('tack_type', '不明')}<br>"
            popup_text += f"推奨タック: {point.get('suggested_tack', '不明')}<br>"
            popup_text += f"VMG改善: {point.get('vmg_gain', 0):.3f}<br>"
        
        elif point_type == "LaylinePoint":
            popup_text += f"マークID: {point.get('mark_id', '不明')}<br>"
            popup_text += f"マークまでの距離: {point.get('distance_to_mark', 0):.1f}m<br>"
            popup_text += f"進入角度: {point.get('approach_angle', 0):.1f}°<br>"
        
        # タイムスタンプがあれば追加
        if "timestamp" in point:
            timestamp = point["timestamp"]
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except ValueError:
                    pass
            
            if isinstance(timestamp, datetime):
                popup_text += f"時間: {timestamp.strftime('%H:%M:%S')}<br>"
        
        # メモが設定されていれば追加
        if "note" in point and point["note"]:
            popup_text += f"メモ: {point['note']}"
        
        # マーカーの追加
        folium.Marker(
            [lat, lon],
            popup=folium.Popup(popup_text, max_width=200),
            icon=folium.Icon(
                color=settings["color"],
                icon=settings["icon"],
                prefix=settings["prefix"]
            )
        ).add_to(marker_cluster)
    
    # 地図の表示
    folium_static(m)


def display_strategy_points_timeline(strategy_points: List[Dict[str, Any]]) -> None:
    """
    戦略ポイントのタイムライン表示
    
    Parameters:
    -----------
    strategy_points : List[Dict[str, Any]]
        検出された戦略ポイントのリスト
    """
    if not strategy_points:
        st.info("表示する戦略ポイントがありません。")
        return
    
    # タイムスタンプがあるポイントのみ抽出
    time_points = []
    for point in strategy_points:
        if "timestamp" in point:
            timestamp = point["timestamp"]
            # タイムスタンプが文字列の場合は変換
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                    point_copy = point.copy()
                    point_copy["timestamp"] = timestamp
                    time_points.append(point_copy)
                except ValueError:
                    continue
            else:
                time_points.append(point)
    
    if not time_points:
        st.info("時間情報のある戦略ポイントがありません。")
        return
    
    # タイプごとに色を設定
    color_map = {
        "WindShiftPoint": "red",
        "TackPoint": "green",
        "LaylinePoint": "orange",
        "MarkRoundingPoint": "blue"
    }
    
    # タイプごとにポイントを分類
    point_types = list(set(point.get("type", "Unknown") for point in time_points))
    
    # タイムラインの作成
    fig = go.Figure()
    
    for point_type in point_types:
        # タイプごとのポイントを抽出
        type_points = [p for p in time_points if p.get("type") == point_type]
        
        # タイプごとに表示名を設定
        display_names = {
            "WindShiftPoint": "風向シフト",
            "TackPoint": "タックポイント",
            "Laylinepoint": "レイライン",
            "MarkRoundingPoint": "マーク回航"
        }
        
        display_name = display_names.get(point_type, point_type)
        
        # タイムラインにポイントを追加
        fig.add_trace(go.Scatter(
            x=[p["timestamp"] for p in type_points],
            y=[p.get("strategic_score", 0) for p in type_points],
            mode="markers",
            name=display_name,
            marker=dict(
                size=[max(5, min(20, p.get("strategic_score", 0) * 10)) for p in type_points],
                color=color_map.get(point_type, "purple"),
                opacity=0.7
            ),
            text=[f"{p.get('type')}: {p.get('strategic_score', 0):.2f}" for p in type_points],
            hovertemplate="時間: %{x}<br>重要度: %{y:.2f}<br>%{text}<extra></extra>"
        ))
    
    # グラフのレイアウト設定
    fig.update_layout(
        title="戦略ポイントのタイムライン",
        xaxis_title="時間",
        yaxis_title="戦略的重要度",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="closest"
    )
    
    # グラフの表示
    st.plotly_chart(fig, use_container_width=True)


def display_wind_shifts(wind_shifts: List[Dict[str, Any]]) -> None:
    """
    風向シフトの詳細表示
    
    Parameters:
    -----------
    wind_shifts : List[Dict[str, Any]]
        検出された風向シフトのリスト
    """
    if not wind_shifts:
        st.info("検出された風向シフトはありません。")
        return
    
    st.subheader(f"検出された風向シフト ({len(wind_shifts)}件)")
    
    # シフトデータをDataFrameに変換
    shifts_df = pd.DataFrame(wind_shifts)
    
    # 表示用に列を選択・整形
    display_columns = [
        "timestamp", "shift_angle", "before_direction", "after_direction", 
        "wind_speed", "duration_seconds", "strategic_score"
    ]
    
    # 存在する列のみ選択
    display_columns = [col for col in display_columns if col in shifts_df.columns]
    
    if display_columns:
        # 表示用のDataFrame作成
        display_df = shifts_df[display_columns].copy()
        
        # 列名の日本語化
        column_labels = {
            "timestamp": "時間",
            "shift_angle": "シフト角度(°)",
            "before_direction": "シフト前風向(°)",
            "after_direction": "シフト後風向(°)",
            "wind_speed": "風速(ノット)",
            "duration_seconds": "持続時間(秒)",
            "strategic_score": "重要度"
        }
        
        display_df.columns = [column_labels.get(col, col) for col in display_df.columns]
        
        # タイムスタンプのフォーマット
        if "時間" in display_df.columns and pd.api.types.is_datetime64_any_dtype(display_df["時間"]):
            display_df["時間"] = display_df["時間"].dt.strftime("%H:%M:%S")
        
        # 数値のフォーマット（小数点以下1桁）
        for col in ["シフト角度(°)", "シフト前風向(°)", "シフト後風向(°)", "風速(ノット)"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
        
        # 重要度のフォーマット（小数点以下2桁）
        if "重要度" in display_df.columns:
            display_df["重要度"] = display_df["重要度"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
        
        # DataFrameの表示
        st.dataframe(display_df)
        
        # シフト方向の分析
        if "shift_angle" in shifts_df.columns:
            st.subheader("シフト方向の分析")
            
            # 左右シフトの分類
            left_shifts = shifts_df[shifts_df["shift_angle"] < 0]
            right_shifts = shifts_df[shifts_df["shift_angle"] > 0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("左シフト（反時計回り）", f"{len(left_shifts)}件")
                if len(left_shifts) > 0:
                    st.metric("平均左シフト角度", f"{left_shifts['shift_angle'].mean():.1f}°")
            
            with col2:
                st.metric("右シフト（時計回り）", f"{len(right_shifts)}件")
                if len(right_shifts) > 0:
                    st.metric("平均右シフト角度", f"{right_shifts['shift_angle'].mean():.1f}°")
            
            with col3:
                st.metric("総シフト数", f"{len(shifts_df)}件")
                st.metric("平均シフト角度", f"{shifts_df['shift_angle'].abs().mean():.1f}°")
            
            # シフト角度の分布
            fig, ax = plt.subplots(figsize=(10, 6))
            bins = np.arange(-40, 41, 5)  # -40°から40°まで5°刻み
            
            ax.hist(shifts_df["shift_angle"], bins=bins, alpha=0.7, color="skyblue", edgecolor="black")
            ax.set_title("風向シフト角度の分布")
            ax.set_xlabel("シフト角度 (°)")
            ax.set_ylabel("頻度")
            ax.axvline(x=0, color="red", linestyle="--")
            ax.grid(True, alpha=0.3)
            
            st.pyplot(fig)
    
    else:
        st.warning("表示可能なデータが見つかりません。")


def display_tack_points(tack_points: List[Dict[str, Any]]) -> None:
    """
    タックポイントの詳細表示
    
    Parameters:
    -----------
    tack_points : List[Dict[str, Any]]
        検出されたタックポイントのリスト
    """
    if not tack_points:
        st.info("検出されたタックポイントはありません。")
        return
    
    st.subheader(f"検出されたタックポイント ({len(tack_points)}件)")
    
    # タックデータをDataFrameに変換
    tacks_df = pd.DataFrame(tack_points)
    
    # 表示用に列を選択・整形
    display_columns = [
        "timestamp", "tack_type", "suggested_tack", "vmg_gain", 
        "heading_before", "heading_after", "strategic_score"
    ]
    
    # 存在する列のみ選択
    display_columns = [col for col in display_columns if col in tacks_df.columns]
    
    if display_columns:
        # 表示用のDataFrame作成
        display_df = tacks_df[display_columns].copy()
        
        # 列名の日本語化
        column_labels = {
            "timestamp": "時間",
            "tack_type": "タックタイプ",
            "suggested_tack": "推奨タック",
            "vmg_gain": "VMG改善率",
            "heading_before": "タック前進路(°)",
            "heading_after": "タック後進路(°)",
            "strategic_score": "重要度"
        }
        
        display_df.columns = [column_labels.get(col, col) for col in display_df.columns]
        
        # タイムスタンプのフォーマット
        if "時間" in display_df.columns and pd.api.types.is_datetime64_any_dtype(display_df["時間"]):
            display_df["時間"] = display_df["時間"].dt.strftime("%H:%M:%S")
        
        # タイプの翻訳
        if "タックタイプ" in display_df.columns:
            type_map = {
                "port_to_starboard": "ポート→スターボード",
                "starboard_to_port": "スターボード→ポート",
                "unknown": "不明"
            }
            display_df["タックタイプ"] = display_df["タックタイプ"].map(lambda x: type_map.get(x, x))
        
        # 推奨タックの翻訳
        if "推奨タック" in display_df.columns:
            suggest_map = {
                "port": "ポート",
                "starboard": "スターボード",
                "none": "なし"
            }
            display_df["推奨タック"] = display_df["推奨タック"].map(lambda x: suggest_map.get(x, x))
        
        # VMG改善率のフォーマット
        if "VMG改善率" in display_df.columns:
            display_df["VMG改善率"] = display_df["VMG改善率"].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "-")
        
        # 進路のフォーマット
        for col in ["タック前進路(°)", "タック後進路(°)"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
        
        # 重要度のフォーマット
        if "重要度" in display_df.columns:
            display_df["重要度"] = display_df["重要度"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
        
        # DataFrameの表示
        st.dataframe(display_df)
        
        # タックの分析
        st.subheader("タック分析")
        
        if "tack_type" in tacks_df.columns:
            # タイプ別の集計
            tack_types = tacks_df["tack_type"].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # タイプ別の数
                port_to_starboard = tack_types.get("port_to_starboard", 0)
                st.metric("ポート→スターボード", f"{port_to_starboard}件")
                
                starboard_to_port = tack_types.get("starboard_to_port", 0)
                st.metric("スターボード→ポート", f"{starboard_to_port}件")
            
            with col2:
                # VMG改善の平均
                if "vmg_gain" in tacks_df.columns:
                    avg_vmg_gain = tacks_df["vmg_gain"].mean()
                    st.metric("平均VMG改善率", f"{avg_vmg_gain*100:.1f}%")
                
                # 重要度の平均
                if "strategic_score" in tacks_df.columns:
                    avg_score = tacks_df["strategic_score"].mean()
                    st.metric("平均重要度", f"{avg_score:.2f}")
            
            # タイプ別のグラフ
            fig, ax = plt.subplots(figsize=(8, 5))
            
            tack_labels = {
                "port_to_starboard": "ポート→スターボード",
                "starboard_to_port": "スターボード→ポート",
                "unknown": "不明"
            }
            
            # タイプ名を変換
            tack_counts = {tack_labels.get(k, k): v for k, v in tack_types.items()}
            
            # 円グラフの作成
            ax.pie(
                tack_counts.values(),
                labels=tack_counts.keys(),
                autopct='%1.1f%%',
                startangle=90,
                shadow=False,
                colors=['lightgreen', 'skyblue', 'lightgray']
            )
            ax.axis('equal')
            ax.set_title("タックタイプの分布")
            
            st.pyplot(fig)
    
    else:
        st.warning("表示可能なデータが見つかりません。")


def display_layline_points(layline_points: List[Dict[str, Any]]) -> None:
    """
    レイラインポイントの詳細表示
    
    Parameters:
    -----------
    layline_points : List[Dict[str, Any]]
        検出されたレイラインポイントのリスト
    """
    if not layline_points:
        st.info("検出されたレイラインポイントはありません。")
        return
    
    st.subheader(f"検出されたレイラインポイント ({len(layline_points)}件)")
    
    # レイラインデータをDataFrameに変換
    laylines_df = pd.DataFrame(layline_points)
    
    # 表示用に列を選択・整形
    display_columns = [
        "timestamp", "mark_id", "distance_to_mark", "approach_angle", 
        "optimal_angle", "angle_difference", "strategic_score"
    ]
    
    # 存在する列のみ選択
    display_columns = [col for col in display_columns if col in laylines_df.columns]
    
    if display_columns:
        # 表示用のDataFrame作成
        display_df = laylines_df[display_columns].copy()
        
        # 列名の日本語化
        column_labels = {
            "timestamp": "時間",
            "mark_id": "マークID",
            "distance_to_mark": "マークまでの距離(m)",
            "approach_angle": "進入角度(°)",
            "optimal_angle": "最適角度(°)",
            "angle_difference": "角度差(°)",
            "strategic_score": "重要度"
        }
        
        display_df.columns = [column_labels.get(col, col) for col in display_df.columns]
        
        # タイムスタンプのフォーマット
        if "時間" in display_df.columns and pd.api.types.is_datetime64_any_dtype(display_df["時間"]):
            display_df["時間"] = display_df["時間"].dt.strftime("%H:%M:%S")
        
        # 数値のフォーマット
        for col in ["マークまでの距離(m)"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
        
        # 角度のフォーマット
        for col in ["進入角度(°)", "最適角度(°)", "角度差(°)"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
        
        # 重要度のフォーマット
        if "重要度" in display_df.columns:
            display_df["重要度"] = display_df["重要度"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
        
        # DataFrameの表示
        st.dataframe(display_df)
        
        # レイラインの分析
        st.subheader("レイライン分析")
        
        if "mark_id" in laylines_df.columns:
            # マーク別の集計
            mark_counts = laylines_df["mark_id"].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # マーク数
                st.metric("検出されたマーク数", f"{len(mark_counts)}個")
                
                # 検出数が最も多いマーク
                if len(mark_counts) > 0:
                    max_mark = mark_counts.idxmax()
                    st.metric("最も多く検出されたマーク", f"{max_mark} ({mark_counts[max_mark]}件)")
            
            with col2:
                # 平均距離
                if "distance_to_mark" in laylines_df.columns:
                    avg_distance = laylines_df["distance_to_mark"].mean()
                    st.metric("平均マーク距離", f"{avg_distance:.1f}m")
                
                # 平均重要度
                if "strategic_score" in laylines_df.columns:
                    avg_score = laylines_df["strategic_score"].mean()
                    st.metric("平均重要度", f"{avg_score:.2f}")
            
            # マーク別の分布グラフ
            if len(mark_counts) > 0:
                fig, ax = plt.subplots(figsize=(10, 6))
                
                # マーク別の検出数グラフ
                mark_counts.plot(kind="bar", ax=ax, color="skyblue")
                ax.set_title("マーク別のレイライン検出数")
                ax.set_xlabel("マークID")
                ax.set_ylabel("検出数")
                ax.grid(True, alpha=0.3, axis="y")
                
                for i, v in enumerate(mark_counts):
                    ax.text(i, v + 0.1, str(v), ha='center')
                
                st.pyplot(fig)
    
    else:
        st.warning("表示可能なデータが見つかりません。")


def detect_strategy_from_df(df: pd.DataFrame, params_manager: ParametersManager) -> Dict[str, Any]:
    """
    データフレームから戦略ポイントを検出
    
    Parameters:
    -----------
    df : pd.DataFrame
        GPSデータを含むデータフレーム
    params_manager : ParametersManager
        パラメータ管理オブジェクト
        
    Returns:
    --------
    Dict[str, Any]
        戦略検出結果
    """
    # 必須カラムの確認
    required_cols = ["timestamp", "latitude", "longitude", "course", "speed"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        return {
            "error": f"データに必須カラムがありません: {', '.join(missing_cols)}",
            "all_points": [],
            "wind_shifts": [],
            "tack_points": [],
            "layline_points": []
        }
    
    try:
        # キャッシュとモジュールのインスタンス化
        cache = AnalysisCache()
        wind_estimator = IntegratedWindEstimator(params_manager, cache)
        strategy_detector = IntegratedStrategyDetector(params_manager, cache, wind_estimator)
        
        # 戦略ポイントの検出
        result = strategy_detector.detect_strategy_points(df)
        
        return result
    except Exception as e:
        logger.exception(f"戦略検出中にエラーが発生しました: {str(e)}")
        return {
            "error": f"戦略検出エラー: {str(e)}",
            "all_points": [],
            "wind_shifts": [],
            "tack_points": [],
            "layline_points": []
        }


def strategy_detection_page() -> None:
    """
    戦略検出ページのメインエントリーポイント
    """
    st.title("戦略ポイント検出")
    
    # セッションデータの取得
    session_data = st.session_state.get('session_data', {})
    
    # 選択されたセッションの情報表示
    current_session = session_data.get('current_session')
    
    if current_session and 'current_session_df' in session_data:
        st.subheader(f"セッション: {current_session.get('name', '名称未設定')}")
        
        # パラメータマネージャーの取得または作成
        params_manager = session_data.get('params_manager')
        if params_manager is None:
            params_manager = ParametersManager()
            session_data['params_manager'] = params_manager
        
        # データフレームの取得
        df = session_data['current_session_df']
        
        if df is None or df.empty:
            st.warning("データが選択されていないか、空です。")
            return
        
        # パラメータ調整と戦略検出
        with st.expander("戦略検出パラメータ", expanded=False):
            st.write("戦略ポイントを検出するためのパラメータを調整できます。")
            
            # パラメータ調整パネル
            strategy_params = parameter_adjustment_panel(
                params_manager, 
                ParameterNamespace.STRATEGY_DETECTION
            )
        
        # 戦略検出実行ボタン
        col1, col2 = st.columns([1, 1])
        
        with col1:
            detect_button = st.button("戦略ポイントを検出", key="detect_strategy", use_container_width=True)
        
        with col2:
            # ワークフローから結果を取得するオプション
            if 'workflow_controller' in st.session_state:
                workflow_button = st.button(
                    "ワークフローから結果を取得", 
                    key="get_from_workflow",
                    use_container_width=True
                )
            else:
                workflow_button = False
                st.info("ワークフローの結果を使用するには、最初にワークフローページで分析を実行してください。")
        
        # 戦略検出結果のキャッシュ
        if 'strategy_result' not in st.session_state:
            st.session_state.strategy_result = None
        
        # 戦略検出の実行
        if detect_button:
            with st.spinner("戦略ポイントを検出中..."):
                strategy_result = detect_strategy_from_df(df, params_manager)
                st.session_state.strategy_result = strategy_result
                
                # 成功メッセージまたはエラーメッセージ
                if "error" in strategy_result:
                    st.error(strategy_result["error"])
                else:
                    all_points = strategy_result.get("all_points", [])
                    wind_shifts = strategy_result.get("wind_shifts", [])
                    tack_points = strategy_result.get("tack_points", [])
                    layline_points = strategy_result.get("layline_points", [])
                    
                    st.success(
                        f"戦略ポイントの検出が完了しました。"
                        f"合計: {len(all_points)}件 "
                        f"(風向シフト: {len(wind_shifts)}件, "
                        f"タックポイント: {len(tack_points)}件, "
                        f"レイライン: {len(layline_points)}件)"
                    )
        
        # ワークフローからの結果取得
        elif workflow_button:
            if 'workflow_controller' in st.session_state:
                workflow_controller = st.session_state.workflow_controller
                
                # 結果の取得
                results = workflow_controller.get_results()
                
                if "strategy_result" in results:
                    st.session_state.strategy_result = results["strategy_result"]
                    
                    # 成功メッセージ
                    result = results["strategy_result"]
                    all_points = result.get("all_points", [])
                    wind_shifts = result.get("wind_shifts", [])
                    tack_points = result.get("tack_points", [])
                    layline_points = result.get("layline_points", [])
                    
                    st.success(
                        f"ワークフローから戦略ポイントを取得しました。"
                        f"合計: {len(all_points)}件 "
                        f"(風向シフト: {len(wind_shifts)}件, "
                        f"タックポイント: {len(tack_points)}件, "
                        f"レイライン: {len(layline_points)}件)"
                    )
                else:
                    st.warning("ワークフローに戦略検出結果が見つかりません。ワークフローを実行してください。")
        
        # 結果の表示
        strategy_result = st.session_state.strategy_result
        
        if strategy_result:
            # 結果を複数のセクションに分けて表示
            tabs = st.tabs(["概要", "地図", "タイムライン", "風向シフト", "タックポイント", "レイライン"])
            
            all_points = strategy_result.get("all_points", [])
            wind_shifts = strategy_result.get("wind_shifts", [])
            tack_points = strategy_result.get("tack_points", [])
            layline_points = strategy_result.get("layline_points", [])
            
            # 概要タブ
            with tabs[0]:
                st.subheader("戦略ポイント検出概要")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("検出ポイント合計", len(all_points))
                
                with col2:
                    st.metric("風向シフト", len(wind_shifts))
                
                with col3:
                    st.metric("タックポイント", len(tack_points))
                
                with col4:
                    st.metric("レイライン", len(layline_points))
                
                # 重要ポイントの表示
                if all_points:
                    st.subheader("重要な戦略ポイント")
                    
                    # 重要度でソート
                    important_points = sorted(
                        all_points, 
                        key=lambda p: p.get("strategic_score", 0), 
                        reverse=True
                    )[:5]  # 上位5件
                    
                    for i, point in enumerate(important_points):
                        point_type = point.get("type", "Unknown")
                        score = point.get("strategic_score", 0)
                        
                        with st.expander(
                            f"{i+1}. {point_type} (重要度: {score:.2f})",
                            expanded=i == 0  # 最初のポイントは展開
                        ):
                            # ポイントの詳細表示
                            if point_type == "WindShiftPoint":
                                st.write(f"シフト角度: {point.get('shift_angle', 0):.1f}°")
                                st.write(f"シフト前風向: {point.get('before_direction', 0):.1f}°")
                                st.write(f"シフト後風向: {point.get('after_direction', 0):.1f}°")
                                st.write(f"風速: {point.get('wind_speed', 0):.1f}ノット")
                            
                            elif point_type == "TackPoint":
                                st.write(f"タックタイプ: {point.get('tack_type', '不明')}")
                                st.write(f"推奨タック: {point.get('suggested_tack', '不明')}")
                                st.write(f"VMG改善: {point.get('vmg_gain', 0):.3f}")
                            
                            elif point_type == "LaylinePoint":
                                st.write(f"マークID: {point.get('mark_id', '不明')}")
                                st.write(f"マークまでの距離: {point.get('distance_to_mark', 0):.1f}m")
                                st.write(f"進入角度: {point.get('approach_angle', 0):.1f}°")
                            
                            # 共通情報
                            st.write(f"メモ: {point.get('note', '情報なし')}")
                            
                            # 位置情報があれば表示
                            lat = point.get("latitude")
                            lon = point.get("longitude")
                            if lat and lon:
                                st.write(f"位置: {lat:.6f}, {lon:.6f}")
                                
                                # 小さな地図表示
                                m = folium.Map(location=[lat, lon], zoom_start=15, width=400, height=300)
                                folium.Marker([lat, lon]).add_to(m)
                                folium_static(m)
            
            # 地図タブ
            with tabs[1]:
                display_strategy_points_map(df, all_points)
            
            # タイムラインタブ
            with tabs[2]:
                display_strategy_points_timeline(all_points)
            
            # 風向シフトタブ
            with tabs[3]:
                display_wind_shifts(wind_shifts)
            
            # タックポイントタブ
            with tabs[4]:
                display_tack_points(tack_points)
            
            # レイラインタブ
            with tabs[5]:
                display_layline_points(layline_points)
        
        else:
            # 戦略検出の説明
            st.info("""
            「戦略ポイントを検出」ボタンをクリックして、GPSデータから重要な戦略判断ポイントを検出します。
            
            このモジュールでは、以下のような重要な戦略ポイントを検出します：
            
            1. **風向シフト**: 風向の変化を検出し、それがレース戦略に与える影響を評価します
            2. **タックポイント**: 最適なタックのタイミングと位置を特定します
            3. **レイライン**: マークへのアプローチ時にレイラインに到達するポイントを検出します
            
            検出されたポイントは地図上やタイムラインで表示され、重要度に基づいてランク付けされます。
            """)
    
    else:
        st.info("戦略ポイントを検出するには、まずプロジェクトからセッションを選択してください。")


if __name__ == "__main__":
    strategy_detection_page()
