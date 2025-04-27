# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.timeline.parameter_timeline

パラメータタイムラインクラスを提供するモジュールです。
速度、風向、風速などのパラメータを時間軸上にグラフとして表示します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid
from datetime import datetime, timedelta
import statistics
import math

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class ParameterTimeline(BaseElement):
    """
    パラメータタイムラインクラス
    
    速度、風向、風速などのパラメータを時間軸上にグラフとして表示します。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, element_id=None, name="パラメータタイムライン", **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            要素モデル, by default None
        element_id : str, optional
            要素ID, by default None (自動生成)
        name : str, optional
            要素名, by default "パラメータタイムライン"
        **kwargs : dict
            その他のプロパティ
        """
        # デフォルトでタイムライン要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.TIMELINE
        
        if element_id is None:
            element_id = f"param_timeline_{uuid.uuid4().hex[:8]}"
        
        super().__init__(model, element_id=element_id, name=name, **kwargs)
        
        # データ
        self._data = None
        
        # 表示オプション
        self._options = {}
            "show_speed": kwargs.get("show_speed", True),
            "show_wind_speed": kwargs.get("show_wind_speed", False),
            "show_wind_direction": kwargs.get("show_wind_direction", False),
            "show_heading": kwargs.get("show_heading", False),
            "show_heel": kwargs.get("show_heel", False),
            "show_vmg": kwargs.get("show_vmg", False),
            "custom_parameters": kwargs.get("custom_parameters", []),
            "timeline_height": kwargs.get("timeline_height", 300),
            "show_statistics": kwargs.get("show_statistics", True),
            "show_trends": kwargs.get("show_trends", False),
            "line_style": kwargs.get("line_style", "linear"),
            "interactive": kwargs.get("interactive", True),
            "point_radius": kwargs.get("point_radius", 2),
            "enable_zoom": kwargs.get("enable_zoom", True),
            "time_format": kwargs.get("time_format", "HH:mm:ss"),
 "show_speed": kwargs.get("show_speed", True),
            "show_wind_speed": kwargs.get("show_wind_speed", False),
            "show_wind_direction": kwargs.get("show_wind_direction", False),
            "show_heading": kwargs.get("show_heading", False),
            "show_heel": kwargs.get("show_heel", False),
            "show_vmg": kwargs.get("show_vmg", False),
            "custom_parameters": kwargs.get("custom_parameters", []),
            "timeline_height": kwargs.get("timeline_height", 300),
            "show_statistics": kwargs.get("show_statistics", True),
            "show_trends": kwargs.get("show_trends", False),
            "line_style": kwargs.get("line_style", "linear"),
            "interactive": kwargs.get("interactive", True),
            "point_radius": kwargs.get("point_radius", 2),
            "enable_zoom": kwargs.get("enable_zoom", True),
            "time_format": kwargs.get("time_format", "HH:mm:ss"),}
        
        # オプションをプロパティに設定
        for key, value in self._options.items():
            self.set_property(key, value)
        
        # パラメータの定義と色
        self._parameters = {
            "speed": "color": "#FF5722", "label": "速度", "unit": "kt", "axis": "y-left"},
            "wind_speed": {"color": "#2196F3", "label": "風速", "unit": "kt", "axis": "y-left"},
            "wind_direction": {"color": "#4CAF50", "label": "風向", "unit": "°", "axis": "y-right"},
            "heading": {"color": "#9C27B0", "label": "艇首方位", "unit": "°", "axis": "y-right"},
            "heel": {"color": "#FFC107", "label": "ヒール角", "unit": "°", "axis": "y-left"},
            "vmg": {"color": "#607D8B", "label": "VMG", "unit": "kt", "axis": "y-left"},
 {
            "speed": "color": "#FF5722", "label": "速度", "unit": "kt", "axis": "y-left"},
            "wind_speed": {"color": "#2196F3", "label": "風速", "unit": "kt", "axis": "y-left"},
            "wind_direction": {"color": "#4CAF50", "label": "風向", "unit": "°", "axis": "y-right"},
            "heading": {"color": "#9C27B0", "label": "艇首方位", "unit": "°", "axis": "y-right"},
            "heel": {"color": "#FFC107", "label": "ヒール角", "unit": "°", "axis": "y-left"},
            "vmg": {"color": "#607D8B", "label": "VMG", "unit": "kt", "axis": "y-left"},}
        
        # データソース
        self.set_property("data_source", kwargs.get("data_source", ""))
    
    def set_property(self, key: str, value: Any) -> None:
        """
        プロパティを設定
        
        Parameters
        ----------
        key : str
            プロパティ名
        value : Any
            プロパティ値
        """
        super().set_property(key, value)
        
        # _optionsも更新
        if key in self._options:
            self._options[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        プロパティを取得
        
        Parameters
        ----------
        key : str
            プロパティ名
        default : Any, optional
            デフォルト値, by default None
            
        Returns
        -------
        Any
            プロパティ値
        """
        return super().get_property(key, default)
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """
        データを設定
        
        Parameters
        ----------
        data : Dict[str, Any]
            タイムラインのデータ
        """
        self._data = data
    
    def add_custom_parameter(self, name: str, field: str, color: str = "#607D8B", 
                            label: Optional[str] = None, unit: str = "", 
                            axis: str = "y-left") -> None:
        """
        カスタムパラメータを追加
        
        Parameters
        ----------
        name : str
            パラメータ名
        field : str
            データ内のフィールド名
        color : str, optional
            パラメータの色, by default "#607D8B"
        label : Optional[str], optional
            表示ラベル, by default None
        unit : str, optional
            単位, by default ""
        axis : str, optional
            使用する軸, by default "y-left"
        """
        # カスタムパラメータをパラメータリストに追加
        self._parameters[name] = {
            "field": field,
            "color": color,
            "label": label or name,
            "unit": unit,
            "axis": axis
 "field": field,
            "color": color,
            "label": label or name,
            "unit": unit,
            "axis": axis}
        
        # カスタムパラメータリストを更新
        custom_parameters = self.get_property("custom_parameters", [])
        if name not in custom_parameters:
            custom_parameters.append(name)
            self.set_property("custom_parameters", custom_parameters)
    
    def remove_custom_parameter(self, name: str) -> bool:
        """
        カスタムパラメータを削除
        
        Parameters
        ----------
        name : str
            削除するパラメータ名
            
        Returns
        -------
        bool
            削除が成功した場合はTrue
        """
        # パラメータリストから削除
        if name in self._parameters:
            del self._parameters[name]
            
            # カスタムパラメータリストを更新
            custom_parameters = self.get_property("custom_parameters", [])
            if name in custom_parameters:
                custom_parameters.remove(name)
                self.set_property("custom_parameters", custom_parameters)
                return True
        
        return False
    
    def calculate_statistics(self, data: Dict[str, Any], parameter: str) -> Dict[str, float]:
        """
        指定されたパラメータの統計情報を計算
        
        Parameters
        ----------
        data : Dict[str, Any]
            データソース
        parameter : str
            パラメータ名
            
        Returns
        -------
        Dict[str, float]
            統計情報
        """
        stats = {}
        
        if parameter not in data or not data[parameter]:
            return stats
        
        # 角度パラメータかどうかを判断
        is_angle = parameter in ["wind_direction", "heading"]
        
        # データを数値に変換
        values = data[parameter]
        numeric_values = []
        
        for value in values:
            if value is not None and value != "" and isinstance(value, (int, float)):
                numeric_values.append(value)
        
        if not numeric_values:
            return stats
        
        # 基本統計量を計算
        stats["min"] = min(numeric_values)
        stats["max"] = max(numeric_values)
        stats["avg"] = sum(numeric_values) / len(numeric_values)
        
        # 標準偏差を計算（データが2つ以上ある場合）
        if len(numeric_values) >= 2:
            stats["std"] = statistics.stdev(numeric_values)
        
        # 角度の場合は平均方向を計算
        if is_angle:
            # 角度を極座標に変換して平均を計算
            sum_sin = 0
            sum_cos = 0
            for angle in numeric_values:
                rad = angle * (3.14159 / 180)  # 度をラジアンに変換
                sum_sin += math.sin(rad)
                sum_cos += math.cos(rad)
            
            avg_rad = math.atan2(sum_sin, sum_cos)
            avg_deg = avg_rad * (180 / 3.14159)  # ラジアンを度に変換
            if avg_deg < 0:
                avg_deg += 360
            
            stats["avg"] = avg_deg
        
        return stats
    
    def get_required_libraries(self) -> List[str]:
        """
        必要なライブラリのURLリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        libraries = [
            "https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js",
            "https://cdn.jsdelivr.net/npm/luxon@2.0.2/build/global/luxon.min.js",
            "https://cdn.jsdelivr.net/npm/chartjs-adapter-luxon@1.1.0/dist/chartjs-adapter-luxon.min.js"
        ]
        
        # ズーム機能が有効な場合
        if self.get_property("enable_zoom", True):
            libraries.append("https://cdn.jsdelivr.net/npm/hammerjs@2.0.8/hammer.min.js")
            libraries.append("https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@2.0.0/dist/chartjs-plugin-zoom.min.js")
        
        # トレンド表示が有効な場合
        if self.get_property("show_trends", False):
            libraries.append("https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@2.1.0/dist/chartjs-plugin-annotation.min.js")
        
        return libraries
    
    def get_required_styles(self) -> List[str]:
        """
        必要なスタイルシートのURLリストを取得
        
        Returns
        -------
        List[str]
            スタイルシートのURLリスト
        """
        return []
    
    def render(self, context: Dict[str, Any] = None) -> str:
        """
        タイムラインのHTMLを生成
        
        Parameters
        ----------
        context : Dict[str, Any], optional
            レンダリングコンテキスト, by default None
            
        Returns
        -------
        str
            生成されたHTML
        """
        if context is None:
            context = {}
        
        # 条件チェック
        if not self.evaluate_conditions(context):
            return ""
        
        # データ取得
        data_source = self.get_property("data_source", "")
        data = self._data or {}  # 直接設定されたデータを使用
        
        if not data and data_source and data_source in context:
            data = context[data_source]
        
        # データがない場合
        if not data or "timestamp" not in data:
            return f'<div id="{self.element_id}" class="parameter-timeline-container"><p>データがありません</p></div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # タイムラインの高さ
        timeline_height = self.get_property("timeline_height", 300)
        
        # 表示設定を取得
        show_speed = self.get_property("show_speed", True)
        show_wind_speed = self.get_property("show_wind_speed", False)
        show_wind_direction = self.get_property("show_wind_direction", False)
        show_heading = self.get_property("show_heading", False)
        show_heel = self.get_property("show_heel", False)
        show_vmg = self.get_property("show_vmg", False)
        custom_parameters = self.get_property("custom_parameters", [])
        
        # 統計情報表示設定
        show_statistics = self.get_property("show_statistics", True)
        
        # トレンド表示設定
        show_trends = self.get_property("show_trends", False)
        
        # 線のスタイル
        line_style = self.get_property("line_style", "linear")
        
        # 点のサイズ
        point_radius = self.get_property("point_radius", 2)
        
        # ズーム設定
        enable_zoom = self.get_property("enable_zoom", True)
        
        # 時間フォーマット
        time_format = self.get_property("time_format", "HH:mm:ss")
        
        # Chart.jsのデータセットを準備
        datasets = []
        
        # 表示するパラメータのリスト
        params_to_show = []
        
        if show_speed and "speed" in data:
            params_to_show.append("speed")
        
        if show_wind_speed and "wind_speed" in data:
            params_to_show.append("wind_speed")
        
        if show_wind_direction and "wind_direction" in data:
            params_to_show.append("wind_direction")
        
        if show_heading and "heading" in data:
            params_to_show.append("heading")
        
        if show_heel and "heel" in data:
            params_to_show.append("heel")
        
        if show_vmg and "vmg" in data:
            params_to_show.append("vmg")
        
        # カスタムパラメータの追加
        for param in custom_parameters:
            if param in self._parameters:
                field = self._parameters[param].get("field", param)
                if field in data:
                    params_to_show.append(param)
        
        # パラメータがない場合
        if not params_to_show:
            return f'<div id="{self.element_id}" class="parameter-timeline-container"><p>表示するパラメータがありません</p></div>'
        
        # タイムスタンプを取得
        timestamps = data["timestamp"]
        
        # 各パラメータのデータセットを作成
        for param in params_to_show:
            if param in data:
                param_info = self._parameters.get(param, {
                    "color": "#607D8B", 
                    "label": param, 
                    "unit": "", 
                    "axis": "y-left"
 "color": "#607D8B", 
                    "label": param, 
                    "unit": "", 
                    "axis": "y-left"}
                })
                
                # フィールド名の取得（カスタムパラメータの場合）
                field = param_info.get("field", param)
                
                # データがない場合はスキップ
                if field not in data:
                    continue
                
                # データポイントを作成
                data_points = []
                for i, ts in enumerate(timestamps):
                    if i < len(data[field]) and data[field][i] is not None:
                        data_points.append({
                            "x": ts,
                            "y": data[field][i]
                        })
                
                # 統計情報を計算
                stats = {}
                if show_statistics and data_points:
                    stats = self.calculate_statistics(data, field)
                
                # データセットを追加
                dataset = {
                    "label": f"param_info['label']} ({param_info['unit']})" if param_info['unit'] else param_info['label'],
                    "data": data_points,
                    "borderColor": param_info['color'],
                    "backgroundColor": f"{param_info['color']}33",  # 半透明
                    "fill": False,
                    "tension": 0.1 if line_style == "spline" else 0,
                    "pointRadius": point_radius,
                    "pointHoverRadius": point_radius + 2,
                    "borderWidth": 2,
                    "yAxisID": param_info['axis'],
                    "statistics": stats
 {
                    "label": f"param_info['label']} ({param_info['unit']})" if param_info['unit'] else param_info['label'],
                    "data": data_points,
                    "borderColor": param_info['color'],
                    "backgroundColor": f"{param_info['color']}33",  # 半透明
                    "fill": False,
                    "tension": 0.1 if line_style == "spline" else 0,
                    "pointRadius": point_radius,
                    "pointHoverRadius": point_radius + 2,
                    "borderWidth": 2,
                    "yAxisID": param_info['axis'],
                    "statistics": stats}
                
                datasets.append(dataset)
        
        # データセットをJSON形式に変換
        datasets_json = json.dumps(datasets, ensure_ascii=False)
        
        # 必要なライブラリを取得
        libraries = self.get_required_libraries()
        library_tags = "\n".join([f'<script src="{lib}"></script>' for lib in libraries])
        
        # 必要なスタイルを取得
        styles = self.get_required_styles()
        style_tags = "\n".join([f'<link rel="stylesheet" href="{style}" />' for style in styles])
        
        # Chart.jsの設定
        chart_config = {
            "type": "line",
            "data": {
                "datasets": []  # データセットはJavaScriptで追加
 {
            "type": "line",
            "data": "datasets": []  # データセットはJavaScriptで追加}
            },
            "options": {
                "responsive": True,
                "maintainAspectRatio": False,
                "interaction": {
                    "mode": "index",
                    "intersect": False
 {
                "responsive": True,
                "maintainAspectRatio": False,
                "interaction": "mode": "index",
                    "intersect": False}
                },
                "scales": {
                    "x": {
                        "type": "time",
                        "time": {
                            "displayFormats": {
                                "millisecond": time_format,
                                "second": time_format,
                                "minute": time_format,
                                "hour": time_format
 {
                    "x": {
                        "type": "time",
                        "time": {
                            "displayFormats": "millisecond": time_format,
                                "second": time_format,
                                "minute": time_format,
                                "hour": time_format}
                        },
                        "title": {
                            "display": True,
                            "text": "時間"
 "display": True,
                            "text": "時間"}
                    },
                    "y-left": {
                        "type": "linear",
                        "position": "left",
                        "title": {
                            "display": True,
                            "text": "値"
 {
                        "type": "linear",
                        "position": "left",
                        "title": "display": True,
                            "text": "値"}
                        },
                        "grid": {
                            "display": True,
                            "color": "rgba(0, 0, 0, 0.1)"
 "display": True,
                            "color": "rgba(0, 0, 0, 0.1)"}
                    },
                    "y-right": {
                        "type": "linear",
                        "position": "right",
                        "grid": {
                            "display": False
 {
                        "type": "linear",
                        "position": "right",
                        "grid": "display": False}
                        },
                        "title": {
                            "display": True,
                            "text": "角度 (°)"
 "display": True,
                            "text": "角度 (°)"}
                },
                "plugins": {
                    "legend": {
                        "display": True,
                        "position": "top"
 {
                    "legend": "display": True,
                        "position": "top"}
                    },
                    "tooltip": {
                        "mode": "index",
                        "intersect": False
 "mode": "index",
                        "intersect": False}
        
        # ズーム機能が有効な場合
        if enable_zoom:
            chart_config["options"]["plugins"]["zoom"] = {
                "zoom": {
                    "wheel": {
                        "enabled": True
 {
                "zoom": {
                    "wheel": "enabled": True}
                    },
                    "pinch": {
                        "enabled": True
 "enabled": True}
                    },
                    "mode": "xy"
                },
                "pan": {
                    "enabled": True,
                    "mode": "xy"
 "enabled": True,
                    "mode": "xy"}
        
        # 設定をJSON形式に変換
        chart_config_json = json.dumps(chart_config, ensure_ascii=False)
        
        # HTMLを生成
        html = f'''
        <div id="{self.element_id}_container" class="parameter-timeline-container" style="{css_style}">
            {style_tags}
            
            <div id="{self.element_id}_wrapper" style="width:100%; height:{timeline_height}px; position:relative;">
                <canvas id="{self.element_id}"></canvas>
            </div>
            
            {library_tags}
            
            <script>
                (function() {{
                    // データセット
                    const datasets = datasets_json};
                    
                    // Chart.jsの設定
                    const config = {chart_config_json};
                    
                    // データセットを設定
                    config.data.datasets = datasets;
                    
                    // チャートを初期化
                    const ctx = document.getElementById('{self.element_id}').getContext('2d');
                    const chart = new Chart(ctx, config);
                    
                    // グローバル変数として保存（外部からアクセス用）
                    window['{self.element_id}_chart'] = chart;
                    
                    // 統計情報が有効な場合
                    if ({str(show_statistics).lower()}) {{
                        // 統計情報をグラフに追加
                        datasets.forEach(dataset => {{
                            if (dataset.statistics && Object.keys(dataset.statistics).length > 0) {{
                                const stats = dataset.statistics;
                                
                                // 最小値/最大値/平均値のラインを追加
                                if ('avg' in stats) {{
                                    config.options.plugins.annotation = config.options.plugins.annotation || {}};
                                    config.options.plugins.annotation.annotations = config.options.plugins.annotation.annotations || {}};
                                    
                                    const avgAnnotation = {{
                                        type: 'line',
                                        yMin: stats.avg,
                                        yMax: stats.avg,
                                        borderColor: dataset.borderColor,
                                        borderWidth: 1,
                                        borderDash: [5, 5],
                                        label: {{
                                            display: true,
                                            content: `平均: ${stats.avg.toFixed(2)}}`,
                                            position: 'start'
                                        }}
                                    }};
                                    
                                    // 注釈のIDを設定
                                    const annotationId = `avg_${dataset.label.replace(/[\\s()]/g, '_')}}`;
                                    config.options.plugins.annotation.annotations[annotationId] = avgAnnotation;
                                }}
                            }}
                        }});
                    }}
                    
                    // トレンドラインが有効な場合
                    if ({str(show_trends).lower()}) {{
                        // 各データセットに回帰直線を追加
                        datasets.forEach(dataset => {{
                            if (dataset.data.length > 1) {{
                                // 回帰分析用のデータを準備
                                const xValues = [];
                                const yValues = [];
                                
                                dataset.data.forEach((point, index) => {xValues.push(index);  // インデックスを使用
                                    yValues.push(point.y);
                                }});
                                
                                // 回帰直線の係数を計算
                                const n = xValues.length;
                                const sumX = xValues.reduce((a, b) => a + b, 0);
                                const sumY = yValues.reduce((a, b) => a + b, 0);
                                const sumXY = xValues.reduce((sum, x, i) => sum + x * yValues[i], 0);
                                const sumXX = xValues.reduce((sum, x) => sum + x * x, 0);
                                
                                const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
                                const intercept = (sumY - slope * sumX) / n;
                                
                                // 直線の始点と終点を計算
                                const startY = intercept;
                                const endY = intercept + slope * (n - 1);
                                
                                // トレンドラインのデータセットを追加
                                const trendDataset = {{
                                    label: `${dataset.label}} トレンド`,
                                    data: [
                                        {x: dataset.data[0].x, y: startY }},
                                        {x: dataset.data[n-1].x, y: endY }}
                                    ],
                                    borderColor: dataset.borderColor,
                                    borderDash: [10, 5],
                                    borderWidth: 1,
                                    fill: false,
                                    pointRadius: 0,
                                    tension: 0,
                                    yAxisID: dataset.yAxisID
                                }};
                                
                                config.data.datasets.push(trendDataset);
                            }}
                        }});
                    }}
                    
                    // グラフを更新
                    chart.update();
                    
                    // リセットボタンを追加
                    if ({str(enable_zoom).lower()}) {{
                        const resetButton = document.createElement('button');
                        resetButton.textContent = 'リセット';
                        resetButton.style.position = 'absolute';
                        resetButton.style.bottom = '10px';
                        resetButton.style.right = '10px';
                        resetButton.style.zIndex = '10';
                        resetButton.style.padding = '5px 10px';
                        resetButton.style.backgroundColor = '#f8f9fa';
                        resetButton.style.border = '1px solid #ddd';
                        resetButton.style.borderRadius = '4px';
                        resetButton.style.cursor = 'pointer';
                        
                        resetButton.addEventListener('click', () => {chart.resetZoom();
                        }});
                        
                        document.getElementById('{self.element_id}_wrapper').appendChild(resetButton);
                    }}
                }})();
            </script>
        </div>
        '''
        
        return html
"""
"""