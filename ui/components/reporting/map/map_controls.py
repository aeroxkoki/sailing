# -*- coding: utf-8 -*-
"""
ui.components.reporting.map.map_controls

マップコントロールUIコンポーネントを提供するモジュールです。
地図の操作や設定を行うためのUIコンポーネントを含みます。
"""

import streamlit as st
import json
from typing import Dict, List, Any, Optional, Union, Tuple, Callable


def map_control_panel(map_id: str = None, on_control_change: Optional[Callable] = None) -> Dict[str, Any]:
    """
    マップコントロールパネルを表示

    Parameters
    ----------
    map_id : str, optional
        マップID, by default None
    on_control_change : Optional[Callable], optional
        コントロール変更時のコールバック関数, by default None

    Returns
    -------
    Dict[str, Any]
        現在の設定値
    """
    st.markdown("### マップコントロール")
    
    with st.expander("基本コントロール", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            center_auto = st.checkbox("自動中心設定", value=True, key=f"{map_id}_center_auto")
            
            if not center_auto:
                lat = st.number_input("緯度", value=35.4498, format="%.6f", key=f"{map_id}_center_lat")
                lng = st.number_input("経度", value=139.6649, format="%.6f", key=f"{map_id}_center_lng")
            else:
                lat = 35.4498
                lng = 139.6649
        
        with col2:
            zoom_level = st.slider("ズームレベル", 1, 18, 12, key=f"{map_id}_zoom_level")
            base_layer = st.selectbox(
                "ベースマップタイプ",
                options=["osm", "satellite", "nautical", "topo"],
                format_func=lambda x: {
                    "osm": "OpenStreetMap",
                    "satellite": "衛星写真",
                    "nautical": "海図",
                    "topo": "地形図"
                }.get(x, x),
                key=f"{map_id}_base_layer"
            )
    
    with st.expander("表示コントロール", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            show_layer_control = st.checkbox("レイヤーコントロール表示", value=True, key=f"{map_id}_show_layer_control")
            show_scale_control = st.checkbox("スケールコントロール表示", value=True, key=f"{map_id}_show_scale_control")
        
        with col2:
            show_fullscreen_control = st.checkbox("全画面コントロール表示", value=True, key=f"{map_id}_show_fullscreen_control")
            show_measure_control = st.checkbox("測定ツール表示", value=False, key=f"{map_id}_show_measure_control")
    
    # 設定値をまとめる
    map_settings = {
        "center_auto": center_auto,
        "center_lat": lat,
        "center_lng": lng,
        "zoom_level": zoom_level,
        "base_layer": base_layer,
        "show_layer_control": show_layer_control,
        "show_scale_control": show_scale_control,
        "show_fullscreen_control": show_fullscreen_control,
        "show_measure_control": show_measure_control
    }
    
    # コールバック呼び出し
    if on_control_change:
        on_control_change(map_settings)
    
    return map_settings


def map_layer_control(map_id: str = None, base_layers: Dict[str, Any] = None, 
                     overlay_layers: Dict[str, Any] = None, 
                     on_layer_change: Optional[Callable] = None) -> Dict[str, Any]:
    """
    マップレイヤーコントロールパネルを表示

    Parameters
    ----------
    map_id : str, optional
        マップID, by default None
    base_layers : Dict[str, Any], optional
        ベースレイヤー情報, by default None
    overlay_layers : Dict[str, Any], optional
        オーバーレイレイヤー情報, by default None
    on_layer_change : Optional[Callable], optional
        レイヤー変更時のコールバック関数, by default None

    Returns
    -------
    Dict[str, Any]
        現在のレイヤー設定
    """
    st.markdown("### レイヤーコントロール")
    
    # デフォルトのレイヤー定義
    if base_layers is None:
        base_layers = {
            "osm": {"name": "OpenStreetMap", "visible": True},
            "satellite": {"name": "衛星写真", "visible": False},
            "nautical": {"name": "海図", "visible": False},
            "topo": {"name": "地形図", "visible": False}
        }
    
    if overlay_layers is None:
        overlay_layers = {
            "track": {"name": "GPS軌跡", "visible": True},
            "markers": {"name": "マーカー", "visible": True},
            "grid": {"name": "グリッド", "visible": False}
        }
    
    # アクティブなベースレイヤーを特定
    active_base_layer = next((k for k, v in base_layers.items() if v.get("visible", False)), "osm")
    
    # ベースレイヤーの選択
    st.radio(
        "ベースマップ",
        options=list(base_layers.keys()),
        format_func=lambda x: base_layers[x]["name"],
        index=list(base_layers.keys()).index(active_base_layer),
        key=f"{map_id}_base_layer_select"
    )
    
    st.markdown("#### オーバーレイレイヤー")
    
    # オーバーレイレイヤーの選択（複数選択可）
    layer_states = {}
    for layer_id, layer_info in overlay_layers.items():
        is_visible = layer_info.get("visible", False)
        layer_states[layer_id] = st.checkbox(
            layer_info["name"],
            value=is_visible,
            key=f"{map_id}_overlay_{layer_id}"
        )
    
    # レイヤー設定の更新
    for layer_id, is_visible in layer_states.items():
        overlay_layers[layer_id]["visible"] = is_visible
    
    # 結果の構築
    layer_settings = {
        "base_layer": active_base_layer,
        "overlay_layers": {k: v for k, v in overlay_layers.items() if v.get("visible", False)}
    }
    
    # コールバック呼び出し
    if on_layer_change:
        on_layer_change(layer_settings)
    
    return layer_settings


def map_tools_panel(map_id: str = None, on_tool_action: Optional[Callable] = None) -> None:
    """
    マップツールパネルを表示

    Parameters
    ----------
    map_id : str, optional
        マップID, by default None
    on_tool_action : Optional[Callable], optional
        ツールアクション時のコールバック関数, by default None
    """
    st.markdown("### マップツール")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("中心をリセット", key=f"{map_id}_reset_center"):
            if on_tool_action:
                on_tool_action({"action": "reset_center"})
        
        if st.button("トラックに合わせる", key=f"{map_id}_fit_track"):
            if on_tool_action:
                on_tool_action({"action": "fit_track"})
    
    with col2:
        if st.button("マーカーをクリア", key=f"{map_id}_clear_markers"):
            if on_tool_action:
                on_tool_action({"action": "clear_markers"})
        
        if st.button("選択をクリア", key=f"{map_id}_clear_selection"):
            if on_tool_action:
                on_tool_action({"action": "clear_selection"})


def export_map_panel(map_id: str = None, on_export: Optional[Callable] = None) -> None:
    """
    マップエクスポートパネルを表示

    Parameters
    ----------
    map_id : str, optional
        マップID, by default None
    on_export : Optional[Callable], optional
        エクスポート時のコールバック関数, by default None
    """
    st.markdown("### エクスポート")
    
    export_format = st.selectbox(
        "フォーマット",
        options=["PNG", "HTML", "GeoJSON", "KML", "GPX"],
        key=f"{map_id}_export_format"
    )
    
    include_layers = st.multiselect(
        "含めるレイヤー",
        options=["ベースマップ", "GPS軌跡", "マーカー", "グリッド"],
        default=["ベースマップ", "GPS軌跡", "マーカー"],
        key=f"{map_id}_export_layers"
    )
    
    if st.button("エクスポート", key=f"{map_id}_export_button"):
        if on_export:
            on_export({
                "format": export_format,
                "include_layers": include_layers
            })
