# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - 風向風速表示デモ

Windy.com風の風向風速表示と艇位置マーカーのデモページです。
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
import datetime
from streamlit_folium import folium_static

from sailing_data_processor.utilities.wind_field_generator import generate_sample_wind_field
from ui.components.visualizations.wind_flow_map import create_wind_flow_map
from ui.components.visualizations.boat_marker import add_boat_to_map, update_boat_position
from ui.components.controls.timeline_control import create_timeline_control
from ui.components.navigation.top_bar import apply_top_bar_style, render_top_bar
from ui.components.navigation.context_bar import render_context_bar

def generate_sample_track(center_lat, center_lon, num_points=100):
    """サンプルのトラックデータを生成"""
    # 時間ステップ
    time_base = datetime.datetime.now().replace(hour=12, minute=0, second=0)
    
    # 円形のトラックを生成
    radius_deg = 0.02  # 約2km程度
    angles = np.linspace(0, 4*np.pi, num_points)  # 4πで2周
    
    track_data = []
    for i, angle in enumerate(angles):
        # スパイラル状に展開（徐々に半径を大きく）
        r = radius_deg * (1 + i/num_points*0.5)
        
        # 位置計算
        lat = center_lat + r * np.cos(angle)
        lon = center_lon + r * np.sin(angle)
        
        # 進行方向を計算（接線方向）
        heading = (np.rad2deg(angle) + 90) % 360
        
        # 風向に対する相対角度を計算（仮の風向として225度を使用）
        wind_dir = 225
        rel_wind_angle = (wind_dir - heading) % 360
        if rel_wind_angle > 180:
            rel_wind_angle = 360 - rel_wind_angle
        
        # 速度を計算（風向との角度によって変化）
        # VMGカーブを模したシンプルな計算
        speed = 6 + 2 * np.sin(np.deg2rad(rel_wind_angle * 2)) - rel_wind_angle/60
        
        # データポイント
        track_data.append({
            'timestamp': time_base + datetime.timedelta(seconds=i*10),
            'lat': lat,
            'lon': lon,
            'course': heading,
            'speed': speed,
            'wind_rel_angle': rel_wind_angle
        })
    
    return track_data

def run_demo():
    """風向風速表示デモを実行"""
    # ページ設定
    st.set_page_config(
        page_title="セーリング戦略分析システム - 風向風速表示デモ",
        page_icon="🌊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # トップバースタイルの適用
    apply_top_bar_style()
    
    # トップバーの表示
    active_section = render_top_bar("dashboard")
    
    # セカンダリナビゲーション
    render_context_bar(active_section)
    
    # メインレイアウト
    map_col, data_col = st.columns([7, 3])
    
    # サンプルデータの生成（東京湾付近）
    center_lat, center_lon = 35.45, 139.65
    
    # トラックデータ
    track_data = generate_sample_track(center_lat, center_lon)
    
    # 風データ
    wind_data = generate_sample_wind_field(center_lat, center_lon, radius_km=10, grid_size=20)
    
    with map_col:
        st.subheader("セーリングトラック + 風向風速")
        
        # マップサイズ設定
        map_height = 600
        
        # 現在のタイムラインインデックス
        if 'current_time_idx' not in st.session_state:
            st.session_state.current_time_idx = 0
        
        # コールバック関数
        def update_map(time_idx):
            st.session_state.current_time_idx = time_idx
        
        # 風向風速マップの作成
        m = create_wind_flow_map(
            center=(center_lat, center_lon),
            wind_data=wind_data
        )
        
        # トラック全体の表示
        track_coords = [[point['lat'], point['lon']] for point in track_data]
        folium.PolyLine(
            track_coords,
            color='#1E88E5',
            weight=2,
            opacity=0.5
        ).add_to(m)
        
        # 現在位置の艇マーカーを追加
        current_point = track_data[st.session_state.current_time_idx]
        add_boat_to_map(
            m, 
            (current_point['lat'], current_point['lon']), 
            current_point['course'],
            f"速度: {current_point['speed']:.1f} kt<br>コース: {current_point['course']:.0f}°"
        )
        
        # マップの表示
        folium_static(m, width=800, height=map_height)
        
        # タイムラインコントロール
        st.subheader("タイムライン")
        current_idx = create_timeline_control(track_data, update_map)
    
    with data_col:
        # タブレイアウト
        tabs = st.tabs(["データ", "風統計", "設定"])
        
        with tabs[0]:
            st.subheader("現在のデータ")
            
            # 現在のポイントデータ
            current_data = track_data[current_idx]
            
            # メトリック表示
            col1, col2 = st.columns(2)
            col1.metric("速度", f"{current_data['speed']:.1f} kt")
            col2.metric("コース", f"{current_data['course']:.0f}°")
            
            col1, col2 = st.columns(2)
            col1.metric("風向角", f"{current_data['wind_rel_angle']:.0f}°")
            
            # 位置情報
            st.subheader("位置")
            st.write(f"緯度: {current_data['lat']:.6f}")
            st.write(f"経度: {current_data['lon']:.6f}")
            
            # 時間
            st.subheader("時間")
            st.write(f"時刻: {current_data['timestamp'].strftime('%H:%M:%S')}")
        
        with tabs[1]:
            st.subheader("風統計")
            
            # 風速分布
            st.write("風速分布")
            speeds = np.array(wind_data['speed'])
            
            # ヒストグラム
            hist_values = np.histogram(speeds, bins=10, range=(0, 25))[0]
            st.bar_chart({
                "風速 (kt)": hist_values
            })
            
            # 風速統計
            st.write(f"平均風速: {np.mean(speeds):.1f} kt")
            st.write(f"最大風速: {np.max(speeds):.1f} kt")
            st.write(f"最小風速: {np.min(speeds):.1f} kt")
            
            # 風向統計
            directions = np.array(wind_data['direction'])
            mean_dir = np.rad2deg(np.arctan2(
                np.mean(np.sin(np.deg2rad(directions))),
                np.mean(np.cos(np.deg2rad(directions)))
            )) % 360
            
            st.write(f"平均風向: {mean_dir:.0f}°")
        
        with tabs[2]:
            st.subheader("表示設定")
            
            # 風の表示設定
            st.checkbox("風の流れを表示", value=True)
            st.checkbox("風向のグリッド表示", value=False)
            
            # 風粒子の数設定
            st.slider("風粒子の密度", 500, 3000, 1000, 500)
            
            # 軌跡の表示設定
            st.checkbox("完了部分を強調表示", value=True)
            
            # ヘルプ情報
            with st.expander("ヘルプ"):
                st.markdown("""
                ### 風向風速表示について
                
                このデモでは、Windy.com風の直感的な風向風速の表示と、
                艇の進行方向を考慮したマーカーを表示しています。
                
                - **風粒子**: 風の流れを視覚的に表現します。色は風速を表します。
                - **軌跡**: 青色の線はトラック全体、オレンジ色は進行済みの部分です。
                - **艇マーカー**: 艇の形状マーカーで、進行方向に合わせて回転します。
                
                タイムラインコントロールを使って、時間に沿った変化を確認できます。
                """)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--check-only":
        print("シンタックスチェックが成功しました。")
    else:
        run_demo()
