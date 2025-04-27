# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.visualizations.map_elements

マップ要素を提供するモジュールです。
航路追跡マップ、ヒートマップレイヤー、戦略ポイントレイヤー、風場の可視化などの
インタラクティブなマップ要素を実装します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
import uuid

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class TrackMapElement(BaseChartElement):
    """
    航路追跡マップ要素
    
    GPSトラックを地図上に表示するための要素です。
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
        # デフォルトでマップ要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.MAP
        
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "track_map"
        
        super().__init__(model, **kwargs)
        
        # マップIDを生成
        self.map_id = f"map_{self.element_id}_{str(uuid.uuid4())[:8]}"
    
    def get_chart_libraries(self) -> List[str]:
        """
        マップの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        return [
            "https://unpkg.com/leaflet@1.7.1/dist/leaflet.js",
            "https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.1/dist/leaflet.timedimension.min.js"
        ]
    
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
            return f'<div id="{self.element_id}" class="report-map-empty">GPSトラックデータがありません</div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # マップのデフォルト中心位置と拡大レベル
        center_auto = self.get_property("center_auto", True)
        center_lat = self.get_property("center_lat", 35.4498)
        center_lng = self.get_property("center_lng", 139.6649)
        zoom_level = self.get_property("zoom_level", 13)
        
        # マップのタイプと設定
        map_type = self.get_property("map_type", "osm")  # osm, satellite, nautical
        track_color = self.get_property("track_color", "rgba(255, 87, 34, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # タイムスライダーの設定
        show_time_slider = self.get_property("show_time_slider", False)
        time_key = self.get_property("time_key", "timestamp")
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        
        # マップ設定をJSON文字列に変換
        map_config = {}
            "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "track_color": track_color,
            "track_width": track_width,
            "show_time_slider": show_time_slider,
            "time_key": time_key
 "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "track_color": track_color,
            "track_width": track_width,
            "show_time_slider": show_time_slider,
            "time_key": time_key}
        
        map_config_json = json.dumps(map_config)
        
        # マップ要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-map-container" style="{css_style}">
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.1/dist/leaflet.timedimension.min.css" />
            
            <div id="{self.map_id}" style="width: {width}; height: {height};"></div>
            
            <script>
                (function() {{
                    // マップデータ
                    var mapData = data_json};
                    var mapConfig = {map_config_json};
                    
                    // マップ初期化
                    window.addEventListener('load', function() {{
                        // マップの作成
                        var map = L.map('self.map_id}');
                        
                        // タイルレイヤーの選択
                        var tileLayer;
                        switch(mapConfig.map_type) {{
                            case 'satellite':
                                tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}}/{y}}/{x}}', {attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                                }});
                                break;
                            case 'nautical':
                                tileLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{z}}/{x}}/{y}}.png', {attribution: 'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                                }});
                                break;
                            default:  // 'osm'
                                tileLayer = L.tileLayer('https://{s}}.tile.openstreetmap.org/{z}}/{x}}/{y}}.png', {attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                }});
                        }}
                        
                        // タイルレイヤーをマップに追加
                        tileLayer.addTo(map);
                        
                        // GPSトラックデータを処理
                        var trackPoints = [];
                        var timeValues = [];
                        var latKey = 'lat';
                        var lngKey = 'lng';
                        var timeKey = mapConfig.time_key || 'timestamp';
                        
                        // データ形式に応じて処理
                        if (Array.isArray(mapData)) {{
                            // 配列形式の場合
                            if (mapData.length > 0) {{
                                // 座標キーを特定
                                if (typeof mapData[0] === 'object') {{
                                    if ('latitude' in mapData[0] && 'longitude' in mapData[0]) {latKey = 'latitude';
                                        lngKey = 'longitude';
                                    }} else if ('lat' in mapData[0] && 'lon' in mapData[0]) {lngKey = 'lon';
                                    }}
                                }}
                                
                                // トラックポイントを抽出
                                for (var i = 0; i < mapData.length; i++) {{
                                    var point = mapData[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                        trackPoints.push([point[latKey], point[lngKey]]);
                                        
                                        // タイムスライダー用の時間値を抽出
                                        if (mapConfig.show_time_slider && timeKey in point) {{
                                            var time = point[timeKey];
                                            if (typeof time === 'string') {timeValues.push(new Date(time));
                                            }} else if (typeof time === 'number') {// Unixタイムスタンプの場合（秒単位）
                                                timeValues.push(new Date(time * 1000));
                                            }}
                                        }}
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
                                        
                                        // タイムスライダー用の時間値を抽出
                                        if (mapConfig.show_time_slider && timeKey in point) {{
                                            var time = point[timeKey];
                                            if (typeof time === 'string') {timeValues.push(new Date(time));
                                            }} else if (typeof time === 'number') {// Unixタイムスタンプの場合（秒単位）
                                                timeValues.push(new Date(time * 1000));
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }}
                        
                        // トラックポイントがない場合は中心座標を設定
                        if (trackPoints.length === 0) {map.setView(mapConfig.center, mapConfig.zoom_level);
                            return;
                        }}
                        
                        // トラックラインを作成
                        var trackLine = L.polyline(trackPoints, {color: mapConfig.track_color,
                            weight: mapConfig.track_width,
                            opacity: 0.8,
                            lineJoin: 'round'
                        }}).addTo(map);
                        
                        // スタート・ゴールマーカーを追加
                        var startPoint = trackPoints[0];
                        var endPoint = trackPoints[trackPoints.length - 1];
                        
                        var startIcon = L.divIcon({html: '<i class="fas fa-play-circle" style="color: green; font-size: 24px;"></i>',
                            className: 'track-start-icon',
                            iconSize: [24, 24],
                            iconAnchor: [12, 12]
                        }});
                        
                        var endIcon = L.divIcon({html: '<i class="fas fa-flag-checkered" style="color: red; font-size: 24px;"></i>',
                            className: 'track-end-icon',
                            iconSize: [24, 24],
                            iconAnchor: [12, 12]
                        }});
                        
                        L.marker(startPoint, {icon: startIcon }}).addTo(map);
                        L.marker(endPoint, {icon: endIcon }}).addTo(map);
                        
                        // 自動的にトラック全体が表示されるようにズーム
                        if (mapConfig.center_auto) {map.fitBounds(trackLine.getBounds());
                        }} else {map.setView(mapConfig.center, mapConfig.zoom_level);
                        }}
                        
                        // タイムスライダーの追加
                        if (mapConfig.show_time_slider && timeValues.length > 0) {{
                            // タイムディメンションの設定
                            var timeDimension = new L.TimeDimension({times: timeValues,
                                currentTime: timeValues[0].getTime()
                            }});
                            
                            map.timeDimension = timeDimension;
                            
                            // タイムディメンションコントロールを追加
                            var tdControl = new L.Control.TimeDimension({{
                                player: {buffer: 1,
                                    minBufferReady: 1,
                                    loop: true,
                                    transitionTime: 500
                                }}
                            }});
                            
                            map.addControl(tdControl);
                            
                            // タイムディメンション対応のトラックラインを作成
                            var geoJsonData = {{
                                "type": "FeatureCollection",
                                "features": [
                                    {{
                                        "type": "Feature",
                                        "properties": {{
                                            "time": timeValues.map(function(time) {return time.toISOString(); }})
                                        }},
                                        "geometry": {{
                                            "type": "LineString",
                                            "coordinates": trackPoints.map(function(point) {return [point[1], point[0]]; }})
                                        }}
                                    }}
                                ]
                            }};
                            
                            var tdGeoJsonLayer = L.timeDimension.layer.geoJson(
                                L.geoJson(geoJsonData, {{
                                    style: {color: mapConfig.track_color,
                                        weight: mapConfig.track_width,
                                        opacity: 0.8
                                    }}
                                }}),
                                {updateTimeDimension: true,
                                    addlastPoint: true,
                                    waitForReady: true
                                }}
                            );
                            
                            tdGeoJsonLayer.addTo(map);
                        }}
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content


