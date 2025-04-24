# -*- coding: utf-8 -*-
"""
visualization.interactive_controls

インタラクティブな制御要素を提供するモジュールです。
時間軸プレイバック、フィルタリング、ズーム/パンなどのユーザー操作を実現します。
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime, timedelta
import time

class PlaybackController:
    """
    時間軸のプレイバック制御を行うコンポーネント
    
    時系列データの再生、一時停止、時間移動などの制御を行います。
    """
    
    def __init__(self, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        name : str, optional
            コンポーネントの表示名
        """
        self.name = name or "プレイバック制御"
        
        # 時間範囲
        self._start_time = 0
        self._end_time = 100
        self._current_time = 0
        
        # 再生制御
        self._playing = False
        self._play_speed = 1.0
        self._loop = False
        
        # キーフレーム
        self._keyframes = []
        
        # コールバック
        self._on_time_change_callback = None
        self._on_play_state_change_callback = None
    
    def set_time_range(self, start_time: Union[float, datetime], end_time: Union[float, datetime]) -> None:
        """
        時間範囲を設定
        
        Parameters
        ----------
        start_time : Union[float, datetime]
            開始時間
        end_time : Union[float, datetime]
            終了時間
        """
        # datetime型の場合はタイムスタンプに変換
        if isinstance(start_time, datetime) and isinstance(end_time, datetime):
            self._start_time = 0
            self._end_time = (end_time - start_time).total_seconds()
            self._time_base = start_time  # 基準時刻を保存
        else:
            self._start_time = float(start_time)
            self._end_time = float(end_time)
            self._time_base = None
        
        # 現在時刻を範囲内に調整
        self._current_time = max(self._start_time, min(self._current_time, self._end_time))
    
    def set_current_time(self, time_value: Union[float, datetime]) -> None:
        """
        現在時刻を設定
        
        Parameters
        ----------
        time_value : Union[float, datetime]
            設定する時刻
        """
        # datetime型の場合はタイムスタンプに変換
        if isinstance(time_value, datetime) and hasattr(self, '_time_base') and self._time_base is not None:
            time_seconds = (time_value - self._time_base).total_seconds()
        else:
            time_seconds = float(time_value)
        
        # 範囲内に調整
        self._current_time = max(self._start_time, min(time_seconds, self._end_time))
        
        # コールバックがある場合は呼び出し
        if self._on_time_change_callback:
            self._on_time_change_callback(self._current_time)
    
    def get_current_time(self) -> float:
        """
        現在時刻を取得
        
        Returns
        -------
        float
            現在時刻（秒）
        """
        return self._current_time
    
    def get_current_datetime(self) -> Optional[datetime]:
        """
        現在時刻をdatetime型で取得
        
        Returns
        -------
        Optional[datetime]
            現在時刻（datetime型）、基準時刻が設定されていない場合はNone
        """
        if hasattr(self, '_time_base') and self._time_base is not None:
            return self._time_base + timedelta(seconds=self._current_time)
        return None
    
    def play(self) -> None:
        """再生を開始"""
        self._playing = True
        if self._on_play_state_change_callback:
            self._on_play_state_change_callback(self._playing)
    
    def pause(self) -> None:
        """再生を一時停止"""
        self._playing = False
        if self._on_play_state_change_callback:
            self._on_play_state_change_callback(self._playing)
    
    def stop(self) -> None:
        """再生を停止して先頭に戻る"""
        self._playing = False
        self._current_time = self._start_time
        if self._on_play_state_change_callback:
            self._on_play_state_change_callback(self._playing)
        if self._on_time_change_callback:
            self._on_time_change_callback(self._current_time)
    
    def is_playing(self) -> bool:
        """
        再生中かどうかを取得
        
        Returns
        -------
        bool
            再生中の場合True
        """
        return self._playing
    
    def set_play_speed(self, speed: float) -> None:
        """
        再生速度を設定
        
        Parameters
        ----------
        speed : float
            再生速度（1.0が等速）
        """
        self._play_speed = max(0.1, min(10.0, speed))
    
    def get_play_speed(self) -> float:
        """
        再生速度を取得
        
        Returns
        -------
        float
            再生速度
        """
        return self._play_speed
    
    def set_loop(self, loop: bool) -> None:
        """
        ループ再生の設定
        
        Parameters
        ----------
        loop : bool
            ループ再生する場合True
        """
        self._loop = loop
    
    def is_loop(self) -> bool:
        """
        ループ再生の設定を取得
        
        Returns
        -------
        bool
            ループ再生する場合True
        """
        return self._loop
    
    def add_keyframe(self, time_value: Union[float, datetime], label: str, details: Optional[Dict] = None) -> None:
        """
        キーフレームを追加
        
        Parameters
        ----------
        time_value : Union[float, datetime]
            キーフレームの時刻
        label : str
            キーフレームのラベル
        details : Optional[Dict], optional
            キーフレームの詳細情報
        """
        # datetime型の場合はタイムスタンプに変換
        if isinstance(time_value, datetime) and hasattr(self, '_time_base') and self._time_base is not None:
            time_seconds = (time_value - self._time_base).total_seconds()
        else:
            time_seconds = float(time_value)
        
        # キーフレーム情報
        keyframe = {
            "time": time_seconds,
            "label": label,
            "details": details or {}
        }
        
        # キーフレームを追加（時間順にソート）
        self._keyframes.append(keyframe)
        self._keyframes.sort(key=lambda kf: kf["time"])
    
    def remove_keyframe(self, index: int) -> bool:
        """
        キーフレームを削除
        
        Parameters
        ----------
        index : int
            削除するキーフレームのインデックス
            
        Returns
        -------
        bool
            削除に成功した場合True
        """
        if 0 <= index < len(self._keyframes):
            self._keyframes.pop(index)
            return True
        return False
    
    def get_keyframes(self) -> List[Dict]:
        """
        すべてのキーフレームを取得
        
        Returns
        -------
        List[Dict]
            キーフレームのリスト
        """
        return self._keyframes
    
    def get_nearest_keyframe(self, time_value: Optional[Union[float, datetime]] = None) -> Optional[Dict]:
        """
        指定時刻に最も近いキーフレームを取得
        
        Parameters
        ----------
        time_value : Optional[Union[float, datetime]], optional
            基準時刻、指定しない場合は現在時刻
            
        Returns
        -------
        Optional[Dict]
            最も近いキーフレーム、見つからない場合はNone
        """
        if not self._keyframes:
            return None
        
        # 基準時刻の決定
        if time_value is None:
            time_seconds = self._current_time
        elif isinstance(time_value, datetime) and hasattr(self, '_time_base') and self._time_base is not None:
            time_seconds = (time_value - self._time_base).total_seconds()
        else:
            time_seconds = float(time_value)
        
        # 最も近いキーフレームを検索
        nearest_keyframe = min(self._keyframes, key=lambda kf: abs(kf["time"] - time_seconds))
        return nearest_keyframe
    
    def jump_to_keyframe(self, index: int) -> bool:
        """
        指定インデックスのキーフレームに移動
        
        Parameters
        ----------
        index : int
            移動先キーフレームのインデックス
            
        Returns
        -------
        bool
            移動に成功した場合True
        """
        if 0 <= index < len(self._keyframes):
            self.set_current_time(self._keyframes[index]["time"])
            return True
        return False
    
    def jump_to_next_keyframe(self) -> bool:
        """
        次のキーフレームに移動
        
        Returns
        -------
        bool
            移動に成功した場合True
        """
        if not self._keyframes:
            return False
        
        # 現在時刻よりも後のキーフレームを検索
        next_keyframes = [kf for kf in self._keyframes if kf["time"] > self._current_time]
        
        if next_keyframes:
            # 最も近い次のキーフレーム
            next_keyframe = min(next_keyframes, key=lambda kf: kf["time"])
            self.set_current_time(next_keyframe["time"])
            return True
        elif self._loop:
            # ループ再生時は最初のキーフレームに戻る
            self.set_current_time(self._keyframes[0]["time"])
            return True
        
        return False
    
    def jump_to_prev_keyframe(self) -> bool:
        """
        前のキーフレームに移動
        
        Returns
        -------
        bool
            移動に成功した場合True
        """
        if not self._keyframes:
            return False
        
        # 現在時刻よりも前のキーフレームを検索
        prev_keyframes = [kf for kf in self._keyframes if kf["time"] < self._current_time]
        
        if prev_keyframes:
            # 最も近い前のキーフレーム
            prev_keyframe = max(prev_keyframes, key=lambda kf: kf["time"])
            self.set_current_time(prev_keyframe["time"])
            return True
        elif self._loop:
            # ループ再生時は最後のキーフレームに移動
            self.set_current_time(self._keyframes[-1]["time"])
            return True
        
        return False
    
    def set_on_time_change(self, callback: Callable[[float], None]) -> None:
        """
        時間変更コールバックを設定
        
        Parameters
        ----------
        callback : Callable[[float], None]
            時間変更時に呼び出すコールバック
        """
        self._on_time_change_callback = callback
    
    def set_on_play_state_change(self, callback: Callable[[bool], None]) -> None:
        """
        再生状態変更コールバックを設定
        
        Parameters
        ----------
        callback : Callable[[bool], None]
            再生状態変更時に呼び出すコールバック
        """
        self._on_play_state_change_callback = callback
    
    def update(self, delta_time: float) -> None:
        """
        プレイバック状態を更新
        
        Parameters
        ----------
        delta_time : float
            前回の更新からの経過時間（秒）
        """
        if self._playing:
            # 時間を進める
            new_time = self._current_time + delta_time * self._play_speed
            
            # 終端に達したかチェック
            if new_time >= self._end_time:
                if self._loop:
                    # ループの場合は先頭に戻る
                    new_time = self._start_time + (new_time - self._end_time) % (self._end_time - self._start_time)
                else:
                    # ループしない場合は終端で停止
                    new_time = self._end_time
                    self._playing = False
                    if self._on_play_state_change_callback:
                        self._on_play_state_change_callback(self._playing)
            
            # 時間を更新
            if new_time != self._current_time:
                self._current_time = new_time
                if self._on_time_change_callback:
                    self._on_time_change_callback(self._current_time)
    
    def render_controls(self, key_prefix: str = "") -> Dict:
        """
        プレイバック制御UI要素をStreamlitで表示
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitウィジェットのキープレフィックス
            
        Returns
        -------
        Dict
            UI操作の結果発生した変更情報
        """
        changes = {}
        
        # レイアウト列
        col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
        
        # 再生/一時停止ボタン
        with col1:
            if self._playing:
                if st.button("⏸️ 一時停止", key=f"{key_prefix}_pause"):
                    self._playing = False
                    changes["playing"] = self._playing
                    if self._on_play_state_change_callback:
                        self._on_play_state_change_callback(self._playing)
            else:
                if st.button("▶️ 再生", key=f"{key_prefix}_play"):
                    self._playing = True
                    changes["playing"] = self._playing
                    if self._on_play_state_change_callback:
                        self._on_play_state_change_callback(self._playing)
        
        # 時間スライダー
        with col2:
            new_time = st.slider(
                "時間", 
                min_value=float(self._start_time), 
                max_value=float(self._end_time), 
                value=float(self._current_time),
                key=f"{key_prefix}_time_slider"
            )
            if new_time != self._current_time:
                self._current_time = new_time
                changes["current_time"] = self._current_time
                if self._on_time_change_callback:
                    self._on_time_change_callback(self._current_time)
        
        # 再生速度
        with col3:
            new_speed = st.select_slider(
                "速度", 
                options=[0.25, 0.5, 1.0, 2.0, 4.0, 8.0],
                value=self._play_speed,
                key=f"{key_prefix}_speed_slider"
            )
            if new_speed != self._play_speed:
                self._play_speed = new_speed
                changes["play_speed"] = self._play_speed
        
        # ループ設定
        with col4:
            new_loop = st.checkbox("ループ", value=self._loop, key=f"{key_prefix}_loop")
            if new_loop != self._loop:
                self._loop = new_loop
                changes["loop"] = self._loop
        
        # キーフレームボタン
        if self._keyframes:
            st.write("キーフレーム:")
            
            # キーフレームボタンをレイアウト
            max_buttons_per_row = 5
            keyframe_chunks = [self._keyframes[i:i+max_buttons_per_row] 
                              for i in range(0, len(self._keyframes), max_buttons_per_row)]
            
            for chunk in keyframe_chunks:
                cols = st.columns(len(chunk))
                for i, (col, keyframe) in enumerate(zip(cols, chunk)):
                    idx = self._keyframes.index(keyframe)
                    with col:
                        if st.button(keyframe["label"], key=f"{key_prefix}_keyframe_{idx}"):
                            self._current_time = keyframe["time"]
                            changes["current_time"] = self._current_time
                            changes["keyframe_index"] = idx
                            if self._on_time_change_callback:
                                self._on_time_change_callback(self._current_time)
        
        return changes
    
    def render_compact_controls(self, key_prefix: str = "") -> Dict:
        """
        コンパクトなプレイバック制御UI要素をStreamlitで表示
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitウィジェットのキープレフィックス
            
        Returns
        -------
        Dict
            UI操作の結果発生した変更情報
        """
        changes = {}
        
        # レイアウト列
        cols = st.columns([1, 1, 1, 1, 4, 1])
        
        # 再生/一時停止ボタン
        with cols[0]:
            if self._playing:
                if st.button("⏸️", key=f"{key_prefix}_pause_mini"):
                    self._playing = False
                    changes["playing"] = self._playing
                    if self._on_play_state_change_callback:
                        self._on_play_state_change_callback(self._playing)
            else:
                if st.button("▶️", key=f"{key_prefix}_play_mini"):
                    self._playing = True
                    changes["playing"] = self._playing
                    if self._on_play_state_change_callback:
                        self._on_play_state_change_callback(self._playing)
        
        # 停止ボタン
        with cols[1]:
            if st.button("⏹️", key=f"{key_prefix}_stop_mini"):
                self._playing = False
                self._current_time = self._start_time
                changes["playing"] = self._playing
                changes["current_time"] = self._current_time
                if self._on_play_state_change_callback:
                    self._on_play_state_change_callback(self._playing)
                if self._on_time_change_callback:
                    self._on_time_change_callback(self._current_time)
        
        # 前のキーフレームボタン
        with cols[2]:
            if st.button("⏮️", key=f"{key_prefix}_prev_keyframe_mini"):
                if self.jump_to_prev_keyframe():
                    changes["current_time"] = self._current_time
        
        # 次のキーフレームボタン
        with cols[3]:
            if st.button("⏭️", key=f"{key_prefix}_next_keyframe_mini"):
                if self.jump_to_next_keyframe():
                    changes["current_time"] = self._current_time
        
        # 時間スライダー
        with cols[4]:
            new_time = st.slider(
                "時間", 
                min_value=float(self._start_time), 
                max_value=float(self._end_time), 
                value=float(self._current_time),
                key=f"{key_prefix}_time_slider_mini",
                label_visibility="collapsed"
            )
            if new_time != self._current_time:
                self._current_time = new_time
                changes["current_time"] = self._current_time
                if self._on_time_change_callback:
                    self._on_time_change_callback(self._current_time)
        
        # 速度/ループ設定
        with cols[5]:
            new_speed = st.selectbox(
                "", 
                options=[0.25, 0.5, 1.0, 2.0, 4.0, 8.0],
                index=3,  # デフォルトで1.0を選択
                key=f"{key_prefix}_speed_select_mini",
                label_visibility="collapsed"
            )
            if new_speed != self._play_speed:
                self._play_speed = new_speed
                changes["play_speed"] = self._play_speed
            
            new_loop = st.checkbox("🔁", value=self._loop, key=f"{key_prefix}_loop_mini", label_visibility="collapsed")
            if new_loop != self._loop:
                self._loop = new_loop
                changes["loop"] = self._loop
        
        return changes


