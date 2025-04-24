#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風の移動予測ビジュアライゼーション

Streamlitを使用して風の移動モデルの予測結果を視覚化するモジュール
"""

import sys
import os
import streamlit as st
import pandas as pd
import numpy as np
import folium
from folium.plugins import TimestampedGeoJson
from streamlit_folium import folium_static
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import math
import time

# モジュールインポートのためにプロジェクトルートをパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from sailing_data_processor.wind_propagation_model import WindPropagationModel
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    import_success = True
except ImportError as e:
    import_success = False
    import_error = str(e)

# 定数定義
DEFAULT_LAT = 35.4
DEFAULT_LON = 139.7
DEFAULT_ZOOM = 13

def load_sample_data():
    """サンプルの風データを生成"""
    base_time = datetime.now()
    data = []
    
    # 基本風データを生成（20分間、1分間隔）
    base_lat, base_lon = 35.4, 139.7
    wind_dir, wind_speed = 90, 10  # 東風、10ノット
    
    for i in range(20):
        time = base_time + timedelta(minutes=i)
        # 時間経過とともに風向を少し変化させる（リアルさのため）
        wind_dir_shift = (i * 2) % 10 - 5  # -5°から+5°の変動
        
        # 緯度経度も風の移動に合わせて少し変化させる
        lon_offset = 0.001 * i * math.cos(math.radians(wind_dir))
        lat_offset = 0.001 * i * math.sin(math.radians(wind_dir))
        
        data.append({
            'timestamp': time,
            'latitude': base_lat + lat_offset,
            'longitude': base_lon + lon_offset,
            'wind_direction': wind_dir + wind_dir_shift,
            'wind_speed': wind_speed + (np.random.random() - 0.5)  # 風速に少し変動
        })
    
    return pd.DataFrame(data)

def create_wind_arrow_style(direction, speed, color='blue', scale=0.0001):
    """風向風速を表す矢印のスタイルを生成"""
    # 矢印の長さは風速に比例
    length = speed * scale
    
    # 風向を単位ベクトルに変換（度から北を0とする右回り方向に）
    # foliumのアイコンは上が0で時計回りなので調整
    rad = math.radians((90 - direction) % 360)  
    dx = length * math.cos(rad)
    dy = length * math.sin(rad)
    
    return {
        'icon': folium.features.DivIcon(
            icon_size=(150, 36),
            icon_anchor=(0, 0),
            html=f'''
                <div style="
                    font-size: 8pt;
                    color: {color};
                    transform: rotate({direction}deg);
                    transform-origin: 0 0;
                ">
                    <svg width="{speed*3}" height="15">
                        <line x1="0" y1="7.5" x2="{speed*3}" y2="7.5" 
                              style="stroke:{color};stroke-width:2" />
                        <polygon points="{speed*3-6},3 {speed*3},7.5 {speed*3-6},12" 
                                 style="fill:{color}" />
                    </svg>
                    <span style="margin-left: 5px; transform: rotate(-{direction}deg);">{speed:.1f}kt</span>
                </div>
            '''
        )
    }

def generate_wind_field_grid(center_lat, center_lon, radius_km=2, grid_size=7):
    """風の場を表示するためのグリッドを生成"""
    # 緯度1度は約111km、経度1度は緯度によって異なる
    lat_offset = radius_km / 111.0
    lon_offset = radius_km / (111.0 * math.cos(math.radians(center_lat)))
    
    lat_range = np.linspace(center_lat - lat_offset, center_lat + lat_offset, grid_size)
    lon_range = np.linspace(center_lon - lon_offset, center_lon + lon_offset, grid_size)
    
    grid_points = []
    for lat in lat_range:
        for lon in lon_range:
            grid_points.append((lat, lon))
    
    return grid_points

def predict_wind_field_at_time(model, historical_data, grid_points, target_time):
    """指定した時間での格子点上の風を予測"""
    predictions = []
    
    for lat, lon in grid_points:
        try:
            pred = model.predict_future_wind(
                position=(lat, lon),
                target_time=target_time,
                historical_data=historical_data
            )
            
            predictions.append({
                'latitude': lat,
                'longitude': lon,
                'wind_direction': pred['wind_direction'],
                'wind_speed': pred['wind_speed'],
                'confidence': pred['confidence'],
                'time': target_time
            })
        except Exception as e:
            st.error(f"予測エラー（位置: {lat},{lon}）: {e}")
    
    return predictions

def visualize_wind_field_on_map(historical_data, predictions, center_lat, center_lon):
    """地図上に風の場を可視化"""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=DEFAULT_ZOOM, 
                  tiles='CartoDB positron')
    
    # 過去の観測点を地図に追加
    for _, row in historical_data.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.5,
            popup=f"時間: {row['timestamp']}<br>"
                  f"風向: {row['wind_direction']:.1f}°<br>"
                  f"風速: {row['wind_speed']:.1f}ノット"
        ).add_to(m)
        
        # 各観測点に風向風速の矢印を追加
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            **create_wind_arrow_style(row['wind_direction'], row['wind_speed'], 'blue')
        ).add_to(m)
    
    # 予測点を地図に追加
    for pred in predictions:
        # 信頼度に基づいて色を変える（高信頼度ほど濃い色）
        color = f'rgba(255, 0, 0, {max(0.3, pred["confidence"])})'
        
        folium.CircleMarker(
            location=[pred['latitude'], pred['longitude']],
            radius=3,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.5,
            popup=f"予測時間: {pred['time']}<br>"
                  f"風向: {pred['wind_direction']:.1f}°<br>"
                  f"風速: {pred['wind_speed']:.1f}ノット<br>"
                  f"信頼度: {pred['confidence']:.2f}"
        ).add_to(m)
        
        # 各予測点に風向風速の矢印を追加
        folium.Marker(
            location=[pred['latitude'], pred['longitude']],
            **create_wind_arrow_style(pred['wind_direction'], pred['wind_speed'], 'red')
        ).add_to(m)
    
    return m

def visualize_wind_field_heatmap(predictions, center_lat, center_lon):
    """予測風の場の信頼度をヒートマップで可視化"""
    # 緯度・経度の範囲を計算
    lats = [p['latitude'] for p in predictions]
    lons = [p['longitude'] for p in predictions]
    
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    
    # グリッドサイズを計算
    grid_size = int(math.sqrt(len(predictions)))
    
    # データをグリッドに整形
    lat_grid = np.linspace(lat_min, lat_max, grid_size)
    lon_grid = np.linspace(lon_min, lon_max, grid_size)
    
    # 風向・風速・信頼度の配列を作成
    dir_grid = np.zeros((grid_size, grid_size))
    speed_grid = np.zeros((grid_size, grid_size))
    conf_grid = np.zeros((grid_size, grid_size))
    
    # 最も近いグリッドポイントに値を代入
    for p in predictions:
        i = np.argmin(np.abs(lat_grid - p['latitude']))
        j = np.argmin(np.abs(lon_grid - p['longitude']))
        dir_grid[i, j] = p['wind_direction']
        speed_grid[i, j] = p['wind_speed']
        conf_grid[i, j] = p['confidence']
    
    # Plotlyを使った対話的プロット作成
    fig = go.Figure()
    
    # 風速ヒートマップタブ
    fig.add_trace(
        go.Heatmap(
            z=speed_grid,
            x=lon_grid,
            y=lat_grid,
            colorscale='Viridis',
            colorbar=dict(title='風速 (ノット)'),
            name='風速',
            hovertemplate='緯度: %{y:.4f}<br>経度: %{x:.4f}<br>風速: %{z:.1f}ノット<extra></extra>'
        )
    )
    
    # 信頼度ヒートマップタブ
    fig.add_trace(
        go.Heatmap(
            z=conf_grid,
            x=lon_grid,
            y=lat_grid,
            colorscale='RdYlGn',
            colorbar=dict(title='信頼度'),
            visible=False,
            name='信頼度',
            hovertemplate='緯度: %{y:.4f}<br>経度: %{x:.4f}<br>信頼度: %{z:.2f}<extra></extra>'
        )
    )
    
    # 風向ヒートマップタブ
    fig.add_trace(
        go.Heatmap(
            z=dir_grid,
            x=lon_grid,
            y=lat_grid,
            colorscale='HSV',  # HSVカラースケールは角度表現に適しています
            colorbar=dict(title='風向 (度)'),
            visible=False,
            name='風向',
            hovertemplate='緯度: %{y:.4f}<br>経度: %{x:.4f}<br>風向: %{z:.1f}°<extra></extra>'
        )
    )
    
    # ボタンで表示切り替え
    fig.update_layout(
        updatemenus=[
            dict(
                type='buttons',
                direction='right',
                active=0,
                x=0.5,
                y=1.15,
                xanchor='center',
                yanchor='top',
                buttons=list([
                    dict(label='風速',
                         method='update',
                         args=[{'visible': [True, False, False]},
                               {'title': '予測風速 (ノット)'}]),
                    dict(label='信頼度',
                         method='update',
                         args=[{'visible': [False, True, False]},
                               {'title': '予測信頼度'}]),
                    dict(label='風向',
                         method='update',
                         args=[{'visible': [False, False, True]},
                               {'title': '予測風向 (度)'}])
                ]),
            )
        ],
        title='予測風速 (ノット)',
        xaxis_title='経度',
        yaxis_title='緯度',
        height=600,
        margin=dict(t=100)  # タイトルとボタンのスペース確保
    )
    
    return fig

def visualize_wind_direction_quiver(predictions, center_lat, center_lon):
    """予測風向をクイバー（矢印）で可視化（Plotlyバージョン）"""
    # 緯度・経度の範囲を計算
    lats = [p['latitude'] for p in predictions]
    lons = [p['longitude'] for p in predictions]
    
    # グリッドサイズを計算
    grid_size = int(math.sqrt(len(predictions)))
    
    # クイバープロット用のデータ整形
    x = np.array(lons).reshape(grid_size, grid_size)
    y = np.array(lats).reshape(grid_size, grid_size)
    
    # 風向を単位ベクトルに変換
    u = np.array([math.sin(math.radians(p['wind_direction'])) for p in predictions]).reshape(grid_size, grid_size)
    v = np.array([math.cos(math.radians(p['wind_direction'])) for p in predictions]).reshape(grid_size, grid_size)
    
    # 風速をスケーリング
    speeds = np.array([p['wind_speed'] for p in predictions]).reshape(grid_size, grid_size)
    
    # Plotlyでのクイバープロット
    # 平坦化して配列を準備
    x_flat = x.flatten()
    y_flat = y.flatten()
    u_flat = u.flatten()
    v_flat = v.flatten()
    speeds_flat = speeds.flatten()
    
    # 風向と風速の取得（ホバー表示用）
    wind_dirs = np.array([p['wind_direction'] for p in predictions])
    
    # Plotlyの図を作成
    fig = go.Figure()
    
    # スケーリング係数（矢印の長さ調整）
    scale = 0.003
    
    # クイバープロット用のデータポイント
    # go.Scatterのモードを'markers+lines'に設定して矢印を表現
    for i in range(len(x_flat)):
        # 風の強さに応じた色のスケーリング
        color_intensity = int(255 * (speeds_flat[i] - speeds.min()) / (speeds.max() - speeds.min()))
        color = f'rgb(0, {color_intensity}, 255)'
        
        # 矢印の終点計算
        arrow_x = x_flat[i] + u_flat[i] * scale * speeds_flat[i]
        arrow_y = y_flat[i] + v_flat[i] * scale * speeds_flat[i]
        
        # 各点に矢印を追加
        fig.add_trace(go.Scatter(
            x=[x_flat[i], arrow_x],
            y=[y_flat[i], arrow_y],
            mode='lines+markers',
            line=dict(color=color, width=1.5),
            marker=dict(size=[0, 5], color=color),
            showlegend=False,
            hoverinfo='text',
            hovertext=f'緯度: {y_flat[i]:.4f}<br>経度: {x_flat[i]:.4f}<br>' +
                     f'風向: {wind_dirs[i]:.1f}°<br>風速: {speeds_flat[i]:.1f}ノット'
        ))
    
    # 風速に基づくヒートマップを追加（背景レイヤー）
    fig.add_trace(go.Contour(
        z=speeds,
        x=lons,
        y=lats,
        colorscale='Viridis',
        colorbar=dict(title='風速 (ノット)'),
        opacity=0.6,
        showscale=True,
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # レイアウト設定
    fig.update_layout(
        title='予測風向風速',
        xaxis_title='経度',
        yaxis_title='緯度',
        height=600,
        margin=dict(t=50, r=50, b=50, l=50)
    )
    
    return fig

def show_wind_propagation_animation(historical_data, model, center_lat, center_lon):
    """風の移動を時間経過アニメーションで可視化"""
    st.write("### 風の移動予測アニメーション")
    
    # 現在の最新時刻
    current_time = historical_data['timestamp'].max()
    
    # 予測時間（30分後まで、5分間隔）
    forecast_times = [current_time + timedelta(minutes=i*5) for i in range(7)]
    
    # 予測対象の格子点
    grid_points = generate_wind_field_grid(center_lat, center_lon, radius_km=2, grid_size=7)
    
    # プログレスバーを表示
    progress_bar = st.progress(0)
    st.write("予測計算中...")
    
    # 各時間の予測を計算
    all_predictions = []
    historical_list = historical_data.to_dict('records')
    
    for i, target_time in enumerate(forecast_times):
        time_predictions = predict_wind_field_at_time(
            model, historical_list, grid_points, target_time
        )
        all_predictions.append(time_predictions)
        progress_bar.progress((i + 1) / len(forecast_times))
    
    # アニメーション表示部分
    st.write("各時間の風向風速予測:")
    
    # タイムスライダー
    time_index = st.slider("時間選択", 0, len(forecast_times) - 1, 0)
    selected_time = forecast_times[time_index]
    selected_predictions = all_predictions[time_index]
    
    st.write(f"表示時間: {selected_time}")
    
    # 地図表示
    m = visualize_wind_field_on_map(historical_data, selected_predictions, center_lat, center_lon)
    folium_static(m)
    
    # ヒートマップとクイバープロット
    if st.checkbox("詳細な風向風速分布を表示"):
        tab1, tab2 = st.tabs(["ヒートマップ", "クイバープロット"])
        
        with tab1:
            fig_heatmap = visualize_wind_field_heatmap(selected_predictions, center_lat, center_lon)
            st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with tab2:
            fig_quiver = visualize_wind_direction_quiver(selected_predictions, center_lat, center_lon)
            st.plotly_chart(fig_quiver, use_container_width=True)

def app():
    """Streamlitアプリのメイン関数"""
    st.title("風の移動予測ビジュアライゼーション")
    
    if not import_success:
        st.error(f"モジュールのインポートに失敗しました: {import_error}")
        st.info("このツールを使用するには、先にセーリング戦略分析システムのモジュールが正しくインストールされている必要があります。")
        return
    
    st.sidebar.header("設定")
    
    # サンプルデータの読み込み
    if st.sidebar.button("サンプルデータを生成"):
        sample_data = load_sample_data()
        st.session_state.data = sample_data
        st.success(f"サンプルデータを生成しました（{len(sample_data)}ポイント）")
    
    # GPSファイルのアップロード
    uploaded_file = st.sidebar.file_uploader("GPSデータをアップロード（CSVまたはGPX）", 
                                           type=["csv", "gpx"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                # CSVファイルを処理
                data = pd.read_csv(uploaded_file)
                
                # カラム名の確認と修正
                required_columns = ['timestamp', 'latitude', 'longitude', 'wind_direction', 'wind_speed']
                if not all(col in data.columns for col in required_columns):
                    st.error("必要なカラムが見つかりません。CSVには次のカラムが必要です: " + ", ".join(required_columns))
                    return
                
                st.success(f"CSVファイルをロードしました（{len(data)}ポイント）")
                st.session_state.data = data
                
            elif uploaded_file.name.endswith('.gpx'):
                st.error("GPXファイルのサポートは準備中です")
                return
                
        except Exception as e:
            st.error(f"ファイル読み込みエラー: {e}")
            return
    
    # データが読み込まれているか確認
    if 'data' not in st.session_state:
        st.info("サイドバーから「サンプルデータを生成」ボタンをクリックするか、GPSデータをアップロードしてください。")
        return
    
    data = st.session_state.data
    
    # データプレビュー
    with st.expander("データプレビュー"):
        st.dataframe(data.head())
    
    # 位置設定
    st.sidebar.subheader("位置設定")
    center_lat = st.sidebar.number_input("中心緯度", value=data['latitude'].mean())
    center_lon = st.sidebar.number_input("中心経度", value=data['longitude'].mean())
    
    # データの可視化
    st.header("風データの可視化")
    
    # WindPropagationModelを初期化
    model = WindPropagationModel()
    
    # 風の移動ベクトルを推定
    data_list = data.to_dict('records')
    propagation_vector = model.estimate_propagation_vector(data_list)
    
    # 風の移動ベクトルを表示
    st.subheader("風の移動ベクトル推定結果")
    col1, col2, col3 = st.columns(3)
    col1.metric("移動速度", f"{propagation_vector['speed']:.2f} m/s")
    col2.metric("移動方向", f"{propagation_vector['direction']:.1f}°")
    col3.metric("信頼度", f"{propagation_vector['confidence']:.2f}")
    
    # 風の移動アニメーション
    show_wind_propagation_animation(data, model, center_lat, center_lon)
    
    st.header("精度と信頼性")
    st.info("""
    風の移動予測の信頼度は、以下の要因に依存します：
    - 入力データの品質と密度
    - 予測先の時間的・空間的距離
    - 風況の安定性

    信頼度の色は次のように解釈できます：
    - 🟢 高信頼度（0.7以上）：信頼性の高い予測
    - 🟡 中信頼度（0.4-0.7）：やや不確実だが参考になる予測
    - 🔴 低信頼度（0.4未満）：不確実性が高い予測
    """)

if __name__ == "__main__":
    app()
