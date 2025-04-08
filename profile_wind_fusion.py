#!/usr/bin/env python3
"""
WindFieldFusionSystemのメモリ使用量と実行時間のプロファイリング

このスクリプトは、WindFieldFusionSystemのメモリ使用量と実行時間をプロファイリングし、
最適化すべきボトルネックを特定します。
"""

import os
import sys
import time
import cProfile
import pstats
import io
import tracemalloc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
except ImportError as e:
    print(f"インポートエラー: {e}")
    sys.exit(1)

def create_test_data(num_boats=3, points_per_boat=100, time_span_minutes=60, area_size=0.05):
    """大規模なテストデータを生成"""
    
    # 基準位置
    base_lat = 35.45
    base_lon = 139.65
    
    # 開始時間
    start_time = datetime.now()
    
    # 各ボートのデータを生成
    boats_data = {}
    
    for boat_id in range(num_boats):
        # ボートの初期位置をランダムに設定（基準位置の周辺）
        boat_base_lat = base_lat + np.random.uniform(-area_size/2, area_size/2)
        boat_base_lon = base_lon + np.random.uniform(-area_size/2, area_size/2)
        
        # 時間列
        timestamps = [start_time + timedelta(minutes=(time_span_minutes/points_per_boat)*i) for i in range(points_per_boat)]
        
        # ボートの動きをシミュレート（滑らかな曲線）
        angle_increment = 2 * np.pi / points_per_boat
        radius = area_size / 4
        
        latitudes = []
        longitudes = []
        wind_directions = []
        wind_speeds = []
        
        for i in range(points_per_boat):
            # 円周上の位置
            angle = angle_increment * i
            latitudes.append(boat_base_lat + radius * np.sin(angle))
            longitudes.append(boat_base_lon + radius * np.cos(angle))
            
            # 風向と風速（少しずつ変化させる）
            wind_directions.append(90 + 5 * np.sin(angle * 2))
            wind_speeds.append(10 + 2 * np.cos(angle * 3))
        
        # DataFrameを作成
        boats_data[f"boat{boat_id+1}"] = pd.DataFrame({
            'timestamp': timestamps,
            'latitude': latitudes,
            'longitude': longitudes,
            'wind_direction': wind_directions,
            'wind_speed_knots': wind_speeds
        })
    
    return boats_data

def profile_memory(func, *args, **kwargs):
    """関数のメモリ使用量をプロファイリング"""
    tracemalloc.start()
    
    result = func(*args, **kwargs)
    
    # スナップショットを取得
    snapshot = tracemalloc.take_snapshot()
    
    current, peak = tracemalloc.get_traced_memory()
    
    print(f"現在のメモリ使用量: {current / (1024 * 1024):.2f} MB")
    print(f"ピークメモリ使用量: {peak / (1024 * 1024):.2f} MB")
    
    # トップ10のメモリ使用箇所を表示
    top_stats = snapshot.statistics('lineno')
    
    print("\nメモリ使用量トップ10:")
    for stat in top_stats[:10]:
        print(f"{stat.count} blocks: {stat.size / 1024:.1f} KB")
        print(f"  {stat.traceback.format()[0]}")
    
    tracemalloc.stop()
    
    return result

def profile_time(func, *args, **kwargs):
    """関数の実行時間をプロファイリング"""
    pr = cProfile.Profile()
    pr.enable()
    
    result = func(*args, **kwargs)
    
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # トップ20の時間がかかっている関数を表示
    print("\n実行時間プロファイル:")
    print(s.getvalue())
    
    return result

def test_wind_field_fusion():
    """WindFieldFusionSystemのテスト"""
    system = WindFieldFusionSystem()
    
    # 小規模データのテスト
    small_data = create_test_data(num_boats=1, points_per_boat=50)
    print("\n== 小規模データのテスト (1艇x50点) ==")
    profile_memory(system.update_with_boat_data, small_data)
    
    # システムをリセット
    system = WindFieldFusionSystem()
    
    # 中規模データのテスト
    medium_data = create_test_data(num_boats=2, points_per_boat=100)
    print("\n== 中規模データのテスト (2艇x100点) ==")
    profile_time(system.update_with_boat_data, medium_data)
    
    # システムをリセット
    system = WindFieldFusionSystem()
    
    # 大規模データのテスト
    large_data = create_test_data(num_boats=5, points_per_boat=200)
    print("\n== 大規模データのテスト (5艇x200点) ==")
    start_time = time.time()
    result = system.update_with_boat_data(large_data)
    execution_time = time.time() - start_time
    print(f"実行時間: {execution_time:.4f}秒")
    
    # 予測テスト
    if result:
        print("\n== 風の場予測テスト ==")
        future_time = datetime.now() + timedelta(minutes=15)
        start_time = time.time()
        prediction = system.predict_wind_field(future_time)
        predict_time = time.time() - start_time
        print(f"予測実行時間: {predict_time:.4f}秒")
        
        if prediction:
            print("予測成功")
            print(f"グリッドサイズ: {prediction['lat_grid'].shape}")
        else:
            print("予測失敗")
    
