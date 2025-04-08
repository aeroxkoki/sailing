import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import folium
from streamlit_folium import folium_static
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import base64
from io import StringIO
import json
import tempfile

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# 自作モジュールのインポート
from visualization.sailing_visualizer import SailingVisualizer
from visualization.map_display import SailingMapDisplay
from visualization.performance_plots import SailingPerformancePlots
import visualization.visualization_utils as viz_utils
from sailing_data_processor.core import SailingDataProcessor

# ページ設定
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# アプリケーションのタイトル - より明確に
st.title('セーリング戦略分析システム')

# セッション状態の初期化
if 'visualizer' not in st.session_state:
    st.session_state.visualizer = SailingVisualizer()
if 'map_display' not in st.session_state:
    st.session_state.map_display = SailingMapDisplay()
if 'performance_plots' not in st.session_state:
    st.session_state.performance_plots = SailingPerformancePlots()
if 'boats_data' not in st.session_state:
    st.session_state.boats_data = {}
if 'data_processor' not in st.session_state:
    st.session_state.data_processor = SailingDataProcessor()
if 'last_center' not in st.session_state:
    st.session_state.last_center = None  # マップの中心座標保存用

# サンプルデータ生成関数（既存のものを使用）
def generate_sample_data():
    """テスト用のサンプルデータを生成"""
    # 既存のコード
    boat1_timestamps = pd.date_range(start='2025-03-01 10:00:00', periods=100, freq='10S')
    
    boat1_data = pd.DataFrame({
        'timestamp': boat1_timestamps,
        'latitude': 35.45 + np.cumsum(np.random.normal(0, 0.0001, 100)),
        'longitude': 139.65 + np.cumsum(np.random.normal(0, 0.0001, 100)),
        'speed': 5 + np.random.normal(0, 0.5, 100),
        'course': 45 + np.random.normal(0, 5, 100),
        'wind_direction': 90 + np.random.normal(0, 3, 100)
    })
    
    # ボート2のデータ
    boat2_timestamps = pd.date_range(start='2025-03-01 10:02:00', periods=100, freq='10S')
    
    boat2_data = pd.DataFrame({
        'timestamp': boat2_timestamps,
        'latitude': 35.45 + np.cumsum(np.random.normal(0, 0.00012, 100)),
        'longitude': 139.65 + np.cumsum(np.random.normal(0, 0.00012, 100)),
        'speed': 5.2 + np.random.normal(0, 0.5, 100),
        'course': 50 + np.random.normal(0, 5, 100),
        'wind_direction': 90 + np.random.normal(0, 3, 100)
    })
    
    return {'ボート1': boat1_data, 'ボート2': boat2_data}

# GPXファイル処理関数を実装
def process_gpx(file):
    """GPXファイルを処理してデータフレームに変換"""
    try:
        # 一時ファイルに保存
        with tempfile.NamedTemporaryFile(delete=False, suffix='.gpx') as tmp_file:
            tmp_file.write(file.getvalue())
            tmp_file_path = tmp_file.name
        
        # ファイル内容を読み込み
        with open(tmp_file_path, 'r') as f:
            gpx_content = f.read()
        
        # 一時ファイルを削除
        os.unlink(tmp_file_path)
        
        # GPXデータをSailingDataProcessorで処理
        processor = st.session_state.data_processor
        df = processor._load_gpx(gpx_content, 'temp_id')
        
        if df is None:
            return None, "GPXファイルの処理に失敗しました。ファイル形式が正しいか確認してください。"
            
        # 最低限必要な列があるか確認
        required_columns = ['timestamp', 'latitude', 'longitude']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return None, f"GPXファイルに必要な列がありません: {missing_columns}"
            
        return df, None
        
    except Exception as e:
        return None, f"GPXファイルの処理中にエラーが発生しました: {str(e)}"

# CSV処理関数（既存のものを使用）
def process_csv(file):
    """CSVファイルを処理してデータフレームに変換"""
    try:
        # CSVファイルの読み込み
        df = pd.read_csv(file)
        
        # 必須カラムの確認
        required_columns = ['latitude', 'longitude']
        for col in required_columns:
            if col not in df.columns:
                return None, f"必須カラム '{col}' がCSVファイルに見つかりません"
        
        # タイムスタンプ列の処理
        if 'timestamp' in df.columns:
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except:
                return None, "タイムスタンプ列の形式が無効です"
        else:
            # タイムスタンプがない場合はインデックスから生成
            df['timestamp'] = pd.date_range(start='2025-03-01', periods=len(df), freq='10S')
        
        return df, None
        
    except Exception as e:
        return None, f"CSVファイルの処理中にエラーが発生しました: {str(e)}"

