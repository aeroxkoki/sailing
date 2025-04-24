"""
sailing_data_processor.reporting.elements.content_elements

レポートのコンテンツ要素を提供するモジュールです。
テキスト、テーブル、チャート、マップなどのコンテンツ要素を定義します。
"""

from typing import Dict, List, Any, Optional, Union, Set
import json
import html

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class TextElement(BaseElement):
    """
    テキスト要素クラス
    
    静的テキストや動的生成テキストを表示するための要素です。
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
        # デフォルトでテキスト要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.TEXT
        
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
        
        # コンテンツの取得
        content = self.get_property("content", "")
        content_type = self.get_property("content_type", "static")
        
        # 変数の置換
        if content_type == "dynamic":
            content = self.replace_variables(content, context)
        elif content_type == "html":
            # HTMLの場合は変数置換のみ行い、エスケープしない
            content = self.replace_variables(content, context)
        else:
            # 静的テキストの場合はHTMLエスケープ
            content = html.escape(content)
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # テキスト要素のレンダリング
        if content_type == "html":
            # HTML直接出力
            return f'<div id="{self.element_id}" class="report-text" style="{css_style}">{content}</div>'
        else:
            # 改行をBRタグに変換
            content = content.replace('\n', '<br>')
            return f'<div id="{self.element_id}" class="report-text" style="{css_style}">{content}</div>'


class TableElement(BaseElement):
    """
    テーブル要素クラス
    
    データをテーブル形式で表示するための要素です。
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
        # デフォルトでテーブル要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.TABLE
        
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
        
        # データソース名の取得
        data_source = self.get_property("data_source", "")
        data = None
        
        # データソースからデータを取得
        if data_source and data_source in context:
            data = context[data_source]
        
        # データがない場合
        if not data or not isinstance(data, list) or len(data) == 0:
            return f'<div id="{self.element_id}" class="report-table-empty">データがありません</div>'
        
        # カラム定義の取得
        columns = self.get_property("columns", [])
        
        # カラム定義がない場合はデータの最初の行からカラムを生成
        if not columns and isinstance(data[0], dict):
            columns = [{"field": key, "header": key} for key in data[0].keys()]
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # テーブルのレンダリング
        html_parts = [
            f'<div id="{self.element_id}" class="report-table-container" style="{css_style}">',
            '<table class="report-table">'
        ]
        
        # テーブルヘッダー
        html_parts.append('<thead><tr>')
        for col in columns:
            header = col.get("header", col.get("field", ""))
            header_style = col.get("style", "")
            html_parts.append(f'<th style="{header_style}">{header}</th>')
        html_parts.append('</tr></thead>')
        
        # テーブルボディ
        html_parts.append('<tbody>')
        for row in data:
            html_parts.append('<tr>')
            
            for col in columns:
                field = col.get("field", "")
                value = ""
                
                # フィールド値の取得
                if isinstance(row, dict) and field in row:
                    value = row[field]
                elif isinstance(row, (list, tuple)) and isinstance(field, int) and 0 <= field < len(row):
                    value = row[field]
                
                # セル内容の整形
                if value is None:
                    value = ""
                elif not isinstance(value, str):
                    value = str(value)
                
                # セルのレンダリング
                cell_style = col.get("cell_style", "")
                html_parts.append(f'<td style="{cell_style}">{html.escape(value)}</td>')
            
            html_parts.append('</tr>')
        
        html_parts.append('</tbody></table></div>')
        
        return ''.join(html_parts)