class SailingPlaybackController(PlaybackController):
    """
    セーリングデータ特化型のプレイバック制御コンポーネント
    
    通常のプレイバックコントローラーに加えて、タック/ジャイブなどのセーリング特有のキーフレーム生成や
    風向・風速データとの連携機能を提供します。
    """
    
    def __init__(self, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        name : str, optional
            コンポーネントの表示名
        """
        super().__init__(name or "セーリングプレイバック制御")
        
        # セーリング特有のデータ設定
        self._tack_points = []  # タックポイントのインデックスリスト
        self._jibe_points = []  # ジャイブポイントのインデックスリスト
        self._start_point = None  # スタートポイントのインデックス
        self._finish_point = None  # フィニッシュポイントのインデックス
        self._mark_roundings = []  # マークラウンディングのインデックスリスト
        
        # 風向風速データ
        self._wind_data = None  # 風データ
        
    def set_sailing_data(self, data: Dict[str, Any]) -> None:
        """
        セーリングデータを設定し、特殊ポイントを検出
        
        Parameters
        ----------
        data : Dict[str, Any]
            セーリングデータ（GPSトラック、風向風速など）
        """
        # データに含まれるイベントを検出
        if "is_tack" in data:
            self._tack_points = [i for i, is_tack in enumerate(data["is_tack"]) if is_tack]
        elif "tack_points" in data:
            self._tack_points = data["tack_points"]
        
        if "is_jibe" in data or "is_gybe" in data:
            jibe_key = "is_jibe" if "is_jibe" in data else "is_gybe"
            self._jibe_points = [i for i, is_jibe in enumerate(data[jibe_key]) if is_jibe]
        elif "jibe_points" in data:
            self._jibe_points = data["jibe_points"]
        
        # 時間範囲の設定
        if "timestamp" in data and len(data["timestamp"]) > 0:
            timestamps = data["timestamp"]
            if isinstance(timestamps[0], datetime):
                # 日時型の場合
                self.set_time_range(timestamps[0], timestamps[-1])
            else:
                # 秒数の場合
                self.set_time_range(0, float(timestamps[-1]))
        
        # キーフレームを生成
        self._generate_sailing_keyframes(data)
        
        # 風データの保存
        if all(k in data for k in ["wind_speed", "wind_direction"]):
            self._wind_data = {
                "speed": data["wind_speed"],
                "direction": data["wind_direction"]
            }
    
    def _generate_sailing_keyframes(self, data: Dict[str, Any]) -> None:
        """
        セーリングデータからキーフレームを生成
        
        Parameters
        ----------
        data : Dict[str, Any]
            セーリングデータ
        """
        # 既存のキーフレームをクリア
        self._keyframes = []
        
        # 時間軸の取得
        if "timestamp" not in data or len(data["timestamp"]) == 0:
            return
        
        timestamps = data["timestamp"]
        
        # スタートポイントのキーフレーム
        if "start_time" in data:
            # 明示的なスタート時間が指定されている場合
            start_time = data["start_time"]
            self.add_keyframe(
                start_time, 
                "スタート", 
                {"type": "start", "description": "レーススタート"}
            )
        elif len(timestamps) > 0:
            # 最初のポイントをスタートとする
            self.add_keyframe(
                timestamps[0], 
                "開始", 
                {"type": "start", "description": "記録開始"}
            )
        
        # タックポイントのキーフレーム
        for i, tack_idx in enumerate(self._tack_points):
            if 0 <= tack_idx < len(timestamps):
                self.add_keyframe(
                    timestamps[tack_idx], 
                    f"タック {i+1}", 
                    {"type": "tack", "index": tack_idx, "description": "タック（風向を横切る方向転換）"}
                )
        
        # ジャイブポイントのキーフレーム
        for i, jibe_idx in enumerate(self._jibe_points):
            if 0 <= jibe_idx < len(timestamps):
                self.add_keyframe(
                    timestamps[jibe_idx], 
                    f"ジャイブ {i+1}", 
                    {"type": "jibe", "index": jibe_idx, "description": "ジャイブ（風下を通る方向転換）"}
                )
        
        # マークラウンディングのキーフレーム
        if "mark_roundings" in data:
            for i, mark_idx in enumerate(data["mark_roundings"]):
                if 0 <= mark_idx < len(timestamps):
                    self.add_keyframe(
                        timestamps[mark_idx], 
                        f"マーク {i+1}", 
                        {"type": "mark", "index": mark_idx, "description": f"マーク{i+1}のラウンディング"}
                    )
        
        # フィニッシュポイントのキーフレーム
        if "finish_time" in data:
            # 明示的なフィニッシュ時間が指定されている場合
            finish_time = data["finish_time"]
            self.add_keyframe(
                finish_time, 
                "フィニッシュ", 
                {"type": "finish", "description": "レースフィニッシュ"}
            )
        elif len(timestamps) > 0:
            # 最後のポイントをフィニッシュとする
            self.add_keyframe(
                timestamps[-1], 
                "終了", 
                {"type": "finish", "description": "記録終了"}
            )
    
    def get_current_wind(self) -> Tuple[Optional[float], Optional[float]]:
        """
        現在時点の風向風速を取得
        
        Returns
        -------
        Tuple[Optional[float], Optional[float]]
            (風速, 風向)のタプル、データがない場合はNone
        """
        if not self._wind_data or "speed" not in self._wind_data or "direction" not in self._wind_data:
            return None, None
        
        # 現在のインデックスを推定
        if hasattr(self, "_current_point_index") and self._current_point_index is not None:
            idx = self._current_point_index
        else:
            # 時間値から最も近いインデックスを見つける
            idx = 0
        
        # インデックスが範囲内かチェック
        if 0 <= idx < len(self._wind_data["speed"]):
            return self._wind_data["speed"][idx], self._wind_data["direction"][idx]
        
        return None, None
    
    def render_sailing_stats(self) -> None:
        """
        セーリング統計情報を表示
        """
        # 基本的な統計情報の表示
        st.markdown("### セーリング統計")
        
        # タック/ジャイブの回数
        col1, col2 = st.columns(2)
        with col1:
            st.metric("タック回数", len(self._tack_points))
        with col2:
            st.metric("ジャイブ回数", len(self._jibe_points))
        
        # 現在の風情報
        wind_speed, wind_direction = self.get_current_wind()
        if wind_speed is not None and wind_direction is not None:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("風速", f"{wind_speed:.1f} kt")
            with col2:
                st.metric("風向", f"{wind_direction:.0f}°")


class AutomaticPlaybackController:
    """
    時間軸の自動プレイバック制御を行うコンポーネント
    
    PlaybackControllerを拡張し、Streamlitの再描画サイクルでも継続的な再生を可能にします。
    """
    
    def __init__(self, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        name : str, optional
            コンポーネントの表示名
        """
        self.name = name or "プレイバック制御"
        
        # 内部プレイバックコントローラー
        self._playback = PlaybackController(name)
        
        # 最終更新時刻
        self._last_update_time = None
        
        # セッション状態キー
        self._session_key_prefix = f"playback_{id(self)}"
        
        # セッション状態の初期化
        if f"{self._session_key_prefix}_playing" not in st.session_state:
            st.session_state[f"{self._session_key_prefix}_playing"] = False
            
        if f"{self._session_key_prefix}_last_time" not in st.session_state:
            st.session_state[f"{self._session_key_prefix}_last_time"] = time.time()
            
        if f"{self._session_key_prefix}_current_time" not in st.session_state:
            st.session_state[f"{self._session_key_prefix}_current_time"] = 0.0
    
    def set_time_range(self, start_time: Union[float, datetime], end_time: Union[float, datetime]) -> None:
        """時間範囲を設定"""
        self._playback.set_time_range(start_time, end_time)
        # 現在時刻をセッション状態に保存
        st.session_state[f"{self._session_key_prefix}_current_time"] = self._playback.get_current_time()
    
    def set_current_time(self, time_value: Union[float, datetime]) -> None:
        """現在時刻を設定"""
        self._playback.set_current_time(time_value)
        # 現在時刻をセッション状態に保存
        st.session_state[f"{self._session_key_prefix}_current_time"] = self._playback.get_current_time()
    
    def get_current_time(self) -> float:
        """現在時刻を取得"""
        # セッション状態から現在時刻を取得
        current_time = st.session_state.get(f"{self._session_key_prefix}_current_time", 0.0)
        self._playback.set_current_time(current_time)  # 内部状態を同期
        return self._playback.get_current_time()
    
    def get_current_datetime(self) -> Optional[datetime]:
        """現在時刻をdatetime型で取得"""
        return self._playback.get_current_datetime()
    
    def play(self) -> None:
        """再生を開始"""
        self._playback.play()
        # 再生状態をセッション状態に保存
        st.session_state[f"{self._session_key_prefix}_playing"] = True
        st.session_state[f"{self._session_key_prefix}_last_time"] = time.time()
    
    def pause(self) -> None:
        """再生を一時停止"""
        self._playback.pause()
        # 再生状態をセッション状態に保存
        st.session_state[f"{self._session_key_prefix}_playing"] = False
    
    def stop(self) -> None:
        """再生を停止して先頭に戻る"""
        self._playback.stop()
        # 再生状態と現在時刻をセッション状態に保存
        st.session_state[f"{self._session_key_prefix}_playing"] = False
        st.session_state[f"{self._session_key_prefix}_current_time"] = self._playback.get_current_time()
    
    def is_playing(self) -> bool:
        """再生中かどうかを取得"""
        # セッション状態から再生状態を取得
        return st.session_state.get(f"{self._session_key_prefix}_playing", False)
    
    def set_play_speed(self, speed: float) -> None:
        """再生速度を設定"""
        self._playback.set_play_speed(speed)
    
    def get_play_speed(self) -> float:
        """再生速度を取得"""
        return self._playback.get_play_speed()
    
    def set_loop(self, loop: bool) -> None:
        """ループ再生の設定"""
        self._playback.set_loop(loop)
    
    def is_loop(self) -> bool:
        """ループ再生の設定を取得"""
        return self._playback.is_loop()
    
    def add_keyframe(self, time_value: Union[float, datetime], label: str, details: Optional[Dict] = None) -> None:
        """キーフレームを追加"""
        self._playback.add_keyframe(time_value, label, details)
    
    def get_keyframes(self) -> List[Dict]:
        """すべてのキーフレームを取得"""
        return self._playback.get_keyframes()
    
    def jump_to_next_keyframe(self) -> bool:
        """次のキーフレームに移動"""
        result = self._playback.jump_to_next_keyframe()
        if result:
            # 現在時刻をセッション状態に保存
            st.session_state[f"{self._session_key_prefix}_current_time"] = self._playback.get_current_time()
        return result
    
    def jump_to_prev_keyframe(self) -> bool:
        """前のキーフレームに移動"""
        result = self._playback.jump_to_prev_keyframe()
        if result:
            # 現在時刻をセッション状態に保存
            st.session_state[f"{self._session_key_prefix}_current_time"] = self._playback.get_current_time()
        return result
    
    def set_on_time_change(self, callback: Callable[[float], None]) -> None:
        """時間変更コールバックを設定"""
        self._playback.set_on_time_change(callback)
    
    def set_on_play_state_change(self, callback: Callable[[bool], None]) -> None:
        """再生状態変更コールバックを設定"""
        self._playback.set_on_play_state_change(callback)
    
    def update(self) -> None:
        """
        現在の時刻状態を更新（Streamlitの再描画サイクルでの利用を想定）
        """
        # 再生中の場合のみ更新
        if self.is_playing():
            # 前回の更新からの経過時間を計算
            current_time = time.time()
            last_time = st.session_state.get(f"{self._session_key_prefix}_last_time", current_time)
            delta_time = current_time - last_time
            
            # 内部プレイバックコントローラーを更新
            self._playback.set_current_time(st.session_state[f"{self._session_key_prefix}_current_time"])
            self._playback.update(delta_time)
            
            # 更新後の状態をセッション状態に保存
            st.session_state[f"{self._session_key_prefix}_current_time"] = self._playback.get_current_time()
            st.session_state[f"{self._session_key_prefix}_last_time"] = current_time
            
            # 再生が停止された場合、セッション状態も更新
            if not self._playback.is_playing():
                st.session_state[f"{self._session_key_prefix}_playing"] = False
    
    def render_controls(self, key_prefix: str = "") -> Dict:
        """プレイバック制御UI要素をStreamlitで表示"""
        # 再生状態を更新
        self.update()
        
        # 内部プレイバックコントローラーの状態を同期
        self._playback._playing = self.is_playing()
        self._playback._current_time = self.get_current_time()
        
        # コントロールを描画
        changes = self._playback.render_controls(key_prefix)
        
        # UI操作による変更をセッション状態に反映
        if "playing" in changes:
            st.session_state[f"{self._session_key_prefix}_playing"] = changes["playing"]
        
        if "current_time" in changes:
            st.session_state[f"{self._session_key_prefix}_current_time"] = changes["current_time"]
        
        return changes
    
    def render_compact_controls(self, key_prefix: str = "") -> Dict:
        """コンパクトなプレイバック制御UI要素をStreamlitで表示"""
        # 再生状態を更新
        self.update()
        
        # 内部プレイバックコントローラーの状態を同期
        self._playback._playing = self.is_playing()
        self._playback._current_time = self.get_current_time()
        
        # コンパクトコントロールを描画
        changes = self._playback.render_compact_controls(key_prefix)
        
        # UI操作による変更をセッション状態に反映
        if "playing" in changes:
            st.session_state[f"{self._session_key_prefix}_playing"] = changes["playing"]
        
        if "current_time" in changes:
            st.session_state[f"{self._session_key_prefix}_current_time"] = changes["current_time"]
        
        return changes


class DataRangeSelector:
    """
    データ範囲を選択するための制御コンポーネント
    
    数値や日付の範囲を選択するためのUIと機能を提供します。
    """
    
    def __init__(self, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        name : str, optional
            コンポーネントの表示名
        """
        self.name = name or "データ範囲選択"
        
        # 範囲設定
        self._min_value = 0
        self._max_value = 100
        self._start_value = 0
        self._end_value = 100
        
        # データ型
        self._data_type = "numeric"  # "numeric", "datetime"
        self._time_base = None
        
        # コールバック
        self._on_range_change_callback = None
    
    def set_numeric_range(self, min_value: float, max_value: float, 
                         start_value: Optional[float] = None, end_value: Optional[float] = None) -> None:
        """
        数値範囲を設定
        
        Parameters
        ----------
        min_value : float
            最小値
        max_value : float
            最大値
        start_value : Optional[float], optional
            開始値、指定しない場合は最小値
        end_value : Optional[float], optional
            終了値、指定しない場合は最大値
        """
        self._min_value = float(min_value)
        self._max_value = float(max_value)
        self._start_value = float(start_value) if start_value is not None else self._min_value
        self._end_value = float(end_value) if end_value is not None else self._max_value
        self._data_type = "numeric"
    
    def set_datetime_range(self, min_date: datetime, max_date: datetime, 
                          start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> None:
        """
        日時範囲を設定
        
        Parameters
        ----------
        min_date : datetime
            最小日時
        max_date : datetime
            最大日時
        start_date : Optional[datetime], optional
            開始日時、指定しない場合は最小日時
        end_date : Optional[datetime], optional
            終了日時、指定しない場合は最大日時
        """
        self._time_base = min_date
        self._min_value = 0
        self._max_value = (max_date - min_date).total_seconds()
        self._start_value = (start_date - min_date).total_seconds() if start_date is not None else self._min_value
        self._end_value = (end_date - min_date).total_seconds() if end_date is not None else self._max_value
        self._data_type = "datetime"
    
    def get_start_value(self) -> float:
        """
        開始値を取得
        
        Returns
        -------
        float
            開始値
        """
        return self._start_value
    
    def get_end_value(self) -> float:
        """
        終了値を取得
        
        Returns
        -------
        float
            終了値
        """
        return self._end_value
    
    def get_start_datetime(self) -> Optional[datetime]:
        """
        開始日時を取得
        
        Returns
        -------
        Optional[datetime]
            開始日時、日時範囲でない場合はNone
        """
        if self._data_type == "datetime" and self._time_base is not None:
            return self._time_base + timedelta(seconds=self._start_value)
        return None
    
    def get_end_datetime(self) -> Optional[datetime]:
        """
        終了日時を取得
        
        Returns
        -------
        Optional[datetime]
            終了日時、日時範囲でない場合はNone
        """
        if self._data_type == "datetime" and self._time_base is not None:
            return self._time_base + timedelta(seconds=self._end_value)
        return None
    
    def set_on_range_change(self, callback: Callable[[float, float], None]) -> None:
        """
        範囲変更コールバックを設定
        
        Parameters
        ----------
        callback : Callable[[float, float], None]
            範囲変更時に呼び出すコールバック
        """
        self._on_range_change_callback = callback
    
    def render_controls(self, key_prefix: str = "") -> Dict:
        """
        範囲選択UI要素をStreamlitで表示
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitウィジェットのキープレフィックス
            
        Returns
        -------
        Dict
            UI操作の結果発生した変更情報
        """
        changes = {}
        
        if self._data_type == "numeric":
            # 数値範囲スライダー
            start_value, end_value = st.slider(
                self.name,
                min_value=float(self._min_value),
                max_value=float(self._max_value),
                value=(float(self._start_value), float(self._end_value)),
                key=f"{key_prefix}_range_slider"
            )
            
            if start_value != self._start_value or end_value != self._end_value:
                self._start_value = start_value
                self._end_value = end_value
                changes["start_value"] = self._start_value
                changes["end_value"] = self._end_value
                
                if self._on_range_change_callback:
                    self._on_range_change_callback(self._start_value, self._end_value)
        
        elif self._data_type == "datetime" and self._time_base is not None:
            # 日時範囲スライダー
            start_time_seconds, end_time_seconds = st.slider(
                self.name,
                min_value=float(self._min_value),
                max_value=float(self._max_value),
                value=(float(self._start_value), float(self._end_value)),
                key=f"{key_prefix}_datetime_range_slider"
            )
            
            # 日時表示
            start_date = self._time_base + timedelta(seconds=start_time_seconds)
            end_date = self._time_base + timedelta(seconds=end_time_seconds)
            
            st.text(f"選択範囲: {start_date.strftime('%Y-%m-%d %H:%M:%S')} から {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if start_time_seconds != self._start_value or end_time_seconds != self._end_value:
                self._start_value = start_time_seconds
                self._end_value = end_time_seconds
                changes["start_value"] = self._start_value
                changes["end_value"] = self._end_value
                
                if self._on_range_change_callback:
                    self._on_range_change_callback(self._start_value, self._end_value)
        
        return changes


class FilterController:
    """
    データフィルタリング制御コンポーネント
    
    データのフィルタリング条件を設定・管理するコンポーネントです。
    """
    
    def __init__(self, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        name : str, optional
            コンポーネントの表示名
        """
        self.name = name or "フィルタ制御"
        
        # フィルタ設定
        self._filters = {}
        
        # カラム情報
        self._columns = {}
        
        # コールバック
        self._on_filter_change_callback = None
    
    def set_columns(self, columns: Dict[str, Dict]) -> None:
        """
        フィルタリング可能なカラム情報を設定
        
        Parameters
        ----------
        columns : Dict[str, Dict]
            カラム情報（カラム名: {type: データ型, min: 最小値, max: 最大値, ...}）
        """
        self._columns = columns
        
        # フィルタの初期化
        for col_name, col_info in columns.items():
            if col_name not in self._filters:
                # デフォルトフィルタを作成
                col_type = col_info.get("type", "unknown")
                
                if col_type in ["numeric", "integer", "float"]:
                    min_val = col_info.get("min", 0)
                    max_val = col_info.get("max", 100)
                    self._filters[col_name] = {
                        "type": col_type,
                        "enabled": False,
                        "min": min_val,
                        "max": max_val,
                        "current_min": min_val,
                        "current_max": max_val
                    }
                elif col_type == "datetime":
                    min_date = col_info.get("min", datetime.now())
                    max_date = col_info.get("max", datetime.now() + timedelta(days=1))
                    self._filters[col_name] = {
                        "type": col_type,
                        "enabled": False,
                        "min": min_date,
                        "max": max_date,
                        "current_min": min_date,
                        "current_max": max_date
                    }
                elif col_type in ["categorical", "string", "object"]:
                    values = col_info.get("values", [])
                    self._filters[col_name] = {
                        "type": col_type,
                        "enabled": False,
                        "values": values,
                        "selected": values.copy() if values else []
                    }
                elif col_type == "boolean":
                    self._filters[col_name] = {
                        "type": col_type,
                        "enabled": False,
                        "value": None  # None=両方, True=真のみ, False=偽のみ
                    }
    
    def enable_filter(self, column: str, enabled: bool = True) -> bool:
        """
        フィルタの有効/無効を設定
        
        Parameters
        ----------
        column : str
            カラム名
        enabled : bool, optional
            有効にする場合True
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if column in self._filters:
            self._filters[column]["enabled"] = enabled
            
            # コールバックがある場合は呼び出し
            if self._on_filter_change_callback:
                self._on_filter_change_callback(self._filters)
            
            return True
        return False
    
    def set_numeric_range(self, column: str, min_value: float, max_value: float) -> bool:
        """
        数値範囲フィルタを設定
        
        Parameters
        ----------
        column : str
            カラム名
        min_value : float
            最小値
        max_value : float
            最大値
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if column in self._filters and self._filters[column]["type"] in ["numeric", "integer", "float"]:
            self._filters[column]["current_min"] = min_value
            self._filters[column]["current_max"] = max_value
            
            # コールバックがある場合は呼び出し
            if self._on_filter_change_callback:
                self._on_filter_change_callback(self._filters)
            
            return True
        return False
    
    def set_datetime_range(self, column: str, min_date: datetime, max_date: datetime) -> bool:
        """
        日時範囲フィルタを設定
        
        Parameters
        ----------
        column : str
            カラム名
        min_date : datetime
            最小日時
        max_date : datetime
            最大日時
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if column in self._filters and self._filters[column]["type"] == "datetime":
            self._filters[column]["current_min"] = min_date
            self._filters[column]["current_max"] = max_date
            
            # コールバックがある場合は呼び出し
            if self._on_filter_change_callback:
                self._on_filter_change_callback(self._filters)
            
            return True
        return False
    
    def set_categorical_values(self, column: str, selected_values: List) -> bool:
        """
        カテゴリフィルタの選択値を設定
        
        Parameters
        ----------
        column : str
            カラム名
        selected_values : List
            選択する値のリスト
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if column in self._filters and self._filters[column]["type"] in ["categorical", "string", "object"]:
            self._filters[column]["selected"] = selected_values
            
            # コールバックがある場合は呼び出し
            if self._on_filter_change_callback:
                self._on_filter_change_callback(self._filters)
            
            return True
        return False
    
    def set_boolean_value(self, column: str, value: Optional[bool]) -> bool:
        """
        真偽値フィルタを設定
        
        Parameters
        ----------
        column : str
            カラム名
        value : Optional[bool]
            フィルタ値（None=両方, True=真のみ, False=偽のみ）
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if column in self._filters and self._filters[column]["type"] == "boolean":
            self._filters[column]["value"] = value
            
            # コールバックがある場合は呼び出し
            if self._on_filter_change_callback:
                self._on_filter_change_callback(self._filters)
            
            return True
        return False
    
    def get_all_filters(self) -> Dict:
        """
        すべてのフィルタ設定を取得
        
        Returns
        -------
        Dict
            フィルタ設定の辞書
        """
        return self._filters
    
    def get_active_filters(self) -> Dict:
        """
        有効なフィルタのみを取得
        
        Returns
        -------
        Dict
            有効なフィルタ設定の辞書
        """
        return {
            col: filter_info
            for col, filter_info in self._filters.items()
            if filter_info["enabled"]
        }
    
    def clear_all_filters(self) -> None:
        """すべてのフィルタを無効化"""
        for col in self._filters:
            self._filters[col]["enabled"] = False
        
        # コールバックがある場合は呼び出し
        if self._on_filter_change_callback:
            self._on_filter_change_callback(self._filters)
    
    def set_on_filter_change(self, callback: Callable[[Dict], None]) -> None:
        """
        フィルタ変更コールバックを設定
        
        Parameters
        ----------
        callback : Callable[[Dict], None]
            フィルタ変更時に呼び出すコールバック
        """
        self._on_filter_change_callback = callback
    
    def render_controls(self, key_prefix: str = "") -> Dict:
        """
        フィルタ制御UI要素をStreamlitで表示
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitウィジェットのキープレフィックス
            
        Returns
        -------
        Dict
            UI操作の結果発生した変更情報
        """
        changes = {}
        
        st.subheader(self.name)
        
        # フィルタのクリアボタン
        if st.button("すべてのフィルタをクリア", key=f"{key_prefix}_clear_filters"):
            self.clear_all_filters()
            changes["clear_all"] = True
        
        # フィルタごとに設定UI
        for col, filter_info in self._filters.items():
            # フィルタの有効/無効
            enabled = st.checkbox(
                f"{col} フィルタを有効化", 
                value=filter_info["enabled"],
                key=f"{key_prefix}_{col}_enabled"
            )
            
            if enabled != filter_info["enabled"]:
                filter_info["enabled"] = enabled
                changes[f"{col}_enabled"] = enabled
            
            # 有効な場合、フィルタ設定を表示
            if enabled:
                filter_type = filter_info["type"]
                
                if filter_type in ["numeric", "integer", "float"]:
                    # 数値範囲フィルタ
                    min_val = filter_info["min"]
                    max_val = filter_info["max"]
                    current_min = filter_info["current_min"]
                    current_max = filter_info["current_max"]
                    
                    # ステップサイズの計算
                    step = 0.1 if filter_type == "float" else 1
                    if filter_type == "float":
                        range_magnitude = max_val - min_val
                        if range_magnitude > 1000:
                            step = 1.0
                        elif range_magnitude > 100:
                            step = 0.1
                        elif range_magnitude > 10:
                            step = 0.01
                        else:
                            step = 0.001
                    
                    # スライダー
                    new_min, new_max = st.slider(
                        f"{col} 範囲", 
                        min_value=float(min_val), 
                        max_value=float(max_val),
                        value=(float(current_min), float(current_max)),
                        step=step,
                        key=f"{key_prefix}_{col}_range"
                    )
                    
                    if new_min != current_min or new_max != current_max:
                        filter_info["current_min"] = new_min
                        filter_info["current_max"] = new_max
                        changes[f"{col}_range"] = (new_min, new_max)
                
                elif filter_type == "datetime":
                    # 日時範囲フィルタ
                    min_date = filter_info["min"]
                    max_date = filter_info["max"]
                    current_min = filter_info["current_min"]
                    current_max = filter_info["current_max"]
                    
                    # 日付選択
                    col1, col2 = st.columns(2)
                    with col1:
                        new_min = st.date_input(
                            f"{col} 開始日", 
                            value=current_min.date(),
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            key=f"{key_prefix}_{col}_min_date"
                        )
                    with col2:
                        new_max = st.date_input(
                            f"{col} 終了日", 
                            value=current_max.date(),
                            min_value=min_date.date(),
                            max_value=max_date.date(),
                            key=f"{key_prefix}_{col}_max_date"
                        )
                    
                    # 日付から日時に変換
                    new_min_dt = datetime.combine(new_min, current_min.time())
                    new_max_dt = datetime.combine(new_max, current_max.time())
                    
                    if new_min_dt != current_min or new_max_dt != current_max:
                        filter_info["current_min"] = new_min_dt
                        filter_info["current_max"] = new_max_dt
                        changes[f"{col}_datetime_range"] = (new_min_dt, new_max_dt)
                
                elif filter_type in ["categorical", "string", "object"]:
                    # カテゴリフィルタ
                    values = filter_info["values"]
                    selected = filter_info["selected"]
                    
                    # 複数選択
                    new_selected = st.multiselect(
                        f"{col} 選択", 
                        options=values,
                        default=selected,
                        key=f"{key_prefix}_{col}_multiselect"
                    )
                    
                    if new_selected != selected:
                        filter_info["selected"] = new_selected
                        changes[f"{col}_selected"] = new_selected
                
                elif filter_type == "boolean":
                    # 真偽値フィルタ
                    value = filter_info["value"]
                    
                    # ラジオボタン
                    options = ["両方", "真のみ", "偽のみ"]
                    default_idx = 0 if value is None else (1 if value else 2)
                    
                    selected = st.radio(
                        f"{col} 選択",
                        options=options,
                        index=default_idx,
                        key=f"{key_prefix}_{col}_radio"
                    )
                    
                    # 選択に応じて値を設定
                    new_value = None if selected == "両方" else (True if selected == "真のみ" else False)
                    
                    if new_value != value:
                        filter_info["value"] = new_value
                        changes[f"{col}_value"] = new_value
                
                st.markdown("---")
        
        # コールバックがある場合は呼び出し
        if changes and self._on_filter_change_callback:
            self._on_filter_change_callback(self._filters)
        
        return changes


class InteractionController:
    """
    インタラクション制御コンポーネント
    
    マップのズーム/パン、選択などのインタラクションを制御するコンポーネントです。
    """
    
    def __init__(self, name: str = ""):
        """
        初期化
        
        Parameters
        ----------
        name : str, optional
            コンポーネントの表示名
        """
        self.name = name or "インタラクション制御"
        
        # 表示設定
        self._view_state = {
            "center": [35.45, 139.65],  # デフォルト: 横浜
            "zoom": 13,
            "pitch": 0,
            "bearing": 0
        }
        
        # 選択状態
        self._selection = {
            "type": None,  # None, "point", "rectangle", "lasso", "click"
            "points": [],
            "current_point": None,
            "bounds": None
        }
        
        # ツール設定
        self._active_tool = "pan"  # "pan", "select", "measure", "draw"
        self._tools = ["pan", "select"]  # 有効なツール
        
        # コールバック
        self._on_view_change_callback = None
        self._on_selection_change_callback = None
        self._on_tool_change_callback = None
    
    def set_view(self, center: List[float], zoom: float, pitch: float = 0, bearing: float = 0) -> None:
        """
        表示設定を変更
        
        Parameters
        ----------
        center : List[float]
            中心座標 [緯度, 経度]
        zoom : float
            ズームレベル
        pitch : float, optional
            傾き（度）
        bearing : float, optional
            回転角（度）
        """
        self._view_state["center"] = center
        self._view_state["zoom"] = zoom
        self._view_state["pitch"] = pitch
        self._view_state["bearing"] = bearing
        
        # コールバックがある場合は呼び出し
        if self._on_view_change_callback:
            self._on_view_change_callback(self._view_state)
    
    def get_view(self) -> Dict:
        """
        表示設定を取得
        
        Returns
        -------
        Dict
            表示設定の辞書
        """
        return self._view_state
    
    def set_selection(self, selection_type: str, points: List = None, bounds: List = None) -> None:
        """
        選択状態を設定
        
        Parameters
        ----------
        selection_type : str
            選択タイプ（"point", "rectangle", "lasso", "click"）
        points : List, optional
            選択ポイントのリスト
        bounds : List, optional
            選択領域の境界（[min_lon, min_lat, max_lon, max_lat]）
        """
        self._selection["type"] = selection_type
        
        if points is not None:
            self._selection["points"] = points
        
        if bounds is not None:
            self._selection["bounds"] = bounds
        
        # コールバックがある場合は呼び出し
        if self._on_selection_change_callback:
            self._on_selection_change_callback(self._selection)
    
    def set_current_point(self, point_index: int) -> None:
        """
        現在選択中のポイントを設定
        
        Parameters
        ----------
        point_index : int
            ポイントのインデックス
        """
        self._selection["current_point"] = point_index
        
        # コールバックがある場合は呼び出し
        if self._on_selection_change_callback:
            self._on_selection_change_callback(self._selection)
    
    def get_selection(self) -> Dict:
        """
        選択状態を取得
        
        Returns
        -------
        Dict
            選択状態の辞書
        """
        return self._selection
    
    def clear_selection(self) -> None:
        """選択状態をクリア"""
        self._selection = {
            "type": None,
            "points": [],
            "current_point": None,
            "bounds": None
        }
        
        # コールバックがある場合は呼び出し
        if self._on_selection_change_callback:
            self._on_selection_change_callback(self._selection)
    
    def set_active_tool(self, tool: str) -> bool:
        """
        アクティブなツールを設定
        
        Parameters
        ----------
        tool : str
            ツール名
            
        Returns
        -------
        bool
            設定に成功した場合True
        """
        if tool in self._tools:
            self._active_tool = tool
            
            # コールバックがある場合は呼び出し
            if self._on_tool_change_callback:
                self._on_tool_change_callback(self._active_tool)
            
            return True
        return False
    
    def get_active_tool(self) -> str:
        """
        アクティブなツールを取得
        
        Returns
        -------
        str
            ツール名
        """
        return self._active_tool
    
    def set_available_tools(self, tools: List[str]) -> None:
        """
        利用可能なツールを設定
        
        Parameters
        ----------
        tools : List[str]
            ツール名のリスト
        """
        self._tools = tools
        
        # アクティブツールが利用可能ツールに含まれない場合、変更
        if self._active_tool not in self._tools and self._tools:
            self._active_tool = self._tools[0]
            
            # コールバックがある場合は呼び出し
            if self._on_tool_change_callback:
                self._on_tool_change_callback(self._active_tool)
    
    def set_on_view_change(self, callback: Callable[[Dict], None]) -> None:
        """
        表示変更コールバックを設定
        
        Parameters
        ----------
        callback : Callable[[Dict], None]
            表示変更時に呼び出すコールバック
        """
        self._on_view_change_callback = callback
    
    def set_on_selection_change(self, callback: Callable[[Dict], None]) -> None:
        """
        選択変更コールバックを設定
        
        Parameters
        ----------
        callback : Callable[[Dict], None]
            選択変更時に呼び出すコールバック
        """
        self._on_selection_change_callback = callback
    
    def set_on_tool_change(self, callback: Callable[[str], None]) -> None:
        """
        ツール変更コールバックを設定
        
        Parameters
        ----------
        callback : Callable[[str], None]
            ツール変更時に呼び出すコールバック
        """
        self._on_tool_change_callback = callback
    
    def render_controls(self, key_prefix: str = "") -> Dict:
        """
        インタラクション制御UI要素をStreamlitで表示
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitウィジェットのキープレフィックス
            
        Returns
        -------
        Dict
            UI操作の結果発生した変更情報
        """
        changes = {}
        
        # ツール選択
        tool_icons = {
            "pan": "👋",
            "select": "👆",
            "measure": "📏",
            "draw": "✏️"
        }
        
        tool_options = [f"{tool_icons.get(tool, '🔧')} {tool.capitalize()}" for tool in self._tools]
        tool_values = self._tools
        
        # 現在のツールのインデックスを取得
        current_tool_idx = tool_values.index(self._active_tool) if self._active_tool in tool_values else 0
        
        # ツール選択ボタン
        st.write("ツール:")
        cols = st.columns(len(tool_options))
        
        for i, (col, tool_option, tool_value) in enumerate(zip(cols, tool_options, tool_values)):
            with col:
                # アクティブなツールの場合はボタンを別の色に
                button_type = "primary" if i == current_tool_idx else "secondary"
                if st.button(tool_option, key=f"{key_prefix}_tool_{tool_value}", type=button_type):
                    self._active_tool = tool_value
                    changes["active_tool"] = tool_value
                    
                    # コールバックがある場合は呼び出し
                    if self._on_tool_change_callback:
                        self._on_tool_change_callback(self._active_tool)
        
        # ツール固有の設定
        st.markdown("---")
        
        if self._active_tool == "pan":
            # センター位置の表示と変更
            center_lat, center_lng = self._view_state["center"]
            st.write(f"中心位置: {center_lat:.6f}, {center_lng:.6f}")
            
            col1, col2 = st.columns(2)
            with col1:
                new_lat = st.number_input(
                    "緯度", 
                    value=float(center_lat),
                    format="%.6f",
                    key=f"{key_prefix}_center_lat"
                )
            with col2:
                new_lng = st.number_input(
                    "経度", 
                    value=float(center_lng),
                    format="%.6f",
                    key=f"{key_prefix}_center_lng"
                )
            
            if new_lat != center_lat or new_lng != center_lng:
                self._view_state["center"] = [new_lat, new_lng]
                changes["center"] = [new_lat, new_lng]
                
                # コールバックがある場合は呼び出し
                if self._on_view_change_callback:
                    self._on_view_change_callback(self._view_state)
            
            # ズームレベル
            zoom = self._view_state["zoom"]
            new_zoom = st.slider(
                "ズームレベル", 
                min_value=1.0, 
                max_value=20.0, 
                value=float(zoom),
                step=0.5,
                key=f"{key_prefix}_zoom"
            )
            
            if new_zoom != zoom:
                self._view_state["zoom"] = new_zoom
                changes["zoom"] = new_zoom
                
                # コールバックがある場合は呼び出し
                if self._on_view_change_callback:
                    self._on_view_change_callback(self._view_state)
        
        elif self._active_tool == "select":
            # 選択モード
            select_modes = ["クリック", "長方形", "円", "多角形"]
            select_mode_values = ["click", "rectangle", "circle", "polygon"]
            
            current_mode = "クリック"
            if self._selection["type"] in select_mode_values:
                current_mode = select_modes[select_mode_values.index(self._selection["type"])]
            
            new_mode = st.radio(
                "選択モード",
                options=select_modes,
                index=select_modes.index(current_mode),
                horizontal=True,
                key=f"{key_prefix}_select_mode"
            )
            
            new_mode_value = select_mode_values[select_modes.index(new_mode)]
            
            if new_mode_value != self._selection["type"]:
                self._selection["type"] = new_mode_value
                changes["selection_type"] = new_mode_value
                
                # 選択をクリア
                self._selection["points"] = []
                self._selection["current_point"] = None
                self._selection["bounds"] = None
                
                # コールバックがある場合は呼び出し
                if self._on_selection_change_callback:
                    self._on_selection_change_callback(self._selection)
            
            # 選択クリアボタン
            if st.button("選択をクリア", key=f"{key_prefix}_clear_selection"):
                self.clear_selection()
                changes["clear_selection"] = True
        
        return changes