# マップの中心座標を計算
def get_map_center(boats_data):
    """GPSデータからマップの中心座標を計算"""
    if not boats_data:
        return (35.45, 139.65)  # デフォルト：東京湾
        
    all_lats = []
    all_lons = []
    
    for _, df in boats_data.items():
        if 'latitude' in df.columns and 'longitude' in df.columns:
            all_lats.extend(df['latitude'].dropna().tolist())
            all_lons.extend(df['longitude'].dropna().tolist())
    
    if all_lats and all_lons:
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
        return (center_lat, center_lon)
    else:
        return (35.45, 139.65)  # デフォルト：東京湾

# サイドバーのナビゲーション - シンプル化
page = st.sidebar.selectbox(
    'ナビゲーション',
    ['マップビュー', 'データ管理', 'パフォーマンス分析']
)

# マップビュー（メイン画面）
if page == 'マップビュー':
    # マップビューのレイアウト
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader('表示設定')
        
        # データがないときのメッセージとサンプルデータボタン
        if not st.session_state.boats_data:
            st.warning('データがありません。データ管理ページでアップロードするか、サンプルデータを使用してください。')
            if st.button('サンプルデータを生成'):
                with st.spinner('サンプルデータを生成中...'):
                    sample_data = generate_sample_data()
                    for boat_name, data in sample_data.items():
                        st.session_state.boats_data[boat_name] = data
                        st.session_state.visualizer.boats_data[boat_name] = data
                    st.success('サンプルデータを読み込みました！')
                    st.experimental_rerun()
        else:
            # 表示するボートの選択
            boat_options = list(st.session_state.boats_data.keys())
            selected_boats = st.multiselect('表示する艇:', boat_options, default=boat_options)
            
            # マップ表示オプション
            map_tile = st.selectbox('地図スタイル', 
                                   options=list(st.session_state.map_display.available_tiles.keys()))
            
            show_labels = st.checkbox('艇名ラベルを表示', value=True)
            show_course = st.checkbox('コース情報を表示', value=True)
            sync_time = st.checkbox('時間を同期して表示', value=False)
            
            # マップ表示ボタン
            if st.button('マップを更新', type="primary"):
                st.session_state.map_refresh = True
            
            # マップを別ウィンドウで開くボタン
            if st.button('マップを新しいウィンドウで開く'):
                st.info('この機能は開発中です。')

    # マップ表示エリア
    with col1:
        st.subheader('セーリング航跡マップ')
        
        if st.session_state.boats_data:
            # 選択ボートがなければ全て選択
            if 'selected_boats' not in locals() or not selected_boats:
                selected_boats = list(st.session_state.boats_data.keys())
            
            try:
                # 地図の中心を計算
                center = get_map_center({k: st.session_state.boats_data[k] for k in selected_boats if k in st.session_state.boats_data})
                st.session_state.last_center = center
                
                # マップオブジェクトの作成
                map_display = st.session_state.map_display
                map_object = map_display.create_map(
                    tile=map_tile if 'map_tile' in locals() else 'ポジトロン',
                    center=center
                )
                
                # 複数艇表示機能を使用
                map_object = st.session_state.visualizer.visualize_multiple_boats(
                    boat_names=selected_boats,
                    map_object=map_object,
                    show_labels=show_labels if 'show_labels' in locals() else True, 
                    sync_time=sync_time if 'sync_time' in locals() else False
                )
                
                # 地図を表示
                folium_static(map_object, width=800, height=600)
                
            except Exception as e:
                st.error(f'マップ生成中にエラーが発生しました: {e}')
        else:
            # データがないときのプレースホルダマップ
            st.info('データがアップロードされていません。右側の「サンプルデータを生成」ボタンを押すか、データ管理ページでデータをアップロードしてください。')
            # デフォルトマップ表示
            m = folium.Map(location=[35.45, 139.65], zoom_start=12)
            folium_static(m, width=800, height=600)

