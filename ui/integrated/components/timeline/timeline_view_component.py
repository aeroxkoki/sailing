# -*- coding: utf-8 -*-
"""
ui.integrated.components.timeline.timeline_view_component

時間軸可視化コンポーネント
時間経過に沿ったイベントやパラメータの変化を表示します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

class TimelineViewComponent:
    """時間軸可視化コンポーネント"""
    
    def __init__(self, title: str = "時間軸分析"):
        """
        初期化
        
        Parameters
        ----------
        title : str, optional
            コンポーネントのタイトル, by default "時間軸分析"
        """
        self.title = title
        self.options = {
            "show_events": True,  # イベントの表示・非表示
            "show_parameters": True,  # パラメータの表示・非表示
            "parameter_count": 3,  # 表示するパラメータの数
            "highlight_markers": True,  # マーカーの強調表示
            "auto_play": False,  # 自動再生
            "play_speed": 1.0,  # 再生速度
            "height": 400,  # チャートの高さ
            "selected_time": None  # 選択された時刻
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
    
    def render_controls(self, events: pd.DataFrame = None, time_range: Tuple[datetime, datetime] = None):
        """
        コントロールパネルを描画
        
        Parameters
        ----------
        events : pd.DataFrame, optional
            イベントデータ, by default None
        time_range : Tuple[datetime, datetime], optional
            時間範囲, by default None
        
        Returns
        -------
        Dict[str, Any]
            更新されたオプション
        """
        # オプションのコピーを作成
        updated_options = self.options.copy()
        
        # タイムラインコントロール
        st.subheader("時間コントロール")
        
        # 表示オプション
        col1, col2 = st.columns(2)
        
        with col1:
            updated_options["show_events"] = st.checkbox(
                "イベントを表示", 
                value=self.options["show_events"]
            )
            
            updated_options["highlight_markers"] = st.checkbox(
                "マーカーを強調表示", 
                value=self.options["highlight_markers"]
            )
        
        with col2:
            updated_options["show_parameters"] = st.checkbox(
                "パラメータを表示", 
                value=self.options["show_parameters"]
            )
            
            if updated_options["show_parameters"]:
                updated_options["parameter_count"] = st.slider(
                    "表示パラメータ数", 
                    min_value=1, 
                    max_value=5, 
                    value=self.options["parameter_count"]
                )
        
        # 時間操作コントロール
        st.subheader("時間操作")
        
        col3, col4, col5 = st.columns([1, 2, 1])
        
        with col3:
            updated_options["auto_play"] = st.checkbox(
                "自動再生", 
                value=self.options["auto_play"]
            )
        
        with col4:
            if updated_options["auto_play"]:
                updated_options["play_speed"] = st.slider(
                    "再生速度", 
                    min_value=0.25, 
                    max_value=2.0, 
                    value=self.options["play_speed"],
                    step=0.25
                )
        
        with col5:
            if st.button("リセット", use_container_width=True):
                updated_options["selected_time"] = None
        
        # 時間範囲があれば時間選択スライダーを表示
        if time_range is not None:
            start_time, end_time = time_range
            
            # 時間選択スライダー
            time_values = pd.date_range(start=start_time, end=end_time, periods=100)
            
            if updated_options["selected_time"] is None or updated_options["selected_time"] not in time_values:
                updated_options["selected_time"] = start_time
            
            # スライダー用のインデックス
            current_index = 0
            if updated_options["selected_time"] is not None:
                closest_idx = np.abs(time_values - updated_options["selected_time"]).argmin()
                current_index = closest_idx
            
            selected_index = st.slider(
                "時間選択", 
                min_value=0, 
                max_value=len(time_values) - 1,
                value=current_index
            )
            
            selected_time = time_values[selected_index]
            updated_options["selected_time"] = selected_time
            
            st.write(f"選択時間: {selected_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # イベントフィルター
        if events is not None and not events.empty and "type" in events.columns:
            unique_types = events["type"].unique().tolist()
            
            if unique_types:
                st.subheader("イベントフィルター")
                
                selected_types = st.multiselect(
                    "表示するイベントタイプ",
                    options=unique_types,
                    default=unique_types
                )
                
                updated_options["event_filter"] = selected_types
        
        return updated_options
    
    def render(self, 
               time_series_data: pd.DataFrame, 
               events: Optional[pd.DataFrame] = None):
        """
        タイムラインビューを描画
        
        Parameters
        ----------
        time_series_data : pd.DataFrame
            時系列データ
            必要なカラム:
            - timestamp: 時間
            - その他の数値パラメータ
        events : Optional[pd.DataFrame], optional
            イベントデータ, by default None
            必要なカラム:
            - timestamp: イベント発生時刻
            - description: イベントの説明
            - type: イベントタイプ
        """
        st.markdown(f"### {self.title}")
        
        # データの検証
        if time_series_data is None or len(time_series_data) == 0:
            st.warning("時系列データがありません。")
            return
        
        if "timestamp" not in time_series_data.columns:
            st.error("時系列データに 'timestamp' カラムがありません。")
            return
        
        # 時間範囲
        time_range = (time_series_data["timestamp"].min(), time_series_data["timestamp"].max())
        
        # 時間軸コントロールを表示（エクスパンダー内）
        with st.expander("時間軸コントロール", expanded=True):
            # コントロールの表示
            updated_options = self.render_controls(events, time_range)
            
            # オプションの更新
            self.update_options(updated_options)
        
        # 現在の表示時刻
        selected_time = self.options["selected_time"]
        if selected_time is None:
            selected_time = time_series_data["timestamp"].min()
        
        # タイムライン表示（時間vs数値パラメータ）
        if self.options["show_parameters"]:
            self._render_parameters_timeline(time_series_data, selected_time)
        
        # イベントタイムライン表示
        if self.options["show_events"] and events is not None:
            self._render_events_timeline(events, selected_time)
        
        # 現在時点の詳細情報
        self._render_current_details(time_series_data, events, selected_time)
    
    def _render_parameters_timeline(self, time_series_data: pd.DataFrame, selected_time: datetime):
        """
        数値パラメータのタイムライン表示
        
        Parameters
        ----------
        time_series_data : pd.DataFrame
            時系列データ
        selected_time : datetime
            選択された時刻
        """
        # 数値パラメータのカラム
        numeric_columns = time_series_data.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_columns:
            st.warning("表示可能な数値パラメータがありません。")
            return
        
        # パラメータ数を表示可能な範囲に制限
        parameter_count = min(self.options["parameter_count"], len(numeric_columns))
        selected_params = numeric_columns[:parameter_count]
        
        # プロットの作成
        fig = go.Figure()
        
        # 各パラメータをプロット
        for i, param in enumerate(selected_params):
            fig.add_trace(
                go.Scatter(
                    x=time_series_data["timestamp"],
                    y=time_series_data[param],
                    name=param,
                    mode="lines",
                    line=dict(width=2)
                )
            )
        
        # 選択時刻の垂直線を追加
        if selected_time is not None:
            fig.add_vline(
                x=selected_time,
                line_dash="dash",
                line_width=2,
                line_color="rgba(0, 0, 0, 0.5)"
            )
            
            # 選択時刻のマーカーを追加
            for i, param in enumerate(selected_params):
                # 最も近い時刻のデータポイントを取得
                closest_idx = (time_series_data["timestamp"] - selected_time).abs().idxmin()
                closest_value = time_series_data.loc[closest_idx, param]
                
                fig.add_trace(
                    go.Scatter(
                        x=[selected_time],
                        y=[closest_value],
                        mode="markers",
                        marker=dict(size=10, color="black"),
                        name=f"現在値 - {param}",
                        showlegend=False
                    )
                )
        
        # レイアウト設定
        fig.update_layout(
            height=self.options["height"],
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(title="時間"),
            yaxis=dict(title="パラメータ値"),
            hovermode="x unified"
        )
        
        # チャートの表示
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_events_timeline(self, events: pd.DataFrame, selected_time: datetime):
        """
        イベントタイムラインの表示
        
        Parameters
        ----------
        events : pd.DataFrame
            イベントデータ
        selected_time : datetime
            選択された時刻
        """
        if events is None or events.empty:
            st.info("イベントデータがありません。")
            return
        
        if "timestamp" not in events.columns:
            st.error("イベントデータに 'timestamp' カラムがありません。")
            return
        
        # イベント表示のコンテナ
        st.markdown("#### イベントタイムライン")
        
        # イベントタイプでフィルタリング
        if "event_filter" in self.options and "type" in events.columns:
            events = events[events["type"].isin(self.options["event_filter"])]
        
        if events.empty:
            st.info("表示するイベントがありません。")
            return
        
        # 時間でソート
        events = events.sort_values("timestamp")
        
        # プロットの作成
        fig = go.Figure()
        
        # イベントタイプごとに異なる色を設定
        type_colors = {}
        if "type" in events.columns:
            unique_types = events["type"].unique()
            colorscale = px.colors.qualitative.Plotly
            for i, event_type in enumerate(unique_types):
                type_colors[event_type] = colorscale[i % len(colorscale)]
        
        # イベントマーカーの表示
        for i, row in events.iterrows():
            event_time = row["timestamp"]
            event_type = row.get("type", "イベント")
            description = row.get("description", event_type)
            
            # イベントタイプに応じた色
            color = type_colors.get(event_type, "blue")
            
            # イベント発生時刻にマーカーを配置
            fig.add_trace(
                go.Scatter(
                    x=[event_time],
                    y=[0],  # Y座標は一定（タイムライン上）
                    mode="markers",
                    marker=dict(
                        size=12,
                        color=color,
                        symbol="diamond"
                    ),
                    name=event_type,
                    text=description,
                    hoverinfo="text+x"
                )
            )
            
            # 選択時刻に近いイベントを強調表示
            if selected_time is not None and self.options["highlight_markers"]:
                # 選択時刻の前後5分以内のイベントを強調
                time_diff = abs((event_time - selected_time).total_seconds())
                if time_diff < 300:  # 5分 = 300秒
                    fig.add_trace(
                        go.Scatter(
                            x=[event_time],
                            y=[0],
                            mode="markers",
                            marker=dict(
                                size=16,
                                color=color,
                                symbol="diamond",
                                line=dict(width=2, color="black")
                            ),
                            showlegend=False,
                            hoverinfo="none"
                        )
                    )
        
        # 選択時刻の垂直線を追加
        if selected_time is not None:
            fig.add_vline(
                x=selected_time,
                line_dash="dash",
                line_width=2,
                line_color="rgba(0, 0, 0, 0.5)"
            )
        
        # レイアウト設定
        fig.update_layout(
            height=150,
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(title="時間"),
            yaxis=dict(
                visible=False,
                showticklabels=False,
                range=[-1, 1]
            ),
            hovermode="closest"
        )
        
        # チャートの表示
        st.plotly_chart(fig, use_container_width=True)
        
        # イベントリスト表示（時間順）
        with st.expander("イベントリスト", expanded=False):
            # イベントデータのテーブル形式での表示
            events_display = events.copy()
            
            # 表示用にカラムを整形
            if "timestamp" in events_display.columns:
                events_display["時刻"] = events_display["timestamp"].dt.strftime("%H:%M:%S")
            
            if "type" in events_display.columns:
                events_display["タイプ"] = events_display["type"]
            
            if "description" in events_display.columns:
                events_display["説明"] = events_display["description"]
            
            # 表示するカラムを選択
            display_columns = ["時刻", "タイプ", "説明"]
            display_columns = [col for col in display_columns if col in events_display.columns]
            
            # テーブル表示
            if display_columns:
                st.dataframe(events_display[display_columns], use_container_width=True)
            else:
                st.warning("表示するイベント情報がありません。")
    
    def _render_current_details(self, time_series_data: pd.DataFrame, 
                               events: Optional[pd.DataFrame], 
                               selected_time: datetime):
        """
        現在時点の詳細情報を表示
        
        Parameters
        ----------
        time_series_data : pd.DataFrame
            時系列データ
        events : Optional[pd.DataFrame]
            イベントデータ
        selected_time : datetime
            選択された時刻
        """
        st.markdown("#### 現在時点の詳細情報")
        
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### パラメータ値")
            
            # 最も近い時刻のデータポイントを取得
            if not time_series_data.empty and "timestamp" in time_series_data.columns:
                closest_idx = (time_series_data["timestamp"] - selected_time).abs().idxmin()
                closest_row = time_series_data.loc[closest_idx]
                
                # 数値パラメータのみを表示
                numeric_data = closest_row.select_dtypes(include=[np.number])
                
                # パラメータ値をメトリクスとして表示
                for col, value in numeric_data.items():
                    st.metric(col, f"{value:.2f}")
            else:
                st.info("表示できるパラメータがありません。")
        
        with col2:
            st.markdown("##### 近隣イベント")
            
            # 選択時点の近くのイベントを表示
            if events is not None and not events.empty and "timestamp" in events.columns:
                # 選択時刻前後10分のイベントをフィルタリング
                time_range = 600  # 10分 = 600秒
                
                # 時間差を計算
                events["time_diff"] = (events["timestamp"] - selected_time).dt.total_seconds().abs()
                
                # 近いイベントをフィルタリング
                nearby_events = events[events["time_diff"] <= time_range].sort_values("time_diff")
                
                if not nearby_events.empty:
                    for i, row in nearby_events.iterrows():
                        with st.container():
                            event_time = row["timestamp"]
                            event_type = row.get("type", "イベント")
                            description = row.get("description", event_type)
                            
                            # 時間差を計算
                            time_diff = (event_time - selected_time).total_seconds()
                            
                            if time_diff < 0:
                                time_label = f"{abs(time_diff):.0f}秒前"
                            elif time_diff > 0:
                                time_label = f"{time_diff:.0f}秒後"
                            else:
                                time_label = "現在"
                            
                            st.markdown(f"**{event_type}** ({time_label}): {description}")
                else:
                    st.info("近隣イベントはありません。")
            else:
                st.info("表示できるイベントがありません。")
