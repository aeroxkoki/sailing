# -*- coding: utf-8 -*-
"""
GPS航跡を地図上に表示するためのマップ要素
"""

from typing import Dict, List, Any, Optional
import json
import uuid

from sailing_data_processor.reporting.elements.visualizations.map.base_map import BaseMapElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class TrackMapElement(BaseMapElement):
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
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "track_map"
        
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
            return f'<div id="{self.element_id}" class="report-map-empty">GPSトラックデータがありません</div>'
        
        # CSSスタイルの取得
        width, height = self.get_chart_dimensions()
        
        # ベースマップ設定の取得
        map_config = self.get_base_map_config()
        
        # トラック設定の追加
        track_color = self.get_property("track_color", "rgba(255, 87, 34, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # タイムスライダーの設定
        show_time_slider = self.get_property("show_time_slider", False)
        time_key = self.get_property("time_key", "timestamp")
        
        # 設定を統合
        map_config.update({
            "track_color": track_color,
            "track_width": track_width,
            "show_time_slider": show_time_slider,
            "time_key": time_key
        })
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        map_config_json = json.dumps(map_config)
        
        # トラックマップ初期化用のJavaScriptコード
        track_map_script = f'''
        <script>
            function initMapContent(map, mapData, mapConfig) {{
                // トラックポイントを抽出
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
                            if ('latitude' in mapData[0] && 'longitude' in mapData[0]) {{
                                latKey = 'latitude';
                                lngKey = 'longitude';
                            }} else if ('lat' in mapData[0] && 'lon' in mapData[0]) {{
                                lngKey = 'lon';
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
                                    if (typeof time === 'string') {{
                                        timeValues.push(new Date(time));
                                    }} else if (typeof time === 'number') {{
                                        // Unixタイムスタンプの場合（秒単位）
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
                                    if (typeof time === 'string') {{
                                        timeValues.push(new Date(time));
                                    }} else if (typeof time === 'number') {{
                                        // Unixタイムスタンプの場合（秒単位）
                                        timeValues.push(new Date(time * 1000));
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
                
                // トラックポイントがない場合は中心座標を設定
                if (trackPoints.length === 0) {{
                    map.setView(mapConfig.center, mapConfig.zoom_level);
                    return;
                }}
                
                // トラックラインを作成
                var trackLine = L.polyline(trackPoints, {{
                    color: mapConfig.track_color,
                    weight: mapConfig.track_width,
                    opacity: 0.8,
                    lineJoin: 'round'
                }}).addTo(map);
                
                // スタート・ゴールマーカーを追加
                var startPoint = trackPoints[0];
                var endPoint = trackPoints[trackPoints.length - 1];
                
                var startIcon = L.divIcon({{
                    html: '<i class="fas fa-play-circle" style="color: green; font-size: 24px;"></i>',
                    className: 'track-start-icon',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                }});
                
                var endIcon = L.divIcon({{
                    html: '<i class="fas fa-flag-checkered" style="color: red; font-size: 24px;"></i>',
                    className: 'track-end-icon',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                }});
                
                L.marker(startPoint, {{icon: startIcon}}).addTo(map);
                L.marker(endPoint, {{icon: endIcon}}).addTo(map);
                
                // 自動的にトラック全体が表示されるようにズーム
                if (mapConfig.center_auto) {{
                    map.fitBounds(trackLine.getBounds());
                }} else {{
                    map.setView(mapConfig.center, mapConfig.zoom_level);
                }}
                
                // タイムスライダーの追加
                if (mapConfig.show_time_slider && timeValues.length > 0) {{
                    // タイムディメンションの設定
                    var timeDimension = new L.TimeDimension({{
                        times: timeValues,
                        currentTime: timeValues[0].getTime()
                    }});
                    
                    map.timeDimension = timeDimension;
                    
                    // タイムディメンションコントロールを追加
                    var tdControl = new L.Control.TimeDimension({{
                        player: {{
                            buffer: 1,
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
                                    "time": timeValues.map(function(time) {{return time.toISOString();}})
                                }},
                                "geometry": {{
                                    "type": "LineString",
                                    "coordinates": trackPoints.map(function(point) {{return [point[1], point[0]]; }})
                                }}
                            }}
                        ]
                    }};
                    
                    var tdGeoJsonLayer = L.timeDimension.layer.geoJson(
                        L.geoJson(geoJsonData, {{
                            style: {{
                                color: mapConfig.track_color,
                                weight: mapConfig.track_width,
                                opacity: 0.8
                            }}
                        }}),
                        {{
                            updateTimeDimension: true,
                            addlastPoint: true,
                            waitForReady: true
                        }}
                    );
                    
                    tdGeoJsonLayer.addTo(map);
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
            track_map_script
        )