# データ管理画面
elif page == 'データ管理':
    st.header('データ管理')
    
    # タブでセクションを分ける
    upload_tab, manage_tab, export_tab = st.tabs(["データアップロード", "データ管理", "データエクスポート"])
    
    with upload_tab:
        st.subheader('新規データアップロード')
        
        # ファイルアップロードエリアの改善
        upload_cols = st.columns([1, 1])
        with upload_cols[0]:
            uploaded_file = st.file_uploader(
                "GPXまたはCSVファイルをアップロード", 
                type=['gpx', 'csv'],
                help="GPXファイル: GPSトラッカーからのデータ\nCSVファイル: カンマ区切りのデータ（少なくとも緯度・経度列が必要）"
            )
        
        with upload_cols[1]:
            if uploaded_file:
                file_info = f"ファイル名: {uploaded_file.name}\nサイズ: {uploaded_file.size / 1024:.1f} KB"
                st.info(file_info)
                
                # ファイル種別を判定
                file_extension = uploaded_file.name.split('.')[-1].lower()
                
                # ボート名入力をシンプルに
                boat_name = st.text_input(
                    'ボート名:', 
                    value=uploaded_file.name.split('.')[0],
                    help="データセットの識別名を入力してください"
                )
                
                if st.button('データを読み込む', type="primary"):
                    with st.spinner('データを処理中...'):
                        try:
                            if file_extension == 'csv':
                                df, error = process_csv(uploaded_file)
                            elif file_extension == 'gpx':
                                df, error = process_gpx(uploaded_file)
                            else:
                                error = f'未対応のファイル形式です: {file_extension}'
                                df = None
                            
                            if error:
                                st.error(error)
                            elif df is not None:
                                # セッションにデータを保存
                                st.session_state.boats_data[boat_name] = df
                                
                                # 可視化クラスにデータをロード
                                st.session_state.visualizer.boats_data[boat_name] = df
                                
                                st.success(f'{boat_name} のデータを正常に読み込みました！')
                                
                                # データプレビュー表示
                                st.subheader('データプレビュー')
                                st.dataframe(df.head(), use_container_width=True)
                                
                                # 基本統計情報
                                stats_cols = st.columns(3)
                                with stats_cols[0]:
                                    st.metric("データポイント数", f"{len(df):,}")
                                with stats_cols[1]:
                                    if 'speed' in df.columns:
                                        st.metric("平均速度", f"{df['speed'].mean() * 1.94384:.1f} ノット")
                                with stats_cols[2]:
                                    if 'timestamp' in df.columns:
                                        duration = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
                                        st.metric("記録時間", f"{duration:.1f} 分")
                            else:
                                st.error('データの処理に失敗しました。')
                        except Exception as e:
                            st.error(f'エラーが発生しました: {e}')
            else:
                st.info('GPXまたはCSVファイルをアップロードしてください。')
                
                # サンプルデータボタン
                if st.button('サンプルデータを生成してテスト'):
                    with st.spinner('サンプルデータを生成中...'):
                        sample_data = generate_sample_data()
                        for boat_name, data in sample_data.items():
                            st.session_state.boats_data[boat_name] = data
                            st.session_state.visualizer.boats_data[boat_name] = data
                        st.success('サンプルデータを読み込みました！')
                        st.experimental_rerun()
    
    with manage_tab:
        st.subheader('読み込み済みのデータ')
        
        if not st.session_state.boats_data:
            st.info('データがまだアップロードされていません')
        else:
            # データ管理テーブル - より視覚的に
            for boat_name, data in st.session_state.boats_data.items():
                with st.container(border=True):
                    cols = st.columns([3, 1, 1, 1])
                    
                    with cols[0]:
                        st.subheader(boat_name)
                        info_text = []
                        info_text.append(f"データ点数: {len(data):,}")
                        if 'timestamp' in data.columns:
                            duration = (data['timestamp'].max() - data['timestamp'].min()).total_seconds() / 60
                            info_text.append(f"期間: {duration:.1f}分")
                        if 'speed' in data.columns:
                            info_text.append(f"平均速度: {data['speed'].mean() * 1.94384:.1f}ノット")
                        
                        st.text(" | ".join(info_text))
                    
                    with cols[1]:
                        if st.button("データ表示", key=f"view_{boat_name}"):
                            st.session_state.view_data = boat_name
                    
                    with cols[2]:
                        if st.button("分析", key=f"analyze_{boat_name}"):
                            st.session_state.page = 'パフォーマンス分析'
                            st.session_state.analyze_boat = boat_name
                            st.experimental_rerun()
                    
                    with cols[3]:
                        if st.button("削除", key=f"del_{boat_name}"):
                            if st.session_state.boats_data.pop(boat_name, None):
                                st.session_state.visualizer.boats_data.pop(boat_name, None)
                                st.success(f"{boat_name} のデータを削除しました")
                                st.experimental_rerun()
                    
            # 選択したデータの詳細表示
            if 'view_data' in st.session_state and st.session_state.view_data in st.session_state.boats_data:
                boat_name = st.session_state.view_data
                data = st.session_state.boats_data[boat_name]
                
                st.subheader(f"{boat_name} - データ詳細")
                st.dataframe(data.head(20), use_container_width=True)
                
                if len(data) > 20:
                    st.info(f"表示: 最初の20行 (全{len(data)}行中)")
                
                # データ操作ボタン
                if st.button("閉じる"):
                    st.session_state.pop('view_data', None)
                    st.experimental_rerun()
            
            # すべてのデータを削除するボタン
            if st.button("すべてのデータを削除", type="primary"):
                st.session_state.boats_data = {}
                st.session_state.visualizer.boats_data = {}
                st.success("すべてのデータを削除しました")
                st.experimental_rerun()
    
    with export_tab:
        st.subheader('データエクスポート')
        
        if not st.session_state.boats_data:
            st.info('エクスポートできるデータがありません。まずデータをアップロードしてください。')
        else:
            # エクスポート設定
            export_boat = st.selectbox('エクスポートするデータを選択:', list(st.session_state.boats_data.keys()))
            export_format = st.radio('エクスポート形式:', ['CSV', 'JSON'])
            
            # エクスポートボタン
            if st.button('データをエクスポート'):
                # データプロセッサを使用
                processor = st.session_state.data_processor
                processor.boat_data = st.session_state.boats_data  # データを設定
                
                try:
                    # エクスポート形式を選択
                    format_type = export_format.lower()
                    exported_data = processor.export_processed_data(export_boat, format_type)
                    
                    if exported_data:
                        # バイナリデータをbase64エンコード
                        b64 = base64.b64encode(exported_data).decode()
                        
                        # ダウンロードリンクを作成
                        href = f'<a href="data:application/{format_type};base64,{b64}" download="{export_boat}.{format_type}">クリックしてダウンロード</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.success(f'{export_boat} のデータをエクスポートしました！')
                    else:
                        st.error('データのエクスポートに失敗しました。')
                except Exception as e:
                    st.error(f'エラーが発生しました: {e}')

