#!/usr/bin/env python3
"""
WindFieldFusionSystem モジュールのパフォーマンスベンチマーク

このスクリプトは風の場融合システムのパフォーマンスを測定し、
最適化前後での比較を可能にします。
"""

import os
import sys
import time
import psutil
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import tracemalloc

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# テスト対象のモジュールをインポート
try:
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
except ImportError as e:
    print(f"インポートエラー: {e}")
    print(f"現在のシステムパス: {sys.path}")
    sys.exit(1)

def generate_test_data(num_boats=2, points_per_boat=100, 
                       time_span_minutes=60, area_size=0.05,
                       base_lat=35.45, base_lon=139.65):
    """
    テスト用の艇データを生成する関数
    
    Parameters:
    -----------
    num_boats : int
        生成する艇の数
    points_per_boat : int
        各艇の位置/風データポイント数
    time_span_minutes : int
        データのタイムスパン（分）
    area_size : float
        データ範囲の広さ（緯度・経度の度数）
    base_lat, base_lon : float
        基準となる位置
        
    Returns:
    --------
    Dict[str, pd.DataFrame]
        艇IDをキーとする艇データのデータフレームの辞書
    """
    base_time = datetime.now()
    boats_data = {}
    
    for boat_idx in range(num_boats):
        # 各艇のデータを生成
        time_points = [base_time + timedelta(minutes=i * time_span_minutes / points_per_boat) 
                      for i in range(points_per_boat)]
        
        # 基準位置からの相対的な位置
        boat_offset_lat = boat_idx * area_size / (num_boats * 2)
        boat_offset_lon = boat_idx * area_size / (num_boats * 2)
        
        # 風のパターンを定義（時間経過で変化する基本パターン + ランダム変動）
        base_wind_direction = 90 + boat_idx * 5  # 基本風向
        base_wind_speed = 10 + boat_idx * 0.5    # 基本風速
        
        # 位置と風データを生成
        latitudes = []
        longitudes = []
        wind_directions = []
        wind_speeds = []
        
        for i in range(points_per_boat):
            # 位置データ - 時間とともに変化させる
            progress = i / points_per_boat
            lat = base_lat + boat_offset_lat + progress * area_size / 2 + np.random.normal(0, 0.0005)
            lon = base_lon + boat_offset_lon + progress * area_size / 2 + np.random.normal(0, 0.0005)
            
            # 風データ - 時間とともに変化させる + ランダム変動
            wind_dir = (base_wind_direction + progress * 20 + np.random.normal(0, 5)) % 360
            wind_spd = base_wind_speed + progress * 2 + np.random.normal(0, 0.8)
            
            latitudes.append(lat)
            longitudes.append(lon)
            wind_directions.append(wind_dir)
            wind_speeds.append(max(0.5, wind_spd))  # 最低0.5ノット
        
        # データフレームを作成
        boat_df = pd.DataFrame({
            'timestamp': time_points,
            'latitude': latitudes,
            'longitude': longitudes,
            'wind_direction': wind_directions,
            'wind_speed_knots': wind_speeds,
            'confidence': [0.8] * points_per_boat  # 一定の信頼度
        })
        
        boats_data[f'boat{boat_idx+1}'] = boat_df
    
    return boats_data

