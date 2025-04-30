# -*- coding: utf-8 -*-
"""
sailing_data_processor.wind_field_fusion_utils モジュール

風の場融合システムのためのユーティリティ関数を提供します。
"""

import numpy as np
import math
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime
from scipy.interpolate import griddata

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2点間のHaversine距離を計算（メートル）
    
    Parameters:
    -----------
    lat1, lon1 : float
        始点の緯度経度
    lat2, lon2 : float
        終点の緯度経度
        
    Returns:
    --------
    float
        距離（メートル）
    """
    # 地球の半径（メートル）
    R = 6371000
    
    # 緯度経度をラジアンに変換
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # 差分
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversineの公式
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance

def scale_data_points(data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    風データポイントを適切にスケーリングして補間処理を安定化
    
    Parameters:
    -----------
    data_points : List[Dict]
        風データポイントのリスト
        
    Returns:
    --------
    List[Dict]
        スケーリングされたデータポイントのリスト
    """
    if not data_points:
        return []
        
    # メモリ効率のため、必要なデータだけを抽出して事前に配列化
    num_points = len(data_points)
    lats = np.zeros(num_points, dtype=np.float32)
    lons = np.zeros(num_points, dtype=np.float32)
    winds = np.zeros(num_points, dtype=np.float32)
    
    # 一度にデータを抽出（ループで複数回アクセスするのを避ける）
    for i, point in enumerate(data_points):
        lats[i] = point['latitude']
        lons[i] = point['longitude']
        winds[i] = point['wind_speed']
    
    # NumPyの組み込み関数を使用して効率的に最小・最大値を計算
    min_lat, max_lat = np.min(lats), np.max(lats)
    min_lon, max_lon = np.min(lons), np.max(lons)
    min_wind, max_wind = np.min(winds), np.max(winds)
    
    # 範囲の計算（一度だけ）
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    wind_range = max_wind - min_wind
    
    # 前もって結果配列を確保（メモリ効率向上）
    scaled_data = []
    
    # 緯度・経度の範囲が狭すぎる場合は人工的に広げる
    min_range = 0.005  # 約500mの最小範囲に拡大
    
    # 必要に応じて範囲を確保（より効率的な計算）
    if lat_range < min_range:
        lat_padding = (min_range - lat_range) / 2 + 0.001
        min_lat -= lat_padding
        max_lat += lat_padding
        lat_range = min_range + 0.002  # パディング後の範囲更新
    
    if lon_range < min_range:
        lon_padding = (min_range - lon_range) / 2 + 0.001
        min_lon -= lon_padding
        max_lon += lon_padding
        lon_range = min_range + 0.002  # パディング後の範囲更新
    
    # 風速の最小範囲を確保
    min_wind_range = 1.0
    if wind_range < min_wind_range:
        wind_padding = (min_wind_range - wind_range) / 2 + 0.2
        min_wind = max(0, min_wind - wind_padding)
        max_wind += wind_padding
        wind_range = min_wind_range + 0.4  # パディング後の範囲更新
    
    # スケール係数を一度だけ計算（ゼロ除算を回避）
    scale_lat = 1.0 / lat_range if lat_range > 0 else 1.0
    scale_lon = 1.0 / lon_range if lon_range > 0 else 1.0
    scale_wind = 1.0 / wind_range if wind_range > 0 else 1.0
    
    # ランダムジッター用に予めシード値を固定（再現性確保）
    np.random.seed(42)
    
    # 一度にジッターランダム値を生成（ベクトル化）
    jitter_lats = np.random.normal(0, 0.002, num_points)
    jitter_lons = np.random.normal(0, 0.002, num_points)
    jitter_winds = np.random.normal(0, 0.005, num_points)
    
    # データポイントのバッチ処理
    for i, point in enumerate(data_points):
        # ポイントデータを変更するのではなく、新しい辞書を作成
        scaled_point = point.copy()
        
        # 正規化と同時にジッターを追加（計算を1回に統合）
        norm_lat = (lats[i] - min_lat) * scale_lat + jitter_lats[i]
        norm_lon = (lons[i] - min_lon) * scale_lon + jitter_lons[i]
        norm_wind = (winds[i] - min_wind) * scale_wind + jitter_winds[i]
        
        # スケーリングした座標を設定（中間変数の再利用を最小化）
        scaled_point['scaled_latitude'] = norm_lat
        scaled_point['scaled_longitude'] = norm_lon
        scaled_point['scaled_height'] = norm_wind
        
        # 元の値を保持
        scaled_point['original_latitude'] = lats[i]
        scaled_point['original_longitude'] = lons[i]
        
        # スケーリングされた値を使用
        scaled_point['latitude'] = norm_lat
        scaled_point['longitude'] = norm_lon
        scaled_point['height'] = norm_wind
        
        # 結果リストに追加
        scaled_data.append(scaled_point)
        
    return scaled_data

