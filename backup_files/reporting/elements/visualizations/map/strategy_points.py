# -*- coding: utf-8 -*-
"""
戦略ポイントを地図上に表示するためのマップ要素
"""

from typing import Dict, List, Any, Optional
import json

from sailing_data_processor.reporting.elements.visualizations.map.base_map import BaseMapElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class StrategyPointLayerElement(BaseMapElement):
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
        if model is None and 'chart_type' not in kwargs:
            kwargs['chart_type'] = "strategy_point_layer"
        
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
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/js/all.min.js"
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
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css"
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
            return f'<div id="{self.element_id}" class="report-map-empty">戦略ポイントデータがありません</div>'
        
        # CSSスタイルの取得
        width, height = self.get_chart_dimensions()
        
        # ベースマップ設定の取得
        map_config = self.get_base_map_config()
        
        # トラック設定
        show_track = self.get_property("show_track", True)
        track_color = self.get_property("track_color", "rgba(54, 162, 235, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # ポイントタイプ別のアイコン設定
        point_icons = self.get_property("point_icons", {
            "tack": {"color": "blue", "icon": "exchange-alt"},
            "gybe": {"color": "green", "icon": "random"},
            "mark_rounding": {"color": "red", "icon": "flag-checkered"},
            "wind_shift": {"color": "purple", "icon": "wind"},
            "default": {"color": "gray", "icon": "map-marker-alt"}
        })
        
        # 設定を統合
        map_config.update({
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width,
            "point_icons": point_icons
        })
        
        # データをJSON文字列に変換
        data_json = json.dumps(data)
        map_config_json = json.dumps(map_config)
        
        # CSS スタイルの追加
        strategy_point_css = """
        <style>
            .strategy-point-icon {
                display: flex;
                align-items: center;
                justify-content: center;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                color: white;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
            }
            
            .strategy-point-popup {
                min-width: 200px;
            }
            
            .strategy-point-popup h4 {
                margin: 0 0 8px 0;
                padding-bottom: 5px;
                border-bottom: 1px solid #eee;
            }
            
            .strategy-point-popup p {
                margin: 5px 0;
            }
        </style>
        """
        
        # 戦略ポイント初期化用のJavaScriptコード
        strategy_point_script = f'''
        <script>
            function initMapContent(map, mapData, mapConfig) {{
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
                        if ('latitude' in mapData[0] && 'longitude' in mapData[0]) {{
                            latKey = 'latitude';
                            lngKey = 'longitude';
                        }} else if ('lat' in mapData[0] && 'lon' in mapData[0]) {{
                            lngKey = 'lon';
                        }}
                    }}
                    
                    // トラックポイントを生成
                    for (var i = 0; i < mapData.length; i++) {{
                        var point = mapData[i];
                        if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                            trackPoints.push([point[latKey], point[lngKey]]);
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
                    
                    if ('points' in mapData && Array.isArray(mapData.points)) {{
                        strategyPoints = mapData.points;
                    }}
                }}
                
                // ポイントがない場合は中心座標を設定
                if (trackPoints.length === 0 && strategyPoints.length === 0) {{
                    map.setView(mapConfig.center, mapConfig.zoom_level);
                    return;
                }}
                
                // トラックラインを作成（表示設定がオンの場合）
                var bounds;
                if (mapConfig.show_track && trackPoints.length > 0) {{
                    var trackLine = L.polyline(trackPoints, {{
                        color: mapConfig.track_color,
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
                        var divIcon = L.divIcon({{
                            html: '<div class="strategy-point-icon" style="background-color: ' + iconConfig.color + ';">' +
                                  '<i class="fas fa-' + iconConfig.icon + '"></i></div>',
                            className: 'strategy-point-div-icon',
                            iconSize: [32, 32],
                            iconAnchor: [16, 16]
                        }});
                        
                        // マーカーの作成
                        var marker = L.marker(latLng, {{
                            icon: divIcon,
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
                        if (!bounds) {{
                            bounds = L.latLngBounds([latLng]);
                        }} else {{
                            bounds.extend(latLng);
                        }}
                    }}
                }}
                
                // 自動的にポイント全体が表示されるようにズーム
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
            strategy_point_css + strategy_point_script
        )
