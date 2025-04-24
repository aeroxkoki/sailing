# -*- coding: utf-8 -*-
"""
ui.demo_playback

プレイバック機能とマップ・タイムライン連携のデモアプリケーションです。
GPSトラックデータを時間軸に沿って再生し、マップとタイムラインの同期を示します。
"""

import streamlit as st
import numpy as np
import pandas as pd
import time
import json
import random
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.abspath('..'))

from sailing_data_processor.reporting.elements.timeline.playback_control import PlaybackControl
from sailing_data_processor.reporting.interaction.view_synchronizer import ViewSynchronizer
from ui.components.reporting.timeline.playback_panel import playback_panel, playback_mini_panel
from sailing_data_processor.reporting.elements.map.base_map_element import BaseMapElement
from sailing_data_processor.reporting.elements.timeline.parameter_timeline import ParameterTimeline

# ダミーデータ生成関数
def generate_dummy_data(num_points=100, start_time=None):
    """
    ダミーGPSトラックデータを生成
    
    Parameters
    ----------
    num_points : int, optional
        データポイント数, by default 100
    start_time : datetime, optional
        開始時刻, by default 現在時刻
        
    Returns
    -------
    dict
        ダミーデータ
    """
    if start_time is None:
        start_time = datetime.now()
    
    # 時間の生成
    timestamps = [start_time + timedelta(seconds=i*10) for i in range(num_points)]
    
    # 緯度/経度の生成（円形の軌跡）
    center_lat, center_lng = 35.4498, 139.6649  # 横浜
    radius = 0.01  # 約1kmの円
    angles = np.linspace(0, 2*np.pi, num_points)
    
    latitudes = [center_lat + radius * np.sin(angle) for angle in angles]
    longitudes = [center_lng + radius * np.cos(angle) for angle in angles]
    
    # 速度と風向風速の生成
    speeds = [5 + 2 * np.sin(angle*2) for angle in angles]  # 5±2ノット
    wind_speeds = [10 + 3 * np.sin(angle*3) for angle in angles]  # 10±3ノット
    wind_directions = [270 + 45 * np.sin(angle) for angle in angles]  # 270±45度
    
    # ヒール角とヘディングの生成
    heels = [5 + 10 * np.sin(angle*4) for angle in angles]  # 5±10度
    headings = [angles[i] * 180/np.pi for i in range(num_points)]  # 進行方向
    
    # タック/ジャイブのマーキング
    tacks = [False] * num_points
    jibes = [False] * num_points
    
    # 約10ポイントごとにタックまたはジャイブ
    for i in range(5, num_points, 10):
        if i % 20 == 5:  # タック
            tacks[i] = True
        elif i % 20 == 15:  # ジャイブ
            jibes[i] = True
    
    # データをまとめる
    data = {
        "timestamp": timestamps,
        "latitude": latitudes,
        "longitude": longitudes,
        "speed": speeds,
        "wind_speed": wind_speeds,
        "wind_direction": wind_directions,
        "heel": heels,
        "heading": headings,
        "is_tack": tacks,
        "is_jibe": jibes
    }
    
    return data

# シンプルなマップ表示クラス
class SimpleMapView:
    """シンプルなマップ表示クラス"""
    
    def __init__(self, element_id=None):
        """初期化"""
        self.element_id = element_id or f"map_view_{int(time.time())}"
        self.name = "マップ表示"
        self._current_time = 0
        self._data = None
        self._current_point_index = 0
    
    def set_data(self, data):
        """データを設定"""
        self._data = data
    
    def set_current_time(self, time_value):
        """現在時刻を設定"""
        self._current_time = time_value
        
        # データから最も近い時間のインデックスを探す
        if self._data and "timestamp" in self._data:
            timestamps = self._data["timestamp"]
            if timestamps:
                # 時間値に変換（秒数の場合）
                if isinstance(time_value, (int, float)) and not isinstance(timestamps[0], (int, float)):
                    reference_time = timestamps[0]
                    target_time = reference_time + timedelta(seconds=time_value)
                else:
                    target_time = time_value
                
                # 最も近いインデックスを見つける
                closest_idx = 0
                min_diff = float('inf')
                
                for i, ts in enumerate(timestamps):
                    if isinstance(ts, datetime) and isinstance(target_time, (int, float)):
                        # target_timeが秒数、tsが日時の場合
                        diff = abs((ts - timestamps[0]).total_seconds() - target_time)
                    elif isinstance(ts, (int, float)) and isinstance(target_time, datetime):
                        # tsが秒数、target_timeが日時の場合
                        diff = abs(ts - (target_time - timestamps[0]).total_seconds())
                    else:
                        # 同じ型の場合
                        diff = abs(ts - target_time)
                    
                    if diff < min_diff:
                        min_diff = diff
                        closest_idx = i
                
                self._current_point_index = closest_idx
    
    def render(self):
        """マップをレンダリング"""
        if self._data is None:
            st.warning("データが設定されていません")
            return
        
        if "latitude" not in self._data or "longitude" not in self._data:
            st.warning("緯度/経度データがありません")
            return
        
        # 現在位置を取得
        if len(self._data["latitude"]) > self._current_point_index:
            current_lat = self._data["latitude"][self._current_point_index]
            current_lng = self._data["longitude"][self._current_point_index]
            
            # その他のデータ（あれば）
            additional_data = {}
            for key in ["speed", "heading", "wind_speed", "wind_direction"]:
                if key in self._data and len(self._data[key]) > self._current_point_index:
                    additional_data[key] = self._data[key][self._current_point_index]
            
            # 軌跡データ（全データの5%をサンプリング表示）
            track_lat = self._data["latitude"][:self._current_point_index+1]
            track_lng = self._data["longitude"][:self._current_point_index+1]
            
            # マップを表示
            st.markdown(f"### 現在位置: ポイント {self._current_point_index+1}/{len(self._data['latitude'])}")
            
            # 情報を表示
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"緯度: {current_lat:.6f}")
                st.write(f"経度: {current_lng:.6f}")
            
            with col2:
                for key, value in additional_data.items():
                    display_name = {
                        "speed": "速度 (kt)",
                        "heading": "艇首方位 (°)",
                        "wind_speed": "風速 (kt)",
                        "wind_direction": "風向 (°)"
                    }.get(key, key)
                    st.write(f"{display_name}: {value:.1f}")
            
            # トラック情報を表示
            track_data = pd.DataFrame({
                "lat": track_lat,
                "lon": track_lng
            })
            
            # マップ表示
            st.map(track_data)