class ListElement(BaseElement):
    """
    リスト要素クラス
    
    データを順序付きまたは順序なしリストとして表示するための要素です。
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
        # デフォルトでリスト要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.LIST
        
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
        
        # データソース名の取得
        data_source = self.get_property("data_source", "")
        data = None
        
        # データソースからデータを取得
        if data_source and data_source in context:
            data = context[data_source]
        
        # データがない場合
        if not data or not isinstance(data, list) or len(data) == 0:
            return f'<div id="{self.element_id}" class="report-list-empty">データがありません</div>'
        
        # リストタイプ（順序付き/順序なし）の取得
        list_type = self.get_property("list_type", "unordered")
        item_template = self.get_property("item_template", "{{item}}")
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # リストタグの選択
        list_tag = "ol" if list_type == "ordered" else "ul"
        
        # リストのレンダリング
        html_parts = [
            f'<div id="{self.element_id}" class="report-list-container" style="{css_style}">',
            f'<{list_tag} class="report-list">'
        ]
        
        # リストアイテムのレンダリング
        for item in data:
            # アイテムをコンテキストに追加
            item_context = context.copy()
            
            # アイテムがディクショナリの場合は直接追加
            if isinstance(item, dict):
                item_context.update(item)
            else:
                item_context["item"] = item
            
            # テンプレートの変数置換
            content = self.replace_variables(item_template, item_context)
            
            # リストアイテムのレンダリング
            html_parts.append(f'<li>{content}</li>')
        
        html_parts.append(f'</{list_tag}></div>')
        
        return ''.join(html_parts)


class KeyValueElement(BaseElement):
    """
    キーバリュー要素クラス
    
    データをキーと値のペアとして表示するための要素です。
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
        # デフォルトでキーバリュー要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.KEY_VALUE
        
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
        
        # データソース名の取得
        data_source = self.get_property("data_source", "")
        data = None
        
        # データソースからデータを取得
        if data_source and data_source in context:
            data = context[data_source]
        
        # データがない場合
        if not data or not isinstance(data, dict) or len(data) == 0:
            return f'<div id="{self.element_id}" class="report-key-value-empty">データがありません</div>'
        
        # タイトルの取得
        title = self.get_property("title", "")
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # キーバリュー要素のレンダリング
        html_parts = [
            f'<div id="{self.element_id}" class="report-key-value-container" style="{css_style}">'
        ]
        
        # タイトルがある場合
        if title:
            html_parts.append(f'<h3 class="report-key-value-title">{html.escape(title)}</h3>')
        
        # キーバリューテーブルのレンダリング
        html_parts.append('<table class="report-key-value-table">')
        
        for key, value in data.items():
            # 値の整形
            if value is None:
                display_value = ""
            elif not isinstance(value, str):
                display_value = str(value)
            else:
                display_value = value
            
            # 行のレンダリング
            html_parts.append('<tr>')
            html_parts.append(f'<th class="report-key-value-key">{html.escape(key)}</th>')
            html_parts.append(f'<td class="report-key-value-value">{html.escape(display_value)}</td>')
            html_parts.append('</tr>')
        
        html_parts.append('</table></div>')
        
        return ''.join(html_parts)


