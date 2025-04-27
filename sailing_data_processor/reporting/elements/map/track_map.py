"""
sailing_data_processor.reporting.elements.map.track_map

GPSトラック（航跡）の表示と操作を行うマップ要素。
地図上に航跡データを表示し、ズーム、パン、ハイライトなどの機能を提供します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
import uuid

from sailing_data_processor.reporting.elements.visualizations.map_elements import TrackMapElement as BaseTrackMapElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class TrackMapElement(BaseTrackMapElement):
    """
    GPSトラック（航跡）の表示と操作を行うマップ要素。
    
    地図上に航跡データを可視化し、様々なインタラクション機能を提供します。
    """
    
    def __init__(self, 
                 title: str = "航跡マップ", 
                 width: str = "100%", 
                 height: str = "400px",
                 **kwargs):
        """
        初期化
        
        Parameters
        ----------
        title : str
            マップタイトル
        width : str
            マップの幅（CSS値）
        height : str
            マップの高さ（CSS値）
        **kwargs
            その他の設定パラメータ
        """
        super().__init__(title=title, width=width, height=height, **kwargs)
        self.map_id = f"track_map_{str(uuid.uuid4()).replace('-', '')}"
        
    def render_html(self) -> str:
        """
        HTML形式でマップ要素をレンダリングする
        
        Returns
        -------
        str
            HTML文字列
        """
        # マップデータの準備
        track_data = self.prepare_track_data()
        if not track_data:
            return '<div class="error">トラックデータがありません</div>'
        
        # マップ設定の準備
        map_config = self.get_map_config()
        map_config_json = json.dumps(map_config)
        
        # トラックデータをJSONに変換
        track_json = json.dumps(track_data)
        
        # HTML生成
        html_content = f'''
        <div class="track-map-container" style="width: {html.escape(self.width)}; height: {html.escape(self.height)};">
            <div id="{self.map_id}" class="map-element" style="width: 100%; height: 100%;"></div>
            <script>
                (function() {{
                    // マップデータの準備
                    const mapConfig = {map_config_json};
                    const trackData = {track_json};
                    
                    // マップの初期化
                    document.addEventListener('DOMContentLoaded', function() {{
                        // マップコンテナの取得
                        const mapContainer = document.getElementById('{self.map_id}');
                        if (!mapContainer) return;
                        
                        // マップの作成
                        const map = L.map('{self.map_id}', {{
                            center: mapConfig.center,
                            zoom: mapConfig.zoom_level,
                            attributionControl: true,
                            zoomControl: true
                        }});
                        
                        // ベースマップレイヤーの追加
                        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        }}).addTo(map);
                        
                        // トラックラインの作成
                        const trackLine = L.polyline(trackData.points, {{
                            color: mapConfig.line_color || 'blue',
                            weight: mapConfig.line_width || 3,
                            opacity: mapConfig.line_opacity || 0.8
                        }}).addTo(map);
                        
                        // 表示範囲を調整
                        if (trackData.bounds) {{
                            map.fitBounds([
                                [trackData.bounds.min_lat, trackData.bounds.min_lon],
                                [trackData.bounds.max_lat, trackData.bounds.max_lon]
                            ]);
                        }} else {{
                            map.setView(mapConfig.center, mapConfig.zoom_level);
                        }}
                        
                        // グローバル参照用にマップを保存
                        window['{self.map_id}_map'] = map;
                        window['{self.map_id}_track'] = trackLine;
                        window['{self.map_id}_data'] = trackData;
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content
