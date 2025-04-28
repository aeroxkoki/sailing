"""
sailing_data_processor.reporting.elements.visualizations.basic.scatter_chart

散布図要素を提供するモジュールです。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import uuid
import json
import html

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.elements.visualizations.chart_data import ChartData
from sailing_data_processor.reporting.elements.visualizations.chart_renderer import RendererFactory
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


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
        }
    
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
                    "callbacks": {
                        "label": "function(context) { return `(${context.parsed.x}, ${context.parsed.y})`; }"
                    }
                }
            },
            "animation": {
                "duration": self.get_property("animation_duration", 1000)
            }
        }
        
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
                }
            }
        
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
                }
        
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
                }
            }
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
