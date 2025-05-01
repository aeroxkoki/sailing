# -*- coding: utf-8 -*-
"""
Module for enhanced sailing chart visualizations.
This module provides enhanced chart elements for sailing data visualization.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
import math
import numpy as np

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.elements.visualizations.sailing_charts import (
    WindRoseElement,
    CoursePerformanceElement,
    TackingAngleElement,
    StrategyPointMapElement
)
from sailing_data_processor.reporting.elements.visualizations.chart_renderer import RendererFactory
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class EnhancedWindRoseElement(WindRoseElement):
    """
    拡張版風配図（Wind Rose）要素
    
    風向風速データを表示するための拡張された風配図。
    複数のレンダラー（ChartJS, Plotly）に対応し、詳細な設定が可能。
    
    機能：
    - 角度分割数の調整 (8/16/32/36分割)
    - 風速カテゴリの詳細設定
    - レンダラー選択と単位（knot、m/s、km/h）の設定
    - 詳細な表示オプションの設定
    - 3D表示機能（Plotlyレンダラー使用時）
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        **kwargs : dict
            追加のプロパティ（キーと値のペア）
        """
        # レンダラーの初期設定
        if model is None and 'renderer' not in kwargs:
            kwargs['renderer'] = "chartjs"  # chartjs, plotly
        
        # 角度分割数の初期設定
        if model is None and 'angle_divisions' not in kwargs:
            kwargs['angle_divisions'] = 16  # 8, 16, 32, 36から選択
            
        # 風速カテゴリの初期設定
        if model is None and 'wind_speed_categories' not in kwargs:
            kwargs['wind_speed_categories'] = [
                {"min": 0, "max": 5, "label": "弱風 (0-5kt)"},
                {"min": 5, "max": 10, "label": "軽風 (5-10kt)"},
                {"min": 10, "max": 15, "label": "中風 (10-15kt)"},
                {"min": 15, "max": 20, "label": "強風 (15-20kt)"},
                {"min": 20, "max": float('inf'), "label": "暴風 (20kt+)"}
            ]
            
        # 単位の初期設定
        if model is None and 'display_unit' not in kwargs:
            kwargs['display_unit'] = "knots"  # knots, m/s, km/h
            
        # 3D表示設定の初期設定（Plotlyレンダラー用）
        if model is None and 'enable_3d' not in kwargs:
            kwargs['enable_3d'] = False
            
        # 集計方法の初期設定
        if model is None and 'aggregation_method' not in kwargs:
            kwargs['aggregation_method'] = "frequency"  # frequency, speed_avg, speed_max
        
        super().__init__(model, **kwargs)
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        風配図のデータを取得
        
        Parameters
        ----------
        context : Dict[str, Any]
            コンテキスト
            
        Returns
        -------
        Dict[str, Any]
            チャートデータ
        """
        # 親クラスのデータ取得処理を呼び出す
        chart_data = super().get_chart_data(context)
        
        # レンダラータイプの取得
        renderer_type = self.get_property("renderer", "chartjs")
        
        # Plotlyレンダラーを使用し、3D表示が有効な場合
        if renderer_type == "plotly" and self.get_property("enable_3d", False):
            # データソースからデータを再取得
            data = None
            if self.data_source and self.data_source in context:
                data = context[self.data_source]
            
            # データがない場合は空のデータを返す
            if not data:
                return {"type": "polar", "data": {"r": [], "theta": [], "type": "barpolar"}}
            
            # 角度分割数の取得
            angle_divisions = self.get_property("angle_divisions", 16)
            
            # 方位と風速データの取得と前処理
            directions = []
            speeds = []
            
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                direction_key = self.get_property("direction_key", "direction")
                speed_key = self.get_property("speed_key", "speed")
                
                for item in data:
                    if direction_key in item and speed_key in item:
                        directions.append(item[direction_key])
                        speeds.append(item[speed_key])
            
            # 単位変換
            display_unit = self.get_property("display_unit", "knots")
            if display_unit == "m/s":
                speeds = [speed * 0.514444 for speed in speeds]  # ノットからm/sに変換
            elif display_unit == "km/h":
                speeds = [speed * 1.852 for speed in speeds]  # ノットからkm/hに変換
            
            # 方位角とビン（区間）の設定
            bin_size = 360 / angle_divisions
            angle_bins = [i * bin_size for i in range(angle_divisions)]
            
            # 風速カテゴリの取得
            wind_speed_categories = self.get_property("wind_speed_categories", [
                {"min": 0, "max": 5, "label": "弱風 (0-5kt)"},
                {"min": 5, "max": 10, "label": "軽風 (5-10kt)"},
                {"min": 10, "max": 15, "label": "中風 (10-15kt)"},
                {"min": 15, "max": 20, "label": "強風 (15-20kt)"},
                {"min": 20, "max": float('inf'), "label": "暴風 (20kt+)"}
            ])
            
            # 3D風配図用のデータ構造を作成
            plotly_data = []
            
            for category in wind_speed_categories:
                min_speed = category["min"]
                max_speed = category["max"]
                label = category["label"]
                
                # このカテゴリに該当する風のデータのみを抽出
                category_directions = []
                category_speeds = []
                
                for direction, speed in zip(directions, speeds):
                    if min_speed <= speed < max_speed:
                        category_directions.append(direction)
                        category_speeds.append(speed)
                
                # 方位角ビンごとに集計
                r_values = [0] * angle_divisions
                
                for direction in category_directions:
                    bin_idx = int(direction / bin_size) % angle_divisions
                    r_values[bin_idx] += 1
                
                # カテゴリごとにデータセットを追加
                plotly_data.append({
                    "type": "barpolar",
                    "r": r_values,
                    "theta": angle_bins,
                    "name": label,
                    "marker": {"line": {"color": "white", "width": 0.5}},
                    "opacity": 0.8
                })
            
            # 集計方法を取得
            aggregation_method = self.get_property("aggregation_method", "frequency")
            title_text = f"風配図 - 集計方法: {self._get_aggregation_method_display(aggregation_method)}"
            
            # Plotly用のレイアウト設定
            layout = {
                "title": {"text": title_text, "font": {"size": 12}},
                "legend": {"font": {"size": 10}, "orientation": "h", "y": -0.1},
                "polar": {
                    "radialaxis": {"ticksuffix": "%" if aggregation_method == "frequency" else ""},
                    "angularaxis": {"direction": "clockwise", "period": 360}
                },
                "margin": {"t": 100, "b": 100}
            }
            
            # 3D風配図データを返す
            return {
                "data": plotly_data,
                "layout": layout,
                "config": {"responsive": True}
            }
        
        # それ以外の場合（標準の風配図）
        return chart_data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        風配図のオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # 表示単位を取得
        display_unit = self.get_property("display_unit", "knots")
        unit_suffix = self._get_unit_suffix(display_unit)
        
        # 集計方法を取得
        aggregation_method = self.get_property("aggregation_method", "frequency")
        
        # 風配図特有のオプションを追加
        additional_options = {
            "plugins": {
                "tooltip": {
                    "callbacks": {
                        "label": f"function(context) {{ return context.label + ': ' + context.raw.toFixed(1) + '{unit_suffix}'; }}"
                    }
                },
                "scale": {
                    "ticks": {
                        "callback": f"function(value) {{ return value + '{unit_suffix}'; }}"
                    }
                }
            }
        }
        
        # 詳細表示が有効な場合の追加設定
        if self.get_property("show_details", True):
            additional_options["plugins"]["tooltip"]["callbacks"] = {
                "title": "function(context) { return context[0].label; }",
                "label": f"function(context) {{ var dataIndex = context.dataIndex; var value = context.raw; " +
                         f"return [" +
                         f"'値: ' + value.toFixed(1) + '{unit_suffix}'," +
                         f"'全体に対する割合: ' + (value / context.chart.data.datasets[0].data.reduce((a,b) => a + b, 0) * 100).toFixed(1) + '%'" +
                         f"]; }}"
            }
        
        # オプションを結合
        self._merge_options(options, additional_options)
        
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
        
        # レンダラータイプの取得（デフォルトはChartJS）
        renderer_type = self.get_property("renderer", "chartjs")
        
        # データとオプションを取得
        chart_data = self.get_chart_data(context)
        chart_options = self.get_chart_options()
        
        # データがない場合
        if not chart_data or ((not chart_data.get("data") and renderer_type != "plotly") or 
                             (renderer_type == "plotly" and len(chart_data.get("data", [])) == 0)):
            return f'<div id="{self.element_id}" class="report-chart-empty">チャートデータがありません</div>'
        
        # 必要に応じてoptionsをチャートデータに追加
        if "options" not in chart_data and renderer_type != "plotly":
            chart_data["options"] = chart_options
        
        # ディメンションを取得
        width, height = self.get_chart_dimensions()
        
        # データラベル表示設定
        show_labels = self.get_property("show_labels", False)
        
        # Plotlyレンダラーを使用し、3D表示が有効な場合はレンダラーオプションを変更
        renderer_options = {"plugins": {"datalabels": show_labels}}
        if renderer_type == "plotly" and self.get_property("enable_3d", False):
            renderer_options["mode"] = "3d"
        
        # レンダラーを作成
        renderer = RendererFactory.create_renderer(
            renderer_type, 
            self.chart_id, 
            renderer_options
        )
        
        # チャートをレンダリング
        html_content = renderer.render(chart_data, width, height)
        
        return html_content
    
    def _get_unit_suffix(self, unit: str) -> str:
        """
        単位に応じたサフィックスを取得
        
        Parameters
        ----------
        unit : str
            単位名 ("knots", "m/s", "km/h")
            
        Returns
        -------
        str
            単位サフィックス
        """
        if unit == "knots":
            return " kt"
        elif unit == "m/s":
            return " m/s"
        elif unit == "km/h":
            return " km/h"
        else:
            return ""
    
    def _get_aggregation_method_display(self, method: str) -> str:
        """
        集計方法の表示名を取得
        
        Parameters
        ----------
        method : str
            集計方法名
            
        Returns
        -------
        str
            表示名
        """
        if method == "frequency":
            return "頻度"
        elif method == "speed_avg":
            return "平均風速"
        elif method == "speed_max":
            return "最大風速"
        else:
            return method
