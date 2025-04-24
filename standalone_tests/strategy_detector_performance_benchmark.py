#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StrategyDetectorWithPropagation モジュールのパフォーマンスベンチマーク

このスクリプトは戦略検出器のパフォーマンスを測定し、
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
    from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    from sailing_data_processor.optimal_vmg_calculator import OptimalVMGCalculator
except ImportError as e:
    print(f"インポートエラー: {e}")
    print(f"現在のシステムパス: {sys.path}")
    sys.exit(1)

def generate_test_course_data(num_legs=2, points_per_leg=50, 
                             area_size=0.05, course_duration_minutes=60,
                             base_lat=35.45, base_lon=139.65):
    """
    テスト用のコースデータを生成する関数
    
    Parameters:
    -----------
    num_legs : int
        コースのレグ数
    points_per_leg : int
        各レグのパスポイント数
    area_size : float
        コース範囲の広さ（緯度・経度の度数）
    course_duration_minutes : int
        コース全体の所要時間（分）
    base_lat, base_lon : float
        基準となる位置
        
    Returns:
    --------
    Dict
        コースデータ
    """
    start_time = datetime.now()
    
    # コースデータの基本構造
    course_data = {
        'start_time': start_time,
        'legs': []
    }
    
    # 各レグを生成
    for leg_idx in range(num_legs):
        # レグの開始/終了ウェイポイント
        leg_progress = leg_idx / max(1, num_legs - 1)
        is_upwind = leg_idx % 2 == 0  # 偶数レグは風上
        
        # ウェイポイント座標を計算
        if is_upwind:
            # 風上レグ - 上に向かう
            start_lat = base_lat + leg_progress * area_size
            start_lon = base_lon
            end_lat = base_lat + (leg_progress + 0.5) * area_size
            end_lon = base_lon
        else:
            # 風下レグ - 下に向かう
            start_lat = base_lat + (leg_progress - 0.5) * area_size
            start_lon = base_lon + 0.2 * area_size
            end_lat = base_lat + leg_progress * area_size
            end_lon = base_lon + 0.2 * area_size
        
        # レグの開始終了時間
        leg_start_time = start_time + timedelta(minutes=leg_idx * course_duration_minutes / num_legs)
        leg_end_time = start_time + timedelta(minutes=(leg_idx + 1) * course_duration_minutes / num_legs)
        
        # パスポイントを生成
        path_points = []
        for i in range(points_per_leg):
            point_progress = i / max(1, points_per_leg - 1)
            
            # 位置を線形補間
            lat = start_lat + point_progress * (end_lat - start_lat)
            lon = start_lon + point_progress * (end_lon - start_lon)
            
            # 時間を線形補間
            point_time = leg_start_time + timedelta(
                seconds=point_progress * (leg_end_time - leg_start_time).total_seconds()
            )
            
            # コース方向
            course_angle = 0 if is_upwind else 180
            
            # パスポイントを追加
            path_points.append({
                'lat': lat,
                'lon': lon,
                'time': point_time,
                'course': course_angle + np.random.normal(0, 5)
            })
        
        # レグデータを追加
        leg_data = {
            'leg_number': leg_idx + 1,
            'is_upwind': is_upwind,
            'start_time': leg_start_time,
            'end_time': leg_end_time,
            'start_waypoint': {
                'lat': start_lat,
                'lon': start_lon,
                'name': f'Mark {leg_idx}'
            },
            'end_waypoint': {
                'lat': end_lat,
                'lon': end_lon,
                'name': f'Mark {leg_idx + 1}'
            },
            'path': {
                'path_points': path_points
            }
        }
        
        course_data['legs'].append(leg_data)
    
    return course_data

def generate_test_wind_field(grid_size=10, area_size=0.05, 
                            base_lat=35.45, base_lon=139.65):
    """
    テスト用の風の場データを生成する関数
    
    Parameters:
    -----------
    grid_size : int
        グリッドの解像度
    area_size : float
        範囲の広さ（緯度・経度の度数）
    base_lat, base_lon : float
        基準となる位置
        
    Returns:
    --------
    Dict
        風の場データ
    """
    # グリッドの生成
    lat_grid = np.linspace(base_lat, base_lat + area_size, grid_size)
    lon_grid = np.linspace(base_lon, base_lon + area_size, grid_size)
    grid_lats, grid_lons = np.meshgrid(lat_grid, lon_grid)
    
    # 風向・風速のパターンを生成
    # 基本的に一定の風向に小さな変動を加える
    base_wind_direction = 180  # 南風
    base_wind_speed = 10       # 10ノット
    
    # 風向のグリッド - 位置ごとに少し変動
    wind_direction = np.ones_like(grid_lats) * base_wind_direction
    for i in range(grid_size):
        for j in range(grid_size):
            # 位置によって風向に変動を加える
            position_factor = (i / grid_size + j / grid_size) / 2
            wind_direction[i, j] += position_factor * 20 - 10  # -10〜+10度の変動
    
    # 風速のグリッド - 位置ごとに少し変動
    wind_speed = np.ones_like(grid_lats) * base_wind_speed
    for i in range(grid_size):
        for j in range(grid_size):
            # 位置によって風速に変動を加える
            position_factor = (i / grid_size + j / grid_size) / 2
            wind_speed[i, j] += position_factor * 4 - 2  # -2〜+2ノットの変動
    
    # 信頼度のグリッド - 一定
    confidence = np.ones_like(grid_lats) * 0.8
    
    # 風の場データを作成
    wind_field = {
        'lat_grid': grid_lats,
        'lon_grid': grid_lons,
        'wind_direction': wind_direction,
        'wind_speed': wind_speed,
        'confidence': confidence,
        'time': datetime.now()
    }
    
    return wind_field

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

