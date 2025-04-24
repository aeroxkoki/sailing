#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メモリ使用量プロファイリングスクリプト

このスクリプトは sailing_data_processor モジュールの各コンポーネントの
メモリ使用量を測定し、潜在的なメモリリークを特定します。
"""

import os
import sys
import gc
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psutil
import argparse
from memory_profiler import profile

# sailing_data_processor モジュールへのパスを追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sailing_data_processor.core import SailingDataProcessor
from sailing_data_processor.wind_estimator import WindEstimator
from sailing_data_processor.performance_optimizer import PerformanceOptimizer

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
    
    # 基本的な経路を生成（円を描く）
    timestamps = []
    latitudes = []
    longitudes = []
    
    start_time = datetime.now()
    
    for i in range(num_points):
        # 時間経過
        current_time = start_time + timedelta(seconds=i)
        
        # 座標（円を描く）
        angle = (i / num_points) * 2 * np.pi
        radius = 0.01  # 約1km程度の円
        lat = start_lat + radius * np.sin(angle)
        lon = start_lon + radius * np.cos(angle)
        
        timestamps.append(current_time)
        latitudes.append(lat)
        longitudes.append(lon)
    
    # DataFrameに変換
    df = pd.DataFrame({
        'timestamp': timestamps,
        'latitude': latitudes,
        'longitude': longitudes,
        'boat_id': 'test_boat'
    })
    
    return df

@profile
def test_core_memory_usage(num_points=10000, iterations=5):
    """SailingDataProcessorのメモリ使用量をテスト"""
    print("\n===== SailingDataProcessor メモリ使用量テスト =====")
    
    initial_memory = get_memory_usage()
    print(f"初期メモリ使用量: {initial_memory:.2f} MB")
    
    # SailingDataProcessorインスタンスを作成
    processor = SailingDataProcessor()
    
    for i in range(iterations):
        print(f"\nイテレーション {i+1}/{iterations}")
        
        # テストデータ生成
        df = generate_sample_data(num_points)
        file_content = df.to_csv().encode('utf-8')
        
        # 開始時のメモリ使用量を記録
        before_load = get_memory_usage()
        print(f"データロード前のメモリ使用量: {before_load:.2f} MB")
        
        # データをロード
        boat_data = processor.load_multiple_files([
            ('test_boat.csv', file_content, 'csv')
        ])
        
        after_load = get_memory_usage()
        print(f"データロード後のメモリ使用量: {after_load:.2f} MB (増加: {after_load - before_load:.2f} MB)")
        
        # GPSデータの異常検出と修正
        before_process = get_memory_usage()
        processed_data = processor.detect_and_fix_gps_anomalies('test_boat')
        
        after_process = get_memory_usage()
        print(f"データ処理後のメモリ使用量: {after_process:.2f} MB (増加: {after_process - before_process:.2f} MB)")
        
        # 風向風速の推定
        before_wind = get_memory_usage()
        wind_data = processor.estimate_wind_from_boat('test_boat')
        
        after_wind = get_memory_usage()
        print(f"風推定後のメモリ使用量: {after_wind:.2f} MB (増加: {after_wind - before_wind:.2f} MB)")
        
        # クリーンアップ
        before_cleanup = get_memory_usage()
        processor.cleanup_memory()
        gc.collect()
        
        after_cleanup = get_memory_usage()
        print(f"クリーンアップ後のメモリ使用量: {after_cleanup:.2f} MB (変化: {after_cleanup - before_cleanup:.2f} MB)")
        
        # メモリリークの検出
        memory_leak = after_cleanup - initial_memory
        print(f"潜在的なメモリリーク: {memory_leak:.2f} MB")
    
    return

@profile
def test_wind_estimator_memory(num_points=10000, iterations=5):
    """WindEstimatorのメモリ使用量をテスト"""
    print("\n===== WindEstimator メモリ使用量テスト =====")
    
    initial_memory = get_memory_usage()
    print(f"初期メモリ使用量: {initial_memory:.2f} MB")
    
    # テストデータ生成
    df = generate_sample_data(num_points)
    
    for i in range(iterations):
        print(f"\nイテレーション {i+1}/{iterations}")
        
        # 開始時のメモリ使用量を記録
        before_estimate = get_memory_usage()
        print(f"風推定前のメモリ使用量: {before_estimate:.2f} MB")
        
        # 新しいWindEstimatorインスタンスを作成
        estimator = WindEstimator()
        
        # 風向風速を推定
        wind_data = estimator.estimate_wind_from_single_boat(
            gps_data=df,
            min_tack_angle=30.0,
            boat_type='default',
            use_bayesian=True
        )
        
        after_estimate = get_memory_usage()
        print(f"風推定後のメモリ使用量: {after_estimate:.2f} MB (増加: {after_estimate - before_estimate:.2f} MB)")
        
        # クリーンアップ
        del estimator
        gc.collect()
        
        after_cleanup = get_memory_usage()
        print(f"クリーンアップ後のメモリ使用量: {after_cleanup:.2f} MB (変化: {after_cleanup - after_estimate:.2f} MB)")
        
        # メモリリークの検出
        memory_leak = after_cleanup - initial_memory
        print(f"潜在的なメモリリーク: {memory_leak:.2f} MB")
    
    return

@profile
def test_storage_operations(num_points=1000, iterations=3):
    """ストレージ操作のメモリ使用量をテスト"""
    print("\n===== ストレージ操作 メモリ使用量テスト =====")
    print("※注: このテストはコマンドラインで実行する必要があります")
    
    try:
        # sailing_data_processor.storage.browser_storageモジュールをインポート
        from sailing_data_processor.storage.browser_storage import BrowserStorage
        print("BrowserStorageモジュールをインポートしました（テスト環境では実際の操作は行われません）")
    except ImportError:
        print("※ BrowserStorageモジュールをインポートできませんでした。スキップします。")
        return
    except Exception as e:
        print(f"※ ストレージモジュールのインポート中にエラーが発生しました: {str(e)}。スキップします。")
        return
    
    # 実際のストレージ操作はブラウザ環境でないとテストできないため、
    # ここではテスト用のダミーデータで代用
    initial_memory = get_memory_usage()
    print(f"初期メモリ使用量: {initial_memory:.2f} MB")
    
    # メモリ内にテスト用の大きなデータセットを作成
    data_list = []
    
    for i in range(iterations):
        print(f"\nイテレーション {i+1}/{iterations}")
        
        before_gen = get_memory_usage()
        print(f"データ生成前のメモリ使用量: {before_gen:.2f} MB")
        
        # 大きなデータを生成
        test_data = {
            'points': [generate_sample_data(num_points).to_dict() for _ in range(5)],
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
        
        data_list.append(test_data)
        
        after_gen = get_memory_usage()
        print(f"データ生成後のメモリ使用量: {after_gen:.2f} MB (増加: {after_gen - before_gen:.2f} MB)")
    
    # クリーンアップ
    before_cleanup = get_memory_usage()
    data_list.clear()
    gc.collect()
    
    after_cleanup = get_memory_usage()
    print(f"クリーンアップ後のメモリ使用量: {after_cleanup:.2f} MB (変化: {after_cleanup - before_cleanup:.2f} MB)")
    
    # メモリリークの検出
    memory_leak = after_cleanup - initial_memory
    print(f"潜在的なメモリリーク: {memory_leak:.2f} MB")
    
    return

def main():
    """メインの実行関数"""
    parser = argparse.ArgumentParser(description='メモリ使用量プロファイリングツール')
    parser.add_argument('--component', choices=['core', 'wind', 'storage', 'all'], 
                        default='all', help='プロファイルするコンポーネント')
    parser.add_argument('--points', type=int, default=10000, help='テストデータポイント数')
    parser.add_argument('--iterations', type=int, default=3, help='繰り返し回数')
    
    args = parser.parse_args()
    
    print("====================================================")
    print("   セーリング戦略分析システム - メモリプロファイリング   ")
    print("====================================================")
    print(f"実行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"データポイント数: {args.points}")
    print(f"繰り返し回数: {args.iterations}")
    
    # 強制的なガベージコレクションで始める
    gc.collect()
    
    if args.component in ['core', 'all']:
        test_core_memory_usage(args.points, args.iterations)
    
    if args.component in ['wind', 'all']:
        test_wind_estimator_memory(args.points, args.iterations)
    
    if args.component in ['storage', 'all']:
        test_storage_operations(args.points // 10, max(1, args.iterations - 1))
    
    print("\n====================================================")
    print("   メモリプロファイリング完了")
    print("====================================================")

if __name__ == "__main__":
    main()
