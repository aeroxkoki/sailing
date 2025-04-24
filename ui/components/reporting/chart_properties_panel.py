# -*- coding: utf-8 -*-
"""
ui.components.reporting.chart_properties_panel

チャート要素のプロパティ編集パネルを提供するモジュールです。
グラフ要素の詳細設定を行うためのUIコンポーネントを実装します。
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable, Union
import json

from sailing_data_processor.reporting.templates.template_model import (
    ElementType, ElementModel, Element
)
from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.elements.visualizations.basic_charts import (
    LineChartElement, ScatterChartElement, BarChartElement, PieChartElement
)
from sailing_data_processor.reporting.elements.visualizations.sailing_charts import (
    WindRoseElement, PolarDiagramElement, TackingAngleElement, CoursePerformanceElement
)


def render_chart_properties_panel(
    selected_element: Optional[Element] = None,
    chart_type: Optional[str] = None,
    on_property_change: Optional[Callable[[Dict[str, Any]], None]] = None,
    available_data_sources: Optional[List[str]] = None
) -> None:
    """
    チャート要素のプロパティパネルを描画

    Parameters
    ----------
    selected_element : Optional[Element], optional
        選択されたチャート要素, by default None
    chart_type : Optional[str], optional
        チャートタイプ（未選択の場合）, by default None
    on_property_change : Optional[Callable[[Dict[str, Any]], None]], optional
        プロパティ変更時のコールバック関数, by default None
    available_data_sources : Optional[List[str]], optional
        利用可能なデータソースのリスト, by default None
    """
    if available_data_sources is None:
        available_data_sources = []

    st.sidebar.header("チャートプロパティ")

    if selected_element is None and chart_type is None:
        st.sidebar.info("チャート要素を選択してください。")
        return

    # チャートタイプの選択（未選択の場合）
    if selected_element is None:
        _render_new_chart_properties(chart_type, on_property_change, available_data_sources)
    else:
        properties = selected_element.properties.copy()
        chart_type = properties.get("chart_type", "")
        
        # チャートタイプに応じたプロパティ編集UIを表示
        _render_chart_type_properties(chart_type, properties, on_property_change, available_data_sources)


def _render_new_chart_properties(
    chart_type: str,
    on_property_change: Optional[Callable[[Dict[str, Any]], None]] = None,
    available_data_sources: Optional[List[str]] = None
) -> None:
    """
    新しいチャート要素のプロパティを描画

    Parameters
    ----------
    chart_type : str
        チャートタイプ
    on_property_change : Optional[Callable[[Dict[str, Any]], None]], optional
        プロパティ変更時のコールバック関数, by default None
    available_data_sources : Optional[List[str]], optional
        利用可能なデータソースのリスト, by default None
    """
    st.sidebar.subheader(f"新規{chart_type}チャート")
    
    # 基本プロパティ
    properties = {}
    
    # データソースを選択
    data_source = ""
    if available_data_sources:
        data_source = st.sidebar.selectbox(
            "データソース",
            options=[""] + available_data_sources,
            index=0,
            key=f"new_chart_{chart_type}_data_source"
        )
    else:
        data_source = st.sidebar.text_input(
            "データソース", 
            "", 
            key=f"new_chart_{chart_type}_data_source"
        )
    
    # タイトル
    title = st.sidebar.text_input("タイトル", "", key=f"new_chart_{chart_type}_title")
    
    properties.update({
        "chart_type": chart_type,
        "data_source": data_source,
        "title": title
    })
    
    # チャートタイプ別のプロパティを追加
    properties = _add_chart_type_properties(chart_type, properties)
    
    # 作成ボタン
    if st.sidebar.button("チャートを作成", key=f"create_{chart_type}_chart"):
        if on_property_change:
            on_property_change(properties)


def _render_chart_type_properties(
    chart_type: str,
    properties: Dict[str, Any],
    on_property_change: Optional[Callable[[Dict[str, Any]], None]] = None,
    available_data_sources: Optional[List[str]] = None
) -> None:
    """
    チャートタイプに応じたプロパティ編集UIを描画

    Parameters
    ----------
    chart_type : str
        チャートタイプ
    properties : Dict[str, Any]
        現在のプロパティ
    on_property_change : Optional[Callable[[Dict[str, Any]], None]], optional
        プロパティ変更時のコールバック関数, by default None
    available_data_sources : Optional[List[str]], optional
        利用可能なデータソースのリスト, by default None
    """
    st.sidebar.subheader(f"{chart_type}チャート設定")
    
    # 基本情報
    with st.sidebar.expander("基本情報", expanded=True):
        # データソース
        if available_data_sources:
            current_idx = 0
            if properties.get("data_source") in available_data_sources:
                current_idx = available_data_sources.index(properties.get("data_source")) + 1
            
            data_source = st.selectbox(
                "データソース",
                options=[""] + available_data_sources,
                index=current_idx,
                key=f"edit_chart_{chart_type}_data_source"
            )
        else:
            data_source = st.text_input(
                "データソース", 
                properties.get("data_source", ""), 
                key=f"edit_chart_{chart_type}_data_source"
            )
        
        # タイトル
        title = st.text_input(
            "タイトル", 
            properties.get("title", ""),
            key=f"edit_chart_{chart_type}_title"
        )
        
        # レンダラータイプ
        renderer_options = ["chartjs", "plotly", "matplotlib"]
        renderer = st.selectbox(
            "レンダラー",
            options=renderer_options,
            index=renderer_options.index(properties.get("renderer", "chartjs")),
            key=f"edit_chart_{chart_type}_renderer"
        )
    
    # プロパティを更新
    properties.update({
        "data_source": data_source,
        "title": title,
        "renderer": renderer
    })
    
    # チャートタイプに応じたプロパティ編集UI
    properties = _add_chart_type_properties(chart_type, properties)
    
    # 変更の適用ボタン
    if st.sidebar.button("変更を適用", key=f"apply_{chart_type}_changes"):
        if on_property_change:
            on_property_change(properties)


def _add_chart_type_properties(
    chart_type: str,
    properties: Dict[str, Any]
) -> Dict[str, Any]:
    """
    チャートタイプに応じたプロパティを追加

    Parameters
    ----------
    chart_type : str
        チャートタイプ
    properties : Dict[str, Any]
        現在のプロパティ

    Returns
    -------
    Dict[str, Any]
        更新されたプロパティ
    """
    # 基本チャートタイプ
    if chart_type == "line":
        return _add_line_chart_properties(properties)
    elif chart_type == "scatter":
        return _add_scatter_chart_properties(properties)
    elif chart_type == "bar":
        return _add_bar_chart_properties(properties)
    elif chart_type == "pie":
        return _add_pie_chart_properties(properties)
    
    # セーリング特化型チャート
    elif chart_type == "windrose":
        return _add_windrose_chart_properties(properties)
    elif chart_type == "polar":
        return _add_polar_diagram_properties(properties)
    elif chart_type == "tacking":
        return _add_tacking_angle_properties(properties)
    elif chart_type == "course_performance":
        return _add_course_performance_properties(properties)
    
    # その他のチャートタイプ
    return properties


def _add_line_chart_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    折れ線グラフのプロパティを追加

    Parameters
    ----------
    properties : Dict[str, Any]
        現在のプロパティ

    Returns
    -------
    Dict[str, Any]
        更新されたプロパティ
    """
    with st.sidebar.expander("折れ線グラフ設定", expanded=True):
        # データフィールド
        x_field = st.text_input(
            "X軸フィールド", 
            properties.get("x_field", "x"),
            key="line_x_field"
        )
        
        y_field = st.text_input(
            "Y軸フィールド", 
            properties.get("y_field", "y"),
            key="line_y_field"
        )
        
        series_field = st.text_input(
            "シリーズフィールド（グループ分け）", 
            properties.get("series_field", ""),
            key="line_series_field"
        )
        
        # 軸設定
        x_axis_title = st.text_input(
            "X軸タイトル", 
            properties.get("x_axis_title", ""),
            key="line_x_axis_title"
        )
        
        y_axis_title = st.text_input(
            "Y軸タイトル", 
            properties.get("y_axis_title", ""),
            key="line_y_axis_title"
        )
        
        begin_at_zero = st.checkbox(
            "Y軸を0から開始", 
            properties.get("begin_at_zero", False),
            key="line_begin_at_zero"
        )
    
    with st.sidebar.expander("線の設定", expanded=False):
        # 線のスタイル設定
        line_style_options = ["solid", "dashed", "dotted"]
        line_style = st.selectbox(
            "線のスタイル",
            options=line_style_options,
            index=line_style_options.index(properties.get("line_style", "solid")),
            key="line_style"
        )
        
        # マーカー設定
        show_markers = st.checkbox(
            "マーカーを表示", 
            properties.get("show_markers", True),
            key="line_show_markers"
        )
        
        # 曲線の張力設定
        tension = st.slider(
            "曲線の張力", 
            min_value=0.0, 
            max_value=1.0, 
            value=properties.get("tension", 0.1),
            step=0.1,
            key="line_tension"
        )
        
        # トレンドライン表示
        show_trendline = st.checkbox(
            "トレンドラインを表示", 
            properties.get("show_trendline", False),
            key="line_show_trendline"
        )
        
        # 領域塗りつぶし設定
        fill_area = st.checkbox(
            "領域を塗りつぶす", 
            properties.get("fill_area", True),
            key="line_fill_area"
        )
    
    with st.sidebar.expander("表示設定", expanded=False):
        # 凡例表示
        show_legend = st.checkbox(
            "凡例を表示", 
            properties.get("show_legend", True),
            key="line_show_legend"
        )
        
        legend_position_options = ["top", "right", "bottom", "left"]
        legend_position = st.selectbox(
            "凡例の位置",
            options=legend_position_options,
            index=legend_position_options.index(properties.get("legend_position", "top")),
            key="line_legend_position"
        )
        
        # データラベル表示
        show_data_labels = st.checkbox(
            "データラベルを表示", 
            properties.get("show_data_labels", False),
            key="line_show_data_labels"
        )
        
        # グリッド表示
        show_x_grid = st.checkbox(
            "X軸グリッドを表示", 
            properties.get("show_x_grid", True),
            key="line_show_x_grid"
        )
        
        show_y_grid = st.checkbox(
            "Y軸グリッドを表示", 
            properties.get("show_y_grid", True),
            key="line_show_y_grid"
        )
        
        # アニメーション
        animation_duration = st.number_input(
            "アニメーション時間（ミリ秒）", 
            min_value=0, 
            max_value=2000, 
            value=properties.get("animation_duration", 1000),
            step=100,
            key="line_animation_duration"
        )
    
    # プロパティを更新
    properties.update({
        "x_field": x_field,
        "y_field": y_field,
        "series_field": series_field,
        "x_axis_title": x_axis_title,
        "y_axis_title": y_axis_title,
        "begin_at_zero": begin_at_zero,
        "line_style": line_style,
        "show_markers": show_markers,
        "tension": tension,
        "show_trendline": show_trendline,
        "fill_area": fill_area,
        "show_legend": show_legend,
        "legend_position": legend_position,
        "show_data_labels": show_data_labels,
        "show_x_grid": show_x_grid,
        "show_y_grid": show_y_grid,
        "animation_duration": animation_duration
    })
    
    return properties


