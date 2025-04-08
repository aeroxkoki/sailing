#!/usr/bin/env python3
"""
データ処理パイプラインのパフォーマンスベンチマーク

このスクリプトは各モジュールの処理速度とメモリ使用量を測定し、
最適化のためのボトルネックを特定します。
"""

import os
import sys
import time
import tracemalloc
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import json

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_memory_usage():
    """現在のプロセスのメモリ使用量を取得（MB単位）"""
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024), peak / (1024 * 1024)

def create_test_data(num_boats=2, points_per_boat=100, time_span_minutes=60, area_size=0.05):
    """ベンチマーク用のテストデータを生成"""
    
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

def benchmark_module(module_name, module_func, test_data, iterations=3):
    """モジュールのパフォーマンスをベンチマーク"""
    
    # 測定結果
    execution_times = []
    memory_usages = []
    
    print(f"\n{module_name}のベンチマーク:")
    
    for i in range(iterations):
        print(f"  イテレーション {i+1}/{iterations}...")
        
        # メモリトラッキング開始
        tracemalloc.start()
        
        # 実行時間計測開始
        start_time = time.time()
        
        # モジュール実行
        try:
            result = module_func(test_data)
            status = "成功"
        except Exception as e:
            print(f"  エラー: {e}")
            status = "失敗"
            result = None
        
        # 実行時間計測終了
        execution_time = time.time() - start_time
        
        # メモリ使用量計測
        current_mem, peak_mem = get_memory_usage()
        
        # トラッキング停止
        tracemalloc.stop()
        
        # 結果を記録
        execution_times.append(execution_time)
        memory_usages.append(peak_mem)
        
        print(f"  時間: {execution_time:.4f}秒, メモリ: {peak_mem:.2f}MB, ステータス: {status}")
        
    # 平均値を計算
    avg_time = sum(execution_times) / len(execution_times)
    avg_memory = sum(memory_usages) / len(memory_usages)
    
    print(f"  平均実行時間: {avg_time:.4f}秒")
    print(f"  平均メモリ使用量: {avg_memory:.2f}MB")
    
    return {
        'module': module_name,
        'avg_time': avg_time,
        'avg_memory': avg_memory,
        'times': execution_times,
        'memories': memory_usages,
        'success': status == "成功"
    }

def benchmark_wind_field_fusion_system(test_configs):
    """WindFieldFusionSystemのベンチマーク"""
    try:
        from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
        
        results = []
        
        for config in test_configs:
            num_boats = config.get('num_boats', 2)
            points_per_boat = config.get('points_per_boat', 100)
            time_span = config.get('time_span_minutes', 60)
            area_size = config.get('area_size', 0.05)
            
            print(f"\n=> 設定: {num_boats}艇 x {points_per_boat}ポイント")
            
            # テストデータを生成
            test_data = create_test_data(
                num_boats=num_boats,
                points_per_boat=points_per_boat,
                time_span_minutes=time_span,
                area_size=area_size
            )
            
            # 関数を定義
            def run_fusion(data):
                system = WindFieldFusionSystem()
                return system.update_with_boat_data(data)
            
            # ベンチマーク実行
            result = benchmark_module(
                module_name=f"WindFieldFusionSystem ({num_boats}艇x{points_per_boat}点)",
                module_func=run_fusion,
                test_data=test_data,
                iterations=3
            )
            
            # 設定情報を追加
            result['config'] = {
                'num_boats': num_boats,
                'points_per_boat': points_per_boat,
                'time_span_minutes': time_span,
                'area_size': area_size
            }
            
            results.append(result)
        
        return results
            
    except ImportError as e:
        print(f"モジュールのインポートエラー: {e}")
        return []

