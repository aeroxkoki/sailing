# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
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
        }
        
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
        
        # JavaScript簡略コード - 構文エラーを避けるため簡素化
        code = f"""
            // 風場レイヤーの作成 {layer_id}
            {layer_var} = (function() {{
                // 設定
                var windFieldConfig = {{
                    displayType: '{display_type}',
                    arrowScale: {arrow_scale},
                    arrowDensity: {arrow_density},
                    colorScale: '{color_scale}',
                    colorBy: '{color_by}',
                    minSpeed: {min_speed if min_speed is not None else "null"},
                    maxSpeed: {max_speed if max_speed is not None else "null"},
                    animate: {str(animate).lower()},
                    showLegend: {str(show_legend).lower()},
                    opacity: {opacity},
                    customColors: {custom_colors_js},
                    minFilter: {min_filter},
                    maxFilter: {max_filter}
                }};
                
                // レイヤーを作成して返す
                var layer = null;
                
                // 基本的なレイヤーグループを作成
                layer = L.layerGroup().addTo({map_var});
                
                // レイヤー情報を保存
                layer.id = '{layer_id}';
                layer.name = '{self.name}';
                layer.type = 'wind_field';
                
                return layer;
            }})();
        """
        
        return code
