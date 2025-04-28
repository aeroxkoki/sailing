# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
import uuid

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class BaseChartElement(BaseElement):
    """
    可視化要素の基底クラス
    
    すべての可視化要素に共通する機能を提供します。
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
        
        # 一意なチャートIDを生成
        self.chart_id = f"chart_{self.element_id}_{str(uuid.uuid4())[:8]}"
    
    @property
    def data_source(self) -> str:
        """
        データソース名を取得
        
        Returns
        -------
        str
            データソース名
        """
        return self.get_property("data_source", "")
    
    @data_source.setter
    def data_source(self, value: str) -> None:
        """
        データソース名を設定
        
        Parameters
        ----------
        value : str
            データソース名
        """
        self.set_property("data_source", value)
    
    @property
    def title(self) -> str:
        """
        タイトルを取得
        
        Returns
        -------
        str
            タイトル
        """
        return self.get_property("title", "")
    
    @title.setter
    def title(self, value: str) -> None:
        """
        タイトルを設定
        
        Parameters
        ----------
        value : str
            タイトル
        """
        self.set_property("title", value)
    
    @property
    def chart_type(self) -> str:
        """
        チャートタイプを取得
        
        Returns
        -------
        str
            チャートタイプ
        """
        return self.get_property("chart_type", "line")
    
    @chart_type.setter
    def chart_type(self, value: str) -> None:
        """
        チャートタイプを設定
        
        Parameters
        ----------
        value : str
            チャートタイプ
        """
        self.set_property("chart_type", value)
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        チャートのデータを取得
        
        コンテキストからデータを取得し、必要な形式に変換します。
        サブクラスでオーバーライドして特定のチャートタイプに対応したデータを提供します。
        
        Parameters
        ----------
        context : Dict[str, Any]
            コンテキスト
            
        Returns
        -------
        Dict[str, Any]
            チャートデータ
        """
        # データソースからデータを取得
        data = None
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        # データがない場合は空のデータを返す
        if not data:
            return {"type": self.chart_type, "data": {}}
        
        # 基本的なチャートデータ
        return {
            "type": self.chart_type,
            "data": data,
            "options": {
                "title": {
                    "display": bool(self.title),
                    "text": self.title
                },
                "responsive": True,
                "maintainAspectRatio": False
            }
        }
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        チャートのオプションを取得
        
        スタイルや振る舞いを制御するオプションを取得します。
        サブクラスでオーバーライドして特定のチャートタイプに対応したオプションを提供します。
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        # 基本的なチャートオプション
        options = {
            "title": {
                "display": bool(self.title),
                "text": self.title
            },
            "responsive": True,
            "maintainAspectRatio": False,
            "animation": {
                "duration": 1000,
                "easing": "easeOutQuart"
            },
            "plugins": {
                "legend": {
                    "display": True,
                    "position": "top"
                },
                "tooltip": {
                    "enabled": True,
                    "mode": "index",
                    "intersect": False
                }
            }
        }
        
        # ユーザー定義のオプションを追加
        user_options = self.get_property("options", {})
        
        # 再帰的にオプションをマージ
        def merge_options(target, source):
            for key, value in source.items():
                if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                    merge_options(target[key], value)
                else:
                    target[key] = value
        
        merge_options(options, user_options)
        
        return options
    
    def get_chart_libraries(self) -> List[str]:
        """
        チャートの描画に必要なライブラリのリストを取得
        
        サブクラスでオーバーライドして特定のライブラリを追加できます。
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        return [
            "https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"
        ]
    
    def get_chart_initialization_code(self, config_var: str = "config") -> str:
        """
        チャート初期化用のJavaScriptコードを取得
        
        Parameters
        ----------
        config_var : str, optional
            設定変数名, by default "config"
            
        Returns
        -------
        str
            初期化コード
        """
        return f"""
            var ctx = document.getElementById('{self.chart_id}').getContext('2d');
            new Chart(ctx, {config_var});
        """
    
    def get_chart_dimensions(self) -> Tuple[str, str]:
        """
        チャートの寸法を取得
        
        Returns
        -------
        Tuple[str, str]
            幅と高さ (width, height) のCSS値のタプル
        """
        width = self.get_style("width", "100%")
        height = self.get_style("height", "400px")
        return width, height
    
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
        
        # データを取得
        chart_data = self.get_chart_data(context)
        
        # データがない場合
        if not chart_data or not chart_data.get("data"):
            return f'<div id="{self.element_id}" class="report-chart-empty">チャートデータがありません</div>'
        
        # チャートオプションをマージ
        chart_data["options"] = self.get_chart_options()
        
        # チャート設定をJSONにシリアライズ
        chart_config_json = json.dumps(chart_data)
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # 必要なライブラリの取得
        libraries = self.get_chart_libraries()
        library_tags = "\n".join([f'<script src="{lib}"></script>' for lib in libraries])
        
        # 初期化コード
        init_code = self.get_chart_initialization_code()
        
        # チャート要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-chart-container" style="{css_style}">
            <div class="report-chart-wrapper" style="width: {width}; height: {height};">
                <canvas id="{self.chart_id}" class="report-chart"></canvas>
            </div>
            
            <!-- Chart.js ライブラリ -->
            {library_tags}
            
            <script>
                (function() {{
                    // チャート設定
                    var config = {chart_config_json};
                    
                    // チャート初期化
                    window.addEventListener('load', function() {{
                        {init_code}
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content