#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風推定アルゴリズムのパフォーマンステスト

このスクリプトは風推定アルゴリズムのパフォーマンスを計測します。
"""

import os
import sys
import time
import gc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psutil
import json

# sailing_data_processor へのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sailing_data_processor.wind_estimator import WindEstimator

def get_memory_usage():
    """現在のメモリ使用量 (MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def generate_sample_data(num_points=5000, noise_level=0.2):
    """テスト用GPSデータ生成"""
    print(f"テストデータ生成中 ({num_points}ポイント)...")
    
    # 開始位置
    start_lat = 35.6230
    start_lon = 139.7724
    
    # データ保存用の配列
    timestamps = []
    latitudes = []
    longitudes = []
    speeds = []
    courses = []
    
    start_time = datetime.now()
    
    for i in range(num_points):
        # 時間進行
        current_time = start_time + timedelta(seconds=i)
        
        # 航跡
        angle = (i / num_points) * 2 * np.pi
        radius = 0.01  # 約1km程度
        
        # ノイズ付加
        noise_factor = noise_level * np.random.random()
        
        lat = start_lat + radius * np.sin(angle) + (noise_factor * 0.001 * np.random.randn())
        lon = start_lon + radius * np.cos(angle) + (noise_factor * 0.001 * np.random.randn())
        
        # 速度は風向により変動
        base_speed = 5.0 + 2.0 * np.sin(angle * 2)  # 3〜7ノット
        speed = base_speed + (noise_factor * 0.5 * np.random.randn())  # ノイズ
        
        # 進行方位 - 円周上の場合は接線方向（円の中心角から90度ずれる）
        base_course = (np.degrees(angle) + 90) % 360
        course = base_course + (noise_factor * 5 * np.random.randn())  # ノイズ
        course = course % 360  # 0-360の範囲に正規化
        
        timestamps.append(current_time)
        latitudes.append(lat)
        longitudes.append(lon)
        speeds.append(max(0.1, speed))  # 最小速度
        courses.append(course)
    
    # タック/ジャイブポイントを挿入（大きなデータセットに合わせて数を調整）
    tack_count = 20 + (num_points // 5000)  # データサイズに応じて増加
    tack_indices = np.linspace(0, num_points-1, tack_count, dtype=int)
    for idx in tack_indices:
        if idx > 0 and idx < num_points - 1:
            # コースを約90度変更
            course_change = 90 if np.random.random() > 0.5 else -90
            courses[idx] = (courses[idx-1] + course_change) % 360
            # タック中は速度低下
            speeds[idx] = speeds[idx] * 0.7
    
    # DataFrame化
    df = pd.DataFrame({
        'timestamp': timestamps,
        'latitude': latitudes,
        'longitude': longitudes,
        'speed': speeds,
        'course': courses,
        'boat_id': 'test_boat'
    })
    
    return df

def benchmark_wind_estimation(df, boat_type='default', iterations=3):
    """風向推定アルゴリズムのパフォーマンス計測"""
    print(f"\n--- 風向推定アルゴリズムのパフォーマンス計測 ({len(df)}ポイント) ---")
    
    # 結果保存
    results = {
        'size': len(df),
        'iterations': iterations,
        'times': [],
        'memory': []
    }
    
    for i in range(iterations):
        print(f"測定回数 {i+1}/{iterations}")
        
        # メモリ測定
        gc.collect()
        initial_memory = get_memory_usage()
        
        # WindEstimator初期化と処理
        start_time = time.time()
        estimator = WindEstimator(boat_type=boat_type)
        wind_data = estimator.estimate_wind_from_single_boat(
            gps_data=df,
            min_tack_angle=30.0,
            boat_type=boat_type,
            use_bayesian=True
        )
        end_time = time.time()
        
        # 時間計測
        elapsed = end_time - start_time
        results['times'].append(elapsed)
        print(f"  処理時間: {elapsed:.3f}秒")
        
        # メモリ計測
        current_memory = get_memory_usage()
        memory_increase = current_memory - initial_memory
        results['memory'].append(memory_increase)
        print(f"  メモリ使用量: {memory_increase:.2f}MB")
        
        # 結果要約
        if wind_data is not None:
            print(f"  結果: {len(wind_data)}行, 信頼度: {estimator.estimated_wind['confidence']:.2f}")
        
        # クリーンアップ
        del estimator
        del wind_data
        gc.collect()
    
    # 平均計算
    results['avg_time'] = sum(results['times']) / len(results['times'])
    results['min_time'] = min(results['times'])
    results['max_time'] = max(results['times'])
    results['avg_memory'] = sum(results['memory']) / len(results['memory'])
    
    print(f"平均処理時間: {results['avg_time']:.3f}秒")
    print(f"平均メモリ使用量: {results['avg_memory']:.2f}MB")
    
    return results

def save_benchmark_results(results, output_file):
    """ベンチマーク結果をJSONファイルに保存"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nベンチマーク結果を保存しました: {output_file}")

def main():
    """メイン処理"""
    print("==================================================")
    print("   風推定アルゴリズム - パフォーマンス計測   ")
    print("==================================================")
    print(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # データポイント数と繰り返し回数
    data_points = 200000  # さらに大きなテストデータ
    iterations = 3
    
    print(f"データポイント数: {data_points}")
    print(f"繰り返し回数: {iterations}")
    
    # 結果保存用
    final_results = {
        'timestamp': datetime.now().isoformat(),
        'data_points': data_points,
        'iterations': iterations
    }
    
    # テストデータ生成
    sample_data = generate_sample_data(num_points=data_points)
    
    # 風向推定のベンチマーク
    wind_results = benchmark_wind_estimation(sample_data, iterations=iterations)
    final_results['wind_estimation'] = wind_results
    
    # 結果保存
    output_file = 'benchmark_results/wind_estimation_performance.json'
    save_benchmark_results(final_results, output_file)
    
    print("\n==================================================")
    print("   測定完了")
    print("==================================================")

if __name__ == "__main__":
    main()
