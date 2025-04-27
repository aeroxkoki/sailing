# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map.wind_field

�4�� �ЛY�����gY
��nٯ��4h:���n��,h�,n�jin_����W~Y
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import uuid

from sailing_data_processor.reporting.elements.visualizations.map_elements import WindFieldElement as BaseWindFieldElement
from sailing_data_processor.reporting.templates.template_model import ElementType, ElementModel


class WindFieldElement(BaseWindFieldElement):
    """
    �5�4�� 
    
    �XnWindFieldElement��5W��ئj�4n�h
    ��鯷��_��ЛW~Y
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
        
        # ��n���#n-�
        self.set_property("show_wind_shifts", self.get_property("show_wind_shifts", False))
        self.set_property("show_wind_trends", self.get_property("show_wind_trends", False))
        self.set_property("compare_forecast", self.get_property("compare_forecast", False))
        self.set_property("forecast_source", self.get_property("forecast_source", ""))
        
        # �4ns0-�
        self.set_property("vector_density", self.get_property("vector_density", 50))
        self.set_property("arrow_scale", self.get_property("arrow_scale", 1.0))
        self.set_property("interpolation_method", self.get_property("interpolation_method", "bilinear"))
        
        # 0b��n-�
        self.set_property("show_terrain_effects", self.get_property("show_terrain_effects", False))
        self.set_property("terrain_source", self.get_property("terrain_source", ""))
    
    def get_chart_libraries(self) -> List[str]:
        """
        �4n�;kŁj����n�Ȓ֗
        
        Returns
        -------
        List[str]
            ����nURL��
        """
        libraries = super().get_chart_libraries()
        
        # ��n����
        additional_libraries = [
            "https://cdn.jsdelivr.net/npm/leaflet-rotatedmarker@0.2.0/leaflet.rotatedMarker.js",
            "https://cdn.jsdelivr.net/npm/d3@7.8.2/dist/d3.min.js"
        ]
        
        return libraries + additional_libraries
    
    def set_forecast_data(self, forecast_source: str) -> None:
        """
        �,�4���n����-�
        
        Parameters
        ----------
        forecast_source : str
            �,�4���n��������	
        """
        self.set_property("compare_forecast", True)
        self.set_property("forecast_source", forecast_source)
    
    def set_terrain_effects(self, show: bool, terrain_source: str = "") -> None:
        """
        0b��nh:-�
        
        Parameters
        ----------
        show : bool
            0b���h:Y�KiFK
        terrain_source : str, optional
            0b���n���, by default ""
        """
        self.set_property("show_terrain_effects", show)
        if terrain_source:
            self.set_property("terrain_source", terrain_source)
    
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
            return f'<div id="{self.element_id}" class="report-map-empty">�4���LB�~[�</div>'
        
        # �,���n֗�L	�j4	
        forecast_data = None
        if self.get_property("compare_forecast"):
            forecast_source = self.get_property("forecast_source")
            if forecast_source and forecast_source in context:
                forecast_data = context[forecast_source]
        
        # 0b���n֗0b��L	�j4	
        terrain_data = None
        if self.get_property("show_terrain_effects"):
            terrain_source = self.get_property("terrain_source")
            if terrain_source and terrain_source in context:
                terrain_data = context[terrain_source]
        
        # CSS����n֗
        css_style = self.get_css_styles()
        width, height = self.get_chart_dimensions()
        
        # ���n-�
        center_auto = self.get_property("center_auto", True)
        center_lat = self.get_property("center_lat", 35.4498)
        center_lng = self.get_property("center_lng", 139.6649)
        zoom_level = self.get_property("zoom_level", 13)
        
        # �4n-�
        wind_speed_scale = self.get_property("wind_speed_scale", 0.01)
        vector_density = self.get_property("vector_density", 50)
        arrow_scale = self.get_property("arrow_scale", 1.0)
        min_velocity = self.get_property("min_velocity", 0)
        max_velocity = self.get_property("max_velocity", 15)
        velocity_units = self.get_property("velocity_units", "kt")
        interpolation_method = self.get_property("interpolation_method", "bilinear")
        
        # h:�׷��
        show_wind_shifts = self.get_property("show_wind_shifts", False)
        show_wind_trends = self.get_property("show_wind_trends", False)
        compare_forecast = self.get_property("compare_forecast", False) and forecast_data is not None
        show_terrain_effects = self.get_property("show_terrain_effects", False) and terrain_data is not None
        
        # ���ǣ����B�		n-�
        show_time_dimension = self.get_property("show_time_dimension", False)
        time_key = self.get_property("time_key", "timestamp")
        animation_duration = self.get_property("animation_duration", 1000)
        animation_loop = self.get_property("animation_loop", True)
        
        # ���n���h-�
        map_type = self.get_property("map_type", "osm")  # osm, satellite, nautical
        show_track = self.get_property("show_track", True)
        track_color = self.get_property("track_color", "rgba(54, 162, 235, 0.8)")
        track_width = self.get_property("track_width", 3)
        
        # ����JSON�Wk	�
        data_json = json.dumps(data)
        forecast_json = json.dumps(forecast_data) if forecast_data else "null"
        terrain_json = json.dumps(terrain_data) if terrain_data else "null"
        
        # ���-��JSON�Wk	�
        map_config = {}
            "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "wind_speed_scale": wind_speed_scale,
            "vector_density": vector_density,
            "arrow_scale": arrow_scale,
            "min_velocity": min_velocity,
            "max_velocity": max_velocity,
            "velocity_units": velocity_units,
            "interpolation_method": interpolation_method,
            "show_wind_shifts": show_wind_shifts,
            "show_wind_trends": show_wind_trends,
            "compare_forecast": compare_forecast,
            "show_terrain_effects": show_terrain_effects,
            "show_time_dimension": show_time_dimension,
            "time_key": time_key,
            "animation_duration": animation_duration,
            "animation_loop": animation_loop,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width
 "map_type": map_type,
            "center_auto": center_auto,
            "center": [center_lat, center_lng],
            "zoom_level": zoom_level,
            "wind_speed_scale": wind_speed_scale,
            "vector_density": vector_density,
            "arrow_scale": arrow_scale,
            "min_velocity": min_velocity,
            "max_velocity": max_velocity,
            "velocity_units": velocity_units,
            "interpolation_method": interpolation_method,
            "show_wind_shifts": show_wind_shifts,
            "show_wind_trends": show_wind_trends,
            "compare_forecast": compare_forecast,
            "show_terrain_effects": show_terrain_effects,
            "show_time_dimension": show_time_dimension,
            "time_key": time_key,
            "animation_duration": animation_duration,
            "animation_loop": animation_loop,
            "show_track": show_track,
            "track_color": track_color,
            "track_width": track_width}
        
        map_config_json = json.dumps(map_config)
        
        # ��nCSS��
        additional_css = """
        <style>
            .wind-field-legend {
                padding: 6px 8px;
                font: 14px/16px Arial, Helvetica, sans-serif;
                background: white;
                background: rgba(255, 255, 255, 0.8);
                box-shadow: 0 0 15px rgba(0, 0, 0, 0.2);
                border-radius: 5px;
                line-height: 18px;
                color: #555;
            
            .wind-field-legend .legend-title {
                font-weight: bold;
                margin-bottom: 5px;
            
            .wind-field-legend .legend-scale {
                display: flex;
                height: 15px;
                margin-bottom: 8px;
            
            .wind-field-legend .legend-scale-segment {
                flex: 1;
                height: 100%;
            
            .wind-field-legend .legend-labels {
                display: flex;
                justify-content: space-between;
                font-size: 12px;
            
            .wind-arrow {
                stroke: rgba(0, 0, 0, 0.7);
                stroke-width: 1.5;
                fill: none;
            
            .wind-shift-marker {
                stroke: purple;
                stroke-width: 2;
                fill: white;
                fill-opacity: 0.7;
            
            .wind-trend-line {
                stroke: rgba(255, 165, 0, 0.8);
                stroke-width: 2;
                stroke-dasharray: 4;
                fill: none;
            
            .terrain-effect-area {
                fill: rgba(255, 0, 0, 0.2);
                stroke: rgba(255, 0, 0, 0.5);
                stroke-width: 1;
        </style>
        """
        
        # ��ׁ n�����
        html_content = f'''
        <div id="self.element_id}" class="report-map-container" style="{css_style}">
            <!-- Leaflet CSS -->
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-velocity@1.7.0/dist/leaflet-velocity.min.css" />
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet-timedimension@1.1.1/dist/leaflet.timedimension.min.css" />
            {additional_css}
            
            <div id="{self.map_id}" style="width: {width}; height: {height};"></div>
            
            }
            <script>
                (function() {{
                    // ������
                    var windData = data_json};
                    var forecastData = {forecast_json};
                    var terrainData = {terrain_json};
                    var mapConfig = {map_config_json};
                    
                    }
                    }
                    }
                    // ���
                    window.addEventListener('load', function() {{
                        // ���n\
                        var map = L.map('self.map_id}');
                        
                        // ������nx�
                        var tileLayer;
                        switch(mapConfig.map_type) {{
                            case 'satellite':
                                tileLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}}/{y}}/{x}}', {attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                                }});
                                break;
                            case 'nautical':
                                tileLayer = L.tileLayer('https://tiles.openseamap.org/seamark/{z}}/{x}}/{y}}.png', {attribution: 'Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors'
                                }});
                                break;
                            default:  // 'osm'
                                tileLayer = L.tileLayer('https://{s}}.tile.openstreetmap.org/{z}}/{x}}/{y}}.png', {attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                                }});
                        }}
                        
                        // ����������k��
                        tileLayer.addTo(map);
                        
                        // ��ïݤ��h�4������
                        var trackPoints = [];
                        var uGrid = null;
                        var vGrid = null;
                        var timeValues = [];
                        var windShifts = [];
                        var windTrends = [];
                        var terrainEffects = [];
                        
                        var latKey = 'lat';
                        var lngKey = 'lng';
                        var timeKey = mapConfig.time_key || 'timestamp';
                        
                        // ���bk�Xf�
                        function processWindData(source) {{
                            var result = {uGrid: null,
                                vGrid: null,
                                gridBounds: null,
                                times: []
                            }};
                            
                            if (!source) return result;
                            
                            // Uq�	hVW�	n���
                            var uComponentKey = 'u-wind';
                            var vComponentKey = 'v-wind';
                            
                            if ('u_component' in source) {uComponentKey = 'u_component';
                                vComponentKey = 'v_component';
                            }}
                            
                            // �����i(
                            var scale = mapConfig.wind_speed_scale || 0.01;
                            
                            // <Pn-�
                            var latMin, latMax, lonMin, lonMax;
                            var nx, ny;
                            
                            if ('lat_min' in source && 'lat_max' in source && 'lon_min' in source && 'lon_max' in source) {latMin = source.lat_min;
                                latMax = source.lat_max;
                                lonMin = source.lon_min;
                                lonMax = source.lon_max;
                            }} else {// �թ��$~_o��$
                                latMin = mapConfig.center[0] - 0.1;
                                latMax = mapConfig.center[0] + 0.1;
                                lonMin = mapConfig.center[1] - 0.1;
                                lonMax = mapConfig.center[1] + 0.1;
                            }}
                            
                            if ('nx' in source && 'ny' in source) {nx = source.nx;
                                ny = source.ny;
                            }} else if (uComponentKey in source && Array.isArray(source[uComponentKey])) {nx = source[uComponentKey].length;
                                ny = source[uComponentKey][0] ? source[uComponentKey][0].length : 0;
                            }} else {nx = 10;
                                ny = 10;
                            }}
                            
                            // <P���Y
                            result.gridBounds = [[latMin, lonMin], [latMax, lonMax]];
                            
                            // �4���L)(��j4
                            if (uComponentKey in source && vComponentKey in source) {{
                                // ����i(W_����$�<
                                result.uGrid = [];
                                result.vGrid = [];
                                
                                for (var i = 0; i < source[uComponentKey].length; i++) {{
                                    var uRow = [];
                                    var vRow = [];
                                    
                                    for (var j = 0; j < source[uComponentKey][i].length; j++) {uRow.push(source[uComponentKey][i][j] * scale);
                                        vRow.push(source[vComponentKey][i][j] * scale);
                                    }}
                                    
                                    result.uGrid.push(uRow);
                                    result.vGrid.push(vRow);
                                }}
                                
                                // B����LB�4
                                if ('times' in source && Array.isArray(source.times)) {result.times = source.times;
                                }}
                            }}
                            
                            return result;
                        }}
                        
                        // ����n��
                        function extractWindShifts(source) {{
                            var shifts = [];
                            
                            if (!source || !('wind_shifts' in source) || !Array.isArray(source.wind_shifts)) {return shifts;
                            }}
                            
                            source.wind_shifts.forEach(function(shift) {{
                                if (shift.lat && shift.lng) {{
                                    shifts.push({position: [shift.lat, shift.lng],
                                        time: shift.time || null,
                                        before_direction: shift.before_direction || 0,
                                        after_direction: shift.after_direction || 0,
                                        magnitude: shift.magnitude || 0,
                                        type: shift.type || 'shift'
                                    }});
                                }}
                            }});
                            
                            return shifts;
                        }}
                        
                        // �����n��
                        function extractWindTrends(source) {{
                            var trends = [];
                            
                            if (!source || !('wind_trends' in source)) {return trends;
                            }}
                            
                            if ('wind_trends' in source && Array.isArray(source.wind_trends)) {{
                                source.wind_trends.forEach(function(trend) {{
                                    if (trend.points && Array.isArray(trend.points)) {{
                                        var points = [];
                                        
                                        trend.points.forEach(function(point) {{
                                            if (point.lat && point.lng) {points.push([point.lat, point.lng]);
                                            }}
                                        }});
                                        
                                        if (points.length > 1) {{
                                            trends.push({points: points,
                                                type: trend.type || 'trend',
                                                value: trend.value || 0
                                            }});
                                        }}
                                    }}
                                }});
                            }}
                            
                            return trends;
                        }}
                        
                        // 0b��n��
                        function extractTerrainEffects(source) {{
                            var effects = [];
                            
                            if (!source || !('effects' in source) || !Array.isArray(source.effects)) {return effects;
                            }}
                            
                            source.effects.forEach(function(effect) {{
                                if (effect.polygon && Array.isArray(effect.polygon)) {{
                                    var points = [];
                                    
                                    effect.polygon.forEach(function(point) {{
                                        if (point.lat && point.lng) {points.push([point.lat, point.lng]);
                                        }}
                                    }});
                                    
                                    if (points.length > 2) {{
                                        effects.push({polygon: points,
                                            type: effect.type || 'acceleration',
                                            intensity: effect.intensity || 1
                                        }});
                                    }}
                                }}
                            }});
                            
                            return effects;
                        }}
                        
                        // ��ïݤ��n��
                        if (Array.isArray(windData)) {{
                            // Mbn4��ïݤ��n��'	
                            if (windData.length > 0 && typeof windData[0] === 'object') {{
                                // ����y�
                                if ('latitude' in windData[0] && 'longitude' in windData[0]) {latKey = 'latitude';
                                    lngKey = 'longitude';
                                }} else if ('lat' in windData[0] && 'lon' in windData[0]) {lngKey = 'lon';
                                }}
                                
                                // ��ïݤ�Ȓ��
                                for (var i = 0; i < windData.length; i++) {{
                                    var point = windData[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                        trackPoints.push([point[latKey], point[lngKey]]);
                                        
                                        // ������(nB�$���
                                        if (mapConfig.show_time_dimension && timeKey in point) {{
                                            var time = point[timeKey];
                                            if (typeof time === 'string') {timeValues.push(new Date(time));
                                            }} else if (typeof time === 'number') {// Unix��๿��n4�XM	
                                                timeValues.push(new Date(time * 1000));
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }} else if (typeof windData === 'object') {{
                            // �ָ���bn4
                            if ('track' in windData && Array.isArray(windData.track)) {{
                                for (var i = 0; i < windData.track.length; i++) {{
                                    var point = windData.track[i];
                                    if (typeof point === 'object' && point[latKey] && point[lngKey]) {{
                                        trackPoints.push([point[latKey], point[lngKey]]);
                                        
                                        // ������(nB�$���
                                        if (mapConfig.show_time_dimension && timeKey in point) {{
                                            var time = point[timeKey];
                                            if (typeof time === 'string') {timeValues.push(new Date(time));
                                            }} else if (typeof time === 'number') {// Unix��๿��n4�XM	
                                                timeValues.push(new Date(time * 1000));
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                            
                            // �4���n�
                            var windGridData = processWindData(windData);
                            uGrid = windGridData.uGrid;
                            vGrid = windGridData.vGrid;
                            gridBounds = windGridData.gridBounds;
                            
                            // ����n��
                            if (mapConfig.show_wind_shifts) {windShifts = extractWindShifts(windData);
                            }}
                            
                            // �����n��
                            if (mapConfig.show_wind_trends) {windTrends = extractWindTrends(windData);
                            }}
                        }}
                        
                        // 0b��n�
                        if (mapConfig.show_terrain_effects && terrainData) {terrainEffects = extractTerrainEffects(terrainData);
                        }}
                        
                        // ��ׁ �����Y�_�n����\
                        var baseLayer = L.layerGroup().addTo(map);
                        var trackLayer = L.layerGroup();
                        var windLayer = L.layerGroup();
                        var forecastLayer = L.layerGroup();
                        var shiftsLayer = L.layerGroup();
                        var trendsLayer = L.layerGroup();
                        var terrainLayer = L.layerGroup();
                        
                        // ���6�n_�n�ָ���
                        var overlays = {}};
                        
                        }
                        // ��ï��\h:-�L��n4	
                        if (mapConfig.show_track && trackPoints.length > 0) {{
                            var trackLine = L.polyline(trackPoints, {color: mapConfig.track_color,
                                weight: mapConfig.track_width,
                                opacity: 0.8,
                                lineJoin: 'round'
                            }}).addTo(trackLayer);
                            
                            overlays["GPS��ï"] = trackLayer;
                            trackLayer.addTo(map);
                        }}
                        
                        // �4�����
                        if (uGrid && vGrid && gridBounds) {{
                            // D3.js�(Wf�nٯ���;
                            function drawWindVectors(uGrid, vGrid, bounds, targetLayer, options) {{
                                var defaultOptions = {density: mapConfig.vector_density || 50,
                                    scale: mapConfig.arrow_scale || 1.0,
                                    color: 'rgba(0, 0, 128, 0.7)',
                                    width: 1.5
                                }};
                                
                                // �׷��n���
                                var opts = Object.assign({}}, defaultOptions, options || {}});
                                
                                // ����n��
                                var latMin = bounds[0][0];
                                var lonMin = bounds[0][1];
                                var latMax = bounds[1][0];
                                var lonMax = bounds[1][1];
                                
                                // ����n!C
                                var nx = uGrid.length;
                                var ny = uGrid[0].length;
                                
                                // Ʀk�eDf�M�LF
                                var xStep = Math.max(1, Math.floor(nx / Math.sqrt(opts.density)));
                                var yStep = Math.max(1, Math.floor(ny / Math.sqrt(opts.density)));
                                
                                // �L�n��
                                var latStep = (latMax - latMin) / (nx - 1);
                                var lonStep = (lonMax - lonMin) / (ny - 1);
                                
                                // �������\
                                for (var i = 0; i < nx; i += xStep) {{
                                    for (var j = 0; j < ny; j += yStep) {{
                                        var lat = latMin + i * latStep;
                                        var lon = lonMin + j * lonStep;
                                        var u = uGrid[i][j];
                                        var v = vGrid[i][j];
                                        
                                        // �L0k�D4o����
                                        if (Math.abs(u) < 1e-6 && Math.abs(v) < 1e-6) continue;
                                        
                                        // �h���
                                        var speed = Math.sqrt(u * u + v * v);
                                        var direction = Math.atan2(v, u) * 180 / Math.PI;
                                        
                                        // �k�Wf�ҹk	�٢��	
                                        direction = 90 - direction;
                                        if (direction < 0) direction += 360;
                                        
                                        // �k�eDf�����
                                        var arrowSize = 20 * opts.scale * Math.min(1, speed / (mapConfig.max_velocity * 0.1 || 1));
                                        
                                        // ����n\
                                        var arrowIcon = L.divIcon({html: '<svg width="' + (arrowSize * 2) + '" height="' + (arrowSize * 2) + '" ' +
                                                 'viewBox="-10 -10 20 20" class="wind-arrow">' +
                                                 '<path d="M0,-8 L0,8 M0,-8 L-4,-4 M0,-8 L4,-4" ' +
                                                 'stroke="' + opts.color + '" stroke-width="' + opts.width + '" />' +
                                                 '</svg>',
                                            className: 'wind-vector-icon',
                                            iconSize: [arrowSize * 2, arrowSize * 2],
                                            iconAnchor: [arrowSize, arrowSize]
                                        }});
                                        
                                        var marker = L.marker([lat, lon], {icon: arrowIcon,
                                            rotationAngle: direction,
                                            rotationOrigin: 'center center'
                                        }}).addTo(targetLayer);
                                        
                                        // ��ע��n��
                                        marker.bindPopup(
                                            '<div><strong>�:</strong> ' + Math.round(direction) + '�</div>' +
                                            '<div><strong>�:</strong> ' + speed.toFixed(1) + ' ' + mapConfig.velocity_units + '</div>'
                                        );
                                    }}
                                }}
                            }}
                            
                            // ,��4n�;
                            drawWindVectors(uGrid, vGrid, gridBounds, windLayer, {color: 'rgba(0, 0, 128, 0.8)'
                            }});
                            
                            overlays["�4"] = windLayer;
                            windLayer.addTo(map);
                            
                            // �,�4n�	�j4	
                            if (mapConfig.compare_forecast && forecastData) {{
                                var forecastGridData = processWindData(forecastData);
                                
                                if (forecastGridData.uGrid && forecastGridData.vGrid && forecastGridData.gridBounds) {{
                                    drawWindVectors(forecastGridData.uGrid, forecastGridData.vGrid, forecastGridData.gridBounds, forecastLayer, {color: 'rgba(0, 128, 0, 0.8)'
                                    }});
                                    
                                    overlays["�,�4"] = forecastLayer;
                                }}
                            }}
                            
                            // ����nh:
                            if (mapConfig.show_wind_shifts && windShifts.length > 0) {{
                                windShifts.forEach(function(shift) {{
                                    // �������n\
                                    var shiftMarker = L.circleMarker(shift.position, {radius: 8,
                                        color: 'purple',
                                        weight: 2,
                                        fillColor: 'white',
                                        fillOpacity: 0.7,
                                        className: 'wind-shift-marker'
                                    }}).addTo(shiftsLayer);
                                    
                                    // ��ע��n��
                                    var popupContent = '<div><strong>����</strong></div>';
                                    if (shift.time) popupContent += '<div><strong>B�:</strong> ' + new Date(shift.time).toLocaleString() + '</div>';
                                    popupContent += '<div><strong>���M:</strong> ' + Math.round(shift.before_direction) + '�</div>';
                                    popupContent += '<div><strong>��Ȍ:</strong> ' + Math.round(shift.after_direction) + '�</div>';
                                    popupContent += '<div><strong>	�:</strong> ' + Math.round(shift.magnitude) + '�</div>';
                                    
                                    shiftMarker.bindPopup(popupContent);
                                }});
                                
                                overlays["����"] = shiftsLayer;
                            }}
                            
                            // �����nh:
                            if (mapConfig.show_wind_trends && windTrends.length > 0) {{
                                windTrends.forEach(function(trend) {{
                                    // ������n\
                                    var trendLine = L.polyline(trend.points, {color: 'rgba(255, 165, 0, 0.8)',
                                        weight: 2,
                                        dashArray: '4',
                                        className: 'wind-trend-line'
                                    }}).addTo(trendsLayer);
                                    
                                    // ��ע��n��
                                    var trendType = trend.type === 'increasing' ? '���' : 
                                                  trend.type === 'decreasing' ? '�' : 
                                                  trend.type === 'shift_left' ? '�������' : 
                                                  trend.type === 'shift_right' ? '�������' : '����';
                                    
                                    var popupContent = '<div><strong>' + trendType + '</strong></div>';
                                    popupContent += '<div><strong>	�:</strong> ' + trend.value + '</div>';
                                    
                                    trendLine.bindPopup(popupContent);
                                }});
                                
                                overlays["�����"] = trendsLayer;
                            }}
                            
                            // 0b��nh:
                            if (mapConfig.show_terrain_effects && terrainEffects.length > 0) {{
                                terrainEffects.forEach(function(effect) {{
                                    // �է�����n\
                                    var effectPolygon = L.polygon(effect.polygon, {color: 'rgba(255, 0, 0, 0.5)',
                                        weight: 1,
                                        fillColor: 'rgba(255, 0, 0, 0.2)',
                                        fillOpacity: 0.2 * effect.intensity,
                                        className: 'terrain-effect-area'
                                    }}).addTo(terrainLayer);
                                    
                                    // ��ע��n��
                                    var effectType = effect.type === 'acceleration' ? '��' : 
                                                  effect.type === 'deceleration' ? '�' : 
                                                  effect.type === 'turbulence' ? 'qA' : '0b��';
                                    
                                    var popupContent = '<div><strong>' + effectType + '</strong></div>';
                                    popupContent += '<div><strong>7�:</strong> ' + effect.intensity.toFixed(1) + '</div>';
                                    
                                    effectPolygon.bindPopup(popupContent);
                                }});
                                
                                overlays["0b��"] = terrainLayer;
                            }}
                            
                            // �����������
                            L.control.layers(null, overlays).addTo(map);
                            
                            // �nዒ��
                            var legend = L.control({position: 'bottomright' }});
                            
                            legend.onAdd = function(map) {var div = L.DomUtil.create('div', 'wind-field-legend');
                                
                                var minVel = mapConfig.min_velocity;
                                var maxVel = mapConfig.max_velocity;
                                var unit = mapConfig.velocity_units;
                                
                                div.innerHTML = '<div class="legend-title">� (' + unit + ')</div>' +
                                               '<div class="legend-scale">' +
                                               '<div class="legend-scale-segment" style="background: rgb(0, 0, 255);"></div>' +
                                               '<div class="legend-scale-segment" style="background: rgb(0, 255, 255);"></div>' +
                                               '<div class="legend-scale-segment" style="background: rgb(0, 255, 0);"></div>' +
                                               '<div class="legend-scale-segment" style="background: rgb(255, 255, 0);"></div>' +
                                               '<div class="legend-scale-segment" style="background: rgb(255, 0, 0);"></div>' +
                                               '</div>' +
                                               '<div class="legend-labels">' +
                                               '<div>' + minVel + '</div>' +
                                               '<div>' + Math.round((minVel + maxVel) / 2) + '</div>' +
                                               '<div>' + maxVel + '</div>' +
                                               '</div>';
                                
                                return div;
                            }};
                            
                            legend.addTo(map);
                            
                            // h:ߒ-�
                            var bounds;
                            if (trackPoints.length > 0) {bounds = L.latLngBounds(trackPoints);
                            }} else {bounds = L.latLngBounds([
                                    [gridBounds[0][0], gridBounds[0][1]],
                                    [gridBounds[1][0], gridBounds[1][1]]
                                ]);
                            }}
                            
                            // ���ǣ������	�j4	
                            if (mapConfig.show_time_dimension && timeValues.length > 0) {{
                                // ���ǣ����n-�
                                var timeDimension = new L.TimeDimension({times: timeValues,
                                    currentTime: timeValues[0].getTime()
                                }});
                                
                                map.timeDimension = timeDimension;
                                
                                // ���ǣ�����������
                                var tdControl = new L.Control.TimeDimension({{
                                    player: {buffer: 1,
                                        minBufferReady: 1,
                                        loop: mapConfig.animation_loop,
                                        transitionTime: mapConfig.animation_duration
                                    }}
                                }});
                                
                                map.addControl(tdControl);
                            }}
                            
                            // �ՄkhSLh:U���Fk���
                            if (mapConfig.center_auto && bounds) {map.fitBounds(bounds);
                            }} else {map.setView(mapConfig.center, mapConfig.zoom_level);
                            }}
                        }} else {{
                            // �4���L)(gMjD4
                            var message = document.createElement('div');
                            message.className = 'report-map-message';
                            message.innerHTML = '<p>�4���nbLcWOB�~[�</p>';
                            
                            var mapContainer = document.getElementById('self.map_id}');
                            mapContainer.appendChild(message);
                            
                            // ���-Ò-�
                            map.setView(mapConfig.center, mapConfig.zoom_level);
                        }}
                        
                        // ��תָ��Ȓ�����kl�
                        window['{self.map_id}_map'] = map;
                    }});
                }})();
            </script>
        </div>
        '''
        
        return html_content