# シンプルなタイムライン表示クラス
class SimpleTimelineView:
    """シンプルなタイムライン表示クラス"""
    
    def __init__(self, element_id=None):
        """初期化"""
        self.element_id = element_id or f"timeline_view_{int(time.time())}"
        self.name = "タイムライン表示"
        self._current_time = 0
        self._data = None
        self._current_point_index = 0
    
    def set_data(self, data):
        """データを設定"""
        self._data = data
    
    def set_current_time(self, time_value):
        """現在時刻を設定"""
        self._current_time = time_value
        
        # データから最も近い時間のインデックスを探す
        if self._data and "timestamp" in self._data:
            timestamps = self._data["timestamp"]
            if timestamps:
                # 時間値に変換（秒数の場合）
                if isinstance(time_value, (int, float)) and not isinstance(timestamps[0], (int, float)):
                    reference_time = timestamps[0]
                    target_time = reference_time + timedelta(seconds=time_value)
                else:
                    target_time = time_value
                
                # 最も近いインデックスを見つける
                closest_idx = 0
                min_diff = float('inf')
                
                for i, ts in enumerate(timestamps):
                    if isinstance(ts, datetime) and isinstance(target_time, (int, float)):
                        # target_timeが秒数、tsが日時の場合
                        diff = abs((ts - timestamps[0]).total_seconds() - target_time)
                    elif isinstance(ts, (int, float)) and isinstance(target_time, datetime):
                        # tsが秒数、target_timeが日時の場合
                        diff = abs(ts - (target_time - timestamps[0]).total_seconds())
                    else:
                        # 同じ型の場合
                        diff = abs(ts - target_time)
                    
                    if diff < min_diff:
                        min_diff = diff
                        closest_idx = i
                
                self._current_point_index = closest_idx
    
    def render(self):
        """タイムラインをレンダリング"""
        if self._data is None:
            st.warning("データが設定されていません")
            return
        
        # 時間軸の表示用に処理
        if "timestamp" not in self._data:
            st.warning("タイムスタンプデータがありません")
            return
        
        # 現在のタイムライン位置を表示
        st.markdown(f"### タイムライン表示: ポイント {self._current_point_index+1}/{len(self._data['timestamp'])}")
        
        # 現在の時間を表示
        if isinstance(self._data["timestamp"][0], datetime):
            current_time = self._data["timestamp"][self._current_point_index]
            st.write(f"時刻: {current_time.strftime('%H:%M:%S')}")
        else:
            st.write(f"経過時間: {self._current_time:.1f}秒")
        
        # グラフ用にデータを準備
        graph_data = pd.DataFrame()
        graph_data["index"] = list(range(len(self._data["timestamp"])))
        
        # 表示するパラメータを選択
        for param in ["speed", "wind_speed", "wind_direction", "heel"]:
            if param in self._data:
                graph_data[param] = self._data[param]
        
        # イベントのマーキング
        events = []
        for i in range(len(self._data["timestamp"])):
            if "is_tack" in self._data and self._data["is_tack"][i]:
                events.append({"index": i, "type": "タック"})
            elif "is_jibe" in self._data and self._data["is_jibe"][i]:
                events.append({"index": i, "type": "ジャイブ"})
        
        # グラフを表示
        st.line_chart(graph_data.set_index("index"))
        
        # 現在位置をマーク
        if events:
            event_df = pd.DataFrame(events)
            st.write("### イベント")
            st.dataframe(event_df)

