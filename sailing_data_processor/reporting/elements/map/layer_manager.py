# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class MapLayerManager:
    """
    マップレイヤーマネージャー
    
    ベースレイヤーとオーバーレイレイヤーを管理するクラスです。
    """
    
    def __init__(self):
        """
        初期化
        """
        self.base_layers = {}  # ベースレイヤー
        self.overlay_layers = {}  # オーバーレイレイヤー
        self.active_base_layer = None  # アクティブなベースレイヤー
        self.active_overlay_layers = []  # アクティブなオーバーレイレイヤー
    
    def add_base_layer(self, layer_id: str, layer_name: str, layer_type: str, options: Dict[str, Any] = None) -> None:
        """
        ベースレイヤーを追加
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        layer_name : str
            レイヤー名
        layer_type : str
            レイヤータイプ (osm, satellite, etc.)
        options : Dict[str, Any], optional
            レイヤーのオプション, by default None
        """
        if options is None:
            options = {}
        
        self.base_layers[layer_id] = {
            "id": layer_id,
            "name": layer_name,
            "type": layer_type,
            "options": options
        }
        
        # 最初に追加されたレイヤーをアクティブにする
        if self.active_base_layer is None:
            self.active_base_layer = layer_id
    
    def add_overlay_layer(self, layer_id: str, layer_name: str, layer_type: str, 
                         visible: bool = True, options: Dict[str, Any] = None) -> None:
        """
        オーバーレイレイヤーを追加
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        layer_name : str
            レイヤー名
        layer_type : str
            レイヤータイプ (track, marker, heatmap, etc.)
        visible : bool, optional
            表示状態, by default True
        options : Dict[str, Any], optional
            レイヤーのオプション, by default None
        """
        if options is None:
            options = {}
        
        self.overlay_layers[layer_id] = {
            "id": layer_id,
            "name": layer_name,
            "type": layer_type,
            "visible": visible,
            "options": options
        }
        
        # 表示状態に応じて追加
        if visible and layer_id not in self.active_overlay_layers:
            self.active_overlay_layers.append(layer_id)
    
    def remove_overlay_layer(self, layer_id: str) -> bool:
        """
        オーバーレイレイヤーを削除
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if layer_id in self.overlay_layers:
            del self.overlay_layers[layer_id]
            
            # アクティブリストからも削除
            if layer_id in self.active_overlay_layers:
                self.active_overlay_layers.remove(layer_id)
            
            return True
        
        return False
    
    def set_active_base_layer(self, layer_id: str) -> bool:
        """
        アクティブなベースレイヤーを設定
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if layer_id in self.base_layers:
            self.active_base_layer = layer_id
            return True
        
        return False
    
    def toggle_overlay_layer(self, layer_id: str) -> Tuple[bool, bool]:
        """
        オーバーレイレイヤーの表示/非表示を切り替え
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
            
        Returns
        -------
        Tuple[bool, bool]
            (成功したか, 新しい表示状態)
        """
        if layer_id not in self.overlay_layers:
            return False, False
        
        new_state = False
        
        if layer_id in self.active_overlay_layers:
            self.active_overlay_layers.remove(layer_id)
            new_state = False
        else:
            self.active_overlay_layers.append(layer_id)
            new_state = True
        
        # レイヤー状態も更新
        self.overlay_layers[layer_id]["visible"] = new_state
        
        return True, new_state
    
    def get_layer_config(self) -> Dict[str, Any]:
        """
        レイヤー設定を取得
        
        Returns
        -------
        Dict[str, Any]
            レイヤー設定
        """
        active_base = None
        if self.active_base_layer and self.active_base_layer in self.base_layers:
            active_base = self.base_layers[self.active_base_layer]
        
        active_overlays = []
        for layer_id in self.active_overlay_layers:
            if layer_id in self.overlay_layers:
                active_overlays.append(self.overlay_layers[layer_id])
        
        return {
            "base_layers": list(self.base_layers.values()),
            "overlay_layers": list(self.overlay_layers.values()),
            "active_base_layer": active_base,
            "active_overlay_layers": active_overlays
        }
    
    def to_json(self) -> str:
        """
        JSON文字列に変換
        
        Returns
        -------
        str
            JSON文字列
        """
        return json.dumps(self.get_layer_config())


