"""
セーリング戦略分析システム - Streamlit Cloudエントリーポイント (新UIデザイン版)

このファイルはStreamlit Cloudでのデプロイ用の改良版です。
新UIデザインに基づいたインターフェースを提供します。
"""

import streamlit as st
import numpy as np
import pandas as pd
import folium
from streamlit_folium import folium_static
import datetime
import os
import pathlib
import sys
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Streamlit Cloudでの実行かどうかを検出（クラウド環境では'STREAMLIT_BROWSER_GATHER_USAGE_STATS'環境変数が設定されています）
IS_CLOUD_ENV = os.environ.get("STREAMLIT_SERVER_HEADLESS") == "true"
logger.info(f"クラウド環境で実行中: {IS_CLOUD_ENV}")

# プロジェクトのルートディレクトリをパスに追加（pathlibを使用してクロスプラットフォーム互換性を向上）
current_dir = pathlib.Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 必要なコンポーネントをインポート
from ui.components.navigation.top_bar import apply_top_bar_style, render_top_bar
from ui.components.visualizations.wind_flow_map import display_wind_flow_map, create_wind_flow_map
from ui.components.visualizations.boat_marker import add_boat_to_map, update_boat_position
from ui.components.controls.timeline_control import create_timeline_control

# ページ設定
st.set_page_config(
    page_title="セーリング戦略分析システム",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# スタイルの適用
apply_top_bar_style()

# トップバーナビゲーションの表示
active_section = render_top_bar()

# ヘッダー部分は隠す（トップバーで代替）
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    .main-content {
        margin-top: 70px;
    }
    .stApp {
        margin-top: -80px;
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# セッション状態の初期化
if 'track_data' not in st.session_state:
    # サンプルトラックデータの生成
    center = [35.45, 139.65]  # 東京湾付近
    points = []
    radius = 0.02
    
    for i in range(0, 360, 5):
        angle = np.radians(i)
        lat = center[0] + radius * np.cos(angle) * (1 + np.random.random() * 0.1)
        lon = center[1] + radius * np.sin(angle) * (1 + np.random.random() * 0.1)
        
        # 艇の進行方向（タンジェント方向）
        if i < 355:
            next_angle = np.radians(i + 5)
            next_lat = center[0] + radius * np.cos(next_angle) * (1 + np.random.random() * 0.1)
            next_lon = center[1] + radius * np.sin(next_angle) * (1 + np.random.random() * 0.1)
            
            dx = next_lon - lon
            dy = next_lat - lat
            course = (np.degrees(np.arctan2(dx, dy)) + 360) % 360
        else:
            course = (i + 90) % 360
        
        # 風速と風向をランダムに生成（ある程度一貫性を持たせる）
        wind_speed = 8 + np.sin(angle * 2) * 3 + np.random.random() * 2
        wind_direction = (i + 180 + np.random.randint(-20, 20)) % 360
        
        # タイムスタンプの生成
        timestamp = datetime.datetime.now().replace(hour=12, minute=0, second=0) + datetime.timedelta(seconds=i * 10)
        
        points.append({
            'lat': lat,
            'lon': lon,
            'course': course,
            'speed': 5 + np.random.random() * 2,
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
            'timestamp': timestamp
        })
    
    st.session_state.track_data = points

# サンプル風データの生成
if 'wind_data' not in st.session_state:
    center = [35.45, 139.65]  # 東京湾付近
    grid_size = 15
    grid_spacing = 0.005
    
    lat_grid = []
    lon_grid = []
    direction_grid = []
    speed_grid = []
    
    for i in range(-grid_size, grid_size + 1):
        for j in range(-grid_size, grid_size + 1):
            lat = center[0] + i * grid_spacing
            lon = center[1] + j * grid_spacing
            
            # 基本風向は180度（南風）で、位置によって少し変動
            base_direction = 180
            direction_variation = np.sin(i * 0.2) * 20 + np.cos(j * 0.2) * 20
            direction = (base_direction + direction_variation) % 360
            
            # 基本風速は8ノットで、位置によって変動
            base_speed = 8
            speed_variation = np.sin(i * 0.3) * 2 + np.cos(j * 0.3) * 2
            speed = base_speed + speed_variation
            
            lat_grid.append(lat)
            lon_grid.append(lon)
            direction_grid.append(direction)
            speed_grid.append(speed)
    
    st.session_state.wind_data = {
        'lat': lat_grid,
        'lon': lon_grid,
        'direction': direction_grid,
        'speed': speed_grid
    }

# メインコンテンツ部分
st.markdown('<div class="main-content"></div>', unsafe_allow_html=True)

# アクティブなセクションに応じて表示内容を変更
if active_section == 'dashboard':
    st.title("セーリング戦略分析ダッシュボード")
    
    # メインレイアウト
    col1, col2 = st.columns((2, 1))
    
    with col1:
        st.subheader("GPSトラックと風向風速")
        
        # 地図表示エリア
        map_container = st.container()
        with map_container:
            # トラックデータから地図の中心位置を計算
            center_lat = np.mean([p['lat'] for p in st.session_state.track_data])
            center_lon = np.mean([p['lon'] for p in st.session_state.track_data])
            center = [center_lat, center_lon]
            
            # タイムラインコントロール作成
            timeline_index = create_timeline_control(st.session_state.track_data)
            
            # 現在位置のデータ
            current_pos = st.session_state.track_data[timeline_index]
            position = [current_pos['lat'], current_pos['lon']]
            course = current_pos['course']
            
            # 風向風速マップを作成
            m = create_wind_flow_map(center, st.session_state.wind_data)
            
            # 艇のトラックを描画
            track_coords = [[p['lat'], p['lon']] for p in st.session_state.track_data]
            folium.PolyLine(
                track_coords,
                color='#888888',
                weight=2,
                opacity=0.7
            ).add_to(m)
            
            # 艇マーカーを追加
            update_boat_position(m, position, course, timeline_index, st.session_state.track_data)
            
            # マップ表示
            folium_static(m, width=800, height=500)
    
    with col2:
        st.subheader("パフォーマンスデータ")
        
        # 現在のデータ表示
        current_data = st.session_state.track_data[timeline_index]
        
        # 風向風速情報
        st.markdown(
            f"""
            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h3 style="margin-top: 0;">現在の風情報</h3>
                <div style="display: flex;">
                    <div style="flex: 1;">
                        <p style="font-size: 24px; font-weight: bold; margin: 0;">{current_data['wind_speed']:.1f} kt</p>
                        <p style="margin: 0;">風速</p>
                    </div>
                    <div style="flex: 1;">
                        <p style="font-size: 24px; font-weight: bold; margin: 0;">{current_data['wind_direction']:.0f}°</p>
                        <p style="margin: 0;">風向</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 艇の情報
        st.markdown(
            f"""
            <div style="background-color: #fff8f0; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h3 style="margin-top: 0;">艇の状態</h3>
                <div style="display: flex;">
                    <div style="flex: 1;">
                        <p style="font-size: 24px; font-weight: bold; margin: 0;">{current_data['speed']:.1f} kt</p>
                        <p style="margin: 0;">速度</p>
                    </div>
                    <div style="flex: 1;">
                        <p style="font-size: 24px; font-weight: bold; margin: 0;">{current_data['course']:.0f}°</p>
                        <p style="margin: 0;">進行方向</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 統計グラフ
        st.subheader("速度推移")
        
        # 速度データの準備
        speeds = [p['speed'] for p in st.session_state.track_data]
        timestamps = [p['timestamp'] for p in st.session_state.track_data]
        
        # グラフ表示
        speed_df = pd.DataFrame({
            '時間': timestamps,
            '速度 (kt)': speeds
        })
        
        # プロット
        st.line_chart(speed_df.set_index('時間')['速度 (kt)'])
        
        # 風向風速の推移
        st.subheader("風速推移")
        
        # 風速データの準備
        wind_speeds = [p['wind_speed'] for p in st.session_state.track_data]
        
        # グラフ表示
        wind_df = pd.DataFrame({
            '時間': timestamps,
            '風速 (kt)': wind_speeds
        })
        
        # プロット
        st.line_chart(wind_df.set_index('時間')['風速 (kt)'])

elif active_section == 'data':
    st.title("データ管理")
    
    st.info("データ管理セクションはただいま準備中です。完成までしばらくお待ちください。")
    
    # データのプレビュー表示
    st.subheader("現在のトラックデータプレビュー")
    
    # データフレームに変換して表示
    track_df = pd.DataFrame(st.session_state.track_data)
    st.dataframe(track_df)

elif active_section == 'analysis':
    st.title("風向分析")
    
    # レイアウト
    col1, col2 = st.columns((3, 2))
    
    with col1:
        st.subheader("風向風速フィールド")
        
        # 風向風速マップの表示
        center_lat = np.mean([p['lat'] for p in st.session_state.track_data])
        center_lon = np.mean([p['lon'] for p in st.session_state.track_data])
        center = [center_lat, center_lon]
        
        display_wind_flow_map(center, st.session_state.wind_data)
    
    with col2:
        st.subheader("風の統計")
        
        # 風速の分布
        st.markdown("#### 風速分布")
        
        # 風速データの集計
        wind_speeds = [p['wind_speed'] for p in st.session_state.track_data]
        wind_speed_hist = pd.DataFrame(np.histogram(wind_speeds, bins=10)[0])
        st.bar_chart(wind_speed_hist)
        
        # 風向の分布
        st.markdown("#### 風向分布")
        
        # 風向データの集計（円形データなので特殊な処理が必要）
        wind_directions = [p['wind_direction'] for p in st.session_state.track_data]
        bins = list(range(0, 361, 45))
        labels = ["北", "北東", "東", "南東", "南", "南西", "西", "北西"]
        
        # 各方位のデータ数をカウント
        direction_counts = [0] * len(labels)
        for direction in wind_directions:
            for i in range(len(bins)-1):
                if bins[i] <= direction < bins[i+1]:
                    direction_counts[i % len(labels)] += 1
                    break
        
        # データフレームに変換してチャート表示
        direction_df = pd.DataFrame({
            '風向': labels,
            'カウント': direction_counts
        })
        direction_df = direction_df.set_index('風向')
        
        st.bar_chart(direction_df)
        
        # 高度な分析情報
        st.markdown("#### 分析結果")
        st.markdown("""
        - 風の安定性: 中程度
        - 主要風向: 南
        - 風シフトパターン: 緩やかに右シフト
        """)

elif active_section == 'report':
    st.title("レポート")
    
    st.info("レポート機能はただいま開発中です。完成までしばらくお待ちください。")
    
    # レポートテンプレート選択
    st.subheader("レポートテンプレート")
    template = st.selectbox(
        "テンプレートを選択",
        ["基本パフォーマンスレポート", "風向分析詳細レポート", "戦略ポイント分析レポート"]
    )
    
    # 出力形式選択
    st.subheader("出力形式")
    format_options = st.multiselect(
        "出力形式を選択",
        ["PDF", "HTML", "CSV", "JSON"],
        ["PDF"]
    )
    
    # レポート生成ボタン
    if st.button("レポートを生成"):
        st.success("レポートの生成をリクエストしました。完成までしばらくお待ちください。")
        st.markdown("（この機能はデモ表示のみで、実際のレポートは生成されません）")

# フッター
st.markdown("---")
st.caption("セーリング戦略分析システム © 2025")
