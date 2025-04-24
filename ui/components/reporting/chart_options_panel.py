# -*- coding: utf-8 -*-
"""
ui.components.reporting.chart_options_panel

チャートオプションを編集するためのパネルを提供するモジュールです。
可視化要素の設定を対話的に変更するためのStreamlitコンポーネントを実装しています。
"""

from typing import Dict, List, Any, Optional, Callable
import streamlit as st
import pandas as pd
import numpy as np
import json

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.elements.visualizations.sailing_charts import (
    WindRoseElement, CoursePerformanceElement, TackingAngleElement, StrategyPointMapElement
)
from sailing_data_processor.reporting.elements.visualizations.statistical_charts import (
    TimeSeriesElement, BoxPlotElement, HeatMapElement, CorrelationElement
)
from sailing_data_processor.reporting.elements.visualizations.map_elements import (
    TrackMapElement, HeatMapLayerElement, StrategyPointLayerElement, WindFieldElement
)
from sailing_data_processor.reporting.elements.visualizations.timeline_elements import (
    EventTimelineElement, ParameterTimelineElement, SegmentComparisonElement, DataViewerElement
)


class ChartOptionsPanel:
    """
    チャートオプションパネルコンポーネント
    
    可視化要素のオプションを編集するためのパネルを提供するStreamlitコンポーネントです。
    """
    
    def __init__(self, on_option_change: Optional[Callable[[str, Any], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        on_option_change : Optional[Callable[[str, Any], None]], optional
            オプション変更時のコールバック, by default None
        """
        self.on_option_change = on_option_change
    
    def render(self, element: Optional[BaseChartElement] = None) -> None:
        """
        チャートオプションパネルを描画
        
        Parameters
        ----------
        element : Optional[BaseChartElement], optional
            編集対象の可視化要素, by default None
        """
        if element is None:
            st.info("要素が選択されていません。")
            return
        
        st.subheader("チャートオプション")
        
        # 可視化要素タイプに応じたオプション設定UI
        element_type = type(element).__name__
        
        # 基本設定
        with st.expander("基本設定", expanded=True):
            # タイトル
            title = st.text_input("タイトル", value=element.title)
            if title != element.title and self.on_option_change:
                self.on_option_change("title", title)
            
            # データソース
            data_source = st.text_input("データソース", value=element.data_source)
            if data_source != element.data_source and self.on_option_change:
                self.on_option_change("data_source", data_source)
            
            # ID
            st.text_input("要素ID", value=element.element_id, disabled=True)
        
        # 要素固有のオプション
        with st.expander("要素固有設定", expanded=True):
            if isinstance(element, WindRoseElement):
                self._render_wind_rose_options(element)
            elif isinstance(element, CoursePerformanceElement):
                self._render_course_performance_options(element)
            elif isinstance(element, TackingAngleElement):
                self._render_tacking_angle_options(element)
            elif isinstance(element, StrategyPointMapElement):
                self._render_strategy_point_map_options(element)
            elif isinstance(element, TimeSeriesElement):
                self._render_time_series_options(element)
            elif isinstance(element, BoxPlotElement):
                self._render_box_plot_options(element)
            elif isinstance(element, HeatMapElement):
                self._render_heat_map_options(element)
            elif isinstance(element, CorrelationElement):
                self._render_correlation_options(element)
            elif isinstance(element, TrackMapElement):
                self._render_track_map_options(element)
            elif isinstance(element, HeatMapLayerElement):
                self._render_heat_map_layer_options(element)
            elif isinstance(element, StrategyPointLayerElement):
                self._render_strategy_point_layer_options(element)
            elif isinstance(element, WindFieldElement):
                self._render_wind_field_options(element)
            elif isinstance(element, EventTimelineElement):
                self._render_event_timeline_options(element)
            elif isinstance(element, ParameterTimelineElement):
                self._render_parameter_timeline_options(element)
            elif isinstance(element, SegmentComparisonElement):
                self._render_segment_comparison_options(element)
            elif isinstance(element, DataViewerElement):
                self._render_data_viewer_options(element)
            else:
                # その他の要素タイプのオプション
                st.write(f"{element_type}の固有設定は現在開発中です。")
        
        # スタイル設定
        with st.expander("スタイル設定", expanded=False):
            # 幅と高さ
            col1, col2 = st.columns(2)
            with col1:
                width = st.text_input("幅", value=element.get_style("width", "100%"))
                if width != element.get_style("width") and self.on_option_change:
                    self.on_option_change("style_width", width)
            
            with col2:
                height = st.text_input("高さ", value=element.get_style("height", "400px"))
                if height != element.get_style("height") and self.on_option_change:
                    self.on_option_change("style_height", height)
            
            # マージンとパディング
            col1, col2 = st.columns(2)
            with col1:
                margin = st.text_input("マージン", value=element.get_style("margin", "0"))
                if margin != element.get_style("margin") and self.on_option_change:
                    self.on_option_change("style_margin", margin)
            
            with col2:
                padding = st.text_input("パディング", value=element.get_style("padding", "0"))
                if padding != element.get_style("padding") and self.on_option_change:
                    self.on_option_change("style_padding", padding)
            
            # 背景色とボーダー
            col1, col2 = st.columns(2)
            with col1:
                bg_color = st.color_picker("背景色", value=element.get_style("background-color", "#FFFFFF"))
                if bg_color != element.get_style("background-color") and self.on_option_change:
                    self.on_option_change("style_background-color", bg_color)
            
            with col2:
                border = st.text_input("ボーダー", value=element.get_style("border", "none"))
                if border != element.get_style("border") and self.on_option_change:
                    self.on_option_change("style_border", border)
    
    def _render_wind_rose_options(self, element: WindRoseElement) -> None:
        """風配図のオプション設定UI"""
        st.subheader("基本設定")
        
        # 角度分割数
        angle_divisions = st.slider("角度分割数", min_value=4, max_value=36, value=element.get_property("angle_divisions", 16), step=4)
        if angle_divisions != element.get_property("angle_divisions") and self.on_option_change:
            self.on_option_change("angle_divisions", angle_divisions)
        
        # 方位表示形式
        direction_format_options = ["cardinal", "degrees", "both"]
        direction_format_labels = {
            "cardinal": "方位名（N, E, S, Wなど）",
            "degrees": "角度（0°, 90°など）",
            "both": "両方（N (0°)など）"
        }
        
        direction_format = st.selectbox(
            "方位表示形式",
            options=direction_format_options,
            index=direction_format_options.index(element.get_property("direction_format", "cardinal")),
            format_func=lambda x: direction_format_labels.get(x, x)
        )
        if direction_format != element.get_property("direction_format") and self.on_option_change:
            self.on_option_change("direction_format", direction_format)
        
        # カラースケール設定
        st.subheader("カラースケール")
        
        # カラースケールのプリセット
        color_scale_preset_options = ["blue", "rainbow", "thermal", "monochrome", "custom"]
        color_scale_preset_labels = {
            "blue": "青のグラデーション",
            "rainbow": "虹色のグラデーション",
            "thermal": "熱分布のグラデーション",
            "monochrome": "モノクロのグラデーション",
            "custom": "カスタム"
        }
        
        color_scale_preset = st.selectbox(
            "カラースケールプリセット",
            options=color_scale_preset_options,
            index=color_scale_preset_options.index(element.get_property("color_scale_preset", "blue")),
            format_func=lambda x: color_scale_preset_labels.get(x, x)
        )
        if color_scale_preset != element.get_property("color_scale_preset") and self.on_option_change:
            self.on_option_change("color_scale_preset", color_scale_preset)
        
        # カスタムカラースケールの場合、色選択UIを表示
        if color_scale_preset == "custom":
            color_scale = element.get_property("color_scale", [
                "rgba(53, 162, 235, 0.2)",
                "rgba(53, 162, 235, 0.4)",
                "rgba(53, 162, 235, 0.6)",
                "rgba(53, 162, 235, 0.8)",
                "rgba(53, 162, 235, 1.0)"
            ])
            
            cols = st.columns(len(color_scale))
            for i, color in enumerate(color_scale):
                with cols[i]:
                    new_color = st.color_picker(f"色 {i+1}", color)
                    if new_color != color and self.on_option_change:
                        color_scale[i] = new_color
                        self.on_option_change("color_scale", color_scale)
        
        # 時間フィルタリング
        st.subheader("時間フィルタリング")
        
        time_filter_enabled = st.checkbox("時間範囲フィルタリングを有効化", value=element.get_property("time_filter_enabled", False))
        if time_filter_enabled != element.get_property("time_filter_enabled") and self.on_option_change:
            self.on_option_change("time_filter_enabled", time_filter_enabled)
        
        if time_filter_enabled:
            col1, col2 = st.columns(2)
            with col1:
                time_start = st.text_input("開始時間", value=element.get_property("time_start", ""))
                if time_start != element.get_property("time_start") and self.on_option_change:
                    self.on_option_change("time_start", time_start)
            
            with col2:
                time_end = st.text_input("終了時間", value=element.get_property("time_end", ""))
                if time_end != element.get_property("time_end") and self.on_option_change:
                    self.on_option_change("time_end", time_end)
            
            time_key = st.text_input("時間キー", value=element.get_property("time_key", "timestamp"))
            if time_key != element.get_property("time_key") and self.on_option_change:
                self.on_option_change("time_key", time_key)
        
        # データキー設定
        st.subheader("データキー設定")
        
        # 方位別の値キー
        direction_key = st.text_input("方位キー", value=element.get_property("direction_key", "direction"))
        if direction_key != element.get_property("direction_key") and self.on_option_change:
            self.on_option_change("direction_key", direction_key)
        
        value_key = st.text_input("値キー", value=element.get_property("value_key", "value"))
        if value_key != element.get_property("value_key") and self.on_option_change:
            self.on_option_change("value_key", value_key)
        
        # 表示設定
        st.subheader("表示設定")
        
        # ラベル表示
        show_labels = st.checkbox("値のラベルを表示", value=element.get_property("show_labels", False))
        if show_labels != element.get_property("show_labels") and self.on_option_change:
            self.on_option_change("show_labels", show_labels)
        
        # 角度ラインの表示
        angle_lines_enabled = st.checkbox("角度ラインを表示", value=element.get_property("angle_lines_enabled", True))
        if angle_lines_enabled != element.get_property("angle_lines_enabled") and self.on_option_change:
            self.on_option_change("angle_lines_enabled", angle_lines_enabled)
            
        if angle_lines_enabled:
            angle_lines_color = st.color_picker("角度ラインの色", value=element.get_property("angle_lines_color", "rgba(0, 0, 0, 0.1)"))
            if angle_lines_color != element.get_property("angle_lines_color") and self.on_option_change:
                self.on_option_change("angle_lines_color", angle_lines_color)
    
    def _render_course_performance_options(self, element: CoursePerformanceElement) -> None:
        """コースパフォーマンスグラフのオプション設定UI"""
        # 角度分割数
        angle_divisions = st.slider("角度分割数", min_value=12, max_value=72, value=element.get_property("angle_divisions", 36), step=6)
        if angle_divisions != element.get_property("angle_divisions") and self.on_option_change:
            self.on_option_change("angle_divisions", angle_divisions)
        
        # 角度キー
        angle_key = st.text_input("角度キー", value=element.get_property("angle_key", "angle"))
        if angle_key != element.get_property("angle_key") and self.on_option_change:
            self.on_option_change("angle_key", angle_key)
        
        # 平均化方法
        avg_methods = ["mean", "max"]
        avg_method = st.selectbox(
            "重複値の平均化方法",
            options=avg_methods,
            format_func=lambda x: {"mean": "平均値", "max": "最大値"}.get(x, x),
            index=avg_methods.index(element.get_property("average_method", "mean")) if element.get_property("average_method") in avg_methods else 0
        )
        if avg_method != element.get_property("average_method") and self.on_option_change:
            self.on_option_change("average_method", avg_method)
        
        # ラベルのカスタマイズ
        st.subheader("データセットラベル")
        col1, col2, col3 = st.columns(3)
        with col1:
            actual_label = st.text_input("実績データラベル", value=element.get_property("actual_label", "実績速度"))
            if actual_label != element.get_property("actual_label") and self.on_option_change:
                self.on_option_change("actual_label", actual_label)
        
        with col2:
            target_label = st.text_input("ターゲットデータラベル", value=element.get_property("target_label", "ターゲット速度"))
            if target_label != element.get_property("target_label") and self.on_option_change:
                self.on_option_change("target_label", target_label)
        
        with col3:
            vmg_label = st.text_input("VMGデータラベル", value=element.get_property("vmg_label", "VMG"))
            if vmg_label != element.get_property("vmg_label") and self.on_option_change:
                self.on_option_change("vmg_label", vmg_label)
    
    def _render_tacking_angle_options(self, element: TackingAngleElement) -> None:
        """タッキングアングル分析のオプション設定UI"""
        # ビンの数
        num_bins = st.slider("ビンの数", min_value=5, max_value=30, value=element.get_property("num_bins", 18))
        if num_bins != element.get_property("num_bins") and self.on_option_change:
            self.on_option_change("num_bins", num_bins)
        
        # 角度範囲
        col1, col2 = st.columns(2)
        with col1:
            min_angle = st.number_input("最小角度", min_value=0, max_value=180, value=element.get_property("min_angle", 70))
            if min_angle != element.get_property("min_angle") and self.on_option_change:
                self.on_option_change("min_angle", min_angle)
        
        with col2:
            max_angle = st.number_input("最大角度", min_value=0, max_value=180, value=element.get_property("max_angle", 140))
            if max_angle != element.get_property("max_angle") and self.on_option_change:
                self.on_option_change("max_angle", max_angle)
        
        # 最適角度範囲
        st.subheader("最適角度範囲")
        col1, col2 = st.columns(2)
        with col1:
            optimal_min = st.number_input("最適角度（最小）", min_value=min_angle, max_value=max_angle, value=element.get_property("optimal_min", 85))
            if optimal_min != element.get_property("optimal_min") and self.on_option_change:
                self.on_option_change("optimal_min", optimal_min)
        
        with col2:
            optimal_max = st.number_input("最適角度（最大）", min_value=min_angle, max_value=max_angle, value=element.get_property("optimal_max", 95))
            if optimal_max != element.get_property("optimal_max") and self.on_option_change:
                self.on_option_change("optimal_max", optimal_max)
        
        # 角度キー
        angle_key = st.text_input("角度キー", value=element.get_property("angle_key", "tacking_angle"))
        if angle_key != element.get_property("angle_key") and self.on_option_change:
            self.on_option_change("angle_key", angle_key)
    
    def _render_strategy_point_map_options(self, element: StrategyPointMapElement) -> None:
        """戦略ポイントマップのオプション設定UI"""
        # マップの中心位置と拡大レベル
        st.subheader("マップの設定")
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.number_input("中心緯度", value=element.get_property("center_lat", 35.4498), format="%.6f")
            if center_lat != element.get_property("center_lat") and self.on_option_change:
                self.on_option_change("center_lat", center_lat)
        
        with col2:
            center_lng = st.number_input("中心経度", value=element.get_property("center_lng", 139.6649), format="%.6f")
            if center_lng != element.get_property("center_lng") and self.on_option_change:
                self.on_option_change("center_lng", center_lng)
        
        zoom_level = st.slider("拡大レベル", min_value=1, max_value=18, value=element.get_property("zoom_level", 13))
        if zoom_level != element.get_property("zoom_level") and self.on_option_change:
            self.on_option_change("zoom_level", zoom_level)
        
        # 自動センタリング
        center_auto = st.checkbox("データに基づいて自動的に中心を決定", value=element.get_property("center_auto", True))
        if center_auto != element.get_property("center_auto") and self.on_option_change:
            self.on_option_change("center_auto", center_auto)
        
        # ポイントタイプ別のアイコン設定
        st.subheader("ポイントタイプ別のアイコン設定")
        
        # 現在のアイコン設定を取得
        icon_config = element.get_property("icon_config", {
            "tack": {"color": "blue", "icon": "exchange-alt"},
            "gybe": {"color": "green", "icon": "random"},
            "mark_rounding": {"color": "red", "icon": "flag"},
            "wind_shift": {"color": "purple", "icon": "wind"},
            "default": {"color": "gray", "icon": "map-marker"}
        })
        
        # アイコン設定の編集
        point_types = ["tack", "gybe", "mark_rounding", "wind_shift", "default"]
        for point_type in point_types:
            st.subheader(f"{point_type} ポイント")
            config = icon_config.get(point_type, {"color": "gray", "icon": "map-marker"})
            
            col1, col2 = st.columns(2)
            with col1:
                color = st.color_picker(f"{point_type} 色", value=config.get("color", "gray"))
                if color != config.get("color") and self.on_option_change:
                    config["color"] = color
                    icon_config[point_type] = config
                    self.on_option_change("icon_config", icon_config)
            
            with col2:
                icon = st.text_input(f"{point_type} アイコン", value=config.get("icon", "map-marker"))
                if icon != config.get("icon") and self.on_option_change:
                    config["icon"] = icon
                    icon_config[point_type] = config
                    self.on_option_change("icon_config", icon_config)
    
    def _render_time_series_options(self, element: TimeSeriesElement) -> None:
        """時系列分析グラフのオプション設定UI"""
        # 時間列
        time_key = st.text_input("時間キー", value=element.get_property("time_key", "time"))
        if time_key != element.get_property("time_key") and self.on_option_change:
            self.on_option_change("time_key", time_key)
        
        # 表示パラメータ
        value_keys_str = st.text_input("表示パラメータ（カンマ区切り）", value=", ".join(element.get_property("value_keys", [])))
        value_keys = [key.strip() for key in value_keys_str.split(",") if key.strip()]
        if value_keys != element.get_property("value_keys") and self.on_option_change:
            self.on_option_change("value_keys", value_keys)
        
        # 軸タイトル
        col1, col2 = st.columns(2)
        with col1:
            x_axis_title = st.text_input("X軸タイトル", value=element.get_property("x_axis_title", "時間"))
            if x_axis_title != element.get_property("x_axis_title") and self.on_option_change:
                self.on_option_change("x_axis_title", x_axis_title)
        
        with col2:
            y_axis_title = st.text_input("Y軸タイトル", value=element.get_property("y_axis_title", "値"))
            if y_axis_title != element.get_property("y_axis_title") and self.on_option_change:
                self.on_option_change("y_axis_title", y_axis_title)
        
        # 時間単位
        time_units = ["millisecond", "second", "minute", "hour", "day", "week", "month", "year"]
        time_unit = st.selectbox(
            "時間単位",
            options=time_units,
            format_func=lambda x: {
                "millisecond": "ミリ秒", "second": "秒", "minute": "分", "hour": "時", 
                "day": "日", "week": "週", "month": "月", "year": "年"
            }.get(x, x),
            index=time_units.index(element.get_property("time_unit", "minute")) if element.get_property("time_unit") in time_units else 2
        )
        if time_unit != element.get_property("time_unit") and self.on_option_change:
            self.on_option_change("time_unit", time_unit)
        
        # Y軸の設定
        begin_at_zero = st.checkbox("Y軸を0から開始", value=element.get_property("begin_at_zero", False))
        if begin_at_zero != element.get_property("begin_at_zero") and self.on_option_change:
            self.on_option_change("begin_at_zero", begin_at_zero)
        
        # 移動平均
        show_ma = st.checkbox("移動平均を表示", value=element.get_property("moving_average", False))
        if show_ma != element.get_property("moving_average") and self.on_option_change:
            self.on_option_change("moving_average", show_ma)
        
        if show_ma:
            window_size = st.slider("窓サイズ", min_value=3, max_value=31, value=element.get_property("moving_average_window", 5), step=2)
            if window_size != element.get_property("moving_average_window") and self.on_option_change:
                self.on_option_change("moving_average_window", window_size)
        
        # トレンドライン
        show_trendline = st.checkbox("トレンドラインを表示", value=element.get_property("trendline", False))
        if show_trendline != element.get_property("trendline") and self.on_option_change:
            self.on_option_change("trendline", show_trendline)
        
        # 異常値ハイライト
        show_outliers = st.checkbox("異常値をハイライト", value=element.get_property("highlight_outliers", False))
        if show_outliers != element.get_property("highlight_outliers") and self.on_option_change:
            self.on_option_change("highlight_outliers", show_outliers)
        
        if show_outliers:
            threshold = st.slider("異常値しきい値（標準偏差の倍数）", min_value=1.0, max_value=5.0, value=element.get_property("outlier_threshold", 2.0), step=0.1)
            if threshold != element.get_property("outlier_threshold") and self.on_option_change:
                self.on_option_change("outlier_threshold", threshold)
    
    def _render_box_plot_options(self, element: BoxPlotElement) -> None:
        """ボックスプロットのオプション設定UI"""
        # グループと値のキー
        col1, col2 = st.columns(2)
        with col1:
            group_key = st.text_input("グループキー", value=element.get_property("group_key", "group"))
            if group_key != element.get_property("group_key") and self.on_option_change:
                self.on_option_change("group_key", group_key)
        
        with col2:
            value_key = st.text_input("値キー", value=element.get_property("value_key", "value"))
            if value_key != element.get_property("value_key") and self.on_option_change:
                self.on_option_change("value_key", value_key)
        
        # 軸タイトル
        col1, col2 = st.columns(2)
        with col1:
            x_axis_title = st.text_input("X軸タイトル", value=element.get_property("x_axis_title", "グループ"))
            if x_axis_title != element.get_property("x_axis_title") and self.on_option_change:
                self.on_option_change("x_axis_title", x_axis_title)
        
        with col2:
            y_axis_title = st.text_input("Y軸タイトル", value=element.get_property("y_axis_title", "値"))
            if y_axis_title != element.get_property("y_axis_title") and self.on_option_change:
                self.on_option_change("y_axis_title", y_axis_title)
        
        # Y軸の設定
        begin_at_zero = st.checkbox("Y軸を0から開始", value=element.get_property("begin_at_zero", False))
        if begin_at_zero != element.get_property("begin_at_zero") and self.on_option_change:
            self.on_option_change("begin_at_zero", begin_at_zero)
        
        # データセットラベル
        dataset_label = st.text_input("データセットラベル", value=element.get_property("dataset_label", "データ分布"))
        if dataset_label != element.get_property("dataset_label") and self.on_option_change:
            self.on_option_change("dataset_label", dataset_label)
        
        # マルチデータセット
        show_multi = st.checkbox("複数データセットを設定", value=bool(element.get_property("multi_datasets")))
        
        if show_multi:
            st.info("この機能はUIで現在開発中です。JSONエディタで直接設定することができます。")
            multi_datasets = element.get_property("multi_datasets", [])
            multi_datasets_json = st.text_area("マルチデータセット設定（JSON）", value=json.dumps(multi_datasets, indent=2, ensure_ascii=False))
            
            try:
                new_multi_datasets = json.loads(multi_datasets_json)
                if new_multi_datasets != multi_datasets and self.on_option_change:
                    self.on_option_change("multi_datasets", new_multi_datasets)
            except json.JSONDecodeError:
                st.error("JSONの形式が正しくありません。")
    
    def _render_heat_map_options(self, element: HeatMapElement) -> None:
        """ヒートマップのオプション設定UI"""
        # X軸とY軸のラベル設定
        st.subheader("軸ラベル")
        col1, col2 = st.columns(2)
        with col1:
            x_labels_str = st.text_input("X軸ラベル（カンマ区切り）", value=", ".join(element.get_property("x_labels", [])))
            x_labels = [label.strip() for label in x_labels_str.split(",") if label.strip()]
            if x_labels != element.get_property("x_labels") and self.on_option_change:
                self.on_option_change("x_labels", x_labels)
        
        with col2:
            y_labels_str = st.text_input("Y軸ラベル（カンマ区切り）", value=", ".join(element.get_property("y_labels", [])))
            y_labels = [label.strip() for label in y_labels_str.split(",") if label.strip()]
            if y_labels != element.get_property("y_labels") and self.on_option_change:
                self.on_option_change("y_labels", y_labels)
        
        # データキー
        st.subheader("データキー")
        col1, col2, col3 = st.columns(3)
        with col1:
            x_key = st.text_input("X位置キー", value=element.get_property("x_key", "x"))
            if x_key != element.get_property("x_key") and self.on_option_change:
                self.on_option_change("x_key", x_key)
        
        with col2:
            y_key = st.text_input("Y位置キー", value=element.get_property("y_key", "y"))
            if y_key != element.get_property("y_key") and self.on_option_change:
                self.on_option_change("y_key", y_key)
        
        with col3:
            value_key = st.text_input("値キー", value=element.get_property("value_key", "value"))
            if value_key != element.get_property("value_key") and self.on_option_change:
                self.on_option_change("value_key", value_key)
        
        # 軸タイトル
        col1, col2 = st.columns(2)
        with col1:
            x_axis_title = st.text_input("X軸タイトル", value=element.get_property("x_axis_title", "X軸"))
            if x_axis_title != element.get_property("x_axis_title") and self.on_option_change:
                self.on_option_change("x_axis_title", x_axis_title)
        
        with col2:
            y_axis_title = st.text_input("Y軸タイトル", value=element.get_property("y_axis_title", "Y軸"))
            if y_axis_title != element.get_property("y_axis_title") and self.on_option_change:
                self.on_option_change("y_axis_title", y_axis_title)
        
        # セル設定
        st.subheader("セル設定")
        col1, col2 = st.columns(2)
        with col1:
            cell_width = st.number_input("セル幅", min_value=5, max_value=100, value=element.get_property("cell_width", 30))
            if cell_width != element.get_property("cell_width") and self.on_option_change:
                self.on_option_change("cell_width", cell_width)
        
        with col2:
            cell_height = st.number_input("セル高さ", min_value=5, max_value=100, value=element.get_property("cell_height", 30))
            if cell_height != element.get_property("cell_height") and self.on_option_change:
                self.on_option_change("cell_height", cell_height)
        
        # カラースケール
        st.subheader("カラースケール")
        color_scale = element.get_property("color_scale", [
            "rgba(0, 0, 255, 0.5)",  # 青 (低)
            "rgba(0, 255, 255, 0.5)",  # シアン
            "rgba(0, 255, 0, 0.5)",  # 緑
            "rgba(255, 255, 0, 0.5)",  # 黄
            "rgba(255, 0, 0, 0.5)"   # 赤 (高)
        ])
        
        cols = st.columns(len(color_scale))
        for i, color in enumerate(color_scale):
            with cols[i]:
                new_color = st.color_picker(f"色 {i+1}", color)
                if new_color != color and self.on_option_change:
                    color_scale[i] = new_color
                    self.on_option_change("color_scale", color_scale)
    
    def _render_correlation_options(self, element: CorrelationElement) -> None:
        """相関分析グラフのオプション設定UI"""
        # X軸とY軸のパラメータ
        col1, col2 = st.columns(2)
        with col1:
            x_param = st.text_input("X軸パラメータ", value=element.get_property("x_param", ""))
            if x_param != element.get_property("x_param") and self.on_option_change:
                self.on_option_change("x_param", x_param)
        
        with col2:
            y_param = st.text_input("Y軸パラメータ", value=element.get_property("y_param", ""))
            if y_param != element.get_property("y_param") and self.on_option_change:
                self.on_option_change("y_param", y_param)
        
        # 軸タイトル
        col1, col2 = st.columns(2)
        with col1:
            x_axis_title = st.text_input("X軸タイトル", value=element.get_property("x_axis_title", x_param))
            if x_axis_title != element.get_property("x_axis_title") and self.on_option_change:
                self.on_option_change("x_axis_title", x_axis_title)
        
        with col2:
            y_axis_title = st.text_input("Y軸タイトル", value=element.get_property("y_axis_title", y_param))
            if y_axis_title != element.get_property("y_axis_title") and self.on_option_change:
                self.on_option_change("y_axis_title", y_axis_title)
        
        # データセットラベル
        dataset_label = st.text_input("データセットラベル", value=element.get_property("dataset_label", f"{x_param} vs {y_param}"))
        if dataset_label != element.get_property("dataset_label") and self.on_option_change:
            self.on_option_change("dataset_label", dataset_label)
        
        # トレンドライン
        show_trendline = st.checkbox("トレンドラインを表示", value=element.get_property("show_trendline", True))
        if show_trendline != element.get_property("show_trendline") and self.on_option_change:
            self.on_option_change("show_trendline", show_trendline)
        
        if show_trendline:
            # 回帰タイプ
            regression_types = ["linear", "exponential", "power", "polynomial"]
            regression_type = st.selectbox(
                "回帰タイプ",
                options=regression_types,
                format_func=lambda x: {
                    "linear": "線形", "exponential": "指数", "power": "べき乗", "polynomial": "多項式"
                }.get(x, x),
                index=regression_types.index(element.get_property("regression_type", "linear")) if element.get_property("regression_type") in regression_types else 0
            )
            if regression_type != element.get_property("regression_type") and self.on_option_change:
                self.on_option_change("regression_type", regression_type)
            
            # トレンドラインラベル
            trendline_label = st.text_input("トレンドラインラベル", value=element.get_property("trendline_label", "回帰直線"))
            if trendline_label != element.get_property("trendline_label") and self.on_option_change:
                self.on_option_change("trendline_label", trendline_label)
    
    def _render_track_map_options(self, element: TrackMapElement) -> None:
        """航路追跡マップのオプション設定UI"""
        # マップの中心位置と拡大レベル
        st.subheader("マップの設定")
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.number_input("中心緯度", value=element.get_property("center_lat", 35.4498), format="%.6f")
            if center_lat != element.get_property("center_lat") and self.on_option_change:
                self.on_option_change("center_lat", center_lat)
        
        with col2:
            center_lng = st.number_input("中心経度", value=element.get_property("center_lng", 139.6649), format="%.6f")
            if center_lng != element.get_property("center_lng") and self.on_option_change:
                self.on_option_change("center_lng", center_lng)
        
        zoom_level = st.slider("拡大レベル", min_value=1, max_value=18, value=element.get_property("zoom_level", 13))
        if zoom_level != element.get_property("zoom_level") and self.on_option_change:
            self.on_option_change("zoom_level", zoom_level)
        
        # 自動センタリング
        center_auto = st.checkbox("データに基づいて自動的に中心を決定", value=element.get_property("center_auto", True))
        if center_auto != element.get_property("center_auto") and self.on_option_change:
            self.on_option_change("center_auto", center_auto)
        
        # マップタイプ
        map_types = ["osm", "satellite", "nautical"]
        map_type = st.selectbox(
            "マップタイプ",
            options=map_types,
            format_func=lambda x: {"osm": "OpenStreetMap", "satellite": "衛星画像", "nautical": "海図"}.get(x, x),
            index=map_types.index(element.get_property("map_type", "osm")) if element.get_property("map_type") in map_types else 0
        )
        if map_type != element.get_property("map_type") and self.on_option_change:
            self.on_option_change("map_type", map_type)
        
        # トラックの設定
        st.subheader("トラックの設定")
        track_color = st.color_picker("トラック色", value=element.get_property("track_color", "rgba(255, 87, 34, 0.8)"))
        if track_color != element.get_property("track_color") and self.on_option_change:
            self.on_option_change("track_color", track_color)
        
        track_width = st.slider("トラック幅", min_value=1, max_value=10, value=element.get_property("track_width", 3))
        if track_width != element.get_property("track_width") and self.on_option_change:
            self.on_option_change("track_width", track_width)
        
        # タイムスライダー
        show_time_slider = st.checkbox("タイムスライダーを表示", value=element.get_property("show_time_slider", False))
        if show_time_slider != element.get_property("show_time_slider") and self.on_option_change:
            self.on_option_change("show_time_slider", show_time_slider)
        
        if show_time_slider:
            time_key = st.text_input("時間キー", value=element.get_property("time_key", "timestamp"))
            if time_key != element.get_property("time_key") and self.on_option_change:
                self.on_option_change("time_key", time_key)
    
    def _render_heat_map_layer_options(self, element: HeatMapLayerElement) -> None:
        """ヒートマップレイヤーのオプション設定UI"""
        # マップの中心位置と拡大レベル
        st.subheader("マップの設定")
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.number_input("中心緯度", value=element.get_property("center_lat", 35.4498), format="%.6f")
            if center_lat != element.get_property("center_lat") and self.on_option_change:
                self.on_option_change("center_lat", center_lat)
        
        with col2:
            center_lng = st.number_input("中心経度", value=element.get_property("center_lng", 139.6649), format="%.6f")
            if center_lng != element.get_property("center_lng") and self.on_option_change:
                self.on_option_change("center_lng", center_lng)
        
        zoom_level = st.slider("拡大レベル", min_value=1, max_value=18, value=element.get_property("zoom_level", 13))
        if zoom_level != element.get_property("zoom_level") and self.on_option_change:
            self.on_option_change("zoom_level", zoom_level)
        
        # 自動センタリング
        center_auto = st.checkbox("データに基づいて自動的に中心を決定", value=element.get_property("center_auto", True))
        if center_auto != element.get_property("center_auto") and self.on_option_change:
            self.on_option_change("center_auto", center_auto)
        
        # マップタイプ
        map_types = ["osm", "satellite", "nautical"]
        map_type = st.selectbox(
            "マップタイプ",
            options=map_types,
            format_func=lambda x: {"osm": "OpenStreetMap", "satellite": "衛星画像", "nautical": "海図"}.get(x, x),
            index=map_types.index(element.get_property("map_type", "osm")) if element.get_property("map_type") in map_types else 0
        )
        if map_type != element.get_property("map_type") and self.on_option_change:
            self.on_option_change("map_type", map_type)
        
        # ヒートマップの設定
        st.subheader("ヒートマップの設定")
        heat_value_key = st.text_input("ヒート値キー", value=element.get_property("heat_value_key", "value"))
        if heat_value_key != element.get_property("heat_value_key") and self.on_option_change:
            self.on_option_change("heat_value_key", heat_value_key)
        
        col1, col2 = st.columns(2)
        with col1:
            radius = st.slider("半径", min_value=5, max_value=50, value=element.get_property("radius", 25))
            if radius != element.get_property("radius") and self.on_option_change:
                self.on_option_change("radius", radius)
        
        with col2:
            blur = st.slider("ぼかし", min_value=5, max_value=30, value=element.get_property("blur", 15))
            if blur != element.get_property("blur") and self.on_option_change:
                self.on_option_change("blur", blur)
        
        # 最大値の設定
        max_value = st.number_input("最大値（0の場合は自動）", min_value=0.0, value=float(element.get_property("max_value", 0)))
        if max_value != element.get_property("max_value") and self.on_option_change:
            self.on_option_change("max_value", max_value)
        
        # カラーグラデーション
        st.subheader("カラーグラデーション")
        gradient = element.get_property("gradient", {
            "0.4": "blue",
            "0.6": "cyan",
            "0.7": "lime",
            "0.8": "yellow",
            "1.0": "red"
        })
        
        key_values = sorted([(float(k), v) for k, v in gradient.items()])
        col1, col2 = st.columns(2)
        
        updated = False
        for i, (key, value) in enumerate(key_values):
            if i % 2 == 0:
                with col1:
                    new_value = st.color_picker(f"強度 {key}", value)
                    if new_value != value:
                        gradient[str(key)] = new_value
                        updated = True
            else:
                with col2:
                    new_value = st.color_picker(f"強度 {key}", value)
                    if new_value != value:
                        gradient[str(key)] = new_value
                        updated = True
        
        if updated and self.on_option_change:
            self.on_option_change("gradient", gradient)
        
        # トラックの表示
        show_track = st.checkbox("トラックを表示", value=element.get_property("show_track", True))
        if show_track != element.get_property("show_track") and self.on_option_change:
            self.on_option_change("show_track", show_track)
        
        if show_track:
            track_color = st.color_picker("トラック色", value=element.get_property("track_color", "rgba(255, 255, 255, 0.6)"))
            if track_color != element.get_property("track_color") and self.on_option_change:
                self.on_option_change("track_color", track_color)
            
            track_width = st.slider("トラック幅", min_value=1, max_value=10, value=element.get_property("track_width", 2))
            if track_width != element.get_property("track_width") and self.on_option_change:
                self.on_option_change("track_width", track_width)
    
    def _render_strategy_point_layer_options(self, element: StrategyPointLayerElement) -> None:
        """戦略ポイントレイヤーのオプション設定UI"""
        # マップの中心位置と拡大レベル
        st.subheader("マップの設定")
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.number_input("中心緯度", value=element.get_property("center_lat", 35.4498), format="%.6f")
            if center_lat != element.get_property("center_lat") and self.on_option_change:
                self.on_option_change("center_lat", center_lat)
        
        with col2:
            center_lng = st.number_input("中心経度", value=element.get_property("center_lng", 139.6649), format="%.6f")
            if center_lng != element.get_property("center_lng") and self.on_option_change:
                self.on_option_change("center_lng", center_lng)
        
        zoom_level = st.slider("拡大レベル", min_value=1, max_value=18, value=element.get_property("zoom_level", 13))
        if zoom_level != element.get_property("zoom_level") and self.on_option_change:
            self.on_option_change("zoom_level", zoom_level)
        
        # 自動センタリング
        center_auto = st.checkbox("データに基づいて自動的に中心を決定", value=element.get_property("center_auto", True))
        if center_auto != element.get_property("center_auto") and self.on_option_change:
            self.on_option_change("center_auto", center_auto)
        
        # マップタイプ
        map_types = ["osm", "satellite", "nautical"]
        map_type = st.selectbox(
            "マップタイプ",
            options=map_types,
            format_func=lambda x: {"osm": "OpenStreetMap", "satellite": "衛星画像", "nautical": "海図"}.get(x, x),
            index=map_types.index(element.get_property("map_type", "osm")) if element.get_property("map_type") in map_types else 0
        )
        if map_type != element.get_property("map_type") and self.on_option_change:
            self.on_option_change("map_type", map_type)
        
        # トラックの表示
        show_track = st.checkbox("トラックを表示", value=element.get_property("show_track", True))
        if show_track != element.get_property("show_track") and self.on_option_change:
            self.on_option_change("show_track", show_track)
        
        if show_track:
            track_color = st.color_picker("トラック色", value=element.get_property("track_color", "rgba(54, 162, 235, 0.8)"))
            if track_color != element.get_property("track_color") and self.on_option_change:
                self.on_option_change("track_color", track_color)
            
            track_width = st.slider("トラック幅", min_value=1, max_value=10, value=element.get_property("track_width", 3))
            if track_width != element.get_property("track_width") and self.on_option_change:
                self.on_option_change("track_width", track_width)
        
        # ポイントアイコン設定
        st.subheader("ポイントアイコン設定")
        
        # 現在のアイコン設定を取得
        point_icons = element.get_property("point_icons", {
            "tack": {"color": "blue", "icon": "exchange-alt"},
            "gybe": {"color": "green", "icon": "random"},
            "mark_rounding": {"color": "red", "icon": "flag-checkered"},
            "wind_shift": {"color": "purple", "icon": "wind"},
            "default": {"color": "gray", "icon": "map-marker-alt"}
        })
        
        # アイコン設定の編集
        point_types = ["tack", "gybe", "mark_rounding", "wind_shift", "default"]
        for point_type in point_types:
            st.subheader(f"{point_type} ポイント")
            config = point_icons.get(point_type, {"color": "gray", "icon": "map-marker-alt"})
            
            col1, col2 = st.columns(2)
            with col1:
                color = st.color_picker(f"{point_type} 色", value=config.get("color", "gray"))
                if color != config.get("color") and self.on_option_change:
                    config["color"] = color
                    point_icons[point_type] = config
                    self.on_option_change("point_icons", point_icons)
            
            with col2:
                icon = st.text_input(f"{point_type} アイコン", value=config.get("icon", "map-marker-alt"))
                if icon != config.get("icon") and self.on_option_change:
                    config["icon"] = icon
                    point_icons[point_type] = config
                    self.on_option_change("point_icons", point_icons)
    
    def _render_wind_field_options(self, element: WindFieldElement) -> None:
        """風場の可視化のオプション設定UI"""
        # マップの中心位置と拡大レベル
        st.subheader("マップの設定")
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.number_input("中心緯度", value=element.get_property("center_lat", 35.4498), format="%.6f")
            if center_lat != element.get_property("center_lat") and self.on_option_change:
                self.on_option_change("center_lat", center_lat)
        
        with col2:
            center_lng = st.number_input("中心経度", value=element.get_property("center_lng", 139.6649), format="%.6f")
            if center_lng != element.get_property("center_lng") and self.on_option_change:
                self.on_option_change("center_lng", center_lng)
        
        zoom_level = st.slider("拡大レベル", min_value=1, max_value=18, value=element.get_property("zoom_level", 13))
        if zoom_level != element.get_property("zoom_level") and self.on_option_change:
            self.on_option_change("zoom_level", zoom_level)
        
        # 自動センタリング
        center_auto = st.checkbox("データに基づいて自動的に中心を決定", value=element.get_property("center_auto", True))
        if center_auto != element.get_property("center_auto") and self.on_option_change:
            self.on_option_change("center_auto", center_auto)
        
        # マップタイプ
        map_types = ["osm", "satellite", "nautical"]
        map_type = st.selectbox(
            "マップタイプ",
            options=map_types,
            format_func=lambda x: {"osm": "OpenStreetMap", "satellite": "衛星画像", "nautical": "海図"}.get(x, x),
            index=map_types.index(element.get_property("map_type", "osm")) if element.get_property("map_type") in map_types else 0
        )
        if map_type != element.get_property("map_type") and self.on_option_change:
            self.on_option_change("map_type", map_type)
        
        # 風場の設定
        st.subheader("風場の設定")
        
        wind_speed_scale = st.number_input("風速スケール", min_value=0.001, max_value=0.1, value=element.get_property("wind_speed_scale", 0.01), format="%.3f", step=0.001)
        if wind_speed_scale != element.get_property("wind_speed_scale") and self.on_option_change:
            self.on_option_change("wind_speed_scale", wind_speed_scale)
        
        col1, col2 = st.columns(2)
        with col1:
            min_velocity = st.number_input("最小風速", min_value=0, max_value=20, value=element.get_property("min_velocity", 0))
            if min_velocity != element.get_property("min_velocity") and self.on_option_change:
                self.on_option_change("min_velocity", min_velocity)
        
        with col2:
            max_velocity = st.number_input("最大風速", min_value=1, max_value=50, value=element.get_property("max_velocity", 15))
            if max_velocity != element.get_property("max_velocity") and self.on_option_change:
                self.on_option_change("max_velocity", max_velocity)
        
        # 単位
        velocity_units = st.selectbox(
            "風速単位",
            options=["kt", "m/s", "km/h", "mph"],
            format_func=lambda x: {"kt": "ノット (kt)", "m/s": "メートル毎秒 (m/s)", "km/h": "キロメートル毎時 (km/h)", "mph": "マイル毎時 (mph)"}.get(x, x),
            index=["kt", "m/s", "km/h", "mph"].index(element.get_property("velocity_units", "kt")) if element.get_property("velocity_units") in ["kt", "m/s", "km/h", "mph"] else 0
        )
        if velocity_units != element.get_property("velocity_units") and self.on_option_change:
            self.on_option_change("velocity_units", velocity_units)
        
        # トラックの表示
        show_track = st.checkbox("トラックを表示", value=element.get_property("show_track", True))
        if show_track != element.get_property("show_track") and self.on_option_change:
            self.on_option_change("show_track", show_track)
        
        if show_track:
            track_color = st.color_picker("トラック色", value=element.get_property("track_color", "rgba(54, 162, 235, 0.8)"))
            if track_color != element.get_property("track_color") and self.on_option_change:
                self.on_option_change("track_color", track_color)
            
            track_width = st.slider("トラック幅", min_value=1, max_value=10, value=element.get_property("track_width", 3))
            if track_width != element.get_property("track_width") and self.on_option_change:
                self.on_option_change("track_width", track_width)
    
    def _render_event_timeline_options(self, element: EventTimelineElement) -> None:
        """イベントタイムラインのオプション設定UI"""
        # キー設定
        st.subheader("データキー")
        col1, col2 = st.columns(2)
        with col1:
            time_key = st.text_input("時間キー", value=element.get_property("time_key", "time"))
            if time_key != element.get_property("time_key") and self.on_option_change:
                self.on_option_change("time_key", time_key)
        
        with col2:
            event_key = st.text_input("イベントキー", value=element.get_property("event_key", "event"))
            if event_key != element.get_property("event_key") and self.on_option_change:
                self.on_option_change("event_key", event_key)
        
        col1, col2 = st.columns(2)
        with col1:
            group_key = st.text_input("グループキー", value=element.get_property("group_key", "group"))
            if group_key != element.get_property("group_key") and self.on_option_change:
                self.on_option_change("group_key", group_key)
        
        with col2:
            content_key = st.text_input("内容キー", value=element.get_property("content_key", "content"))
            if content_key != element.get_property("content_key") and self.on_option_change:
                self.on_option_change("content_key", content_key)
        
        # 表示オプション
        st.subheader("表示オプション")
        
        show_groups = st.checkbox("グループを表示", value=element.get_property("show_groups", True))
        if show_groups != element.get_property("show_groups") and self.on_option_change:
            self.on_option_change("show_groups", show_groups)
        
        show_tooltips = st.checkbox("ツールチップを表示", value=element.get_property("show_tooltips", True))
        if show_tooltips != element.get_property("show_tooltips") and self.on_option_change:
            self.on_option_change("show_tooltips", show_tooltips)
        
        cluster_events = st.checkbox("近接イベントをクラスタリング", value=element.get_property("cluster_events", True))
        if cluster_events != element.get_property("cluster_events") and self.on_option_change:
            self.on_option_change("cluster_events", cluster_events)
        
        # イベント色の設定
        st.subheader("イベント色")
        
        # 現在のイベント色を取得
        event_colors = element.get_property("event_colors", {
            "tack": "blue",
            "gybe": "green",
            "mark_rounding": "red",
            "wind_shift": "purple",
            "default": "gray"
        })
        
        # イベント色の編集
        event_types = ["tack", "gybe", "mark_rounding", "wind_shift", "default"]
        cols = st.columns(len(event_types))
        
        for i, event_type in enumerate(event_types):
            with cols[i]:
                color = st.color_picker(event_type, value=event_colors.get(event_type, "gray"))
                if color != event_colors.get(event_type) and self.on_option_change:
                    event_colors[event_type] = color
                    self.on_option_change("event_colors", event_colors)
    
    def _render_parameter_timeline_options(self, element: ParameterTimelineElement) -> None:
        """パラメータタイムラインのオプション設定UI"""
        # 時間キー
        time_key = st.text_input("時間キー", value=element.get_property("time_key", "time"))
        if time_key != element.get_property("time_key") and self.on_option_change:
            self.on_option_change("time_key", time_key)
        
        # パラメータ
        parameters_str = st.text_input("パラメータ（カンマ区切り）", value=", ".join(element.get_property("parameters", [])))
        parameters = [param.strip() for param in parameters_str.split(",") if param.strip()]
        if parameters != element.get_property("parameters") and self.on_option_change:
            self.on_option_change("parameters", parameters)
        
        # 自動検出
        auto_detect = st.checkbox("パラメータを自動検出", value=element.get_property("auto_detect", True))
        if auto_detect != element.get_property("auto_detect") and self.on_option_change:
            self.on_option_change("auto_detect", auto_detect)
        
        if auto_detect:
            excluded_keys_str = st.text_input("除外キー（カンマ区切り）", value=", ".join(element.get_property("excluded_keys", [time_key, "lat", "lng", "latitude", "longitude"])))
            excluded_keys = [key.strip() for key in excluded_keys_str.split(",") if key.strip()]
            if excluded_keys != element.get_property("excluded_keys") and self.on_option_change:
                self.on_option_change("excluded_keys", excluded_keys)
        
        # 表示オプション
        st.subheader("表示オプション")
        
        show_points = st.checkbox("ポイントを表示", value=element.get_property("show_points", True))
        if show_points != element.get_property("show_points") and self.on_option_change:
            self.on_option_change("show_points", show_points)
        
        if show_points:
            point_radius = st.slider("ポイント半径", min_value=0, max_value=10, value=element.get_property("point_radius", 2))
            if point_radius != element.get_property("point_radius") and self.on_option_change:
                self.on_option_change("point_radius", point_radius)
        
        brush_selection = st.checkbox("範囲選択を有効化", value=element.get_property("brush_selection", True))
        if brush_selection != element.get_property("brush_selection") and self.on_option_change:
            self.on_option_change("brush_selection", brush_selection)
    
    def _render_segment_comparison_options(self, element: SegmentComparisonElement) -> None:
        """セグメント比較のオプション設定UI"""
        # キー設定
        st.subheader("データキー")
        col1, col2, col3 = st.columns(3)
        with col1:
            segment_key = st.text_input("セグメントキー", value=element.get_property("segment_key", "segment"))
            if segment_key != element.get_property("segment_key") and self.on_option_change:
                self.on_option_change("segment_key", segment_key)
        
        with col2:
            session_key = st.text_input("セッションキー", value=element.get_property("session_key", "session"))
            if session_key != element.get_property("session_key") and self.on_option_change:
                self.on_option_change("session_key", session_key)
        
        with col3:
            value_key = st.text_input("値キー", value=element.get_property("value_key", "value"))
            if value_key != element.get_property("value_key") and self.on_option_change:
                self.on_option_change("value_key", value_key)
        
        # チャートタイプ
        chart_types = ["bar", "line", "radar"]
        chart_type = st.selectbox(
            "チャートタイプ",
            options=chart_types,
            format_func=lambda x: {"bar": "棒グラフ", "line": "折れ線グラフ", "radar": "レーダーチャート"}.get(x, x),
            index=chart_types.index(element.get_property("chart_type", "bar")) if element.get_property("chart_type") in chart_types else 0
        )
        if chart_type != element.get_property("chart_type") and self.on_option_change:
            self.on_option_change("chart_type", chart_type)
        
        # 表示オプション
        st.subheader("表示オプション")
        
        stack_data = st.checkbox("データを積み重ねる", value=element.get_property("stack_data", False))
        if stack_data != element.get_property("stack_data") and self.on_option_change:
            self.on_option_change("stack_data", stack_data)
        
        show_average = st.checkbox("平均値を表示", value=element.get_property("show_average", True))
        if show_average != element.get_property("show_average") and self.on_option_change:
            self.on_option_change("show_average", show_average)
        
        normalize_values = st.checkbox("値を正規化", value=element.get_property("normalize_values", False))
        if normalize_values != element.get_property("normalize_values") and self.on_option_change:
            self.on_option_change("normalize_values", normalize_values)
    
    def _render_data_viewer_options(self, element: DataViewerElement) -> None:
        """データビューアのオプション設定UI"""
        # 時間キー
        time_key = st.text_input("時間キー", value=element.get_property("time_key", "time"))
        if time_key != element.get_property("time_key") and self.on_option_change:
            self.on_option_change("time_key", time_key)
        
        # パラメータ
        parameters_str = st.text_input("パラメータ（カンマ区切り）", value=", ".join(element.get_property("parameters", [])))
        parameters = [param.strip() for param in parameters_str.split(",") if param.strip()]
        if parameters != element.get_property("parameters") and self.on_option_change:
            self.on_option_change("parameters", parameters)
        
        # 表示オプション
        st.subheader("表示パネル")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            map_view = st.checkbox("マップビューを表示", value=element.get_property("map_view", True))
            if map_view != element.get_property("map_view") and self.on_option_change:
                self.on_option_change("map_view", map_view)
        
        with col2:
            chart_view = st.checkbox("チャートビューを表示", value=element.get_property("chart_view", True))
            if chart_view != element.get_property("chart_view") and self.on_option_change:
                self.on_option_change("chart_view", chart_view)
        
        with col3:
            data_table = st.checkbox("データテーブルを表示", value=element.get_property("data_table", True))
            if data_table != element.get_property("data_table") and self.on_option_change:
                self.on_option_change("data_table", data_table)
