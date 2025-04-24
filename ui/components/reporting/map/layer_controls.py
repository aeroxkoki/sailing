# -*- coding: utf-8 -*-
"""
ui.components.reporting.map.layer_controls

マップレイヤーコントロールUIコンポーネントを提供するモジュールです。
このモジュールは、レイヤーの表示/非表示、順序、プロパティなどを制御するUIを含みます。
"""

import streamlit as st
import json
from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd

from sailing_data_processor.reporting.elements.map.layers.base_layer import BaseMapLayer
from sailing_data_processor.reporting.elements.map.layers.layer_manager import LayerManager
from sailing_data_processor.reporting.elements.map.layers.wind_field_layer import WindFieldLayer
from sailing_data_processor.reporting.elements.map.layers.course_elements_layer import CourseElementsLayer
from sailing_data_processor.reporting.elements.map.layers.heat_map_layer import HeatMapLayer


def layer_manager_panel(layer_manager: LayerManager, 
                       on_change: Optional[Callable[[str], None]] = None,
                       key_prefix: str = "") -> Dict[str, Any]:
    """
    レイヤーマネージャーコントロールパネルを表示

    Parameters
    ----------
    layer_manager : LayerManager
        レイヤーマネージャー
    on_change : Optional[Callable[[str], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""

    Returns
    -------
    Dict[str, Any]
        変更されたレイヤー情報
    """
    st.markdown("### レイヤー管理")
    
    changes = {}
    
    # レイヤー一覧の表示
    ordered_layers = layer_manager.get_ordered_layers()
    
    if not ordered_layers:
        st.info("レイヤーがありません。レイヤーを追加してください。")
        return changes
    
    # レイヤーコントロールテーブル
    layer_data = []
    for layer in ordered_layers:
        layer_data.append({
            "ID": layer.layer_id,
            "名前": layer.name,
            "タイプ": layer.__class__.__name__,
            "表示": layer.visible,
            "不透明度": layer.opacity,
            "Z順序": layer.z_index
        })
    
    # DataFrameとして表示
    df = pd.DataFrame(layer_data)
    
    # インタラクティブなレイヤーコントロール
    with st.expander("レイヤー一覧", expanded=True):
        # 表示設定テーブル
        edited_df = st.data_editor(
            df,
            column_config={
                "ID": st.column_config.TextColumn("ID", width="small", disabled=True),
                "名前": st.column_config.TextColumn("名前", width="medium"),
                "タイプ": st.column_config.TextColumn("タイプ", width="small", disabled=True),
                "表示": st.column_config.CheckboxColumn("表示", width="small"),
                "不透明度": st.column_config.NumberColumn("不透明度", width="small", min_value=0.0, max_value=1.0, format="%.2f", step=0.1),
                "Z順序": st.column_config.NumberColumn("Z順序", width="small", format="%d", step=1)
            },
            hide_index=True,
            key=f"{key_prefix}_layer_editor"
        )
        
        # 変更を検出して反映
        for i, row in edited_df.iterrows():
            layer_id = row["ID"]
            layer = layer_manager.get_layer(layer_id)
            if layer:
                # 表示状態の変更
                if layer.visible != row["表示"]:
                    layer.visible = row["表示"]
                    changes[f"{layer_id}_visible"] = row["表示"]
                
                # 不透明度の変更
                if layer.opacity != row["不透明度"]:
                    layer.opacity = row["不透明度"]
                    changes[f"{layer_id}_opacity"] = row["不透明度"]
                
                # Z順序の変更
                if layer.z_index != row["Z順序"]:
                    layer.z_index = int(row["Z順序"])
                    changes[f"{layer_id}_z_index"] = int(row["Z順序"])
                
                # 名前の変更
                if layer.name != row["名前"]:
                    layer.name = row["名前"]
                    changes[f"{layer_id}_name"] = row["名前"]
    
    # レイヤー順序操作ツール
    st.markdown("#### レイヤー操作")
    
    # レイヤー選択
    selected_layer_id = st.selectbox(
        "レイヤーを選択",
        options=[layer.layer_id for layer in ordered_layers],
        format_func=lambda x: next((layer.name for layer in ordered_layers if layer.layer_id == x), x),
        key=f"{key_prefix}_layer_select"
    )
    
    if selected_layer_id:
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            if st.button("上へ移動", key=f"{key_prefix}_move_up"):
                if layer_manager.move_layer_up(selected_layer_id):
                    changes[f"{selected_layer_id}_moved"] = "up"
                    if on_change:
                        on_change("layer_order_changed")
        
        with col2:
            if st.button("下へ移動", key=f"{key_prefix}_move_down"):
                if layer_manager.move_layer_down(selected_layer_id):
                    changes[f"{selected_layer_id}_moved"] = "down"
                    if on_change:
                        on_change("layer_order_changed")
        
        with col3:
            if st.button("表示切替", key=f"{key_prefix}_toggle_visibility"):
                layer = layer_manager.get_layer(selected_layer_id)
                if layer:
                    layer.visible = not layer.visible
                    changes[f"{selected_layer_id}_visible"] = layer.visible
                    if on_change:
                        on_change("layer_visibility_changed")
        
        with col4:
            if st.button("削除", key=f"{key_prefix}_delete_layer"):
                if st.session_state.get(f"{key_prefix}_confirm_delete_{selected_layer_id}", False):
                    layer_manager.remove_layer(selected_layer_id)
                    changes[f"{selected_layer_id}_deleted"] = True
                    if on_change:
                        on_change("layer_deleted")
                    st.session_state[f"{key_prefix}_confirm_delete_{selected_layer_id}"] = False
                else:
                    st.session_state[f"{key_prefix}_confirm_delete_{selected_layer_id}"] = True
                    st.warning(f"削除を確認するには、もう一度「削除」ボタンをクリックしてください。")
    
    # グループコントロール（グループがある場合）
    groups = layer_manager.get_groups()
    if groups:
        st.markdown("#### グループ管理")
        selected_group = st.selectbox(
            "グループを選択",
            options=groups,
            key=f"{key_prefix}_group_select"
        )
        
        if selected_group:
            group_layers = layer_manager.get_group_layers(selected_group)
            
            if group_layers:
                group_visible = all(layer.visible for layer in group_layers)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(
                        "すべて表示" if not group_visible else "すべて非表示", 
                        key=f"{key_prefix}_toggle_group"
                    ):
                        layer_manager.set_group_visibility(selected_group, not group_visible)
                        changes[f"group_{selected_group}_visible"] = not group_visible
                        if on_change:
                            on_change("group_visibility_changed")
                
                with col2:
                    if st.button("グループ削除", key=f"{key_prefix}_delete_group"):
                        if st.session_state.get(f"{key_prefix}_confirm_delete_group_{selected_group}", False):
                            layer_manager.remove_group(selected_group)
                            changes[f"group_{selected_group}_deleted"] = True
                            if on_change:
                                on_change("group_deleted")
                            st.session_state[f"{key_prefix}_confirm_delete_group_{selected_group}"] = False
                        else:
                            st.session_state[f"{key_prefix}_confirm_delete_group_{selected_group}"] = True
                            st.warning(f"グループの削除を確認するには、もう一度「グループ削除」ボタンをクリックしてください。")
    
    # レイヤーの追加
    st.markdown("#### レイヤーの追加")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_layer_type = st.selectbox(
            "レイヤータイプ", 
            options=["WindFieldLayer", "CourseElementsLayer", "HeatMapLayer"],
            format_func=lambda x: {
                "WindFieldLayer": "風場レイヤー",
                "CourseElementsLayer": "コース要素レイヤー",
                "HeatMapLayer": "ヒートマップレイヤー"
            }.get(x, x),
            key=f"{key_prefix}_new_layer_type"
        )
    
    with col2:
        new_layer_name = st.text_input(
            "レイヤー名",
            value="",
            key=f"{key_prefix}_new_layer_name"
        )
    
    if st.button("レイヤーを追加", key=f"{key_prefix}_add_layer"):
        if new_layer_name:
            # レイヤーの作成
            new_layer = None
            if new_layer_type == "WindFieldLayer":
                new_layer = WindFieldLayer(name=new_layer_name)
            elif new_layer_type == "CourseElementsLayer":
                new_layer = CourseElementsLayer(name=new_layer_name)
            elif new_layer_type == "HeatMapLayer":
                new_layer = HeatMapLayer(name=new_layer_name)
            
            if new_layer:
                # Z順序の設定（最大Z順序+1）
                max_z = max([layer.z_index for layer in ordered_layers], default=-1)
                new_layer.z_index = max_z + 1
                
                # レイヤーの追加
                layer_manager.add_layer(new_layer)
                changes[f"new_layer_{new_layer.layer_id}"] = {
                    "type": new_layer_type,
                    "name": new_layer_name
                }
                
                if on_change:
                    on_change("layer_added")
        else:
            st.warning("レイヤー名を入力してください。")
    
    # コールバックを呼び出し
    if changes and on_change:
        on_change("layer_changed")
    
    return changes


