"""
ui.demo_gps_track_map

GPSトラック表示マップのデモアプリケーション。

このモジュールは、実装したGPSトラック表示マップ機能のデモンストレーションを行うStreamlitアプリケーションを提供します。
テストデータを読み込み、マップ上に表示します。
"""

import streamlit as st
import json
import pandas as pd
import numpy as np
import os
import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import random

# コンポーネントのインポート
from ui.components.reporting.map.map_component import gps_track_map_component
from sailing_data_processor.reporting.elements.map.map_utils import analyze_track_statistics

# ページ設定
st.set_page_config(
    page_title="GPSトラック表示マップデモ",
    page_icon="🗺️",
    layout="wide"
)

# タイトル
st.title("GPSトラック表示マップ - デモ")
st.markdown("""
このデモアプリケーションでは、GPSトラックデータを地図上に表示し、インタラクティブに操作することができます。
サンプルデータを選択するか、CSVファイルをアップロードして試してみてください。
""")

# ヘルパー関数
def load_sample_data(sample_type: str = "simple") -> List[Dict[str, Any]]:
    """
    サンプルデータを生成

    Parameters
    ----------
    sample_type : str, optional
        データタイプ, by default "simple"

    Returns
    -------
    List[Dict[str, Any]]
        GPSトラックデータ
    """
    if sample_type == "simple":
        # 横浜周辺の単純なルート
        base_lat = 35.4498
        base_lng = 139.6649
        num_points = 100
        track_data = []
        
        for i in range(num_points):
            # 円形のトラックを作成
            angle = 2 * np.pi * i / num_points
            radius = 0.01  # 約1km
            
            lat = base_lat + radius * np.cos(angle)
            lng = base_lng + radius * np.sin(angle)
            
            # 速度は5〜15ノット
            speed = 5 + 10 * np.sin(angle * 2)
            
            # 時刻は1分ごと
            timestamp = (datetime.datetime.now() + datetime.timedelta(minutes=i)).isoformat()
            
            track_data.append({
                "lat": lat,
                "lng": lng,
                "speed": speed,
                "heading": (i * 360 / num_points) % 360,
                "timestamp": timestamp
            })
        
        return track_data
    
    elif sample_type == "zigzag":
        # ジグザグパターン
        base_lat = 35.4498
        base_lng = 139.6649
        num_points = 100
        track_data = []
        
        for i in range(num_points):
            # ジグザグパターンを作成
            progress = i / num_points
            zigzag = 0.005 * np.sin(progress * 10 * np.pi)  # 約500mの振幅
            
            lat = base_lat + progress * 0.02 + zigzag  # 北に約2km
            lng = base_lng + zigzag
            
            # 速度は方向転換で変化
            speed = 10 - 5 * abs(np.cos(progress * 10 * np.pi))
            
            # 方向は頻繁に変化
            heading = 0 if np.cos(progress * 10 * np.pi) > 0 else 180
            
            # 時刻は1分ごと
            timestamp = (datetime.datetime.now() + datetime.timedelta(minutes=i)).isoformat()
            
            track_data.append({
                "lat": lat,
                "lng": lng,
                "speed": speed,
                "heading": heading,
                "timestamp": timestamp
            })
        
        return track_data
    
    elif sample_type == "random":
        # ランダムウォーク
        base_lat = 35.4498
        base_lng = 139.6649
        num_points = 100
        track_data = []
        
        current_lat = base_lat
        current_lng = base_lng
        
        for i in range(num_points):
            # ランダムな方向に移動
            current_lat += random.uniform(-0.0005, 0.0005)  # 約±50m
            current_lng += random.uniform(-0.0005, 0.0005)  # 約±50m
            
            # 速度は3〜20ノットでランダム
            speed = random.uniform(3, 20)
            
            # 方向はランダム
            heading = random.uniform(0, 360)
            
            # 時刻は1分ごと
            timestamp = (datetime.datetime.now() + datetime.timedelta(minutes=i)).isoformat()
            
            track_data.append({
                "lat": current_lat,
                "lng": current_lng,
                "speed": speed,
                "heading": heading,
                "timestamp": timestamp
            })
        
        return track_data
    
    else:
        # デフォルトは単純なルート
        return load_sample_data("simple")


def load_csv_data(file) -> List[Dict[str, Any]]:
    """
    CSVファイルからデータを読み込む

    Parameters
    ----------
    file : UploadedFile
        アップロードされたCSVファイル

    Returns
    -------
    List[Dict[str, Any]]
        GPSトラックデータ
    """
    try:
        df = pd.read_csv(file)
        
        # 必要なカラムの確認
        required_cols = ["lat", "lng"] if "lat" in df.columns and "lng" in df.columns else []
        required_cols = ["latitude", "longitude"] if "latitude" in df.columns and "longitude" in df.columns else required_cols
        required_cols = ["lat", "lon"] if "lat" in df.columns and "lon" in df.columns else required_cols
        
        if not required_cols:
            st.error("CSVファイルには緯度・経度情報が必要です。lat/lng、latitude/longitude、またはlat/lonというカラム名を使用してください。")
            return None
        
        # データの変換
        track_data = []
        for _, row in df.iterrows():
            point = {}
            for col in df.columns:
                point[col] = row[col]
            track_data.append(point)
        
        return track_data
    
    except Exception as e:
        st.error(f"CSVファイルの読み込みエラー: {str(e)}")
        return None


# データ選択UI
st.sidebar.header("データ選択")
data_source = st.sidebar.radio(
    "データソース",
    ["サンプルデータ", "ファイルアップロード"]
)

track_data = None

if data_source == "サンプルデータ":
    sample_type = st.sidebar.selectbox(
        "サンプルタイプ",
        ["simple", "zigzag", "random"],
        format_func=lambda x: {
            "simple": "単純なルート（円形）",
            "zigzag": "ジグザグパターン",
            "random": "ランダムウォーク"
        }.get(x, x)
    )
    
    track_data = load_sample_data(sample_type)
    
    if track_data:
        st.sidebar.success(f"{len(track_data)}ポイントのサンプルデータを読み込みました。")
else:
    uploaded_file = st.sidebar.file_uploader("GPSデータのCSVファイル", type=["csv"])
    
    if uploaded_file:
        track_data = load_csv_data(uploaded_file)
        
        if track_data:
            st.sidebar.success(f"{len(track_data)}ポイントのデータを読み込みました。")

# メインコンテンツ
if track_data:
    # GPSトラックマップコンポーネントの表示
    gps_track_map_component(track_data=track_data)
else:
    st.warning("データが選択されていません。サイドバーからサンプルデータを選択するか、CSVファイルをアップロードしてください。")
    
    # データ形式の説明
    st.markdown("""
    ## データ形式について
    
    CSVファイルには、少なくとも以下のいずれかの組み合わせのカラムが必要です：
    
    - `lat` と `lng`
    - `latitude` と `longitude`
    - `lat` と `lon`
    
    オプションで以下のカラムも利用できます：
    
    - `speed`: 速度（ノット）
    - `heading`: 進行方向（度）
    - `timestamp`: タイムスタンプ（ISO形式）
    
    ### サンプルCSV形式
    
    ```
    lat,lng,speed,heading,timestamp
    35.4498,139.6649,10.5,45.2,2023-01-01T12:00:00
    35.4499,139.6650,11.2,46.8,2023-01-01T12:01:00
    ...
    ```
    """)

# フッター
st.markdown("---")
st.markdown("GPSトラック表示マップデモ | セーリング戦略分析システム")
