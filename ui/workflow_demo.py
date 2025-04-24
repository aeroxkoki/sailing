# -*- coding: utf-8 -*-
"""
統合分析ワークフローデモアプリケーション

このアプリケーションはセーリング戦略分析システムの分析ワークフローを
統合的に実行するためのデモです。
GPSトラックデータを読み込み、風推定、戦略検出、パフォーマンス分析などの
一連の分析ステップを実行できます。
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import sys
from datetime import datetime, timedelta
from io import StringIO
import time

# 親ディレクトリをパスに追加（インポート用）
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# 内部モジュールのインポート
from sailing_data_processor.analysis.analysis_parameters import ParametersManager, ParameterNamespace
from sailing_data_processor.analysis.analysis_cache import AnalysisCache
from sailing_data_processor.storage.browser_storage import BrowserStorage
from ui.components.workflow_components import complete_workflow_panel


def load_sample_data() -> pd.DataFrame:
    """サンプルデータをロード"""
    # サンプルデータの生成（実際のアプリケーションではファイルから読み込むなど）
    start_time = datetime.now() - timedelta(hours=1)
    n_points = 500
    
    # タイムスタンプの生成（1秒間隔）
    timestamps = [start_time + timedelta(seconds=i) for i in range(n_points)]
    
    # 緯度経度の生成（シンプルな周回コース - 四角形に近い）
    center_lat, center_lon = 35.6, 139.7  # 東京付近
    
    # コースの形状を定義（四角形のコーナー位置）
    corners = [
        (0.008, 0.008),   # 右上
        (0.008, -0.008),  # 右下
        (-0.008, -0.008), # 左下
        (-0.008, 0.008),  # 左上
    ]
    
    # 各辺のポイント数
    points_per_edge = n_points // 4
    
    latitudes = []
    longitudes = []
    
    # 四角形の各辺に沿ってポイントを配置
    for i in range(4):
        start_corner = corners[i]
        end_corner = corners[(i+1) % 4]
        
        for j in range(points_per_edge):
            # 線形補間
            ratio = j / points_per_edge
            dlat = start_corner[0] * (1 - ratio) + end_corner[0] * ratio
            dlon = start_corner[1] * (1 - ratio) + end_corner[1] * ratio
            
            latitudes.append(center_lat + dlat)
            longitudes.append(center_lon + dlon)
    
    # 余りのポイントを最後の辺に追加
    remaining = n_points - len(latitudes)
    for i in range(remaining):
        latitudes.append(center_lat + corners[0][0])
        longitudes.append(center_lon + corners[0][1])
    
    # 速度の生成（5〜8ノット、風向によって変動）
    speeds = []
    headings = []
    
    for i in range(n_points):
        # 現在のエッジを特定
        edge = min(i // points_per_edge, 3)
        
        # エッジごとの方向
        directions = [0, 90, 180, 270]  # 北、東、南、西
        heading = directions[edge]
        
        # 風に対する姿勢によって速度が変わる
        # 風上：遅い、風下：速い
        wind_angle = (heading - 225) % 360  # 風向225度と艇の向きの差
        rel_wind_effect = abs(wind_angle - 180) / 180.0  # 0:真風下、1:真風上
        
        speed = 7.5 - 2.5 * rel_wind_effect + 0.5 * np.random.randn()  # 5〜8ノット + ノイズ
        
        speeds.append(max(4.0, min(9.0, speed)))  # 4〜9ノットに制限
        headings.append(heading)
    
    # データフレームの作成
    data = {
        'timestamp': timestamps,
        'latitude': latitudes,
        'longitude': longitudes,
        'speed': speeds,
        'course': headings  # 進行方向
    }
    
    return pd.DataFrame(data)


def load_file_data(uploaded_file):
    """アップロードされたファイルからデータをロード"""
    if uploaded_file is None:
        return None
    
    try:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            # CSVファイルの読み込み
            df = pd.read_csv(uploaded_file)
            
            # 必須カラムのチェック
            required_columns = ['timestamp', 'latitude', 'longitude']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"必要なカラムがありません: {', '.join(missing_columns)}")
                return None
            
            # タイムスタンプ列の変換
            if 'timestamp' in df.columns:
                try:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                except:
                    st.error("タイムスタンプの形式が正しくありません")
                    return None
            
            # 速度がない場合は計算（簡易的な実装）
            if 'speed' not in df.columns:
                st.warning("速度データがありません。位置情報から概算します。")
                df = calculate_speed(df)
            
            # コースがない場合は計算
            if 'course' not in df.columns:
                st.warning("進行方向データがありません。位置情報から概算します。")
                df = calculate_course(df)
            
            return df
        
        elif file_extension in ['gpx', 'tcx', 'fit']:
            # GPX, TCX, FITファイルの処理はここに実装（今回は簡略化のため省略）
            st.error(f"{file_extension.upper()}ファイルの読み込みはこのデモではサポートされていません。")
            return None
        
        else:
            st.error(f"サポートされていないファイル形式です: {file_extension}")
            return None
            
    except Exception as e:
        st.error(f"ファイルの読み込み中にエラーが発生しました: {str(e)}")
        return None


def calculate_speed(df):
    """位置情報から速度を計算"""
    # タイムスタンプでソート
    df = df.sort_values('timestamp').copy()
    
    # 距離と時間差の計算
    df['prev_lat'] = df['latitude'].shift(1)
    df['prev_lon'] = df['longitude'].shift(1)
    df['time_diff'] = (df['timestamp'] - df['timestamp'].shift(1)).dt.total_seconds()
    
    # 最初の行はNaNになるので0に設定
    df.loc[df.index[0], 'time_diff'] = 0
    
    # ヒュベニの公式による距離計算
    def haversine(lat1, lon1, lat2, lon2):
        """2点間の距離をメートルで計算"""
        R = 6371000  # 地球の半径（メートル）
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        distance = R * c
        
        return distance
    
    # 各点間の距離を計算（メートル）
    distances = []
    for _, row in df.iterrows():
        if row['time_diff'] > 0 and not np.isnan(row['prev_lat']):
            distance = haversine(row['latitude'], row['longitude'], row['prev_lat'], row['prev_lon'])
            distances.append(distance)
        else:
            distances.append(0)
    
    df['distance'] = distances
    
    # 速度の計算（ノット、1ノット = 0.514444 m/s）
    df['speed'] = np.where(
        df['time_diff'] > 0,
        df['distance'] / df['time_diff'] / 0.514444,
        0
    )
    
    # 不要な列を削除
    df = df.drop(['prev_lat', 'prev_lon', 'distance'], axis=1)
    
    return df


def calculate_course(df):
    """位置情報から進行方向を計算"""
    # タイムスタンプでソート
    df = df.sort_values('timestamp').copy()
    
    # 前後の位置を使って方位を計算
    df['next_lat'] = df['latitude'].shift(-1)
    df['next_lon'] = df['longitude'].shift(-1)
    
    # 方位角の計算（北を0度として時計回り）
    def calculate_bearing(lat1, lon1, lat2, lon2):
        """2点間の方位角を計算"""
        if np.isnan(lat1) or np.isnan(lon1) or np.isnan(lat2) or np.isnan(lon2):
            return np.nan
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        dlon = lon2 - lon1
        
        y = np.sin(dlon) * np.cos(lat2)
        x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
        
        bearing = np.arctan2(y, x)
        bearing = np.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
    
    # 各点の方位を計算
    courses = []
    for _, row in df.iterrows():
        if not np.isnan(row['next_lat']):
            course = calculate_bearing(row['latitude'], row['longitude'], row['next_lat'], row['next_lon'])
            courses.append(course)
        else:
            # 最後の点は直前の方位を使用
            courses.append(courses[-1] if courses else 0)
    
    df['course'] = courses
    
    # 不要な列を削除
    df = df.drop(['next_lat', 'next_lon'], axis=1)
    
    return df


def initialize_parameters_and_cache():
    """パラメータとキャッシュの初期化"""
    # ストレージの初期化
    try:
        browser_storage = BrowserStorage(namespace="sailing_analysis")
    except Exception as e:
        st.warning(f"ブラウザストレージの初期化に失敗しました: {str(e)}。インメモリモードで実行します。")
        browser_storage = None
    
    # パラメータマネージャーの初期化
    params_manager = ParametersManager(storage_interface=browser_storage)
    
    # キャッシュの初期化
    cache = AnalysisCache(storage_interface=browser_storage)
    
    # ストレージからロード
    if browser_storage:
        params_manager.load_from_storage()
    
    return params_manager, cache


def main():
    # アプリケーション構成
    st.set_page_config(
        page_title="セーリング戦略分析 - 統合ワークフロー",
        page_icon="🚢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # タイトル
    st.title("セーリング戦略分析 - 統合ワークフロー")
    
    # サイドバー
    with st.sidebar:
        st.header("データ設定")
        
        # データソース選択
        data_source = st.radio(
            "データソース",
            ["サンプルデータ", "ファイルをアップロード"],
            index=0
        )
        
        # ファイルアップロード
        if data_source == "ファイルをアップロード":
            uploaded_file = st.file_uploader(
                "GPSトラックデータをアップロード",
                type=["csv", "gpx", "tcx", "fit"]
            )
            
            if uploaded_file is not None:
                st.success(f"ファイル '{uploaded_file.name}' がアップロードされました。")
                df = load_file_data(uploaded_file)
            else:
                st.info("ファイルをアップロードしてください。")
                df = None
        else:
            # サンプルデータの使用
            df = load_sample_data()
            st.success("サンプルデータをロードしました。")
        
        # データフレームの情報を表示
        if df is not None:
            st.write(f"データポイント数: {len(df)}")
            
            if 'timestamp' in df.columns:
                duration = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
                hours = int(duration / 3600)
                minutes = int((duration % 3600) / 60)
                seconds = int(duration % 60)
                st.write(f"データ期間: {hours}時間 {minutes}分 {seconds}秒")
    
    # メインエリア
    if df is not None:
        # パラメータとキャッシュの初期化
        params_manager, cache = initialize_parameters_and_cache()
        
        # 完全なワークフローパネルの表示
        complete_workflow_panel(df, params_manager, cache)
        
        # 定期的な自動保存
        if 'last_save_time' not in st.session_state:
            st.session_state.last_save_time = time.time()
        
        current_time = time.time()
        if current_time - st.session_state.last_save_time > 60:  # 1分ごとに保存
            if hasattr(params_manager, 'save_to_storage'):
                params_manager.save_to_storage()
                st.session_state.last_save_time = current_time
    
    else:
        # データがない場合の表示
        st.info("分析を開始するには、サイドバーからデータを選択またはアップロードしてください。")
        
        with st.expander("サポートされるファイル形式", expanded=False):
            st.write("""
            このデモアプリケーションでは、以下のファイル形式をサポートしています：
            
            - **CSV**: カンマ区切りのテキストファイル。必須カラムは `timestamp`, `latitude`, `longitude` です。
              `speed` と `course` も含まれていることが望ましいですが、必要に応じて計算できます。
            
            - **GPX、TCX、FIT**: 現在のデモではサポートされていませんが、完全なアプリケーションでは対応予定です。
            
            CSVファイルの例：
            ```
            timestamp,latitude,longitude,speed,course
            2023-01-01T12:00:00,35.65,139.75,5.2,45
            2023-01-01T12:00:10,35.652,139.753,5.5,48
            ...
            ```
            """)
        
        with st.expander("分析ワークフローについて", expanded=True):
            st.write("""
            ### 統合分析ワークフロー
            
            このデモアプリケーションは、セーリングのGPSトラックデータを分析するための一連のステップを提供します：
            
            1. **データ前処理**: タイムスタンプの整列、異常値の除去、基本的な検証を行います。
            
            2. **風向風速推定**: GPSデータから風の状況を推定します。風上/風下のパターンやタック/ジャイブなどのマニューバーから計算されます。
            
            3. **戦略ポイント検出**: 風向シフト、最適なタックポイント、レイラインなどの重要な戦略的判断ポイントを検出します。
            
            4. **パフォーマンス分析**: VMG（Velocity Made Good）、タック/ジャイブ効率などのパフォーマンス指標を計算し、総合的な評価を行います。
            
            5. **レポート作成**: 上記の分析結果を統合したレポートを生成します。
            
            各ステップには調整可能なパラメータがあり、分析の詳細度や焦点を変更できます。
            """)


if __name__ == "__main__":
    main()
