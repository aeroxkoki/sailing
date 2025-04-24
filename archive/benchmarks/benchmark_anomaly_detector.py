# -*- coding: utf-8 -*-
"""
AnomalyDetector パフォーマンス検証用ベンチマーク

このスクリプトは異常値検出のパフォーマンスをテストし、
オリジナルのアルゴリズムと最適化されたアルゴリズムの
実行時間と使用メモリを比較します。
"""

import time
import os
import psutil  # メモリ使用量を測定するために必要
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from memory_profiler import profile  # メモリプロファイリング用

# sailing_data_processorモジュールをインポート
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from sailing_data_processor.utilities.gps_anomaly_detector import AnomalyDetector

def generate_test_data(num_points=1000, abnormal_ratio=0.05):
    """
    テスト用のGPSデータを生成する関数
    
    Parameters:
    -----------
    num_points : int
        生成するデータポイントの数
    abnormal_ratio : float
        異常値の割合（0.0〜1.0）
        
    Returns:
    --------
    pd.DataFrame
        生成されたGPSデータのDataFrame
    """
    # 基準点（東京）
    base_lat, base_lon = 35.6812, 139.7671
    
    # 通常の動きを生成
    lats = np.random.normal(base_lat, 0.01, num_points)
    lons = np.random.normal(base_lon, 0.01, num_points)
    
    # 時間の生成（1秒間隔）
    start_time = datetime.now() - timedelta(seconds=num_points)
    times = [start_time + timedelta(seconds=i) for i in range(num_points)]
    
    # データフレーム作成
    df = pd.DataFrame({
        'latitude': lats,
        'longitude': lons,
        'timestamp': times
    })
    
    # 異常値の追加（指定された割合）
    abnormal_count = int(num_points * abnormal_ratio)
    abnormal_indices = np.random.choice(num_points, abnormal_count, replace=False)
    
    # 異常値を設定（通常の5倍程度のジャンプを持つポイント）
    for idx in abnormal_indices:
        jump_size = np.random.uniform(0.05, 0.1)  # 0.05〜0.1度の大きなジャンプ
        df.loc[idx, 'latitude'] += np.random.choice([-1, 1]) * jump_size
        df.loc[idx, 'longitude'] += np.random.choice([-1, 1]) * jump_size
    
    return df

