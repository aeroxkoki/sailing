"""
sailing_data_processor.reporting.elements.map.layer_manager

��������ЛY�����gY
pn����h:/^h:n��H*HM-�jin_����W~Y
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid

from sailing_data_processor.reporting.elements.base_element import BaseElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class MapLayerManager:
    """
    ������������
    
    ���k��Y������Y���ƣ�ƣ��gY
    """
    
    def __init__(self):
        """
        
        """
        self.base_layers = {}  # ������0��	
        self.overlay_layers = {}  # ��������
        self.active_base_layer = None  # ��ƣ�j������
        self.active_overlay_layers = []  # ��ƣ�j��������
    
    def add_base_layer(self, layer_id: str, layer_name: str, layer_type: str, options: Dict[str, Any] = None) -> None:
        """
        ���������
        
        Parameters
        ----------
        layer_id : str
            ���ID
        layer_name : str
            ���
        layer_type : str
            ������ (osm, satellite, etc.)
        options : Dict[str, Any], optional
            ����׷��, by default None
        """
        if options is None:
            options = {}
        
        self.base_layers[layer_id] = {
            "id": layer_id,
            "name": layer_name,
            "type": layer_type,
            "options": options
        
        # k��U�_������ƣ�kY�
        if self.active_base_layer is None:
            self.active_base_layer = layer_id
    
    def add_overlay_layer(self, layer_id: str, layer_name: str, layer_type: str, 
                         visible: bool = True, options: Dict[str, Any] = None) -> None:
        """
        �����������
        
        Parameters
        ----------
        layer_id : str
            ���ID
        layer_name : str
            ���
        layer_type : str
            ������ (track, marker, heatmap, etc.)
        visible : bool, optional
            h:�K, by default True
        options : Dict[str, Any], optional
            ����׷��, by default None
        """
        if options is None:
            options = {}
        
        self.overlay_layers[layer_id] = {
            "id": layer_id,
            "name": layer_name,
            "type": layer_type,
            "visible": visible,
            "options": options
        
        # h:Y����k��
        if visible and layer_id not in self.active_overlay_layers:
            self.active_overlay_layers.append(layer_id)
    
    def remove_overlay_layer(self, layer_id: str) -> bool:
        """
        ���������Jd
        
        Parameters
        ----------
        layer_id : str
            ���ID
            
        Returns
        -------
        bool
            Jdk�W_4True
        """
        if layer_id in self.overlay_layers:
            del self.overlay_layers[layer_id]
            
            # ��ƣ���K��Jd
            if layer_id in self.active_overlay_layers:
                self.active_overlay_layers.remove(layer_id)
            
            return True
        
        return False
    
    def set_active_base_layer(self, layer_id: str) -> bool:
        """
        ��ƣ�j�������-�
        
        Parameters
        ----------
        layer_id : str
            ���ID
            
        Returns
        -------
        bool
            -�k�W_4True
        """
        if layer_id in self.base_layers:
            self.active_base_layer = layer_id
            return True
        
        return False
    
    def toggle_overlay_layer(self, layer_id: str) -> Tuple[bool, bool]:
        """
        ��������nh:/^h:���H
        
        Parameters
        ----------
        layer_id : str
            ���ID
            
        Returns
        -------
        Tuple[bool, bool]
            (�W_K, ��H�nh:�K)
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
        
        # ����1���
        self.overlay_layers[layer_id]["visible"] = new_state
        
        return True, new_state
    
    def get_layer_config(self) -> Dict[str, Any]:
        """
        ���-��֗
        
        Returns
        -------
        Dict[str, Any]
            ���-�
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
    
    def to_json(self) -> str:
        """
        JSON�Wk	�
        
        Returns
        -------
        str
            JSON�W
        """
        return json.dumps(self.get_layer_config())


class MapLayerElement(BaseElement):
    """
    ������� 
    
    pj�.^n�������q�k�Y�� gY
    """
    
    def __init__(self, model: Optional[ElementModel] = None, **kwargs):
        """
        
        
        Parameters
        ----------
        model : Optional[ElementModel], optional
            � ���, by default None
        **kwargs : dict
            ���LЛU�jD4k(U�����ƣ
        """
        # �թ��g��ׁ ��ג-�
        if model is None and 'element_type' not in kwargs:
            kwargs['element_type'] = ElementType.MAP
        
        super().__init__(model, **kwargs)
        
        # ���������n\
        self.layer_manager = MapLayerManager()
        
        # �թ��������
        self._add_default_layers()
    
    def _add_default_layers(self) -> None:
        """
        �թ��n������
        """
        # ������0��	
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
        
        # �թ��n��������
        self.layer_manager.add_overlay_layer("track", "GPS Track", "track", True, {
            "color": "rgba(255, 87, 34, 0.8)",
            "weight": 3
        })
        
        self.layer_manager.add_overlay_layer("markers", "Markers", "markers", True)
        self.layer_manager.add_overlay_layer("grid", "Grid", "grid", False)
    
    def add_base_layer(self, layer_id: str, layer_name: str, layer_type: str, options: Dict[str, Any] = None) -> None:
        """
        ���������
        
        Parameters
        ----------
        layer_id : str
            ���ID
        layer_name : str
            ���
        layer_type : str
            ������
        options : Dict[str, Any], optional
            ����׷��, by default None
        """
        self.layer_manager.add_base_layer(layer_id, layer_name, layer_type, options)
    
    def add_overlay_layer(self, layer_id: str, layer_name: str, layer_type: str, 
                         visible: bool = True, options: Dict[str, Any] = None) -> None:
        """
        �����������
        
        Parameters
        ----------
        layer_id : str
            ���ID
        layer_name : str
            ���
        layer_type : str
            ������
        visible : bool, optional
            h:�K, by default True
        options : Dict[str, Any], optional
            ����׷��, by default None
        """
        self.layer_manager.add_overlay_layer(layer_id, layer_name, layer_type, visible, options)
    
    def get_layer_config(self) -> Dict[str, Any]:
        """
        ���-��֗
        
        Returns
        -------
        Dict[str, Any]
            ���-�
        """
        return self.layer_manager.get_layer_config()
    
    def render(self, context: Dict[str, Any]) -> str:
        """
        � �HTMLk�����
        
        Parameters
        ----------
        context : Dict[str, Any]
            ������ƭ��
            
        Returns
        -------
        str
            �����U�_HTML
        """
        # a���ï
        if not self.evaluate_conditions(context):
            return ""
        
        # CSS����n֗
        css_style = self.get_css_styles()
        
        # ���-�
        layer_config = self.get_layer_config()
        layer_config_json = json.dumps(layer_config)
        
        # !Xj���������UI
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
                    // ���-�
                    var layerConfig = {layer_config_json};
                    
                    // ���������\
                    function createLayerControls() {{
                        var baseLayersContainer = document.getElementById('{self.element_id}_base_layers');
                        var overlayLayersContainer = document.getElementById('{self.element_id}_overlay_layers');
                        
                        // ������n鸪ܿ�
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
                                    // ������Ȓǣ����
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
                        
                        // ��������n��ï�ï�
                        if (overlayLayersContainer) {{
                            overlayLayersContainer.innerHTML = '';
                            
                            layerConfig.overlay_layers.forEach(function(layer) {{
                                var checked = layerConfig.active_overlay_layers.some(function(l) {{ return l.id === layer.id; }});
                                
                                var itemDiv = document.createElement('div');
                                itemDiv.className = 'map-layer-item';
                                
                                var label = document.createElement('label');
                                var input = document.createElement('input');
                                input.type = 'checkbox';
                                input.name = '{self.element_id}_overlay_layer_' + layer.id;
                                input.value = layer.id;
                                input.checked = checked;
                                
                                input.addEventListener('change', function(e) {{
                                    // ������Ȓǣ����
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
                    
                    // ���������\
                    window.addEventListener('load', createLayerControls);
                }})();
            </script>
        </div>
        '''
        
        return html_content