class HeatMapLayerElement(BaseChartElement):
    """
    ヒートマップレイヤー要素
    
    速度、風速、角度などの分布を地図上にヒートマップとして表示するための要素です。
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
        # デフォルトでマップ要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.MAP
        
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "heatmap_layer"
        
        super().__init__(model, **kwargs)
        
        # マップIDを生成
        self.map_id = f"map_{self.element_id}_{str(uuid.uuid4())[:8]}"
    
    def get_chart_libraries(self) -> List[str]:
        """
        マップの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        return [
            "https://unpkg.com/leaflet@1.7.1/dist/leaflet.js",
            "https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js"
        ]
    
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
            return f'<div id="{self.element_id}" class="report-map-empty">ヒートマップデータがありません</div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # マップのデフォルト中心位置と拡大レベル
        center_auto = self.get_property("center_auto", True)
        center_lat = self.get_property("center_lat", 35.4498)
        center_lng = self.get_property("center_lng", 139.6649)
        zoom_level = self.get_property("zoom_level", 13)
        
        # ヒートマップの設定
        heat_value_key = self.get_property("heat_value_key", "value")
        max_value = self.get_property("max_value", None)
        radius = self.get_property("radius", 25)
        blur = self.get_property("blur", 15)
        gradient = self.get_property("gradient", {
            "0.4": "blue",
            "0.6": "cyan",
            "0.7": "lime",
            "0.8": "yellow",
            "1.0": "red"
 "0.4": "blue",
            "0.6": "cyan",
            "0.7": "lime",
            "0.8": "yellow",
            "1.0": "red"}
        })
        
        # マップのタイプと設定
        map_type = self.get_property("map_type", "osm")  # osm, satellite, nautical
        show_track = self.get_property("show_track", True)
        track_color = self.get_property("track_color", "rgba(255, 255, 255, 0.6)")
        track_width = self.get_property("track_width", 2)
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        
        # マップ設定をJSON文字列に変換
        map_config = {
            "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "heat_value_key": heat_value_key,
            "max_value": max_value,
            "radius": radius,
            "blur": blur,
            "gradient": gradient,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width
 "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "heat_value_key": heat_value_key,
            "max_value": max_value,
            "radius": radius,
            "blur": blur,
            "gradient": gradient,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width}
        
        map_config_json = json.dumps(map_config)
        
        # マップ要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-map-container" style="{css_style}">
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            
            <div id="{self.map_id}" style="width: {width}; height: {height};"></div>
            
            <script>
                (function() {{
                    // マップデータ
                    var mapData = data_json};
                    var mapConfig = {map_config_json};
                    
                    // マップ初期化
                    window.addEventListener('load', function() {{
                        // マップの作成
                        var map = L.map('self.map_id}');
                        
                        // タイルレイヤーの選択
                        var tileLayer;
                        switch(mapConfig.map_type) {{
                            case 'satellite':
                                tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}}/{y}}/{x}}', {attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                                }});
                                break;
                            case 'nautical':
                                tileLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{z}}/{x}}/{y}}.png', {attribution: 'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                                }});
                                break;
                            default:  // 'osm'
                                tileLayer = L.tileLayer('https://{s}}.tile.openstreetmap.org/{z}}/{x}}/{y}}.png', {attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                }});
                        }}
                        
                        // タイルレイヤーをマップに追加
                        tileLayer.addTo(map);
                        
                        // ヒートマップポイントとトラックポイントを抽出
                        var heatPoints = [];
                        var trackPoints = [];
                        var latKey = 'lat';
                        var lngKey = 'lng';
                        var valueKey = mapConfig.heat_value_key || 'value';
                        var maxValue = mapConfig.max_value || 0;
                        
                        // データ形式に応じて処理
                        if (Array.isArray(mapData)) {{
                            // 配列形式の場合
                            if (mapData.length > 0) {{
                                // 座標キーを特定
                                if (typeof mapData[0] === 'object') {{
                                    if ('latitude' in mapData[0] && 'longitude' in mapData[0]) {latKey = 'latitude';
                                        lngKey = 'longitude';
                                    }} else if ('lat' in mapData[0] && 'lon' in mapData[0]) {lngKey = 'lon';
                                    }}
                                }}
                                
                                // 最大値を計算（指定がない場合）
                                if (!maxValue && valueKey in mapData[0]) {maxValue = Math.max(...mapData.map(p => p[valueKey] || 0));
                                }}
                                
                                // ポイントを抽出
                                for (var i = 0; i < mapData.length; i++) {{
                                    var point = mapData[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                        // トラックポイントを追加
                                        trackPoints.push([point[latKey], point[lngKey]]);
                                        
                                        // ヒートマップポイントを追加
                                        var intensity = 0;
                                        if (valueKey in point) {intensity = maxValue ? point[valueKey] / maxValue : point[valueKey];
                                        }}
                                        
                                        heatPoints.push([point[latKey], point[lngKey], intensity]);
                                    }}
                                }}
                            }}
                        }} else if (typeof mapData === 'object') {{
                            // オブジェクト形式の場合
                            var pointsArray = mapData.points || mapData.data || [];
                            
                            if (Array.isArray(pointsArray) && pointsArray.length > 0) {{
                                // 最大値を計算（指定がない場合）
                                if (!maxValue && valueKey in pointsArray[0]) {maxValue = Math.max(...pointsArray.map(p => p[valueKey] || 0));
                                }}
                                
                                // ポイントを抽出
                                for (var i = 0; i < pointsArray.length; i++) {{
                                    var point = pointsArray[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                        // トラックポイントを追加
                                        trackPoints.push([point[latKey], point[lngKey]]);
                                        
                                        // ヒートマップポイントを追加
                                        var intensity = 0;
                                        if (valueKey in point) {intensity = maxValue ? point[valueKey] / maxValue : point[valueKey];
                                        }}
                                        
                                        heatPoints.push([point[latKey], point[lngKey], intensity]);
                                    }}
                                }}
                            }}
                        }}
                        
                        // ポイントがない場合は中心座標を設定
                        if (trackPoints.length === 0) {map.setView(mapConfig.center, mapConfig.zoom_level);
                            return;
                        }}
                        
                        // トラックラインを作成（表示設定がオンの場合）
                        if (mapConfig.show_track) {{
                            var trackLine = L.polyline(trackPoints, {color: mapConfig.track_color,
                                weight: mapConfig.track_width,
                                opacity: 0.8,
                                lineJoin: 'round'
                            }}).addTo(map);
                        }}
                        
                        // ヒートマップレイヤーを作成
                        var heat = L.heatLayer(heatPoints, {radius: mapConfig.radius,
                            blur: mapConfig.blur,
                            maxZoom: 18,
                            gradient: mapConfig.gradient
                        }}).addTo(map);
                        
                        // 自動的にトラック全体が表示されるようにズーム
                        if (mapConfig.center_auto && trackPoints.length > 0) {var bounds = L.latLngBounds(trackPoints);
                            map.fitBounds(bounds);
                        }} else {map.setView(mapConfig.center, mapConfig.zoom_level);
                        }}
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content