# パフォーマンス分析画面
elif page == 'パフォーマンス分析':
    st.header('パフォーマンス分析')
    
    if not st.session_state.boats_data:
        st.warning('データがありません。マップビューページからサンプルデータを生成するか、データ管理ページでデータをアップロードしてください。')
        if st.button('サンプルデータを生成'):
            with st.spinner('サンプルデータを生成中...'):
                sample_data = generate_sample_data()
                for boat_name, data in sample_data.items():
                    st.session_state.boats_data[boat_name] = data
                    st.session_state.visualizer.boats_data[boat_name] = data
                st.success('サンプルデータを読み込みました！')
                st.experimental_rerun()
    else:
        # 分析タブ
        tabs = st.tabs(["単艇分析", "複数艇比較", "パフォーマンスサマリー"])
        
        with tabs[0]:
            st.subheader('単艇分析')
            
            # 分析対象ボートの選択
            boat_options = list(st.session_state.boats_data.keys())
            
            # 前の画面から選択されたボートがあれば優先的に選択
            default_boat = st.session_state.get('analyze_boat', boat_options[0] if boat_options else None)
            if default_boat not in boat_options and boat_options:
                default_boat = boat_options[0]
            
            selected_boat = st.selectbox('分析するボート:', boat_options, index=boat_options.index(default_boat) if default_boat in boat_options else 0)
            
            # グラフ選択
            plot_options = [
                '速度の時系列', 
                '風向と速度', 
                'ポーラーチャート', 
                'タック分析',
                'パフォーマンスダッシュボード'
            ]
            
            plot_type = st.selectbox('グラフ:', plot_options)
            
            # 画面分割でパラメータ設定とグラフ表示
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.subheader('パラメータ設定')
                
                # グラフに応じた設定パラメータ
                if plot_type == '速度の時系列':
                    smooth = st.slider('平滑化レベル:', 0, 10, 0, help="0:なし、10:最大平滑化")
                    show_raw = st.checkbox('生データも表示', value=False)
                elif plot_type == '風向と速度':
                    bin_size = st.slider('ビンサイズ (度):', 5, 30, 10, step=5)
                    color_scale = st.selectbox('カラースケール:', ['Viridis', 'Plasma', 'Inferno', 'Magma', 'Cividis'])
                elif plot_type == 'ポーラーチャート':
                    max_speed = st.slider('最大速度 (ノット):', 5, 30, 15, step=1)
                    resolution = st.slider('解像度:', 8, 72, 36, step=8)
                elif plot_type == 'タック分析':
                    tack_threshold = st.slider('タック検出閾値 (度):', 30, 120, 60, step=5)
                    window_size = st.slider('解析ウィンドウ (秒):', 10, 60, 30, step=5)
                elif plot_type == 'パフォーマンスダッシュボード':
                    time_window = st.selectbox('時間枠:', ['全期間', '前半', '後半'])
                    metrics = st.multiselect(
                        '表示する指標:', 
                        ['速度', '風向', 'VMG', 'タック'], 
                        default=['速度', '風向']
                    )
                
                # グラフ生成ボタン
                generate_button = st.button('グラフを生成', type="primary")
            
            with col2:
                # 選択したグラフを表示
                if generate_button or 'last_plot' in st.session_state:
                    # 最後に生成したグラフを保存
                    if generate_button:
                        st.session_state.last_plot = {
                            'boat': selected_boat,
                            'type': plot_type,
                            'params': {
                                'smooth': locals().get('smooth', 0),
                                'show_raw': locals().get('show_raw', False),
                                'bin_size': locals().get('bin_size', 10),
                                'color_scale': locals().get('color_scale', 'Viridis'),
                                'max_speed': locals().get('max_speed', 15),
                                'resolution': locals().get('resolution', 36),
                                'tack_threshold': locals().get('tack_threshold', 60),
                                'window_size': locals().get('window_size', 30),
                                'time_window': locals().get('time_window', '全期間'),
                                'metrics': locals().get('metrics', ['速度', '風向'])
                            }
                        }
                    
                    # グラフ生成
                    fig = None  # 初期化
                    try:
                        boat_data = st.session_state.boats_data[selected_boat]
                        performance_plots = st.session_state.performance_plots
                        
                        # グラフタイプに応じた処理
                        if plot_type == '速度の時系列':
                            fig = performance_plots.create_speed_vs_time_plot(
                                boat_data, 
                                selected_boat,
                                smooth=st.session_state.last_plot['params']['smooth'],
                                show_raw=st.session_state.last_plot['params']['show_raw']
                            )
                        elif plot_type == '風向と速度':
                            if 'wind_direction' not in boat_data.columns:
                                st.error('このグラフには風向データが必要です')
                            else:
                                fig = performance_plots.create_wind_speed_heatmap(
                                    boat_data,
                                    bin_size=st.session_state.last_plot['params']['bin_size'],
                                    color_scale=st.session_state.last_plot['params']['color_scale'].lower()
                                )
                        elif plot_type == 'ポーラーチャート':
                            if 'wind_direction' not in boat_data.columns:
                                st.error('このグラフには風向データが必要です')
                            else:
                                fig = performance_plots.create_speed_polar_plot(
                                    boat_data,
                                    max_speed=st.session_state.last_plot['params']['max_speed'],
                                    resolution=st.session_state.last_plot['params']['resolution']
                                )
                        elif plot_type == 'タック分析':
                            if 'course' not in boat_data.columns:
                                st.error('このグラフにはコースデータが必要です')
                            else:
                                fig = performance_plots.create_tack_analysis_plot(
                                    boat_data,
                                    tack_threshold=st.session_state.last_plot['params']['tack_threshold'],
                                    window_size=st.session_state.last_plot['params']['window_size']
                                )
                        elif plot_type == 'パフォーマンスダッシュボード':
                            # 必要なカラムのチェック
                            required_cols = []
                            if '速度' in st.session_state.last_plot['params']['metrics']:
                                required_cols.append('speed')
                            if '風向' in st.session_state.last_plot['params']['metrics']:
                                required_cols.append('wind_direction')
                            if 'VMG' in st.session_state.last_plot['params']['metrics']:
                                required_cols.extend(['speed', 'course', 'wind_direction'])
                            if 'タック' in st.session_state.last_plot['params']['metrics']:
                                required_cols.append('course')
                            
                            missing_cols = [col for col in required_cols if col not in boat_data.columns]
                            if missing_cols:
                                st.error(f'選択した指標には次の列が必要です: {", ".join(missing_cols)}')
                            else:
                                # 時間枠でデータをフィルタリング
                                filtered_data = boat_data.copy()
                                if st.session_state.last_plot['params']['time_window'] == '前半':
                                    mid_point = filtered_data['timestamp'].min() + (filtered_data['timestamp'].max() - filtered_data['timestamp'].min()) / 2
                                    filtered_data = filtered_data[filtered_data['timestamp'] <= mid_point]
                                elif st.session_state.last_plot['params']['time_window'] == '後半':
                                    mid_point = filtered_data['timestamp'].min() + (filtered_data['timestamp'].max() - filtered_data['timestamp'].min()) / 2
                                    filtered_data = filtered_data[filtered_data['timestamp'] > mid_point]
                                
                                fig = performance_plots.create_performance_dashboard(
                                    filtered_data, 
                                    selected_boat,
                                    metrics=st.session_state.last_plot['params']['metrics']
                                )
                                # グラフ表示
                        if fig is not None:
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # グラフ保存機能
                            try:
                                st.download_button(
                                    label="グラフを画像として保存",
                                    data=fig.to_image(format="png", engine="kaleido"),
                                    file_name=f"{selected_boat}_{plot_type}.png",
                                    mime="image/png",
                                )
                            except Exception as e:
                                st.warning("グラフの画像エクスポート機能を使用するには、追加のライブラリが必要です。")
                    
                    except Exception as e:
                        st.error(f'グラフ生成中にエラーが発生しました: {e}')
                else:
                    st.info('左側の「グラフを生成」ボタンをクリックしてください。')
        
        with tabs[1]:
            st.subheader('複数艇比較')
            
            # 比較するボートを選択
            boat_options = list(st.session_state.boats_data.keys())
            if len(boat_options) >= 2:
                comparison_boats = st.multiselect(
                    '比較するボートを選択:', 
                    boat_options, 
                    default=boat_options[:min(3, len(boat_options))]
                )
                
                if comparison_boats and len(comparison_boats) >= 2:
                    # 比較グラフの種類
                    comparison_type = st.selectbox(
                        '比較タイプ:',
                        ['速度比較', '航跡比較', '風向対応比較', '時間同期比較']
                    )
                    
                    # 比較パラメータ設定
                    if comparison_type == '速度比較':
                        smoothing = st.slider('平滑化:', 0, 10, 2)
                        use_time = st.checkbox('時間軸で表示', value=True)
                    elif comparison_type == '航跡比較':
                        show_markers = st.checkbox('ポイントを表示', value=True)
                        colorscale = st.selectbox('カラースケール:', ['rainbow', 'viridis', 'plasma'])
                    elif comparison_type == '風向対応比較':
                        bin_count = st.slider('風向ビン数:', 4, 36, 12, step=4)
                    elif comparison_type == '時間同期比較':
                        sync_window = st.slider('同期ウィンドウ (分):', 5, 60, 30, step=5)
                        metrics = st.multiselect(
                            '表示する指標:', 
                            ['速度', '風向', 'コース'], 
                            default=['速度']
                        )
                    
                    # 比較グラフ生成
                    if st.button('比較グラフを生成', type="primary"):
                        with st.spinner('比較グラフを生成中...'):
                            fig = None  # 初期化
                            try:
                                # 選択したボートのデータを辞書に格納
                                data_dict = {}
                                for boat in comparison_boats:
                                    data_dict[boat] = st.session_state.boats_data[boat]
                                
                                # 比較グラフの生成
                                if comparison_type == '速度比較':
                                    fig = st.session_state.performance_plots.create_multi_boat_speed_comparison(
                                        data_dict,
                                        smoothing=smoothing,
                                        use_time=use_time
                                    )
                                elif comparison_type == '航跡比較':
                                    fig = st.session_state.performance_plots.create_multi_boat_track_comparison(
                                        data_dict,
                                        show_markers=show_markers,
                                        colorscale=colorscale
                                    )
                                elif comparison_type == '風向対応比較':
                                    fig = st.session_state.performance_plots.create_wind_response_comparison(
                                        data_dict,
                                        bin_count=bin_count
                                    )
                                elif comparison_type == '時間同期比較':
                                    fig = st.session_state.performance_plots.create_synchronized_comparison(
                                        data_dict,
                                        sync_window=sync_window,
                                        metrics=metrics
                                    )
                                
                                # グラフ表示
                                if fig is not None:
                                    st.plotly_chart(fig, use_container_width=True)
                                
                            except Exception as e:
                                st.error(f'比較グラフ生成中にエラーが発生しました: {e}')
                else:
                    st.info('比較するには2つ以上のボートを選択してください。')
            else:
                st.warning('比較するにはデータが2つ以上必要です。まずはデータをアップロードしてください。')
        
        with tabs[2]:
            st.subheader('パフォーマンスサマリー')
            
            # サマリーを表示するボートの選択
            summary_boat = st.selectbox('サマリーを表示するボート:', list(st.session_state.boats_data.keys()), key='summary_boat')
            
            # サマリータイプの選択
            summary_type = st.radio(
                'サマリータイプ:',
                ['基本統計', '詳細分析', '総合レポート'],
                horizontal=True
            )
            
            if st.button('サマリーを生成', type="primary"):
                with st.spinner('サマリーを生成中...'):
                    try:
                        # パフォーマンスサマリーの取得
                        summary = st.session_state.visualizer.create_performance_summary(summary_boat)
                        
                        if summary:
                            if summary_type == '基本統計':
                                # 基本統計を表形式で表示
                                st.subheader(f"{summary_boat} の基本統計")
                                
                                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                                
                                with metrics_col1:
                                    if 'speed' in summary:
                                        st.metric("最高速度", f"{summary['speed']['max']:.1f} ノット")
                                        st.metric("平均速度", f"{summary['speed']['avg']:.1f} ノット")
                                
                                with metrics_col2:
                                    if 'total_distance_nm' in summary:
                                        st.metric("走行距離", f"{summary['total_distance_nm']:.2f} 海里")
                                    if 'duration_seconds' in summary:
                                        minutes = summary['duration_seconds'] / 60
                                        st.metric("走行時間", f"{minutes:.1f} 分")
                                
                                with metrics_col3:
                                    if 'tack_count' in summary:
                                        st.metric("タック回数", summary['tack_count'])
                                    if 'vmg' in summary:
                                        st.metric("平均VMG", f"{summary['vmg']['avg_vmg']:.2f}")
                                
                                # データポイントの分布を表示
                                if 'speed' in summary:
                                    speed_data = st.session_state.boats_data[summary_boat]['speed'] * 1.94384  # m/s -> ノット
                                    
                                    # ヒストグラム
                                    fig = px.histogram(
                                        speed_data,
                                        title="速度分布",
                                        labels={'value': '速度 (ノット)', 'count': '頻度'},
                                        nbins=20
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            elif summary_type == '詳細分析':
                                # 詳細分析表示
                                st.subheader(f"{summary_boat} の詳細分析")
                                
                                # タブで情報を整理
                                detail_tabs = st.tabs(['速度分析', 'タック分析', 'VMG分析'])
                                
                                with detail_tabs[0]:
                                    if 'speed_segments' in summary:
                                        segments = summary['speed_segments']
                                        
                                        # セグメント別の速度表
                                        st.subheader('セグメント別速度分析')
                                        segment_data = []
                                        for i, seg in enumerate(segments):
                                            segment_data.append({
                                                'セグメント': f"Seg {i+1}",
                                                '平均速度 (ノット)': f"{seg['avg_speed']:.1f}",
                                                '最高速度 (ノット)': f"{seg['max_speed']:.1f}",
                                                '持続時間 (秒)': f"{seg['duration']:.0f}"
                                            })
                                        
                                        st.table(pd.DataFrame(segment_data))
                                        
                                        # 速度トレンドグラフ
                                        fig = go.Figure()
                                        
                                        boat_data = st.session_state.boats_data[summary_boat]
                                        if 'timestamp' in boat_data.columns and 'speed' in boat_data.columns:
                                            # 時間を分単位に変換
                                            times = [(t - boat_data['timestamp'].iloc[0]).total_seconds() / 60 
                                                    for t in boat_data['timestamp']]
                                            
                                            # 速度をノットに変換
                                            speeds = boat_data['speed'] * 1.94384
                                            
                                            fig.add_trace(go.Scatter(
                                                x=times,
                                                y=speeds,
                                                mode='lines',
                                                name='速度'
                                            ))
                                            
                                            fig.update_layout(
                                                title='速度トレンド',
                                                xaxis_title='時間 (分)',
                                                yaxis_title='速度 (ノット)'
                                            )
                                            
                                            st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.info('速度セグメント分析データはありません。')
                                
                                with detail_tabs[1]:
                                    if 'tack_analysis' in summary:
                                        tack_analysis = summary['tack_analysis']
                                        
                                        # タック分析メトリクス
                                        metrics_cols = st.columns(3)
                                        with metrics_cols[0]:
                                            st.metric("タック回数", summary.get('tack_count', 0))
                                        with metrics_cols[1]:
                                            st.metric("平均速度損失", f"{tack_analysis.get('avg_loss_knots', 0):.2f} ノット")
                                        with metrics_cols[2]:
                                            st.metric("平均回復時間", f"{tack_analysis.get('avg_recovery_time', 0):.1f} 秒")
                                        
                                        # タック詳細テーブル
                                        if 'tacks' in tack_analysis:
                                            tack_data = []
                                            for i, tack in enumerate(tack_analysis['tacks']):
                                                tack_data.append({
                                                    'タック#': i+1,
                                                    '時間': tack.get('time', ''),
                                                    '前コース': f"{tack.get('pre_course', 0):.0f}°",
                                                    '後コース': f"{tack.get('post_course', 0):.0f}°",
                                                    '損失 (ノット)': f"{tack.get('speed_loss', 0):.2f}",
                                                    '回復時間 (秒)': f"{tack.get('recovery_time', 0):.1f}"
                                                })
                                            
                                            st.subheader('タック詳細')
                                            st.table(pd.DataFrame(tack_data))
                                    else:
                                        st.info('タック分析データはありません。')
                                
                                with detail_tabs[2]:
                                    if 'vmg' in summary:
                                        vmg = summary['vmg']
                                        
                                        # VMGメトリクス
                                        metrics_cols = st.columns(3)
                                        with metrics_cols[0]:
                                            st.metric("平均VMG", f"{vmg.get('avg_vmg', 0):.2f}")
                                        with metrics_cols[1]:
                                            st.metric("最大VMG", f"{vmg.get('max_vmg', 0):.2f}")
                                        with metrics_cols[2]:
                                            st.metric("VMG効率", f"{vmg.get('vmg_efficiency', 0):.1f}%")
                                        
                                        # VMGプロット
                                        if 'vmg_data' in vmg:
                                            fig = px.scatter(
                                                vmg['vmg_data'],
                                                x='wind_angle',
                                                y='vmg',
                                                color='speed',
                                                title='風向角度とVMGの関係',
                                                labels={
                                                    'wind_angle': '風向角度 (度)',
                                                    'vmg': 'VMG',
                                                    'speed': '速度 (ノット)'
                                                }
                                            )
                                            st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.info('VMG分析データはありません。')
                            
                            elif summary_type == '総合レポート':
                                # 総合レポートを表示
                                st.subheader(f"{summary_boat} の総合パフォーマンスレポート")
                                
                                # 全体評価
                                st.subheader('📊 全体評価')
                                
                                if 'overall_rating' in summary:
                                    rating = summary['overall_rating']
                                    st.progress(rating / 100)
                                    st.write(f"総合評価: {rating}/100")
                                
                                # 主要指標サマリー
                                st.subheader('📈 主要指標')
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("### 速度指標")
                                    if 'speed' in summary:
                                        speed_stats = summary['speed']
                                        st.write(f"🚀 最高速度: {speed_stats['max']:.2f} ノット")
                                        st.write(f"🔄 平均速度: {speed_stats['avg']:.2f} ノット")
                                        st.write(f"⬇️ 最低速度: {speed_stats['min']:.2f} ノット")
                                    
                                    if 'total_distance_nm' in summary:
                                        st.write(f"🛣️ 走行距離: {summary['total_distance_nm']:.2f} 海里")
                                
                                with col2:
                                    st.write("### 運航指標")
                                    if 'tack_count' in summary:
                                        st.write(f"↪️ タック回数: {summary['tack_count']}")
                                    
                                    if 'tack_analysis' in summary:
                                        tack_analysis = summary['tack_analysis']
                                        st.write(f"⏱️ 平均タック回復時間: {tack_analysis.get('avg_recovery_time', 0):.1f} 秒")
                                    
                                    if 'vmg' in summary:
                                        vmg = summary['vmg']
                                        st.write(f"🎯 VMG効率: {vmg.get('vmg_efficiency', 0):.1f}%")
                                
                                # 改善点
                                st.subheader('📝 改善点とアドバイス')
                                
                                if 'improvement_points' in summary:
                                    for i, point in enumerate(summary['improvement_points']):
                                        st.write(f"{i+1}. {point}")
                                else:
                                    # 改善点がない場合は自動生成
                                    if 'speed' in summary and 'tack_analysis' in summary:
                                        speed = summary['speed']
                                        tack = summary['tack_analysis']
                                        
                                        st.write("1. 速度の安定性を高めることで平均速度の向上が見込めます")
                                        
                                        if tack.get('avg_loss_knots', 0) > 1.0:
                                            st.write("2. タック時の速度損失を低減することで効率が向上します")
                                        
                                        if 'vmg' in summary and summary['vmg'].get('vmg_efficiency', 0) < 80:
                                            st.write("3. 風上帆走時のVMG効率の改善が推奨されます")
                                
                                # データ品質評価
                                st.subheader('📋 データ品質評価')
                                
                                if 'data_quality' in summary:
                                    quality = summary['data_quality']
                                    st.write(f"📊 サンプリング密度: {quality.get('sampling_rate', 0):.2f} Hz")
                                    st.write(f"⏱️ データ期間: {quality.get('duration_minutes', 0):.1f} 分")
                                    st.write(f"🔢 データポイント: {quality.get('points_count', 0)}")
                                    
                                    if 'noise_level' in quality:
                                        st.write(f"📶 ノイズレベル: {quality['noise_level']}")
                                else:
                                    # データ品質情報がない場合の表示
                                    points_count = len(st.session_state.boats_data[summary_boat])
                                    if 'timestamp' in st.session_state.boats_data[summary_boat].columns:
                                        df = st.session_state.boats_data[summary_boat]
                                        duration = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
                                        sampling_rate = points_count / (duration * 60) if duration > 0 else 0
                                        
                                        st.write(f"📊 サンプリング密度: {sampling_rate:.2f} Hz")
                                        st.write(f"⏱️ データ期間: {duration:.1f} 分")
                                    
                                    st.write(f"🔢 データポイント: {points_count}")
                        else:
                            st.warning(f"{summary_boat} のパフォーマンスサマリーを生成できませんでした")
                    
                    except Exception as e:
                        st.error(f'サマリー生成中にエラーが発生しました: {e}')

# フッター（シンプル化）
st.sidebar.markdown('---')
st.sidebar.info('セーリング戦略分析システム v1.0')