def measure_memory_usage():
    """
    現在のプロセスのメモリ使用量を返す関数
    
    Returns:
    --------
    float
        メモリ使用量（MB単位）
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB単位に変換

def run_benchmark(data_sizes=[100, 1000, 10000, 100000]):
    """
    様々なデータサイズでのベンチマークを実行する関数
    
    Parameters:
    -----------
    data_sizes : list
        テストするデータポイント数のリスト
        
    Returns:
    --------
    dict
        各データサイズごとの実行時間と使用メモリのデータ
    """
    results = {
        'size': [],
        'original_time': [],
        'optimized_time': [],
        'original_memory': [],
        'optimized_memory': []
    }
    
    detector = AnomalyDetector()
    
    for size in data_sizes:
        print(f"\n測定データサイズ: {size}ポイント")
        
        # テストデータ生成
        df = generate_test_data(size)
        
        # オリジナルアルゴリズムの計測
        # 測定前にメモリ使用量を記録
        gc_before_original = measure_memory_usage()
        
        start_time = time.time()
        _, _ = detector._detect_by_speed_original(
            df['latitude'],
            df['longitude'],
            df['timestamp']
        )
        original_time = time.time() - start_time
        
        # 測定後のメモリ使用量から差分を計算
        gc_after_original = measure_memory_usage()
        original_memory = gc_after_original - gc_before_original
        
        print(f"オリジナル実行時間: {original_time:.6f}秒")
        print(f"オリジナルメモリ使用: {original_memory:.2f}MB")
        
        # 最適化アルゴリズムの計測
        gc_before_optimized = measure_memory_usage()
        
        start_time = time.time()
        _, _ = detector._detect_by_speed_optimized(
            df['latitude'],
            df['longitude'],
            df['timestamp']
        )
        optimized_time = time.time() - start_time
        
        gc_after_optimized = measure_memory_usage()
        optimized_memory = gc_after_optimized - gc_before_optimized
        
        print(f"最適化版実行時間: {optimized_time:.6f}秒")
        print(f"最適化版メモリ使用: {optimized_memory:.2f}MB")
        
        speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
        memory_reduction = original_memory / optimized_memory if optimized_memory > 0 else float('inf')
        
        print(f"速度向上率: {speedup:.2f}倍")
        print(f"メモリ削減率: {memory_reduction:.2f}倍")
        
        # 結果を記録
        results['size'].append(size)
        results['original_time'].append(original_time)
        results['optimized_time'].append(optimized_time)
        results['original_memory'].append(original_memory)
        results['optimized_memory'].append(optimized_memory)
    
    return results

def plot_results(results):
    """
    ベンチマーク結果をグラフとして表示する関数
    
    Parameters:
    -----------
    results : dict
        ベンチマーク結果のデータ
    """
    # グラフ表示用の設定
    plt.figure(figsize=(15, 10))
    
    # 実行時間グラフ（対数スケール）
    plt.subplot(2, 2, 1)
    plt.plot(results['size'], results['original_time'], 'o-', label='オリジナル')
    plt.plot(results['size'], results['optimized_time'], 'o-', label='最適化版')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('データポイント数')
    plt.ylabel('実行時間 (秒)')
    plt.title('実行時間比較 (対数スケール)')
    plt.grid(True)
    plt.legend()
    
    # 実行時間グラフ（線形スケール）
    plt.subplot(2, 2, 2)
    plt.plot(results['size'], results['original_time'], 'o-', label='オリジナル')
    plt.plot(results['size'], results['optimized_time'], 'o-', label='最適化版')
    plt.xlabel('データポイント数')
    plt.ylabel('実行時間 (秒)')
    plt.title('実行時間比較 (線形スケール)')
    plt.grid(True)
    plt.legend()
    
    # メモリ使用量グラフ（対数スケール）
    plt.subplot(2, 2, 3)
    plt.plot(results['size'], results['original_memory'], 'o-', label='オリジナル')
    plt.plot(results['size'], results['optimized_memory'], 'o-', label='最適化版')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('データポイント数')
    plt.ylabel('メモリ使用量 (MB)')
    plt.title('メモリ使用量比較 (対数スケール)')
    plt.grid(True)
    plt.legend()
    
    # メモリ使用量グラフ（線形スケール）
    plt.subplot(2, 2, 4)
    plt.plot(results['size'], results['original_memory'], 'o-', label='オリジナル')
    plt.plot(results['size'], results['optimized_memory'], 'o-', label='最適化版')
    plt.xlabel('データポイント数')
    plt.ylabel('メモリ使用量 (MB)')
    plt.title('メモリ使用量比較 (線形スケール)')
    plt.grid(True)
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('benchmark_results.png')
    plt.show()

def main():
    """
    メイン関数 - ベンチマーク実行と結果表示
    """
    print("AnomalyDetector パフォーマンステスト開始")
    print("-" * 50)
    
    # psutilがインストールされていない場合の処理
    try:
        import psutil
    except ImportError:
        print("パッケージ 'psutil' がインストールされていません。pip install psutil でインストールしてください。")
        print("メモリ使用量の測定はスキップされます。")
        return
    
    # memory_profilerがインストールされていない場合の処理
    try:
        import memory_profiler
    except ImportError:
        print("パッケージ 'memory_profiler' がインストールされていません。pip install memory_profiler でインストールしてください。")
        print("詳細なメモリプロファイリングはスキップされます。")
    
    # ベンチマーク実行
    # データサイズは、小規模から超大規模までの範囲を設定
    results = run_benchmark([100, 1000, 10000])  # 最大サイズを調整可能
    
    # 結果の詳細表示
    print("\n結果サマリー:")
    print("-" * 50)
    print(f"{'データサイズ':>12} | {'オリジナル時間(秒)':>18} | {'最適化時間(秒)':>18} | {'速度向上率':>10} | {'メモリ削減率':>10}")
    print("-" * 80)
    
    for i, size in enumerate(results['size']):
        speedup = results['original_time'][i] / results['optimized_time'][i] if results['optimized_time'][i] > 0 else float('inf')
        memory_reduction = results['original_memory'][i] / results['optimized_memory'][i] if results['optimized_memory'][i] > 0 else float('inf')
        
        print(f"{size:>12,d} | {results['original_time'][i]:>18.6f} | {results['optimized_time'][i]:>18.6f} | {speedup:>10.2f}x | {memory_reduction:>10.2f}x")
    
    # グラフ表示（可能な場合）
    try:
        import matplotlib.pyplot as plt
        plot_results(results)
    except ImportError:
        print("\nmatplotlibがインストールされていないため、グラフ表示をスキップします。pip install matplotlib でインストールしてください。")
    
    print("\n全てのベンチマークテストが完了しました。")

if __name__ == "__main__":
    main()
