"""
sailing_data_processor.reporting.elements.visualizations.basic.line_chart

折れ線グラフ要素を提供するモジュールです。
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
        }
    
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
                    "beginAtZero": self.get_property("begin_at_zero", False)
                }
            },
            "plugins": {
                "legend": {
                    "display": self.get_property("show_legend", True),
                    "position": self.get_property("legend_position", "top")
                },
                "tooltip": {
                    "mode": self.get_property("tooltip_mode", "index"),
                    "intersect": False
                }
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
                }
            }
        }
        
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
            }
        
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
