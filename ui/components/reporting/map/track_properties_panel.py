"""
ui.components.reporting.map.track_properties_panel

GPSトラックのプロパティ設定パネルを提供するモジュールです。
トラックの表示スタイルやオプションを設定するためのUIコンポーネントを含みます。
"""

import streamlit as st
import json
from typing import Dict, List, Any, Optional, Union, Tuple, Callable


def track_style_panel(map_id: str = None, track_settings: Dict[str, Any] = None,
                     on_style_change: Optional[Callable] = None) -> Dict[str, Any]:
    """
    トラックスタイル設定パネルを表示

    Parameters
    ----------
    map_id : str, optional
        マップID, by default None
    track_settings : Dict[str, Any], optional
        トラック設定の初期値, by default None
    on_style_change : Optional[Callable], optional
        スタイル変更時のコールバック関数, by default None

    Returns
    -------
    Dict[str, Any]
        現在のトラックスタイル設定
    """
    if track_settings is None:
        track_settings = {}
    
    st.markdown("### トラックスタイル")
    
    with st.expander("ライン設定", expanded=True):
        track_color = st.color_picker(
            "トラック色",
            value=track_settings.get("track_color", "#FF5722"),
            key=f"{map_id}_track_color"
        )
        
        track_width = st.slider(
            "線の太さ",
            min_value=1,
            max_value=10,
            value=track_settings.get("track_width", 3),
            key=f"{map_id}_track_width"
        )
        
        track_opacity = st.slider(
            "不透明度",
            min_value=0.0,
            max_value=1.0,
            value=track_settings.get("track_opacity", 0.8),
            step=0.1,
            key=f"{map_id}_track_opacity"
        )
    
    with st.expander("色分け設定", expanded=True):
        color_by = st.selectbox(
            "色分け基準",
            options=["none", "speed", "direction", "time"],
            format_func=lambda x: {
                "none": "単色",
                "speed": "速度",
                "direction": "方向",
                "time": "時間"
            }.get(x, x),
            index=["none", "speed", "direction", "time"].index(track_settings.get("color_by", "none")),
            key=f"{map_id}_color_by"
        )
        
        if color_by != "none":
            color_palette = st.selectbox(
                "カラーパレット",
                options=["default", "viridis", "plasma", "inferno", "magma", "cividis", "turbo"],
                format_func=lambda x: {
                    "default": "デフォルト",
                    "viridis": "Viridis",
                    "plasma": "Plasma",
                    "inferno": "Inferno",
                    "magma": "Magma",
                    "cividis": "Cividis",
                    "turbo": "Turbo"
                }.get(x, x),
                index=["default", "viridis", "plasma", "inferno", "magma", "cividis", "turbo"].index(
                    track_settings.get("color_palette", "default")
                ),
                key=f"{map_id}_color_palette"
            )
    
    with st.expander("マーカー設定", expanded=True):
        show_markers = st.checkbox(
            "マーカーを表示",
            value=track_settings.get("show_markers", True),
            key=f"{map_id}_show_markers"
        )
        
        if show_markers:
            show_start_end_markers = st.checkbox(
                "開始/終了マーカー表示",
                value=track_settings.get("show_start_end_markers", True),
                key=f"{map_id}_show_start_end_markers"
            )
            
            show_significant_points = st.checkbox(
                "重要ポイントを表示",
                value=track_settings.get("show_significant_points", False),
                key=f"{map_id}_show_significant_points"
            )
            
            if show_significant_points:
                min_angle = st.slider(
                    "最小方向変化角度 (度)",
                    min_value=10,
                    max_value=90,
                    value=track_settings.get("significant_min_angle", 30),
                    key=f"{map_id}_significant_min_angle"
                )
                
                min_distance = st.slider(
                    "ポイント間最小距離 (m)",
                    min_value=10,
                    max_value=500,
                    value=track_settings.get("significant_min_distance", 50),
                    key=f"{map_id}_significant_min_distance"
                )
    
    with st.expander("インタラクション設定", expanded=True):
        enable_interaction = st.checkbox(
            "インタラクションを有効化",
            value=track_settings.get("enable_interaction", True),
            key=f"{map_id}_enable_interaction"
        )
        
        if enable_interaction:
            enable_selection = st.checkbox(
                "選択機能を有効化",
                value=track_settings.get("enable_selection", True),
                key=f"{map_id}_enable_selection"
            )
            
            selection_color = st.color_picker(
                "選択時の色",
                value=track_settings.get("selection_color", "#FF4000"),
                key=f"{map_id}_selection_color"
            )
            
            hover_color = st.color_picker(
                "ホバー時の色",
                value=track_settings.get("hover_color", "#FF8000"),
                key=f"{map_id}_hover_color"
            )
    
    # RGB色をRGBA文字列に変換
    def hex_to_rgba(hex_color, opacity=1.0):
        h = hex_color.lstrip('#')
        rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"
    
    # 設定値をまとめる
    updated_settings = {
        "track_color": hex_to_rgba(track_color, track_opacity),
        "track_width": track_width,
        "track_opacity": track_opacity,
        "color_by": color_by,
        "show_markers": show_markers,
        "enable_interaction": enable_interaction,
        "enable_selection": enable_selection if enable_interaction else False,
        "selection_color": hex_to_rgba(selection_color, track_opacity + 0.1),
        "hover_color": hex_to_rgba(hover_color, track_opacity - 0.1)
    }
    
    if color_by != "none":
        updated_settings["color_palette"] = color_palette
    
    if show_markers:
        updated_settings["show_start_end_markers"] = show_start_end_markers
        updated_settings["show_significant_points"] = show_significant_points
        
        if show_significant_points:
            updated_settings["significant_min_angle"] = min_angle
            updated_settings["significant_min_distance"] = min_distance
    
    # コールバック呼び出し
    if on_style_change:
        on_style_change(updated_settings)
    
    return updated_settings


