"""
ui.components.reporting.template_editor

テンプレートエディタのUIコンポーネントを提供するモジュールです。
テンプレートの作成、編集、プレビューのためのStreamlitコンポーネントを実装します。
"""

import streamlit as st
import pandas as pd
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Callable

from sailing_data_processor.reporting.templates.template_model import (
    Template, Section, Element, ElementType, SectionType, TemplateOutputFormat
)
from sailing_data_processor.reporting.templates.template_manager import TemplateManager
from sailing_data_processor.reporting.elements.element_factory import create_element
from sailing_data_processor.reporting.renderer.html_renderer import HTMLRenderer


class TemplateEditor:
    """
    テンプレートエディタコンポーネント
    
    テンプレートの編集、プレビュー、保存などの機能を提供するStreamlitコンポーネントです。
    """
    
    def __init__(self, template_manager: Optional[TemplateManager] = None):
        """
        初期化
        
        Parameters
        ----------
        template_manager : Optional[TemplateManager], optional
            テンプレートマネージャー, by default None
            Noneの場合は新しいインスタンスを作成
        """
        # テンプレートマネージャーの初期化
        self.template_manager = template_manager or TemplateManager()
        
        # セッション状態の初期化
        if 'current_template' not in st.session_state:
            st.session_state.current_template = None
        
        if 'template_modified' not in st.session_state:
            st.session_state.template_modified = False
        
        if 'current_section_index' not in st.session_state:
            st.session_state.current_section_index = 0
        
        if 'current_element_id' not in st.session_state:
            st.session_state.current_element_id = None
        
        if 'preview_data' not in st.session_state:
            st.session_state.preview_data = {}
    
    def render(self) -> None:
        """
        テンプレートエディタを描画
        """
        # タブの作成
        tabs = st.tabs(["テンプレート選択", "テンプレート編集", "プレビュー"])
        
        # テンプレート選択タブ
        with tabs[0]:
            self._render_template_selection()
        
        # テンプレート編集タブ
        with tabs[1]:
            self._render_template_editor()
        
        # プレビュータブ
        with tabs[2]:
            self._render_template_preview()
    
    def _render_template_selection(self) -> None:
        """
        テンプレート選択画面を描画
        """
        st.header("テンプレートの選択")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # テンプレートリストの取得
            template_list = []
            for fmt in [f.value for f in TemplateOutputFormat]:
                templates = self.template_manager.list_templates(fmt)
                for template_info in templates.get(fmt, []):
                    template_list.append({
                        "id": template_info.get("template_id"),
                        "name": template_info.get("name"),
                        "format": fmt,
                        "description": template_info.get("description", ""),
                        "updated_at": template_info.get("updated_at", "")
                    })
            
            # テンプレートリストを表示
            if template_list:
                df = pd.DataFrame(template_list)
                st.dataframe(df, hide_index=True)
                
                # テンプレート選択
                selected_template_id = st.selectbox(
                    "編集するテンプレートを選択",
                    options=[t["id"] for t in template_list],
                    format_func=lambda x: next((t["name"] for t in template_list if t["id"] == x), ""),
                    index=None
                )
                
                if selected_template_id:
                    if st.button("テンプレートを読み込む"):
                        template = self.template_manager.get_template(selected_template_id)
                        if template:
                            st.session_state.current_template = template
                            st.session_state.template_modified = False
                            st.session_state.current_section_index = 0
                            st.session_state.current_element_id = None
                            st.success(f"テンプレート '{template.name}' を読み込みました")
                            st.rerun()
            else:
                st.info("テンプレートがありません。新しいテンプレートを作成するか、標準テンプレートを生成してください。")
        
        with col2:
            st.subheader("テンプレート操作")
            
            # 新規テンプレート作成
            if st.button("新規テンプレート作成"):
                self._create_new_template()
                st.success("新しいテンプレートを作成しました")
                st.rerun()
            
            # 標準テンプレート生成
            if st.button("標準テンプレートを生成"):
                self._create_standard_templates()
                st.success("標準テンプレートを生成しました")
                st.rerun()
            
            # テンプレートインポート
            uploaded_file = st.file_uploader("テンプレートファイルをインポート", type=["json"])
            if uploaded_file is not None:
                try:
                    # アップロードされたJSONをロード
                    template_data = json.loads(uploaded_file.getvalue().decode())
                    
                    # テンプレートを作成
                    template = Template.from_dict(template_data)
                    
                    # テンプレートを保存
                    self.template_manager.save_template(template)
                    
                    st.success(f"テンプレート '{template.name}' をインポートしました")
                    st.rerun()
                except Exception as e:
                    st.error(f"テンプレートのインポートに失敗しました: {str(e)}")
    
    def _render_template_editor(self) -> None:
        """
        テンプレート編集画面を描画
        """
        st.header("テンプレートの編集")
        
        # 現在のテンプレートがない場合
        if st.session_state.current_template is None:
            st.info("編集するテンプレートを選択してください")
            return
        
        template = st.session_state.current_template
        
        # テンプレート情報の表示と編集
        with st.expander("テンプレート基本情報", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # テンプレート名の編集
                new_name = st.text_input("テンプレート名", value=template.name)
                if new_name != template.name:
                    template.name = new_name
                    st.session_state.template_modified = True
                
                # 出力形式の選択
                current_format = template.output_format.value
                format_options = [f.value for f in TemplateOutputFormat]
                new_format = st.selectbox("出力形式", options=format_options, index=format_options.index(current_format))
                if new_format != current_format:
                    template.output_format = TemplateOutputFormat(new_format)
                    st.session_state.template_modified = True
                
                # カテゴリの編集
                new_category = st.text_input("カテゴリ", value=template.category)
                if new_category != template.category:
                    template.category = new_category
                    st.session_state.template_modified = True
            
            with col2:
                # 説明の編集
                new_description = st.text_area("説明", value=template.description, height=100)
                if new_description != template.description:
                    template.description = new_description
                    st.session_state.template_modified = True
                
                # タグの編集
                tags_str = ", ".join(template.tags)
                new_tags_str = st.text_input("タグ（カンマ区切り）", value=tags_str)
                new_tags = [tag.strip() for tag in new_tags_str.split(",") if tag.strip()]
                if new_tags != template.tags:
                    template.tags = new_tags
                    st.session_state.template_modified = True
        
        # グローバルスタイル設定
        with st.expander("グローバルスタイル設定"):
            col1, col2 = st.columns(2)
            
            with col1:
                # フォントファミリー
                new_font_family = st.text_input(
                    "フォントファミリー", 
                    value=template.global_styles.get("font_family", "Arial, sans-serif")
                )
                if new_font_family != template.global_styles.get("font_family"):
                    template.global_styles["font_family"] = new_font_family
                    st.session_state.template_modified = True
                
                # 基本フォントサイズ
                new_font_size = st.number_input(
                    "基本フォントサイズ", 
                    min_value=8, 
                    max_value=24, 
                    value=template.global_styles.get("base_font_size", 14)
                )
                if new_font_size != template.global_styles.get("base_font_size"):
                    template.global_styles["base_font_size"] = new_font_size
                    st.session_state.template_modified = True
            
            with col2:
                # 色設定
                new_color_primary = st.color_picker(
                    "プライマリカラー", 
                    value=template.global_styles.get("color_primary", "#3498db")
                )
                if new_color_primary != template.global_styles.get("color_primary"):
                    template.global_styles["color_primary"] = new_color_primary
                    st.session_state.template_modified = True
                
                new_color_secondary = st.color_picker(
                    "セカンダリカラー", 
                    value=template.global_styles.get("color_secondary", "#2c3e50")
                )
                if new_color_secondary != template.global_styles.get("color_secondary"):
                    template.global_styles["color_secondary"] = new_color_secondary
                    st.session_state.template_modified = True
                
                new_color_accent = st.color_picker(
                    "アクセントカラー", 
                    value=template.global_styles.get("color_accent", "#e74c3c")
                )
                if new_color_accent != template.global_styles.get("color_accent"):
                    template.global_styles["color_accent"] = new_color_accent
                    st.session_state.template_modified = True
        
        # セクション一覧と編集
        st.subheader("セクション編集")
        
        # セクション選択
        section_names = [f"{i+1}. {s.title or s.name} ({s.section_type.value})" for i, s in enumerate(template.sections)]
        if not section_names:
            section_names = ["セクションがありません"]
        
        current_section_index = st.session_state.current_section_index
        if current_section_index >= len(template.sections):
            current_section_index = 0 if template.sections else -1
            st.session_state.current_section_index = current_section_index
        
        selected_section_index = st.selectbox(
            "編集するセクション",
            options=list(range(len(section_names))),
            format_func=lambda i: section_names[i],
            index=current_section_index if current_section_index >= 0 else 0
        )
        
        if selected_section_index != current_section_index:
            st.session_state.current_section_index = selected_section_index
            st.session_state.current_element_id = None
            st.rerun()
        
        # セクション操作ボタン
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("新規セクション追加"):
                self._add_new_section()
                st.session_state.template_modified = True
                st.rerun()
        
        # セクションがある場合のみ表示
        if template.sections:
            with col2:
                if st.button("セクションを複製"):
                    self._duplicate_section(selected_section_index)
                    st.session_state.template_modified = True
                    st.rerun()
            
            with col3:
                if st.button("セクションを削除"):
                    self._delete_section(selected_section_index)
                    st.session_state.template_modified = True
                    st.rerun()
            
            with col4:
                if st.button("セクションを並べ替え"):
                    template.sort_sections()
                    st.session_state.template_modified = True
                    st.rerun()
        
        # 選択されたセクションの編集
        if template.sections and 0 <= selected_section_index < len(template.sections):
            section = template.sections[selected_section_index]
            
            with st.expander("セクション設定", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    # セクション名
                    new_section_name = st.text_input("セクション内部名", value=section.name)
                    if new_section_name != section.name:
                        section.name = new_section_name
                        st.session_state.template_modified = True
                    
                    # セクションタイプ
                    section_types = [t.value for t in SectionType]
                    current_type = section.section_type.value
                    new_section_type = st.selectbox(
                        "セクションタイプ",
                        options=section_types,
                        index=section_types.index(current_type)
                    )
                    if new_section_type != current_type:
                        section.section_type = SectionType(new_section_type)
                        st.session_state.template_modified = True
                    
                    # セクション順序
                    new_order = st.number_input("表示順序", min_value=0, value=section.order)
                    if new_order != section.order:
                        section.order = new_order
                        st.session_state.template_modified = True
                
                with col2:
                    # セクションタイトル
                    new_title = st.text_input("セクションタイトル", value=section.title)
                    if new_title != section.title:
                        section.title = new_title
                        st.session_state.template_modified = True
                    
                    # セクション説明
                    new_description = st.text_area("セクション説明", value=section.description, height=100)
                    if new_description != section.description:
                        section.description = new_description
                        st.session_state.template_modified = True
            
            # セクション内の要素一覧と編集
            st.subheader("要素編集")
            
            # 要素一覧
            if section.elements:
                element_names = [f"{i+1}. {e.name} ({e.element_type.value})" for i, e in enumerate(section.elements)]
                
                # 要素の選択
                selected_element_index = None
                
                if st.session_state.current_element_id:
                    # 現在の要素IDから選択インデックスを取得
                    for i, element in enumerate(section.elements):
                        if element.element_id == st.session_state.current_element_id:
                            selected_element_index = i
                            break
                
                selected_element_index = st.selectbox(
                    "編集する要素",
                    options=list(range(len(element_names))),
                    format_func=lambda i: element_names[i],
                    index=selected_element_index if selected_element_index is not None else 0
                )
                
                st.session_state.current_element_id = section.elements[selected_element_index].element_id
                
                # 要素操作ボタン
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("要素を追加"):
                        self._add_new_element(section)
                        st.session_state.template_modified = True
                        st.rerun()
                
                with col2:
                    if st.button("要素を複製"):
                        self._duplicate_element(section, selected_element_index)
                        st.session_state.template_modified = True
                        st.rerun()
                
                with col3:
                    if st.button("要素を削除"):
                        self._delete_element(section, selected_element_index)
                        st.session_state.template_modified = True
                        st.rerun()
                
                # 選択された要素の編集
                element = section.elements[selected_element_index]
                
                with st.expander("要素設定", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # 要素名
                        new_element_name = st.text_input("要素名", value=element.name)
                        if new_element_name != element.name:
                            element.name = new_element_name
                            st.session_state.template_modified = True
                        
                        # 要素タイプ（表示のみ）
                        st.text_input("要素タイプ", value=element.element_type.value, disabled=True)
                    
                    with col2:
                        # 要素ID（表示のみ）
                        st.text_input("要素ID", value=element.element_id, disabled=True)
                    
                    # 要素のプロパティ編集
                    st.subheader("プロパティ")
                    
                    # 要素タイプに応じたプロパティエディタを表示
                    self._render_element_properties(element)
                    
                    # スタイル編集
                    st.subheader("スタイル")
                    
                    # よく使うスタイル
                    common_styles = [
                        "width", "height", "margin", "padding", "background-color",
                        "color", "font-size", "font-weight", "text-align", "border"
                    ]
                    
                    for style_name in common_styles:
                        if style_name in element.styles:
                            new_value = st.text_input(f"スタイル: {style_name}", value=element.styles[style_name])
                            if new_value != element.styles[style_name]:
                                element.styles[style_name] = new_value
                                st.session_state.template_modified = True
                    
                    # 新しいスタイルの追加
                    with st.expander("スタイルを追加"):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_style_name = st.text_input("スタイル名")
                        with col2:
                            new_style_value = st.text_input("スタイル値")
                        
                        if st.button("スタイルを追加") and new_style_name and new_style_value:
                            element.styles[new_style_name] = new_style_value
                            st.session_state.template_modified = True
                            st.rerun()
            else:
                st.info("このセクションには要素がありません")
                
                if st.button("要素を追加"):
                    self._add_new_element(section)
                    st.session_state.template_modified = True
                    st.rerun()
        
        # テンプレート保存ボタン
        st.subheader("テンプレート保存")
        
        if st.session_state.template_modified:
            if st.button("テンプレートを保存", type="primary"):
                try:
                    # テンプレートを保存
                    template.updated_at = datetime.datetime.now()
                    self.template_manager.save_template(template)
                    st.session_state.template_modified = False
                    st.success(f"テンプレート '{template.name}' を保存しました")
                except Exception as e:
                    st.error(f"テンプレートの保存に失敗しました: {str(e)}")
        else:
            st.button("テンプレートを保存", disabled=True)
        
        # テンプレートのエクスポート
        if st.button("テンプレートをエクスポート"):
            template_json = template.to_json()
            st.download_button(
                label="JSONとしてダウンロード",
                data=template_json,
                file_name=f"{template.name}_{template.template_id}.json",
                mime="application/json"
            )
    
    def _render_element_properties(self, element: Element) -> None:
        """
        要素タイプに応じたプロパティエディタを表示
        
        Parameters
        ----------
        element : Element
            編集対象の要素
        """
        # 要素タイプに応じたプロパティの表示と編集
        element_type = element.element_type
        
        if element_type == ElementType.TEXT:
            # テキスト要素のプロパティ
            content = element.properties.get("content", "")
            new_content = st.text_area("テキスト内容", value=content, height=150)
            if new_content != content:
                element.properties["content"] = new_content
                st.session_state.template_modified = True
            
            content_type = element.properties.get("content_type", "static")
            content_types = ["static", "dynamic", "html"]
            new_content_type = st.selectbox(
                "コンテンツタイプ",
                options=content_types,
                index=content_types.index(content_type) if content_type in content_types else 0
            )
            if new_content_type != content_type:
                element.properties["content_type"] = new_content_type
                st.session_state.template_modified = True
        
        elif element_type == ElementType.TABLE:
            # テーブル要素のプロパティ
            data_source = element.properties.get("data_source", "")
            new_data_source = st.text_input("データソース", value=data_source)
            if new_data_source != data_source:
                element.properties["data_source"] = new_data_source
                st.session_state.template_modified = True
            
            # カラム定義
            st.subheader("カラム定義")
            columns = element.properties.get("columns", [])
            
            # 既存のカラムを表示
            for i, column in enumerate(columns):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    field = column.get("field", "")
                    new_field = st.text_input(f"フィールド #{i+1}", value=field, key=f"field_{i}")
                    if new_field != field:
                        column["field"] = new_field
                        st.session_state.template_modified = True
                
                with col2:
                    header = column.get("header", "")
                    new_header = st.text_input(f"ヘッダー #{i+1}", value=header, key=f"header_{i}")
                    if new_header != header:
                        column["header"] = new_header
                        st.session_state.template_modified = True
                
                with col3:
                    if st.button("削除", key=f"delete_column_{i}"):
                        columns.pop(i)
                        st.session_state.template_modified = True
                        st.rerun()
            
            # 新しいカラムの追加
            if st.button("カラムを追加"):
                columns.append({"field": "", "header": ""})
                st.session_state.template_modified = True
                st.rerun()
        
        elif element_type == ElementType.LIST:
            # リスト要素のプロパティ
            data_source = element.properties.get("data_source", "")
            new_data_source = st.text_input("データソース", value=data_source)
            if new_data_source != data_source:
                element.properties["data_source"] = new_data_source
                st.session_state.template_modified = True
            
            list_type = element.properties.get("list_type", "unordered")
            list_types = ["unordered", "ordered"]
            new_list_type = st.selectbox(
                "リストタイプ",
                options=list_types,
                index=list_types.index(list_type) if list_type in list_types else 0
            )
            if new_list_type != list_type:
                element.properties["list_type"] = new_list_type
                st.session_state.template_modified = True
            
            item_template = element.properties.get("item_template", "{{item}}")
            new_item_template = st.text_input("アイテムテンプレート", value=item_template)
            if new_item_template != item_template:
                element.properties["item_template"] = new_item_template
                st.session_state.template_modified = True
        
        elif element_type == ElementType.CHART:
            # チャート要素のプロパティ
            data_source = element.properties.get("data_source", "")
            new_data_source = st.text_input("データソース", value=data_source)
            if new_data_source != data_source:
                element.properties["data_source"] = new_data_source
                st.session_state.template_modified = True
            
            chart_type = element.properties.get("chart_type", "line")
            chart_types = ["line", "bar", "pie", "scatter", "area", "radar"]
            new_chart_type = st.selectbox(
                "チャートタイプ",
                options=chart_types,
                index=chart_types.index(chart_type) if chart_type in chart_types else 0
            )
            if new_chart_type != chart_type:
                element.properties["chart_type"] = new_chart_type
                st.session_state.template_modified = True
            
            chart_title = element.properties.get("title", "")
            new_chart_title = st.text_input("チャートタイトル", value=chart_title)
            if new_chart_title != chart_title:
                element.properties["title"] = new_chart_title
                st.session_state.template_modified = True
            
            x_axis = element.properties.get("x_axis", "")
            new_x_axis = st.text_input("X軸フィールド", value=x_axis)
            if new_x_axis != x_axis:
                element.properties["x_axis"] = new_x_axis
                st.session_state.template_modified = True
        
        elif element_type == ElementType.MAP:
            # マップ要素のプロパティ
            data_source = element.properties.get("data_source", "")
            new_data_source = st.text_input("データソース", value=data_source)
            if new_data_source != data_source:
                element.properties["data_source"] = new_data_source
                st.session_state.template_modified = True
            
            map_type = element.properties.get("map_type", "track")
            map_types = ["track", "heatmap", "points"]
            new_map_type = st.selectbox(
                "マップタイプ",
                options=map_types,
                index=map_types.index(map_type) if map_type in map_types else 0
            )
            if new_map_type != map_type:
                element.properties["map_type"] = new_map_type
                st.session_state.template_modified = True
            
            track_color = element.properties.get("track_color", "#FF5722")
            new_track_color = st.color_picker("トラックの色", value=track_color)
            if new_track_color != track_color:
                element.properties["track_color"] = new_track_color
                st.session_state.template_modified = True
            
            center_auto = element.properties.get("center_auto", True)
            new_center_auto = st.checkbox("自動中心位置", value=center_auto)
            if new_center_auto != center_auto:
                element.properties["center_auto"] = new_center_auto
                st.session_state.template_modified = True
            
            zoom_level = element.properties.get("zoom_level", 13)
            new_zoom_level = st.slider("ズームレベル", min_value=1, max_value=20, value=zoom_level)
            if new_zoom_level != zoom_level:
                element.properties["zoom_level"] = new_zoom_level
                st.session_state.template_modified = True
        
        # その他の要素タイプも同様に実装...
        else:
            # 汎用的なプロパティエディタ
            for prop_name, prop_value in element.properties.items():
                if isinstance(prop_value, str):
                    new_value = st.text_input(f"{prop_name}", value=prop_value)
                    if new_value != prop_value:
                        element.properties[prop_name] = new_value
                        st.session_state.template_modified = True
                elif isinstance(prop_value, bool):
                    new_value = st.checkbox(f"{prop_name}", value=prop_value)
                    if new_value != prop_value:
                        element.properties[prop_name] = new_value
                        st.session_state.template_modified = True
                elif isinstance(prop_value, (int, float)):
                    new_value = st.number_input(f"{prop_name}", value=prop_value)
                    if new_value != prop_value:
                        element.properties[prop_name] = new_value
                        st.session_state.template_modified = True
            
            # 新しいプロパティの追加
            with st.expander("プロパティを追加"):
                col1, col2 = st.columns(2)
                with col1:
                    new_prop_name = st.text_input("プロパティ名")
                with col2:
                    new_prop_value = st.text_input("プロパティ値")
                
                if st.button("プロパティを追加") and new_prop_name:
                    element.properties[new_prop_name] = new_prop_value
                    st.session_state.template_modified = True
                    st.rerun()
    
    def _render_template_preview(self) -> None:
        """
        テンプレートのプレビュー画面を描画
        """
        st.header("テンプレートのプレビュー")
        
        # 現在のテンプレートがない場合
        if st.session_state.current_template is None:
            st.info("プレビューするテンプレートを選択してください")
            return
        
        template = st.session_state.current_template
        
        # プレビューデータの作成・編集
        with st.expander("プレビューデータ", expanded=False):
            st.subheader("プレビューデータの編集")
            
            # サンプルデータの生成
            if st.button("サンプルデータを生成"):
                self._generate_sample_data()
                st.success("サンプルデータを生成しました")
                st.rerun()
            
            # 現在のプレビューデータを表示
            st.json(st.session_state.preview_data)
            
            # プレビューデータの編集
            st.subheader("データの編集")
            
            # データソースの追加
            with st.expander("データソースを追加"):
                col1, col2 = st.columns(2)
                with col1:
                    data_source_name = st.text_input("データソース名")
                with col2:
                    data_source_type = st.selectbox(
                        "データ型",
                        options=["文字列", "数値", "真偽値", "リスト", "辞書"]
                    )
                
                if data_source_type == "文字列":
                    data_value = st.text_input("値")
                elif data_source_type == "数値":
                    data_value = st.number_input("値", value=0)
                elif data_source_type == "真偽値":
                    data_value = st.checkbox("値")
                elif data_source_type == "リスト":
                    data_value = st.text_area("値（JSON形式のリスト）", value="[]")
                    try:
                        data_value = json.loads(data_value)
                    except:
                        st.error("有効なJSONリストではありません")
                        data_value = []
                elif data_source_type == "辞書":
                    data_value = st.text_area("値（JSON形式の辞書）", value="{}")
                    try:
                        data_value = json.loads(data_value)
                    except:
                        st.error("有効なJSON辞書ではありません")
                        data_value = {}
                
                if st.button("データソースを追加") and data_source_name:
                    st.session_state.preview_data[data_source_name] = data_value
                    st.success(f"データソース '{data_source_name}' を追加しました")
                    st.rerun()
        
        # プレビューの表示
        st.subheader("プレビュー")
        
        # レンダラーの作成
        renderer = HTMLRenderer(template)
        
        # コンテキストの設定
        renderer.set_context(st.session_state.preview_data)
        
        try:
            # テンプレートをレンダリング
            html_content = renderer.render()
            
            # HTMLの表示
            st.components.v1.html(html_content, height=600, scrolling=True)
            
            # HTMLのダウンロード
            st.download_button(
                label="HTMLとしてダウンロード",
                data=html_content,
                file_name=f"{template.name}_preview.html",
                mime="text/html"
            )
        except Exception as e:
            st.error(f"プレビューのレンダリングに失敗しました: {str(e)}")
            st.code(str(e), language="plaintext")
    
    def _create_new_template(self) -> None:
        """
        新しいテンプレートを作成
        """
        # 新しいテンプレートを作成
        template = Template(
            name="新しいテンプレート",
            description="説明を入力してください",
            author="",
            output_format=TemplateOutputFormat.HTML
        )
        
        # 基本的なセクションを追加
        header_section = Section(
            section_type=SectionType.HEADER,
            name="header",
            title="ヘッダー",
            description="レポートのヘッダーセクション",
            order=0
        )
        
        content_section = Section(
            section_type=SectionType.CONTENT,
            name="content",
            title="コンテンツ",
            description="レポートのメインコンテンツ",
            order=1
        )
        
        footer_section = Section(
            section_type=SectionType.FOOTER,
            name="footer",
            title="フッター",
            description="レポートのフッターセクション",
            order=2
        )
        
        # セクションをテンプレートに追加
        template.add_section(header_section)
        template.add_section(content_section)
        template.add_section(footer_section)
        
        # テンプレートを保存
        self.template_manager.save_template(template)
        
        # 現在のテンプレートとして設定
        st.session_state.current_template = template
        st.session_state.template_modified = False
        st.session_state.current_section_index = 0
    
    def _create_standard_templates(self) -> None:
        """
        標準テンプレートを生成
        """
        # 標準テンプレートモジュールのインポート
        from sailing_data_processor.reporting.templates.standard_templates import get_all_standard_templates
        
        # 標準テンプレートを取得
        templates = get_all_standard_templates()
        
        # テンプレートを保存
        for template in templates:
            self.template_manager.save_template(template)
    
    def _add_new_section(self) -> None:
        """
        新しいセクションを追加
        """
        template = st.session_state.current_template
        
        # 新しいセクションを作成
        section = Section(
            section_type=SectionType.CONTENT,
            name=f"section_{len(template.sections)}",
            title=f"新しいセクション {len(template.sections)}",
            description="セクションの説明",
            order=len(template.sections)
        )
        
        # セクションをテンプレートに追加
        template.add_section(section)
        
        # 現在のセクションとして設定
        st.session_state.current_section_index = len(template.sections) - 1
    
    def _duplicate_section(self, section_index: int) -> None:
        """
        セクションを複製
        
        Parameters
        ----------
        section_index : int
            複製するセクションのインデックス
        """
        template = st.session_state.current_template
        
        if 0 <= section_index < len(template.sections):
            # セクションの複製
            section = template.sections[section_index]
            section_dict = section.to_dict()
            
            # IDとプロパティを変更
            section_dict.pop("section_id", None)
            section_dict["name"] = f"{section.name}_copy"
            section_dict["title"] = f"{section.title} (コピー)"
            section_dict["order"] = len(template.sections)
            
            # 新しいセクションを作成
            new_section = Section.from_dict(section_dict)
            
            # セクションをテンプレートに追加
            template.add_section(new_section)
            
            # 現在のセクションとして設定
            st.session_state.current_section_index = len(template.sections) - 1
    
    def _delete_section(self, section_index: int) -> None:
        """
        セクションを削除
        
        Parameters
        ----------
        section_index : int
            削除するセクションのインデックス
        """
        template = st.session_state.current_template
        
        if 0 <= section_index < len(template.sections):
            # セクションの削除
            section = template.sections[section_index]
            template.remove_section(section.section_id)
            
            # 現在のセクションを更新
            if len(template.sections) > 0:
                st.session_state.current_section_index = min(section_index, len(template.sections) - 1)
            else:
                st.session_state.current_section_index = -1
            
            # 現在の要素をクリア
            st.session_state.current_element_id = None
    
    def _add_new_element(self, section: Section) -> None:
        """
        新しい要素を追加
        
        Parameters
        ----------
        section : Section
            要素を追加するセクション
        """
        # 要素タイプの選択
        element_types = [t.value for t in ElementType]
        
        # 要素タイプの選択ダイアログ
        element_type_index = st.radio(
            "追加する要素タイプを選択",
            options=list(range(len(element_types))),
            format_func=lambda i: element_types[i]
        )
        
        element_type = ElementType(element_types[element_type_index])
        
        # 要素名の入力
        element_name = st.text_input("要素名", value=f"{element_type.value}_{len(section.elements)}")
        
        # 要素の作成と追加
        if st.button("要素を追加"):
            element = Element(
                element_type=element_type,
                name=element_name
            )
            
            # 要素のデフォルトプロパティを設定
            if element_type == ElementType.TEXT:
                element.properties["content"] = "テキストを入力してください"
                element.properties["content_type"] = "static"
            elif element_type == ElementType.TABLE:
                element.properties["data_source"] = "data_source"
                element.properties["columns"] = [
                    {"field": "field1", "header": "ヘッダー1"},
                    {"field": "field2", "header": "ヘッダー2"}
                ]
            elif element_type == ElementType.LIST:
                element.properties["data_source"] = "list_data"
                element.properties["list_type"] = "unordered"
                element.properties["item_template"] = "{{item}}"
            elif element_type == ElementType.CHART:
                element.properties["data_source"] = "chart_data"
                element.properties["chart_type"] = "line"
                element.properties["title"] = "チャートタイトル"
                element.properties["x_axis"] = "x"
            elif element_type == ElementType.MAP:
                element.properties["data_source"] = "gps_data"
                element.properties["map_type"] = "track"
                element.properties["track_color"] = "#FF5722"
                element.properties["center_auto"] = True
                element.properties["zoom_level"] = 13
            
            # 要素をセクションに追加
            section.elements.append(element)
            
            # 現在の要素として設定
            st.session_state.current_element_id = element.element_id
            
            st.rerun()
    
    def _duplicate_element(self, section: Section, element_index: int) -> None:
        """
        要素を複製
        
        Parameters
        ----------
        section : Section
            要素を含むセクション
        element_index : int
            複製する要素のインデックス
        """
        if 0 <= element_index < len(section.elements):
            # 要素の複製
            element = section.elements[element_index]
            element_dict = element.to_dict()
            
            # IDとプロパティを変更
            element_dict.pop("element_id", None)
            element_dict["name"] = f"{element.name}_copy"
            
            # 新しい要素を作成
            new_element = Element.from_dict(element_dict)
            
            # 要素をセクションに追加
            section.elements.append(new_element)
            
            # 現在の要素として設定
            st.session_state.current_element_id = new_element.element_id
    
    def _delete_element(self, section: Section, element_index: int) -> None:
        """
        要素を削除
        
        Parameters
        ----------
        section : Section
            要素を含むセクション
        element_index : int
            削除する要素のインデックス
        """
        if 0 <= element_index < len(section.elements):
            # 要素の削除
            section.elements.pop(element_index)
            
            # 現在の要素をクリア
            st.session_state.current_element_id = None
    
    def _generate_sample_data(self) -> None:
        """
        プレビュー用のサンプルデータを生成
        """
        # サンプルデータの生成
        sample_data = {
            # メタデータ
            "session_name": "サンプルセーリングセッション",
            "session_date": "2023-05-15",
            "session_location": "東京湾",
            "sailor_name": "山田太郎",
            "boat_name": "シーブリーズ",
            
            # サマリーデータ
            "session_summary": "晴天の東京湾で行われたトレーニングセッション。風は北東から5ノット、波高は0.5m程度でした。",
            
            # セッションサマリーテーブル
            "session_summary": [
                {"metric": "平均速度", "value": "4.2 ノット"},
                {"metric": "最高速度", "value": "6.8 ノット"},
                {"metric": "平均風速", "value": "5.2 ノット"},
                {"metric": "航行距離", "value": "12.4 km"},
                {"metric": "航行時間", "value": "2時間15分"}
            ],
            
            # 風データ
            "wind_data": [
                {"timestamp": "09:00", "wind_speed": 4.5, "wind_direction": 45},
                {"timestamp": "09:30", "wind_speed": 5.0, "wind_direction": 50},
                {"timestamp": "10:00", "wind_speed": 5.2, "wind_direction": 55},
                {"timestamp": "10:30", "wind_speed": 5.5, "wind_direction": 60},
                {"timestamp": "11:00", "wind_speed": 5.8, "wind_direction": 55},
                {"timestamp": "11:30", "wind_speed": 5.4, "wind_direction": 50},
                {"timestamp": "12:00", "wind_speed": 5.0, "wind_direction": 45}
            ],
            
            # GPSデータ
            "gps_data": [
                {"timestamp": "09:00", "latitude": 35.6500, "longitude": 139.7700, "speed": 3.5},
                {"timestamp": "09:30", "latitude": 35.6520, "longitude": 139.7720, "speed": 4.0},
                {"timestamp": "10:00", "latitude": 35.6540, "longitude": 139.7740, "speed": 4.5},
                {"timestamp": "10:30", "latitude": 35.6560, "longitude": 139.7760, "speed": 5.0},
                {"timestamp": "11:00", "latitude": 35.6580, "longitude": 139.7780, "speed": 4.8},
                {"timestamp": "11:30", "latitude": 35.6600, "longitude": 139.7800, "speed": 4.5},
                {"timestamp": "12:00", "latitude": 35.6620, "longitude": 139.7820, "speed": 4.0}
            ],
            
            # 戦略ポイント
            "strategy_points": [
                {"timestamp": "09:15", "type": "タック", "score": 85, "description": "風向変化に対応したタック"},
                {"timestamp": "10:05", "type": "ジャイブ", "score": 75, "description": "最適航路へのジャイブ"},
                {"timestamp": "10:45", "type": "マーク回航", "score": 90, "description": "効率的なマーク回航"},
                {"timestamp": "11:20", "type": "ポインティング", "score": 80, "description": "風向変化に合わせた最適ポイント"}
            ],
            
            # 戦略ハイライト
            "strategy_highlights": [
                {"timestamp": "09:15", "description": "風向変化に対応した素早いタック", "score": 85},
                {"timestamp": "10:45", "description": "効率的なマーク回航、内側ラインの確保", "score": 90},
                {"timestamp": "11:20", "description": "ポインティングの調整による速度維持", "score": 80}
            ],
            
            # パフォーマンスデータ
            "performance_data": [
                {"timestamp": "09:00", "speed": 3.5, "optimal_speed": 3.8, "vmg": 2.8, "optimal_vmg": 3.0, "wind_speed": 4.5},
                {"timestamp": "09:30", "speed": 4.0, "optimal_speed": 4.1, "vmg": 3.2, "optimal_vmg": 3.4, "wind_speed": 5.0},
                {"timestamp": "10:00", "speed": 4.5, "optimal_speed": 4.3, "vmg": 3.5, "optimal_vmg": 3.5, "wind_speed": 5.2},
                {"timestamp": "10:30", "speed": 5.0, "optimal_speed": 4.6, "vmg": 3.8, "optimal_vmg": 3.7, "wind_speed": 5.5},
                {"timestamp": "11:00", "speed": 4.8, "optimal_speed": 4.8, "vmg": 3.7, "optimal_vmg": 3.8, "wind_speed": 5.8},
                {"timestamp": "11:30", "speed": 4.5, "optimal_speed": 4.5, "vmg": 3.5, "optimal_vmg": 3.6, "wind_speed": 5.4},
                {"timestamp": "12:00", "speed": 4.0, "optimal_speed": 4.2, "vmg": 3.2, "optimal_vmg": 3.3, "wind_speed": 5.0}
            ],
            
            # パフォーマンスサマリー
            "performance_summary": {
                "平均パフォーマンス比率": "95%",
                "最適VMG達成率": "90%",
                "上り角度平均": "42度",
                "下り角度平均": "138度"
            },
            
            # 比較データ
            "comparison_data": [
                {"metric": "平均速度", "current_value": 4.2, "average_value": 3.8},
                {"metric": "最高速度", "current_value": 6.8, "average_value": 6.2},
                {"metric": "平均VMG", "current_value": 3.4, "average_value": 3.1},
                {"metric": "タック回数", "current_value": 8, "average_value": 10}
            ],
            
            # 強みリスト
            "strengths_list": [
                {"title": "風の変化への対応", "description": "風向・風速の変化に対して素早く調整ができていた"},
                {"title": "マーク回航", "description": "効率的なライン取りによる優れたマーク回航"},
                {"title": "一定のパフォーマンス", "description": "セッションを通じて安定したパフォーマンスを維持"}
            ],
            
            # 弱みリスト
            "weaknesses_list": [
                {"title": "タックの効率", "description": "タック後の加速がやや遅い傾向がある"},
                {"title": "軽風時の速度", "description": "風速が4ノット以下の時にスピードの維持が難しい"},
                {"title": "セール調整", "description": "風の変化に対するセール調整のタイミングが遅れる場合がある"}
            ],
            
            # 改善計画
            "improvement_intro": "次回のセッションでは以下の点に焦点を当てます：",
            "improvement_items": [
                {"title": "タック技術", "description": "タック後の加速を改善するためのセール操作を練習"},
                {"title": "軽風走法", "description": "軽風時のウェイトポジションとセールトリムの最適化"},
                {"title": "風の変化への注意", "description": "風向・風速の変化をより早く察知する意識を高める"}
            ],
            
            # 練習計画
            "practice_plan": [
                {"day": "5月18日", "focus": "タック技術", "exercises": "タック後加速練習", "goals": "タック後5秒以内に通常速度の80%回復"},
                {"day": "5月20日", "focus": "軽風走法", "exercises": "軽風時のトリム練習", "goals": "風速4ノット以下で3.5ノット維持"},
                {"day": "5月22日", "focus": "風の変化", "exercises": "風上フォーカス練習", "goals": "風向変化を事前に読む精度向上"}
            ]
        }
        
        # サンプルデータをセッション状態に保存
        st.session_state.preview_data = sample_data


class ElementPalette:
    """
    要素パレットコンポーネント
    
    新しい要素を追加するためのパレットを提供するStreamlitコンポーネントです。
    """
    
    def __init__(self, on_element_select: Optional[Callable[[ElementType], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        on_element_select : Optional[Callable[[ElementType], None]], optional
            要素選択時のコールバック, by default None
        """
        self.on_element_select = on_element_select
    
    def render(self) -> None:
        """
        要素パレットを描画
        """
        st.subheader("要素パレット")
        
        # 要素タイプのカテゴリ
        element_categories = {
            "コンテンツ要素": [
                ElementType.TEXT, ElementType.TABLE, ElementType.LIST, 
                ElementType.KEY_VALUE
            ],
            "視覚化要素": [
                ElementType.CHART, ElementType.MAP, ElementType.DIAGRAM, 
                ElementType.IMAGE
            ],
            "レイアウト要素": [
                ElementType.SECTION, ElementType.COLUMN, ElementType.GRID, 
                ElementType.TAB, ElementType.DIVIDER, ElementType.BOX, 
                ElementType.BACKGROUND
            ]
        }
        
        # カテゴリごとに要素を表示
        for category, element_types in element_categories.items():
            with st.expander(category, expanded=True):
                for i in range(0, len(element_types), 3):
                    cols = st.columns(3)
                    for j in range(3):
                        if i + j < len(element_types):
                            element_type = element_types[i + j]
                            with cols[j]:
                                if st.button(element_type.value, key=f"element_{element_type.value}"):
                                    if self.on_element_select:
                                        self.on_element_select(element_type)


class PropertyPanel:
    """
    プロパティパネルコンポーネント
    
    要素のプロパティを編集するためのパネルを提供するStreamlitコンポーネントです。
    """
    
    def __init__(self, on_property_change: Optional[Callable[[str, Any], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        on_property_change : Optional[Callable[[str, Any], None]], optional
            プロパティ変更時のコールバック, by default None
        """
        self.on_property_change = on_property_change
    
    def render(self, element: Optional[Element] = None) -> None:
        """
        プロパティパネルを描画
        
        Parameters
        ----------
        element : Optional[Element], optional
            編集する要素, by default None
        """
        st.subheader("プロパティ")
        
        if element is None:
            st.info("要素が選択されていません")
            return
        
        # 要素の基本情報
        st.text_input("要素ID", value=element.element_id, disabled=True)
        
        # 要素名の編集
        new_name = st.text_input("要素名", value=element.name)
        if new_name != element.name and self.on_property_change:
            self.on_property_change("name", new_name)
        
        # 要素タイプの表示
        st.text_input("要素タイプ", value=element.element_type.value, disabled=True)
        
        # 要素タイプに応じたプロパティエディタを表示
        st.subheader("プロパティ")
        
        # プロパティの編集
        for prop_name, prop_value in element.properties.items():
            if isinstance(prop_value, str):
                new_value = st.text_input(f"{prop_name}", value=prop_value)
                if new_value != prop_value and self.on_property_change:
                    self.on_property_change(prop_name, new_value)
            elif isinstance(prop_value, bool):
                new_value = st.checkbox(f"{prop_name}", value=prop_value)
                if new_value != prop_value and self.on_property_change:
                    self.on_property_change(prop_name, new_value)
            elif isinstance(prop_value, (int, float)):
                new_value = st.number_input(f"{prop_name}", value=prop_value)
                if new_value != prop_value and self.on_property_change:
                    self.on_property_change(prop_name, new_value)
        
        # スタイルの編集
        st.subheader("スタイル")
        
        for style_name, style_value in element.styles.items():
            new_value = st.text_input(f"スタイル: {style_name}", value=style_value)
            if new_value != style_value and self.on_property_change:
                self.on_property_change(f"style_{style_name}", new_value)


class PreviewPanel:
    """
    プレビューパネルコンポーネント
    
    テンプレートのプレビューを表示するためのパネルを提供するStreamlitコンポーネントです。
    """
    
    def __init__(self):
        """
        初期化
        """
        # プレビューデータ
        if 'preview_data' not in st.session_state:
            st.session_state.preview_data = {}
    
    def render(self, template: Optional[Template] = None) -> None:
        """
        プレビューパネルを描画
        
        Parameters
        ----------
        template : Optional[Template], optional
            プレビューするテンプレート, by default None
        """
        st.subheader("プレビュー")
        
        if template is None:
            st.info("プレビューするテンプレートがありません")
            return
        
        # プレビューデータの編集オプション
        with st.expander("プレビューデータ", expanded=False):
            # サンプルデータの生成
            if st.button("サンプルデータを生成"):
                self._generate_sample_data()
                st.success("サンプルデータを生成しました")
                st.rerun()
            
            # 現在のプレビューデータを表示
            st.json(st.session_state.preview_data)
        
        # レンダラーの作成
        renderer = HTMLRenderer(template)
        
        # コンテキストの設定
        renderer.set_context(st.session_state.preview_data)
        
        try:
            # テンプレートをレンダリング
            html_content = renderer.render()
            
            # HTMLの表示
            st.components.v1.html(html_content, height=600, scrolling=True)
        except Exception as e:
            st.error(f"プレビューのレンダリングに失敗しました: {str(e)}")
            st.code(str(e), language="plaintext")
    
    def _generate_sample_data(self) -> None:
        """
        プレビュー用のサンプルデータを生成
        """
        # サンプルデータの生成（TemplateEditor._generate_sample_dataと同じ）
        sample_data = {
            # メタデータ
            "session_name": "サンプルセーリングセッション",
            "session_date": "2023-05-15",
            "session_location": "東京湾",
            "sailor_name": "山田太郎",
            "boat_name": "シーブリーズ",
            
            # 以下略（TemplateEditor._generate_sample_dataと同じ）
        }
        
        # サンプルデータをセッション状態に保存
        st.session_state.preview_data = sample_data