def restore_original_coordinates(scaled_data_points: List[Dict[str, Any]]) -> None:
    """
    スケーリングされたデータポイントの座標を元に戻す
    
    Parameters:
    -----------
    scaled_data_points : List[Dict]
        スケーリングされたデータポイントのリスト
    """
    for point in scaled_data_points:
        if 'original_latitude' in point and 'original_longitude' in point:
            point['latitude'] = point['original_latitude']
            point['longitude'] = point['original_longitude']

def create_dummy_wind_field(timestamp: datetime, grid_resolution: int = 10) -> Dict[str, Any]:
    """
    テスト用のダミー風の場を生成する
    データが不足している場合や、エラー発生時のフォールバックとして使用
    
    Parameters:
    -----------
    timestamp : datetime
        風の場のタイムスタンプ
    grid_resolution : int
        出力グリッド解像度
    
    Returns:
    --------
    Dict[str, Any]
        ダミーの風の場
    """
    # デフォルトの緯度経度範囲（東京湾付近）
    min_lat, max_lat = 35.4, 35.5
    min_lon, max_lon = 139.6, 139.7
    
    # グリッドの作成
    lat_range = np.linspace(min_lat, max_lat, grid_resolution)
    lon_range = np.linspace(min_lon, max_lon, grid_resolution)
    grid_lats, grid_lons = np.meshgrid(lat_range, lon_range)
    
    # 一定の風向風速（比較的典型的な東京湾の風）
    wind_dir = 225.0  # 南西の風
    wind_speed = 5.0  # 5m/s
    
    # 全グリッドに同じ値を設定
    wind_dirs = np.full_like(grid_lats, wind_dir)
    wind_speeds = np.full_like(grid_lats, wind_speed)
    
    # 信頼度は低めに設定
    confidence = np.full_like(grid_lats, 0.3)
    
    # ダミーの風の場
    return {
        'lat_grid': grid_lats,
        'lon_grid': grid_lons,
        'wind_direction': wind_dirs,
        'wind_speed': wind_speeds,
        'confidence': confidence,
        'time': timestamp,
        'is_dummy': True  # ダミーデータであることを示すフラグ
    }

