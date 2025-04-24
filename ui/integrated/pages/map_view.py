# -*- coding: utf-8 -*-
"""
ui.integrated.pages.map_view

セーリング戦略分析システムのインタラクティブマップビューページ
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import folium_static
from folium.plugins import HeatMap, TimestampedGeoJson, MarkerCluster, Draw, Fullscreen
import json
import os
import sys
from datetime import datetime, timedelta
import branca.colormap as cm

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

# マップレイヤー管理システムのインポート
from ui.integrated.components.map.layer_manager import LayerManager

def render_page():
    """マップビューページをレンダリングする関数"""
    
    st.title('インタラクティブマップ分析')
    
    # セッション状態の初期化
    if 'map_initialized' not in st.session_state:
        st.session_state.map_initialized = True
        st.session_state.selected_map_session = None
        st.session_state.visible_layers = ["gps_track", "wind_direction", "strategy_points"]
        st.session_state.map_time_index = 0
        st.session_state.selected_base_map = "OpenStreetMap"
    
    # サイドバーのセッション選択
    with st.sidebar:
        st.subheader("セッション選択")
        # 実際にはプロジェクト管理システムからセッションを取得する
        # サンプルとしてダミーデータを使用
        sessions = ["2025/03/27 レース練習", "2025/03/25 風向変化トレーニング", "2025/03/20 スピードテスト"]
        selected_session = st.selectbox("分析するセッションを選択", sessions)
        
        if selected_session != st.session_state.selected_map_session:
            st.session_state.selected_map_session = selected_session
            # セッションが変更されたら関連データを読み込む処理をここに追加
            st.experimental_rerun()
    
    # 選択されたセッションの情報表示
    if st.session_state.selected_map_session:
        st.markdown(f"## セッション: {st.session_state.selected_map_session}")
        
        # タブを使用して異なるマップビューを提供
        tab1, tab2, tab3 = st.tabs(["標準ビュー", "風向分析", "戦略ポイント"])
        
        # 標準ビュータブ
        with tab1:
            # マップコントロールエリア
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # ベースマップ選択
                base_map_options = ["OpenStreetMap", "CartoDB dark_matter", "CartoDB positron", "Stamen Terrain", "Esri Satellite"]
                selected_base_map = st.selectbox("ベースマップ", base_map_options, index=base_map_options.index(st.session_state.selected_base_map))
                
                if selected_base_map != st.session_state.selected_base_map:
                    st.session_state.selected_base_map = selected_base_map
                    st.experimental_rerun()
            
            with col2:
                # 時間スライダー
                # 実際の実装では、セッションの開始時刻と終了時刻を使用
                if 'time_slider' not in st.session_state:
                    st.session_state.time_slider = 0
                
                time_slider = st.slider(
                    "時間",
                    min_value=0,
                    max_value=100,
                    value=st.session_state.time_slider,
                    step=1
                )
                
                if time_slider != st.session_state.time_slider:
                    st.session_state.time_slider = time_slider
                    st.session_state.map_time_index = time_slider
            
            with col3:
                # 全画面表示ボタン
                if st.button("全画面表示", use_container_width=True):
                    st.session_state.fullscreen_map = True
                
                # マップのリセットボタン
                if st.button("リセット", use_container_width=True):
                    st.session_state.map_time_index = 0
                    st.session_state.time_slider = 0
                    st.experimental_rerun()
            
            # レイヤー管理サイドバー
            with st.sidebar:
                st.subheader("レイヤー管理")
                
                # レイヤーの表示/非表示選択
                st.markdown("### 表示レイヤー")
                
                layer_options = {
                    "gps_track": "GPSトラック",
                    "wind_direction": "風向ベクトル",
                    "wind_field": "風向場",
                    "strategy_points": "戦略ポイント",
                    "tack_points": "タックポイント",
                    "laylines": "レイライン",
                    "vmg_heatmap": "VMGヒートマップ",
                    "speed_heatmap": "速度ヒートマップ"
                }
                
                # 各レイヤーの表示/非表示をチェックボックスで選択
                visible_layers = []
                for layer_id, layer_name in layer_options.items():
                    if st.checkbox(layer_name, value=layer_id in st.session_state.visible_layers):
                        visible_layers.append(layer_id)
                
                if visible_layers != st.session_state.visible_layers:
                    st.session_state.visible_layers = visible_layers
                    st.experimental_rerun()
                
                # レイヤーの透明度調整
                st.markdown("### レイヤー設定")
                
                layer_transparency = st.slider(
                    "レイヤー透明度",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1
                )
                
                # レイヤーのスタイル設定（例：トラックの色と太さ）
                st.markdown("### スタイル設定")
                
                track_color = st.color_picker(
                    "トラックの色",
                    "#FF5733"
                )
                
                track_width = st.slider(
                    "トラックの太さ",
                    min_value=1,
                    max_value=10,
                    value=3,
                    step=1
                )
                
                # レイヤー保存ボタン
                if st.button("現在のレイヤー設定を保存"):
                    # 実際の実装では、レイヤー設定をDB/ファイルに保存
                    st.success("レイヤー設定を保存しました。")
            
            # マップの生成と表示
            map_container = st.container()
            with map_container:
                # foliumマップの作成
                m = create_map(
                    base_map=st.session_state.selected_base_map,
                    visible_layers=st.session_state.visible_layers,
                    time_index=st.session_state.map_time_index,
                    layer_transparency=layer_transparency,
                    track_color=track_color,
                    track_width=track_width
                )
                
                # マップの表示
                folium_static(m, width=1000, height=600)
            
            # タイムラインコントロール
            st.markdown("### 時間経過ビュー")
            play_col1, play_col2, play_col3 = st.columns([1, 3, 1])
            
            with play_col1:
                if st.button("再生", use_container_width=True):
                    # 実際の実装では、タイムスライダーを自動で進めるロジックを追加
                    st.info("タイムラインの再生機能は開発中です。")
            
            with play_col2:
                # 現在表示している時間を表示
                # 実際の実装では、セッションの時間範囲に基づく実際の時刻を表示
                start_time = datetime(2025, 3, 27, 13, 0, 0)
                current_time = start_time + timedelta(minutes=int(st.session_state.map_time_index * 1.5))
                st.markdown(f"**現在時刻: {current_time.strftime('%H:%M:%S')}**")
            
            with play_col3:
                if st.button("停止", use_container_width=True):
                    # 実際の実装では、タイムスライダーの自動進行を停止するロジックを追加
                    st.info("タイムラインの停止機能は開発中です。")
            
            # 現在選択されているポイントの詳細情報
            st.markdown("### ポイント詳細")
            
            # 実際の実装では、マップ上でクリックされたポイントの情報を表示
            # MVPではサンプルデータを表示
            point_data = {
                "時間": "13:42:15",
                "座標": "35.2982, 139.5713",
                "速度": "6.3 kt",
                "風向": "210°",
                "風速": "12.5 kt",
                "VMG": "3.8 kt",
                "対地進路": "225°",
                "対水進路": "220°"
            }
            
            point_info_cols = st.columns(4)
            for i, (key, value) in enumerate(point_data.items()):
                with point_info_cols[i % 4]:
                    st.metric(key, value)
            
            # エクスポートボタン
            st.markdown("### マップエクスポート")
            export_cols = st.columns(4)
            
            with export_cols[0]:
                if st.button("PNG画像として保存", use_container_width=True):
                    st.info("マップを画像として保存する機能は開発中です。")
            
            with export_cols[1]:
                if st.button("インタラクティブHTMLとして保存", use_container_width=True):
                    st.info("マップをHTMLとして保存する機能は開発中です。")
            
            with export_cols[2]:
                if st.button("GPX形式でエクスポート", use_container_width=True):
                    st.info("トラックをGPXとしてエクスポートする機能は開発中です。")
            
            with export_cols[3]:
                if st.button("レポートに追加", use_container_width=True):
                    st.info("マップをレポートに追加する機能は開発中です。")
        
        # 風向分析タブ
        with tab2:
            st.subheader("風向分析ビュー")
            
            # 風向フィルター
            wind_filter_cols = st.columns(3)
            
            with wind_filter_cols[0]:
                min_wind_speed = st.slider(
                    "最小風速 (kt)",
                    min_value=0.0,
                    max_value=20.0,
                    value=0.0,
                    step=0.5
                )
            
            with wind_filter_cols[1]:
                max_wind_speed = st.slider(
                    "最大風速 (kt)",
                    min_value=0.0,
                    max_value=20.0,
                    value=20.0,
                    step=0.5
                )
            
            with wind_filter_cols[2]:
                wind_direction_range = st.slider(
                    "風向範囲 (度)",
                    min_value=0,
                    max_value=360,
                    value=(0, 360),
                    step=5
                )
            
            # 風向場の表示設定
            wind_display_cols = st.columns(2)
            
            with wind_display_cols[0]:
                wind_field_resolution = st.select_slider(
                    "風向場の解像度",
                    options=["低", "中", "高"],
                    value="中"
                )
            
            with wind_display_cols[1]:
                wind_field_style = st.selectbox(
                    "表示スタイル",
                    ["ベクトル", "ストリームライン", "ヒートマップ", "等値線"]
                )
            
            # 風向分析用のマップ表示
            st.markdown("### 風向分析マップ")
            
            # foliumマップの作成（風向分析特化）
            wind_map = create_wind_analysis_map(
                min_wind_speed=min_wind_speed,
                max_wind_speed=max_wind_speed,
                wind_direction_range=wind_direction_range,
                resolution=wind_field_resolution,
                style=wind_field_style
            )
            
            # マップの表示
            folium_static(wind_map, width=1000, height=600)
            
            # 風向シフト検出結果
            st.markdown("### 検出された風向シフト")
            
            # 実際の実装では、分析結果からの風向シフトデータを表示
            # MVPではサンプルデータを表示
            shift_data = {
                "時間": ["13:15", "13:42", "14:10", "14:35", "15:05"],
                "シフト量": ["右 15°", "左 12°", "右 8°", "右 20°", "左 10°"],
                "シフト速度": ["緩やか", "急激", "緩やか", "緩やか", "急激"],
                "対応状況": ["良好", "遅延", "良好", "見逃し", "良好"]
            }
            
            st.dataframe(pd.DataFrame(shift_data))
            
            # 風向の時系列グラフ
            st.markdown("### 風向の時間変化")
            
            # 実際の実装では、実際のデータを使用したグラフを表示
            # MVPではサンプルデータを使用
            wind_dir_data = pd.DataFrame(
                np.sin(np.linspace(0, 10, 100)) * 30 + 180,
                columns=['風向 (度)']
            )
            st.line_chart(wind_dir_data)
        
        # 戦略ポイントタブ
        with tab3:
            st.subheader("戦略ポイント分析")
            
            # 戦略ポイントフィルター
            strategy_filter_cols = st.columns(3)
            
            with strategy_filter_cols[0]:
                point_types = st.multiselect(
                    "ポイントタイプ",
                    ["タック", "ジャイブ", "風向シフト", "レイライン", "障害物回避", "コース変更"],
                    default=["タック", "風向シフト", "レイライン"]
                )
            
            with strategy_filter_cols[1]:
                importance_level = st.select_slider(
                    "重要度",
                    options=["すべて", "低", "中", "高", "最高"],
                    value="すべて"
                )
            
            with strategy_filter_cols[2]:
                decision_quality = st.select_slider(
                    "判断品質",
                    options=["すべて", "最適", "適切", "改善必要", "不適切"],
                    value="すべて"
                )
            
            # 戦略ポイント分析用のマップ表示
            st.markdown("### 戦略ポイントマップ")
            
            # foliumマップの作成（戦略ポイント特化）
            strategy_map = create_strategy_points_map(
                point_types=point_types,
                importance_level=importance_level,
                decision_quality=decision_quality
            )
            
            # マップの表示
            folium_static(strategy_map, width=1000, height=600)
            
            # 戦略ポイント一覧
            st.markdown("### 戦略ポイント一覧")
            
            # 実際の実装では、フィルタリングされた戦略ポイントを表示
            # MVPではサンプルデータを表示
            strategy_data = {
                "時間": ["13:10", "13:38", "14:05", "14:32", "15:00"],
                "タイプ": ["風向シフト対応", "レイライン接近", "風向シフト対応", "障害物回避", "コース変更"],
                "判断": ["シフト前にタック", "レイラインでタック", "様子見", "早めの回避行動", "風上へのコース変更"],
                "結果": ["レグ短縮", "オーバースタンド", "不利なレイヤー", "ロス最小化", "有利なレイヤー獲得"],
                "評価": ["最適", "改善必要", "不適切", "適切", "最適"]
            }
            
            st.dataframe(pd.DataFrame(strategy_data))
            
            # 戦略ポイントの詳細分析
            st.markdown("### 戦略的判断の効果分析")
            
            effect_cols = st.columns(2)
            
            with effect_cols[0]:
                st.markdown("#### 風向変化への対応速度")
                response_data = pd.DataFrame(
                    np.random.normal(85, 10, 10),
                    columns=['対応速度 (%)']
                )
                st.bar_chart(response_data)
                
            with effect_cols[1]:
                st.markdown("#### 戦略効果")
                effect_data = {
                    "戦略": ["早めのタック", "レイヤー選択", "周囲艇観察", "風予測に基づく展開"],
                    "効果 (推定利得)": ["+45秒", "+30秒", "+15秒", "+60秒"]
                }
                st.dataframe(pd.DataFrame(effect_data))

# ダミーデータを使用して基本マップを作成する関数
def create_map(base_map="OpenStreetMap", visible_layers=None, time_index=0, 
               layer_transparency=0.7, track_color="#FF5733", track_width=3):
    """
    基本的なマップを作成する関数
    
    Args:
        base_map (str): ベースマップの種類
        visible_layers (list): 表示するレイヤーのリスト
        time_index (int): 時間インデックス
        layer_transparency (float): レイヤーの透明度
        track_color (str): トラックの色
        track_width (int): トラックの太さ
    
    Returns:
        folium.Map: 作成されたfoliumマップ
    """
    # ベースの位置（江の島周辺）
    center_lat, center_lon = 35.300, 139.480
    
    # foliumマップの作成
    if base_map == "CartoDB dark_matter":
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, 
                      tiles="CartoDB dark_matter")
    elif base_map == "CartoDB positron":
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, 
                      tiles="CartoDB positron")
    elif base_map == "Stamen Terrain":
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, 
                      tiles="Stamen Terrain")
    elif base_map == "Esri Satellite":
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13, 
                      tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", 
                      attr="Esri")
    else:  # OpenStreetMap
        m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    # 全画面表示ボタンの追加
    Fullscreen().add_to(m)
    
    # 描画コントロールの追加
    Draw(export=True).add_to(m)
    
    # GPSトラックレイヤーの作成
    if visible_layers and "gps_track" in visible_layers:
        # ダミーのGPSトラックデータを生成
        track_data = generate_dummy_track_data(center_lat, center_lon)
        
        # 時間インデックスに基づくデータのフィルタリング
        filtered_track = track_data[:time_index + 1] if time_index < len(track_data) else track_data
        
        # トラックの描画
        folium.PolyLine(
            filtered_track,
            color=track_color,
            weight=track_width,
            opacity=layer_transparency,
            tooltip="GPSトラック"
        ).add_to(m)
        
        # 現在位置のマーカー
        if filtered_track:
            current_pos = filtered_track[-1]
            folium.Marker(
                location=current_pos,
                popup="現在位置",
                icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")
            ).add_to(m)
    
    # 風向ベクトルレイヤーの作成
    if visible_layers and "wind_direction" in visible_layers:
        # ダミーの風向データを生成
        wind_data = generate_dummy_wind_data(center_lat, center_lon, 15)
        
        # 風向ベクトルの描画
        for point in wind_data:
            lat, lon = point["position"]
            direction = point["direction"]
            speed = point["speed"]
            
            # 風向を示す矢印
            folium.RegularPolygonMarker(
                location=[lat, lon],
                fill_color="blue",
                number_of_sides=3,
                radius=5,
                rotation=direction,
                fill_opacity=layer_transparency,
                tooltip=f"風向: {direction}°, 風速: {speed} kt"
            ).add_to(m)
    
    # 風向場レイヤーの作成
    if visible_layers and "wind_field" in visible_layers:
        # ヒートマップ形式で風速を可視化
        wind_field_data = generate_dummy_wind_field(center_lat, center_lon, 30)
        
        # カラーマップの定義
        colormap = cm.LinearColormap(
            colors=['blue', 'green', 'yellow', 'orange', 'red'],
            vmin=min(point[2] for point in wind_field_data),
            vmax=max(point[2] for point in wind_field_data)
        )
        
        # ヒートマップの追加
        HeatMap(
            wind_field_data,
            radius=15,
            gradient={0.0: 'blue', 0.25: 'green', 0.5: 'yellow', 0.75: 'orange', 1.0: 'red'},
            min_opacity=layer_transparency * 0.5,
            max_opacity=layer_transparency,
            blur=10
        ).add_to(m)
        
        # カラースケールの追加
        colormap.caption = '風速 (kt)'
        colormap.add_to(m)
    
    # 戦略ポイントレイヤーの作成
    if visible_layers and "strategy_points" in visible_layers:
        # ダミーの戦略ポイントデータを生成
        strategy_points = generate_dummy_strategy_points(center_lat, center_lon)
        
        # 戦略ポイントのマーカークラスター
        marker_cluster = MarkerCluster(name="戦略ポイント").add_to(m)
        
        # 各戦略ポイントの描画
        for point in strategy_points:
            lat, lon = point["position"]
            point_type = point["type"]
            time = point["time"]
            description = point["description"]
            
            # ポイントタイプに応じたアイコン設定
            if point_type == "tack":
                icon = folium.Icon(color="green", icon="exchange", prefix="fa")
            elif point_type == "wind_shift":
                icon = folium.Icon(color="blue", icon="wind", prefix="fa")
            elif point_type == "layline":
                icon = folium.Icon(color="purple", icon="location-arrow", prefix="fa")
            else:
                icon = folium.Icon(color="orange", icon="info", prefix="fa")
            
            # マーカーの追加
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(f"<b>{point_type.capitalize()}</b><br>{time}<br>{description}", max_width=300),
                tooltip=f"{point_type.capitalize()} at {time}",
                icon=icon
            ).add_to(marker_cluster)
    
    # タックポイントレイヤーの作成
    if visible_layers and "tack_points" in visible_layers:
        # ダミーのタックポイントデータを生成
        tack_points = generate_dummy_tack_points(center_lat, center_lon)
        
        # タックポイントの描画
        for point in tack_points:
            lat, lon = point["position"]
            time = point["time"]
            duration = point["duration"]
            speed_loss = point["speed_loss"]
            
            # タックポイントのマーカー
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                color="green",
                fill=True,
                fill_color="green",
                fill_opacity=layer_transparency,
                tooltip=f"タック at {time}<br>所要時間: {duration}秒<br>速度損失: {speed_loss} kt"
            ).add_to(m)
    
    # レイラインレイヤーの作成
    if visible_layers and "laylines":
        # ダミーのレイラインデータを生成
        laylines = generate_dummy_laylines(center_lat, center_lon)
        
        # レイラインの描画
        for line in laylines:
            start, end = line["points"]
            side = line["side"]
            
            # レイラインの描画
            folium.PolyLine(
                locations=[start, end],
                color="purple" if side == "starboard" else "blue",
                weight=2,
                opacity=layer_transparency,
                dash_array="5, 10",
                tooltip=f"{side.capitalize()} Layline"
            ).add_to(m)
    
    # VMGヒートマップレイヤーの作成
    if visible_layers and "vmg_heatmap" in visible_layers:
        # ダミーのVMGデータを生成
        vmg_data = generate_dummy_vmg_data(center_lat, center_lon, 40)
        
        # VMGヒートマップの追加
        HeatMap(
            vmg_data,
            radius=12,
            gradient={0.0: 'blue', 0.25: 'green', 0.5: 'yellow', 0.75: 'orange', 1.0: 'red'},
            min_opacity=layer_transparency * 0.5,
            max_opacity=layer_transparency,
            blur=10
        ).add_to(m)
    
    # 速度ヒートマップレイヤーの作成
    if visible_layers and "speed_heatmap" in visible_layers:
        # ダミーの速度データを生成
        speed_data = generate_dummy_speed_data(center_lat, center_lon, 40)
        
        # 速度ヒートマップの追加
        HeatMap(
            speed_data,
            radius=12,
            gradient={0.0: 'blue', 0.25: 'green', 0.5: 'yellow', 0.75: 'orange', 1.0: 'red'},
            min_opacity=layer_transparency * 0.5,
            max_opacity=layer_transparency,
            blur=10
        ).add_to(m)
    
    return m

# 風向分析特化のマップを作成する関数
def create_wind_analysis_map(min_wind_speed=0, max_wind_speed=20, 
                            wind_direction_range=(0, 360), resolution="中",
                            style="ベクトル"):
    """
    風向分析特化のマップを作成する関数
    
    Args:
        min_wind_speed (float): 最小風速
        max_wind_speed (float): 最大風速
        wind_direction_range (tuple): 風向範囲
        resolution (str): 解像度
        style (str): 表示スタイル
    
    Returns:
        folium.Map: 作成されたfoliumマップ
    """
    # ベースの位置（江の島周辺）
    center_lat, center_lon = 35.300, 139.480
    
    # foliumマップの作成
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    # 全画面表示ボタンの追加
    Fullscreen().add_to(m)
    
    # 解像度に応じたポイント数
    resolution_points = {"低": 10, "中": 20, "高": 40}
    points = resolution_points.get(resolution, 20)
    
    # 風向場データの生成
    wind_field_data = generate_dummy_wind_field_detailed(
        center_lat, center_lon, points, 
        min_wind_speed, max_wind_speed, 
        wind_direction_range
    )
    
    # 表示スタイルに応じた描画
    if style == "ベクトル":
        # ベクトル表示
        for point in wind_field_data:
            lat, lon = point["position"]
            direction = point["direction"]
            speed = point["speed"]
            
            # フィルタリング
            if speed < min_wind_speed or speed > max_wind_speed:
                continue
            
            if not (wind_direction_range[0] <= direction <= wind_direction_range[1]):
                if wind_direction_range[0] <= (direction % 360) <= wind_direction_range[1]:
                    pass
                else:
                    continue
            
            # 風速に応じた矢印の長さ
            arrow_length = speed / 20.0 * 0.01  # スケーリングファクター
            
            # 風向を示す矢印マーカー
            folium.RegularPolygonMarker(
                location=[lat, lon],
                fill_color="blue",
                number_of_sides=3,
                radius=5 + speed / 2,  # 風速に応じたサイズ
                rotation=direction,
                fill_opacity=0.7,
                tooltip=f"風向: {direction}°, 風速: {speed:.1f} kt"
            ).add_to(m)
            
    elif style == "ヒートマップ":
        # ヒートマップ表示用にデータを変換
        heatmap_data = []
        for point in wind_field_data:
            lat, lon = point["position"]
            speed = point["speed"]
            
            # フィルタリング
            if speed >= min_wind_speed and speed <= max_wind_speed:
                heatmap_data.append([lat, lon, speed])
        
        # カラーマップの定義
        colormap = cm.LinearColormap(
            colors=['blue', 'green', 'yellow', 'orange', 'red'],
            vmin=min_wind_speed,
            vmax=max_wind_speed
        )
        
        # ヒートマップの追加
        HeatMap(
            heatmap_data,
            radius=15,
            min_opacity=0.5,
            max_opacity=0.8,
            blur=10
        ).add_to(m)
        
        # カラースケールの追加
        colormap.caption = '風速 (kt)'
        colormap.add_to(m)
    
    elif style == "等値線":
        # 等値線表示は実際の実装では複雑なので、MVPでは簡略化
        # 実際の実装では、griddata等を使用して等値線を生成する
        st.warning("等値線表示は開発中です。現在はベクトル表示を使用しています。")
        
        # 代わりにベクトル表示
        for point in wind_field_data:
            lat, lon = point["position"]
            direction = point["direction"]
            speed = point["speed"]
            
            # フィルタリング
            if speed < min_wind_speed or speed > max_wind_speed:
                continue
            
            # 風向を示す矢印
            folium.RegularPolygonMarker(
                location=[lat, lon],
                fill_color="blue",
                number_of_sides=3,
                radius=5,
                rotation=direction,
                fill_opacity=0.7,
                tooltip=f"風向: {direction}°, 風速: {speed:.1f} kt"
            ).add_to(m)
    
    else:  # ストリームライン
        # ストリームライン表示は実際の実装では複雑なので、MVPでは簡略化
        st.warning("ストリームライン表示は開発中です。現在はベクトル表示を使用しています。")
        
        # 代わりにベクトル表示
        for point in wind_field_data:
            lat, lon = point["position"]
            direction = point["direction"]
            speed = point["speed"]
            
            # フィルタリング
            if speed < min_wind_speed or speed > max_wind_speed:
                continue
            
            # 風向を示す矢印
            folium.RegularPolygonMarker(
                location=[lat, lon],
                fill_color="blue",
                number_of_sides=3,
                radius=5,
                rotation=direction,
                fill_opacity=0.7,
                tooltip=f"風向: {direction}°, 風速: {speed:.1f} kt"
            ).add_to(m)
    
    # GPSトラックの追加（透過度を上げて背景的に表示）
    track_data = generate_dummy_track_data(center_lat, center_lon)
    folium.PolyLine(
        track_data,
        color="#FF5733",
        weight=3,
        opacity=0.4,
        tooltip="GPSトラック"
    ).add_to(m)
    
    return m

# 戦略ポイント特化のマップを作成する関数
def create_strategy_points_map(point_types=None, importance_level="すべて", decision_quality="すべて"):
    """
    戦略ポイント特化のマップを作成する関数
    
    Args:
        point_types (list): 表示するポイントタイプのリスト
        importance_level (str): 重要度フィルター
        decision_quality (str): 判断品質フィルター
    
    Returns:
        folium.Map: 作成されたfoliumマップ
    """
    # ベースの位置（江の島周辺）
    center_lat, center_lon = 35.300, 139.480
    
    # foliumマップの作成
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    
    # 全画面表示ボタンの追加
    Fullscreen().add_to(m)
    
    # GPSトラックの追加（背景的に表示）
    track_data = generate_dummy_track_data(center_lat, center_lon)
    folium.PolyLine(
        track_data,
        color="#FF5733",
        weight=3,
        opacity=0.4,
        tooltip="GPSトラック"
    ).add_to(m)
    
    # 重要度と判断品質のマッピング
    importance_map = {
        "すべて": ["低", "中", "高", "最高"],
        "低": ["低"],
        "中": ["中"],
        "高": ["高"],
        "最高": ["最高"]
    }
    
    quality_map = {
        "すべて": ["最適", "適切", "改善必要", "不適切"],
        "最適": ["最適"],
        "適切": ["適切"],
        "改善必要": ["改善必要"],
        "不適切": ["不適切"]
    }
    
    # 適用するフィルターの取得
    importance_filter = importance_map.get(importance_level, [])
    quality_filter = quality_map.get(decision_quality, [])
    
    # 戦略ポイントデータの生成
    all_strategy_points = generate_dummy_strategy_points_detailed(center_lat, center_lon)
    
    # フィルタリング
    filtered_points = []
    for point in all_strategy_points:
        point_type = point["type"]
        importance = point["importance"]
        quality = point["quality"]
        
        # タイプフィルター
        if point_types and point_type not in point_types:
            continue
        
        # 重要度フィルター
        if importance_level != "すべて" and importance not in importance_filter:
            continue
        
        # 判断品質フィルター
        if decision_quality != "すべて" and quality not in quality_filter:
            continue
        
        filtered_points.append(point)
    
    # マーカークラスターの作成
    marker_cluster = MarkerCluster(name="戦略ポイント").add_to(m)
    
    # 戦略ポイントの描画
    for point in filtered_points:
        lat, lon = point["position"]
        point_type = point["type"]
        time = point["time"]
        description = point["description"]
        importance = point["importance"]
        quality = point["quality"]
        
        # ポイントタイプに応じたアイコン設定
        if point_type == "タック":
            icon_name = "exchange"
            color = "green"
        elif point_type == "ジャイブ":
            icon_name = "refresh"
            color = "orange"
        elif point_type == "風向シフト":
            icon_name = "flag"
            color = "blue"
        elif point_type == "レイライン":
            icon_name = "location-arrow"
            color = "purple"
        elif point_type == "障害物回避":
            icon_name = "warning"
            color = "red"
        else:  # コース変更など
            icon_name = "random"
            color = "cadetblue"
        
        # 判断品質に応じた色の調整
        if quality == "最適":
            color_prefix = "dark"
        elif quality == "不適切":
            color_prefix = "light"
        else:
            color_prefix = ""
        
        # 重要度に応じたアイコンサイズの調整（実際のfoliumでは難しいので、MVPではポップアップ内で表示）
        importance_stars = "★" * (["低", "中", "高", "最高"].index(importance) + 1)
        
        # マーカーの追加
        popup_html = f"""
        <div style='min-width: 200px'>
            <h4>{point_type} @ {time}</h4>
            <p><b>重要度:</b> {importance_stars}</p>
            <p><b>判断品質:</b> {quality}</p>
            <p>{description}</p>
        </div>
        """
        
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{point_type} ({quality})",
            icon=folium.Icon(color=color, icon=icon_name, prefix="fa")
        ).add_to(marker_cluster)
    
    return m

# ダミーGPSトラックデータを生成する関数
def generate_dummy_track_data(center_lat, center_lon):
    """
    ダミーのGPSトラックデータを生成する関数
    
    Args:
        center_lat (float): 中心緯度
        center_lon (float): 中心経度
    
    Returns:
        list: GPSトラックのポイントリスト
    """
    # シンプルなコース形状を生成
    track = []
    
    # スタート
    start_lat = center_lat - 0.01
    start_lon = center_lon - 0.02
    track.append([start_lat, start_lon])
    
    # 上に進む（風上へ）
    for i in range(1, 21):
        lat = start_lat + i * 0.001
        lon = start_lon + np.sin(i * 0.3) * 0.002
        track.append([lat, lon])
    
    # マーク回航
    mark_lat = start_lat + 0.02
    mark_lon = start_lon + 0.002
    track.append([mark_lat, mark_lon])
    
    # 下に進む（風下へ）
    for i in range(1, 21):
        lat = mark_lat - i * 0.001
        lon = mark_lon + 0.01 + np.sin(i * 0.3) * 0.002
        track.append([lat, lon])
    
    # 2回目の風上
    for i in range(1, 21):
        lat = start_lat + i * 0.001
        lon = start_lon + 0.02 + np.sin(i * 0.3) * 0.002
        track.append([lat, lon])
    
    return track

# ダミー風向データを生成する関数
def generate_dummy_wind_data(center_lat, center_lon, points):
    """
    ダミーの風向データを生成する関数
    
    Args:
        center_lat (float): 中心緯度
        center_lon (float): 中心経度
        points (int): 生成するポイント数
    
    Returns:
        list: 風向データのリスト
    """
    wind_data = []
    
    # エリア範囲
    lat_range = 0.03
    lon_range = 0.03
    
    # 基準風向と風速
    base_direction = 210  # 南西
    base_speed = 12.0  # 12kt
    
    # 格子点を生成
    grid_size = int(np.sqrt(points))
    for i in range(grid_size):
        for j in range(grid_size):
            lat = center_lat - lat_range/2 + lat_range * i / (grid_size - 1)
            lon = center_lon - lon_range/2 + lon_range * j / (grid_size - 1)
            
            # 位置による変動
            direction_var = np.sin(lat * 100) * 10 + np.cos(lon * 100) * 10
            speed_var = np.cos(lat * 100) * 2 + np.sin(lon * 100) * 2
            
            direction = (base_direction + direction_var) % 360
            speed = max(5, min(18, base_speed + speed_var))  # 5-18ktの範囲に制限
            
            wind_data.append({
                "position": [lat, lon],
                "direction": direction,
                "speed": speed
            })
    
    return wind_data

# ダミー風向場データを生成する関数
def generate_dummy_wind_field(center_lat, center_lon, points):
    """
    ダミーの風向場データを生成する関数
    
    Args:
        center_lat (float): 中心緯度
        center_lon (float): 中心経度
        points (int): 生成するポイント数
    
    Returns:
        list: 風向場データのリスト
    """
    wind_field = []
    
    # エリア範囲
    lat_range = 0.03
    lon_range = 0.03
    
    # 基準風速
    base_speed = 12.0  # 12kt
    
    # 格子点を生成
    grid_size = int(np.sqrt(points))
    for i in range(grid_size):
        for j in range(grid_size):
            lat = center_lat - lat_range/2 + lat_range * i / (grid_size - 1)
            lon = center_lon - lon_range/2 + lon_range * j / (grid_size - 1)
            
            # 位置による変動（単純な勾配）
            speed_var = np.cos(lat * 100) * 2 + np.sin(lon * 100) * 2
            speed = max(5, min(18, base_speed + speed_var))  # 5-18ktの範囲に制限
            
            wind_field.append([lat, lon, speed])
    
    return wind_field

# ダミー戦略ポイントデータを生成する関数
def generate_dummy_strategy_points(center_lat, center_lon):
    """
    ダミーの戦略ポイントデータを生成する関数
    
    Args:
        center_lat (float): 中心緯度
        center_lon (float): 中心経度
    
    Returns:
        list: 戦略ポイントのリスト
    """
    strategy_points = []
    
    # トラックデータを取得
    track = generate_dummy_track_data(center_lat, center_lon)
    
    # トラック上にいくつかの戦略ポイントを配置
    points = [
        {
            "position": track[5],
            "type": "tack",
            "time": "13:10",
            "description": "最初の風向シフトで早めにタック"
        },
        {
            "position": track[15],
            "type": "tack",
            "time": "13:20",
            "description": "風上マークに向けてレイラインでタック"
        },
        {
            "position": track[20],
            "type": "wind_shift",
            "time": "13:30",
            "description": "右シフト発生、対応良好"
        },
        {
            "position": track[28],
            "type": "layline",
            "time": "13:40",
            "description": "トップマークレイライン到達"
        },
        {
            "position": track[35],
            "type": "wind_shift",
            "time": "13:50",
            "description": "左シフト発生、対応が遅れる"
        },
        {
            "position": track[45],
            "type": "layline",
            "time": "14:05",
            "description": "ボトムマークレイライン到達"
        },
        {
            "position": track[55],
            "type": "tack",
            "time": "14:15",
            "description": "風向変化の兆候でタック"
        }
    ]
    
    strategy_points.extend(points)
    return strategy_points

# ダミータックポイントデータを生成する関数
def generate_dummy_tack_points(center_lat, center_lon):
    """
    ダミーのタックポイントデータを生成する関数
    
    Args:
        center_lat (float): 中心緯度
        center_lon (float): 中心経度
    
    Returns:
        list: タックポイントのリスト
    """
    tack_points = []
    
    # トラックデータを取得
    track = generate_dummy_track_data(center_lat, center_lon)
    
    # トラック上にいくつかのタックポイントを配置
    points = [
        {
            "position": track[5],
            "time": "13:10",
            "duration": 8,
            "speed_loss": 0.8
        },
        {
            "position": track[15],
            "time": "13:20",
            "duration": 7,
            "speed_loss": 0.6
        },
        {
            "position": track[35],
            "time": "13:45",
            "duration": 9,
            "speed_loss": 1.0
        },
        {
            "position": track[50],
            "time": "14:10",
            "duration": 6,
            "speed_loss": 0.5
        },
        {
            "position": track[60],
            "time": "14:25",
            "duration": 8,
            "speed_loss": 0.7
        }
    ]
    
    tack_points.extend(points)
    return tack_points

# ダミーレイラインデータを生成する関数
def generate_dummy_laylines(center_lat, center_lon):
    """
    ダミーのレイラインデータを生成する関数
    
    Args:
        center_lat (float): 中心緯度
        center_lon (float): 中心経度
    
    Returns:
        list: レイラインのリスト
    """
    laylines = []
    
    # トラックデータを取得してマークポイントを特定
    track = generate_dummy_track_data(center_lat, center_lon)
    mark_position = track[20]  # トップマーク位置
    
    # 左右のレイライン
    starboard_end = [mark_position[0] - 0.01, mark_position[1] - 0.01]
    port_end = [mark_position[0] - 0.01, mark_position[1] + 0.01]
    
    laylines.append({
        "points": [starboard_end, mark_position],
        "side": "starboard"
    })
    
    laylines.append({
        "points": [port_end, mark_position],
        "side": "port"
    })
    
    return laylines

# ダミーVMGデータを生成する関数
def generate_dummy_vmg_data(center_lat, center_lon, points):
    """
    ダミーのVMGデータを生成する関数
    
    Args:
        center_lat (float): 中心緯度
        center_lon (float): 中心経度
        points (int): 生成するポイント数
    
    Returns:
        list: VMGデータのリスト
    """
    vmg_data = []
    
    # トラックデータを取得
    track = generate_dummy_track_data(center_lat, center_lon)
    
    # トラックの周囲にVMGデータを生成
    for point in track[::len(track)//points]:  # トラックを間引いてポイント数を調整
        lat, lon = point
        
        # 周囲に小さな揺らぎを加える
        for _ in range(3):
            lat_var = np.random.normal(0, 0.0005)
            lon_var = np.random.normal(0, 0.0005)
            
            # VMG値（風上/風下で異なる）
            if lat > center_lat:  # 上半分（風上）
                vmg = np.random.normal(3.2, 0.5)
            else:  # 下半分（風下）
                vmg = np.random.normal(4.5, 0.6)
            
            vmg_data.append([lat + lat_var, lon + lon_var, vmg])
    
    return vmg_data

# ダミー速度データを生成する関数
def generate_dummy_speed_data(center_lat, center_lon, points):
    """
    ダミーの速度データを生成する関数
    
    Args:
        center_lat (float): 中心緯度
        center_lon (float): 中心経度
        points (int): 生成するポイント数
    
    Returns:
        list: 速度データのリスト
    """
    speed_data = []
    
    # トラックデータを取得
    track = generate_dummy_track_data(center_lat, center_lon)
    
    # トラックの周囲に速度データを生成
    for point in track[::len(track)//points]:  # トラックを間引いてポイント数を調整
        lat, lon = point
        
        # 周囲に小さな揺らぎを加える
        for _ in range(3):
            lat_var = np.random.normal(0, 0.0005)
            lon_var = np.random.normal(0, 0.0005)
            
            # 速度値（風上/風下で異なる）
            if lat > center_lat:  # 上半分（風上）
                speed = np.random.normal(5.5, 0.8)
            else:  # 下半分（風下）
                speed = np.random.normal(6.8, 0.7)
            
            speed_data.append([lat + lat_var, lon + lon_var, speed])
    
    return speed_data

# より詳細な風向場データを生成する関数
def generate_dummy_wind_field_detailed(center_lat, center_lon, points, 
                                       min_wind_speed, max_wind_speed, 
                                       wind_direction_range):
    """
    より詳細なダミーの風向場データを生成する関数
    
    Args:
        center_lat (float): 中心緯度
        center_lon (float): 中心経度
        points (int): 生成するポイント数
        min_wind_speed (float): 最小風速
        max_wind_speed (float): 最大風速
        wind_direction_range (tuple): 風向範囲
    
    Returns:
        list: 風向場データのリスト
    """
    wind_field = []
    
    # エリア範囲
    lat_range = 0.03
    lon_range = 0.03
    
    # 基準風向と風速
    base_direction = (wind_direction_range[0] + wind_direction_range[1]) / 2 if wind_direction_range[1] > wind_direction_range[0] else 210
    base_speed = (min_wind_speed + max_wind_speed) / 2
    
    # 格子点を生成
    grid_size = int(np.sqrt(points))
    for i in range(grid_size):
        for j in range(grid_size):
            lat = center_lat - lat_range/2 + lat_range * i / (grid_size - 1)
            lon = center_lon - lon_range/2 + lon_range * j / (grid_size - 1)
            
            # 位置による変動（複雑なパターンをシミュレート）
            lat_factor = np.sin(lat * 200) * 5
            lon_factor = np.cos(lon * 200) * 5
            distance_factor = np.sqrt((lat - center_lat)**2 + (lon - center_lon)**2) * 1000
            
            direction_var = lat_factor + lon_factor + np.sin(distance_factor) * 15
            speed_var = np.cos(lat * 100) * 1.5 + np.sin(lon * 100) * 1.5 + np.cos(distance_factor) * 2
            
            direction = (base_direction + direction_var) % 360
            speed = max(min_wind_speed, min(max_wind_speed, base_speed + speed_var))
            
            wind_field.append({
                "position": [lat, lon],
                "direction": direction,
                "speed": speed
            })
    
    return wind_field

# より詳細な戦略ポイントデータを生成する関数
def generate_dummy_strategy_points_detailed(center_lat, center_lon):
    """
    より詳細なダミーの戦略ポイントデータを生成する関数
    
    Args:
        center_lat (float): 中心緯度
        center_lon (float): 中心経度
    
    Returns:
        list: 戦略ポイントのリスト
    """
    strategy_points = []
    
    # トラックデータを取得
    track = generate_dummy_track_data(center_lat, center_lon)
    
    # 戦略ポイントの詳細データ
    points = [
        {
            "position": track[5],
            "type": "タック",
            "time": "13:10",
            "description": "風向シフト検出に対応し早めにタック。相対利得+20秒。",
            "importance": "高",
            "quality": "最適"
        },
        {
            "position": track[12],
            "type": "風向シフト",
            "time": "13:18",
            "description": "右シフト12度検出。対応が少し遅れる。",
            "importance": "中",
            "quality": "改善必要"
        },
        {
            "position": track[20],
            "type": "レイライン",
            "time": "13:30",
            "description": "トップマークレイラインに早めに到達。やや内側過ぎ。",
            "importance": "高",
            "quality": "適切"
        },
        {
            "position": track[27],
            "type": "コース変更",
            "time": "13:42",
            "description": "風下コースでのコース変更。VMG最適化に成功。",
            "importance": "中",
            "quality": "最適"
        },
        {
            "position": track[32],
            "type": "ジャイブ",
            "time": "13:52",
            "description": "風向シフトに合わせたジャイブ。タイミングが早過ぎた。",
            "importance": "高",
            "quality": "不適切"
        },
        {
            "position": track[40],
            "type": "風向シフト",
            "time": "14:05",
            "description": "左シフト15度検出。完全に見逃し。大きな不利。",
            "importance": "最高",
            "quality": "不適切"
        },
        {
            "position": track[48],
            "type": "障害物回避",
            "time": "14:18",
            "description": "他艇との交差回避。早めの判断で損失最小化。",
            "importance": "中",
            "quality": "適切"
        },
        {
            "position": track[55],
            "type": "レイライン",
            "time": "14:28",
            "description": "ボトムマークレイライン到達。理想的な接近角度。",
            "importance": "高",
            "quality": "最適"
        },
        {
            "position": track[60],
            "type": "タック",
            "time": "14:40",
            "description": "風上マークへの最終アプローチでのタック。タイミング良好。",
            "importance": "最高",
            "quality": "最適"
        }
    ]
    
    strategy_points.extend(points)
    return strategy_points

if __name__ == "__main__":
    render_page()