class ChartElement(BaseElement):
    """
    チャート要素クラス
    
    データをチャートとして視覚化するための要素です。
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
        # デフォルトでチャート要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.CHART
        
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
        
        # データソース名の取得
        data_source = self.get_property("data_source", "")
        data = None
        
        # データソースからデータを取得
        if data_source and data_source in context:
            data = context[data_source]
        
        # データがない場合
        if not data:
            return f'<div id="{self.element_id}" class="report-chart-empty">チャートデータがありません</div>'
        
        # チャートタイプの取得
        chart_type = self.get_property("chart_type", "line")
        
        # チャートタイトルの取得
        chart_title = self.get_property("title", "")
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # チャート設定のJSON取得
        chart_config = {
            "type": chart_type,
            "data": data,
            "options": {
                "title": chart_title,
                "responsive": True,
                "maintainAspectRatio": False
        
        # X軸とシリーズ設定を追加
        x_axis = self.get_property("x_axis", "")
        series = self.get_property("series", [])
        
        if x_axis and series:
            chart_config["x_axis"] = x_axis
            chart_config["series"] = series
        
        # チャート設定をJSONにシリアライズ
        chart_config_json = json.dumps(chart_config)
        
        # 一意のチャートIDを生成
        chart_id = f"chart_{self.element_id}"
        
        # チャート要素のレンダリング
        html = f'''
        <div id="{self.element_id}" class="report-chart-container" style="{css_style}">
            <canvas id="{chart_id}" class="report-chart"></canvas>
            <script>
                (function() {{
                    // チャート設定
                    var config = {chart_config_json};
                    
                    // チャート初期化
                    window.addEventListener('load', function() {{
                        var ctx = document.getElementById('{chart_id}').getContext('2d');
                        new Chart(ctx, config);
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html


class MapElement(BaseElement):
    """
    マップ要素クラス
    
    地理データをマップとして表示するための要素です。
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
        # デフォルトでマップ要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.MAP
        
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
        
        # データソース名の取得
        data_source = self.get_property("data_source", "")
        data = None
        
        # データソースからデータを取得
        if data_source and data_source in context:
            data = context[data_source]
        
        # データがない場合
        if not data:
            return f'<div id="{self.element_id}" class="report-map-empty">マップデータがありません</div>'
        
        # マップタイプの取得
        map_type = self.get_property("map_type", "track")
        
        # マップ設定の取得
        center_auto = self.get_property("center_auto", True)
        zoom_level = self.get_property("zoom_level", 13)
        track_color = self.get_property("track_color", "#FF5722")
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # マップ設定のJSON取得
        map_config = {
            "type": map_type,
            "data": data,
            "options": {
                "center_auto": center_auto,
                "zoom_level": zoom_level,
                "track_color": track_color
        
        # 追加オプションの取得
        show_wind = self.get_property("show_wind", False)
        show_strategy_points = self.get_property("show_strategy_points", False)
        
        if show_wind:
            map_config["options"]["show_wind"] = True
        
        if show_strategy_points:
            map_config["options"]["show_strategy_points"] = True
        
        # マップ設定をJSONにシリアライズ
        map_config_json = json.dumps(map_config)
        
        # 一意のマップIDを生成
        map_id = f"map_{self.element_id}"
        
        # マップ要素のレンダリング
        html = f'''
        <div id="{self.element_id}" class="report-map-container" style="{css_style}">
            <div id="{map_id}" class="report-map"></div>
            <script>
                (function() {{
                    // マップ設定
                    var config = {map_config_json};
                    
                    // マップ初期化
                    window.addEventListener('load', function() {{
                        initMap('{map_id}', config);
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html


class DiagramElement(BaseElement):
    """
    ダイアグラム要素クラス
    
    データをダイアグラムとして表示するための要素です。
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
        # デフォルトでダイアグラム要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.DIAGRAM
        
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
        
        # データソース名の取得
        data_source = self.get_property("data_source", "")
        data = None
        
        # データソースからデータを取得
        if data_source and data_source in context:
            data = context[data_source]
        
        # データがない場合
        if not data:
            return f'<div id="{self.element_id}" class="report-diagram-empty">ダイアグラムデータがありません</div>'
        
        # ダイアグラムタイプの取得
        diagram_type = self.get_property("diagram_type", "windrose")
        
        # ダイアグラムタイトルの取得
        diagram_title = self.get_property("title", "")
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # ダイアグラム設定のJSON取得
        diagram_config = {
            "type": diagram_type,
            "data": data,
            "options": {
                "title": diagram_title
        
        # ダイアグラム設定をJSONにシリアライズ
        diagram_config_json = json.dumps(diagram_config)
        
        # 一意のダイアグラムIDを生成
        diagram_id = f"diagram_{self.element_id}"
        
        # ダイアグラム要素のレンダリング
        html = f'''
        <div id="{self.element_id}" class="report-diagram-container" style="{css_style}">
            <div id="{diagram_id}" class="report-diagram"></div>
            <script>
                (function() {{
                    // ダイアグラム設定
                    var config = {diagram_config_json};
                    
                    // ダイアグラム初期化
                    window.addEventListener('load', function() {{
                        initDiagram('{diagram_id}', config);
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html


class ImageElement(BaseElement):
    """
    画像要素クラス
    
    画像を表示するための要素です。
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
        # デフォルトで画像要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.IMAGE
        
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
        
        # 画像ソースの取得
        src = self.get_property("src", "")
        if not src:
            return f'<div id="{self.element_id}" class="report-image-empty">画像ソースが指定されていません</div>'
        
        # 画像ソースの変数置換
        src = self.replace_variables(src, context)
        
        # 代替テキストの取得
        alt = self.get_property("alt", "")
        alt = self.replace_variables(alt, context)
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # 画像要素のレンダリング
        return f'<div id="{self.element_id}" class="report-image-container" style="{css_style}"><img src="{src}" alt="{alt}" class="report-image"></div>'