# メイン関数
def main():
    """メイン関数"""
    st.set_page_config(page_title="セーリング戦略分析システム - プレイバックデモ", layout="wide")
    
    st.title("セーリング戦略分析システム - プレイバックデモ")
    st.markdown("""
    GPSトラックデータのプレイバック機能とマップ・タイムライン連携のデモアプリケーションです。
    プレイバックコントロールを使用して、マップとタイムラインの同期表示を確認できます。
    """)
    
    # セッション状態の初期化
    if "initialized" not in st.session_state:
        # ダミーデータの生成
        data = generate_dummy_data(num_points=100)
        
        # 相対時間に変換（秒数）
        base_time = data["timestamp"][0]
        relative_timestamps = [(ts - base_time).total_seconds() for ts in data["timestamp"]]
        
        # データを更新
        data["seconds"] = relative_timestamps
        
        # プレイバックコントロールの作成
        playback_control = PlaybackControl(
            element_id="playback_demo",
            name="プレイバックデモ"
        )
        
        # 時間範囲の設定
        playback_control.set_time_range(0, relative_timestamps[-1])
        
        # キーフレームの追加（タック・ジャイブ位置）
        for i in range(len(data["timestamp"])):
            if data["is_tack"][i]:
                playback_control.add_keyframe(
                    time=relative_timestamps[i],
                    label=f"タック {i+1}",
                    details={"type": "tack", "index": i}
                )
            elif data["is_jibe"][i]:
                playback_control.add_keyframe(
                    time=relative_timestamps[i],
                    label=f"ジャイブ {i+1}",
                    details={"type": "jibe", "index": i}
                )
        
        # ビュー作成
        map_view = SimpleMapView(element_id="map_view")
        map_view.set_data(data)
        
        timeline_view = SimpleTimelineView(element_id="timeline_view")
        timeline_view.set_data(data)
        
        # 同期マネージャーの作成
        synchronizer = ViewSynchronizer()
        
        # ビューの登録
        synchronizer.register_view("playback", playback_control, "playback")
        synchronizer.register_view("map", map_view, "map")
        synchronizer.register_view("timeline", timeline_view, "timeline")
        
        # ビュー間の接続を設定
        synchronizer.connect_views("playback", "map", ["time"])
        synchronizer.connect_views("playback", "timeline", ["time"])
        
        # セッション状態に保存
        st.session_state.data = data
        st.session_state.playback_control = playback_control
        st.session_state.map_view = map_view
        st.session_state.timeline_view = timeline_view
        st.session_state.synchronizer = synchronizer
        st.session_state.initialized = True
    
    # プレイバック変更処理
    def on_playback_change(changes):
        """プレイバック変更時のコールバック"""
        if "current_time" in changes:
            # 同期マネージャーに時間変更を通知
            st.session_state.synchronizer.update_view_context(
                "playback", {"time": changes["current_time"]}
            )
    
    # レイアウト
    st.markdown("## プレイバック制御")
    
    # プレイバックコントロールの表示
    playback_changes = playback_panel(
        st.session_state.playback_control,
        on_change=on_playback_change,
        key_prefix="main"
    )
    
    # コンパクトな表示切り替え
    compact_view = st.checkbox("コンパクト表示に切り替え", value=False)
    
    if compact_view:
        playback_mini_panel(
            st.session_state.playback_control,
            on_change=on_playback_change,
            key_prefix="mini"
        )
    
    # マップとタイムラインの表示
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("## マップ表示")
        st.session_state.map_view.render()
    
    with col2:
        st.markdown("## タイムライン表示")
        st.session_state.timeline_view.render()
    
    # 同期状態の表示
    st.markdown("## 同期状態")
    
    # 現在の同期状態を取得
    sync_info = st.session_state.synchronizer.to_dict()
    
    # 同期情報をJSONで表示
    st.json(sync_info)
    
    # アプリケーション情報
    st.markdown("---")
    st.markdown("""
    ### このデモについて
    
    このデモアプリケーションは、セーリング戦略分析システムのプレイバック機能とマップ・タイムライン連携機能を示しています。
    
    **主な機能:**
    
    - GPSトラックデータの時間軸に沿った再生
    - プレイバックコントロール（再生/一時停止/停止/早送り/巻き戻し）
    - マップ表示とタイムラインの同期
    - キーフレーム（タック/ジャイブ位置）へのジャンプ
    - 時間範囲の設定
    - ビュー間の同期管理
    
    **実装したクラス:**
    
    - `PlaybackControl`: プレイバック制御クラス
    - `ViewSynchronizer`: ビュー同期マネージャークラス
    - `playback_panel`: プレイバックコントロールのUI
    
    このデモではダミーデータを使用していますが、実際のシステムでは実際のGPSデータを使用します。
    """)

if __name__ == "__main__":
    main()