def create_simple_wind_field(data_points: List[Dict[str, Any]], 
                         grid_resolution: int, 
                         timestamp: datetime) -> Dict[str, Any]:
    """
    最も単純な方法で風の場を生成するフォールバックメソッド
    他の補間方法が失敗した場合の最終手段として使用
    
    Parameters:
    -----------
    data_points : List[Dict]
        風データポイントのリスト
    grid_resolution : int
        出力グリッド解像度
    timestamp : datetime
        風の場のタイムスタンプ
        
    Returns:
    --------
    Dict[str, Any]
        作成された風の場
    """
    if not data_points:
        # データポイントがない場合は東京湾付近のダミーデータを作成
        return create_dummy_wind_field(timestamp, grid_resolution)
        
    # データポイントから緯度・経度の範囲を取得
    lats = [point['latitude'] for point in data_points]
    lons = [point['longitude'] for point in data_points]
    
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # 範囲が狭すぎる場合は人工的に広げる
    if abs(max_lat - min_lat) < 0.005:
        padding = (0.005 - abs(max_lat - min_lat)) / 2
        min_lat -= padding
        max_lat += padding
        
    if abs(max_lon - min_lon) < 0.005:
        padding = (0.005 - abs(max_lon - min_lon)) / 2
        min_lon -= padding
        max_lon += padding
    
    # グリッドの作成
    lat_range = np.linspace(min_lat, max_lat, grid_resolution)
    lon_range = np.linspace(min_lon, max_lon, grid_resolution)
    grid_lats, grid_lons = np.meshgrid(lat_range, lon_range)
    
    # 風向風速の平均値を計算（風向はベクトル平均）
    sin_sum = 0
    cos_sum = 0
    speed_sum = 0
    
    for point in data_points:
        dir_rad = math.radians(point['wind_direction'])
        sin_sum += math.sin(dir_rad)
        cos_sum += math.cos(dir_rad)
        speed_sum += point['wind_speed']
    
    # 平均風向
    avg_dir = math.degrees(math.atan2(sin_sum, cos_sum)) % 360
    
    # 平均風速
    avg_speed = speed_sum / len(data_points)
    
    # 全グリッドに同じ値を設定
    wind_dirs = np.full_like(grid_lats, avg_dir)
    wind_speeds = np.full_like(grid_lats, avg_speed)
    
    # 信頼度は低めに設定
    confidence = np.full_like(grid_lats, 0.4)
    
    # 風の場の作成
    wind_field = {
        'lat_grid': grid_lats,
        'lon_grid': grid_lons,
        'wind_direction': wind_dirs,
        'wind_speed': wind_speeds,
        'confidence': confidence,
        'time': timestamp
    }
    
    return wind_field

def interpolate_field_to_grid(source_field: Dict[str, Any], 
                          target_lat_grid: np.ndarray, 
                          target_lon_grid: np.ndarray) -> Optional[Dict[str, Any]]:
    """
    風の場を新しいグリッドに補間
    
    Parameters:
    -----------
    source_field : Dict[str, Any]
        元の風の場
    target_lat_grid : np.ndarray
        対象の緯度グリッド
    target_lon_grid : np.ndarray
        対象の経度グリッド
        
    Returns:
    --------
    Dict[str, Any] or None
        補間された風の場
    """
    try:
        # 元の風の場のグリッド情報を取得
        source_lat_grid = source_field['lat_grid']
        source_lon_grid = source_field['lon_grid']
        source_wind_dirs = source_field['wind_direction']
        source_wind_speeds = source_field['wind_speed']
        source_confidence = source_field['confidence']
        
        # 元のポイントを準備
        points = np.vstack([source_lat_grid.ravel(), source_lon_grid.ravel()]).T
        
        # 対象のポイントを準備
        xi = np.vstack([target_lat_grid.ravel(), target_lon_grid.ravel()]).T
        
        # 風向の補間（循環データなので特別な処理が必要）
        sin_dirs = np.sin(np.radians(source_wind_dirs.ravel()))
        cos_dirs = np.cos(np.radians(source_wind_dirs.ravel()))
        
        interp_sin = griddata(points, sin_dirs, xi, method='linear', fill_value=0)
        interp_cos = griddata(points, cos_dirs, xi, method='linear', fill_value=1)
        
        interp_dirs = np.degrees(np.arctan2(interp_sin, interp_cos)) % 360
        interp_dirs = interp_dirs.reshape(target_lat_grid.shape)
        
        # 風速の補間
        interp_speeds = griddata(points, source_wind_speeds.ravel(), xi, method='linear', fill_value=0)
        interp_speeds = interp_speeds.reshape(target_lat_grid.shape)
        
        # 信頼度の補間
        interp_conf = griddata(points, source_confidence.ravel(), xi, method='linear', fill_value=0.3)
        interp_conf = interp_conf.reshape(target_lat_grid.shape)
        
        # 補間された風の場を返す
        return {
            'lat_grid': target_lat_grid,
            'lon_grid': target_lon_grid,
            'wind_direction': interp_dirs,
            'wind_speed': interp_speeds,
            'confidence': interp_conf,
            'time': source_field.get('time')
        }
        
    except Exception as e:
        print(f"Field interpolation failed: {e}")
        return None
