"""
sailing_data_processor.reporting.elements.visualizations.enhanced_sailing_charts

セーリング分析に特化したチャート要素の拡張バージョンを提供するモジュールです。
新しいチャートレンダラーを活用して、より柔軟な可視化を実現します。
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
    
    新しいチャートレンダラーを活用した風配図要素です。
    複数のレンダラー（ChartJS, Plotly）に対応し、より柔軟な可視化を実現します。
    
    拡張機能:
    - よりきめ細かな方位分割 (8/16/32/36分割など)
    - カスタマイズ可能な風速カテゴリの範囲設定
    - 複数の表示単位（ノット、m/s、km/h）のサポート
    - 時間範囲に基づくデータフィルタリング
    - 3D表示モード（Plotlyレンダラーを使用時）
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
        # レンダラー設定
        if model is None and 'renderer' not in kwargs:
            kwargs['renderer'] = "chartjs"  # chartjs, plotly
        
        # きめ細かな方位分割のデフォルト設定
        if model is None and 'angle_divisions' not in kwargs:
            kwargs['angle_divisions'] = 16  # 8, 16, 32, 36から選択可能
            
        # 風速カテゴリ範囲のデフォルト設定
        if model is None and 'wind_speed_categories' not in kwargs:
            kwargs['wind_speed_categories'] = [
                {"min": 0, "max": 5, "label": "弱風 (0-5kt)"},
                {"min": 5, "max": 10, "label": "軽風 (5-10kt)"},
                {"min": 10, "max": 15, "label": "中風 (10-15kt)"},
                {"min": 15, "max": 20, "label": "強風 (15-20kt)"},
                {"min": 20, "max": float('inf'), "label": "暴風 (20kt+)"}
            ]
            
        # 表示単位のデフォルト設定
        if model is None and 'display_unit' not in kwargs:
            kwargs['display_unit'] = "knots"  # knots, m/s, km/h
            
        # 3D表示モードのデフォルト設定（Plotlyレンダラーでのみ有効）
        if model is None and 'enable_3d' not in kwargs:
            kwargs['enable_3d'] = False
            
        # 集計方法のデフォルト設定
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
                "title": title_text,
                "font": {"size": 12},
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
                }
            },
            "scale": {
                "ticks": {
                    "callback": f"function(value) {{ return value + '{unit_suffix}'; }}"
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


class EnhancedCoursePerformanceElement(CoursePerformanceElement):
    """
    拡張版コースパフォーマンスグラフ要素
    
    新しいチャートレンダラーを活用したコースパフォーマンスグラフ要素です。
    複数のレンダラー（ChartJS, Plotly）に対応し、より柔軟な可視化を実現します。
    
    拡張機能:
    - 複数風速の同時表示とフィルタリング
    - VMG（Velocity Made Good）最適化分析
    - ボートポーラーの動的参照と比較
    - カスタマイズ可能な角度範囲と表示設定
    - インタラクティブなデータポイント選択
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
        # レンダラー設定
        if model is None and 'renderer' not in kwargs:
            kwargs['renderer'] = "chartjs"  # chartjs, plotly
        
        # 複数風速表示のデフォルト設定
        if model is None and 'show_multiple_wind_speeds' not in kwargs:
            kwargs['show_multiple_wind_speeds'] = False
            
        # VMG最適化分析のデフォルト設定
        if model is None and 'show_vmg_optimization' not in kwargs:
            kwargs['show_vmg_optimization'] = False
            
        # ボートポーラーの動的参照のデフォルト設定
        if model is None and 'dynamic_polar_reference' not in kwargs:
            kwargs['dynamic_polar_reference'] = None
            
        # 表示風速のデフォルト設定
        if model is None and 'wind_speed_filter' not in kwargs:
            kwargs['wind_speed_filter'] = None
            
        # インタラクティブ選択のデフォルト設定
        if model is None and 'enable_interactive_selection' not in kwargs:
            kwargs['enable_interactive_selection'] = True
            
        super().__init__(model, **kwargs)
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        コースパフォーマンスのデータを取得
        
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
        
        # データソースからデータを再取得
        data = None
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        # データがない場合は親クラスのデータを返す
        if not data:
            return chart_data
        
        # レンダラータイプの取得
        renderer_type = self.get_property("renderer", "chartjs")
        
        # 複数風速表示が有効で、データが適切な形式の場合
        show_multiple_wind_speeds = self.get_property("show_multiple_wind_speeds", False)
        if show_multiple_wind_speeds and isinstance(data, dict) and "wind_speeds" in data:
            wind_speeds = data["wind_speeds"]
            
            # 複数風速のデータセットを作成
            if renderer_type == "plotly":
                # Plotly用のデータ構造
                plotly_data = []
                
                for wind_speed, speed_data in wind_speeds.items():
                    # 風速フィルタが設定されている場合は該当する風速のみ表示
                    wind_speed_filter = self.get_property("wind_speed_filter", None)
                    if wind_speed_filter is not None and float(wind_speed) != float(wind_speed_filter):
                        continue
                    
                    if "angles" in speed_data and "speeds" in speed_data:
                        angles = speed_data["angles"]
                        speeds = speed_data["speeds"]
                        
                        # データセットを追加
                        plotly_data.append({
                            "type": "scatterpolar",
                            "r": speeds,
                            "theta": angles,
                            "name": f"{wind_speed} kt",
                            "mode": "lines+markers",
                            "fill": "toself"
                        })
                
                # レイアウト設定
                layout = {
                    "polar": {
                        "radialaxis": {"visible": True, "range": [0, None]},
                        "angularaxis": {"direction": "clockwise", "period": 360}
                    },
                    "showlegend": True
                }
                
                return {
                    "data": plotly_data,
                    "layout": layout
                }
            else:
                # ChartJS用のデータ構造
                labels = []
                datasets = []
                
                # 登場する全ての角度を収集
                all_angles = set()
                for speed_data in wind_speeds.values():
                    if "angles" in speed_data:
                        all_angles.update(speed_data["angles"])
                
                # 全ての角度をソート
                all_angles = sorted(list(all_angles))
                labels = [f"{int(angle)}°" for angle in all_angles]
                
                # 色のリスト
                colors = [
                    "rgba(54, 162, 235, 0.5)",
                    "rgba(255, 99, 132, 0.5)",
                    "rgba(75, 192, 192, 0.5)",
                    "rgba(255, 159, 64, 0.5)",
                    "rgba(153, 102, 255, 0.5)"
                ]
                
                # 各風速のデータセットを作成
                color_idx = 0
                for wind_speed, speed_data in wind_speeds.items():
                    # 風速フィルタが設定されている場合は該当する風速のみ表示
                    wind_speed_filter = self.get_property("wind_speed_filter", None)
                    if wind_speed_filter is not None and float(wind_speed) != float(wind_speed_filter):
                        continue
                    
                    if "angles" in speed_data and "speeds" in speed_data:
                        # 角度と速度のマッピングを作成
                        angle_to_speed = dict(zip(speed_data["angles"], speed_data["speeds"]))
                        
                        # 全角度に対応するデータを準備
                        speeds = [angle_to_speed.get(angle, 0) for angle in all_angles]
                        
                        # データセットを追加
                        color = colors[color_idx % len(colors)]
                        datasets.append({
                            "label": f"{wind_speed} kt",
                            "data": speeds,
                            "backgroundColor": color,
                            "borderColor": color.replace("0.5", "1"),
                            "pointBackgroundColor": color.replace("0.5", "1"),
                            "pointBorderColor": "#fff",
                            "pointHoverBackgroundColor": "#fff",
                            "pointHoverBorderColor": color.replace("0.5", "1"),
                            "fill": True
                        })
                        
                        color_idx += 1
                
                # ChartJSデータを返す
                return {
                    "type": "radar",
                    "data": {
                        "labels": labels,
                        "datasets": datasets
                    }
                }
        
        # VMG最適化分析が有効な場合
        show_vmg_optimization = self.get_property("show_vmg_optimization", False)
        if show_vmg_optimization and isinstance(data, dict) and "actual" in data and "vmg" in data:
            # VMGのピーク（最適な風上/風下角度）を特定
            angles = data.get("angles", [i * 10 for i in range(36)])  # デフォルトは10度間隔
            vmg_values = data["vmg"]
            
            # 風上側と風下側のVMG最適角度を計算
            upwind_vmg = []
            downwind_vmg = []
            
            for i, angle in enumerate(angles):
                if 0 <= angle < 180:  # 風上側
                    upwind_vmg.append((angle, vmg_values[i]))
                else:  # 風下側
                    downwind_vmg.append((angle, vmg_values[i]))
            
            # VMG最大の角度を特定
            upwind_optimal = max(upwind_vmg, key=lambda x: x[1]) if upwind_vmg else (None, 0)
            downwind_optimal = max(downwind_vmg, key=lambda x: x[1]) if downwind_vmg else (None, 0)
            
            # 既存のチャートデータに最適VMG情報を追加
            if renderer_type == "plotly":
                # Plotly用のデータセット
                plotly_data = chart_data.get("data", [])
                
                # 最適VMGを示すマーカーを追加
                if upwind_optimal[0] is not None:
                    plotly_data.append({
                        "type": "scatterpolar",
                        "r": [upwind_optimal[1]],
                        "theta": [upwind_optimal[0]],
                        "name": f"最適風上角 ({int(upwind_optimal[0])}°)",
                        "mode": "markers",
                        "marker": {
                            "size": 10,
                            "symbol": "star",
                            "color": "green"
                        }
                    })
                
                if downwind_optimal[0] is not None:
                    plotly_data.append({
                        "type": "scatterpolar",
                        "r": [downwind_optimal[1]],
                        "theta": [downwind_optimal[0]],
                        "name": f"最適風下角 ({int(downwind_optimal[0])}°)",
                        "mode": "markers",
                        "marker": {
                            "size": 10,
                            "symbol": "star",
                            "color": "orange"
                        }
                    })
                
                # レイアウト設定
                layout = chart_data.get("layout", {})
                layout["annotations"] = [
                    {"text": f"最適風上角: {int(upwind_optimal[0])}°", "x": 0.1, "y": 1.1, "showarrow": False},
                    {"text": f"最適風下角: {int(downwind_optimal[0])}°", "x": 0.9, "y": 1.1, "showarrow": False}
                ]
                
                return {
                    "data": plotly_data,
                    "layout": layout
                }
            else:
                # ChartJS用のデータセット
                datasets = chart_data["data"]["datasets"]
                
                # 最適VMG情報を新しいデータセットとして追加
                optimal_points = []
                for i, angle in enumerate(angles):
                    if (angle == upwind_optimal[0] or angle == downwind_optimal[0]):
                        optimal_points.append(vmg_values[i])
                    else:
                        optimal_points.append(None)  # 最適点以外はNull
                
                # 最適VMGのデータセットを追加
                datasets.append({
                    "label": "最適VMG点",
                    "data": optimal_points,
                    "backgroundColor": "rgba(75, 192, 192, 0.8)",
                    "borderColor": "rgba(75, 192, 192, 1)",
                    "pointBackgroundColor": "gold",
                    "pointBorderColor": "rgba(75, 192, 192, 1)",
                    "pointRadius": 8,
                    "pointHoverRadius": 10,
                    "fill": False,
                    "showLine": False
                })
                
                # アノテーションの追加（ChartJSのオプションで設定）
                annotations = {}
                annotations["optimal_upwind"] = {
                    "type": "label",
                    "xValue": f"{int(upwind_optimal[0])}°",
                    "yValue": upwind_optimal[1],
                    "backgroundColor": "rgba(75, 192, 192, 0.7)",
                    "content": f"最適風上角: {int(upwind_optimal[0])}°",
                    "font": {"style": "bold"}
                }
                
                annotations["optimal_downwind"] = {
                    "type": "label",
                    "xValue": f"{int(downwind_optimal[0])}°",
                    "yValue": downwind_optimal[1],
                    "backgroundColor": "rgba(255, 159, 64, 0.7)",
                    "content": f"最適風下角: {int(downwind_optimal[0])}°",
                    "font": {"style": "bold"}
                }
                
                # オプションにアノテーション設定を追加
                if "options" not in chart_data:
                    chart_data["options"] = {}
                
                if "plugins" not in chart_data["options"]:
                    chart_data["options"]["plugins"] = {}
                
                chart_data["options"]["plugins"]["annotation"] = {
                    "annotations": annotations
                }
        
        # 拡張機能をすべて処理した後のデータを返す
        return chart_data
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        コースパフォーマンスのオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # インタラクティブ選択が有効な場合
        enable_interactive_selection = self.get_property("enable_interactive_selection", True)
        if enable_interactive_selection:
            # インタラクティブ機能を追加
            interactive_options = {
                "plugins": {
                    "crosshair": {
                        "line": {
                            "color": "rgba(100, 100, 100, 0.4)",
                            "width": 1
                        },
                        "sync": {
                            "enabled": True
                        }
                    },
                    "zoom": {
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
                }
            }
            
            # オプションを結合
            self._merge_options(options, interactive_options)
        
        # VMG最適化分析が有効な場合
        show_vmg_optimization = self.get_property("show_vmg_optimization", False)
        if show_vmg_optimization:
            # VMG分析用のオプションを追加
            vmg_options = {
                "plugins": {
                    "title": {
                        "display": True,
                        "text": self.title,
                        "subtitle": {
                            "display": True,
                            "text": "VMG最適化分析を含む",
                            "font": {
                                "size": 12,
                                "style": "italic"
                            }
                        }
                    },
                    "tooltip": {
                        "callbacks": {
                            "label": "function(context) { " +
                                    "var label = context.dataset.label || ''; " +
                                    "var value = context.raw; " +
                                    "var isOptimal = context.datasetIndex === context.chart.data.datasets.length - 1; " +
                                    "if (isOptimal && value !== null) { " +
                                    "   return '最適VMG点: ' + value.toFixed(1) + ' kt'; " +
                                    "} " +
                                    "return label + ': ' + value.toFixed(1) + ' kt'; " +
                                    "}"
                        }
                    }
                }
            }
            
            # オプションを結合
            self._merge_options(options, vmg_options)
        
        # 複数風速表示が有効な場合
        show_multiple_wind_speeds = self.get_property("show_multiple_wind_speeds", False)
        if show_multiple_wind_speeds:
            # 風速表示用のオプションを追加
            wind_speed_options = {
                "plugins": {
                    "title": {
                        "display": True,
                        "text": self.title,
                        "subtitle": {
                            "display": True,
                            "text": "複数風速の性能比較",
                            "font": {
                                "size": 12,
                                "style": "italic"
                            }
                        }
                    }
                }
            }
            
            # 風速フィルタが設定されている場合はサブタイトルに表示
            wind_speed_filter = self.get_property("wind_speed_filter", None)
            if wind_speed_filter is not None:
                wind_speed_options["plugins"]["title"]["subtitle"]["text"] = f"表示風速: {wind_speed_filter} kt"
            
            # オプションを結合
            self._merge_options(options, wind_speed_options)
        
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
        
        # インタラクティブ選択が有効かどうか
        enable_interactive_selection = self.get_property("enable_interactive_selection", True)
        
        # VMG最適化分析が有効かどうか
        show_vmg_optimization = self.get_property("show_vmg_optimization", False)
        
        # レンダラーオプションを設定
        renderer_options = {
            "plugins": {
                "datalabels": False,
                "crosshair": enable_interactive_selection,
                "zoom": enable_interactive_selection,
                "annotation": show_vmg_optimization
            }
        }
        
        # レンダラーを作成
        renderer = RendererFactory.create_renderer(
            renderer_type, 
            self.chart_id, 
            renderer_options
        )
        
        # チャートをレンダリング
        html_content = renderer.render(chart_data, width, height)
        
        return html_content


class EnhancedTackingAngleElement(TackingAngleElement):
    """
    拡張版タッキングアングル分析要素
    
    新しいチャートレンダラーを活用したタッキングアングル分析要素です。
    複数のレンダラー（ChartJS, Plotly）に対応し、より柔軟な可視化を実現します。
    
    拡張機能:
    - タッキング効率の可視化と評価
    - 時間または位置によるフィルタリング
    - 複数の表示モード（ヒストグラム、散布図、箱ひげ図）
    - インタラクティブなデータポイント選択
    - 詳細なタッキング統計情報の表示
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
        # レンダラー設定
        if model is None and 'renderer' not in kwargs:
            kwargs['renderer'] = "chartjs"  # chartjs, plotly
            
        # 表示モードのデフォルト設定
        if model is None and 'display_mode' not in kwargs:
            kwargs['display_mode'] = "histogram"  # histogram, scatter, boxplot
            
        # タッキング効率表示のデフォルト設定
        if model is None and 'show_efficiency' not in kwargs:
            kwargs['show_efficiency'] = False
            
        # 時間フィルタリングのデフォルト設定
        if model is None and 'time_filter_enabled' not in kwargs:
            kwargs['time_filter_enabled'] = False
            
        # 詳細統計情報表示のデフォルト設定
        if model is None and 'show_statistics' not in kwargs:
            kwargs['show_statistics'] = True
            
        # インタラクティブ選択のデフォルト設定
        if model is None and 'enable_interactive_selection' not in kwargs:
            kwargs['enable_interactive_selection'] = False
            
        super().__init__(model, **kwargs)
    
    def get_chart_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        タッキングアングル分析のデータを取得
        
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
            return {"type": "bar", "data": {"labels": [], "datasets": []}}
        
        # 表示モードを取得
        display_mode = self.get_property("display_mode", "histogram")
        
        # 最小角度と最大角度を取得
        min_angle = self.get_property("min_angle", 70)
        max_angle = self.get_property("max_angle", 140)
        
        # 最適角度範囲を取得
        optimal_min = self.get_property("optimal_min", 85)
        optimal_max = self.get_property("optimal_max", 95)
        
        # 時間フィルタリングが有効な場合
        time_filter_enabled = self.get_property("time_filter_enabled", False)
        time_start = self.get_property("time_start", None)
        time_end = self.get_property("time_end", None)
        time_key = self.get_property("time_key", "timestamp")
        
        # レンダラータイプの取得
        renderer_type = self.get_property("renderer", "chartjs")
        
        # タッキングデータの抽出
        tacking_angles = []
        tacking_timestamps = []
        tacking_efficiency = []
        
        if isinstance(data, dict) and "angles" in data and isinstance(data["angles"], list):
            # キー"angles"のリスト形式の場合
            tacking_angles = data["angles"]
            
            # タイムスタンプがある場合は取得
            if "timestamps" in data and isinstance(data["timestamps"], list):
                tacking_timestamps = data["timestamps"]
            
            # 効率データがある場合は取得
            if "efficiency" in data and isinstance(data["efficiency"], list):
                tacking_efficiency = data["efficiency"]
                
        elif isinstance(data, list):
            # リスト形式のデータの場合
            if all(isinstance(item, (int, float)) for item in data):
                # 数値のリストの場合（角度のリスト）
                tacking_angles = data
            
            elif all(isinstance(item, dict) for item in data):
                # 辞書のリストの場合
                angle_key = self.get_property("angle_key", "tacking_angle")
                efficiency_key = self.get_property("efficiency_key", "efficiency")
                
                for item in data:
                    # 角度を取得
                    if angle_key in item:
                        angle = item[angle_key]
                        if min_angle <= angle < max_angle:
                            tacking_angles.append(angle)
                            
                            # タイムスタンプを取得
                            if time_key in item:
                                tacking_timestamps.append(item[time_key])
                            else:
                                tacking_timestamps.append(None)
                            
                            # 効率を取得
                            if efficiency_key in item:
                                tacking_efficiency.append(item[efficiency_key])
                            else:
                                tacking_efficiency.append(None)
        
        # 時間フィルタリングが有効な場合はフィルタリングを適用
        if time_filter_enabled and (time_start or time_end) and tacking_timestamps:
            filtered_angles = []
            filtered_efficiency = []
            
            for i, timestamp in enumerate(tacking_timestamps):
                if timestamp is None:
                    continue
                
                # 時間範囲チェック
                time_obj = None
                
                # 時間値の変換
                if isinstance(timestamp, str):
                    try:
                        # ISO形式の文字列からDateオブジェクトへ変換
                        import datetime
                        time_obj = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        # 変換に失敗した場合は別の形式を試みる
                        try:
                            import dateutil.parser
                            time_obj = dateutil.parser.parse(timestamp)
                        except:
                            continue
                elif isinstance(timestamp, (int, float)):
                    # Unixタイムスタンプから変換
                    import datetime
                    time_obj = datetime.datetime.fromtimestamp(timestamp)
                
                # 時間オブジェクトが取得できなかった場合はスキップ
                if not time_obj:
                    continue
                
                # 時間範囲チェック
                time_start_obj = None
                time_end_obj = None
                
                if time_start:
                    try:
                        time_start_obj = datetime.datetime.fromisoformat(time_start.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        try:
                            import dateutil.parser
                            time_start_obj = dateutil.parser.parse(time_start)
                        except:
                            pass
                
                if time_end:
                    try:
                        time_end_obj = datetime.datetime.fromisoformat(time_end.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        try:
                            import dateutil.parser
                            time_end_obj = dateutil.parser.parse(time_end)
                        except:
                            pass
                
                # 範囲チェック
                in_range = True
                if time_start_obj and time_obj < time_start_obj:
                    in_range = False
                if time_end_obj and time_obj > time_end_obj:
                    in_range = False
                
                # 範囲内のデータのみ追加
                if in_range and i < len(tacking_angles):
                    filtered_angles.append(tacking_angles[i])
                    if i < len(tacking_efficiency):
                        filtered_efficiency.append(tacking_efficiency[i])
            
            # フィルタリングされたデータで置き換え
            tacking_angles = filtered_angles
            tacking_efficiency = filtered_efficiency if len(filtered_efficiency) > 0 else []
        
        # 表示モードに応じたデータ構造を作成
        if display_mode == "histogram":
            # ヒストグラムモード
            if renderer_type == "plotly":
                # Plotly用のヒストグラムデータ
                return {
                    "data": [
                        {
                            "type": "histogram",
                            "x": tacking_angles,
                            "nbinsx": self.get_property("num_bins", 18),
                            "marker": {
                                "color": "rgba(54, 162, 235, 0.6)",
                                "line": {
                                    "color": "rgba(54, 162, 235, 1)",
                                    "width": 1
                                }
                            },
                            "name": "タッキング角度"
                        }
                    ],
                    "layout": {
                        "xaxis": {
                            "title": "タッキング角度",
                            "range": [min_angle, max_angle]
                        },
                        "yaxis": {
                            "title": "頻度"
                        },
                        "shapes": [
                            {
                                "type": "rect",
                                "x0": optimal_min,
                                "x1": optimal_max,
                                "y0": 0,
                                "y1": 1,
                                "yref": "paper",
                                "fillcolor": "rgba(75, 192, 192, 0.2)",
                                "line": {
                                    "color": "rgba(75, 192, 192, 1)",
                                    "width": 1
                                }
                            }
                        ],
                        "annotations": [
                            {
                                "x": (optimal_min + optimal_max) / 2,
                                "y": 1,
                                "yref": "paper",
                                "text": "最適範囲",
                                "showarrow": False,
                                "font": {
                                    "size": 12
                                }
                            }
                        ]
                    }
                }
            else:
                # ChartJS用のヒストグラムデータ
                # ビンの数を取得
                num_bins = self.get_property("num_bins", 18)
                
                # ビンの幅を計算
                bin_width = (max_angle - min_angle) / num_bins
                
                # ヒストグラムのビンを初期化
                bins = [0] * num_bins
                bin_edges = [min_angle + i * bin_width for i in range(num_bins + 1)]
                bin_labels = [f"{int(edge)}°" for edge in bin_edges[:-1]]
                
                # ヒストグラムを計算
                for angle in tacking_angles:
                    if min_angle <= angle < max_angle:
                        bin_idx = min(int((angle - min_angle) / bin_width), num_bins - 1)
                        bins[bin_idx] += 1
                
                # 背景色の設定
                background_colors = []
                for i in range(len(bins)):
                    edge = bin_edges[i]
                    
                    # 最適範囲内は緑色、それ以外は青色
                    if optimal_min <= edge < optimal_max:
                        background_colors.append("rgba(75, 192, 192, 0.6)")  # 緑色
                    else:
                        background_colors.append("rgba(54, 162, 235, 0.6)")  # 青色
                
                # データセットを作成
                datasets = [{
                    "label": self.get_property("label", "タッキング角度分布"),
                    "data": bins,
                    "backgroundColor": background_colors,
                    "borderColor": [c.replace("0.6", "1") for c in background_colors],
                    "borderWidth": 1
                }]
                
                # チャートデータの作成
                return {
                    "type": "bar",
                    "data": {
                        "labels": bin_labels,
                        "datasets": datasets
                    }
                }
        
        elif display_mode == "scatter":
            # 散布図モード（タッキング効率の可視化に適している）
            if len(tacking_angles) > 0 and len(tacking_efficiency) > 0 and len(tacking_angles) == len(tacking_efficiency):
                if renderer_type == "plotly":
                    # Plotly用の散布図データ
                    return {
                        "data": [
                            {
                                "type": "scatter",
                                "x": tacking_angles,
                                "y": tacking_efficiency,
                                "mode": "markers",
                                "marker": {
                                    "color": "rgba(54, 162, 235, 0.6)",
                                    "size": 10,
                                    "line": {
                                        "color": "rgba(54, 162, 235, 1)",
                                        "width": 1
                                    }
                                },
                                "name": "タッキング効率"
                            }
                        ],
                        "layout": {
                            "xaxis": {
                                "title": "タッキング角度",
                                "range": [min_angle, max_angle]
                            },
                            "yaxis": {
                                "title": "効率 (%)"
                            },
                            "shapes": [
                                {
                                    "type": "rect",
                                    "x0": optimal_min,
                                    "x1": optimal_max,
                                    "y0": 0,
                                    "y1": 100,
                                    "fillcolor": "rgba(75, 192, 192, 0.2)",
                                    "line": {
                                        "color": "rgba(75, 192, 192, 1)",
                                        "width": 1
                                    }
                                }
                            ]
                        }
                    }
                else:
                    # ChartJS用の散布図データ
                    datasets = [{
                        "label": "タッキング効率",
                        "data": [{"x": angle, "y": eff} for angle, eff in zip(tacking_angles, tacking_efficiency)],
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 1)",
                        "pointRadius": 6,
                        "pointHoverRadius": 8
                    }]
                    
                    return {
                        "type": "scatter",
                        "data": {
                            "datasets": datasets
                        },
                        "options": {
                            "scales": {
                                "x": {
                                    "title": {
                                        "display": True,
                                        "text": "タッキング角度"
                                    },
                                    "min": min_angle,
                                    "max": max_angle
                                },
                                "y": {
                                    "title": {
                                        "display": True,
                                        "text": "効率 (%)"
                                    },
                                    "min": 0,
                                    "max": 100
                                }
                            }
                        }
                    }
            else:
                # 効率データがない場合は時系列散布図を表示
                if renderer_type == "plotly":
                    # Plotly用の時系列散布図データ
                    return {
                        "data": [
                            {
                                "type": "scatter",
                                "x": list(range(len(tacking_angles))),
                                "y": tacking_angles,
                                "mode": "markers+lines",
                                "marker": {
                                    "color": "rgba(54, 162, 235, 0.6)",
                                    "size": 8
                                },
                                "line": {
                                    "color": "rgba(54, 162, 235, 0.3)",
                                    "width": 1
                                },
                                "name": "タッキング角度"
                            }
                        ],
                        "layout": {
                            "xaxis": {
                                "title": "タッキング順序"
                            },
                            "yaxis": {
                                "title": "タッキング角度",
                                "range": [min_angle, max_angle]
                            },
                            "shapes": [
                                {
                                    "type": "rect",
                                    "x0": 0,
                                    "x1": len(tacking_angles),
                                    "y0": optimal_min,
                                    "y1": optimal_max,
                                    "fillcolor": "rgba(75, 192, 192, 0.2)",
                                    "line": {
                                        "color": "rgba(75, 192, 192, 1)",
                                        "width": 1
                                    }
                                }
                            ]
                        }
                    }
                else:
                    # ChartJS用の時系列散布図データ
                    datasets = [{
                        "label": "タッキング角度",
                        "data": [{"x": i, "y": angle} for i, angle in enumerate(tacking_angles)],
                        "backgroundColor": "rgba(54, 162, 235, 0.6)",
                        "borderColor": "rgba(54, 162, 235, 0.3)",
                        "borderWidth": 1,
                        "pointRadius": 5,
                        "pointHoverRadius": 7,
                        "showLine": True,
                        "tension": 0.1
                    }]
                    
                    return {
                        "type": "scatter",
                        "data": {
                            "datasets": datasets
                        }
                    }
        
        elif display_mode == "boxplot":
            # 箱ひげ図モード
            if renderer_type == "plotly":
                # Plotly用の箱ひげ図データ
                return {
                    "data": [
                        {
                            "type": "box",
                            "y": tacking_angles,
                            "name": "タッキング角度",
                            "boxmean": True,
                            "marker": {
                                "color": "rgba(54, 162, 235, 0.6)"
                            }
                        }
                    ],
                    "layout": {
                        "yaxis": {
                            "title": "タッキング角度",
                            "range": [min_angle, max_angle]
                        },
                        "shapes": [
                            {
                                "type": "rect",
                                "x0": 0,
                                "x1": 1,
                                "xref": "paper",
                                "y0": optimal_min,
                                "y1": optimal_max,
                                "fillcolor": "rgba(75, 192, 192, 0.2)",
                                "line": {
                                    "color": "rgba(75, 192, 192, 1)",
                                    "width": 1
                                }
                            }
                        ]
                    }
                }
            else:
                # ChartJSは箱ひげ図に直接対応していないため、代わりにヒストグラムを返す
                return self.get_chart_data(context)
        
        # デフォルトはヒストグラムモード
        return super().get_chart_data(context)
    
    def get_chart_options(self) -> Dict[str, Any]:
        """
        タッキングアングル分析のオプションを取得
        
        Returns
        -------
        Dict[str, Any]
            チャートオプション
        """
        options = super().get_chart_options()
        
        # 表示モードを取得
        display_mode = self.get_property("display_mode", "histogram")
        
        # インタラクティブ選択が有効かどうか
        enable_interactive_selection = self.get_property("enable_interactive_selection", False)
        if enable_interactive_selection:
            # インタラクティブ機能を追加
            interactive_options = {
                "plugins": {
                    "zoom": {
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
                }
            }
            
            # オプションを結合
            self._merge_options(options, interactive_options)
        
        # 表示モードに応じたオプションを追加
        if display_mode == "scatter":
            # 散布図モード用のオプション
            scatter_options = {
                "scales": {
                    "x": {
                        "type": "linear",
                        "position": "bottom",
                        "title": {
                            "display": True,
                            "text": "タッキング角度" if self.get_property("show_efficiency", False) else "タッキング順序"
                        }
                    },
                    "y": {
                        "title": {
                            "display": True,
                            "text": "効率 (%)" if self.get_property("show_efficiency", False) else "タッキング角度"
                        }
                    }
                },
                "plugins": {
                    "tooltip": {
                        "callbacks": {
                            "label": "function(context) { return `${context.dataset.label}: (${context.parsed.x.toFixed(1)}, ${context.parsed.y.toFixed(1)})`; }"
                        }
                    }
                }
            }
            
            # オプションを結合
            self._merge_options(options, scatter_options)
        
        # タッキング統計情報を表示するかどうか
        show_statistics = self.get_property("show_statistics", True)
        if show_statistics and len(self.get_statistics_text()) > 0:
            # 統計情報表示用のオプションを追加
            stats_options = {
                "plugins": {
                    "title": {
                        "display": True,
                        "text": self.title,
                        "subtitle": {
                            "display": True,
                            "text": self.get_statistics_text(),
                            "font": {
                                "size": 12,
                                "style": "italic"
                            }
                        }
                    }
                }
            }
            
            # オプションを結合
            self._merge_options(options, stats_options)
        
        # 時間フィルタリングが有効な場合
        time_filter_enabled = self.get_property("time_filter_enabled", False)
        time_start = self.get_property("time_start", None)
        time_end = self.get_property("time_end", None)
        
        if time_filter_enabled and (time_start or time_end):
            # フィルター情報を表示するオプションを追加
            filter_text = "期間フィルター適用:"
            if time_start:
                from_str = time_start.split("T")[0] if "T" in time_start else time_start
                filter_text += f" 開始: {from_str}"
            if time_end:
                to_str = time_end.split("T")[0] if "T" in time_end else time_end
                filter_text += f" 終了: {to_str}"
            
            filter_options = {
                "plugins": {
                    "title": {
                        "display": True,
                        "text": self.title,
                        "subtitle": {
                            "display": True,
                            "text": filter_text,
                            "font": {
                                "size": 12,
                                "style": "italic"
                            }
                        }
                    }
                }
            }
            
            # オプションを結合
            self._merge_options(options, filter_options)
        
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
        
        # 表示モードを取得
        display_mode = self.get_property("display_mode", "histogram")
        
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
        
        # インタラクティブ選択が有効かどうか
        enable_interactive_selection = self.get_property("enable_interactive_selection", False)
        
        # レンダラーオプションを設定
        renderer_options = {
            "plugins": {
                "annotation": True,
                "zoom": enable_interactive_selection
            }
        }
        
        # レンダラーを作成
        renderer = RendererFactory.create_renderer(
            renderer_type, 
            self.chart_id, 
            renderer_options
        )
        
        # チャートをレンダリング
        html_content = renderer.render(chart_data, width, height)
        
        return html_content
    
    def get_statistics_text(self) -> str:
        """
        タッキング統計情報のテキストを取得
        
        Returns
        -------
        str
            統計情報テキスト
        """
        # データソースからデータを取得
        data = None
        if self.data_source and hasattr(self, '_last_context') and self._last_context and self.data_source in self._last_context:
            data = self._last_context[self.data_source]
        
        # データがない場合は空文字を返す
        if not data:
            return ""
        
        # タッキングデータの抽出
        tacking_angles = []
        
        if isinstance(data, dict) and "angles" in data and isinstance(data["angles"], list):
            # キー"angles"のリスト形式の場合
            tacking_angles = data["angles"]
        elif isinstance(data, list):
            # リスト形式のデータの場合
            if all(isinstance(item, (int, float)) for item in data):
                # 数値のリストの場合（角度のリスト）
                tacking_angles = data
            elif all(isinstance(item, dict) for item in data):
                # 辞書のリストの場合
                angle_key = self.get_property("angle_key", "tacking_angle")
                tacking_angles = [item[angle_key] for item in data if angle_key in item]
        
        # 統計情報を計算
        if len(tacking_angles) > 0:
            # 最小値、最大値、平均値、中央値
            min_angle = min(tacking_angles)
            max_angle = max(tacking_angles)
            avg_angle = sum(tacking_angles) / len(tacking_angles)
            median_angle = sorted(tacking_angles)[len(tacking_angles) // 2]
            
            # 最適範囲内の割合
            optimal_min = self.get_property("optimal_min", 85)
            optimal_max = self.get_property("optimal_max", 95)
            optimal_count = sum(1 for angle in tacking_angles if optimal_min <= angle <= optimal_max)
            optimal_percentage = (optimal_count / len(tacking_angles)) * 100
            
            # 統計情報テキストを作成
            return f"平均: {avg_angle:.1f}° | 中央値: {median_angle:.1f}° | 最小: {min_angle:.1f}° | 最大: {max_angle:.1f}° | 最適範囲内: {optimal_percentage:.1f}%"
        
        return ""
