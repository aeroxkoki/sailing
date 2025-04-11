#!/usr/bin/env python3
"""
パフォーマンス改善のベンチマークスクリプト

このスクリプトはSailing Strategy Analyzerの主要コンポーネントの
パフォーマンスをベンチマークし、改善前後の比較を行います。
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
import argparse

# sailing_data_processor モジュールへのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sailing_data_processor.core import SailingDataProcessor
from sailing_data_processor.wind_estimator import WindEstimator

def get_memory_usage():
    """現在のメモリ使用量を取得 (MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def generate_sample_data(num_points=10000):
    """テスト用のサンプルGPSデータを生成"""
    print(f"サンプルデータを生成中 ({num_points}ポイント)...")
    
    # 開始位置（東京湾）
    start_lat = 35.6230
    start_lon = 139.7724
    
    # 基本的な経路を生成（半径の大きな円を描く）
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
        lat = start_lat + radius * np.sin(angle)
        lon = start_lon + radius * np.cos(angle)
        
        # 風上風下の模擬
        speed = 5.0 + 2.0 * np.sin(angle * 2)  # 速度変動（3〜7ノット）
        
        # コース（進行方向）
        # 円周上を移動する場合の接線方向（90度ずらす）
        course = (np.degrees(angle) + 90) % 360
        
        timestamps.append(current_time)
        latitudes.append(lat)
        longitudes.append(lon)
        speeds.append(speed)
        courses.append(course)
    
    # タック/ジャイブポイントを追加（20箇所）
    tack_indices = np.linspace(0, num_points-1, 20, dtype=int)
    for idx in tack_indices:
        if idx > 0 and idx < num_points - 1:
            # コースを急激に変える（約90度）
            course_change = 90 if np.random.random() > 0.5 else -90
            courses[idx] = (courses[idx-1] + course_change) % 360
            # タック中は速度が落ちる傾向
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

def benchmark_core_data_processing(samples, iterations=3):
    """SailingDataProcessorのデータ処理パフォーマンスをベンチマーク"""
    results = {
        'load_time': [],
        'process_time': [],
        'wind_estimate_time': [],
        'memory_usage': []
    }
    
    for i in range(iterations):
        print(f"\nイテレーション {i+1}/{iterations}")
        
        # 新しいプロセッサインスタンスを作成
        processor = SailingDataProcessor()
        
        # データの読み込み
        start_time = time.time()
        file_content = samples.to_csv().encode('utf-8')
        processor.load_multiple_files([
            ('test_boat.csv', file_content, 'csv')
        ])
        load_time = time.time() - start_time
        results['load_time'].append(load_time)
        print(f"データロード時間: {load_time:.3f}秒")
        
        # GPSデータの処理
        start_time = time.time()
        processor.detect_and_fix_gps_anomalies('test_boat')
        process_time = time.time() - start_time
        results['process_time'].append(process_time)
        print(f"データ処理時間: {process_time:.3f}秒")
        
        # 風推定
        start_time = time.time()
        processor.estimate_wind_from_boat('test_boat')
        wind_time = time.time() - start_time
        results['wind_estimate_time'].append(wind_time)
        print(f"風推定時間: {wind_time:.3f}秒")
        
        # メモリ使用量
        memory = get_memory_usage()
        results['memory_usage'].append(memory)
        print(f"メモリ使用量: {memory:.2f}MB")
        
        # クリーンアップ
        del processor
        gc.collect()
    
    # 平均値を計算
    avg_results = {
        'load_time': sum(results['load_time']) / len(results['load_time']),
        'process_time': sum(results['process_time']) / len(results['process_time']),
        'wind_estimate_time': sum(results['wind_estimate_time']) / len(results['wind_estimate_time']),
        'memory_usage': sum(results['memory_usage']) / len(results['memory_usage']),
    }
    
    return avg_results

def benchmark_wind_estimator(samples, iterations=3):
    """WindEstimatorの計算パフォーマンスをベンチマーク"""
    results = {
        'estimate_time': [],
        'memory_usage': []
    }
    
    for i in range(iterations):
        print(f"\nイテレーション {i+1}/{iterations}")
        
        # 新しいインスタンスを作成
        estimator = WindEstimator()
        
        # 風推定
        start_time = time.time()
        estimator.estimate_wind_from_single_boat(
            gps_data=samples,
            min_tack_angle=30.0,
            boat_type='default',
            use_bayesian=True
        )
        estimate_time = time.time() - start_time
        results['estimate_time'].append(estimate_time)
        print(f"風推定時間: {estimate_time:.3f}秒")
        
        # メモリ使用量
        memory = get_memory_usage()
        results['memory_usage'].append(memory)
        print(f"メモリ使用量: {memory:.2f}MB")
        
        # クリーンアップ
        del estimator
        gc.collect()
    
    # 平均値を計算
    avg_results = {
        'estimate_time': sum(results['estimate_time']) / len(results['estimate_time']),
        'memory_usage': sum(results['memory_usage']) / len(results['memory_usage']),
    }
    
    return avg_results

def save_benchmark_results(results, output_file):
    """ベンチマーク結果をJSONファイルに保存"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nベンチマーク結果を保存しました: {output_file}")

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='パフォーマンス改善ベンチマークツール')
    parser.add_argument('--output', default='benchmark_results/latest_results.json',
                        help='結果の出力先JSONファイル')
    parser.add_argument('--points', type=int, default=5000, help='テストデータポイント数')
    parser.add_argument('--iterations', type=int, default=3, help='繰り返し回数')
    
    args = parser.parse_args()
    
    print("===================================================")
    print("   セーリング戦略分析システム - パフォーマンスベンチマーク   ")
    print("===================================================")
    print(f"実行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"データポイント数: {args.points}")
    print(f"繰り返し回数: {args.iterations}")
    
    # 出力ディレクトリの確保
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # テストデータの生成
    sample_data = generate_sample_data(args.points)
    
    # ベンチマーク実行
    print("\n--- コアデータ処理のベンチマーク ---")
    core_results = benchmark_core_data_processing(sample_data, args.iterations)
    
    print("\n--- 風推定のベンチマーク ---")
    wind_results = benchmark_wind_estimator(sample_data, args.iterations)
    
    # 結果のまとめ
    results = {
        'timestamp': datetime.now().isoformat(),
        'data_points': args.points,
        'iterations': args.iterations,
        'core_processing': core_results,
        'wind_estimation': wind_results
    }
    
    # 結果の保存
    save_benchmark_results(results, args.output)
    
    print("\n--- ベンチマーク結果サマリー ---")
    print(f"コアデータ処理:")
    print(f"  データロード時間: {core_results['load_time']:.3f}秒")
    print(f"  データ処理時間: {core_results['process_time']:.3f}秒")
    print(f"  風推定時間: {core_results['wind_estimate_time']:.3f}秒")
    print(f"  メモリ使用量: {core_results['memory_usage']:.2f}MB")
    
    print(f"\n風推定:")
    print(f"  推定時間: {wind_results['estimate_time']:.3f}秒")
    print(f"  メモリ使用量: {wind_results['memory_usage']:.2f}MB")
    
    print("\n===================================================")
    print("   ベンチマーク完了")
    print("===================================================")

if __name__ == "__main__":
    main()
