#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
風推定アルゴリズムのパフォーマンスベンチマークスクリプト

このスクリプトは風向風速推定アルゴリズムのパフォーマンスを
測定し、最適化前後の比較を行います。
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
import matplotlib.pyplot as plt

# sailing_data_processor モジュールへのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sailing_data_processor.wind_estimator import WindEstimator
from sailing_data_processor.core import SailingDataProcessor

def get_memory_usage():
    """現在のメモリ使用量を取得 (MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def generate_sample_data(num_points=10000, noise_level=0.2):
    """テスト用のサンプルGPSデータを生成"""
    print(f"サンプルデータを生成中 ({num_points}ポイント)...")
    
    # 開始位置（東京湾）
    start_lat = 35.6230
    start_lon = 139.7724
    
    # 基本的なデータを生成（円を描く）
    timestamps = []
    latitudes = []
    longitudes = []
    speeds = []
    courses = []
    
    start_time = datetime.now()
    
    for i in range(num_points):
        # 時間経過（1秒間隔）
        current_time = start_time + timedelta(seconds=i)
        
        # 座標（円を描く）
        angle = (i / num_points) * 2 * np.pi
        radius = 0.01  # 約1km程度の円
        
        # ノイズを加える
        noise_factor = noise_level * np.random.random()
        
        lat = start_lat + radius * np.sin(angle) + (noise_factor * 0.001 * np.random.randn())
        lon = start_lon + radius * np.cos(angle) + (noise_factor * 0.001 * np.random.randn())
        
        # 速度（ノット）（3～7ノット）
        base_speed = 5.0 + 2.0 * np.sin(angle * 2)
        speed = base_speed + (noise_factor * 0.5 * np.random.randn())
        
        # コース（進行方向）- 円周上の接線方向（90度ずらす）
        base_course = (np.degrees(angle) + 90) % 360
        course = base_course + (noise_factor * 5 * np.random.randn())
        course = course % 360  # 0-360の範囲に正規化
        
        timestamps.append(current_time)
        latitudes.append(lat)
        longitudes.append(lon)
        speeds.append(max(0.1, speed))  # 負の速度を防止
        courses.append(course)
    
    # タックポイントをいくつか追加（20箇所）
    tack_indices = np.linspace(0, num_points-1, 20, dtype=int)
    for idx in tack_indices:
        if idx > 0 and idx < num_points - 1:
            # コースを急激に変える（約90度）
            course_change = 90 if np.random.random() > 0.5 else -90
            courses[idx] = (courses[idx-1] + course_change) % 360
            # タック中は速度が落ちる
            speeds[idx] = speeds[idx] * 0.7
    
    # DataFrameに変換
    df = pd.DataFrame({
        'timestamp': timestamps,
        'latitude': latitudes,
        'longitude': longitudes,
        'speed': speeds,
        'course': courses,
        'boat_id': 'test_boat'
    })
    
    return df

def benchmark_wind_estimation(df, boat_types=None, iterations=3):
    """風向風速推定アルゴリズムのベンチマーク"""
    if boat_types is None:
        boat_types = ['default', 'laser', '49er', '470']
    
    print(f"\n--- 風向風速推定アルゴリズムのベンチマーク ({len(df)}ポイント) ---")
    
    # 結果を格納する辞書
    results = {
        'size': len(df),
        'iterations': iterations,
        'by_boat_type': {}
    }
    
    total_times = []
    total_memory = []
    
    for boat_type in boat_types:
        print(f"\n## 艇種: {boat_type}")
        
        type_times = []
        type_memory = []
        
        for i in range(iterations):
            print(f"イテレーション {i+1}/{iterations}")
            
            # メモリ使用量を測定
            gc.collect()
            initial_memory = get_memory_usage()
            
            # WindEstimatorを使用して風推定
            start_time = time.time()
            estimator = WindEstimator(boat_type=boat_type)
            wind_data = estimator.estimate_wind_from_single_boat(
                gps_data=df,
                min_tack_angle=30.0,
                boat_type=boat_type,
                use_bayesian=True
            )
            end_time = time.time()
            
            # 所要時間を記録
            elapsed = end_time - start_time
            type_times.append(elapsed)
            print(f"  所要時間: {elapsed:.3f}秒")
            
            # メモリ使用量を記録
            current_memory = get_memory_usage()
            memory_increase = current_memory - initial_memory
            type_memory.append(memory_increase)
            print(f"  メモリ使用: {memory_increase:.2f}MB")
            
            # 結果のサマリー
            if wind_data is not None:
                print(f"  結果行数: {len(wind_data)}行, 信頼度: {estimator.estimated_wind['confidence']:.2f}")
            
            # 後処理
            del estimator
            del wind_data
            gc.collect()
        
        # 艇種ごとの結果集計
        results['by_boat_type'][boat_type] = {
            'avg_time': sum(type_times) / len(type_times),
            'min_time': min(type_times),
            'max_time': max(type_times),
            'avg_memory': sum(type_memory) / len(type_memory)
        }
        
        # 全体集計用のリストに追加
        total_times.extend(type_times)
        total_memory.extend(type_memory)
        
        print(f"平均所要時間 ({boat_type}): {results['by_boat_type'][boat_type]['avg_time']:.3f}秒")
    
    # 全体の平均値を計算
    results['overall'] = {
        'avg_time': sum(total_times) / len(total_times),
        'avg_memory': sum(total_memory) / len(total_memory)
    }
    
    print(f"\n全体平均所要時間: {results['overall']['avg_time']:.3f}秒")
    print(f"全体平均メモリ使用: {results['overall']['avg_memory']:.2f}MB")
    
    return results

def benchmark_with_different_sizes(size_multipliers=(0.2, 0.5, 1.0, 2.0), base_size=5000):
    """異なるデータサイズでのベンチマーク"""
    print("\n--- 異なるデータサイズでのベンチマーク ---")
    
    results = []
    
    for multiplier in size_multipliers:
        size = int(base_size * multiplier)
        print(f"\n=== データサイズ: {size} ポイント ===")
        
        # サンプルデータを生成
        sample_data = generate_sample_data(num_points=size)
        
        # ベンチマーク実行
        result = benchmark_wind_estimation(sample_data, boat_types=['default'], iterations=2)
        
        # 結果を保存
        results.append({
            'size': size,
            'time': result['by_boat_type']['default']['avg_time'],
            'memory': result['by_boat_type']['default']['avg_memory']
        })
        
        # クリーンアップ
        del sample_data
        gc.collect()
    
    return results

def plot_benchmark_results(size_results, output_file=None):
    """異なるサイズでのベンチマーク結果をグラフ化"""
    plt.figure(figsize=(12, 5))
    
    # データポイント数と処理時間の関係
    plt.subplot(1, 2, 1)
    sizes = [r['size'] for r in size_results]
    times = [r['time'] for r in size_results]
    
    plt.plot(sizes, times, 'o-', color='blue')
    plt.xlabel('データポイント数')
    plt.ylabel('処理時間 (秒)')
    plt.title('風向推定時間とデータサイズの関係')
    plt.grid(True)
    
    # データポイント数とメモリ使用量の関係
    plt.subplot(1, 2, 2)
    memory = [r['memory'] for r in size_results]
    
    plt.plot(sizes, memory, 'o-', color='green')
    plt.xlabel('データポイント数')
    plt.ylabel('メモリ使用量 (MB)')
    plt.title('メモリ使用量とデータサイズの関係')
    plt.grid(True)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
        print(f"ベンチマークグラフを保存しました: {output_file}")
    
    plt.close()

def save_benchmark_results(results, output_file):
    """ベンチマーク結果をJSONファイルに保存"""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nベンチマーク結果を保存しました: {output_file}")

def main():
    """メイン関数"""
    output_file = 'benchmark_results/my_wind_estimation_benchmark.json'
    points = 5000
    iterations = 2
    size_test = True
    
    print("==================================================")
    print("   風向風速推定 - パフォーマンスベンチマーク   ")
    print("==================================================")
    print(f"実行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"基本データポイント数: {points}")
    print(f"繰り返し回数: {iterations}")
    
    # 出力ディレクトリの確保
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 結果を格納する辞書
    final_results = {
        'timestamp': datetime.now().isoformat(),
        'data_points': points,
        'iterations': iterations
    }
    
    # サンプルデータを生成
    sample_data = generate_sample_data(num_points=points)
    
    # 風向推定のベンチマーク
    wind_results = benchmark_wind_estimation(sample_data, iterations=iterations)
    final_results['wind_estimation'] = wind_results
    
    # サイズ別ベンチマーク
    if size_test:
        print("\n--- サイズ別ベンチマーク実行 ---")
        size_results = benchmark_with_different_sizes(base_size=points)
        final_results['size_benchmark'] = size_results
        
        # グラフの生成
        graph_file = os.path.splitext(output_file)[0] + '.png'
        plot_benchmark_results(size_results, graph_file)
    
    # 結果の保存
    save_benchmark_results(final_results, output_file)
    
    print("\n--- ベンチマーク結果サマリー ---")
    print(f"風向推定 ({points}ポイント):")
    print(f"  平均所要時間: {wind_results['overall']['avg_time']:.3f}秒")
    print(f"  平均メモリ使用: {wind_results['overall']['avg_memory']:.2f}MB")
    
    print("\n==================================================")
    print("   ベンチマーク完了")
    print("==================================================")

if __name__ == "__main__":
    main()
