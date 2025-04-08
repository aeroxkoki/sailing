"""
ui.components.reporting.statistical_properties_panel

統計分析グラフのプロパティ設定を行うためのパネルを提供するモジュールです。
時系列分析、ボックスプロット、ヒートマップ、相関分析グラフのプロパティを
対話的に設定するためのStreamlitコンポーネントを実装しています。
"""

from typing import Dict, List, Any, Optional, Callable, Union, Tuple
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from sailing_data_processor.reporting.elements.visualizations.statistical_charts import (
    TimeSeriesElement, BoxPlotElement, HeatMapElement, CorrelationElement
)
from sailing_data_processor.reporting.templates.template_model import ElementModel


class StatisticalPropertiesPanel:
    """
    統計分析グラフのプロパティパネル
    
    時系列分析、ボックスプロット、ヒートマップ、相関分析グラフなどの
    統計分析グラフのプロパティを設定するためのパネルです。
    """
    
    def __init__(self, on_change: Optional[Callable[[Dict[str, Any]], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        on_change : Optional[Callable[[Dict[str, Any]], None]], optional
            プロパティ変更時のコールバック, by default None
            - 引数: 更新されたプロパティ辞書
        """
        self.on_change = on_change
    
    def render(self, graph_type: str, properties: Dict[str, Any], data_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        プロパティパネルを描画
        
        Parameters
        ----------
        graph_type : str
            グラフタイプ ("time_series", "box_plot", "heat_map", "correlation")
        properties : Dict[str, Any]
            現在のプロパティ値
        data_context : Optional[Dict[str, Any]], optional
            利用可能なデータコンテキスト, by default None
            
        Returns
        -------
        Dict[str, Any]
            更新されたプロパティ値
        """
        st.subheader("グラフプロパティ")
        
        updated_properties = properties.copy()
        
        # グラフタイプに応じたパネルを表示
        if graph_type == "time_series":
            updated_properties = self._render_time_series_panel(updated_properties, data_context)
        elif graph_type == "box_plot":
            updated_properties = self._render_box_plot_panel(updated_properties, data_context)
        elif graph_type == "heat_map":
            updated_properties = self._render_heat_map_panel(updated_properties, data_context)
        elif graph_type == "correlation":
            updated_properties = self._render_correlation_panel(updated_properties, data_context)
        else:
            st.warning(f"未対応のグラフタイプ: {graph_type}")
        
        # 変更があった場合、コールバックを呼び出す
        if self.on_change and updated_properties != properties:
            self.on_change(updated_properties)
        
        return updated_properties
    
    def _get_data_fields(self, data_context: Optional[Dict[str, Any]]) -> List[str]:
        """
        利用可能なデータフィールドを取得
        
        Parameters
        ----------
        data_context : Optional[Dict[str, Any]]
            データコンテキスト
            
        Returns
        -------
        List[str]
            フィールド名のリスト
        """
        fields = []
        
        if data_context:
            for key, value in data_context.items():
                if isinstance(value, pd.DataFrame):
                    fields.extend(value.columns.tolist())
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    fields.extend(value[0].keys())
        
        # 重複を排除
        fields = list(set(fields))
        
        return sorted(fields)
    
    def _get_data_sources(self, data_context: Optional[Dict[str, Any]]) -> List[str]:
        """
        利用可能なデータソースを取得
        
        Parameters
        ----------
        data_context : Optional[Dict[str, Any]]
            データコンテキスト
            
        Returns
        -------
        List[str]
            データソース名のリスト
        """
        if data_context:
            return sorted(list(data_context.keys()))
        return []
    
    def _render_time_series_panel(self, properties: Dict[str, Any], data_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        時系列分析グラフのプロパティパネルを描画
        
        Parameters
        ----------
        properties : Dict[str, Any]
            現在のプロパティ値
        data_context : Optional[Dict[str, Any]]
            データコンテキスト
            
        Returns
        -------
        Dict[str, Any]
            更新されたプロパティ値
        """
        # プロパティのコピーを作成
        updated_props = properties.copy()
        
        # データソース設定
        with st.expander("データソース設定", expanded=True):
            data_sources = self._get_data_sources(data_context)
            selected_source = st.selectbox(
                "データソース",
                options=data_sources,
                index=data_sources.index(updated_props.get("data_source", "")) if updated_props.get("data_source", "") in data_sources else 0,
                key="time_series_data_source"
            )
            updated_props["data_source"] = selected_source
            
            # データフィールド
            fields = self._get_data_fields(data_context)
            
            # 時間キー
            time_key = st.selectbox(
                "時間キー",
                options=fields,
                index=fields.index(updated_props.get("time_key", "time")) if updated_props.get("time_key", "time") in fields else 0,
                key="time_series_time_key"
            )
            updated_props["time_key"] = time_key
            
            # 値キー（複数選択可能）
            value_keys = st.multiselect(
                "値キー",
                options=fields,
                default=updated_props.get("value_keys", []),
                key="time_series_value_keys"
            )
            updated_props["value_keys"] = value_keys
        
        # グラフ表示設定
        with st.expander("グラフ表示設定", expanded=False):
            # タイトル
            title = st.text_input(
                "グラフタイトル",
                value=updated_props.get("title", "時系列分析"),
                key="time_series_title"
            )
            updated_props["title"] = title
            
            # 軸ラベル
            col1, col2 = st.columns(2)
            with col1:
                x_axis_title = st.text_input(
                    "X軸ラベル",
                    value=updated_props.get("x_axis_title", "時間"),
                    key="time_series_x_axis_title"
                )
                updated_props["x_axis_title"] = x_axis_title
            
            with col2:
                y_axis_title = st.text_input(
                    "Y軸ラベル",
                    value=updated_props.get("y_axis_title", "値"),
                    key="time_series_y_axis_title"
                )
                updated_props["y_axis_title"] = y_axis_title
            
            # 時間単位
            time_unit = st.selectbox(
                "時間単位",
                options=["minute", "hour", "day", "week", "month", "year"],
                index=["minute", "hour", "day", "week", "month", "year"].index(updated_props.get("time_unit", "minute")),
                format_func=lambda x: {
                    "minute": "分", "hour": "時間", "day": "日",
                    "week": "週", "month": "月", "year": "年"
                }.get(x, x),
                key="time_series_time_unit"
            )
            updated_props["time_unit"] = time_unit
            
            # Y軸の開始を0にするかどうか
            begin_at_zero = st.checkbox(
                "Y軸を0から開始",
                value=updated_props.get("begin_at_zero", False),
                key="time_series_begin_at_zero"
            )
            updated_props["begin_at_zero"] = begin_at_zero
        
        # 分析設定
        with st.expander("分析設定", expanded=False):
            # 移動平均の表示
            moving_average = st.checkbox(
                "移動平均を表示",
                value=updated_props.get("moving_average", False),
                key="time_series_moving_average"
            )
            updated_props["moving_average"] = moving_average
            
            if moving_average:
                moving_average_window = st.slider(
                    "移動平均の窓サイズ",
                    min_value=2,
                    max_value=30,
                    value=updated_props.get("moving_average_window", 5),
                    key="time_series_moving_average_window"
                )
                updated_props["moving_average_window"] = moving_average_window
            
            # トレンドラインの表示
            trendline = st.checkbox(
                "トレンドラインを表示",
                value=updated_props.get("trendline", False),
                key="time_series_trendline"
            )
            updated_props["trendline"] = trendline
            
            # 異常値のハイライト
            highlight_outliers = st.checkbox(
                "異常値をハイライト",
                value=updated_props.get("highlight_outliers", False),
                key="time_series_highlight_outliers"
            )
            updated_props["highlight_outliers"] = highlight_outliers
            
            if highlight_outliers:
                outlier_threshold = st.slider(
                    "異常値の閾値（標準偏差の倍数）",
                    min_value=1.0,
                    max_value=5.0,
                    value=updated_props.get("outlier_threshold", 2.0),
                    step=0.1,
                    key="time_series_outlier_threshold"
                )
                updated_props["outlier_threshold"] = outlier_threshold
        
        return updated_props
    
    def _render_box_plot_panel(self, properties: Dict[str, Any], data_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        ボックスプロットのプロパティパネルを描画
        
        Parameters
        ----------
        properties : Dict[str, Any]
            現在のプロパティ値
        data_context : Optional[Dict[str, Any]]
            データコンテキスト
            
        Returns
        -------
        Dict[str, Any]
            更新されたプロパティ値
        """
        # プロパティのコピーを作成
        updated_props = properties.copy()
        
        # データソース設定
        with st.expander("データソース設定", expanded=True):
            data_sources = self._get_data_sources(data_context)
            selected_source = st.selectbox(
                "データソース",
                options=data_sources,
                index=data_sources.index(updated_props.get("data_source", "")) if updated_props.get("data_source", "") in data_sources else 0,
                key="box_plot_data_source"
            )
            updated_props["data_source"] = selected_source
            
            # データフィールド
            fields = self._get_data_fields(data_context)
            
            # グループキー
            group_key = st.selectbox(
                "グループキー",
                options=fields,
                index=fields.index(updated_props.get("group_key", "group")) if updated_props.get("group_key", "group") in fields else 0,
                key="box_plot_group_key"
            )
            updated_props["group_key"] = group_key
            
            # 値キー
            value_key = st.selectbox(
                "値キー",
                options=fields,
                index=fields.index(updated_props.get("value_key", "value")) if updated_props.get("value_key", "value") in fields else 0,
                key="box_plot_value_key"
            )
            updated_props["value_key"] = value_key
        
        # グラフ表示設定
        with st.expander("グラフ表示設定", expanded=False):
            # タイトル
            title = st.text_input(
                "グラフタイトル",
                value=updated_props.get("title", "ボックスプロット"),
                key="box_plot_title"
            )
            updated_props["title"] = title
            
            # 軸ラベル
            col1, col2 = st.columns(2)
            with col1:
                x_axis_title = st.text_input(
                    "X軸ラベル",
                    value=updated_props.get("x_axis_title", "グループ"),
                    key="box_plot_x_axis_title"
                )
                updated_props["x_axis_title"] = x_axis_title
            
            with col2:
                y_axis_title = st.text_input(
                    "Y軸ラベル",
                    value=updated_props.get("y_axis_title", "値"),
                    key="box_plot_y_axis_title"
                )
                updated_props["y_axis_title"] = y_axis_title
            
            # Y軸の開始を0にするかどうか
            begin_at_zero = st.checkbox(
                "Y軸を0から開始",
                value=updated_props.get("begin_at_zero", False),
                key="box_plot_begin_at_zero"
            )
            updated_props["begin_at_zero"] = begin_at_zero
            
            # データセットのラベル
            dataset_label = st.text_input(
                "データセットラベル",
                value=updated_props.get("dataset_label", "データ分布"),
                key="box_plot_dataset_label"
            )
            updated_props["dataset_label"] = dataset_label
        
        # マルチデータセット設定
        with st.expander("マルチデータセット設定", expanded=False):
            use_multi_datasets = st.checkbox(
                "複数データセットを使用",
                value="multi_datasets" in updated_props,
                key="box_plot_use_multi_datasets"
            )
            
            if use_multi_datasets:
                dataset_count = st.number_input(
                    "データセット数",
                    min_value=1,
                    max_value=5,
                    value=len(updated_props.get("multi_datasets", [])) or 1,
                    key="box_plot_dataset_count"
                )
                
                multi_datasets = []
                for i in range(int(dataset_count)):
                    st.subheader(f"データセット {i+1}")
                    
                    # 既存の設定があれば取得
                    dataset_config = {}
                    if "multi_datasets" in updated_props and i < len(updated_props["multi_datasets"]):
                        dataset_config = updated_props["multi_datasets"][i]
                    
                    # データソース
                    ds_source = st.selectbox(
                        "データソース",
                        options=data_sources,
                        index=data_sources.index(dataset_config.get("data_source", "")) if dataset_config.get("data_source", "") in data_sources else 0,
                        key=f"box_plot_ds{i}_source"
                    )
                    
                    # グループキー
                    ds_group_key = st.selectbox(
                        "グループキー",
                        options=fields,
                        index=fields.index(dataset_config.get("group_key", "group")) if dataset_config.get("group_key", "group") in fields else 0,
                        key=f"box_plot_ds{i}_group_key"
                    )
                    
                    # 値キー
                    ds_value_key = st.selectbox(
                        "値キー",
                        options=fields,
                        index=fields.index(dataset_config.get("value_key", "value")) if dataset_config.get("value_key", "value") in fields else 0,
                        key=f"box_plot_ds{i}_value_key"
                    )
                    
                    # ラベル
                    ds_label = st.text_input(
                        "ラベル",
                        value=dataset_config.get("label", f"データセット {i+1}"),
                        key=f"box_plot_ds{i}_label"
                    )
                    
                    # 設定を保存
                    multi_datasets.append({
                        "data_source": ds_source,
                        "group_key": ds_group_key,
                        "value_key": ds_value_key,
                        "label": ds_label
                    })
                
                updated_props["multi_datasets"] = multi_datasets
            else:
                # マルチデータセットを使用しない場合は削除
                if "multi_datasets" in updated_props:
                    del updated_props["multi_datasets"]
        
        return updated_props
    
    def _render_heat_map_panel(self, properties: Dict[str, Any], data_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        ヒートマップのプロパティパネルを描画
        
        Parameters
        ----------
        properties : Dict[str, Any]
            現在のプロパティ値
        data_context : Optional[Dict[str, Any]]
            データコンテキスト
            
        Returns
        -------
        Dict[str, Any]
            更新されたプロパティ値
        """
        # プロパティのコピーを作成
        updated_props = properties.copy()
        
        # データソース設定
        with st.expander("データソース設定", expanded=True):
            data_sources = self._get_data_sources(data_context)
            selected_source = st.selectbox(
                "データソース",
                options=data_sources,
                index=data_sources.index(updated_props.get("data_source", "")) if updated_props.get("data_source", "") in data_sources else 0,
                key="heat_map_data_source"
            )
            updated_props["data_source"] = selected_source
            
            # データフィールド
            fields = self._get_data_fields(data_context)
            
            # マトリックスデータの場合
            data_type = st.radio(
                "データ形式",
                options=["coordinates", "matrix"],
                index=0 if updated_props.get("x_key", "") else 1,
                format_func=lambda x: {
                    "coordinates": "座標形式 (x, y, value)",
                    "matrix": "マトリックス形式 (2次元配列)"
                }.get(x, x),
                key="heat_map_data_type"
            )
            
            if data_type == "coordinates":
                # X、Y、値のキー
                x_key = st.selectbox(
                    "X座標キー",
                    options=fields,
                    index=fields.index(updated_props.get("x_key", "x")) if updated_props.get("x_key", "x") in fields else 0,
                    key="heat_map_x_key"
                )
                updated_props["x_key"] = x_key
                
                y_key = st.selectbox(
                    "Y座標キー",
                    options=fields,
                    index=fields.index(updated_props.get("y_key", "y")) if updated_props.get("y_key", "y") in fields else 0,
                    key="heat_map_y_key"
                )
                updated_props["y_key"] = y_key
                
                value_key = st.selectbox(
                    "値キー",
                    options=fields,
                    index=fields.index(updated_props.get("value_key", "value")) if updated_props.get("value_key", "value") in fields else 0,
                    key="heat_map_value_key"
                )
                updated_props["value_key"] = value_key
            else:
                # マトリックス形式の場合、X軸とY軸のラベルを設定
                x_labels_str = st.text_input(
                    "X軸ラベル（カンマ区切り）",
                    value=",".join(updated_props.get("x_labels", [])) or "A,B,C,D,E",
                    key="heat_map_x_labels"
                )
                updated_props["x_labels"] = [label.strip() for label in x_labels_str.split(",")]
                
                y_labels_str = st.text_input(
                    "Y軸ラベル（カンマ区切り）",
                    value=",".join(updated_props.get("y_labels", [])) or "1,2,3,4,5",
                    key="heat_map_y_labels"
                )
                updated_props["y_labels"] = [label.strip() for label in y_labels_str.split(",")]
        
        # グラフ表示設定
        with st.expander("グラフ表示設定", expanded=False):
            # タイトル
            title = st.text_input(
                "グラフタイトル",
                value=updated_props.get("title", "ヒートマップ"),
                key="heat_map_title"
            )
            updated_props["title"] = title
            
            # 軸ラベル
            col1, col2 = st.columns(2)
            with col1:
                x_axis_title = st.text_input(
                    "X軸ラベル",
                    value=updated_props.get("x_axis_title", "X軸"),
                    key="heat_map_x_axis_title"
                )
                updated_props["x_axis_title"] = x_axis_title
            
            with col2:
                y_axis_title = st.text_input(
                    "Y軸ラベル",
                    value=updated_props.get("y_axis_title", "Y軸"),
                    key="heat_map_y_axis_title"
                )
                updated_props["y_axis_title"] = y_axis_title
            
            # データセットのラベル
            dataset_label = st.text_input(
                "データセットラベル",
                value=updated_props.get("dataset_label", "データ分布"),
                key="heat_map_dataset_label"
            )
            updated_props["dataset_label"] = dataset_label
            
            # セルサイズ
            col1, col2 = st.columns(2)
            with col1:
                cell_width = st.number_input(
                    "セル幅",
                    min_value=10,
                    max_value=100,
                    value=updated_props.get("cell_width", 30),
                    key="heat_map_cell_width"
                )
                updated_props["cell_width"] = cell_width
            
            with col2:
                cell_height = st.number_input(
                    "セル高さ",
                    min_value=10,
                    max_value=100,
                    value=updated_props.get("cell_height", 30),
                    key="heat_map_cell_height"
                )
                updated_props["cell_height"] = cell_height
        
        # カラースケール設定
        with st.expander("カラースケール設定", expanded=False):
            color_scale_type = st.selectbox(
                "カラースケールタイプ",
                options=["blue_to_red", "green_to_red", "blue_cyan_green_yellow_red", "custom"],
                index=0,
                format_func=lambda x: {
                    "blue_to_red": "青→赤",
                    "green_to_red": "緑→赤",
                    "blue_cyan_green_yellow_red": "青→シアン→緑→黄→赤",
                    "custom": "カスタム"
                }.get(x, x),
                key="heat_map_color_scale_type"
            )
            
            if color_scale_type == "blue_to_red":
                color_scale = [
                    "rgba(0, 0, 255, 0.5)",  # 青
                    "rgba(255, 0, 0, 0.5)"   # 赤
                ]
            elif color_scale_type == "green_to_red":
                color_scale = [
                    "rgba(0, 255, 0, 0.5)",  # 緑
                    "rgba(255, 255, 0, 0.5)",  # 黄
                    "rgba(255, 0, 0, 0.5)"   # 赤
                ]
            elif color_scale_type == "blue_cyan_green_yellow_red":
                color_scale = [
                    "rgba(0, 0, 255, 0.5)",  # 青
                    "rgba(0, 255, 255, 0.5)",  # シアン
                    "rgba(0, 255, 0, 0.5)",  # 緑
                    "rgba(255, 255, 0, 0.5)",  # 黄
                    "rgba(255, 0, 0, 0.5)"   # 赤
                ]
            elif color_scale_type == "custom":
                color_scale_str = st.text_input(
                    "カラースケール（カンマ区切りのRGBA形式）",
                    value=",".join(updated_props.get("color_scale", ["rgba(0, 0, 255, 0.5)", "rgba(255, 0, 0, 0.5)"])),
                    key="heat_map_custom_color_scale"
                )
                color_scale = [color.strip() for color in color_scale_str.split(",")]
            
            updated_props["color_scale"] = color_scale
        
        return updated_props
    
    def _render_correlation_panel(self, properties: Dict[str, Any], data_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        相関分析グラフのプロパティパネルを描画
        
        Parameters
        ----------
        properties : Dict[str, Any]
            現在のプロパティ値
        data_context : Optional[Dict[str, Any]]
            データコンテキスト
            
        Returns
        -------
        Dict[str, Any]
            更新されたプロパティ値
        """
        # プロパティのコピーを作成
        updated_props = properties.copy()
        
        # データソース設定
        with st.expander("データソース設定", expanded=True):
            data_sources = self._get_data_sources(data_context)
            selected_source = st.selectbox(
                "データソース",
                options=data_sources,
                index=data_sources.index(updated_props.get("data_source", "")) if updated_props.get("data_source", "") in data_sources else 0,
                key="correlation_data_source"
            )
            updated_props["data_source"] = selected_source
            
            # データフィールド
            fields = self._get_data_fields(data_context)
            
            # X軸とY軸のパラメータ
            x_param = st.selectbox(
                "X軸パラメータ",
                options=fields,
                index=fields.index(updated_props.get("x_param", "")) if updated_props.get("x_param", "") in fields else 0,
                key="correlation_x_param"
            )
            updated_props["x_param"] = x_param
            
            y_param = st.selectbox(
                "Y軸パラメータ",
                options=fields,
                index=fields.index(updated_props.get("y_param", "")) if updated_props.get("y_param", "") in fields else 0,
                key="correlation_y_param"
            )
            updated_props["y_param"] = y_param
        
        # グラフ表示設定
        with st.expander("グラフ表示設定", expanded=False):
            # タイトル
            title = st.text_input(
                "グラフタイトル",
                value=updated_props.get("title", "相関分析"),
                key="correlation_title"
            )
            updated_props["title"] = title
            
            # 軸ラベル
            col1, col2 = st.columns(2)
            with col1:
                x_axis_title = st.text_input(
                    "X軸ラベル",
                    value=updated_props.get("x_axis_title", x_param),
                    key="correlation_x_axis_title"
                )
                updated_props["x_axis_title"] = x_axis_title
            
            with col2:
                y_axis_title = st.text_input(
                    "Y軸ラベル",
                    value=updated_props.get("y_axis_title", y_param),
                    key="correlation_y_axis_title"
                )
                updated_props["y_axis_title"] = y_axis_title
            
            # データセットのラベル
            dataset_label = st.text_input(
                "データセットラベル",
                value=updated_props.get("dataset_label", f"{x_param} vs {y_param}"),
                key="correlation_dataset_label"
            )
            updated_props["dataset_label"] = dataset_label
        
        # 回帰設定
        with st.expander("回帰設定", expanded=False):
            # トレンドラインの表示
            show_trendline = st.checkbox(
                "トレンドラインを表示",
                value=updated_props.get("show_trendline", True),
                key="correlation_show_trendline"
            )
            updated_props["show_trendline"] = show_trendline
            
            if show_trendline:
                # 回帰タイプ
                regression_type = st.selectbox(
                    "回帰タイプ",
                    options=["linear", "exponential", "polynomial", "power", "logarithmic"],
                    index=["linear", "exponential", "polynomial", "power", "logarithmic"].index(updated_props.get("regression_type", "linear")),
                    format_func=lambda x: {
                        "linear": "線形回帰",
                        "exponential": "指数回帰",
                        "polynomial": "多項式回帰",
                        "power": "累乗回帰",
                        "logarithmic": "対数回帰"
                    }.get(x, x),
                    key="correlation_regression_type"
                )
                updated_props["regression_type"] = regression_type
                
                # 多項式回帰の場合、次数を設定
                if regression_type == "polynomial":
                    polynomial_order = st.slider(
                        "多項式の次数",
                        min_value=2,
                        max_value=5,
                        value=updated_props.get("polynomial_order", 2),
                        key="correlation_polynomial_order"
                    )
                    updated_props["polynomial_order"] = polynomial_order
                
                # トレンドラインのラベル
                trendline_label = st.text_input(
                    "トレンドラインのラベル",
                    value=updated_props.get("trendline_label", "回帰直線"),
                    key="correlation_trendline_label"
                )
                updated_props["trendline_label"] = trendline_label
        
        return updated_props