def track_data_panel(track_data: Dict[str, Any] = None) -> None:
    """
    トラックデータ情報パネルを表示

    Parameters
    ----------
    track_data : Dict[str, Any], optional
        トラックデータ統計情報, by default None
    """
    st.markdown("### トラック情報")
    
    if track_data is None:
        st.info("トラックデータがありません")
        return
    
    with st.expander("基本情報", expanded=True):
        distance = track_data.get("distance", 0)
        if distance < 1000:
            distance_text = f"{distance:.1f} m"
        else:
            distance_text = f"{distance/1000:.2f} km"
        
        duration = track_data.get("duration", 0)
        if duration < 60:
            duration_text = f"{int(duration)} 秒"
        elif duration < 3600:
            minutes = int(duration // 60)
            seconds = int(duration % 60)
            duration_text = f"{minutes}分 {seconds}秒"
        else:
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            duration_text = f"{hours}時間 {minutes}分"
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("総距離", distance_text)
            
            if track_data.get("avg_speed", 0) > 0:
                st.metric("平均速度", f"{track_data.get('avg_speed', 0):.1f} kn")
        
        with col2:
            st.metric("所要時間", duration_text)
            
            if track_data.get("max_speed", 0) > 0:
                st.metric("最高速度", f"{track_data.get('max_speed', 0):.1f} kn")
    
    with st.expander("詳細情報", expanded=False):
        if track_data.get("min_speed", 0) > 0:
            st.metric("最低速度", f"{track_data.get('min_speed', 0):.1f} kn")
        
        if track_data.get("median_speed", 0) > 0:
            st.metric("中央値速度", f"{track_data.get('median_speed', 0):.1f} kn")
        
        if track_data.get("speed_variance", 0) > 0:
            st.metric("速度分散", f"{track_data.get('speed_variance', 0):.2f}")
        
        bb = track_data.get("bounding_box", {})
        if bb and all(v != 0 for v in bb.values()):
            st.markdown("##### 範囲")
            st.text(f"北緯: {bb.get('max_lat', 0):.6f}")
            st.text(f"南緯: {bb.get('min_lat', 0):.6f}")
            st.text(f"東経: {bb.get('max_lng', 0):.6f}")
            st.text(f"西経: {bb.get('min_lng', 0):.6f}")


def track_custom_marker_panel(map_id: str = None, on_add_marker: Optional[Callable] = None) -> Optional[Dict[str, Any]]:
    """
    カスタムマーカー追加パネルを表示

    Parameters
    ----------
    map_id : str, optional
        マップID, by default None
    on_add_marker : Optional[Callable], optional
        マーカー追加時のコールバック関数, by default None

    Returns
    -------
    Optional[Dict[str, Any]]
        追加されたマーカー情報（追加がない場合はNone）
    """
    st.markdown("### カスタムマーカー追加")
    
    with st.form(key=f"{map_id}_add_marker_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            lat = st.number_input("緯度", value=0.0, format="%.6f", key=f"{map_id}_marker_lat")
            title = st.text_input("タイトル", key=f"{map_id}_marker_title")
        
        with col2:
            lng = st.number_input("経度", value=0.0, format="%.6f", key=f"{map_id}_marker_lng")
            description = st.text_input("説明", key=f"{map_id}_marker_description")
        
        color = st.color_picker("マーカー色", value="#1E88E5", key=f"{map_id}_marker_color")
        
        icon = st.selectbox(
            "アイコン",
            options=["map-marker-alt", "flag", "star", "circle", "info", "exclamation", "anchor", "ship"],
            key=f"{map_id}_marker_icon"
        )
        
        submitted = st.form_submit_button("マーカーを追加")
        
        if submitted and lat != 0 and lng != 0:
            marker_info = {
                "lat": lat,
                "lng": lng,
                "title": title,
                "description": description,
                "color": color,
                "icon": icon
            }
            
            if on_add_marker:
                on_add_marker(marker_info)
            
            return marker_info
    
    return None