def measure_memory_usage():
    """
    現在のメモリ使用量を測定する関数
    
    Returns:
    --------
    float
        使用メモリ量（MB）
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return memory_info.rss / 1024 / 1024  # バイトからMBに変換

def benchmark_wind_field_fusion(test_data_configs, iterations=3):
    """
    風の場融合システムのパフォーマンスをベンチマークする関数
    
    Parameters:
    -----------
    test_data_configs : List[Dict]
        テストデータ設定のリスト
    iterations : int
        各設定での反復回数
        
    Returns:
    --------
    Dict
        ベンチマーク結果
    """
    results = {
        'config': [],
        'num_boats': [],
        'points_per_boat': [],
        'total_points': [],
        'execution_time': [],
        'memory_usage': [],
        'success_rate': []
    }
    
    for config in test_data_configs:
        num_boats = config.get('num_boats', 2)
        points_per_boat = config.get('points_per_boat', 100)
        config_name = f"{num_boats}艇x{points_per_boat}ポイント"
        
        print(f"\n▶ ベンチマーク実行: {config_name}")
        
        # 複数回実行して平均を取る
        times = []
        memory_usages = []
        success_count = 0
        
        for i in range(iterations):
            # テストデータ生成
            boats_data = generate_test_data(
                num_boats=num_boats,
                points_per_boat=points_per_boat,
                time_span_minutes=config.get('time_span_minutes', 60),
                area_size=config.get('area_size', 0.05)
            )
            
            # メモリトラッキング開始
            tracemalloc.start()
            start_memory = measure_memory_usage()
            
            # 風の場融合システムの初期化
            fusion_system = WindFieldFusionSystem()
            
            # 処理時間測定開始
            start_time = time.time()
            
            try:
                # データ更新処理
                result = fusion_system.update_with_boat_data(boats_data)
                
                # 将来時点の予測処理も実行
                future_time = datetime.now() + timedelta(minutes=15)
                predicted_field = fusion_system.predict_wind_field(future_time)
                
                # 処理成功
                if result is not None and predicted_field is not None:
                    success_count += 1
                
                # 処理時間の記録
                execution_time = time.time() - start_time
                times.append(execution_time)
                
                # メモリ使用量の記録
                end_memory = measure_memory_usage()
                memory_usages.append(end_memory - start_memory)
                
                print(f"  イテレーション {i+1}/{iterations}: 時間 {execution_time:.4f}秒, メモリ使用 {end_memory - start_memory:.2f}MB")
                
            except Exception as e:
                print(f"  エラー発生: {e}")
            
            # メモリトラッキング停止
            tracemalloc.stop()
        
        # 結果を記録
        avg_time = sum(times) / len(times) if times else 0
        avg_memory = sum(memory_usages) / len(memory_usages) if memory_usages else 0
        success_rate = success_count / iterations
        
        results['config'].append(config_name)
        results['num_boats'].append(num_boats)
        results['points_per_boat'].append(points_per_boat)
        results['total_points'].append(num_boats * points_per_boat)
        results['execution_time'].append(avg_time)
        results['memory_usage'].append(avg_memory)
        results['success_rate'].append(success_rate)
        
        print(f"  ✓ 平均実行時間: {avg_time:.4f}秒")
        print(f"  ✓ 平均メモリ使用量: {avg_memory:.2f}MB")
        print(f"  ✓ 成功率: {success_rate * 100:.1f}%")
    
    return results

def plot_benchmark_results(results):
    """
    ベンチマーク結果をプロットする関数
    
    Parameters:
    -----------
    results : Dict
        ベンチマーク結果
    """
    # プロット用データフレーム作成
    df = pd.DataFrame(results)
    
    # 実行時間プロット
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    bar_width = 0.35
    x = np.arange(len(df['config']))
    plt.bar(x, df['execution_time'], bar_width, label='実行時間')
    for i, v in enumerate(df['execution_time']):
        plt.text(i, v + 0.05, f"{v:.2f}秒", ha='center')
    
    plt.xlabel('データサイズ')
    plt.ylabel('平均実行時間（秒）')
    plt.title('データサイズ別実行時間')
    plt.xticks(x, df['config'], rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # メモリ使用量プロット
    plt.subplot(1, 2, 2)
    plt.bar(x, df['memory_usage'], bar_width, color='orange', label='メモリ使用量')
    for i, v in enumerate(df['memory_usage']):
        plt.text(i, v + 0.5, f"{v:.1f}MB", ha='center')
    
    plt.xlabel('データサイズ')
    plt.ylabel('平均メモリ使用量（MB）')
    plt.title('データサイズ別メモリ使用量')
    plt.xticks(x, df['config'], rotation=45)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(project_root, 'benchmark_results.png'))
    plt.close()
    
    # ポイント数と時間/メモリの関係プロット
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.scatter(df['total_points'], df['execution_time'], s=80, alpha=0.7)
    for i, row in df.iterrows():
        plt.annotate(row['config'], 
                    (row['total_points'], row['execution_time']),
                    xytext=(5, 5), textcoords='offset points')
    
    plt.xlabel('総データポイント数')
    plt.ylabel('平均実行時間（秒）')
    plt.title('データポイント数と実行時間の関係')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.subplot(1, 2, 2)
    plt.scatter(df['total_points'], df['memory_usage'], s=80, alpha=0.7, color='orange')
    for i, row in df.iterrows():
        plt.annotate(row['config'], 
                    (row['total_points'], row['memory_usage']),
                    xytext=(5, 5), textcoords='offset points')
    
    plt.xlabel('総データポイント数')
    plt.ylabel('平均メモリ使用量（MB）')
    plt.title('データポイント数とメモリ使用量の関係')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(project_root, 'benchmark_scaling.png'))
    plt.close()
    
    # 結果を表形式でファイルに保存
    df.to_csv(os.path.join(project_root, 'benchmark_results.csv'), index=False)

def main():
    """メイン関数"""
    print("風の場融合システムのパフォーマンスベンチマークを実行します...")
    
    # テスト設定
    test_configs = [
        {'num_boats': 1, 'points_per_boat': 50},
        {'num_boats': 2, 'points_per_boat': 50},
        {'num_boats': 3, 'points_per_boat': 50},
        {'num_boats': 1, 'points_per_boat': 100},
        {'num_boats': 2, 'points_per_boat': 100},
        {'num_boats': 1, 'points_per_boat': 200},
        {'num_boats': 3, 'points_per_boat': 100},  # 大規模データ
    ]
    
    # ベンチマーク実行
    results = benchmark_wind_field_fusion(test_configs)
    
    # 結果の可視化
    plot_benchmark_results(results)
    
    print("\n✅ ベンチマーク完了！結果は以下のファイルに保存されました:")
    print(f"  - {os.path.join(project_root, 'benchmark_results.csv')}")
    print(f"  - {os.path.join(project_root, 'benchmark_results.png')}")
    print(f"  - {os.path.join(project_root, 'benchmark_scaling.png')}")

if __name__ == "__main__":
    main()
