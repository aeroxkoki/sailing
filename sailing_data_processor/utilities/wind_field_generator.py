# -*- coding: utf-8 -*-
"""
セーリング戦略分析システム - 風場生成ユーティリティ

風向風速の流場を生成するためのユーティリティ関数を提供します。
テスト用およびシミュレーション用途です。
"""

import numpy as np

def generate_sample_wind_field(center_lat, center_lon, radius_km=5, grid_size=20):
    """
    テスト用のサンプル風データを生成
    
    Parameters:
    -----------
    center_lat : float
        中心緯度
    center_lon : float
        中心経度
    radius_km : float
        生成する風データの半径（キロメートル）
    grid_size : int
        グリッドの分割数
    
    Returns:
    --------
    dict
        風データディクショナリ
    """
    # 緯度経度グリッドの作成
    lat_offset = radius_km / 111  # 1度あたり約111km
    lon_offset = radius_km / (111 * np.cos(np.deg2rad(center_lat)))
    
    lat_min = center_lat - lat_offset
    lat_max = center_lat + lat_offset
    lon_min = center_lon - lon_offset
    lon_max = center_lon + lon_offset
    
    lats = np.linspace(lat_min, lat_max, grid_size)
    lons = np.linspace(lon_min, lon_max, grid_size)
    
    lat_grid, lon_grid = np.meshgrid(lats, lons)
    
    # 風向風速の生成（簡易的な風の場をシミュレート）
    # 中心から放射状に風が吹く + 全体的な基本風向
    base_direction = 225  # 南西の風
    
    # グリッド座標を平坦化
    flat_lats = lat_grid.flatten()
    flat_lons = lon_grid.flatten()
    
    # 風向風速データの作成
    directions = []
    speeds = []
    
    for i in range(len(flat_lats)):
        lat = flat_lats[i]
        lon = flat_lons[i]
        
        # 中心からの距離と角度を計算
        dlat = lat - center_lat
        dlon = lon - center_lon
        distance = np.sqrt(dlat**2 + dlon**2)
        
        # 中心からの影響
        angle_from_center = np.rad2deg(np.arctan2(dlon, dlat))
        # 基本風向と中心からの影響を混合
        direction = (base_direction + angle_from_center * 0.2) % 360
        
        # 風速（周期的なパターンを追加）
        speed = 8 + 3 * np.sin(distance * 10) + np.random.normal(0, 1)
        speed = max(1, min(25, speed))  # 風速を1〜25ノットに制限
        
        directions.append(direction)
        speeds.append(speed)
    
    # 結果を辞書形式で返す
    return {
        'lat': flat_lats.tolist(),
        'lon': flat_lons.tolist(),
        'direction': directions,
        'speed': speeds
    }