class StrategyPointLayerElement(BaseChartElement):
    """
    戦略ポイントレイヤー要素
    
    重要な戦略ポイントを地図上に表示するための要素です。
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
        # デフォルトでマップ要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.MAP
        
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "strategy_point_layer"
        
        super().__init__(model, **kwargs)
        
        # マップIDを生成
        self.map_id = f"map_{self.element_id}_{str(uuid.uuid4())[:8]}"
    
    def get_chart_libraries(self) -> List[str]:
        """
        マップの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        return [
            "https://unpkg.com/leaflet@1.7.1/dist/leaflet.js",
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/js/all.min.js"
        ]
    
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
            return f'<div id="{self.element_id}" class="report-map-empty">戦略ポイントデータがありません</div>'
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # マップのデフォルト中心位置と拡大レベル
        center_auto = self.get_property("center_auto", True)
        center_lat = self.get_property("center_lat", 35.4498)
        center_lng = self.get_property("center_lng", 139.6649)
        zoom_level = self.get_property("zoom_level", 13)
        
        # マップのタイプと設定
        map_type = self.get_property("map_type", "osm")  # osm, satellite, nautical
        show_track = self.get_property("show_track", True)
        track_color = self.get_property("track_color", "rgba(54, 162, 235, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # ポイントタイプ別のアイコン設定
        point_icons = self.get_property("point_icons", {
            "tack": "color": "blue", "icon": "exchange-alt"},
            "gybe": {"color": "green", "icon": "random"},
            "mark_rounding": {"color": "red", "icon": "flag-checkered"},
            "wind_shift": {"color": "purple", "icon": "wind"},
            "default": {"color": "gray", "icon": "map-marker-alt"}
 {
            "tack": "color": "blue", "icon": "exchange-alt"},
            "gybe": {"color": "green", "icon": "random"},
            "mark_rounding": {"color": "red", "icon": "flag-checkered"},
            "wind_shift": {"color": "purple", "icon": "wind"},
            "default": {"color": "gray", "icon": "map-marker-alt"}}
        })
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        
        # マップ設定をJSON文字列に変換
        map_config = {
            "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width,
            "point_icons": point_icons
 "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width,
            "point_icons": point_icons}
        
        map_config_json = json.dumps(map_config)
        
        # マップ要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-map-container" style="{css_style}">
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" />
            
            <style>
                .strategy-point-icon {display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    color: white;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
                }}
                
                .strategy-point-popup {min-width: 200px;
                }}
                
                .strategy-point-popup h4 {margin: 0 0 8px 0;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #eee;
                }}
                
                .strategy-point-popup p {margin: 5px 0;
                }}
            </style>
            
            <div id="{self.map_id}" style="width: {width}; height: {height};"></div>
            
            <script>
                (function() {{
                    // マップデータ
                    var mapData = data_json};
                    var mapConfig = {map_config_json};
                    
                    // マップ初期化
                    window.addEventListener('load', function() {{
                        // マップの作成
                        var map = L.map('self.map_id}');
                        
                        // タイルレイヤーの選択
                        var tileLayer;
                        switch(mapConfig.map_type) {{
                            case 'satellite':
                                tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}}/{y}}/{x}}', {attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                                }});
                                break;
                            case 'nautical':
                                tileLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{z}}/{x}}/{y}}.png', {attribution: 'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                                }});
                                break;
                            default:  // 'osm'
                                tileLayer = L.tileLayer('https://{s}}.tile.openstreetmap.org/{z}}/{x}}/{y}}.png', {attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                }});
                        }}
                        
                        // タイルレイヤーをマップに追加
                        tileLayer.addTo(map);
                        
                        // トラックポイントと戦略ポイントを抽出
                        var trackPoints = [];
                        var strategyPoints = [];
                        var latKey = 'lat';
                        var lngKey = 'lng';
                        
                        // データ形式に応じて処理
                        if (Array.isArray(mapData)) {{
                            // 配列形式の場合
                            strategyPoints = mapData;
                            
                            // 座標キーを特定
                            if (mapData.length > 0 && typeof mapData[0] === 'object') {{
                                if ('latitude' in mapData[0] && 'longitude' in mapData[0]) {latKey = 'latitude';
                                    lngKey = 'longitude';
                                }} else if ('lat' in mapData[0] && 'lon' in mapData[0]) {lngKey = 'lon';
                                }}
                            }}
                            
                            // トラックポイントを生成
                            for (var i = 0; i < mapData.length; i++) {{
                                var point = mapData[i];
                                if (typeof point === 'object' && point[latKey] && point[lngKey]) {trackPoints.push([point[latKey], point[lngKey]]);
                                }}
                            }}
                        }} else if (typeof mapData === 'object') {{
                            // オブジェクト形式の場合
                            if ('track' in mapData && Array.isArray(mapData.track)) {{
                                for (var i = 0; i < mapData.track.length; i++) {{
                                    var point = mapData.track[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {trackPoints.push([point[latKey], point[lngKey]]);
                                    }}
                                }}
                            }}
                            
                            if ('points' in mapData && Array.isArray(mapData.points)) {strategyPoints = mapData.points;
                            }}
                        }}
                        
                        // ポイントがない場合は中心座標を設定
                        if (trackPoints.length === 0 && strategyPoints.length === 0) {map.setView(mapConfig.center, mapConfig.zoom_level);
                            return;
                        }}
                        
                        // トラックラインを作成（表示設定がオンの場合）
                        var bounds;
                        if (mapConfig.show_track && trackPoints.length > 0) {{
                            var trackLine = L.polyline(trackPoints, {color: mapConfig.track_color,
                                weight: mapConfig.track_width,
                                opacity: 0.8,
                                lineJoin: 'round'
                            }}).addTo(map);
                            
                            bounds = trackLine.getBounds();
                        }}
                        
                        // 戦略ポイントを追加
                        for (var i = 0; i < strategyPoints.length; i++) {{
                            var point = strategyPoints[i];
                            if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                var latLng = [point[latKey], point[lngKey]];
                                
                                // ポイントタイプに基づいてアイコンを選択
                                var pointType = point.type || 'default';
                                var iconConfig = mapConfig.point_icons[pointType] || mapConfig.point_icons.default;
                                
                                // アイコンの作成
                                var divIcon = L.divIcon({html: '<div class="strategy-point-icon" style="background-color: ' + iconConfig.color + ';">' +
                                          '<i class="fas fa-' + iconConfig.icon + '"></i></div>',
                                    className: 'strategy-point-div-icon',
                                    iconSize: [32, 32],
                                    iconAnchor: [16, 16]
                                }});
                                
                                // マーカーの作成
                                var marker = L.marker(latLng, {icon: divIcon,
                                    title: point.name || point.description || pointType
                                }}).addTo(map);
                                
                                // ポップアップの追加
                                var popupContent = '<div class="strategy-point-popup">';
                                if (point.name) popupContent += '<h4>' + point.name + '</h4>';
                                if (point.type) popupContent += '<p><strong>タイプ:</strong> ' + point.type + '</p>';
                                if (point.description) popupContent += '<p>' + point.description + '</p>';
                                if (point.time) popupContent += '<p><strong>時間:</strong> ' + point.time + '</p>';
                                if (point.value) popupContent += '<p><strong>値:</strong> ' + point.value + '</p>';
                                popupContent += '</div>';
                                
                                marker.bindPopup(popupContent);
                                
                                // 境界を更新
                                if (!bounds) {bounds = L.latLngBounds([latLng]);
                                }} else {bounds.extend(latLng);
                                }}
                            }}
                        }}
                        
                        // 自動的にポイント全体が表示されるようにズーム
                        if (mapConfig.center_auto && bounds) {map.fitBounds(bounds);
                        }} else {map.setView(mapConfig.center, mapConfig.zoom_level);
                        }}
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content


