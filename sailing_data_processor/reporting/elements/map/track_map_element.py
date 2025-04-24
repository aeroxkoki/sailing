# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map.track_map_element

GPSトラック表示マップ要素を提供するモジュールです。
このモジュールは、セーリングのGPSトラックを表示するマップ要素を定義します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid

from sailing_data_processor.reporting.elements.map.base_map_element import BaseMapElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class TrackMapElement(BaseMapElement):
    """
    GPSトラック表示マップ要素
    
    セーリングのGPSトラックを表示するためのマップ要素を提供します。
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
        super().__init__(model, **kwargs)
        
        # トラック表示設定
        self.set_property("track_color", self.get_property("track_color", "rgba(255, 87, 34, 0.8)"))
        self.set_property("track_width", self.get_property("track_width", 3))
        self.set_property("show_start_end_markers", self.get_property("show_start_end_markers", True))
        self.set_property("color_by", self.get_property("color_by", "none"))  # none, speed, direction, time
        
        # インタラクション設定
        self.set_property("enable_interaction", self.get_property("enable_interaction", True))
        self.set_property("enable_selection", self.get_property("enable_selection", True))
        self.set_property("selection_color", self.get_property("selection_color", "rgba(255, 64, 0, 0.8)"))
        self.set_property("hover_color", self.get_property("hover_color", "rgba(255, 128, 0, 0.6)"))
        
        # マーカー設定
        self.set_property("show_markers", self.get_property("show_markers", True))
        self.set_property("custom_markers", self.get_property("custom_markers", []))
    
    def add_custom_marker(self, lat: float, lng: float, title: str = "", description: str = "", 
                         color: str = "blue", icon: str = "map-marker-alt") -> None:
        """
        カスタムマーカーを追加
        
        Parameters
        ----------
        lat : float
            緯度
        lng : float
            経度
        title : str, optional
            タイトル, by default ""
        description : str, optional
            説明, by default ""
        color : str, optional
            色, by default "blue"
        icon : str, optional
            アイコン, by default "map-marker-alt"
        """
        markers = self.get_property("custom_markers", [])
        markers.append({
            "lat": lat,
            "lng": lng,
            "title": title,
            "description": description,
            "color": color,
            "icon": icon
        })
        
        self.set_property("custom_markers", markers)
    
    def clear_custom_markers(self) -> None:
        """
        すべてのカスタムマーカーをクリア
        """
        self.set_property("custom_markers", [])
    
    def set_color_by(self, color_by: str) -> None:
        """
        トラックの色分けモードを設定
        
        Parameters
        ----------
        color_by : str
            色分けモード ("none", "speed", "direction", "time")
        """
        valid_modes = ["none", "speed", "direction", "time"]
        if color_by in valid_modes:
            self.set_property("color_by", color_by)
    
    def get_map_libraries(self) -> List[str]:
        """
        マップの描画に必要なライブラリのリストを取得
        
        Returns
        -------
        List[str]
            ライブラリのURLリスト
        """
        libraries = super().get_map_libraries()
        
        # 追加のトラック表示関連ライブラリ
        additional_libraries = [
            "https://cdn.jsdelivr.net/npm/leaflet-hotline@0.4.0/dist/leaflet-hotline.min.js",
            "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.1/js/all.min.js"
        ]
        
        return libraries + additional_libraries
    
    def get_map_styles(self) -> List[str]:
        """
        マップの表示に必要なスタイルシートのリストを取得
        
        Returns
        -------
        List[str]
            スタイルシートのURLリスト
        """
        styles = super().get_map_styles()
        
        # 追加のスタイルシート
        additional_styles = [
            "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.5.1/css/all.min.css"
        ]
        
        return styles + additional_styles
    
    def get_track_visualization_code(self, data_var: str = "trackData", map_var: str = "map") -> str:
        """
        トラック可視化用のJavaScriptコードを取得
        
        Parameters
        ----------
        data_var : str, optional
            データ変数名, by default "trackData"
        map_var : str, optional
            マップ変数名, by default "map"
            
        Returns
        -------
        str
            トラック可視化コード
        """
        track_color = self.get_property("track_color", "rgba(255, 87, 34, 0.8)")
        track_width = self.get_property("track_width", 3)
        color_by = self.get_property("color_by", "none")
        show_markers = self.get_property("show_markers", True)
        show_start_end_markers = self.get_property("show_start_end_markers", True)
        enable_interaction = self.get_property("enable_interaction", True)
        enable_selection = self.get_property("enable_selection", True)
        selection_color = self.get_property("selection_color", "rgba(255, 64, 0, 0.8)")
        hover_color = self.get_property("hover_color", "rgba(255, 128, 0, 0.6)")
        custom_markers = self.get_property("custom_markers", [])
        
        custom_markers_json = json.dumps(custom_markers)
        
        return f"""
            // データフィールドの確認
            var latKey = 'lat';
            var lngKey = 'lng';
            var speedKey = 'speed';
            var directionKey = 'heading';
            var timeKey = 'timestamp';
            
            // データの最初の要素でフィールド名を確認
            if ({data_var}.length > 0) {{
                var firstPoint = {data_var}[0];
                
                // 緯度・経度キーの確認
                if ('latitude' in firstPoint && 'longitude' in firstPoint) {{
                    latKey = 'latitude';
                    lngKey = 'longitude';
                }} else if ('lat' in firstPoint && 'lon' in firstPoint) {{
                    lngKey = 'lon';
                }} else if ('lat' in firstPoint && 'long' in firstPoint) {{
                    lngKey = 'long';
                }}
                
                // 速度キーの確認
                if ('spd' in firstPoint) {{
                    speedKey = 'spd';
                }} else if ('sog' in firstPoint) {{
                    speedKey = 'sog';
                }}
                
                // 方向キーの確認
                if ('cog' in firstPoint) {{
                    directionKey = 'cog';
                }} else if ('course' in firstPoint) {{
                    directionKey = 'course';
                }} else if ('dir' in firstPoint) {{
                    directionKey = 'dir';
                }}
                
                // 時間キーの確認
                if ('time' in firstPoint) {{
                    timeKey = 'time';
                }} else if ('date' in firstPoint) {{
                    timeKey = 'date';
                }}
            }}
            
            // トラックの作成
            var trackPoints = [];
            var trackValues = [];
            var minValue = Infinity;
            var maxValue = -Infinity;
            
            // データの変換
            for (var i = 0; i < {data_var}.length; i++) {{
                var point = {data_var}[i];
                if (point[latKey] && point[lngKey]) {{
                    var latLng = [parseFloat(point[latKey]), parseFloat(point[lngKey])];
                    trackPoints.push(latLng);
                    
                    // カラーマッピング用の値
                    var value = null;
                    if ('{color_by}' === 'speed' && speedKey in point) {{
                        value = parseFloat(point[speedKey]);
                    }} else if ('{color_by}' === 'direction' && directionKey in point) {{
                        value = parseFloat(point[directionKey]);
                    }} else if ('{color_by}' === 'time' && timeKey in point) {{
                        var time = point[timeKey];
                        if (typeof time === 'string') {{
                            value = new Date(time).getTime() / 1000;
                        }} else if (typeof time === 'number') {{
                            value = time;
                        }}
                    }}
                    
                    trackValues.push(value);
                    
                    // 最小・最大値の更新
                    if (value !== null) {{
                        minValue = Math.min(minValue, value);
                        maxValue = Math.max(maxValue, value);
                    }}
                }}
            }}
            
            // レイヤーグループの作成
            var trackLayerGroup = L.layerGroup().addTo({map_var});
            var markerLayerGroup = L.layerGroup().addTo({map_var});
            
            // トラックの描画
            var trackLine;
            if ('{color_by}' !== 'none' && minValue !== Infinity && maxValue !== -Infinity) {{
                // 色分けトラック
                var palette;
                if ('{color_by}' === 'speed') {{
                    // 速度用パレット（青→緑→黄→赤）
                    palette = {{
                        0.0: 'blue',
                        0.33: 'green',
                        0.66: 'yellow',
                        1.0: 'red'
                    }};
                }} else if ('{color_by}' === 'direction') {{
                    // 方向用パレット
                    palette = {{
                        0.0: 'blue',  // 0度 (北)
                        0.25: 'green', // 90度 (東)
                        0.5: 'yellow', // 180度 (南)
                        0.75: 'red',   // 270度 (西)
                        1.0: 'blue'    // 360度 (北)
                    }};
                }} else {{
                    // 時間用パレット
                    palette = {{
                        0.0: 'blue',
                        0.5: 'yellow',
                        1.0: 'red'
                    }};
                }}
                
                // 値を正規化
                var normalizedValues = trackValues.map(function(value) {{
                    if (value === null) return null;
                    return (value - minValue) / (maxValue - minValue);
                }});
                
                // ホットラインとして描画
                trackLine = L.hotline(
                    trackPoints.map(function(point, i) {{
                        return [point[0], point[1], normalizedValues[i] !== null ? normalizedValues[i] : 0];
                    }}),
                    {{
                        min: 0,
                        max: 1,
                        palette: palette,
                        weight: {track_width},
                        outlineWidth: 1,
                        outlineColor: 'rgba(0, 0, 0, 0.5)'
                    }}
                );
            }} else {{
                // 単色トラック
                trackLine = L.polyline(trackPoints, {{
                    color: '{track_color}',
                    weight: {track_width},
                    opacity: 0.8,
                    lineJoin: 'round'
                }});
            }}
            
            // インタラクションの設定
            if ({str(enable_interaction).lower()}) {{
                // ホバー効果
                trackLine.on('mouseover', function(e) {{
                    if (!this._selected) {{
                        this.setStyle({{ color: '{hover_color}', weight: {track_width + 1}, opacity: 0.7 }});
                    }}
                }});
                
                trackLine.on('mouseout', function(e) {{
                    if (!this._selected) {{
                        if ('{color_by}' === 'none') {{
                            this.setStyle({{ color: '{track_color}', weight: {track_width}, opacity: 0.8 }});
                        }} else {{
                            // ホットラインの場合はリセットが不要
                        }}
                    }}
                }});
                
                // 選択機能
                if ({str(enable_selection).lower()}) {{
                    trackLine.on('click', function(e) {{
                        if (this._selected) {{
                            this._selected = false;
                            if ('{color_by}' === 'none') {{
                                this.setStyle({{ color: '{track_color}', weight: {track_width}, opacity: 0.8 }});
                            }} else {{
                                // ホットラインの場合はリセット
                                // TODO: ホットラインの選択解除処理
                            }}
                            
                            // カスタムイベントの発火
                            var event = new CustomEvent('track_deselected', {{ detail: {{ element_id: '{self.element_id}' }} }});
                            document.dispatchEvent(event);
                        }} else {{
                            this._selected = true;
                            this.setStyle({{ color: '{selection_color}', weight: {track_width + 2}, opacity: 0.9 }});
                            
                            // カスタムイベントの発火
                            var latLng = e.latlng;
                            var event = new CustomEvent('track_selected', {{ 
                                detail: {{ 
                                    element_id: '{self.element_id}',
                                    lat: latLng.lat,
                                    lng: latLng.lng
                                }} 
                            }});
                            document.dispatchEvent(event);
                        }}
                    }});
                }}
            }}
            
            // マップにトラックを追加
            trackLine.addTo(trackLayerGroup);
            
            // レイヤーコントロールへの追加
            var overlayLayers = {map_var}._layers;
            for (var key in overlayLayers) {{
                if (overlayLayers[key] instanceof L.Control.Layers) {{
                    overlayLayers[key].addOverlay(trackLayerGroup, "Track");
                    overlayLayers[key].addOverlay(markerLayerGroup, "Markers");
                    break;
                }}
            }}
            
            // マーカーの追加
            if ({str(show_markers).lower()}) {{
                // スタート・フィニッシュマーカー
                if ({str(show_start_end_markers).lower()} && trackPoints.length > 1) {{
                    var startPoint = trackPoints[0];
                    var endPoint = trackPoints[trackPoints.length - 1];
                    
                    var startIcon = L.divIcon({{
                        html: '<div style="background-color: green; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 50%; color: white; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);"><i class="fas fa-play-circle"></i></div>',
                        className: 'track-start-icon',
                        iconSize: [32, 32],
                        iconAnchor: [16, 16]
                    }});
                    
                    var endIcon = L.divIcon({{
                        html: '<div style="background-color: red; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 50%; color: white; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);"><i class="fas fa-flag-checkered"></i></div>',
                        className: 'track-end-icon',
                        iconSize: [32, 32],
                        iconAnchor: [16, 16]
                    }});
                    
                    var startMarker = L.marker(startPoint, {{ icon: startIcon }})
                        .bindPopup('<div style="min-width: 200px;"><h4 style="margin: 0 0 8px 0; padding-bottom: 5px; border-bottom: 1px solid #eee;">Start Point</h4><p style="margin: 5px 0;">Starting position of the track</p></div>');
                        
                    var endMarker = L.marker(endPoint, {{ icon: endIcon }})
                        .bindPopup('<div style="min-width: 200px;"><h4 style="margin: 0 0 8px 0; padding-bottom: 5px; border-bottom: 1px solid #eee;">End Point</h4><p style="margin: 5px 0;">Ending position of the track</p></div>');
                    
                    startMarker.addTo(markerLayerGroup);
                    endMarker.addTo(markerLayerGroup);
                }}
                
                // カスタムマーカーの追加
                var customMarkers = {custom_markers_json};
                if (customMarkers && customMarkers.length > 0) {{
                    for (var i = 0; i < customMarkers.length; i++) {{
                        var markerData = customMarkers[i];
                        var markerLatLng = [markerData.lat, markerData.lng];
                        var markerColor = markerData.color || 'blue';
                        var markerIcon = markerData.icon || 'map-marker-alt';
                        var markerTitle = markerData.title || '';
                        var markerDesc = markerData.description || '';
                        
                        var customIcon = L.divIcon({{
                            html: '<div style="background-color: ' + markerColor + '; display: flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 50%; color: white; box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);"><i class="fas fa-' + markerIcon + '"></i></div>',
                            className: 'custom-marker-icon',
                            iconSize: [32, 32],
                            iconAnchor: [16, 16]
                        }});
                        
                        var popupContent = '<div style="min-width: 200px;">';
                        if (markerTitle) popupContent += '<h4 style="margin: 0 0 8px 0; padding-bottom: 5px; border-bottom: 1px solid #eee;">' + markerTitle + '</h4>';
                        if (markerDesc) popupContent += '<p style="margin: 5px 0;">' + markerDesc + '</p>';
                        popupContent += '</div>';
                        
                        var marker = L.marker(markerLatLng, {{ icon: customIcon }})
                            .bindPopup(popupContent);
                        
                        marker.addTo(markerLayerGroup);
                    }}
                }}
            }}
            
            // 自動中心設定
            if ({str(self.center_auto).lower()}) {{
                {map_var}.fitBounds(trackLine.getBounds());
            }}
            
            // グローバル変数として保存（外部からアクセス用）
            window['{self.map_id}_track'] = trackLine;
            window['{self.map_id}_track_data'] = {data_var};
        """
    
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
        
        # 基本マップのレンダリング
        base_html = super().render(context)
        if not base_html:
            return ""
        
        # データの整形とJSON化
        data_json = json.dumps(data)
        
        # トラック可視化コードの挿入位置を特定
        script_end = base_html.rfind("</script>")
        if script_end == -1:
            return base_html
        
        # トラック可視化コードを挿入
        track_code = f"""
                        // トラックデータの処理と表示
                        var trackData = {data_json};
                        {self.get_track_visualization_code("trackData")}
        """
        
        # コードの挿入
        modified_html = base_html[:script_end] + track_code + base_html[script_end:]
        
        return modified_html
