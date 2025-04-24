# -*- coding: utf-8 -*-
"""
ui.app_mvp

セーリング戦略分析システムのMVP（Minimum Viable Product）バージョン
ユーザー中心UIを持つシンプルなワンページアプリケーション
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import logging
import pathlib
from streamlit_folium import folium_static
import folium
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import tempfile
from io import StringIO
import base64

# プロジェクトのルートディレクトリをパスに追加
current_dir = pathlib.Path(__file__).parent
project_root = current_dir.parent.absolute()
sys.path.insert(0, str(project_root))

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app_mvp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# セーリングデータ処理モジュールのインポート
try:
    from sailing_data_processor.wind_estimator import WindEstimator
    from sailing_data_processor.strategy.detector import StrategyDetector
    from sailing_data_processor.importers.gpx_importer import GPXImporter
    from sailing_data_processor.importers.csv_importer import CSVImporter
    from sailing_data_processor.data_model.container import GPSDataContainer
    logger.info("コア機能のインポートに成功しました")
except ImportError as e:
    logger.error(f"モジュールのインポートに失敗しました: {e}")
    # エラー表示用のダミー関数を準備
    WindEstimator = None
    StrategyDetector = None

# ページ設定
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# セッション状態の初期化
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if 'gps_data' not in st.session_state:
    st.session_state.gps_data = None

if 'estimated_wind' not in st.session_state:
    st.session_state.estimated_wind = None

if 'strategy_points' not in st.session_state:
    st.session_state.strategy_points = None

if 'display_options' not in st.session_state:
    st.session_state.display_options = {
        'show_wind': True,
        'show_strategy': True,
        'basic_mode': True
    }

# GPXファイル処理関数
def process_gpx_file(uploaded_file):
    """
    GPXファイルを処理してデータフレームを返す
    
    Parameters
    ----------
    uploaded_file : UploadedFile
        アップロードされたGPXファイル
    
    Returns
    -------
    tuple
        (成功時はDataFrame、失敗時はNone), エラーメッセージ(成功時はNone)
    """
    try:
        # インポーターを使用
        importer = GPXImporter()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gpx') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # ファイルを処理
        result = importer.import_file(tmp_path)
        
        # 一時ファイルを削除
        os.unlink(tmp_path)
        
        if result.success:
            return result.data, None
        else:
            return None, result.error_message
    except Exception as e:
        logger.error(f"GPXファイル処理エラー: {e}")
        return None, f"GPXファイルの処理に失敗しました: {str(e)}"

# CSVファイル処理関数
def process_csv_file(uploaded_file):
    """
    CSVファイルを処理してデータフレームを返す
    
    Parameters
    ----------
    uploaded_file : UploadedFile
        アップロードされたCSVファイル
    
    Returns
    -------
    tuple
        (成功時はDataFrame、失敗時はNone), エラーメッセージ(成功時はNone)
    """
    try:
        # インポーターを使用
        importer = CSVImporter()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # ファイルを処理
        result = importer.import_file(tmp_path)
        
        # 一時ファイルを削除
        os.unlink(tmp_path)
        
        if result.success:
            return result.data, None
        else:
            return None, result.error_message
    except Exception as e:
        logger.error(f"CSVファイル処理エラー: {e}")
        return None, f"CSVファイルの処理に失敗しました: {str(e)}"

# 風向風速を推定する関数
def estimate_wind(gps_data):
    """
    GPSデータから風向風速を推定
    
    Parameters
    ----------
    gps_data : pd.DataFrame
        GPSデータを含むデータフレーム
    
    Returns
    -------
    dict
        風推定の結果と信頼度
    """
    if WindEstimator is None:
        return {"error": "WindEstimatorモジュールがロードできませんでした"}
    
    try:
        # 風推定器の初期化
        estimator = WindEstimator()
        
        # データの準備
        if 'timestamp' not in gps_data.columns:
            gps_data['timestamp'] = pd.date_range(start='2025-01-01', periods=len(gps_data), freq='1S')
            
        required_columns = ['latitude', 'longitude', 'speed', 'course']
        missing_columns = [col for col in required_columns if col not in gps_data.columns]
        
        if missing_columns:
            return {"error": f"風推定に必要なカラムがありません: {', '.join(missing_columns)}"}
        
        # 風推定の実行
        wind_result = estimator.estimate_wind_field(gps_data)
        
        if wind_result:
            return wind_result
        else:
            return {"error": "風推定に失敗しました"}
    except Exception as e:
        logger.error(f"風推定エラー: {e}")
        return {"error": f"風推定処理でエラーが発生しました: {str(e)}"}

# 戦略ポイントを検出する関数
def detect_strategy_points(gps_data, wind_data):
    """
    GPSデータと風データから戦略ポイントを検出
    
    Parameters
    ----------
    gps_data : pd.DataFrame
        GPSデータを含むデータフレーム
    wind_data : dict
        風推定の結果
        
    Returns
    -------
    list
        検出された戦略ポイントのリスト
    """
    if StrategyDetector is None:
        return {"error": "StrategyDetectorモジュールがロードできませんでした"}
    
    try:
        # 戦略検出器の初期化
        detector = StrategyDetector()
        
        # 戦略ポイント検出の実行
        strategy_points = detector.detect_strategy_points(gps_data, wind_data)
        
        if strategy_points:
            return strategy_points
        else:
            return {"error": "戦略ポイントの検出に失敗しました"}
    except Exception as e:
        logger.error(f"戦略検出エラー: {e}")
        return {"error": f"戦略ポイント検出でエラーが発生しました: {str(e)}"}

# サンプルデータを生成する関数
def generate_sample_data():
    """サンプルのGPSデータを生成"""
    # サンプルデータを生成
    num_points = 200
    start_time = pd.Timestamp('2025-01-01 10:00:00')
    timestamps = [start_time + pd.Timedelta(seconds=i*10) for i in range(num_points)]
    
    # 基本位置とランダムなコースを設定
    base_lat, base_lon = 35.45, 139.65
    
    # コース変化（タックを含む）を生成
    course = []
    current_course = 45
    for i in range(num_points):
        if i > 0 and i % 50 == 0:  # タック
            current_course = (current_course + 180) % 360
        
        # コースにランダムな変動を加える
        course.append(current_course + np.random.normal(0, 2))
    
    # 緯度経度を生成
    latitude = [base_lat]
    longitude = [base_lon]
    
    for i in range(1, num_points):
        heading_rad = np.radians(course[i-1])
        speed = 5 + np.random.normal(0, 0.5)  # 5m/sを平均とした速度
        
        # 前の位置から計算
        prev_lat, prev_lon = latitude[i-1], longitude[i-1]
        
        # 簡易的な位置計算（短距離のみ有効）
        dlat = speed * np.cos(heading_rad) * 0.00001  # 緯度の変化
        dlon = speed * np.sin(heading_rad) * 0.00001  # 経度の変化
        
        latitude.append(prev_lat + dlat)
        longitude.append(prev_lon + dlon)
    
    # 風向と風速を生成
    wind_direction = [90 + np.random.normal(0, 5) for _ in range(num_points)]
    wind_speed = [10 + np.random.normal(0, 1) for _ in range(num_points)]
    
    # データフレームを作成
    sample_data = pd.DataFrame({
        'timestamp': timestamps,
        'latitude': latitude,
        'longitude': longitude,
        'course': course,
        'speed': [5 + np.random.normal(0, 0.5) for _ in range(num_points)],
        'wind_direction': wind_direction,
        'wind_speed': wind_speed
    })
    
    return sample_data

# UIコンポーネント：ヘッダーセクション
def render_header():
    """アプリケーションのヘッダーを表示"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title('セーリング戦略分析システム')
    
    with col2:
        if st.session_state.data_loaded:
            st.success('データ読み込み済み')
            # 追加情報（データポイント数など）
            points = len(st.session_state.gps_data)
            st.caption(f"データポイント数: {points:,}")

