# -*- coding: utf-8 -*-
"""
ui.integrated.components.charts.vmg_analysis_chart

VMG分析チャートコンポーネント
風上/風下のVMG（Velocity Made Good）パフォーマンスを分析します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

class VMGAnalysisChart:
    """VMG分析チャートコンポーネント"""
    
    def __init__(self, title: str = "VMG分析"):
        """
        初期化
        
        Parameters
        ----------
        title : str, optional
            チャートのタイトル, by default "VMG分析"
        """
        self.title = title
        self.options = {
            "upwind_threshold": 45,  # 風上セグメントの閾値（度）
            "downwind_threshold": 120,  # 風下セグメントの閾値（度）
            "show_segments": True,  # 風上/風下セグメントの表示
            "show_histograms": True,  # ヒストグラム表示
            "height": 400
        }
    
    def update_options(self, options: Dict[str, Any]):
        """
        オプションを更新
        
        Parameters
        ----------
        options : Dict[str, Any]
            更新するオプション
        """
        self.options.update(options)
    
    def render_controls(self):
        """
        チャートのコントロールを描画
        
        Returns
        -------
        Dict[str, Any]
            更新されたオプション
        """
        # オプションのコピーを作成
        updated_options = self.options.copy()
        
        # コントロールを2列のレイアウトで表示
        col1, col2 = st.columns(2)
        
        with col1:
            updated_options["upwind_threshold"] = st.slider(
                "風上セグメント閾値 (度)", 
                min_value=0, 
                max_value=90, 
                value=self.options["upwind_threshold"],
                help="この角度未満を風上セグメントとして扱います"
            )
            
            updated_options["show_segments"] = st.checkbox(
                "風上/風下セグメント分割を表示", 
                value=self.options["show_segments"]
            )
        
        with col2:
            updated_options["downwind_threshold"] = st.slider(
                "風下セグメント閾値 (度)", 
                min_value=90, 
                max_value=180, 
                value=self.options["downwind_threshold"],
                help="この角度を超える場合を風下セグメントとして扱います"
            )
            
            updated_options["show_histograms"] = st.checkbox(
                "VMG分布ヒストグラムを表示", 
                value=self.options["show_histograms"]
            )
        
        return updated_options
    
    def render(self, data: pd.DataFrame, target_vmg: Optional[Dict[str, float]] = None):
        """
        VMG分析チャートを描画
        
        Parameters
        ----------
        data : pd.DataFrame
            描画するデータ
            必要なカラム:
            - wind_angle: 風向角度（船の進行方向に対する相対角度、0-180度）
            - boat_speed: 船速 (ノット)
            - vmg: VMG (ノット)
        target_vmg : Optional[Dict[str, float]], optional
            目標VMG値, by default None
            "upwind"と"downwind"をキーとする辞書
        """
        st.write(f"### {self.title}")
        
        # データの検証
        if data is None or len(data) == 0:
            st.warning("データがありません。")
            return
        
        if "wind_angle" not in data.columns:
            st.error("データに 'wind_angle' カラムがありません。")
            return
            
        if "boat_speed" not in data.columns:
            st.error("データに 'boat_speed' カラムがありません。")
            return
            
        if "vmg" not in data.columns:
            st.error("データに 'vmg' カラムがありません。")
            return
        
        # 風上/風下セグメントの分類
        upwind_mask = data["wind_angle"] < self.options["upwind_threshold"]
        downwind_mask = data["wind_angle"] > self.options["downwind_threshold"]
        reach_mask = ~(upwind_mask | downwind_mask)
        
        # 風上/風下/リーチのデータを抽出
        upwind_data = data[upwind_mask].copy()
        downwind_data = data[downwind_mask].copy()
        reach_data = data[reach_mask].copy()
        
        # VMGの符号を調整（風上は正、風下は負のVMGとする場合）
        # 実装によっては既に適切な符号が付けられている場合もある
        
        # 風上/風下のVMG分析
        upwind_vmg_mean = upwind_data["vmg"].mean() if not upwind_data.empty else np.nan
        downwind_vmg_mean = downwind_data["vmg"].mean() if not downwind_data.empty else np.nan
        
        upwind_vmg_max = upwind_data["vmg"].max() if not upwind_data.empty else np.nan
        downwind_vmg_min = downwind_data["vmg"].min() if not downwind_data.empty else np.nan
        
        # タブでVMG分析コンテンツを分ける
        tab1, tab2, tab3 = st.tabs(["時系列VMG", "VMG分布", "VMG vs 風向角度"])
        
        with tab1:
            # 時系列VMGチャート
            self._render_vmg_time_series(data, upwind_data, downwind_data, target_vmg)
        
        with tab2:
            # VMG分布チャート
            if self.options["show_histograms"]:
                self._render_vmg_distribution(upwind_data, downwind_data, target_vmg)
        
        with tab3:
            # VMG vs 風向角度チャート
            self._render_vmg_vs_angle(data, target_vmg)
        
        # VMG分析の統計情報の表示
        self._render_vmg_stats(upwind_data, downwind_data, target_vmg)
    
    def _render_vmg_time_series(self, data: pd.DataFrame, 
                               upwind_data: pd.DataFrame, 
                               downwind_data: pd.DataFrame,
                               target_vmg: Optional[Dict[str, float]] = None):
        """
        時系列VMGチャートを描画
        
        Parameters
        ----------
        data : pd.DataFrame
            全データ
        upwind_data : pd.DataFrame
            風上セグメントのデータ
        downwind_data : pd.DataFrame
            風下セグメントのデータ
        target_vmg : Optional[Dict[str, float]], optional
            目標VMG値, by default None
        """
        # 時系列があるか確認
        if "timestamp" not in data.columns:
            st.error("時系列分析には 'timestamp' カラムが必要です。")
            return
        
        # 基本グラフの作成
        fig = go.Figure()
        
        # 全データのVMGプロット
        fig.add_trace(
            go.Scatter(
                x=data["timestamp"],
                y=data["vmg"],
                name="VMG",
                mode="lines",
                line=dict(color="#1f77b4", width=2)
            )
        )
        
        # 風上/風下セグメントをハイライト表示
        if self.options["show_segments"]:
            # 風上セグメントのハイライト
            if not upwind_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=upwind_data["timestamp"],
                        y=upwind_data["vmg"],
                        name="風上VMG",
                        mode="markers",
                        marker=dict(size=8, color="green", opacity=0.5)
                    )
                )
            
            # 風下セグメントのハイライト
            if not downwind_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=downwind_data["timestamp"],
                        y=downwind_data["vmg"],
                        name="風下VMG",
                        mode="markers",
                        marker=dict(size=8, color="red", opacity=0.5)
                    )
                )
        
        # 目標VMG値の表示
        if target_vmg is not None:
            # 風上の目標VMG
            if "upwind" in target_vmg:
                fig.add_trace(
                    go.Scatter(
                        x=[data["timestamp"].min(), data["timestamp"].max()],
                        y=[target_vmg["upwind"], target_vmg["upwind"]],
                        name="目標風上VMG",
                        mode="lines",
                        line=dict(color="green", width=2, dash="dash")
                    )
                )
            
            # 風下の目標VMG
            if "downwind" in target_vmg:
                fig.add_trace(
                    go.Scatter(
                        x=[data["timestamp"].min(), data["timestamp"].max()],
                        y=[target_vmg["downwind"], target_vmg["downwind"]],
                        name="目標風下VMG",
                        mode="lines",
                        line=dict(color="red", width=2, dash="dash")
                    )
                )
        
        # レイアウト設定
        fig.update_layout(
            height=self.options["height"],
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(title="時間"),
            yaxis=dict(title="VMG (ノット)"),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="closest"
        )
        
        # チャートの表示
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_vmg_distribution(self, upwind_data: pd.DataFrame, 
                                downwind_data: pd.DataFrame,
                                target_vmg: Optional[Dict[str, float]] = None):
        """
        VMG分布チャートを描画
        
        Parameters
        ----------
        upwind_data : pd.DataFrame
            風上セグメントのデータ
        downwind_data : pd.DataFrame
            風下セグメントのデータ
        target_vmg : Optional[Dict[str, float]], optional
            目標VMG値, by default None
        """
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        # 風上VMG分布
        with col1:
            st.write("#### 風上VMG分布")
            
            if upwind_data.empty:
                st.info("風上セグメントのデータがありません。")
            else:
                # 風上VMGのヒストグラム
                fig_upwind = px.histogram(
                    upwind_data, 
                    x="vmg",
                    nbins=20,
                    labels={"vmg": "VMG (ノット)"},
                    title="風上VMG分布"
                )
                
                # 目標VMG値の表示
                if target_vmg is not None and "upwind" in target_vmg:
                    fig_upwind.add_vline(
                        x=target_vmg["upwind"],
                        line_dash="dash",
                        line_color="green",
                        annotation_text="目標VMG",
                        annotation_position="top right"
                    )
                
                # 平均VMG値の表示
                upwind_vmg_mean = upwind_data["vmg"].mean()
                fig_upwind.add_vline(
                    x=upwind_vmg_mean,
                    line_dash="solid",
                    line_color="blue",
                    annotation_text=f"平均: {upwind_vmg_mean:.2f} kt",
                    annotation_position="top left"
                )
                
                # レイアウト設定
                fig_upwind.update_layout(
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0),
                    xaxis=dict(title="VMG (ノット)"),
                    yaxis=dict(title="頻度")
                )
                
                # チャートの表示
                st.plotly_chart(fig_upwind, use_container_width=True)
        
        # 風下VMG分布
        with col2:
            st.write("#### 風下VMG分布")
            
            if downwind_data.empty:
                st.info("風下セグメントのデータがありません。")
            else:
                # 風下VMGのヒストグラム
                fig_downwind = px.histogram(
                    downwind_data, 
                    x="vmg",
                    nbins=20,
                    labels={"vmg": "VMG (ノット)"},
                    title="風下VMG分布"
                )
                
                # 目標VMG値の表示
                if target_vmg is not None and "downwind" in target_vmg:
                    fig_downwind.add_vline(
                        x=target_vmg["downwind"],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="目標VMG",
                        annotation_position="top right"
                    )
                
                # 平均VMG値の表示
                downwind_vmg_mean = downwind_data["vmg"].mean()
                fig_downwind.add_vline(
                    x=downwind_vmg_mean,
                    line_dash="solid",
                    line_color="blue",
                    annotation_text=f"平均: {downwind_vmg_mean:.2f} kt",
                    annotation_position="top left"
                )
                
                # レイアウト設定
                fig_downwind.update_layout(
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0),
                    xaxis=dict(title="VMG (ノット)"),
                    yaxis=dict(title="頻度")
                )
                
                # チャートの表示
                st.plotly_chart(fig_downwind, use_container_width=True)
    
    def _render_vmg_vs_angle(self, data: pd.DataFrame,
                            target_vmg: Optional[Dict[str, float]] = None):
        """
        VMG vs 風向角度チャートを描画
        
        Parameters
        ----------
        data : pd.DataFrame
            全データ
        target_vmg : Optional[Dict[str, float]], optional
            目標VMG値, by default None
        """
        if data.empty:
            st.info("データがありません。")
            return
        
        # VMG vs 風向角度の散布図
        fig = px.scatter(
            data, 
            x="wind_angle",
            y="vmg",
            color="boat_speed",
            color_continuous_scale="Viridis",
            labels={
                "wind_angle": "風向角度 (度)",
                "vmg": "VMG (ノット)",
                "boat_speed": "船速 (ノット)"
            },
            title="VMG vs 風向角度"
        )
        
        # 目標VMG値の表示
        if target_vmg is not None:
            # 風上の目標VMG
            if "upwind" in target_vmg:
                fig.add_hline(
                    y=target_vmg["upwind"],
                    line_dash="dash",
                    line_color="green",
                    annotation_text="目標風上VMG",
                    annotation_position="top right"
                )
            
            # 風下の目標VMG
            if "downwind" in target_vmg:
                fig.add_hline(
                    y=target_vmg["downwind"],
                    line_dash="dash",
                    line_color="red",
                    annotation_text="目標風下VMG",
                    annotation_position="bottom right"
                )
        
        # 風上/風下の閾値ラインを追加
        fig.add_vline(
            x=self.options["upwind_threshold"],
            line_dash="dot",
            line_color="green",
            annotation_text="風上閾値",
            annotation_position="top right"
        )
        
        fig.add_vline(
            x=self.options["downwind_threshold"],
            line_dash="dot",
            line_color="red",
            annotation_text="風下閾値",
            annotation_position="top right"
        )
        
        # 回帰曲線の追加（VMGと風向角度の関係）
        try:
            # 風向角度の範囲
            angle_range = np.linspace(0, 180, 100)
            
            # 2次多項式フィッティング
            poly_coeffs = np.polyfit(data["wind_angle"], data["vmg"], 2)
            poly_fn = np.poly1d(poly_coeffs)
            fitted_vmg = poly_fn(angle_range)
            
            # 回帰曲線を追加
            fig.add_trace(
                go.Scatter(
                    x=angle_range,
                    y=fitted_vmg,
                    mode="lines",
                    line=dict(color="black", width=2),
                    name="VMG曲線"
                )
            )
            
            # 最適風上/風下VMG角度を見つける
            upwind_mask = angle_range < 90
            downwind_mask = angle_range >= 90
            
            # 風上最適角度（VMG最大値）
            if any(upwind_mask):
                upwind_angles = angle_range[upwind_mask]
                upwind_vmgs = fitted_vmg[upwind_mask]
                best_upwind_idx = np.argmax(upwind_vmgs)
                best_upwind_angle = upwind_angles[best_upwind_idx]
                best_upwind_vmg = upwind_vmgs[best_upwind_idx]
                
                # 最適角度にマーカーを追加
                fig.add_trace(
                    go.Scatter(
                        x=[best_upwind_angle],
                        y=[best_upwind_vmg],
                        mode="markers+text",
                        marker=dict(size=10, color="green", symbol="star"),
                        text=f"{best_upwind_angle:.1f}°",
                        textposition="top center",
                        name=f"最適風上角度: {best_upwind_angle:.1f}°"
                    )
                )
            
            # 風下最適角度（VMG最小値 - 負のVMGが大きいほど風下効率が高い）
            if any(downwind_mask):
                downwind_angles = angle_range[downwind_mask]
                downwind_vmgs = fitted_vmg[downwind_mask]
                best_downwind_idx = np.argmin(downwind_vmgs)
                best_downwind_angle = downwind_angles[best_downwind_idx]
                best_downwind_vmg = downwind_vmgs[best_downwind_idx]
                
                # 最適角度にマーカーを追加
                fig.add_trace(
                    go.Scatter(
                        x=[best_downwind_angle],
                        y=[best_downwind_vmg],
                        mode="markers+text",
                        marker=dict(size=10, color="red", symbol="star"),
                        text=f"{best_downwind_angle:.1f}°",
                        textposition="bottom center",
                        name=f"最適風下角度: {best_downwind_angle:.1f}°"
                    )
                )
                
        except Exception as e:
            st.warning(f"回帰曲線のフィッティングに失敗しました: {e}")
        
        # レイアウト設定
        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(title="風向角度 (度)"),
            yaxis=dict(title="VMG (ノット)"),
            hovermode="closest"
        )
        
        # チャートの表示
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_vmg_stats(self, upwind_data: pd.DataFrame, 
                         downwind_data: pd.DataFrame,
                         target_vmg: Optional[Dict[str, float]] = None):
        """
        VMG統計情報を表示
        
        Parameters
        ----------
        upwind_data : pd.DataFrame
            風上セグメントのデータ
        downwind_data : pd.DataFrame
            風下セグメントのデータ
        target_vmg : Optional[Dict[str, float]], optional
            目標VMG値, by default None
        """
        # 風上/風下のVMG統計
        upwind_vmg_mean = upwind_data["vmg"].mean() if not upwind_data.empty else np.nan
        downwind_vmg_mean = downwind_data["vmg"].mean() if not downwind_data.empty else np.nan
        
        upwind_vmg_max = upwind_data["vmg"].max() if not upwind_data.empty else np.nan
        downwind_vmg_min = downwind_data["vmg"].min() if not downwind_data.empty else np.nan
        
        # 目標VMGに対するパフォーマンス
        upwind_performance = None
        downwind_performance = None
        
        if target_vmg is not None:
            if "upwind" in target_vmg and not np.isnan(upwind_vmg_mean):
                upwind_performance = (upwind_vmg_mean / target_vmg["upwind"]) * 100
            
            if "downwind" in target_vmg and not np.isnan(downwind_vmg_mean):
                # 風下VMGが負の場合
                if downwind_vmg_mean < 0 and target_vmg["downwind"] < 0:
                    downwind_performance = (downwind_vmg_mean / target_vmg["downwind"]) * 100
                # 風下VMGが正の場合（風下だが値自体は正の場合）
                elif downwind_vmg_mean > 0 and target_vmg["downwind"] > 0:
                    downwind_performance = (downwind_vmg_mean / target_vmg["downwind"]) * 100
        
        # 4列レイアウト
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "平均風上VMG",
                f"{upwind_vmg_mean:.2f} kt" if not np.isnan(upwind_vmg_mean) else "N/A"
            )
        
        with col2:
            st.metric(
                "平均風下VMG",
                f"{downwind_vmg_mean:.2f} kt" if not np.isnan(downwind_vmg_mean) else "N/A"
            )
        
        with col3:
            # 風上パフォーマンス表示
            if upwind_performance is not None:
                delta = f"{upwind_performance - 100:.1f}%" if upwind_performance > 0 else None
                st.metric(
                    "風上目標達成率",
                    f"{upwind_performance:.1f}%",
                    delta=delta
                )
            else:
                st.metric("風上目標達成率", "N/A")
        
        with col4:
            # 風下パフォーマンス表示
            if downwind_performance is not None:
                delta = f"{downwind_performance - 100:.1f}%" if downwind_performance > 0 else None
                st.metric(
                    "風下目標達成率",
                    f"{downwind_performance:.1f}%",
                    delta=delta
                )
            else:
                st.metric("風下目標達成率", "N/A")
