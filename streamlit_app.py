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

# Streamlit Cloudでの実行かどうかを検出（クラウド環境では'STREAMLIT_SERVER_HEADLESS'環境変数が設定されています）
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

# レスポンシブマップ関数
def create_responsive_map(center, wind_data, container_height=500, map_type="CartoDB positron"):
    """レスポンシブなマップを作成"""
    # マップオブジェクト作成（既存のcreate_wind_flow_map関数をベースにする）
    m = create_wind_flow_map(center, wind_data, map_type=map_type)
    
    # JavaScriptでウィンドウサイズに応じた調整
    resize_script = """
    <script>
    function adjustMapSize() {
        const mapContainer = document.getElementById('map');
        if (mapContainer) {
            const width = window.innerWidth > 992 ? 
                window.innerWidth - 300 : // サイドバーの幅を考慮
                window.innerWidth - 40;
            
            mapContainer.style.width = width + 'px';
            mapContainer.style.height = '""" + str(container_height) + """px';
        }
    }
    
    // 初期調整
    window.addEventListener('load', adjustMapSize);
    // リサイズ時の調整
    window.addEventListener('resize', adjustMapSize);
    </script>
    """
    
    # スクリプトをマップに追加
    m.get_root().html.add_child(folium.Element(resize_script))
    
    return m

def display_responsive_map(m, height=500):
    """レスポンシブ対応のマップ表示"""
    # マップをHTML文字列として取得
    map_html = m.get_root()._repr_html_()
    
    # スタイルを適用したコンテナを作成
    styled_map = f"""
    <div style="width:100%; height:{height}px; overflow:hidden; border-radius:5px;">
        {map_html}
    </div>
    """
    
    # 表示
    st.markdown(styled_map, unsafe_allow_html=True)

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

