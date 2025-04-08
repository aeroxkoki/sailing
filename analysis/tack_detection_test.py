#!/usr/bin/env python3
"""
タック検出テストスクリプト
WindEstimatorクラスのタック/ジャイブ検出機能を検証する
"""

import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import math
import warnings

# モジュールの参照パスを設定
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# テスト対象のモジュールをインポート
from sailing_data_processor.wind_estimator import WindEstimator

def create_test_data(pattern_type='tack'):
    """
    テスト用GPSデータを作成
    
    Parameters:
    -----------
    pattern_type : str
        'tack': タックパターン
        'jibe': ジャイブパターン
        'mixed': 混合パターン
    
    Returns:
    --------
    pd.DataFrame
        テスト用GPSデータ
    """
    # 基本情報
    base_lat, base_lon = 35.6, 139.7
    points = 200
    timestamps = [datetime(2024, 3, 1, 10, 0, 0) + timedelta(seconds=i*5) for i in range(points)]
    
    # パターンタイプに基づいて方位と速度を生成
    if pattern_type == 'tack':
        # タックパターン（45度と315度を交互に）
        bearings = []
        for i in range(points):
            if i < 50:
                bearings.append(45)
            elif i < 60:
                # タック操作（45度から315度への急な変化）
                progress = (i - 50) / 10
                bearings.append(45 + progress * 270)
            elif i < 110:
                bearings.append(315)
            elif i < 120:
                # タック操作（315度から45度への急な変化）
                progress = (i - 110) / 10
                bearings.append(315 - progress * 270)
            elif i < 170:
                bearings.append(45)
            else:
                bearings.append(315)
        
        # 風上は遅め（4-5ノット）で、タック時にさらに遅くなる
        speeds = []
        for i in range(points):
            if 50 <= i < 60 or 110 <= i < 120:
                # タック中は遅くなる
                speeds.append(3.0 + np.random.random() * 0.5)
            else:
                speeds.append(4.5 + np.random.random())
                
    elif pattern_type == 'jibe':
        # ジャイブパターン（135度と225度を交互に）
        bearings = []
        for i in range(points):
            if i < 50:
                bearings.append(135)
            elif i < 60:
                # ジャイブ操作（135度から225度への急な変化）
                progress = (i - 50) / 10
                bearings.append(135 + progress * 90)
            elif i < 110:
                bearings.append(225)
            elif i < 120:
                # ジャイブ操作（225度から135度への急な変化）
                progress = (i - 110) / 10
                bearings.append(225 - progress * 90)
            elif i < 170:
                bearings.append(135)
            else:
                bearings.append(225)
        
        # 風下は速め（6-7ノット）で、ジャイブ時にさらに遅くなる
        speeds = []
        for i in range(points):
            if 50 <= i < 60 or 110 <= i < 120:
                # ジャイブ中は遅くなる
                speeds.append(5.0 + np.random.random() * 0.5)
            else:
                speeds.append(6.5 + np.random.random())
                
    else:  # mixed
        # 風上（タック）と風下（ジャイブ）の混合パターン
        bearings = []
        
        # 最初の風上レグ
        for i in range(60):
            if i < 25:
                bearings.append(45)
            elif i < 35:
                # タック
                progress = (i - 25) / 10
                bearings.append(45 + progress * 270)
            else:
                bearings.append(315)
        
        # 風下への転換
        for i in range(10):
            progress = i / 10
            bearings.append(315 - progress * 180)
        
        # 風下レグ
        for i in range(60):
            if i < 25:
                bearings.append(135)
            elif i < 35:
                # ジャイブ
                progress = (i - 25) / 10
                bearings.append(135 + progress * 90)
            else:
                bearings.append(225)
        
        # 風上への転換
        for i in range(10):
            progress = i / 10
            bearings.append(225 - progress * 180)
        
        # 最後の風上レグ
        for i in range(60):
            if i < 30:
                bearings.append(45)
            else:
                bearings.append(315)
        
        # 速度パターン（風上は遅く、風下は速く）
        speeds = []
        for i in range(points):
            if i < 60:  # 最初の風上レグ
                base_speed = 4.5
            elif i < 70:  # 風下への転換
                base_speed = 5.0
            elif i < 130:  # 風下レグ
                base_speed = 6.5
            elif i < 140:  # 風上への転換
                base_speed = 5.0
            else:  # 最後の風上レグ
                base_speed = 4.5
            
            # タック/ジャイブ操作中は遅くなる
            if (25 <= i < 35) or (95 <= i < 105):
                speeds.append(base_speed - 1.5 + np.random.random() * 0.5)
            else:
                speeds.append(base_speed + np.random.random())
    
    # パターンを少し短くする必要がある場合
    if len(bearings) > points:
        bearings = bearings[:points]
    if len(speeds) > points:
        speeds = speeds[:points]
    
    # 座標を計算
    lats = [base_lat]
    lons = [base_lon]
    
    for i in range(1, points):
        # 前の位置から新しい位置を計算
        dist = speeds[i-1] * 5 * 0.514444  # 5秒分の距離（ノット→m/s）
        dx = dist * math.sin(math.radians(bearings[i-1]))
        dy = dist * math.cos(math.radians(bearings[i-1]))
        
        # メートルを度に変換（近似）
        dlat = dy / 111000  # 1度 ≈ 111km
        dlon = dx / (111000 * math.cos(math.radians(lats[-1])))
        
        lats.append(lats[-1] + dlat)
        lons.append(lons[-1] + dlon)
    
    # DataFrameに変換
    return pd.DataFrame({
        'timestamp': timestamps,
        'latitude': lats,
        'longitude': lons,
        'bearing': bearings,
        'speed': np.array(speeds) * 0.514444,  # ノット→m/s変換
        'boat_id': ['test_boat'] * points
    })

