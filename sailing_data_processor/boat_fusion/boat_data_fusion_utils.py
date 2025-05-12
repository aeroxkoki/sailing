# -*- coding: utf-8 -*-
"""
sailing_data_processor.boat_fusion.boat_data_fusion_utils モジュール

船舶データ融合のためのユーティリティ関数を提供します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
from scipy.spatial import KDTree
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel, ConstantKernel

def bayesian_wind_integration(model, boat_data: List[Dict[str, Any]], 
                            time_point: datetime) -> Dict[str, Any]:
    """
    ベイズ更新を使用した風向風速の統合
    
    Parameters:
    -----------
    model : BoatDataFusionModel
        モデルインスタンス
    boat_data : List[Dict[str, Any]]
        各艇の風推定データ
    time_point : datetime
        対象時間点
        
    Returns:
    --------
    Dict[str, Any]
        ベイズ更新された風向風速データ
    """
    # 十分なデータがなければ単純な重み付き平均を使用
    if len(boat_data) < 3:
        return weighted_average_integration(boat_data)
    
    # 1. 風向の統合（循環データなので特殊処理）
    
    # 事前分布の平均（指定がない場合は最初の推定値を使用）
    if model.wind_dir_prior_mean is None:
        model.wind_dir_prior_mean = boat_data[0]['wind_direction']
    
    # 風向のsin/cos成分を変換
    dir_sin_values = [math.sin(math.radians(d['wind_direction'])) for d in boat_data]
    dir_cos_values = [math.cos(math.radians(d['wind_direction'])) for d in boat_data]
    
    # 風向の重み
    dir_weights = [d['weight'] for d in boat_data]
    
    # 事前確率の組み込み
    prior_weight = 0.3  # 事前確率の重み
    
    # 事前分布のsin/cos
    prior_sin = math.sin(math.radians(model.wind_dir_prior_mean))
    prior_cos = math.cos(math.radians(model.wind_dir_prior_mean))
    
    # 重み付き平均のsin/cos
    weighted_sin = np.average(dir_sin_values, weights=dir_weights)
    weighted_cos = np.average(dir_cos_values, weights=dir_weights)
    
    # 事前確率と観測値の統合
    posterior_sin = (prior_sin * prior_weight + weighted_sin * (1 - prior_weight))
    posterior_cos = (prior_cos * prior_weight + weighted_cos * (1 - prior_weight))
    
    # 風向の復元
    integrated_direction = math.degrees(math.atan2(posterior_sin, posterior_cos)) % 360
    
    # 分散の計算
    dir_variance = 0.0
    for i, d in enumerate(boat_data):
        # 風向の差（循環性を考慮）
        dir_diff = abs((d['wind_direction'] - integrated_direction + 180) % 360 - 180)
        dir_variance += dir_diff**2 * dir_weights[i]
    
    dir_variance /= sum(dir_weights)
    dir_std = math.sqrt(dir_variance)
    
    # 方向の不確実性（0-1の範囲で、0が最も確実）
    dir_uncertainty = min(1.0, dir_std / 90.0)  # 90度の標準偏差で最大不確実性
    
    # 2. 風速の統合
    
    # 事前分布の平均（指定がない場合は最初の推定値を使用）
    if model.wind_speed_prior_mean is None:
        model.wind_speed_prior_mean = boat_data[0]['wind_speed_knots']
    
    # 風速の値と重み
    speed_values = [d['wind_speed_knots'] for d in boat_data]
    speed_weights = [d['weight'] for d in boat_data]
    
    # ロバスト重み付き平均（外れ値に強い）
    speed_data = np.array(speed_values)
    speed_median = np.median(speed_data)
    
    # 中央値からの差を計算
    speed_deviations = np.abs(speed_data - speed_median)
    max_deviation = np.max(speed_deviations) if len(speed_deviations) > 0 else 1.0
    if max_deviation == 0:
        max_deviation = 1.0
    
    # 中央値からの距離に基づいて重みを調整
    robust_weights = np.array(speed_weights) * (1 - speed_deviations / max_deviation)
    robust_weights = np.maximum(0.1, robust_weights)  # 最小重みを0.1に設定
    
    # 重み付き平均
    if sum(robust_weights) > 0:
        weighted_speed = np.average(speed_data, weights=robust_weights)
    else:
        weighted_speed = np.mean(speed_data)
    
    # 事前確率と観測値の統合
    integrated_speed = (model.wind_speed_prior_mean * prior_weight + 
                     weighted_speed * (1 - prior_weight))
    
    # 分散の計算
    speed_variance = 0.0
    for i, speed in enumerate(speed_values):
        speed_variance += (speed - integrated_speed)**2 * robust_weights[i]
    
    if sum(robust_weights) > 0:
        speed_variance /= sum(robust_weights)
    else:
        speed_variance = np.var(speed_values)
    
    speed_std = math.sqrt(speed_variance)
    
    # 速度の不確実性（0-1の範囲で、0が最も確実）
    speed_uncertainty = min(1.0, speed_std / (integrated_speed * 0.5 + 0.1))  # 風速の50%の標準偏差で最大不確実性
    
    # 3. 信頼度の計算
    
    # 観測数に基づく信頼度向上
    n_factor = min(0.2, 0.05 * len(boat_data))  # 最大0.2の信頼度向上
    
    # 総合的な信頼度
    base_confidence = 0.5 + n_factor
    adjusted_confidence = base_confidence * (1 - 0.6 * dir_uncertainty) * (1 - 0.4 * speed_uncertainty)
    
    # 経度緯度の計算（重み付き平均）
    latitude, longitude = None, None
    valid_positions = [(d['latitude'], d['longitude'], d['weight']) 
                     for d in boat_data if d['latitude'] is not None and d['longitude'] is not None]
    
    if valid_positions:
        total_weight = sum(w for _, _, w in valid_positions)
        if total_weight > 0:
            latitude = sum(lat * w for lat, _, w in valid_positions) / total_weight
            longitude = sum(lon * w for _, lon, w in valid_positions) / total_weight
    
    # 結果の整理
    return {
        'timestamp': time_point,
        'wind_direction': integrated_direction,
        'wind_speed': integrated_speed,
        'confidence': adjusted_confidence,
        'direction_std': dir_std,
        'speed_std': speed_std,
        'latitude': latitude,
        'longitude': longitude,
        'boat_count': len(boat_data)
    }

def weighted_average_integration(boat_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    単純な重み付き平均による風向風速の統合
    
    Parameters:
    -----------
    boat_data : List[Dict[str, Any]]
        各艇の風推定データ
        
    Returns:
    --------
    Dict[str, Any]
        重み付き平均による風向風速データ
    """
    # 重み付き平均のための準備
    dir_sin_values = [math.sin(math.radians(d['wind_direction'])) for d in boat_data]
    dir_cos_values = [math.cos(math.radians(d['wind_direction'])) for d in boat_data]
    speed_values = [d['wind_speed_knots'] for d in boat_data]
    weights = [d['weight'] for d in boat_data]
    timestamps = [d['timestamp'] for d in boat_data]
    
    # 風向の重み付き平均（sin/cosを使用）
    if sum(weights) > 0:
        weighted_sin = np.average(dir_sin_values, weights=weights)
        weighted_cos = np.average(dir_cos_values, weights=weights)
        integrated_direction = math.degrees(math.atan2(weighted_sin, weighted_cos)) % 360
        
        # 風速の重み付き平均
        integrated_speed = np.average(speed_values, weights=weights)
    else:
        # 重みがゼロの場合は単純平均
        weighted_sin = np.mean(dir_sin_values)
        weighted_cos = np.mean(dir_cos_values)
        integrated_direction = math.degrees(math.atan2(weighted_sin, weighted_cos)) % 360
        
        integrated_speed = np.mean(speed_values)
    
    # 時間の中央値
    if timestamps:
        integrated_time = sorted(timestamps)[len(timestamps) // 2]
    else:
        integrated_time = datetime.now()
    
    # 信頼度の計算（艇数と重みの平均に基づく）
    avg_weight = np.mean([d['weight'] for d in boat_data])
    confidence = min(0.9, 0.4 + 0.1 * len(boat_data) + 0.4 * avg_weight)
    
    # 経度緯度の計算（重み付き平均）
    latitude, longitude = None, None
    valid_positions = [(d['latitude'], d['longitude'], d['weight']) 
                     for d in boat_data if d['latitude'] is not None and d['longitude'] is not None]
    
    if valid_positions:
        total_weight = sum(w for _, _, w in valid_positions)
        if total_weight > 0:
            latitude = sum(lat * w for lat, _, w in valid_positions) / total_weight
            longitude = sum(lon * w for _, lon, w in valid_positions) / total_weight
    
    # 標準偏差の計算
    dir_var = 0.0
    speed_var = 0.0
    
    for d, w in zip(boat_data, weights):
        # 風向の差（循環性を考慮）
        dir_diff = abs((d['wind_direction'] - integrated_direction + 180) % 360 - 180)
        dir_var += dir_diff**2 * w
        
        # 風速の差
        speed_diff = d['wind_speed_knots'] - integrated_speed
        speed_var += speed_diff**2 * w
    
    if sum(weights) > 0:
        dir_var /= sum(weights)
        speed_var /= sum(weights)
    
    dir_std = math.sqrt(dir_var)
    speed_std = math.sqrt(speed_var)
    
    return {
        'timestamp': integrated_time,
        'wind_direction': integrated_direction,
        'wind_speed': integrated_speed,
        'confidence': confidence,
        'direction_std': dir_std,
        'speed_std': speed_std,
        'latitude': latitude,
        'longitude': longitude,
        'boat_count': len(boat_data)
    }

def update_time_change_model(model):
    """
    風向風速の時間変化モデルを更新
    
    Parameters:
    -----------
    model : BoatDataFusionModel
        モデルインスタンス
    """
    if len(model.estimation_history) < 3:
        return
    
    # 直近の履歴のみを使用
    recent_history = model.estimation_history[-10:]
    
    # 隣接する時間点間の変化率を計算
    dir_changes = []
    speed_changes = []
    
    for i in range(1, len(recent_history)):
        prev = recent_history[i-1]
        curr = recent_history[i]
        
        # 時間差（分）
        time_diff_minutes = (curr['timestamp'] - prev['timestamp']).total_seconds() / 60
        if time_diff_minutes <= 0:
            continue
        
        # 風向の変化率（度/分）
        dir_diff = (curr['wind_direction'] - prev['wind_direction'] + 180) % 360 - 180
        dir_change_rate = dir_diff / time_diff_minutes
        
        # 風速の変化率（ノット/分）
        speed_diff = curr['wind_speed_knots'] - prev['wind_speed_knots']
        speed_change_rate = speed_diff / time_diff_minutes
        
        dir_changes.append(dir_change_rate)
        speed_changes.append(speed_change_rate)
    
    # 変化率の統計を更新
    if dir_changes:
        model.direction_time_change = np.median(dir_changes)
        model.direction_time_change_std = np.std(dir_changes)
    
    if speed_changes:
        model.speed_time_change = np.median(speed_changes)
        model.speed_time_change_std = np.std(speed_changes)

def create_spatiotemporal_wind_field(model, time_points: List[datetime], 
                                   grid_resolution: int = 20) -> Dict[datetime, Dict[str, Any]]:
    """
    時空間的な風の場を作成
    
    Parameters:
    -----------
    model : BoatDataFusionModel
        モデルインスタンス
    time_points : List[datetime]
        対象時間点のリスト
    grid_resolution : int
        空間グリッドの解像度
        
    Returns:
    --------
    Dict[datetime, Dict[str, Any]]
        時間点ごとの風の場データ
    """
    # 履歴が不十分な場合は空の辞書を返す
    if len(model.estimation_history) < 3:
        return {}
    
    wind_fields = {}
    
    # 各時間点での風の場を推定
    for time_point in time_points:
        wind_field = estimate_wind_field_at_time(model, time_point, grid_resolution)
        if wind_field is not None:
            wind_fields[time_point] = wind_field
    
    return wind_fields

def estimate_wind_field_at_time(model, time_point: datetime, 
                              grid_resolution: int = 20) -> Optional[Dict[str, Any]]:
    """
    特定時点での風の場を推定
    
    Parameters:
    -----------
    model : BoatDataFusionModel
        モデルインスタンス
    time_point : datetime
        対象時間点
    grid_resolution : int
        空間グリッドの解像度
        
    Returns:
    --------
    Dict[str, Any] or None
        風の場データ
    """
    # 時間的に近い履歴エントリを探す
    nearby_entries = []
    
    for entry in model.estimation_history:
        # 時間差（分）
        time_diff_minutes = abs((entry['timestamp'] - time_point).total_seconds() / 60)
        
        if time_diff_minutes <= 30:  # 30分以内のデータを使用
            # 時間差に基づく重み
            time_weight = max(0.1, 1.0 - time_diff_minutes / 30)
            
            nearby_entries.append({
                'timestamp': entry['timestamp'],
                'wind_direction': entry['wind_direction'],
                'wind_speed_knots': entry['wind_speed_knots'],
                'time_weight': time_weight
            })
    
    if not nearby_entries:
        return None
    
    # 標準的なグリッド境界
    lat_min, lat_max = 35.6, 35.7  # 仮の値
    lon_min, lon_max = 139.7, 139.8  # 仮の値
    
    # 位置情報がある場合は境界を調整
    location_entries = [entry for entry in model.estimation_history 
                      if 'latitude' in entry and entry['latitude'] is not None 
                      and 'longitude' in entry and entry['longitude'] is not None]
    
    if location_entries:
        lat_values = [entry['latitude'] for entry in location_entries]
        lon_values = [entry['longitude'] for entry in location_entries]
        
        lat_min, lat_max = min(lat_values), max(lat_values)
        lon_min, lon_max = min(lon_values), max(lon_values)
        
        # 少し余裕を持たせる
        lat_margin = (lat_max - lat_min) * 0.1
        lon_margin = (lon_max - lon_min) * 0.1
        lat_min -= lat_margin
        lat_max += lat_margin
        lon_min -= lon_margin
        lon_max += lon_margin
    
    # グリッドの作成
    lat_grid = np.linspace(lat_min, lat_max, grid_resolution)
    lon_grid = np.linspace(lon_min, lon_max, grid_resolution)
    grid_lats, grid_lons = np.meshgrid(lat_grid, lon_grid)
    
    # 時間に最も近い風向風速を基準とし、時間変化モデルで補正
    closest_entry = min(nearby_entries, key=lambda e: abs((e['timestamp'] - time_point).total_seconds()))
    time_diff_minutes = (time_point - closest_entry['timestamp']).total_seconds() / 60
    
    # 基準風向風速の算出
    base_direction = closest_entry['wind_direction']
    base_speed = closest_entry['wind_speed_knots']
    
    # 時間変化モデルによる補正
    projected_direction = (base_direction + model.direction_time_change * time_diff_minutes) % 360
    projected_speed = max(0, base_speed + model.speed_time_change * time_diff_minutes)
    
    # 時間変化の不確実性
    direction_uncertainty = min(1.0, abs(time_diff_minutes) * model.direction_time_change_std / 30)
    speed_uncertainty = min(1.0, abs(time_diff_minutes) * model.speed_time_change_std / (base_speed * 0.2 + 0.1))
    
    # 風向風速グリッドを初期化
    wind_directions = np.ones_like(grid_lats) * projected_direction
    wind_speeds = np.ones_like(grid_lats) * projected_speed
    confidence = np.ones_like(grid_lats) * max(0.1, 0.8 - 0.4 * direction_uncertainty - 0.4 * speed_uncertainty)
    
    # 空間的な変動（単純な実装）
    # TODO: 空間補間モデルの高度化
    
    # 位置情報がある場合は空間変動を計算
    position_entries = [e for e in nearby_entries if 'latitude' in e and e['latitude'] is not None 
                     and 'longitude' in e and e['longitude'] is not None]
    
    if position_entries and len(position_entries) >= 3:
        try:
            # ガウス過程回帰を使用した空間補間
            points = np.array([[e['latitude'], e['longitude']] for e in position_entries])
            
            # 風向のsin/cos成分
            dir_sin = np.array([math.sin(math.radians(e['wind_direction'])) for e in position_entries])
            dir_cos = np.array([math.cos(math.radians(e['wind_direction'])) for e in position_entries])
            speeds = np.array([e['wind_speed_knots'] for e in position_entries])
            
            # カーネルの定義
            kernel = ConstantKernel(1.0) * RBF(length_scale=0.01) + WhiteKernel(noise_level=0.1)
            
            try:
                # sin/cos成分のGP回帰
                gp_sin = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5)
                gp_cos = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5)
                gp_speed = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=5)
                
                gp_sin.fit(points, dir_sin)
                gp_cos.fit(points, dir_cos)
                gp_speed.fit(points, speeds)
                
                # グリッドポイント形状の変更
                X_pred = np.column_stack([grid_lats.ravel(), grid_lons.ravel()])
                
                # 各グリッドポイントでの予測
                sin_pred = gp_sin.predict(X_pred).reshape(grid_lats.shape)
                cos_pred = gp_cos.predict(X_pred).reshape(grid_lats.shape)
                speed_pred = gp_speed.predict(X_pred).reshape(grid_lats.shape)
                
                # 風向の復元
                wind_directions = np.degrees(np.arctan2(sin_pred, cos_pred)) % 360
                wind_speeds = np.maximum(0, speed_pred)
                
                # ガウス過程の不確実性を考慮した信頼度
                _, sin_std = gp_sin.predict(X_pred, return_std=True)
                _, cos_std = gp_cos.predict(X_pred, return_std=True)
                _, speed_std = gp_speed.predict(X_pred, return_std=True)
                
                sin_std = sin_std.reshape(grid_lats.shape)
                cos_std = cos_std.reshape(grid_lats.shape)
                speed_std = speed_std.reshape(grid_lats.shape)
                
                # 正規化された不確実性
                dir_uncertainty = np.minimum(1.0, np.sqrt(sin_std**2 + cos_std**2) / 0.5)
                speed_uncertainty = np.minimum(1.0, speed_std / (wind_speeds * 0.3 + 0.1))
                
                # 信頼度を更新
                confidence = np.maximum(0.1, 0.8 - 0.4 * dir_uncertainty - 0.4 * speed_uncertainty)
                
            except Exception as e:
                # ガウス過程回帰に失敗した場合はIDW（逆距離加重）を使用
                pass
        except Exception as e:
            # 外部の例外をキャッチ
            pass
    
    return {
        'lat_grid': grid_lats,
        'lon_grid': grid_lons,
        'wind_direction': wind_directions,
        'wind_speed': wind_speeds,
        'confidence': confidence,
        'time': time_point
    }
