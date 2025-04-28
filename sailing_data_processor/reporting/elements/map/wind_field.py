# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map.wind_field

風向風速場を表示するマップ要素を提供するモジュール。
このモジュールは、風向風速データの視覚化機能を定義します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid
import os
import pathlib

from sailing_data_processor.reporting.elements.visualizations.map_elements import WindFieldElement as BaseWindFieldElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class WindFieldElement(BaseWindFieldElement):
    """
    風向風速場表示要素
    
    ベースのWindFieldElementを拡張し、風向風速場の高度な可視化機能を
    提供するマップ要素です。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            モデル設定, by default None
        **kwargs : dict
            追加パラメータとしてレイヤーに渡す設定オプション
        """
        super().__init__(model, **kwargs)
        
        # 表示の詳細設定
        self.set_property("show_wind_shifts", self.get_property("show_wind_shifts", False))
        self.set_property("show_wind_trends", self.get_property("show_wind_trends", False))
        self.set_property("compare_forecast", self.get_property("compare_forecast", False))
        self.set_property("forecast_source", self.get_property("forecast_source", ""))
        
        # 風の設定
        self.set_property("vector_density", self.get_property("vector_density", 50))
        self.set_property("arrow_scale", self.get_property("arrow_scale", 1.0))
        self.set_property("interpolation_method", self.get_property("interpolation_method", "bilinear"))
        
        # 地形効果の設定
        self.set_property("show_terrain_effects", self.get_property("show_terrain_effects", False))
        self.set_property("terrain_source", self.get_property("terrain_source", ""))
    
    def get_chart_libraries(self) -> List[str]:
        """
        風向風速場の表示に必要なライブラリリスト
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        libraries = super().get_chart_libraries()
        
        # 追加のライブラリ
        additional_libraries = [
            "https://cdn.jsdelivr.net/npm/leaflet-rotatedmarker@0.2.0/leaflet.rotatedMarker.js",
            "https://cdn.jsdelivr.net/npm/d3@7.8.2/dist/d3.min.js"
        ]
        
        return libraries + additional_libraries
    
    def set_forecast_data(self, forecast_source: str) -> None:
        """
        予測風向風速の表示設定
        
        Parameters
        ----------
        forecast_source : str
            予測風向風速のデータソース名
        """
        self.set_property("compare_forecast", True)
        self.set_property("forecast_source", forecast_source)
    
    def set_terrain_effects(self, show: bool, terrain_source: str = "") -> None:
        """
        地形効果の表示設定
        
        Parameters
        ----------
        show : bool
            地形効果を表示するかどうか
        terrain_source : str, optional
            地形効果のデータソース, by default ""
        """
        self.set_property("show_terrain_effects", show)
        if terrain_source:
            self.set_property("terrain_source", terrain_source)
    
    def render_html(self, data: Any = None) -> str:
        """
        HTMLレンダリング
        
        Parameters
        ----------
        data : Any, optional
            表示するデータ, by default None
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 静的ファイルのパスを取得
        module_path = pathlib.Path(__file__).parent.parent.parent.parent
        js_path = module_path / 'reporting' / 'static' / 'js' / 'wind_field.js'
        
        # テンプレートを読み込む関数
        def load_js_file(path: pathlib.Path) -> str:
            """JavaScriptファイルの読み込み"""
            try:
                if path.exists():
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
                else:
                    import logging
                    logging.warning(f"JavaScript file not found: {path}")
                    return "console.error('JavaScript file for wind field not found.');"
            except Exception as e:
                import logging
                logging.error(f"Error loading JavaScript file: {e}")
                return f"console.error('Error loading JavaScript file: {e}');"
        
        # 条件評価
        if not self.evaluate_conditions(context={}):
            return ""
        
        # データソースからデータを取得
        data_from_source = None
        if self.data_source and self.data_source in context:
            data_from_source = context[self.data_source]
        data_to_use = data if data is not None else data_from_source
        
        # データがない場合
        if not data_to_use:
            return f'<div id="{self.element_id}" class="report-map-empty">風向風速データが見つかりません</div>'
        
        # 予測データ（設定がある場合）を取得
        forecast_data = None
        if self.get_property("compare_forecast"):
            forecast_source = self.get_property("forecast_source")
            if forecast_source and forecast_source in context:
                forecast_data = context[forecast_source]
        
        # 地形効果データ（設定がある場合）を取得
        terrain_data = None
        if self.get_property("show_terrain_effects"):
            terrain_source = self.get_property("terrain_source")
            if terrain_source and terrain_source in context:
                terrain_data = context[terrain_source]
        
        # CSS設定の取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # マップの設定
        center_auto = self.get_property("center_auto", True)
        center_lat = self.get_property("center_lat", 35.4498)
        center_lng = self.get_property("center_lng", 139.6649)
        zoom_level = self.get_property("zoom_level", 13)
        
        # 風の設定
        wind_speed_scale = self.get_property("wind_speed_scale", 0.01)
        vector_density = self.get_property("vector_density", 50)
        arrow_scale = self.get_property("arrow_scale", 1.0)
        min_velocity = self.get_property("min_velocity", 0)
        max_velocity = self.get_property("max_velocity", 15)
        velocity_units = self.get_property("velocity_units", "kt")
        interpolation_method = self.get_property("interpolation_method", "bilinear")
        
        # 表示設定
        show_wind_shifts = self.get_property("show_wind_shifts", False)
        show_wind_trends = self.get_property("show_wind_trends", False)
        compare_forecast = self.get_property("compare_forecast", False) and forecast_data is not None
        show_terrain_effects = self.get_property("show_terrain_effects", False) and terrain_data is not None
        
        # アニメーション（時間次元）の設定
        show_time_dimension = self.get_property("show_time_dimension", False)
        time_key = self.get_property("time_key", "timestamp")
        animation_duration = self.get_property("animation_duration", 1000)
        animation_loop = self.get_property("animation_loop", True)
        
        # マップの表示設定
        map_type = self.get_property("map_type", "osm")  # osm, satellite, nautical
        show_track = self.get_property("show_track", True)
        track_color = self.get_property("track_color", "rgba(54, 162, 235, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # データをJSON形式に変換
        data_json = json.dumps(data_to_use)
        forecast_json = json.dumps(forecast_data) if forecast_data else "null"
        terrain_json = json.dumps(terrain_data) if terrain_data else "null"
        
        # マップ設定をJSON形式に変換
        map_config = {
            "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "wind_speed_scale": wind_speed_scale,
            "vector_density": vector_density,
            "arrow_scale": arrow_scale,
            "min_velocity": min_velocity,
            "max_velocity": max_velocity,
            "velocity_units": velocity_units,
            "interpolation_method": interpolation_method,
            "show_wind_shifts": show_wind_shifts,
            "show_wind_trends": show_wind_trends,
            "compare_forecast": compare_forecast,
            "show_terrain_effects": show_terrain_effects,
            "show_time_dimension": show_time_dimension,
            "time_key": time_key,
            "animation_duration": animation_duration,
            "animation_loop": animation_loop,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width
        }
        
        map_config_json = json.dumps(map_config)
        
        # マップID
        map_id = self.get_property("map_id", f"wind_map_{uuid.uuid4().hex[:8]}")
        
        # 追加のCSS定義
        additional_css = """
        <style>
            .wind-field-legend {
                padding: 6px 8px;
                font: 14px/16px Arial, Helvetica, sans-serif;
                background: white;
                background: rgba(255, 255, 255, 0.8);
                box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
                border-radius: 5px;
                line-height: 18px;
                color: #555;
            }
            
            .wind-field-legend .legend-title {
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .wind-field-legend .legend-scale {
                display: flex;
                height: 15px;
                margin-bottom: 8px;
            }
            
            .wind-field-legend .legend-scale-segment {
                flex: 1;
                height: 100%;
            }
            
            .wind-field-legend .legend-labels {
                display: flex;
                justify-content: space-between;
                font-size: 12px;
            }
            
            .wind-arrow {
                stroke: rgba(0, 0, 0, 0.7);
                stroke-width: 1.5;
                fill: none;
            }
            
            .wind-shift-marker {
                stroke: purple;
                stroke-width: 2;
                fill: white;
                fill-opacity: 0.7;
            }
            
            .wind-trend-line {
                stroke: rgba(255, 165, 0, 0.8);
                stroke-width: 2;
                stroke-dasharray: 4;
                fill: none;
            }
            
            .terrain-effect-area {
                fill: rgba(255, 0, 0, 0.2);
                stroke: rgba(255, 0, 0, 0.5);
                stroke-width: 1;
            }
        </style>
        """
        
        # HTMLテンプレート
        html_content = f'''
        <div id="{self.element_id}" class="report-map-container" style="{css_style}">
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-velocity@1.7.0/dist/leaflet-velocity.min.css" />
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.1/dist/leaflet.timedimension.min.css" />
            {additional_css}
            
            <div id="{map_id}" style="width: {width}; height: {height};"></div>
            
            <script>
                (function() {{
                    // データの設定
                    var windData = {data_json};
                    var forecastData = {forecast_json};
                    var terrainData = {terrain_json};
                    var mapConfig = {map_config_json};
                    var mapId = "{map_id}";
                    
                    // JavaScriptファイルが存在する場合は、そこから読み込む
                    // 存在しない場合は、ベーシックな風の表示のみ実装する
                    {load_js_file(js_path)}
                }})();
            </script>
        </div>
        '''
        
        return html_content