def layer_property_panel(layer: BaseMapLayer, 
                        on_change: Optional[Callable[[str], None]] = None,
                        key_prefix: str = "") -> Dict[str, Any]:
    """
    レイヤープロパティパネルを表示

    Parameters
    ----------
    layer : BaseMapLayer
        レイヤー
    on_change : Optional[Callable[[str], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""

    Returns
    -------
    Dict[str, Any]
        変更されたプロパティ情報
    """
    st.markdown(f"### {layer.name} - プロパティ")
    
    changes = {}
    
    # レイヤータイプに応じたプロパティパネルを表示
    if isinstance(layer, WindFieldLayer):
        changes.update(wind_field_layer_property_panel(layer, on_change, key_prefix))
    elif isinstance(layer, CourseElementsLayer):
        changes.update(course_elements_layer_property_panel(layer, on_change, key_prefix))
    elif isinstance(layer, HeatMapLayer):
        changes.update(heat_map_layer_property_panel(layer, on_change, key_prefix))
    else:
        # 基本プロパティ（すべてのレイヤータイプ共通）
        changes.update(base_layer_property_panel(layer, on_change, key_prefix))
    
    return changes


def base_layer_property_panel(layer: BaseMapLayer, 
                             on_change: Optional[Callable[[str], None]] = None,
                             key_prefix: str = "") -> Dict[str, Any]:
    """
    基本レイヤープロパティパネルを表示

    Parameters
    ----------
    layer : BaseMapLayer
        レイヤー
    on_change : Optional[Callable[[str], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""

    Returns
    -------
    Dict[str, Any]
        変更されたプロパティ情報
    """
    changes = {}
    
    with st.expander("基本設定", expanded=True):
        # 表示設定
        visible = st.checkbox(
            "表示",
            value=layer.visible,
            key=f"{key_prefix}_{layer.layer_id}_visible"
        )
        
        if visible != layer.visible:
            layer.visible = visible
            changes["visible"] = visible
        
        # 不透明度
        opacity = st.slider(
            "不透明度",
            min_value=0.0,
            max_value=1.0,
            value=layer.opacity,
            step=0.1,
            format="%.1f",
            key=f"{key_prefix}_{layer.layer_id}_opacity"
        )
        
        if opacity != layer.opacity:
            layer.opacity = opacity
            changes["opacity"] = opacity
        
        # Z順序
        z_index = st.number_input(
            "Z順序",
            min_value=0,
            value=layer.z_index,
            step=1,
            key=f"{key_prefix}_{layer.layer_id}_z_index"
        )
        
        if z_index != layer.z_index:
            layer.z_index = z_index
            changes["z_index"] = z_index
        
        # データソース
        data_source = st.text_input(
            "データソース",
            value=layer.data_source or "",
            key=f"{key_prefix}_{layer.layer_id}_data_source"
        )
        
        if data_source != (layer.data_source or ""):
            layer.data_source = data_source if data_source else None
            changes["data_source"] = data_source
    
    # その他のプロパティ
    with st.expander("詳細設定", expanded=False):
        st.markdown("#### その他のプロパティ")
        
        # プロパティの表示と編集
        for key, value in layer._properties.items():
            # 既に上部で編集したプロパティはスキップ
            if key in ["visible", "opacity", "z_index", "data_source"]:
                continue
            
            # プロパティの型に応じたUI要素
            if isinstance(value, bool):
                new_value = st.checkbox(
                    key,
                    value=value,
                    key=f"{key_prefix}_{layer.layer_id}_prop_{key}"
                )
            elif isinstance(value, (int, float)) and key != "z_index":
                if isinstance(value, int):
                    new_value = st.number_input(
                        key,
                        value=value,
                        key=f"{key_prefix}_{layer.layer_id}_prop_{key}"
                    )
                else:
                    new_value = st.number_input(
                        key,
                        value=value,
                        format="%.2f",
                        key=f"{key_prefix}_{layer.layer_id}_prop_{key}"
                    )
            elif isinstance(value, str):
                new_value = st.text_input(
                    key,
                    value=value,
                    key=f"{key_prefix}_{layer.layer_id}_prop_{key}"
                )
            elif value is None:
                if st.checkbox(
                    f"設定: {key}",
                    value=False,
                    key=f"{key_prefix}_{layer.layer_id}_prop_{key}_set"
                ):
                    new_value = st.text_input(
                        key,
                        value="",
                        key=f"{key_prefix}_{layer.layer_id}_prop_{key}_value"
                    )
                else:
                    new_value = None
            else:
                # 複雑な型はJSON形式で表示
                st.text(f"{key}: {value}")
                continue
            
            # 値が変更された場合
            if new_value != value:
                layer.set_property(key, new_value)
                changes[key] = new_value
    
    # コールバックを呼び出し
    if changes and on_change:
        on_change("base_properties_changed")
    
    return changes