def _add_scatter_chart_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    散布図のプロパティを追加

    Parameters
    ----------
    properties : Dict[str, Any]
        現在のプロパティ

    Returns
    -------
    Dict[str, Any]
        更新されたプロパティ
    """
    with st.sidebar.expander("散布図設定", expanded=True):
        # データフィールド
        x_field = st.text_input(
            "X軸フィールド", 
            properties.get("x_field", "x"),
            key="scatter_x_field"
        )
        
        y_field = st.text_input(
            "Y軸フィールド", 
            properties.get("y_field", "y"),
            key="scatter_y_field"
        )
        
        series_field = st.text_input(
            "シリーズフィールド（グループ分け）", 
            properties.get("series_field", ""),
            key="scatter_series_field"
        )
        
        # 軸設定
        x_axis_title = st.text_input(
            "X軸タイトル", 
            properties.get("x_axis_title", ""),
            key="scatter_x_axis_title"
        )
        
        y_axis_title = st.text_input(
            "Y軸タイトル", 
            properties.get("y_axis_title", ""),
            key="scatter_y_axis_title"
        )
        
        begin_at_zero = st.checkbox(
            "Y軸を0から開始", 
            properties.get("begin_at_zero", False),
            key="scatter_begin_at_zero"
        )
    
    with st.sidebar.expander("マーカー設定", expanded=False):
        # マーカースタイル設定
        point_style_options = ["circle", "cross", "star", "triangle", "rect"]
        point_style = st.selectbox(
            "マーカースタイル",
            options=point_style_options,
            index=point_style_options.index(properties.get("point_style", "circle")),
            key="scatter_point_style"
        )
        
        # マーカーサイズ
        point_radius = st.slider(
            "マーカーサイズ", 
            min_value=1, 
            max_value=20, 
            value=properties.get("point_radius", 5),
            key="scatter_point_radius"
        )
        
        # 回帰線表示
        show_regression_line = st.checkbox(
            "回帰線を表示", 
            properties.get("show_regression_line", False),
            key="scatter_show_regression_line"
        )
        
        # 回帰線の投影表示
        regression_projection = st.checkbox(
            "回帰線の投影を表示", 
            properties.get("regression_projection", False),
            key="scatter_regression_projection"
        )
        
        # 密度表示
        show_density = st.checkbox(
            "密度表示", 
            properties.get("show_density", False),
            key="scatter_show_density"
        )
    
    with st.sidebar.expander("表示設定", expanded=False):
        # ズーム有効化
        enable_zoom = st.checkbox(
            "ズーム機能を有効化", 
            properties.get("enable_zoom", True),
            key="scatter_enable_zoom"
        )
        
        # 凡例表示
        show_legend = st.checkbox(
            "凡例を表示", 
            properties.get("show_legend", True),
            key="scatter_show_legend"
        )
        
        legend_position_options = ["top", "right", "bottom", "left"]
        legend_position = st.selectbox(
            "凡例の位置",
            options=legend_position_options,
            index=legend_position_options.index(properties.get("legend_position", "top")),
            key="scatter_legend_position"
        )
        
        # グリッド表示
        show_x_grid = st.checkbox(
            "X軸グリッドを表示", 
            properties.get("show_x_grid", True),
            key="scatter_show_x_grid"
        )
        
        show_y_grid = st.checkbox(
            "Y軸グリッドを表示", 
            properties.get("show_y_grid", True),
            key="scatter_show_y_grid"
        )
        
        # アニメーション
        animation_duration = st.number_input(
            "アニメーション時間（ミリ秒）", 
            min_value=0, 
            max_value=2000, 
            value=properties.get("animation_duration", 1000),
            step=100,
            key="scatter_animation_duration"
        )
    
    # プロパティを更新
    properties.update({
        "x_field": x_field,
        "y_field": y_field,
        "series_field": series_field,
        "x_axis_title": x_axis_title,
        "y_axis_title": y_axis_title,
        "begin_at_zero": begin_at_zero,
        "point_style": point_style,
        "point_radius": point_radius,
        "show_regression_line": show_regression_line,
        "regression_projection": regression_projection,
        "show_density": show_density,
        "enable_zoom": enable_zoom,
        "show_legend": show_legend,
        "legend_position": legend_position,
        "show_x_grid": show_x_grid,
        "show_y_grid": show_y_grid,
        "animation_duration": animation_duration
    })
    
    return properties


def _add_bar_chart_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    棒グラフのプロパティを追加

    Parameters
    ----------
    properties : Dict[str, Any]
        現在のプロパティ

    Returns
    -------
    Dict[str, Any]
        更新されたプロパティ
    """
    with st.sidebar.expander("棒グラフ設定", expanded=True):
        # データフィールド
        label_field = st.text_input(
            "ラベルフィールド", 
            properties.get("label_field", "label"),
            key="bar_label_field"
        )
        
        value_field = st.text_input(
            "値フィールド", 
            properties.get("value_field", "value"),
            key="bar_value_field"
        )
        
        series_field = st.text_input(
            "シリーズフィールド（グループ分け）", 
            properties.get("series_field", ""),
            key="bar_series_field"
        )
        
        # 軸設定
        x_axis_title = st.text_input(
            "X軸タイトル", 
            properties.get("x_axis_title", ""),
            key="bar_x_axis_title"
        )
        
        y_axis_title = st.text_input(
            "Y軸タイトル", 
            properties.get("y_axis_title", ""),
            key="bar_y_axis_title"
        )
    
    with st.sidebar.expander("棒グラフ表示設定", expanded=False):
        # 棒の方向設定
        horizontal = st.checkbox(
            "水平棒グラフ", 
            properties.get("horizontal", False),
            key="bar_horizontal"
        )
        
        # 棒グラフタイプ
        bar_type_options = ["default", "stacked", "percent"]
        bar_type = st.selectbox(
            "棒グラフタイプ",
            options=bar_type_options,
            index=bar_type_options.index(properties.get("bar_type", "default")),
            key="bar_type"
        )
        
        # 棒の幅設定
        bar_thickness_options = ["auto", "10", "15", "20", "25", "30"]
        bar_thickness_value = properties.get("bar_thickness", "auto")
        bar_thickness_idx = bar_thickness_options.index(bar_thickness_value) if bar_thickness_value in bar_thickness_options else 0
        
        bar_thickness = st.selectbox(
            "棒の幅",
            options=bar_thickness_options,
            index=bar_thickness_idx,
            key="bar_thickness"
        )
        
        # 棒の間隔設定
        bar_space = st.slider(
            "棒の間隔", 
            min_value=0.0, 
            max_value=0.5, 
            value=properties.get("bar_space", 0.1),
            step=0.05,
            key="bar_space"
        )
        
        # 棒の角の丸み設定
        bar_border_radius = st.slider(
            "棒の角の丸み", 
            min_value=0, 
            max_value=15, 
            value=properties.get("bar_border_radius", 0),
            key="bar_border_radius"
        )
    
    with st.sidebar.expander("データと表示", expanded=False):
        # 値ラベル表示
        show_data_labels = st.checkbox(
            "値ラベルを表示", 
            properties.get("show_data_labels", False),
            key="bar_show_data_labels"
        )
        
        # ソート設定
        sort_data_options = ["none", "asc", "desc"]
        sort_data = st.selectbox(
            "データソート",
            options=sort_data_options,
            index=sort_data_options.index(properties.get("sort_data", "none")),
            key="bar_sort_data"
        )
        
        # 凡例表示
        show_legend = st.checkbox(
            "凡例を表示", 
            properties.get("show_legend", True),
            key="bar_show_legend"
        )
        
        legend_position_options = ["top", "right", "bottom", "left"]
        legend_position = st.selectbox(
            "凡例の位置",
            options=legend_position_options,
            index=legend_position_options.index(properties.get("legend_position", "top")),
            key="bar_legend_position"
        )
        
        # グリッド表示
        show_x_grid = st.checkbox(
            "X軸グリッドを表示", 
            properties.get("show_x_grid", True),
            key="bar_show_x_grid"
        )
        
        show_y_grid = st.checkbox(
            "Y軸グリッドを表示", 
            properties.get("show_y_grid", True),
            key="bar_show_y_grid"
        )
    
    # プロパティを更新
    properties.update({
        "label_field": label_field,
        "value_field": value_field,
        "series_field": series_field,
        "x_axis_title": x_axis_title,
        "y_axis_title": y_axis_title,
        "horizontal": horizontal,
        "bar_type": bar_type,
        "bar_thickness": bar_thickness,
        "bar_space": bar_space,
        "bar_border_radius": bar_border_radius,
        "show_data_labels": show_data_labels,
        "sort_data": sort_data,
        "show_legend": show_legend,
        "legend_position": legend_position,
        "show_x_grid": show_x_grid,
        "show_y_grid": show_y_grid
    })
    
    return properties


