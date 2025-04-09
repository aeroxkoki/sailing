"""
ui.integrated.components.charts.speed_profile_chart

速度プロファイルチャートコンポーネント
時間経過による速度変化を可視化します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

class SpeedProfileChart:
    """速度プロファイルチャートコンポーネント"""
    
    def __init__(self, title: str = "速度プロファイル"):
        """
        初期化
        
        Parameters
        ----------
        title : str, optional
            チャートのタイトル, by default "速度プロファイル"
        """
        self.title = title
        self.options = {
            "show_moving_average": True,
            "moving_average_window": 5,
            "show_target_speed": False,
            "target_speed": None,
            "show_annotations": True,
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
            updated_options["show_moving_average"] = st.checkbox(
                "移動平均を表示", 
                value=self.options["show_moving_average"]
            )
            
            if updated_options["show_moving_average"]:
                updated_options["moving_average_window"] = st.slider(
                    "移動平均ウィンドウ", 
                    min_value=2, 
                    max_value=20, 
                    value=self.options["moving_average_window"]
                )
        
        with col2:
            updated_options["show_target_speed"] = st.checkbox(
                "目標速度を表示", 
                value=self.options["show_target_speed"]
            )
            
            if updated_options["show_target_speed"]:
                updated_options["target_speed"] = st.number_input(
                    "目標速度 (ノット)", 
                    min_value=0.0, 
                    max_value=20.0, 
                    value=self.options.get("target_speed", 6.0),
                    step=0.5
                )
            
            updated_options["show_annotations"] = st.checkbox(
                "注釈を表示", 
                value=self.options["show_annotations"]
            )
        
        return updated_options
    
    def render(self, data: pd.DataFrame, events: Optional[List[Dict[str, Any]]] = None):
        """
        速度プロファイルチャートを描画
        
        Parameters
        ----------
        data : pd.DataFrame
            描画するデータ
            必要なカラム:
            - timestamp: 時間
            - boat_speed: 船速 (ノット)
            - (オプション) vmg: VMG (ノット)
        events : Optional[List[Dict[str, Any]]], optional
            チャート上に表示するイベント情報, by default None
            各イベントは以下のキーを含む辞書:
            - timestamp: イベント発生時刻
            - description: イベントの説明
            - (オプション) type: イベントタイプ
        """
        st.write(f"### {self.title}")
        
        # データの検証
        if data is None or len(data) == 0:
            st.warning("データがありません。")
            return
        
        if "timestamp" not in data.columns:
            st.error("データに 'timestamp' カラムがありません。")
            return
            
        if "boat_speed" not in data.columns:
            st.error("データに 'boat_speed' カラムがありません。")
            return
        
        # 基本グラフの作成
        fig = go.Figure()
        
        # 船速の描画
        fig.add_trace(
            go.Scatter(
                x=data["timestamp"],
                y=data["boat_speed"],
                name="船速 (kt)",
                mode="lines",
                line=dict(color="#1f77b4", width=2)
            )
        )
        
        # VMGがある場合は追加
        if "vmg" in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data["timestamp"],
                    y=data["vmg"],
                    name="VMG (kt)",
                    mode="lines",
                    line=dict(color="#ff7f0e", width=2, dash="dash")
                )
            )
        
        # 移動平均が有効なら追加
        if self.options["show_moving_average"]:
            window = self.options["moving_average_window"]
            data["boat_speed_ma"] = data["boat_speed"].rolling(window=window).mean()
            
            fig.add_trace(
                go.Scatter(
                    x=data["timestamp"],
                    y=data["boat_speed_ma"],
                    name=f"船速 {window}点移動平均",
                    mode="lines",
                    line=dict(color="#2ca02c", width=3)
                )
            )
            
            if "vmg" in data.columns:
                data["vmg_ma"] = data["vmg"].rolling(window=window).mean()
                
                fig.add_trace(
                    go.Scatter(
                        x=data["timestamp"],
                        y=data["vmg_ma"],
                        name=f"VMG {window}点移動平均",
                        mode="lines",
                        line=dict(color="#d62728", width=3, dash="dash")
                    )
                )
        
        # 目標速度が有効なら追加
        if self.options["show_target_speed"] and self.options["target_speed"] is not None:
            target_speed = self.options["target_speed"]
            
            fig.add_trace(
                go.Scatter(
                    x=[data["timestamp"].min(), data["timestamp"].max()],
                    y=[target_speed, target_speed],
                    name=f"目標速度 ({target_speed} kt)",
                    mode="lines",
                    line=dict(color="rgba(128, 0, 128, 0.5)", width=2, dash="dot")
                )
            )
        
        # イベント情報の追加
        if events is not None and len(events) > 0 and self.options["show_annotations"]:
            for event in events:
                if "timestamp" not in event:
                    continue
                
                # イベント時刻の船速を取得
                event_time = event["timestamp"]
                
                # 最も近い時刻のデータポイントを見つける
                closest_idx = (data["timestamp"] - event_time).abs().idxmin()
                event_speed = data.loc[closest_idx, "boat_speed"]
                
                # イベントタイプに応じた色の設定
                event_type = event.get("type", "default")
                if event_type == "tack":
                    color = "rgba(255, 0, 0, 0.7)"
                    symbol = "circle"
                elif event_type == "gybe":
                    color = "rgba(0, 0, 255, 0.7)"
                    symbol = "square"
                elif event_type == "mark_rounding":
                    color = "rgba(128, 0, 128, 0.7)"
                    symbol = "diamond"
                else:
                    color = "rgba(0, 128, 0, 0.7)"
                    symbol = "circle"
                
                # イベントマーカーの追加
                fig.add_trace(
                    go.Scatter(
                        x=[event_time],
                        y=[event_speed],
                        mode="markers",
                        marker=dict(
                            size=10,
                            color=color,
                            symbol=symbol
                        ),
                        name=event.get("description", event_type),
                        text=event.get("description", ""),
                        hoverinfo="text+x+y"
                    )
                )
        
        # レイアウト設定
        fig.update_layout(
            height=self.options["height"],
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis=dict(title="時間"),
            yaxis=dict(title="スピード (ノット)"),
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
        
        # 速度統計情報の表示
        self._render_stats(data)
    
    def _render_stats(self, data: pd.DataFrame):
        """
        速度統計情報を表示
        
        Parameters
        ----------
        data : pd.DataFrame
            描画するデータ
        """
        # 基本統計量
        boat_speed_mean = data["boat_speed"].mean()
        boat_speed_max = data["boat_speed"].max()
        boat_speed_std = data["boat_speed"].std()
        
        # VMGがある場合
        if "vmg" in data.columns:
            vmg_mean = data["vmg"].mean()
            vmg_max = data["vmg"].max()
            # 正のVMGのみの平均（風上パフォーマンス）
            vmg_upwind = data[data["vmg"] > 0]["vmg"].mean()
            # 負のVMGのみの平均（風下パフォーマンス）
            vmg_downwind = abs(data[data["vmg"] < 0]["vmg"].mean())
            
            # 4列レイアウト
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("平均速度", f"{boat_speed_mean:.2f} kt")
            
            with col2:
                st.metric("最高速度", f"{boat_speed_max:.2f} kt")
            
            with col3:
                st.metric("風上VMG平均", f"{vmg_upwind:.2f} kt" if not np.isnan(vmg_upwind) else "N/A")
            
            with col4:
                st.metric("風下VMG平均", f"{vmg_downwind:.2f} kt" if not np.isnan(vmg_downwind) else "N/A")
        
        else:
            # VMGがない場合は2列レイアウト
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("平均速度", f"{boat_speed_mean:.2f} kt")
            
            with col2:
                st.metric("最高速度", f"{boat_speed_max:.2f} kt")
