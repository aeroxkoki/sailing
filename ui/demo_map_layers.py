"""
ui.demo_map_layers

マップレイヤー管理とデータ連携機能のデモアプリケーションです。
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import random

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sailing_data_processor.reporting.elements.map.layers.base_layer import BaseMapLayer
from sailing_data_processor.reporting.elements.map.layers.enhanced_layer_manager import EnhancedLayerManager
from sailing_data_processor.reporting.elements.map.layers.wind_field_layer import WindFieldLayer
from sailing_data_processor.reporting.elements.map.layers.course_elements_layer import CourseElementsLayer
from sailing_data_processor.reporting.elements.map.layers.heat_map_layer import HeatMapLayer

from ui.components.reporting.map.layer_controls import layer_manager_panel, layer_property_panel
from ui.components.reporting.map.layer_data_connector_panel import layer_data_connector_panel, data_source_editor_panel


# セッションステートの初期化
if 'layer_manager' not in st.session_state:
    st.session_state.layer_manager = EnhancedLayerManager()

if 'map_rendered' not in st.session_state:
    st.session_state.map_rendered = False

if 'selected_layer_id' not in st.session_state:
    st.session_state.selected_layer_id = None

if 'map_center' not in st.session_state:
    st.session_state.map_center = [35.4498, 139.6649]  # 横浜

if 'map_zoom' not in st.session_state:
    st.session_state.map_zoom = 13


def generate_sample_gps_data(center_lat=35.4498, center_lng=139.6649, num_points=100, time_interval=10):
    """サンプルGPSデータを生成する"""
    data = []
    start_time = datetime.now() - timedelta(minutes=num_points * time_interval)
    
    # セーリングの軌跡をシミュレート (ジグザグパターン)
    lat = center_lat
    lng = center_lng
    speed = 5.0
    heading = 45.0
    wind_speed = 12.0
    wind_direction = 30.0
    
    for i in range(num_points):
        # 時間の進行
        timestamp = start_time + timedelta(minutes=i * time_interval)
        
        # 風向風速の変動
        wind_direction = (wind_direction + random.uniform(-5.0, 5.0)) % 360
        wind_speed = max(3.0, min(20.0, wind_speed + random.uniform(-1.0, 1.0)))
        
        # タックまたはジャイブの判定
        if i > 0 and i % 10 == 0:
            heading = (heading + 90) % 360
        
        # 船の動き
        speed = max(2.0, min(10.0, speed + random.uniform(-0.5, 0.5)))
        heading = (heading + random.uniform(-3.0, 3.0)) % 360
        
        # 位置の更新
        heading_rad = heading * np.pi / 180.0
        lat += np.cos(heading_rad) * speed * 0.0001
        lng += np.sin(heading_rad) * speed * 0.0001
        
        # VMGの計算
        wind_angle = abs((wind_direction - heading + 180) % 360 - 180)
        vmg = speed * np.cos(wind_angle * np.pi / 180.0)
        
        # データポイントの追加
        data.append({
            'lat': lat,
            'lng': lng,
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'speed': speed,
            'heading': heading,
            'wind_speed': wind_speed,
            'wind_direction': wind_direction,
            'vmg': vmg
        })
    
    return data


def generate_sample_wind_field(center_lat=35.4498, center_lng=139.6649, grid_size=5, time_points=3):
    """サンプル風場データを生成する"""
    data = {
        'type': 'wind_field',
        'time': [],
        'points': []
    }
    
    start_time = datetime.now() - timedelta(hours=time_points)
    
    # グリッドポイントの生成
    lat_step = 0.01
    lng_step = 0.01
    
    for t in range(time_points):
        time = start_time + timedelta(hours=t)
        data['time'].append(time.strftime('%Y-%m-%d %H:%M:%S'))
        
        # ベース風向風速
        base_direction = (30.0 + t * 10.0) % 360
        base_speed = 10.0 + t * 1.0
        
        for i in range(-grid_size, grid_size + 1):
            for j in range(-grid_size, grid_size + 1):
                lat = center_lat + i * lat_step
                lng = center_lng + j * lng_step
                
                # 位置に応じた風向風速の変動
                direction_offset = (i + j) * 2.0
                speed_offset = (i**2 + j**2) * 0.05
                
                # 時間変化とノイズを追加
                direction = (base_direction + direction_offset + random.uniform(-5.0, 5.0)) % 360
                speed = max(3.0, base_speed + speed_offset + random.uniform(-1.0, 1.0))
                
                # ポイント追加
                data['points'].append({
                    'lat': lat,
                    'lng': lng,
                    'time_index': t,
                    'wind_speed': speed,
                    'wind_direction': direction
                })
    
    return data


def create_sample_data():
    """サンプルデータを生成してデータソースを作成する"""
    layer_manager = st.session_state.layer_manager
    
    # GPSトラックデータ
    gps_data = generate_sample_gps_data()
    layer_manager.set_context_data('gps_track', gps_data)
    
    # 風場データ
    wind_field = generate_sample_wind_field()
    layer_manager.set_context_data('wind_field', wind_field)
    
    # コースデータの作成
    course_data = {
        'marks': [
            # スタートライン
            {
                'lat': 35.4498,
                'lng': 139.6649,
                'name': 'Start Pin',
                'is_start': True,
                'start_pair': 1
            },
            {
                'lat': 35.4508,
                'lng': 139.6659,
                'name': 'Start Committee',
                'is_start': True,
                'start_pair': 0
            },
            # 風上マーク
            {
                'lat': 35.4598,
                'lng': 139.6749,
                'name': 'Windward Mark',
                'color': '#FF4500'
            },
            # 風下ゲート
            {
                'lat': 35.4488,
                'lng': 139.6639,
                'name': 'Leeward Gate Left',
                'is_gate': True,
                'gate_pair': 4
            },
            {
                'lat': 35.4488,
                'lng': 139.6659,
                'name': 'Leeward Gate Right',
                'is_gate': True,
                'gate_pair': 3
            },
            # フィニッシュライン
            {
                'lat': 35.4598,
                'lng': 139.6739,
                'name': 'Finish Pin',
                'is_finish': True,
                'finish_pair': 6
            },
            {
                'lat': 35.4598,
                'lng': 139.6759,
                'name': 'Finish Committee',
                'is_finish': True,
                'finish_pair': 5
            }
        ],
        'wind_direction': 30.0
    }
    layer_manager.set_context_data('course', course_data)
    
    # ヒートマップデータの作成
    heat_data = []
    
    for i in range(len(gps_data)):
        if i % 3 == 0:  # サンプルデータの間引き
            heat_data.append({
                'lat': gps_data[i]['lat'],
                'lng': gps_data[i]['lng'],
                'value': gps_data[i]['speed']
            })
    
    layer_manager.set_context_data('heat_map', heat_data)
    
    # 追加の統計データを作成
    stats_data = {
        'min_speed': min(point['speed'] for point in gps_data),
        'max_speed': max(point['speed'] for point in gps_data),
        'avg_speed': sum(point['speed'] for point in gps_data) / len(gps_data),
        'min_wind': min(point['wind_speed'] for point in gps_data),
        'max_wind': max(point['wind_speed'] for point in gps_data),
        'avg_wind': sum(point['wind_speed'] for point in gps_data) / len(gps_data),
        'avg_vmg': sum(point['vmg'] for point in gps_data) / len(gps_data),
        'distance': sum(
            np.sqrt(
                (gps_data[i]['lat'] - gps_data[i-1]['lat'])**2 + 
                (gps_data[i]['lng'] - gps_data[i-1]['lng'])**2
            ) * 111000  # 緯度経度を概算でメートルに変換
            for i in range(1, len(gps_data))
        )
    }
    layer_manager.set_context_data('stats', stats_data)


def on_layer_change(change_type):
    """レイヤー変更時のコールバック"""
    st.session_state.map_rendered = False
    

def render_map():
    """マップをレンダリングする"""
    if not st.session_state.map_rendered:
        center_lat, center_lng = st.session_state.map_center
        zoom = st.session_state.map_zoom
        
        # マップコンテナにHTML出力
        with st.container():
            map_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Map Layers Demo</title>
                <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
                <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
                <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>
                <style>
                    #map {{
                        height: 500px;
                        width: 100%;
                        border: 1px solid #ccc;
                        border-radius: 5px;
                    }}
                </style>
            </head>
            <body>
                <div id="map"></div>
                <script>
                    var map = L.map('map').setView([{center_lat}, {center_lng}], {zoom});
                    
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    }}).addTo(map);
                    
                    // レイヤーレンダリングコード
                    {st.session_state.layer_manager.render_layers("map")}
                    
                    // マップの中心とズームレベルを監視
                    map.on('moveend', function(e) {{
                        var center = map.getCenter();
                        var zoom = map.getZoom();
                        window.parent.postMessage({{
                            'type': 'map_moved',
                            'center': [center.lat, center.lng],
                            'zoom': zoom
                        }}, '*');
                    }});
                </script>
            </body>
            </html>
            """
            st.components.v1.html(map_html, height=520)
            st.session_state.map_rendered = True