def _add_pie_chart_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    円グラフのプロパティを追加

    Parameters
    ----------
    properties : Dict[str, Any]
        現在のプロパティ

    Returns
    -------
    Dict[str, Any]
        更新されたプロパティ
    """
    with st.sidebar.expander("円グラフ設定", expanded=True):
        # データフィールド
        label_field = st.text_input(
            "ラベルフィールド", 
            properties.get("label_field", "label"),
            key="pie_label_field"
        )
        
        value_field = st.text_input(
            "値フィールド", 
            properties.get("value_field", "value"),
            key="pie_value_field"
        )
        
        # 円グラフタイプ
        pie_type_options = ["pie", "doughnut"]
        pie_type = st.selectbox(
            "円グラフタイプ",
            options=pie_type_options,
            index=pie_type_options.index(properties.get("pie_type", "pie")),
            key="pie_type"
        )
        
        # ドーナツグラフのカットアウト
        if pie_type == "doughnut":
            cutout_percentage = st.slider(
                "中央の穴の大きさ (%)", 
                min_value=10, 
                max_value=90, 
                value=properties.get("cutout_percentage", 50),
                key="pie_cutout_percentage"
            )
            properties["cutout_percentage"] = cutout_percentage
    
    with st.sidebar.expander("表示設定", expanded=False):
        # セグメント切り離し設定
        explode_segments_str = st.text_input(
            "切り離すセグメント（カンマ区切り）", 
            ",".join(properties.get("explode_segments", [])),
            key="pie_explode_segments"
        )
        explode_segments = [segment.strip() for segment in explode_segments_str.split(",") if segment.strip()]
        
        # 開始角度設定
        start_angle = st.slider(
            "開始角度 (度)", 
            min_value=-180, 
            max_value=180, 
            value=properties.get("start_angle", -90),
            key="pie_start_angle"
        )
        
        # 回転方向設定
        counter_clockwise = st.checkbox(
            "反時計回り", 
            properties.get("counter_clockwise", False),
            key="pie_counter_clockwise"
        )
        
        # アニメーション設定
        animate_scale = st.checkbox(
            "スケールアニメーション", 
            properties.get("animate_scale", True),
            key="pie_animate_scale"
        )
    
    with st.sidebar.expander("ラベル設定", expanded=False):
        # ラベル表示
        show_labels = st.checkbox(
            "ラベルを表示", 
            properties.get("show_labels", True),
            key="pie_show_labels"
        )
        
        # パーセント表示
        show_percentages = st.checkbox(
            "パーセント表示", 
            properties.get("show_percentages", True),
            key="pie_show_percentages"
        )
        
        # 値表示
        show_values = st.checkbox(
            "値を表示", 
            properties.get("show_values", False),
            key="pie_show_values"
        )
        
        # 凡例表示
        show_legend = st.checkbox(
            "凡例を表示", 
            properties.get("show_legend", True),
            key="pie_show_legend"
        )
        
        legend_position_options = ["top", "right", "bottom", "left"]
        legend_position = st.selectbox(
            "凡例の位置",
            options=legend_position_options,
            index=legend_position_options.index(properties.get("legend_position", "top")),
            key="pie_legend_position"
        )
    
    # プロパティを更新
    properties.update({
        "label_field": label_field,
        "value_field": value_field,
        "pie_type": pie_type,
        "explode_segments": explode_segments,
        "start_angle": start_angle,
        "counter_clockwise": counter_clockwise,
        "animate_scale": animate_scale,
        "show_labels": show_labels,
        "show_percentages": show_percentages,
        "show_values": show_values,
        "show_legend": show_legend,
        "legend_position": legend_position
    })
    
    return properties


def _add_windrose_chart_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    風配図（Wind Rose）のプロパティを追加

    Parameters
    ----------
    properties : Dict[str, Any]
        現在のプロパティ

    Returns
    -------
    Dict[str, Any]
        更新されたプロパティ
    """
    with st.sidebar.expander("風配図基本設定", expanded=True):
        # データフィールド
        direction_key = st.text_input(
            "方位フィールド", 
            properties.get("direction_key", "direction"),
            key="windrose_direction_key"
        )
        
        value_key = st.text_input(
            "値フィールド（風速/頻度）", 
            properties.get("value_key", "speed"),
            key="windrose_value_key"
        )
        
        time_key = st.text_input(
            "時間フィールド", 
            properties.get("time_key", "timestamp"),
            key="windrose_time_key"
        )
        
        # 角度分割数設定
        angle_divisions = st.selectbox(
            "方位分割数",
            options=[4, 8, 16, 32, 36],
            index=[4, 8, 16, 32, 36].index(properties.get("angle_divisions", 16)),
            key="windrose_angle_divisions"
        )
        
        # 方位表示形式
        direction_format_options = ["cardinal", "degrees", "both"]
        direction_format = st.selectbox(
            "方位表示形式",
            options=direction_format_options,
            index=direction_format_options.index(properties.get("direction_format", "cardinal")),
            key="windrose_direction_format"
        )
    
    with st.sidebar.expander("表示設定", expanded=False):
        # カラースケール設定
        color_scale_preset_options = ["blue", "rainbow", "thermal", "monochrome"]
        color_scale_preset = st.selectbox(
            "カラースケール",
            options=color_scale_preset_options,
            index=color_scale_preset_options.index(properties.get("color_scale_preset", "blue")),
            key="windrose_color_scale_preset"
        )
        
        # カラースケールタイプ
        color_scale_type_options = ["sequential", "diverging", "categorical"]
        color_scale_type = st.selectbox(
            "カラースケールタイプ",
            options=color_scale_type_options,
            index=color_scale_type_options.index(properties.get("color_scale_type", "sequential")),
            key="windrose_color_scale_type"
        )
        
        # 詳細表示設定
        show_details = st.checkbox(
            "詳細表示", 
            properties.get("show_details", True),
            key="windrose_show_details"
        )
        
        # 表示モード設定
        display_mode_options = ["frequency", "speed", "both"]
        display_mode = st.selectbox(
            "表示モード",
            options=display_mode_options,
            index=display_mode_options.index(properties.get("display_mode", "frequency")),
            key="windrose_display_mode"
        )
        
        # 角度ライン設定
        angle_lines_enabled = st.checkbox(
            "角度ラインを表示", 
            properties.get("angle_lines_enabled", True),
            key="windrose_angle_lines_enabled"
        )
        
        angle_lines_color = st.color_picker(
            "角度ライン色", 
            properties.get("angle_lines_color", "rgba(0, 0, 0, 0.1)"),
            key="windrose_angle_lines_color"
        )
        
        # ラベル表示設定
        show_labels = st.checkbox(
            "値ラベルを表示", 
            properties.get("show_labels", False),
            key="windrose_show_labels"
        )
    
    with st.sidebar.expander("時間フィルタリング", expanded=False):
        # 時間フィルタリング設定
        time_filter_enabled = st.checkbox(
            "時間フィルタリングを有効化", 
            properties.get("time_filter_enabled", False),
            key="windrose_time_filter_enabled"
        )
        
        if time_filter_enabled:
            time_start = st.text_input(
                "開始時間（ISO形式）", 
                properties.get("time_start", ""),
                key="windrose_time_start"
            )
            
            time_end = st.text_input(
                "終了時間（ISO形式）", 
                properties.get("time_end", ""),
                key="windrose_time_end"
            )
            
            properties.update({
                "time_start": time_start,
                "time_end": time_end
            })
    
    # プロパティを更新
    properties.update({
        "direction_key": direction_key,
        "value_key": value_key,
        "time_key": time_key,
        "angle_divisions": angle_divisions,
        "direction_format": direction_format,
        "color_scale_preset": color_scale_preset,
        "color_scale_type": color_scale_type,
        "show_details": show_details,
        "display_mode": display_mode,
        "angle_lines_enabled": angle_lines_enabled,
        "angle_lines_color": angle_lines_color,
        "show_labels": show_labels,
        "time_filter_enabled": time_filter_enabled,
        "chart_type": "windrose"  # Chart.js用の設定
    })
    
    return properties


