# -*- coding: utf-8 -*-
"""
風場をベクトル表示するためのマップ要素
"""

from typing import Dict, List, Any, Optional
import json

from sailing_data_processor.reporting.elements.visualizations.map.base_map import BaseMapElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class WindFieldElement(BaseMapElement):
    """
    風場の可視化要素
    
    風向と風速のベクトル場を地図上に表示するための要素です。
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
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "wind_field"
        
        super().__init__(model, **kwargs)
    
    def get_chart_libraries(self) -> List[str]:
        """
        マップの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        libraries = super().get_chart_libraries()
        libraries.extend([
            "https://cdn.jsdelivr.net/npm/leaflet-velocity@1.7.0/dist/leaflet-velocity.min.js",
            "https://cdn.jsdelivr.net/npm/iso8601-js-period@0.2.1/iso8601.min.js",
            "https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.1/dist/leaflet.timedimension.min.js"
        ])
        return libraries
    
    def get_css_links(self) -> List[str]:
        """
        マップの描画に必要なCSSのリストを取得
        
        Returns
        -------
        List[str]
            CSSのURLリスト
        """
        css_links = super().get_css_links()
        css_links.extend([
            "https://cdn.jsdelivr.net/npm/leaflet-velocity@1.7.0/dist/leaflet-velocity.min.css",
            "https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.1/dist/leaflet.timedimension.min.css"
        ])
        return css_links
    
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
        
        # データソースからデータを取得
        data = None
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        # データがない場合
        if not data:
            return f'<div id="{self.element_id}" class="report-map-empty">風場データがありません</div>'
        
        # CSSスタイルの取得
        width, height = self.get_chart_dimensions()
        
        # ベースマップ設定の取得
        map_config = self.get_base_map_config()
        
        # 風場の設定
        wind_speed_scale = self.get_property("wind_speed_scale", 0.01)
        min_velocity = self.get_property("min_velocity", 0)
        max_velocity = self.get_property("max_velocity", 15)
        velocity_units = self.get_property("velocity_units", "kt")
        
        # タイムディメンション（時間変化）の設定
        show_time_dimension = self.get_property("show_time_dimension", False)
        time_key = self.get_property("time_key", "timestamp")
        animation_duration = self.get_property("animation_duration", 1000)
        animation_loop = self.get_property("animation_loop", True)
        
        # トラック設定
        show_track = self.get_property("show_track", True)
        track_color = self.get_property("track_color", "rgba(54, 162, 235, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # 設定を統合
        map_config.update({
            "wind_speed_scale": wind_speed_scale,
            "min_velocity": min_velocity,
            "max_velocity": max_velocity,
            "velocity_units": velocity_units,
            "show_time_dimension": show_time_dimension,
            "time_key": time_key,
            "animation_duration": animation_duration,
            "animation_loop": animation_loop,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width
        })
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        map_config_json = json.dumps(map_config)
        
        # 風場初期化用のJavaScriptコード
        wind_field_script = f'''
        <script>
            function initMapContent(map, mapData, mapConfig) {{
                // トラックポイントと風場データを抽出
                var trackPoints = [];
                var windFieldData = null;
                var latKey = 'lat';
                var lngKey = 'lng';
                
                // データ形式に応じて処理
                if (Array.isArray(mapData)) {{
                    // 配列形式の場合（トラックポイントの可能性）
                    if (mapData.length > 0 && typeof mapData[0] === 'object') {{
                        // 座標キーを特定
                        if ('latitude' in mapData[0] && 'longitude' in mapData[0]) {{
                            latKey = 'latitude';
                            lngKey = 'longitude';
                        }} else if ('lat' in mapData[0] && 'lon' in mapData[0]) {{
                            lngKey = 'lon';
                        }}
                        
                        // トラックポイントを抽出
                        for (var i = 0; i < mapData.length; i++) {{
                            var point = mapData[i];
                            if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                trackPoints.push([point[latKey], point[lngKey]]);
                            }}
                        }}
                    }}
                }} else if (typeof mapData === 'object') {{
                    // オブジェクト形式の場合
                    if ('track' in mapData && Array.isArray(mapData.track)) {{
                        for (var i = 0; i < mapData.track.length; i++) {{
                            var point = mapData.track[i];
                            if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                trackPoints.push([point[latKey], point[lngKey]]);
                            }}
                        }}
                    }}
                    
                    // 風場データの抽出
                    if ('wind_field' in mapData) {{
                        windFieldData = mapData.wind_field;
                    }} else if ('data' in mapData && 
                               (('u-wind' in mapData.data && 'v-wind' in mapData.data) || 
                                ('u_component' in mapData.data && 'v_component' in mapData.data))) {{
                        windFieldData = mapData.data;
                    }} else if ('u-wind' in mapData && 'v-wind' in mapData) {{
                        windFieldData = mapData;
                    }} else if ('u_component' in mapData && 'v_component' in mapData) {{
                        windFieldData = mapData;
                    }}
                }}
                
                // ポイントがない場合は中心座標を設定
                var bounds;
                if (trackPoints.length === 0 && !windFieldData) {{
                    map.setView(mapConfig.center, mapConfig.zoom_level);
                    return;
                }}
                
                // トラックラインを作成（表示設定がオンの場合）
                if (mapConfig.show_track && trackPoints.length > 0) {{
                    var trackLine = L.polyline(trackPoints, {{
                        color: mapConfig.track_color,
                        weight: mapConfig.track_width,
                        opacity: 0.8,
                        lineJoin: 'round'
                    }}).addTo(map);
                    
                    bounds = trackLine.getBounds();
                }}
                
                // 風場データをLeafletVelocity形式に変換
                if (windFieldData) {{
                    // 風場データを処理
                    var velocityData = [];
                    
                    // U成分（東西方向）とV成分（南北方向）のデータ
                    var uComponentKey = 'u-wind';
                    var vComponentKey = 'v-wind';
                    
                    if ('u_component' in windFieldData) {{
                        uComponentKey = 'u_component';
                        vComponentKey = 'v_component';
                    }}
                    
                    // 風速スケールを適用
                    var scale = mapConfig.wind_speed_scale || 0.01;
                    
                    // 風場データをLeaflet-Velocity形式に変換
                    if (uComponentKey in windFieldData && vComponentKey in windFieldData) {{
                        // U成分の設定
                        var uData = {{
                            header: {{
                                parameterUnit: mapConfig.velocity_units || "kt",
                                parameterNumberName: "eastward_wind",
                                parameterNumber: 2,
                                parameterCategory: 2,
                                dx: windFieldData.dx || 1,
                                dy: windFieldData.dy || 1,
                                la1: windFieldData.lat_min || mapConfig.center[0] - 0.1,
                                lo1: windFieldData.lon_min || mapConfig.center[1] - 0.1,
                                la2: windFieldData.lat_max || mapConfig.center[0] + 0.1,
                                lo2: windFieldData.lon_max || mapConfig.center[1] + 0.1,
                                nx: windFieldData.nx || windFieldData[uComponentKey].length,
                                ny: windFieldData.ny || windFieldData[uComponentKey][0].length,
                                refTime: new Date().toISOString()
                            }},
                            data: windFieldData[uComponentKey].flat().map(function(val) {{return val * scale; }})
                        }};
                        
                        // V成分の設定
                        var vData = {{
                            header: {{
                                parameterUnit: mapConfig.velocity_units || "kt",
                                parameterNumberName: "northward_wind",
                                parameterNumber: 3,
                                parameterCategory: 2,
                                dx: windFieldData.dx || 1,
                                dy: windFieldData.dy || 1,
                                la1: windFieldData.lat_min || mapConfig.center[0] - 0.1,
                                lo1: windFieldData.lon_min || mapConfig.center[1] - 0.1,
                                la2: windFieldData.lat_max || mapConfig.center[0] + 0.1,
                                lo2: windFieldData.lon_max || mapConfig.center[1] + 0.1,
                                nx: windFieldData.nx || windFieldData[uComponentKey].length,
                                ny: windFieldData.ny || windFieldData[uComponentKey][0].length,
                                refTime: new Date().toISOString()
                            }},
                            data: windFieldData[vComponentKey].flat().map(function(val) {{return val * scale; }})
                        }};
                        
                        velocityData.push(uData);
                        velocityData.push(vData);
                        
                        // 風場レイヤーを作成
                        var velocityLayer = L.velocityLayer({{
                            displayValues: true,
                            displayOptions: {{
                                velocityType: 'Wind',
                                position: 'bottomleft',
                                emptyString: 'No wind data',
                                angleConvention: 'bearingCW',
                                speedUnit: mapConfig.velocity_units || 'kt'
                            }},
                            data: velocityData,
                            minVelocity: mapConfig.min_velocity || 0,
                            maxVelocity: mapConfig.max_velocity || 15,
                            velocityScale: 0.1,
                            colorScale: ['rgb(0, 0, 255)', 'rgb(0, 255, 255)', 'rgb(0, 255, 0)', 'rgb(255, 255, 0)', 'rgb(255, 0, 0)']
                        }}).addTo(map);
                        
                        // 風場の範囲も考慮して境界を拡張
                        if (!bounds) {{
                            bounds = L.latLngBounds(
                                [uData.header.la1, uData.header.lo1],
                                [uData.header.la2, uData.header.lo2]
                            );
                        }} else {{
                            bounds.extend([uData.header.la1, uData.header.lo1]);
                            bounds.extend([uData.header.la2, uData.header.lo2]);
                        }}
                    }}
                }}
                
                // 自動的に全体が表示されるようにズーム
                if (mapConfig.center_auto && bounds) {{
                    map.fitBounds(bounds);
                }} else {{
                    map.setView(mapConfig.center, mapConfig.zoom_level);
                }}
            }}
        </script>
        '''
        
        # ベースマップHTMLをレンダリング
        return self.render_base_map_html(
            self.map_id, 
            width, 
            height, 
            map_config_json, 
            data_json, 
            wind_field_script
        )