def analyze_memory_allocation():
    """メソッド別のメモリ割り当てを分析"""
    system = WindFieldFusionSystem()
    
    # テスト用データ
    test_data = create_test_data(num_boats=2, points_per_boat=100)
    
    # 個別のメソッドをプロファイリング
    print("\n== メソッド別のメモリ割り当て分析 ==")
    
    # add_wind_data_pointのテスト
    point = {
        'timestamp': datetime.now(),
        'latitude': 35.45,
        'longitude': 139.65,
        'wind_direction': 90,
        'wind_speed': 10
    }
    
    print("\n-- add_wind_data_point --")
    tracemalloc.start()
    for _ in range(100):  # 100回呼び出し
        system.add_wind_data_point(point.copy())
    snapshot = tracemalloc.take_snapshot()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"100回の呼び出しでのピークメモリ: {peak / (1024 * 1024):.2f} MB")
    
    # システムをリセット
    system = WindFieldFusionSystem()
    
    # fuse_wind_dataのテスト
    # まずデータポイントを追加
    for boat_id, boat_df in test_data.items():
        for _, row in boat_df.iterrows():
            point = {
                'timestamp': row['timestamp'],
                'latitude': row['latitude'],
                'longitude': row['longitude'],
                'wind_direction': row['wind_direction'],
                'wind_speed': row['wind_speed_knots'] * 0.51444
            }
            system.wind_data_points.append(point)
    
    print("\n-- fuse_wind_data --")
    tracemalloc.start()
    system.fuse_wind_data()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print(f"ピークメモリ: {peak / (1024 * 1024):.2f} MB")
    
    # predict_wind_fieldのテスト
    if system.current_wind_field:
        print("\n-- predict_wind_field --")
        future_time = datetime.now() + timedelta(minutes=15)
        tracemalloc.start()
        system.predict_wind_field(future_time)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"ピークメモリ: {peak / (1024 * 1024):.2f} MB")

def profile_different_data_sizes():
    """異なるデータサイズでのパフォーマンスをプロファイリング"""
    # 異なるサイズのデータでテスト
    sizes = [
        (1, 50),    # 小
        (2, 100),   # 中
        (3, 150),   # 中大
        (5, 200),   # 大
        (10, 300)   # 超大
    ]
    
    execution_times = []
    memory_usages = []
    data_points = []
    
    print("\n== 異なるデータサイズでのパフォーマンス比較 ==")
    
    for boats, points in sizes:
        total_points = boats * points
        data_points.append(total_points)
        
        # データ作成
        test_data = create_test_data(num_boats=boats, points_per_boat=points)
        
        # システム初期化
        system = WindFieldFusionSystem()
        
        # 時間測定
        start_time = time.time()
        system.update_with_boat_data(test_data)
        execution_time = time.time() - start_time
        execution_times.append(execution_time)
        
        # メモリ測定
        tracemalloc.start()
        system = WindFieldFusionSystem()
        system.update_with_boat_data(test_data)
        # スナップショットを取得
        snapshot = tracemalloc.take_snapshot()
        _, peak = tracemalloc.get_traced_memory()
        memory_usages.append(peak / (1024 * 1024))  # MB単位
        tracemalloc.stop()
        
        print(f"データサイズ: {boats}艇 x {points}点 = {total_points}点")
        print(f"  実行時間: {execution_time:.4f}秒")
        print(f"  ピークメモリ: {peak / (1024 * 1024):.2f} MB")
    
    # グラフ作成
    plt.figure(figsize=(12, 5))
    
    # 実行時間グラフ
    plt.subplot(1, 2, 1)
    plt.plot(data_points, execution_times, 'o-', color='blue')
    plt.title('データサイズと実行時間の関係')
    plt.xlabel('データポイント数')
    plt.ylabel('実行時間 (秒)')
    plt.grid(True)
    
    # メモリ使用量グラフ
    plt.subplot(1, 2, 2)
    plt.plot(data_points, memory_usages, 'o-', color='green')
    plt.title('データサイズとメモリ使用量の関係')
    plt.xlabel('データポイント数')
    plt.ylabel('ピークメモリ使用量 (MB)')
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('wind_fusion_profiling.png')
    print(f"プロファイリンググラフを保存しました: wind_fusion_profiling.png")

if __name__ == "__main__":
    print("WindFieldFusionSystemのプロファイリングを開始します...")
    
    try:
        # 基本テスト
        test_wind_field_fusion()
        
        # メモリ割り当て分析
        analyze_memory_allocation()
        
        # データサイズ変化のテスト
        profile_different_data_sizes()
        
        print("\nプロファイリングが完了しました")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
