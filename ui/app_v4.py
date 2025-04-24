# -*- coding: utf-8 -*-
"""
ui.app_v4

セーリング戦略分析システムの改良版UIアプリケーション
フェーズ2のステップ2で実装されたコンポーネントを使用
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta
import tempfile

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 自作モジュールのインポート
from sailing_data_processor.core import SailingDataProcessor
from sailing_data_processor.data_model.container import GPSDataContainer, WindDataContainer
from ui.data_binding import DataBindingManager, UIStateManager
from ui.components.visualizations.map_view import MapViewComponent
from ui.components.visualizations.performance_charts import PerformanceChartsComponent
from ui.components.visualizations.metrics_dashboard import MetricsDashboardComponent
from ui.components.visualizations.wind_field_view import WindFieldViewComponent
from ui.components.controls.interactive_controls import ControlPanelComponent

# ページ設定
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# アプリケーションのタイトル
st.title('セーリング戦略分析システム (v4)')

# セッション状態の初期化
if 'data_processor' not in st.session_state:
    st.session_state.data_processor = SailingDataProcessor()

if 'data_binding' not in st.session_state:
    st.session_state.data_binding = DataBindingManager()

if 'ui_state' not in st.session_state:
    st.session_state.ui_state = UIStateManager()

# コンポーネントの初期化
if 'map_view' not in st.session_state:
    st.session_state.map_view = MapViewComponent(
        st.session_state.data_binding,
        st.session_state.ui_state
    )

if 'performance_charts' not in st.session_state:
    st.session_state.performance_charts = PerformanceChartsComponent(
        st.session_state.data_binding,
        st.session_state.ui_state
    )

if 'metrics_dashboard' not in st.session_state:
    st.session_state.metrics_dashboard = MetricsDashboardComponent(
        st.session_state.data_binding,
        st.session_state.ui_state
    )

if 'wind_field_view' not in st.session_state:
    st.session_state.wind_field_view = WindFieldViewComponent(
        st.session_state.data_binding,
        st.session_state.ui_state
    )

if 'control_panel' not in st.session_state:
    st.session_state.control_panel = ControlPanelComponent(
        st.session_state.data_binding,
        st.session_state.ui_state
    )

# サンプルデータ生成関数
def generate_sample_data():
    """テスト用のサンプルデータを生成"""
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
    
    # データコンテナを作成して登録
    container1 = GPSDataContainer(boat1_data, {'boat_name': 'ボート1'})
    container2 = GPSDataContainer(boat2_data, {'boat_name': 'ボート2'})
    
    # 風データのサンプルを生成
    wind_data = {
        'direction': 90.0,
        'speed': 15.0,
        'timestamp': boat1_timestamps[0],
        'position': {'latitude': 35.45, 'longitude': 139.65},
        'confidence': 0.8
    }
    wind_container = WindDataContainer(wind_data, {'source': 'sample'})
    
    # データバインディングに登録
    data_binding = st.session_state.data_binding
    data_binding.register_container('boat1', container1)
    data_binding.register_container('boat2', container2)
    data_binding.register_container('wind1', wind_container)
    
    # UI状態を更新
    ui_state = st.session_state.ui_state
    ui_state.select_datasets(['boat1', 'boat2'])
    
    return {'boat1': container1, 'boat2': container2, 'wind1': wind_container}

# CSV処理関数
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

# サイドバーのナビゲーション
page = st.sidebar.selectbox(
    'ナビゲーション',
    ['マップビュー', 'データ管理', 'パフォーマンス分析', '風分析']
)

# マップビュー（メイン画面）
if page == 'マップビュー':
    # マップビューのレイアウト
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader('セーリング航跡マップ')
        
        # データコンテナの取得
        containers = st.session_state.data_binding.get_all_containers()
        
        # データがあればマップを表示
        if any(isinstance(container, GPSDataContainer) for container in containers.values()):
            # マップ表示
            st.session_state.map_view.render(key="main_map")
        else:
            # データがないときのプレースホルダメッセージ
            st.info('データがアップロードされていません。右側の「サンプルデータを生成」ボタンを押すか、データ管理ページでデータをアップロードしてください。')
    
    with col2:
        st.subheader('コントロールパネル')
        
        # データがないときのメッセージとサンプルデータボタン
        if not any(isinstance(container, GPSDataContainer) for container in st.session_state.data_binding.get_all_containers().values()):
            st.warning('データがありません。データ管理ページでアップロードするか、サンプルデータを使用してください。')
            if st.button('サンプルデータを生成'):
                with st.spinner('サンプルデータを生成中...'):
                    sample_data = generate_sample_data()
                    st.success('サンプルデータを読み込みました！')
                    st.experimental_rerun()
        else:
            # コントロールパネルを表示
            st.session_state.control_panel.render(key_prefix="map_")

# データ管理画面
elif page == 'データ管理':
    st.header('データ管理')
    
    # タブでセクションを分ける
    upload_tab, manage_tab = st.tabs(["データアップロード", "データ管理"])
    
    with upload_tab:
        st.subheader('新規データアップロード')
        
        # ファイルアップロードエリア
        uploaded_file = st.file_uploader(
            "GPXまたはCSVファイルをアップロード",
            type=['gpx', 'csv'],
            help="GPXファイル: GPSトラッカーからのデータ\nCSVファイル: カンマ区切りのデータ（少なくとも緯度・経度列が必要）"
        )
        
        if uploaded_file:
            file_info = f"ファイル名: {uploaded_file.name}\nサイズ: {uploaded_file.size / 1024:.1f} KB"
            st.info(file_info)
            
            # ファイル種別を判定
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            # ボート名入力
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
                        else:
                            error = f'未対応のファイル形式です: {file_extension}'
                            df = None
                        
                        if error:
                            st.error(error)
                        elif df is not None:
                            # コンテナを作成して登録
                            container_id = boat_name.lower().replace(' ', '_')
                            container = GPSDataContainer(df, {'boat_name': boat_name})
                            st.session_state.data_binding.register_container(container_id, container)
                            
                            st.success(f'{boat_name} のデータを正常に読み込みました！')
                            
                            # データプレビュー表示
                            st.subheader('データプレビュー')
                            st.dataframe(df.head(), use_container_width=True)
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
                    st.success('サンプルデータを読み込みました！')
                    st.experimental_rerun()
    
    with manage_tab:
        st.subheader('読み込み済みのデータ')
        
        # コンテナ一覧を取得
        containers = st.session_state.data_binding.get_all_containers()
        gps_containers = {id: container for id, container in containers.items() if isinstance(container, GPSDataContainer)}
        
        if not gps_containers:
            st.info('データがまだアップロードされていません')
        else:
            # データ管理テーブル
            for container_id, container in gps_containers.items():
                # メタデータからボート名を取得
                boat_name = container.get_metadata('boat_name', container_id)
                
                with st.container(border=True):
                    cols = st.columns([3, 1, 1, 1])
                    
                    with cols[0]:
                        st.subheader(boat_name)
                        data = container.data
                        info_text = []
                        info_text.append(f"データ点数: {len(data):,}")
                        if 'timestamp' in data.columns:
                            duration = (data['timestamp'].max() - data['timestamp'].min()).total_seconds() / 60
                            info_text.append(f"期間: {duration:.1f}分")
                        if 'speed' in data.columns:
                            info_text.append(f"平均速度: {data['speed'].mean() * 1.94384:.1f}ノット")
                        
                        st.text(" | ".join(info_text))
                    
                    with cols[1]:
                        if st.button("データ表示", key=f"view_{container_id}"):
                            st.session_state.view_data = container_id
                    
                    with cols[2]:
                        if st.button("分析", key=f"analyze_{container_id}"):
                            st.session_state.page = 'パフォーマンス分析'
                            st.session_state.analyze_boat = container_id
                            st.experimental_rerun()
                    
                    with cols[3]:
                        if st.button("削除", key=f"del_{container_id}"):
                            if container_id in st.session_state.data_binding.get_all_containers():
                                # コンテナの削除
                                st.session_state.data_binding.get_all_containers().pop(container_id, None)
                                st.success(f"{boat_name} のデータを削除しました")
                                st.experimental_rerun()
            
            # 選択したデータの詳細表示
            if 'view_data' in st.session_state and st.session_state.view_data in st.session_state.data_binding.get_all_containers():
                container_id = st.session_state.view_data
                container = st.session_state.data_binding.get_container(container_id)
                
                if isinstance(container, GPSDataContainer):
                    boat_name = container.get_metadata('boat_name', container_id)
                    data = container.data
                    
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
                # コンテナをクリア
                st.session_state.data_binding.get_all_containers().clear()
                st.success("すべてのデータを削除しました")
                st.experimental_rerun()

# パフォーマンス分析画面
elif page == 'パフォーマンス分析':
    st.header('パフォーマンス分析')
    
    # データコンテナの取得
    containers = st.session_state.data_binding.get_all_containers()
    gps_containers = {id: container for id, container in containers.items() if isinstance(container, GPSDataContainer)}
    
    if not gps_containers:
        st.warning('データがありません。マップビューページからサンプルデータを生成するか、データ管理ページでデータをアップロードしてください。')
        if st.button('サンプルデータを生成'):
            with st.spinner('サンプルデータを生成中...'):
                sample_data = generate_sample_data()
                st.success('サンプルデータを読み込みました！')
                st.experimental_rerun()
    else:
        # 分析タブ
        tabs = st.tabs(["速度分析", "タック分析", "パフォーマンスダッシュボード"])
        
        with tabs[0]:
            st.subheader('速度分析')
            
            # 分析対象ボートの選択
            container_ids = list(gps_containers.keys())
            
            # 前の画面から選択されたボートがあれば優先的に選択
            default_container = st.session_state.get('analyze_boat', container_ids[0] if container_ids else None)
            if default_container not in container_ids and container_ids:
                default_container = container_ids[0]
            
            selected_container = st.selectbox(
                '分析するボート:',
                container_ids,
                index=container_ids.index(default_container) if default_container in container_ids else 0,
                format_func=lambda x: gps_containers[x].get_metadata('boat_name', x)
            )
            
            # グラフオプション
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.subheader('グラフオプション')
                
                # 速度時系列オプション
                smoothing = st.slider('平滑化レベル:', 0, 10, 0, help="0:なし、10:最大平滑化")
                show_raw = st.checkbox('生データも表示', value=False)
                
                # グラフ生成ボタン
                if st.button('速度時系列グラフ生成', type="primary"):
                    # 選択したコンテナでグラフを生成
                    container = gps_containers[selected_container]
                    fig = st.session_state.performance_charts.create_speed_vs_time_chart(
                        container,
                        name=container.get_metadata('boat_name', selected_container),
                        smoothing=smoothing,
                        show_raw=show_raw
                    )
                    
                    # グラフをキャッシュ
                    st.session_state.current_chart = fig
                
                # 風向速度グラフボタン
                if st.button('風向速度グラフ生成'):
                    # 選択したコンテナでグラフを生成
                    container = gps_containers[selected_container]
                    fig = st.session_state.performance_charts.create_speed_vs_wind_angle_chart(
                        container,
                        name=container.get_metadata('boat_name', selected_container)
                    )
                    
                    # グラフをキャッシュ
                    st.session_state.current_chart = fig
                
                # ポーラーチャートボタン
                if st.button('ポーラーチャート生成'):
                    # 選択したコンテナでグラフを生成
                    container = gps_containers[selected_container]
                    fig = st.session_state.performance_charts.create_polar_chart(
                        container,
                        name=container.get_metadata('boat_name', selected_container)
                    )
                    
                    # グラフをキャッシュ
                    st.session_state.current_chart = fig
            
            with col2:
                st.subheader('速度グラフ')
                
                # キャッシュされたグラフがあれば表示
                if 'current_chart' in st.session_state:
                    st.session_state.performance_charts.render_chart(st.session_state.current_chart)
                else:
                    st.info('左側のオプションを選択してグラフを生成してください。')
        
        with tabs[1]:
            st.subheader('タック分析')
            
            # 分析対象ボートの選択
            container_ids = list(gps_containers.keys())
            
            selected_container = st.selectbox(
                'タック分析するボート:',
                container_ids,
                format_func=lambda x: gps_containers[x].get_metadata('boat_name', x),
                key='tack_boat_select'
            )
            
            # タック分析オプション
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.subheader('タック分析オプション')
                
                # タック分析オプション
                tack_threshold = st.slider('タック検出閾値 (度):', 30, 120, 60, step=5)
                window_size = st.slider('解析ウィンドウ (秒):', 10, 60, 30, step=5)
                
                # グラフ生成ボタン
                if st.button('タック分析グラフ生成', type="primary"):
                    # 選択したコンテナでグラフを生成
                    container = gps_containers[selected_container]
                    fig = st.session_state.performance_charts.create_tack_analysis_chart(
                        container,
                        name=container.get_metadata('boat_name', selected_container),
                        window_size=window_size,
                        tack_threshold=tack_threshold
                    )
                    
                    # グラフをキャッシュ
                    st.session_state.tack_chart = fig
            
            with col2:
                st.subheader('タック分析グラフ')
                
                # キャッシュされたグラフがあれば表示
                if 'tack_chart' in st.session_state:
                    st.session_state.performance_charts.render_chart(st.session_state.tack_chart)
                else:
                    st.info('左側のオプションを選択してタック分析グラフを生成してください。')
        
        with tabs[2]:
            st.subheader('パフォーマンスダッシュボード')
            
            # 分析対象ボートの選択
            container_ids = list(gps_containers.keys())
            
            selected_container = st.selectbox(
                'ダッシュボード表示するボート:',
                container_ids,
                format_func=lambda x: gps_containers[x].get_metadata('boat_name', x),
                key='dashboard_boat_select'
            )
            
            # 選択したコンテナでメトリクスダッシュボードを表示
            container = gps_containers[selected_container]
            st.session_state.metrics_dashboard.render_dashboard(
                container,
                name=container.get_metadata('boat_name', selected_container)
            )

# 風分析画面
elif page == '風分析':
    st.header('風分析')
    
    # データコンテナの取得
    containers = st.session_state.data_binding.get_all_containers()
    gps_containers = {id: container for id, container in containers.items() if isinstance(container, GPSDataContainer)}
    wind_containers = {id: container for id, container in containers.items() if isinstance(container, WindDataContainer)}
    
    if not gps_containers and not wind_containers:
        st.warning('データがありません。マップビューページからサンプルデータを生成するか、データ管理ページでデータをアップロードしてください。')
        if st.button('サンプルデータを生成'):
            with st.spinner('サンプルデータを生成中...'):
                sample_data = generate_sample_data()
                st.success('サンプルデータを読み込みました！')
                st.experimental_rerun()
    else:
        # 風分析タブ
        tabs = st.tabs(["風向変化", "風配図", "風の場"])
        
        with tabs[0]:
            st.subheader('風向変化分析')
            
            if gps_containers:
                # 分析対象ボートの選択
                container_ids = list(gps_containers.keys())
                
                selected_container = st.selectbox(
                    '風データ元のボート:',
                    container_ids,
                    format_func=lambda x: gps_containers[x].get_metadata('boat_name', x),
                    key='wind_boat_select'
                )
                
                # グラフオプション
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.subheader('風シフト分析')
                    
                    # 風シフト検出オプション
                    threshold = st.slider('シフト検出閾値 (度):', 5, 30, 15, step=1)
                    
                    # グラフ生成ボタン
                    if st.button('風向変化グラフ生成', type="primary"):
                        # 選択したコンテナから風データを抽出
                        container = gps_containers[selected_container]
                        df = container.data
                        
                        if 'timestamp' in df.columns and 'wind_direction' in df.columns:
                            # 風データを辞書に変換
                            wind_data = {
                                'directions': df['wind_direction'].values,
                                'timestamps': df['timestamp'].values
                            }
                            
                            # 風向変化グラフを作成
                            fig = st.session_state.wind_field_view.create_wind_shift_analysis(
                                wind_data,
                                threshold=threshold
                            )
                            
                            # グラフをキャッシュ
                            st.session_state.wind_shift_chart = fig
                        else:
                            st.error('選択したデータに風向または時間データがありません。')
                
                with col2:
                    st.subheader('風向変化グラフ')
                    
                    # キャッシュされたグラフがあれば表示
                    if 'wind_shift_chart' in st.session_state:
                        st.session_state.wind_field_view.render_plotly_chart(st.session_state.wind_shift_chart)
                    else:
                        st.info('左側のオプションを選択して風向変化グラフを生成してください。')
            else:
                st.info('GPS/風向データがありません。')
        
        with tabs[1]:
            st.subheader('風配図')
            
            if gps_containers:
                # 分析対象ボートの選択
                container_ids = list(gps_containers.keys())
                
                selected_container = st.selectbox(
                    '風データ元のボート:',
                    container_ids,
                    format_func=lambda x: gps_containers[x].get_metadata('boat_name', x),
                    key='windrose_boat_select'
                )
                
                # グラフオプション
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.subheader('風配図オプション')
                    
                    # 風配図オプション
                    bin_size = st.slider('風向分割サイズ (度):', 5, 30, 10, step=5)
                    
                    # グラフ生成ボタン
                    if st.button('風配図生成', type="primary"):
                        # 選択したコンテナから風データを抽出
                        container = gps_containers[selected_container]
                        df = container.data
                        
                        if 'wind_direction' in df.columns and 'speed' in df.columns:
                            # 風データを辞書に変換
                            wind_data = {
                                'directions': df['wind_direction'].values,
                                'speeds': df['speed'].values * 1.94384  # m/s -> ノット
                            }
                            
                            # 風配図を作成
                            fig = st.session_state.wind_field_view.create_wind_rose(
                                wind_data,
                                bin_size=bin_size
                            )
                            
                            # グラフをキャッシュ
                            st.session_state.windrose_chart = fig
                        else:
                            st.error('選択したデータに風向または速度データがありません。')
                
                with col2:
                    st.subheader('風配図')
                    
                    # キャッシュされたグラフがあれば表示
                    if 'windrose_chart' in st.session_state:
                        st.session_state.wind_field_view.render_plotly_chart(st.session_state.windrose_chart)
                    else:
                        st.info('左側のオプションを選択して風配図を生成してください。')
            else:
                st.info('GPS/風向データがありません。')
        
        with tabs[2]:
            st.subheader('風の場')
            
            # 表示用の風格子データがない場合はサンプルを生成
            if 'wind_grid' not in st.session_state:
                # サンプルの風格子を生成
                grid_size = 5
                lat_base, lon_base = 35.45, 139.65
                grid_step = 0.001
                
                positions = []
                directions = []
                speeds = []
                
                for i in range(grid_size):
                    for j in range(grid_size):
                        lat = lat_base + i * grid_step
                        lon = lon_base + j * grid_step
                        
                        # 位置をリストに追加
                        positions.append((lat, lon))
                        
                        # 風向をランダムに生成（基本風向からの変動）
                        direction = 90 + np.random.normal(0, 10)
                        directions.append(direction)
                        
                        # 風速をランダムに生成
                        speed = 15 + np.random.normal(0, 2)
                        speeds.append(speed)
                
                st.session_state.wind_grid = {
                    'positions': positions,
                    'directions': directions,
                    'speeds': speeds
                }
            
            # 風の場マップを表示
            wind_map = st.session_state.wind_field_view.create_wind_field_map(
                st.session_state.wind_grid
            )
            st.session_state.wind_field_view.render_folium_map(wind_map)
            
            # 風速ヒートマップを表示
            st.subheader('風速ヒートマップ')
            wind_heatmap = st.session_state.wind_field_view.create_wind_heatmap(
                st.session_state.wind_grid, 
                property_name='speed'
            )
            st.session_state.wind_field_view.render_plotly_chart(wind_heatmap)
            
            # リセットボタン
            if st.button('風の場データをリセット'):
                # 風格子データをクリア
                st.session_state.pop('wind_grid', None)
                st.experimental_rerun()

# フッター
st.sidebar.markdown('---')
st.sidebar.info('セーリング戦略分析システム v1.0')
