#!/usr/bin/env python3
"""
GPSデータ処理のパフォーマンスベンチマークスクリプト

このスクリプトは大規模GPSデータの読み込み、処理、および異常検出の
パフォーマンスを測定し、最適化前後の比較を行います。
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
import matplotlib.pyplot as plt
import io
import tempfile
import random

# sailing_data_processor モジュールへのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sailing_data_processor.core import SailingDataProcessor
from sailing_data_processor.importers.csv_importer import CSVImporter
from sailing_data_processor.importers.gpx_importer import GPXImporter  # 存在する場合

def get_memory_usage():
    """現在のメモリ使用量を取得 (MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def generate_sample_gps_data(num_points=5000, noise_level=0.2, file_format='csv'):
    """テスト用のサンプルGPSデータを生成"""
    print(f"サンプルGPSデータを生成中 ({num_points}ポイント, 形式:{file_format})...")
    
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
        
        # ノイズを加える
        noise_factor = noise_level * np.random.random()
        
        lat = start_lat + radius * np.sin(angle) + (noise_factor * 0.001 * np.random.randn())
        lon = start_lon + radius * np.cos(angle) + (noise_factor * 0.001 * np.random.randn())
        
        # 速度（ノット）
        base_speed = 5.0 + 2.0 * np.sin(angle * 2)  # 速度変動（3〜7ノット）
        speed = base_speed + (noise_factor * 0.5 * np.random.randn())  # ノイズ追加
        
        # コース（進行方向）
        # 円周上を移動する場合の接線方向（90度ずらす）
        base_course = (np.degrees(angle) + 90) % 360
        course = base_course + (noise_factor * 5 * np.random.randn())  # ノイズ追加
        course = course % 360  # 0-360の範囲に正規化
        
        timestamps.append(current_time)
        latitudes.append(lat)
        longitudes.append(lon)
        speeds.append(max(0.1, speed))  # 負の速度を防止
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
    
    # 異常値を追加（テスト用）
    if num_points > 100:
        anomaly_count = int(num_points * 0.02)  # 全体の2%
        anomaly_indices = np.random.choice(range(len(df)), size=anomaly_count, replace=False)
        
        for idx in anomaly_indices:
            anomaly_type = random.choice(['position', 'speed', 'course'])
            
            if anomaly_type == 'position':
                # 位置が急に遠くに飛ぶ
                df.loc[idx, 'latitude'] += random.choice([-1, 1]) * random.uniform(0.01, 0.05)
                df.loc[idx, 'longitude'] += random.choice([-1, 1]) * random.uniform(0.01, 0.05)
            elif anomaly_type == 'speed':
                # 異常な速度
                df.loc[idx, 'speed'] = random.uniform(25, 50)  # 非現実的な速度
            else:  # course
                # 急激なコース変更
                df.loc[idx, 'course'] = (df.loc[idx, 'course'] + random.uniform(100, 260)) % 360
    
    # 指定されたフォーマットでデータを返す
    if file_format == 'dataframe':
        return df
    elif file_format == 'csv':
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        return csv_buffer.getvalue().encode('utf-8')
    else:
        # 未対応のフォーマット
        raise ValueError(f"未対応のファイル形式: {file_format}")

def benchmark_data_loading(sample_data, iterations=3, chunk_sizes=None):
    """データ読み込みのパフォーマンスをベンチマーク"""
    print(f"\n--- GPSデータ読み込みのベンチマーク ---")
    
    if isinstance(sample_data, pd.DataFrame):
        # DataFrameをCSVに変換
        csv_data = io.StringIO()
        sample_data.to_csv(csv_data, index=False)
        csv_bytes = csv_data.getvalue().encode('utf-8')
        data_points = len(sample_data)
    else:
        # バイナリデータと想定
        csv_bytes = sample_data
        # 行数を概算
        data_points = sample_data.count(b'\n')
    
    print(f"データサイズ: {len(csv_bytes) / 1024:.1f}KB, 概算行数: {data_points}")
    
    results = {
        'data_bytes': len(csv_bytes),
        'data_points': data_points,
        'load_time': [],
        'memory_usage': []
    }
    
    # チャンク読み込みテスト用のサイズ設定
    if chunk_sizes is None:
        # デフォルトのチャンクサイズリスト
        if data_points > 100000:
            chunk_sizes = [1000, 5000, 10000, 20000]
        elif data_points > 10000:
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
            
            # CSVインポーター直接利用（チャンク読み込み）
            start_time = time.time()
            importer = CSVImporter()
            # チャンク処理をシミュレート
            chunk_read_time = _simulate_chunked_reading(csv_bytes, chunk_size)
            results[f'chunk_{chunk_size}'].append(chunk_read_time)
            print(f"チャンク読み込み時間 (サイズ {chunk_size}): {chunk_read_time:.3f}秒")
            
            # クリーンアップ
            del importer
        
        # クリーンアップ
        gc.collect()
    
    # 平均値を計算
    avg_results = {
        'data_bytes': len(csv_bytes),
        'data_points': data_points,
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
    """チャンク読み込みシミュレーション（実装がない場合のダミー）"""
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

def benchmark_anomaly_detection(sample_data, iterations=3):
    """異常検出アルゴリズムのパフォーマンスをベンチマーク"""
    print(f"\n--- 異常検出アルゴリズムのベンチマーク ---")
    
    if not isinstance(sample_data, pd.DataFrame):
        # バイナリデータの場合はDataFrameに変換
        df = pd.read_csv(io.BytesIO(sample_data))
    else:
        df = sample_data.copy()
    
    print(f"データポイント数: {len(df)}")
    
    results = {
        'data_points': len(df),
        'detection_time': [],
        'memory_usage': []
    }
    
    for i in range(iterations):
        print(f"\nイテレーション {i+1}/{iterations}")
        
        # 最初に明示的にガベージコレクション
        gc.collect()
        
        # 初期メモリ使用量を記録
        initial_memory = get_memory_usage()
        print(f"初期メモリ使用量: {initial_memory:.2f}MB")
        
        # 新しいプロセッサインスタンスを作成
        processor = SailingDataProcessor()
        
        # 最初にデータをロード
        processor.boat_data['test_boat'] = df.copy()
        
        # 異常検出の実行
        start_time = time.time()
        fixed_df = processor.detect_and_fix_gps_anomalies('test_boat')
        detection_time = time.time() - start_time
        results['detection_time'].append(detection_time)
        print(f"異常検出処理時間: {detection_time:.3f}秒")
        
        # メモリ使用量
        current_memory = get_memory_usage()
        memory_increase = current_memory - initial_memory
        results['memory_usage'].append(memory_increase)
        print(f"メモリ増加量: {memory_increase:.2f}MB")
        
        # 異常の統計情報
        if fixed_df is not None:
            # 元のdfと修正済みdfを比較して変更を検出
            modified_rows = (~df.equals(fixed_df))
            if isinstance(modified_rows, bool):
                # データフレーム全体で比較した場合
                print(f"データに変更がありました: {modified_rows}")
            else:
                # 各行を比較している場合
                modified_count = modified_rows.sum()
                print(f"修正された異常データポイント数: {modified_count}")
        
        # クリーンアップ
        del processor
        del fixed_df
        gc.collect()
    
    # 平均値を計算
    avg_results = {
        'data_points': len(df),
        'detection_time': sum(results['detection_time']) / len(results['detection_time']),
        'memory_usage': sum(results['memory_usage']) / len(results['memory_usage']),
        'raw_data': results  # 生データも保存
    }
    
    return avg_results

def benchmark_with_different_sizes(size_multipliers=(0.2, 0.5, 1.0, 2.0, 5.0), base_size=5000):
    """異なるデータサイズでのベンチマーク"""
    print("\n--- 異なるデータサイズでのベンチマーク ---")
    
    size_results = []
    
    for multiplier in size_multipliers:
        size = int(base_size * multiplier)
        print(f"\n=== データサイズ: {size} ポイント ===")
        
        # サンプルデータ生成
        sample_data = generate_sample_gps_data(num_points=size, file_format='dataframe')
        
        # 読み込みベンチマーク（コピーを使用）
        load_result = benchmark_data_loading(sample_data.copy(), iterations=2)
        
        # 異常検出ベンチマーク
        anomaly_result = benchmark_anomaly_detection(sample_data, iterations=2)
        
        # 結果を追加
        size_results.append({
            'size': size,
            'load_time': load_result['load_time'],
            'detection_time': anomaly_result['detection_time'],
            'memory_load': load_result['memory_usage'],
            'memory_detection': anomaly_result['memory_usage']
        })
        
        # クリーンアップ
        del sample_data
        gc.collect()
    
    return size_results

def save_benchmark_results(results, output_file):
    """ベンチマーク結果をJSONファイルに保存"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nベンチマーク結果を保存しました: {output_file}")

def plot_benchmark_results(size_results, output_file=None):
    """異なるサイズでのベンチマーク結果を視覚化"""
    plt.figure(figsize=(14, 6))
    
    # 処理時間のプロット
    plt.subplot(1, 2, 1)
    sizes = [r['size'] for r in size_results]
    load_times = [r['load_time'] for r in size_results]
    detection_times = [r['detection_time'] for r in size_results]
    
    plt.plot(sizes, load_times, 'o-', label='Data Loading')
    plt.plot(sizes, detection_times, 's-', label='Anomaly Detection')
    plt.xlabel('Data Points')
    plt.ylabel('Time (seconds)')
    plt.title('Processing Time vs. Data Size')
    plt.legend()
    plt.grid(True)
    
    # メモリ使用量のプロット
    plt.subplot(1, 2, 2)
    memory_load = [r['memory_load'] for r in size_results]
    memory_detection = [r['memory_detection'] for r in size_results]
    
    plt.plot(sizes, memory_load, 'o-', label='Data Loading', color='green')
    plt.plot(sizes, memory_detection, 's-', label='Anomaly Detection', color='orange')
    plt.xlabel('Data Points')
    plt.ylabel('Memory Usage (MB)')
    plt.title('Memory Usage vs. Data Size')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file)
        print(f"ベンチマークグラフを保存しました: {output_file}")
    
    plt.close()

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='GPSデータ処理のパフォーマンスベンチマーク')
    parser.add_argument('--output', default='benchmark_results/data_processing_benchmark.json',
                        help='結果の出力先JSONファイル')
    parser.add_argument('--points', type=int, default=5000, help='テストデータポイント数')
    parser.add_argument('--iterations', type=int, default=3, help='繰り返し回数')
    parser.add_argument('--size-test', action='store_true', 
                        help='異なるデータサイズでのテストを実行')
    
    args = parser.parse_args()
    
    print("==================================================")
    print("   GPSデータ処理 - パフォーマンスベンチマーク   ")
    print("==================================================")
    print(f"実行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"基本データポイント数: {args.points}")
    print(f"繰り返し回数: {args.iterations}")
    
    # 出力ディレクトリの確保
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # 結果を格納するディクショナリ
    final_results = {
        'timestamp': datetime.now().isoformat(),
        'data_points': args.points,
        'iterations': args.iterations
    }
    
    # 標準サイズのベンチマーク
    # サンプルデータ生成
    sample_data_df = generate_sample_gps_data(args.points, file_format='dataframe')
    sample_data_csv = generate_sample_gps_data(args.points, file_format='csv')
    
    # データロードのベンチマーク
    load_results = benchmark_data_loading(sample_data_csv, args.iterations)
    final_results['data_loading'] = load_results
    
    # 異常検出のベンチマーク
    anomaly_results = benchmark_anomaly_detection(sample_data_df, args.iterations)
    final_results['anomaly_detection'] = anomaly_results
    
    # サイズ別ベンチマーク（オプション）
    if args.size_test:
        print("\n--- データサイズ別ベンチマーク実行 ---")
        size_results = benchmark_with_different_sizes()
        final_results['size_benchmark'] = size_results
        
        # グラフの生成
        graph_file = os.path.splitext(args.output)[0] + '.png'
        plot_benchmark_results(size_results, graph_file)
    
    # 結果の保存
    save_benchmark_results(final_results, args.output)
    
    print("\n--- ベンチマーク結果サマリー ---")
    print(f"データロード ({args.points}ポイント):")
    print(f"  標準読み込み時間: {load_results['load_time']:.3f}秒")
    if 'best_chunk_size' in load_results:
        print(f"  最適チャンクサイズ: {load_results['best_chunk_size']} (時間: {load_results['best_chunk_time']:.3f}秒)")
    print(f"  メモリ使用量: {load_results['memory_usage']:.2f}MB")
    
    print(f"\n異常検出 ({args.points}ポイント):")
    print(f"  検出処理時間: {anomaly_results['detection_time']:.3f}秒")
    print(f"  メモリ使用量: {anomaly_results['memory_usage']:.2f}MB")
    
    print("\n==================================================")
    print("   ベンチマーク完了")
    print("==================================================")

if __name__ == "__main__":
    main()
