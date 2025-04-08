"""
ui.components.reporting.map.map_component

地図表示コンポーネントを提供するモジュールです。
Streamlitで地図要素を表示するためのコンポーネントを含みます。
"""

import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import folium_static
import json
import uuid
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

from sailing_data_processor.reporting.elements.map.base_map_element import BaseMapElement
from sailing_data_processor.reporting.elements.map.track_map_element import TrackMapElement
from sailing_data_processor.reporting.elements.map.map_utils import (
    analyze_track_statistics, 
    detect_significant_points,
    simplify_track
)

from ui.components.reporting.map.map_controls import (
    map_control_panel,
    map_layer_control,
    map_tools_panel,
    export_map_panel
)

from ui.components.reporting.map.track_properties_panel import (
    track_style_panel,
    track_data_panel,
    track_custom_marker_panel
)


def display_map_element(map_element: BaseMapElement, 
                       context: Dict[str, Any] = None,
                       show_controls: bool = True) -> None:
    """
    マップ要素を表示

    Parameters
    ----------
    map_element : BaseMapElement
        マップ要素
    context : Dict[str, Any], optional
        レンダリングコンテキスト, by default None
    show_controls : bool, optional
        コントロールの表示有無, by default True
    """
    if context is None:
        context = {}
    
    # マップ要素をHTMLとしてレンダリング
    map_html = map_element.render(context)
    
    # マップを表示
    if map_html:
        components.html(map_html, height=500, scrolling=False)
    else:
        st.warning("マップデータを表示できませんでした。")


def display_folium_map(track_data: List[Dict[str, Any]] = None,
                      map_settings: Dict[str, Any] = None,
                      track_settings: Dict[str, Any] = None) -> folium.Map:
    """
    Foliumマップを表示

    Parameters
    ----------
    track_data : List[Dict[str, Any]], optional
        トラックデータ, by default None
    map_settings : Dict[str, Any], optional
        マップ設定, by default None
    track_settings : Dict[str, Any], optional
        トラック設定, by default None

    Returns
    -------
    folium.Map
        Foliumマップオブジェクト
    """
    if map_settings is None:
        map_settings = {}
    
    if track_settings is None:
        track_settings = {}
    
    # マップ設定を取得
    center_auto = map_settings.get("center_auto", True)
    center_lat = map_settings.get("center_lat", 35.4498)
    center_lng = map_settings.get("center_lng", 139.6649)
    zoom_level = map_settings.get("zoom_level", 12)
    base_layer = map_settings.get("base_layer", "osm")
    
    # マップの初期化
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=zoom_level,
        control_scale=map_settings.get("show_scale_control", True)
    )
    
    # ベースレイヤーの設定
    if base_layer == "satellite":
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Satellite",
            overlay=False
        ).add_to(m)
    elif base_layer == "nautical":
        folium.TileLayer(
            tiles="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
            attr="OpenSeaMap",
            name="Nautical",
            overlay=False
        ).add_to(m)
    elif base_layer == "topo":
        folium.TileLayer(
            tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
            attr="OpenTopoMap",
            name="Topographic",
            overlay=False
        ).add_to(m)
    
    # トラックデータがある場合
    if track_data:
        # データフィールド名の確認
        lat_key = "lat"
        lng_key = "lng"
        
        # 最初の要素をチェック
        if track_data and isinstance(track_data[0], dict):
            if "latitude" in track_data[0] and "longitude" in track_data[0]:
                lat_key = "latitude"
                lng_key = "longitude"
            elif "lat" in track_data[0] and "lon" in track_data[0]:
                lng_key = "lon"
        
        # トラック設定の取得
        track_color = track_settings.get("track_color", "rgba(255, 87, 34, 0.8)")
        track_width = track_settings.get("track_width", 3)
        color_by = track_settings.get("color_by", "none")
        show_markers = track_settings.get("show_markers", True)
        show_start_end_markers = track_settings.get("show_start_end_markers", True)
        
        # トラックポイントの抽出
        points = []
        for point in track_data:
            if lat_key in point and lng_key in point:
                lat = point[lat_key]
                lng = point[lng_key]
                if isinstance(lat, (int, float)) and isinstance(lng, (int, float)):
                    points.append([lat, lng])
        
        # トラックデータがある場合
        if points:
            # 色分けなしの場合は通常のPolyline
            if color_by == "none":
                # rgba色をhex色に変換
                rgba_parts = track_color.replace("rgba(", "").replace(")", "").split(",")
                r, g, b = map(int, rgba_parts[:3])
                opacity = float(rgba_parts[3])
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                
                folium.PolyLine(
                    points,
                    color=hex_color,
                    weight=track_width,
                    opacity=opacity
                ).add_to(m)
            else:
                # TODO: 色分けトラックの実装（現在のFoliumでは簡単ではない）
                pass
            
            # マーカーの追加
            if show_markers and show_start_end_markers and len(points) > 1:
                # スタートマーカー
                folium.Marker(
                    points[0],
                    popup="Start",
                    icon=folium.Icon(color="green", icon="play", prefix="fa")
                ).add_to(m)
                
                # フィニッシュマーカー
                folium.Marker(
                    points[-1],
                    popup="Finish",
                    icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa")
                ).add_to(m)
            
            # カスタムマーカーの追加
            custom_markers = track_settings.get("custom_markers", [])
            for marker in custom_markers:
                if "lat" in marker and "lng" in marker:
                    folium.Marker(
                        [marker["lat"], marker["lng"]],
                        popup=marker.get("title", ""),
                        tooltip=marker.get("description", ""),
                        icon=folium.Icon(
                            color=marker.get("color", "blue").replace("#", ""),
                            icon=marker.get("icon", "info-sign"),
                            prefix="fa"
                        )
                    ).add_to(m)
            
            # 自動中心設定の場合はトラックに合わせる
            if center_auto:
                m.fit_bounds(folium.folium.utilities.get_bounds(points))
    
    # レイヤーコントロールの追加
    if map_settings.get("show_layer_control", True):
        folium.LayerControl().add_to(m)
    
    # 全画面コントロールの追加
    if map_settings.get("show_fullscreen_control", True):
        plugins.Fullscreen().add_to(m)
    
    return m


