#!/usr/bin/env python3
"""
最適化された風の場融合システムと戦略検出器のテスト・ベンチマークスクリプト

このスクリプトは最適化されたモジュールの機能検証とパフォーマンス測定を行います。
"""

import os
import sys
import time
import tracemalloc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json

# プロジェクトルートをPythonパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# テスト対象のモジュールをインポート
try:
    # オリジナルクラス
    from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
    from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
    from sailing_data_processor.optimal_vmg_calculator import OptimalVMGCalculator
    
    # 最適化クラス
    from sailing_data_processor.optimized_wind_field_fusion_system import OptimizedWindFieldFusionSystem
    from sailing_data_processor.strategy.optimized_strategy_detector import OptimizedStrategyDetector
    
    # データ生成ヘルパー
    from standalone_tests.wind_field_performance_benchmark import generate_test_data
    from standalone_tests.strategy_detector_performance_benchmark import generate_test_course_data, generate_test_wind_field
    
except ImportError as e:
    print(f"インポートエラー: {e}")
    print(f"現在のシステムパス: {sys.path}")
    sys.exit(1)

def get_current_memory_usage():
    """
    現在のメモリ使用量を取得（MB単位）
    
    Returns:
    --------
    float
        メモリ使用量（MB）
    """
    _, current = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)  # バイトからMBに変換

def check_wind_field_accuracy(original_field, optimized_field):
    """
    風の場データの精度を基本的に検証する関数
    
    Parameters:
    -----------
    original_field : Dict
        オリジナル版の風の場
    optimized_field : Dict
        最適化版の風の場
    """
    # 両方の風の場が生成されたかチェック
    if not original_field or not optimized_field:
        print("    ⚠ いずれかの風の場が生成されませんでした")
        return
    
    # 格子サイズのチェック
    if original_field['lat_grid'].shape != optimized_field['lat_grid'].shape:
        print(f"    ⚠ 格子サイズが異なります: " 
              f"オリジナル {original_field['lat_grid'].shape} vs "
              f"最適化版 {optimized_field['lat_grid'].shape}")
    
    # 風向の平均値の差をチェック
    orig_dir_avg = np.mean(original_field['wind_direction'])
    opt_dir_avg = np.mean(optimized_field['wind_direction'])
    
    dir_diff = abs(orig_dir_avg - opt_dir_avg)
    if dir_diff > 10:
        print(f"    ⚠ 風向平均値の差が大きいです: {dir_diff:.2f}度")
    else:
        print(f"    ✓ 風向平均値の差: {dir_diff:.2f}度")
    
    # 風速の平均値の差をチェック
    orig_speed_avg = np.mean(original_field['wind_speed'])
    opt_speed_avg = np.mean(optimized_field['wind_speed'])
    
    speed_diff = abs(orig_speed_avg - opt_speed_avg)
    if speed_diff > 2:
        print(f"    ⚠ 風速平均値の差が大きいです: {speed_diff:.2f}")
    else:
        print(f"    ✓ 風速平均値の差: {speed_diff:.2f}")

