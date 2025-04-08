"""
セーリング戦略分析システム - メインアプリケーション

フェーズ2のUI/UX改善に対応した改良版アプリケーション
"""

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
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 自作モジュールのインポート
from ui.components import load_css, render_metric_card, alert, enhanced_file_uploader, interactive_map
from ui.navigation import create_navigation
from visualization.sailing_visualizer import SailingVisualizer
from visualization.map_display import SailingMapDisplay
from visualization.performance_plots import SailingPerformancePlots
import visualization.visualization_utils as viz_utils
from sailing_data_processor.core import SailingDataProcessor

# ページ設定（レスポンシブ対応）
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSSスタイルのロード
load_css()

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
if 'map_settings' not in st.session_state:
    st.session_state.map_settings = {
        'tile': 'OpenStreetMap',
        'show_labels': True,
        'show_tracks': True,
        'show_markers': True,
        'sync_time': False,
        'marker_size': 10,
        'line_width': 3,
        'opacity': 0.8
    }

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
    
    return {'ボート1': boat1_data, 'ボート2': boat2_data}

# GPXファイル処理関数
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

# マップビューページの表示
def show_map_view():
    st.header('セーリング航跡マップ', divider='blue')
    
    # 2カラムレイアウト
    map_col, setting_col = st.columns([3, 1])
    
    with setting_col:
        st.subheader('表示設定')
        
        # データがないときのメッセージとサンプルデータボタン
        if not st.session_state.boats_data:
            alert("データがアップロードされていません。サンプルデータを生成するか、データ管理ページでデータをアップロードしてください。", 
                  type="warning")
            
            if st.button('サンプルデータを生成', type="primary", use_container_width=True):
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
            
            # マップ表示オプション - 改良されたインターフェース
            with st.container(border=True):
                # ベースマップ選択
                map_tile = st.selectbox('地図スタイル', 
                               options=list(st.session_state.map_display.available_tiles.keys()),
                               index=list(st.session_state.map_display.available_tiles.keys()).index(
                                   st.session_state.map_settings.get('tile', 'OpenStreetMap')))
                
                # 表示オプション
                col1, col2 = st.columns(2)
                with col1:
                    show_labels = st.checkbox('艇名ラベルを表示', 
                                             value=st.session_state.map_settings.get('show_labels', True))
                    show_tracks = st.checkbox('航跡を表示', 
                                             value=st.session_state.map_settings.get('show_tracks', True))
                
                with col2:
                    show_markers = st.checkbox('マーカーを表示', 
                                              value=st.session_state.map_settings.get('show_markers', True))
                    sync_time = st.checkbox('時間を同期して表示', 
                                           value=st.session_state.map_settings.get('sync_time', False))
            
            # 詳細設定
            with st.expander("詳細設定"):
                col1, col2 = st.columns(2)
                with col1:
                    marker_size = st.slider('マーカーサイズ', 5, 20, 
                                           value=st.session_state.map_settings.get('marker_size', 10))
                    line_width = st.slider('航跡の太さ', 1, 10, 
                                          value=st.session_state.map_settings.get('line_width', 3))
                
                with col2:
                    opacity = st.slider('透明度', 0.1, 1.0, 
                                      value=st.session_state.map_settings.get('opacity', 0.8), step=0.1)
                    # 時間フィルター（将来的に実装）
            
            # 設定を保存
            st.session_state.map_settings = {
                'tile': map_tile,
                'show_labels': show_labels,
                'show_tracks': show_tracks,
                'show_markers': show_markers,
                'sync_time': sync_time,
                'marker_size': marker_size,
                'line_width': line_width,
                'opacity': opacity
            }
            
            # マップ表示ボタン
            if st.button('マップを更新', type="primary", use_container_width=True):
                st.session_state.map_refresh = True
            
            # マップを別ウィンドウで開くボタン（将来的な機能）
            if st.button('マップを新しいウィンドウで開く', use_container_width=True):
                st.info('この機能は開発中です。')
            
            # フィードバックボタン
            if st.button('フィードバックを送信', use_container_width=True):
                st.session_state.show_feedback = True
    
    # マップ表示エリア
    with map_col:
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
                    tile=st.session_state.map_settings['tile'],
                    center=center
                )
                
                # 改良された可視化関数の使用
                map_object = st.session_state.visualizer.visualize_multiple_boats(
                    boat_names=selected_boats,
                    map_object=map_object,
                    show_labels=st.session_state.map_settings['show_labels'],
                    show_tracks=st.session_state.map_settings['show_tracks'],
                    show_markers=st.session_state.map_settings['show_markers'],
                    sync_time=st.session_state.map_settings['sync_time'],
                    marker_size=st.session_state.map_settings['marker_size'],
                    line_width=st.session_state.map_settings['line_width'],
                    opacity=st.session_state.map_settings['opacity']
                )
                
                # インタラクティブマップの表示（コントロール付き）
                interactive_map(map_object, width=800, height=600, with_controls=True)
                
            except Exception as e:
                alert(f'マップ生成中にエラーが発生しました: {e}', type="error")
        else:
            # データがないときのプレースホルダマップ
            alert('データがアップロードされていません。右側の「サンプルデータを生成」ボタンを押すか、データ管理ページでデータをアップロードしてください。',
                 type="info")
            
            # デフォルトマップ表示
            m = folium.Map(location=[35.45, 139.65], zoom_start=12)
            folium_static(m, width=800, height=600)
    
    # フィードバックフォーム（表示フラグがオンの場合）
    if st.session_state.get('show_feedback', False):
        with st.container(border=True):
            st.subheader('フィードバック')
            
            col1, col2 = st.columns(2)
            
            with col1:
                feedback_type = st.selectbox('フィードバックの種類:', 
                                           ['機能改善', 'バグ報告', '使いやすさ', 'その他'])
            
            with col2:
                rating = st.slider('満足度:', 1, 5, 3)
            
            feedback_text = st.text_area('詳細:', height=100)
            
            submit_col, cancel_col = st.columns([1, 3])
            with submit_col:
                if st.button('送信', type="primary"):
                    # フィードバックの保存（将来的に実装）
                    st.success('フィードバックを受け付けました。ありがとうございます！')
                    st.session_state.show_feedback = False
            
            with cancel_col:
                if st.button('キャンセル'):
                    st.session_state.show_feedback = False
                    st.experimental_rerun()

