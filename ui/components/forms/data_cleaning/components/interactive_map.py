"""
ui.components.forms.data_cleaning.components.interactive_map

問題箇所をハイライト表示するインタラクティブなマップコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
import plotly.express as px
import plotly.graph_objects as go


class InteractiveMap:
    """
    問題箇所をハイライト表示するインタラクティブなマップコンポーネント
    
    Parameters
    ----------
    data : pd.DataFrame
        マップ表示するデータフレーム
    problem_indices : Dict[str, List[int]]
        問題タイプごとのインデックスリスト
    on_select : Callable[[List[int]], None], optional
        エリア選択時のコールバック関数
    key : str, optional
        コンポーネントのキー, by default "interactive_map"
    """
    
    def __init__(self, 
                data: pd.DataFrame, 
                problem_indices: Dict[str, List[int]],
                on_select: Callable[[List[int]], None] = None,
                key: str = "interactive_map"):
        """
        初期化
        
        Parameters
        ----------
        data : pd.DataFrame
            マップ表示するデータフレーム
        problem_indices : Dict[str, List[int]]
            問題タイプごとのインデックスリスト
        on_select : Callable[[List[int]], None], optional
            エリア選択時のコールバック関数
        key : str, optional
            コンポーネントのキー, by default "interactive_map"
        """
        self.data = data
        self.problem_indices = problem_indices
        self.on_select = on_select
        self.key = key
        
        # 位置情報カラムのチェック
        self.has_location_data = "latitude" in data.columns and "longitude" in data.columns
        
        # 問題タイプの日本語表示名
        self.problem_type_names = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複データ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        }
        
        # 問題タイプの色
        self.problem_type_colors = {
            "missing_data": "blue",
            "out_of_range": "red",
            "duplicates": "green",
            "spatial_anomalies": "purple",
            "temporal_anomalies": "orange"
        }
        
        # 重要度の色
        self.severity_colors = {
            "error": "#f44336",   # 赤
            "warning": "#ff9800", # オレンジ
            "info": "#2196f3"     # 青
        }
        
        # マップのデフォルト設定
        self.default_zoom = 11
        
        # セッション状態の初期化
        if f"{self.key}_selected_area" not in st.session_state:
            st.session_state[f"{self.key}_selected_area"] = None
        
        if f"{self.key}_selected_points" not in st.session_state:
            st.session_state[f"{self.key}_selected_points"] = []
        
        if f"{self.key}_map_type" not in st.session_state:
            st.session_state[f"{self.key}_map_type"] = "散布図"
        
        if f"{self.key}_filtered_problem_type" not in st.session_state:
            st.session_state[f"{self.key}_filtered_problem_type"] = "all"
    
    def render(self) -> Dict[str, Any]:
        """
        インタラクティブマップを表示
        
        Returns
        -------
        Dict[str, Any]
            選択状態などの情報
        """
        if not self.has_location_data:
            st.warning("位置情報（緯度・経度）がデータ内にありません。マップ表示には latitude と longitude カラムが必要です。")
            return {"status": "no_location_data"}
        
        # マップ表示のコントロールを表示
        self._render_map_controls()
        
        # 選択されたマップタイプでマップを表示
        map_type = st.session_state[f"{self.key}_map_type"]
        
        if map_type == "散布図":
            fig = self._create_scatter_map()
        elif map_type == "ヒートマップ":
            fig = self._create_heat_map()
        elif map_type == "詳細マップ":
            fig = self._create_detailed_map()
        
        # マップ表示
        st.plotly_chart(fig, use_container_width=True)
        
        # 問題サマリー情報の表示（問題の分布や傾向を視覚的に把握できるよう）
        self._render_problem_summary()
        
        # セレクタコントロール
        self._render_selector_controls()
        
        # 選択されたポイントの情報を表示
        selected_points = st.session_state.get(f"{self.key}_selected_points", [])
        
        if selected_points:
            self._render_selected_points_info(selected_points)
        
        # 選択状態を返す
        return {
            "status": "rendered",
            "selected_area": st.session_state.get(f"{self.key}_selected_area"),
            "selected_points": selected_points,
            "map_type": map_type,
            "filtered_problem_type": st.session_state.get(f"{self.key}_filtered_problem_type")
        }
    
    def _render_map_controls(self):
        """
        マップ表示のコントロールを表示
        """
        st.subheader("インタラクティブマップ")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # マップタイプの選択
            map_types = ["散布図", "ヒートマップ", "詳細マップ"]
            
            map_type = st.radio(
                "マップタイプ:",
                options=map_types,
                index=map_types.index(st.session_state[f"{self.key}_map_type"]) if st.session_state[f"{self.key}_map_type"] in map_types else 0,
                horizontal=True,
                key=f"{self.key}_map_type_selector"
            )
            
            st.session_state[f"{self.key}_map_type"] = map_type
        
        with col2:
            # 問題タイプのフィルタリング
            problem_types = ["all"] + list(self.problem_type_names.keys())
            problem_type_labels = ["すべての問題"] + [self.problem_type_names[pt] for pt in self.problem_type_names]
            
            # 問題タイプマッピング
            type_mapping = {label: key for key, label in zip(problem_types, problem_type_labels)}
            
            selected_type_label = st.selectbox(
                "表示する問題タイプ:",
                options=problem_type_labels,
                index=problem_types.index(st.session_state[f"{self.key}_filtered_problem_type"]) if st.session_state[f"{self.key}_filtered_problem_type"] in problem_types else 0,
                key=f"{self.key}_problem_type_filter"
            )
            
            # 選択された問題タイプを保存
            selected_type = type_mapping.get(selected_type_label, "all")
            st.session_state[f"{self.key}_filtered_problem_type"] = selected_type
    
    def _render_selector_controls(self):
        """
        選択コントロールを表示
        """
        # 選択モードのコントロール
        col1, col2 = st.columns(2)
        
        with col1:
            # 領域選択のコントロール
            st.write("**領域選択**")
            st.write("マップ上でドラッグして領域を選択できます。")
            
            if st.button("選択領域をクリア", key=f"{self.key}_clear_area_btn"):
                st.session_state[f"{self.key}_selected_area"] = None
                st.session_state[f"{self.key}_selected_points"] = []
                st.experimental_rerun()
        
        with col2:
            # ポイント選択のコントロール
            st.write("**ポイント選択**")
            st.write("問題ポイントをクリックして選択できます。")
            
            if st.button("選択ポイントをクリア", key=f"{self.key}_clear_points_btn"):
                st.session_state[f"{self.key}_selected_points"] = []
                st.experimental_rerun()
    
    def _render_selected_points_info(self, selected_points: List[int]):
        """
        選択されたポイントの情報を表示
        
        Parameters
        ----------
        selected_points : List[int]
            選択されたポイントのインデックスリスト
        """
        st.subheader("選択されたポイント")
        st.write(f"{len(selected_points)} ポイントが選択されています")
        
        # 選択されたポイントの情報を表として表示
        selected_data = []
        
        for idx in selected_points:
            if idx < len(self.data):
                row = self.data.iloc[idx]
                point_info = {"インデックス": idx}
                
                # タイムスタンプがあれば追加
                if "timestamp" in row:
                    point_info["タイムスタンプ"] = row["timestamp"]
                
                # 位置情報を追加
                if "latitude" in row and "longitude" in row:
                    point_info["緯度"] = row["latitude"]
                    point_info["経度"] = row["longitude"]
                
                # 速度があれば追加
                if "speed" in row:
                    point_info["速度"] = row["speed"]
                
                # 問題タイプを追加
                problem_types = []
                for pt, indices in self.problem_indices.items():
                    if pt != "all" and idx in indices:
                        problem_types.append(self.problem_type_names[pt])
                
                point_info["問題タイプ"] = ", ".join(problem_types) if problem_types else "なし"
                
                selected_data.append(point_info)
        
        if selected_data:
            selected_df = pd.DataFrame(selected_data)
            st.dataframe(selected_df, use_container_width=True)
            
            # ポイントに対するアクション
            st.write("**選択ポイントに対するアクション**")
            
            action = st.selectbox(
                "アクション:",
                options=["アクションを選択...", "選択ポイントを表示", "問題詳細を表示", "選択ポイントを修正"],
                key=f"{self.key}_point_action"
            )
            
            if action == "選択ポイントを表示":
                # ポイントを地図上で表示（すでに表示されている）
                st.info("選択したポイントはすでにマップ上でハイライト表示されています。")
            
            elif action == "問題詳細を表示":
                # 問題詳細を表示するためのコールバックを呼び出し
                if self.on_select:
                    self.on_select(selected_points)
            
            elif action == "選択ポイントを修正":
                st.info("修正機能は別のタブで提供されています。「修正提案」タブを確認してください。")
    
    def _create_scatter_map(self) -> go.Figure:
        """
        散布図形式のマップを作成
        
        Returns
        -------
        go.Figure
            散布図マップ
        """
        # フィルタリングされた問題インデックスの取得
        filtered_indices = self._get_filtered_indices()
        
        # マップの作成
        fig = go.Figure()
        
        # 通常のトラックの線を追加
        fig.add_trace(go.Scattermapbox(
            lat=self.data["latitude"],
            lon=self.data["longitude"],
            mode="lines",
            line=dict(width=2, color="blue", opacity=0.5),
            name="トラック",
            hoverinfo="none"
        ))
        
        # 問題ポイントを問題タイプごとに追加
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                # フィルタリングとの交差
                problem_indices = list(set(indices) & set(filtered_indices))
                
                if problem_indices:
                    problem_df = self.data.iloc[problem_indices]
                    
                    # 問題の詳細情報を作成
                    hover_texts = []
                    for idx in problem_indices:
                        if idx < len(self.data):
                            row = self.data.iloc[idx]
                            
                            text = f"インデックス: {idx}<br>"
                            text += f"問題タイプ: {self.problem_type_names.get(problem_type, problem_type)}<br>"
                            
                            if "timestamp" in row:
                                text += f"タイムスタンプ: {row['timestamp']}<br>"
                            
                            if "speed" in row:
                                text += f"速度: {row['speed']:.2f}<br>"
                            
                            hover_texts.append(text)
                    
                    # マーカーのスタイル
                    marker_style = dict(
                        size=10,
                        color=self.problem_type_colors.get(problem_type, "red"),
                        symbol="circle"
                    )
                    
                    # 選択されたポイントがあれば、それを特定
                    selected_points = st.session_state.get(f"{self.key}_selected_points", [])
                    
                    # 問題ポイントを追加
                    fig.add_trace(go.Scattermapbox(
                        lat=problem_df["latitude"],
                        lon=problem_df["longitude"],
                        mode="markers",
                        marker=marker_style,
                        name=self.problem_type_names.get(problem_type, problem_type),
                        hoverinfo="text",
                        hovertext=hover_texts,
                        customdata=problem_indices,
                        selected=dict(marker=dict(size=15, color="yellow"))
                    ))
        
        # 選択されたポイントをハイライト
        selected_points = st.session_state.get(f"{self.key}_selected_points", [])
        
        if selected_points:
            selected_df = self.data.iloc[selected_points]
            
            fig.add_trace(go.Scattermapbox(
                lat=selected_df["latitude"],
                lon=selected_df["longitude"],
                mode="markers",
                marker=dict(
                    size=15,
                    color="yellow",
                    opacity=0.8,
                    symbol="star"
                ),
                name="選択されたポイント",
                hoverinfo="text",
                hovertext=[f"選択されたポイント: {idx}" for idx in selected_points]
            ))
        
        # マップの中心を設定
        center_lat = self.data["latitude"].mean()
        center_lon = self.data["longitude"].mean()
        
        # 選択領域がある場合は、その範囲を表示
        selected_area = st.session_state.get(f"{self.key}_selected_area")
        
        if selected_area:
            lat_min, lat_max, lon_min, lon_max = selected_area
            
            # 選択領域の矩形を追加
            fig.add_trace(go.Scattermapbox(
                lat=[lat_min, lat_max, lat_max, lat_min, lat_min],
                lon=[lon_min, lon_min, lon_max, lon_max, lon_min],
                mode="lines",
                line=dict(width=2, color="yellow"),
                name="選択領域",
                hoverinfo="none"
            ))
            
            # 選択領域を中心に表示
            center_lat = (lat_min + lat_max) / 2
            center_lon = (lon_min + lon_max) / 2
        
        # レイアウト設定
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=self.default_zoom
            ),
            height=500,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            title="問題ポイントのマップ表示"
        )
        
        # マップのクリック・選択イベントの追加
        # （HTMLとJavaScriptを使う必要があるが、Streamlitの制約でここでは実装できない）
        # 代わりに、Plotlyのイベント機能を使用するインストラクションをユーザーに提供
        
        return fig
    
    def _create_heat_map(self) -> go.Figure:
        """
        ヒートマップ形式のマップを作成
        
        Returns
        -------
        go.Figure
            ヒートマップ
        """
        # フィルタリングされた問題インデックスの取得
        filtered_indices = self._get_filtered_indices()
        
        # 問題ポイントのみを使用
        problem_df = self.data.iloc[filtered_indices].copy()
        
        if problem_df.empty:
            # 問題がない場合は空のマップを返す
            fig = go.Figure()
            fig.update_layout(
                title="問題密度ヒートマップ (問題が見つかりません)",
                mapbox=dict(
                    style="open-street-map",
                    center=dict(lat=self.data["latitude"].mean(), lon=self.data["longitude"].mean()),
                    zoom=self.default_zoom
                ),
                height=500,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            return fig
        
        # 問題の重要度を重みとしてカウント
        weights = []
        for idx in filtered_indices:
            if idx < len(self.data):
                severity = self._get_issue_severity(idx)
                weight = 3 if severity == "error" else 2 if severity == "warning" else 1
                weights.append(weight)
            else:
                weights.append(1)  # デフォルト
        
        problem_df["weight"] = weights
        
        # ヒートマップを作成
        fig = px.density_mapbox(
            problem_df,
            lat="latitude",
            lon="longitude",
            z="weight",
            radius=15,
            center=dict(lat=problem_df["latitude"].mean(), lon=problem_df["longitude"].mean()),
            zoom=self.default_zoom,
            mapbox_style="open-street-map",
            color_continuous_scale="Viridis",
            opacity=0.7,
            title="問題密度ヒートマップ"
        )
        
        # 選択されたポイントをハイライト
        selected_points = st.session_state.get(f"{self.key}_selected_points", [])
        
        if selected_points:
            selected_df = self.data.iloc[selected_points]
            
            fig.add_trace(go.Scattermapbox(
                lat=selected_df["latitude"],
                lon=selected_df["longitude"],
                mode="markers",
                marker=dict(
                    size=15,
                    color="yellow",
                    opacity=0.8,
                    symbol="star"
                ),
                name="選択されたポイント",
                hoverinfo="text",
                hovertext=[f"選択されたポイント: {idx}" for idx in selected_points]
            ))
        
        # 選択領域がある場合は、その範囲を表示
        selected_area = st.session_state.get(f"{self.key}_selected_area")
        
        if selected_area:
            lat_min, lat_max, lon_min, lon_max = selected_area
            
            # 選択領域の矩形を追加
            fig.add_trace(go.Scattermapbox(
                lat=[lat_min, lat_max, lat_max, lat_min, lat_min],
                lon=[lon_min, lon_min, lon_max, lon_max, lon_min],
                mode="lines",
                line=dict(width=2, color="yellow"),
                name="選択領域",
                hoverinfo="none"
            ))
        
        # レイアウト設定
        fig.update_layout(
            height=500,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig
    
    def _create_detailed_map(self) -> go.Figure:
        """
        詳細マップを作成
        
        Returns
        -------
        go.Figure
            詳細マップ
        """
        # フィルタリングされた問題インデックスの取得
        filtered_indices = self._get_filtered_indices()
        
        # マップの作成
        fig = go.Figure()
        
        # 通常のトラックの線を追加
        fig.add_trace(go.Scattermapbox(
            lat=self.data["latitude"],
            lon=self.data["longitude"],
            mode="lines",
            line=dict(width=2, color="blue", opacity=0.3),
            name="トラック",
            hoverinfo="none"
        ))
        
        # 問題カテゴリとマーカー形状のマッピング
        marker_symbols = {
            "missing_data": "circle",
            "out_of_range": "triangle-up",
            "duplicates": "square",
            "spatial_anomalies": "diamond",
            "temporal_anomalies": "star"
        }
        
        # 問題ポイントを問題タイプごとに追加
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                # フィルタリングとの交差
                problem_indices = list(set(indices) & set(filtered_indices))
                
                if problem_indices:
                    problem_df = self.data.iloc[problem_indices]
                    
                    # 問題の詳細情報を作成
                    hover_texts = []
                    custom_data = []
                    for idx in problem_indices:
                        if idx < len(self.data):
                            row = self.data.iloc[idx]
                            
                            text = f"インデックス: {idx}<br>"
                            text += f"問題タイプ: {self.problem_type_names.get(problem_type, problem_type)}<br>"
                            
                            if "timestamp" in row:
                                text += f"タイムスタンプ: {row['timestamp']}<br>"
                            
                            if "speed" in row:
                                text += f"速度: {row['speed']:.2f}<br>"
                            
                            # 問題の重要度を取得
                            severity = self._get_issue_severity(idx)
                            text += f"重要度: {severity}<br>"
                            
                            hover_texts.append(text)
                            custom_data.append([idx, severity])
                    
                    # マーカーのスタイル
                    marker_style = dict(
                        size=12,
                        color=self.problem_type_colors.get(problem_type, "red"),
                        symbol=marker_symbols.get(problem_type, "circle"),
                        opacity=0.8
                    )
                    
                    # 問題ポイントを追加
                    fig.add_trace(go.Scattermapbox(
                        lat=problem_df["latitude"],
                        lon=problem_df["longitude"],
                        mode="markers",
                        marker=marker_style,
                        name=self.problem_type_names.get(problem_type, problem_type),
                        hoverinfo="text",
                        hovertext=hover_texts,
                        customdata=custom_data
                    ))
        
        # 選択されたポイントをハイライト
        selected_points = st.session_state.get(f"{self.key}_selected_points", [])
        
        if selected_points:
            selected_df = self.data.iloc[selected_points]
            
            fig.add_trace(go.Scattermapbox(
                lat=selected_df["latitude"],
                lon=selected_df["longitude"],
                mode="markers",
                marker=dict(
                    size=15,
                    color="yellow",
                    opacity=0.8,
                    symbol="star"
                ),
                name="選択されたポイント",
                hoverinfo="text",
                hovertext=[f"選択されたポイント: {idx}" for idx in selected_points]
            ))
        
        # マップの中心を設定
        center_lat = self.data["latitude"].mean()
        center_lon = self.data["longitude"].mean()
        
        # 選択領域がある場合は、その範囲を表示
        selected_area = st.session_state.get(f"{self.key}_selected_area")
        
        if selected_area:
            lat_min, lat_max, lon_min, lon_max = selected_area
            
            # 選択領域の矩形を追加
            fig.add_trace(go.Scattermapbox(
                lat=[lat_min, lat_max, lat_max, lat_min, lat_min],
                lon=[lon_min, lon_min, lon_max, lon_max, lon_min],
                mode="lines",
                line=dict(width=2, color="yellow"),
                name="選択領域",
                hoverinfo="none"
            ))
            
            # 選択領域を中心に表示
            center_lat = (lat_min + lat_max) / 2
            center_lon = (lon_min + lon_max) / 2
        
        # レイアウト設定
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=self.default_zoom
            ),
            height=500,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            title="詳細問題マップ"
        )
        
        return fig
    
    def _get_filtered_indices(self) -> List[int]:
        """
        フィルタリングされた問題インデックスを取得
        
        Returns
        -------
        List[int]
            フィルタリングされた問題インデックス
        """
        # 問題タイプのフィルタリング
        filtered_type = st.session_state.get(f"{self.key}_filtered_problem_type", "all")
        
        if filtered_type == "all":
            indices = self.problem_indices["all"]
        else:
            indices = self.problem_indices.get(filtered_type, [])
        
        # 選択領域でのフィルタリング
        selected_area = st.session_state.get(f"{self.key}_selected_area")
        
        if selected_area:
            lat_min, lat_max, lon_min, lon_max = selected_area
            
            # 選択領域内のポイントを抽出
            area_indices = []
            
            for i, row in self.data.iterrows():
                lat, lon = row["latitude"], row["longitude"]
                
                if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                    area_indices.append(i)
            
            # 問題インデックスと選択領域の交差
            indices = list(set(indices) & set(area_indices))
        
        return indices
    
    def _get_issue_severity(self, idx: int) -> str:
        """
        問題の重要度を取得
        
        Parameters
        ----------
        idx : int
            問題のインデックス
            
        Returns
        -------
        str
            重要度 ("error", "warning", "info")
        """
        # 問題タイプがあれば重要度を判定
        problem_types = [pt for pt, indices in self.problem_indices.items() 
                        if pt != "all" and idx in indices]
        
        if "spatial_anomalies" in problem_types or "temporal_anomalies" in problem_types:
            return "error"
        elif "out_of_range" in problem_types or "duplicates" in problem_types:
            return "warning"
        elif "missing_data" in problem_types:
            return "warning"
        
        return "info"
    
    def set_selected_area(self, lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> None:
        """
        選択領域を設定
        
        Parameters
        ----------
        lat_min : float
            最小緯度
        lat_max : float
            最大緯度
        lon_min : float
            最小経度
        lon_max : float
            最大経度
        """
        st.session_state[f"{self.key}_selected_area"] = (lat_min, lat_max, lon_min, lon_max)
        
        # 選択領域内の問題ポイントを自動選択
        filtered_indices = self._get_filtered_indices()
        
        if self.on_select and filtered_indices:
            self.on_select(filtered_indices)
    
    def set_selected_points(self, points: List[int]) -> None:
        """
        選択ポイントを設定
        
        Parameters
        ----------
        points : List[int]
            選択するポイントのインデックスリスト
        """
        st.session_state[f"{self.key}_selected_points"] = points
        
        if self.on_select and points:
            self.on_select(points)
    
    def get_selected_points(self) -> List[int]:
        """
        選択されたポイントを取得
        
        Returns
        -------
        List[int]
            選択されたポイントのインデックスリスト
        """
        return st.session_state.get(f"{self.key}_selected_points", [])
    
    def clear_selection(self) -> None:
        """
        選択をクリア
        """
        st.session_state[f"{self.key}_selected_area"] = None
        st.session_state[f"{self.key}_selected_points"] = []
        
    def _render_problem_summary(self):
        """
        問題のサマリー情報を表示
        
        問題の分布や傾向を視覚的に把握できるようにする
        """
        # フィルタリングされた問題インデックスを取得
        filtered_indices = self._get_filtered_indices()
        
        if not filtered_indices:
            # 問題がない場合は表示しない
            return
        
        st.subheader("問題分布サマリー")
        
        # 問題タイプごとのカウント
        problem_type_counts = {}
        
        for pt, indices in self.problem_indices.items():
            if pt != "all":
                matched_indices = list(set(indices) & set(filtered_indices))
                if matched_indices:
                    problem_type_counts[self.problem_type_names.get(pt, pt)] = len(matched_indices)
        
        # 重要度ごとのカウント
        severity_counts = {"エラー": 0, "警告": 0, "情報": 0}
        severity_mapping = {"error": "エラー", "warning": "警告", "info": "情報"}
        
        for idx in filtered_indices:
            severity = self._get_issue_severity(idx)
            severity_counts[severity_mapping.get(severity, "情報")] += 1
        
        # 選択エリア内のサマリー表示
        selected_area = st.session_state.get(f"{self.key}_selected_area")
        
        if selected_area:
            lat_min, lat_max, lon_min, lon_max = selected_area
            
            # 選択領域内の問題数と全体に対する割合
            area_indices = []
            
            for i, row in self.data.iterrows():
                lat, lon = row["latitude"], row["longitude"]
                
                if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                    area_indices.append(i)
            
            # 問題インデックスと選択領域の交差
            area_problem_indices = list(set(self.problem_indices["all"]) & set(area_indices))
            
            area_percentage = 0
            if self.problem_indices["all"]:
                area_percentage = len(area_problem_indices) / len(self.problem_indices["all"]) * 100
            
            st.info(f"選択領域内の問題: {len(area_problem_indices)}件 (全体の{area_percentage:.1f}%)")
        
        # 可視化: 問題タイプ別の円グラフと重要度別の棒グラフを並べて表示
        col1, col2 = st.columns(2)
        
        with col1:
            if problem_type_counts:
                # 問題タイプの円グラフ
                fig = go.Figure(data=[go.Pie(
                    labels=list(problem_type_counts.keys()),
                    values=list(problem_type_counts.values()),
                    hole=.3,
                    marker_colors=[self.problem_type_colors.get(pt, "blue") for pt in self.problem_indices if pt != "all" and self.problem_type_names.get(pt, pt) in problem_type_counts]
                )])
                
                fig.update_layout(
                    title="問題タイプ別の分布",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0)
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if any(severity_counts.values()):
                # 重要度別の棒グラフ
                severity_colors = {"エラー": "#f44336", "警告": "#ff9800", "情報": "#2196f3"}
                
                fig = go.Figure(data=[go.Bar(
                    x=list(severity_counts.keys()),
                    y=list(severity_counts.values()),
                    marker_color=[severity_colors.get(sev, "#2196f3") for sev in severity_counts.keys()]
                )])
                
                fig.update_layout(
                    title="重要度別の問題数",
                    height=300,
                    margin=dict(l=0, r=0, t=30, b=0),
                    xaxis_title="重要度",
                    yaxis_title="問題数"
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # 空間クラスタリング: 問題の集中エリアの把握
        if len(filtered_indices) > 5:  # 一定数以上の問題がある場合のみ
            st.subheader("問題の空間分布")
            
            # 問題の密度マップをヒートマップで表示
            problem_df = self.data.iloc[filtered_indices]
            
            # 重要度に応じた重み付け
            weights = []
            for idx in filtered_indices:
                severity = self._get_issue_severity(idx)
                weight = 3 if severity == "error" else 2 if severity == "warning" else 1
                weights.append(weight)
            
            problem_df["weight"] = weights
            
            # 密度マップ
            fig = px.density_mapbox(
                problem_df,
                lat="latitude",
                lon="longitude",
                z="weight",
                radius=10,
                center=dict(lat=problem_df["latitude"].mean(), lon=problem_df["longitude"].mean()),
                zoom=10,
                mapbox_style="open-street-map",
                color_continuous_scale="Viridis",
                opacity=0.7,
                title="問題の密度分布"
            )
            
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 問題が多い地域の特定
            # (実際のクラスタリングはこのStreamlitの制約の中では簡易的に行う)
            
            if "latitude" in problem_df.columns and "longitude" in problem_df.columns:
                # 緯度経度の四分位数で簡易的に地域分割
                lat_q1, lat_q3 = problem_df["latitude"].quantile(0.25), problem_df["latitude"].quantile(0.75)
                lon_q1, lon_q3 = problem_df["longitude"].quantile(0.25), problem_df["longitude"].quantile(0.75)
                
                # 4つの象限に分けて各象限の問題数をカウント
                ne_count = ((problem_df["latitude"] >= lat_q3) & (problem_df["longitude"] >= lon_q3)).sum()
                nw_count = ((problem_df["latitude"] >= lat_q3) & (problem_df["longitude"] < lon_q3)).sum()
                se_count = ((problem_df["latitude"] < lat_q3) & (problem_df["longitude"] >= lon_q3)).sum()
                sw_count = ((problem_df["latitude"] < lat_q3) & (problem_df["longitude"] < lon_q3)).sum()
                
                # 最も問題が多い象限を特定
                quadrants = {"北東": ne_count, "北西": nw_count, "南東": se_count, "南西": sw_count}
                max_quadrant = max(quadrants, key=quadrants.get)
                
                if quadrants[max_quadrant] > len(filtered_indices) / 3:  # 一定以上の問題が集中している場合
                    st.info(f"問題が最も集中しているエリア: {max_quadrant}象限 ({quadrants[max_quadrant]}件、全体の{quadrants[max_quadrant]/len(filtered_indices)*100:.1f}%)")
                    
                    # この象限を地図上で選択するためのボタン
                    if st.button(f"{max_quadrant}象限を地図上で選択", key=f"{self.key}_select_max_quadrant"):
                        if max_quadrant == "北東":
                            self.set_selected_area(lat_q3, problem_df["latitude"].max(), lon_q3, problem_df["longitude"].max())
                        elif max_quadrant == "北西":
                            self.set_selected_area(lat_q3, problem_df["latitude"].max(), problem_df["longitude"].min(), lon_q3)
                        elif max_quadrant == "南東":
                            self.set_selected_area(problem_df["latitude"].min(), lat_q3, lon_q3, problem_df["longitude"].max())
                        elif max_quadrant == "南西":
                            self.set_selected_area(problem_df["latitude"].min(), lat_q3, problem_df["longitude"].min(), lon_q3)
                        
                        # 再レンダリング
                        st.experimental_rerun()

def interactive_map(data: pd.DataFrame, 
                   problem_indices: Dict[str, List[int]],
                   on_select: Callable[[List[int]], None] = None,
                   key: str = "interactive_map") -> InteractiveMap:
    """
    インタラクティブマップコンポーネントを作成
    
    Parameters
    ----------
    data : pd.DataFrame
        マップ表示するデータフレーム
    problem_indices : Dict[str, List[int]]
        問題タイプごとのインデックスリスト
    on_select : Callable[[List[int]], None], optional
        エリア選択時のコールバック関数
    key : str, optional
        コンポーネントのキー, by default "interactive_map"
    
    Returns
    -------
    InteractiveMap
        インタラクティブマップコンポーネント
    """
    return InteractiveMap(data, problem_indices, on_select, key)