def compare_wind_fusion_systems(test_data_configs, iterations=2, save_results=True):
    """
    風の場融合システムの最適化版と従来版を比較する関数
    
    Parameters:
    -----------
    test_data_configs : List[Dict]
        テストデータ設定のリスト
    iterations : int
        各設定での反復回数
    save_results : bool
        結果をファイルに保存するかどうか
        
    Returns:
    --------
    Dict
        比較結果
    """
    print("\n===== 風の場融合システム 比較テスト =====\n")
    
    # 結果格納用
    results = {
        'config': [],
        'original_time': [],
        'optimized_time': [],
        'speedup': [],
        'original_memory': [],
        'optimized_memory': [],
        'memory_reduction': []
    }
    
    for config in test_data_configs:
        num_boats = config.get('num_boats', 2)
        points_per_boat = config.get('points_per_boat', 100)
        config_name = f"{num_boats}艇x{points_per_boat}ポイント"
        
        print(f"\n▶ 設定: {config_name}")
        
        # 各テスト設定に対して実行
        orig_times = []
        opt_times = []
        orig_memory = []
        opt_memory = []
        
        for i in range(iterations):
            print(f"  イテレーション {i+1}/{iterations}")
            
            # テストデータ生成
            boats_data = generate_test_data(
                num_boats=num_boats,
                points_per_boat=points_per_boat,
                time_span_minutes=config.get('time_span_minutes', 60),
                area_size=config.get('area_size', 0.05)
            )
            
            # === オリジナル版テスト ===
            # メモリ計測開始
            tracemalloc.start()
            start_memory = get_current_memory_usage()
            
            # 処理時間計測開始
            start_time = time.time()
            
            # 風の場融合システムの初期化と実行
            original_system = WindFieldFusionSystem()
            original_field = original_system.update_with_boat_data(boats_data)
            
            # 予測処理も実行
            future_time = datetime.now() + timedelta(minutes=15)
            original_prediction = original_system.predict_wind_field(future_time)
            
            # 処理時間記録
            orig_time = time.time() - start_time
            orig_times.append(orig_time)
            
            # メモリ使用量記録
            end_memory = get_current_memory_usage()
            orig_memory.append(end_memory - start_memory)
            
            # メモリ計測終了
            tracemalloc.stop()
            
            
            # === 最適化版テスト ===
            # メモリ計測開始
            tracemalloc.start()
            start_memory = get_current_memory_usage()
            
            # 処理時間計測開始
            start_time = time.time()
            
            # 最適化された風の場融合システムの初期化と実行
            optimized_system = OptimizedWindFieldFusionSystem(
                max_points_per_fusion=config.get('max_points', 1000)
            )
            optimized_field = optimized_system.update_with_boat_data(boats_data)
            
            # 予測処理も実行
            future_time = datetime.now() + timedelta(minutes=15)
            optimized_prediction = optimized_system.predict_wind_field(future_time)
            
            # 処理時間記録
            opt_time = time.time() - start_time
            opt_times.append(opt_time)
            
            # メモリ使用量記録
            end_memory = get_current_memory_usage()
            opt_memory.append(end_memory - start_memory)
            
            # メモリ計測終了
            tracemalloc.stop()
            
            # 結果出力
            print(f"    オリジナル版: {orig_time:.4f}秒, {orig_memory[-1]:.2f}MB")
            print(f"    最適化版: {opt_time:.4f}秒, {opt_memory[-1]:.2f}MB")
            
            # 基本的な正確性チェック
            if original_field and optimized_field:
                check_wind_field_accuracy(original_field, optimized_field)
        
        # 平均値を計算
        avg_orig_time = sum(orig_times) / len(orig_times) if orig_times else 0
        avg_opt_time = sum(opt_times) / len(opt_times) if opt_times else 0
        avg_orig_memory = sum(orig_memory) / len(orig_memory) if orig_memory else 0
        avg_opt_memory = sum(opt_memory) / len(opt_memory) if opt_memory else 0
        
        # 高速化率とメモリ削減率
        speedup = avg_orig_time / max(0.001, avg_opt_time)
        memory_reduction = 1.0 - (avg_opt_memory / max(0.001, avg_orig_memory))
        
        # 結果を記録
        results['config'].append(config_name)
        results['original_time'].append(avg_orig_time)
        results['optimized_time'].append(avg_opt_time)
        results['speedup'].append(speedup)
        results['original_memory'].append(avg_orig_memory)
        results['optimized_memory'].append(avg_opt_memory)
        results['memory_reduction'].append(memory_reduction)
        
        # 結果要約を表示
        print(f"  ✓ 平均処理時間: {avg_orig_time:.4f}秒 → {avg_opt_time:.4f}秒 (速度向上: {speedup:.2f}倍)")
        print(f"  ✓ 平均メモリ使用量: {avg_orig_memory:.2f}MB → {avg_opt_memory:.2f}MB (削減率: {memory_reduction*100:.1f}%)")
    
    # 結果を保存
    if save_results:
        # DataFrame作成
        df = pd.DataFrame(results)
        
        # CSVファイルとして保存
        csv_path = os.path.join(project_root, 'wind_fusion_comparison.csv')
        df.to_csv(csv_path, index=False)
        
        # 結果をプロット
        plot_comparison_results(results, 'wind_fusion')
        
        print(f"\n結果を保存しました: {csv_path}")
    
    return results