def gps_track_map_component(track_data: List[Dict[str, Any]] = None,
                           key: str = None,
                           height: int = 500,
                           sidebar_width: int = 300) -> Dict[str, Any]:
    """
    GPSトラックマップコンポーネント

    Parameters
    ----------
    track_data : List[Dict[str, Any]], optional
        トラックデータ, by default None
    key : str, optional
        コンポーネントのキー, by default None
    height : int, optional
        地図の高さ, by default 500
    sidebar_width : int, optional
        サイドバーの幅, by default 300

    Returns
    -------
    Dict[str, Any]
        コンポーネントの状態
    """
    if key is None:
        key = f"map_{str(uuid.uuid4())[:8]}"
    
    # コンポーネントの状態管理
    if f"{key}_initialized" not in st.session_state:
        # デフォルト設定
        st.session_state[f"{key}_map_settings"] = {
            "center_auto": True,
            "center_lat": 35.4498,
            "center_lng": 139.6649,
            "zoom_level": 12,
            "base_layer": "osm",
            "show_layer_control": True,
            "show_scale_control": True,
            "show_fullscreen_control": True,
            "show_measure_control": False
        }
        
        st.session_state[f"{key}_track_settings"] = {
            "track_color": "rgba(255, 87, 34, 0.8)",
            "track_width": 3,
            "color_by": "none",
            "show_markers": True,
            "show_start_end_markers": True,
            "enable_interaction": True,
            "enable_selection": True,
            "custom_markers": []
        }
        
        # 統計情報
        if track_data:
            try:
                st.session_state[f"{key}_track_stats"] = analyze_track_statistics(track_data)
            except Exception as e:
                st.error(f"トラック統計の計算エラー: {str(e)}")
                st.session_state[f"{key}_track_stats"] = None
        else:
            st.session_state[f"{key}_track_stats"] = None
        
        st.session_state[f"{key}_initialized"] = True
    
    # レイアウト
    col1, col2 = st.columns([3, 1])
    
    # マップ表示エリア
    with col1:
        # トラックマップ要素の作成
        track_map = TrackMapElement(element_id=f"{key}_map")
        
        # マップ設定の適用
        for setting, value in st.session_state[f"{key}_map_settings"].items():
            track_map.set_property(setting, value)
        
        # トラック設定の適用
        for setting, value in st.session_state[f"{key}_track_settings"].items():
            track_map.set_property(setting, value)
        
        # コンテキストの作成
        context = {"track_data": track_data} if track_data else {}
        
        # マップの表示
        st.markdown("### GPSトラックマップ")
        display_map_element(track_map, context)
    
    # コントロールパネル
    with col2:
        # タブの設定
        tabs = st.tabs(["マップ設定", "トラック設定", "情報"])
        
        # マップ設定タブ
        with tabs[0]:
            # マップコントロールパネル
            def on_map_control_change(settings):
                st.session_state[f"{key}_map_settings"].update(settings)
                st.experimental_rerun()
            
            map_control_panel(
                map_id=key,
                on_control_change=on_map_control_change
            )
            
            # マップツールパネル
            def on_tool_action(action_data):
                action = action_data.get("action")
                if action == "reset_center":
                    st.session_state[f"{key}_map_settings"]["center_auto"] = True
                    st.experimental_rerun()
                elif action == "fit_track":
                    st.session_state[f"{key}_map_settings"]["center_auto"] = True
                    st.experimental_rerun()
                elif action == "clear_markers":
                    st.session_state[f"{key}_track_settings"]["custom_markers"] = []
                    st.experimental_rerun()
                elif action == "clear_selection":
                    # 選択クリアのカスタムイベントは現在JavaScriptで実装が必要
                    pass
            
            map_tools_panel(
                map_id=key,
                on_tool_action=on_tool_action
            )
        
        # トラック設定タブ
        with tabs[1]:
            # トラックスタイルパネル
            def on_style_change(settings):
                st.session_state[f"{key}_track_settings"].update(settings)
                st.experimental_rerun()
            
            track_style_panel(
                map_id=key,
                track_settings=st.session_state[f"{key}_track_settings"],
                on_style_change=on_style_change
            )
            
            # カスタムマーカー追加パネル
            def on_add_marker(marker_info):
                if f"{key}_track_settings" in st.session_state:
                    if "custom_markers" not in st.session_state[f"{key}_track_settings"]:
                        st.session_state[f"{key}_track_settings"]["custom_markers"] = []
                    
                    st.session_state[f"{key}_track_settings"]["custom_markers"].append(marker_info)
                    st.experimental_rerun()
            
            track_custom_marker_panel(
                map_id=key,
                on_add_marker=on_add_marker
            )
        
        # 情報タブ
        with tabs[2]:
            track_data_panel(st.session_state[f"{key}_track_stats"])
    
    # 現在の状態を返す
    return {
        "map_settings": st.session_state[f"{key}_map_settings"],
        "track_settings": st.session_state[f"{key}_track_settings"],
        "track_stats": st.session_state[f"{key}_track_stats"]
    }
