# -*- coding: utf-8 -*-
"""
ヒートマップを地図上に表示するためのマップ要素
"""

from typing import Dict, List, Any, Optional
import json

from sailing_data_processor.reporting.elements.visualizations.map.base_map import BaseMapElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class HeatMapLayerElement(BaseMapElement):
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
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "heatmap_layer"
        
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
            "https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js"
        ])
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
        
        # データソースからデータを取得
        data = None
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        # データがない場合
        if not data:
            return f'<div id="{self.element_id}" class="report-map-empty">ヒートマップデータがありません</div>'
        
        # CSSスタイルの取得
        width, height = self.get_chart_dimensions()
        
        # ベースマップ設定の取得
        map_config = self.get_base_map_config()
        
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
        })
        
        # トラック設定
        show_track = self.get_property("show_track", True)
        track_color = self.get_property("track_color", "rgba(255, 255, 255, 0.6)")
        track_width = self.get_property("track_width", 2)
        
        # 設定を統合
        map_config.update({
            "heat_value_key": heat_value_key,
            "max_value": max_value,
            "radius": radius,
            "blur": blur,
            "gradient": gradient,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width
        })
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        map_config_json = json.dumps(map_config)
        
        # ヒートマップ初期化用のJavaScriptコード
        heat_map_script = f'''
        <script>
            function initMapContent(map, mapData, mapConfig) {{
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
                            if ('latitude' in mapData[0] && 'longitude' in mapData[0]) {{
                                latKey = 'latitude';
                                lngKey = 'longitude';
                            }} else if ('lat' in mapData[0] && 'lon' in mapData[0]) {{
                                lngKey = 'lon';
                            }}
                        }}
                        
                        // 最大値を計算（指定がない場合）
                        if (!maxValue && valueKey in mapData[0]) {{
                            maxValue = Math.max(...mapData.map(p => p[valueKey] || 0));
                        }}
                        
                        // ポイントを抽出
                        for (var i = 0; i < mapData.length; i++) {{
                            var point = mapData[i];
                            if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                // トラックポイントを追加
                                trackPoints.push([point[latKey], point[lngKey]]);
                                
                                // ヒートマップポイントを追加
                                var intensity = 0;
                                if (valueKey in point) {{
                                    intensity = maxValue ? point[valueKey] / maxValue : point[valueKey];
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
                        if (!maxValue && valueKey in pointsArray[0]) {{
                            maxValue = Math.max(...pointsArray.map(p => p[valueKey] || 0));
                        }}
                        
                        // ポイントを抽出
                        for (var i = 0; i < pointsArray.length; i++) {{
                            var point = pointsArray[i];
                            if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                // トラックポイントを追加
                                trackPoints.push([point[latKey], point[lngKey]]);
                                
                                // ヒートマップポイントを追加
                                var intensity = 0;
                                if (valueKey in point) {{
                                    intensity = maxValue ? point[valueKey] / maxValue : point[valueKey];
                                }}
                                
                                heatPoints.push([point[latKey], point[lngKey], intensity]);
                            }}
                        }}
                    }}
                }}
                
                // ポイントがない場合は中心座標を設定
                if (trackPoints.length === 0) {{
                    map.setView(mapConfig.center, mapConfig.zoom_level);
                    return;
                }}
                
                // トラックラインを作成（表示設定がオンの場合）
                if (mapConfig.show_track) {{
                    var trackLine = L.polyline(trackPoints, {{
                        color: mapConfig.track_color,
                        weight: mapConfig.track_width,
                        opacity: 0.8,
                        lineJoin: 'round'
                    }}).addTo(map);
                }}
                
                // ヒートマップレイヤーを作成
                var heat = L.heatLayer(heatPoints, {{
                    radius: mapConfig.radius,
                    blur: mapConfig.blur,
                    maxZoom: 18,
                    gradient: mapConfig.gradient
                }}).addTo(map);
                
                // 自動的にトラック全体が表示されるようにズーム
                if (mapConfig.center_auto && trackPoints.length > 0) {{
                    var bounds = L.latLngBounds(trackPoints);
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
            heat_map_script
        )