def _add_polar_diagram_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    ポーラーダイアグラムのプロパティを追加

    Parameters
    ----------
    properties : Dict[str, Any]
        現在のプロパティ

    Returns
    -------
    Dict[str, Any]
        更新されたプロパティ
    """
    with st.sidebar.expander("ポーラーダイアグラム基本設定", expanded=True):
        # 表示設定
        show_target_curve = st.checkbox(
            "ターゲット曲線を表示", 
            properties.get("show_target_curve", True),
            key="polar_show_target_curve"
        )
        
        show_actual_data = st.checkbox(
            "実測データを表示", 
            properties.get("show_actual_data", True),
            key="polar_show_actual_data"
        )
        
        show_vmg_points = st.checkbox(
            "VMGポイントを表示", 
            properties.get("show_vmg_points", True),
            key="polar_show_vmg_points"
        )
        
        # 角度範囲
        angle_range_options = ["full", "upwind", "downwind", "custom"]
        angle_range = st.selectbox(
            "角度範囲",
            options=angle_range_options,
            index=angle_range_options.index(properties.get("angle_range", "full")),
            key="polar_angle_range"
        )
        
        # カスタム角度範囲
        if angle_range == "custom":
            custom_angle_min = st.number_input(
                "最小角度", 
                min_value=0, 
                max_value=359, 
                value=properties.get("custom_angle_min", 0),
                key="polar_custom_angle_min"
            )
            
            custom_angle_max = st.number_input(
                "最大角度", 
                min_value=custom_angle_min + 1, 
                max_value=360, 
                value=properties.get("custom_angle_max", 360),
                key="polar_custom_angle_max"
            )
            
            properties.update({
                "custom_angle_min": custom_angle_min,
                "custom_angle_max": custom_angle_max
            })
    
    with st.sidebar.expander("データ設定", expanded=False):
        # 表示する風速
        wind_speeds_str = st.text_input(
            "表示する風速値（カンマ区切り）", 
            ",".join(str(ws) for ws in properties.get("wind_speeds", [5, 10, 15, 20])),
            key="polar_wind_speeds"
        )
        try:
            wind_speeds = [float(ws.strip()) for ws in wind_speeds_str.split(",") if ws.strip()]
        except ValueError:
            wind_speeds = [5, 10, 15, 20]
        
        # 最大ボート速度
        max_boat_speed_options = ["auto", "5", "10", "15", "20", "25"]
        max_boat_speed_value = properties.get("max_boat_speed", "auto")
        max_boat_speed_idx = max_boat_speed_options.index(str(max_boat_speed_value)) if str(max_boat_speed_value) in max_boat_speed_options else 0
        
        max_boat_speed = st.selectbox(
            "最大ボート速度",
            options=max_boat_speed_options,
            index=max_boat_speed_idx,
            key="polar_max_boat_speed"
        )
        
        # 角度ステップ
        angle_step = st.selectbox(
            "角度ステップ（度）",
            options=[1, 5, 10, 15, 30],
            index=[1, 5, 10, 15, 30].index(properties.get("angle_step", 5)),
            key="polar_angle_step"
        )
    
    # プロパティを更新
    properties.update({
        "show_target_curve": show_target_curve,
        "show_actual_data": show_actual_data,
        "show_vmg_points": show_vmg_points,
        "angle_range": angle_range,
        "wind_speeds": wind_speeds,
        "max_boat_speed": max_boat_speed,
        "angle_step": angle_step,
        "chart_type": "polar"  # Chart.js用の設定
    })
    
    return properties


def _add_tacking_angle_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    タッキングアングル分析のプロパティを追加

    Parameters
    ----------
    properties : Dict[str, Any]
        現在のプロパティ

    Returns
    -------
    Dict[str, Any]
        更新されたプロパティ
    """
    with st.sidebar.expander("タッキングアングル基本設定", expanded=True):
        # データフィールド
        angle_key = st.text_input(
            "角度フィールド", 
            properties.get("angle_key", "tacking_angle"),
            key="tacking_angle_key"
        )
        
        # 角度範囲設定
        min_angle = st.number_input(
            "最小角度", 
            min_value=0, 
            max_value=180, 
            value=properties.get("min_angle", 70),
            key="tacking_min_angle"
        )
        
        max_angle = st.number_input(
            "最大角度", 
            min_value=min_angle, 
            max_value=180, 
            value=properties.get("max_angle", 140),
            key="tacking_max_angle"
        )
        
        # ビン数設定
        num_bins = st.slider(
            "ビン数（角度範囲の分割数）", 
            min_value=5, 
            max_value=30, 
            value=properties.get("num_bins", 18),
            key="tacking_num_bins"
        )
    
    with st.sidebar.expander("最適範囲設定", expanded=False):
        # 最適角度範囲
        optimal_min = st.number_input(
            "最適角度（最小）", 
            min_value=min_angle, 
            max_value=max_angle - 1, 
            value=properties.get("optimal_min", 85),
            key="tacking_optimal_min"
        )
        
        optimal_max = st.number_input(
            "最適角度（最大）", 
            min_value=optimal_min + 1, 
            max_value=max_angle, 
            value=properties.get("optimal_max", 95),
            key="tacking_optimal_max"
        )
        
        # 最適範囲の色設定
        optimal_color = st.color_picker(
            "最適範囲の色", 
            properties.get("optimal_color", "rgba(75, 192, 192, 0.2)"),
            key="tacking_optimal_color"
        )
    
    # プロパティを更新
    properties.update({
        "angle_key": angle_key,
        "min_angle": min_angle,
        "max_angle": max_angle,
        "num_bins": num_bins,
        "optimal_min": optimal_min,
        "optimal_max": optimal_max,
        "optimal_color": optimal_color,
        "chart_type": "bar"  # Chart.js用の設定
    })
    
    return properties


