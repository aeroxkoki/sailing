"""
ui.components.visualizations.map_view

マップビューコンポーネント - GPSトラックなどを地図上に表示するためのコンポーネント
"""

import streamlit as st
import folium
from streamlit_folium import folium_static
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
import random
import colorsys
from sailing_data_processor.data_model.container import GPSDataContainer, WindDataContainer, StrategyPointContainer
from ui.data_binding import DataBindingManager, UIStateManager

class MapViewComponent:
    """
    マップ表示用のコンポーネント
    
    GPS位置データを地図上に可視化するためのコンポーネントです。
    """
    
    def __init__(self, data_binding: DataBindingManager, ui_state: UIStateManager):
        """
        初期化
        
        Parameters
        ----------
        data_binding : DataBindingManager
            データバインディング管理オブジェクト
        ui_state : UIStateManager
            UI状態管理オブジェクト
        """
        self.data_binding = data_binding
        self.ui_state = ui_state
        
        # 利用可能な地図タイル
        self.available_tiles = {
            'OpenStreetMap': 'OpenStreetMap',
            'Stamen Terrain': 'Stamen Terrain',
            'Stamen Toner': 'Stamen Toner',
            'Stamen Watercolor': 'Stamen Watercolor',
            'CartoDB positron': 'CartoDB positron',
            'CartoDB dark_matter': 'CartoDB dark_matter',
            'ポジトロン（海図風）': 'CartoDB positron'
        }
        
        # マップオブジェクトをキャッシュ
        self._map_cache = None
        self._cache_key = None
    
    def create_map(self, center: Optional[Tuple[float, float]] = None, 
                  zoom_start: int = 13, 
                  tile: str = 'OpenStreetMap') -> folium.Map:
        """
        Foliumマップオブジェクトを作成
        
        Parameters
        ----------
        center : Optional[Tuple[float, float]], optional
            地図の中心座標 (緯度, 経度)
        zoom_start : int, optional
            初期ズームレベル
        tile : str, optional
            地図タイル名
            
        Returns
        -------
        folium.Map
            作成されたマップオブジェクト
        """
        # 中心座標とズームレベルの設定
        if center is None:
            map_settings = self.ui_state.get_state('map_settings', {})
            center = map_settings.get('center', [35.45, 139.65])
            zoom_start = map_settings.get('zoom', 13)
        
        # タイル名の設定
        if tile not in self.available_tiles:
            tile = 'OpenStreetMap'
        
        # タイル名の変換
        tile_name = self.available_tiles.get(tile, tile)
        
        # マップオブジェクトの作成
        m = folium.Map(
            location=center,
            zoom_start=zoom_start,
            tiles=tile_name,
            control_scale=True
        )
        
        # レイヤーコントロールを追加
        folium.LayerControl().add_to(m)
        
        # マップをキャッシュ
        cache_key = f"{center}-{zoom_start}-{tile}"
        self._map_cache = m
        self._cache_key = cache_key
        
        return m
    
    def add_gps_track(self, 
                     map_obj: folium.Map, 
                     container: GPSDataContainer,
                     name: str = 'トラック',
                     color: Optional[str] = None,
                     show_markers: bool = True,
                     color_by: Optional[str] = None,
                     max_points: int = 1000) -> folium.Map:
        """
        マップにGPSトラックを追加
        
        Parameters
        ----------
        map_obj : folium.Map
            追加先のマップオブジェクト
        container : GPSDataContainer
            GPS位置データを含むコンテナ
        name : str, optional
            レイヤー名
        color : Optional[str], optional
            ラインの色。Noneの場合はランダムに生成
        show_markers : bool, optional
            重要ポイントにマーカーを表示するか
        color_by : Optional[str], optional
            カラーマッピングの基準とする列名
        max_points : int, optional
            表示する最大ポイント数（パフォーマンス最適化用）
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # データフレームを取得
        df = container.data
        
        # データポイントが多すぎる場合はダウンサンプリング
        if len(df) > max_points:
            # 等間隔サンプリング（時間的に均等にポイントを選択）
            sample_rate = max(1, len(df) // max_points)
            df_sampled = df.iloc[::sample_rate].copy()
            st.session_state['_downsampling_applied'] = True
            st.session_state['_original_points'] = len(df)
            st.session_state['_sampled_points'] = len(df_sampled)
            df = df_sampled
        else:
            if '_downsampling_applied' in st.session_state:
                del st.session_state['_downsampling_applied']
        
        # 位置データの取得
        positions = list(zip(df['latitude'], df['longitude']))
        
        # 色が指定されていない場合はランダムに生成
        if color is None:
            hue = random.random()
            rgb = colorsys.hsv_to_rgb(hue, 0.8, 0.8)
            color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
        
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
                    weight=3,
                    opacity=0.8,
                    tooltip=f"{name}: {df[color_by].iloc[i]:.2f}"
                ).add_to(map_obj)
        else:
            # 単色ライン
            folium.PolyLine(
                positions,
                color=color,
                weight=3,
                opacity=0.7,
                tooltip=name
            ).add_to(map_obj)
        
        # 始点と終点のマーカー
        if len(positions) > 0:
            # スタートマーカー
            folium.Marker(
                positions[0],
                tooltip=f"{name} スタート",
                icon=folium.Icon(color='green', icon='play', prefix='fa')
            ).add_to(map_obj)
            
            # ゴールマーカー
            folium.Marker(
                positions[-1],
                tooltip=f"{name} ゴール",
                icon=folium.Icon(color='red', icon='stop', prefix='fa')
            ).add_to(map_obj)
        
        # 追加のマーカー（必要に応じて）
        if show_markers and len(positions) > 10:
            # 主要な変化点などにマーカーを追加
            if 'course' in df.columns:
                # コース変化の検出（例: タック）
                course_changes = self._detect_significant_changes(df['course'], threshold=45)
                
                for idx in course_changes:
                    if 0 <= idx < len(positions):
                        folium.Marker(
                            positions[idx],
                            tooltip=f"{name} ターン: {df['timestamp'].iloc[idx]}",
                            icon=folium.Icon(color='blue', icon='exchange', prefix='fa')
                        ).add_to(map_obj)
        
        return map_obj
    
    def add_wind_arrows(self, 
                        map_obj: folium.Map,
                        container: WindDataContainer,
                        name: str = '風',
                        color: str = 'blue',
                        scale: float = 5.0) -> folium.Map:
        """
        マップに風向を示す矢印を追加
        
        Parameters
        ----------
        map_obj : folium.Map
            追加先のマップオブジェクト
        container : WindDataContainer
            風データを含むコンテナ
        name : str, optional
            レイヤー名
        color : str, optional
            矢印の色
        scale : float, optional
            矢印のスケール
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # 風データの取得
        wind_data = container.data
        
        # 位置座標を取得
        if 'position' in wind_data:
            lat = wind_data['position'].get('latitude', 0.0)
            lon = wind_data['position'].get('longitude', 0.0)
            
            # 風向と風速の取得
            direction = wind_data.get('direction', 0.0)  # 北が0度、時計回り
            speed = wind_data.get('speed', 0.0)
            
            # 矢印の向きを計算（foliumの矢印は南北方向が0度）
            arrow_angle = (90 - direction) % 360
            
            # 矢印の長さを風速に比例させる
            length = scale * speed
            
            # 矢印を追加
            folium.RegularPolygonMarker(
                location=[lat, lon],
                number_of_sides=3,
                rotation=arrow_angle,
                radius=length,
                color=color,
                fill_color=color,
                fill_opacity=0.6,
                popup=f"風向: {direction}°, 風速: {speed}ノット"
            ).add_to(map_obj)
        
        return map_obj
    
    def add_wind_field(self, 
                      map_obj: folium.Map,
                      wind_grid: Dict[str, Any],
                      name: str = '風分布',
                      color: str = 'blue',
                      opacity: float = 0.7) -> folium.Map:
        """
        マップに風の場を追加
        
        Parameters
        ----------
        map_obj : folium.Map
            追加先のマップオブジェクト
        wind_grid : Dict[str, Any]
            風の格子データ
            {'positions': [(lat, lon), ...], 'directions': [dir, ...], 'speeds': [speed, ...]}
        name : str, optional
            レイヤー名
        color : str, optional
            矢印の基本色
        opacity : float, optional
            透明度
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # 風の格子データを取得
        positions = wind_grid.get('positions', [])
        directions = wind_grid.get('directions', [])
        speeds = wind_grid.get('speeds', [])
        
        # データ数の確認
        n_points = min(len(positions), len(directions), len(speeds))
        
        if n_points == 0:
            return map_obj
        
        # 風速の最大値と最小値
        max_speed = max(speeds) if speeds else 1.0
        min_speed = min(speeds) if speeds else 0.0
        
        # 風矢印を各格子点に配置
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
            length = 3 + 7 * intensity  # 3〜10の範囲でスケール
            
            # 矢印を追加
            folium.RegularPolygonMarker(
                location=[lat, lon],
                number_of_sides=3,
                rotation=arrow_angle,
                radius=length,
                color=arrow_color,
                fill_color=arrow_color,
                fill_opacity=opacity,
                popup=f"風向: {direction}°, 風速: {speed}ノット"
            ).add_to(map_obj)
        
        return map_obj
    
    def add_strategy_points(self, 
                           map_obj: folium.Map,
                           container: StrategyPointContainer,
                           name: str = '戦略ポイント') -> folium.Map:
        """
        マップに戦略ポイントを追加
        
        Parameters
        ----------
        map_obj : folium.Map
            追加先のマップオブジェクト
        container : StrategyPointContainer
            戦略ポイントデータを含むコンテナ
        name : str, optional
            レイヤー名
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # 戦略ポイントのデータを取得
        point_data = container.data
        
        # ポイントのタイプを取得
        point_type = point_data.get('type', 'other')
        
        # 位置情報の取得
        position = point_data.get('position', {})
        lat = position.get('latitude', 0.0)
        lon = position.get('longitude', 0.0)
        
        # 重要度
        importance = point_data.get('importance', 0.5)
        
        # タイプに応じたアイコン設定
        icon_mapping = {
            'tack': {'icon': 'exchange', 'color': 'blue'},
            'jibe': {'icon': 'refresh', 'color': 'purple'},
            'layline': {'icon': 'arrows', 'color': 'green'},
            'wind_shift': {'icon': 'random', 'color': 'orange'},
            'start': {'icon': 'play', 'color': 'green'},
            'finish': {'icon': 'stop', 'color': 'red'},
            'mark': {'icon': 'flag', 'color': 'cadetblue'},
            'other': {'icon': 'info', 'color': 'gray'}
        }
        
        # アイコン設定の取得
        icon_config = icon_mapping.get(point_type, icon_mapping['other'])
        
        # 詳細情報の生成
        details = point_data.get('details', {})
        detail_html = '<dl>'
        for key, value in details.items():
            detail_html += f'<dt>{key}</dt><dd>{value}</dd>'
        detail_html += '</dl>'
        
        # タイムスタンプ情報
        timestamp = point_data.get('timestamp', None)
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A'
        
        # ポップアップの内容
        popup_html = f"""
        <div style="min-width: 200px;">
            <h4>{point_type.title()} ポイント</h4>
            <p>時刻: {timestamp_str}</p>
            <p>重要度: {importance:.2f}</p>
            {detail_html}
        </div>
        """
        
        # マーカーを追加
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{name}: {point_type}",
            icon=folium.Icon(
                color=icon_config['color'],
                icon=icon_config['icon'],
                prefix='fa'
            )
        ).add_to(map_obj)
        
        return map_obj
    
    def update_from_containers(self, map_obj: Optional[folium.Map] = None) -> folium.Map:
        """
        登録されているデータコンテナからマップを更新
        
        Parameters
        ----------
        map_obj : Optional[folium.Map], optional
            更新するマップオブジェクト。Noneの場合は新規作成
            
        Returns
        -------
        folium.Map
            更新されたマップオブジェクト
        """
        # マップがない場合は新規作成
        if map_obj is None:
            map_settings = self.ui_state.get_state('map_settings', {})
            map_obj = self.create_map(
                center=map_settings.get('center', [35.45, 139.65]),
                zoom_start=map_settings.get('zoom', 13),
                tile=map_settings.get('tile', 'OpenStreetMap')
            )
        
        # 表示設定の取得
        display_options = self.ui_state.get_state('display_options', {})
        selected_datasets = self.ui_state.get_selected_datasets()
        
        # すべてのコンテナを取得
        containers = self.data_binding.get_all_containers()
        
        # GPSトラックの追加
        if display_options.get('show_tracks', True):
            for container_id, container in containers.items():
                if isinstance(container, GPSDataContainer) and (not selected_datasets or container_id in selected_datasets):
                    # コンテナのメタデータからボート名を取得
                    boat_name = container.get_metadata('boat_name', container_id)
                    
                    # トラックの追加
                    map_obj = self.add_gps_track(
                        map_obj,
                        container,
                        name=boat_name,
                        show_markers=display_options.get('show_markers', True),
                        color_by=display_options.get('color_by', None),
                        max_points=display_options.get('max_points', 1000)  # UI設定から最大ポイント数を取得
                    )
        
        # 風データの追加
        if display_options.get('show_wind', True):
            for container_id, container in containers.items():
                if isinstance(container, WindDataContainer) and (not selected_datasets or container_id in selected_datasets):
                    # 風矢印の追加
                    map_obj = self.add_wind_arrows(
                        map_obj,
                        container,
                        name=f"風: {container_id}",
                        color='blue',
                        scale=5.0
                    )
        
        # 戦略ポイントの追加
        if display_options.get('show_strategy_points', True):
            for container_id, container in containers.items():
                if isinstance(container, StrategyPointContainer) and (not selected_datasets or container_id in selected_datasets):
                    # 戦略ポイントの追加
                    map_obj = self.add_strategy_points(
                        map_obj,
                        container,
                        name=f"戦略: {container_id}"
                    )
        
        return map_obj
    
    def render(self, key: Optional[str] = None, width: int = 800, height: int = 600) -> None:
        """
        マップをStreamlitに表示
        
        Parameters
        ----------
        key : Optional[str], optional
            Streamlitコンポーネントのキー
        width : int, optional
            表示幅
        height : int, optional
            表示高さ
        """
        # マップの自動更新
        map_obj = self.update_from_containers()
        
        # ダウンサンプリング情報の表示
        if '_downsampling_applied' in st.session_state:
            original = st.session_state.get('_original_points', 0)
            sampled = st.session_state.get('_sampled_points', 0)
            reduction = ((original - sampled) / original * 100) if original > 0 else 0
            st.info(f"パフォーマンス最適化: データポイントが多いため、表示を最適化しています。(元: {original:,}点 → 表示: {sampled:,}点、{reduction:.1f}%削減)")
        
        # Streamlitにマップを表示
        folium_static(map_obj, width=width, height=height, key=key)
    
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
        if series.name == 'course' or series.name == 'direction':
            diffs = diffs.apply(lambda x: min(x, 360 - x) if not pd.isna(x) else x)
        
        # 閾値以上の変化を検出
        for i in range(1, len(diffs)):
            if diffs.iloc[i] >= threshold:
                changes.append(i)
        
        return changes
