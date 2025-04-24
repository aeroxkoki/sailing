# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.visualizations.basic_charts

基本的なチャートタイプ（折れ線グラフ、散布図、棒グラフ、円グラフ）を提供するモジュールです。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import uuid
import json
import html

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.elements.visualizations.chart_data import ChartData
from sailing_data_processor.reporting.elements.visualizations.chart_renderer import RendererFactory
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class LineChartElement(BaseChartElement):
    """
    折れ線グラフ要素
    
    時系列データやトレンドを表示するための要素です。
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
        
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "line"
        
        # 拡張デフォルトプロパティ
        if model is None:
            # 線のスタイル設定
            if 'line_style' not in kwargs:
                kwargs['line_style'] = "solid"  # solid, dashed, dotted
            
            # マーカー設定
            if 'show_markers' not in kwargs:
                kwargs['show_markers'] = True
                
            # 曲線の張力設定
            if 'tension' not in kwargs:
                kwargs['tension'] = 0.1  # 0=直線, 0.5=緩やかな曲線
                
            # トレンドライン表示
            if 'show_trendline' not in kwargs:
                kwargs['show_trendline'] = False
                
            # デザイン設定
            if 'fill_area' not in kwargs:
                kwargs['fill_area'] = True
                
            # 凡例表示
            if 'show_legend' not in kwargs:
                kwargs['show_legend'] = True
                
            # レンダラー設定
            if 'renderer' not in kwargs:
                kwargs['renderer'] = "chartjs"  # chartjs, plotly
                
            # データラベル表示
            if 'show_data_labels' not in kwargs:
                kwargs['show_data_labels'] = False
                
            # ステップライン設定
            if 'step_line' not in kwargs:
                kwargs['step_line'] = False
        
        super().__init__(model, **kwargs)
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        折れ線グラフのデータを取得
        
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
        chart_data = ChartData().from_context(context, self.data_source)
        
        if chart_data.get_data() is None:
            return {"type": "line", "data": {"labels": [], "datasets": []}}
        
        # データを適切な形式に変換
        x_key = self.get_property("x_field", "x")
        y_key = self.get_property("y_field", "y")
        series_key = self.get_property("series_field", None)
        
        # 折れ線グラフデータに変換
        chart_data.to_line_data(x_key, y_key, series_key)
        
        # 設定を適用
        data = chart_data.get_data()
        chart_type = "line"
        
        # ステップライン設定
        step_line = self.get_property("step_line", False)
        if step_line:
            for dataset in data["datasets"]:
                dataset["steppedLine"] = True
        
        # 線のスタイル設定
        line_style = self.get_property("line_style", "solid")
        for dataset in data["datasets"]:
            if line_style == "dashed":
                dataset["borderDash"] = [5, 5]
            elif line_style == "dotted":
                dataset["borderDash"] = [2, 2]
        
        # マーカー表示設定
        show_markers = self.get_property("show_markers", True)
        for dataset in data["datasets"]:
            if not show_markers:
                dataset["pointRadius"] = 0
                dataset["pointHoverRadius"] = 0
            else:
                dataset["pointRadius"] = 4
                dataset["pointHoverRadius"] = 6
        
        # 曲線の張力設定
        tension = self.get_property("tension", 0.1)
        for dataset in data["datasets"]:
            dataset["tension"] = tension
        
        # 領域塗りつぶし設定
        fill_area = self.get_property("fill_area", True)
        for dataset in data["datasets"]:
            dataset["fill"] = fill_area
        
        # 完全なチャートデータを作成
        return {
            "type": chart_type,
            "data": data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        折れ線グラフのオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # 折れ線グラフ特有のオプション
        line_options = {
            "scales": {
                "x": {
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "")
                    },
                    "grid": {
                        "display": self.get_property("show_x_grid", True),
                        "color": "rgba(0, 0, 0, 0.1)"
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": self.get_property("y_axis_title", "")
                    },
                    "grid": {
                        "display": self.get_property("show_y_grid", True),
                        "color": "rgba(0, 0, 0, 0.1)"
                    },
                    "beginAtZero": self.get_property("begin_at_zero", False)
            },
            "plugins": {
                "legend": {
                    "display": self.get_property("show_legend", True),
                    "position": self.get_property("legend_position", "top")
                },
                "tooltip": {
                    "mode": self.get_property("tooltip_mode", "index"),
                    "intersect": False
            },
            "interaction": {
                "mode": "nearest",
                "axis": "x",
                "intersect": False
            },
            "animation": {
                "duration": self.get_property("animation_duration", 1000)
            },
            "elements": {
                "line": {
                    "tension": self.get_property("tension", 0.1)
        
        # データラベル表示設定
        show_data_labels = self.get_property("show_data_labels", False)
        if show_data_labels:
            line_options["plugins"]["datalabels"] = {
                "display": True,
                "anchor": "end",
                "align": "top",
                "formatter": "function(value) { return value.toFixed(1); }",
                "font": {
                    "weight": "bold"
                },
                "padding": 6
        
        # オプションを結合
        self._merge_options(options, line_options)
        
        return options
    
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
        
        # レンダラータイプの取得
        renderer_type = self.get_property("renderer", "chartjs")
        
        # データとオプションを取得
        chart_data = self.get_chart_data(context)
        chart_options = self.get_chart_options()
        
        # 必要に応じてoptionsをチャートデータに追加
        if "options" not in chart_data:
            chart_data["options"] = chart_options
        
        # ディメンションを取得
        width, height = self.get_chart_dimensions()
        
        # レンダラーを作成
        renderer = RendererFactory.create_renderer(
            renderer_type, 
            self.chart_id, 
            {"plugins": {"datalabels": self.get_property("show_data_labels", False)}}
        )
        
        # チャートをレンダリング
        html_content = renderer.render(chart_data, width, height)
        
        return html_content
    
    def _merge_options(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        オプション辞書を再帰的にマージ
        
        Parameters
        ----------
        target : Dict[str, Any]
            ターゲット辞書
        source : Dict[str, Any]
            ソース辞書
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_options(target[key], value)
            else:
                target[key] = value


class ScatterChartElement(BaseChartElement):
    """
    散布図要素
    
    2次元データポイントを表示するための要素です。
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
        
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "scatter"
        
        # 拡張デフォルトプロパティ
        if model is None:
            # マーカー設定
            if 'point_style' not in kwargs:
                kwargs['point_style'] = "circle"  # circle, cross, star, triangle
            
            # マーカーサイズ設定
            if 'point_radius' not in kwargs:
                kwargs['point_radius'] = 5
                
            # 回帰線表示
            if 'show_regression_line' not in kwargs:
                kwargs['show_regression_line'] = False
                
            # 密度表示
            if 'show_density' not in kwargs:
                kwargs['show_density'] = False
                
            # ズーム有効化
            if 'enable_zoom' not in kwargs:
                kwargs['enable_zoom'] = True
                
            # レンダラー設定
            if 'renderer' not in kwargs:
                kwargs['renderer'] = "chartjs"  # chartjs, plotly
        
        super().__init__(model, **kwargs)
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        散布図のデータを取得
        
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
        chart_data = ChartData().from_context(context, self.data_source)
        
        if chart_data.get_data() is None:
            return {"type": "scatter", "data": {"datasets": []}}
        
        # データを適切な形式に変換
        x_key = self.get_property("x_field", "x")
        y_key = self.get_property("y_field", "y")
        series_key = self.get_property("series_field", None)
        
        # 散布図データに変換
        chart_data.to_scatter_data(x_key, y_key, series_key)
        
        # 設定を適用
        data = chart_data.get_data()
        chart_type = "scatter"
        
        # ポイントスタイル設定
        point_style = self.get_property("point_style", "circle")
        point_radius = self.get_property("point_radius", 5)
        
        for dataset in data["datasets"]:
            dataset["pointStyle"] = point_style
            dataset["radius"] = point_radius
            dataset["hoverRadius"] = point_radius + 2
        
        # 完全なチャートデータを作成
        return {
            "type": chart_type,
            "data": data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        散布図のオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # 散布図特有のオプション
        scatter_options = {
            "scales": {
                "x": {
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "")
                    },
                    "grid": {
                        "display": self.get_property("show_x_grid", True),
                        "color": "rgba(0, 0, 0, 0.1)"
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": self.get_property("y_axis_title", "")
                    },
                    "grid": {
                        "display": self.get_property("show_y_grid", True),
                        "color": "rgba(0, 0, 0, 0.1)"
                    },
                    "beginAtZero": self.get_property("begin_at_zero", False)
            },
            "plugins": {
                "legend": {
                    "display": self.get_property("show_legend", True),
                    "position": self.get_property("legend_position", "top")
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) { return `(${context.parsed.x}, ${context.parsed.y})`; }"
            },
            "animation": {
                "duration": self.get_property("animation_duration", 1000)
        
        # ズーム有効化
        enable_zoom = self.get_property("enable_zoom", True)
        if enable_zoom and self.get_property("renderer", "chartjs") == "chartjs":
            scatter_options["plugins"]["zoom"] = {
                "pan": {
                    "enabled": True,
                    "mode": "xy"
                },
                "zoom": {
                    "wheel": {
                        "enabled": True
                    },
                    "pinch": {
                        "enabled": True
                    },
                    "mode": "xy"
        
        # オプションを結合
        self._merge_options(options, scatter_options)
        
        return options
    
    def get_required_libraries(self) -> List[str]:
        """
        必要なライブラリのURLリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        libraries = super().get_required_libraries()
        
        # ズーム機能が有効な場合は、ズームプラグインを追加
        if self.get_property("enable_zoom", True) and self.get_property("renderer", "chartjs") == "chartjs":
            libraries.append("https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@1.2.1/dist/chartjs-plugin-zoom.min.js")
        
        # 回帰線表示が有効な場合は、回帰プラグインを追加
        if self.get_property("show_regression_line", False) and self.get_property("renderer", "chartjs") == "chartjs":
            libraries.append("https://cdn.jsdelivr.net/npm/chartjs-plugin-regression@0.2.1/dist/chartjs-plugin-regression.min.js")
        
        return libraries
    
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
        
        # レンダラータイプの取得
        renderer_type = self.get_property("renderer", "chartjs")
        
        # データとオプションを取得
        chart_data = self.get_chart_data(context)
        chart_options = self.get_chart_options()
        
        # 必要に応じてoptionsをチャートデータに追加
        if "options" not in chart_data:
            chart_data["options"] = chart_options
        
        # 回帰線表示が有効な場合は設定を追加
        show_regression_line = self.get_property("show_regression_line", False)
        if show_regression_line and renderer_type == "chartjs":
            for dataset in chart_data["data"]["datasets"]:
                dataset["trendlineLinear"] = {
                    "style": dataset["borderColor"].replace("0.7", "1"),
                    "width": 2,
                    "lineStyle": "dotted",
                    "projection": self.get_property("regression_projection", False)
        
        # ディメンションを取得
        width, height = self.get_chart_dimensions()
        
        # レンダラーを作成
        renderer = RendererFactory.create_renderer(
            renderer_type, 
            self.chart_id, 
            {
                "plugins": {
                    "zoom": self.get_property("enable_zoom", True),
                    "regression": self.get_property("show_regression_line", False)
        )
        
        # チャートをレンダリング
        html_content = renderer.render(chart_data, width, height)
        
        return html_content
    
    def _merge_options(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        オプション辞書を再帰的にマージ
        
        Parameters
        ----------
        target : Dict[str, Any]
            ターゲット辞書
        source : Dict[str, Any]
            ソース辞書
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_options(target[key], value)
            else:
                target[key] = value


class BarChartElement(BaseChartElement):
    """
    棒グラフ要素
    
    カテゴリデータを棒グラフで表示するための要素です。
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
        
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "bar"
        
        # 拡張デフォルトプロパティ
        if model is None:
            # 棒の方向設定
            if 'horizontal' not in kwargs:
                kwargs['horizontal'] = False
                
            # 棒グラフタイプ設定
            if 'bar_type' not in kwargs:
                kwargs['bar_type'] = "default"  # default, stacked, percent
                
            # 棒の幅設定
            if 'bar_thickness' not in kwargs:
                kwargs['bar_thickness'] = "auto"  # auto, または数値
                
            # 棒の間隔設定
            if 'bar_space' not in kwargs:
                kwargs['bar_space'] = 0.1  # 0.0-1.0
                
            # 値ラベル表示
            if 'show_data_labels' not in kwargs:
                kwargs['show_data_labels'] = False
                
            # 棒の角の丸み設定
            if 'bar_border_radius' not in kwargs:
                kwargs['bar_border_radius'] = 0
                
            # ソート設定
            if 'sort_data' not in kwargs:
                kwargs['sort_data'] = "none"  # none, asc, desc
                
            # レンダラー設定
            if 'renderer' not in kwargs:
                kwargs['renderer'] = "chartjs"  # chartjs, plotly
        
        super().__init__(model, **kwargs)
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        棒グラフのデータを取得
        
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
        chart_data = ChartData().from_context(context, self.data_source)
        
        if chart_data.get_data() is None:
            return {"type": "bar", "data": {"labels": [], "datasets": []}}
        
        # データを適切な形式に変換
        label_key = self.get_property("label_field", "label")
        value_key = self.get_property("value_field", "value")
        series_key = self.get_property("series_field", None)
        
        # ソート設定
        sort_data = self.get_property("sort_data", "none")
        if sort_data != "none" and isinstance(chart_data.get_data(), list):
            reverse = sort_data == "desc"
            chart_data.sort(value_key, reverse=reverse)
        
        # 棒グラフデータに変換
        chart_data.to_bar_data(label_key, value_key, series_key)
        
        # 設定を適用
        data = chart_data.get_data()
        chart_type = "bar"
        
        # 水平棒グラフの場合
        horizontal = self.get_property("horizontal", False)
        if horizontal:
            chart_type = "horizontalBar"
        
        # 棒の厚さ設定
        bar_thickness = self.get_property("bar_thickness", "auto")
        if bar_thickness != "auto":
            for dataset in data["datasets"]:
                dataset["barThickness"] = int(bar_thickness)
        
        # 棒の間隔設定
        bar_space = self.get_property("bar_space", 0.1)
        for dataset in data["datasets"]:
            dataset["barPercentage"] = 1.0 - bar_space
        
        # 棒の角の丸み設定
        bar_border_radius = self.get_property("bar_border_radius", 0)
        if bar_border_radius > 0:
            for dataset in data["datasets"]:
                dataset["borderRadius"] = bar_border_radius
        
        # 完全なチャートデータを作成
        return {
            "type": chart_type,
            "data": data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        棒グラフのオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # 棒グラフ特有のオプション
        bar_options = {
            "scales": {
                "x": {
                    "title": {
                        "display": True,
                        "text": self.get_property("x_axis_title", "")
                    },
                    "grid": {
                        "display": self.get_property("show_x_grid", True),
                        "color": "rgba(0, 0, 0, 0.1)"
                },
                "y": {
                    "title": {
                        "display": True,
                        "text": self.get_property("y_axis_title", "")
                    },
                    "grid": {
                        "display": self.get_property("show_y_grid", True),
                        "color": "rgba(0, 0, 0, 0.1)"
                    },
                    "beginAtZero": True
            },
            "plugins": {
                "legend": {
                    "display": self.get_property("show_legend", True),
                    "position": self.get_property("legend_position", "top")
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False
            },
            "animation": {
                "duration": self.get_property("animation_duration", 1000)
        
        # 横棒グラフの場合、x軸とy軸の設定を入れ替え
        horizontal = self.get_property("horizontal", False)
        if horizontal:
            x_settings = bar_options["scales"]["x"]
            y_settings = bar_options["scales"]["y"]
            bar_options["scales"]["x"] = y_settings
            bar_options["scales"]["y"] = x_settings
        
        # 積み上げ棒グラフの場合の設定
        bar_type = self.get_property("bar_type", "default")
        if bar_type == "stacked" or bar_type == "percent":
            stacked_axis = "y" if not horizontal else "x"
            percent_axis = bar_type == "percent"
            
            bar_options["scales"]["x"]["stacked"] = True
            bar_options["scales"]["y"]["stacked"] = True
            
            if percent_axis:
                stacked_key = stacked_axis
                bar_options["scales"][stacked_key]["min"] = 0
                bar_options["scales"][stacked_key]["max"] = 100
                bar_options["scales"][stacked_key]["ticks"] = {
                    "callback": "function(value) { return value + '%'; }"
        
        # データラベル表示設定
        show_data_labels = self.get_property("show_data_labels", False)
        if show_data_labels:
            bar_options["plugins"]["datalabels"] = {
                "display": True,
                "anchor": "end",
                "align": "top",
                "formatter": "function(value) { return value.toFixed(1); }",
                "font": {
                    "weight": "bold"
                },
                "padding": 6
        
        # オプションを結合
        self._merge_options(options, bar_options)
        
        return options
    
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
        
        # レンダラータイプの取得
        renderer_type = self.get_property("renderer", "chartjs")
        
        # データとオプションを取得
        chart_data = self.get_chart_data(context)
        chart_options = self.get_chart_options()
        
        # 必要に応じてoptionsをチャートデータに追加
        if "options" not in chart_data:
            chart_data["options"] = chart_options
        
        # ディメンションを取得
        width, height = self.get_chart_dimensions()
        
        # レンダラーを作成
        renderer = RendererFactory.create_renderer(
            renderer_type, 
            self.chart_id, 
            {"plugins": {"datalabels": self.get_property("show_data_labels", False)}}
        )
        
        # チャートをレンダリング
        html_content = renderer.render(chart_data, width, height)
        
        return html_content
    
    def _merge_options(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        オプション辞書を再帰的にマージ
        
        Parameters
        ----------
        target : Dict[str, Any]
            ターゲット辞書
        source : Dict[str, Any]
            ソース辞書
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_options(target[key], value)
            else:
                target[key] = value


class PieChartElement(BaseChartElement):
    """
    円グラフ要素
    
    比率や割合を円グラフで表示するための要素です。
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
        
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "pie"
        
        # 拡張デフォルトプロパティ
        if model is None:
            # 円グラフタイプ設定
            if 'pie_type' not in kwargs:
                kwargs['pie_type'] = "pie"  # pie, doughnut
                
            # 切り離し設定
            if 'explode_segments' not in kwargs:
                kwargs['explode_segments'] = []
                
            # 開始角度設定
            if 'start_angle' not in kwargs:
                kwargs['start_angle'] = -90  # 度数法（上から時計回り）
                
            # 回転方向設定
            if 'counter_clockwise' not in kwargs:
                kwargs['counter_clockwise'] = False
                
            # ラベル表示
            if 'show_labels' not in kwargs:
                kwargs['show_labels'] = True
                
            # パーセント表示
            if 'show_percentages' not in kwargs:
                kwargs['show_percentages'] = True
                
            # 値表示
            if 'show_values' not in kwargs:
                kwargs['show_values'] = False
                
            # レンダラー設定
            if 'renderer' not in kwargs:
                kwargs['renderer'] = "chartjs"  # chartjs, plotly
        
        super().__init__(model, **kwargs)
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        円グラフのデータを取得
        
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
        chart_data = ChartData().from_context(context, self.data_source)
        
        if chart_data.get_data() is None:
            return {"type": "pie", "data": {"labels": [], "datasets": [{"data": []}]}}
        
        # データを適切な形式に変換
        label_key = self.get_property("label_field", "label")
        value_key = self.get_property("value_field", "value")
        
        # 円グラフデータに変換
        chart_data.to_pie_data(label_key, value_key)
        
        # 設定を適用
        data = chart_data.get_data()
        
        # 円グラフタイプを設定
        pie_type = self.get_property("pie_type", "pie")
        chart_type = pie_type  # pie または doughnut
        
        # 切り離し設定
        explode_segments = self.get_property("explode_segments", [])
        if explode_segments and len(explode_segments) > 0 and len(data["labels"]) > 0:
            offsets = []
            for label in data["labels"]:
                offset = 0
                if label in explode_segments:
                    offset = 0.1
                offsets.append(offset)
            
            if len(data["datasets"]) > 0:
                data["datasets"][0]["offset"] = offsets
        
        # 完全なチャートデータを作成
        return {
            "type": chart_type,
            "data": data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        円グラフのオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # 開始角度設定
        start_angle = self.get_property("start_angle", -90)
        counter_clockwise = self.get_property("counter_clockwise", False)
        
        # 円グラフ特有のオプション
        pie_options = {
            "plugins": {
                "legend": {
                    "display": self.get_property("show_legend", True),
                    "position": self.get_property("legend_position", "top")
                },
                "tooltip": {
                    "callbacks": {
                        "label": "function(context) { " +
                                "var dataset = context.dataset; " +
                                "var total = dataset.data.reduce((sum, value) => sum + value, 0); " +
                                "var value = dataset.data[context.dataIndex]; " +
                                "var percentage = Math.round((value / total) * 100); " +
                                "return ' ' + context.label + ': ' + value + ' (' + percentage + '%)'; " +
                                "}"
            },
            "rotation": (start_angle * 3.14159) / 180,
            "circumference": -2 * 3.14159 if counter_clockwise else 2 * 3.14159,
            "animation": {
                "duration": self.get_property("animation_duration", 1000),
                "animateRotate": True,
                "animateScale": self.get_property("animate_scale", True)
        
        # ドーナツグラフの場合
        if self.get_property("pie_type", "pie") == "doughnut":
            pie_options["cutout"] = str(self.get_property("cutout_percentage", 50)) + "%"
        
        # ラベル表示設定
        show_labels = self.get_property("show_labels", True)
        show_percentages = self.get_property("show_percentages", True)
        show_values = self.get_property("show_values", False)
        
        if show_labels:
            pie_options["plugins"]["datalabels"] = {
                "display": True,
                "color": "#fff",
                "font": {
                    "weight": "bold"
                },
                "formatter": "function(value, context) { " +
                            "var label = context.chart.data.labels[context.dataIndex]; " +
                            "var dataset = context.chart.data.datasets[context.datasetIndex]; " +
                            "var total = dataset.data.reduce(function(sum, val) { return sum + val; }, 0); " +
                            "var percentage = Math.round((value / total) * 100); " +
                            "var result = ''; " +
                            f"var showLabels = {str(show_labels).lower()}; " +
                            f"var showValues = {str(show_values).lower()}; " +
                            f"var showPercentages = {str(show_percentages).lower()}; " +
                            "if (showLabels) { result += label; } " +
                            "if (showValues) { if (result) result += ': '; result += value; } " +
                            "if (showPercentages) { if (result) result += ' '; result += '(' + percentage + '%)'; } " +
                            "return result; " +
                            "}"
        
        # オプションを結合
        self._merge_options(options, pie_options)
        
        return options
    
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
        
        # レンダラータイプの取得
        renderer_type = self.get_property("renderer", "chartjs")
        
        # データとオプションを取得
        chart_data = self.get_chart_data(context)
        chart_options = self.get_chart_options()
        
        # 必要に応じてoptionsをチャートデータに追加
        if "options" not in chart_data:
            chart_data["options"] = chart_options
        
        # ディメンションを取得
        width, height = self.get_chart_dimensions()
        
        # レンダラーを作成
        renderer = RendererFactory.create_renderer(
            renderer_type, 
            self.chart_id, 
            {"plugins": {"datalabels": self.get_property("show_labels", True)}}
        )
        
        # チャートをレンダリング
        html_content = renderer.render(chart_data, width, height)
        
        return html_content
    
    def _merge_options(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        オプション辞書を再帰的にマージ
        
        Parameters
        ----------
        target : Dict[str, Any]
            ターゲット辞書
        source : Dict[str, Any]
            ソース辞書
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_options(target[key], value)
            else:
                target[key] = value

