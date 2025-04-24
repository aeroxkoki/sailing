# -*- coding: utf-8 -*-
"""
ui.demo.demo_post_race モジュール

レース後戦略分析エンジンのデモアプリケーション。
このモジュールはStreamlitを使用して、レース後戦略分析エンジンの機能を
ユーザーが簡単に試せるようにするためのデモインターフェースを提供します。
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys
import logging

# モジュールの検索パスに親ディレクトリを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 内部モジュールのインポート
from sailing_data_processor.analysis.post_race_analyzer import PostRaceAnalyzer
from ui.components.analysis.post_race_panel import post_race_analysis_panel

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """メインアプリケーション関数"""
    # アプリケーションのタイトルと説明
    st.title("セーリング戦略分析 - レース後分析デモ")
    st.markdown("""
    このデモアプリケーションでは、レース後戦略分析エンジンの機能を体験できます。
    GPSトラックデータと風データに基づいて、レース戦略の評価、重要な判断ポイントの特定、
    スキル向上のための提案を生成します。
    
    以下の機能を試すことができます：
    - **コンテキスト認識型評価**: レースの状況を考慮した戦略評価
    - **重要ポイント特定**: レース中の重要な判断ポイントの検出
    - **スキルレベル対応提案**: セーラーの経験レベルに合わせた改善提案
    - **レポート生成**: 分析結果をレポートとして出力
    
    サンプルデータを使用して機能をお試しください。
    """)
    
    # サイドバーに設定オプション
    with st.sidebar:
        st.header("デモ設定")
        
        # データセットの選択
        dataset = st.selectbox(
            "デモデータセット",
            options=["風上/風下コース", "三角コース", "カスタムデータ"],
            index=0,
            help="分析に使用するサンプルデータセットを選択してください。"
        )
        
        # 分析レベルの選択
        analysis_level = st.selectbox(
            "分析レベル",
            options=["basic", "intermediate", "advanced", "professional"],
            format_func=lambda x: {
                "basic": "基本", 
                "intermediate": "中級", 
                "advanced": "高度", 
                "professional": "プロフェッショナル"
            }.get(x, x),
            index=2,
            help="分析の詳細度を選択します。上級者ほど詳細な分析結果が表示されます。"
        )
        
        # 詳細設定の展開
        with st.expander("詳細設定", expanded=False):
            # シミュレーションレベル
            simulation_fidelity = st.slider(
                "シミュレーション精度",
                min_value=1,
                max_value=5,
                value=3,
                help="データ生成の精度です。値が高いほど詳細なシミュレーションが行われます。"
            )
            
            # 風の変動性
            wind_variability = st.slider(
                "風の変動性",
                min_value=0.1,
                max_value=1.0,
                value=0.5,
                step=0.1,
                help="風向風速の変動量です。値が高いほど風の変化が大きくなります。"
            )
        
        # データの再生成ボタン
        if st.button("データ再生成"):
            # セッション状態をクリア
            for key in list(st.session_state.keys()):
                if key.startswith("demo_"):
                    del st.session_state[key]
            
            st.success("データを再生成しました。新しいデータで分析を実行してください。")
    
    # データの生成または取得
    track_data, wind_data, competitor_data, course_data = get_or_generate_data(
        dataset, simulation_fidelity, wind_variability
    )
    
    # データ管理用のダミークラス
    class DummyDataManager:
        def get_available_data(self):
            return {
                "tracks": ["デモトラック"],
                "wind_data": ["推定風データ"],
                "competitors": ["競合艇データ", "なし"],
                "courses": ["コースデータ", "なし"]
            }
        
        def get_track_data(self, name):
            return track_data
        
        def get_wind_data(self, name):
            return wind_data
        
        def get_competitor_data(self, name):
            return competitor_data if name != "なし" else None
        
        def get_course_data(self, name):
            return course_data if name != "なし" else None
    
    # データマネージャーの作成
    data_manager = DummyDataManager()
    
    # 分析エンジンの作成または取得
    analyzer = get_or_create_analyzer(analysis_level)
    
    # 分析パネルの表示
    post_race_analysis_panel(analyzer, data_manager, on_change=None, key_prefix="demo_")

def get_or_create_analyzer(analysis_level):
    """分析エンジンの作成または取得"""
    if "demo_analyzer" not in st.session_state or st.session_state["demo_analyzer"].analysis_level != analysis_level:
        # サンプルのセーラープロファイル
        sailor_profile = {
            "name": "Demo Sailor",
            "skill_level": "intermediate",
            "experience_years": 5,
            "competition_level": "regional",
            "preferred_boat_class": "Laser",
            "goals": "全国選手権への出場とトップ10入賞"
        }
        
        # レースコンテキスト
        race_context = {
            "race_type": "club_race",
            "wind_conditions": "medium",
            "competition_level": "intermediate"
        }
        
        # 分析エンジンの作成
        st.session_state["demo_analyzer"] = PostRaceAnalyzer(
            sailor_profile=sailor_profile,
            race_context=race_context,
            analysis_level=analysis_level
        )
    
    return st.session_state["demo_analyzer"]

def get_or_generate_data(dataset_type, simulation_fidelity, wind_variability):
    """データセットの取得または生成"""
    # セッションに保存されたデータがあれば再利用
    if all(key in st.session_state for key in ["demo_track_data", "demo_wind_data", "demo_competitor_data", "demo_course_data"]):
        return (
            st.session_state["demo_track_data"],
            st.session_state["demo_wind_data"],
            st.session_state["demo_competitor_data"],
            st.session_state["demo_course_data"]
        )
    
    # データセットに基づいてデータを生成
    if dataset_type == "風上/風下コース":
        track_data, wind_data, competitor_data, course_data = generate_upwind_downwind_dataset(
            simulation_fidelity, wind_variability
        )
    elif dataset_type == "三角コース":
        track_data, wind_data, competitor_data, course_data = generate_triangle_dataset(
            simulation_fidelity, wind_variability
        )
    else:  # カスタムデータ
        track_data, wind_data, competitor_data, course_data = generate_custom_dataset(
            simulation_fidelity, wind_variability
        )
    
    # セッションに保存
    st.session_state["demo_track_data"] = track_data
    st.session_state["demo_wind_data"] = wind_data
    st.session_state["demo_competitor_data"] = competitor_data
    st.session_state["demo_course_data"] = course_data
    
    return track_data, wind_data, competitor_data, course_data

def generate_upwind_downwind_dataset(fidelity, wind_variability):
    """風上/風下コースのデータセットを生成"""
    # 開始時刻（現在時刻の1時間前）
    start_time = datetime.now() - timedelta(hours=1)
    
    # データポイント数（精度によって調整）
    n_points = 500 * fidelity
    
    # コース情報
    course_data = {
        "course_type": "windward_leeward",
        "marks": [
            {"name": "スタート/フィニッシュライン", "position": [35.6, 139.7]},
            {"name": "風上マーク", "position": [35.61, 139.7]},
            {"name": "風下マーク", "position": [35.6, 139.7]}
        ],
        "laps": 2,
        "start_direction": 0,
        "wind_conditions": {
            "avg_wind_direction": 0,  # 北からの風
            "avg_wind_speed": 10,     # 10ノット
            "wind_variability": wind_variability * 30  # 風の変動幅（度）
        }
    }
    
    # タイムスタンプの生成（1秒間隔）
    timestamps = [start_time + timedelta(seconds=i * (60 / fidelity)) for i in range(n_points)]
    
    # コース上の位置の生成
    # 風上/風下コースのパターン（スタート→風上→風下→風上→風下→フィニッシュ）
    center_lat, center_lon = 35.6, 139.7  # 中心位置
    
    # 各レグの割合
    leg_ratios = [0.05, 0.2, 0.2, 0.2, 0.2, 0.15]  # スタート準備、風上1、風下1、風上2、風下2、フィニッシュ
    leg_points = [int(ratio * n_points) for ratio in leg_ratios]
    
    # 位置データの生成
    latitudes = []
    longitudes = []
    headings = []
    
    # スタート準備
    start_points = leg_points[0]
    start_lat = np.linspace(35.595, 35.6, start_points)
    start_lon = np.full(start_points, 139.7)
    start_heading = np.full(start_points, 0)  # 北向き
    
    # 風上1
    upwind1_points = leg_points[1]
    upwind1_lat = np.linspace(35.6, 35.61, upwind1_points)
    
    # ジグザグパターンの生成（タック）
    zigzag_amplitude = 0.002 * wind_variability
    zigzag_frequency = 5 * fidelity
    upwind1_lon = 139.7 + zigzag_amplitude * np.sin(np.linspace(0, zigzag_frequency * np.pi, upwind1_points))
    
    # 風上時の艇の方向（ジグザグに合わせて変化）
    upwind1_heading = 0 + 40 * np.sign(np.gradient(upwind1_lon))
    
    # 風下1
    downwind1_points = leg_points[2]
    downwind1_lat = np.linspace(35.61, 35.6, downwind1_points)
    
    # ジグザグパターンの生成（ジャイブ）
    downwind1_lon = 139.7 + zigzag_amplitude * 0.7 * np.sin(np.linspace(0, (zigzag_frequency * 0.7) * np.pi, downwind1_points))
    
    # 風下時の艇の方向
    downwind1_heading = 180 + 20 * np.sign(np.gradient(downwind1_lon))
    
    # 風上2
    upwind2_points = leg_points[3]
    upwind2_lat = np.linspace(35.6, 35.61, upwind2_points)
    
    # 異なるジグザグパターン
    upwind2_lon = 139.7 + zigzag_amplitude * 1.2 * np.sin(np.linspace(0, (zigzag_frequency * 1.2) * np.pi, upwind2_points))
    
    # 風上時の艇の方向
    upwind2_heading = 0 + 40 * np.sign(np.gradient(upwind2_lon))
    
    # 風下2
    downwind2_points = leg_points[4]
    downwind2_lat = np.linspace(35.61, 35.6, downwind2_points)
    
    # 異なるジグザグパターン
    downwind2_lon = 139.7 + zigzag_amplitude * 0.5 * np.sin(np.linspace(0, (zigzag_frequency * 0.5) * np.pi, downwind2_points))
    
    # 風下時の艇の方向
    downwind2_heading = 180 + 20 * np.sign(np.gradient(downwind2_lon))
    
    # フィニッシュ
    finish_points = leg_points[5]
    finish_lat = np.full(finish_points, 35.6)
    finish_lon = np.linspace(139.7, 139.705, finish_points)
    finish_heading = np.full(finish_points, 90)  # 東向き
    
    # 全てのセグメントを結合
    latitudes = np.concatenate([start_lat, upwind1_lat, downwind1_lat, upwind2_lat, downwind2_lat, finish_lat])
    longitudes = np.concatenate([start_lon, upwind1_lon, downwind1_lon, upwind2_lon, downwind2_lon, finish_lon])
    headings = np.concatenate([start_heading, upwind1_heading, downwind1_heading, upwind2_heading, downwind2_heading, finish_heading])
    
    # 速度の生成
    # 各レグでの基本速度と変動
    base_speeds = [3, 5.5, 7, 5.8, 6.5, 4]  # 各レグの基本速度
    speed_variations = [1, 1.5, 2, 1.8, 2.2, 1]  # 各レグの速度変動
    
    speeds = []
    
    for i, points in enumerate(leg_points):
        # 基本速度と変動
        base = base_speeds[i]
        variation = speed_variations[i] * wind_variability
        
        # 乱数で揺らぎを加える
        leg_speeds = base + variation * np.random.randn(points)
        
        # 負の速度を修正
        leg_speeds = np.maximum(leg_speeds, 0.5)
        
        speeds.append(leg_speeds)
    
    # 速度の結合
    speeds = np.concatenate(speeds)
    
    # VMGの計算（単純化: 風上/風下時の速度成分）
    vmg = np.zeros_like(speeds)
    
    # 風上レグでのVMG計算
    upwind_mask = np.zeros_like(vmg, dtype=bool)
    upwind_mask[leg_points[0]:leg_points[0]+leg_points[1]] = True
    upwind_mask[leg_points[0]+leg_points[1]+leg_points[2]:leg_points[0]+leg_points[1]+leg_points[2]+leg_points[3]] = True
    
    vmg[upwind_mask] = speeds[upwind_mask] * np.cos(np.radians(headings[upwind_mask]))
    
    # 風下レグでのVMG計算
    downwind_mask = np.zeros_like(vmg, dtype=bool)
    downwind_mask[leg_points[0]+leg_points[1]:leg_points[0]+leg_points[1]+leg_points[2]] = True
    downwind_mask[leg_points[0]+leg_points[1]+leg_points[2]+leg_points[3]:leg_points[0]+leg_points[1]+leg_points[2]+leg_points[3]+leg_points[4]] = True
    
    vmg[downwind_mask] = -speeds[downwind_mask] * np.cos(np.radians(headings[downwind_mask]))
    
    # 負のVMGを修正
    vmg = np.abs(vmg)
    
    # トラックデータの作成
    track_data = pd.DataFrame({
        'timestamp': timestamps[:len(latitudes)],
        'latitude': latitudes,
        'longitude': longitudes,
        'speed': speeds,
        'vmg': vmg,
        'heading': headings
    })
    
    # 風データの生成
    wind_directions = np.zeros(len(timestamps))
    wind_speeds = np.zeros(len(timestamps))
    
    # 基本風向と風速
    base_direction = 0  # 北からの風
    base_speed = 10     # 10ノット
    
    # 風向変化の生成（徐々に変化）
    for i in range(len(timestamps)):
        # シヌソイダルな変化 + ランダムノイズ
        time_factor = i / len(timestamps)
        direction_change = (
            20 * wind_variability * np.sin(time_factor * 2 * np.pi) + 
            10 * wind_variability * np.sin(time_factor * 5 * np.pi) +
            5 * wind_variability * np.random.randn()
        )
        wind_directions[i] = (base_direction + direction_change) % 360
        
        # 風速の変化も同様に
        speed_change = (
            2 * wind_variability * np.sin(time_factor * 3 * np.pi) +
            1 * wind_variability * np.random.randn()
        )
        wind_speeds[i] = max(base_speed + speed_change, 1)  # 最低1ノット
    
    # 風データの作成
    wind_data = pd.DataFrame({
        'timestamp': timestamps[:len(wind_directions)],
        'wind_direction': wind_directions,
        'wind_speed': wind_speeds
    })
    
    # 競合艇データの生成
    # シンプルな競合艇（自艇より少し後ろを走る）
    competitor_latitudes = latitudes + 0.001 * np.random.randn(len(latitudes))
    competitor_longitudes = longitudes + 0.001 * np.random.randn(len(longitudes))
    competitor_speeds = speeds * (0.9 + 0.2 * np.random.rand(len(speeds)))
    
    competitor_data = pd.DataFrame({
        'timestamp': timestamps[:len(competitor_latitudes)],
        'boat_id': ['competitor_1'] * len(competitor_latitudes),
        'latitude': competitor_latitudes,
        'longitude': competitor_longitudes,
        'speed': competitor_speeds
    })
    
    return track_data, wind_data, competitor_data, course_data

def generate_triangle_dataset(fidelity, wind_variability):
    """三角コースのデータセット生成"""
    # 開始時刻（現在時刻の1時間前）
    start_time = datetime.now() - timedelta(hours=1)
    
    # データポイント数（精度によって調整）
    n_points = 500 * fidelity
    
    # コース情報
    course_data = {
        "course_type": "triangle",
        "marks": [
            {"name": "スタート/フィニッシュライン", "position": [35.6, 139.7]},
            {"name": "風上マーク", "position": [35.61, 139.7]},
            {"name": "ジャイブマーク", "position": [35.605, 139.71]},
            {"name": "風下マーク", "position": [35.6, 139.7]}
        ],
        "laps": 1,
        "start_direction": 0,
        "wind_conditions": {
            "avg_wind_direction": 0,  # 北からの風
            "avg_wind_speed": 12,     # 12ノット
            "wind_variability": wind_variability * 25  # 風の変動幅（度）
        }
    }
    
    # タイムスタンプの生成（1秒間隔）
    timestamps = [start_time + timedelta(seconds=i * (60 / fidelity)) for i in range(n_points)]
    
    # 三角コースのパターン（スタート→風上→リーチ→ブロードリーチ→フィニッシュ）
    # 各レグの割合
    leg_ratios = [0.05, 0.25, 0.25, 0.25, 0.2]  # スタート準備、風上、リーチ、ブロードリーチ、フィニッシュ
    leg_points = [int(ratio * n_points) for ratio in leg_ratios]
    
    # 位置データの生成
    latitudes = []
    longitudes = []
    headings = []
    
    # スタート準備
    start_points = leg_points[0]
    start_lat = np.linspace(35.595, 35.6, start_points)
    start_lon = np.full(start_points, 139.7)
    start_heading = np.full(start_points, 0)  # 北向き
    
    # 風上
    upwind_points = leg_points[1]
    upwind_lat = np.linspace(35.6, 35.61, upwind_points)
    
    # ジグザグパターンの生成（タック）
    zigzag_amplitude = 0.002 * wind_variability
    zigzag_frequency = 4 * fidelity
    upwind_lon = 139.7 + zigzag_amplitude * np.sin(np.linspace(0, zigzag_frequency * np.pi, upwind_points))
    
    # 風上時の艇の方向（ジグザグに合わせて変化）
    upwind_heading = 0 + 40 * np.sign(np.gradient(upwind_lon))
    
    # リーチ（風上マーク→ジャイブマーク）
    reach_points = leg_points[2]
    reach_lat = np.linspace(35.61, 35.605, reach_points)
    reach_lon = np.linspace(139.7, 139.71, reach_points)
    
    # リーチ時の艇の方向
    reach_heading = np.full(reach_points, 120)  # 南東向き
    
    # ブロードリーチ（ジャイブマーク→風下マーク）
    broad_reach_points = leg_points[3]
    broad_reach_lat = np.linspace(35.605, 35.6, broad_reach_points)
    broad_reach_lon = np.linspace(139.71, 139.7, broad_reach_points)
    
    # ブロードリーチ時の艇の方向
    broad_reach_heading = np.full(broad_reach_points, 240)  # 南西向き
    
    # フィニッシュ
    finish_points = leg_points[4]
    finish_lat = np.full(finish_points, 35.6)
    finish_lon = np.linspace(139.7, 139.705, finish_points)
    finish_heading = np.full(finish_points, 90)  # 東向き
    
    # 全てのセグメントを結合
    latitudes = np.concatenate([start_lat, upwind_lat, reach_lat, broad_reach_lat, finish_lat])
    longitudes = np.concatenate([start_lon, upwind_lon, reach_lon, broad_reach_lon, finish_lon])
    headings = np.concatenate([start_heading, upwind_heading, reach_heading, broad_reach_heading, finish_heading])
    
    # 速度の生成
    # 各レグでの基本速度と変動
    base_speeds = [3, 5.5, 7.5, 6.8, 4]  # 各レグの基本速度
    speed_variations = [1, 1.5, 2, 2.2, 1]  # 各レグの速度変動
    
    speeds = []
    
    for i, points in enumerate(leg_points):
        # 基本速度と変動
        base = base_speeds[i]
        variation = speed_variations[i] * wind_variability
        
        # 乱数で揺らぎを加える
        leg_speeds = base + variation * np.random.randn(points)
        
        # 負の速度を修正
        leg_speeds = np.maximum(leg_speeds, 0.5)
        
        speeds.append(leg_speeds)
    
    # 速度の結合
    speeds = np.concatenate(speeds)
    
    # VMGの計算（単純化）
    vmg = np.zeros_like(speeds)
    
    # 風上レグでのVMG計算
    upwind_mask = np.zeros_like(vmg, dtype=bool)
    upwind_mask[leg_points[0]:leg_points[0]+leg_points[1]] = True
    
    vmg[upwind_mask] = speeds[upwind_mask] * np.cos(np.radians(headings[upwind_mask]))
    
    # その他のレグでは単純に速度の一部としてVMGを設定
    non_upwind_mask = ~upwind_mask
    vmg[non_upwind_mask] = speeds[non_upwind_mask] * 0.5
    
    # トラックデータの作成
    track_data = pd.DataFrame({
        'timestamp': timestamps[:len(latitudes)],
        'latitude': latitudes,
        'longitude': longitudes,
        'speed': speeds,
        'vmg': np.abs(vmg),
        'heading': headings
    })
    
    # 風データの生成
    wind_directions = np.zeros(len(timestamps))
    wind_speeds = np.zeros(len(timestamps))
    
    # 基本風向と風速
    base_direction = 0  # 北からの風
    base_speed = 12     # 12ノット
    
    # 風向変化の生成（徐々に変化）
    for i in range(len(timestamps)):
        # シフトする風向（時間経過で右に振れる）
        time_factor = i / len(timestamps)
        direction_change = (
            15 * wind_variability * np.sin(time_factor * 2 * np.pi) + 
            8 * wind_variability * np.sin(time_factor * 4 * np.pi) +
            5 * wind_variability * np.random.randn()
        )
        wind_directions[i] = (base_direction + direction_change) % 360
        
        # 風速の変化も同様に
        speed_change = (
            2.5 * wind_variability * np.sin(time_factor * 3 * np.pi) +
            1.2 * wind_variability * np.random.randn()
        )
        wind_speeds[i] = max(base_speed + speed_change, 1)  # 最低1ノット
    
    # 風データの作成
    wind_data = pd.DataFrame({
        'timestamp': timestamps[:len(wind_directions)],
        'wind_direction': wind_directions,
        'wind_speed': wind_speeds
    })
    
    # 競合艇データの生成
    # シンプルな競合艇（自艇より少し前を走る）
    competitor_latitudes = latitudes - 0.001 * np.random.randn(len(latitudes))
    competitor_longitudes = longitudes - 0.001 * np.random.randn(len(longitudes))
    competitor_speeds = speeds * (1.05 + 0.15 * np.random.rand(len(speeds)))
    
    competitor_data = pd.DataFrame({
        'timestamp': timestamps[:len(competitor_latitudes)],
        'boat_id': ['competitor_1'] * len(competitor_latitudes),
        'latitude': competitor_latitudes,
        'longitude': competitor_longitudes,
        'speed': competitor_speeds
    })
    
    return track_data, wind_data, competitor_data, course_data

def generate_custom_dataset(fidelity, wind_variability):
    """カスタムコースのデータセット生成（ユーザー定義シナリオ）"""
    # 開始時刻（現在時刻の1時間前）
    start_time = datetime.now() - timedelta(hours=1)
    
    # データポイント数（精度によって調整）
    n_points = 500 * fidelity
    
    # より複雑なカスタムコース情報
    course_data = {
        "course_type": "custom",
        "marks": [
            {"name": "スタートライン", "position": [35.6, 139.7]},
            {"name": "マーク1", "position": [35.605, 139.71]},
            {"name": "マーク2", "position": [35.61, 139.705]},
            {"name": "マーク3", "position": [35.605, 139.695]},
            {"name": "フィニッシュライン", "position": [35.6, 139.7]}
        ],
        "laps": 1,
        "start_direction": 45,  # 北東スタート
        "wind_conditions": {
            "avg_wind_direction": 30,  # 北北東からの風
            "avg_wind_speed": 8,      # 8ノット
            "wind_variability": wind_variability * 40  # 風の変動幅（度）
        }
    }
    
    # タイムスタンプの生成
    timestamps = [start_time + timedelta(seconds=i * (60 / fidelity)) for i in range(n_points)]
    
    # カスタムコースのパターン
    leg_ratios = [0.1, 0.2, 0.25, 0.25, 0.2]  # スタート準備、レグ1、レグ2、レグ3、フィニッシュ
    leg_points = [int(ratio * n_points) for ratio in leg_ratios]
    
    # 位置データの生成
    latitudes = []
    longitudes = []
    headings = []
    
    # スタート準備
    start_points = leg_points[0]
    start_lat = np.linspace(35.595, 35.6, start_points)
    start_lon = np.linspace(139.695, 139.7, start_points)
    start_heading = np.full(start_points, 45)  # 北東向き
    
    # レグ1: スタート→マーク1
    leg1_points = leg_points[1]
    leg1_lat = np.linspace(35.6, 35.605, leg1_points)
    leg1_lon = np.linspace(139.7, 139.71, leg1_points)
    
    # レグ1の艇の方向（変動を加える）
    leg1_heading = np.full(leg1_points, 45)
    leg1_heading += 10 * wind_variability * np.sin(np.linspace(0, 3 * np.pi, leg1_points))
    
    # レグ2: マーク1→マーク2
    leg2_points = leg_points[2]
    leg2_lat = np.linspace(35.605, 35.61, leg2_points)
    leg2_lon = np.linspace(139.71, 139.705, leg2_points)
    
    # レグ2の艇の方向
    leg2_heading = np.full(leg2_points, 315)  # 北西向き
    leg2_heading += 15 * wind_variability * np.sin(np.linspace(0, 4 * np.pi, leg2_points))
    
    # レグ3: マーク2→マーク3
    leg3_points = leg_points[3]
    leg3_lat = np.linspace(35.61, 35.605, leg3_points)
    leg3_lon = np.linspace(139.705, 139.695, leg3_points)
    
    # レグ3の艇の方向
    leg3_heading = np.full(leg3_points, 225)  # 南西向き
    leg3_heading += 20 * wind_variability * np.sin(np.linspace(0, 5 * np.pi, leg3_points))
    
    # フィニッシュ: マーク3→フィニッシュ
    finish_points = leg_points[4]
    finish_lat = np.linspace(35.605, 35.6, finish_points)
    finish_lon = np.linspace(139.695, 139.7, finish_points)
    
    # フィニッシュの艇の方向
    finish_heading = np.full(finish_points, 135)  # 南東向き
    finish_heading += 5 * wind_variability * np.sin(np.linspace(0, 2 * np.pi, finish_points))
    
    # 全てのセグメントを結合
    latitudes = np.concatenate([start_lat, leg1_lat, leg2_lat, leg3_lat, finish_lat])
    longitudes = np.concatenate([start_lon, leg1_lon, leg2_lon, leg3_lon, finish_lon])
    headings = np.concatenate([start_heading, leg1_heading, leg2_heading, leg3_heading, finish_heading])
    
    # 各レグでの基本速度と変動
    base_speeds = [3, 5, 6.5, 7, 4.5]  # 各レグの基本速度
    speed_variations = [1, 1.2, 1.8, 1.5, 1.3]  # 各レグの速度変動
    
    speeds = []
    
    for i, points in enumerate(leg_points):
        # 基本速度と変動
        base = base_speeds[i]
        variation = speed_variations[i] * wind_variability
        
        # 風向との関係で速度変化（簡易化）
        leg_speeds = np.zeros(points)
        
        for j in range(points):
            # 風向と艇の向きの角度差
            if i == 0:  # スタート準備
                angle_diff = abs((30 - start_heading[j] + 180) % 360 - 180)
            elif i == 1:  # レグ1
                angle_diff = abs((30 - leg1_heading[j] + 180) % 360 - 180)
            elif i == 2:  # レグ2
                angle_diff = abs((30 - leg2_heading[j] + 180) % 360 - 180)
            elif i == 3:  # レグ3
                angle_diff = abs((30 - leg3_heading[j] + 180) % 360 - 180)
            else:  # フィニッシュ
                angle_diff = abs((30 - finish_heading[j] + 180) % 360 - 180)
            
            # 角度によるパフォーマンス係数
            if angle_diff < 30:  # 風上に近い
                perf = 0.7
            elif angle_diff > 150:  # 風下に近い
                perf = 0.9
            else:  # リーチング
                perf = 1.0
            
            # 速度の計算
            leg_speeds[j] = base * perf + variation * np.random.randn()
        
        # 負の速度を修正
        leg_speeds = np.maximum(leg_speeds, 0.5)
        
        speeds.append(leg_speeds)
    
    # 速度の結合
    speeds = np.concatenate(speeds)
    
    # VMGの計算（風向に対する速度成分）
    vmg = np.zeros_like(speeds)
    wind_direction_rad = np.radians(30)  # 基本風向
    
    for i in range(len(vmg)):
        # 艇の向きをラジアンに変換
        heading_rad = np.radians(headings[i])
        
        # 風向と艇の向きの角度差
        angle_diff = abs((wind_direction_rad - heading_rad + np.pi) % (2 * np.pi) - np.pi)
        
        # VMGの計算
        if angle_diff < np.pi / 2:  # 風上
            vmg[i] = speeds[i] * np.cos(angle_diff)
        else:  # 風下
            vmg[i] = speeds[i] * np.cos(np.pi - angle_diff)
    
    # トラックデータの作成
    track_data = pd.DataFrame({
        'timestamp': timestamps[:len(latitudes)],
        'latitude': latitudes,
        'longitude': longitudes,
        'speed': speeds,
        'vmg': np.abs(vmg),
        'heading': headings
    })
    
    # 風データの生成
    wind_directions = np.zeros(len(timestamps))
    wind_speeds = np.zeros(len(timestamps))
    
    # 基本風向と風速
    base_direction = 30  # 北北東からの風
    base_speed = 8      # 8ノット
    
    # 風向変化の生成（徐々に変化）
    for i in range(len(timestamps)):
        # より複雑な風向変化パターン
        time_factor = i / len(timestamps)
        
        # 前半と後半で風向変化パターンを変える
        if time_factor < 0.5:
            # 前半：右シフト傾向
            shift_trend = 20 * time_factor * wind_variability
        else:
            # 後半：左シフト傾向
            shift_trend = 20 * (1 - time_factor) * wind_variability
        
        # 風向変化の計算
        direction_change = (
            shift_trend +
            15 * wind_variability * np.sin(time_factor * 2 * np.pi) + 
            10 * wind_variability * np.sin(time_factor * 5 * np.pi) +
            7 * wind_variability * np.random.randn()
        )
        
        wind_directions[i] = (base_direction + direction_change) % 360
        
        # 風速の変化も複雑に
        # 中盤で風が弱まるパターン
        time_pattern = 1 - 0.4 * np.sin(np.pi * time_factor)
        
        speed_change = (
            base_speed * time_pattern * (0.8 + 0.4 * wind_variability) +
            2 * wind_variability * np.sin(time_factor * 3 * np.pi) +
            1.5 * wind_variability * np.random.randn()
        )
        
        wind_speeds[i] = max(speed_change, 0.5)  # 最低0.5ノット
    
    # 風データの作成
    wind_data = pd.DataFrame({
        'timestamp': timestamps[:len(wind_directions)],
        'wind_direction': wind_directions,
        'wind_speed': wind_speeds
    })
    
    # 競合艇データの生成
    # 複数の競合艇
    competitor_count = 2
    competitor_data_list = []
    
    for comp_id in range(competitor_count):
        # 各競合艇のパフォーマンス特性
        if comp_id == 0:
            # 競合艇1：風上が速い
            lat_offset = -0.0005 - 0.001 * np.random.rand(len(latitudes))
            lon_offset = 0.001 * np.random.randn(len(longitudes))
            speed_factor = 1.1 + 0.1 * np.random.rand(len(speeds))
            
            # 風上で特に速い
            upwind_mask = np.zeros_like(speeds, dtype=bool)
            upwind_mask[leg_points[0]:leg_points[0]+leg_points[1]] = True
            speed_factor[upwind_mask] *= 1.1
        else:
            # 競合艇2：風下が速い
            lat_offset = 0.0008 * np.random.randn(len(latitudes))
            lon_offset = -0.0005 - 0.001 * np.random.rand(len(longitudes))
            speed_factor = 0.95 + 0.1 * np.random.rand(len(speeds))
            
            # 風下で特に速い
            downwind_mask = np.zeros_like(speeds, dtype=bool)
            downwind_mask[leg_points[0]+leg_points[1]+leg_points[2]:] = True
            speed_factor[downwind_mask] *= 1.15
        
        # 競合艇のデータ生成
        comp_data = pd.DataFrame({
            'timestamp': timestamps[:len(latitudes)],
            'boat_id': [f'competitor_{comp_id+1}'] * len(latitudes),
            'latitude': latitudes + lat_offset,
            'longitude': longitudes + lon_offset,
            'speed': speeds * speed_factor
        })
        
        competitor_data_list.append(comp_data)
    
    # 競合艇データの結合
    competitor_data = pd.concat(competitor_data_list, ignore_index=True)
    
    return track_data, wind_data, competitor_data, course_data

if __name__ == "__main__":
    main()
