#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ検証機能の単体テスト

このスクリプトは、品質メトリクス計算と視覚化機能を単体でテストします。
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.io as pio

# プロジェクトのルートディレクトリをパスに追加
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir))
sys.path.insert(0, project_root)

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics_integration import EnhancedQualityMetricsCalculator
from sailing_data_processor.validation.visualization_integration import EnhancedValidationVisualizer

def create_sample_data(rows=1000, error_rate=0.1):
    """サンプルデータを生成する"""
    # 現在時刻から24時間のデータを生成
    base_time = datetime.now()
    timestamps = [base_time + timedelta(seconds=i*10) for i in range(rows)]
    
    # 基準となる緯度・経度
    base_lat, base_lon = 35.6, 139.7
    
    # 正常データの作成
    data = {
        "timestamp": timestamps,
        "latitude": [base_lat + (np.sin(i/100) * 0.01) for i in range(rows)],
        "longitude": [base_lon + (np.cos(i/100) * 0.01) for i in range(rows)],
        "speed": [np.abs(10 + np.sin(i/50) * 5) for i in range(rows)],
        "heading": [np.abs((i * 5) % 360) for i in range(rows)]
    }
    
    # エラーの導入
    error_indices = np.random.choice(rows, int(rows * error_rate), replace=False)
    
    # 欠損値の追加
    for idx in error_indices[:int(len(error_indices) * 0.3)]:
        col = np.random.choice(["latitude", "longitude", "speed", "heading"])
        data[col][idx] = np.nan
    
    # 異常値の追加
    for idx in error_indices[int(len(error_indices) * 0.3):int(len(error_indices) * 0.6)]:
        col = np.random.choice(["speed", "heading"])
        if col == "speed":
            data[col][idx] = np.random.choice([-10, 100])  # 負の速度または極端に大きい速度
        else:
            data[col][idx] = np.random.choice([-30, 400])  # 範囲外の方位
    
    # 重複タイムスタンプの追加
    for idx in error_indices[int(len(error_indices) * 0.6):]:
        duplicate_idx = np.random.choice(rows)
        data["timestamp"][idx] = data["timestamp"][duplicate_idx]
    
    return pd.DataFrame(data)

def test_quality_metrics():
    print("データ品質メトリクス計算のテスト")
    
    # サンプルデータ生成
    df = create_sample_data(rows=500, error_rate=0.15)
    print(f"生成データ: {len(df)}行, 欠損値: {df.isna().sum().sum()}個")
    
    # GPSDataContainerを作成
    container = GPSDataContainer()
    container.data = df
    
    # データ検証
    validator = DataValidator()
    validation_results = validator.validate(container)
    
    # 拡張品質メトリクス計算
    metrics = EnhancedQualityMetricsCalculator(validation_results, df)
    
    # 品質スコアを計算
    quality_scores = metrics.calculate_quality_scores()
    print("\n品質スコア:")
    for key, value in quality_scores.items():
        print(f"  {key}: {value}")
    
    # カテゴリ別スコアを計算
    category_scores = metrics.calculate_category_quality_scores()
    print("\nカテゴリ別スコア:")
    for key, value in category_scores.items():
        print(f"  {key}: {value}")
    
    # 時間帯別スコアを計算
    temporal_scores = metrics.calculate_temporal_quality_scores()
    print(f"\n時間帯別スコア: {len(temporal_scores)}件")
    if temporal_scores:
        for i, score in enumerate(temporal_scores[:3]):  # 最初の3つのみ表示
            print(f"  {score['period']}: {score['quality_score']} (問題: {score['problem_count']}/{score['total_count']})")
    
    # 空間グリッド別スコアを計算
    spatial_scores = metrics.calculate_spatial_quality_scores()
    print(f"\n空間グリッド別スコア: {len(spatial_scores)}件")
    if spatial_scores:
        for i, score in enumerate(spatial_scores[:3]):  # 最初の3つのみ表示
            print(f"  {score['grid_id']}: {score['quality_score']} (問題: {score['problem_count']}/{score['total_count']})")
    
    print("\n品質メトリクス計算テスト完了")
    return metrics, df

def test_visualization(metrics, df):
    print("\n視覚化機能のテスト")
    
    # 視覚化クラスを初期化
    visualizer = EnhancedValidationVisualizer(metrics, df)
    
    # 品質スコアの視覚化をテスト
    gauge_chart, bar_chart = visualizer.generate_quality_score_visualization()
    print("  品質スコア視覚化生成: 成功")
    
    # 空間的な品質分布マップをテスト
    spatial_map = visualizer.generate_spatial_quality_map()
    print("  空間品質マップ生成: 成功")
    
    # 時間帯別の品質分布チャートをテスト
    temporal_chart = visualizer.generate_temporal_quality_chart()
    print("  時間帯別品質チャート生成: 成功")
    
    # ダッシュボードをテスト
    dashboard = visualizer.generate_quality_score_dashboard()
    print("  ダッシュボード生成: 成功")
    
    print("\n視覚化機能テスト完了")
    return visualizer

def save_html_output(visualizer, output_dir="test_output"):
    """視覚化結果をHTMLファイルとして保存"""
    print("\n視覚化結果をHTMLとして保存")
    
    # 出力ディレクトリを作成
    os.makedirs(output_dir, exist_ok=True)
    
    # 品質スコアの視覚化
    gauge_chart, bar_chart = visualizer.generate_quality_score_visualization()
    pio.write_html(gauge_chart, file=os.path.join(output_dir, "gauge_chart.html"))
    pio.write_html(bar_chart, file=os.path.join(output_dir, "bar_chart.html"))
    
    # 空間的な品質分布マップ
    spatial_map = visualizer.generate_spatial_quality_map()
    pio.write_html(spatial_map, file=os.path.join(output_dir, "spatial_map.html"))
    
    # 時間帯別の品質分布チャート
    temporal_chart = visualizer.generate_temporal_quality_chart()
    pio.write_html(temporal_chart, file=os.path.join(output_dir, "temporal_chart.html"))
    
    print(f"視覚化結果を {output_dir} ディレクトリに保存しました")

if __name__ == "__main__":
    print("=== データ検証機能の単体テスト開始 ===")
    
    # 詳細なエラー出力を有効化
    import traceback
    
    # サンプルデータ生成
    print("サンプルデータ生成中...")
    df = create_sample_data(rows=100, error_rate=0.15)
    print(f"生成データ: {len(df)}行, 欠損値: {df.isna().sum().sum()}個")
    
    # GPSDataContainerを作成
    print("GPSDataContainer作成中...")
    container = GPSDataContainer()
    container.data = df
    
    # データ検証
    print("データ検証中...")
    validator = DataValidator()
    validation_results = validator.validate(container)
    print(f"検証結果: {len(validation_results)}件")
    
    # 拡張品質メトリクス計算
    print("品質メトリクス計算中...")
    metrics = EnhancedQualityMetricsCalculator(validation_results, df)
    
    # 視覚化クラスを初期化
    print("視覚化クラス初期化中...")
    visualizer = EnhancedValidationVisualizer(metrics, df)
    
    # 出力を保存
    print("視覚化結果を保存中...")
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # 品質スコアの視覚化
        print("品質スコア視覚化生成中...")
        gauge_chart, bar_chart = visualizer.generate_quality_score_visualization()
        print("  品質スコア視覚化生成: 成功")
        
        print("\n全テスト完了")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        traceback.print_exc()
