"""
sailing_data_processor.reporting.elements.visualizations.basic.bar_chart

棒グラフ要素を提供するモジュールです。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import uuid
import json
import html

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.elements.visualizations.chart_data import ChartData
from sailing_data_processor.reporting.elements.visualizations.chart_renderer import RendererFactory
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


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
        }
    
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
                    }
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
                }
            },
            "plugins": {
                "legend": {
                    "display": self.get_property("show_legend", True),
                    "position": self.get_property("legend_position", "top")
                },
                "tooltip": {
                    "mode": "index",
                    "intersect": False
                }
            },
            "animation": {
                "duration": self.get_property("animation_duration", 1000)
            }
        }
        
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
                }
        
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
            }
        
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
