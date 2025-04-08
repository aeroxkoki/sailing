
"""
ui.demo_wind_shift モジュール

風向シフト分析機能のデモアプリケーション
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os
import sys
import logging
from pathlib import Path

# 上位ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# アプリケーションモジュールのインポート
from sailing_data_processor.analysis.wind_shift_detector import WindShiftDetector
from sailing_data_processor.analysis.wind_pattern_analyzer import WindPatternAnalyzer
from sailing_data_processor.analysis.ml_models.shift_predictor import WindShiftPredictor
from sailing_data_processor.visualization.shift_visualization import ShiftVisualizer
from sailing_data_processor.importers.csv_importer import CSVImporter
from sailing_data_processor.importers.gpx_importer import GPXImporter

# UIコンポーネントのインポート
from ui.components.common.card import card
from ui.components.common.alert import info_alert, success_alert, warning_alert, error_alert
from ui.components.analysis.wind_shift_panel import wind_shift_analysis_panel

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataManager:
    """
    デモ用のデータ管理クラス
    
    風向データ、位置データなどを提供するシンプルなデータ管理クラス
    """
    
    def __init__(self):
        """初期化"""
        self.wind_data = None
        self.track_data = None
        self.course_info = None
    
    def load_data(self, file_path, data_type="wind"):
        """
        データをロード
        
        Parameters
        ----------
        file_path : str
            データファイルのパス
        data_type : str, optional
            データタイプ ("wind" または "track"), by default "wind"
            
        Returns
        -------
        bool
            ロードが成功したかどうか
        """
        try:
            # ファイル拡張子の判定
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.csv':
                # CSVファイルの読み込み
                importer = CSVImporter()
                data = importer.import_file(file_path)
                
                # タイムスタンプカラムの確認
                if 'timestamp' not in data.columns:
                    # 'time'カラムをタイムスタンプとして解釈
                    if 'time' in data.columns:
                        data['timestamp'] = pd.to_datetime(data['time'])
                    # 'date'カラムをタイムスタンプとして解釈
                    elif 'date' in data.columns:
                        data['timestamp'] = pd.to_datetime(data['date'])
                    else:
                        return False
                
                # 風向データの場合
                if data_type == "wind":
                    required_cols = ['timestamp', 'wind_direction']
                    
                    # 風向カラムの確認と変換
                    if 'wind_direction' not in data.columns:
                        # 'direction'カラムを風向として解釈
                        if 'direction' in data.columns:
                            data['wind_direction'] = data['direction']
                        # 'wind_dir'カラムを風向として解釈
                        elif 'wind_dir' in data.columns:
                            data['wind_direction'] = data['wind_dir']
                        else:
                            return False
                    
                    # 風速カラムの確認と変換
                    if 'wind_speed' not in data.columns:
                        # 'speed'カラムを風速として解釈
                        if 'speed' in data.columns:
                            data['wind_speed'] = data['speed']
                    
                    # 必要なカラムの検証
                    if not all(col in data.columns for col in required_cols):
                        return False
                    
                    self.wind_data = data
                
                # 位置データの場合
                elif data_type == "track":
                    required_cols = ['timestamp', 'latitude', 'longitude']
                    
                    # 位置カラムの確認と変換
                    if 'latitude' not in data.columns:
                        # 'lat'カラムを緯度として解釈
                        if 'lat' in data.columns:
                            data['latitude'] = data['lat']
                        else:
                            return False
                    
                    if 'longitude' not in data.columns:
                        # 'lon'または'long'カラムを経度として解釈
                        if 'lon' in data.columns:
                            data['longitude'] = data['lon']
                        elif 'long' in data.columns:
                            data['longitude'] = data['long']
                        else:
                            return False
                    
                    # 必要なカラムの検証
                    if not all(col in data.columns for col in required_cols):
                        return False
                    
                    self.track_data = data
                
                return True
            
            elif file_ext == '.gpx':
                # GPXファイルの読み込み
                importer = GPXImporter()
                data = importer.import_file(file_path)
                
                # トラックデータとして保存
                if data_type == "track":
                    if 'latitude' in data.columns and 'longitude' in data.columns and 'timestamp' in data.columns:
                        self.track_data = data
                        return True
                
                return False
            
            else:
                # サポートされていないファイル形式
                return False
                
        except Exception as e:
            logger.exception(f"データロード中にエラーが発生: {str(e)}")
            return False
    
    def get_wind_data(self):
        """
        風向データを取得
        
        Returns
        -------
        pd.DataFrame
            風向データ
        """
        return self.wind_data
    
    def get_track_data(self):
        """
        位置データを取得
        
        Returns
        -------
        pd.DataFrame
            位置データ
        """
        return self.track_data
    
    def get_course_info(self):
        """
        コース情報を取得
        
        Returns
        -------
        dict
            コース情報
        """
        return self.course_info
    
    def set_course_info(self, course_info):
        """
        コース情報を設定
        
        Parameters
        ----------
        course_info : dict
            コース情報
        """
        self.course_info = course_info
    
    def generate_sample_data(self, data_type="wind", sample_size=1000):
        """
        サンプルデータを生成
        
        Parameters
        ----------
        data_type : str, optional
            データタイプ ("wind" または "track"), by default "wind"
        sample_size : int, optional
            サンプルサイズ, by default 1000
            
        Returns
        -------
        bool
            生成が成功したかどうか
        """
        try:
            # 開始時間
            start_time = datetime.now() - timedelta(hours=6)
            
            # タイムスタンプの生成（等間隔）
            timestamps = [start_time + timedelta(seconds=i*20) for i in range(sample_size)]
            
            if data_type == "wind":
                # 風向データの生成
                # 基本風向
                base_direction = 180.0  # 南風
                
                # トレンド成分（徐々に右シフト）
                trend = np.linspace(0, 30, sample_size)
                
                # 周期成分（正弦波、30分周期）
                period_minutes = 30
                seconds_per_sample = 20
                samples_per_period = (period_minutes * 60) / seconds_per_sample
                period = np.sin(np.linspace(0, 2*np.pi * (sample_size / samples_per_period), sample_size)) * 15
                
                # ノイズ成分
                noise = np.random.normal(0, 3, sample_size)
                
                # 風向の組み合わせ
                wind_direction = (base_direction + trend + period + noise) % 360
                
                # 風速の生成（平均10ノット、変動あり）
                base_speed = 10.0
                speed_variation = np.sin(np.linspace(0, 4*np.pi, sample_size)) * 2
                speed_noise = np.random.normal(0, 0.5, sample_size)
                wind_speed = base_speed + speed_variation + speed_noise
                wind_speed = np.maximum(1.0, wind_speed)  # 最低1ノット
                
                # データフレームの作成
                self.wind_data = pd.DataFrame({
                    'timestamp': timestamps,
                    'wind_direction': wind_direction,
                    'wind_speed': wind_speed
                })
                
                return True
                
            elif data_type == "track":
                # 位置データの生成
                # 開始位置（東京湾付近）
                base_lat = 35.6
                base_lon = 139.8
                
                # コースの形状（上り下りのコース）
                course_len = sample_size
                laps = 3  # 周回数
                points_per_lap = course_len // laps
                
                # 各周回のコース形状を生成
                latitudes = []
                longitudes = []
                
                for lap in range(laps):
                    # 風上（北）へ向かう
                    up_leg = np.linspace(0, 0.01, points_per_lap // 2)
                    # 風下（南）へ向かう
                    down_leg = np.linspace(0.01, 0, points_per_lap // 2)
                    
                    # 緯度（南北方向）の変化
                    lat_change = np.concatenate([up_leg, down_leg])
                    latitudes.extend(base_lat + lat_change + lap * 0.001)  # 各周回で少しずつ北にシフト
                    
                    # 経度（東西方向）の変化（ジグザグパターン）
                    lon_change = np.sin(np.linspace(0, 2*np.pi, points_per_lap)) * 0.005
                    longitudes.extend(base_lon + lon_change)
                
                # 残りのポイントを調整
                remaining = course_len - len(latitudes)
                if remaining > 0:
                    latitudes.extend([latitudes[-1]] * remaining)
                    longitudes.extend([longitudes[-1]] * remaining)
                
                # 海上での速度（2-6ノット）
                speed = np.random.uniform(2, 6, sample_size)
                
                # 航行方向（コースに沿った方向）
                course = np.zeros(sample_size)
                for i in range(1, sample_size):
                    # 2点間の方位角を計算
                    dx = longitudes[i] - longitudes[i-1]
                    dy = latitudes[i] - latitudes[i-1]
                    course[i] = (np.degrees(np.arctan2(dx, dy)) + 360) % 360
                
                # データフレームの作成
                self.track_data = pd.DataFrame({
                    'timestamp': timestamps,
                    'latitude': latitudes,
                    'longitude': longitudes,
                    'speed': speed,
                    'course': course
                })
                
                # コース情報の生成
                marks = []
                # 風上マーク
                marks.append({
                    "name": "風上マーク",
                    "type": "mark",
                    "position": (base_lat + 0.01, base_lon)
                })
                # 風下マーク
                marks.append({
                    "name": "風下マーク",
                    "type": "mark",
                    "position": (base_lat, base_lon)
                })
                
                # 戦略的ポイント（各マークの周辺）
                strategic_points = []
                for mark in marks:
                    lat, lon = mark["position"]
                    # マーク手前のポイント
                    strategic_points.append({
                        "name": f"{mark['name']}手前",
                        "type": "strategic",
                        "position": (lat - 0.002, lon)
                    })
                
                self.course_info = {
                    "marks": marks,
                    "strategic_points": strategic_points
                }
                
                return True
            
            return False
            
        except Exception as e:
            logger.exception(f"サンプルデータ生成中にエラーが発生: {str(e)}")
            return False

def main():
    """アプリケーションのメインエントリーポイント"""
    # ページ設定
    st.set_page_config(
        page_title="風向シフト分析デモ",
        page_icon="🌬️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # サイドバー
    with st.sidebar:
        st.title("風向シフト分析")
        st.markdown("セーリングデータから風向シフトを検出・分析するデモアプリケーションです。")
        
        # セッション状態の初期化
        if "data_manager" not in st.session_state:
            st.session_state.data_manager = DataManager()
        
        # データ読み込みセクション
        st.subheader("データの読み込み")
        
        # データ読み込み方法の選択
        data_load_method = st.radio(
            "データ読み込み方法",
            options=["サンプルデータを生成", "ファイルから読み込み"],
            index=0
        )
        
        if data_load_method == "サンプルデータを生成":
            # サンプルデータ生成
            if st.button("風向データと位置データを生成", type="primary"):
                data_manager = st.session_state.data_manager
                
                with st.spinner("サンプルデータを生成中..."):
                    # 風向データの生成
                    wind_success = data_manager.generate_sample_data(data_type="wind", sample_size=1080)  # 6時間分（20秒間隔）
                    
                    # 位置データの生成
                    track_success = data_manager.generate_sample_data(data_type="track", sample_size=1080)
                    
                    if wind_success and track_success:
                        st.success("サンプルデータの生成が完了しました。")
                    else:
                        st.error("サンプルデータの生成中にエラーが発生しました。")
        
        else:
            # ファイルからの読み込み
            wind_file = st.file_uploader(
                "風向データファイル (.csv)",
                type=["csv"],
                help="風向・風速データを含むCSVファイル"
            )
            
            track_file = st.file_uploader(
                "位置データファイル (.csv, .gpx)",
                type=["csv", "gpx"],
                help="緯度・経度データを含むファイル"
            )
            
            if wind_file is not None:
                # 一時ファイルとして保存
                with open("temp_wind.csv", "wb") as f:
                    f.write(wind_file.getbuffer())
                
                # データ読み込み
                data_manager = st.session_state.data_manager
                if data_manager.load_data("temp_wind.csv", data_type="wind"):
                    st.success("風向データを読み込みました。")
                else:
                    st.error("風向データの読み込みに失敗しました。ファイル形式を確認してください。")
            
            if track_file is not None:
                # ファイル拡張子の取得
                extension = track_file.name.split(".")[-1].lower()
                temp_file = f"temp_track.{extension}"
                
                # 一時ファイルとして保存
                with open(temp_file, "wb") as f:
                    f.write(track_file.getbuffer())
                
                # データ読み込み
                data_manager = st.session_state.data_manager
                if data_manager.load_data(temp_file, data_type="track"):
                    st.success("位置データを読み込みました。")
                else:
                    st.error("位置データの読み込みに失敗しました。ファイル形式を確認してください。")
        
        # データ情報の表示
        data_manager = st.session_state.data_manager
        wind_data = data_manager.get_wind_data()
        track_data = data_manager.get_track_data()
        
        st.subheader("読み込み済みデータ")
        
        if wind_data is not None:
            st.info(f"風向データ: {len(wind_data)} レコード ({wind_data['timestamp'].min().strftime('%Y-%m-%d %H:%M')} - {wind_data['timestamp'].max().strftime('%Y-%m-%d %H:%M')})")
        else:
            st.warning("風向データが読み込まれていません。")
        
        if track_data is not None:
            st.info(f"位置データ: {len(track_data)} レコード ({track_data['timestamp'].min().strftime('%Y-%m-%d %H:%M')} - {track_data['timestamp'].max().strftime('%Y-%m-%d %H:%M')})")
        else:
            st.warning("位置データが読み込まれていません。")
    
    # メインコンテンツエリア
    st.title("風向シフト分析デモ")
    
    # データの有無を確認
    data_manager = st.session_state.data_manager
    wind_data = data_manager.get_wind_data()
    
    if wind_data is None:
        # データがない場合の表示
        st.warning("風向データが読み込まれていません。サイドバーからデータを読み込んでください。")
        
        # サンプル画像の表示
        st.subheader("風向シフト分析例")
        st.markdown("""
        このデモアプリケーションでは、以下のような分析が可能です：
        
        - GPSデータに基づく風向シフトの高精度検出
        - 機械学習を用いたシフト予測
        - 風向パターンの分析と可視化
        - 地理的な風向変化の分析
        
        サイドバーからサンプルデータを生成するか、独自のデータをアップロードしてお試しください。
        """)
        
        # カラム分割
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 風向の時系列と検出されたシフト")
            st.image("https://via.placeholder.com/800x400?text=風向時系列グラフ例", use_column_width=True)
        
        with col2:
            st.markdown("#### 風配図とシフトパターン")
            st.image("https://via.placeholder.com/800x400?text=風配図例", use_column_width=True)
    
    else:
        # データがある場合は風向シフト分析パネルを表示
        # 検出器と予測器のインスタンス化
        if "detector" not in st.session_state:
            st.session_state.detector = WindShiftDetector()
        
        if "predictor" not in st.session_state:
            st.session_state.predictor = None  # 初期状態では予測器はnull
        
        # パネルの表示
        wind_shift_analysis_panel(
            detector=st.session_state.detector,
            predictor=st.session_state.predictor,
            data_manager=data_manager,
            key_prefix="main"
        )

# アプリケーションのエントリーポイント
if __name__ == "__main__":
    main()
