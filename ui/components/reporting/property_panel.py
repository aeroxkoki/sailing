"""
ui.components.reporting.property_panel

プロパティパネルコンポーネントを提供するモジュールです。
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable, Union
import json

from sailing_data_processor.reporting.templates.template_model import (
    ElementType, ElementModel, SectionType, Section, Element
)


def render_property_panel(
    selected_item: Optional[Union[Element, Section]] = None,
    on_property_change: Optional[Callable[[Dict[str, Any]], None]] = None
) -> None:
    """
    プロパティパネルを描画
    
    Parameters
    ----------
    selected_item : Optional[Union[Element, Section]], optional
        選択されたアイテム（要素またはセクション）, by default None
    on_property_change : Optional[Callable[[Dict[str, Any]], None]], optional
        プロパティ変更時のコールバック関数, by default None
    """
    st.sidebar.header("プロパティ")
    
    if selected_item is None:
        st.sidebar.info("要素を選択してプロパティを編集してください。")
        return
    
    # セクションの場合
    if isinstance(selected_item, Section):
        _render_section_properties(selected_item, on_property_change)
    # 要素の場合
    elif isinstance(selected_item, Element):
        _render_element_properties(selected_item, on_property_change)
    else:
        st.sidebar.error("サポートされていない項目タイプです。")


def _render_section_properties(
    section: Section,
    on_property_change: Optional[Callable[[Dict[str, Any]], None]] = None
) -> None:
    """
    セクションのプロパティを描画
    
    Parameters
    ----------
    section : Section
        プロパティを編集するセクション
    on_property_change : Optional[Callable[[Dict[str, Any]], None]], optional
        プロパティ変更時のコールバック関数, by default None
    """
    st.sidebar.subheader("セクション情報")
    
    # セクション基本情報
    with st.sidebar.expander("基本情報", expanded=True):
        # 名前
        name = st.text_input("名前", section.name, key="section_name")
        
        # タイトル
        title = st.text_input("タイトル", section.title, key="section_title")
        
        # 説明
        description = st.text_area("説明", section.description, key="section_description")
        
        # タイプ
        section_type_options = {t.value: t.name for t in SectionType}
        section_type = st.selectbox(
            "タイプ",
            options=list(section_type_options.keys()),
            index=list(section_type_options.keys()).index(section.section_type.value),
            format_func=lambda x: section_type_options[x],
            key="section_type"
        )
        
        # 順序
        order = st.number_input("順序", min_value=0, value=section.order, key="section_order")
    
    # レイアウト設定
    with st.sidebar.expander("レイアウト設定", expanded=False):
        # カラム数
        columns = st.number_input(
            "カラム数",
            min_value=1,
            max_value=12,
            value=section.layout.get("columns", 1),
            key="section_columns"
        )
        
        # マージン
        margin_top = st.number_input(
            "上マージン (px)",
            min_value=0,
            value=section.layout.get("margin", {}).get("top", 20),
            key="section_margin_top"
        )
        
        margin_right = st.number_input(
            "右マージン (px)",
            min_value=0,
            value=section.layout.get("margin", {}).get("right", 20),
            key="section_margin_right"
        )
        
        margin_bottom = st.number_input(
            "下マージン (px)",
            min_value=0,
            value=section.layout.get("margin", {}).get("bottom", 20),
            key="section_margin_bottom"
        )
        
        margin_left = st.number_input(
            "左マージン (px)",
            min_value=0,
            value=section.layout.get("margin", {}).get("left", 20),
            key="section_margin_left"
        )
    
    # スタイル設定
    with st.sidebar.expander("スタイル設定", expanded=False):
        # 背景色
        background_color = st.color_picker(
            "背景色",
            section.styles.get("background-color", "#FFFFFF"),
            key="section_background_color"
        )
        
        # テキスト色
        text_color = st.color_picker(
            "テキスト色",
            section.styles.get("color", "#333333"),
            key="section_text_color"
        )
        
        # パディング
        padding = st.number_input(
            "パディング (px)",
            min_value=0,
            value=_extract_px_value(section.styles.get("padding", "20px")),
            key="section_padding"
        )
        
        # ボーダー半径
        border_radius = st.number_input(
            "ボーダー半径 (px)",
            min_value=0,
            value=_extract_px_value(section.styles.get("border-radius", "5px")),
            key="section_border_radius"
        )
    
    # 変更の適用ボタン
    if st.sidebar.button("変更を適用", key="apply_section_changes"):
        # 変更の適用
        changes = {
            "name": name,
            "title": title,
            "description": description,
            "section_type": section_type,
            "order": order,
            "layout": {
                "columns": columns,
                "margin": {
                    "top": margin_top,
                    "right": margin_right,
                    "bottom": margin_bottom,
                    "left": margin_left
                }
            },
            "styles": {
                "background-color": background_color,
                "color": text_color,
                "padding": f"{padding}px",
                "border-radius": f"{border_radius}px"
            }
        }
        
        # コールバック関数を呼び出し
        if on_property_change:
            on_property_change(changes)


def _render_element_properties(
    element: Element,
    on_property_change: Optional[Callable[[Dict[str, Any]], None]] = None
) -> None:
    """
    要素のプロパティを描画
    
    Parameters
    ----------
    element : Element
        プロパティを編集する要素
    on_property_change : Optional[Callable[[Dict[str, Any]], None]], optional
        プロパティ変更時のコールバック関数, by default None
    """
    st.sidebar.subheader("要素情報")
    
    # 要素基本情報
    with st.sidebar.expander("基本情報", expanded=True):
        # 名前
        name = st.text_input("名前", element.name, key="element_name")
        
        # タイプ（表示のみ）
        element_type = element.element_type.value if element.element_type else ""
        st.text_input("タイプ", element_type, disabled=True, key="element_type")
    
    # 要素固有プロパティ
    with st.sidebar.expander("プロパティ", expanded=True):
        # 要素タイプに応じて異なるプロパティを表示
        properties = element.properties.copy()
        updated_properties = _render_element_type_properties(element.element_type, properties)
    
    # スタイル設定
    with st.sidebar.expander("スタイル設定", expanded=False):
        # 幅
        width = st.text_input(
            "幅",
            element.styles.get("width", "100%"),
            key="element_width"
        )
        
        # 高さ
        height = st.text_input(
            "高さ",
            element.styles.get("height", "auto"),
            key="element_height"
        )
        
        # マージン
        margin = st.text_input(
            "マージン",
            element.styles.get("margin", "0"),
            key="element_margin"
        )
        
        # パディング
        padding = st.text_input(
            "パディング",
            element.styles.get("padding", "0"),
            key="element_padding"
        )
        
        # 背景色
        background_color = st.color_picker(
            "背景色",
            element.styles.get("background-color", "#FFFFFF"),
            key="element_background_color"
        )
        
        # テキスト色
        text_color = st.color_picker(
            "テキスト色",
            element.styles.get("color", "#333333"),
            key="element_text_color"
        )
        
        # ボーダー
        border = st.text_input(
            "ボーダー",
            element.styles.get("border", "none"),
            key="element_border"
        )
        
        # ボーダー半径
        border_radius = st.text_input(
            "ボーダー半径",
            element.styles.get("border-radius", "0"),
            key="element_border_radius"
        )
    
    # 条件設定
    with st.sidebar.expander("条件設定", expanded=False):
        st.info("条件設定機能は現在開発中です。")
    
    # 変更の適用ボタン
    if st.sidebar.button("変更を適用", key="apply_element_changes"):
        # 変更の適用
        changes = {
            "name": name,
            "properties": updated_properties,
            "styles": {
                "width": width,
                "height": height,
                "margin": margin,
                "padding": padding,
                "background-color": background_color,
                "color": text_color,
                "border": border,
                "border-radius": border_radius
            }
        }
        
        # コールバック関数を呼び出し
        if on_property_change:
            on_property_change(changes)


def _render_element_type_properties(
    element_type: ElementType,
    properties: Dict[str, Any]
) -> Dict[str, Any]:
    """
    要素タイプに応じたプロパティ編集UIを描画
    
    Parameters
    ----------
    element_type : ElementType
        要素タイプ
    properties : Dict[str, Any]
        現在のプロパティ
    
    Returns
    -------
    Dict[str, Any]
        更新されたプロパティ
    """
    updated_properties = properties.copy()
    
    # 要素タイプに応じて異なるプロパティを表示
    if element_type == ElementType.TEXT:
        # テキスト要素
        content = st.text_area("コンテンツ", properties.get("content", ""), key="text_content")
        content_type = st.selectbox(
            "コンテンツタイプ",
            options=["static", "dynamic", "html"],
            index=["static", "dynamic", "html"].index(properties.get("content_type", "static")),
            key="text_content_type"
        )
        updated_properties.update({
            "content": content,
            "content_type": content_type
        })
    
    elif element_type == ElementType.TABLE:
        # テーブル要素
        data_source = st.text_input("データソース", properties.get("data_source", ""), key="table_data_source")
        
        # カラム設定（JSONエディタ）
        columns_json = json.dumps(properties.get("columns", []), ensure_ascii=False, indent=2)
        columns_str = st.text_area(
            "カラム設定（JSON）",
            columns_json,
            height=150,
            key="table_columns"
        )
        
        try:
            columns = json.loads(columns_str)
        except json.JSONDecodeError:
            st.error("JSONの形式が正しくありません。")
            columns = properties.get("columns", [])
        
        updated_properties.update({
            "data_source": data_source,
            "columns": columns
        })
    
    elif element_type == ElementType.LIST:
        # リスト要素
        data_source = st.text_input("データソース", properties.get("data_source", ""), key="list_data_source")
        list_type = st.selectbox(
            "リストタイプ",
            options=["ordered", "unordered"],
            index=["ordered", "unordered"].index(properties.get("list_type", "unordered")),
            key="list_type"
        )
        item_template = st.text_input("アイテムテンプレート", properties.get("item_template", "{{item}}"), key="list_item_template")
        
        updated_properties.update({
            "data_source": data_source,
            "list_type": list_type,
            "item_template": item_template
        })
    
    elif element_type == ElementType.CHART:
        # チャート要素
        data_source = st.text_input("データソース", properties.get("data_source", ""), key="chart_data_source")
        chart_type = st.selectbox(
            "チャートタイプ",
            options=["line", "bar", "pie", "scatter", "radar", "heatmap"],
            index=["line", "bar", "pie", "scatter", "radar", "heatmap"].index(properties.get("chart_type", "line")),
            key="chart_type"
        )
        title = st.text_input("タイトル", properties.get("title", ""), key="chart_title")
        x_axis = st.text_input("X軸フィールド", properties.get("x_axis", ""), key="chart_x_axis")
        
        # シリーズ設定（JSONエディタ）
        series_json = json.dumps(properties.get("series", []), ensure_ascii=False, indent=2)
        series_str = st.text_area(
            "シリーズ設定（JSON）",
            series_json,
            height=150,
            key="chart_series"
        )
        
        try:
            series = json.loads(series_str)
        except json.JSONDecodeError:
            st.error("JSONの形式が正しくありません。")
            series = properties.get("series", [])
        
        updated_properties.update({
            "data_source": data_source,
            "chart_type": chart_type,
            "title": title,
            "x_axis": x_axis,
            "series": series
        })
    
    elif element_type == ElementType.MAP:
        # マップ要素
        data_source = st.text_input("データソース", properties.get("data_source", ""), key="map_data_source")
        map_type = st.selectbox(
            "マップタイプ",
            options=["track", "heatmap", "points"],
            index=["track", "heatmap", "points"].index(properties.get("map_type", "track")),
            key="map_type"
        )
        track_color = st.color_picker("トラック色", properties.get("track_color", "#FF5722"), key="map_track_color")
        center_auto = st.checkbox("自動センタリング", properties.get("center_auto", True), key="map_center_auto")
        zoom_level = st.slider("ズームレベル", 1, 20, properties.get("zoom_level", 13), key="map_zoom_level")
        show_wind = st.checkbox("風を表示", properties.get("show_wind", False), key="map_show_wind")
        show_strategy_points = st.checkbox("戦略ポイントを表示", properties.get("show_strategy_points", False), key="map_show_strategy_points")
        
        updated_properties.update({
            "data_source": data_source,
            "map_type": map_type,
            "track_color": track_color,
            "center_auto": center_auto,
            "zoom_level": zoom_level,
            "show_wind": show_wind,
            "show_strategy_points": show_strategy_points
        })
    
    elif element_type == ElementType.IMAGE:
        # 画像要素
        src = st.text_input("画像ソース", properties.get("src", ""), key="image_src")
        alt = st.text_input("代替テキスト", properties.get("alt", ""), key="image_alt")
        
        updated_properties.update({
            "src": src,
            "alt": alt
        })
    
    # その他の要素タイプに対する処理は省略
    # 実際のアプリケーションでは、すべての要素タイプに対する処理を実装する
    
    return updated_properties


def _extract_px_value(px_string: str) -> int:
    """
    'px'単位の文字列から数値を抽出
    
    Parameters
    ----------
    px_string : str
        'px'単位の文字列（例: '20px'）
    
    Returns
    -------
    int
        抽出された数値
    """
    if not px_string:
        return 0
    
    try:
        # 'px'を削除して数値に変換
        return int(px_string.replace('px', ''))
    except (ValueError, TypeError):
        return 0