# データ管理ページの表示
def show_data_management():
    st.header('データ管理', divider='blue')
    
    # タブでセクションを分ける
    upload_tab, manage_tab, export_tab = st.tabs(["データアップロード", "データ管理", "データエクスポート"])
    
    with upload_tab:
        st.subheader('新規データアップロード')
        
        # 拡張されたファイルアップローダーの使用
        uploaded_file = enhanced_file_uploader(
            "GPXまたはCSVファイルをアップロード", 
            accepted_types=['gpx', 'csv'],
            help_text="GPXファイル: GPSトラッカーからのデータ\nCSVファイル: カンマ区切りのデータ（少なくとも緯度・経度列が必要）",
            icon="file-upload"
        )
        
        if uploaded_file:
            # メタデータの入力欄
            with st.container(border=True):
                st.subheader('データ情報')
                
                col1, col2 = st.columns(2)
                
                with col1:
                    boat_name = st.text_input(
                        'ボート名:', 
                        value=uploaded_file.name.split('.')[0],
                        help="データセットの識別名を入力してください"
                    )
                
                with col2:
                    boat_type = st.selectbox(
                        'ボートタイプ:',
                        ['470', '49er', 'Laser', 'Nacra17', 'Finn', 'その他'],
                        index=5
                    )
                
                comments = st.text_area('コメント:', placeholder='データに関する補足情報を入力（オプション）')
                
                process_btn = st.button('データを読み込む', type="primary", use_container_width=True)
                
                if process_btn:
                    with st.spinner('データを処理中...'):
                        try:
                            # ファイル種別を判定
                            file_extension = uploaded_file.name.split('.')[-1].lower()
                            
                            if file_extension == 'csv':
                                df, error = process_csv(uploaded_file)
                            elif file_extension == 'gpx':
                                df, error = process_gpx(uploaded_file)
                            else:
                                error = f'未対応のファイル形式です: {file_extension}'
                                df = None
                            
                            if error:
                                alert(error, type="error")
                            elif df is not None:
                                # セッションにデータを保存
                                st.session_state.boats_data[boat_name] = df
                                
                                # 可視化クラスにデータをロード
                                st.session_state.visualizer.boats_data[boat_name] = df
                                
                                # メタデータの保存（将来的に実装）
                                
                                alert(f'{boat_name} のデータを正常に読み込みました！', type="success")
                                
                                # データプレビュー表示
                                st.subheader('データプレビュー')
                                st.dataframe(df.head(), use_container_width=True)
                                
                                # 基本統計情報
                                stats_cols = st.columns(3)
                                with stats_cols[0]:
                                    render_metric_card("データポイント数", f"{len(df):,}", icon="table")
                                with stats_cols[1]:
                                    if 'speed' in df.columns:
                                        render_metric_card("平均速度", f"{df['speed'].mean() * 1.94384:.1f}", "ノット", icon="tachometer-alt")
                                with stats_cols[2]:
                                    if 'timestamp' in df.columns:
                                        duration = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
                                        render_metric_card("記録時間", f"{duration:.1f}", "分", icon="clock")
                            else:
                                alert('データの処理に失敗しました。', type="error")
                        except Exception as e:
                            alert(f'エラーが発生しました: {e}', type="error")
        else:
            alert('GPXまたはCSVファイルをアップロードしてください。')
            
            # サンプルデータボタン
            if st.button('サンプルデータを生成してテスト', use_container_width=True):
                with st.spinner('サンプルデータを生成中...'):
                    sample_data = generate_sample_data()
                    for boat_name, data in sample_data.items():
                        st.session_state.boats_data[boat_name] = data
                        st.session_state.visualizer.boats_data[boat_name] = data
                    alert('サンプルデータを読み込みました！', type="success")
                    st.experimental_rerun()
    
    with manage_tab:
        st.subheader('読み込み済みのデータ')
        
        if not st.session_state.boats_data:
            alert('データがまだアップロードされていません', type="info")
        else:
            # グリッドレイアウトでデータ管理カードを表示
            st.markdown('<div class="grid-container">', unsafe_allow_html=True)
            
            for boat_name, data in st.session_state.boats_data.items():
                stats = {
                    "ポイント数": f"{len(data):,}",
                    "期間": f"{(data['timestamp'].max() - data['timestamp'].min()).total_seconds() / 60:.1f}分" if 'timestamp' in data.columns else "不明",
                    "平均速度": f"{data['speed'].mean() * 1.94384:.1f}ノット" if 'speed' in data.columns else "不明"
                }
                
                card_html = f"""
                <div class="data-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h3 style="margin: 0;">{boat_name}</h3>
                        <div>
                            <button onclick="Streamlit.setComponentValue('view_{boat_name}')" 
                                    style="background: none; border: none; cursor: pointer; margin-left: 8px;">
                                <i class="fas fa-eye" title="データ表示"></i>
                            </button>
                            <button onclick="Streamlit.setComponentValue('analyze_{boat_name}')" 
                                    style="background: none; border: none; cursor: pointer; margin-left: 8px;">
                                <i class="fas fa-chart-line" title="分析"></i>
                            </button>
                            <button onclick="Streamlit.setComponentValue('delete_{boat_name}')" 
                                    style="background: none; border: none; cursor: pointer; margin-left: 8px;">
                                <i class="fas fa-trash" title="削除"></i>
                            </button>
                        </div>
                    </div>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;">
                        <div style="background-color: rgba(21, 101, 192, 0.1); border-radius: 4px; padding: 4px 8px;">
                            <span style="font-size: 12px; color: var(--text-secondary);">ポイント数</span>
                            <div style="font-weight: 600;">{stats["ポイント数"]}</div>
                        </div>
                        <div style="background-color: rgba(21, 101, 192, 0.1); border-radius: 4px; padding: 4px 8px;">
                            <span style="font-size: 12px; color: var(--text-secondary);">期間</span>
                            <div style="font-weight: 600;">{stats["期間"]}</div>
                        </div>
                        <div style="background-color: rgba(21, 101, 192, 0.1); border-radius: 4px; padding: 4px 8px;">
                            <span style="font-size: 12px; color: var(--text-secondary);">平均速度</span>
                            <div style="font-weight: 600;">{stats["平均速度"]}</div>
                        </div>
                    </div>
                </div>
                """
                
                st.markdown(card_html, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # クリックイベントの処理
            event = st.markdown("", unsafe_allow_html=True)
            if event:
                if event.startswith('view_'):
                    boat_name = event[5:]
                    st.session_state.view_boat = boat_name
                    st.experimental_rerun()
                elif event.startswith('analyze_'):
                    boat_name = event[8:]
                    st.session_state.page = 'パフォーマンス分析'
                    st.session_state.analyze_boat = boat_name
                    st.experimental_rerun()
                elif event.startswith('delete_'):
                    boat_name = event[7:]
                    if st.session_state.boats_data.pop(boat_name, None):
                        st.session_state.visualizer.boats_data.pop(boat_name, None)
                        st.success(f"{boat_name} のデータを削除しました")
                        st.experimental_rerun()
            
            # データ詳細表示
            if 'view_boat' in st.session_state and st.session_state.view_boat in st.session_state.boats_data:
                boat_name = st.session_state.view_boat
                data = st.session_state.boats_data[boat_name]
                
                with st.container(border=True):
                    st.subheader(f"{boat_name} - データ詳細")
                    
                    # データフレーム表示
                    st.dataframe(data.head(20), use_container_width=True)
                    
                    if len(data) > 20:
                        st.caption(f"表示: 最初の20行 (全{len(data)}行中)")
                    
                    # データ操作ボタン
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("閉じる", key="close_view"):
                            st.session_state.pop('view_boat', None)
                            st.experimental_rerun()
                    
                    with col2:
                        if st.button("分析へ進む", key="go_analyze"):
                            st.session_state.page = 'パフォーマンス分析'
                            st.session_state.analyze_boat = boat_name
                            st.experimental_rerun()
                    
                    with col3:
                        if st.button("マップで表示", key="show_map"):
                            st.session_state.page = 'マップビュー'
                            st.experimental_rerun()
            
            # 一括操作ボタン
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("すべてのデータを削除", type="primary", use_container_width=True):
                    confirmation = st.checkbox("削除を確認する", key="confirm_delete_all")
                    if confirmation:
                        st.session_state.boats_data = {}
                        st.session_state.visualizer.boats_data = {}
                        alert("すべてのデータを削除しました", type="success")
                        st.experimental_rerun()
            
            with col2:
                if st.button("すべてのデータをバックアップ", use_container_width=True):
                    # バックアップ機能（将来的に実装）
                    st.info("この機能は開発中です")
    
    with export_tab:
        st.subheader('データエクスポート')
        
        if not st.session_state.boats_data:
            alert('エクスポートできるデータがありません。まずデータをアップロードしてください。', type="info")
        else:
            # エクスポート設定
            col1, col2 = st.columns(2)
            
            with col1:
                export_boat = st.selectbox('エクスポートするデータを選択:', list(st.session_state.boats_data.keys()))
            
            with col2:
                export_format = st.radio('エクスポート形式:', ['CSV', 'JSON', 'Excel'], horizontal=True)
            
            # 高度なエクスポート設定
            with st.expander("詳細設定"):
                include_index = st.checkbox("インデックスを含める", value=False)
                
                if export_format == 'CSV':
                    delimiter = st.selectbox("区切り文字", [",", ";", "\\t"], index=0)
                    encoding = st.selectbox("エンコーディング", ["utf-8", "shift-jis", "cp932"], index=0)
                
                elif export_format == 'Excel':
                    sheet_name = st.text_input("シート名", value=export_boat)
                
                elif export_format == 'JSON':
                    orient = st.selectbox("JSONフォーマット", 
                                        ["records", "columns", "values", "index", "table"],
                                        index=0,
                                        help="records: リスト形式、columns: カラム優先、values: 値のみ、index: インデックス優先、table: テーブル形式")
            
            # エクスポートボタン
            if st.button('データをエクスポート', type="primary", use_container_width=True):
                try:
                    # データプロセッサを使用
                    processor = st.session_state.data_processor
                    processor.boat_data = st.session_state.boats_data  # データを設定
                    
                    # エクスポート形式を選択
                    format_type = export_format.lower()
                    exported_data = processor.export_processed_data(export_boat, format_type)
                    
                    if exported_data:
                        # バイナリデータをbase64エンコード
                        b64 = base64.b64encode(exported_data).decode()
                        
                        # ダウンロードリンクを作成
                        mime_type = {
                            'csv': 'text/csv',
                            'json': 'application/json',
                            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                        }.get(format_type, 'application/octet-stream')
                        
                        ext = {'csv': 'csv', 'json': 'json', 'excel': 'xlsx'}.get(format_type, format_type)
                        
                        href = f'<a href="data:{mime_type};base64,{b64}" download="{export_boat}.{ext}" class="download-button">\
                                <i class="fas fa-download"></i> クリックしてダウンロード</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        alert(f'{export_boat} のデータをエクスポートしました！', type="success")
                    else:
                        alert('データのエクスポートに失敗しました。', type="error")
                except Exception as e:
                    alert(f'エラーが発生しました: {e}', type="error")

# パフォーマンス分析ページの表示
def show_performance_analysis():
    st.header('パフォーマンス分析', divider='blue')
    
    if not st.session_state.boats_data:
        alert('データがありません。マップビューページからサンプルデータを生成するか、データ管理ページでデータをアップロードしてください。', type="warning")
        if st.button('サンプルデータを生成', type="primary", use_container_width=True):
            with st.spinner('サンプルデータを生成中...'):
                sample_data = generate_sample_data()
                for boat_name, data in sample_data.items():
                    st.session_state.boats_data[boat_name] = data
                    st.session_state.visualizer.boats_data[boat_name] = data
                alert('サンプルデータを読み込みました！', type="success")
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
            
            selected_boat = st.selectbox('分析するボート:', boat_options, 
                                       index=boat_options.index(default_boat) if default_boat in boat_options else 0)
            
            # グラフ選択
            plot_options = [
                '速度の時系列', 
                '風向と速度', 
                'ポーラーチャート', 
                'タック分析',
                'パフォーマンスダッシュボード'
            ]
            
            plot_type = st.selectbox('グラフタイプ:', plot_options)
            
            # 画面分割でパラメータ設定とグラフ表示
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.subheader('パラメータ設定')
                
                # グラフに応じた設定パラメータ
                with st.container(border=True):
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
                generate_button = st.button('グラフを生成', type="primary", use_container_width=True)
            
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
                                alert('このグラフには風向データが必要です', type="error")
                            else:
                                fig = performance_plots.create_wind_speed_heatmap(
                                    boat_data,
                                    bin_size=st.session_state.last_plot['params']['bin_size'],
                                    color_scale=st.session_state.last_plot['params']['color_scale'].lower()
                                )
                        elif plot_type == 'ポーラーチャート':
                            if 'wind_direction' not in boat_data.columns:
                                alert('このグラフには風向データが必要です', type="error")
                            else:
                                fig = performance_plots.create_speed_polar_plot(
                                    boat_data,
                                    max_speed=st.session_state.last_plot['params']['max_speed'],
                                    resolution=st.session_state.last_plot['params']['resolution']
                                )
                        elif plot_type == 'タック分析':
                            if 'course' not in boat_data.columns:
                                alert('このグラフにはコースデータが必要です', type="error")
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
                                alert(f'選択した指標には次の列が必要です: {", ".join(missing_cols)}', type="error")
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
                            col1, col2 = st.columns(2)
                            with col1:
                                try:
                                    img_bytes = fig.to_image(format="png", engine="kaleido")
                                    b64 = base64.b64encode(img_bytes).decode()
                                    href = f'<a href="data:image/png;base64,{b64}" download="{selected_boat}_{plot_type}.png" class="download-button">\
                                            <i class="fas fa-download"></i> PNG画像として保存</a>'
                                    st.markdown(href, unsafe_allow_html=True)
                                except Exception as e:
                                    st.warning("画像のエクスポート機能には追加のライブラリが必要です。")
                            
                            with col2:
                                try:
                                    html_str = fig.to_html(include_plotlyjs="cdn")
                                    b64 = base64.b64encode(html_str.encode()).decode()
                                    href = f'<a href="data:text/html;base64,{b64}" download="{selected_boat}_{plot_type}.html" class="download-button">\
                                            <i class="fas fa-code"></i> インタラクティブHTMLとして保存</a>'
                                    st.markdown(href, unsafe_allow_html=True)
                                except Exception as e:
                                    st.warning("HTMLエクスポート機能には追加のライブラリが必要です。")
                    
                    except Exception as e:
                        alert(f'グラフ生成中にエラーが発生しました: {e}', type="error")
                else:
                    alert('左側の「グラフを生成」ボタンをクリックしてください。', type="info")
        
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
                    with st.container(border=True):
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
                    
                    # 比較グラフ生成ボタン
                    if st.button('比較グラフを生成', type="primary", use_container_width=True):
                        with st.spinner('比較グラフを生成中...'):
                            fig = None  # 初期化
                            try:
                                # 選択したボートのデータを辞書に格納
                                data_dict = {boat: st.session_state.boats_data[boat] for boat in comparison_boats}
                                
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
                                    
                                    # エクスポートボタン
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        try:
                                            img_bytes = fig.to_image(format="png", engine="kaleido")
                                            b64 = base64.b64encode(img_bytes).decode()
                                            href = f'<a href="data:image/png;base64,{b64}" download="comparison_{comparison_type}.png" class="download-button">\
                                                    <i class="fas fa-download"></i> PNG画像として保存</a>'
                                            st.markdown(href, unsafe_allow_html=True)
                                        except Exception as e:
                                            st.warning("画像のエクスポート機能には追加のライブラリが必要です。")
                                    
                                    with col2:
                                        try:
                                            html_str = fig.to_html(include_plotlyjs="cdn")
                                            b64 = base64.b64encode(html_str.encode()).decode()
                                            href = f'<a href="data:text/html;base64,{b64}" download="comparison_{comparison_type}.html" class="download-button">\
                                                    <i class="fas fa-code"></i> インタラクティブHTMLとして保存</a>'
                                            st.markdown(href, unsafe_allow_html=True)
                                        except Exception as e:
                                            st.warning("HTMLエクスポート機能には追加のライブラリが必要です。")
                                
                            except Exception as e:
                                alert(f'比較グラフ生成中にエラーが発生しました: {e}', type="error")
                else:
                    alert('比較するには2つ以上のボートを選択してください。', type="info")
            else:
                alert('比較するにはデータが2つ以上必要です。まずはデータをアップロードしてください。', type="warning")
        
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
            
            if st.button('サマリーを生成', type="primary", use_container_width=True):
                with st.spinner('サマリーを生成中...'):
                    try:
                        # パフォーマンスサマリーの取得
                        summary = st.session_state.visualizer.create_performance_summary(summary_boat)
                        
                        if summary:
                            if summary_type == '基本統計':
                                # 基本統計を表形式で表示
                                st.subheader(f"{summary_boat} の基本統計")
                                
                                # カード形式での表示
                                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                                
                                with metrics_col1:
                                    if 'speed' in summary:
                                        render_metric_card("最高速度", f"{summary['speed']['max']:.1f}", "ノット", 
                                                      icon="tachometer-alt", color="#1565C0")
                                        render_metric_card("平均速度", f"{summary['speed']['avg']:.1f}", "ノット", 
                                                      icon="tachometer-alt", color="#1565C0")
                                
                                with metrics_col2:
                                    if 'total_distance_nm' in summary:
                                        render_metric_card("走行距離", f"{summary['total_distance_nm']:.2f}", "海里", 
                                                      icon="route", color="#26A69A")
                                    if 'duration_seconds' in summary:
                                        minutes = summary['duration_seconds'] / 60
                                        render_metric_card("走行時間", f"{minutes:.1f}", "分", 
                                                      icon="clock", color="#26A69A")
                                
                                with metrics_col3:
                                    if 'tack_count' in summary:
                                        render_metric_card("タック回数", f"{summary['tack_count']}", "", 
                                                      icon="exchange-alt", color="#FFA726")
                                    if 'vmg' in summary:
                                        render_metric_card("平均VMG", f"{summary['vmg']['avg_vmg']:.2f}", "", 
                                                      icon="compass", color="#FFA726")
                                
                                # データポイントの分布を表示
                                if 'speed' in summary:
                                    speed_data = st.session_state.boats_data[summary_boat]['speed'] * 1.94384  # m/s -> ノット
                                    
                                    # ヒストグラム（改良版）
                                    fig = px.histogram(
                                        speed_data,
                                        title="速度分布",
                                        labels={'value': '速度 (ノット)', 'count': '頻度'},
                                        nbins=20,
                                        color_discrete_sequence=['#1565C0']
                                    )
                                    fig.update_layout(
                                        plot_bgcolor='white',
                                        paper_bgcolor='white',
                                        margin=dict(l=40, r=40, t=40, b=40),
                                        font=dict(family="Arial, sans-serif"),
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            elif summary_type == '詳細分析':
                                # 詳細分析表示（タブで整理）
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
                                        
                                        # データフレームをエレガントに表示
                                        st.dataframe(pd.DataFrame(segment_data), use_container_width=True, 
                                                   column_config={"セグメント": st.column_config.TextColumn("セグメント", width="small")})
                                        
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
                                                name='速度',
                                                line=dict(color='#1565C0', width=2)
                                            ))
                                            
                                            fig.update_layout(
                                                title='速度トレンド',
                                                xaxis_title='時間 (分)',
                                                yaxis_title='速度 (ノット)',
                                                plot_bgcolor='white',
                                                paper_bgcolor='white',
                                                margin=dict(l=40, r=40, t=40, b=40),
                                                font=dict(family="Arial, sans-serif"),
                                            )
                                            
                                            st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        alert('速度セグメント分析データはありません。', type="info")
                                
                                with detail_tabs[1]:
                                    if 'tack_analysis' in summary:
                                        tack_analysis = summary['tack_analysis']
                                        
                                        # タック分析メトリクス（カード形式）
                                        metrics_cols = st.columns(3)
                                        with metrics_cols[0]:
                                            render_metric_card("タック回数", f"{summary.get('tack_count', 0)}", "",
                                                          icon="exchange-alt", color="#FFA726")
                                        with metrics_cols[1]:
                                            render_metric_card("平均速度損失", f"{tack_analysis.get('avg_loss_knots', 0):.2f}", "ノット",
                                                          icon="arrow-down", color="#EF5350")
                                        with metrics_cols[2]:
                                            render_metric_card("平均回復時間", f"{tack_analysis.get('avg_recovery_time', 0):.1f}", "秒",
                                                          icon="clock", color="#26A69A")
                                        
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
                                            st.dataframe(pd.DataFrame(tack_data), use_container_width=True)
                                    else:
                                        alert('タック分析データはありません。', type="info")
                                
                                with detail_tabs[2]:
                                    if 'vmg' in summary:
                                        vmg = summary['vmg']
                                        
                                        # VMGメトリクス（カード形式）
                                        metrics_cols = st.columns(3)
                                        with metrics_cols[0]:
                                            render_metric_card("平均VMG", f"{vmg.get('avg_vmg', 0):.2f}", "",
                                                          icon="compass", color="#1565C0")
                                        with metrics_cols[1]:
                                            render_metric_card("最大VMG", f"{vmg.get('max_vmg', 0):.2f}", "",
                                                          icon="compass", color="#1565C0")
                                        with metrics_cols[2]:
                                            render_metric_card("VMG効率", f"{vmg.get('vmg_efficiency', 0):.1f}", "%",
                                                          icon="percentage", color="#26A69A")
                                        
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
                                                },
                                                color_continuous_scale='Viridis'
                                            )
                                            fig.update_layout(
                                                plot_bgcolor='white',
                                                paper_bgcolor='white',
                                                margin=dict(l=40, r=40, t=40, b=40),
                                                font=dict(family="Arial, sans-serif"),
                                            )
                                            st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        alert('VMG分析データはありません。', type="info")
                            
                            elif summary_type == '総合レポート':
                                # 総合レポートを表示（カード形式を活用）
                                st.subheader(f"{summary_boat} の総合パフォーマンスレポート")
                                
                                # 全体評価
                                st.subheader('📊 全体評価')
                                
                                if 'overall_rating' in summary:
                                    rating = summary['overall_rating']
                                    st.progress(rating / 100)
                                    
                                    # 評価に応じたカラー選定
                                    rating_color = "#EF5350"  # 赤（低評価）
                                    if rating >= 80:
                                        rating_color = "#26A69A"  # 緑（高評価）
                                    elif rating >= 50:
                                        rating_color = "#FFA726"  # オレンジ（中評価）
                                    
                                    st.markdown(f"""
                                    <div style="text-align: center; margin: 20px 0;">
                                        <span style="font-size: 36px; color: {rating_color}; font-weight: bold;">{rating}/100</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # 主要指標サマリー
                                st.subheader('📈 主要指標')
                                
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    with st.container(border=True):
                                        st.markdown("### 速度指標")
                                        if 'speed' in summary:
                                            speed_stats = summary['speed']
                                            st.markdown(f"""
                                            <div style="margin: 10px 0;">
                                                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                    <i class="fas fa-tachometer-alt" style="color: #1565C0; font-size: 18px; width: 24px;"></i>
                                                    <span style="margin-left: 10px;">最高速度: <b>{speed_stats['max']:.2f} ノット</b></span>
                                                </div>
                                                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                    <i class="fas fa-tachometer-alt" style="color: #1565C0; font-size: 18px; width: 24px;"></i>
                                                    <span style="margin-left: 10px;">平均速度: <b>{speed_stats['avg']:.2f} ノット</b></span>
                                                </div>
                                                <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                    <i class="fas fa-tachometer-alt" style="color: #1565C0; font-size: 18px; width: 24px;"></i>
                                                    <span style="margin-left: 10px;">最低速度: <b>{speed_stats['min']:.2f} ノット</b></span>
                                                </div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        if 'total_distance_nm' in summary:
                                            st.markdown(f"""
                                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                <i class="fas fa-route" style="color: #26A69A; font-size: 18px; width: 24px;"></i>
                                                <span style="margin-left: 10px;">走行距離: <b>{summary['total_distance_nm']:.2f} 海里</b></span>
                                            </div>
                                            """, unsafe_allow_html=True)
                                
                                with col2:
                                    with st.container(border=True):
                                        st.markdown("### 運航指標")
                                        html_content = ""
                                        
                                        if 'tack_count' in summary:
                                            html_content += f"""
                                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                <i class="fas fa-exchange-alt" style="color: #FFA726; font-size: 18px; width: 24px;"></i>
                                                <span style="margin-left: 10px;">タック回数: <b>{summary['tack_count']}</b></span>
                                            </div>
                                            """
                                        
                                        if 'tack_analysis' in summary:
                                            tack_analysis = summary['tack_analysis']
                                            html_content += f"""
                                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                <i class="fas fa-clock" style="color: #FFA726; font-size: 18px; width: 24px;"></i>
                                                <span style="margin-left: 10px;">平均タック回復時間: <b>{tack_analysis.get('avg_recovery_time', 0):.1f} 秒</b></span>
                                            </div>
                                            """
                                        
                                        if 'vmg' in summary:
                                            vmg = summary['vmg']
                                            html_content += f"""
                                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                <i class="fas fa-compass" style="color: #FFA726; font-size: 18px; width: 24px;"></i>
                                                <span style="margin-left: 10px;">VMG効率: <b>{vmg.get('vmg_efficiency', 0):.1f}%</b></span>
                                            </div>
                                            """
                                        
                                        if html_content:
                                            st.markdown(html_content, unsafe_allow_html=True)
                                        else:
                                            st.write("指標データがありません")
                                
                                # 改善点
                                st.subheader('📝 改善点とアドバイス')
                                
                                with st.container(border=True):
                                    if 'improvement_points' in summary:
                                        for i, point in enumerate(summary['improvement_points']):
                                            st.markdown(f"""
                                            <div style="display: flex; align-items: flex-start; margin-bottom: 10px;">
                                                <div style="background-color: #1565C0; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; justify-content: center; align-items: center; margin-right: 10px; flex-shrink: 0;">
                                                    {i+1}
                                                </div>
                                                <div>{point}</div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                    else:
                                        # 改善点がない場合は自動生成
                                        improvement_points = []
                                        
                                        if 'speed' in summary and 'tack_analysis' in summary:
                                            speed = summary['speed']
                                            tack = summary['tack_analysis']
                                            
                                            improvement_points.append("速度の安定性を高めることで平均速度の向上が見込めます")
                                            
                                            if tack.get('avg_loss_knots', 0) > 1.0:
                                                improvement_points.append("タック時の速度損失を低減することで効率が向上します")
                                            
                                            if 'vmg' in summary and summary['vmg'].get('vmg_efficiency', 0) < 80:
                                                improvement_points.append("風上帆走時のVMG効率の改善が推奨されます")
                                        
                                        if not improvement_points:
                                            improvement_points = ["十分なデータがないため、詳細な改善点を提案できません"]
                                            
                                        for i, point in enumerate(improvement_points):
                                            st.markdown(f"""
                                            <div style="display: flex; align-items: flex-start; margin-bottom: 10px;">
                                                <div style="background-color: #1565C0; color: white; border-radius: 50%; width: 24px; height: 24px; display: flex; justify-content: center; align-items: center; margin-right: 10px; flex-shrink: 0;">
                                                    {i+1}
                                                </div>
                                                <div>{point}</div>
                                            </div>
                                            """, unsafe_allow_html=True)
                                
                                # データ品質評価
                                st.subheader('📋 データ品質評価')
                                
                                with st.container(border=True):
                                    if 'data_quality' in summary:
                                        quality = summary['data_quality']
                                        st.markdown(f"""
                                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                            <i class="fas fa-chart-line" style="color: #1565C0; font-size: 18px; width: 24px;"></i>
                                            <span style="margin-left: 10px;">サンプリング密度: <b>{quality.get('sampling_rate', 0):.2f} Hz</b></span>
                                        </div>
                                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                            <i class="fas fa-clock" style="color: #1565C0; font-size: 18px; width: 24px;"></i>
                                            <span style="margin-left: 10px;">データ期間: <b>{quality.get('duration_minutes', 0):.1f} 分</b></span>
                                        </div>
                                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                            <i class="fas fa-table" style="color: #1565C0; font-size: 18px; width: 24px;"></i>
                                            <span style="margin-left: 10px;">データポイント: <b>{quality.get('points_count', 0)}</b></span>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        if 'noise_level' in quality:
                                            noise_color = "#26A69A"  # 緑（低ノイズ）
                                            if quality['noise_level'] == "高":
                                                noise_color = "#EF5350"  # 赤（高ノイズ）
                                            elif quality['noise_level'] == "中":
                                                noise_color = "#FFA726"  # オレンジ（中ノイズ）
                                                
                                            st.markdown(f"""
                                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                <i class="fas fa-wave-square" style="color: {noise_color}; font-size: 18px; width: 24px;"></i>
                                                <span style="margin-left: 10px;">ノイズレベル: <b style="color: {noise_color};">{quality['noise_level']}</b></span>
                                            </div>
                                            """, unsafe_allow_html=True)
                                    else:
                                        # データ品質情報がない場合の表示
                                        points_count = len(st.session_state.boats_data[summary_boat])
                                        
                                        if 'timestamp' in st.session_state.boats_data[summary_boat].columns:
                                            df = st.session_state.boats_data[summary_boat]
                                            duration = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
                                            sampling_rate = points_count / (duration * 60) if duration > 0 else 0
                                            
                                            st.markdown(f"""
                                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                <i class="fas fa-chart-line" style="color: #1565C0; font-size: 18px; width: 24px;"></i>
                                                <span style="margin-left: 10px;">サンプリング密度: <b>{sampling_rate:.2f} Hz</b></span>
                                            </div>
                                            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                                <i class="fas fa-clock" style="color: #1565C0; font-size: 18px; width: 24px;"></i>
                                                <span style="margin-left: 10px;">データ期間: <b>{duration:.1f} 分</b></span>
                                            </div>
                                            """, unsafe_allow_html=True)
                                        
                                        st.markdown(f"""
                                        <div style="display: flex; align-items: center; margin-bottom: 8px;">
                                            <i class="fas fa-table" style="color: #1565C0; font-size: 18px; width: 24px;"></i>
                                            <span style="margin-left: 10px;">データポイント: <b>{points_count}</b></span>
                                        </div>
                                        """, unsafe_allow_html=True)
                        else:
                            alert(f"{summary_boat} のパフォーマンスサマリーを生成できませんでした", type="warning")
                    
                    except Exception as e:
                        alert(f'サマリー生成中にエラーが発生しました: {e}', type="error")

# 戦略評価ページの表示
def show_strategy_evaluation():
    st.header('戦略評価', divider='blue')
    
    # コンテンツ準備中メッセージ
    with st.container(border=True):
        st.markdown("""
        <div style="text-align: center; padding: 20px;">
            <i class="fas fa-tools" style="font-size: 48px; color: var(--accent-color); margin-bottom: 16px;"></i>
            <h2 style="margin-bottom: 16px;">この機能は開発中です</h2>
            <p>戦略評価機能は現在開発中で、近日中にリリース予定です。</p>
            <p>この機能では以下のことができるようになります：</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            * 戦略的判断ポイントの自動検出
            * 戦略的意思決定の最適性評価
            * 他の選手との戦略比較
            * 戦略改善のためのアドバイス
            """)
        
        with col2:
            st.markdown("""
            * 風向シフトの予測と検出
            * 最適なコース選択のシミュレーション
            * レースシナリオの分析
            * レース戦略の視覚化
            """)
    
    # フィーチャープレビュー
    st.subheader('機能プレビュー')
    
    # プレビュー画像または動画を表示
    col1, col2 = st.columns(2)
    
    with col1:
        # プレースホルダー画像を表示
        st.markdown("""
        <div style="border: 1px solid #EEEEEE; border-radius: 8px; padding: 16px; text-align: center; background-color: #FAFAFA;">
            <i class="fas fa-wind" style="font-size: 64px; color: #1565C0; margin-bottom: 16px;"></i>
            <h3>風向シフト分析</h3>
            <p>風向変化を検出し、最適なコース選択をサポート</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # プレースホルダー画像を表示
        st.markdown("""
        <div style="border: 1px solid #EEEEEE; border-radius: 8px; padding: 16px; text-align: center; background-color: #FAFAFA;">
            <i class="fas fa-chess" style="font-size: 64px; color: #26A69A; margin-bottom: 16px;"></i>
            <h3>戦略的判断ポイント</h3>
            <p>重要な意思決定ポイントを特定し評価</p>
        </div>
        """, unsafe_allow_html=True)
    
    # ベータテスター募集
    st.subheader('ベータテスター募集')
    
    with st.container(border=True):
        st.markdown("""
        この機能のベータテストにご興味があれば、以下のフォームにご記入ください。
        新機能がリリースされた際にいち早くアクセスできます。
        """)
        
        with st.form("beta_tester_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("お名前")
                email = st.text_input("メールアドレス")
            
            with col2:
                experience = st.selectbox("セーリング経験", ["初心者", "中級者", "上級者", "プロ/指導者"])
                interests = st.multiselect("関心のある機能", 
                                        ["風向シフト分析", "戦略的判断評価", "レースシナリオ分析", "他の選手との比較"])
            
            comments = st.text_area("コメントやリクエスト", height=100)
            submitted = st.form_submit_button("登録する", type="primary")
            
            if submitted:
                # ここで登録処理を行う（将来的に実装）
                st.success("ベータテスター登録を受け付けました。ありがとうございます！")

# 設定ページの表示
def show_settings():
    st.header('システム設定', divider='blue')
    
    # 設定タブ
    tabs = st.tabs(["一般設定", "表示設定", "データ設定", "高度な設定"])
    
    with tabs[0]:
        st.subheader('一般設定')
        
        with st.container(border=True):
            # ユーザー設定
            st.subheader('ユーザー設定')
            
            col1, col2 = st.columns(2)
            
            with col1:
                user_name = st.text_input("ユーザー名", value="Guest User")
            
            with col2:
                language = st.selectbox("言語", ["日本語", "English", "中文", "Français", "Deutsch"])
            
            # 保存ボタン
            st.button("設定を保存", type="primary")
        
        with st.container(border=True):
            # 通知設定
            st.subheader('通知設定')
            
            email_notifications = st.checkbox("メール通知を受け取る", value=False)
            
            if email_notifications:
                notification_email = st.text_input("通知用メールアドレス")
                
                st.multiselect("通知を受け取るイベント", 
                              ["重要な更新", "データ処理完了", "エラーとバグ", "ヒントとコツ"],
                              default=["重要な更新", "エラーとバグ"])
            
            # 保存ボタン
            st.button("通知設定を保存", type="primary")
    
    with tabs[1]:
        st.subheader('表示設定')
        
        with st.container(border=True):
            # テーマ設定
            st.subheader('テーマ設定')
            
            theme = st.radio("テーマ", ["ライト", "ダーク", "システムに合わせる"], horizontal=True)
            
            # カラーパレット選択
            st.color_picker("アクセントカラー", "#1565C0")
            
            # フォント設定
            font_size = st.slider("フォントサイズ", 12, 24, 14)
            font_family = st.selectbox("フォント", ["システムフォント", "Arial", "Roboto", "Noto Sans JP"])
        
        with st.container(border=True):
            # マップ表示設定
            st.subheader('マップ表示設定')
            
            default_map_style = st.selectbox("デフォルトマップスタイル", 
                                           list(st.session_state.map_display.available_tiles.keys()))
            
            show_grid = st.checkbox("グリッド線を表示", value=True)
            
            map_colors = st.selectbox("マップカラースキーム", 
                                    ["デフォルト", "高コントラスト", "パステル", "モノクロ"])
            
            # 保存ボタン
            st.button("表示設定を保存", type="primary")
    
    with tabs[2]:
        st.subheader('データ設定')
        
        with st.container(border=True):
            # データ処理設定
            st.subheader('データ処理設定')
            
            smooth_factor = st.slider("GPSスムージング係数", 0.0, 1.0, 0.2, 0.05)
            
            outlier_threshold = st.slider("異常値検出閾値", 1.0, 5.0, 3.0, 0.1)
            
            col1, col2 = st.columns(2)
            
            with col1:
                timestamp_format = st.selectbox("タイムスタンプ形式", 
                                              ["ISO 8601", "YYYY/MM/DD HH:MM:SS", "MM/DD/YYYY HH:MM:SS"])
            
            with col2:
                speed_unit = st.selectbox("速度単位", ["ノット", "km/h", "m/s"])
        
        with st.container(border=True):
            # データストレージ設定
            st.subheader('データストレージ')
            
            storage_option = st.radio("データ保存方法", ["ローカル", "クラウド同期"], horizontal=True)
            
            auto_save = st.checkbox("自動保存を有効にする", value=True)
            
            if auto_save:
                auto_save_interval = st.selectbox("保存間隔", ["5分ごと", "10分ごと", "30分ごと", "1時間ごと"])
            
            # データのバックアップと回復
            st.subheader("バックアップと回復")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.button("データをバックアップ", use_container_width=True)
            
            with col2:
                st.button("バックアップから復元", use_container_width=True)
            
            # 保存ボタン
            st.button("データ設定を保存", type="primary")
    
    with tabs[3]:
        st.subheader('高度な設定')
        
        with st.container(border=True):
            # パフォーマンス設定
            st.subheader('パフォーマンス設定')
            
            cache_size = st.slider("キャッシュサイズ (MB)", 50, 1000, 200, 50)
            
            threading = st.checkbox("マルチスレッド処理を有効にする", value=True)
            
            if threading:
                thread_count = st.number_input("スレッド数", 1, 16, 4)
        
        with st.container(border=True):
            # デバッグ設定
            st.subheader('デバッグ設定')
            
            debug_mode = st.checkbox("デバッグモードを有効にする", value=False)
            
            if debug_mode:
                log_level = st.selectbox("ログレベル", ["ERROR", "WARNING", "INFO", "DEBUG"])
                
                st.checkbox("詳細ログを有効にする", value=False)
        
        with st.container(border=True):
            # リセットとクリア
            st.subheader('リセットとクリア')
            
            st.warning("以下の操作は元に戻せません。注意して実行してください。")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("設定をリセット", use_container_width=True):
                    reset_confirm = st.checkbox("リセットを確認", key="reset_confirm")
                    if reset_confirm:
                        # リセット処理（将来的に実装）
                        st.success("設定をリセットしました")
            
            with col2:
                if st.button("全データを消去", use_container_width=True):
                    clear_confirm = st.checkbox("消去を確認", key="clear_confirm")
                    if clear_confirm:
                        # データ消去処理（将来的に実装）
                        st.success("全データを消去しました")
        
        # 保存ボタン
        st.button("高度な設定を保存", type="primary")

# フィードバックコンポーネント（全ページ下部に表示）
def show_feedback_button():
    with st.container():
        st.markdown("""
        <div style="text-align: center; margin-top: 30px; padding: 10px;">
            <a href="#" onclick="Streamlit.setComponentValue('show_feedback_form');" 
               style="color: var(--accent-color); text-decoration: none; font-size: 14px;">
                <i class="fas fa-comment"></i> フィードバックを送る
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        # フィードバックボタンがクリックされた場合
        clicked = st.markdown("", unsafe_allow_html=True)
        if clicked == 'show_feedback_form':
            st.session_state.show_feedback = True
            st.experimental_rerun()

# メイン関数
def main():
    # ナビゲーションバーを表示
    page = create_navigation()
    
    # ページに応じたコンテンツを表示
    if page == "マップビュー":
        show_map_view()
    elif page == "データ管理":
        show_data_management()
    elif page == "パフォーマンス分析":
        show_performance_analysis()
    elif page == "戦略評価":
        show_strategy_evaluation()
    elif page == "設定":
        show_settings()
    
    # フィードバックボタン
    show_feedback_button()

if __name__ == "__main__":
    main()