# UIコンポーネント：サイドバー
def render_sidebar():
    """サイドバーのUIコンポーネントを表示"""
    with st.sidebar:
        st.title("セーリング戦略分析")
        
        # モード切替
        advanced_mode = st.toggle("詳細モードを表示", 
                                 value=not st.session_state.display_options['basic_mode'],
                                 help="詳細な分析機能とオプションを表示します")
        st.session_state.display_options['basic_mode'] = not advanced_mode
        
        # ファイルアップロード
        st.subheader("GPSデータをアップロード")
        uploaded_file = st.file_uploader(
            "サポートするファイル形式",
            type=["csv", "gpx", "tcx", "fit"],
            help="GPSデータを含むファイルをアップロードしてください"
        )
        
        if uploaded_file is not None:
            file_details = {"Filename": uploaded_file.name, "FileType": uploaded_file.type, 
                           "FileSize": f"{uploaded_file.size / 1024:.2f} KB"}
            st.write(file_details)
            
            # 処理ボタン
            if st.button("データを処理", type="primary"):
                with st.spinner('データを処理中...'):
                    # ファイルの種類に応じた処理
                    file_extension = uploaded_file.name.split('.')[-1].lower()
                    
                    if file_extension == 'gpx':
                        df, error = process_gpx_file(uploaded_file)
                    elif file_extension == 'csv':
                        df, error = process_csv_file(uploaded_file)
                    else:
                        df, error = None, f"未対応のファイル形式です: {file_extension}"
                    
                    if error:
                        st.error(error)
                    else:
                        # データをセッションに保存
                        st.session_state.gps_data = df
                        st.session_state.data_loaded = True
                        
                        # 風推定と戦略ポイント検出
                        with st.spinner('風向風速を推定中...'):
                            st.session_state.estimated_wind = estimate_wind(df)
                        
                        with st.spinner('戦略ポイントを検出中...'):
                            st.session_state.strategy_points = detect_strategy_points(
                                df, st.session_state.estimated_wind
                            )
                        
                        st.success('データ処理が完了しました！')
                        st.experimental_rerun()
        
        # サンプルデータボタン
        if not st.session_state.data_loaded:
            if st.button("サンプルデータを使用"):
                with st.spinner('サンプルデータを生成中...'):
                    # サンプルデータを生成
                    sample_data = generate_sample_data()
                    
                    # データをセッションに保存
                    st.session_state.gps_data = sample_data
                    st.session_state.data_loaded = True
                    
                    # 風推定と戦略ポイント検出（サンプルデータには既に含まれているが、処理の例として実行）
                    with st.spinner('風向風速を推定中...'):
                        st.session_state.estimated_wind = {
                            "direction": sample_data['wind_direction'].mean(),
                            "speed": sample_data['wind_speed'].mean(),
                            "confidence": 0.8
                        }
                    
                    with st.spinner('戦略ポイントを検出中...'):
                        # サンプル戦略ポイント
                        st.session_state.strategy_points = [
                            {"type": "tack", "position": {"latitude": lat, "longitude": lon}, 
                             "timestamp": time, "importance": 0.8,
                             "details": {"angle_change": "90°", "speed_loss": "0.5 knots"}}
                            for lat, lon, time in zip(
                                sample_data['latitude'][50::50],
                                sample_data['longitude'][50::50],
                                sample_data['timestamp'][50::50]
                            )
                        ]
                    
                    st.success('サンプルデータを読み込みました！')
                    st.experimental_rerun()
        
        # データロード後の表示設定
        if st.session_state.data_loaded:
            st.subheader("表示設定")
            st.checkbox("風向風速を表示", value=st.session_state.display_options['show_wind'], 
                       key="show_wind", on_change=update_display_option, args=('show_wind',))
            st.checkbox("戦略ポイントを表示", value=st.session_state.display_options['show_strategy'], 
                       key="show_strategy", on_change=update_display_option, args=('show_strategy',))
        
        # ヘルプへのリンク
        st.markdown("---")
        st.markdown("[ヘルプ & ドキュメント](https://example.com)")