def plot_detection_results(df, tack_points=None, jibe_points=None):
    """
    検出結果を可視化
    
    Parameters:
    -----------
    df : pd.DataFrame
        GPSデータ
    tack_points : pd.DataFrame, optional
        検出されたタックポイント
    jibe_points : pd.DataFrame, optional
        検出されたジャイブポイント
    """
    plt.figure(figsize=(12, 8))
    
    # 1. 航跡図
    plt.subplot(2, 2, 1)
    plt.plot(df['longitude'], df['latitude'], 'b-', label='Boat Track')
    
    # タック/ジャイブポイントをプロット
    if tack_points is not None and not tack_points.empty:
        plt.plot(tack_points['longitude'], tack_points['latitude'], 'ro', label='Tacks')
    if jibe_points is not None and not jibe_points.empty:
        plt.plot(jibe_points['longitude'], jibe_points['latitude'], 'go', label='Jibes')
    
    plt.grid(True)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Sailing Track with Maneuvers')
    plt.legend()
    
    # 2. 時系列の方位
    plt.subplot(2, 2, 2)
    time_indices = np.arange(len(df))
    plt.plot(time_indices, df['bearing'], 'b-', label='Bearing')
    
    # タック/ジャイブタイミングを示す縦線
    if tack_points is not None and not tack_points.empty:
        for idx in tack_points.index:
            plt.axvline(x=idx, color='r', linestyle='--', alpha=0.5)
    if jibe_points is not None and not jibe_points.empty:
        for idx in jibe_points.index:
            plt.axvline(x=idx, color='g', linestyle='--', alpha=0.5)
    
    plt.grid(True)
    plt.xlabel('Time (steps)')
    plt.ylabel('Bearing (deg)')
    plt.title('Bearing over Time')
    
    # 3. 時系列の速度
    plt.subplot(2, 2, 3)
    # m/s → ノット変換
    speeds_knots = df['speed'] / 0.514444
    plt.plot(time_indices, speeds_knots, 'g-', label='Speed')
    
    # タック/ジャイブタイミングを示す縦線
    if tack_points is not None and not tack_points.empty:
        for idx in tack_points.index:
            plt.axvline(x=idx, color='r', linestyle='--', alpha=0.5)
    if jibe_points is not None and not jibe_points.empty:
        for idx in jibe_points.index:
            plt.axvline(x=idx, color='g', linestyle='--', alpha=0.5)
    
    plt.grid(True)
    plt.xlabel('Time (steps)')
    plt.ylabel('Speed (knots)')
    plt.title('Speed over Time')
    
    # 4. 方位変化の大きさ
    plt.subplot(2, 2, 4)
    if 'bearing_change' in df.columns:
        plt.plot(time_indices[1:], df['bearing_change'].iloc[1:], 'k-', label='Bearing Change')
        
        # 検出閾値を示す水平線
        plt.axhline(y=30, color='r', linestyle='--', alpha=0.5, label='Detection Threshold')
        
        plt.grid(True)
        plt.xlabel('Time (steps)')
        plt.ylabel('Bearing Change (deg)')
        plt.title('Bearing Change over Time')
        plt.legend()
    else:
        plt.text(0.5, 0.5, 'Bearing change data not available', 
                 horizontalalignment='center', verticalalignment='center')
    
    plt.tight_layout()
    plt.show()

def run_tack_detection_test():
    """WindEstimatorのタック検出機能をテスト"""
    # タック検出器の初期化
    estimator = WindEstimator()
    
    # テストケース
    test_cases = [
        ('tack', 'Simple Tack Pattern'),
        ('jibe', 'Simple Jibe Pattern'),
        ('mixed', 'Mixed Tack/Jibe Pattern')
    ]
    
    for pattern, description in test_cases:
        print(f"=== Testing: {description} ===")
        
        # テストデータを生成
        test_data = create_test_data(pattern)
        
        # 方位変化を計算
        test_data = estimator._calculate_bearing_change(test_data)
        
        # 風向を推定（簡易方法）
        if pattern == 'tack':
            estimated_wind = 0  # 北風（タックは45度と315度で風上走行）
        elif pattern == 'jibe':
            estimated_wind = 180  # 南風（ジャイブは135度と225度で風下走行）
        else:
            estimated_wind = 0  # 混合パターンでも北風と仮定
        
        # マニューバ（方向転換）を検出
        maneuvers = estimator.detect_maneuvers(
            df=test_data,
            wind_direction=estimated_wind,
            min_angle_change=25.0
        )
        
        # 検出結果を分類
        tack_points = pd.DataFrame()
        jibe_points = pd.DataFrame()
        
        if not maneuvers.empty and 'maneuver_type' in maneuvers.columns:
            # タックとジャイブを分離
            tack_points = maneuvers[maneuvers['maneuver_type'] == 'tack']
            jibe_points = maneuvers[maneuvers['maneuver_type'] == 'jibe']
            
            print(f"検出されたタック: {len(tack_points)}")
            print(f"検出されたジャイブ: {len(jibe_points)}")
            
            # 他のマニューバも表示
            bear_away = maneuvers[maneuvers['maneuver_type'] == 'bear_away']
            head_up = maneuvers[maneuvers['maneuver_type'] == 'head_up']
            
            if not bear_away.empty:
                print(f"検出されたベアアウェイ: {len(bear_away)}")
            if not head_up.empty:
                print(f"検出されたヘッドアップ: {len(head_up)}")
        else:
            print("マニューバが検出されませんでした")
        
        # 結果の可視化
        plot_detection_results(test_data, tack_points, jibe_points)

if __name__ == "__main__":
    warnings.filterwarnings("ignore")  # 警告を非表示
    run_tack_detection_test()
