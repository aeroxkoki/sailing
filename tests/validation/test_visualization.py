# -*- coding: utf-8 -*-
"""
sailing_data_processor.validation.visualization のテスト
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization import ValidationVisualizer, ValidationDashboard


def test_validation_visualizer_initialization():
    """ValidationVisualizer の初期化テスト"""
    # サンプルデータ作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # バリデーション結果サンプル
    validation_results = [{
        'rule_name': 'Required Columns Check',
        'is_valid': True,
        'severity': 'error',
        'details': {'required_columns': ['timestamp', 'latitude', 'longitude']}
    }]
    
    # メトリクス計算機のインスタンス化
    calculator = QualityMetricsCalculator(validation_results, data)
    
    # ビジュアライザのインスタンス化
    visualizer = ValidationVisualizer(calculator, data)
    
    # 基本的なプロパティの確認
    assert visualizer is not None
    assert visualizer.quality_metrics == calculator
    assert visualizer.data.equals(data)


def test_generate_heatmap_data():
    """ヒートマップデータの生成テスト"""
    # サンプルデータ作成（問題あり）
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # 範囲外の値を挿入
    data.loc[3, 'speed'] = 100.0  # あり得ない速度
    
    # バリデーション結果サンプル
    validation_results = [{
        'rule_name': 'Value Range Check',
        'is_valid': False,
        'severity': 'warning',
        'details': {
            'column': 'speed',
            'min_value': 0.0,
            'max_value': 20.0,
            'actual_min': 5.0,
            'actual_max': 100.0,
            'out_of_range_count': 1,
            'out_of_range_indices': [3]
        }
    }]
    
    # インスタンス化
    calculator = QualityMetricsCalculator(validation_results, data)
    visualizer = ValidationVisualizer(calculator, data)
    
    # ヒートマップデータの生成
    heatmap_data = visualizer.generate_heatmap_data()
    
    # データの基本チェック
    assert heatmap_data["has_data"] == True
    assert "heatmap_data" in heatmap_data
    assert "lat_range" in heatmap_data
    assert "lon_range" in heatmap_data


def test_generate_distribution_charts():
    """分布チャートデータの生成テスト"""
    # サンプルデータ作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # 空間的異常の作成
    data.loc[6, 'latitude'] = 36.0  # 急激な位置の変化
    
    # バリデーション結果サンプル
    validation_results = [{
        'rule_name': 'Spatial Consistency Check',
        'is_valid': False,
        'severity': 'warning',
        'details': {
            'anomaly_count': 1,
            'max_calculated_speed': 50.0,
            'anomaly_indices': [6]
        }
    }]
    
    # インスタンス化
    calculator = QualityMetricsCalculator(validation_results, data)
    visualizer = ValidationVisualizer(calculator, data)
    
    # 分布チャートデータの生成
    distribution_charts = visualizer.generate_distribution_charts()
    
    # データの基本チェック
    assert "pie_data" in distribution_charts
    assert "temporal_distribution" in distribution_charts
    assert "spatial_distribution" in distribution_charts
    
    # パイチャートデータの確認
    pie_data = distribution_charts["pie_data"]
    assert "problem_types" in pie_data
    assert "severity" in pie_data


def test_generate_quality_score_chart():
    """品質スコアチャートの生成テスト"""
    # サンプルデータ作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # バリデーション結果サンプル
    validation_results = [{
        'rule_name': 'Required Columns Check',
        'is_valid': True,
        'severity': 'error',
        'details': {'required_columns': ['timestamp', 'latitude', 'longitude']}
    }]
    
    # インスタンス化
    calculator = QualityMetricsCalculator(validation_results, data)
    visualizer = ValidationVisualizer(calculator, data)
    
    # 品質スコアチャートの生成
    chart = visualizer.generate_quality_score_chart()
    
    # チャートの基本チェック
    assert isinstance(chart, go.Figure)
    assert len(chart.data) > 0  # データがあることを確認


def test_generate_quality_score_visualization():
    """品質スコアの可視化（ゲージとバーチャート）のテスト"""
    # サンプルデータ作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # NULLデータを一部に挿入
    data.loc[2, 'latitude'] = None
    
    # バリデーション結果サンプル
    validation_results = [{
        'rule_name': 'No Null Values Check',
        'is_valid': False,
        'severity': 'error',
        'details': {
            'columns': ['latitude', 'longitude', 'speed'],
            'total_null_count': 1,
            'null_counts': {'latitude': 1, 'longitude': 0, 'speed': 0},
            'null_indices': {'latitude': [2]}
        }
    }]
    
    # インスタンス化
    calculator = QualityMetricsCalculator(validation_results, data)
    visualizer = ValidationVisualizer(calculator, data)
    
    # 品質スコアの可視化
    gauge_chart, bar_chart = visualizer.generate_quality_score_visualization()
    
    # ゲージチャートの検証
    assert isinstance(gauge_chart, go.Figure)
    assert len(gauge_chart.data) > 0
    
    # バーチャートの検証
    assert isinstance(bar_chart, go.Figure)
    assert len(bar_chart.data) > 0


def test_validation_dashboard_initialization():
    """ValidationDashboard の初期化テスト"""
    # サンプルデータ作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # バリデーション結果サンプル
    validation_results = [{
        'rule_name': 'Required Columns Check',
        'is_valid': True,
        'severity': 'error',
        'details': {'required_columns': ['timestamp', 'latitude', 'longitude']}
    }]
    
    # ダッシュボードのインスタンス化
    dashboard = ValidationDashboard(validation_results, data)
    
    # 基本的なプロパティの確認
    assert dashboard is not None
    assert dashboard.validation_results == validation_results
    assert dashboard.data.equals(data)
    assert hasattr(dashboard, 'metrics_calculator')
    assert hasattr(dashboard, 'visualizer')


def test_render_overview_section():
    """概要セクションのレンダリングテスト"""
    # サンプルデータ作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # データに問題を作成
    data.loc[2, 'latitude'] = None  # 欠損値
    
    # バリデーション結果サンプル
    validation_results = [{
        'rule_name': 'No Null Values Check',
        'is_valid': False,
        'severity': 'error',
        'details': {
            'columns': ['latitude', 'longitude', 'speed'],
            'total_null_count': 1,
            'null_counts': {'latitude': 1, 'longitude': 0, 'speed': 0},
            'null_indices': {'latitude': [2]}
        }
    }]
    
    # ダッシュボードのインスタンス化
    dashboard = ValidationDashboard(validation_results, data)
    
    # 概要セクションのレンダリング
    overview = dashboard.render_overview_section()
    
    # 基本的な構造の確認
    assert "quality_summary" in overview
    assert "charts" in overview
    assert "quality_score" in overview["charts"]
    assert "category_scores" in overview["charts"]


def test_render_details_section():
    """詳細セクションのレンダリングテスト"""
    # サンプルデータ作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(10)],
        'latitude': [35.0 + i * 0.001 for i in range(10)],
        'longitude': [135.0 + i * 0.001 for i in range(10)],
        'speed': [5.0 + i * 0.2 for i in range(10)]
    })
    
    # 重複タイムスタンプの作成
    data.loc[9, 'timestamp'] = data.loc[8, 'timestamp']
    
    # バリデーション結果サンプル
    validation_results = [{
        'rule_name': 'No Duplicate Timestamps',
        'is_valid': False,
        'severity': 'warning',
        'details': {
            'duplicate_count': 2,
            'duplicate_timestamps': [data.loc[8, 'timestamp']],
            'duplicate_indices': {str(data.loc[8, 'timestamp']): [8, 9]}
        }
    }]
    
    # ダッシュボードのインスタンス化
    dashboard = ValidationDashboard(validation_results, data)
    
    # 詳細セクションのレンダリング
    details = dashboard.render_details_section()
    
    # 基本的な構造の確認
    assert "charts" in details
    assert "detailed_report" in details
    assert "problem_records_df" in details