def compare_strategy_detectors(test_data_configs, iterations=2, save_results=True):
    """
    戦略検出器の最適化版と従来版を比較する関数
    
    Parameters:
    -----------
    test_data_configs : List[Dict]
        テストデータ設定のリスト
    iterations : int
        各設定での反復回数
    save_results : bool
        結果をファイルに保存するかどうか
        
    Returns:
    --------
    Dict
        比較結果
    """
    print("\n===== 戦略検出器 比較テスト =====\n")
    
    # 結果格納用
    results = {
        'config': [],
        'original_time': [],
        'optimized_time': [],
        'speedup': [],
        'original_memory': [],
        'optimized_memory': [],
        'memory_reduction': []
    }
    
    # VMG計算機と風統合システム（共通で使用）
    vmg_calculator = OptimalVMGCalculator()
    wind_fusion_system = OptimizedWindFieldFusionSystem()
    
    for config in test_data_configs:
        num_legs = config.get('num_legs', 2)
        points_per_leg = config.get('points_per_leg', 50)
        config_name = f"{num_legs}レグx{points_per_leg}ポイント"
        
        print(f"\n▶ 設定: {config_name}")
        
        # 各テスト設定に対して実行
        orig_times = []
        opt_times = []
        orig_memory = []
        opt_memory = []
        
        for i in range(iterations):
            print(f"  イテレーション {i+1}/{iterations}")
            
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
            
            # === オリジナル版テスト ===
            # メモリ計測開始
            tracemalloc.start()
            start_memory = get_current_memory_usage()
            
            # 処理時間計測開始
            start_time = time.time()
            
            # 戦略検出器の初期化
            original_detector = StrategyDetectorWithPropagation(
                vmg_calculator=vmg_calculator,
                wind_fusion_system=wind_fusion_system
            )
            
            # 風向シフト検出
            original_shifts = original_detector.detect_wind_shifts_with_propagation(
                course_data, wind_field
            )
            
            # タックポイント検出
            original_tacks = original_detector.detect_optimal_tacks_with_forecast(
                course_data, wind_field
            )
            
            # レイライン検出
            original_laylines = original_detector.detect_laylines(
                course_data, wind_field
            )
            
            # 処理時間記録
            orig_time = time.time() - start_time
            orig_times.append(orig_time)
            
            # メモリ使用量記録
            end_memory = get_current_memory_usage()
            orig_memory.append(end_memory - start_memory)
            
            # メモリ計測終了
            tracemalloc.stop()
            
            # === 最適化版テスト ===
            # メモリ計測開始
            tracemalloc.start()
            start_memory = get_current_memory_usage()
            
            # 処理時間計測開始
            start_time = time.time()
            
            # 最適化された戦略検出器の初期化
            optimized_detector = OptimizedStrategyDetector(
                vmg_calculator=vmg_calculator,
                wind_fusion_system=wind_fusion_system
            )
            
            # 風向シフト検出
            optimized_shifts = optimized_detector.detect_wind_shifts_with_propagation(
                course_data, wind_field
            )
            
            # タックポイント検出
            optimized_tacks = optimized_detector.detect_optimal_tacks_with_forecast(
                course_data, wind_field
            )
            
            # レイライン検出
            optimized_laylines = optimized_detector.detect_laylines(
                course_data, wind_field
            )
            
            # 処理時間記録
            opt_time = time.time() - start_time
            opt_times.append(opt_time)
            
            # メモリ使用量記録
            end_memory = get_current_memory_usage()
            opt_memory.append(end_memory - start_memory)
            
            # メモリ計測終了
            tracemalloc.stop()
            
            # 結果出力
            print(f"    オリジナル版: {orig_time:.4f}秒, {orig_memory[-1]:.2f}MB")
            print(f"      - 風向シフト: {len(original_shifts)}個")
            print(f"      - タックポイント: {len(original_tacks)}個")
            print(f"      - レイライン: {len(original_laylines)}個")
            
            print(f"    最適化版: {opt_time:.4f}秒, {opt_memory[-1]:.2f}MB")
            print(f"      - 風向シフト: {len(optimized_shifts)}個")
            print(f"      - タックポイント: {len(optimized_tacks)}個")
            print(f"      - レイライン: {len(optimized_laylines)}個")
            
            # キャッシュをクリア
            optimized_detector.clear_caches()
        
        # 平均値を計算
        avg_orig_time = sum(orig_times) / len(orig_times) if orig_times else 0
        avg_opt_time = sum(opt_times) / len(opt_times) if opt_times else 0
        avg_orig_memory = sum(orig_memory) / len(orig_memory) if orig_memory else 0
        avg_opt_memory = sum(opt_memory) / len(opt_memory) if opt_memory else 0
        
        # 高速化率とメモリ削減率
        speedup = avg_orig_time / max(0.001, avg_opt_time)
        memory_reduction = 1.0 - (avg_opt_memory / max(0.001, avg_orig_memory))
        
        # 結果を記録
        results['config'].append(config_name)
        results['original_time'].append(avg_orig_time)
        results['optimized_time'].append(avg_opt_time)
        results['speedup'].append(speedup)
        results['original_memory'].append(avg_orig_memory)
        results['optimized_memory'].append(avg_opt_memory)
        results['memory_reduction'].append(memory_reduction)
        
        # 結果要約を表示
        print(f"  ✓ 平均処理時間: {avg_orig_time:.4f}秒 → {avg_opt_time:.4f}秒 (速度向上: {speedup:.2f}倍)")
        print(f"  ✓ 平均メモリ使用量: {avg_orig_memory:.2f}MB → {avg_opt_memory:.2f}MB (削減率: {memory_reduction*100:.1f}%)")
    
    # 結果を保存
    if save_results:
        # DataFrame作成
        df = pd.DataFrame(results)
        
        # CSVファイルとして保存
        csv_path = os.path.join(project_root, 'strategy_detector_comparison.csv')
        df.to_csv(csv_path, index=False)
        
        # 結果をプロット
        plot_comparison_results(results, 'strategy_detector')
        
        print(f"\n結果を保存しました: {csv_path}")
    
    return results

