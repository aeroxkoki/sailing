"""
sailing_data_processor.visualization.map_components

マップベースの可視化コンポーネントを提供するモジュール。
GPSトラック、風向風速、戦略ポイントなどのレイヤー表示が可能なマップコンポーネントを提供します。
"""

import os
import json
import uuid
from typing import Dict, List, Any, Optional, Union, Callable, Tuple, Set
import numpy as np
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta

from sailing_data_processor.visualization.visualization_manager import VisualizationComponent
from sailing_data_processor.reporting.elements.map.layers.base_layer import BaseMapLayer
from sailing_data_processor.reporting.elements.map.layers.enhanced_layer_manager import EnhancedLayerManager

class MapLayerConfiguration:
    """
    マップレイヤーの設定情報を保持するクラス
    """
    
    def __init__(self, layer_id: str, name: str, type_name: str, visible: bool = True, 
                properties: Dict[str, Any] = None):
        """
        初期化
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        name : str
            レイヤー名
        type_name : str
            レイヤータイプ名
        visible : bool, optional
            表示状態, by default True
        properties : Dict[str, Any], optional
            プロパティ辞書, by default None
        """
        self.layer_id = layer_id
        self.name = name
        self.type_name = type_name
        self.visible = visible
        self.properties = properties or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書表現に変換
        
        Returns
        -------
        Dict[str, Any]
            辞書表現
        """
        return {
            "layer_id": self.layer_id,
            "name": self.name,
            "type_name": self.type_name,
            "visible": self.visible,
            "properties": self.properties.copy()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MapLayerConfiguration":
        """
        辞書から生成
        
        Parameters
        ----------
        data : Dict[str, Any]
            辞書データ
            
        Returns
        -------
        MapLayerConfiguration
            生成されたオブジェクト
        """
        return cls(
            layer_id=data["layer_id"],
            name=data["name"],
            type_name=data["type_name"],
            visible=data.get("visible", True),
            properties=data.get("properties", {}).copy()
        )


class MapVisualizationComponent(VisualizationComponent):
    """
    Foliumを使用したマップベースの可視化コンポーネント
    """
    
    def __init__(self, component_id: str = None, name: str = None):
        """
        初期化
        
        Parameters
        ----------
        component_id : str, optional
            コンポーネントID
        name : str, optional
            コンポーネント名
        """
        super().__init__(
            component_id=component_id,
            component_type="map",
            name=name or "マップ表示"
        )
        
        # マップの基本設定
        self._center = [35.4498, 139.6649]  # デフォルト: 横浜
        self._zoom = 13
        self._map_type = "OpenStreetMap"
        
        # レイヤー管理
        self._layer_manager = EnhancedLayerManager()
        
        # 追加の視覚化設定
        self._show_markers = True
        self._color_by = None
        self._max_points = 1000  # 最大表示ポイント数（パフォーマンス用）
        self._auto_fit = True    # データに合わせて自動ズーム
        
        # イベントのセットアップ
        self.setup_events()
    
    def setup_events(self):
        """イベントハンドラの初期設定"""
        # マップ移動イベントのハンドラを登録
        self.on("map_moved", self._handle_map_moved)
        # レイヤー変更イベントのハンドラを登録
        self.on("layer_changed", self._handle_layer_changed)
        # データ更新イベントのハンドラを登録
        self.on("data_updated", self._handle_data_updated)
        # 選択変更イベントのハンドラを登録
        self.on("selection_changed", self._handle_selection_changed)
    
    def _handle_map_moved(self, component, event_name, event_data):
        """マップ移動イベントハンドラ"""
        if isinstance(event_data, dict) and "center" in event_data and "zoom" in event_data:
            self._center = event_data["center"]
            self._zoom = event_data["zoom"]
    
    def _handle_layer_changed(self, component, event_name, event_data):
        """レイヤー変更イベントハンドラ"""
        # 必要に応じて再レンダリング
        pass
    
    def _handle_data_updated(self, component, event_name, event_data):
        """データ更新イベントハンドラ"""
        if self.data_source:
            # データソースが更新された場合、関連するレイヤーも更新
            for layer in self._layer_manager.get_all_layers():
                if layer.data_source == self.data_source:
                    self._layer_manager.update_data_source(self.data_source, event_data)
    
    def _handle_selection_changed(self, component, event_name, event_data):
        """選択変更イベントハンドラ"""
        # 選択が変更された場合の処理
        pass
    
    @property
    def center(self) -> List[float]:
        """マップの中心座標"""
        return self._center
    
    @center.setter
    def center(self, value: List[float]):
        """マップの中心座標を設定"""
        if isinstance(value, list) and len(value) == 2:
            self._center = value
    
    @property
    def zoom(self) -> int:
        """マップのズームレベル"""
        return self._zoom
    
    @zoom.setter
    def zoom(self, value: int):
        """マップのズームレベルを設定"""
        self._zoom = max(1, min(20, int(value)))
    
    @property
    def map_type(self) -> str:
        """マップのタイプ"""
        return self._map_type
    
    @map_type.setter
    def map_type(self, value: str):
        """マップのタイプを設定"""
        allowed_types = ["OpenStreetMap", "CartoDB positron", "CartoDB dark_matter", "Stamen Terrain", "Stamen Toner"]
        if value in allowed_types:
            self._map_type = value
    
    @property
    def layer_manager(self) -> EnhancedLayerManager:
        """レイヤーマネージャー"""
        return self._layer_manager
    
    @property
    def show_markers(self) -> bool:
        """マーカー表示状態"""
        return self._show_markers
    
    @show_markers.setter
    def show_markers(self, value: bool):
        """マーカー表示状態を設定"""
        self._show_markers = bool(value)
    
    @property
    def color_by(self) -> Optional[str]:
        """色付けの基準フィールド"""
        return self._color_by
    
    @color_by.setter
    def color_by(self, value: Optional[str]):
        """色付けの基準フィールドを設定"""
        self._color_by = value
    
    @property
    def max_points(self) -> int:
        """最大表示ポイント数"""
        return self._max_points
    
    @max_points.setter
    def max_points(self, value: int):
        """最大表示ポイント数を設定"""
        self._max_points = max(100, int(value))
    
    @property
    def auto_fit(self) -> bool:
        """データに合わせて自動ズーム"""
        return self._auto_fit
    
    @auto_fit.setter
    def auto_fit(self, value: bool):
        """自動ズーム設定を変更"""
        self._auto_fit = bool(value)
    
    def add_layer(self, layer: BaseMapLayer, group: Optional[str] = None) -> str:
        """
        レイヤーを追加
        
        Parameters
        ----------
        layer : BaseMapLayer
            追加するレイヤー
        group : Optional[str], optional
            グループ名
            
        Returns
        -------
        str
            レイヤーID
        """
        layer_id = self._layer_manager.add_layer(layer, group)
        # レイヤー変更イベントを発火
        self.trigger("layer_changed", {"action": "add", "layer_id": layer_id})
        return layer_id
    
    def remove_layer(self, layer_id: str) -> Optional[BaseMapLayer]:
        """
        レイヤーを削除
        
        Parameters
        ----------
        layer_id : str
            削除するレイヤーID
            
        Returns
        -------
        Optional[BaseMapLayer]
            削除されたレイヤー
        """
        layer = self._layer_manager.remove_layer(layer_id)
        if layer:
            # レイヤー変更イベントを発火
            self.trigger("layer_changed", {"action": "remove", "layer_id": layer_id})
        return layer
    
    def get_layer(self, layer_id: str) -> Optional[BaseMapLayer]:
        """
        レイヤーを取得
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
            
        Returns
        -------
        Optional[BaseMapLayer]
            レイヤー
        """
        return self._layer_manager.get_layer(layer_id)
    
    def toggle_layer_visibility(self, layer_id: str, visible: bool = None) -> bool:
        """
        レイヤーの表示/非表示を切り替え
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        visible : bool, optional
            表示状態、Noneの場合は現在の状態を反転
            
        Returns
        -------
        bool
            操作後の表示状態
        """
        layer = self.get_layer(layer_id)
        if not layer:
            return False
        
        current = layer.visible
        if visible is None:
            layer.visible = not current
        else:
            layer.visible = visible
        
        # レイヤー変更イベントを発火
        self.trigger("layer_changed", {
            "action": "visibility", 
            "layer_id": layer_id, 
            "visible": layer.visible
        })
        
        return layer.visible
    
    def update_layer_properties(self, layer_id: str, properties: Dict[str, Any]) -> bool:
        """
        レイヤーのプロパティを更新
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        properties : Dict[str, Any]
            更新するプロパティ
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        layer = self.get_layer(layer_id)
        if not layer:
            return False
        
        for key, value in properties.items():
            if hasattr(layer, key) and key != "layer_id":
                setattr(layer, key, value)
        
        # レイヤー変更イベントを発火
        self.trigger("layer_changed", {
            "action": "properties", 
            "layer_id": layer_id, 
            "properties": properties
        })
        
        return True
    
    def create_map(self, context: Dict[str, Any] = None) -> folium.Map:
        """
        Foliumマップを作成
        
        Parameters
        ----------
        context : Dict[str, Any], optional
            レンダリングコンテキスト
            
        Returns
        -------
        folium.Map
            作成されたマップオブジェクト
        """
        # マップを作成
        folium_map = folium.Map(
            location=self._center,
            zoom_start=self._zoom,
            tiles=self._map_type,
            control_scale=True
        )
        
        # レイヤー用コンテキストを準備
        merged_context = {}
        if context:
            merged_context.update(context)
        
        # コンポーネントがデータソースを持っている場合はコンテキストに追加
        if self.data_source and context and self.data_source in context:
            self._layer_manager.set_context_data(self.data_source, context[self.data_source])
        
        # 現在のマップコンテキストも追加
        merged_context["map_center"] = self._center
        merged_context["map_zoom"] = self._zoom
        merged_context["show_markers"] = self._show_markers
        merged_context["color_by"] = self._color_by
        merged_context["max_points"] = self._max_points
        
        # レイヤーをレンダリング
        for layer in self._layer_manager.get_all_layers():
            if not layer.visible:
                continue
            
            try:
                # レイヤーを描画
                layer.render_to_map(folium_map, merged_context)
            except Exception as e:
                st.error(f"レイヤー描画エラー: {str(e)}")
        
        # データに自動フィットするオプションが有効な場合
        if self._auto_fit and context and self.data_source in context:
            try:
                data = context[self.data_source]
                bounds = self._extract_bounds_from_data(data)
                if bounds:
                    folium_map.fit_bounds(bounds)
            except Exception as e:
                st.warning(f"自動ズーム調整エラー: {str(e)}")
        
        # マップオブジェクトを返す
        return folium_map
    
    def _extract_bounds_from_data(self, data: Any) -> Optional[List[List[float]]]:
        """
        データから境界情報を抽出
        
        Parameters
        ----------
        data : Any
            データオブジェクト
            
        Returns
        -------
        Optional[List[List[float]]]
            [[min_lat, min_lng], [max_lat, max_lng]] 形式の境界情報
            データがない場合はNone
        """
        if isinstance(data, pd.DataFrame):
            # DataFrameの場合
            lat_cols = [col for col in data.columns if col.lower() in ['lat', 'latitude']]
            lng_cols = [col for col in data.columns if col.lower() in ['lon', 'lng', 'longitude']]
            
            if lat_cols and lng_cols:
                lat_col = lat_cols[0]
                lng_col = lng_cols[0]
                
                if not data.empty:
                    min_lat = data[lat_col].min()
                    max_lat = data[lat_col].max()
                    min_lng = data[lng_col].min()
                    max_lng = data[lng_col].max()
                    
                    # 境界に余裕を持たせる（10%程度）
                    lat_padding = (max_lat - min_lat) * 0.1
                    lng_padding = (max_lng - min_lng) * 0.1
                    
                    return [
                        [min_lat - lat_padding, min_lng - lng_padding],
                        [max_lat + lat_padding, max_lng + lng_padding]
                    ]
        
        elif isinstance(data, list) and data:
            # リスト形式の場合
            if isinstance(data[0], dict):
                # 辞書のリストの場合
                lat_keys = [key for key in data[0].keys() if key.lower() in ['lat', 'latitude']]
                lng_keys = [key for key in data[0].keys() if key.lower() in ['lon', 'lng', 'longitude']]
                
                if lat_keys and lng_keys:
                    lat_key = lat_keys[0]
                    lng_key = lng_keys[0]
                    
                    lats = [item[lat_key] for item in data if lat_key in item]
                    lngs = [item[lng_key] for item in data if lng_key in item]
                    
                    if lats and lngs:
                        min_lat = min(lats)
                        max_lat = max(lats)
                        min_lng = min(lngs)
                        max_lng = max(lngs)
                        
                        # 境界に余裕を持たせる（10%程度）
                        lat_padding = (max_lat - min_lat) * 0.1
                        lng_padding = (max_lng - min_lng) * 0.1
                        
                        return [
                            [min_lat - lat_padding, min_lng - lng_padding],
                            [max_lat + lat_padding, max_lng + lng_padding]
                        ]
        
        return None
    
    def render(self, context: Dict[str, Any] = None) -> Any:
        """
        マップをレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any], optional
            レンダリングコンテキスト
            
        Returns
        -------
        Any
            レンダリング結果
        """
        # コンテキストがない場合は空の辞書を使用
        if context is None:
            context = {}
        
        # マップを作成
        folium_map = self.create_map(context)
        
        # Streamlitに表示
        folium_static(folium_map, width=800)
        
        # マップ設定情報
        with st.expander("マップ設定", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                lat = st.number_input(
                    "緯度", 
                    value=self._center[0], 
                    min_value=-90.0, 
                    max_value=90.0,
                    step=0.0001,
                    format="%.6f",
                    key=f"{self.component_id}_lat"
                )
            with col2:
                lng = st.number_input(
                    "経度", 
                    value=self._center[1], 
                    min_value=-180.0, 
                    max_value=180.0,
                    step=0.0001,
                    format="%.6f",
                    key=f"{self.component_id}_lng"
                )
            
            zoom = st.slider(
                "ズームレベル", 
                min_value=1, 
                max_value=20, 
                value=self._zoom,
                key=f"{self.component_id}_zoom"
            )
            
            map_type = st.selectbox(
                "マップタイプ",
                options=["OpenStreetMap", "CartoDB positron", "CartoDB dark_matter", "Stamen Terrain", "Stamen Toner"],
                index=["OpenStreetMap", "CartoDB positron", "CartoDB dark_matter", "Stamen Terrain", "Stamen Toner"].index(self._map_type),
                key=f"{self.component_id}_map_type"
            )
            
            # 表示設定
            st.write("### 表示設定")
            col1, col2 = st.columns(2)
            
            with col1:
                show_markers = st.checkbox(
                    "マーカーを表示", 
                    value=self._show_markers,
                    key=f"{self.component_id}_show_markers"
                )
            
            with col2:
                auto_fit = st.checkbox(
                    "データに自動フィット", 
                    value=self._auto_fit,
                    key=f"{self.component_id}_auto_fit"
                )
            
            # 色付けオプション
            color_options = ["なし", "速度", "風向", "時間"]
            color_by_index = 0
            
            if self._color_by == "speed":
                color_by_index = 1
            elif self._color_by == "wind_direction":
                color_by_index = 2
            elif self._color_by == "timestamp":
                color_by_index = 3
            
            color_by = st.selectbox(
                "色付け基準", 
                options=color_options,
                index=color_by_index,
                key=f"{self.component_id}_color_by"
            )
            
            # 値を変換
            color_by_value = None
            if color_by == "速度":
                color_by_value = "speed"
            elif color_by == "風向":
                color_by_value = "wind_direction"
            elif color_by == "時間":
                color_by_value = "timestamp"
            
            # パフォーマンス設定
            max_points = st.number_input(
                "最大表示ポイント数", 
                value=self._max_points,
                min_value=100,
                max_value=10000,
                step=100,
                key=f"{self.component_id}_max_points"
            )
            
            # 設定が変更された場合に更新
            if (lat != self._center[0] or lng != self._center[1] or 
                zoom != self._zoom or map_type != self._map_type or
                show_markers != self._show_markers or auto_fit != self._auto_fit or
                color_by_value != self._color_by or max_points != self._max_points):
                
                self._center = [lat, lng]
                self._zoom = zoom
                self._map_type = map_type
                self._show_markers = show_markers
                self._auto_fit = auto_fit
                self._color_by = color_by_value
                self._max_points = max_points
                
                # 設定変更を反映するために再レンダリング
                st.rerun()
        
        # レイヤー情報
        with st.expander("レイヤー管理", expanded=False):
            layers = self._layer_manager.get_all_layers()
            if not layers:
                st.info("レイヤーはありません。レイヤーを追加してください。")
            else:
                for layer in layers:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**{layer.name}** ({layer.layer_id[:8]}...)")
                    with col2:
                        visible = st.checkbox(
                            "表示", 
                            value=layer.visible, 
                            key=f"vis_{layer.layer_id}"
                        )
                        if visible != layer.visible:
                            self.toggle_layer_visibility(layer.layer_id, visible)
                            st.rerun()
        
        return folium_map
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書表現に変換
        
        Returns
        -------
        Dict[str, Any]
            辞書表現
        """
        # 基底クラスの変換結果を取得
        data = super().to_dict()
        
        # マップコンポーネント固有のデータを追加
        data.update({
            "center": self._center,
            "zoom": self._zoom,
            "map_type": self._map_type,
            "show_markers": self._show_markers,
            "color_by": self._color_by,
            "max_points": self._max_points,
            "auto_fit": self._auto_fit,
            "layer_manager": self._layer_manager.to_dict()
        })
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MapVisualizationComponent":
        """
        辞書から生成
        
        Parameters
        ----------
        data : Dict[str, Any]
            辞書データ
            
        Returns
        -------
        MapVisualizationComponent
            生成されたオブジェクト
        """
        # 基底クラスから生成（注意: ここでは基底クラスのメソッドを直接呼び出さず、新しいインスタンスを作成）
        component = cls(
            component_id=data.get("component_id"),
            name=data.get("name")
        )
        
        # 基底クラスのプロパティを設定
        component._visible = data.get("visible", True)
        component._properties = data.get("properties", {}).copy()
        component._data_source = data.get("data_source")
        
        # マップコンポーネント固有のデータを設定
        component._center = data.get("center", [35.4498, 139.6649])
        component._zoom = data.get("zoom", 13)
        component._map_type = data.get("map_type", "OpenStreetMap")
        component._show_markers = data.get("show_markers", True)
        component._color_by = data.get("color_by")
        component._max_points = data.get("max_points", 1000)
        component._auto_fit = data.get("auto_fit", True)
        
        # レイヤーマネージャーの復元（必要に応じて）
        # 注: 完全な実装には、レイヤークラスの登録などが必要
        
        return component


class PlaybackMapComponent(MapVisualizationComponent):
    """
    時間軸に沿ったプレイバック機能を持つマップ可視化コンポーネント
    """
    
    def __init__(self, component_id: str = None, name: str = None):
        """
        初期化
        
        Parameters
        ----------
        component_id : str, optional
            コンポーネントID
        name : str, optional
            コンポーネント名
        """
        super().__init__(component_id=component_id, name=name or "プレイバック可能マップ")
        
        # プレイバック関連の設定
        self._current_time = None
        self._start_time = None
        self._end_time = None
        self._time_step = timedelta(seconds=1)
        self._playing = False
        self._playback_speed = 1.0
        self._loop = False
        self._time_field = "timestamp"
    
    @property
    def current_time(self) -> Optional[datetime]:
        """現在の再生時刻"""
        return self._current_time
    
    @current_time.setter
    def current_time(self, value: Optional[datetime]):
        """現在の再生時刻を設定"""
        self._current_time = value
        # 時間変更イベントを発火
        self.trigger("time_changed", {"current_time": value})
    
    @property
    def time_field(self) -> str:
        """時間フィールド名"""
        return self._time_field
    
    @time_field.setter
    def time_field(self, value: str):
        """時間フィールド名を設定"""
        self._time_field = value
    
    @property
    def playing(self) -> bool:
        """再生中かどうか"""
        return self._playing
    
    @playing.setter
    def playing(self, value: bool):
        """再生状態を設定"""
        self._playing = bool(value)
        if value:
            self.trigger("playback_started", {"current_time": self._current_time})
        else:
            self.trigger("playback_paused", {"current_time": self._current_time})
    
    @property
    def playback_speed(self) -> float:
        """再生速度"""
        return self._playback_speed
    
    @playback_speed.setter
    def playback_speed(self, value: float):
        """再生速度を設定"""
        self._playback_speed = max(0.1, min(10.0, float(value)))
    
    @property
    def loop(self) -> bool:
        """ループ再生設定"""
        return self._loop
    
    @loop.setter
    def loop(self, value: bool):
        """ループ再生設定を変更"""
        self._loop = bool(value)
    
    def analyze_time_range(self, data: Any) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        データの時間範囲を分析
        
        Parameters
        ----------
        data : Any
            分析対象データ
            
        Returns
        -------
        Tuple[Optional[datetime], Optional[datetime]]
            開始時刻と終了時刻
        """
        if not data:
            return None, None
        
        # データの形式に応じて時間範囲を抽出
        time_field = self._time_field
        
        if isinstance(data, list) and data:
            # リスト形式のデータ
            times = []
            for item in data:
                if isinstance(item, dict) and time_field in item:
                    time_str = item[time_field]
                    try:
                        time = pd.to_datetime(time_str)
                        times.append(time)
                    except:
                        pass
            
            if times:
                return min(times), max(times)
        
        elif isinstance(data, pd.DataFrame) and not data.empty and time_field in data.columns:
            # DataFrameの場合
            try:
                time_series = pd.to_datetime(data[time_field])
                return time_series.min(), time_series.max()
            except:
                pass
        
        return None, None
    
    def setup_playback(self, data: Any = None) -> bool:
        """
        プレイバック設定を初期化
        
        Parameters
        ----------
        data : Any, optional
            時間範囲を決定するためのデータ
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if data is None and self.data_source:
            # データソースからデータを取得
            context = self.get_property("context", {})
            if self.data_source in context:
                data = context[self.data_source]
        
        if not data:
            return False
        
        # 時間範囲を分析
        start_time, end_time = self.analyze_time_range(data)
        if not start_time or not end_time:
            return False
        
        # プレイバック設定
        self._start_time = start_time
        self._end_time = end_time
        
        # 開始時刻を現在時刻に設定
        if self._current_time is None or self._current_time < start_time or self._current_time > end_time:
            self._current_time = start_time
        
        # 時間ステップを計算（データ全体の1/100程度）
        time_range = (end_time - start_time).total_seconds()
        self._time_step = timedelta(seconds=max(1, time_range / 100))
        
        return True
    
    def play(self):
        """プレイバックを開始"""
        self._playing = True
        # プレイ開始イベントを発火
        self.trigger("playback_started", {"current_time": self._current_time})
    
    def pause(self):
        """プレイバックを一時停止"""
        self._playing = False
        # 一時停止イベントを発火
        self.trigger("playback_paused", {"current_time": self._current_time})
    
    def stop(self):
        """プレイバックを停止して先頭に戻る"""
        self._playing = False
        self._current_time = self._start_time
        # 停止イベントを発火
        self.trigger("playback_stopped", {"current_time": self._current_time})
    
    def set_time_position(self, position: float):
        """
        時間位置を設定（0.0～1.0）
        
        Parameters
        ----------
        position : float
            時間位置（0.0: 開始時刻、1.0: 終了時刻）
        """
        if self._start_time is None or self._end_time is None:
            return
        
        position = max(0.0, min(1.0, position))
        time_range = (self._end_time - self._start_time).total_seconds()
        offset = timedelta(seconds=time_range * position)
        self._current_time = self._start_time + offset
        
        # 時間変更イベントを発火
        self.trigger("time_changed", {"current_time": self._current_time})
    
    def set_speed(self, speed: float):
        """
        再生速度を設定
        
        Parameters
        ----------
        speed : float
            再生速度（1.0: 通常速度）
        """
        self._playback_speed = max(0.1, min(10.0, speed))
    
    def set_loop(self, loop: bool):
        """
        ループ再生の設定
        
        Parameters
        ----------
        loop : bool
            ループ再生を有効にする場合True
        """
        self._loop = loop
    
    def step_forward(self):
        """次のステップに進む"""
        if self._current_time is None or self._end_time is None:
            return
        
        step = self._time_step * self._playback_speed
        new_time = self._current_time + step
        
        if new_time > self._end_time:
            if self._loop:
                new_time = self._start_time
            else:
                new_time = self._end_time
                self._playing = False
        
        self._current_time = new_time
        
        # 時間変更イベントを発火
        self.trigger("time_changed", {"current_time": self._current_time})
    
    def step_backward(self):
        """前のステップに戻る"""
        if self._current_time is None or self._start_time is None:
            return
        
        step = self._time_step * self._playback_speed
        new_time = self._current_time - step
        
        if new_time < self._start_time:
            if self._loop:
                new_time = self._end_time
            else:
                new_time = self._start_time
        
        self._current_time = new_time
        
        # 時間変更イベントを発火
        self.trigger("time_changed", {"current_time": self._current_time})
    
    def update_playback(self):
        """プレイバック状態を更新"""
        if self._playing:
            self.step_forward()
    
    def filter_data_by_time(self, data: Any) -> Any:
        """
        現在時刻に基づいてデータをフィルタリング
        
        Parameters
        ----------
        data : Any
            フィルタリング対象データ
            
        Returns
        -------
        Any
            フィルタリングされたデータ
        """
        if not data or self._current_time is None:
            return data
        
        time_field = self._time_field
        
        if isinstance(data, list) and data:
            # リスト形式のデータ
            filtered_data = []
            for item in data:
                if isinstance(item, dict) and time_field in item:
                    time_str = item[time_field]
                    try:
                        time = pd.to_datetime(time_str)
                        if time <= self._current_time:
                            filtered_data.append(item)
                    except:
                        # 時間形式が解析できない場合はスキップ
                        pass
            
            return filtered_data
        
        elif isinstance(data, pd.DataFrame) and not data.empty and time_field in data.columns:
            # DataFrameの場合
            try:
                time_series = pd.to_datetime(data[time_field])
                return data[time_series <= self._current_time]
            except:
                # 時間形式が解析できない場合は元のデータを返す
                pass
        
        return data
    
    def render(self, context: Dict[str, Any] = None) -> Any:
        """
        プレイバック機能付きマップをレンダリング
        
        Parameters
        ----------
        context : Dict[str, Any], optional
            レンダリングコンテキスト
            
        Returns
        -------
        Any
            レンダリング結果
        """
        # コンテキストがない場合は空の辞書を使用
        if context is None:
            context = {}
        
        # プレイバック設定
        if self._start_time is None or self._end_time is None:
            self.setup_playback(context.get(self.data_source))
        
        # 時間フィルタリングを適用したコンテキストを作成
        filtered_context = context.copy()
        
        if self.data_source and self.data_source in context:
            filtered_data = self.filter_data_by_time(context[self.data_source])
            filtered_context[self.data_source] = filtered_data
        
        # プレイバックコントロール
        st.subheader("プレイバックコントロール")
        
        if self._start_time is not None and self._end_time is not None:
            # 現在時刻を表示
            current_time_str = self._current_time.strftime("%Y-%m-%d %H:%M:%S") if self._current_time else "不明"
            start_time_str = self._start_time.strftime("%Y-%m-%d %H:%M:%S")
            end_time_str = self._end_time.strftime("%Y-%m-%d %H:%M:%S")
            
            st.write(f"時間範囲: {start_time_str} 〜 {end_time_str}")
            st.write(f"現在時刻: {current_time_str}")
            
            # 時間スライダー
            if self._start_time and self._end_time:
                time_range = (self._end_time - self._start_time).total_seconds()
                if time_range > 0 and self._current_time:
                    current_position = (self._current_time - self._start_time).total_seconds() / time_range
                    new_position = st.slider(
                        "時間位置", 
                        0.0, 1.0, 
                        float(current_position), 
                        0.01,
                        key=f"{self.component_id}_time_slider"
                    )
                    
                    if new_position != current_position:
                        self.set_time_position(new_position)
                        st.rerun()
            
            # プレイバックコントロールボタン
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                if st.button(
                    "⏮️ 先頭", 
                    key=f"{self.component_id}_first"
                ):
                    self._current_time = self._start_time
                    st.rerun()
            
            with col2:
                if st.button(
                    "⏪ 前へ", 
                    key=f"{self.component_id}_prev"
                ):
                    self.step_backward()
                    st.rerun()
            
            with col3:
                if self._playing:
                    if st.button(
                        "⏸️ 一時停止", 
                        key=f"{self.component_id}_pause"
                    ):
                        self.pause()
                        st.rerun()
                else:
                    if st.button(
                        "▶️ 再生", 
                        key=f"{self.component_id}_play"
                    ):
                        self.play()
                        st.rerun()
            
            with col4:
                if st.button(
                    "⏩ 次へ", 
                    key=f"{self.component_id}_next"
                ):
                    self.step_forward()
                    st.rerun()
            
            with col5:
                if st.button(
                    "⏭️ 末尾", 
                    key=f"{self.component_id}_last"
                ):
                    self._current_time = self._end_time
                    st.rerun()
            
            # 再生速度とループ設定
            col1, col2 = st.columns(2)
            
            with col1:
                speed = st.slider(
                    "再生速度", 
                    0.1, 10.0, 
                    float(self._playback_speed), 
                    0.1,
                    key=f"{self.component_id}_speed"
                )
                if speed != self._playback_speed:
                    self.set_speed(speed)
            
            with col2:
                loop = st.checkbox(
                    "ループ再生", 
                    value=self._loop,
                    key=f"{self.component_id}_loop"
                )
                if loop != self._loop:
                    self.set_loop(loop)
        else:
            st.warning("時間範囲が設定されていません。有効なデータを読み込んでください。")
        
        # マップを描画（基底クラスのrenderメソッドを使用）
        super().render(filtered_context)
        
        # 再生中の場合は状態を更新して再描画
        if self._playing:
            self.update_playback()
            import time
            time.sleep(0.1)  # 短い遅延を入れて連続的な更新の負荷を抑制
            st.rerun()
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書表現に変換
        
        Returns
        -------
        Dict[str, Any]
            辞書表現
        """
        # 基底クラスの変換結果を取得
        data = super().to_dict()
        
        # プレイバックコンポーネント固有のデータを追加
        data.update({
            "time_field": self._time_field,
            "playback_speed": self._playback_speed,
            "loop": self._loop,
            "playing": self._playing
        })
        
        # 時間情報（シリアライズ可能な形式に変換）
        if self._current_time:
            data["current_time"] = self._current_time.isoformat()
        if self._start_time:
            data["start_time"] = self._start_time.isoformat()
        if self._end_time:
            data["end_time"] = self._end_time.isoformat()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlaybackMapComponent":
        """
        辞書から生成
        
        Parameters
        ----------
        data : Dict[str, Any]
            辞書データ
            
        Returns
        -------
        PlaybackMapComponent
            生成されたオブジェクト
        """
        # 基底クラスから生成（注: ここでも新しいインスタンスを作成）
        component = cls(
            component_id=data.get("component_id"),
            name=data.get("name")
        )
        
        # 基底クラスのプロパティを設定
        component._visible = data.get("visible", True)
        component._properties = data.get("properties", {}).copy()
        component._data_source = data.get("data_source")
        component._center = data.get("center", [35.4498, 139.6649])
        component._zoom = data.get("zoom", 13)
        component._map_type = data.get("map_type", "OpenStreetMap")
        component._show_markers = data.get("show_markers", True)
        component._color_by = data.get("color_by")
        component._max_points = data.get("max_points", 1000)
        component._auto_fit = data.get("auto_fit", True)
        
        # プレイバックコンポーネント固有のデータを設定
        component._time_field = data.get("time_field", "timestamp")
        component._playback_speed = data.get("playback_speed", 1.0)
        component._loop = data.get("loop", False)
        component._playing = data.get("playing", False)
        
        # 時間情報の復元
        if "current_time" in data:
            try:
                component._current_time = pd.to_datetime(data["current_time"])
            except:
                component._current_time = None
        
        if "start_time" in data:
            try:
                component._start_time = pd.to_datetime(data["start_time"])
            except:
                component._start_time = None
        
        if "end_time" in data:
            try:
                component._end_time = pd.to_datetime(data["end_time"])
            except:
                component._end_time = None
        
        return component
