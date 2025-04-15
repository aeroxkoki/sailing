"""
セーリング戦略分析システム - Windy.com風の風向風速表示コンポーネント

GPSデータと風向風速データを使用して、Windy.comスタイルのインタラクティブな
風の流れを表示するマップコンポーネントを提供します。
"""

import streamlit as st
import folium
import json
import numpy as np

def get_wind_color(speed):
    """風速に応じた色を返す（Windy.comスタイル）"""
    if speed < 5:
        return '#2468B4'  # 弱風: 青系
    elif speed < 10:
        return '#57AEC7'  # 中風: 青緑系
    elif speed < 15:
        return '#90C85E'  # 強風: 緑系
    elif speed < 20:
        return '#F8C537'  # 非常に強い風: 黄色系
    else:
        return '#F08119'  # 猛烈な風: オレンジ系

def create_wind_flow_map(center, wind_data, gps_track=None):
    """
    Windy.com風の風向風速表示を含むマップを作成
    
    Parameters:
    -----------
    center : tuple
        地図の中心座標 (緯度, 経度)
    wind_data : dict
        風データ {'lat': [...], 'lon': [...], 'direction': [...], 'speed': [...]}
    gps_track : list, optional
        GPSトラックポイントのリスト
    
    Returns:
    --------
    folium.Map
        Foliumマップオブジェクト
    """
    # 基本マップの作成
    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles='CartoDB positron',
        control_scale=True
    )
    
    # GPSトラックの表示（データがある場合）
    if gps_track is not None:
        folium.PolyLine(
            gps_track,
            color='#FF5722',
            weight=3,
            opacity=0.7
        ).add_to(m)
    
    # 風データをJSON形式に変換
    wind_data_json = json.dumps(wind_data)
    
    # 風の流れを表示するためのJavaScriptコード
    wind_flow_js = f"""
    <canvas id="wind-layer" style="position:absolute; left:0; top:0; z-index:400; pointer-events:none;"></canvas>
    
    <script>
    // 風データ
    const windData = {wind_data_json};
    
    // マップインスタンスを取得
    const map = document.querySelector('.folium-map')._leaflet_map;
    
    // キャンバス設定
    const canvas = document.getElementById('wind-layer');
    canvas.width = map.getSize().x;
    canvas.height = map.getSize().y;
    const ctx = canvas.getContext('2d');
    
    // 風向きに応じた色を取得する関数
    function getWindColor(speed) {{
        if (speed < 5) return '#2468B4';
        else if (speed < 10) return '#57AEC7';
        else if (speed < 15) return '#90C85E';
        else if (speed < 20) return '#F8C537';
        else return '#F08119';
    }}
    
    // 風粒子クラス
    class WindParticle {{
        constructor() {{
            this.reset();
        }}
        
        reset() {{
            // ランダムな位置に配置
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.age = 0;
            this.maxAge = 50 + Math.random() * 50;
        }}
        
        update() {{
            // 現在位置のピクセル座標を地理座標に変換
            const latlng = map.containerPointToLatLng([this.x, this.y]);
            
            // 最も近い風データポイントを見つける
            let closestPoint = null;
            let minDist = Infinity;
            
            for (let i = 0; i < windData.lat.length; i++) {{
                const dx = windData.lat[i] - latlng.lat;
                const dy = windData.lon[i] - latlng.lng;
                const dist = dx * dx + dy * dy;
                
                if (dist < minDist) {{
                    minDist = dist;
                    closestPoint = i;
                }}
            }}
            
            // 風向きと風速を取得
            if (closestPoint !== null) {{
                const direction = windData.direction[closestPoint] * Math.PI / 180;
                const speed = windData.speed[closestPoint];
                
                // 風の方向に移動（風向は「風が吹いてくる方向」なので反転）
                const moveX = Math.sin(direction + Math.PI) * speed * 0.5;
                const moveY = Math.cos(direction + Math.PI) * speed * 0.5;
                
                this.x += moveX;
                this.y += moveY;
                
                // 粒子を描画
                const alpha = 1 - (this.age / this.maxAge);
                ctx.strokeStyle = getWindColor(speed);
                ctx.globalAlpha = alpha;
                ctx.beginPath();
                ctx.moveTo(this.x, this.y);
                ctx.lineTo(this.x - moveX * 2, this.y - moveY * 2);
                ctx.stroke();
                
                // 粒子の寿命を増やす
                this.age++;
                
                // 画面外に出たか寿命が尽きたら新しい粒子にリセット
                if (this.x < 0 || this.x > canvas.width || 
                    this.y < 0 || this.y > canvas.height ||
                    this.age > this.maxAge) {{
                    this.reset();
                }}
            }}
        }}
    }}
    
    // 粒子の生成
    const particles = [];
    const particleCount = 1000;
    
    for (let i = 0; i < particleCount; i++) {{
        particles.push(new WindParticle());
    }}
    
    // アニメーションループ
    function animate() {{
        // 前のフレームをクリア
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // 粒子を更新
        for (let i = 0; i < particles.length; i++) {{
            particles[i].update();
        }}
        
        // 次のフレームを要求
        requestAnimationFrame(animate);
    }}
    
    // マップのズームや移動時にキャンバスを再調整
    map.on('moveend', function() {{
        canvas.width = map.getSize().x;
        canvas.height = map.getSize().y;
    }});
    
    // アニメーションを開始
    animate();
    </script>
    """
    
    # JavaScriptをマップに追加
    m.get_root().html.add_child(folium.Element(wind_flow_js))
    
    # 風速の凡例を追加
    legend_html = """
    <div style="position: fixed; bottom: 50px; right: 50px; z-index: 1000; background-color: white; padding: 10px; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2);">
      <div style="font-weight: bold; margin-bottom: 5px;">風速 (kt)</div>
      <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 10px; background-color: #2468B4; margin-right: 5px;"></div>
        <span>0-5</span>
      </div>
      <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 10px; background-color: #57AEC7; margin-right: 5px;"></div>
        <span>5-10</span>
      </div>
      <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 10px; background-color: #90C85E; margin-right: 5px;"></div>
        <span>10-15</span>
      </div>
      <div style="display: flex; align-items: center; margin-bottom: 5px;">
        <div style="width: 20px; height: 10px; background-color: #F8C537; margin-right: 5px;"></div>
        <span>15-20</span>
      </div>
      <div style="display: flex; align-items: center;">
        <div style="width: 20px; height: 10px; background-color: #F08119; margin-right: 5px;"></div>
        <span>20+</span>
      </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def display_wind_flow_map(center, wind_data, gps_track=None):
    """
    Windy.com風のマップをStreamlitに表示
    
    Parameters:
    -----------
    center : tuple
        地図の中心座標 (緯度, 経度)
    wind_data : dict
        風データ
    gps_track : list, optional
        GPSトラックポイントのリスト
    """
    # マップの作成
    m = create_wind_flow_map(center, wind_data, gps_track)
    
    # Streamlitに表示
    from streamlit_folium import folium_static
    folium_static(m, width=800, height=500)
    
    # 風向風速情報のサマリー表示
    if wind_data and len(wind_data.get('speed', [])) > 0:
        speeds = np.array(wind_data['speed'])
        avg_speed = np.mean(speeds)
        max_speed = np.max(speeds)
        
        # 主要風向を計算
        directions = np.array(wind_data['direction'])
        sin_sum = np.sum(np.sin(np.deg2rad(directions)))
        cos_sum = np.sum(np.cos(np.deg2rad(directions)))
        avg_direction = np.rad2deg(np.arctan2(sin_sum, cos_sum)) % 360
        
        # サマリー表示
        col1, col2, col3 = st.columns(3)
        col1.metric("平均風速", f"{avg_speed:.1f} kt")
        col2.metric("最大風速", f"{max_speed:.1f} kt")
        col3.metric("主要風向", f"{avg_direction:.0f}°")
