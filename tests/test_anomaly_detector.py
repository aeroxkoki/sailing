"""
AnomalyDetector テストスクリプト

このスクリプトは異常値検出アルゴリズムの動作確認とパフォーマンス簡易測定を行います。
"""

import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# sailing_data_processorモジュールをインポート
import os
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

def test_anomaly_detection():
    """
    オリジナルアルゴリズムと最適化アルゴリズムの一貫性を検証する関数
    """
    print("異常値検出テスト開始")
    print("-" * 40)
    
    detector = AnomalyDetector()
    test_sizes = [100, 1000]
    
    for size in test_sizes:
        print(f"\nデータサイズ: {size}ポイント")
        df = generate_test_data(size)
        
        # オリジナルバージョンの実行
        start_time = time.time()
        original_indices, original_scores = detector._detect_by_speed_original(
            df['latitude'],
            df['longitude'],
            df['timestamp']
        )
        original_time = time.time() - start_time
        
        # 最適化バージョンの実行
        start_time = time.time()
        optimized_indices, optimized_scores = detector._detect_by_speed_optimized(
            df['latitude'],
            df['longitude'],
            df['timestamp']
        )
        optimized_time = time.time() - start_time
        
        # 結果の確認
        original_indices_set = set(original_indices)
        optimized_indices_set = set(optimized_indices)
        
        # 検出された異常値の数を比較
        print(f"オリジナル版検出異常値数: {len(original_indices)}")
        print(f"最適化版検出異常値数: {len(optimized_indices)}")
        
        # 一致率を計算
        if len(original_indices_set) > 0:
            matching_indices = original_indices_set.intersection(optimized_indices_set)
            match_ratio = len(matching_indices) / len(original_indices_set) * 100
            print(f"一致率: {match_ratio:.2f}%")
        else:
            print("オリジナル版が検出した異常値なし")
        
        # 実行時間の比較
        print(f"オリジナル実行時間: {original_time:.6f}秒")
        print(f"最適化版実行時間: {optimized_time:.6f}秒")
        speedup = original_time / optimized_time if optimized_time > 0 else float('inf')
        print(f"速度向上率: {speedup:.2f}倍")
        
        # 不一致がある場合の詳細（10件まで表示）
        diff_original = original_indices_set - optimized_indices_set
        diff_optimized = optimized_indices_set - original_indices_set
        
        if diff_original or diff_optimized:
            print("\n不一致の詳細:")
            if diff_original:
                print(f"オリジナルのみで検出: {len(diff_original)}件")
                sample = list(diff_original)[:10]  # 最大10件表示
                print(f"サンプル: {sample}")
            
            if diff_optimized:
                print(f"最適化版のみで検出: {len(diff_optimized)}件")
                sample = list(diff_optimized)[:10]  # 最大10件表示
                print(f"サンプル: {sample}")
    
    print("\n全てのテストが完了しました。")

if __name__ == "__main__":
    test_anomaly_detection()
