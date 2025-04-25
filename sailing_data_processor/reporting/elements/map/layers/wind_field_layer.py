# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map.layers.wind_field_layer

風場表示レイヤーを提供するモジュールです。
このモジュールは、風向風速データを視覚化するレイヤーを定義します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import json
import uuid
import numpy as np
from datetime import datetime

from sailing_data_processor.reporting.elements.map.layers.base_layer import BaseMapLayer


class WindFieldLayer(BaseMapLayer):
    """
    風場表示レイヤー
    
    風向風速データを地図上に可視化するためのレイヤーを提供します。
    """
    
    def __init__(self, layer_id: Optional[str] = None, name: str = "風場", 
                description: str = "風向風速データを表示", **kwargs):
        """
        初期化
        
        Parameters
        ----------
        layer_id : Optional[str], optional
            レイヤーID, by default None
        name : str, optional
            レイヤー名, by default "風場"
        description : str, optional
            レイヤーの説明, by default "風向風速データを表示"
        **kwargs : dict
            追加のプロパティ
        """
        super().__init__(layer_id, name, description, **kwargs)
        
        # デフォルト設定
        self.set_property("display_type", kwargs.get("display_type", "arrows"))  # arrows, streamlines, barbs, grid
        self.set_property("arrow_scale", kwargs.get("arrow_scale", 1.0))  # 矢印のスケール
        self.set_property("arrow_density", kwargs.get("arrow_density", 15))  # 25x25のグリッド
        self.set_property("animate", kwargs.get("animate", False))  # アニメーション有無
        self.set_property("show_legend", kwargs.get("show_legend", True))  # 凡例の表示
        self.set_property("speed_scale", kwargs.get("speed_scale", "linear"))  # linear, sqrt, log
        self.set_property("time_index", kwargs.get("time_index", 0))  # 時間インデックス
        
        # 色設定
        self.set_property("color_scale", kwargs.get("color_scale", "viridis"))  # viridis, plasma, inferno, magma, blues
        self.set_property("color_by", kwargs.get("color_by", "speed"))  # speed, direction, none
        self.set_property("min_speed", kwargs.get("min_speed", None))  # 最小風速
        self.set_property("max_speed", kwargs.get("max_speed", None))  # 最大風速
        self.set_property("custom_colors", kwargs.get("custom_colors", {}))  # カスタム色マッピング
        
        # 表示フィルタ
        self.set_property("min_filter", kwargs.get("min_filter", 0.0))  # 最小値フィルタ
        self.set_property("max_filter", kwargs.get("max_filter", 50.0))  # 最大値フィルタ
        self.set_property("show_calm", kwargs.get("show_calm", True))  # 微風の表示
        
        # シフト検出
        self.set_property("show_shifts", kwargs.get("show_shifts", False))  # シフト表示
        self.set_property("shift_threshold", kwargs.get("shift_threshold", 15))  # シフト検出閾値（度）
        
        # データ処理
        self.set_property("interpolation", kwargs.get("interpolation", "linear"))  # 補間方法
        self.set_property("smoothing", kwargs.get("smoothing", 0))  # 平滑化レベル
    
    def set_display_type(self, display_type: str) -> None:
        """
        表示タイプを設定
        
        Parameters
        ----------
        display_type : str
            表示タイプ ("arrows", "streamlines", "barbs", "grid")
        """
        valid_types = ["arrows", "streamlines", "barbs", "grid"]
        if display_type in valid_types:
            self.set_property("display_type", display_type)
    
    def set_arrow_scale(self, scale: float) -> None:
        """
        矢印のスケールを設定
        
        Parameters
        ----------
        scale : float
            スケール係数
        """
        self.set_property("arrow_scale", max(0.1, min(5.0, float(scale))))
    
    def set_arrow_density(self, density: int) -> None:
        """
        矢印の密度を設定
        
        Parameters
        ----------
        density : int
            密度（グリッドサイズ）
        """
        self.set_property("arrow_density", max(5, min(50, int(density))))
    
    def set_color_scale(self, color_scale: str) -> None:
        """
        色スケールを設定
        
        Parameters
        ----------
        color_scale : str
            色スケール名
        """
        valid_scales = ["viridis", "plasma", "inferno", "magma", "blues", "custom"]
        if color_scale in valid_scales:
            self.set_property("color_scale", color_scale)
    
    def set_custom_colors(self, colors: Dict[float, str]) -> None:
        """
        カスタム色マッピングを設定
        
        Parameters
        ----------
        colors : Dict[float, str]
            値から色へのマッピング
        """
        self.set_property("custom_colors", dict(colors))
        self.set_property("color_scale", "custom")
    
    def set_speed_range(self, min_speed: Optional[float] = None, max_speed: Optional[float] = None) -> None:
        """
        風速範囲を設定
        
        Parameters
        ----------
        min_speed : Optional[float], optional
            最小風速, by default None
        max_speed : Optional[float], optional
            最大風速, by default None
        """
        if min_speed is not None:
            self.set_property("min_speed", float(min_speed))
        if max_speed is not None:
            self.set_property("max_speed", float(max_speed))
    
    def set_speed_filter(self, min_filter: float = 0.0, max_filter: float = 50.0) -> None:
        """
        風速フィルタを設定
        
        Parameters
        ----------
        min_filter : float, optional
            最小風速フィルタ, by default 0.0
        max_filter : float, optional
            最大風速フィルタ, by default 50.0
        """
        self.set_property("min_filter", float(min_filter))
        self.set_property("max_filter", float(max_filter))
    
    def set_show_shifts(self, show: bool, threshold: float = 15.0) -> None:
        """
        風向シフト表示設定
        
        Parameters
        ----------
        show : bool
            シフト表示有無
        threshold : float, optional
            シフト検出閾値（度）, by default 15.0
        """
        self.set_property("show_shifts", bool(show))
        self.set_property("shift_threshold", float(threshold))
    
    def set_time_index(self, index: int) -> None:
        """
        時間インデックスを設定
        
        Parameters
        ----------
        index : int
            時間インデックス
        """
        self.set_property("time_index", max(0, int(index)))
    
    def get_bounds(self) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        レイヤーの境界ボックスを取得
        
        Returns
        -------
        Optional[Tuple[Tuple[float, float], Tuple[float, float]]]
            ((min_lat, min_lng), (max_lat, max_lng))の形式の境界ボックス
            または境界が定義できない場合はNone
        """
        # 準備済みのデータがある場合は、そのデータの境界を返す
        if hasattr(self, "_prepared_data") and self._prepared_data:
            data = self._prepared_data
            if 'bounds' in data:
                return data['bounds']
        
        return None
    
    def prepare_data(self, context: Dict[str, Any]) -> Any:
        """
        データを準備
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
            
        Returns
        -------
        Any
            準備されたデータ
        """
        # データソースからデータを取得
        data = None
        if self.data_source and self.data_source in context:
            data = context[self.data_source]
        
        if not data:
            return None
        
        # 時間インデックスの取得
        time_index = self.get_property("time_index", 0)
        
        # 準備済みデータ
        prepared_data = {
            'type': 'wind_field',
            'points': [],
            'bounds': None,
            'min_speed': float('inf'),
            'max_speed': float('-inf'),
            'timestamp': None
        
        # データ形式に応じた処理
        if isinstance(data, list) and len(data) > 0:
            # リスト形式の場合
            if 'wind_speed' in data[0] and 'wind_direction' in data[0]:
                # 風速風向形式
                min_lat = min_lng = float('inf')
                max_lat = max_lng = float('-inf')
                
                for point in data:
                    if 'lat' in point and 'lng' in point and 'wind_speed' in point and 'wind_direction' in point:
                        lat = float(point['lat'])
                        lng = float(point['lng'])
                        speed = float(point['wind_speed'])
                        direction = float(point['wind_direction'])
                        
                        # 範囲更新
                        min_lat = min(min_lat, lat)
                        min_lng = min(min_lng, lng)
                        max_lat = max(max_lat, lat)
                        max_lng = max(max_lng, lng)
                        
                        # 速度範囲更新
                        prepared_data['min_speed'] = min(prepared_data['min_speed'], speed)
                        prepared_data['max_speed'] = max(prepared_data['max_speed'], speed)
                        
                        # タイムスタンプ
                        if 'timestamp' in point and not prepared_data['timestamp']:
                            prepared_data['timestamp'] = point['timestamp']
                        
                        # ポイント追加
                        prepared_data['points'].append({
                            'lat': lat,
                            'lng': lng,
                            'speed': speed,
                            'direction': direction
                        })
                
                # 境界設定
                if min_lat != float('inf') and min_lng != float('inf'):
                    prepared_data['bounds'] = ((min_lat, min_lng), (max_lat, max_lng))
            
            elif 'time' in data and isinstance(data['time'], list):
                # 時系列データ
                if time_index < len(data['time']):
                    # 指定時間のデータを取得
                    current_time = data['time'][time_index]
                    
                    # グリッドまたはポイントデータ
                    if 'lat' in data and 'lng' in data and 'speed' in data and 'direction' in data:
                        # グリッドデータ
                        lats = data['lat']
                        lngs = data['lng']
                        speeds = data['speed'][time_index] if isinstance(data['speed'][0], list) else data['speed']
                        directions = data['direction'][time_index] if isinstance(data['direction'][0], list) else data['direction']
                        
                        min_lat = min(lats)
                        min_lng = min(lngs)
                        max_lat = max(lats)
                        max_lng = max(lngs)
                        
                        # 各グリッドポイントを追加
                        for i, lat in enumerate(lats):
                            for j, lng in enumerate(lngs):
                                speed_idx = i * len(lngs) + j
                                speed = speeds[speed_idx]
                                direction = directions[speed_idx]
                                
                                # 速度範囲更新
                                prepared_data['min_speed'] = min(prepared_data['min_speed'], speed)
                                prepared_data['max_speed'] = max(prepared_data['max_speed'], speed)
                                
                                # ポイント追加
                                prepared_data['points'].append({
                                    'lat': lat,
                                    'lng': lng,
                                    'speed': speed,
                                    'direction': direction
                                })
                        
                        # 境界設定
                        prepared_data['bounds'] = ((min_lat, min_lng), (max_lat, max_lng))
                        prepared_data['timestamp'] = current_time
        
        # min_speedとmax_speedの設定
        if prepared_data['min_speed'] == float('inf'):
            prepared_data['min_speed'] = 0
        if prepared_data['max_speed'] == float('-inf'):
            prepared_data['max_speed'] = 30
        
        # デフォルト境界
        if not prepared_data['bounds']:
            prepared_data['bounds'] = ((35.4, 139.6), (35.5, 139.7))  # 横浜付近
        
        # 準備したデータを保存
        self._prepared_data = prepared_data
        
        return prepared_data
    
    def render_layer(self, map_var: str = "map") -> str:
        """
        レイヤーのレンダリングコードを生成
        
        Parameters
        ----------
        map_var : str, optional
            マップ変数名, by default "map"
            
        Returns
        -------
        str
            レイヤーをレンダリングするJavaScriptコード
        """
        # レイヤー設定
        layer_id = self.layer_id
        layer_var = f"layer_{layer_id}"
        data_var = f"data_{layer_id}"
        
        # レイヤープロパティ
        display_type = self.get_property("display_type", "arrows")
        arrow_scale = self.get_property("arrow_scale", 1.0)
        arrow_density = self.get_property("arrow_density", 15)
        color_scale = self.get_property("color_scale", "viridis")
        color_by = self.get_property("color_by", "speed")
        min_speed = self.get_property("min_speed", None)
        max_speed = self.get_property("max_speed", None)
        animate = self.get_property("animate", False)
        show_legend = self.get_property("show_legend", True)
        opacity = self.opacity
        
        # フィルタ設定
        min_filter = self.get_property("min_filter", 0.0)
        max_filter = self.get_property("max_filter", 50.0)
        
        # カスタム色
        custom_colors = self.get_property("custom_colors", {})
        custom_colors_js = json.dumps(custom_colors)
        
        # 設定パラメータのJavaScript
        params = {
            "displayType": display_type,
            "arrowScale": arrow_scale,
            "arrowDensity": arrow_density,
            "colorScale": color_scale,
            "colorBy": color_by,
            "minSpeed": "null" if min_speed is None else min_speed,
            "maxSpeed": "null" if max_speed is None else max_speed,
            "animate": str(animate).lower(),
            "showLegend": str(show_legend).lower(),
            "opacity": opacity,
            "customColors": custom_colors_js,
            "minFilter": min_filter,
            "maxFilter": max_filter
 {
            "displayType": display_type,
            "arrowScale": arrow_scale,
            "arrowDensity": arrow_density,
            "colorScale": color_scale,
            "colorBy": color_by,
            "minSpeed": "null" if min_speed is None else min_speed,
            "maxSpeed": "null" if max_speed is None else max_speed,
            "animate": str(animate).lower(),
            "showLegend": str(show_legend).lower(),
            "opacity": opacity,
            "customColors": custom_colors_js,
            "minFilter": min_filter,
            "maxFilter": max_filter}
        
        # JavaScript コード
        code = f"""
            // 風場レイヤーの作成 {layer_id}
            {layer_var} = (function() {{
                var windFieldConfig = {{
                    displayType: '{params["displayType"]}',
                    arrowScale: {params["arrowScale"]},
                    arrowDensity: {params["arrowDensity"]},
                    colorScale: '{params["colorScale"]}',
                    colorBy: '{params["colorBy"]}',
                    minSpeed: {params["minSpeed"]},
                    maxSpeed: {params["maxSpeed"]},
                    animate: {params["animate"]},
                    showLegend: {params["showLegend"]},
                    opacity: {params["opacity"]},
                    customColors: {params["customColors"]},
                    minFilter: {params["minFilter"]},
                    maxFilter: {params["maxFilter"]}
                }};
                
                // 風場レイヤーを作成するヘルパー関数
                function createWindLayer(data, config) {{
                    var points = data.points || [];
                    
                    // データが空の場合は空のレイヤーグループを返す
                    if (!points.length) {{
                        return L.layerGroup();
                    }}
                    
                    // 風速の範囲設定
                    var minSpeed = config.minSpeed !== null ? config.minSpeed : data.min_speed;
                    var maxSpeed = config.maxSpeed !== null ? config.maxSpeed : data.max_speed;
                    
                    // レイヤーグループ
                    var layerGroup = L.layerGroup();
                    
                    // 表示タイプに合わせた描画処理
                    if (config.displayType === 'arrows') {{
                        // 矢印表示
                        var arrowIcon = function(speed, direction, config) {{
                            // 風速でサイズを調整
                            var normalizedSpeed = Math.min(1.0, (speed - minSpeed) / (maxSpeed - minSpeed || 1));
                            var size = 10 + normalizedSpeed * 15 * config.arrowScale;
                            
                            // 風速で色を決定
                            var color = getWindColor(speed, direction, config);
                            
                            // 矢印アイコン作成
                            return L.divIcon({{
                                html: '<div style="' +
                                    'width: ' + size + 'px; ' +
                                    'height: ' + size + 'px; ' +
                                    'background-color: ' + color + '; ' +
                                    'transform: rotate(' + (direction + 180) + 'deg); ' +
                                    'clip-path: polygon(50% 0%, 0% 100%, 100% 100%); ' +
                                    'opacity: ' + config.opacity + ';">' +
                                    '</div>',
                                className: 'wind-arrow',
                                iconSize: [size, size],
                                iconAnchor: [size / 2, size / 2]
                            }});
                        }};
                        
                        // 矢印の密度を調整
                        var subset = [];
                        
                        if (points.length > config.arrowDensity * config.arrowDensity) {{
                            // 表示を簡略化するためのサブサンプリング
                            var gridSize = Math.ceil(Math.sqrt(points.length));
                            var step = Math.ceil(gridSize / config.arrowDensity);
                            
                            for (var i = 0; i < gridSize; i += step) {{
                                for (var j = 0; j < gridSize; j += step) {{
                                    var idx = i * gridSize + j;
                                    if (idx < points.length) {{
                                        subset.push(points[idx]);
                                    }}
                                }}
                            }}
                        }} else {{
                            subset = points;
                        }}
                        
                        // 矢印マーカーを追加
                        for (var i = 0; i < subset.length; i++) {{
                            var point = subset[i];
                            
                            // フィルタリング
                            if (point.speed < config.minFilter || point.speed > config.maxFilter) {{
                                continue;
                            }}
                            
                            // マーカー作成
                            var marker = L.marker([point.lat, point.lng], {{
                                icon: arrowIcon(point.speed, point.direction, config),
                                interactive: false
                            }});
                            
                            layerGroup.addLayer(marker);
                        }}
                    }} else if (config.displayType === 'streamlines') {{
                        // ストリームライン実装
                        // Note: ストリームラインの実装には追加のライブラリや計算が必要
                        console.warn('Streamlines display is not implemented yet');
                    }} else if (config.displayType === 'barbs') {{
                        // 風向羽実装
                        // Note: 風向羽表示の実装
                        console.warn('Wind barbs display is not implemented yet');
                    }} else if (config.displayType === 'grid') {{
                        // グリッドカラーマップ実装
                        // Note: 補間とグリッド表示の実装
                        console.warn('Grid display is not implemented yet');
                    }}
                    
                    // 凡例の追加
                    if (config.showLegend) {{
                        addWindLegend(layerGroup, minSpeed, maxSpeed, config);
                    }}
                    
                    return layerGroup;
                }}
                
                // 色を取得する関数
                function getWindColor(speed, direction, config) {{
                    var value = config.colorBy === 'speed' ? speed :
                             config.colorBy === 'direction' ? direction : null;
                    
                    if (value === null) {{
                        return '#3388ff';  // デフォルト色
                    }}
                    
                    if (config.colorScale === 'custom' && Object.keys(config.customColors).length > 0) {{
                        // カスタム色のマッピング
                        var customColors = config.customColors;
                        var keys = Object.keys(customColors).map(Number).sort((a, b) => a - b);
                        
                        // 値に対応する色を検索
                        if (value <= keys[0]) return customColors[keys[0]];
                        if (value >= keys[keys.length - 1]) return customColors[keys[keys.length - 1]];
                        
                        for (var i = 0; i < keys.length - 1; i++) {{
                            if (value >= keys[i] && value < keys[i + 1]) {{
                                var t = (value - keys[i]) / (keys[i + 1] - keys[i]);
                                return interpolateColor(customColors[keys[i]], customColors[keys[i + 1]], t);
                            }}
                        }}
                        
                        return customColors[keys[0]];  // フォールバック
                    }}
                    
                    // 組み込みカラースケール
                    var minValue = config.colorBy === 'speed' ? 
                            (config.minSpeed !== null ? config.minSpeed : 0) : 0;
                    var maxValue = config.colorBy === 'speed' ? 
                            (config.maxSpeed !== null ? config.maxSpeed : 30) : 
                            (config.colorBy === 'direction' ? 360 : 100);
                    
                    var normalizedValue = Math.max(0, Math.min(1, (value - minValue) / (maxValue - minValue || 1)));
                    
                    // スケールに基づいて色を返す
                    if (config.colorScale === 'viridis') {{
                        return interpolateViridis(normalizedValue);
                    }} else if (config.colorScale === 'plasma') {{
                        return interpolatePlasma(normalizedValue);
                    }} else if (config.colorScale === 'inferno') {{
                        return interpolateInferno(normalizedValue);
                    }} else if (config.colorScale === 'magma') {{
                        return interpolateMagma(normalizedValue);
                    }} else if (config.colorScale === 'blues') {{
                        return interpolateBlues(normalizedValue);
                    }}
                    
                    // デフォルト: 青から赤へのグラデーション
                    return interpolateColor('#00f', '#f00', normalizedValue);
                }}
                
                // 色の補間
                function interpolateColor(color1, color2, factor) {{
                    // HTMLカラーコードを変換
                    function hex2rgb(hex) {{
                        var result = /^#?([a-f\\d]{{2}})([a-f\\d]{{2}})([a-f\\d]{{2}})$/i.exec(hex);
                        return result ? {{
                            r: parseInt(result[1], 16),
                            g: parseInt(result[2], 16),
                            b: parseInt(result[3], 16)
                        }} : null;
                    }}
                    
                    function rgb2hex(rgb) {{
                        return "#" + ((1 << 24) + (rgb.r << 16) + (rgb.g << 8) + rgb.b).toString(16).slice(1);
                    }}
                    
                    var rgb1 = hex2rgb(color1) || {{ r: 0, g: 0, b: 255 }};
                    var rgb2 = hex2rgb(color2) || {{ r: 255, g: 0, b: 0 }};
                    
                    var r = Math.round(rgb1.r + factor * (rgb2.r - rgb1.r));
                    var g = Math.round(rgb1.g + factor * (rgb2.g - rgb1.g));
                    var b = Math.round(rgb1.b + factor * (rgb2.b - rgb1.b));
                    
                    return rgb2hex({{ r: r, g: g, b: b }});
                }}
                
                // カラースケール関数 (Viridis)
                function interpolateViridis(t) {{
                    // Viridisの簡略版
                    var colors = [
                        [68, 1, 84],     // 0.0
                        [65, 68, 135],   // 0.25
                        [42, 120, 142],  // 0.5
                        [34, 168, 132],  // 0.75
                        [122, 209, 81],  // 0.875
                        [253, 231, 37]   // 1.0
                    ];
                    
                    return interpolateColorScale(t, colors);
                }}
                
                // カラースケール関数 (Plasma)
                function interpolatePlasma(t) {{
                    // Plasmaの簡略版
                    var colors = [
                        [13, 8, 135],     // 0.0
                        [126, 3, 168],    // 0.25
                        [204, 71, 120],   // 0.5
                        [248, 149, 64],   // 0.75
                        [240, 249, 33]    // 1.0
                    ];
                    
                    return interpolateColorScale(t, colors);
                }}
                
                // カラースケール関数 (Inferno)
                function interpolateInferno(t) {{
                    // Infernoの簡略版
                    var colors = [
                        [0, 0, 4],        // 0.0
                        [85, 16, 67],     // 0.25
                        [187, 55, 84],    // 0.5
                        [250, 192, 40],   // 0.875
                        [252, 255, 164]   // 1.0
                    ];
                    
                    return interpolateColorScale(t, colors);
                }}
                
                // カラースケール関数 (Magma)
                function interpolateMagma(t) {{
                    // Magmaの簡略版
                    var colors = [
                        [0, 0, 4],        // 0.0
                        [81, 18, 124],    // 0.25
                        [183, 55, 121],   // 0.5
                        [252, 169, 126],  // 0.875
                        [252, 253, 191]   // 1.0
                    ];
                    
                    return interpolateColorScale(t, colors);
                }}
                
                // カラースケール関数 (Blues)
                function interpolateBlues(t) {{
                    // Bluesの簡略版
                    var colors = [
                        [247, 251, 255],  // 0.0
                        [198, 219, 239],  // 0.25
                        [107, 174, 214],  // 0.5
                        [33, 113, 181],   // 0.75
                        [8, 48, 107]      // 1.0
                    ];
                    
                    return interpolateColorScale(t, colors);
                }}
                
                // カラースケールの補間
                function interpolateColorScale(t, colors) {{
                    if (t <= 0) return rgbToHex(colors[0][0], colors[0][1], colors[0][2]);
                    if (t >= 1) return rgbToHex(colors[colors.length-1][0], colors[colors.length-1][1], colors[colors.length-1][2]);
                    
                    var i = Math.floor(t * (colors.length - 1));
                    var f = t * (colors.length - 1) - i;
                    
                    var r = Math.round(colors[i][0] + f * (colors[i+1][0] - colors[i][0]));
                    var g = Math.round(colors[i][1] + f * (colors[i+1][1] - colors[i][1]));
                    var b = Math.round(colors[i][2] + f * (colors[i+1][2] - colors[i][2]));
                    
                    return rgbToHex(r, g, b);
                }}
                
                // RGBをHEXに変換
                function rgbToHex(r, g, b) {{
                    return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1);
                }}
                
                // 凡例の追加
                function addWindLegend(layerGroup, minSpeed, maxSpeed, config) {{
                    var legend = L.control({{ position: 'bottomright' }});
                    
                    legend.onAdd = function(map) {{
                        var div = L.DomUtil.create('div', 'wind-legend');
                        div.style.backgroundColor = 'white';
                        div.style.padding = '10px';
                        div.style.border = '1px solid #ccc';
                        div.style.borderRadius = '5px';
                        div.style.opacity = '0.8';
                        
                        var title = config.colorBy === 'speed' ? '風速 (kt)' : 
                                 config.colorBy === 'direction' ? '風向 (°)' : '';
                        
                        var html = '<div style="text-align: center; margin-bottom: 5px;"><b>' + title + '</b></div>';
                        
                        if (config.colorBy === 'speed') {{
                            // 風速カラーバー
                            var steps = 5;
                            var stepSize = (maxSpeed - minSpeed) / steps;
                            
                            html += '<div style="display: flex; height: 20px; margin-bottom: 5px;">';
                            
                            for (var i = 0; i <= steps; i++) {{
                                var value = minSpeed + i * stepSize;
                                var color = getWindColor(value, 0, config);
                                
                                html += '<div style="flex: 1; background-color: ' + color + ';"></div>';
                            }}
                            
                            html += '</div>';
                            
                            // ラベル
                            html += '<div style="display: flex; justify-content: space-between;">';
                            html += '<div>' + minSpeed.toFixed(1) + '</div>';
                            html += '<div>' + ((minSpeed + maxSpeed) / 2).toFixed(1) + '</div>';
                            html += '<div>' + maxSpeed.toFixed(1) + '</div>';
                            html += '</div>';
                        }} else if (config.colorBy === 'direction') {{
                            // 風向カラーバー
                            var directions = ['北(0°)', '東(90°)', '南(180°)', '西(270°)', '北(360°)'];
                            var values = [0, 90, 180, 270, 360];
                            
                            html += '<div style="display: flex; height: 20px; margin-bottom: 5px;">';
                            
                            for (var i = 0; i < values.length - 1; i++) {{
                                var color = getWindColor(values[i], values[i], config);
                                html += '<div style="flex: 1; background-color: ' + color + ';"></div>';
                            }}
                            
                            html += '</div>';
                            
                            // ラベル
                            html += '<div style="display: flex; justify-content: space-between; font-size: 10px;">';
                            for (var i = 0; i < directions.length; i++) {{
                                html += '<div>' + directions[i] + '</div>';
                            }}
                            html += '</div>';
                        }}
                        
                        div.innerHTML = html;
                        return div;
                    }};
                    
                    layerGroup.addLayer(legend);
                    return legend;
                }}
                
                // レイヤーを作成して返す
                var layer = null;
                
                if (typeof {data_var} !== 'undefined' && {data_var} && {data_var}.points) {{
                    layer = createWindLayer({data_var}, windFieldConfig);
                    layer.addTo({map_var});
                }} else {{
                    console.warn('No wind field data available for layer {layer_id}');
                    layer = L.layerGroup().addTo({map_var});
                }}
                
                // レイヤー情報を保存
                layer.id = '{layer_id}';
                layer.name = '{self.name}';
                layer.type = 'wind_field';
                
                return layer;
            }})();
        """
        
        return code
