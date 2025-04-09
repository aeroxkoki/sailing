"""
パフォーマンス分析モジュールページ

このモジュールはセーリングパフォーマンスの分析と表示を行うためのStreamlitページを提供します。
VMG分析、タック効率、ジャイブ効率などのパフォーマンス指標を計算・可視化します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional

from sailing_data_processor.analysis.analysis_parameters import ParametersManager, ParameterNamespace
from sailing_data_processor.analysis.integrated_performance_analyzer import IntegratedPerformanceAnalyzer
from sailing_data_processor.analysis.integrated_wind_estimator import IntegratedWindEstimator
from sailing_data_processor.analysis.analysis_cache import AnalysisCache
from ui.components.workflow_components import parameter_adjustment_panel
from ui.integrated.controllers.workflow_controller import IntegratedWorkflowController


# ロガーの設定
logger = logging.getLogger(__name__)


def display_performance_overview(performance_data: Dict[str, Any]) -> None:
    """
    パフォーマンス概要の表示
    
    Parameters:
    -----------
    performance_data : Dict[str, Any]
        パフォーマンス分析データ
    """
    if not performance_data:
        st.warning("パフォーマンスデータがありません。")
        return
    
    # 総合評価の取得
    overall = performance_data.get("overall_performance", {})
    
    if not overall:
        st.warning("総合パフォーマンス評価データがありません。")
        return
    
    # スコアと評価の表示
    score = overall.get("score", 0)
    rating = overall.get("rating", "評価なし")
    
    # スコアに応じた色の設定
    if score >= 80:
        score_color = "green"
    elif score >= 60:
        score_color = "orange"
    else:
        score_color = "red"
    
    # 総合評価の表示
    st.markdown(f"""
    <div style="
        padding: 20px;
        border-radius: 10px;
        border: 2px solid {score_color};
        text-align: center;
        margin-bottom: 20px;
    ">
        <h2 style="margin-bottom: 10px;">総合パフォーマンス</h2>
        <div style="
            font-size: 3em;
            font-weight: bold;
            color: {score_color};
            margin-bottom: 10px;
        ">{score:.1f}/100</div>
        <div style="
            font-size: 1.5em;
            font-weight: bold;
        ">{rating}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if "summary" in overall:
        st.subheader("評価サマリー")
        st.info(overall["summary"])
    
    # 強みと改善点の表示
    if "strengths" in overall and overall["strengths"]:
        st.subheader("強み")
        for strength in overall["strengths"]:
            st.success(strength)
    
    if "weaknesses" in overall and overall["weaknesses"]:
        st.subheader("改善点")
        for weakness in overall["weaknesses"]:
            st.warning(weakness)
    
    # 基本統計情報
    basic_stats = performance_data.get("basic_stats", {})
    
    if basic_stats:
        st.subheader("基本統計情報")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if "speed" in basic_stats:
                speed_stats = basic_stats["speed"]
                st.metric("平均速度", f"{speed_stats.get('mean', 0):.1f}ノット")
                st.metric("最大速度", f"{speed_stats.get('max', 0):.1f}ノット")
        
        with col2:
            if "sailing_mode_percentage" in basic_stats:
                modes = basic_stats["sailing_mode_percentage"]
                st.metric("風上時間", f"{modes.get('upwind', 0):.1f}%")
                st.metric("風下時間", f"{modes.get('downwind', 0):.1f}%")
        
        with col3:
            if "vmg" in basic_stats:
                vmg_stats = basic_stats["vmg"]
                upwind_vmg = vmg_stats.get("upwind_mean")
                downwind_vmg = vmg_stats.get("downwind_mean")
                
                if upwind_vmg is not None:
                    st.metric("風上VMG平均", f"{upwind_vmg:.2f}ノット")
                
                if downwind_vmg is not None:
                    st.metric("風下VMG平均", f"{downwind_vmg:.2f}ノット")