def benchmark_strategy_detector(test_data_configs, iterations=3):
    """
    戦略検出器のパフォーマンスをベンチマークする関数
    
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
        'num_legs': [],
        'points_per_leg': [],
        'total_points': [],
        'wind_shift_time': [],
        'tack_point_time': [],
        'layline_time': [],
        'total_time': [],
        'memory_usage': [],
        'success_rate': []
    }
    
    # VMG計算機とWindFieldFusionSystemを初期化（共通で使用）
    vmg_calculator = OptimalVMGCalculator()
    wind_fusion_system = WindFieldFusionSystem()
    
    for config in test_data_configs:
        num_legs = config.get('num_legs', 2)
        points_per_leg = config.get('points_per_leg', 50)
        config_name = f"{num_legs}レグx{points_per_leg}ポイント"
        
        print(f"\n▶ ベンチマーク実行: {config_name}")
        
        # 複数回実行して平均を取る
        wind_shift_times = []
        tack_point_times = []
        layline_times = []
        total_times = []
        memory_usages = []
        success_count = 0
        
        for i in range(iterations):
            # テストデータ生成
            course_data = generate_test_course_data(
                num_legs=num_legs,
                points_per_leg=points_per_leg,
                area_size=config.get('area_size', 0.05),
                course_duration_minutes=config.get('course_duration_minutes', 60)
            )
            
            wind_field = generate_test_wind_field(
                grid_size=config.get('grid_size', 10),
                area_size=config.get('area_size', 0.05)
            )
            
            # メモリトラッキング開始
            tracemalloc.start()
            start_memory = measure_memory_usage()
            
            # 戦略検出器の初期化
            strategy_detector = StrategyDetectorWithPropagation(
                vmg_calculator=vmg_calculator,
                wind_fusion_system=wind_fusion_system
            )
            
            try:
                # 風向シフト検出の時間測定
                start_time = time.time()
                wind_shifts = strategy_detector.detect_wind_shifts_with_propagation(
                    course_data, wind_field
                )
                wind_shift_time = time.time() - start_time
                wind_shift_times.append(wind_shift_time)
                
                # タックポイント検出の時間測定
                start_time = time.time()
                tack_points = strategy_detector.detect_optimal_tacks_with_forecast(
                    course_data, wind_field
                )
                tack_point_time = time.time() - start_time
                tack_point_times.append(tack_point_time)
                
                # レイライン検出の時間測定
                start_time = time.time()
                laylines = strategy_detector.detect_laylines(
                    course_data, wind_field
                )
                layline_time = time.time() - start_time
                layline_times.append(layline_time)
                
                # 合計時間
                total_time = wind_shift_time + tack_point_time + layline_time
                total_times.append(total_time)
                
                # メモリ使用量の記録
                end_memory = measure_memory_usage()
                memory_usages.append(end_memory - start_memory)
                
                # 結果の出力
                print(f"  イテレーション {i+1}/{iterations}:")
                print(f"    風向シフト検出: {wind_shift_time:.4f}秒, {len(wind_shifts)}件")
                print(f"    タックポイント検出: {tack_point_time:.4f}秒, {len(tack_points)}件")
                print(f"    レイライン検出: {layline_time:.4f}秒, {len(laylines)}件")
                print(f"    合計時間: {total_time:.4f}秒")
                print(f"    メモリ使用: {end_memory - start_memory:.2f}MB")
                
                # 処理成功
                success_count += 1
                
            except Exception as e:
                print(f"  エラー発生: {e}")
            
            # メモリトラッキング停止
            tracemalloc.stop()
        
        # 結果を記録
        avg_wind_shift_time = sum(wind_shift_times) / len(wind_shift_times) if wind_shift_times else 0
        avg_tack_point_time = sum(tack_point_times) / len(tack_point_times) if tack_point_times else 0
        avg_layline_time = sum(layline_times) / len(layline_times) if layline_times else 0
        avg_total_time = sum(total_times) / len(total_times) if total_times else 0
        avg_memory = sum(memory_usages) / len(memory_usages) if memory_usages else 0
        success_rate = success_count / iterations
        
        results['config'].append(config_name)
        results['num_legs'].append(num_legs)
        results['points_per_leg'].append(points_per_leg)
        results['total_points'].append(num_legs * points_per_leg)
        results['wind_shift_time'].append(avg_wind_shift_time)
        results['tack_point_time'].append(avg_tack_point_time)
        results['layline_time'].append(avg_layline_time)
        results['total_time'].append(avg_total_time)
        results['memory_usage'].append(avg_memory)
        results['success_rate'].append(success_rate)
        
        print(f"  ✓ 平均風向シフト検出時間: {avg_wind_shift_time:.4f}秒")
        print(f"  ✓ 平均タックポイント検出時間: {avg_tack_point_time:.4f}秒")
        print(f"  ✓ 平均レイライン検出時間: {avg_layline_time:.4f}秒")
        print(f"  ✓ 平均合計時間: {avg_total_time:.4f}秒")
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
    
    # 処理時間の内訳プロット
    plt.figure(figsize=(14, 6))
    plt.subplot(1, 2, 1)
    df_plot = pd.DataFrame({
        'Wind Shift': df['wind_shift_time'],
        'Tack Points': df['tack_point_time'],
        'Laylines': df['layline_time']
    }, index=df['config'])
    ax = df_plot.plot(kind='bar', stacked=True, figsize=(14, 6))
    plt.xlabel('データサイズ')
    plt.ylabel('平均処理時間（秒）')
    plt.title('戦略検出処理時間の内訳')
    plt.legend(title="処理種別")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # 合計値を表示
    for i, total in enumerate(df['total_time']):
        plt.text(i, total + 0.1, f"{total:.2f}秒", ha='center')
    
    # メモリ使用量プロット
    plt.subplot(1, 2, 2)
    plt.bar(df['config'], df['memory_usage'], color='orange')
    for i, v in enumerate(df['memory_usage']):
        plt.text(i, v + 0.5, f"{v:.1f}MB", ha='center')
    
    plt.xlabel('データサイズ')
    plt.ylabel('平均メモリ使用量（MB）')
    plt.title('データサイズ別メモリ使用量')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(project_root, 'strategy_benchmark_results.png'))
    plt.close()
    
    # ポイント数と時間の関係プロット
    plt.figure(figsize=(14, 6))
    
    plt.subplot(1, 2, 1)
    # 各処理の時間を積み上げプロット
    plt.scatter(df['total_points'], df['total_time'], s=80, alpha=0.7, label='合計時間')
    plt.scatter(df['total_points'], df['wind_shift_time'], s=60, alpha=0.7, label='風向シフト検出')
    plt.scatter(df['total_points'], df['tack_point_time'], s=60, alpha=0.7, label='タックポイント検出')
    plt.scatter(df['total_points'], df['layline_time'], s=60, alpha=0.7, label='レイライン検出')
    
    for i, row in df.iterrows():
        plt.annotate(row['config'], 
                  (row['total_points'], row['total_time']),
                  xytext=(5, 5), textcoords='offset points')
    
    plt.xlabel('総データポイント数')
    plt.ylabel('平均処理時間（秒）')
    plt.title('データポイント数と処理時間の関係')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.subplot(1, 2, 2)
    plt.scatter(df['total_points'], df['memory_usage'], s=80, alpha=0.7, color='orange')
    
    # メモリ使用量の近似曲線
    try:
        z = np.polyfit(df['total_points'], df['memory_usage'], 1)
        p = np.poly1d(z)
        x_range = np.linspace(min(df['total_points']), max(df['total_points']), 100)
        plt.plot(x_range, p(x_range), "r--", alpha=0.8, label=f"傾向線: {z[0]:.2f}x + {z[1]:.2f}")
    except:
        # データが少ない場合などにフィットできない場合はスキップ
        pass
    
    for i, row in df.iterrows():
        plt.annotate(row['config'], 
                  (row['total_points'], row['memory_usage']),
                  xytext=(5, 5), textcoords='offset points')
    
    plt.xlabel('総データポイント数')
    plt.ylabel('平均メモリ使用量（MB）')
    plt.title('データポイント数とメモリ使用量の関係')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(project_root, 'strategy_benchmark_scaling.png'))
    plt.close()
    
    # 結果を表形式でファイルに保存
    df.to_csv(os.path.join(project_root, 'strategy_benchmark_results.csv'), index=False)

def main():
    """メイン関数"""
    print("戦略検出器のパフォーマンスベンチマークを実行します...")
    
    # テスト設定
    test_configs = [
        {'num_legs': 1, 'points_per_leg': 50},
        {'num_legs': 2, 'points_per_leg': 50},
        {'num_legs': 1, 'points_per_leg': 100},
        {'num_legs': 2, 'points_per_leg': 100},
        {'num_legs': 3, 'points_per_leg': 50},
        {'num_legs': 1, 'points_per_leg': 200},
        {'num_legs': 4, 'points_per_leg': 100},  # 大規模データ
    ]
    
    # ベンチマーク実行
    results = benchmark_strategy_detector(test_configs)
    
    # 結果の可視化
    plot_benchmark_results(results)
    
    print("\n✅ ベンチマーク完了！結果は以下のファイルに保存されました:")
    print(f"  - {os.path.join(project_root, 'strategy_benchmark_results.csv')}")
    print(f"  - {os.path.join(project_root, 'strategy_benchmark_results.png')}")
    print(f"  - {os.path.join(project_root, 'strategy_benchmark_scaling.png')}")

if __name__ == "__main__":
    main()
