"""
検証フィードバック強化システムのデモプログラム

このスクリプトは、セーリングデータの検証、品質メトリクス計算、可視化、
およびインタラクティブな修正機能の動作を確認するデモです。

使用方法:
    python3 validation_demo.py

注意: 
    このプログラムはテスト用で、実際の運用環境では専用のUIを使用してください。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import matplotlib.pyplot as plt
import os
import json

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.visualization import ValidationVisualizer
from sailing_data_processor.validation.correction import InteractiveCorrectionInterface

def create_sample_data():
    """サンプルデータの作成"""
    print("サンプルデータを作成中...")
    
    # 正常なデータをベースに作成
    data = pd.DataFrame({
        'timestamp': [datetime(2025, 1, 1, 12, 0, i) for i in range(30)],
        'latitude': [35.0 + i * 0.001 for i in range(30)],
        'longitude': [135.0 + i * 0.001 for i in range(30)],
        'speed': [5.0 + i * 0.2 for i in range(30)],
        'course': [45.0 + i * 1.0 for i in range(30)],
        'boat_id': ['demo_boat'] * 30
    })
    
    # いくつかの問題を作成
    # 欠損値
    data.loc[2, 'latitude'] = None
    data.loc[5, 'speed'] = None
    data.loc[10, 'course'] = None
    
    # 範囲外の値
    data.loc[8, 'speed'] = 100.0  # 異常な速度
    data.loc[12, 'course'] = 500.0  # 異常な角度
    
    # 重複タイムスタンプ
    data.loc[15, 'timestamp'] = data.loc[14, 'timestamp']
    data.loc[16, 'timestamp'] = data.loc[14, 'timestamp']
    
    # 時間逆行
    data.loc[20, 'timestamp'] = data.loc[19, 'timestamp'] - timedelta(seconds=30)
    
    # 空間的異常（急激な位置の変化）
    data.loc[25, 'latitude'] = 36.0
    
    # GPSDataContainerの作成
    container = GPSDataContainer()
    container.data = data
    container.metadata = {
        'boat_id': 'demo_boat',
        'data_source': 'validation_demo',
        'created_at': datetime.now().isoformat()
    }
    
    print(f"サンプルデータを作成しました（{len(data)}レコード）")
    return container

def print_separator(title=""):
    """区切り線を表示"""
    width = 80
    if title:
        padding = (width - len(title) - 4) // 2
        print("=" * padding + f" {title} " + "=" * padding)
    else:
        print("=" * width)

def run_validation_workflow():
    """検証ワークフローの実行"""
    print_separator("検証フィードバック強化システムデモ")
    print("このデモでは、データ検証、品質メトリクス計算、可視化、および修正機能を実行します。\n")
    
    # サンプルデータを作成
    container = create_sample_data()
    
    print_separator("1. データ検証")
    # バリデーションの実行
    validator = DataValidator()
    validation_results = validator.validate(container)
    
    # 検証結果のサマリーを表示
    valid_count = sum(1 for res in validation_results if res['is_valid'])
    invalid_count = len(validation_results) - valid_count
    
    print(f"検証ルール数: {len(validation_results)}")
    print(f"  - 合格: {valid_count}")
    print(f"  - 不合格: {invalid_count}")
    
    if invalid_count > 0:
        print("\n検出された問題:")
        for i, result in enumerate(validation_results):
            if not result['is_valid']:
                print(f"  {i+1}. [{result['severity']}] {result['rule_name']}")
    
    print_separator("2. 品質メトリクス計算")
    # 品質メトリクスの計算
    metrics_calculator = QualityMetricsCalculator(validation_results, container.data)
    
    # 品質スコアの表示
    quality_scores = metrics_calculator.quality_scores
    print("データ品質スコア:")
    print(f"  - 総合スコア: {quality_scores['total']:.1f}/100")
    print(f"  - 完全性: {quality_scores['completeness']:.1f}/100")
    print(f"  - 正確性: {quality_scores['accuracy']:.1f}/100")
    print(f"  - 一貫性: {quality_scores['consistency']:.1f}/100")
    
    # 問題の分布
    problem_distribution = metrics_calculator.problem_distribution
    if problem_distribution['problem_type']['has_data']:
        problem_counts = problem_distribution['problem_type']['problem_counts']
        print("\n問題タイプ別の件数:")
        for problem_type, count in problem_counts.items():
            if count > 0:
                print(f"  - {problem_type}: {count}件")
    
    print_separator("3. データ品質の可視化")
    # 可視化の生成
    visualizer = ValidationVisualizer(metrics_calculator, container.data)
    
    # 可視化の出力先ディレクトリを作成
    output_dir = "validation_demo_output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 品質スコアチャートの保存
    quality_chart = visualizer.generate_quality_score_chart()
    quality_chart.write_image(f"{output_dir}/quality_score.png")
    print(f"品質スコアチャートを保存しました: {output_dir}/quality_score.png")
    
    # カテゴリスコアチャートの保存
    category_chart = visualizer.generate_category_scores_chart()
    category_chart.write_image(f"{output_dir}/category_scores.png")
    print(f"カテゴリスコアチャートを保存しました: {output_dir}/category_scores.png")
    
    # 問題分布チャートの保存
    distribution_chart = visualizer.generate_problem_distribution_chart()
    distribution_chart.write_image(f"{output_dir}/problem_distribution.png")
    print(f"問題分布チャートを保存しました: {output_dir}/problem_distribution.png")
    
    # 空間分布のヒートマップの保存
    heatmap = visualizer.generate_problem_heatmap()
    heatmap.write_image(f"{output_dir}/problem_heatmap.png")
    print(f"問題ヒートマップを保存しました: {output_dir}/problem_heatmap.png")
    
    # タイムラインチャートの保存
    timeline = visualizer.generate_timeline_chart()
    timeline.write_image(f"{output_dir}/problem_timeline.png")
    print(f"問題タイムラインを保存しました: {output_dir}/problem_timeline.png")
    
    print_separator("4. データ修正インターフェース")
    # 修正インターフェースの作成
    correction_interface = InteractiveCorrectionInterface(
        container=container,
        validator=validator
    )
    
    # 問題カテゴリとその件数を表示
    categories = correction_interface.get_problem_categories()
    print("問題カテゴリ別の件数:")
    for category, count in categories.items():
        if category != "all" and count > 0:
            print(f"  - {category}: {count}件")
            
            # カテゴリごとの修正オプションを表示
            options = correction_interface.get_correction_options(category)
            if options:
                print(f"    利用可能な修正オプション:")
                for option in options:
                    print(f"    * {option['name']}: {option['description']}")
    
    # 自動修正を実行
    print("\n自動修正を実行中...")
    fixed_container = correction_interface.auto_fix_all()
    
    if fixed_container:
        print("自動修正が完了しました")
        
        # 修正後のバリデーション実行
        new_validator = DataValidator()
        new_results = new_validator.validate(fixed_container)
        
        # 修正後の品質メトリクス計算
        new_metrics = QualityMetricsCalculator(new_results, fixed_container.data)
        new_scores = new_metrics.quality_scores
        
        print("\n修正前後の品質スコア比較:")
        print(f"  - 修正前総合スコア: {quality_scores['total']:.1f}/100")
        print(f"  - 修正後総合スコア: {new_scores['total']:.1f}/100")
        print(f"  - 改善: {new_scores['total'] - quality_scores['total']:.1f}ポイント")
        
        # 修正後のデータを保存
        fixed_data_path = f"{output_dir}/fixed_data.csv"
        fixed_container.data.to_csv(fixed_data_path, index=False)
        print(f"\n修正後のデータを保存しました: {fixed_data_path}")
        
        # 修正前後のレポートを生成
        original_report = metrics_calculator.get_quality_report()
        fixed_report = new_metrics.get_quality_report()
        
        with open(f"{output_dir}/original_quality_report.json", "w", encoding="utf-8") as f:
            json.dump(original_report, f, ensure_ascii=False, indent=2, default=str)
        
        with open(f"{output_dir}/fixed_quality_report.json", "w", encoding="utf-8") as f:
            json.dump(fixed_report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"品質レポートを保存しました: {output_dir}/original_quality_report.json")
        print(f"修正後の品質レポートを保存しました: {output_dir}/fixed_quality_report.json")
    else:
        print("自動修正に失敗しました")
    
    print_separator("デモ完了")
    print(f"すべての出力ファイルは {output_dir} ディレクトリに保存されています。")

if __name__ == "__main__":
    try:
        run_validation_workflow()
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