def display_vmg_analysis(vmg_analysis: Dict[str, Any]) -> None:
    """
    VMG分析の表示
    
    Parameters:
    -----------
    vmg_analysis : Dict[str, Any]
        VMG分析データ
    """
    if not vmg_analysis:
        st.warning("VMG分析データがありません。")
        return
    
    st.subheader("VMG分析")
    
    # タブの作成
    vmg_tab1, vmg_tab2 = st.tabs(["風上VMG", "風下VMG"])
    
    # 風上VMG分析
    with vmg_tab1:
        upwind = vmg_analysis.get("upwind", {})
        
        if upwind and not upwind.get("insufficient_data", False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("平均VMG", f"{upwind.get('mean_vmg', 0):.2f}ノット")
                st.metric("最大VMG", f"{upwind.get('max_vmg', 0):.2f}ノット")
            
            with col2:
                st.metric("平均角度", f"{upwind.get('mean_angle', 0):.1f}°")
                st.metric("最適角度", f"{upwind.get('optimal_angle', 0):.1f}°")
            
            with col3:
                # 最適値との比較
                if upwind.get("optimal_vmg") and upwind.get("performance_ratio"):
                    st.metric("最適VMG", f"{upwind.get('optimal_vmg', 0):.2f}ノット")
                    st.metric("最適VMG比", f"{upwind.get('performance_ratio', 0):.1%}")
            
            # VMG分布のグラフ
            if "vmg_distribution" in upwind and upwind["vmg_distribution"]:
                vmg_dist = upwind["vmg_distribution"]
                
                # VMG分布データフレームの作成
                angles = []
                vmgs = []
                counts = []
                
                for angle, data in vmg_dist.items():
                    angles.append(float(angle))
                    vmgs.append(data.get("mean_vmg", 0))
                    counts.append(data.get("count", 0))
                
                df = pd.DataFrame({
                    "angle": angles,
                    "vmg": vmgs,
                    "count": counts
                })
                
                # 最適角度
                optimal_angle = upwind.get("optimal_angle")
                
                # VMG-角度分布のプロット
                fig = px.scatter(
                    df,
                    x="angle",
                    y="vmg",
                    size="count",
                    color="vmg",
                    color_continuous_scale="Viridis",
                    title="風上VMG分布",
                    labels={"angle": "風に対する角度 (°)", "vmg": "VMG (ノット)", "count": "データポイント数"}
                )
                
                # 最適角度の縦線を追加
                if optimal_angle is not None:
                    fig.add_vline(
                        x=optimal_angle, 
                        line_width=2, 
                        line_dash="dash", 
                        line_color="red",
                        annotation_text="最適角度",
                        annotation_position="top right"
                    )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("風上VMGデータが十分ではありません。")
    
    # 風下VMG分析
    with vmg_tab2:
        downwind = vmg_analysis.get("downwind", {})
        
        if downwind and not downwind.get("insufficient_data", False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("平均VMG", f"{downwind.get('mean_vmg', 0):.2f}ノット")
                st.metric("最大VMG", f"{downwind.get('max_vmg', 0):.2f}ノット")
            
            with col2:
                st.metric("平均角度", f"{downwind.get('mean_angle', 0):.1f}°")
                st.metric("最適角度", f"{downwind.get('optimal_angle', 0):.1f}°")
            
            with col3:
                # 最適値との比較
                if downwind.get("optimal_vmg") and downwind.get("performance_ratio"):
                    st.metric("最適VMG", f"{downwind.get('optimal_vmg', 0):.2f}ノット")
                    st.metric("最適VMG比", f"{downwind.get('performance_ratio', 0):.1%}")
            
            # VMG分布のグラフ
            if "vmg_distribution" in downwind and downwind["vmg_distribution"]:
                vmg_dist = downwind["vmg_distribution"]
                
                # VMG分布データフレームの作成
                angles = []
                vmgs = []
                counts = []
                
                for angle, data in vmg_dist.items():
                    angles.append(float(angle))
                    vmgs.append(data.get("mean_vmg", 0))
                    counts.append(data.get("count", 0))
                
                df = pd.DataFrame({
                    "angle": angles,
                    "vmg": vmgs,
                    "count": counts
                })
                
                # 最適角度
                optimal_angle = downwind.get("optimal_angle")
                
                # VMG-角度分布のプロット
                fig = px.scatter(
                    df,
                    x="angle",
                    y="vmg",
                    size="count",
                    color="vmg",
                    color_continuous_scale="Viridis",
                    title="風下VMG分布",
                    labels={"angle": "風に対する角度 (°)", "vmg": "VMG (ノット)", "count": "データポイント数"}
                )
                
                # 最適角度の縦線を追加
                if optimal_angle is not None:
                    fig.add_vline(
                        x=optimal_angle, 
                        line_width=2, 
                        line_dash="dash", 
                        line_color="red",
                        annotation_text="最適角度",
                        annotation_position="top right"
                    )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("風下VMGデータが十分ではありません。")


def display_maneuver_analysis(maneuver_analysis: Dict[str, Any]) -> None:
    """
    マニューバー分析の表示
    
    Parameters:
    -----------
    maneuver_analysis : Dict[str, Any]
        マニューバー分析データ
    """
    if not maneuver_analysis:
        st.warning("マニューバー分析データがありません。")
        return
    
    if maneuver_analysis.get("insufficient_data", False):
        st.info("マニューバー分析に十分なデータがありません。")
        return
    
    st.subheader("マニューバー分析")
    
    # タブの作成
    maneuver_tab1, maneuver_tab2 = st.tabs(["タック分析", "ジャイブ分析"])
    
    # タック分析
    with maneuver_tab1:
        tacks = maneuver_analysis.get("tacks", {})
        tack_count = maneuver_analysis.get("tack_count", 0)
        
        if tacks and tack_count > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("タック回数", tack_count)
            
            with col2:
                st.metric("平均所要時間", f"{tacks.get('avg_duration', 0):.1f}秒")
            
            with col3:
                st.metric("平均速度損失", f"{tacks.get('avg_speed_loss', 0):.1%}")
            
            # タック詳細情報
            st.subheader("タック詳細")
            
            if "details" in tacks and tacks["details"]:
                # タック詳細をデータフレームに変換
                tack_details = tacks["details"]
                
                if isinstance(tack_details, list) and len(tack_details) > 0:
                    # データフレームに変換
                    df_tacks = pd.DataFrame(tack_details)
                    
                    # 表示カラムの選択
                    display_columns = [
                        "timestamp", "duration_seconds", "start_speed", 
                        "min_speed", "end_speed", "speed_loss_percentage", 
                        "heading_change", "quality_score"
                    ]
                    
                    # 存在するカラムのみ選択
                    display_columns = [col for col in display_columns if col in df_tacks.columns]
                    
                    if display_columns:
                        # 表示用データフレーム作成
                        display_df = df_tacks[display_columns].copy()
                        
                        # カラム名の日本語化
                        column_labels = {
                            "timestamp": "時間",
                            "duration_seconds": "所要時間(秒)",
                            "start_speed": "開始速度(ノット)",
                            "min_speed": "最低速度(ノット)",
                            "end_speed": "終了速度(ノット)",
                            "speed_loss_percentage": "速度損失(%)",
                            "heading_change": "進路変化(°)",
                            "quality_score": "品質スコア"
                        }
                        
                        display_df.columns = [column_labels.get(col, col) for col in display_df.columns]
                        
                        # タイムスタンプのフォーマット
                        if "時間" in display_df.columns and pd.api.types.is_datetime64_any_dtype(display_df["時間"]):
                            display_df["時間"] = display_df["時間"].dt.strftime("%H:%M:%S")
                        
                        # 数値のフォーマット
                        for col in ["所要時間(秒)", "開始速度(ノット)", "最低速度(ノット)", "終了速度(ノット)"]:
                            if col in display_df.columns:
                                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
                        
                        # パーセントのフォーマット
                        if "速度損失(%)" in display_df.columns:
                            display_df["速度損失(%)"] = display_df["速度損失(%)"].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "-")
                        
                        # 角度のフォーマット
                        if "進路変化(°)" in display_df.columns:
                            display_df["進路変化(°)"] = display_df["進路変化(°)"].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
                        
                        # 品質スコアのフォーマット
                        if "品質スコア" in display_df.columns:
                            display_df["品質スコア"] = display_df["品質スコア"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
                        
                        # データフレームの表示
                        st.dataframe(display_df)
                        
                        # タック速度損失の分布グラフ
                        if "speed_loss_percentage" in df_tacks.columns:
                            # 速度損失のヒストグラム
                            fig, ax = plt.subplots(figsize=(10, 6))
                            
                            # パーセント表示に変換
                            speed_loss_pct = df_tacks["speed_loss_percentage"] * 100
                            
                            ax.hist(
                                speed_loss_pct, 
                                bins=10, 
                                alpha=0.7, 
                                color="green", 
                                edgecolor="black"
                            )
                            
                            ax.set_title("タック速度損失の分布")
                            ax.set_xlabel("速度損失 (%)")
                            ax.set_ylabel("頻度")
                            ax.grid(True, alpha=0.3)
                            
                            # 平均値の縦線
                            ax.axvline(
                                x=speed_loss_pct.mean(),
                                color="red",
                                linestyle="--",
                                label=f"平均: {speed_loss_pct.mean():.1f}%"
                            )
                            
                            ax.legend()
                            
                            st.pyplot(fig)
                    else:
                        st.warning("表示するデータ列がありません。")
                else:
                    st.info("タックの詳細データがありません。")
            else:
                st.info("タックの詳細情報がありません。")
        else:
            st.info("タックデータがありません。")
    
    # ジャイブ分析
    with maneuver_tab2:
        gybes = maneuver_analysis.get("gybes", {})
        gybe_count = maneuver_analysis.get("gybe_count", 0)
        
        if gybes and gybe_count > 0:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("ジャイブ回数", gybe_count)
            
            with col2:
                st.metric("平均所要時間", f"{gybes.get('avg_duration', 0):.1f}秒")
            
            with col3:
                st.metric("平均速度損失", f"{gybes.get('avg_speed_loss', 0):.1%}")
            
            # ジャイブ詳細情報
            st.subheader("ジャイブ詳細")
            
            if "details" in gybes and gybes["details"]:
                # ジャイブ詳細をデータフレームに変換
                gybe_details = gybes["details"]
                
                if isinstance(gybe_details, list) and len(gybe_details) > 0:
                    # データフレームに変換
                    df_gybes = pd.DataFrame(gybe_details)
                    
                    # 表示カラムの選択
                    display_columns = [
                        "timestamp", "duration_seconds", "start_speed", 
                        "min_speed", "end_speed", "speed_loss_percentage", 
                        "heading_change", "quality_score"
                    ]
                    
                    # 存在するカラムのみ選択
                    display_columns = [col for col in display_columns if col in df_gybes.columns]
                    
                    if display_columns:
                        # 表示用データフレーム作成
                        display_df = df_gybes[display_columns].copy()
                        
                        # カラム名の日本語化
                        column_labels = {
                            "timestamp": "時間",
                            "duration_seconds": "所要時間(秒)",
                            "start_speed": "開始速度(ノット)",
                            "min_speed": "最低速度(ノット)",
                            "end_speed": "終了速度(ノット)",
                            "speed_loss_percentage": "速度損失(%)",
                            "heading_change": "進路変化(°)",
                            "quality_score": "品質スコア"
                        }
                        
                        display_df.columns = [column_labels.get(col, col) for col in display_df.columns]
                        
                        # タイムスタンプのフォーマット
                        if "時間" in display_df.columns and pd.api.types.is_datetime64_any_dtype(display_df["時間"]):
                            display_df["時間"] = display_df["時間"].dt.strftime("%H:%M:%S")
                        
                        # 数値のフォーマット
                        for col in ["所要時間(秒)", "開始速度(ノット)", "最低速度(ノット)", "終了速度(ノット)"]:
                            if col in display_df.columns:
                                display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
                        
                        # パーセントのフォーマット
                        if "速度損失(%)" in display_df.columns:
                            display_df["速度損失(%)"] = display_df["速度損失(%)"].apply(lambda x: f"{x*100:.1f}%" if pd.notnull(x) else "-")
                        
                        # 角度のフォーマット
                        if "進路変化(°)" in display_df.columns:
                            display_df["進路変化(°)"] = display_df["進路変化(°)"].apply(lambda x: f"{x:.1f}" if pd.notnull(x) else "-")
                        
                        # 品質スコアのフォーマット
                        if "品質スコア" in display_df.columns:
                            display_df["品質スコア"] = display_df["品質スコア"].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "-")
                        
                        # データフレームの表示
                        st.dataframe(display_df)
                        
                        # ジャイブ速度損失の分布グラフ
                        if "speed_loss_percentage" in df_gybes.columns:
                            # 速度損失のヒストグラム
                            fig, ax = plt.subplots(figsize=(10, 6))
                            
                            # パーセント表示に変換
                            speed_loss_pct = df_gybes["speed_loss_percentage"] * 100
                            
                            ax.hist(
                                speed_loss_pct, 
                                bins=10, 
                                alpha=0.7, 
                                color="orange", 
                                edgecolor="black"
                            )
                            
                            ax.set_title("ジャイブ速度損失の分布")
                            ax.set_xlabel("速度損失 (%)")
                            ax.set_ylabel("頻度")
                            ax.grid(True, alpha=0.3)
                            
                            # 平均値の縦線
                            ax.axvline(
                                x=speed_loss_pct.mean(),
                                color="red",
                                linestyle="--",
                                label=f"平均: {speed_loss_pct.mean():.1f}%"
                            )
                            
                            ax.legend()
                            
                            st.pyplot(fig)
                    else:
                        st.warning("表示するデータ列がありません。")
                else:
                    st.info("ジャイブの詳細データがありません。")
            else:
                st.info("ジャイブの詳細情報がありません。")
        else:
            st.info("ジャイブデータがありません。")


def display_speed_analysis(performance_data: Dict[str, Any], df: pd.DataFrame) -> None:
    """
    速度分析の表示
    
    Parameters:
    -----------
    performance_data : Dict[str, Any]
        パフォーマンス分析データ
    df : pd.DataFrame
        元のGPSデータフレーム
    """
    if not performance_data:
        st.warning("パフォーマンスデータがありません。")
        return
    
    st.subheader("速度分析")
    
    # 基本統計情報
    basic_stats = performance_data.get("basic_stats", {})
    
    if "speed" in basic_stats:
        speed_stats = basic_stats["speed"]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("平均速度", f"{speed_stats.get('mean', 0):.1f}ノット")
        
        with col2:
            st.metric("最大速度", f"{speed_stats.get('max', 0):.1f}ノット")
        
        with col3:
            st.metric("中央値速度", f"{speed_stats.get('median', 0):.1f}ノット")
    
    # 速度分布のヒストグラム
    if df is not None and "speed" in df.columns:
        fig = px.histogram(
            df,
            x="speed",
            nbins=20,
            title="速度分布",
            labels={"speed": "速度 (ノット)", "count": "頻度"},
            color_discrete_sequence=["skyblue"]
        )
        
        # 平均値の縦線を追加
        if "speed" in basic_stats and "mean" in basic_stats["speed"]:
            mean_speed = basic_stats["speed"]["mean"]
            fig.add_vline(
                x=mean_speed, 
                line_width=2, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"平均: {mean_speed:.1f}ノット",
                annotation_position="top right"
            )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 風角度別の速度分析
    polar_data = performance_data.get("polar_analysis", {})
    
    if polar_data:
        st.subheader("風角度別の速度分析")
        
        # 極座標グラフの作成
        angles = []
        speeds = []
        counts = []
        
        for angle_str, data in polar_data.items():
            try:
                angle = float(angle_str)
                speeds.append(data.get("avg_speed", 0))
                angles.append(angle)
                counts.append(data.get("count", 0))
            except (ValueError, TypeError):
                continue
        
        if angles and speeds:
            # データフレーム作成
            df_polar = pd.DataFrame({
                "angle": angles,
                "speed": speeds,
                "count": counts
            })
            
            # カラーマップの設定
            fig = go.Figure()
            
            # 極座標グラフの作成
            fig.add_trace(go.Scatterpolar(
                r=df_polar["speed"],
                theta=df_polar["angle"],
                mode="markers+lines",
                marker=dict(
                    size=df_polar["count"],
                    sizemode="area",
                    sizeref=2.*max(df_polar["count"])/(40.**2),
                    sizemin=4,
                    color=df_polar["speed"],
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(
                        title="速度<br>(ノット)"
                    )
                ),
                line=dict(color="rgba(255, 255, 255, 0.5)"),
                name="平均速度"
            ))
            
            # レイアウト設定
            fig.update_layout(
                title="風角度別の速度分布",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(df_polar["speed"]) * 1.1]
                    ),
                    angularaxis=dict(
                        tickmode="array",
                        tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                        ticktext=["0°", "45°", "90°", "135°", "180°", "225°", "270°", "315°"]
                    )
                ),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 説明テキスト
            st.info("""
            このグラフは風角度別の平均速度を示しています。
            - 中心から外側に向かうほど速度が高いことを示します
            - 円の大きさはその角度でのデータポイント数を表します
            - カラーは速度を表し、赤色ほど速度が高いことを示します
            """)
        else:
            st.info("風角度別の速度データがありません。")
    else:
        st.info("風角度別の速度分析データがありません。")


