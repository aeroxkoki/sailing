# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map.track_map

GPS��ïh:��ׁ �ЛY�����gY
��ïnh:����-���������鯷��_�ji���W~Y
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import html
import uuid

from sailing_data_processor.reporting.elements.visualizations.map_elements import TrackMapElement as BaseTrackMapElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class TrackMapElement(BaseTrackMapElement):
    """
    �5GPS��ïh:��ׁ 
    
    �XnTrackMapElement��5W��ئj��鯷��_��
    ���ޤ��׷��ЛW~Y
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
        super().__init__(model, **kwargs)
        
        # ��鯷��#n-�
        self.set_property("enable_interaction", self.get_property("enable_interaction", True))
        self.set_property("enable_selection", self.get_property("enable_selection", True))
        self.set_property("selection_color", self.get_property("selection_color", "rgba(255, 64, 0, 0.8)"))
        self.set_property("hover_color", self.get_property("hover_color", "rgba(255, 128, 0, 0.6)"))
        
        # �����#n-�
        self.set_property("show_markers", self.get_property("show_markers", True))
        self.set_property("custom_markers", self.get_property("custom_markers", []))
        
        # ����#n-�
        self.set_property("layers", self.get_property("layers", ["track", "markers", "labels"]))
        self.set_property("base_layer", self.get_property("base_layer", "osm"))
        self.set_property("overlay_layers", self.get_property("overlay_layers", []))
        
        # ������#n-�
        self.set_property("show_layer_control", self.get_property("show_layer_control", True))
        self.set_property("show_scale_control", self.get_property("show_scale_control", True))
        self.set_property("show_fullscreen_control", self.get_property("show_fullscreen_control", True))
    
    def get_chart_libraries(self) -> List[str]:
        """
        ���n�;kŁj����n�Ȓ֗
        
        Returns
        -------
        List[str]
            ����nURL��
        """
        libraries = super().get_chart_libraries()
        
        # ��n����
        additional_libraries = [
            "https://unpkg.com/leaflet.markercluster@1.5.1/dist/leaflet.markercluster.js",
            "https://unpkg.com/leaflet-fullscreen@1.0.2/dist/Leaflet.fullscreen.min.js",
            "https://cdn.jsdelivr.net/npm/leaflet-measure@3.1.0/dist/leaflet-measure.min.js"
        ]
        
        return libraries + additional_libraries
    
    def add_custom_marker(self, lat: float, lng: float, options: Dict[str, Any] = None) -> None:
        """
        �����������
        
        Parameters
        ----------
        lat : float
            �
        lng : float
            L�
        options : Dict[str, Any], optional
            �����׷��, by default None
        """
        if options is None:
            options = {}
        
        markers = self.get_property("custom_markers", [])
        markers.append({
            "lat": lat,
            "lng": lng,
            **options
        })
        
        self.set_property("custom_markers", markers)
    
    def clear_custom_markers(self) -> None:
        """
        Yyfn�����������
        """
        self.set_property("custom_markers", [])
    
    def add_overlay_layer(self, layer_id: str, layer_type: str, options: Dict[str, Any] = None) -> None:
        """
        �����������
        
        Parameters
        ----------
        layer_id : str
            ���ID
        layer_type : str
            ������ (heatmap, grid, vector, etc.)
        options : Dict[str, Any], optional
            ����׷��, by default None
        """
        if options is None:
            options = {}
        
        layers = self.get_property("overlay_layers", [])
        layers.append({
            "id": layer_id,
            "type": layer_type,
            "visible": True,
            **options
        })
        
        self.set_property("overlay_layers", layers)
    
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
        
        # ������K�����֗
        data = None
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        # ���LjD4
        if not data:
            return f'<div id="{self.element_id}" class="report-map-empty">GPS��ï���LB�~[�</div>'
        
        # CSS����n֗
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # ���n�թ��-�Mnh�'���
        center_auto = self.get_property("center_auto", True)
        center_lat = self.get_property("center_lat", 35.4498)
        center_lng = self.get_property("center_lng", 139.6649)
        zoom_level = self.get_property("zoom_level", 13)
        
        # ���n���h-�
        map_type = self.get_property("base_layer", "osm")  # osm, satellite, nautical, etc.
        track_color = self.get_property("track_color", "rgba(255, 87, 34, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # ��鯷��-�
        enable_interaction = self.get_property("enable_interaction", True)
        enable_selection = self.get_property("enable_selection", True)
        selection_color = self.get_property("selection_color", "rgba(255, 64, 0, 0.8)")
        hover_color = self.get_property("hover_color", "rgba(255, 128, 0, 0.6)")
        
        # ����n-�
        show_markers = self.get_property("show_markers", True)
        custom_markers = self.get_property("custom_markers", [])
        
        # ���-�
        layers = self.get_property("layers", ["track", "markers", "labels"])
        overlay_layers = self.get_property("overlay_layers", [])
        
        # ������-�
        show_layer_control = self.get_property("show_layer_control", True)
        show_scale_control = self.get_property("show_scale_control", True)
        show_fullscreen_control = self.get_property("show_fullscreen_control", True)
        
        # ������n-�
        show_time_slider = self.get_property("show_time_slider", False)
        time_key = self.get_property("time_key", "timestamp")
        
        # ����JSON�Wk	�
        data_json = json.dumps(data)
        
        # ���-��JSON�Wk	�
        map_config = {
            "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "track_color": track_color,
            "track_width": track_width,
            "show_time_slider": show_time_slider,
            "time_key": time_key,
            "enable_interaction": enable_interaction,
            "enable_selection": enable_selection,
            "selection_color": selection_color,
            "hover_color": hover_color,
            "show_markers": show_markers,
            "custom_markers": custom_markers,
            "layers": layers,
            "overlay_layers": overlay_layers,
            "show_layer_control": show_layer_control,
            "show_scale_control": show_scale_control,
            "show_fullscreen_control": show_fullscreen_control
        
        map_config_json = json.dumps(map_config)
        
        # ��nCSS��
        additional_css = """
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.1/dist/MarkerCluster.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.1/dist/MarkerCluster.Default.css" />
        <link rel="stylesheet" href="https://unpkg.com/leaflet-fullscreen@1.0.2/dist/leaflet.fullscreen.css" />
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-measure@3.1.0/dist/leaflet-measure.css" />
        """
        
        # ��ׁ n�����
        html_content = f'''
        <div id="{self.element_id}" class="report-map-container" style="{css_style}">
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.1/dist/leaflet.timedimension.min.css" />
            {additional_css}
            
            <style>
                #{self.map_id} {{
                    width: {width};
                    height: {height};
                }}
                
                .track-selection {{
                    stroke: {selection_color};
                    stroke-width: {track_width + 2}px;
                    stroke-opacity: 0.9;
                    animation: pulse 1.5s infinite;
                }}
                
                .track-hover {{
                    stroke: {hover_color};
                    stroke-width: {track_width + 1}px;
                    stroke-opacity: 0.7;
                }}
                
                @keyframes pulse {{
                    0% {{ stroke-opacity: 0.9; }}
                    50% {{ stroke-opacity: 0.6; }}
                    100% {{ stroke-opacity: 0.9; }}
                }}
                
                .custom-marker-icon {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    width: 32px;
                    height: 32px;
                    border-radius: 50%;
                    color: white;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
                }}
                
                .custom-marker-popup {{
                    min-width: 200px;
                }}
                
                .custom-marker-popup h4 {{
                    margin: 0 0 8px 0;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #eee;
                }}
                
                .custom-marker-popup p {{
                    margin: 5px 0;
                }}
            </style>
            
            <div id="{self.map_id}"></div>
            
            <script>
                (function() {{
                    // ������
                    var mapData = {data_json};
                    var mapConfig = {map_config_json};
                    
                    // ���
                    window.addEventListener('load', function() {{
                        // ���n\
                        var map = L.map('{self.map_id}', {{
                            fullscreenControl: mapConfig.show_fullscreen_control
                        }});
                        
                        // ������ג\
                        var baseLayers = {{}};
                        var overlayLayers = {{}};
                        
                        // ������n\
                        var osmLayer = L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        }});
                        
                        var satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
                            attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                        }});
                        
                        var nauticalLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{{z}}/{{x}}/{{y}}.png', {{
                            attribution: 'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                        }});
                        
                        var topoLayer = L.tileLayer('https://{{s}}.tile.opentopomap.org/{{z}}/{{x}}/{{y}}.png', {{
                            attribution: 'Map data: &copy; <a href="https://www.opentopomap.org">OpenTopoMap</a> contributors'
                        }});
                        
                        // ���������k��
                        baseLayers["OpenStreetMap"] = osmLayer;
                        baseLayers["Satellite"] = satelliteLayer;
                        baseLayers["Nautical"] = nauticalLayer;
                        baseLayers["Topographic"] = topoLayer;
                        
                        // �թ��n�������x�
                        var defaultBaseLayer;
                        switch(mapConfig.map_type) {{
                            case 'satellite':
                                defaultBaseLayer = satelliteLayer;
                                break;
                            case 'nautical':
                                defaultBaseLayer = nauticalLayer;
                                break;
                            case 'topo':
                                defaultBaseLayer = topoLayer;
                                break;
                            default:  // 'osm'
                                defaultBaseLayer = osmLayer;
                        }}
                        
                        // �թ��n����������k��
                        defaultBaseLayer.addTo(map);
                        
                        // GPS��ï�����
                        var trackPoints = [];
                        var timeValues = [];
                        var latKey = 'lat';
                        var lngKey = 'lng';
                        var timeKey = mapConfig.time_key || 'timestamp';
                        
                        // ���bk�Xf�
                        if (Array.isArray(mapData)) {{
                            // Mbn4
                            if (mapData.length > 0) {{
                                // ����y�
                                if (typeof mapData[0] === 'object') {{
                                    if ('latitude' in mapData[0] && 'longitude' in mapData[0]) {{
                                        latKey = 'latitude';
                                        lngKey = 'longitude';
                                    }} else if ('lat' in mapData[0] && 'lon' in mapData[0]) {{
                                        lngKey = 'lon';
                                    }}
                                }}
                                
                                // ��ïݤ�Ȓ��
                                for (var i = 0; i < mapData.length; i++) {{
                                    var point = mapData[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                        trackPoints.push([point[latKey], point[lngKey]]);
                                        
                                        // ������(nB�$���
                                        if (mapConfig.show_time_slider && timeKey in point) {{
                                            var time = point[timeKey];
                                            if (typeof time === 'string') {{
                                                timeValues.push(new Date(time));
                                            }} else if (typeof time === 'number') {{
                                                // Unix��๿��n4�XM	
                                                timeValues.push(new Date(time * 1000));
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }} else if (typeof mapData === 'object') {{
                            // �ָ���bn4
                            if ('track' in mapData && Array.isArray(mapData.track)) {{
                                for (var i = 0; i < mapData.track.length; i++) {{
                                    var point = mapData.track[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                        trackPoints.push([point[latKey], point[lngKey]]);
                                        
                                        // ������(nB�$���
                                        if (mapConfig.show_time_slider && timeKey in point) {{
                                            var time = point[timeKey];
                                            if (typeof time === 'string') {{
                                                timeValues.push(new Date(time));
                                            }} else if (typeof time === 'number') {{
                                                // Unix��๿��n4�XM	
                                                timeValues.push(new Date(time * 1000));
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }}
                        
                        // ��ïݤ��LjD4o-ç�-�
                        if (trackPoints.length === 0) {{
                            map.setView(mapConfig.center, mapConfig.zoom_level);
                            return;
                        }}
                        
                        // ��ï������ג\
                        var trackLayerGroup = L.layerGroup();
                        
                        // ��ï��\
                        var trackLine = L.polyline(trackPoints, {{
                            color: mapConfig.track_color,
                            weight: mapConfig.track_width,
                            opacity: 0.8,
                            lineJoin: 'round'
                        }});
                        
                        // ��鯷��L	�j4
                        if (mapConfig.enable_interaction) {{
                            // �������
                            trackLine.on('mouseover', function(e) {{
                                if (!this._selected) {{
                                    this.setStyle({{ color: mapConfig.hover_color, weight: mapConfig.track_width + 1, opacity: 0.7 }});
                                }}
                            }});
                            
                            trackLine.on('mouseout', function(e) {{
                                if (!this._selected) {{
                                    this.setStyle({{ color: mapConfig.track_color, weight: mapConfig.track_width, opacity: 0.8 }});
                                }}
                            }});
                            
                            // x�����
                            if (mapConfig.enable_selection) {{
                                trackLine.on('click', function(e) {{
                                    if (this._selected) {{
                                        this._selected = false;
                                        this.setStyle({{ color: mapConfig.track_color, weight: mapConfig.track_width, opacity: 0.8 }});
                                        
                                        // ������Ȓǣ����
                                        var event = new CustomEvent('track_deselected', {{ detail: {{ element_id: '{self.element_id}' }} }});
                                        document.dispatchEvent(event);
                                    }} else {{
                                        this._selected = true;
                                        this.setStyle({{ color: mapConfig.selection_color, weight: mapConfig.track_width + 2, opacity: 0.9 }});
                                        
                                        // ������Ȓǣ����
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
                        
                        // ���k��ï����
                        trackLine.addTo(trackLayerGroup);
                        
                        // �������ג\
                        var markerLayerGroup = L.layerGroup();
                        
                        // �������������������h:L	�j4	
                        if (mapConfig.show_markers) {{
                            var startPoint = trackPoints[0];
                            var endPoint = trackPoints[trackPoints.length - 1];
                            
                            var startIcon = L.divIcon({{
                                html: '<div class="custom-marker-icon" style="background-color: green;"><i class="fas fa-play-circle"></i></div>',
                                className: 'track-start-icon',
                                iconSize: [32, 32],
                                iconAnchor: [16, 16]
                            }});
                            
                            var endIcon = L.divIcon({{
                                html: '<div class="custom-marker-icon" style="background-color: red;"><i class="fas fa-flag-checkered"></i></div>',
                                className: 'track-end-icon',
                                iconSize: [32, 32],
                                iconAnchor: [16, 16]
                            }});
                            
                            var startMarker = L.marker(startPoint, {{ icon: startIcon }})
                                .bindPopup('<div class="custom-marker-popup"><h4>Start Point</h4><p>Starting position of the track</p></div>');
                                
                            var endMarker = L.marker(endPoint, {{ icon: endIcon }})
                                .bindPopup('<div class="custom-marker-popup"><h4>End Point</h4><p>Ending position of the track</p></div>');
                            
                            startMarker.addTo(markerLayerGroup);
                            endMarker.addTo(markerLayerGroup);
                            
                            // ��������n��
                            if (mapConfig.custom_markers && mapConfig.custom_markers.length > 0) {{
                                for (var i = 0; i < mapConfig.custom_markers.length; i++) {{
                                    var markerData = mapConfig.custom_markers[i];
                                    var markerLatLng = [markerData.lat, markerData.lng];
                                    var markerColor = markerData.color || 'blue';
                                    var markerIcon = markerData.icon || 'map-marker-alt';
                                    var markerTitle = markerData.title || '';
                                    var markerDesc = markerData.description || '';
                                    
                                    var customIcon = L.divIcon({{
                                        html: '<div class="custom-marker-icon" style="background-color: ' + markerColor + ';"><i class="fas fa-' + markerIcon + '"></i></div>',
                                        className: 'custom-marker-icon',
                                        iconSize: [32, 32],
                                        iconAnchor: [16, 16]
                                    }});
                                    
                                    var popupContent = '<div class="custom-marker-popup">';
                                    if (markerTitle) popupContent += '<h4>' + markerTitle + '</h4>';
                                    if (markerDesc) popupContent += '<p>' + markerDesc + '</p>';
                                    popupContent += '</div>';
                                    
                                    var marker = L.marker(markerLatLng, {{ icon: customIcon }})
                                        .bindPopup(popupContent);
                                    
                                    marker.addTo(markerLayerGroup);
                                }}
                            }}
                        }}
                        
                        // ������n��
                        var timeLayerGroup = L.layerGroup();
                        if (mapConfig.show_time_slider && timeValues.length > 0) {{
                            // ���ǣ����n-�
                            var timeDimension = new L.TimeDimension({{
                                times: timeValues,
                                currentTime: timeValues[0].getTime()
                            }});
                            
                            map.timeDimension = timeDimension;
                            
                            // ���ǣ�����������
                            var tdControl = new L.Control.TimeDimension({{
                                player: {{
                                    buffer: 1,
                                    minBufferReady: 1,
                                    loop: true,
                                    transitionTime: 500
                                }}
                            }});
                            
                            map.addControl(tdControl);
                            
                            // ���ǣ������n��ï��\
                            var geoJsonData = {{
                                "type": "FeatureCollection",
                                "features": [
                                    {{
                                        "type": "Feature",
                                        "properties": {{
                                            "time": timeValues.map(function(time) {{ return time.toISOString(); }})
                                        }},
                                        "geometry": {{
                                            "type": "LineString",
                                            "coordinates": trackPoints.map(function(point) {{ return [point[1], point[0]]; }})
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
                            
                            tdGeoJsonLayer.addTo(timeLayerGroup);
                        }}
                        
                        // ,�����
                        var measureControl = new L.Control.Measure({{
                            position: 'topleft',
                            primaryLengthUnit: 'meters',
                            secondaryLengthUnit: 'kilometers',
                            primaryAreaUnit: 'sqmeters',
                            secondaryAreaUnit: 'hectares',
                            activeColor: '#ff8800',
                            completedColor: '#ff4400'
                        }});
                        
                        if (mapConfig.layers.includes('measure')) {{
                            map.addControl(measureControl);
                        }}
                        
                        // �����������
                        if (mapConfig.show_scale_control) {{
                            L.control.scale({{
                                imperial: false,
                                maxWidth: 200
                            }}).addTo(map);
                        }}
                        
                        // �����������
                        var availableLayers = {{
                            "Track": trackLayerGroup,
                            "Markers": markerLayerGroup
                        }};
                        
                        if (mapConfig.show_time_slider && timeValues.length > 0) {{
                            availableLayers["Time Animation"] = timeLayerGroup;
                        }}
                        
                        // ��n��������
                        if (mapConfig.overlay_layers && mapConfig.overlay_layers.length > 0) {{
                            for (var i = 0; i < mapConfig.overlay_layers.length; i++) {{
                                var layerData = mapConfig.overlay_layers[i];
                                
                                // TODO: ��n������k��
                                // �(o_`n�:hWf�����������
                                if (layerData.visible) {{
                                    availableLayers[layerData.id] = L.layerGroup();
                                }}
                            }}
                        }}
                        
                        // �թ��n������
                        if (mapConfig.layers.includes('track')) {{
                            trackLayerGroup.addTo(map);
                            overlayLayers["Track"] = trackLayerGroup;
                        }}
                        
                        if (mapConfig.layers.includes('markers')) {{
                            markerLayerGroup.addTo(map);
                            overlayLayers["Markers"] = markerLayerGroup;
                        }}
                        
                        if (mapConfig.show_time_slider && timeValues.length > 0 && mapConfig.layers.includes('time')) {{
                            timeLayerGroup.addTo(map);
                            overlayLayers["Time Animation"] = timeLayerGroup;
                        }}
                        
                        // �����������
                        if (mapConfig.show_layer_control) {{
                            L.control.layers(baseLayers, overlayLayers).addTo(map);
                        }}
                        
                        // �Մk��ïhSLh:U���Fk���
                        if (mapConfig.center_auto) {{
                            map.fitBounds(trackLine.getBounds());
                        }} else {{
                            map.setView(mapConfig.center, mapConfig.zoom_level);
                        }}
                        
                        // ��תָ��Ȓ�����kl�
                        window['{self.map_id}_map'] = map;
                        window['{self.map_id}_track'] = trackLine;
                        window['{self.map_id}_data'] = mapData;
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content
