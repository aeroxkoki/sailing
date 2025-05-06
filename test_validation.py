#!/usr/bin/env python3
"""
セーリング戦略分析システム 検証モジュールテスト

quality_metricsモジュールの検証テストを実行します。
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# モジュールのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sailing_data_processor.validation.quality_metrics_improvements import QualityMetricsCalculator

def test_precision_and_validity_scores():
    """精度と妥当性スコア計算のテスト"""
    # 範囲外の値と時間的異常を含むサンプルデータを作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # 一部のデータに問題を作成
    data.loc[3, 'speed'] = 100.0  # 範囲外の速度
    data.loc[5, 'timestamp'] = data.loc[4, 'timestamp'] - timedelta(seconds=10)  # 時間逆行
    
    # バリデーション結果を手動で作成
    validation_results = [
        {
            'rule_name': 'Value Range Check',
            'is_valid': False,
            'severity': 'warning',
            'details': {
                'column': 'speed',
                'min_value': 0.0,
                'max_value': 20.0,
                'out_of_range_count': 1,
                'out_of_range_indices': [3]
            }
        },
        {
            'rule_name': 'Temporal Consistency Check',
            'is_valid': False,
            'severity': 'warning',
            'details': {
                'reverse_count': 1,
                'reverse_indices': [5]
            }
        }
    ]
    
    # インスタンス化
    calculator = QualityMetricsCalculator(validation_results, data)
    
    # 精度スコアの計算
    precision_score = calculator._calculate_precision_score()
    assert 0 <= precision_score <= 100
    assert precision_score < 100  # 範囲外の値があるので100未満
    print(f"Precision Score: {precision_score}")
    
    # 妥当性スコアの計算
    validity_score = calculator._calculate_validity_score()
    assert 0 <= validity_score <= 100
    assert validity_score < 100  # 時間逆行があるので100未満
    print(f"Validity Score: {validity_score}")
    
    return True

def test_calculate_uniformity_score():
    """データ均一性スコア計算のテスト"""
    # 均一な間隔のデータ
    uniform_intervals = [10.0] * 10
    
    # 不均一な間隔のデータ
    non_uniform_intervals = [5.0, 15.0, 5.0, 15.0, 5.0, 15.0, 5.0, 15.0, 5.0, 15.0]
    
    # 非常に不均一な間隔のデータ
    very_non_uniform_intervals = [1.0, 50.0, 2.0, 40.0, 3.0, 30.0, 4.0, 20.0, 5.0, 10.0]
    
    # サンプルデータと検証結果
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)]
    })
    validation_results = [{'rule_name': 'Required Columns Check', 'is_valid': True, 'severity': 'error'}]
    
    # インスタンス化
    calculator = QualityMetricsCalculator(validation_results, data)
    
    # 均一性スコア計算
    uniform_score = calculator._calculate_uniformity_score(uniform_intervals)
    non_uniform_score = calculator._calculate_uniformity_score(non_uniform_intervals)
    very_non_uniform_score = calculator._calculate_uniformity_score(very_non_uniform_intervals)
    
    # スコアの範囲確認
    assert 0 <= uniform_score <= 100
    assert 0 <= non_uniform_score <= 100
    assert 0 <= very_non_uniform_score <= 100
    
    # 均一なデータのスコアが最も高い
    assert uniform_score > non_uniform_score
    assert non_uniform_score > very_non_uniform_score
    
    print(f"Uniform Score: {uniform_score}")
    print(f"Non-Uniform Score: {non_uniform_score}")
    print(f"Very Non-Uniform Score: {very_non_uniform_score}")
    
    return True

def test_calculate_spatial_quality_scores():
    """空間品質スコア計算のテスト"""
    # サンプルデータ作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # 空間的異常の作成
    data.loc[3, 'latitude'] = 36.0  # 急激な位置の変化
    
    # バリデーション結果サンプル
    validation_results = [{
        'rule_name': 'Spatial Consistency Check',
        'is_valid': False,
        'severity': 'warning',
        'details': {
            'anomaly_count': 1,
            'max_calculated_speed': 50.0,
            'anomaly_indices': [3]
        }
    }]
    
    # インスタンス化
    calculator = QualityMetricsCalculator(validation_results, data)
    
    # 空間品質スコアの計算
    spatial_scores = calculator.calculate_spatial_quality_scores()
    
    # スコアの基本チェック
    assert isinstance(spatial_scores, list)
    assert len(spatial_scores) > 0
    
    # グリッドの検証
    for grid in spatial_scores:
        assert "grid_id" in grid
        assert "center" in grid
        assert "bounds" in grid
        assert "quality_score" in grid
        assert "problem_count" in grid
        assert "total_count" in grid
        assert "problem_percentage" in grid
        assert "impact_level" in grid
        assert 0 <= grid["quality_score"] <= 100
        
    # 問題のあるグリッドが存在するか確認
    problem_grids = [grid for grid in spatial_scores if grid["problem_count"] > 0]
    assert len(problem_grids) > 0
    
    # 問題のあるグリッドのスコアが下がっていることを確認
    problem_grid = problem_grids[0]
    assert problem_grid["quality_score"] < 100
    
    # 問題のないグリッドがあれば、そのスコアは100であることを確認
    no_problem_grids = [grid for grid in spatial_scores if grid["problem_count"] == 0]
    if no_problem_grids:
        assert no_problem_grids[0]["quality_score"] == 100
        
    print(f"Found {len(spatial_scores)} spatial grids")
    print(f"Problem grids: {len(problem_grids)}")
    
    return True

def test_calculate_temporal_quality_scores():
    """時間帯別品質スコア計算のテスト"""
    # サンプルデータ作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # 時間的異常の作成（タイムスタンプの逆行）
    data.loc[5, 'timestamp'] = data.loc[4, 'timestamp'] - timedelta(seconds=10)
    
    # バリデーション結果サンプル
    validation_results = [{
        'rule_name': 'Temporal Consistency Check',
        'is_valid': False,
        'severity': 'warning',
        'details': {
            'reverse_count': 1,
            'reverse_indices': [5]
        }
    }]
    
    # インスタンス化
    calculator = QualityMetricsCalculator(validation_results, data)
    
    # 時間帯別品質スコアの計算
    temporal_scores = calculator.calculate_temporal_quality_scores()
    
    # スコアの基本チェック
    assert isinstance(temporal_scores, list)
    assert len(temporal_scores) > 0
    
    # データがある場合のみ詳細チェック
    period = temporal_scores[0]
    assert "period" in period
    assert "start_time" in period
    assert "end_time" in period
    assert "label" in period
    assert "quality_score" in period
    assert "problem_count" in period
    assert "total_count" in period
    assert "problem_percentage" in period
    assert "impact_level" in period
    assert 0 <= period["quality_score"] <= 100
    
    # 問題のある時間帯を探す
    problem_periods = [p for p in temporal_scores if p["problem_count"] > 0]
    if problem_periods:
        assert problem_periods[0]["quality_score"] < 100
        
    print(f"Found {len(temporal_scores)} time periods")
    print(f"Problem periods: {len(problem_periods)}")
    
    return True

def run_all_tests():
    """すべてのテストを実行"""
    print("===== テスト: 精度と妥当性スコア計算 =====")
    test_precision_and_validity_scores()
    print("\n===== テスト: データ均一性スコア計算 =====")
    test_calculate_uniformity_score()
    print("\n===== テスト: 空間品質スコア計算 =====")
    test_calculate_spatial_quality_scores()
    print("\n===== テスト: 時間帯別品質スコア計算 =====")
    test_calculate_temporal_quality_scores()
    print("\n===== すべてのテストが成功しました！ =====")

if __name__ == "__main__":
    run_all_tests()
