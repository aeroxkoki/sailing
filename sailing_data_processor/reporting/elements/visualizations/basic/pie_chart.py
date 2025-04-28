"""
sailing_data_processor.reporting.elements.visualizations.basic.pie_chart

円グラフ要素を提供するモジュールです。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import uuid
import json
import html

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.elements.visualizations.chart_data import ChartData
from sailing_data_processor.reporting.elements.visualizations.chart_renderer import RendererFactory
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


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
        }
    
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
                    }
                }
            },
            "rotation": (start_angle * 3.14159) / 180,
            "circumference": -2 * 3.14159 if counter_clockwise else 2 * 3.14159,
            "animation": {
                "duration": self.get_property("animation_duration", 1000),
                "animateRotate": True,
                "animateScale": self.get_property("animate_scale", True)
            }
        }
        
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
            }
        
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