def plot_comparison_results(results, module_name):
    """
    比較結果をプロットする関数
    
    Parameters:
    -----------
    results : Dict
        比較結果
    module_name : str
        モジュール名（ファイル名に使用）
    """
    # プロット用データフレーム作成
    df = pd.DataFrame(results)
    
    # 実行時間比較プロット
    plt.figure(figsize=(14, 6))
    plt.subplot(1, 2, 1)
    
    x = np.arange(len(df['config']))
    width = 0.35
    
    rects1 = plt.bar(x - width/2, df['original_time'], width, label='オリジナル版')
    rects2 = plt.bar(x + width/2, df['optimized_time'], width, label='最適化版')
    
    plt.xlabel('データサイズ')
    plt.ylabel('平均処理時間（秒）')
    plt.title('処理時間比較')
    plt.xticks(x, df['config'], rotation=45)
    plt.legend()
    
    # 高速化率ラベルを追加
    for i, speed in enumerate(df['speedup']):
        plt.text(i, df['original_time'][i] * 0.5, f"{speed:.2f}倍", 
                 ha='center', va='center', color='white', fontweight='bold')
    
    # メモリ使用量比較プロット
    plt.subplot(1, 2, 2)
    
    rects3 = plt.bar(x - width/2, df['original_memory'], width, label='オリジナル版')
    rects4 = plt.bar(x + width/2, df['optimized_memory'], width, label='最適化版')
    
    plt.xlabel('データサイズ')
    plt.ylabel('平均メモリ使用量（MB）')
    plt.title('メモリ使用量比較')
    plt.xticks(x, df['config'], rotation=45)
    plt.legend()
    
    # メモリ削減率ラベルを追加
    for i, reduction in enumerate(df['memory_reduction']):
        plt.text(i, df['original_memory'][i] * 0.5, f"{reduction*100:.1f}%削減", 
                 ha='center', va='center', color='white', fontweight='bold')
    
    plt.tight_layout()
    
    # プロットを保存
    plt.savefig(os.path.join(project_root, f'{module_name}_comparison.png'))
    plt.close()

def main():
    """メイン関数"""
    print("最適化モジュールの比較ベンチマークを実行します...")
    
    # 風の場融合システムのテスト設定
    wind_fusion_configs = [
        {'num_boats': 1, 'points_per_boat': 50},
        {'num_boats': 2, 'points_per_boat': 50},
        {'num_boats': 1, 'points_per_boat': 100},
        {'num_boats': 2, 'points_per_boat': 100},
        {'num_boats': 3, 'points_per_boat': 100},  # 大規模データ
    ]
    
    # 戦略検出器のテスト設定
    strategy_detector_configs = [
        {'num_legs': 1, 'points_per_leg': 50},
        {'num_legs': 2, 'points_per_leg': 50},
        {'num_legs': 1, 'points_per_leg': 100},
        {'num_legs': 2, 'points_per_leg': 100}
    ]
    
    # 風の場融合システムの比較
    wind_fusion_results = compare_wind_fusion_systems(
        wind_fusion_configs, iterations=3, save_results=True
    )
    
    # 戦略検出器の比較
    strategy_detector_results = compare_strategy_detectors(
        strategy_detector_configs, iterations=3, save_results=True
    )
    
    print("\n✅ 比較ベンチマークが完了しました！")

if __name__ == "__main__":
    main()
