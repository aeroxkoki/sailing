#!/usr/bin/env python3
"""
GPSデータ処理のパフォーマンスベンチマークスクリプト

このスクリプトはGPSデータの読み込みと処理のパフォーマンスを
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
import io
import tempfile

# sailing_data_processor モジュールへのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sailing_data_processor.core import SailingDataProcessor

def get_memory_usage():
    """現在のメモリ使用量を取得 (MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def generate_sample_data(num_points=5000, noise_level=0.2):
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

def benchmark_data_loading(df, iterations=3, chunk_sizes=None):
    """データ読み込みのパフォーマンスをベンチマーク"""
    print(f"\n--- GPSデータ読み込みのベンチマーク ({len(df)}ポイント) ---")
    
    # DataFrameをCSVに変換
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode('utf-8')
    
    print(f"データサイズ: {len(csv_bytes) / 1024:.1f}KB, 行数: {len(df)}")
    
    results = {
        'data_bytes': len(csv_bytes),
        'data_points': len(df),
        'load_time': [],
        'memory_usage': []
    }
    
    # チャンク読み込みテスト用のサイズ設定
    if chunk_sizes is None:
        # デフォルトのチャンクサイズリスト
        if len(df) > 100000:
            chunk_sizes = [1000, 5000, 10000]
        elif len(df) > 10000:
            chunk_sizes = [500, 1000, 5000]
        else:
            chunk_sizes = [100, 500, 1000]
    
    # チャンクサイズごとの結果を追加
    for chunk_size in chunk_sizes:
        results[f'chunk_{chunk_size}'] = []
    
    for i in range(iterations):
        print(f"\nイテレーション {i+1}/{iterations}")
        
        # 最初に明示的にガベージコレクション
        gc.collect()
        
        # 初期メモリ使用量を記録
        initial_memory = get_memory_usage()
        print(f"初期メモリ使用量: {initial_memory:.2f}MB")
        
        # 標準読み込み（一括）
        start_time = time.time()
        processor = SailingDataProcessor()
        processor.load_multiple_files([
            ('test_boat.csv', csv_bytes, 'csv')
        ])
        load_time = time.time() - start_time
        results['load_time'].append(load_time)
        print(f"標準読み込み時間: {load_time:.3f}秒")
        
        # メモリ使用量
        current_memory = get_memory_usage()
        memory_increase = current_memory - initial_memory
        results['memory_usage'].append(memory_increase)
        print(f"メモリ増加量: {memory_increase:.2f}MB")
        
        # チャンク処理のテスト
        for chunk_size in chunk_sizes:
            # リセット
            del processor
            gc.collect()
            
            # チャンク読み込みのシミュレーション
            start_time = time.time()
            chunk_read_time = _simulate_chunked_reading(csv_bytes, chunk_size)
            results[f'chunk_{chunk_size}'].append(chunk_read_time)
            print(f"チャンク読み込み時間 (サイズ {chunk_size}): {chunk_read_time:.3f}秒")
        
        # クリーンアップ
        gc.collect()
    
    # 平均値を計算
    avg_results = {
        'data_bytes': len(csv_bytes),
        'data_points': len(df),
        'load_time': sum(results['load_time']) / len(results['load_time']),
        'memory_usage': sum(results['memory_usage']) / len(results['memory_usage']),
    }
    
    # チャンクサイズごとの平均値も計算
    for chunk_size in chunk_sizes:
        chunk_key = f'chunk_{chunk_size}'
        avg_results[chunk_key] = sum(results[chunk_key]) / len(results[chunk_key])
    
    # 最適なチャンクサイズを探す
    chunk_times = [(chunk_size, avg_results[f'chunk_{chunk_size}']) for chunk_size in chunk_sizes]
    best_chunk_size, best_time = min(chunk_times, key=lambda x: x[1])
    avg_results['best_chunk_size'] = best_chunk_size
    avg_results['best_chunk_time'] = best_time
    
    print(f"\n最適なチャンクサイズ: {best_chunk_size} (処理時間: {best_time:.3f}秒)")
    print(f"標準読み込みとの比較: {avg_results['load_time'] / best_time:.1f}倍 高速")
    
    return avg_results

def _simulate_chunked_reading(csv_data, chunk_size):
    """チャンク読み込みシミュレーション"""
    start_time = time.time()
    
    # CSVファイルの内容を一時ファイルに書き込む
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(csv_data)
        temp_file_path = temp_file.name
    
    try:
        # chunksizeを指定してパンダスで読み込み
        chunks = pd.read_csv(temp_file_path, chunksize=chunk_size)
        
        # 各チャンクを読み込む（処理をシミュレート）
        data_frames = []
        for chunk in chunks:
            # 何らかの処理（ここではデータを保存するだけ）
            data_frames.append(chunk)
        
        # 全チャンクを結合（実際の実装では必要に応じて行う）
        if data_frames:
            combined_df = pd.concat(data_frames, ignore_index=True)
    finally:
        # 一時ファイルを削除
        os.unlink(temp_file_path)
    
    return time.time() - start_time

def benchmark_data_processing(df, iterations=3):
    """GPSデータ処理のパフォーマンスをベンチマーク"""
    print(f"\n--- GPSデータ処理のベンチマーク ({len(df)}ポイント) ---")
    
    results = {
        'data_points': len(df),
        'preprocess_time': [],
        'memory_usage': []
    }
    
    for i in range(iterations):
        print(f"\nイテレーション {i+1}/{iterations}")
        
        # 明示的にガベージコレクション
        gc.collect()
        
        # 初期メモリ使用量を記録
        initial_memory = get_memory_usage()
        print(f"初期メモリ使用量: {initial_memory:.2f}MB")
        
        # 新しいプロセッサインスタンスを作成
        processor = SailingDataProcessor()
        
        # データを設定
        processor.boat_data['test_boat'] = df.copy()
        
        # データ処理の実行
        start_time = time.time()
        processor.process_multiple_boats()
        preprocess_time = time.time() - start_time
        results['preprocess_time'].append(preprocess_time)
        print(f"データ処理時間: {preprocess_time:.3f}秒")
        
        # メモリ使用量
        current_memory = get_memory_usage()
        memory_increase = current_memory - initial_memory
        results['memory_usage'].append(memory_increase)
        print(f"メモリ増加量: {memory_increase:.2f}MB")
        
        # クリーンアップ
        del processor
        gc.collect()
    
    # 平均値を計算
    avg_results = {
        'data_points': len(df),
        'preprocess_time': sum(results['preprocess_time']) / len(results['preprocess_time']),
        'memory_usage': sum(results['memory_usage']) / len(results['memory_usage']),
    }
    
    return avg_results

def benchmark_with_different_sizes(size_multipliers=(0.2, 0.5, 1.0, 2.0), base_size=5000):
    """異なるデータサイズでのベンチマーク"""
    print("\n--- 異なるデータサイズでのベンチマーク ---")
    
    results = []
    
    for multiplier in size_multipliers:
        size = int(base_size * multiplier)
        print(f"\n=== データサイズ: {size} ポイント ===")
        
        # サンプルデータを生成
        sample_data = generate_sample_data(num_points=size)
        
        # 読み込みベンチマーク
        load_result = benchmark_data_loading(sample_data, iterations=2, chunk_sizes=[100, 500])
        
        # 処理ベンチマーク
        process_result = benchmark_data_processing(sample_data, iterations=2)
        
        # 結果を保存
        results.append({
            'size': size,
            'load_time': load_result['load_time'],
            'process_time': process_result['preprocess_time'],
            'memory_load': load_result['memory_usage'],
            'memory_process': process_result['memory_usage']
        })
        
        # クリーンアップ
        del sample_data
        gc.collect()
    
    return results

def plot_benchmark_results(size_results, output_file=None):
    """異なるサイズでのベンチマーク結果をグラフ化"""
    plt.figure(figsize=(12, 5))
    
    # 処理時間のプロット
    plt.subplot(1, 2, 1)
    sizes = [r['size'] for r in size_results]
    load_times = [r['load_time'] for r in size_results]
    process_times = [r['process_time'] for r in size_results]
    
    plt.plot(sizes, load_times, 'o-', label='データ読み込み')
    plt.plot(sizes, process_times, 's-', label='データ処理')
    plt.xlabel('データポイント数')
    plt.ylabel('処理時間 (秒)')
    plt.title('処理時間とデータサイズの関係')
    plt.legend()
    plt.grid(True)
    
    # メモリ使用量のプロット
    plt.subplot(1, 2, 2)
    memory_load = [r['memory_load'] for r in size_results]
    memory_process = [r['memory_process'] for r in size_results]
    
    plt.plot(sizes, memory_load, 'o-', label='データ読み込み', color='green')
    plt.plot(sizes, memory_process, 's-', label='データ処理', color='orange')
    plt.xlabel('データポイント数')
    plt.ylabel('メモリ使用量 (MB)')
    plt.title('メモリ使用量とデータサイズの関係')
    plt.legend()
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
    output_file = 'benchmark_results/my_gps_processing_benchmark.json'
    points = 5000
    iterations = 2
    size_test = True
    
    print("==================================================")
    print("   GPSデータ処理 - パフォーマンスベンチマーク   ")
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
    
    # データ読み込みのベンチマーク
    load_results = benchmark_data_loading(sample_data, iterations=iterations)
    final_results['data_loading'] = load_results
    
    # データ処理のベンチマーク
    process_results = benchmark_data_processing(sample_data, iterations=iterations)
    final_results['data_processing'] = process_results
    
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
    print(f"データ読み込み ({points}ポイント):")
    print(f"  標準読み込み時間: {load_results['load_time']:.3f}秒")
    if 'best_chunk_size' in load_results:
        print(f"  最適チャンクサイズ: {load_results['best_chunk_size']} (時間: {load_results['best_chunk_time']:.3f}秒)")
    print(f"  メモリ使用量: {load_results['memory_usage']:.2f}MB")
    
    print(f"\nデータ処理 ({points}ポイント):")
    print(f"  処理時間: {process_results['preprocess_time']:.3f}秒")
    print(f"  メモリ使用量: {process_results['memory_usage']:.2f}MB")
    
    print("\n==================================================")
    print("   ベンチマーク完了")
    print("==================================================")

if __name__ == "__main__":
    main()