def benchmark_strategy_detector(test_configs):
    """StrategyDetectorWithPropagationのベンチマーク"""
    try:
        from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
        from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
        
        results = []
        
        # 基準位置
        base_lat = 35.45
        base_lon = 139.65
        
        for config in test_configs:
            num_legs = config.get('num_legs', 2)
            points_per_leg = config.get('points_per_leg', 50)
            
            print(f"\n=> 設定: {num_legs}レグ x {points_per_leg}ポイント")
            
            # コースデータを生成
            course_data = {
                'start_time': datetime.now(),
                'legs': []
            }
            
            for leg_idx in range(num_legs):
                # レグデータ
                start_lat = base_lat + leg_idx * 0.01
                start_lon = base_lon
                end_lat = base_lat + (leg_idx + 1) * 0.01
                end_lon = base_lon + 0.01
                
                # パスポイント
                path_points = []
                for i in range(points_per_leg):
                    # 線形補間で中間点を生成
                    ratio = i / (points_per_leg - 1)
                    lat = start_lat + ratio * (end_lat - start_lat)
                    lon = start_lon + ratio * (end_lon - start_lon)
                    
                    point = {
                        'lat': lat,
                        'lon': lon,
                        'time': course_data['start_time'] + timedelta(minutes=leg_idx*10 + i),
                        'course': 45 if leg_idx % 2 == 0 else 225
                    }
                    path_points.append(point)
                
                # レグ情報
                leg = {
                    'leg_number': leg_idx + 1,
                    'is_upwind': leg_idx % 2 == 0,
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
                
                course_data['legs'].append(leg)
            
            # 風の場データを生成
            wind_field = {
                'lat_grid': np.linspace(base_lat - 0.01, base_lat + 0.11, 20),
                'lon_grid': np.linspace(base_lon - 0.01, base_lon + 0.11, 20),
                'wind_direction': np.ones((20, 20)) * 90,
                'wind_speed': np.ones((20, 20)) * 10,
                'confidence': np.ones((20, 20)) * 0.8,
                'time': datetime.now()
            }
            
            # 関数を定義
            def run_detector(data):
                # dataは無視して先に生成したデータを使用
                detector = StrategyDetectorWithPropagation(
                    wind_fusion_system=WindFieldFusionSystem()
                )
                shifts = detector.detect_wind_shifts_with_propagation(course_data, wind_field)
                return shifts
            
            # ベンチマーク実行
            result = benchmark_module(
                module_name=f"StrategyDetector ({num_legs}レグx{points_per_leg}点)",
                module_func=run_detector,
                test_data={},  # ダミーデータ
                iterations=3
            )
            
            # 設定情報を追加
            result['config'] = {
                'num_legs': num_legs,
                'points_per_leg': points_per_leg
            }
            
            results.append(result)
        
        return results
            
    except ImportError as e:
        print(f"モジュールのインポートエラー: {e}")
        return []

def benchmark_anomaly_detector(test_configs):
    """AnomalyDetectorのベンチマーク"""
    try:
        from sailing_data_processor.utilities.gps_anomaly_detector import AnomalyDetector, process_gps_data
        
        results = []
        
        for config in test_configs:
            data_size = config.get('data_size', 1000)
            anomaly_ratio = config.get('anomaly_ratio', 0.05)
            anomaly_count = int(data_size * anomaly_ratio)
            
            print(f"\n=> 設定: {data_size}ポイント (異常値約{anomaly_count}個)")
            
            # テストデータ生成
            base_lat = 35.45
            base_lon = 139.65
            start_time = datetime.now()
            
            # 基本的なGPSトラック（滑らかな曲線）
            latitudes = [base_lat + 0.001 * i + 0.0001 * np.sin(i * 0.1) for i in range(data_size)]
            longitudes = [base_lon + 0.001 * i + 0.0001 * np.cos(i * 0.2) for i in range(data_size)]
            timestamps = [start_time + timedelta(seconds=i * 5) for i in range(data_size)]
            
            # ランダムな異常値を追加
            for _ in range(anomaly_count):
                idx = np.random.randint(1, data_size - 1)
                anomaly_type = np.random.choice(['position', 'time'])
                
                if anomaly_type == 'position':
                    # 位置の異常値
                    latitudes[idx] += np.random.choice([-1, 1]) * 0.01
                    longitudes[idx] += np.random.choice([-1, 1]) * 0.01
                else:
                    # 時間の異常値
                    timestamps[idx] = timestamps[idx - 1] + timedelta(seconds=60)
            
            # DataFrameを作成
            test_df = pd.DataFrame({
                'latitude': latitudes,
                'longitude': longitudes,
                'timestamp': timestamps
            })
            
            # 関数を定義
            def run_anomaly_detection(df):
                detector = AnomalyDetector()
                methods = ['z_score', 'speed', 'acceleration', 'distance', 'time_gap']
                detected_df = detector.detect_anomalies(df, methods)
                corrected_df = detector.correct_anomalies(detected_df, 'linear')
                return corrected_df
            
            # ベンチマーク実行
            result = benchmark_module(
                module_name=f"AnomalyDetector ({data_size}ポイント)",
                module_func=run_anomaly_detection,
                test_data=test_df,
                iterations=3
            )
            
            # 設定情報を追加
            result['config'] = {
                'data_size': data_size,
                'anomaly_ratio': anomaly_ratio,
                'anomaly_count': anomaly_count
            }
            
            results.append(result)
        
        return results
            
    except ImportError as e:
        print(f"モジュールのインポートエラー: {e}")
        return []

def plot_benchmark_results(results, title, filename_prefix):
    """ベンチマーク結果をプロット"""
    if not results:
        print(f"{title}の結果がありません。プロットをスキップします。")
        return
    
    # データの整形
    configs = []
    avg_times = []
    avg_memories = []
    
    for result in results:
        module_name = result['module']
        configs.append(module_name)
        avg_times.append(result['avg_time'])
        avg_memories.append(result['avg_memory'])
    
    # 2つのサブプロットを作成
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # 実行時間のプロット
    ax1.bar(configs, avg_times, color='blue', alpha=0.7)
    ax1.set_title('実行時間の比較')
    ax1.set_ylabel('平均実行時間（秒）')
    ax1.set_xticks(range(len(configs)))
    ax1.set_xticklabels(configs, rotation=45, ha='right')
    
    # メモリ使用量のプロット
    ax2.bar(configs, avg_memories, color='green', alpha=0.7)
    ax2.set_title('メモリ使用量の比較')
    ax2.set_ylabel('平均メモリ使用量（MB）')
    ax2.set_xticks(range(len(configs)))
    ax2.set_xticklabels(configs, rotation=45, ha='right')
    
    # レイアウト調整
    plt.suptitle(title)
    plt.tight_layout()
    
    # プロット保存
    plt.savefig(f"{filename_prefix}_benchmark.png")
    print(f"プロットを保存しました: {filename_prefix}_benchmark.png")

def main():
    """メイン関数"""
    print("パフォーマンスベンチマークを実行します...")
    
    # 結果の保存ディレクトリ
    os.makedirs("benchmark_results", exist_ok=True)
    
    # 風の場融合システムのベンチマーク
    wind_field_configs = [
        {'num_boats': 1, 'points_per_boat': 50},
        {'num_boats': 2, 'points_per_boat': 50},
        {'num_boats': 1, 'points_per_boat': 100},
        {'num_boats': 2, 'points_per_boat': 100}
    ]
    
    wind_field_results = benchmark_wind_field_fusion_system(wind_field_configs)
    
    # 結果をJSONで保存
    with open("benchmark_results/wind_field_benchmark.json", "w") as f:
        json.dump(wind_field_results, f, indent=2)
    
    # 結果をプロット
    plot_benchmark_results(
        wind_field_results, 
        "風の場融合システムのパフォーマンス", 
        "benchmark_results/wind_field"
    )
    
    # 戦略検出器のベンチマーク
    strategy_configs = [
        {'num_legs': 1, 'points_per_leg': 50},
        {'num_legs': 2, 'points_per_leg': 50},
        {'num_legs': 1, 'points_per_leg': 100},
        {'num_legs': 2, 'points_per_leg': 100}
    ]
    
    strategy_results = benchmark_strategy_detector(strategy_configs)
    
    # 結果をJSONで保存
    with open("benchmark_results/strategy_benchmark.json", "w") as f:
        json.dump(strategy_results, f, indent=2)
    
    # 結果をプロット
    plot_benchmark_results(
        strategy_results, 
        "戦略検出器のパフォーマンス", 
        "benchmark_results/strategy"
    )
    
    # 異常値検出器のベンチマーク
    anomaly_configs = [
        {'data_size': 100, 'anomaly_ratio': 0.05},
        {'data_size': 500, 'anomaly_ratio': 0.05},
        {'data_size': 1000, 'anomaly_ratio': 0.05},
        {'data_size': 5000, 'anomaly_ratio': 0.05}
    ]
    
    anomaly_results = benchmark_anomaly_detector(anomaly_configs)
    
    # 結果をJSONで保存
    with open("benchmark_results/anomaly_benchmark.json", "w") as f:
        json.dump(anomaly_results, f, indent=2)
    
    # 結果をプロット
    plot_benchmark_results(
        anomaly_results, 
        "異常値検出器のパフォーマンス", 
        "benchmark_results/anomaly"
    )
    
    print("\n✅ パフォーマンスベンチマークが完了しました！")

if __name__ == "__main__":
    main()