def main():
    st.set_page_config(page_title="マップレイヤー管理とデータ連携", page_icon="🧭", layout="wide")
    
    st.title("🧭 マップレイヤー管理とデータ連携")
    st.markdown("""
    このデモでは、マップレイヤー管理とデータ連携機能を試すことができます。
    レイヤーの追加、設定、データソースとの連携などを実験してください。
    """)
    
    # レイヤーマネージャーを取得
    layer_manager = st.session_state.layer_manager
    
    # サイドバーにレイヤー管理コントロールを表示
    with st.sidebar:
        st.header("コントロールパネル")
        
        # データ作成ボタン
        if st.button("サンプルデータを作成"):
            create_sample_data()
            st.success("サンプルデータが作成されました！")
            st.session_state.map_rendered = False
            st.rerun()
        
        # タブでコントロールを分ける
        tab1, tab2, tab3, tab4 = st.tabs(["レイヤー管理", "レイヤー設定", "データ連携", "データソース"])
        
        with tab1:
            # レイヤー管理パネル
            changes = layer_manager_panel(layer_manager, on_change=on_layer_change)
            
            if changes and "selected_layer_id" in changes:
                st.session_state.selected_layer_id = changes["selected_layer_id"]
                st.rerun()
        
        with tab2:
            # 選択されたレイヤーのプロパティパネル
            if st.session_state.selected_layer_id:
                selected_layer = layer_manager.get_layer(st.session_state.selected_layer_id)
                if selected_layer:
                    layer_property_panel(selected_layer, on_change=on_layer_change)
                else:
                    st.info("レイヤーを選択してください。")
            else:
                st.info("レイヤーを選択してください。")
        
        with tab3:
            # データ連携パネル
            layer_data_connector_panel(layer_manager, on_change=on_layer_change)
        
        with tab4:
            # データソース編集パネル
            data_source_editor_panel(layer_manager, on_change=on_layer_change)
    
    # メインエリアにマップを表示
    render_map()
    
    # 統計情報表示
    st.subheader("統計情報")
    
    # データソースからの統計情報表示
    stats_data = layer_manager.get_context_data('stats')
    if stats_data:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("平均速度", f"{stats_data['avg_speed']:.1f} kt")
        
        with col2:
            st.metric("平均風速", f"{stats_data['avg_wind']:.1f} kt")
        
        with col3:
            st.metric("平均VMG", f"{stats_data['avg_vmg']:.1f} kt")
        
        with col4:
            st.metric("走行距離", f"{stats_data['distance']:.0f} m")
    else:
        st.info("統計情報はありません。サンプルデータを作成してください。")
    
    # レイヤー情報
    st.subheader("レイヤー情報")
    
    # レイヤー一覧の表示
    layers = layer_manager.get_ordered_layers()
    if layers:
        layer_data = []
        for layer in layers:
            layer_data.append({
                "ID": layer.layer_id,
                "名前": layer.name,
                "タイプ": layer.__class__.__name__,
                "表示": "表示" if layer.visible else "非表示",
                "データソース": layer.data_source or "-"
            })
        
        st.dataframe(pd.DataFrame(layer_data), hide_index=True)
    else:
        st.info("レイヤーがありません。レイヤーを追加してください。")
    
    # データソース情報
    st.subheader("データソース情報")
    sources = list(layer_manager.get_context().keys())
    if sources:
        source_data = []
        for source_id in sources:
            data = layer_manager.get_context_data(source_id)
            data_type = type(data).__name__
            data_size = "N/A"
            
            if isinstance(data, list):
                data_size = f"{len(data)} アイテム"
            elif isinstance(data, dict):
                data_size = f"{len(data)} キー"
            
            source_data.append({
                "データソースID": source_id,
                "データ型": data_type,
                "サイズ": data_size
            })
        
        st.dataframe(pd.DataFrame(source_data), hide_index=True)
    else:
        st.info("データソースがありません。サンプルデータを作成してください。")


if __name__ == "__main__":
    main()