def update_display_option(option_name):
    """表示オプションの更新コールバック"""
    st.session_state.display_options[option_name] = st.session_state[option_name]

# UIコンポーネント：マップビュー
def render_map_view():
    """マップビューを表示"""
    st.subheader("GPSトラックマップ")
    
    if st.session_state.data_loaded and st.session_state.gps_data is not None:
        # マップオブジェクトの作成
        center = get_map_center(st.session_state.gps_data)
        m = folium.Map(location=center, zoom_start=14, control_scale=True)
        
        # GPSトラックの表示
        positions = list(zip(st.session_state.gps_data['latitude'], 
                            st.session_state.gps_data['longitude']))
        
        # トラックラインを追加
        folium.PolyLine(
            positions,
            color='blue',
            weight=3,
            opacity=0.7,
            tooltip="GPSトラック"
        ).add_to(m)
        
        # 始点と終点のマーカー
        if positions:
            # スタートマーカー
            folium.Marker(
                positions[0],
                tooltip="スタート",
                icon=folium.Icon(color='green', icon='play', prefix='fa')
            ).add_to(m)
            
            # ゴールマーカー
            folium.Marker(
                positions[-1],
                tooltip="ゴール",
                icon=folium.Icon(color='red', icon='stop', prefix='fa')
            ).add_to(m)
        
        # 風向風速の表示
        if st.session_state.display_options['show_wind'] and st.session_state.estimated_wind:
            if 'error' not in st.session_state.estimated_wind:
                # 全体の風向風速を表示
                wind_direction = st.session_state.estimated_wind.get('direction', 0)
                wind_speed = st.session_state.estimated_wind.get('speed', 0)
                
                # 風向を示す矢印を追加（簡易表示）
                arrow_points = []
                for i in range(0, len(positions), max(1, len(positions) // 10)):
                    lat, lon = positions[i]
                    
                    # 矢印マーカーの追加
                    folium.Marker(
                        [lat, lon],
                        tooltip=f"風向: {wind_direction:.1f}°, 風速: {wind_speed:.1f}ノット",
                        icon=folium.DivIcon(
                            icon_size=(30, 30),
                            icon_anchor=(15, 15),
                            html=f'''
                                <div style="
                                    transform: rotate({90 - wind_direction}deg);
                                    font-size: {10 + wind_speed/2}px;
                                    color: blue;
                                ">➤</div>
                            '''
                        )
                    ).add_to(m)
        
        # 戦略ポイントの表示
        if st.session_state.display_options['show_strategy'] and st.session_state.strategy_points:
            if 'error' not in st.session_state.strategy_points:
                for point in st.session_state.strategy_points:
                    point_type = point.get('type', 'other')
                    position = point.get('position', {})
                    lat = position.get('latitude', 0)
                    lon = position.get('longitude', 0)
                    
                    # アイコン設定
                    icon_mapping = {
                        'tack': {'icon': 'exchange', 'color': 'blue'},
                        'jibe': {'icon': 'refresh', 'color': 'purple'},
                        'layline': {'icon': 'arrows', 'color': 'green'},
                        'wind_shift': {'icon': 'random', 'color': 'orange'},
                        'other': {'icon': 'info', 'color': 'gray'}
                    }
                    
                    icon_config = icon_mapping.get(point_type, icon_mapping['other'])
                    
                    # 詳細情報
                    details = point.get('details', {})
                    detail_html = '<dl>'
                    for key, value in details.items():
                        detail_html += f'<dt>{key}</dt><dd>{value}</dd>'
                    detail_html += '</dl>'
                    
                    # ポップアップの内容
                    popup_html = f'''
                    <div style="min-width: 200px;">
                        <h4>{point_type.title()} ポイント</h4>
                        <p>重要度: {point.get("importance", 0):.2f}</p>
                        {detail_html}
                    </div>
                    '''
                    
                    # マーカーを追加
                    folium.Marker(
                        [lat, lon],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=f"戦略ポイント: {point_type}",
                        icon=folium.Icon(
                            color=icon_config['color'],
                            icon=icon_config['icon'],
                            prefix='fa'
                        )
                    ).add_to(m)
        
        # マップの表示
        folium_static(m, width=800, height=600)
    else:
        # データがない場合のプレースホルダ
        st.info("GPSデータがありません。左側のサイドバーからデータをアップロードするか、サンプルデータを使用してください。")
        m = folium.Map(location=[35.45, 139.65], zoom_start=12)
        folium_static(m, width=800, height=600)

def get_map_center(gps_data):
    """GPSデータの中心座標を計算"""
    if 'latitude' in gps_data.columns and 'longitude' in gps_data.columns:
        center_lat = gps_data['latitude'].mean()
        center_lon = gps_data['longitude'].mean()
        return [center_lat, center_lon]
    else:
        return [35.45, 139.65]  # デフォルト座標（東京湾）

# UIコンポーネント：分析パネル
def render_analysis_panel():
    """分析パネルのUIコンポーネントを表示"""
    if st.session_state.data_loaded and st.session_state.gps_data is not None:
        # タブスタイルの分析パネル
        tabs = st.tabs(["基本パフォーマンス", "戦略分析", "風分析"])
        
        with tabs[0]:
            render_performance_analysis()
        
        with tabs[1]:
            render_strategy_analysis()
        
        with tabs[2]:
            render_wind_analysis()
        
        # 詳細モードの追加コンポーネント
        if not st.session_state.display_options['basic_mode']:
            st.subheader("詳細分析")
            render_advanced_analysis()
    else:
        st.info("データがロードされていません。分析を行うにはデータが必要です。")

def render_performance_analysis():
    """基本パフォーマンス分析を表示"""
    st.subheader("速度と効率の分析")
    
    if 'speed' in st.session_state.gps_data.columns:
        # 速度の時系列グラフ
        speed_data = st.session_state.gps_data[['timestamp', 'speed']].copy()
        
        # m/sをノットに変換（必要に応じて）
        if speed_data['speed'].mean() > 0.1:  # 既にノットの場合は変換不要
            speed_data['speed_knots'] = speed_data['speed'] * 1.94384  # m/s to knots
            y_column = 'speed_knots'
            y_label = "速度 (ノット)"
        else:
            y_column = 'speed'
            y_label = "速度 (m/s)"
        
        fig = px.line(
            speed_data, 
            x='timestamp', 
            y=y_column,
            title="速度の時系列変化",
            labels={'timestamp': '時間', y_column: y_label}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 速度の分布ヒストグラム
        fig = px.histogram(
            speed_data, 
            x=y_column,
            nbins=20,
            title="速度の分布",
            labels={y_column: y_label, 'count': '頻度'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # サマリー統計
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("平均速度", f"{speed_data[y_column].mean():.2f}")
        with col2:
            st.metric("最高速度", f"{speed_data[y_column].max():.2f}")
        with col3:
            st.metric("中央速度", f"{speed_data[y_column].median():.2f}")
    else:
        st.info("速度データがありません。")

def render_strategy_analysis():
    """戦略分析を表示"""
    st.subheader("戦略ポイントの分析")
    
    if st.session_state.strategy_points and 'error' not in st.session_state.strategy_points:
        # 戦略ポイントの種類をカウント
        point_types = {}
        
        for point in st.session_state.strategy_points:
            point_type = point.get('type', 'その他')
            if point_type in point_types:
                point_types[point_type] += 1
            else:
                point_types[point_type] = 1
        
        # 戦略ポイントの種類の分布
        fig = px.pie(
            values=list(point_types.values()),
            names=list(point_types.keys()),
            title="戦略ポイントの種類"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 戦略ポイントの詳細テーブル
        if st.checkbox("戦略ポイントの詳細を表示"):
            # 表示用のデータを整形
            strategy_data = []
            
            for i, point in enumerate(st.session_state.strategy_points):
                # 基本情報
                point_info = {
                    "ID": i + 1,
                    "種類": point.get('type', 'その他'),
                    "重要度": f"{point.get('importance', 0):.2f}"
                }
                
                # 位置情報
                position = point.get('position', {})
                point_info["緯度"] = position.get('latitude', '-')
                point_info["経度"] = position.get('longitude', '-')
                
                # タイムスタンプ
                if 'timestamp' in point:
                    if isinstance(point['timestamp'], pd.Timestamp):
                        point_info["時刻"] = point['timestamp'].strftime('%H:%M:%S')
                    else:
                        point_info["時刻"] = str(point['timestamp'])
                else:
                    point_info["時刻"] = '-'
                
                # 詳細情報
                details = point.get('details', {})
                for key, value in details.items():
                    point_info[key] = value
                
                strategy_data.append(point_info)
            
            # データフレームとして表示
            if strategy_data:
                st.dataframe(pd.DataFrame(strategy_data))
            else:
                st.info("詳細データがありません。")
    else:
        st.info("戦略ポイントがありません。")

def render_wind_analysis():
    """風分析を表示"""
    st.subheader("風向風速の分析")
    
    if st.session_state.estimated_wind and 'error' not in st.session_state.estimated_wind:
        # 風向風速のサマリー
        wind_direction = st.session_state.estimated_wind.get('direction', 0)
        wind_speed = st.session_state.estimated_wind.get('speed', 0)
        confidence = st.session_state.estimated_wind.get('confidence', 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("風向", f"{wind_direction:.1f}°")
        with col2:
            st.metric("風速", f"{wind_speed:.1f} ノット")
        with col3:
            st.metric("推定信頼度", f"{confidence:.2f}")
        
        # 風向図
        fig = go.Figure()
        
        # 風向を示す円グラフ
        fig.add_trace(go.Barpolar(
            r=[1],
            theta=[wind_direction],
            width=[15],
            marker_color=["rgba(0, 0, 255, 0.8)"],
            marker_line_color="black",
            marker_line_width=2,
            opacity=0.8,
            hoverinfo="text",
            hovertext=f"風向: {wind_direction:.1f}°<br>風速: {wind_speed:.1f} ノット"
        ))
        
        # レイアウト設定
        fig.update_layout(
            title="風向",
            polar=dict(
                radialaxis=dict(visible=False, range=[0, 1]),
                angularaxis=dict(
                    direction="clockwise",
                    tickmode="array",
                    tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                    ticktext=["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
                )
            ),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 時系列での風向風速分析（ダミーデータ）
        if 'wind_direction' in st.session_state.gps_data.columns and 'timestamp' in st.session_state.gps_data.columns:
            # 実際の風向データがある場合
            wind_data = st.session_state.gps_data[['timestamp', 'wind_direction']].copy()
            
            if 'wind_speed' in st.session_state.gps_data.columns:
                wind_data['wind_speed'] = st.session_state.gps_data['wind_speed']
            
            # 風向の時系列グラフ
            fig = px.line(
                wind_data, 
                x='timestamp', 
                y='wind_direction',
                title="風向の時系列変化",
                labels={'timestamp': '時間', 'wind_direction': '風向 (度)'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 風速がある場合
            if 'wind_speed' in wind_data.columns:
                # 風速の時系列グラフ
                fig = px.line(
                    wind_data, 
                    x='timestamp', 
                    y='wind_speed',
                    title="風速の時系列変化",
                    labels={'timestamp': '時間', 'wind_speed': '風速 (ノット)'}
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("時系列での風向風速データはありません。")
    else:
        st.info("風向風速の推定データがありません。")

def render_advanced_analysis():
    """詳細モードでの追加分析を表示"""
    # タブスタイルの詳細分析
    tabs = st.tabs(["ポーラーチャート", "タック分析", "VMG分析", "データエクスポート"])
    
    with tabs[0]:
        st.subheader("ポーラーチャート")
        
        if ('course' in st.session_state.gps_data.columns and 
            'speed' in st.session_state.gps_data.columns and
            'wind_direction' in st.session_state.gps_data.columns):
            
            # 風向との相対角度を計算
            df = st.session_state.gps_data.copy()
            wind_dir = st.session_state.estimated_wind.get('direction', 0)
            
            # 相対風向角度の計算（風向と船の進行方向の差）
            df['relative_wind_angle'] = (df['wind_direction'] - df['course']).apply(
                lambda x: (x + 180) % 360 - 180
            ).abs()
            
            # 速度をノットに変換（必要に応じて）
            if df['speed'].mean() > 0.1:  # 既にノットの場合は変換不要
                df['speed_knots'] = df['speed'] * 1.94384  # m/s to knots
            else:
                df['speed_knots'] = df['speed']
            
            # 極座標グラフ
            fig = px.scatter_polar(
                df, 
                r="speed_knots", 
                theta="relative_wind_angle",
                color="speed_knots",
                title="速度と風向の関係（ポーラーチャート）",
                color_continuous_scale=px.colors.sequential.Plasma,
                range_theta=[0, 180],
                labels={"speed_knots": "速度 (ノット)", "relative_wind_angle": "風向との相対角度 (度)"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ポーラーチャートに必要なデータがありません。")
    
    with tabs[1]:
        st.subheader("タック分析")
        
        if 'course' in st.session_state.gps_data.columns and 'speed' in st.session_state.gps_data.columns:
            # タック検出のためのパラメータ
            tack_threshold = st.slider("タック検出角度閾値", 60, 120, 90, step=5)
            window_size = st.slider("検出ウィンドウサイズ", 3, 20, 5, step=1)
            
            if st.button("タックを検出"):
                with st.spinner("タックを検出中..."):
                    # コースの差分を計算
                    df = st.session_state.gps_data.copy()
                    df['course_diff'] = df['course'].diff().abs()
                    
                    # 角度の折り返しを処理（例：350度から10度への変化を正しく計算）
                    df['course_diff'] = df['course_diff'].apply(lambda x: min(x, 360-x) if not pd.isna(x) else x)
                    
                    # タック検出（簡易的なアルゴリズム）
                    tacks = []
                    for i in range(window_size, len(df) - window_size):
                        # 前後のウィンドウでのコース変化を計算
                        pre_course = df['course'].iloc[i-window_size:i].mean()
                        post_course = df['course'].iloc[i:i+window_size].mean()
                        
                        # コース変化の絶対値
                        course_change = abs(post_course - pre_course)
                        if course_change > 180:
                            course_change = 360 - course_change
                        
                        # 閾値以上の変化をタックとして検出
                        if course_change >= tack_threshold:
                            # タック中の速度変化も計算
                            pre_speed = df['speed'].iloc[i-window_size:i].mean()
                            min_speed = df['speed'].iloc[i-window_size:i+window_size].min()
                            post_speed = df['speed'].iloc[i:i+window_size].mean()
                            
                            speed_drop = (pre_speed - min_speed) / pre_speed if pre_speed > 0 else 0
                            recovery_time = window_size * 2  # 簡易的な回復時間
                            
                            tacks.append({
                                "index": i,
                                "timestamp": df['timestamp'].iloc[i],
                                "pre_course": pre_course,
                                "post_course": post_course,
                                "course_change": course_change,
                                "speed_drop": speed_drop,
                                "recovery_time": recovery_time,
                                "latitude": df['latitude'].iloc[i],
                                "longitude": df['longitude'].iloc[i]
                            })
                            
                            # 連続検出を避けるためにスキップ
                            i += window_size
                    
                    # 結果表示
                    if tacks:
                        st.success(f"{len(tacks)}個のタックを検出しました")
                        
                        # データフレームとして表示
                        tack_df = pd.DataFrame(tacks)
                        st.dataframe(tack_df[['timestamp', 'pre_course', 'post_course', 
                                             'course_change', 'speed_drop', 'recovery_time']])
                        
                        # タック位置のマップ表示
                        tack_map = folium.Map(location=get_map_center(st.session_state.gps_data), zoom_start=14)
                        
                        # トラックを表示
                        positions = list(zip(st.session_state.gps_data['latitude'], 
                                           st.session_state.gps_data['longitude']))
                        folium.PolyLine(
                            positions,
                            color='blue',
                            weight=2,
                            opacity=0.5
                        ).add_to(tack_map)
                        
                        # タックポイントを表示
                        for tack in tacks:
                            folium.Marker(
                                [tack['latitude'], tack['longitude']],
                                tooltip=f"タック: {tack['pre_course']:.0f}° → {tack['post_course']:.0f}°",
                                icon=folium.Icon(color='red', icon='exchange', prefix='fa')
                            ).add_to(tack_map)
                        
                        # マップを表示
                        st.subheader("タック位置")
                        folium_static(tack_map, width=700, height=500)
                    else:
                        st.warning("タックが検出されませんでした。パラメータを調整してみてください。")
        else:
            st.info("タック分析に必要なデータがありません。")
    
    with tabs[2]:
        st.subheader("VMG (Velocity Made Good) 分析")
        
        if ('course' in st.session_state.gps_data.columns and 
            'speed' in st.session_state.gps_data.columns and
            'wind_direction' in st.session_state.gps_data.columns):
            
            # VMG計算（風上/風下方向への速度成分）
            df = st.session_state.gps_data.copy()
            
            # 風向との相対角度
            df['relative_wind_angle'] = (df['wind_direction'] - df['course']).apply(
                lambda x: (x + 180) % 360 - 180
            ).abs()
            
            # 風上風下の判定
            upwind_threshold = 90  # 風上判定閾値（度）
            df['point_of_sail'] = df['relative_wind_angle'].apply(
                lambda x: '風上' if x < upwind_threshold else '風下'
            )
            
            # 速度をノットに変換（必要に応じて）
            if df['speed'].mean() > 0.1:  # 既にノットの場合は変換不要
                df['speed_knots'] = df['speed'] * 1.94384  # m/s to knots
            else:
                df['speed_knots'] = df['speed']
            
            # VMG計算
            df['vmg'] = df.apply(
                lambda row: row['speed_knots'] * np.cos(np.radians(row['relative_wind_angle'])) 
                            if row['point_of_sail'] == '風上' else
                            row['speed_knots'] * np.cos(np.radians(180 - row['relative_wind_angle'])),
                axis=1
            )
            
            # VMGの散布図
            fig = px.scatter(
                df, 
                x="relative_wind_angle", 
                y="vmg",
                color="point_of_sail",
                title="風向角度とVMGの関係",
                labels={"relative_wind_angle": "風向との相対角度 (度)", 
                        "vmg": "VMG (Velocity Made Good)", 
                        "point_of_sail": "セーリングポイント"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # VMGの時系列グラフ
            fig = px.line(
                df, 
                x="timestamp", 
                y="vmg",
                color="point_of_sail",
                title="VMGの時系列変化",
                labels={"timestamp": "時間", 
                        "vmg": "VMG (Velocity Made Good)", 
                        "point_of_sail": "セーリングポイント"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # VMGの統計
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("風上時のVMG")
                upwind_vmg = df[df['point_of_sail'] == '風上']['vmg']
                if not upwind_vmg.empty:
                    st.metric("平均VMG（風上）", f"{upwind_vmg.mean():.2f}")
                    st.metric("最大VMG（風上）", f"{upwind_vmg.max():.2f}")
                    
                    # 最適風向角度
                    optimal_angle_upwind = df[df['point_of_sail'] == '風上'].loc[df[df['point_of_sail'] == '風上']['vmg'].idxmax()]['relative_wind_angle']
                    st.metric("最適風向角度（風上）", f"{optimal_angle_upwind:.1f}°")
                else:
                    st.info("風上データがありません")
            
            with col2:
                st.subheader("風下時のVMG")
                downwind_vmg = df[df['point_of_sail'] == '風下']['vmg']
                if not downwind_vmg.empty:
                    st.metric("平均VMG（風下）", f"{downwind_vmg.mean():.2f}")
                    st.metric("最大VMG（風下）", f"{downwind_vmg.max():.2f}")
                    
                    # 最適風向角度
                    optimal_angle_downwind = df[df['point_of_sail'] == '風下'].loc[df[df['point_of_sail'] == '風下']['vmg'].idxmax()]['relative_wind_angle']
                    st.metric("最適風向角度（風下）", f"{optimal_angle_downwind:.1f}°")
                else:
                    st.info("風下データがありません")
        else:
            st.info("VMG分析に必要なデータがありません。")
    
    with tabs[3]:
        st.subheader("データエクスポート")
        
        # エクスポート形式の選択
        export_format = st.radio(
            "エクスポート形式を選択:",
            ["CSV", "JSON", "GPX"]
        )
        
        # エクスポートボタン
        if st.button("データをエクスポート"):
            with st.spinner("データをエクスポート中..."):
                try:
                    if export_format == "CSV":
                        # CSVエクスポート
                        csv_data = st.session_state.gps_data.to_csv(index=False)
                        b64 = base64.b64encode(csv_data.encode()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="sailing_data.csv">CSVファイルをダウンロード</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    elif export_format == "JSON":
                        # JSONエクスポート
                        json_data = st.session_state.gps_data.to_json(orient='records', date_format='iso')
                        b64 = base64.b64encode(json_data.encode()).decode()
                        href = f'<a href="data:file/json;base64,{b64}" download="sailing_data.json">JSONファイルをダウンロード</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    elif export_format == "GPX":
                        # GPXエクスポート（簡易実装）
                        gpx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Sailing Strategy Analyzer">
<trk>
<name>Sailing Track</name>
<trkseg>
'''
                        
                        # トラックポイントの追加
                        for _, row in st.session_state.gps_data.iterrows():
                            timestamp = row['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ') if isinstance(row['timestamp'], pd.Timestamp) else row['timestamp']
                            lat = row['latitude']
                            lon = row['longitude']
                            
                            gpx_content += f'<trkpt lat="{lat}" lon="{lon}">\n'
                            gpx_content += f'<time>{timestamp}</time>\n'
                            
                            # 追加データがあれば含める
                            if 'speed' in row:
                                gpx_content += f'<speed>{row["speed"]}</speed>\n'
                            if 'course' in row:
                                gpx_content += f'<course>{row["course"]}</course>\n'
                            
                            gpx_content += '</trkpt>\n'
                        
                        # GPXの終了タグ
                        gpx_content += '''</trkseg>
</trk>
</gpx>'''
                        
                        b64 = base64.b64encode(gpx_content.encode()).decode()
                        href = f'<a href="data:application/gpx+xml;base64,{b64}" download="sailing_data.gpx">GPXファイルをダウンロード</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    st.success(f"{export_format}形式でデータをエクスポートしました！")
                
                except Exception as e:
                    st.error(f"エクスポート中にエラーが発生しました: {str(e)}")

# メインアプリケーション
def main():
    """メインアプリケーションの実行"""
    # ヘッダーの表示
    render_header()
    
    # サイドバーの表示
    render_sidebar()
    
    # メインコンテンツエリア
    # マップビュー
    render_map_view()
    
    # 分析パネル
    render_analysis_panel()
    
    # フッター
    st.markdown("---")
    st.caption("セーリング戦略分析システム v1.0.0 | © 2025 Sailing Strategy Analyzer Team")

# アプリケーションの実行
if __name__ == "__main__":
    main()