# ヘッダー部分は隠す（トップバーで代替）とCSSグリッドレイアウトの適用
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
        padding-top: 60px;
    }
    
    /* Streamlitコンテナの調整 */
    .block-container {
        max-width: 100%;
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* フッターの調整 */
    footer {
        visibility: visible;
        margin-top: 5px;
    }
    
    /* CSSグリッドレイアウト */
    .main-grid {
        display: grid;
        grid-template-columns: 250px 1fr;
        grid-template-rows: 1fr auto auto;
        grid-template-areas:
            "sidebar map"
            "sidebar timeline"
            "details details";
        height: calc(100vh - 80px);
        gap: 10px;
        padding: 10px;
    }
    
    .sidebar-area {
        grid-area: sidebar;
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        overflow-y: auto;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .map-area {
        grid-area: map;
        background-color: white;
        border-radius: 5px;
        padding: 0;
        min-height: 500px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .timeline-area {
        grid-area: timeline;
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .details-area {
        grid-area: details;
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 15px;
        height: 250px;
        overflow-y: auto;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* レスポンシブ対応 */
    @media (max-width: 992px) {
        .main-grid {
            grid-template-columns: 1fr;
            grid-template-rows: auto 1fr auto auto;
            grid-template-areas:
                "sidebar"
                "map"
                "timeline"
                "details";
        }
        
        .sidebar-area {
            max-height: 200px;
        }
    }
    </style>
    """, 
    unsafe_allow_html=True
)

# セッション状態の初期化
if 'app_state' not in st.session_state:
    st.session_state.app_state = {
        'current_index': 0,
        'selected_point': None,
        'map_center': [35.45, 139.65],
        'display_options': {
            'show_wind': True,
            'show_track': True,
            'show_points': True
        },
        'last_update': datetime.datetime.now()
    }

# タイムラインとマップの連携関数
def sync_timeline_to_map(timeline_index):
    """タイムラインの変更をマップに反映"""
    st.session_state.app_state['current_index'] = timeline_index
    st.session_state.app_state['last_update'] = datetime.datetime.now()
    
    # 現在の位置データを取得
    current_data = st.session_state.track_data[timeline_index]
    
    # セッション状態に保存（マップ更新のトリガーに使用）
    st.session_state.app_state['selected_point'] = {
        'position': [current_data['lat'], current_data['lon']],
        'course': current_data['course'],
        'speed': current_data['speed'],
        'wind': {
            'speed': current_data['wind_speed'],
            'direction': current_data['wind_direction']
        }
    }
    
    # 再描画をトリガー
    st.experimental_rerun()

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

# グローバルスタイルの定義
st.markdown("""
<style>
/* スクロールバーの最適化 */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: #f1f1f1;
}
::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: #555;
}

/* フォントとテキストの最適化 */
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    font-size: 14px;
    line-height: 1.5;
    color: #212529;
}

/* サイズ単位の標準化 */
html {
    box-sizing: border-box;
}
*, *:before, *:after {
    box-sizing: inherit;
}

/* Streamlitの要素カスタマイズ */
.stButton > button {
    width: 100%;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.stSelectbox > div > div {
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.element-container {
    margin-bottom: 0.5rem;
}

/* レスポンシブ対応の基本設定 */
@media (max-width: 768px) {
    .row-widget.stRadio > div {
        flex-direction: column;
    }
}
</style>
""", unsafe_allow_html=True)

# アクティブなセクションに応じて表示内容を変更
if active_section == 'dashboard':
    # CSSスタイルの定義
    st.markdown("""
    <style>
    /* ダッシュボードレイアウト */
    .dashboard-container {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    
    /* パネルの共通スタイル */
    .panel {
        background: #fff;
        border-radius: 6px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    
    /* 特定のパネルスタイル */
    .left-side-panel {
        background-color: #f8f9fa;
    }
    
    .map-panel {
        padding: 0;
        overflow: hidden;
        height: 520px; /* マップの高さを固定 */
    }
    
    .timeline-panel {
        background-color: #f8f9fa;
        padding: 0.5rem;
        margin: 0.75rem 0;
        width: 100%;
    }
    
    .details-panel {
        background-color: #f8f9fa;
        width: 100%;
        margin-bottom: 1rem;
    }
    
    /* foliumマップの調整 */
    .folium-map {
        width: 100% !important;
        border-radius: 6px;
        overflow: hidden;
    }
    
    /* タイトルスタイル */
    .panel-title {
        margin-top: 0;
        margin-bottom: 0.75rem;
        font-size: 1rem;
        font-weight: 600;
        color: #333;
    }
    
    /* ボタン調整 */
    .update-button {
        margin-top: 1rem;
    }
    
    /* インジケーターカード */
    .indicator-card {
        padding: 0.75rem;
        border-radius: 4px;
        margin-bottom: 0.75rem;
    }
    
    .indicator-value {
        font-size: 1.5rem;
        font-weight: bold;
        margin: 0;
    }
    
    .indicator-label {
        font-size: 0.875rem;
        color: #666;
        margin: 0;
    }
    
    /* タブ調整 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 2.5rem;
        padding: 0 1rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #e6f0ff;
        border-radius: 4px 4px 0 0;
    }
    
    /* データテーブルスタイル */
    .dataframe {
        font-size: 0.875rem;
    }
    
    /* 空のスペーサー */
    .spacer {
        height: 1.5rem;
    }
    
    /* モバイル対応 */
    @media (max-width: 992px) {
        .responsive-grid {
            grid-template-columns: 1fr !important;
        }
        
        .map-panel {
            height: 400px; /* モバイルでは高さを小さく */
        }
        
        .indicator-value {
            font-size: 1.25rem; /* モバイルでは少し小さく */
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0 0.5rem; /* タブの幅を小さく */
            font-size: 0.9rem;
        }
    }
    
    /* 特小画面対応 */
    @media (max-width: 768px) {
        .map-panel {
            height: 350px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # タイムラインインデックスの管理
    if 'timeline_index' not in st.session_state:
        st.session_state.timeline_index = 0
    
    # Streamlitのネイティブなカラムレイアウトを使用
    # サイドバーとメインエリアの2カラムレイアウト
    left_col, right_col = st.columns([1, 3])
    
    # サイドバーエリアコンテンツ
    with left_col:
        st.markdown('<div class="sidebar-panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">セッション</div>', unsafe_allow_html=True)
        sessions = ["レース1 (2025-04-10)", "トレーニング (2025-04-05)", "レース2 (2025-03-28)"]
        selected_session = st.selectbox("", sessions, label_visibility="collapsed")
        
        st.markdown('<div class="panel-title">表示設定</div>', unsafe_allow_html=True)
        show_wind = st.checkbox("風向風速を表示", value=True)
        show_strategy = st.checkbox("戦略ポイントを表示", value=True)
        
        st.markdown('<div class="panel-title">分析設定</div>', unsafe_allow_html=True)
        analysis_type = st.radio("", ["風向分析", "タック効率", "VMG最適化"], label_visibility="collapsed")
        
        st.markdown('<div class="update-button">', unsafe_allow_html=True)
        st.button("データを更新", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # マップエリアコンテンツ
    with right_col:
        st.markdown('<div class="map-panel">', unsafe_allow_html=True)
        
        # マップビューの計算と表示
        center_lat = np.mean([p['lat'] for p in st.session_state.track_data])
        center_lon = np.mean([p['lon'] for p in st.session_state.track_data])
        center = [center_lat, center_lon]
        
        # タイムラインインデックスの取得
        timeline_index = st.session_state.timeline_index
        
        # 現在位置のデータ
        current_pos = st.session_state.track_data[timeline_index]
        position = [current_pos['lat'], current_pos['lon']]
        course = current_pos['course']
        
        # 風向風速マップを作成（元の関数を使用）
        map_type = "CartoDB positron"
        m = create_wind_flow_map(center, st.session_state.wind_data, map_type=map_type)
        
        # GPSトラックをマップに追加
        track_coords = [[p['lat'], p['lon']] for p in st.session_state.track_data]
        folium.PolyLine(
            track_coords,
            color='#FF5722',
            weight=3,
            opacity=0.7,
            name="トラック"
        ).add_to(m)
        
        # 艇マーカーを追加
        update_boat_position(m, position, course, timeline_index, st.session_state.track_data)
        
        # folium_staticを使用してマップを表示
        folium_static(m, width=800, height=500)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # タイムラインエリアコンテンツ（全幅）
    st.markdown('<div class="timeline-panel">', unsafe_allow_html=True)
    timeline_index = create_timeline_control(st.session_state.track_data, callback=sync_timeline_to_map, show_key_points=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 詳細データエリアコンテンツ（全幅）
    st.markdown('<div class="details-panel">', unsafe_allow_html=True)
    
    # 共通スタイル定義の適用
    def apply_common_styles():
        """アプリケーション全体に共通スタイルを適用"""
        st.markdown("""
        <style>
        /* カラーパレット */
        :root {
            --primary: #1565C0;
            --primary-light: #3b82f6;
            --primary-dark: #0D47A1;
            --secondary: #00ACC1;
            --accent: #FF5722;
            --gray-light: #f8f9fa;
            --gray-medium: #e9ecef;
            --gray-dark: #495057;
            --text-primary: #212121;
            --text-secondary: #616161;
        }
        
        /* タイポグラフィ */
        .section-title {
            font-size: 14px;
            font-weight: 500;
            margin: 15px 0 5px 0;
            color: var(--text-secondary);
        }
        
        .data-label {
            font-size: 12px;
            color: var(--text-secondary);
            margin: 0;
        }
        
        .data-value {
            font-size: 18px;
            font-weight: 500;
            color: var(--text-primary);
            margin: 0 0 5px 0;
        }
        
        /* カード */
        .info-card {
            background-color: white;
            border-radius: 5px;
            padding: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 10px;
        }
        
        /* ボタンスタイル */
        .custom-button {
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }
        
        .custom-button:hover {
            background-color: var(--primary-dark);
        }
        
        .custom-button.secondary {
            background-color: white;
            color: var(--primary);
            border: 1px solid var(--primary);
        }
        
        .custom-button.secondary:hover {
            background-color: var(--gray-light);
        }
        </style>
        """, unsafe_allow_html=True)
    
    # 共通スタイルを適用
    apply_common_styles()
    
    # 詳細データカードのレンダリング関数
    def render_detail_card(title, value, unit, bg_color="#f8f9fa"):
        """詳細データを表示するカードコンポーネント"""
        return f"""
        <div class="info-card" style="background-color: {bg_color};">
            <p class="data-label">{title}</p>
            <p class="data-value">{value} <span style="font-size: 14px;">{unit}</span></p>
        </div>
        """
    
    # タブでデータビューを整理
    tab1, tab2, tab3 = st.tabs(["現在値", "グラフ", "統計"])
    
    with tab1:
        # 現在のデータ取得
        current_data = st.session_state.track_data[timeline_index]
        
        # カードの生成
        wind_speed_card = render_detail_card(
            "風速", 
            f"{current_data['wind_speed']:.1f}", 
            "kt", 
            bg_color="#e3f2fd"
        )
        
        wind_direction_card = render_detail_card(
            "風向", 
            f"{current_data['wind_direction']:.0f}", 
            "°", 
            bg_color="#e3f2fd"
        )
        
        boat_speed_card = render_detail_card(
            "艇速", 
            f"{current_data['speed']:.1f}", 
            "kt", 
            bg_color="#fff3e0"
        )
        
        boat_course_card = render_detail_card(
            "艇向", 
            f"{current_data['course']:.0f}", 
            "°", 
            bg_color="#fff3e0"
        )
        
        # 2列レイアウトでカードを表示
        st.markdown(f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            {wind_speed_card}
            {wind_direction_card}
            {boat_speed_card}
            {boat_course_card}
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
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
    
    with tab3:
        # 統計情報
        st.markdown("### 統計サマリー")
        
        # 基本統計量を表示
        speeds = [p['speed'] for p in st.session_state.track_data]
        wind_speeds = [p['wind_speed'] for p in st.session_state.track_data]
        
        stats_df = pd.DataFrame({
            '指標': ['平均速度', '最大速度', '平均風速', '最大風速'],
            '値': [
                f"{np.mean(speeds):.1f} kt",
                f"{np.max(speeds):.1f} kt",
                f"{np.mean(wind_speeds):.1f} kt",
                f"{np.max(wind_speeds):.1f} kt"
            ]
        })
        
        st.table(stats_df)
        
    st.markdown('</div>', unsafe_allow_html=True)
    
    # スペーサー追加
    st.markdown('<div class="spacer"></div>', unsafe_allow_html=True)

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
