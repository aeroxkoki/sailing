"""
セーリング戦略分析システム - メインアプリケーション（Version 3）

フェーズ2で実装された新しいUI/UXデザインを反映したメインアプリケーション
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
import folium
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 自作モジュールのインポート
from ui.components import (load_css, create_navigation, render_metric_card, alert, 
                          action_button_group, section_header, data_card, interactive_data_card,
                          interactive_map, map_settings_panel, enhanced_file_uploader,
                          process_file, export_dataframe, feedback_form, dataset_comparison_viewer,
                          styled_tabs, time_range_selector)

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

# グローバルCSSをロード
load_css()

# ユーザーフィードバック機能（どのページからでも利用可能）
with st.sidebar:
    feedback_data = feedback_form("機能フィードバック")
    if feedback_data:
        # ここでフィードバックデータを保存または処理
        # 実際の実装では外部ストレージやAPIに送信
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        feedback_file = Path("feedback") / f"feedback_{timestamp}.json"
        os.makedirs(Path("feedback"), exist_ok=True)
        
        try:
            with open(feedback_file, "w", encoding="utf-8") as f:
                json.dump(feedback_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"フィードバックの保存中にエラーが発生しました: {str(e)}")

# セッション状態の初期化
def initialize_session_state():
    """セッション状態を初期化する"""
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
    if 'display_settings' not in st.session_state:
        # デフォルトの表示設定
        st.session_state.display_settings = {
            "map_tile": "OpenStreetMap",
            "show_labels": True,
            "show_tracks": True,
            "show_markers": True,
            "sync_time": False,
            "marker_size": 10,
            "line_width": 3,
            "opacity": 0.8
        }
    if 'page' not in st.session_state:
        st.session_state.page = "マップビュー"

# セッション状態を初期化
initialize_session_state()

# サンプルデータ生成関数
def generate_sample_data():
    """テスト用のサンプルデータを生成"""
    # 艇1のデータ
    boat1_timestamps = pd.date_range(start='2025-03-01 10:00:00', periods=100, freq='10S')
    
    boat1_data = pd.DataFrame({
        'timestamp': boat1_timestamps,
        'latitude': 35.45 + np.cumsum(np.random.normal(0, 0.0001, 100)),
        'longitude': 139.65 + np.cumsum(np.random.normal(0, 0.0001, 100)),
        'speed': 5 + np.random.normal(0, 0.5, 100),
        'course': 45 + np.random.normal(0, 5, 100),
        'wind_direction': 90 + np.random.normal(0, 3, 100)
    })
    
    # 艇2のデータ
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

# サイドバーのナビゲーション
selected_page = create_navigation()

# 選択されたページに応じた表示
if selected_page == "マップビュー":
    # マップビューページ
    st.title('セーリング航跡マップ')
    
    # 2カラムレイアウト
    map_col, settings_col = st.columns([3, 1])
    
    with settings_col:
        st.subheader('表示設定')
        
        # データがないときのメッセージとサンプルデータボタン
        if not st.session_state.boats_data:
            alert('データがありません。データ管理ページでアップロードするか、サンプルデータを使用してください。', 'warning')
            if st.button('サンプルデータを生成', type="primary"):
                with st.spinner('サンプルデータを生成中...'):
                    sample_data = generate_sample_data()
                    for boat_name, data in sample_data.items():
                        st.session_state.boats_data[boat_name] = data
                        st.session_state.visualizer.boats_data[boat_name] = data
                    alert('サンプルデータを読み込みました！', 'success')
                    st.experimental_rerun()
        else:
            # 表示するボートの選択
            boat_options = list(st.session_state.boats_data.keys())
            selected_boats = st.multiselect(
                '表示する艇:',
                boat_options,
                default=boat_options,
                key='map_selected_boats'
            )
            
            # マップ設定パネル
            map_tiles = st.session_state.map_display.available_tiles
            settings = map_settings_panel(map_tiles, default_tile="OpenStreetMap")
            
            # 設定をセッションに保存
            st.session_state.display_settings.update(settings)
            
            # マップ表示ボタン
            update_cols = st.columns(2)
            with update_cols[0]:
                if st.button('マップを更新', type="primary", key="update_map"):
                    st.session_state.map_refresh = True
            
            with update_cols[1]:
                if st.button('新ウィンドウで表示', key="map_new_window"):
                    # 実際の実装では、外部ページへのリンクやモーダルウィンドウを表示
                    alert('この機能は開発中です。', 'info')
            
            # データ統計サマリー
            if selected_boats:
                st.subheader('データサマリー')
                
                for boat_name in selected_boats:
                    if boat_name in st.session_state.boats_data:
                        df = st.session_state.boats_data[boat_name]
                        
                        with st.expander(f"{boat_name} の統計", expanded=False):
                            # 基本統計を表示
                            stats_cols = st.columns(3)
                            
                            with stats_cols[0]:
                                if 'speed' in df.columns:
                                    avg_speed = df['speed'].mean() * 1.94384  # m/s -> ノット
                                    max_speed = df['speed'].max() * 1.94384
                                    render_metric_card(
                                        "平均速度",
                                        f"{avg_speed:.1f}",
                                        "ノット",
                                        f"最高: {max_speed:.1f} ノット",
                                        "tachometer-alt",
                                        "#1565C0"
                                    )
                            
                            with stats_cols[1]:
                                if 'timestamp' in df.columns:
                                    duration = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
                                    distance = None
                                    # 総距離を計算（実装されていれば）
                                    if hasattr(st.session_state.data_processor, 'calculate_distance'):
                                        distance = st.session_state.data_processor.calculate_distance(df)
                                    
                                    render_metric_card(
                                        "記録時間",
                                        f"{duration:.1f}",
                                        "分",
                                        f"データ点数: {len(df):,}",
                                        "clock",
                                        "#26A69A"
                                    )
                            
                            with stats_cols[2]:
                                # 風向の統計またはコースの統計
                                if 'wind_direction' in df.columns:
                                    avg_wind = df['wind_direction'].mean()
                                    render_metric_card(
                                        "平均風向",
                                        f"{avg_wind:.1f}",
                                        "°",
                                        "真北から時計回り",
                                        "wind",
                                        "#FFA726"
                                    )
                                elif 'course' in df.columns:
                                    avg_course = df['course'].mean()
                                    render_metric_card(
                                        "平均コース",
                                        f"{avg_course:.1f}",
                                        "°",
                                        "真北から時計回り",
                                        "compass",
                                        "#FFA726"
                                    )
    
    # マップ表示エリア
    with map_col:
        if st.session_state.boats_data and 'map_selected_boats' in st.session_state and st.session_state.map_selected_boats:
            selected_boats = st.session_state.map_selected_boats
            
            try:
                # 地図の中心を計算
                center = get_map_center({k: st.session_state.boats_data[k] for k in selected_boats if k in st.session_state.boats_data})
                st.session_state.last_center = center
                
                # マップオブジェクトの作成
                map_display = st.session_state.map_display
                display_settings = st.session_state.display_settings
                
                map_object = map_display.create_map(
                    tile=display_settings["tile"],
                    center=center
                )
                
                # 複数艇表示機能を使用
                map_object = st.session_state.visualizer.visualize_multiple_boats(
                    boat_names=selected_boats,
                    map_object=map_object,
                    show_labels=display_settings["show_labels"],
                    show_tracks=display_settings["show_tracks"],
                    show_markers=display_settings["show_markers"],
                    sync_time=display_settings["sync_time"],
                    marker_size=display_settings["marker_size"],
                    line_width=display_settings["line_width"],
                    opacity=display_settings["opacity"]
                )
                
                # インタラクティブマップを表示
                interactive_map(map_object, width=800, height=600, with_controls=True)
                
            except Exception as e:
                alert(f'マップ生成中にエラーが発生しました: {e}', 'error')
        else:
            # データがないときのプレースホルダマップ
            if not st.session_state.boats_data:
                alert('データがアップロードされていません。右側の「サンプルデータを生成」ボタンを押すか、データ管理ページでデータをアップロードしてください。', 'info')
            elif not ('map_selected_boats' in st.session_state and st.session_state.map_selected_boats):
                alert('表示する艇が選択されていません。右側のパネルから艇を選択してください。', 'info')
                
            # デフォルトマップ表示
            m = folium.Map(location=[35.45, 139.65], zoom_start=12)
            interactive_map(m, width=800, height=600, with_controls=False)

elif selected_page == "データ管理":
    # データ管理ページ
    section_header('データ管理', '航跡データのアップロード、管理、エクスポートを行います。')
    
    # タブでセクションを分ける
    tab_labels = ["データアップロード", "データ管理", "データエクスポート"]
    active_tab = styled_tabs(tab_labels)
    
    if active_tab == 0:  # データアップロード
        st.subheader('新規データアップロード')
        
        # 拡張ファイルアップローダー
        uploaded_file = enhanced_file_uploader(
            "GPXまたはCSVファイルをアップロード",
            accepted_types=["gpx", "csv", "xlsx", "xls", "json"],
            help_text="GPXファイル: GPSトラッカーからのデータ\nCSVファイル: カンマ区切りのデータ（少なくとも緯度・経度列が必要）",
            key="file_uploader"
        )
        
        if uploaded_file:
            # アップロードファイルの処理
            col1, col2 = st.columns(2)
            
            with col1:
                # ボート名入力
                boat_name = st.text_input(
                    'ボート名:',
                    value=uploaded_file.name.split('.')[0],
                    help="データセットの識別名を入力してください",
                    key="boat_name_input"
                )
            
            with col2:
                file_type = uploaded_file.name.split('.')[-1].lower()
                if file_type == "csv":
                    encoding = st.selectbox(
                        "ファイルエンコーディング:",
                        options=["utf-8", "shift-jis", "cp932", "euc-jp", "latin1"],
                        index=0,
                        help="CSVファイルの文字エンコーディングを選択してください",
                        key="encoding_select"
                    )
                else:
                    encoding = "utf-8"
            
            # データ処理ボタン
            if st.button('データを読み込む', type="primary", key="process_data_btn"):
                with st.spinner('データを処理中...'):
                    try:
                        # 自動ファイルタイプ検出と処理
                        df, error = process_file(uploaded_file, encoding=encoding)
                        
                        if error:
                            alert(error, 'error')
                        elif df is not None:
                            # セッションにデータを保存
                            st.session_state.boats_data[boat_name] = df
                            st.session_state.visualizer.boats_data[boat_name] = df
                            
                            alert(f'{boat_name} のデータを正常に読み込みました！', 'success')
                            
                            # データプレビュー表示
                            st.subheader('データプレビュー')
                            st.dataframe(df.head(), use_container_width=True)
                            
                            # 基本統計情報
                            stats_cols = st.columns(3)
                            with stats_cols[0]:
                                render_metric_card(
                                    "データポイント数",
                                    f"{len(df):,}",
                                    "",
                                    "",
                                    "database"
                                )
                            with stats_cols[1]:
                                if 'speed' in df.columns:
                                    avg_speed = df['speed'].mean() * 1.94384  # m/s -> ノット
                                    render_metric_card(
                                        "平均速度",
                                        f"{avg_speed:.1f}",
                                        "ノット",
                                        "",
                                        "tachometer-alt"
                                    )
                            with stats_cols[2]:
                                if 'timestamp' in df.columns:
                                    duration = (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
                                    render_metric_card(
                                        "記録時間",
                                        f"{duration:.1f}",
                                        "分",
                                        "",
                                        "clock"
                                    )
                        else:
                            alert('データの処理に失敗しました。', 'error')
                    except Exception as e:
                        alert(f'エラーが発生しました: {e}', 'error')
        else:
            # サンプルデータボタン
            st.info('GPXまたはCSVファイルをアップロードしてください。代わりにサンプルデータを生成することもできます。')
            
            if st.button('サンプルデータを生成してテスト', key="gen_sample_data_btn"):
                with st.spinner('サンプルデータを生成中...'):
                    sample_data = generate_sample_data()
                    for boat_name, data in sample_data.items():
                        st.session_state.boats_data[boat_name] = data
                        st.session_state.visualizer.boats_data[boat_name] = data
                    alert('サンプルデータを読み込みました！', 'success')
                    st.experimental_rerun()
    
    elif active_tab == 1:  # データ管理
        st.subheader('読み込み済みのデータ')
        
        if not st.session_state.boats_data:
            alert('データがまだアップロードされていません', 'info')
        else:
            # データセット数を表示
            st.write(f"読み込み済みデータセット: {len(st.session_state.boats_data)}件")
            
            # データ一覧のグリッド表示
            for i, (boat_name, data) in enumerate(st.session_state.boats_data.items()):
                # 各データセットをインタラクティブカードで表示
                info_text = []
                info_text.append(f"データ点数: {len(data):,}")
                if 'timestamp' in data.columns:
                    duration = (data['timestamp'].max() - data['timestamp'].min()).total_seconds() / 60
                    info_text.append(f"期間: {duration:.1f}分")
                if 'speed' in data.columns:
                    info_text.append(f"平均速度: {data['speed'].mean() * 1.94384:.1f}ノット")
                
                footer = " | ".join(info_text)
                
                # カードのアクション定義
                def get_view_action(name):
                    return lambda: st.session_state.update(view_data=name)
                
                def get_analyze_action(name):
                    def action():
                        st.session_state.page = 'パフォーマンス分析'
                        st.session_state.analyze_boat = name
                        st.experimental_rerun()
                    return action
                
                def get_delete_action(name):
                    def action():
                        if st.session_state.boats_data.pop(name, None):
                            st.session_state.visualizer.boats_data.pop(name, None)
                            st.success(f"{name} のデータを削除しました")
                            st.experimental_rerun()
                    return action
                
                # アクションの定義
                actions = [
                    ("表示", "eye", get_view_action(boat_name)),
                    ("分析", "chart-bar", get_analyze_action(boat_name)),
                    ("削除", "trash", get_delete_action(boat_name))
                ]
                
                # データセットのプレビュー（最初の数行）を表示
                preview = data.head(3) if 'view_data' not in st.session_state or st.session_state.view_data != boat_name else data.head(10)
                
                # インタラクティブカードの表示
                interactive_data_card(
                    title=boat_name,
                    content=preview,
                    actions=actions,
                    footer=footer,
                    expanded=st.session_state.get('view_data') == boat_name,
                    key=f"data_card_{i}"
                )
            
            # すべてのデータを削除するボタン
            if st.button("すべてのデータを削除", type="primary"):
                st.session_state.boats_data = {}
                st.session_state.visualizer.boats_data = {}
                alert("すべてのデータを削除しました", 'success')
                st.experimental_rerun()
    
    elif active_tab == 2:  # データエクスポート
        st.subheader('データエクスポート')
        
        if not st.session_state.boats_data:
            alert('エクスポートできるデータがありません。まずデータをアップロードしてください。', 'info')
        else:
            # エクスポート設定
            export_boat = st.selectbox(
                'エクスポートするデータを選択:',
                list(st.session_state.boats_data.keys()),
                key="export_boat_select"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                export_format = st.radio(
                    'エクスポート形式:',
                    ['CSV', 'JSON', 'Excel'],
                    horizontal=True,
                    key="export_format_radio"
                )
            
            with col2:
                include_index = st.checkbox(
                    'インデックスを含める',
                    value=False,
                    key="include_index_checkbox"
                )
            
            # エクスポート前にプレビュー表示
            if export_boat in st.session_state.boats_data:
                st.subheader("データプレビュー")
                st.dataframe(
                    st.session_state.boats_data[export_boat].head(),
                    use_container_width=True
                )
            
            # エクスポートボタン
            if st.button('データをエクスポート', type="primary", key="export_data_btn"):
                try:
                    # 選択したデータを取得
                    df = st.session_state.boats_data[export_boat]
                    
                    # 選択した形式でエクスポート
                    format_type = export_format.lower()
                    data, filename, mime = export_dataframe(
                        df,
                        format=format_type,
                        filename=f"{export_boat}_export",
                        include_index=include_index
                    )
                    
                    if data:
                        # ダウンロードリンクを生成
                        b64 = base64.b64encode(data).decode()
                        href = f'<a href="data:{mime};base64,{b64}" download="{filename}" class="download-button">ダウンロード：{filename}</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        alert('エクスポートが完了しました！ダウンロードリンクをクリックしてファイルを保存してください。', 'success')
                    else:
                        alert('データのエクスポートに失敗しました。', 'error')
                except Exception as e:
                    alert(f'エラーが発生しました: {e}', 'error')

elif selected_page == "パフォーマンス分析":
    # パフォーマンス分析ページ
    section_header('パフォーマンス分析', 'セーリングデータの詳細なパフォーマンス分析を行います。')
    
    if not st.session_state.boats_data:
        alert('データがありません。マップビューページからサンプルデータを生成するか、データ管理ページでデータをアップロードしてください。', 'warning')
        if st.button('サンプルデータを生成', key="gen_sample_perform_btn"):
            with st.spinner('サンプルデータを生成中...'):
                sample_data = generate_sample_data()
                for boat_name, data in sample_data.items():
                    st.session_state.boats_data[boat_name] = data
                    st.session_state.visualizer.boats_data[boat_name] = data
                alert('サンプルデータを読み込みました！', 'success')
                st.experimental_rerun()
    else:
        # 分析タブ
        tab_labels = ["単艇分析", "複数艇比較", "パフォーマンスサマリー"]
        active_tab = styled_tabs(tab_labels)
        
        if active_tab == 0:  # 単艇分析
            st.subheader('単艇分析')
            
            # 分析対象ボートの選択
            boat_options = list(st.session_state.boats_data.keys())
            
            # 前の画面から選択されたボートがあれば優先的に選択
            default_boat = st.session_state.get('analyze_boat', boat_options[0] if boat_options else None)
            if default_boat not in boat_options and boat_options:
                default_boat = boat_options[0]
            
            selected_boat = st.selectbox(
                '分析するボート:',
                boat_options,
                index=boat_options.index(default_boat) if default_boat in boat_options else 0,
                key="analyze_boat_select"
            )
            
            # グラフ選択
            plot_options = [
                '速度の時系列',
                '風向と速度',
                'ポーラーチャート',
                'タック分析',
                'パフォーマンスダッシュボード'
            ]
            
            plot_type = st.selectbox(
                'グラフ:',
                plot_options,
                key="plot_type_select"
            )
            
            # 画面分割でパラメータ設定とグラフ表示
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.subheader('パラメータ設定')
                
                # グラフに応じた設定パラメータ
                if plot_type == '速度の時系列':
                    smooth = st.slider('平滑化レベル:', 0, 10, 2, help="0:なし、10:最大平滑化", key="smooth_slider")
                    show_raw = st.checkbox('生データも表示', value=False, key="show_raw_checkbox")
                    
                    if 'timestamp' in st.session_state.boats_data[selected_boat].columns:
                        # 時間範囲選択
                        start_time, end_time = time_range_selector(
                            st.session_state.boats_data[selected_boat],
                            key_prefix="speed_time"
                        )
                
                elif plot_type == '風向と速度':
                    bin_size = st.slider('ビンサイズ (度):', 5, 30, 10, step=5, key="bin_size_slider")
                    color_scale = st.selectbox(
                        'カラースケール:',
                        ['Viridis', 'Plasma', 'Inferno', 'Magma', 'Cividis'],
                        key="color_scale_select"
                    )
                
                elif plot_type == 'ポーラーチャート':
                    max_speed = st.slider('最大速度 (ノット):', 5, 30, 15, step=1, key="max_speed_slider")
                    resolution = st.slider('解像度:', 8, 72, 36, step=8, key="resolution_slider")
                
                elif plot_type == 'タック分析':
                    tack_threshold = st.slider('タック検出閾値 (度):', 30, 120, 60, step=5, key="tack_threshold_slider")
                    window_size = st.slider('解析ウィンドウ (秒):', 10, 60, 30, step=5, key="window_size_slider")
                
                elif plot_type == 'パフォーマンスダッシュボード':
                    time_window = st.selectbox(
                        '時間枠:',
                        ['全期間', '前半', '後半'],
                        key="time_window_select"
                    )
                    metrics = st.multiselect(
                        '表示する指標:',
                        ['速度', '風向', 'VMG', 'タック'],
                        default=['速度', '風向'],
                        key="metrics_multiselect"
                    )
                
                # グラフ生成ボタン
                generate_button = st.button('グラフを生成', type="primary", key="generate_graph_btn")
            
            with col2:
                # 選択したグラフを表示
                if generate_button or 'last_plot' in st.session_state:
                    # 最後に生成したグラフを保存
                    if generate_button:
                        st.session_state.last_plot = {
                            'boat': selected_boat,
                            'type': plot_type,
                            'params': {
                                'smooth': locals().get('smooth', 2),
                                'show_raw': locals().get('show_raw', False),
                                'bin_size': locals().get('bin_size', 10),
                                'color_scale': locals().get('color_scale', 'Viridis'),
                                'max_speed': locals().get('max_speed', 15),
                                'resolution': locals().get('resolution', 36),
                                'tack_threshold': locals().get('tack_threshold', 60),
                                'window_size': locals().get('window_size', 30),
                                'time_window': locals().get('time_window', '全期間'),
                                'metrics': locals().get('metrics', ['速度', '風向']),
                                'start_time': locals().get('start_time', None),
                                'end_time': locals().get('end_time', None)
                            }
                        }
                    
                    # グラフ生成
                    fig = None  # 初期化
                    try:
                        boat_data = st.session_state.boats_data[selected_boat]
                        performance_plots = st.session_state.performance_plots
                        params = st.session_state.last_plot['params']
                        
                        # 時間範囲でフィルタリング
                        if params.get('start_time') and params.get('end_time') and 'timestamp' in boat_data.columns:
                            boat_data = boat_data[(boat_data['timestamp'] >= params['start_time']) & 
                                                  (boat_data['timestamp'] <= params['end_time'])]
                        
                        # グラフタイプに応じた処理
                        if plot_type == '速度の時系列':
                            fig = performance_plots.create_speed_vs_time_plot(
                                boat_data, 
                                selected_boat,
                                smooth=params['smooth'],
                                show_raw=params['show_raw']
                            )
                        elif plot_type == '風向と速度':
                            if 'wind_direction' not in boat_data.columns:
                                alert('このグラフには風向データが必要です', 'error')
                            else:
                                fig = performance_plots.create_wind_speed_heatmap(
                                    boat_data,
                                    bin_size=params['bin_size'],
                                    color_scale=params['color_scale'].lower()
                                )
                        elif plot_type == 'ポーラーチャート':
                            if 'wind_direction' not in boat_data.columns:
                                alert('このグラフには風向データが必要です', 'error')
                            else:
                                fig = performance_plots.create_speed_polar_plot(
                                    boat_data,
                                    max_speed=params['max_speed'],
                                    resolution=params['resolution']
                                )
                        elif plot_type == 'タック分析':
                            if 'course' not in boat_data.columns:
                                alert('このグラフにはコースデータが必要です', 'error')
                            else:
                                fig = performance_plots.create_tack_analysis_plot(
                                    boat_data,
                                    tack_threshold=params['tack_threshold'],
                                    window_size=params['window_size']
                                )
                        elif plot_type == 'パフォーマンスダッシュボード':
                            # 必要なカラムのチェック
                            required_cols = []
                            if '速度' in params['metrics']:
                                required_cols.append('speed')
                            if '風向' in params['metrics']:
                                required_cols.append('wind_direction')
                            if 'VMG' in params['metrics']:
                                required_cols.extend(['speed', 'course', 'wind_direction'])
                            if 'タック' in params['metrics']:
                                required_cols.append('course')
                            
                            missing_cols = [col for col in required_cols if col not in boat_data.columns]
                            if missing_cols:
                                alert(f'選択した指標には次の列が必要です: {", ".join(missing_cols)}', 'error')
                            else:
                                # 時間枠でデータをフィルタリング
                                filtered_data = boat_data.copy()
                                if params['time_window'] == '前半':
                                    mid_point = filtered_data['timestamp'].min() + (filtered_data['timestamp'].max() - filtered_data['timestamp'].min()) / 2
                                    filtered_data = filtered_data[filtered_data['timestamp'] <= mid_point]
                                elif params['time_window'] == '後半':
                                    mid_point = filtered_data['timestamp'].min() + (filtered_data['timestamp'].max() - filtered_data['timestamp'].min()) / 2
                                    filtered_data = filtered_data[filtered_data['timestamp'] > mid_point]
                                
                                fig = performance_plots.create_performance_dashboard(
                                    filtered_data, 
                                    selected_boat,
                                    metrics=params['metrics']
                                )
                        
                        # グラフ表示
                        if fig is not None:
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # グラフ保存機能
                            export_col1, export_col2 = st.columns(2)
                            with export_col1:
                                if st.button('PNG形式で保存', key="png_export_btn"):
                                    try:
                                        img_bytes = fig.to_image(format="png", engine="kaleido")
                                        b64 = base64.b64encode(img_bytes).decode()
                                        href = f'<a href="data:image/png;base64,{b64}" download="{selected_boat}_{plot_type}.png">ダウンロード: PNG画像</a>'
                                        st.markdown(href, unsafe_allow_html=True)
                                    except Exception as e:
                                        alert(f"エクスポートエラー: {str(e)}", 'warning')
                            
                            with export_col2:
                                if st.button('HTML形式で保存', key="html_export_btn"):
                                    try:
                                        html_str = fig.to_html(include_plotlyjs="cdn")
                                        b64 = base64.b64encode(html_str.encode()).decode()
                                        href = f'<a href="data:text/html;base64,{b64}" download="{selected_boat}_{plot_type}.html">ダウンロード: インタラクティブHTML</a>'
                                        st.markdown(href, unsafe_allow_html=True)
                                    except Exception as e:
                                        alert(f"エクスポートエラー: {str(e)}", 'warning')
                    
                    except Exception as e:
                        alert(f'グラフ生成中にエラーが発生しました: {e}', 'error')
                else:
                    st.info('左側の「グラフを生成」ボタンをクリックしてください。')
        
        elif active_tab == 1:  # 複数艇比較
            st.subheader('複数艇比較')
            
            # 比較するボートを選択
            boat_options = list(st.session_state.boats_data.keys())
            if len(boat_options) >= 2:
                comparison_boats = st.multiselect(
                    '比較するボートを選択:',
                    boat_options,
                    default=boat_options[:min(3, len(boat_options))],
                    key="comparison_boats_select"
                )
                
                if comparison_boats and len(comparison_boats) >= 2:
                    # 比較グラフの種類
                    comparison_type = st.selectbox(
                        '比較タイプ:',
                        ['速度比較', '航跡比較', '風向対応比較', '時間同期比較', 'データテーブル比較'],
                        key="comparison_type_select"
                    )
                    
                    # 比較パラメータ設定
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        if comparison_type == '速度比較':
                            smoothing = st.slider('平滑化:', 0, 10, 2, key="compare_smooth_slider")
                            use_time = st.checkbox('時間軸で表示', value=True, key="use_time_checkbox")
                        
                        elif comparison_type == '航跡比較':
                            show_markers = st.checkbox('ポイントを表示', value=True, key="show_markers_checkbox")
                            colorscale = st.selectbox('カラースケール:', ['rainbow', 'viridis', 'plasma'], key="colorscale_select")
                        
                        elif comparison_type == '風向対応比較':
                            bin_count = st.slider('風向ビン数:', 4, 36, 12, step=4, key="bin_count_slider")
                        
                        elif comparison_type == '時間同期比較':
                            sync_window = st.slider('同期ウィンドウ (分):', 5, 60, 30, step=5, key="sync_window_slider")
                            metrics = st.multiselect(
                                '表示する指標:',
                                ['速度', '風向', 'コース'],
                                default=['速度'],
                                key="sync_metrics_select"
                            )
                        
                        elif comparison_type == 'データテーブル比較':
                            # データテーブル表示のパラメータはデフォルト
                            st.info('データテーブル比較はデータセットの内容を並べて表示します')
                    
                        # 比較グラフ生成ボタン
                        if st.button('比較データを表示', type="primary", key="compare_data_btn"):
                            with st.spinner('比較データを生成中...'):
                                # ここでグラフまたは比較表示を生成
                                st.session_state.comparison_requested = True
                    
                    with col2:
                        # 比較表示エリア
                        if st.session_state.get('comparison_requested', False):
                            # 選択したボートのデータを辞書に格納
                            data_dict = {}
                            for boat in comparison_boats:
                                data_dict[boat] = st.session_state.boats_data[boat]
                            
                            try:
                                if comparison_type == '速度比較':
                                    fig = st.session_state.performance_plots.create_multi_boat_speed_comparison(
                                        data_dict,
                                        smoothing=smoothing,
                                        use_time=use_time
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                elif comparison_type == '航跡比較':
                                    fig = st.session_state.performance_plots.create_multi_boat_track_comparison(
                                        data_dict,
                                        show_markers=show_markers,
                                        colorscale=colorscale
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                elif comparison_type == '風向対応比較':
                                    fig = st.session_state.performance_plots.create_wind_response_comparison(
                                        data_dict,
                                        bin_count=bin_count
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                elif comparison_type == '時間同期比較':
                                    fig = st.session_state.performance_plots.create_synchronized_comparison(
                                        data_dict,
                                        sync_window=sync_window,
                                        metrics=metrics
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                elif comparison_type == 'データテーブル比較':
                                    # データセット比較ビューアーを使用
                                    dataset_comparison_viewer(
                                        data_dict,
                                        visualization_type="table",
                                        key_prefix="data_compare"
                                    )
                            
                            except Exception as e:
                                alert(f'比較データ生成中にエラーが発生しました: {e}', 'error')
                else:
                    alert('比較するには2つ以上のボートを選択してください。', 'info')
            else:
                alert('比較するにはデータが2つ以上必要です。まずはデータをアップロードしてください。', 'warning')
        
        elif active_tab == 2:  # パフォーマンスサマリー
            st.subheader('パフォーマンスサマリー')
            
            # サマリーを表示するボートの選択
            summary_boat = st.selectbox(
                'サマリーを表示するボート:',
                list(st.session_state.boats_data.keys()),
                key='summary_boat_select'
            )
            
            # サマリータイプの選択
            summary_type = st.radio(
                'サマリータイプ:',
                ['基本統計', '詳細分析', '総合レポート'],
                horizontal=True,
                key="summary_type_radio"
            )
            
            if st.button('サマリーを生成', type="primary", key="generate_summary_btn"):
                with st.spinner('サマリーを生成中...'):
                    try:
                        # パフォーマンスサマリーの取得
                        summary = st.session_state.visualizer.create_performance_summary(summary_boat)
                        
                        if summary:
                            if summary_type == '基本統計':
                                # 基本統計を表示
                                st.subheader(f"{summary_boat} の基本統計")
                                
                                metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                                
                                with metrics_col1:
                                    if 'speed' in summary:
                                        render_metric_card(
                                            "最高速度",
                                            f"{summary['speed']['max']:.1f}",
                                            "ノット",
                                            f"平均: {summary['speed']['avg']:.1f} ノット",
                                            "tachometer-alt",
                                            "#1565C0"
                                        )
                                
                                with metrics_col2:
                                    if 'total_distance_nm' in summary:
                                        render_metric_card(
                                            "走行距離",
                                            f"{summary['total_distance_nm']:.2f}",
                                            "海里",
                                            "",
                                            "route",
                                            "#26A69A"
                                        )
                                    
                                    if 'duration_seconds' in summary:
                                        minutes = summary['duration_seconds'] / 60
                                        render_metric_card(
                                            "走行時間",
                                            f"{minutes:.1f}",
                                            "分",
                                            "",
                                            "clock",
                                            "#26A69A"
                                        )
                                
                                with metrics_col3:
                                    if 'tack_count' in summary:
                                        render_metric_card(
                                            "タック回数",
                                            f"{summary['tack_count']}",
                                            "",
                                            "",
                                            "exchange-alt",
                                            "#FFA726"
                                        )
                                    
                                    if 'vmg' in summary:
                                        render_metric_card(
                                            "平均VMG",
                                            f"{summary['vmg']['avg_vmg']:.2f}",
                                            "",
                                            "",
                                            "compass",
                                            "#FFA726"
                                        )
                                
                                # データポイントの分布を表示
                                if 'speed' in summary:
                                    boat_data = st.session_state.boats_data[summary_boat]
                                    if 'speed' in boat_data.columns:
                                        speed_data = boat_data['speed'] * 1.94384  # m/s -> ノット
                                        
                                        # ヒストグラム
                                        import plotly.express as px
                                        
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
                                        import plotly.graph_objects as go
                                        
                                        boat_data = st.session_state.boats_data[summary_boat]
                                        if 'timestamp' in boat_data.columns and 'speed' in boat_data.columns:
                                            # 時間を分単位に変換
                                            times = [(t - boat_data['timestamp'].iloc[0]).total_seconds() / 60 
                                                    for t in boat_data['timestamp']]
                                            
                                            # 速度をノットに変換
                                            speeds = boat_data['speed'] * 1.94384
                                            
                                            fig = go.Figure()
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
                                        alert('速度セグメント分析データはありません。', 'info')
                                
                                with detail_tabs[1]:
                                    if 'tack_analysis' in summary:
                                        tack_analysis = summary['tack_analysis']
                                        
                                        # タック分析メトリクス
                                        metrics_cols = st.columns(3)
                                        with metrics_cols[0]:
                                            render_metric_card(
                                                "タック回数",
                                                f"{summary.get('tack_count', 0)}",
                                                "",
                                                "",
                                                "exchange-alt"
                                            )
                                        with metrics_cols[1]:
                                            render_metric_card(
                                                "平均速度損失",
                                                f"{tack_analysis.get('avg_loss_knots', 0):.2f}",
                                                "ノット",
                                                "",
                                                "arrow-down"
                                            )
                                        with metrics_cols[2]:
                                            render_metric_card(
                                                "平均回復時間",
                                                f"{tack_analysis.get('avg_recovery_time', 0):.1f}",
                                                "秒",
                                                "",
                                                "clock"
                                            )
                                        
                                        # タック詳細テーブル
                                        if 'tacks' in tack_analysis:
                                            st.subheader('タック詳細')
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
                                            
                                            st.table(pd.DataFrame(tack_data))
                                    else:
                                        alert('タック分析データはありません。', 'info')
                                
                                with detail_tabs[2]:
                                    if 'vmg' in summary:
                                        vmg = summary['vmg']
                                        
                                        # VMGメトリクス
                                        metrics_cols = st.columns(3)
                                        with metrics_cols[0]:
                                            render_metric_card(
                                                "平均VMG",
                                                f"{vmg.get('avg_vmg', 0):.2f}",
                                                "",
                                                "",
                                                "compass"
                                            )
                                        with metrics_cols[1]:
                                            render_metric_card(
                                                "最大VMG",
                                                f"{vmg.get('max_vmg', 0):.2f}",
                                                "",
                                                "",
                                                "arrow-up"
                                            )
                                        with metrics_cols[2]:
                                            render_metric_card(
                                                "VMG効率",
                                                f"{vmg.get('vmg_efficiency', 0):.1f}",
                                                "%",
                                                "",
                                                "tachometer-alt"
                                            )
                                        
                                        # VMGプロット
                                        if 'vmg_data' in vmg:
                                            import plotly.express as px
                                            
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
                                        alert('VMG分析データはありません。', 'info')
                            
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
                            alert(f"{summary_boat} のパフォーマンスサマリーを生成できませんでした", 'warning')
                    
                    except Exception as e:
                        alert(f'サマリー生成中にエラーが発生しました: {e}', 'error')

elif selected_page == "設定":
    # 設定ページ
    section_header('システム設定', 'アプリケーションの設定を調整します。')
    
    # 利用可能な設定項目
    settings_dict = {
        "theme": {
            "label": "テーマ",
            "type": "select",
            "options": ["ライト", "ダーク", "システムデフォルト"],
            "value": st.session_state.get("theme_setting", "システムデフォルト"),
            "help": "アプリケーションの表示テーマを選択",
            "default": "システムデフォルト"
        },
        "language": {
            "label": "言語",
            "type": "select",
            "options": ["日本語", "English"],
            "value": st.session_state.get("language_setting", "日本語"),
            "help": "インターフェース言語を選択",
            "default": "日本語"
        },
        "units": {
            "label": "計測単位",
            "type": "select",
            "options": ["メートル法", "ヤード・ポンド法"],
            "value": st.session_state.get("units_setting", "メートル法"),
            "help": "距離と速度の単位設定",
            "default": "メートル法"
        },
        "data_retention": {
            "label": "データ保持期間",
            "type": "select",
            "options": ["セッション中のみ", "7日間", "30日間", "無期限"],
            "value": st.session_state.get("data_retention_setting", "セッション中のみ"),
            "help": "アップロードデータの保持期間",
            "default": "セッション中のみ"
        },
        "map_detail": {
            "label": "マップ詳細度",
            "type": "slider",
            "min": 1,
            "max": 5,
            "step": 1,
            "value": st.session_state.get("map_detail_setting", 3),
            "help": "マップの詳細度レベル (1:低 - 5:高)",
            "default": 3
        }
    }
    
    # 設定の変更時に呼び出すコールバック
    def update_settings(new_settings):
        for key, value in new_settings.items():
            setting_key = f"{key}_setting"
            st.session_state[setting_key] = value
        
        alert("設定が更新されました。", "success")
    
    # 設定パネルの表示
    updated_settings = settings_panel("アプリケーション設定", settings_dict, update_settings)
    
    # システム情報も表示
    with st.expander("システム情報", expanded=False):
        system_info = {
            "アプリケーションバージョン": "1.0.0",
            "最終更新日": "2025年3月29日",
            "データモデルバージョン": "0.9.5",
            "可視化エンジンバージョン": "0.8.3",
            "Pythonバージョン": sys.version.split()[0],
            "Streamlitバージョン": st.__version__,
            "Pandasバージョン": pd.__version__,
            "Numpyバージョン": np.__version__
        }
        
        for key, value in system_info.items():
            st.text(f"{key}: {value}")
    
    # データクリーンアップ機能
    with st.expander("データクリーンアップ", expanded=False):
        st.write("セッションデータのクリーンアップオプション:")
        
        if st.button("セッションデータをクリア", type="primary"):
            for key in list(st.session_state.keys()):
                # 特定のキーを除外して削除
                if key not in ['theme_setting', 'language_setting', 'units_setting', 'data_retention_setting', 'map_detail_setting']:
                    if key in st.session_state:
                        del st.session_state[key]
            
            # セッション状態を再初期化
            initialize_session_state()
            
            alert("セッションデータがクリアされました。", "success")
            time.sleep(1)  # 少し待機してからリロード
            st.experimental_rerun()

# フッター
st.sidebar.markdown('---')
st.sidebar.info('セーリング戦略分析システム v1.0 - フェーズ2 UI/UX改善版')
