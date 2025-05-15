#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WindFieldFusionSystem の機能検証テスト
"""

import sys
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytest

# 計測用デコレータ
def time_it(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 実行時間: {end_time - start_time:.4f}秒")
        return result
    return wrapper

class WindDataGenerator:
    """テスト用の風データ生成クラス"""
    
    @staticmethod
    def create_random_points(num_points=20, base_lat=35.45, base_lon=139.65, 
                            time_interval=5, spread=0.01):
        """ランダムな風データポイントを生成"""
        base_time = datetime.now()
        points = []
        
        for i in range(num_points):
            # ランダムな位置（正規分布）
            lat = base_lat + np.random.normal(0, spread)
            lon = base_lon + np.random.normal(0, spread)
            
            # ランダムな風向風速
            wind_dir = np.random.uniform(0, 360)
            wind_speed = np.random.uniform(5, 15)
            
            # 時間
            time = base_time + timedelta(seconds=i*time_interval)
            
            points.append({
                'timestamp': time,
                'latitude': lat,
                'longitude': lon,
                'wind_direction': wind_dir,
                'wind_speed': wind_speed
            })
        
        return points
    
    @staticmethod
    def create_pathological_points(num_points=10, base_lat=35.45, base_lon=139.65,
                                 time_interval=5):
        """Qhull precision error を誘発しやすいデータポイント"""
        base_time = datetime.now()
        points = []
        
        # ケース1: 完全に同じ位置の点
        for i in range(3):
            points.append({
                'timestamp': base_time + timedelta(seconds=i*time_interval),
                'latitude': base_lat,
                'longitude': base_lon,
                'wind_direction': 90,
                'wind_speed': 10
            })
        
        # ケース2: 極めて近い位置の点（Qhull精度エラーを誘発）
        for i in range(3):
            eps = 1e-10  # 極めて小さな差
            points.append({
                'timestamp': base_time + timedelta(seconds=(i+3)*time_interval),
                'latitude': base_lat + eps * i,
                'longitude': base_lon + eps * i,
                'wind_direction': 90,
                'wind_speed': 10
            })
        
        # ケース3: 直線上に並ぶ点（Qhull精度エラーを誘発）
        for i in range(4):
            points.append({
                'timestamp': base_time + timedelta(seconds=(i+6)*time_interval),
                'latitude': base_lat + i * 0.001,
                'longitude': base_lon,
                'wind_direction': 90,
                'wind_speed': 10
            })
        
        return points
    
    @staticmethod
    def create_boat_data(num_boats=3, points_per_boat=20, spread=0.1):
        """複数艇のテストデータを生成"""
        boats_data = {}
        base_time = datetime.now()
        
        for boat_idx in range(num_boats):
            boat_id = f"boat_{boat_idx}"
            data = []
            
            # 各艇に異なる基準位置を設定
            base_lat = 35.4 + boat_idx * spread
            base_lon = 139.7 + boat_idx * spread
            
            # 各艇に若干異なる風向・風速を設定
            wind_dir = 90 + boat_idx * 10
            wind_speed = 10 + boat_idx * 1.0
            
            # 各艇の航跡を生成
            for i in range(points_per_boat):
                angle = i * 0.31
                time = base_time + timedelta(seconds=i*10)
                
                # 8の字を描くような位置の変化
                lat_offset = 0.005 * np.sin(angle)
                lon_offset = 0.005 * np.sin(angle * 2)
                
                # 風向・風速にも変動を追加
                dir_oscillation = np.sin(angle) * 5
                speed_oscillation = np.cos(angle) * 1.0
                
                data.append({
                    'timestamp': time,
                    'latitude': base_lat + lat_offset,
                    'longitude': base_lon + lon_offset,
                    'wind_direction': (wind_dir + dir_oscillation) % 360,
                    'wind_speed_knots': max(0.5, wind_speed + speed_oscillation),
                    'confidence': 0.8
                })
            
            boats_data[boat_id] = pd.DataFrame(data)
        
        return boats_data

@pytest.mark.core
def test_qhull_precision_error():
    """Qhull precision errorの対策テスト"""
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    
    fusion_system = WindFieldFusionSystem()
    
    # 問題を引き起こしやすいデータ
    pathological_points = WindDataGenerator.create_pathological_points()
    
    # 各ポイントを追加
    for point in pathological_points:
        fusion_system.add_wind_data_point(point)
    
    # 風の場生成が成功したか確認
    assert fusion_system.current_wind_field is not None, "風の場生成に失敗しました"

def test_data_scaling():
    """データスケーリング機能のテスト"""
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    
    fusion_system = WindFieldFusionSystem()
    
    # テストケース1: 単一位置のデータポイント（極小範囲）
    single_point_data = [
        {'latitude': 35.45, 'longitude': 139.65, 'wind_speed': 10, 'wind_direction': 90},
        {'latitude': 35.45, 'longitude': 139.65, 'wind_speed': 12, 'wind_direction': 95}
    ]
    
    scaled_points = fusion_system._scale_data_points(single_point_data)
    
    assert len(scaled_points) == len(single_point_data), "スケーリング後のデータ数が一致しません"
    
    # スケーリング結果の検証
    has_scaled_values = all('scaled_latitude' in p and 'scaled_longitude' in p for p in scaled_points)
    assert has_scaled_values, "スケーリング結果にscaled_latitudeなどが含まれていません"
    
    # テストケース2: 広範囲のデータポイント
    wide_range_data = [
        {'latitude': 35.0, 'longitude': 139.0, 'wind_speed': 10, 'wind_direction': 90},
        {'latitude': 36.0, 'longitude': 140.0, 'wind_speed': 15, 'wind_direction': 180}
    ]
    
    scaled_points_wide = fusion_system._scale_data_points(wide_range_data)
    
    assert len(scaled_points_wide) == len(wide_range_data), "スケーリング後のデータ数が一致しません"
    
    # スケーリングの具体的な動作確認
    p0 = scaled_points_wide[0]
    p1 = scaled_points_wide[1]
    
    assert 0 <= p0['scaled_latitude'] <= 1 and 0 <= p1['scaled_latitude'] <= 1, \
           "位置データは0-1の範囲にスケーリングされています"

@time_it
def test_performance_large_dataset():
    """大規模データセットでのパフォーマンステスト"""
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    
    fusion_system = WindFieldFusionSystem()
    
    # 大量のボートデータを生成
    num_boats = 5
    points_per_boat = 50
    
    large_boat_data = WindDataGenerator.create_boat_data(
        num_boats=num_boats, 
        points_per_boat=points_per_boat,
        spread=0.2  # より広い範囲に分散
    )
    
    # 処理時間を計測
    start_time = time.time()
    result = fusion_system.update_with_boat_data(large_boat_data)
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    
    # 処理時間の目標： 5秒以内
    assert elapsed_time < 5.0, f"パフォーマンス目標未達: {elapsed_time:.4f}秒 > 5.0秒"
    
    # 結果の検証
    assert result, "風の場生成に失敗しました"
    
    wind_field = fusion_system.current_wind_field
    assert wind_field is not None, "風の場が生成されていません"
    assert 'wind_direction' in wind_field, "風向データが見つかりません"
    assert 'wind_speed' in wind_field, "風速データが見つかりません"

def test_create_random_points():
    """ランダムポイント生成のテスト"""
    points = WindDataGenerator.create_random_points()
    
    assert len(points) == 20, "生成されたポイント数が正しくありません"
    
    first_point = points[0]
    assert 'timestamp' in first_point, "タイムスタンプが見つかりません"
    assert 'latitude' in first_point, "緯度が見つかりません"
    assert 'longitude' in first_point, "経度が見つかりません"
    assert 'wind_direction' in first_point, "風向が見つかりません"
    assert 'wind_speed' in first_point, "風速が見つかりません"

def test_create_boat_data():
    """ボートデータ生成のテスト"""
    boat_data = WindDataGenerator.create_boat_data()
    
    assert len(boat_data) == 3, "生成されたボート数が正しくありません"
    
    for boat_id, data in boat_data.items():
        assert isinstance(data, pd.DataFrame), "データがDataFrameではありません"
        assert len(data) == 20, "ポイント数が正しくありません"
        assert 'timestamp' in data.columns, "タイムスタンプ列が見つかりません"
        assert 'latitude' in data.columns, "緯度列が見つかりません"
        assert 'longitude' in data.columns, "経度列が見つかりません"
        assert 'wind_direction' in data.columns, "風向列が見つかりません"
        assert 'wind_speed_knots' in data.columns, "風速列が見つかりません"