def _add_course_performance_properties(properties: Dict[str, Any]) -> Dict[str, Any]:
    """
    コースパフォーマンスグラフのプロパティを追加

    Parameters
    ----------
    properties : Dict[str, Any]
        現在のプロパティ

    Returns
    -------
    Dict[str, Any]
        更新されたプロパティ
    """
    with st.sidebar.expander("コースパフォーマンス基本設定", expanded=True):
        # データフィールド
        label_field = st.text_input(
            "ラベルフィールド", 
            properties.get("label_field", "angle"),
            key="course_label_field"
        )
        
        value_field = st.text_input(
            "値フィールド", 
            properties.get("value_field", "speed"),
            key="course_value_field"
        )
        
        series_field = st.text_input(
            "シリーズフィールド", 
            properties.get("series_field", "type"),
            key="course_series_field"
        )
        
        # 詳細表示設定
        show_details = st.checkbox(
            "詳細表示", 
            properties.get("show_details", True),
            key="course_show_details"
        )
        
        # 効率指標表示設定
        show_efficiency = st.checkbox(
            "効率指標を表示", 
            properties.get("show_efficiency", True),
            key="course_show_efficiency"
        )
    
    with st.sidebar.expander("ボートポーラー設定", expanded=False):
        # ボートポーラー参照
        polar_reference_options = ["", "470", "49er", "finn", "laser", "nacra17"]
        polar_reference_value = properties.get("polar_reference", "")
        polar_reference_idx = polar_reference_options.index(polar_reference_value) if polar_reference_value in polar_reference_options else 0
        
        polar_reference = st.selectbox(
            "ボートポーラー参照",
            options=polar_reference_options,
            index=polar_reference_idx,
            key="course_polar_reference"
        )
        
        # 表示角度範囲
        angle_range_options = ["full", "upwind", "downwind"]
        angle_range = st.selectbox(
            "表示角度範囲",
            options=angle_range_options,
            index=angle_range_options.index(properties.get("angle_range", "full")),
            key="course_angle_range"
        )
        
        # 角度分割数設定
        angle_divisions = st.selectbox(
            "角度分割数",
            options=[36, 18, 12, 8],
            index=[36, 18, 12, 8].index(properties.get("angle_divisions", 36)),
            key="course_angle_divisions"
        )
    
    with st.sidebar.expander("表示設定", expanded=False):
        # 角度ライン設定
        angle_lines_enabled = st.checkbox(
            "角度ラインを表示", 
            properties.get("angle_lines_enabled", True),
            key="course_angle_lines_enabled"
        )
        
        angle_lines_color = st.color_picker(
            "角度ライン色", 
            properties.get("angle_lines_color", "rgba(0, 0, 0, 0.1)"),
            key="course_angle_lines_color"
        )
        
        # 最大目盛り数
        max_ticks = st.slider(
            "最大目盛り数", 
            min_value=3, 
            max_value=10, 
            value=properties.get("max_ticks", 5),
            key="course_max_ticks"
        )
    
    # プロパティを更新
    properties.update({
        "label_field": label_field,
        "value_field": value_field,
        "series_field": series_field,
        "show_details": show_details,
        "show_efficiency": show_efficiency,
        "polar_reference": polar_reference,
        "angle_range": angle_range,
        "angle_divisions": angle_divisions,
        "angle_lines_enabled": angle_lines_enabled,
        "angle_lines_color": angle_lines_color,
        "max_ticks": max_ticks,
        "chart_type": "radar"  # Chart.js用の設定
    })
    
    return properties
