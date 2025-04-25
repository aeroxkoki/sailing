# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map.course_elements

セーリングコースの要素（マーク、スタートライン、レイライン等）を管理するモジュール。
このモジュールは、コース上の様々な要素とその視覚化機能を定義します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid

from sailing_data_processor.reporting.elements.visualizations.map_elements import StrategyPointLayerElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class CourseElementsLayer(StrategyPointLayerElement):
    """
    コース要素レイヤー
    
    セーリングコース上のマーク、ライン、レイライン、戦略ポイントを管理します。
    現在のコース状態を視覚化するためのレイヤーです。
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
        
        # マーク設定の初期化
        self.set_property("marks", self.get_property("marks", []))
        self.set_property("course_shape", self.get_property("course_shape", "windward_leeward"))
        self.set_property("start_line", self.get_property("start_line", {}))
        self.set_property("finish_line", self.get_property("finish_line", {}))
        
        # レイライン設定の初期化
        self.set_property("show_laylines", self.get_property("show_laylines", True))
        self.set_property("tacking_angle", self.get_property("tacking_angle", 90))
        self.set_property("layline_style", self.get_property("layline_style", {
            "color": "rgba(255, 0, 0, 0.6)",
            "weight": 2,
            "dashArray": "5,5"
 {
            "color": "rgba(255, 0, 0, 0.6)",
            "weight": 2,
            "dashArray": "5,5"}
        }))
        
        # 戦略設定の初期化
        self.set_property("strategy_points", self.get_property("strategy_points", []))
        self.set_property("optimal_route", self.get_property("optimal_route", []))
        self.set_property("risk_areas", self.get_property("risk_areas", []))
    
    def add_mark(self, lat: float, lng: float, mark_type: str = "rounding", 
               options: Dict[str, Any] = None) -> None:
        """
        マークを追加
        
        Parameters
        ----------
        lat : float
            緯度
        lng : float
            経度
        mark_type : str, optional
            マークタイプ, by default "rounding"
        options : Dict[str, Any], optional
            マークの追加設定, by default None
        """
        if options is None:
            options = {}
        
        marks = self.get_property("marks", [])
        marks.append({
            "lat": lat,
            "lng": lng,
            "type": mark_type,
            **options
        })
        
        self.set_property("marks", marks)
    
    def set_start_line(self, pin: Dict[str, float], boat: Dict[str, float], 
                      options: Dict[str, Any] = None) -> None:
        """
        スタートラインを設定
        
        Parameters
        ----------
        pin : Dict[str, float]
            ピン側 {lat, lng}
        boat : Dict[str, float]
            コミッティボート側 {lat, lng}
        options : Dict[str, Any], optional
            ラインの追加設定, by default None
        """
        if options is None:
            options = {}
        
        start_line = {
            "pin": pin,
            "boat": boat,
 {
            "pin": pin,
            "boat": boat,}
            **options
        }
        
        self.set_property("start_line", start_line)
    
    def add_strategy_point(self, lat: float, lng: float, point_type: str, 
                         options: Dict[str, Any] = None) -> None:
        """
        戦略ポイントを追加
        
        Parameters
        ----------
        lat : float
            緯度
        lng : float
            経度
        point_type : str
            ポイントタイプ (advantage, caution, information, etc.)
        options : Dict[str, Any], optional
            ポイントの追加設定, by default None
        """
        if options is None:
            options = {}
        
        points = self.get_property("strategy_points", [])
        points.append({
            "lat": lat,
            "lng": lng,
            "type": point_type,
            **options
        })
        
        self.set_property("strategy_points", points)
    
    def add_risk_area(self, polygon: List[Dict[str, float]], risk_type: str = "caution", 
                    options: Dict[str, Any] = None) -> None:
        """
        リスクエリアを追加
        
        Parameters
        ----------
        polygon : List[Dict[str, float]]
            エリアの座標点リスト [{lat, lng}, ...]
        risk_type : str, optional
            リスクタイプ, by default "caution"
        options : Dict[str, Any], optional
            エリアの追加設定, by default None
        """
        if options is None:
            options = {}
        
        areas = self.get_property("risk_areas", [])
        areas.append({
            "polygon": polygon,
            "type": risk_type,
            **options
        })
        
        self.set_property("risk_areas", areas)
    
    def set_optimal_route(self, points: List[Dict[str, float]], 
                        options: Dict[str, Any] = None) -> None:
        """
        最適ルートを設定
        
        Parameters
        ----------
        points : List[Dict[str, float]]
            ルート上のポイントリスト [{lat, lng}, ...]
        options : Dict[str, Any], optional
            ルートの追加設定, by default None
        """
        if options is None:
            options = {}
        
        route = {
            "points": points,
 {
            "points": points,}
            **options
        }
        
        self.set_property("optimal_route", route)
    
    def get_chart_libraries(self) -> List[str]:
        """
        必要なJavaScriptライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        libraries = super().get_chart_libraries()
        
        # 追加のライブラリ
        additional_libraries = [
            "https://cdn.jsdelivr.net/npm/leaflet-geometryutil@0.9.3/src/leaflet.geometryutil.min.js"
        ]
        
        return libraries + additional_libraries
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        HTMLとしてレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        # 条件評価
        if not self.evaluate_conditions(context):
            return ""
        
        # コンテキストからデータソースを取得
        data = None
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        # データがない場合は空のデータセットを用意（エラー回避）
        if not data:
            data = {"points": []}
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # マップの設定
        center_auto = self.get_property("center_auto", True)
        center_lat = self.get_property("center_lat", 35.4498)
        center_lng = self.get_property("center_lng", 139.6649)
        zoom_level = self.get_property("zoom_level", 13)
        
        # マークの設定
        marks = self.get_property("marks", [])
        course_shape = self.get_property("course_shape", "windward_leeward")
        start_line = self.get_property("start_line", {})
        finish_line = self.get_property("finish_line", {})
        
        # レイラインの設定
        show_laylines = self.get_property("show_laylines", True)
        tacking_angle = self.get_property("tacking_angle", 90)
        layline_style = self.get_property("layline_style", {
            "color": "rgba(255, 0, 0, 0.6)",
            "weight": 2,
            "dashArray": "5,5"
 {
            "color": "rgba(255, 0, 0, 0.6)",
            "weight": 2,
            "dashArray": "5,5"}
        })
        
        # 戦略設定
        strategy_points = self.get_property("strategy_points", [])
        optimal_route = self.get_property("optimal_route", [])
        risk_areas = self.get_property("risk_areas", [])
        
        # マップの表示設定
        map_type = self.get_property("map_type", "osm")
        show_track = self.get_property("show_track", True)
        track_color = self.get_property("track_color", "rgba(54, 162, 235, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # ポイントアイコン設定
        point_icons = self.get_property("point_icons", {
            "mark": {"color": "red", "icon": "map-marker-alt"},
            "start": {"color": "green", "icon": "flag"},
            "finish": {"color": "blue", "icon": "flag-checkered"},
            "advantage": {"color": "green", "icon": "thumbs-up"},
            "caution": {"color": "orange", "icon": "exclamation-triangle"},
            "information": {"color": "blue", "icon": "info-circle"},
            "default": {"color": "gray", "icon": "map-marker-alt"}
 {
            "mark": {"color": "red", "icon": "map-marker-alt"},
            "start": {"color": "green", "icon": "flag"},
            "finish": {"color": "blue", "icon": "flag-checkered"},
            "advantage": {"color": "green", "icon": "thumbs-up"},
            "caution": {"color": "orange", "icon": "exclamation-triangle"},
            "information": {"color": "blue", "icon": "info-circle"},
            "default": {"color": "gray", "icon": "map-marker-alt"}}
        })
        
        # データをJSON形式に変換
        data_json = json.dumps(data)
        
        # コース設定をJSON形式に変換
        course_config = {
            "marks": marks,
            "course_shape": course_shape,
            "start_line": start_line,
            "finish_line": finish_line,
            "show_laylines": show_laylines,
            "tacking_angle": tacking_angle,
            "layline_style": layline_style,
            "strategy_points": strategy_points,
            "optimal_route": optimal_route,
            "risk_areas": risk_areas
 {
            "marks": marks,
            "course_shape": course_shape,
            "start_line": start_line,
            "finish_line": finish_line,
            "show_laylines": show_laylines,
            "tacking_angle": tacking_angle,
            "layline_style": layline_style,
            "strategy_points": strategy_points,
            "optimal_route": optimal_route,
            "risk_areas": risk_areas}
        }
        
        course_config_json = json.dumps(course_config)
        
        # マップ設定をJSON形式に変換
        map_config = {
            "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width,
            "point_icons": point_icons
 {
            "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width,
            "point_icons": point_icons}
        }
        
        map_config_json = json.dumps(map_config)
        
        # 追加のCSS定義
        additional_css = """
        <style>
            .course-mark-icon {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                color: white;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
            
            .start-line {
                stroke: green;
                stroke-width: 3;
                stroke-opacity: 0.8;
            
            .finish-line {
                stroke: blue;
                stroke-width: 3;
                stroke-opacity: 0.8;
            
            .layline {
                stroke-dasharray: 5, 5;
                stroke-opacity: 0.6;
            
            .optimal-route {
                stroke: rgba(0, 128, 0, 0.8);
                stroke-width: 3;
                stroke-opacity: 0.8;
            
            .risk-area {
                fill-opacity: 0.3;
                stroke-opacity: 0.6;
            
            .risk-area-caution {
                fill: rgba(255, 165, 0, 0.3);
                stroke: rgba(255, 165, 0, 0.8);
            
            .risk-area-danger {
                fill: rgba(255, 0, 0, 0.3);
                stroke: rgba(255, 0, 0, 0.8);
            
            .risk-area-information {
                fill: rgba(0, 0, 255, 0.2);
                stroke: rgba(0, 0, 255, 0.6);
            
            .course-popup {
                min-width: 200px;
            
            .course-popup h4 {
                margin: 0 0 8px 0;
                padding-bottom: 5px;
                border-bottom: 1px solid #eee;
            
            .course-popup p {
                margin: 5px 0;
        </style>
        """
        
        # 完全なHTMLコンテンツ
        html_content = f'''
        <div id="{self.element_id}" class="report-map-container" style="{css_style}">
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" />
            {additional_css}
            
            <div id="{self.map_id}" style="width: {width}; height: {height};"></div>
            
            <script>
                (function() {{
                    // 基本データ
                    var courseData = {data_json};
                    var courseConfig = {course_config_json};
                    var mapConfig = {map_config_json};
                    
                    // 初期化関数
                    window.addEventListener('load', function() {{
                        // マップの作成
                        var map = L.map('{self.map_id}');
                        
                        // ベースマップの選択
                        var tileLayer;
                        switch(mapConfig.map_type) {{
                            case 'satellite':
                                tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                                }});
                                break;
                            case 'nautical':
                                tileLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{{z}}/{{x}}/{{y}}.png', {{
                                    attribution: 'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                                }});
                                break;
                            default:  // 'osm'
                                tileLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                }});
                        }}
                        
                        // ベースマップをマップに追加
                        tileLayer.addTo(map);
                        
                        // 座標データの情報を取得
                        var trackPoints = [];
                        var latKey = 'lat';
                        var lngKey = 'lng';
                        
                        // データ形式をチェック
                        if (Array.isArray(courseData)) {{
                            // 配列形式の場合、座標データの取得
                            if (courseData.length > 0 && typeof courseData[0] === 'object') {{
                                // キー名の確認
                                if ('latitude' in courseData[0] && 'longitude' in courseData[0]) {{
                                    latKey = 'latitude';
                                    lngKey = 'longitude';
                                }} else if ('lat' in courseData[0] && 'lon' in courseData[0]) {{
                                    lngKey = 'lon';
                                }}
                                
                                // 座標ポイントを追加
                                for (var i = 0; i < courseData.length; i++) {{
                                    var point = courseData[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                        trackPoints.push([point[latKey], point[lngKey]]);
                                    }}
                                }}
                            }}
                        }} else if (typeof courseData === 'object') {{
                            // オブジェクト形式の場合
                            if ('track' in courseData && Array.isArray(courseData.track)) {{
                                for (var i = 0; i < courseData.track.length; i++) {{
                                    var point = courseData.track[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                        trackPoints.push([point[latKey], point[lngKey]]);
                                    }}
                                }}
                            }} else if ('points' in courseData && Array.isArray(courseData.points)) {{
                                for (var i = 0; i < courseData.points.length; i++) {{
                                    var point = courseData.points[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                        trackPoints.push([point[latKey], point[lngKey]]);
                                    }}
                                }}
                            }}
                        }}
                        
                        // レイヤーグループの作成
                        var trackLayer = L.layerGroup();
                        var markLayer = L.layerGroup();
                        var lineLayer = L.layerGroup();
                        var laylinesLayer = L.layerGroup();
                        var strategyLayer = L.layerGroup();
                        var routeLayer = L.layerGroup();
                        var riskLayer = L.layerGroup();
                        
                        // オーバーレイのリスト作成
                        var overlays = {{}};
                        
                        // トラック表示（GPS航跡の場合）
                        if (mapConfig.show_track && trackPoints.length > 0) {{
                            var trackLine = L.polyline(trackPoints, {{
                                color: mapConfig.track_color,
                                weight: mapConfig.track_width,
                                opacity: 0.8,
                                lineJoin: 'round'
                            }}).addTo(trackLayer);
                            
                            overlays["GPS航跡"] = trackLayer;
                            trackLayer.addTo(map);
                        }}
                        
                        // マークの表示
                        if (courseConfig.marks && courseConfig.marks.length > 0) {{
                            courseConfig.marks.forEach(function(mark) {{
                                // アイコン設定を取得
                                var iconConfig = mapConfig.point_icons[mark.type] || mapConfig.point_icons.mark || mapConfig.point_icons.default;
                                var iconColor = mark.color || iconConfig.color || 'red';
                                var iconName = mark.icon || iconConfig.icon || 'map-marker-alt';
                                
                                // アイコンを作成
                                var markIcon = L.divIcon({{
                                    html: '<div class="course-mark-icon" style="background-color: ' + iconColor + ';"><i class="fas fa-' + iconName + '"></i></div>',
                                    className: 'course-mark-icon-wrapper',
                                    iconSize: [32, 32],
                                    iconAnchor: [16, 16]
                                }});
                                
                                // マーカーの作成
                                var marker = L.marker([mark.lat, mark.lng], {{
                                    icon: markIcon,
                                    title: mark.name || 'Mark'
                                }}).addTo(markLayer);
                                
                                // ポップアップの内容
                                var popupContent = '<div class="course-popup">';
                                popupContent += '<h4>' + (mark.name || 'Mark') + '</h4>';
                                if (mark.description) popupContent += '<p>' + mark.description + '</p>';
                                popupContent += '<p><strong>タイプ:</strong> ' + mark.type + '</p>';
                                if (mark.rounding_direction) popupContent += '<p><strong>回航方向:</strong> ' + mark.rounding_direction + '</p>';
                                popupContent += '</div>';
                                
                                marker.bindPopup(popupContent);
                            }});
                            
                            overlays["コースマーク"] = markLayer;
                            markLayer.addTo(map);
                        }}
                        
                        // スタートラインの表示
                        if (courseConfig.start_line && courseConfig.start_line.pin && courseConfig.start_line.boat) {{
                            var pinPos = [courseConfig.start_line.pin.lat, courseConfig.start_line.pin.lng];
                            var boatPos = [courseConfig.start_line.boat.lat, courseConfig.start_line.boat.lng];
                            
                            // ラインを作成
                            var startLine = L.polyline([pinPos, boatPos], {{
                                color: 'green',
                                weight: 3,
                                opacity: 0.8,
                                className: 'start-line'
                            }}).addTo(lineLayer);
                            
                            // ピン側のマーカー
                            var pinIcon = L.divIcon({{
                                html: '<div class="course-mark-icon" style="background-color: green;"><i class="fas fa-flag"></i></div>',
                                className: 'course-mark-icon-wrapper',
                                iconSize: [24, 24],
                                iconAnchor: [12, 12]
                            }});
                            
                            var pinMarker = L.marker(pinPos, {{
                                icon: pinIcon,
                                title: 'Start Line (Pin End)'
                            }}).addTo(lineLayer);
                            
                            // コミッティボート側のマーカー
                            var boatIcon = L.divIcon({{
                                html: '<div class="course-mark-icon" style="background-color: green;"><i class="fas fa-ship"></i></div>',
                                className: 'course-mark-icon-wrapper',
                                iconSize: [24, 24],
                                iconAnchor: [12, 12]
                            }});
                            
                            var boatMarker = L.marker(boatPos, {{
                                icon: boatIcon,
                                title: 'Start Line (Boat End)'
                            }}).addTo(lineLayer);
                            
                            // ポップアップ
                            var lineLength = L.GeometryUtil.length(startLine);
                            
                            startLine.bindPopup('<div class="course-popup"><h4>スタートライン</h4>' +
                                              '<p><strong>長さ:</strong> ' + lineLength.toFixed(1) + ' m</p>' +
                                              '</div>');
                        }}
                        
                        // フィニッシュラインの表示
                        if (courseConfig.finish_line && courseConfig.finish_line.pin && courseConfig.finish_line.boat) {{
                            var pinPos = [courseConfig.finish_line.pin.lat, courseConfig.finish_line.pin.lng];
                            var boatPos = [courseConfig.finish_line.boat.lat, courseConfig.finish_line.boat.lng];
                            
                            // フィニッシュライン
                            var finishLine = L.polyline([pinPos, boatPos], {{
                                color: 'blue',
                                weight: 3,
                                opacity: 0.8,
                                className: 'finish-line'
                            }}).addTo(lineLayer);
                            
                            // ピン側のマーカー
                            var pinIcon = L.divIcon({{
                                html: '<div class="course-mark-icon" style="background-color: blue;"><i class="fas fa-flag"></i></div>',
                                className: 'course-mark-icon-wrapper',
                                iconSize: [24, 24],
                                iconAnchor: [12, 12]
                            }});
                            
                            var pinMarker = L.marker(pinPos, {{
                                icon: pinIcon,
                                title: 'Finish Line (Pin End)'
                            }}).addTo(lineLayer);
                            
                            // コミッティボート側のマーカー
                            var boatIcon = L.divIcon({{
                                html: '<div class="course-mark-icon" style="background-color: blue;"><i class="fas fa-ship"></i></div>',
                                className: 'course-mark-icon-wrapper',
                                iconSize: [24, 24],
                                iconAnchor: [12, 12]
                            }});
                            
                            var boatMarker = L.marker(boatPos, {{
                                icon: boatIcon,
                                title: 'Finish Line (Boat End)'
                            }}).addTo(lineLayer);
                            
                            // ポップアップ
                            var lineLength = L.GeometryUtil.length(finishLine);
                            
                            finishLine.bindPopup('<div class="course-popup"><h4>フィニッシュライン</h4>' +
                                               '<p><strong>長さ:</strong> ' + lineLength.toFixed(1) + ' m</p>' +
                                               '</div>');
                        }}
                        
                        // スタート/フィニッシュラインを追加
                        overlays["スタート/フィニッシュライン"] = lineLayer;
                        lineLayer.addTo(map);
                        
                        // レイラインの表示
                        if (courseConfig.show_laylines && courseConfig.marks && courseConfig.marks.length > 0) {{
                            // マーク情報の取得
                            var windwardMark = null;
                            var leewardMark = null;
                            
                            // コース形状からマークを特定
                            if (courseConfig.course_shape === 'windward_leeward') {{
                                // 風上風下コースの場合、順番で判定
                                if (courseConfig.marks.length >= 2) {{
                                    windwardMark = courseConfig.marks[0];
                                    leewardMark = courseConfig.marks[1];
                                }}
                            }} else {{
                                // それ以外の場合、タイプで特定
                                for (var i = 0; i < courseConfig.marks.length; i++) {{
                                    var mark = courseConfig.marks[i];
                                    if (mark.type === 'windward' || mark.role === 'windward') {{
                                        windwardMark = mark;
                                    }} else if (mark.type === 'leeward' || mark.role === 'leeward') {{
                                        leewardMark = mark;
                                    }}
                                }}
                            }}
                            
                            // デフォルトのタッキング角度は90度
                            var tackingAngle = courseConfig.tacking_angle || 90;
                            var halfAngle = tackingAngle / 2;
                            
                            // レイラインのスタイル
                            var laylineStyle = {{
                                color: 'rgba(255, 0, 0, 0.6)',
                                weight: 2,
                                dashArray: '5,5',
                                className: 'layline'
                            }};
                            
                            // スタイルのカスタマイズ
                            if (courseConfig.layline_style) {{
                                laylineStyle = Object.assign({{}}, laylineStyle, courseConfig.layline_style);
                            }}
                            
                            // 風上マークのレイライン
                            if (windwardMark) {{
                                var windwardPos = [windwardMark.lat, windwardMark.lng];
                                
                                // ラインの長さ（約1km）
                                var laylineLength = 0.01;  // 約1kmの経度差
                                
                                // 左側のレイライン
                                var leftAngle = 180 + halfAngle;
                                var leftEndLat = windwardMark.lat + Math.sin(leftAngle * Math.PI / 180) * laylineLength;
                                var leftEndLng = windwardMark.lng + Math.cos(leftAngle * Math.PI / 180) * laylineLength;
                                
                                var leftLayline = L.polyline([windwardPos, [leftEndLat, leftEndLng]], laylineStyle).addTo(laylinesLayer);
                                
                                // 右側のレイライン
                                var rightAngle = 180 - halfAngle;
                                var rightEndLat = windwardMark.lat + Math.sin(rightAngle * Math.PI / 180) * laylineLength;
                                var rightEndLng = windwardMark.lng + Math.cos(rightAngle * Math.PI / 180) * laylineLength;
                                
                                var rightLayline = L.polyline([windwardPos, [rightEndLat, rightEndLng]], laylineStyle).addTo(laylinesLayer);
                                
                                // ポップアップ
                                leftLayline.bindPopup('<div class="course-popup"><h4>レイライン</h4>' +
                                                    '<p><strong>角度:</strong> ' + leftAngle + '°</p></div>');
                                
                                rightLayline.bindPopup('<div class="course-popup"><h4>レイライン</h4>' +
                                                     '<p><strong>角度:</strong> ' + rightAngle + '°</p></div>');
                            }}
                            
                            // 風下マークのレイライン
                            if (leewardMark) {{
                                var leewardPos = [leewardMark.lat, leewardMark.lng];
                                
                                // ラインの長さ（約1km）
                                var laylineLength = 0.01;  // 約1kmの経度差
                                
                                // 左側のレイライン
                                var leftAngle = halfAngle;
                                var leftEndLat = leewardMark.lat + Math.sin(leftAngle * Math.PI / 180) * laylineLength;
                                var leftEndLng = leewardMark.lng + Math.cos(leftAngle * Math.PI / 180) * laylineLength;
                                
                                var leftLayline = L.polyline([leewardPos, [leftEndLat, leftEndLng]], laylineStyle).addTo(laylinesLayer);
                                
                                // 右側のレイライン
                                var rightAngle = 360 - halfAngle;
                                var rightEndLat = leewardMark.lat + Math.sin(rightAngle * Math.PI / 180) * laylineLength;
                                var rightEndLng = leewardMark.lng + Math.cos(rightAngle * Math.PI / 180) * laylineLength;
                                
                                var rightLayline = L.polyline([leewardPos, [rightEndLat, rightEndLng]], laylineStyle).addTo(laylinesLayer);
                                
                                // ポップアップ
                                leftLayline.bindPopup('<div class="course-popup"><h4>レイライン</h4>' +
                                                    '<p><strong>角度:</strong> ' + leftAngle + '°</p></div>');
                                
                                rightLayline.bindPopup('<div class="course-popup"><h4>レイライン</h4>' +
                                                     '<p><strong>角度:</strong> ' + rightAngle + '°</p></div>');
                            }}
                            
                            overlays["レイライン"] = laylinesLayer;
                            laylinesLayer.addTo(map);
                        }}
                        
                        // 戦略ポイントの表示
                        if (courseConfig.strategy_points && courseConfig.strategy_points.length > 0) {{
                            courseConfig.strategy_points.forEach(function(point) {{
                                // ポイントタイプの設定
                                var iconConfig = mapConfig.point_icons[point.type] || mapConfig.point_icons.default;
                                var iconColor = point.color || iconConfig.color || 'blue';
                                var iconName = point.icon || iconConfig.icon || 'info-circle';
                                
                                // ポイントアイコンの作成
                                var pointIcon = L.divIcon({{
                                    html: '<div class="course-mark-icon" style="background-color: ' + iconColor + ';"><i class="fas fa-' + iconName + '"></i></div>',
                                    className: 'course-mark-icon-wrapper',
                                    iconSize: [32, 32],
                                    iconAnchor: [16, 16]
                                }});
                                
                                // マーカーの作成
                                var marker = L.marker([point.lat, point.lng], {{
                                    icon: pointIcon,
                                    title: point.name || point.description || 'Strategy Point'
                                }}).addTo(strategyLayer);
                                
                                // ポップアップの内容
                                var pointType = point.type === 'advantage' ? '有利ポイント' : 
                                              point.type === 'caution' ? '注意ポイント' : 
                                              point.type === 'information' ? '情報ポイント' : 
                                              '戦略ポイント';
                                
                                var popupContent = '<div class="course-popup">';
                                if (point.name) popupContent += '<h4>' + point.name + '</h4>';
                                popupContent += '<p><strong>タイプ:</strong> ' + pointType + '</p>';
                                if (point.description) popupContent += '<p>' + point.description + '</p>';
                                popupContent += '</div>';
                                
                                marker.bindPopup(popupContent);
                            }});
                            
                            overlays["戦略ポイント"] = strategyLayer;
                            strategyLayer.addTo(map);
                        }}
                        
                        // 最適ルートの表示
                        if (courseConfig.optimal_route && courseConfig.optimal_route.points && courseConfig.optimal_route.points.length > 0) {{
                            var routePoints = [];
                            
                            courseConfig.optimal_route.points.forEach(function(point) {{
                                routePoints.push([point.lat, point.lng]);
                            }});
                            
                            // ルートライン
                            var routeLine = L.polyline(routePoints, {{
                                color: 'rgba(0, 128, 0, 0.8)',
                                weight: 3,
                                opacity: 0.8,
                                lineJoin: 'round',
                                className: 'optimal-route'
                            }}).addTo(routeLayer);
                            
                            // ルートの説明
                            var description = courseConfig.optimal_route.description || '最適ルート';
                            var reason = courseConfig.optimal_route.reason || '';
                            
                            // ポップアップの内容
                            var popupContent = '<div class="course-popup">';
                            popupContent += '<h4>' + description + '</h4>';
                            if (reason) popupContent += '<p>' + reason + '</p>';
                            popupContent += '</div>';
                            
                            routeLine.bindPopup(popupContent);
                            
                            overlays["最適ルート"] = routeLayer;
                            routeLayer.addTo(map);
                        }}
                        
                        // リスクエリアの表示
                        if (courseConfig.risk_areas && courseConfig.risk_areas.length > 0) {{
                            courseConfig.risk_areas.forEach(function(area) {{
                                // ポリゴンの座標点
                                var polygonPoints = [];
                                
                                area.polygon.forEach(function(point) {{
                                    polygonPoints.push([point.lat, point.lng]);
                                }});
                                
                                // リスクタイプに応じたスタイル
                                var areaStyle = {{
                                    color: 'rgba(255, 165, 0, 0.8)',
                                    weight: 1,
                                    fillColor: 'rgba(255, 165, 0, 0.3)',
                                    fillOpacity: 0.3,
                                    className: 'risk-area risk-area-caution'
                                }};
                                
                                if (area.type === 'danger') {{
                                    areaStyle.color = 'rgba(255, 0, 0, 0.8)';
                                    areaStyle.fillColor = 'rgba(255, 0, 0, 0.3)';
                                    areaStyle.className = 'risk-area risk-area-danger';
                                }} else if (area.type === 'information') {{
                                    areaStyle.color = 'rgba(0, 0, 255, 0.6)';
                                    areaStyle.fillColor = 'rgba(0, 0, 255, 0.2)';
                                    areaStyle.className = 'risk-area risk-area-information';
                                }}
                                
                                // ポリゴンの作成
                                var polygon = L.polygon(polygonPoints, areaStyle).addTo(riskLayer);
                                
                                // エリアの説明
                                var areaType = area.type === 'danger' ? '危険エリア' : 
                                             area.type === 'caution' ? '注意エリア' : 
                                             area.type === 'information' ? '情報エリア' : 
                                             'エリア';
                                
                                var description = area.description || '';
                                
                                // ポップアップの内容
                                var popupContent = '<div class="course-popup">';
                                popupContent += '<h4>' + areaType + '</h4>';
                                if (description) popupContent += '<p>' + description + '</p>';
                                popupContent += '</div>';
                                
                                polygon.bindPopup(popupContent);
                            }});
                            
                            overlays["リスクエリア"] = riskLayer;
                            riskLayer.addTo(map);
                        }}
                        
                        // レイヤーコントロールを追加
                        L.control.layers(null, overlays).addTo(map);
                        
                        // 表示範囲の決定
                        var bounds;
                        
                        // マークがある場合はマークから範囲を決定
                        if (courseConfig.marks && courseConfig.marks.length > 0) {{
                            var points = [];
                            
                            courseConfig.marks.forEach(function(mark) {{
                                points.push([mark.lat, mark.lng]);
                            }});
                            
                            // スタート/フィニッシュラインの座標も追加
                            if (courseConfig.start_line && courseConfig.start_line.pin && courseConfig.start_line.boat) {{
                                points.push([courseConfig.start_line.pin.lat, courseConfig.start_line.pin.lng]);
                                points.push([courseConfig.start_line.boat.lat, courseConfig.start_line.boat.lng]);
                            }}
                            
                            if (courseConfig.finish_line && courseConfig.finish_line.pin && courseConfig.finish_line.boat) {{
                                points.push([courseConfig.finish_line.pin.lat, courseConfig.finish_line.pin.lng]);
                                points.push([courseConfig.finish_line.boat.lat, courseConfig.finish_line.boat.lng]);
                            }}
                            
                            bounds = L.latLngBounds(points);
                        }}
                        // マークがなく、トラックデータがある場合はトラックから範囲を決定
                        else if (trackPoints.length > 0) {{
                            bounds = L.latLngBounds(trackPoints);
                        }}
                        
                        // 自動的に表示範囲を調整
                        if (mapConfig.center_auto && bounds) {{
                            map.fitBounds(bounds, {{
                                padding: [50, 50]  // 余白
                            }});
                        }} else {{
                            map.setView(mapConfig.center, mapConfig.zoom_level);
                        }}
                        
                        // グローバル変数にマップを保存
                        window['{self.map_id}_map'] = map;
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content
