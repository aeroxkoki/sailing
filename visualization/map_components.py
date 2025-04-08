"""
visualization.map_components

マップベースの可視化コンポーネントを提供するモジュールです。
GPSトラック、風向風速、戦略ポイントなどのデータを地図上に表示します。
"""

import streamlit as st
from streamlit_folium import folium_static
import folium
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
import colorsys
import json
import branca.colormap as cm

class MapLayerBase:
    """
    マップレイヤーの基底クラス
    
    すべてのマップレイヤーはこのクラスを継承します。
    """
    
    def __init__(self, layer_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        layer_id : str
            レイヤーの一意ID
        name : str, optional
            レイヤーの表示名
        """
        self.layer_id = layer_id
        self.name = name or layer_id
        self.visible = True
        self.z_index = 0
        self._properties = {}
    
    def set_property(self, name: str, value: Any) -> None:
        """
        プロパティを設定
        
        Parameters
        ----------
        name : str
            プロパティ名
        value : Any
            プロパティ値
        """
        self._properties[name] = value
    
    def get_property(self, name: str, default: Any = None) -> Any:
        """
        プロパティを取得
        
        Parameters
        ----------
        name : str
            プロパティ名
        default : Any, optional
            プロパティが存在しない場合のデフォルト値
            
        Returns
        -------
        Any
            プロパティ値
        """
        return self._properties.get(name, default)
    
    def render(self, map_obj: folium.Map) -> folium.Map:
        """
        レイヤーをレンダリング（オーバーライド用）
        
        Parameters
        ----------
        map_obj : folium.Map
            フォリウムマップオブジェクト
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # 基底クラスでは何もしない
        return map_obj


class GPSTrackLayer(MapLayerBase):
    """
    GPSトラックを表示するレイヤー
    """
    
    def __init__(self, layer_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        layer_id : str
            レイヤーの一意ID
        name : str, optional
            レイヤーの表示名
        """
        super().__init__(layer_id, name or "GPSトラック")
        
        # デフォルト設定
        self.set_property("color", "#3388ff")
        self.set_property("weight", 3)
        self.set_property("opacity", 0.7)
        self.set_property("show_markers", True)
        self.set_property("color_by", None)
        self.set_property("smoothing", False)
        self.set_property("max_points", 1000)
        
        # データ保持用
        self._data = None
        self._current_time = None
        self._selected_point = None
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """
        GPSトラックデータを設定
        
        Parameters
        ----------
        data : Dict[str, Any]
            GPSトラックデータ（timestamps, lats, lngsなどを含む辞書またはDataFrame）
        """
        self._data = data
    
    def set_current_time(self, time_value: Union[datetime, float]) -> None:
        """
        現在時刻を設定（時間同期用）
        
        Parameters
        ----------
        time_value : Union[datetime, float]
            設定する時刻（datetime型または開始からの秒数）
        """
        self._current_time = time_value
    
    def set_selected_point(self, point_index: int) -> None:
        """
        選択ポイントを設定
        
        Parameters
        ----------
        point_index : int
            選択されたポイントのインデックス
        """
        self._selected_point = point_index
    
    def _normalize_series(self, series: pd.Series) -> pd.Series:
        """
        系列を0〜1の範囲に正規化
        
        Parameters
        ----------
        series : pd.Series
            正規化する系列
            
        Returns
        -------
        pd.Series
            正規化された系列
        """
        min_val = series.min()
        max_val = series.max()
        
        if max_val == min_val:
            return pd.Series(0.5, index=series.index)
        
        return (series - min_val) / (max_val - min_val)
    
    def _get_color_list(self, normalized_values: pd.Series) -> List[str]:
        """
        正規化された値に対応する色リストを生成
        
        Parameters
        ----------
        normalized_values : pd.Series
            0〜1の範囲の正規化された値
            
        Returns
        -------
        List[str]
            16進数形式の色コードのリスト
        """
        colors = []
        
        for value in normalized_values:
            # HSVカラーモデルを使用（青から赤へのグラデーション）
            hue = 0.6 * (1 - value)  # 0.6（青）から0（赤）へ
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
            color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
            colors.append(color)
        
        return colors
    
    def _detect_significant_changes(self, series: pd.Series, threshold: float = 30.0) -> List[int]:
        """
        系列内の大きな変化を検出
        
        Parameters
        ----------
        series : pd.Series
            検査する系列
        threshold : float, optional
            閾値
            
        Returns
        -------
        List[int]
            大きな変化が検出されたインデックスのリスト
        """
        changes = []
        
        if len(series) < 2:
            return changes
        
        # 前後の値の差を計算
        diffs = series.diff().abs()
        
        # 角度の特殊処理（0度と360度が近い）
        if series.name == 'course' or series.name == 'direction' or series.name == 'heading':
            diffs = diffs.apply(lambda x: min(x, 360 - x) if not pd.isna(x) else x)
        
        # 閾値以上の変化を検出
        for i in range(1, len(diffs)):
            if diffs.iloc[i] >= threshold:
                changes.append(i)
        
        return changes
    
    def render(self, map_obj: folium.Map) -> folium.Map:
        """
        GPSトラックレイヤーをレンダリング
        
        Parameters
        ----------
        map_obj : folium.Map
            フォリウムマップオブジェクト
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # データが設定されていない場合
        if not self._data:
            return map_obj
        
        # 可視性チェック
        if not self.visible:
            return map_obj
        
        # データをDataFrameに変換
        df = self._data
        if not isinstance(df, pd.DataFrame):
            if isinstance(df, dict):
                df = pd.DataFrame(df)
            else:
                return map_obj
        
        # 必要なカラムをチェック
        required_columns = ['latitude', 'longitude']
        # latitude/longitudeの代わりにlat/lngがあれば変換
        if 'lat' in df.columns and 'latitude' not in df.columns:
            df['latitude'] = df['lat']
        if 'lng' in df.columns and 'longitude' not in df.columns:
            df['longitude'] = df['lng']
        
        if not all(col in df.columns for col in required_columns):
            return map_obj
        
        # データポイントが多すぎる場合はダウンサンプリング
        max_points = self.get_property("max_points", 1000)
        if len(df) > max_points:
            # 等間隔サンプリング（時間的に均等にポイントを選択）
            sample_rate = max(1, len(df) // max_points)
            df_sampled = df.iloc[::sample_rate].copy()
            df = df_sampled
        
        # 設定の取得
        line_color = self.get_property("color", "#3388ff")
        line_weight = self.get_property("weight", 3)
        line_opacity = self.get_property("opacity", 0.7)
        show_markers = self.get_property("show_markers", True)
        color_by = self.get_property("color_by", None)
        
        # 位置データの取得
        positions = list(zip(df['latitude'], df['longitude']))
        
        # フィーチャーグループの作成
        feature_group = folium.FeatureGroup(name=self.name)
        
        # カラーマッピングの設定
        if color_by is not None and color_by in df.columns:
            # カラーマップ用の値を正規化
            norm_values = self._normalize_series(df[color_by])
            colors = self._get_color_list(norm_values)
            
            # セグメント分割
            segments = []
            
            for i in range(len(positions) - 1):
                segments.append([positions[i], positions[i + 1]])
            
            # 各セグメントに対してラインを追加
            for i, segment in enumerate(segments):
                folium.PolyLine(
                    segment,
                    color=colors[i],
                    weight=line_weight,
                    opacity=line_opacity,
                    tooltip=f"{self.name}: {df[color_by].iloc[i]:.2f}"
                ).add_to(feature_group)
        else:
            # 単色ライン
            folium.PolyLine(
                positions,
                color=line_color,
                weight=line_weight,
                opacity=line_opacity,
                tooltip=self.name
            ).add_to(feature_group)
        
        # 始点と終点のマーカー
        if len(positions) > 0 and show_markers:
            # スタートマーカー
            folium.Marker(
                positions[0],
                tooltip=f"{self.name} スタート",
                icon=folium.Icon(color='green', icon='play', prefix='fa')
            ).add_to(feature_group)
            
            # ゴールマーカー
            folium.Marker(
                positions[-1],
                tooltip=f"{self.name} 最終点",
                icon=folium.Icon(color='red', icon='stop', prefix='fa')
            ).add_to(feature_group)
        
        # 追加のマーカー（重要な変化点など）
        if show_markers and len(positions) > 10:
            if 'course' in df.columns or 'heading' in df.columns:
                # コース変化の検出（例: タック）
                course_column = 'course' if 'course' in df.columns else 'heading'
                course_changes = self._detect_significant_changes(df[course_column], threshold=45)
                
                for idx in course_changes:
                    if 0 <= idx < len(positions):
                        folium.Marker(
                            positions[idx],
                            tooltip=f"{self.name} ターン: {df['timestamp'].iloc[idx] if 'timestamp' in df.columns else idx}",
                            icon=folium.Icon(color='blue', icon='exchange', prefix='fa')
                        ).add_to(feature_group)
        
        # 現在時刻のマーカー表示（時間同期がある場合）
        if self._current_time is not None and 'timestamp' in df.columns:
            current_idx = 0
            
            # 最も近い時間のインデックスを探す
            if isinstance(self._current_time, datetime) and isinstance(df['timestamp'].iloc[0], datetime):
                # 日時型同士の比較
                time_diffs = [(t - self._current_time).total_seconds() ** 2 for t in df['timestamp']]
                current_idx = time_diffs.index(min(time_diffs))
            elif isinstance(self._current_time, (int, float)) and isinstance(df['timestamp'].iloc[0], (int, float)):
                # 数値型同士の比較
                time_diffs = [(t - self._current_time) ** 2 for t in df['timestamp']]
                current_idx = time_diffs.index(min(time_diffs))
            elif isinstance(self._current_time, (int, float)) and isinstance(df['timestamp'].iloc[0], datetime):
                # 数値型とdatetime型の比較（相対時間）
                base_time = df['timestamp'].iloc[0]
                time_diffs = [((t - base_time).total_seconds() - self._current_time) ** 2 for t in df['timestamp']]
                current_idx = time_diffs.index(min(time_diffs))
            
            # 現在位置のマーカー
            if 0 <= current_idx < len(positions):
                # ポップアップ用テキスト
                popup_html = "<div style='min-width: 180px;'>"
                popup_html += f"<h4>{self.name}</h4>"
                popup_html += f"<p>時刻: {df['timestamp'].iloc[current_idx]}</p>"
                
                # 追加情報
                for col in ['speed', 'course', 'heading', 'wind_speed', 'wind_direction']:
                    if col in df.columns:
                        value = df[col].iloc[current_idx]
                        # 数値の場合は小数点以下2桁まで表示
                        if isinstance(value, (int, float)):
                            popup_html += f"<p>{col}: {value:.2f}</p>"
                        else:
                            popup_html += f"<p>{col}: {value}</p>"
                
                popup_html += "</div>"
                
                folium.Marker(
                    positions[current_idx],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"現在位置: {self.name}",
                    icon=folium.Icon(color='orange', icon='location-arrow', prefix='fa')
                ).add_to(feature_group)
        
        # 選択ポイントのマーカー表示
        if self._selected_point is not None and 0 <= self._selected_point < len(positions):
            folium.Marker(
                positions[self._selected_point],
                tooltip=f"選択ポイント: {self.name}",
                icon=folium.Icon(color='purple', icon='crosshairs', prefix='fa')
            ).add_to(feature_group)
        
        # マップにフィーチャーグループを追加
        feature_group.add_to(map_obj)
        
        return map_obj


class WindFieldLayer(MapLayerBase):
    """
    風向風速を表示するレイヤー
    """
    
    def __init__(self, layer_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        layer_id : str
            レイヤーの一意ID
        name : str, optional
            レイヤーの表示名
        """
        super().__init__(layer_id, name or "風向風速")
        
        # デフォルト設定
        self.set_property("color", "#3388ff")
        self.set_property("scale", 5.0)
        self.set_property("arrow_size", 5)
        self.set_property("opacity", 0.7)
        self.set_property("show_legend", True)
        self.set_property("interpolation", False)
        self.set_property("grid_size", 10)
        
        # データ保持用
        self._data = None
        self._current_time = None
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """
        風向風速データを設定
        
        Parameters
        ----------
        data : Dict[str, Any]
            風向風速データ
        """
        self._data = data
    
    def set_current_time(self, time_value: Union[datetime, float]) -> None:
        """
        現在時刻を設定（時間同期用）
        
        Parameters
        ----------
        time_value : Union[datetime, float]
            設定する時刻
        """
        self._current_time = time_value
    
    def render(self, map_obj: folium.Map) -> folium.Map:
        """
        風向風速レイヤーをレンダリング
        
        Parameters
        ----------
        map_obj : folium.Map
            フォリウムマップオブジェクト
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # データが設定されていない場合
        if not self._data:
            return map_obj
        
        # 可視性チェック
        if not self.visible:
            return map_obj
        
        # 設定の取得
        arrow_color = self.get_property("color", "#3388ff")
        arrow_scale = self.get_property("scale", 5.0)
        arrow_size = self.get_property("arrow_size", 5)
        arrow_opacity = self.get_property("opacity", 0.7)
        show_legend = self.get_property("show_legend", True)
        
        # フィーチャーグループを作成
        feature_group = folium.FeatureGroup(name=self.name)
        
        # データ形式に応じた処理
        if isinstance(self._data, dict):
            # 単一地点の風データ
            if 'position' in self._data:
                lat = self._data['position'].get('latitude', 0.0)
                lon = self._data['position'].get('longitude', 0.0)
                
                # 緯度/経度が配列ではなく単一の値である場合
                if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                    # 風向と風速の取得
                    direction = self._data.get('direction', 0.0)  # 北が0度、時計回り
                    speed = self._data.get('speed', 0.0)
                    
                    # 矢印の向きを計算（foliumの矢印は南北方向が0度）
                    arrow_angle = (90 - direction) % 360
                    
                    # 矢印の長さを風速に比例させる
                    length = arrow_scale * speed
                    
                    # 矢印を追加
                    folium.RegularPolygonMarker(
                        location=[lat, lon],
                        number_of_sides=3,
                        rotation=arrow_angle,
                        radius=length,
                        color=arrow_color,
                        fill_color=arrow_color,
                        fill_opacity=arrow_opacity,
                        popup=f"風向: {direction}°, 風速: {speed}ノット"
                    ).add_to(feature_group)
            
            # 風の格子データ
            elif 'positions' in self._data and 'directions' in self._data and 'speeds' in self._data:
                positions = self._data.get('positions', [])
                directions = self._data.get('directions', [])
                speeds = self._data.get('speeds', [])
                
                # データ数の確認
                n_points = min(len(positions), len(directions), len(speeds))
                
                if n_points > 0:
                    # 風速の最大値と最小値
                    max_speed = max(speeds) if speeds else 1.0
                    min_speed = min(speeds) if speeds else 0.0
                    
                    # 各格子点に風矢印を配置
                    for i in range(n_points):
                        lat, lon = positions[i]
                        direction = directions[i]
                        speed = speeds[i]
                        
                        # 風速に応じた色の調整
                        intensity = (speed - min_speed) / (max_speed - min_speed) if max_speed > min_speed else 0.5
                        rgb = colorsys.hsv_to_rgb(0.6, 0.8, 0.5 + 0.5 * intensity)  # 青から水色へのグラデーション
                        arrow_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
                        
                        # 矢印の向きを計算
                        arrow_angle = (90 - direction) % 360
                        
                        # 矢印の長さを風速に比例させる
                        length = arrow_size * (1 + intensity)
                        
                        # 矢印を追加
                        folium.RegularPolygonMarker(
                            location=[lat, lon],
                            number_of_sides=3,
                            rotation=arrow_angle,
                            radius=length,
                            color=arrow_color,
                            fill_color=arrow_color,
                            fill_opacity=arrow_opacity,
                            popup=f"風向: {direction}°, 風速: {speed}ノット"
                        ).add_to(feature_group)
                    
                    # 凡例を追加
                    if show_legend:
                        map_obj = self._add_wind_legend(map_obj, min_speed, max_speed)
            
            # 時間変化する風場データ
            elif 'wind_field' in self._data:
                wind_field = self._data['wind_field']
                
                # 必要なキーが存在するか確認
                if all(k in wind_field for k in ['lat_min', 'lat_max', 'lon_min', 'lon_max', 'nx', 'ny', 'u-wind', 'v-wind']):
                    # グリッド情報
                    lat_min = wind_field['lat_min']
                    lat_max = wind_field['lat_max']
                    lon_min = wind_field['lon_min']
                    lon_max = wind_field['lon_max']
                    nx = wind_field['nx']
                    ny = wind_field['ny']
                    
                    # 風速データ
                    u_wind = wind_field['u-wind']  # 東西方向の風速
                    v_wind = wind_field['v-wind']  # 南北方向の風速
                    
                    # 緯度経度グリッドを生成
                    lat_step = (lat_max - lat_min) / (ny - 1) if ny > 1 else 0
                    lon_step = (lon_max - lon_min) / (nx - 1) if nx > 1 else 0
                    
                    # グリッドの各点をプロット
                    for y in range(ny):
                        for x in range(nx):
                            lat = lat_min + y * lat_step
                            lon = lon_min + x * lon_step
                            
                            # 風速ベクトル
                            u = u_wind[y][x]
                            v = v_wind[y][x]
                            
                            # 風速と風向
                            speed = np.sqrt(u**2 + v**2)
                            direction = (270 - np.degrees(np.arctan2(v, u))) % 360
                            
                            # 風速に応じた色の調整
                            intensity = min(1.0, speed / 20.0)  # 20ノットを最大値として正規化
                            rgb = colorsys.hsv_to_rgb(0.6, 0.8, 0.5 + 0.5 * intensity)
                            arrow_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
                            
                            # 矢印の向きを計算
                            arrow_angle = (90 - direction) % 360
                            
                            # 矢印の長さを風速に比例させる
                            length = arrow_size * (1 + intensity)
                            
                            # 矢印を追加
                            folium.RegularPolygonMarker(
                                location=[lat, lon],
                                number_of_sides=3,
                                rotation=arrow_angle,
                                radius=length,
                                color=arrow_color,
                                fill_color=arrow_color,
                                fill_opacity=arrow_opacity,
                                popup=f"風向: {direction:.1f}°, 風速: {speed:.1f}ノット"
                            ).add_to(feature_group)
                    
                    # 凡例を追加
                    if show_legend:
                        map_obj = self._add_wind_legend(map_obj, 0, 20)
        
        # DataFrame形式の場合
        elif isinstance(self._data, pd.DataFrame):
            df = self._data
            
            # 必要なカラムのチェック
            required_columns = ['latitude', 'longitude', 'wind_direction', 'wind_speed']
            # latitude/longitudeの代わりにlat/lngがあれば変換
            if 'lat' in df.columns and 'latitude' not in df.columns:
                df['latitude'] = df['lat']
            if 'lng' in df.columns and 'longitude' not in df.columns:
                df['longitude'] = df['lng']
            
            if all(col in df.columns for col in required_columns):
                # 時間に応じたフィルタリング
                if self._current_time is not None and 'timestamp' in df.columns:
                    # 最も近い時間のデータを選択
                    if isinstance(self._current_time, datetime) and isinstance(df['timestamp'].iloc[0], datetime):
                        time_diffs = [(t - self._current_time).total_seconds() ** 2 for t in df['timestamp']]
                        current_idx = time_diffs.index(min(time_diffs))
                        df = df.iloc[[current_idx]]
                    elif isinstance(self._current_time, (int, float)) and isinstance(df['timestamp'].iloc[0], (int, float)):
                        time_diffs = [(t - self._current_time) ** 2 for t in df['timestamp']]
                        current_idx = time_diffs.index(min(time_diffs))
                        df = df.iloc[[current_idx]]
                
                # 各ポイントに風向風速を表示
                for _, row in df.iterrows():
                    lat = row['latitude']
                    lon = row['longitude']
                    direction = row['wind_direction']
                    speed = row['wind_speed']
                    
                    # 風速に応じた色の調整
                    intensity = min(1.0, speed / 20.0)  # 20ノットを最大値として正規化
                    rgb = colorsys.hsv_to_rgb(0.6, 0.8, 0.5 + 0.5 * intensity)
                    arrow_color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
                    
                    # 矢印の向きを計算
                    arrow_angle = (90 - direction) % 360
                    
                    # 矢印の長さを風速に比例させる
                    length = arrow_scale * speed
                    
                    # 矢印を追加
                    folium.RegularPolygonMarker(
                        location=[lat, lon],
                        number_of_sides=3,
                        rotation=arrow_angle,
                        radius=length,
                        color=arrow_color,
                        fill_color=arrow_color,
                        fill_opacity=arrow_opacity,
                        popup=f"風向: {direction}°, 風速: {speed}ノット"
                    ).add_to(feature_group)
                
                # 凡例を追加
                if show_legend:
                    min_speed = df['wind_speed'].min()
                    max_speed = df['wind_speed'].max()
                    map_obj = self._add_wind_legend(map_obj, min_speed, max_speed)
        
        # マップにフィーチャーグループを追加
        feature_group.add_to(map_obj)
        
        return map_obj
    
    def _add_wind_legend(self, map_obj: folium.Map, min_speed: float, max_speed: float) -> folium.Map:
        """
        風速の凡例を追加
        
        Parameters
        ----------
        map_obj : folium.Map
            フォリウムマップオブジェクト
        min_speed : float
            最小風速
        max_speed : float
            最大風速
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # カラーマップの作成
        colormap = cm.LinearColormap(
            colors=['blue', 'cyan', 'lightblue'],
            vmin=min_speed,
            vmax=max_speed,
            caption='風速 (ノット)'
        )
        
        # マップに追加
        colormap.add_to(map_obj)
        
        return map_obj


class StrategyPointLayer(MapLayerBase):
    """
    戦略ポイントを表示するレイヤー
    """
    
    def __init__(self, layer_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        layer_id : str
            レイヤーの一意ID
        name : str, optional
            レイヤーの表示名
        """
        super().__init__(layer_id, name or "戦略ポイント")
        
        # デフォルト設定
        self.set_property("show_all_points", True)
        self.set_property("min_importance", 0.0)
        self.set_property("max_importance", 1.0)
        self.set_property("filter_types", [])
        self.set_property("icon_size", "medium")  # "small", "medium", "large"
        
        # データ保持用
        self._data = None
        self._selected_point = None
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """
        戦略ポイントデータを設定
        
        Parameters
        ----------
        data : Dict[str, Any]
            戦略ポイントデータ
        """
        self._data = data
    
    def set_selected_point(self, point_id: Any) -> None:
        """
        選択ポイントを設定
        
        Parameters
        ----------
        point_id : Any
            選択された戦略ポイントのID
        """
        self._selected_point = point_id
    
    def render(self, map_obj: folium.Map) -> folium.Map:
        """
        戦略ポイントレイヤーをレンダリング
        
        Parameters
        ----------
        map_obj : folium.Map
            フォリウムマップオブジェクト
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # データが設定されていない場合
        if not self._data:
            return map_obj
        
        # 可視性チェック
        if not self.visible:
            return map_obj
        
        # 設定の取得
        show_all_points = self.get_property("show_all_points", True)
        min_importance = self.get_property("min_importance", 0.0)
        max_importance = self.get_property("max_importance", 1.0)
        filter_types = self.get_property("filter_types", [])
        icon_size = self.get_property("icon_size", "medium")
        
        # アイコンサイズの変換
        icon_pixel_size = {
            "small": 20,
            "medium": 30,
            "large": 40
        }.get(icon_size, 30)
        
        # フィーチャーグループを作成
        feature_group = folium.FeatureGroup(name=self.name)
        
        # データ処理
        if isinstance(self._data, dict):
            # ポイントリストの場合
            points_list = []
            
            if 'points' in self._data:
                # 標準的な形式
                points_list = self._data['points']
            elif 'features' in self._data:
                # GeoJSON形式
                points_list = self._data['features']
            elif isinstance(self._data.get('type'), str) and self._data.get('type') == 'FeatureCollection':
                # 完全なGeoJSON
                points_list = self._data.get('features', [])
            elif all(k in self._data for k in ['latitude', 'longitude', 'type']):
                # 単一ポイント
                points_list = [self._data]
            
            # ポイントを処理
            for i, point in enumerate(points_list):
                # 緯度経度の取得（データ形式によって異なる）
                if 'latitude' in point and 'longitude' in point:
                    lat = point['latitude']
                    lon = point['longitude']
                elif 'lat' in point and 'lng' in point:
                    lat = point['lat']
                    lon = point['lng']
                elif 'position' in point:
                    pos = point['position']
                    lat = pos.get('latitude', pos.get('lat'))
                    lon = pos.get('longitude', pos.get('lng'))
                elif 'geometry' in point and 'coordinates' in point['geometry']:
                    # GeoJSON形式
                    coords = point['geometry']['coordinates']
                    lon, lat = coords  # GeoJSONは[経度, 緯度]の順
                else:
                    continue  # 位置情報がない場合はスキップ
                
                # 点の種類を取得
                if 'properties' in point and 'type' in point['properties']:
                    point_type = point['properties']['type']
                elif 'type' in point:
                    point_type = point['type']
                else:
                    point_type = 'other'
                
                # 重要度を取得
                importance = 0.5  # デフォルト
                if 'properties' in point and 'importance' in point['properties']:
                    importance = point['properties']['importance']
                elif 'importance' in point:
                    importance = point['importance']
                
                # フィルタリング
                if not show_all_points:
                    # 重要度でフィルタリング
                    if not (min_importance <= importance <= max_importance):
                        continue
                    
                    # タイプでフィルタリング
                    if filter_types and point_type not in filter_types:
                        continue
                
                # ポイントのIDまたはインデックス
                point_id = point.get('id', i)
                
                # アイコン設定
                icon_config = self._get_icon_config(point_type)
                
                # 詳細情報の取得
                details = {}
                if 'properties' in point:
                    details = {k: v for k, v in point['properties'].items() if k not in ['type', 'importance']}
                elif 'details' in point:
                    details = point['details']
                else:
                    # 標準外のフィールドを詳細として扱う
                    std_fields = ['latitude', 'longitude', 'lat', 'lng', 'position', 'type', 'importance', 'id', 'name']
                    details = {k: v for k, v in point.items() if k not in std_fields}
                
                # 点の名前を取得
                if 'properties' in point and 'name' in point['properties']:
                    point_name = point['properties']['name']
                elif 'name' in point:
                    point_name = point['name']
                else:
                    point_name = f"{point_type.capitalize()} {i+1}"
                
                # 詳細情報のHTML生成
                detail_html = '<dl>'
                for key, value in details.items():
                    detail_html += f'<dt>{key}</dt><dd>{value}</dd>'
                detail_html += '</dl>'
                
                # 時間情報の取得
                timestamp = None
                timestamp_str = "N/A"
                if 'properties' in point and 'timestamp' in point['properties']:
                    timestamp = point['properties']['timestamp']
                elif 'timestamp' in point:
                    timestamp = point['timestamp']
                elif 'properties' in point and 'time' in point['properties']:
                    timestamp = point['properties']['time']
                elif 'time' in point:
                    timestamp = point['time']
                
                if timestamp:
                    if isinstance(timestamp, datetime):
                        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        timestamp_str = str(timestamp)
                
                # ポップアップのHTML
                popup_html = f"""
                <div style="min-width: 200px;">
                    <h4>{point_name}</h4>
                    <p>タイプ: {point_type}</p>
                    <p>時刻: {timestamp_str}</p>
                    <p>重要度: {importance:.2f}</p>
                    {detail_html}
                </div>
                """
                
                # 選択されたポイントかどうか
                is_selected = (self._selected_point is not None and point_id == self._selected_point)
                
                # マーカーの作成
                # 選択されている場合は目立つように表示
                icon_color = "red" if is_selected else icon_config['color']
                icon_prefix = "fa"
                
                # アイコンの作成（選択状態を反映）
                icon = folium.Icon(
                    color=icon_color,
                    icon=icon_config['icon'],
                    prefix=icon_prefix
                )
                
                # マーカーを追加
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"{point_name}: {point_type}",
                    icon=icon
                ).add_to(feature_group)
        
        # マップにフィーチャーグループを追加
        feature_group.add_to(map_obj)
        
        return map_obj
    
    def _get_icon_config(self, point_type: str) -> Dict[str, str]:
        """
        点の種類に応じたアイコン設定を取得
        
        Parameters
        ----------
        point_type : str
            点の種類
            
        Returns
        -------
        Dict[str, str]
            アイコン設定
        """
        # アイコンマッピング
        icon_mapping = {
            'tack': {'icon': 'exchange', 'color': 'blue'},
            'jibe': {'icon': 'refresh', 'color': 'purple'},
            'gybe': {'icon': 'refresh', 'color': 'purple'},  # 別表記
            'layline': {'icon': 'arrows', 'color': 'green'},
            'wind_shift': {'icon': 'random', 'color': 'orange'},
            'start': {'icon': 'play', 'color': 'green'},
            'finish': {'icon': 'stop', 'color': 'red'},
            'mark': {'icon': 'flag', 'color': 'cadetblue'},
            'mark_rounding': {'icon': 'flag-checkered', 'color': 'cadetblue'},
            'other': {'icon': 'info', 'color': 'gray'}
        }
        
        # マッピングから設定を取得（なければデフォルト）
        return icon_mapping.get(point_type.lower(), icon_mapping['other'])


class HeatMapLayer(MapLayerBase):
    """
    ヒートマップを表示するレイヤー
    """
    
    def __init__(self, layer_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        layer_id : str
            レイヤーの一意ID
        name : str, optional
            レイヤーの表示名
        """
        super().__init__(layer_id, name or "ヒートマップ")
        
        # デフォルト設定
        self.set_property("radius", 15)
        self.set_property("blur", 10)
        self.set_property("max_zoom", 18)
        self.set_property("min_opacity", 0.5)
        self.set_property("gradient", None)  # None=デフォルトグラデーション
        self.set_property("value_key", "value")
        
        # データ保持用
        self._data = None
    
    def set_data(self, data: Any) -> None:
        """
        ヒートマップデータを設定
        
        Parameters
        ----------
        data : Any
            ヒートマップデータ
        """
        self._data = data
    
    def render(self, map_obj: folium.Map) -> folium.Map:
        """
        ヒートマップレイヤーをレンダリング
        
        Parameters
        ----------
        map_obj : folium.Map
            フォリウムマップオブジェクト
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # データが設定されていない場合
        if not self._data:
            return map_obj
        
        # 可視性チェック
        if not self.visible:
            return map_obj
        
        # 設定の取得
        radius = self.get_property("radius", 15)
        blur = self.get_property("blur", 10)
        max_zoom = self.get_property("max_zoom", 18)
        min_opacity = self.get_property("min_opacity", 0.5)
        gradient = self.get_property("gradient", None)
        value_key = self.get_property("value_key", "value")
        
        # ヒートマップデータの準備
        heat_data = []
        
        # データタイプに応じた処理
        if isinstance(self._data, list):
            # リスト形式の場合
            for item in self._data:
                # 緯度経度の取得
                if isinstance(item, dict):
                    if 'latitude' in item and 'longitude' in item:
                        lat = item['latitude']
                        lng = item['longitude']
                    elif 'lat' in item and 'lng' in item:
                        lat = item['lat']
                        lng = item['lng']
                    else:
                        continue  # 位置情報がない場合はスキップ
                    
                    # 値の取得
                    value = 1.0  # デフォルト値
                    if value_key in item:
                        value = item[value_key]
                    
                    # ヒートマップデータに追加
                    heat_data.append([lat, lng, value])
                elif isinstance(item, (list, tuple)) and len(item) >= 2:
                    # リスト/タプル形式の場合
                    lat, lng = item[0], item[1]
                    value = item[2] if len(item) >= 3 else 1.0
                    heat_data.append([lat, lng, value])
        
        elif isinstance(self._data, pd.DataFrame):
            # DataFrame形式の場合
            df = self._data
            
            # 必要なカラムのチェック
            lat_col = next((col for col in ['latitude', 'lat'] if col in df.columns), None)
            lng_col = next((col for col in ['longitude', 'lng'] if col in df.columns), None)
            
            if lat_col and lng_col:
                # 値のカラム
                val_col = value_key if value_key in df.columns else None
                
                # ヒートマップデータの生成
                for _, row in df.iterrows():
                    lat = row[lat_col]
                    lng = row[lng_col]
                    value = row[val_col] if val_col else 1.0
                    heat_data.append([lat, lng, value])
        
        # ヒートマップデータが存在する場合
        if heat_data:
            # ヒートマッププラグインを使用
            from folium.plugins import HeatMap
            
            # ヒートマップレイヤーを作成
            heat_map = HeatMap(
                heat_data,
                name=self.name,
                radius=radius,
                blur=blur,
                max_zoom=max_zoom,
                min_opacity=min_opacity,
                gradient=gradient
            )
            
            # マップに追加
            heat_map.add_to(map_obj)
        
        return map_obj


class CourseLayer(MapLayerBase):
    """
    コース（マーク、ライン）を表示するレイヤー
    """
    
    def __init__(self, layer_id: str, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        layer_id : str
            レイヤーの一意ID
        name : str, optional
            レイヤーの表示名
        """
        super().__init__(layer_id, name or "コースレイアウト")
        
        # デフォルト設定
        self.set_property("show_marks", True)
        self.set_property("show_lines", True)
        self.set_property("show_labels", True)
        self.set_property("mark_color", "#ff4500")
        self.set_property("line_color", "#0000ff")
        self.set_property("line_width", 2)
        self.set_property("line_opacity", 0.7)
        
        # データ保持用
        self._data = None
    
    def set_data(self, data: Dict[str, Any]) -> None:
        """
        コースデータを設定
        
        Parameters
        ----------
        data : Dict[str, Any]
            コースデータ
        """
        self._data = data
    
    def render(self, map_obj: folium.Map) -> folium.Map:
        """
        コースレイヤーをレンダリング
        
        Parameters
        ----------
        map_obj : folium.Map
            フォリウムマップオブジェクト
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # データが設定されていない場合
        if not self._data:
            return map_obj
        
        # 可視性チェック
        if not self.visible:
            return map_obj
        
        # 設定の取得
        show_marks = self.get_property("show_marks", True)
        show_lines = self.get_property("show_lines", True)
        show_labels = self.get_property("show_labels", True)
        mark_color = self.get_property("mark_color", "#ff4500")
        line_color = self.get_property("line_color", "#0000ff")
        line_width = self.get_property("line_width", 2)
        line_opacity = self.get_property("line_opacity", 0.7)
        
        # フィーチャーグループを作成
        feature_group = folium.FeatureGroup(name=self.name)
        
        # マークのリスト
        marks = []
        
        # データ形式に応じた処理
        if isinstance(self._data, dict) and 'marks' in self._data:
            marks = self._data['marks']
        elif isinstance(self._data, list):
            marks = self._data
        
        # マークがある場合
        if marks and show_marks:
            # マークをレンダリング
            for i, mark in enumerate(marks):
                # 緯度経度の取得
                if 'latitude' in mark and 'longitude' in mark:
                    lat = mark['latitude']
                    lng = mark['longitude']
                elif 'lat' in mark and 'lng' in mark:
                    lat = mark['lat']
                    lng = mark['lng']
                elif 'position' in mark:
                    pos = mark['position']
                    lat = pos.get('latitude', pos.get('lat'))
                    lng = pos.get('longitude', pos.get('lng'))
                else:
                    continue  # 位置情報がない場合はスキップ
                
                # マークの名前を取得
                mark_name = mark.get('name', f"マーク {i+1}")
                
                # マークの種類に応じたアイコン設定
                icon_config = {'icon': 'flag', 'color': 'red'}
                
                # スタートマーク
                if mark.get('is_start', False):
                    icon_config = {'icon': 'play', 'color': 'green'}
                # フィニッシュマーク
                elif mark.get('is_finish', False):
                    icon_config = {'icon': 'stop', 'color': 'red'}
                # ゲートマーク
                elif mark.get('is_gate', False):
                    icon_config = {'icon': 'arrows-h', 'color': 'blue'}
                # 風上マーク
                elif 'windward' in mark_name.lower():
                    icon_config = {'icon': 'arrow-up', 'color': 'orange'}
                # 風下マーク
                elif 'leeward' in mark_name.lower():
                    icon_config = {'icon': 'arrow-down', 'color': 'purple'}
                
                # マークの色（個別設定があれば優先）
                mark_color_specific = mark.get('color', mark_color)
                
                # マーカーを追加
                folium.Marker(
                    location=[lat, lng],
                    tooltip=mark_name,
                    icon=folium.Icon(
                        color=icon_config['color'],
                        icon=icon_config['icon'],
                        prefix='fa'
                    )
                ).add_to(feature_group)
                
                # ラベルの表示
                if show_labels:
                    folium.map.Marker(
                        [lat, lng],
                        icon=folium.DivIcon(
                            icon_size=(150, 36),
                            icon_anchor=(0, 0),
                            html=f'<div style="font-size: 12pt; color: {mark_color_specific};">{mark_name}</div>'
                        )
                    ).add_to(feature_group)
            
            # ラインを描画
            if show_lines:
                # スタートラインの描画
                start_marks = [mark for mark in marks if mark.get('is_start', False)]
                if len(start_marks) >= 2:
                    for mark in start_marks:
                        if 'start_pair' in mark:
                            pair_idx = mark['start_pair']
                            if 0 <= pair_idx < len(marks):
                                # スタートライン
                                positions = []
                                if 'latitude' in mark and 'longitude' in mark:
                                    positions.append([mark['latitude'], mark['longitude']])
                                elif 'lat' in mark and 'lng' in mark:
                                    positions.append([mark['lat'], mark['lng']])
                                
                                pair = marks[pair_idx]
                                if 'latitude' in pair and 'longitude' in pair:
                                    positions.append([pair['latitude'], pair['longitude']])
                                elif 'lat' in pair and 'lng' in pair:
                                    positions.append([pair['lat'], pair['lng']])
                                
                                if len(positions) == 2:
                                    folium.PolyLine(
                                        positions,
                                        color='green',
                                        weight=line_width,
                                        opacity=line_opacity,
                                        tooltip="スタートライン"
                                    ).add_to(feature_group)
                
                # フィニッシュラインの描画
                finish_marks = [mark for mark in marks if mark.get('is_finish', False)]
                if len(finish_marks) >= 2:
                    for mark in finish_marks:
                        if 'finish_pair' in mark:
                            pair_idx = mark['finish_pair']
                            if 0 <= pair_idx < len(marks):
                                # フィニッシュライン
                                positions = []
                                if 'latitude' in mark and 'longitude' in mark:
                                    positions.append([mark['latitude'], mark['longitude']])
                                elif 'lat' in mark and 'lng' in mark:
                                    positions.append([mark['lat'], mark['lng']])
                                
                                pair = marks[pair_idx]
                                if 'latitude' in pair and 'longitude' in pair:
                                    positions.append([pair['latitude'], pair['longitude']])
                                elif 'lat' in pair and 'lng' in pair:
                                    positions.append([pair['lat'], pair['lng']])
                                
                                if len(positions) == 2:
                                    folium.PolyLine(
                                        positions,
                                        color='red',
                                        weight=line_width,
                                        opacity=line_opacity,
                                        tooltip="フィニッシュライン"
                                    ).add_to(feature_group)
                
                # ゲートの描画
                gate_marks = [mark for mark in marks if mark.get('is_gate', False)]
                if len(gate_marks) >= 2:
                    for mark in gate_marks:
                        if 'gate_pair' in mark:
                            pair_idx = mark['gate_pair']
                            if 0 <= pair_idx < len(marks):
                                # ゲートライン
                                positions = []
                                if 'latitude' in mark and 'longitude' in mark:
                                    positions.append([mark['latitude'], mark['longitude']])
                                elif 'lat' in mark and 'lng' in mark:
                                    positions.append([mark['lat'], mark['lng']])
                                
                                pair = marks[pair_idx]
                                if 'latitude' in pair and 'longitude' in pair:
                                    positions.append([pair['latitude'], pair['longitude']])
                                elif 'lat' in pair and 'lng' in pair:
                                    positions.append([pair['lat'], pair['lng']])
                                
                                if len(positions) == 2:
                                    folium.PolyLine(
                                        positions,
                                        color='blue',
                                        weight=line_width,
                                        opacity=line_opacity,
                                        tooltip="ゲート"
                                    ).add_to(feature_group)
                
                # コースラインの描画
                if 'course_order' in self._data:
                    # コース順序が指定されている場合
                    course_order = self._data['course_order']
                    positions = []
                    
                    for idx in course_order:
                        if 0 <= idx < len(marks):
                            mark = marks[idx]
                            if 'latitude' in mark and 'longitude' in mark:
                                positions.append([mark['latitude'], mark['longitude']])
                            elif 'lat' in mark and 'lng' in mark:
                                positions.append([mark['lat'], mark['lng']])
                    
                    if positions:
                        folium.PolyLine(
                            positions,
                            color=line_color,
                            weight=line_width,
                            opacity=line_opacity * 0.7,  # 少し透明に
                            tooltip="コースライン",
                            dash_array='5, 10'  # 破線
                        ).add_to(feature_group)
        
        # マップにフィーチャーグループを追加
        feature_group.add_to(map_obj)
        
        return map_obj


class MapVisualizer:
    """
    マップ可視化コンポーネントクラス
    
    Foliumを使用したインタラクティブなマップを提供します。
    """
    
    def __init__(self):
        """初期化"""
        self.name = "マップ可視化"
        
        # マップの設定
        self._map_center = [35.45, 139.65]  # デフォルト: 横浜
        self._map_zoom = 13
        self._map_tile = "OpenStreetMap"
        
        # 利用可能なタイル
        self.available_tiles = {
            'OpenStreetMap': 'OpenStreetMap',
            'Stamen Terrain': 'Stamen Terrain',
            'Stamen Toner': 'Stamen Toner',
            'Stamen Watercolor': 'Stamen Watercolor',
            'CartoDB positron': 'CartoDB positron',
            'CartoDB dark_matter': 'CartoDB dark_matter',
            'ポジトロン（海図風）': 'CartoDB positron'
        }
        
        # レイヤー管理
        self._layers = {}
        self._layer_order = []
        
        # マップオブジェクトをキャッシュ
        self._map_cache = None
        self._cache_key = None
    
    def set_center(self, lat: float, lng: float) -> None:
        """
        地図の中心を設定
        
        Parameters
        ----------
        lat : float
            中心緯度
        lng : float
            中心経度
        """
        self._map_center = [lat, lng]
        self._cache_key = None  # キャッシュを無効化
    
    def set_zoom(self, zoom: int) -> None:
        """
        ズームレベルを設定
        
        Parameters
        ----------
        zoom : int
            ズームレベル（1-18）
        """
        self._map_zoom = max(1, min(18, zoom))
        self._cache_key = None  # キャッシュを無効化
    
    def set_tile(self, tile: str) -> None:
        """
        地図タイルを設定
        
        Parameters
        ----------
        tile : str
            タイル名
        """
        if tile in self.available_tiles:
            self._map_tile = tile
            self._cache_key = None  # キャッシュを無効化
    
    def add_layer(self, layer: MapLayerBase) -> None:
        """
        レイヤーを追加
        
        Parameters
        ----------
        layer : MapLayerBase
            追加するレイヤー
        """
        if layer.layer_id not in self._layers:
            self._layers[layer.layer_id] = layer
            self._layer_order.append(layer.layer_id)
            self._cache_key = None  # キャッシュを無効化
    
    def remove_layer(self, layer_id: str) -> bool:
        """
        レイヤーを削除
        
        Parameters
        ----------
        layer_id : str
            削除するレイヤーのID
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if layer_id in self._layers:
            del self._layers[layer_id]
            self._layer_order.remove(layer_id)
            self._cache_key = None  # キャッシュを無効化
            return True
        return False
    
    def get_layer(self, layer_id: str) -> Optional[MapLayerBase]:
        """
        レイヤーを取得
        
        Parameters
        ----------
        layer_id : str
            取得するレイヤーのID
            
        Returns
        -------
        Optional[MapLayerBase]
            レイヤーオブジェクト、なければNone
        """
        return self._layers.get(layer_id)
    
    def get_all_layers(self) -> Dict[str, MapLayerBase]:
        """
        すべてのレイヤーを取得
        
        Returns
        -------
        Dict[str, MapLayerBase]
            レイヤーID: レイヤーオブジェクトの辞書
        """
        return self._layers
    
    def set_layer_visibility(self, layer_id: str, visible: bool) -> bool:
        """
        レイヤーの表示/非表示を設定
        
        Parameters
        ----------
        layer_id : str
            レイヤーID
        visible : bool
            表示する場合True
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if layer_id in self._layers:
            self._layers[layer_id].visible = visible
            self._cache_key = None  # キャッシュを無効化
            return True
        return False
    
    def set_layer_order(self, layer_order: List[str]) -> None:
        """
        レイヤーの表示順序を設定
        
        Parameters
        ----------
        layer_order : List[str]
            レイヤーIDのリスト（上から順）
        """
        # 有効なレイヤーIDのみで順序を更新
        valid_ids = [layer_id for layer_id in layer_order if layer_id in self._layers]
        
        # 順序に含まれていないレイヤーを追加
        for layer_id in self._layers.keys():
            if layer_id not in valid_ids:
                valid_ids.append(layer_id)
        
        self._layer_order = valid_ids
        self._cache_key = None  # キャッシュを無効化
    
    def create_map(self) -> folium.Map:
        """
        Foliumマップオブジェクトを作成
        
        Returns
        -------
        folium.Map
            作成されたマップオブジェクト
        """
        # キャッシュキーの生成
        cache_key = f"{self._map_center}-{self._map_zoom}-{self._map_tile}"
        
        # キャッシュにある場合はそれを返す
        if self._cache_key == cache_key and self._map_cache is not None:
            return self._map_cache
        
        # タイル名の変換
        tile_name = self.available_tiles.get(self._map_tile, 'OpenStreetMap')
        
        # マップオブジェクトの作成
        m = folium.Map(
            location=self._map_center,
            zoom_start=self._map_zoom,
            tiles=tile_name,
            control_scale=True
        )
        
        # レイヤーコントロールを追加
        folium.LayerControl().add_to(m)
        
        # キャッシュを更新
        self._map_cache = m
        self._cache_key = cache_key
        
        return m
    
    def render_layers(self, map_obj: folium.Map) -> folium.Map:
        """
        すべてのレイヤーをレンダリング
        
        Parameters
        ----------
        map_obj : folium.Map
            マップオブジェクト
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # レイヤー順にレンダリング
        for layer_id in self._layer_order:
            if layer_id in self._layers:
                layer = self._layers[layer_id]
                if layer.visible:
                    map_obj = layer.render(map_obj)
        
        return map_obj
    
    def render(self, width: int = 800, height: int = 600, key: Optional[str] = None) -> None:
        """
        マップをStreamlitに表示
        
        Parameters
        ----------
        width : int, optional
            表示幅, by default 800
        height : int, optional
            表示高さ, by default 600
        key : Optional[str], optional
            Streamlitコンポーネントのキー
        """
        # マップオブジェクトを作成
        map_obj = self.create_map()
        
        # レイヤーをレンダリング
        map_obj = self.render_layers(map_obj)
        
        # Streamlitに表示
        folium_static(map_obj, width=width, height=height, key=key)
    
    def to_dict(self) -> Dict:
        """
        現在の設定を辞書として出力
        
        Returns
        -------
        Dict
            現在の設定を含む辞書
        """
        return {
            "map_center": self._map_center,
            "map_zoom": self._map_zoom,
            "map_tile": self._map_tile,
            "layer_order": self._layer_order
        }
    
    def from_dict(self, config: Dict) -> None:
        """
        辞書から設定を読み込み
        
        Parameters
        ----------
        config : Dict
            設定を含む辞書
        """
        if "map_center" in config:
            self._map_center = config["map_center"]
        if "map_zoom" in config:
            self._map_zoom = config["map_zoom"]
        if "map_tile" in config and config["map_tile"] in self.available_tiles:
            self._map_tile = config["map_tile"]
        if "layer_order" in config:
            # 有効なレイヤーIDのみを使用
            valid_ids = [layer_id for layer_id in config["layer_order"] if layer_id in self._layers]
            # 順序に含まれていないレイヤーを追加
            for layer_id in self._layers.keys():
                if layer_id not in valid_ids:
                    valid_ids.append(layer_id)
            self._layer_order = valid_ids
        
        # キャッシュを無効化
        self._cache_key = None