class MapLayerElement(BaseElement):
    """
    マップレイヤーコントロール要素
    
    ユーザーインターフェースによるレイヤー選択をサポートする要素です。
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            モデル設定, by default None
        **kwargs : dict
            その他のパラメータ（要素の種類や表示オプションなど）
        """
        # 要素種別が未設定の場合はMAP種別を設定
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.MAP
        
        super().__init__(model, **kwargs)
        
        # レイヤーマネージャーの作成
        self.layer_manager = MapLayerManager()
        
        # 初期レイヤーを追加
        self._add_default_layers()
    
    def _add_default_layers(self) -> None:
        """
        初期のレイヤーを追加
        """
        # ベースレイヤー
        self.layer_manager.add_base_layer("osm", "OpenStreetMap", "tile", {
            "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attribution": "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
        })
        
        self.layer_manager.add_base_layer("satellite", "Satellite", "tile", {
            "url": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            "attribution": "Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
        })
        
        self.layer_manager.add_base_layer("nautical", "Nautical", "tile", {
            "url": "https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
            "attribution": "Map data: &copy; <a href='http://www.openseamap.org'>OpenSeaMap</a> contributors"
        })
        
        # 初期のオーバーレイレイヤー
        self.layer_manager.add_overlay_layer("track", "GPS Track", "track", True, {
            "color": "rgba(255, 87, 34, 0.8)",
            "weight": 3
        })
        
        self.layer_manager.add_overlay_layer("markers", "Markers", "markers", True)
        self.layer_manager.add_overlay_layer("grid", "Grid", "grid", False)
    
    def add_base_layer(self, layer_id: str, layer_name: str, layer_type: str, options: Dict[str, Any] = None) -> None:
        """
        ベースレイヤーを追加
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        layer_name : str
            レイヤー名
        layer_type : str
            レイヤータイプ
        options : Dict[str, Any], optional
            レイヤーのオプション, by default None
        """
        self.layer_manager.add_base_layer(layer_id, layer_name, layer_type, options)
    
    def add_overlay_layer(self, layer_id: str, layer_name: str, layer_type: str, 
                         visible: bool = True, options: Dict[str, Any] = None) -> None:
        """
        オーバーレイレイヤーを追加
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        layer_name : str
            レイヤー名
        layer_type : str
            レイヤータイプ
        visible : bool, optional
            表示状態, by default True
        options : Dict[str, Any], optional
            レイヤーのオプション, by default None
        """
        self.layer_manager.add_overlay_layer(layer_id, layer_name, layer_type, visible, options)
    
    def get_layer_config(self) -> Dict[str, Any]:
        """
        レイヤー設定を取得
        
        Returns
        -------
        Dict[str, Any]
            レイヤー設定
        """
        return self.layer_manager.get_layer_config()
    
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
        # 条件評価
        if not self.evaluate_conditions(context):
            return ""
        
        # CSSスタイルの取得
        css_style = self.get_css_styles()
        
        # レイヤー設定
        layer_config = self.get_layer_config()
        layer_config_json = json.dumps(layer_config)
        
        # マップレイヤーコントロールUI
        html_content = f'''
        <div id="{self.element_id}" class="map-layer-control" style="{css_style}">
            <style>
                .map-layer-control {{
                    padding: 10px;
                    background: white;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                
                .map-layer-section {{
                    margin-bottom: 10px;
                }}
                
                .map-layer-section h4 {{
                    margin: 0 0 8px 0;
                    padding-bottom: 5px;
                    font-size: 14px;
                    border-bottom: 1px solid #eee;
                }}
                
                .map-layer-item {{
                    margin-bottom: 5px;
                }}
                
                .map-layer-item label {{
                    display: flex;
                    align-items: center;
                    cursor: pointer;
                }}
                
                .map-layer-item input {{
                    margin-right: 8px;
                }}
            </style>
            
            <div class="map-layer-section">
                <h4>Base Layers</h4>
                <div class="map-layer-list" id="{self.element_id}_base_layers">
                    <!-- Base layers will be inserted here -->
                </div>
            </div>
            
            <div class="map-layer-section">
                <h4>Overlay Layers</h4>
                <div class="map-layer-list" id="{self.element_id}_overlay_layers">
                    <!-- Overlay layers will be inserted here -->
                </div>
            </div>
            
            <script>
                (function() {{
                    // レイヤー設定
                    var layerConfig = {layer_config_json};
                    
                    // レイヤーコントロールを作成
                    function createLayerControls() {{
                        var baseLayersContainer = document.getElementById('{self.element_id}_base_layers');
                        var overlayLayersContainer = document.getElementById('{self.element_id}_overlay_layers');
                        
                        // ベースレイヤーの選択肢を生成
                        if (baseLayersContainer) {{
                            baseLayersContainer.innerHTML = '';
                            
                            layerConfig.base_layers.forEach(function(layer) {{
                                var checked = layerConfig.active_base_layer && layer.id === layerConfig.active_base_layer.id;
                                
                                var itemDiv = document.createElement('div');
                                itemDiv.className = 'map-layer-item';
                                
                                var label = document.createElement('label');
                                var input = document.createElement('input');
                                input.type = 'radio';
                                input.name = '{self.element_id}_base_layer';
                                input.value = layer.id;
                                input.checked = checked;
                                
                                input.addEventListener('change', function(e) {{
                                    // レイヤー変更イベントを発行
                                    var event = new CustomEvent('base_layer_changed', {{ 
                                        detail: {{ element_id: '{self.element_id}', layer_id: layer.id }}
                                    }});
                                    document.dispatchEvent(event);
                                }});
                                
                                label.appendChild(input);
                                label.appendChild(document.createTextNode(layer.name));
                                
                                itemDiv.appendChild(label);
                                baseLayersContainer.appendChild(itemDiv);
                            }});
                        }}
                        
                        // オーバーレイレイヤーのチェックボックス
                        if (overlayLayersContainer) {{
                            overlayLayersContainer.innerHTML = '';
                            
                            layerConfig.overlay_layers.forEach(function(layer) {{
                                var checked = layerConfig.active_overlay_layers.some(function(l) {{return l.id === layer.id; }});
                                
                                var itemDiv = document.createElement('div');
                                itemDiv.className = 'map-layer-item';
                                
                                var label = document.createElement('label');
                                var input = document.createElement('input');
                                input.type = 'checkbox';
                                input.name = '{self.element_id}_overlay_layer_' + layer.id;
                                input.value = layer.id;
                                input.checked = checked;
                                
                                input.addEventListener('change', function(e) {{
                                    // レイヤー変更イベントを発行
                                    var event = new CustomEvent('overlay_layer_toggled', {{ 
                                        detail: {{ 
                                            element_id: '{self.element_id}',
                                            layer_id: layer.id,
                                            visible: this.checked
                                        }}
                                    }});
                                    document.dispatchEvent(event);
                                }});
                                
                                label.appendChild(input);
                                label.appendChild(document.createTextNode(layer.name));
                                
                                itemDiv.appendChild(label);
                                overlayLayersContainer.appendChild(itemDiv);
                            }});
                        }}
                    }}
                    
                    // コントロールを初期化
                    window.addEventListener('load', createLayerControls);
                }})();
            </script>
        </div>
        '''
        
        return html_content
