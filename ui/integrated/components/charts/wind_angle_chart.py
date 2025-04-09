"""
ui.integrated.components.charts.wind_angle_chart

風向角度効率チャートコンポーネント
異なる風向角度における船速やVMGを極座標で可視化します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

class WindAngleChart:
    """風向角度効率チャートコンポーネント"""
    
    def __init__(self, title: str = "風向角度効率"):
        """
        初期化
        
        Parameters
        ----------
        title : str, optional
            チャートのタイトル, by default "風向角度効率"
        """
        self.title = title
        self.options = {
            "show_ideal_curve": False,
            "show_annotations": True,
            "bin_size": 5,  # 風向角度のビンサイズ（度）
            "smooth_curve": True,
            "height": 600
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
            updated_options["show_ideal_curve"] = st.checkbox(
                "理想曲線を表示", 
                value=self.options["show_ideal_curve"]
            )
            
            updated_options["show_annotations"] = st.checkbox(
                "注釈を表示", 
                value=self.options["show_annotations"]
            )
        
        with col2:
            updated_options["bin_size"] = st.select_slider(
                "風向角度のビンサイズ", 
                options=[1, 2, 5, 10, 15, 20],
                value=self.options["bin_size"]
            )
            
            updated_options["smooth_curve"] = st.checkbox(
                "スムーズな曲線", 
                value=self.options["smooth_curve"]
            )
        
        return updated_options
    
    def render(self, data: pd.DataFrame, polar_data: Optional[Dict[str, Any]] = None):
        """
        風向角度効率チャートを描画
        
        Parameters
        ----------
        data : pd.DataFrame
            描画するデータ
            必要なカラム:
            - wind_angle: 風向角度（船の進行方向に対する相対角度、0-180度）
            - boat_speed: 船速 (ノット)
            - (オプション) vmg: VMG (ノット)
        polar_data : Optional[Dict[str, Any]], optional
            極図データ（理想的な性能曲線）, by default None
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
        
        # 風向角度を区間（ビン）に分類
        bin_size = self.options["bin_size"]
        bins = list(range(0, 181, bin_size))
        labels = [f"{b}" for b in bins]
        
        data["angle_bin"] = pd.cut(
            data["wind_angle"], 
            bins=bins + [180 + bin_size], 
            labels=labels,
            include_lowest=True
        )
        
        # 各ビンごとの平均速度を計算
        angle_speed = data.groupby("angle_bin").agg(
            boat_speed_mean=("boat_speed", "mean"),
            boat_speed_max=("boat_speed", "max"),
            boat_speed_count=("boat_speed", "count"),
            vmg_mean=("vmg", "mean") if "vmg" in data.columns else (None, None)
        ).reset_index()
        
        # 角度を数値に変換
        angle_speed["angle"] = angle_speed["angle_bin"].astype(float)
        
        # 極座標チャートの作成
        fig = go.Figure()
        
        # スムーズな曲線を描画するか
        if self.options["smooth_curve"]:
            # 船速の極座標プロット（スムーズ曲線）
            interpolated_angles = np.linspace(0, 180, 100)
            interpolated_speeds = np.interp(
                interpolated_angles, 
                angle_speed["angle"], 
                angle_speed["boat_speed_mean"]
            )
            
            r_values = interpolated_speeds
            theta_values = np.radians(interpolated_angles)
            
            # プロット用の座標変換
            x_values = r_values * np.cos(theta_values)
            y_values = r_values * np.sin(theta_values)
            
            # 全周に拡張（左右対称）
            x_all = np.concatenate([x_values, -x_values])
            y_all = np.concatenate([y_values, y_values])
            
            fig.add_trace(
                go.Scatter(
                    x=x_all, 
                    y=y_all,
                    mode="lines",
                    line=dict(color="blue", width=3),
                    name="平均船速"
                )
            )
            
            # VMGがある場合はVMGの極座標も描画
            if "vmg_mean" in angle_speed.columns and not angle_speed["vmg_mean"].isna().all():
                interpolated_vmg = np.interp(
                    interpolated_angles, 
                    angle_speed["angle"], 
                    angle_speed["vmg_mean"]
                )
                
                r_values_vmg = interpolated_vmg
                
                # プロット用の座標変換
                x_values_vmg = r_values_vmg * np.cos(theta_values)
                y_values_vmg = r_values_vmg * np.sin(theta_values)
                
                # 全周に拡張（左右対称）
                x_all_vmg = np.concatenate([x_values_vmg, -x_values_vmg])
                y_all_vmg = np.concatenate([y_values_vmg, y_values_vmg])
                
                fig.add_trace(
                    go.Scatter(
                        x=x_all_vmg, 
                        y=y_all_vmg,
                        mode="lines",
                        line=dict(color="red", width=3, dash="dash"),
                        name="平均VMG"
                    )
                )
            
        else:
            # 船速の極座標プロット（ポイント＋折れ線）
            theta_values = np.radians(angle_speed["angle"])
            r_values = angle_speed["boat_speed_mean"]
            
            # プロット用の座標変換
            x_values = r_values * np.cos(theta_values)
            y_values = r_values * np.sin(theta_values)
            
            # 全周に拡張（左右対称）
            x_all = np.concatenate([x_values, -x_values])
            y_all = np.concatenate([y_values, y_values])
            
            fig.add_trace(
                go.Scatter(
                    x=x_all, 
                    y=y_all,
                    mode="lines+markers",
                    line=dict(color="blue", width=2),
                    marker=dict(size=8, color="blue"),
                    name="平均船速"
                )
            )
            
            # VMGがある場合はVMGの極座標も描画
            if "vmg_mean" in angle_speed.columns and not angle_speed["vmg_mean"].isna().all():
                r_values_vmg = angle_speed["vmg_mean"]
                
                # プロット用の座標変換
                x_values_vmg = r_values_vmg * np.cos(theta_values)
                y_values_vmg = r_values_vmg * np.sin(theta_values)
                
                # 全周に拡張（左右対称）
                x_all_vmg = np.concatenate([x_values_vmg, -x_values_vmg])
                y_all_vmg = np.concatenate([y_values_vmg, y_values_vmg])
                
                fig.add_trace(
                    go.Scatter(
                        x=x_all_vmg, 
                        y=y_all_vmg,
                        mode="lines+markers",
                        line=dict(color="red", width=2, dash="dash"),
                        marker=dict(size=8, color="red"),
                        name="平均VMG"
                    )
                )
        
        # 理想曲線の追加
        if self.options["show_ideal_curve"] and polar_data is not None:
            try:
                # 極図データから理想的な性能曲線を描画
                if "angles" in polar_data and "speeds" in polar_data:
                    ideal_angles = np.array(polar_data["angles"])
                    ideal_speeds = np.array(polar_data["speeds"])
                    
                    # ラジアンに変換
                    ideal_theta = np.radians(ideal_angles)
                    
                    # 座標変換
                    ideal_x = ideal_speeds * np.cos(ideal_theta)
                    ideal_y = ideal_speeds * np.sin(ideal_theta)
                    
                    # 全周に拡張（左右対称）
                    ideal_x_all = np.concatenate([ideal_x, -ideal_x])
                    ideal_y_all = np.concatenate([ideal_y, ideal_y])
                    
                    fig.add_trace(
                        go.Scatter(
                            x=ideal_x_all, 
                            y=ideal_y_all,
                            mode="lines",
                            line=dict(color="green", width=2, dash="dot"),
                            name="理想性能曲線"
                        )
                    )
            except Exception as e:
                st.warning(f"理想曲線の描画に失敗しました: {e}")
        
        # 注釈の追加
        if self.options["show_annotations"]:
            # 風向角度のティック線
            for angle in [0, 30, 60, 90, 120, 150, 180]:
                angle_rad = np.radians(angle)
                x_start, y_start = 0, 0
                x_end = 15 * np.cos(angle_rad)  # グラフの最大スケールに合わせて調整
                y_end = 15 * np.sin(angle_rad)
                
                fig.add_trace(
                    go.Scatter(
                        x=[x_start, x_end, -x_end], 
                        y=[y_start, y_end, y_end],
                        mode="lines",
                        line=dict(color="gray", width=1, dash="dot"),
                        showlegend=False
                    )
                )
                
                # 角度ラベル
                if angle > 0:  # 0度は原点と重なるため除外
                    fig.add_annotation(
                        x=x_end * 1.1,
                        y=y_end * 1.1,
                        text=f"{angle}°",
                        showarrow=False,
                        font=dict(size=10)
                    )
                    
                    # 対称側にも表示
                    fig.add_annotation(
                        x=-x_end * 1.1,
                        y=y_end * 1.1,
                        text=f"{angle}°",
                        showarrow=False,
                        font=dict(size=10)
                    )
            
            # 最適なVMG角度を見つける（もしVMGデータがあれば）
            if "vmg_mean" in angle_speed.columns and not angle_speed["vmg_mean"].isna().all():
                # 風上の最適VMG（正のVMG）
                upwind_data = angle_speed[angle_speed["vmg_mean"] > 0]
                if not upwind_data.empty:
                    best_upwind_idx = upwind_data["vmg_mean"].idxmax()
                    best_upwind_angle = upwind_data.loc[best_upwind_idx, "angle"]
                    best_upwind_vmg = upwind_data.loc[best_upwind_idx, "vmg_mean"]
                    best_upwind_speed = upwind_data.loc[best_upwind_idx, "boat_speed_mean"]
                    
                    # 最適風上VMG角度の注釈
                    angle_rad = np.radians(best_upwind_angle)
                    x_point = best_upwind_speed * np.cos(angle_rad)
                    y_point = best_upwind_speed * np.sin(angle_rad)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=[x_point, -x_point], 
                            y=[y_point, y_point],
                            mode="markers",
                            marker=dict(size=10, color="green", symbol="star"),
                            name="最適風上VMG角度",
                            text=[f"風上最適VMG: {best_upwind_angle:.1f}°", f"風上最適VMG: {best_upwind_angle:.1f}°"],
                            hoverinfo="text+name"
                        )
                    )
                
                # 風下の最適VMG（負のVMG）
                downwind_data = angle_speed[angle_speed["vmg_mean"] < 0]
                if not downwind_data.empty:
                    best_downwind_idx = downwind_data["vmg_mean"].idxmin()  # 最小の負のVMG
                    best_downwind_angle = downwind_data.loc[best_downwind_idx, "angle"]
                    best_downwind_vmg = downwind_data.loc[best_downwind_idx, "vmg_mean"]
                    best_downwind_speed = downwind_data.loc[best_downwind_idx, "boat_speed_mean"]
                    
                    # 最適風下VMG角度の注釈
                    angle_rad = np.radians(best_downwind_angle)
                    x_point = best_downwind_speed * np.cos(angle_rad)
                    y_point = best_downwind_speed * np.sin(angle_rad)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=[x_point, -x_point], 
                            y=[y_point, y_point],
                            mode="markers",
                            marker=dict(size=10, color="purple", symbol="star"),
                            name="最適風下VMG角度",
                            text=[f"風下最適VMG: {best_downwind_angle:.1f}°", f"風下最適VMG: {best_downwind_angle:.1f}°"],
                            hoverinfo="text+name"
                        )
                    )
        
        # レイアウト設定
        fig.update_layout(
            height=self.options["height"],
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode="closest",
            # 極座標のような外観に設定
            xaxis=dict(
                title="",
                zeroline=True,
                showgrid=True,
                range=[-15, 15],  # チャートのスケールを調整
                showticklabels=False,
                scaleanchor="y",
                scaleratio=1  # アスペクト比を固定
            ),
            yaxis=dict(
                title="",
                zeroline=True,
                showgrid=True,
                range=[0, 15],  # チャートのスケールを調整
                showticklabels=False
            ),
            shapes=[
                # 原点を中心とする円を描画してスケールを示す
                {
                    "type": "circle",
                    "xref": "x",
                    "yref": "y",
                    "x0": -5,
                    "y0": -5,
                    "x1": 5,
                    "y1": 5,
                    "line": {
                        "color": "lightgray",
                        "width": 1,
                        "dash": "dot"
                    }
                },
                {
                    "type": "circle",
                    "xref": "x",
                    "yref": "y",
                    "x0": -10,
                    "y0": -10,
                    "x1": 10,
                    "y1": 10,
                    "line": {
                        "color": "lightgray",
                        "width": 1,
                        "dash": "dot"
                    }
                }
            ]
        )
        
        # スケール表示
        fig.add_annotation(
            x=0,
            y=5,
            text="5 kt",
            showarrow=False,
            font=dict(size=10)
        )
        fig.add_annotation(
            x=0,
            y=10,
            text="10 kt",
            showarrow=False,
            font=dict(size=10)
        )
        
        # チャートの表示
        st.plotly_chart(fig, use_container_width=True)
        
        # 角度効率の統計情報の表示
        self._render_angle_stats(angle_speed)
    
    def _render_angle_stats(self, angle_speed: pd.DataFrame):
        """
        角度効率の統計情報を表示
        
        Parameters
        ----------
        angle_speed : pd.DataFrame
            風向角度別の速度データ
        """
        # 最大速度とその角度を取得
        if "boat_speed_mean" in angle_speed.columns:
            max_speed_idx = angle_speed["boat_speed_mean"].idxmax()
            max_speed = angle_speed.loc[max_speed_idx, "boat_speed_mean"]
            max_speed_angle = angle_speed.loc[max_speed_idx, "angle"]
            
            # VMGデータがある場合
            if "vmg_mean" in angle_speed.columns and not angle_speed["vmg_mean"].isna().all():
                # 風上の最適VMG（正のVMG）
                upwind_data = angle_speed[angle_speed["vmg_mean"] > 0]
                downwind_data = angle_speed[angle_speed["vmg_mean"] < 0]
                
                if not upwind_data.empty:
                    best_upwind_idx = upwind_data["vmg_mean"].idxmax()
                    best_upwind_angle = upwind_data.loc[best_upwind_idx, "angle"]
                    best_upwind_vmg = upwind_data.loc[best_upwind_idx, "vmg_mean"]
                    
                    # 風下の最適VMG（負のVMG）
                    if not downwind_data.empty:
                        best_downwind_idx = downwind_data["vmg_mean"].idxmin()  # 最小の負のVMG
                        best_downwind_angle = downwind_data.loc[best_downwind_idx, "angle"]
                        best_downwind_vmg = abs(downwind_data.loc[best_downwind_idx, "vmg_mean"])
                        
                        # 4列レイアウト
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("最高速度", f"{max_speed:.2f} kt")
                        
                        with col2:
                            st.metric("最高速度角度", f"{max_speed_angle:.1f}°")
                        
                        with col3:
                            st.metric("最適風上角度", f"{best_upwind_angle:.1f}°")
                        
                        with col4:
                            st.metric("最適風下角度", f"{best_downwind_angle:.1f}°")
                        
                        return
            
            # VMGデータがない場合は2列レイアウト
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("最高速度", f"{max_speed:.2f} kt")
            
            with col2:
                st.metric("最高速度角度", f"{max_speed_angle:.1f}°")
