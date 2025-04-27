# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map.layers.heat_map_layer

ヒートマップレイヤーを提供するモジュールです。
このモジュールは、セーリングデータの密度やメトリックをヒートマップとして視覚化するレイヤーを定義します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Set, Callable
import json
import uuid
import math
import numpy as np
from datetime import datetime

from sailing_data_processor.reporting.elements.map.layers.base_layer import BaseMapLayer


class HeatMapLayer(BaseMapLayer):
    """
    ヒートマップレイヤー
    
    セーリングデータの密度やメトリック（速度、風速など）を地図上にヒートマップとして視覚化するためのレイヤーを提供します。
    """
    
    def __init__(self, layer_id: Optional[str] = None, name: str = "ヒートマップ", 
                description: str = "セーリングデータの密度/メトリックを表示", **kwargs):
        """
        初期化
        
        Parameters
        ----------
        layer_id : Optional[str], optional
            レイヤーID, by default None
        name : str, optional
            レイヤー名, by default "ヒートマップ"
        description : str, optional
            レイヤーの説明, by default "セーリングデータの密度/メトリックを表示"
        **kwargs : dict
            追加のプロパティ
        """
        super().__init__(layer_id, name, description, **kwargs)
        
        # デフォルト設定
        self.set_property("metric", kwargs.get("metric", "speed"))  # 表示するメトリック: speed, wind_speed, heading, density, custom
        self.set_property("custom_field", kwargs.get("custom_field", ""))  # カスタムフィールド名
        self.set_property("radius", kwargs.get("radius", 15))  # ヒートマップのポイント半径
        self.set_property("blur", kwargs.get("blur", 15))  # ぼかしの度合い
        self.set_property("max_zoom", kwargs.get("max_zoom", 18))  # 最大ズームレベル
        self.set_property("min_opacity", kwargs.get("min_opacity", 0.3))  # 最小不透明度
        
        # 色設定
        self.set_property("gradient", kwargs.get("gradient", None))  # カスタムグラデーション
        self.set_property("color_scale", kwargs.get("color_scale", "default"))  # カラースケール
        self.set_property("invert_scale", kwargs.get("invert_scale", False))  # スケールの反転
        
        # 値範囲設定
        self.set_property("min_value", kwargs.get("min_value", None))  # 最小値
        self.set_property("max_value", kwargs.get("max_value", None))  # 最大値
        
        # 表示設定
        self.set_property("show_legend", kwargs.get("show_legend", True))  # 凡例の表示
        self.set_property("intensity", kwargs.get("intensity", 1.0))  # 強度（0.0-1.0）
        self.set_property("aggregation", kwargs.get("aggregation", "max"))  # 集約方法: max, min, avg
        
        # データ処理設定
        self.set_property("smoothing", kwargs.get("smoothing", 0))  # 平滑化レベル（0-10）
        self.set_property("discretize", kwargs.get("discretize", False))  # 離散化の有無
        self.set_property("num_bins", kwargs.get("num_bins", 10))  # 離散化のビン数
    
    def set_metric(self, metric: str, custom_field: str = "") -> None:
        """
        表示するメトリックを設定
        
        Parameters
        ----------
        metric : str
            メトリック名 ("speed", "wind_speed", "heading", "density", "custom")
        custom_field : str, optional
            カスタムフィールド名, by default ""
        """
        valid_metrics = ["speed", "wind_speed", "heading", "density", "custom"]
        if metric in valid_metrics:
            self.set_property("metric", metric)
            if metric == "custom" and custom_field:
                self.set_property("custom_field", custom_field)
    
    def set_radius_and_blur(self, radius: int = None, blur: int = None) -> None:
        """
        ヒートマップの半径とぼかしを設定
        
        Parameters
        ----------
        radius : int, optional
            ポイント半径（ピクセル）, by default None
        blur : int, optional
            ぼかしの度合い（ピクセル）, by default None
        """
        if radius is not None:
            self.set_property("radius", max(5, min(50, int(radius))))
        if blur is not None:
            self.set_property("blur", max(0, min(50, int(blur))))
    
    def set_color_scale(self, color_scale: str, invert: bool = False) -> None:
        """
        カラースケールを設定
        
        Parameters
        ----------
        color_scale : str
            カラースケール名
        invert : bool, optional
            スケールの反転, by default False
        """
        valid_scales = ["default", "viridis", "plasma", "inferno", "magma", "blues", "greens", "reds", "spectral"]
        if color_scale in valid_scales:
            self.set_property("color_scale", color_scale)
            self.set_property("invert_scale", bool(invert))
    
    def set_custom_gradient(self, gradient: Dict[float, str]) -> None:
        """
        カスタムグラデーションを設定
        
        Parameters
        ----------
        gradient : Dict[float, str]
            値の割合から色へのマッピング（0.0-1.0の範囲の浮動小数点数をキーとするdict）
        """
        if gradient:
            self.set_property("gradient", dict(gradient))
            self.set_property("color_scale", "custom")
    
    def set_value_range(self, min_value: Optional[float] = None, max_value: Optional[float] = None) -> None:
        """
        値の範囲を設定
        
        Parameters
        ----------
        min_value : Optional[float], optional
            最小値, by default None
        max_value : Optional[float], optional
            最大値, by default None
        """
        if min_value is not None:
            self.set_property("min_value", float(min_value))
        if max_value is not None:
            self.set_property("max_value", float(max_value))
    
    def set_aggregation(self, method: str) -> None:
        """
        集約方法を設定
        
        Parameters
        ----------
        method : str
            集約方法 ("max", "min", "avg")
        """
        valid_methods = ["max", "min", "avg"]
        if method in valid_methods:
            self.set_property("aggregation", method)
    
    def set_discretize(self, enable: bool, num_bins: int = 10) -> None:
        """
        離散化設定
        
        Parameters
        ----------
        enable : bool
            離散化の有無
        num_bins : int, optional
            ビン数, by default 10
        """
        self.set_property("discretize", bool(enable))
        if num_bins > 0:
            self.set_property("num_bins", int(num_bins))
    
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
        
        # 設定を取得
        metric = self.get_property("metric", "speed")
        custom_field = self.get_property("custom_field", "")
        min_value = self.get_property("min_value", None)
        max_value = self.get_property("max_value", None)
        discretize = self.get_property("discretize", False)
        num_bins = self.get_property("num_bins", 10)
        smoothing = self.get_property("smoothing", 0)
        
        # 準備済みデータ
        prepared_data = {}
            'type': 'heat_map',
            'points': [],
            'bounds': None,
            'min_value': min_value,
            'max_value': max_value,
            'metric': metric,
            'custom_field': custom_field
        
        # データ形式に応じた処理
        if isinstance(data, list) and len(data) > 0:
            # リスト形式
            min_lat = min_lng = float('inf')
            max_lat = max_lng = float('-inf')
            all_values = []
            
            for point in data:
                if 'lat' in point and 'lng' in point:
                    lat = float(point['lat'])
                    lng = float(point['lng'])
                    
                    # 範囲更新
                    min_lat = min(min_lat, lat)
                    min_lng = min(min_lng, lng)
                    max_lat = max(max_lat, lat)
                    max_lng = max(max_lng, lng)
                    
                    # メトリック値の取得
                    value = None
                    if metric == "speed" and "speed" in point:
                        value = float(point["speed"])
                    elif metric == "wind_speed" and "wind_speed" in point:
                        value = float(point["wind_speed"])
                    elif metric == "heading" and "heading" in point:
                        value = float(point["heading"])
                    elif metric == "custom" and custom_field and custom_field in point:
                        value = float(point[custom_field])
                    elif metric == "density":
                        value = 1.0  # 密度の場合は常に1.0（点の数で密度を表現）
                    
                    if value is not None:
                        all_values.append(value)
                        prepared_data['points'].append('lat': lat,
                            'lng': lng,
                            'value': value
                        })
            
            # 境界設定
            if min_lat != float('inf') and min_lng != float('inf'):
                prepared_data['bounds'] = ((min_lat, min_lng), (max_lat, max_lng))
            
            # 最小・最大値の設定
            if all_values:
                if min_value is None:
                    prepared_data['min_value'] = min(all_values)
                if max_value is None:
                    prepared_data['max_value'] = max(all_values)
            
            # 離散化処理
            if discretize and prepared_data['min_value'] is not None and prepared_data['max_value'] is not None:
                bins = np.linspace(prepared_data['min_value'], prepared_data['max_value'], num_bins + 1)
                for point in prepared_data['points']:
                    # 値を対応するビンの中央値に変更
                    bin_index = np.digitize(point['value'], bins) - 1
                    if bin_index >= len(bins) - 1:
                        bin_index = len(bins) - 2
                    if bin_index < 0:
                        bin_index = 0
                    
                    point['value'] = (bins[bin_index] + bins[bin_index + 1]) / 2
            
            # 平滑化処理
            if smoothing > 0 and len(prepared_data['points']) > 0:
                # 平滑化の実装は簡易的な方法を使用
                # より高度な平滑化はバックエンドで実装する必要がある
                pass
        
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
        radius = self.get_property("radius", 15)
        blur = self.get_property("blur", 15)
        max_zoom = self.get_property("max_zoom", 18)
        min_opacity = self.get_property("min_opacity", 0.3)
        color_scale = self.get_property("color_scale", "default")
        invert_scale = self.get_property("invert_scale", False)
        gradient = self.get_property("gradient", None)
        show_legend = self.get_property("show_legend", True)
        intensity = self.get_property("intensity", 1.0)
        metric = self.get_property("metric", "speed")
        
        # カスタムグラデーションのJSON
        gradient_json = "null"
        if gradient:
            # JavaScriptのヒートマップレイヤー用に形式変換
            js_gradient = {}
            for k, v in gradient.items():
                js_gradient[str(k)] = v
            gradient_json = json.dumps(js_gradient)
        
        # JavaScript コード
        code = f"""
            // ヒートマップレイヤーの作成 {layer_id}
            {layer_var} = (function() {{
                var heatConfig = {{
                    radius: radius},
                    blur: {blur},
                    maxZoom: {max_zoom},
                    minOpacity: {min_opacity},
                    colorScale: '{color_scale}',
                    invertScale: {str(invert_scale).lower()},
                    gradient: {gradient_json},
                    showLegend: {str(show_legend).lower()},
                    intensity: {intensity},
                    metric: '{metric}'
                }};
                
                // ヒートマップレイヤーを作成するヘルパー関数
                function createHeatmapLayer(data, config) {{
                    // leaflet-heatmap.jsがロードされているか確認
                    if (typeof L.heatLayer !== 'function') {console.error('leaflet-heatmap.js library is not loaded.');
                        return L.layerGroup();
                    }}
                    
                    var points = data.points || [];
                    var minValue = data.min_value;
                    var maxValue = data.max_value;
                    
                    // データが空の場合は空のレイヤーグループを返す
                    if (!points.length) {return L.layerGroup();
                    }}
                    
                    // リーフレット用のデータ形式に変換
                    var heatmapData = [];
                    
                    for (var i = 0; i < points.length; i++) {{
                        var point = points[i];
                        var intensity = 1.0;
                        
                        // 値の正規化（密度以外の場合）
                        if (config.metric !== 'density' && minValue !== null && maxValue !== null && minValue !== maxValue) {{
                            intensity = (point.value - minValue) / (maxValue - minValue);
                            
                            // 必要に応じてスケールを反転
                            if (config.invertScale) {intensity = 1.0 - intensity;
                            }}
                        }}
                        
                        // 強度を調整
                        intensity *= config.intensity;
                        
                        heatmapData.push([point.lat, point.lng, intensity]);
                    }}
                    
                    // グラデーションの設定
                    var heatmapOptions = {radius: config.radius,
                        blur: config.blur,
                        maxZoom: config.maxZoom,
                        minOpacity: config.minOpacity
                    }};
                    
                    // カスタムグラデーションが指定されている場合
                    if (config.gradient) {heatmapOptions.gradient = config.gradient;
                    }} else if (config.colorScale !== 'default') {// 組み込みカラースケールの利用
                        heatmapOptions.gradient = getColorScale(config.colorScale, config.invertScale);
                    }}
                    
                    // ヒートマップレイヤーの作成
                    var heatLayer = L.heatLayer(heatmapData, heatmapOptions);
                    
                    // レイヤーグループの作成
                    var layerGroup = L.layerGroup();
                    heatLayer.addTo(layerGroup);
                    
                    // 凡例の追加
                    if (config.showLegend && config.metric !== 'density') {addHeatmapLegend(layerGroup, minValue, maxValue, config);
                    }}
                    
                    return layerGroup;
                }}
                
                // カラースケールのグラデーションを取得
                function getColorScale(scaleName, invert) {{
                    var gradient = null;
                    
                    if (scaleName === 'viridis') {{
                        gradient = {0.0: '#440154',
                            0.2: '#414487',
                            0.4: '#2a788e',
                            0.6: '#22a884',
                            0.8: '#7ad151',
                            1.0: '#fde725'
                        }};
                    }} else if (scaleName === 'plasma') {{
                        gradient = {0.0: '#0d0887',
                            0.2: '#5402a3',
                            0.4: '#8b0aa5',
                            0.6: '#cc4778',
                            0.8: '#fb8861',
                            1.0: '#fcfdbf'
                        }};
                    }} else if (scaleName === 'inferno') {{
                        gradient = {0.0: '#000004',
                            0.2: '#420a68',
                            0.4: '#932667',
                            0.6: '#dd513a',
                            0.8: '#fca50a',
                            1.0: '#fcffa4'
                        }};
                    }} else if (scaleName === 'magma') {{
                        gradient = {0.0: '#000004',
                            0.2: '#3b0f70',
                            0.4: '#8c2981',
                            0.6: '#dd4a69',
                            0.8: '#fa7e4b',
                            1.0: '#fcfdbf'
                        }};
                    }} else if (scaleName === 'blues') {{
                        gradient = {0.0: '#f7fbff',
                            0.2: '#d2e3f3',
                            0.4: '#9ecae1',
                            0.6: '#57a0ce',
                            0.8: '#2171b5',
                            1.0: '#084594'
                        }};
                    }} else if (scaleName === 'greens') {{
                        gradient = {0.0: '#f7fcf5',
                            0.2: '#c7e9c0',
                            0.4: '#86cc8f',
                            0.6: '#41ab5d',
                            0.8: '#1a702b',
                            1.0: '#00441b'
                        }};
                    }} else if (scaleName === 'reds') {{
                        gradient = {0.0: '#fff5f0',
                            0.2: '#fdbcaa',
                            0.4: '#fc8e6b',
                            0.6: '#ef563b',
                            0.8: '#c71d17',
                            1.0: '#7f0000'
                        }};
                    }} else if (scaleName === 'spectral') {{
                        gradient = {0.0: '#9e0142',
                            0.2: '#d53e4f',
                            0.4: '#f46d43',
                            0.6: '#fdae61',
                            0.8: '#66c2a5',
                            1.0: '#3288bd'
                        }};
                    }}
                    
                    // 反転フラグが設定されていれば反転
                    if (invert && gradient) {{
                        var inverted = {}};
                        var keys = Object.keys(gradient);
                        for (var i = 0; i < keys.length; i++) {var key = keys[i];
                            inverted[(1.0 - parseFloat(key)).toFixed(1)] = gradient[key];
                        }}
                        gradient = inverted;
                    }}
                    
                    return gradient;
                }}
                
                // 凡例の追加
                function addHeatmapLegend(layerGroup, minValue, maxValue, config) {{
                    var legend = L.control({position: 'bottomright' }});
                    
                    legend.onAdd = function(map) {{
                        var div = L.DomUtil.create('div', 'heatmap-legend');
                        div.style.backgroundColor = 'white';
                        div.style.padding = '10px';
                        div.style.border = '1px solid #ccc';
                        div.style.borderRadius = '5px';
                        div.style.opacity = '0.8';
                        
                        var title = '';
                        if (config.metric === 'speed') {title = '速度 (kt)';
                        }} else if (config.metric === 'wind_speed') {title = '風速 (kt)';
                        }} else if (config.metric === 'heading') {title = '方向 (°)';
                        }} else if (config.metric === 'custom') {title = 'カスタム値';
                        }}
                        
                        var html = '<div style="text-align: center; margin-bottom: 5px;"><b>' + title + '</b></div>';
                        
                        // 値の範囲が有効な場合のみ表示
                        if (minValue !== null && maxValue !== null && minValue !== maxValue) {{
                            // グラデーションバー
                            html += '<div style="display: flex; height: 20px; margin-bottom: 5px;">';
                            
                            // グラデーションの表示
                            var gradient = config.gradient;
                            if (!gradient && config.colorScale !== 'default') {gradient = getColorScale(config.colorScale, config.invertScale);
                            }}
                            
                            if (gradient) {{
                                // カスタムグラデーション
                                var gradientStyle = 'background: linear-gradient(to right, ';
                                var stops = [];
                                for (var pos in gradient) {{
                                    if (gradient.hasOwnProperty(pos)) {stops.push(gradient[pos] + ' ' + (parseFloat(pos) * 100) + '%');
                                    }}
                                }}
                                gradientStyle += stops.join(', ') + ');';
                                html += '<div style="flex: 1; ' + gradientStyle + '"></div>';
                            }} else {// デフォルトグラデーション（青→赤）
                                var invertClass = config.invertScale ? 'rev' : '';
                                html += '<div style="flex: 1; background: linear-gradient(to right, ' +
                                       (invertClass ? 'red, blue' : 'blue, red') + ');"></div>';
                            }}
                            
                            html += '</div>';
                            
                            // ラベル
                            html += '<div style="display: flex; justify-content: space-between;">';
                            html += '<div>' + (config.invertScale ? maxValue : minValue).toFixed(1) + '</div>';
                            html += '<div>' + ((minValue + maxValue) / 2).toFixed(1) + '</div>';
                            html += '<div>' + (config.invertScale ? minValue : maxValue).toFixed(1) + '</div>';
                            html += '</div>';
                        }} else {html += '<div>データ不足</div>';
                        }}
                        
                        div.innerHTML = html;
                        return div;
                    }};
                    
                    layerGroup.addLayer(legend);
                    return legend;
                }}
                
                // leaflet-heatmap.jsの読み込み
                function loadHeatmapLibrary(callback) {{
                    if (typeof L.heatLayer === 'function') {// 既にロード済み
                        callback();
                        return;
                    }}
                    
                    var script = document.createElement('script');
                    script.src = 'https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js';
                    script.onload = function() {callback();
                    }};
                    script.onerror = function() {console.error('Failed to load leaflet-heatmap.js');
                    }};
                    document.head.appendChild(script);
                }}
                
                // レイヤーを作成して返す
                var layerGroup = L.layerGroup();
                
                loadHeatmapLibrary(function() {{
                    if (typeof data_var} !== 'undefined' && {data_var} && {data_var}.points) {{
                        var heatLayer = createHeatmapLayer(data_var}, heatConfig);
                        
                        // レイヤーグループの全レイヤーをマップに追加
                        var heatLayers = heatLayer.getLayers();
                        for (var i = 0; i < heatLayers.length; i++) {layerGroup.addLayer(heatLayers[i]);
                        }}
                        
                        layerGroup.addTo({map_var});
                    }} else {{
                        console.warn('No heatmap data available for layer layer_id}');
                    }}
                }});
                
                // レイヤー情報を保存
                layerGroup.id = '{layer_id}';
                layerGroup.name = '{self.name}';
                layerGroup.type = 'heat_map';
                
                return layerGroup;
            }})();
        """
        
        return code
