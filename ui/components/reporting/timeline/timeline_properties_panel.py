"""
ui.components.reporting.timeline.timeline_properties_panel

タイムライン要素のプロパティ編集パネルを提供するモジュールです。
イベントタイムラインやパラメータタイムラインの設定を行うためのUIコンポーネントを実装します。
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable, Union
import json

from sailing_data_processor.reporting.elements.timeline.event_timeline import EventTimeline
from sailing_data_processor.reporting.elements.timeline.parameter_timeline import ParameterTimeline


def timeline_properties_panel(
    timeline: Union[EventTimeline, ParameterTimeline],
    on_change: Optional[Callable[[Dict[str, Any]], None]] = None,
    key_prefix: str = ""
) -> Dict[str, Any]:
    """
    タイムラインプロパティパネルを表示
    
    Parameters
    ----------
    timeline : Union[EventTimeline, ParameterTimeline]
        タイムラインオブジェクト
    on_change : Optional[Callable[[Dict[str, Any]], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""
        
    Returns
    -------
    Dict[str, Any]
        変更されたプロパティ情報
    """
    changed_properties = {}
    
    # タイムラインの種類を判断
    is_event_timeline = isinstance(timeline, EventTimeline)
    is_parameter_timeline = isinstance(timeline, ParameterTimeline)
    
    if not (is_event_timeline or is_parameter_timeline):
        st.warning("サポートされていないタイムラインタイプです。")
        return changed_properties
    
    # プロパティ変更のハンドラー
    def handle_property_change(key, value):
        changed_properties[key] = value
        if on_change:
            on_change({key: value})
    
    # 共通プロパティ
    with st.expander("基本設定", expanded=True):
        # タイムラインの高さ
        timeline_height = st.number_input(
            "タイムラインの高さ", 
            min_value=100, 
            max_value=800, 
            value=timeline.get_property("timeline_height", 
                                        150 if is_event_timeline else 300),
            step=10,
            key=f"{key_prefix}_timeline_height"
        )
        
        if timeline_height != timeline.get_property("timeline_height"):
            handle_property_change("timeline_height", timeline_height)
        
        # 時間フォーマット
        time_format_options = ["HH:mm:ss", "HH:mm", "MM/DD HH:mm", "YYYY/MM/DD HH:mm"]
        time_format_index = time_format_options.index(timeline.get_property("time_format", "HH:mm:ss")) if timeline.get_property("time_format", "HH:mm:ss") in time_format_options else 0
        
        time_format = st.selectbox(
            "時間フォーマット",
            options=time_format_options,
            index=time_format_index,
            key=f"{key_prefix}_time_format"
        )
        
        if time_format != timeline.get_property("time_format"):
            handle_property_change("time_format", time_format)
    
    # イベントタイムライン固有のプロパティ
    if is_event_timeline:
        _render_event_timeline_properties(timeline, handle_property_change, key_prefix)
    
    # パラメータタイムライン固有のプロパティ
    if is_parameter_timeline:
        _render_parameter_timeline_properties(timeline, handle_property_change, key_prefix)
    
    return changed_properties


def _render_event_timeline_properties(
    timeline: EventTimeline, 
    on_property_change: Callable[[str, Any], None], 
    key_prefix: str
) -> None:
    """
    イベントタイムラインのプロパティ編集UIを表示
    
    Parameters
    ----------
    timeline : EventTimeline
        イベントタイムライン
    on_property_change : Callable[[str, Any], None]
        プロパティ変更時のコールバック
    key_prefix : str
        キー接頭辞
    """
    # イベント表示設定
    with st.expander("イベント表示設定"):
        # イベント表示の有効/無効
        show_tacks = st.checkbox(
            "タックを表示", 
            value=timeline.get_property("show_tacks", True),
            key=f"{key_prefix}_show_tacks"
        )
        
        if show_tacks != timeline.get_property("show_tacks"):
            on_property_change("show_tacks", show_tacks)
        
        show_jibes = st.checkbox(
            "ジャイブを表示", 
            value=timeline.get_property("show_jibes", True),
            key=f"{key_prefix}_show_jibes"
        )
        
        if show_jibes != timeline.get_property("show_jibes"):
            on_property_change("show_jibes", show_jibes)
        
        show_marks = st.checkbox(
            "マーク回航を表示", 
            value=timeline.get_property("show_marks", True),
            key=f"{key_prefix}_show_marks"
        )
        
        if show_marks != timeline.get_property("show_marks"):
            on_property_change("show_marks", show_marks)
        
        show_custom = st.checkbox(
            "カスタムイベントを表示", 
            value=timeline.get_property("show_custom", True),
            key=f"{key_prefix}_show_custom"
        )
        
        if show_custom != timeline.get_property("show_custom"):
            on_property_change("show_custom", show_custom)
    
    # イベント表示スタイル
    with st.expander("表示スタイル"):
        # イベントのグループ化
        group_events = st.checkbox(
            "近接イベントをグループ化", 
            value=timeline.get_property("group_events", True),
            key=f"{key_prefix}_group_events"
        )
        
        if group_events != timeline.get_property("group_events"):
            on_property_change("group_events", group_events)
        
        # イベントマーカーの高さ
        event_height = st.slider(
            "イベントマーカーのサイズ", 
            min_value=10, 
            max_value=40, 
            value=timeline.get_property("event_height", 20),
            step=2,
            key=f"{key_prefix}_event_height"
        )
        
        if event_height != timeline.get_property("event_height"):
            on_property_change("event_height", event_height)
        
        # オーバーフロー処理
        handle_overflow = st.checkbox(
            "表示範囲外のイベントを調整", 
            value=timeline.get_property("handle_overflow", True),
            key=f"{key_prefix}_handle_overflow"
        )
        
        if handle_overflow != timeline.get_property("handle_overflow"):
            on_property_change("handle_overflow", handle_overflow)
        
        # ツールチップの配置
        tooltip_placement_options = ["top", "bottom", "left", "right"]
        tooltip_placement_index = tooltip_placement_options.index(timeline.get_property("tooltip_placement", "top")) if timeline.get_property("tooltip_placement", "top") in tooltip_placement_options else 0
        
        tooltip_placement = st.selectbox(
            "ツールチップの配置",
            options=tooltip_placement_options,
            index=tooltip_placement_index,
            key=f"{key_prefix}_tooltip_placement"
        )
        
        if tooltip_placement != timeline.get_property("tooltip_placement"):
            on_property_change("tooltip_placement", tooltip_placement)


def _render_parameter_timeline_properties(
    timeline: ParameterTimeline, 
    on_property_change: Callable[[str, Any], None], 
    key_prefix: str
) -> None:
    """
    パラメータタイムラインのプロパティ編集UIを表示
    
    Parameters
    ----------
    timeline : ParameterTimeline
        パラメータタイムライン
    on_property_change : Callable[[str, Any], None]
        プロパティ変更時のコールバック
    key_prefix : str
        キー接頭辞
    """
    # パラメータ表示設定
    with st.expander("パラメータ表示設定"):
        # パラメータ表示の有効/無効
        show_speed = st.checkbox(
            "速度を表示", 
            value=timeline.get_property("show_speed", True),
            key=f"{key_prefix}_show_speed"
        )
        
        if show_speed != timeline.get_property("show_speed"):
            on_property_change("show_speed", show_speed)
        
        show_wind_speed = st.checkbox(
            "風速を表示", 
            value=timeline.get_property("show_wind_speed", False),
            key=f"{key_prefix}_show_wind_speed"
        )
        
        if show_wind_speed != timeline.get_property("show_wind_speed"):
            on_property_change("show_wind_speed", show_wind_speed)
        
        show_wind_direction = st.checkbox(
            "風向を表示", 
            value=timeline.get_property("show_wind_direction", False),
            key=f"{key_prefix}_show_wind_direction"
        )
        
        if show_wind_direction != timeline.get_property("show_wind_direction"):
            on_property_change("show_wind_direction", show_wind_direction)
        
        show_heading = st.checkbox(
            "艇首方位を表示", 
            value=timeline.get_property("show_heading", False),
            key=f"{key_prefix}_show_heading"
        )
        
        if show_heading != timeline.get_property("show_heading"):
            on_property_change("show_heading", show_heading)
        
        show_heel = st.checkbox(
            "ヒール角を表示", 
            value=timeline.get_property("show_heel", False),
            key=f"{key_prefix}_show_heel"
        )
        
        if show_heel != timeline.get_property("show_heel"):
            on_property_change("show_heel", show_heel)
        
        show_vmg = st.checkbox(
            "VMGを表示", 
            value=timeline.get_property("show_vmg", False),
            key=f"{key_prefix}_show_vmg"
        )
        
        if show_vmg != timeline.get_property("show_vmg"):
            on_property_change("show_vmg", show_vmg)
        
        # カスタムパラメータの表示設定
        custom_parameters = timeline.get_property("custom_parameters", [])
        if custom_parameters:
            st.subheader("カスタムパラメータ")
            for param in custom_parameters:
                show_param = st.checkbox(
                    f"{param}を表示", 
                    value=True,
                    key=f"{key_prefix}_show_custom_{param}"
                )
                
                # カスタムパラメータの表示/非表示は未実装
    
    # グラフ表示設定
    with st.expander("グラフ表示設定"):
        # 線のスタイル
        line_style_options = ["linear", "spline", "step"]
        line_style_labels = ["直線", "曲線", "階段"]
        line_style_index = line_style_options.index(timeline.get_property("line_style", "linear")) if timeline.get_property("line_style", "linear") in line_style_options else 0
        
        line_style = st.selectbox(
            "線のスタイル",
            options=line_style_labels,
            index=line_style_index,
            key=f"{key_prefix}_line_style"
        )
        
        if line_style_labels.index(line_style) != line_style_index:
            on_property_change("line_style", line_style_options[line_style_labels.index(line_style)])
        
        # 点のサイズ
        point_radius = st.slider(
            "点のサイズ", 
            min_value=0, 
            max_value=10, 
            value=timeline.get_property("point_radius", 2),
            step=1,
            key=f"{key_prefix}_point_radius"
        )
        
        if point_radius != timeline.get_property("point_radius"):
            on_property_change("point_radius", point_radius)
        
        # ズーム機能
        enable_zoom = st.checkbox(
            "ズーム機能を有効化", 
            value=timeline.get_property("enable_zoom", True),
            key=f"{key_prefix}_enable_zoom"
        )
        
        if enable_zoom != timeline.get_property("enable_zoom"):
            on_property_change("enable_zoom", enable_zoom)
    
    # 分析設定
    with st.expander("分析設定"):
        # 統計情報の表示
        show_statistics = st.checkbox(
            "統計情報を表示", 
            value=timeline.get_property("show_statistics", True),
            key=f"{key_prefix}_show_statistics"
        )
        
        if show_statistics != timeline.get_property("show_statistics"):
            on_property_change("show_statistics", show_statistics)
        
        # トレンドラインの表示
        show_trends = st.checkbox(
            "トレンドラインを表示", 
            value=timeline.get_property("show_trends", False),
            key=f"{key_prefix}_show_trends"
        )
        
        if show_trends != timeline.get_property("show_trends"):
            on_property_change("show_trends", show_trends)
"""