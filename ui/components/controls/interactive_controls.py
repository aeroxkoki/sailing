"""
ui.components.controls.interactive_controls

インタラクティブコントロールパネル - データの表示設定やフィルタリングを行うためのコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
from sailing_data_processor.data_model.container import GPSDataContainer, WindDataContainer
from ui.data_binding import DataBindingManager, UIStateManager

class TimeSliderComponent:
    """
    時間スライダーコンポーネント
    
    データの時間範囲を制御するためのスライダーコンポーネント
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
        
        # 再生状態の管理
        self._playing = False
        self._play_speed = 1.0
        self._current_time = None
    
    def render(self, key_prefix: str = '') -> None:
        """
        タイムスライダーを表示
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        # 選択中のデータセットから時間範囲を取得
        time_range = self._get_time_range()
        
        if time_range is None:
            st.info("利用可能な時間データがありません")
            return
        
        start_time, end_time = time_range
        
        # 現在の時間状態を取得
        current_time = self.ui_state.get_current_time()
        if current_time is None or current_time < start_time or current_time > end_time:
            current_time = start_time
        
        # 時間範囲を人間が読みやすい形式に変換
        start_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
        end_str = end_time.strftime('%Y-%m-%d %H:%M:%S')
        duration_sec = (end_time - start_time).total_seconds()
        
        # 時間範囲を表示
        st.write(f"時間範囲: {start_str} 〜 {end_str} (期間: {self._format_duration(duration_sec)})")
        
        # スライダーのステップを計算（データポイント数や総時間に応じて調整）
        steps = min(100, max(10, int(duration_sec / 10)))  # 10秒ごと〜データ点100個分
        step_sec = duration_sec / steps
        
        # スライダー用の値域を生成
        slider_range = range(steps + 1)
        
        # 現在位置をスライダー値に変換
        current_pos = int((current_time - start_time).total_seconds() / step_sec)
        current_pos = max(0, min(current_pos, steps))
        
        # スライダーを表示
        slider_pos = st.slider(
            "時間",
            min_value=0,
            max_value=steps,
            value=current_pos,
            key=f"{key_prefix}time_slider"
        )
        
        # スライダー位置から時間を計算
        selected_time = start_time + timedelta(seconds=slider_pos * step_sec)
        
        # 再生コントロールを表示
        cols = st.columns([1, 1, 1, 2])
        
        # 再生/一時停止ボタン
        playing = self.ui_state.get_state('time_window', {}).get('playing', False)
        play_label = "⏸️ 一時停止" if playing else "▶️ 再生"
        
        if cols[0].button(play_label, key=f"{key_prefix}play_button"):
            playing = not playing
            self.ui_state.update_time_window(playing=playing)
            
            if playing:
                # 再生モードの場合、時間の自動更新を開始
                st.experimental_rerun()
        
        # 速度調整
        play_speed = self.ui_state.get_state('time_window', {}).get('speed', 1.0)
        new_speed = cols[1].selectbox(
            "速度",
            options=[0.25, 0.5, 1.0, 2.0, 5.0],
            index=2,  # 1.0が初期値
            format_func=lambda x: f"{x}x",
            key=f"{key_prefix}speed_select"
        )
        
        if new_speed != play_speed:
            self.ui_state.update_time_window(speed=new_speed)
        
        # リセットボタン
        if cols[2].button("⏮️ リセット", key=f"{key_prefix}reset_button"):
            self.ui_state.set_current_time(start_time)
            self.ui_state.update_time_window(playing=False)
            st.experimental_rerun()
        
        # 現在時刻の表示
        cols[3].write(f"現在: {selected_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 時間の更新
        if selected_time != current_time or (playing and self._playing != playing):
            self.ui_state.set_current_time(selected_time)
            self._current_time = selected_time
            
            # 再生モードの処理
            if playing:
                self._handle_playback(start_time, end_time, step_sec, selected_time, new_speed)
    
    def _handle_playback(self, start_time: datetime, end_time: datetime, 
                        step_sec: float, current_time: datetime, speed: float) -> None:
        """
        再生モードの処理
        
        Parameters
        ----------
        start_time : datetime
            開始時間
        end_time : datetime
            終了時間
        step_sec : float
            ステップ秒数
        current_time : datetime
            現在時間
        speed : float
            再生速度
        """
        # 前回の再生状態を記録
        self._playing = True
        self._play_speed = speed
        
        # 次の時間を計算
        next_time = current_time + timedelta(seconds=step_sec * speed)
        
        # 終了時間を超える場合はリセット
        if next_time > end_time:
            next_time = start_time
        
        # 次の時間を設定
        self.ui_state.set_current_time(next_time)
        
        # 少し待機してから自動更新
        time_to_wait_ms = int(1000 / speed)  # 速度によって待機時間を調整
        st.experimental_set_query_params(dummy=time_to_wait_ms)
        st.experimental_rerun()
    
    def _get_time_range(self) -> Optional[Tuple[datetime, datetime]]:
        """
        利用可能なデータセットから時間範囲を取得
        
        Returns
        -------
        Optional[Tuple[datetime, datetime]]
            開始時間と終了時間のタプル。データがない場合はNone
        """
        # 選択中のデータセット
        selected_datasets = self.ui_state.get_selected_datasets()
        
        # すべてのデータコンテナを取得
        containers = self.data_binding.get_all_containers()
        
        # 時間範囲を計算
        min_time = None
        max_time = None
        
        for container_id, container in containers.items():
            # 選択されていないデータセットはスキップ
            if selected_datasets and container_id not in selected_datasets:
                continue
            
            # GPSデータコンテナのみ処理
            if not isinstance(container, GPSDataContainer):
                continue
            
            df = container.data
            
            # タイムスタンプ列があるか確認
            if 'timestamp' not in df.columns:
                continue
            
            # このデータセットの時間範囲
            dataset_min = df['timestamp'].min()
            dataset_max = df['timestamp'].max()
            
            # 全体の時間範囲を更新
            if min_time is None or dataset_min < min_time:
                min_time = dataset_min
            
            if max_time is None or dataset_max > max_time:
                max_time = dataset_max
        
        # 時間範囲が取得できなければNoneを返す
        if min_time is None or max_time is None:
            return None
        
        return (min_time, max_time)
    
    def _format_duration(self, seconds: float) -> str:
        """
        秒数を読みやすい形式にフォーマット
        
        Parameters
        ----------
        seconds : float
            秒数
            
        Returns
        -------
        str
            フォーマットされた文字列
        """
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}時間"

class LayerControlComponent:
    """
    レイヤー制御コンポーネント
    
    マップ上の表示レイヤーを制御するためのコンポーネント
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
    
    def render(self, key_prefix: str = '') -> None:
        """
        レイヤー制御パネルを表示
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        st.subheader("レイヤー表示設定")
        
        # 利用可能なデータセットの一覧を取得
        containers = self.data_binding.get_all_containers()
        
        # データセットを種類ごとに分類
        gps_containers = {}
        wind_containers = {}
        strategy_containers = {}
        
        for container_id, container in containers.items():
            if isinstance(container, GPSDataContainer):
                gps_containers[container_id] = container
            elif isinstance(container, WindDataContainer):
                wind_containers[container_id] = container
            else:
                # その他のコンテナは戦略ポイントなどとして扱う
                strategy_containers[container_id] = container
        
        # 現在の選択状態を取得
        selected_datasets = set(self.ui_state.get_selected_datasets())
        
        # GPSトラックの選択
        if gps_containers:
            st.write("### GPSトラック")
            
            # 全選択/解除ボタン
            cols = st.columns(2)
            if cols[0].button("すべて選択", key=f"{key_prefix}select_all_gps"):
                selected_datasets.update(gps_containers.keys())
                self.ui_state.select_datasets(list(selected_datasets))
                st.experimental_rerun()
                
            if cols[1].button("すべて解除", key=f"{key_prefix}deselect_all_gps"):
                selected_datasets = selected_datasets - set(gps_containers.keys())
                self.ui_state.select_datasets(list(selected_datasets))
                st.experimental_rerun()
            
            # 各GPSトラックの選択チェックボックス
            for container_id, container in gps_containers.items():
                # メタデータからボート名を取得
                boat_name = container.get_metadata('boat_name', container_id)
                
                # チェックボックスで選択状態を制御
                is_selected = container_id in selected_datasets
                if st.checkbox(
                    boat_name, 
                    value=is_selected, 
                    key=f"{key_prefix}gps_{container_id}"
                ):
                    selected_datasets.add(container_id)
                else:
                    if container_id in selected_datasets:
                        selected_datasets.remove(container_id)
        
        # 風データの選択
        if wind_containers:
            st.write("### 風データ")
            
            # 全選択/解除ボタン
            cols = st.columns(2)
            if cols[0].button("すべて選択", key=f"{key_prefix}select_all_wind"):
                selected_datasets.update(wind_containers.keys())
                self.ui_state.select_datasets(list(selected_datasets))
                st.experimental_rerun()
                
            if cols[1].button("すべて解除", key=f"{key_prefix}deselect_all_wind"):
                selected_datasets = selected_datasets - set(wind_containers.keys())
                self.ui_state.select_datasets(list(selected_datasets))
                st.experimental_rerun()
            
            # 各風データの選択チェックボックス
            for container_id, container in wind_containers.items():
                # メタデータから名前を取得
                wind_name = container.get_metadata('wind_name', f"風データ {container_id}")
                
                # チェックボックスで選択状態を制御
                is_selected = container_id in selected_datasets
                if st.checkbox(
                    wind_name, 
                    value=is_selected, 
                    key=f"{key_prefix}wind_{container_id}"
                ):
                    selected_datasets.add(container_id)
                else:
                    if container_id in selected_datasets:
                        selected_datasets.remove(container_id)
        
        # 戦略ポイントの選択
        if strategy_containers:
            st.write("### 戦略ポイント")
            
            # 全選択/解除ボタン
            cols = st.columns(2)
            if cols[0].button("すべて選択", key=f"{key_prefix}select_all_strategy"):
                selected_datasets.update(strategy_containers.keys())
                self.ui_state.select_datasets(list(selected_datasets))
                st.experimental_rerun()
                
            if cols[1].button("すべて解除", key=f"{key_prefix}deselect_all_strategy"):
                selected_datasets = selected_datasets - set(strategy_containers.keys())
                self.ui_state.select_datasets(list(selected_datasets))
                st.experimental_rerun()
            
            # 各戦略ポイントの選択チェックボックス
            for container_id, container in strategy_containers.items():
                # メタデータから名前を取得
                strategy_name = container.get_metadata('strategy_name', f"戦略データ {container_id}")
                
                # チェックボックスで選択状態を制御
                is_selected = container_id in selected_datasets
                if st.checkbox(
                    strategy_name, 
                    value=is_selected, 
                    key=f"{key_prefix}strategy_{container_id}"
                ):
                    selected_datasets.add(container_id)
                else:
                    if container_id in selected_datasets:
                        selected_datasets.remove(container_id)
        
        # 表示オプションの設定
        st.write("### 表示オプション")
        
        # 現在の表示オプションを取得
        display_options = self.ui_state.get_state('display_options', {})
        
        # トラック表示オプション
        show_tracks = st.checkbox(
            "GPSトラックを表示", 
            value=display_options.get('show_tracks', True),
            key=f"{key_prefix}show_tracks"
        )
        if show_tracks:
            cols = st.columns(2)
            
            # マーカー表示オプション
            show_markers = cols[0].checkbox(
                "マーカーを表示", 
                value=display_options.get('show_markers', True),
                key=f"{key_prefix}show_markers"
            )
            
            # カラーマッピングオプション
            color_by_options = ["なし", "速度", "風向", "時間"]
            color_by_index = 0
            current_color_by = display_options.get('color_by', None)
            
            if current_color_by == 'speed':
                color_by_index = 1
            elif current_color_by == 'wind_direction':
                color_by_index = 2
            elif current_color_by == 'timestamp':
                color_by_index = 3
            
            color_by = cols[1].selectbox(
                "色付け", 
                options=color_by_options,
                index=color_by_index,
                key=f"{key_prefix}color_by"
            )
            
            # 値を変換
            if color_by == "速度":
                color_by = 'speed'
            elif color_by == "風向":
                color_by = 'wind_direction'
            elif color_by == "時間":
                color_by = 'timestamp'
            else:
                color_by = None
        else:
            show_markers = False
            color_by = None
        
        # 風データ表示オプション
        show_wind = st.checkbox(
            "風データを表示", 
            value=display_options.get('show_wind', True),
            key=f"{key_prefix}show_wind"
        )
        
        # 戦略ポイント表示オプション
        show_strategy_points = st.checkbox(
            "戦略ポイントを表示", 
            value=display_options.get('show_strategy_points', True),
            key=f"{key_prefix}show_strategy_points"
        )
        
        # マップタイルの選択
        st.write("### マップ設定")
        map_settings = self.ui_state.get_state('map_settings', {})
        
        # マップタイル選択
        tile_options = {
            'OpenStreetMap': 'OpenStreetMap',
            'CartoDB positron': 'ポジトロン（海図風）',
            'CartoDB dark_matter': 'ダークマター',
            'Stamen Terrain': '地形図',
            'Stamen Watercolor': '水彩画風'
        }
        
        current_tile = map_settings.get('tile', 'OpenStreetMap')
        tile_index = list(tile_options.keys()).index(current_tile) if current_tile in tile_options else 0
        
        selected_tile = st.selectbox(
            "マップスタイル",
            options=list(tile_options.keys()),
            index=tile_index,
            format_func=lambda x: tile_options[x],
            key=f"{key_prefix}map_tile"
        )
        
        # 変更を適用するボタン
        if st.button("設定を適用", type="primary", key=f"{key_prefix}apply_settings"):
            # 選択されたデータセットを保存
            self.ui_state.select_datasets(list(selected_datasets))
            
            # 表示オプションを更新
            self.ui_state.update_display_options(
                show_tracks=show_tracks,
                show_markers=show_markers,
                show_wind=show_wind,
                show_strategy_points=show_strategy_points,
                color_by=color_by
            )
            
            # マップ設定を更新
            self.ui_state.update_map_settings(
                tile=selected_tile
            )
            
            # 更新を反映
            st.success("設定を適用しました")
            st.experimental_rerun()

class FilterComponent:
    """
    フィルタリングコンポーネント
    
    データのフィルタリングを制御するためのコンポーネント
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
    
    def render(self, key_prefix: str = '') -> None:
        """
        フィルタリング設定を表示
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        st.subheader("データフィルタ")
        
        # 現在のフィルタ設定を取得
        filters = self.ui_state.get_state('filters', {})
        
        # 速度フィルタ
        st.write("### 速度フィルタ")
        
        # 速度の範囲を取得
        speed_range = self._get_speed_range()
        
        if speed_range:
            min_speed, max_speed = speed_range
            
            # 現在のフィルタ値
            current_min = filters.get('speed_min', min_speed)
            current_max = filters.get('speed_max', max_speed)
            
            # スライダーの表示
            speed_min, speed_max = st.slider(
                "速度範囲 (ノット)",
                min_value=min_speed,
                max_value=max_speed,
                value=(current_min, current_max),
                step=0.5,
                key=f"{key_prefix}speed_range"
            )
        else:
            st.info("速度データがありません")
            speed_min, speed_max = 0, 100
        
        # 風向フィルタ
        st.write("### 風向フィルタ")
        
        # 風向の有無を確認
        has_wind_direction = self._has_wind_direction()
        
        if has_wind_direction:
            # 風向範囲の設定
            direction_min = filters.get('direction_min', 0)
            direction_max = filters.get('direction_max', 360)
            
            direction_min, direction_max = st.slider(
                "風向範囲 (度)",
                min_value=0,
                max_value=360,
                value=(direction_min, direction_max),
                step=5,
                key=f"{key_prefix}direction_range"
            )
            
            # 風速範囲の設定
            wind_speed_min = filters.get('wind_speed_min', 0)
            wind_speed_max = filters.get('wind_speed_max', 50)
            
            wind_speed_min, wind_speed_max = st.slider(
                "風速範囲 (ノット)",
                min_value=0,
                max_value=50,
                value=(wind_speed_min, wind_speed_max),
                step=1,
                key=f"{key_prefix}wind_speed_range"
            )
        else:
            st.info("風向データがありません")
            direction_min, direction_max = 0, 360
            wind_speed_min, wind_speed_max = 0, 50
        
        # フィルタを適用するボタン
        if st.button("フィルタを適用", type="primary", key=f"{key_prefix}apply_filter"):
            # フィルタ設定を更新
            self.ui_state.update_filters(
                speed_min=speed_min,
                speed_max=speed_max,
                direction_min=direction_min,
                direction_max=direction_max,
                wind_speed_min=wind_speed_min,
                wind_speed_max=wind_speed_max
            )
            
            # フィルタを適用
            self._apply_filters()
            
            # 更新を反映
            st.success("フィルタを適用しました")
            st.experimental_rerun()
    
    def _get_speed_range(self) -> Optional[Tuple[float, float]]:
        """
        利用可能なデータセットから速度範囲を取得
        
        Returns
        -------
        Optional[Tuple[float, float]]
            最小速度と最大速度のタプル。データがない場合はNone
        """
        # すべてのデータコンテナを取得
        containers = self.data_binding.get_all_containers()
        
        # 速度範囲を計算
        min_speed = None
        max_speed = None
        
        for container_id, container in containers.items():
            # GPSデータコンテナのみ処理
            if not isinstance(container, GPSDataContainer):
                continue
            
            df = container.data
            
            # 速度列があるか確認
            if 'speed' not in df.columns:
                continue
            
            # 速度をノットに変換（必要な場合）
            speed_col = 'speed'
            if df[speed_col].mean() < 10:  # おそらくm/s表記
                speeds = df[speed_col] * 1.94384  # m/s からノットに変換
            else:
                speeds = df[speed_col]
            
            # このデータセットの速度範囲
            dataset_min = speeds.min()
            dataset_max = speeds.max()
            
            # 全体の速度範囲を更新
            if min_speed is None or dataset_min < min_speed:
                min_speed = dataset_min
            
            if max_speed is None or dataset_max > max_speed:
                max_speed = dataset_max
        
        # 速度範囲が取得できなければNoneを返す
        if min_speed is None or max_speed is None:
            return None
        
        # 範囲を少し広げて余裕を持たせる
        min_speed = max(0, min_speed - 1)
        max_speed = max_speed + 1
        
        return (min_speed, max_speed)
    
    def _has_wind_direction(self) -> bool:
        """
        風向データがあるかを確認
        
        Returns
        -------
        bool
            風向データがある場合はTrue
        """
        # すべてのデータコンテナを取得
        containers = self.data_binding.get_all_containers()
        
        for container_id, container in containers.items():
            # GPSデータコンテナのみ処理
            if isinstance(container, GPSDataContainer):
                df = container.data
                
                # 風向列があるか確認
                if 'wind_direction' in df.columns:
                    return True
            
            # 風データコンテナの場合
            elif isinstance(container, WindDataContainer):
                return True
        
        return False
    
    def _apply_filters(self) -> None:
        """フィルタを適用してフィルタ済みデータセットを作成"""
        # 現在のフィルタ設定を取得
        filters = self.ui_state.get_state('filters', {})
        
        # すべてのデータコンテナを取得
        containers = self.data_binding.get_all_containers()
        
        for container_id, container in containers.items():
            # GPSデータコンテナのみ処理
            if not isinstance(container, GPSDataContainer):
                continue
            
            # フィルタ関数を定義
            def apply_filter(container: GPSDataContainer) -> GPSDataContainer:
                df = container.data.copy()
                
                # 速度フィルタ
                if 'speed' in df.columns:
                    speed_min = filters.get('speed_min', 0)
                    speed_max = filters.get('speed_max', 100)
                    
                    # 速度の変換（必要な場合）
                    speed_col = 'speed'
                    if df[speed_col].mean() < 10:  # おそらくm/s表記
                        speed_min_ms = speed_min / 1.94384  # ノットからm/sに変換
                        speed_max_ms = speed_max / 1.94384
                        
                        df = df[(df[speed_col] >= speed_min_ms) & (df[speed_col] <= speed_max_ms)]
                    else:
                        df = df[(df[speed_col] >= speed_min) & (df[speed_col] <= speed_max)]
                
                # 風向フィルタ
                if 'wind_direction' in df.columns:
                    direction_min = filters.get('direction_min', 0)
                    direction_max = filters.get('direction_max', 360)
                    
                    # 範囲が一周を超える場合の特殊処理
                    if direction_min <= direction_max:
                        df = df[(df['wind_direction'] >= direction_min) & (df['wind_direction'] <= direction_max)]
                    else:
                        # 例: 330度〜30度の場合 → 330度以上または30度以下
                        df = df[(df['wind_direction'] >= direction_min) | (df['wind_direction'] <= direction_max)]
                
                # 新しいコンテナを作成
                metadata = container.metadata.copy()
                metadata['filtered'] = True
                metadata['filter_settings'] = filters
                
                return GPSDataContainer(df, metadata)
            
            # フィルタを適用してフィルタ済みデータセットを作成
            filtered_id = f"{container_id}_filtered"
            self.data_binding.create_filtered_view(container_id, apply_filter, filtered_id)

class DetailViewComponent:
    """
    詳細情報表示コンポーネント
    
    選択されたポイントの詳細情報を表示するコンポーネント
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
    
    def render(self, key_prefix: str = '') -> None:
        """
        詳細情報表示を表示
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        st.subheader("詳細情報")
        
        # 選択されたポイント情報を取得
        selected_point = self.ui_state.get_state('selected_point')
        
        if selected_point:
            # ポイント情報を表示
            st.json(selected_point)
        else:
            st.info("ポイントを選択すると詳細情報が表示されます")

class InteractiveControlPanel:
    """
    インタラクティブコントロールパネル
    
    複数のコントロールコンポーネントを統合したパネル
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
        
        # 各コンポーネントを初期化
        self.time_slider = TimeSliderComponent(data_binding, ui_state)
        self.layer_control = LayerControlComponent(data_binding, ui_state)
        self.filter = FilterComponent(data_binding, ui_state)
        self.detail_view = DetailViewComponent(data_binding, ui_state)
    
    def render(self, key_prefix: str = '') -> None:
        """
        コントロールパネルを表示
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントのキープレフィックス
        """
        # タブでコンポーネントを分ける
        tabs = st.tabs(["時間制御", "レイヤー", "フィルタ", "詳細"])
        
        # 時間スライダータブ
        with tabs[0]:
            self.time_slider.render(key_prefix=f"{key_prefix}time_")
        
        # レイヤー制御タブ
        with tabs[1]:
            self.layer_control.render(key_prefix=f"{key_prefix}layer_")
        
        # フィルタタブ
        with tabs[2]:
            self.filter.render(key_prefix=f"{key_prefix}filter_")
        
        # 詳細表示タブ
        with tabs[3]:
            self.detail_view.render(key_prefix=f"{key_prefix}detail_")