class WindFieldElement(BaseChartElement):
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
        # デフォルトでマップ要素タイプを設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.MAP
        
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "wind_field"
        
        super().__init__(model, **kwargs)
        
        # マップIDを生成
        self.map_id = f"map_{self.element_id}_{str(uuid.uuid4())[:8]}"
    
    def get_chart_libraries(self) -> List[str]:
        """
        マップの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        return [
            "https://unpkg.com/leaflet@1.7.1/dist/leaflet.js",
            "https://cdn.jsdelivr.net/npm/leaflet-velocity@1.7.0/dist/leaflet-velocity.min.js",
            "https://cdn.jsdelivr.net/npm/iso8601-js-period@0.2.1/iso8601.min.js",
            "https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.1/dist/leaflet.timedimension.min.js"
        ]
    
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
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # マップのデフォルト中心位置と拡大レベル
        center_auto = self.get_property("center_auto", True)
        center_lat = self.get_property("center_lat", 35.4498)
        center_lng = self.get_property("center_lng", 139.6649)
        zoom_level = self.get_property("zoom_level", 13)
        
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
        
        # マップのタイプと設定
        map_type = self.get_property("map_type", "osm")  # osm, satellite, nautical
        show_track = self.get_property("show_track", True)
        track_color = self.get_property("track_color", "rgba(54, 162, 235, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        
        # マップ設定をJSON文字列に変換
        map_config = {
            "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
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
 "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
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
            "track_width": track_width}
        
        map_config_json = json.dumps(map_config)
        
        # マップ要素のレンダリング
        html_content = f'''
        <div id="{self.element_id}" class="report-map-container" style="{css_style}">
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-velocity@1.7.0/dist/leaflet-velocity.min.css" />
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.1/dist/leaflet.timedimension.min.css" />
            
            <div id="{self.map_id}" style="width: {width}; height: {height};"></div>
            
            <script>
                (function() {{
                    // マップデータ
                    var mapData = data_json};
                    var mapConfig = {map_config_json};
                    
                    // マップ初期化
                    window.addEventListener('load', function() {{
                        // マップの作成
                        var map = L.map('self.map_id}');
                        
                        // タイルレイヤーの選択
                        var tileLayer;
                        switch(mapConfig.map_type) {{
                            case 'satellite':
                                tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}}/{y}}/{x}}', {attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                                }});
                                break;
                            case 'nautical':
                                tileLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{z}}/{x}}/{y}}.png', {attribution: 'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                                }});
                                break;
                            default:  // 'osm'
                                tileLayer = L.tileLayer('https://{s}}.tile.openstreetmap.org/{z}}/{x}}/{y}}.png', {attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                }});
                        }}
                        
                        // タイルレイヤーをマップに追加
                        tileLayer.addTo(map);
                        
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
                                if ('latitude' in mapData[0] && 'longitude' in mapData[0]) {latKey = 'latitude';
                                    lngKey = 'longitude';
                                }} else if ('lat' in mapData[0] && 'lon' in mapData[0]) {lngKey = 'lon';
                                }}
                                
                                // トラックポイントを抽出
                                for (var i = 0; i < mapData.length; i++) {{
                                    var point = mapData[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {trackPoints.push([point[latKey], point[lngKey]]);
                                    }}
                                }}
                            }}
                        }} else if (typeof mapData === 'object') {{
                            // オブジェクト形式の場合
                            if ('track' in mapData && Array.isArray(mapData.track)) {{
                                for (var i = 0; i < mapData.track.length; i++) {{
                                    var point = mapData.track[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {trackPoints.push([point[latKey], point[lngKey]]);
                                    }}
                                }}
                            }}
                            
                            // 風場データの抽出
                            if ('wind_field' in mapData) {windFieldData = mapData.wind_field;
                            }} else if ('data' in mapData && 
                                      (('u-wind' in mapData.data && 'v-wind' in mapData.data) || 
                                       ('u_component' in mapData.data && 'v_component' in mapData.data))) {windFieldData = mapData.data;
                            }} else if ('u-wind' in mapData && 'v-wind' in mapData) {windFieldData = mapData;
                            }} else if ('u_component' in mapData && 'v_component' in mapData) {windFieldData = mapData;
                            }}
                        }}
                        
                        // ポイントがない場合は中心座標を設定
                        var bounds;
                        if (trackPoints.length === 0 && !windFieldData) {map.setView(mapConfig.center, mapConfig.zoom_level);
                            return;
                        }}
                        
                        // トラックラインを作成（表示設定がオンの場合）
                        if (mapConfig.show_track && trackPoints.length > 0) {{
                            var trackLine = L.polyline(trackPoints, {color: mapConfig.track_color,
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
                            
                            if ('u_component' in windFieldData) {uComponentKey = 'u_component';
                                vComponentKey = 'v_component';
                            }}
                            
                            // 風速スケールを適用
                            var scale = mapConfig.wind_speed_scale || 0.01;
                            
                            // 風場データをLeaflet-Velocity形式に変換
                            if (uComponentKey in windFieldData && vComponentKey in windFieldData) {{
                                // U成分の設定
                                var uData = {{
                                    header: {parameterUnit: mapConfig.velocity_units || "kt",
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
                                    data: windFieldData[uComponentKey].flat().map(function(val) {return val * scale; }})
                                }};
                                
                                // V成分の設定
                                var vData = {{
                                    header: {parameterUnit: mapConfig.velocity_units || "kt",
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
                                    data: windFieldData[vComponentKey].flat().map(function(val) {return val * scale; }})
                                }};
                                
                                velocityData.push(uData);
                                velocityData.push(vData);
                                
                                // 風場レイヤーを作成
                                var velocityLayer = L.velocityLayer({{
                                    displayValues: true,
                                    displayOptions: {velocityType: 'Wind',
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
                                if (!bounds) {bounds = L.latLngBounds(
                                        [uData.header.la1, uData.header.lo1],
                                        [uData.header.la2, uData.header.lo2]
                                    );
                                }} else {bounds.extend([uData.header.la1, uData.header.lo1]);
                                    bounds.extend([uData.header.la2, uData.header.lo2]);
                                }}
                            }}
                        }}
                        
                        // 自動的に全体が表示されるようにズーム
                        if (mapConfig.center_auto && bounds) {map.fitBounds(bounds);
                        }} else {map.setView(mapConfig.center, mapConfig.zoom_level);
                        }}
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content
