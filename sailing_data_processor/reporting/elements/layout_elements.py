# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.layout_elements

レポートのレイアウト要素を提供するモジュールです。
セクション、カラム、グリッド、タブなどのレイアウト要素を定義します。
"""

from typing import Dict, List, Any, Optional, Union, Set
import json
import html

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class SectionElement(BaseElement):
    """
    セクション要素クラス
    
    コンテンツをセクションとしてグループ化するための要素です。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        **kwargs : dict
            モデルが提供されない場合に使用されるプロパティ
        """
        # デフォルトでセクション要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.SECTION
        
        super().__init__(model, **kwargs)
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLにレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # タイトルの取得
        title = self.get_property("title", "")
        title = self.replace_variables(title, context)
        
        # 説明の取得
        description = self.get_property("description", "")
        description = self.replace_variables(description, context)
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # セクション要素のレンダリング
        html_parts = [
            f'<section id="{self.element_id}" class="report-section" style="{css_style}">'
        ]
        
        # タイトルがある場合
        if title:
            title_level = self.get_property("title_level", 2)
            html_parts.append(f'<h{title_level} class="report-section-title">{html.escape(title)}</h{title_level}>')
        
        # 説明がある場合
        if description:
            html_parts.append(f'<div class="report-section-description">{html.escape(description)}</div>')
        
        # 子要素のコンテンツ部分
        html_parts.append('<div class="report-section-content">')
        
        # 子要素のインポートと初期化（要素工場を使用）
        from sailing_data_processor.reporting.elements.element_factory import create_element
        
        # 子要素のレンダリング
        for child_model in self.children:
            child_element = create_element(child_model)
            if child_element:
                html_parts.append(child_element.render(context))
        
        html_parts.append('</div></section>')
        
        return ''.join(html_parts)


class ColumnElement(BaseElement):
    """
    カラム要素クラス
    
    コンテンツを垂直方向にレイアウトするための要素です。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        **kwargs : dict
            モデルが提供されない場合に使用されるプロパティ
        """
        # デフォルトでカラム要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.COLUMN
        
        super().__init__(model, **kwargs)
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLにレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # 幅の取得
        width = self.get_property("width", "auto")
        
        # CSSスタイルの取得（幅を追加）
        styles = self.styles.copy()
        styles["width"] = width
        css_style = '; '.join([f"{k}: {v}" for k, v in styles.items()])
        # カラム要素のレンダリング
        html_parts = [
            f'<div id="{self.element_id}" class="report-column" style="{css_style}">'
        ]
        
        # 子要素のインポートと初期化
        from sailing_data_processor.reporting.elements.element_factory import create_element
        
        # 子要素のレンダリング
        for child_model in self.children:
            child_element = create_element(child_model)
            if child_element:
                html_parts.append(child_element.render(context))
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)


class GridElement(BaseElement):
    """
    グリッド要素クラス
    
    コンテンツをグリッドレイアウトで表示するための要素です。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        **kwargs : dict
            モデルが提供されない場合に使用されるプロパティ
        """
        # デフォルトでグリッド要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.GRID
        
        super().__init__(model, **kwargs)
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLにレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # グリッド設定の取得
        columns = self.get_property("columns", 2)
        gap = self.get_property("gap", "10px")
        
        # CSSスタイルの取得（グリッド設定を追加）
        styles = self.styles.copy()
        styles["display"] = "grid"
        styles["grid-template-columns"] = f"repeat({columns}, 1fr)"
        styles["grid-gap"] = gap
        css_style = '; '.join([f"{k}: {v}" for k, v in styles.items()])
        # グリッド要素のレンダリング
        html_parts = [
            f'<div id="{self.element_id}" class="report-grid" style="{css_style}">'
        ]
        
        # 子要素のインポートと初期化
        from sailing_data_processor.reporting.elements.element_factory import create_element
        
        # 子要素のレンダリング
        for child_model in self.children:
            # グリッドアイテムの設定を取得
            span = child_model.properties.get("grid_span", 1)
            row_span = child_model.properties.get("grid_row_span", 1)
            
            # グリッドアイテム用のラッパー
            item_style = f"grid-column: span {span}; grid-row: span {row_span};"
            html_parts.append(f'<div class="report-grid-item" style="{item_style}">')
            
            # 子要素のレンダリング
            child_element = create_element(child_model)
            if child_element:
                html_parts.append(child_element.render(context))
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)


class TabElement(BaseElement):
    """
    タブ要素クラス
    
    コンテンツをタブ形式で表示するための要素です。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        **kwargs : dict
            モデルが提供されない場合に使用されるプロパティ
        """
        # デフォルトでタブ要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.TAB
        
        super().__init__(model, **kwargs)
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLにレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # タブ設定の取得
        tab_items = self.get_property("tabs", [])
        
        # タブアイテムがない場合は子要素からタブを生成
        if not tab_items and self.children:
            tab_items = []
            for i, child in enumerate(self.children):
                tab_items.append({
                    "id": f"tab_{self.element_id}_{i}",
                    "label": child.name or f"タブ {i+1}",
                    "content_index": i
                })
        
        # タブアイテムがない場合
        if not tab_items:
            return f'<div id="{self.element_id}" class="report-tab-empty">タブ要素がありません</div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # タブコンテナID
        tab_id = f"tab_container_{self.element_id}"
        
        # タブのレンダリング
        html_parts = [
            f'<div id="{self.element_id}" class="report-tab-container" style="{css_style}">',
            f'<div class="report-tab-nav" role="tablist" aria-labelledby="{tab_id}_label">'
        ]
        
        # タブナビゲーションのレンダリング
        for i, tab in enumerate(tab_items):
            tab_button_id = f"tab_button_{self.element_id}_{i}"
            tab_panel_id = f"tab_panel_{self.element_id}_{i}"
            selected = "true" if i == 0 else "false"
            active_class = "report-tab-active" if i == 0 else ""
            
            html_parts.append(
                f'<button id="{tab_button_id}" class="report-tab-button {active_class}" '
                f'role="tab" aria-controls="{tab_panel_id}" aria-selected="{selected}" '
                f'data-tab-index="{i}">{html.escape(tab["label"])}</button>'
            )
        
        html_parts.append('</div><div class="report-tab-content">')
        
        # 子要素のインポートと初期化
        from sailing_data_processor.reporting.elements.element_factory import create_element
        
        # タブパネルのレンダリング
        for i, tab in enumerate(tab_items):
            tab_panel_id = f"tab_panel_{self.element_id}_{i}"
            tab_button_id = f"tab_button_{self.element_id}_{i}"
            hidden = "" if i == 0 else "hidden"
            
            html_parts.append(
                f'<div id="{tab_panel_id}" class="report-tab-panel" role="tabpanel" '
                f'aria-labelledby="{tab_button_id}" {hidden}>'
            )
            
            # タブコンテンツのレンダリング
            if "content" in tab:
                # 静的コンテンツの場合
                content = tab["content"]
                content = self.replace_variables(content, context)
                html_parts.append(content)
            elif "content_index" in tab and isinstance(tab["content_index"], int):
                # 子要素から取得する場合
                index = tab["content_index"]
                if 0 <= index < len(self.children):
                    child_model = self.children[index]
                    child_element = create_element(child_model)
                    if child_element:
                        html_parts.append(child_element.render(context))
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        # タブの切り替え用JavaScript
        html_parts.append(f'''
        <script>
            (function() {{
                // タブの切り替え機能
                document.addEventListener('DOMContentLoaded', function() {{
                    var tabs = document.querySelectorAll('#{self.element_id} .report-tab-button');
                    
                    for (var i = 0; i < tabs.length; i++) {{
                        tabs[i].addEventListener('click', function() {{
                            // 現在のアクティブタブを非アクティブに
                            var currentActive = document.querySelector('#{self.element_id} .report-tab-active');
                            if (currentActive) {currentActive.classList.remove('report-tab-active');
                                currentActive.setAttribute('aria-selected', 'false');
                                document.getElementById(currentActive.getAttribute('aria-controls')).hidden = true;
                            }}
                            
                            // クリックされたタブをアクティブに
                            this.classList.add('report-tab-active');
                            this.setAttribute('aria-selected', 'true');
                            document.getElementById(this.getAttribute('aria-controls')).hidden = false;
                        }});
                    }}
                }});
            }})();
        </script>
        ''')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)


class DividerElement(BaseElement):
    """
    区切り線要素クラス
    
    コンテンツを視覚的に区切るための要素です。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        **kwargs : dict
            モデルが提供されない場合に使用されるプロパティ
        """
        # デフォルトで区切り線要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.DIVIDER
        
        super().__init__(model, **kwargs)
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLにレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # 区切り線のスタイル取得
        style = self.get_property("style", "solid")
        color = self.get_property("color", "#cccccc")
        thickness = self.get_property("thickness", "1px")
        margin = self.get_property("margin", "20px 0")
        
        # CSSスタイルの取得（区切り線スタイルを追加）
        styles = self.styles.copy()
        styles["border"] = "none"
        styles["border-top"] = f"{thickness} {style} {color}"
        styles["margin"] = margin
        styles["width"] = "100%"
        css_style = '; '.join([f"{k}: {v}" for k, v in styles.items()])
        # 区切り線要素のレンダリング
        return f'<hr id="{self.element_id}" class="report-divider" style="{css_style}">'


class BoxElement(BaseElement):
    """
    ボックス要素クラス
    
    コンテンツをボックスで囲むための要素です。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        **kwargs : dict
            モデルが提供されない場合に使用されるプロパティ
        """
        # デフォルトでボックス要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.BOX
        
        super().__init__(model, **kwargs)
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLにレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # ボックス設定の取得
        title = self.get_property("title", "")
        title = self.replace_variables(title, context)
        icon = self.get_property("icon", "")
        
        # 値の取得（単一値または子要素）
        value = self.get_property("value", "")
        value = self.replace_variables(str(value), context)
        
        # コンテンツソースの取得
        content_source = self.get_property("content_source", "")
        content = ""
        
        if content_source and content_source in context:
            # コンテンツソースからデータを取得
            content_data = context[content_source]
            
            # データ形式に応じた処理
            if isinstance(content_data, list):
                content = "<ul>"
                for item in content_data:
                    if isinstance(item, dict):
                        # タイトルと説明の要素がある場合
                        if "title" in item and "description" in item:
                            content += f"<li><strong>{html.escape(item['title'])}</strong>: {html.escape(item['description'])}</li>"
                        else:
                            content += f"<li>{html.escape(str(item))}</li>"
                    else:
                        content += f"<li>{html.escape(str(item))}</li>"
                content += "</ul>"
            elif isinstance(content_data, dict):
                content = "<dl>"
                for key, val in content_data.items():
                    content += f"<dt>{html.escape(key)}</dt><dd>{html.escape(str(val))}</dd>"
                content += "</dl>"
            else:
                content = html.escape(str(content_data))
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # ボックス要素のレンダリング
        html_parts = [
            f'<div id="{self.element_id}" class="report-box" style="{css_style}">'
        ]
        
        # アイコンがある場合
        if icon:
            html_parts.append(f'<div class="report-box-icon"><i class="material-icons">{icon}</i></div>')
        
        # タイトルがある場合
        if title:
            html_parts.append(f'<div class="report-box-title">{html.escape(title)}</div>')
        
        # 値がある場合
        if value:
            html_parts.append(f'<div class="report-box-value">{value}</div>')
        
        # コンテンツがある場合
        if content:
            html_parts.append(f'<div class="report-box-content">{content}</div>')
        
        # 子要素がある場合
        if self.children:
            html_parts.append('<div class="report-box-children">')
            
            # 子要素のインポートと初期化
            from sailing_data_processor.reporting.elements.element_factory import create_element
            
            # 子要素のレンダリング
            for child_model in self.children:
                child_element = create_element(child_model)
                if child_element:
                    html_parts.append(child_element.render(context))
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)


class BackgroundElement(BaseElement):
    """
    背景要素クラス
    
    子要素に背景を提供するための要素です。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        **kwargs : dict
            モデルが提供されない場合に使用されるプロパティ
        """
        # デフォルトで背景要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.BACKGROUND
        
        super().__init__(model, **kwargs)
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        要素をHTMLにレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # 背景設定の取得
        background_color = self.get_property("background_color", "")
        background_image = self.get_property("background_image", "")
        
        # CSSスタイルの取得（背景スタイルを追加）
        styles = self.styles.copy()
        
        if background_color:
            styles["background-color"] = background_color
        
        if background_image:
            # 変数置換
            background_image = self.replace_variables(background_image, context)
            styles["background-image"] = f"url('{background_image}')"
            styles["background-size"] = self.get_property("background_size", "cover")
            styles["background-position"] = self.get_property("background_position", "center")
            styles["background-repeat"] = self.get_property("background_repeat", "no-repeat")
        
        css_style = '; '.join([f"{k}: {v}" for k, v in styles.items()])
        # 背景要素のレンダリング
        html_parts = [
            f'<div id="{self.element_id}" class="report-background" style="{css_style}">'
        ]
        
        # 子要素のインポートと初期化
        from sailing_data_processor.reporting.elements.element_factory import create_element
        
        # 子要素のレンダリング
        for child_model in self.children:
            child_element = create_element(child_model)
            if child_element:
                html_parts.append(child_element.render(context))
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)