def wind_field_layer_property_panel(layer: WindFieldLayer, 
                                   on_change: Optional[Callable[[str], None]] = None,
                                   key_prefix: str = "") -> Dict[str, Any]:
    """
    風場レイヤープロパティパネルを表示

    Parameters
    ----------
    layer : WindFieldLayer
        風場レイヤー
    on_change : Optional[Callable[[str], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""

    Returns
    -------
    Dict[str, Any]
        変更されたプロパティ情報
    """
    changes = {}
    
    # 基本設定
    base_changes = base_layer_property_panel(layer, None, key_prefix)
    changes.update(base_changes)
    
    # 表示設定
    with st.expander("表示設定", expanded=True):
        # 表示タイプ
        display_type = st.selectbox(
            "表示タイプ",
            options=["arrows", "streamlines", "barbs", "grid"],
            format_func=lambda x: {
                "arrows": "矢印",
                "streamlines": "ストリームライン",
                "barbs": "風向羽",
                "grid": "グリッド"
            }.get(x, x),
            index=["arrows", "streamlines", "barbs", "grid"].index(layer.get_property("display_type", "arrows")),
            key=f"{key_prefix}_{layer.layer_id}_display_type"
        )
        
        if display_type != layer.get_property("display_type", "arrows"):
            layer.set_display_type(display_type)
            changes["display_type"] = display_type
        
        # 矢印スケール（矢印表示の場合）
        if display_type == "arrows":
            arrow_scale = st.slider(
                "矢印スケール",
                min_value=0.1,
                max_value=5.0,
                value=layer.get_property("arrow_scale", 1.0),
                step=0.1,
                format="%.1f",
                key=f"{key_prefix}_{layer.layer_id}_arrow_scale"
            )
            
            if arrow_scale != layer.get_property("arrow_scale", 1.0):
                layer.set_arrow_scale(arrow_scale)
                changes["arrow_scale"] = arrow_scale
            
            arrow_density = st.slider(
                "矢印密度",
                min_value=5,
                max_value=50,
                value=layer.get_property("arrow_density", 15),
                step=1,
                key=f"{key_prefix}_{layer.layer_id}_arrow_density"
            )
            
            if arrow_density != layer.get_property("arrow_density", 15):
                layer.set_arrow_density(arrow_density)
                changes["arrow_density"] = arrow_density
        
        # カラースケール
        col1, col2 = st.columns(2)
        
        with col1:
            color_scale = st.selectbox(
                "カラースケール",
                options=["viridis", "plasma", "inferno", "magma", "blues", "custom"],
                format_func=lambda x: {
                    "viridis": "Viridis",
                    "plasma": "Plasma",
                    "inferno": "Inferno",
                    "magma": "Magma",
                    "blues": "Blues",
                    "custom": "カスタム"
                }.get(x, x),
                index=["viridis", "plasma", "inferno", "magma", "blues", "custom"].index(
                    layer.get_property("color_scale", "viridis")
                ),
                key=f"{key_prefix}_{layer.layer_id}_color_scale"
            )
            
            if color_scale != layer.get_property("color_scale", "viridis"):
                layer.set_color_scale(color_scale)
                changes["color_scale"] = color_scale
        
        with col2:
            color_by = st.selectbox(
                "色付け基準",
                options=["speed", "direction", "none"],
                format_func=lambda x: {
                    "speed": "風速",
                    "direction": "風向",
                    "none": "なし"
                }.get(x, x),
                index=["speed", "direction", "none"].index(
                    layer.get_property("color_by", "speed")
                ),
                key=f"{key_prefix}_{layer.layer_id}_color_by"
            )
            
            if color_by != layer.get_property("color_by", "speed"):
                layer.set_property("color_by", color_by)
                changes["color_by"] = color_by
        
        # 凡例表示
        show_legend = st.checkbox(
            "凡例を表示",
            value=layer.get_property("show_legend", True),
            key=f"{key_prefix}_{layer.layer_id}_show_legend"
        )
        
        if show_legend != layer.get_property("show_legend", True):
            layer.set_property("show_legend", show_legend)
            changes["show_legend"] = show_legend
    
    # 風速範囲設定
    with st.expander("風速範囲設定", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            min_speed = layer.get_property("min_speed", None)
            min_speed_value = "" if min_speed is None else str(min_speed)
            
            new_min_speed = st.text_input(
                "最小風速（kt）",
                value=min_speed_value,
                key=f"{key_prefix}_{layer.layer_id}_min_speed"
            )
            
            try:
                if new_min_speed:
                    new_min_speed = float(new_min_speed)
                    if min_speed != new_min_speed:
                        layer.set_property("min_speed", new_min_speed)
                        changes["min_speed"] = new_min_speed
                else:
                    if min_speed is not None:
                        layer.set_property("min_speed", None)
                        changes["min_speed"] = None
            except ValueError:
                st.warning("最小風速には数値を入力してください。")
        
        with col2:
            max_speed = layer.get_property("max_speed", None)
            max_speed_value = "" if max_speed is None else str(max_speed)
            
            new_max_speed = st.text_input(
                "最大風速（kt）",
                value=max_speed_value,
                key=f"{key_prefix}_{layer.layer_id}_max_speed"
            )
            
            try:
                if new_max_speed:
                    new_max_speed = float(new_max_speed)
                    if max_speed != new_max_speed:
                        layer.set_property("max_speed", new_max_speed)
                        changes["max_speed"] = new_max_speed
                else:
                    if max_speed is not None:
                        layer.set_property("max_speed", None)
                        changes["max_speed"] = None
            except ValueError:
                st.warning("最大風速には数値を入力してください。")
    
    # フィルタ設定
    with st.expander("フィルタ設定", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            min_filter = st.number_input(
                "最小表示風速（kt）",
                min_value=0.0,
                value=layer.get_property("min_filter", 0.0),
                step=0.5,
                format="%.1f",
                key=f"{key_prefix}_{layer.layer_id}_min_filter"
            )
            
            if min_filter != layer.get_property("min_filter", 0.0):
                layer.set_property("min_filter", min_filter)
                changes["min_filter"] = min_filter
        
        with col2:
            max_filter = st.number_input(
                "最大表示風速（kt）",
                min_value=0.0,
                value=layer.get_property("max_filter", 50.0),
                step=1.0,
                format="%.1f",
                key=f"{key_prefix}_{layer.layer_id}_max_filter"
            )
            
            if max_filter != layer.get_property("max_filter", 50.0):
                layer.set_property("max_filter", max_filter)
                changes["max_filter"] = max_filter
        
        show_calm = st.checkbox(
            "微風を表示",
            value=layer.get_property("show_calm", True),
            key=f"{key_prefix}_{layer.layer_id}_show_calm"
        )
        
        if show_calm != layer.get_property("show_calm", True):
            layer.set_property("show_calm", show_calm)
            changes["show_calm"] = show_calm
    
    # シフト検出設定
    with st.expander("シフト検出", expanded=False):
        show_shifts = st.checkbox(
            "風向シフトを表示",
            value=layer.get_property("show_shifts", False),
            key=f"{key_prefix}_{layer.layer_id}_show_shifts"
        )
        
        if show_shifts != layer.get_property("show_shifts", False):
            layer.set_property("show_shifts", show_shifts)
            changes["show_shifts"] = show_shifts
        
        if show_shifts:
            shift_threshold = st.slider(
                "シフト検出閾値（度）",
                min_value=5,
                max_value=45,
                value=layer.get_property("shift_threshold", 15),
                step=1,
                key=f"{key_prefix}_{layer.layer_id}_shift_threshold"
            )
            
            if shift_threshold != layer.get_property("shift_threshold", 15):
                layer.set_property("shift_threshold", shift_threshold)
                changes["shift_threshold"] = shift_threshold
    
    # 時間設定
    with st.expander("時間設定", expanded=False):
        time_index = st.number_input(
            "時間インデックス",
            min_value=0,
            value=layer.get_property("time_index", 0),
            step=1,
            key=f"{key_prefix}_{layer.layer_id}_time_index"
        )
        
        if time_index != layer.get_property("time_index", 0):
            layer.set_time_index(time_index)
            changes["time_index"] = time_index
        
        animate = st.checkbox(
            "アニメーション",
            value=layer.get_property("animate", False),
            key=f"{key_prefix}_{layer.layer_id}_animate"
        )
        
        if animate != layer.get_property("animate", False):
            layer.set_property("animate", animate)
            changes["animate"] = animate
    
    # コールバックを呼び出し
    if changes and on_change:
        on_change("wind_field_properties_changed")
    
    return changes


def course_elements_layer_property_panel(layer: CourseElementsLayer, 
                                        on_change: Optional[Callable[[str], None]] = None,
                                        key_prefix: str = "") -> Dict[str, Any]:
    """
    コース要素レイヤープロパティパネルを表示

    Parameters
    ----------
    layer : CourseElementsLayer
        コース要素レイヤー
    on_change : Optional[Callable[[str], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""

    Returns
    -------
    Dict[str, Any]
        変更されたプロパティ情報
    """
    changes = {}
    
    # 基本設定
    base_changes = base_layer_property_panel(layer, None, key_prefix)
    changes.update(base_changes)
    
    # コース設定
    with st.expander("コース設定", expanded=True):
        # コースタイプ
        course_type = st.selectbox(
            "コースタイプ",
            options=["windward_leeward", "triangle", "trapezoid", "custom"],
            format_func=lambda x: {
                "windward_leeward": "ウインドワード/リーワード",
                "triangle": "トライアングル",
                "trapezoid": "トラぺゾイド",
                "custom": "カスタム"
            }.get(x, x),
            index=["windward_leeward", "triangle", "trapezoid", "custom"].index(
                layer.get_property("course_type", "windward_leeward")
            ),
            key=f"{key_prefix}_{layer.layer_id}_course_type"
        )
        
        if course_type != layer.get_property("course_type", "windward_leeward"):
            layer.set_course_type(course_type)
            changes["course_type"] = course_type
        
        # 風向設定
        wind_direction = st.slider(
            "風向（度）",
            min_value=0,
            max_value=359,
            value=layer.get_property("wind_direction", 0),
            step=1,
            key=f"{key_prefix}_{layer.layer_id}_wind_direction"
        )
        
        if wind_direction != layer.get_property("wind_direction", 0):
            layer.set_wind_direction(wind_direction)
            changes["wind_direction"] = wind_direction
    
    # マーク設定
    with st.expander("マーク設定", expanded=True):
        # マークサイズ
        mark_size = st.slider(
            "マークサイズ",
            min_value=5,
            max_value=30,
            value=layer.get_property("mark_size", 15),
            step=1,
            key=f"{key_prefix}_{layer.layer_id}_mark_size"
        )
        
        if mark_size != layer.get_property("mark_size", 15):
            layer.set_property("mark_size", mark_size)
            changes["mark_size"] = mark_size
        
        # 色設定
        col1, col2 = st.columns(2)
        
        with col1:
            mark_color = st.color_picker(
                "マーク色",
                value=layer.get_property("mark_color", "#FF4500"),
                key=f"{key_prefix}_{layer.layer_id}_mark_color"
            )
            
            if mark_color != layer.get_property("mark_color", "#FF4500"):
                layer.set_property("mark_color", mark_color)
                changes["mark_color"] = mark_color
            
            gate_color = st.color_picker(
                "ゲート色",
                value=layer.get_property("gate_color", "#4169E1"),
                key=f"{key_prefix}_{layer.layer_id}_gate_color"
            )
            
            if gate_color != layer.get_property("gate_color", "#4169E1"):
                layer.set_property("gate_color", gate_color)
                changes["gate_color"] = gate_color
        
        with col2:
            start_color = st.color_picker(
                "スタートライン色",
                value=layer.get_property("start_color", "#32CD32"),
                key=f"{key_prefix}_{layer.layer_id}_start_color"
            )
            
            if start_color != layer.get_property("start_color", "#32CD32"):
                layer.set_property("start_color", start_color)
                changes["start_color"] = start_color
            
            finish_color = st.color_picker(
                "フィニッシュライン色",
                value=layer.get_property("finish_color", "#FF6347"),
                key=f"{key_prefix}_{layer.layer_id}_finish_color"
            )
            
            if finish_color != layer.get_property("finish_color", "#FF6347"):
                layer.set_property("finish_color", finish_color)
                changes["finish_color"] = finish_color
        
        # 表示設定
        col1, col2 = st.columns(2)
        
        with col1:
            show_marks = st.checkbox(
                "マークを表示",
                value=layer.get_property("show_marks", True),
                key=f"{key_prefix}_{layer.layer_id}_show_marks"
            )
            
            if show_marks != layer.get_property("show_marks", True):
                layer.set_property("show_marks", show_marks)
                changes["show_marks"] = show_marks
            
            show_gates = st.checkbox(
                "ゲートを表示",
                value=layer.get_property("show_gates", True),
                key=f"{key_prefix}_{layer.layer_id}_show_gates"
            )
            
            if show_gates != layer.get_property("show_gates", True):
                layer.set_property("show_gates", show_gates)
                changes["show_gates"] = show_gates
        
        with col2:
            show_start_finish = st.checkbox(
                "スタート/フィニッシュを表示",
                value=layer.get_property("show_start_finish", True),
                key=f"{key_prefix}_{layer.layer_id}_show_start_finish"
            )
            
            if show_start_finish != layer.get_property("show_start_finish", True):
                layer.set_property("show_start_finish", show_start_finish)
                changes["show_start_finish"] = show_start_finish
            
            show_course_lines = st.checkbox(
                "コース線を表示",
                value=layer.get_property("show_course_lines", True),
                key=f"{key_prefix}_{layer.layer_id}_show_course_lines"
            )
            
            if show_course_lines != layer.get_property("show_course_lines", True):
                layer.set_property("show_course_lines", show_course_lines)
                changes["show_course_lines"] = show_course_lines
    
    # レイライン設定
    with st.expander("レイライン設定", expanded=False):
        show_laylines = st.checkbox(
            "レイラインを表示",
            value=layer.get_property("show_laylines", False),
            key=f"{key_prefix}_{layer.layer_id}_show_laylines"
        )
        
        if show_laylines != layer.get_property("show_laylines", False):
            layer.set_property("show_laylines", show_laylines)
            changes["show_laylines"] = show_laylines
        
        if show_laylines:
            col1, col2 = st.columns(2)
            
            with col1:
                twa_upwind = st.slider(
                    "風上艇角度（度）",
                    min_value=30,
                    max_value=90,
                    value=layer.get_property("twa_upwind", 45),
                    step=1,
                    key=f"{key_prefix}_{layer.layer_id}_twa_upwind"
                )
                
                if twa_upwind != layer.get_property("twa_upwind", 45):
                    layer.set_twa(upwind=twa_upwind)
                    changes["twa_upwind"] = twa_upwind
            
            with col2:
                twa_downwind = st.slider(
                    "風下艇角度（度）",
                    min_value=90,
                    max_value=180,
                    value=layer.get_property("twa_downwind", 150),
                    step=1,
                    key=f"{key_prefix}_{layer.layer_id}_twa_downwind"
                )
                
                if twa_downwind != layer.get_property("twa_downwind", 150):
                    layer.set_twa(downwind=twa_downwind)
                    changes["twa_downwind"] = twa_downwind
            
            layline_length = st.slider(
                "レイライン長さ（km）",
                min_value=0.1,
                max_value=2.0,
                value=layer.get_property("layline_length", 0.5),
                step=0.1,
                format="%.1f",
                key=f"{key_prefix}_{layer.layer_id}_layline_length"
            )
            
            if layline_length != layer.get_property("layline_length", 0.5):
                layer.set_property("layline_length", layline_length)
                changes["layline_length"] = layline_length
            
            layline_color = st.color_picker(
                "レイライン色",
                value=layer.get_property("layline_color", "#FF8C00"),
                key=f"{key_prefix}_{layer.layer_id}_layline_color"
            )
            
            if layline_color != layer.get_property("layline_color", "#FF8C00"):
                layer.set_property("layline_color", layline_color)
                changes["layline_color"] = layline_color
    
    # マーク管理
    with st.expander("マーク管理", expanded=False):
        marks = layer.get_property("marks", [])
        
        if marks:
            st.markdown("#### 既存のマーク")
            
            # マークのテーブル表示
            mark_data = []
            for i, mark in enumerate(marks):
                mark_type = "通常"
                if mark.get("is_gate", False):
                    mark_type = "ゲート"
                elif mark.get("is_start", False):
                    mark_type = "スタート"
                elif mark.get("is_finish", False):
                    mark_type = "フィニッシュ"
                
                mark_data.append({
                    "索引": i,
                    "名前": mark.get("name", f"マーク {i+1}"),
                    "タイプ": mark_type,
                    "緯度": mark.get("lat"),
                    "経度": mark.get("lng")
                })
            
            mark_df = pd.DataFrame(mark_data)
            st.dataframe(mark_df, hide_index=True)
            
            # マーク削除
            if st.button("すべてのマークを削除", key=f"{key_prefix}_{layer.layer_id}_clear_marks"):
                if st.session_state.get(f"{key_prefix}_{layer.layer_id}_confirm_clear_marks", False):
                    layer.clear_marks()
                    changes["marks_cleared"] = True
                    st.session_state[f"{key_prefix}_{layer.layer_id}_confirm_clear_marks"] = False
                    st.rerun()
                else:
                    st.session_state[f"{key_prefix}_{layer.layer_id}_confirm_clear_marks"] = True
                    st.warning("すべてのマークを削除します。もう一度ボタンをクリックして確認してください。")
        else:
            st.info("マークがありません。マークを追加してください。")
        
        # マーク追加
        st.markdown("#### マークの追加")
        
        mark_type = st.selectbox(
            "マークタイプ",
            options=["standard", "gate", "start", "finish"],
            format_func=lambda x: {
                "standard": "通常マーク",
                "gate": "ゲート",
                "start": "スタートライン",
                "finish": "フィニッシュライン"
            }.get(x, x),
            key=f"{key_prefix}_{layer.layer_id}_new_mark_type"
        )
        
        if mark_type == "standard":
            # 通常マーク
            col1, col2 = st.columns(2)
            
            with col1:
                mark_lat = st.number_input(
                    "緯度",
                    min_value=-90.0,
                    max_value=90.0,
                    value=35.4498,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_mark_lat"
                )
            
            with col2:
                mark_lng = st.number_input(
                    "経度",
                    min_value=-180.0,
                    max_value=180.0,
                    value=139.6649,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_mark_lng"
                )
            
            mark_name = st.text_input(
                "マーク名",
                value="",
                key=f"{key_prefix}_{layer.layer_id}_new_mark_name"
            )
            
            if st.button("マークを追加", key=f"{key_prefix}_{layer.layer_id}_add_mark"):
                layer.add_mark(mark_lat, mark_lng, name=mark_name)
                changes["mark_added"] = {
                    "type": "standard",
                    "lat": mark_lat,
                    "lng": mark_lng,
                    "name": mark_name
                }
                st.rerun()
        
        elif mark_type == "gate":
            # ゲート
            st.markdown("左右のマーク位置を指定してください")
            
            col1, col2 = st.columns(2)
            
            with col1:
                left_lat = st.number_input(
                    "左マーク緯度",
                    min_value=-90.0,
                    max_value=90.0,
                    value=35.4498,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_gate_left_lat"
                )
                
                left_lng = st.number_input(
                    "左マーク経度",
                    min_value=-180.0,
                    max_value=180.0,
                    value=139.6649,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_gate_left_lng"
                )
            
            with col2:
                right_lat = st.number_input(
                    "右マーク緯度",
                    min_value=-90.0,
                    max_value=90.0,
                    value=35.4508,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_gate_right_lat"
                )
                
                right_lng = st.number_input(
                    "右マーク経度",
                    min_value=-180.0,
                    max_value=180.0,
                    value=139.6659,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_gate_right_lng"
                )
            
            gate_name = st.text_input(
                "ゲート名",
                value="",
                key=f"{key_prefix}_{layer.layer_id}_new_gate_name"
            )
            
            if st.button("ゲートを追加", key=f"{key_prefix}_{layer.layer_id}_add_gate"):
                layer.add_gate(left_lat, left_lng, right_lat, right_lng, name=gate_name)
                changes["gate_added"] = {
                    "type": "gate",
                    "left_lat": left_lat,
                    "left_lng": left_lng,
                    "right_lat": right_lat,
                    "right_lng": right_lng,
                    "name": gate_name
                }
                st.rerun()
        
        elif mark_type == "start":
            # スタートライン
            st.markdown("ピン側とコミッティ側の位置を指定してください")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pin_lat = st.number_input(
                    "ピン側緯度",
                    min_value=-90.0,
                    max_value=90.0,
                    value=35.4498,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_start_pin_lat"
                )
                
                pin_lng = st.number_input(
                    "ピン側経度",
                    min_value=-180.0,
                    max_value=180.0,
                    value=139.6649,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_start_pin_lng"
                )
            
            with col2:
                committee_lat = st.number_input(
                    "コミッティ側緯度",
                    min_value=-90.0,
                    max_value=90.0,
                    value=35.4508,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_start_committee_lat"
                )
                
                committee_lng = st.number_input(
                    "コミッティ側経度",
                    min_value=-180.0,
                    max_value=180.0,
                    value=139.6659,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_start_committee_lng"
                )
            
            start_name = st.text_input(
                "スタートライン名",
                value="スタート",
                key=f"{key_prefix}_{layer.layer_id}_new_start_name"
            )
            
            if st.button("スタートラインを追加", key=f"{key_prefix}_{layer.layer_id}_add_start"):
                layer.add_start_line(pin_lat, pin_lng, committee_lat, committee_lng, name=start_name)
                changes["start_added"] = {
                    "type": "start",
                    "pin_lat": pin_lat,
                    "pin_lng": pin_lng,
                    "committee_lat": committee_lat,
                    "committee_lng": committee_lng,
                    "name": start_name
                }
                st.rerun()
        
        elif mark_type == "finish":
            # フィニッシュライン
            st.markdown("ピン側とコミッティ側の位置を指定してください")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pin_lat = st.number_input(
                    "ピン側緯度",
                    min_value=-90.0,
                    max_value=90.0,
                    value=35.4498,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_finish_pin_lat"
                )
                
                pin_lng = st.number_input(
                    "ピン側経度",
                    min_value=-180.0,
                    max_value=180.0,
                    value=139.6649,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_finish_pin_lng"
                )
            
            with col2:
                committee_lat = st.number_input(
                    "コミッティ側緯度",
                    min_value=-90.0,
                    max_value=90.0,
                    value=35.4508,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_finish_committee_lat"
                )
                
                committee_lng = st.number_input(
                    "コミッティ側経度",
                    min_value=-180.0,
                    max_value=180.0,
                    value=139.6659,
                    format="%.6f",
                    key=f"{key_prefix}_{layer.layer_id}_new_finish_committee_lng"
                )
            
            finish_name = st.text_input(
                "フィニッシュライン名",
                value="フィニッシュ",
                key=f"{key_prefix}_{layer.layer_id}_new_finish_name"
            )
            
            if st.button("フィニッシュラインを追加", key=f"{key_prefix}_{layer.layer_id}_add_finish"):
                layer.add_finish_line(pin_lat, pin_lng, committee_lat, committee_lng, name=finish_name)
                changes["finish_added"] = {
                    "type": "finish",
                    "pin_lat": pin_lat,
                    "pin_lng": pin_lng,
                    "committee_lat": committee_lat,
                    "committee_lng": committee_lng,
                    "name": finish_name
                }
                st.rerun()
    
    # 制限エリア管理
    with st.expander("制限エリア管理", expanded=False):
        restricted_areas = layer.get_property("restricted_areas", [])
        
        if restricted_areas:
            st.markdown("#### 既存の制限エリア")
            
            # 制限エリアのリスト表示
            for i, area in enumerate(restricted_areas):
                st.markdown(f"**{i+1}. {area.get('name', '制限エリア')}**")
                st.write(f"座標数: {len(area.get('coordinates', []))}")
            
            # 制限エリア削除
            if st.button("すべての制限エリアを削除", key=f"{key_prefix}_{layer.layer_id}_clear_restricted"):
                if st.session_state.get(f"{key_prefix}_{layer.layer_id}_confirm_clear_restricted", False):
                    layer.clear_restricted_areas()
                    changes["restricted_cleared"] = True
                    st.session_state[f"{key_prefix}_{layer.layer_id}_confirm_clear_restricted"] = False
                    st.rerun()
                else:
                    st.session_state[f"{key_prefix}_{layer.layer_id}_confirm_clear_restricted"] = True
                    st.warning("すべての制限エリアを削除します。もう一度ボタンをクリックして確認してください。")
        else:
            st.info("制限エリアがありません。制限エリアを追加してください。")
        
        # 制限エリア表示設定
        show_restricted = st.checkbox(
            "制限エリアを表示",
            value=layer.get_property("show_restricted", False),
            key=f"{key_prefix}_{layer.layer_id}_show_restricted"
        )
        
        if show_restricted != layer.get_property("show_restricted", False):
            layer.set_property("show_restricted", show_restricted)
            changes["show_restricted"] = show_restricted
        
        restricted_color = st.color_picker(
            "制限エリア色",
            value=layer.get_property("restricted_color", "#FF0000"),
            key=f"{key_prefix}_{layer.layer_id}_restricted_color"
        )
        
        if restricted_color != layer.get_property("restricted_color", "#FF0000"):
            layer.set_property("restricted_color", restricted_color)
            changes["restricted_color"] = restricted_color
        
        # 制限エリア追加
        st.markdown("#### 制限エリアの追加")
        
        area_name = st.text_input(
            "エリア名",
            value="制限エリア",
            key=f"{key_prefix}_{layer.layer_id}_new_area_name"
        )
        
        # 座標入力
        st.markdown("座標の入力（CSV形式: 緯度,経度 - 1行に1座標）")
        
        area_coords = st.text_area(
            "座標リスト",
            value="35.4498,139.6649\n35.4508,139.6659\n35.4508,139.6649",
            height=100,
            key=f"{key_prefix}_{layer.layer_id}_new_area_coords"
        )
        
        if st.button("制限エリアを追加", key=f"{key_prefix}_{layer.layer_id}_add_area"):
            # 座標の解析
            try:
                coords = []
                for line in area_coords.strip().split("\n"):
                    parts = line.strip().split(",")
                    if len(parts) == 2:
                        lat = float(parts[0])
                        lng = float(parts[1])
                        coords.append((lat, lng))
                
                if len(coords) >= 3:
                    layer.add_restricted_area(coords, name=area_name)
                    changes["area_added"] = {
                        "name": area_name,
                        "coords": coords
                    }
                    st.rerun()
                else:
                    st.error("制限エリアには少なくとも3つの座標が必要です。")
            except ValueError:
                st.error("座標の形式が正しくありません。緯度,経度の形式で入力してください。")
    
    # コールバックを呼び出し
    if changes and on_change:
        on_change("course_elements_properties_changed")
    
    return changes


def heat_map_layer_property_panel(layer: HeatMapLayer, 
                                 on_change: Optional[Callable[[str], None]] = None,
                                 key_prefix: str = "") -> Dict[str, Any]:
    """
    ヒートマップレイヤープロパティパネルを表示

    Parameters
    ----------
    layer : HeatMapLayer
        ヒートマップレイヤー
    on_change : Optional[Callable[[str], None]], optional
        変更時のコールバック, by default None
    key_prefix : str, optional
        キー接頭辞, by default ""

    Returns
    -------
    Dict[str, Any]
        変更されたプロパティ情報
    """
    changes = {}
    
    # 基本設定
    base_changes = base_layer_property_panel(layer, None, key_prefix)
    changes.update(base_changes)
    
    # ヒートマップ設定
    with st.expander("ヒートマップ設定", expanded=True):
        # メトリック設定
        metric = st.selectbox(
            "メトリック",
            options=["speed", "wind_speed", "heading", "density", "custom"],
            format_func=lambda x: {
                "speed": "速度",
                "wind_speed": "風速",
                "heading": "方向",
                "density": "密度",
                "custom": "カスタム"
            }.get(x, x),
            index=["speed", "wind_speed", "heading", "density", "custom"].index(
                layer.get_property("metric", "speed")
            ),
            key=f"{key_prefix}_{layer.layer_id}_metric"
        )
        
        if metric != layer.get_property("metric", "speed"):
            layer.set_property("metric", metric)
            changes["metric"] = metric
        
        # カスタムフィールド（カスタムメトリックの場合）
        if metric == "custom":
            custom_field = st.text_input(
                "カスタムフィールド名",
                value=layer.get_property("custom_field", ""),
                key=f"{key_prefix}_{layer.layer_id}_custom_field"
            )
            
            if custom_field != layer.get_property("custom_field", ""):
                layer.set_property("custom_field", custom_field)
                changes["custom_field"] = custom_field
        
        # 半径とぼかし
        col1, col2 = st.columns(2)
        
        with col1:
            radius = st.slider(
                "ポイント半径",
                min_value=5,
                max_value=50,
                value=layer.get_property("radius", 15),
                step=1,
                key=f"{key_prefix}_{layer.layer_id}_radius"
            )
            
            if radius != layer.get_property("radius", 15):
                layer.set_radius_and_blur(radius=radius)
                changes["radius"] = radius
        
        with col2:
            blur = st.slider(
                "ぼかし",
                min_value=0,
                max_value=50,
                value=layer.get_property("blur", 15),
                step=1,
                key=f"{key_prefix}_{layer.layer_id}_blur"
            )
            
            if blur != layer.get_property("blur", 15):
                layer.set_radius_and_blur(blur=blur)
                changes["blur"] = blur
        
        # 強度
        intensity = st.slider(
            "強度",
            min_value=0.1,
            max_value=3.0,
            value=layer.get_property("intensity", 1.0),
            step=0.1,
            format="%.1f",
            key=f"{key_prefix}_{layer.layer_id}_intensity"
        )
        
        if intensity != layer.get_property("intensity", 1.0):
            layer.set_property("intensity", intensity)
            changes["intensity"] = intensity
    
    # カラースケール設定
    with st.expander("カラースケール設定", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            color_scale = st.selectbox(
                "カラースケール",
                options=["default", "viridis", "plasma", "inferno", "magma", "blues", "greens", "reds", "spectral"],
                format_func=lambda x: {
                    "default": "デフォルト（青→赤）",
                    "viridis": "Viridis",
                    "plasma": "Plasma",
                    "inferno": "Inferno",
                    "magma": "Magma",
                    "blues": "Blues",
                    "greens": "Greens",
                    "reds": "Reds",
                    "spectral": "Spectral"
                }.get(x, x),
                index=["default", "viridis", "plasma", "inferno", "magma", "blues", "greens", "reds", "spectral"].index(
                    layer.get_property("color_scale", "default")
                ),
                key=f"{key_prefix}_{layer.layer_id}_color_scale"
            )
            
            if color_scale != layer.get_property("color_scale", "default"):
                invert_scale = layer.get_property("invert_scale", False)
                layer.set_color_scale(color_scale, invert=invert_scale)
                changes["color_scale"] = color_scale
        
        with col2:
            invert_scale = st.checkbox(
                "スケールを反転",
                value=layer.get_property("invert_scale", False),
                key=f"{key_prefix}_{layer.layer_id}_invert_scale"
            )
            
            if invert_scale != layer.get_property("invert_scale", False):
                layer.set_property("invert_scale", invert_scale)
                changes["invert_scale"] = invert_scale
        
        # カスタムグラデーション（将来実装）
        if color_scale == "custom":
            st.info("カスタムグラデーションは現在APIのみで設定可能です。")
        
        # 凡例表示
        show_legend = st.checkbox(
            "凡例を表示",
            value=layer.get_property("show_legend", True),
            key=f"{key_prefix}_{layer.layer_id}_show_legend"
        )
        
        if show_legend != layer.get_property("show_legend", True):
            layer.set_property("show_legend", show_legend)
            changes["show_legend"] = show_legend
    
    # 値範囲設定
    with st.expander("値範囲設定", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            min_value = layer.get_property("min_value", None)
            min_value_str = "" if min_value is None else str(min_value)
            
            new_min_value = st.text_input(
                "最小値",
                value=min_value_str,
                key=f"{key_prefix}_{layer.layer_id}_min_value"
            )
            
            try:
                if new_min_value:
                    new_min_value = float(new_min_value)
                    if min_value != new_min_value:
                        layer.set_value_range(min_value=new_min_value)
                        changes["min_value"] = new_min_value
                else:
                    if min_value is not None:
                        layer.set_value_range(min_value=None)
                        changes["min_value"] = None
            except ValueError:
                st.warning("最小値には数値を入力してください。")
        
        with col2:
            max_value = layer.get_property("max_value", None)
            max_value_str = "" if max_value is None else str(max_value)
            
            new_max_value = st.text_input(
                "最大値",
                value=max_value_str,
                key=f"{key_prefix}_{layer.layer_id}_max_value"
            )
            
            try:
                if new_max_value:
                    new_max_value = float(new_max_value)
                    if max_value != new_max_value:
                        layer.set_value_range(max_value=new_max_value)
                        changes["max_value"] = new_max_value
                else:
                    if max_value is not None:
                        layer.set_value_range(max_value=None)
                        changes["max_value"] = None
            except ValueError:
                st.warning("最大値には数値を入力してください。")
    
    # データ処理設定
    with st.expander("データ処理設定", expanded=False):
        # 集約方法
        aggregation = st.selectbox(
            "集約方法",
            options=["max", "min", "avg"],
            format_func=lambda x: {
                "max": "最大値",
                "min": "最小値",
                "avg": "平均値"
            }.get(x, x),
            index=["max", "min", "avg"].index(
                layer.get_property("aggregation", "max")
            ),
            key=f"{key_prefix}_{layer.layer_id}_aggregation"
        )
        
        if aggregation != layer.get_property("aggregation", "max"):
            layer.set_aggregation(aggregation)
            changes["aggregation"] = aggregation
        
        # 離散化
        discretize = st.checkbox(
            "値を離散化",
            value=layer.get_property("discretize", False),
            key=f"{key_prefix}_{layer.layer_id}_discretize"
        )
        
        if discretize != layer.get_property("discretize", False):
            layer.set_property("discretize", discretize)
            changes["discretize"] = discretize
        
        if discretize:
            num_bins = st.slider(
                "ビン数",
                min_value=2,
                max_value=20,
                value=layer.get_property("num_bins", 10),
                step=1,
                key=f"{key_prefix}_{layer.layer_id}_num_bins"
            )
            
            if num_bins != layer.get_property("num_bins", 10):
                layer.set_discretize(True, num_bins=num_bins)
                changes["num_bins"] = num_bins
        
        # 平滑化
        smoothing = st.slider(
            "平滑化レベル",
            min_value=0,
            max_value=10,
            value=layer.get_property("smoothing", 0),
            step=1,
            key=f"{key_prefix}_{layer.layer_id}_smoothing"
        )
        
        if smoothing != layer.get_property("smoothing", 0):
            layer.set_property("smoothing", smoothing)
            changes["smoothing"] = smoothing
    
    # コールバックを呼び出し
    if changes and on_change:
        on_change("heat_map_properties_changed")
    
    return changes