def analyze_performance_from_df(df: pd.DataFrame, params_manager: ParametersManager) -> Dict[str, Any]:
    """
    データフレームからパフォーマンスを分析
    
    Parameters:
    -----------
    df : pd.DataFrame
        GPSデータを含むデータフレーム
    params_manager : ParametersManager
        パラメータ管理オブジェクト
        
    Returns:
    --------
    Dict[str, Any]
        パフォーマンス分析結果
    """
    # 必須カラムの確認
    required_cols = ["timestamp", "latitude", "longitude", "course", "speed"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        return {
            "error": f"データに必須カラムがありません: {', '.join(missing_cols)}",
            "overall_performance": {
                "score": 0,
                "rating": "評価不能",
                "summary": "必要なデータが不足しています。"
            }
        }
    
    try:
        # 分析モジュールのインスタンス化
        cache = AnalysisCache()
        wind_estimator = IntegratedWindEstimator(params_manager, cache)
        performance_analyzer = IntegratedPerformanceAnalyzer(params_manager, cache, wind_estimator)
        
        # パフォーマンス分析の実行
        result = performance_analyzer.analyze_performance(df)
        
        return result
    except Exception as e:
        logger.exception(f"パフォーマンス分析中にエラーが発生しました: {str(e)}")
        return {
            "error": f"パフォーマンス分析エラー: {str(e)}",
            "overall_performance": {
                "score": 0,
                "rating": "エラー",
                "summary": f"分析中にエラーが発生しました: {str(e)}"
            }
        }


def performance_analysis_page() -> None:
    """
    パフォーマンス分析ページのメインエントリーポイント
    """
    st.title("パフォーマンス分析")
    
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
        
        # パラメータ調整とパフォーマンス分析
        with st.expander("パフォーマンス分析パラメータ", expanded=False):
            st.write("パフォーマンス分析のためのパラメータを調整できます。")
            
            # パラメータ調整パネル
            performance_params = parameter_adjustment_panel(
                params_manager, 
                ParameterNamespace.PERFORMANCE_ANALYSIS
            )
        
        # パフォーマンス分析実行ボタン
        col1, col2 = st.columns([1, 1])
        
        with col1:
            analyze_button = st.button("パフォーマンスを分析", key="analyze_performance", use_container_width=True)
        
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
        
        # パフォーマンス分析結果のキャッシュ
        if 'performance_result' not in st.session_state:
            st.session_state.performance_result = None
        
        # パフォーマンス分析の実行
        if analyze_button:
            with st.spinner("パフォーマンスを分析中..."):
                performance_result = analyze_performance_from_df(df, params_manager)
                st.session_state.performance_result = performance_result
                
                # 成功メッセージまたはエラーメッセージ
                if "error" in performance_result:
                    st.error(performance_result["error"])
                else:
                    overall = performance_result.get("overall_performance", {})
                    score = overall.get("score", 0)
                    rating = overall.get("rating", "評価なし")
                    
                    st.success(
                        f"パフォーマンス分析が完了しました。"
                        f"総合スコア: {score:.1f}/100 ({rating})"
                    )
        
        # ワークフローからの結果取得
        elif workflow_button:
            if 'workflow_controller' in st.session_state:
                workflow_controller = st.session_state.workflow_controller
                
                # 結果の取得
                results = workflow_controller.get_results()
                
                if "performance_result" in results:
                    st.session_state.performance_result = results["performance_result"]
                    
                    # 成功メッセージ
                    overall = results["performance_result"].get("overall_performance", {})
                    score = overall.get("score", 0)
                    rating = overall.get("rating", "評価なし")
                    
                    st.success(
                        f"ワークフローからパフォーマンス分析を取得しました。"
                        f"総合スコア: {score:.1f}/100 ({rating})"
                    )
                else:
                    st.warning("ワークフローにパフォーマンス分析結果が見つかりません。ワークフローを実行してください。")
        
        # 結果の表示
        performance_result = st.session_state.performance_result
        
        if performance_result:
            # 結果を複数のセクションに分けて表示
            tabs = st.tabs(["概要", "VMG分析", "マニューバー分析", "速度分析"])
            
            # 概要タブ
            with tabs[0]:
                display_performance_overview(performance_result)
            
            # VMG分析タブ
            with tabs[1]:
                vmg_analysis = performance_result.get("vmg_analysis", {})
                display_vmg_analysis(vmg_analysis)
            
            # マニューバー分析タブ
            with tabs[2]:
                maneuver_analysis = performance_result.get("maneuver_analysis", {})
                display_maneuver_analysis(maneuver_analysis)
            
            # 速度分析タブ
            with tabs[3]:
                display_speed_analysis(performance_result, df)
        
        else:
            # パフォーマンス分析の説明
            st.info("""
            「パフォーマンスを分析」ボタンをクリックして、セーリングパフォーマンスを評価します。
            
            このモジュールでは、以下のようなパフォーマンス指標を分析します：
            
            1. **VMG分析**: 風上/風下での速度と角度の最適性を評価します
            2. **マニューバー分析**: タックやジャイブの効率を評価します
            3. **速度分析**: 風向や風速に対する速度パフォーマンスを分析します
            
            分析結果は総合スコアとして0〜100点で評価され、詳細な改善点が提案されます。
            """)
    
    else:
        st.info("パフォーマンスを分析するには、まずプロジェクトからセッションを選択してください。")


if __name__ == "__main__":
    performance_analysis_page()
