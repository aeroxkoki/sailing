# -*- coding: utf-8 -*-
"""
マップ要素の基本機能を提供するベースクラス
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
import uuid

from sailing_data_processor.reporting.elements.visualizations.base_chart import BaseChartElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class BaseMapElement(BaseChartElement):
    """
    マップ要素の基底クラス
    
    地図ベースの可視化要素の共通機能を提供します。
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
            "https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"
        ]
    
    def get_css_links(self) -> List[str]:
        """
        マップの描画に必要なCSSのリストを取得
        
        Returns
        -------
        List[str]
            CSSのURLリスト
        """
        return [
            "https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"
        ]
    
    def extract_track_points(self, data: Any, lat_key: str = 'lat', lng_key: str = 'lng') -> List[List[float]]:
        """
        データからトラックポイント（緯度・経度の配列）を抽出
        
        Parameters
        ----------
        data : Any
            ソースデータ
        lat_key : str, optional
            緯度のキー名, by default 'lat'
        lng_key : str, optional
            経度のキー名, by default 'lng'
            
        Returns
        -------
        List[List[float]]
            トラックポイントのリスト [[lat1, lng1], [lat2, lng2], ...]
        """
        track_points = []
        lat_key_detected = lat_key
        lng_key_detected = lng_key
        
        # データ形式に応じて処理
        if isinstance(data, list):
            # 配列形式の場合
            if len(data) > 0 and isinstance(data[0], dict):
                # 座標キーを特定
                if 'latitude' in data[0] and 'longitude' in data[0]:
                    lat_key_detected = 'latitude'
                    lng_key_detected = 'longitude'
                elif 'lat' in data[0] and 'lon' in data[0]:
                    lng_key_detected = 'lon'
            
            # トラックポイントを抽出
            for point in data:
                if isinstance(point, dict) and lat_key_detected in point and lng_key_detected in point:
                    track_points.append([point[lat_key_detected], point[lng_key_detected]])
        
        elif isinstance(data, dict):
            # オブジェクト形式の場合
            if 'track' in data and isinstance(data['track'], list):
                track_points = self.extract_track_points(data['track'], lat_key_detected, lng_key_detected)
            elif 'points' in data and isinstance(data['points'], list):
                track_points = self.extract_track_points(data['points'], lat_key_detected, lng_key_detected)
        
        return track_points
    
    def get_base_map_config(self) -> Dict[str, Any]:
        """
        ベースとなるマップ設定を取得
        
        Returns
        -------
        Dict[str, Any]
            マップ設定辞書
        """
        # マップのデフォルト中心位置と拡大レベル
        center_auto = self.get_property("center_auto", True)
        center_lat = self.get_property("center_lat", 35.4498)
        center_lng = self.get_property("center_lng", 139.6649)
        zoom_level = self.get_property("zoom_level", 13)
        
        # マップのタイプ
        map_type = self.get_property("map_type", "osm")  # osm, satellite, nautical
        
        return {
            "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level
        }
    
    def render_base_map_html(self, map_id: str, width: str, height: str, map_config_json: str, data_json: str, extra_content: str = '') -> str:
        """
        ベースマップのHTML構造をレンダリング
        
        Parameters
        ----------
        map_id : str
            マップ要素のID
        width : str
            幅（CSSの値）
        height : str
            高さ（CSSの値）
        map_config_json : str
            マップ設定のJSON文字列
        data_json : str
            データのJSON文字列
        extra_content : str, optional
            追加のHTML内容, by default ''
            
        Returns
        -------
        str
            レンダリングされたHTML
        """
        css_links = '\n'.join([f'<link rel="stylesheet" href="{link}" />' for link in self.get_css_links()])
        
        html_content = f'''
        <div id="{self.element_id}" class="report-map-container" style="{self.get_css_styles()}">
            {css_links}
            
            <div id="{map_id}" style="width: {width}; height: {height};"></div>
            
            {extra_content}
            
            <script>
                (function() {{
                    // マップデータ
                    var mapData = {data_json};
                    var mapConfig = {map_config_json};
                    
                    // マップ初期化
                    window.addEventListener('load', function() {{
                        // マップの作成
                        var map = L.map('{map_id}');
                        
                        // タイルレイヤーの選択
                        var tileLayer;
                        switch(mapConfig.map_type) {{
                            case 'satellite':
                                tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {{
                                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                                }});
                                break;
                            case 'nautical':
                                tileLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png', {{
                                    attribution: 'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                                }});
                                break;
                            default:  // 'osm'
                                tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {{
                                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                }});
                        }}
                        
                        // タイルレイヤーをマップに追加
                        tileLayer.addTo(map);
                        
                        // カスタム初期化コード
                        if (typeof initMapContent === 'function') {{
                            initMapContent(map, mapData, mapConfig);
                        }}
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content
