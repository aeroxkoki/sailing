#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
インポートシステムのテスト用スクリプト

基本的なインポーターとバッチインポーターのテストを行います。
"""

import os
import sys
import pandas as pd
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from sailing_data_processor.importers.csv_importer import CSVImporter
from sailing_data_processor.importers.importer_factory import ImporterFactory
from sailing_data_processor.importers.batch_importer import BatchImporter
from sailing_data_processor.validation.data_validator import DataValidator


def test_csv_importer():
    """CSVインポーターのテスト"""
    print("\n=== CSVインポーターのテスト ===")
    
    # テストファイルのパス
    test_file = "test_data/sample_gps.csv"
    if not Path(test_file).exists():
        print(f"エラー: テストファイル {test_file} が見つかりません")
        return
    
    # CSVインポーターを作成（日付フォーマットを明示的に指定）
    importer = CSVImporter({
        'date_format': '%Y-%m-%dT%H:%M:%S' # ISO8601形式を指定
    })
    
    # インポート可能かチェック
    can_import = importer.can_import(test_file)
    print(f"インポート可能: {can_import}")
    
    if not can_import:
        print("インポート可能性のチェックに失敗しました")
        print(f"エラー: {importer.get_errors()}")
        return
    
    # データをインポート
    container = importer.import_data(test_file)
    
    if container is None:
        print("インポートに失敗しました")
        print(f"エラー: {importer.get_errors()}")
        return
    
    # 成功した場合はデータを表示
    print(f"インポートに成功しました: {len(container.data)} 行のデータ")
    print("\nデータのサンプル:")
    print(container.data.head())
    
    # メタデータを表示
    print("\nメタデータ:")
    for key, value in container.metadata.items():
        print(f"  {key}: {value}")
    
    # 時間範囲を表示
    time_range = container.get_time_range()
    print("\n時間範囲:")
    print(f"  開始: {time_range['start']}")
    print(f"  終了: {time_range['end']}")
    print(f"  期間: {time_range['duration_seconds'] / 60:.2f} 分")
    
    # データの内容を確認
    print("\n列の概要:")
    for col in container.data.columns:
        if col == 'timestamp':
            continue  # タイムスタンプはスキップ
        
        if pd.api.types.is_numeric_dtype(container.data[col]):
            min_val = container.data[col].min()
            max_val = container.data[col].max()
            avg_val = container.data[col].mean()
            print(f"  {col}: 最小={min_val:.2f}, 最大={max_val:.2f}, 平均={avg_val:.2f}")
        else:
            print(f"  {col}: 非数値型")
    
    return container


def test_importer_factory():
    """インポーターファクトリーのテスト"""
    print("\n=== インポーターファクトリーのテスト ===")
    
    # テストファイルのパス
    test_file = "test_data/sample_gps.csv"
    if not Path(test_file).exists():
        print(f"エラー: テストファイル {test_file} が見つかりません")
        return
    
    # インポーターファクトリーからインポーターを取得
    importer = ImporterFactory.get_importer(test_file)
    
    if importer is None:
        print(f"適切なインポーターが見つかりませんでした: {test_file}")
        return
    
    print(f"検出されたインポーター: {importer.__class__.__name__}")
    
    # データをインポート
    container = importer.import_data(test_file)
    
    if container is None:
        print("インポートに失敗しました")
        print(f"エラー: {importer.get_errors()}")
        return
    
    print(f"インポートに成功しました: {len(container.data)} 行のデータ")
    
    return container


def test_column_mapping():
    """カラムマッピング機能のテスト"""
    print("\n=== カラムマッピング機能のテスト ===")
    
    # テストファイルのパス
    test_file = "test_data/sample_different_columns.csv"
    if not Path(test_file).exists():
        print(f"エラー: テストファイル {test_file} が見つかりません")
        return
    
    # CSVインポーターを作成（カラムマッピング設定付き）
    column_mapping = {
        "timestamp": "Time",
        "latitude": "Lat",
        "longitude": "Lon",
        "speed": "Velocity",
        "course": "Heading",
        "elevation": "Alt"
    }
    
    importer = CSVImporter({
        "column_mapping": column_mapping,
        "date_format": '%Y-%m-%dT%H:%M:%S' # ISO8601形式を指定
    })
    
    # データをインポート
    container = importer.import_data(test_file)
    
    if container is None:
        print("インポートに失敗しました")
        print(f"エラー: {importer.get_errors()}")
        return
    
    # 成功した場合はデータを表示
    print(f"インポートに成功しました: {len(container.data)} 行のデータ")
    print("\nデータのサンプル:")
    print(container.data.head())
    
    # 列名を確認（マッピングされていることを確認）
    expected_columns = ["timestamp", "latitude", "longitude", "speed", "course", "elevation"]
    actual_columns = container.data.columns.tolist()
    
    print("\n列名のマッピング確認:")
    print(f"  期待される列名: {expected_columns}")
    print(f"  実際の列名: {actual_columns}")
    
    missing_columns = [col for col in expected_columns if col not in actual_columns]
    if missing_columns:
        print(f"  一部の列が見つかりません: {missing_columns}")
    else:
        print("  すべての列が期待通りにマッピングされました")
    
    return container


def test_batch_importer():
    """バッチインポーターのテスト"""
    print("\n=== バッチインポーターのテスト ===")
    
    # テストファイルのパス
    test_files = [
        "test_data/sample_gps.csv",
        "test_data/sample_different_columns.csv"
    ]
    
    # ファイルの存在を確認
    missing_files = [f for f in test_files if not Path(f).exists()]
    if missing_files:
        print(f"エラー: 一部のテストファイルが見つかりません: {missing_files}")
        return
    
    # バッチインポーターの設定
    config = {
        'parallel': False,  # テストでは直列処理が分かりやすい
        'max_workers': 1
    }
    
    # カラムマッピングと設定を追加
    config['csv'] = {
        'column_mapping': {
            "timestamp": "Time",
            "latitude": "Lat",
            "longitude": "Lon",
            "speed": "Velocity",
            "course": "Heading",
            "elevation": "Alt"
        },
        'date_format': '%Y-%m-%dT%H:%M:%S' # ISO8601形式を指定
    }
    
    batch_importer = BatchImporter(config)
    
    # メタデータの設定
    metadata = {
        'batch_test': True,
        'description': 'バッチインポーターのテスト'
    }
    
    # インポート実行
    result = batch_importer.import_files(test_files, metadata)
    
    # 結果表示
    summary = result.get_summary()
    print(f"総ファイル数: {summary['total_files']}")
    print(f"成功: {summary['successful_count']}")
    print(f"失敗: {summary['failed_count']}")
    print(f"警告あり: {summary['warning_count']}")
    
    # 成功したファイル
    if summary['successful_count'] > 0:
        print("\n成功したファイル:")
        for i, (file_name, container) in enumerate(result.successful.items()):
            print(f"  {i+1}. {file_name} - {len(container.data)}行")
    
    # 失敗したファイル
    if summary['failed_count'] > 0:
        print("\n失敗したファイル:")
        for i, (file_name, errors) in enumerate(result.failed.items()):
            print(f"  {i+1}. {file_name} - エラー:")
            for error in errors:
                print(f"    - {error}")
    
    # マージテスト
    if summary['successful_count'] > 1:
        print("\nマージテスト:")
        merged = result.merge_containers()
        if merged:
            print(f"  マージ結果: {len(merged.data)}行 ({summary['successful_count']}ファイルを結合)")
            print(f"  タイムスタンプ範囲: {merged.get_time_range()['start']} から {merged.get_time_range()['end']}")
        else:
            print("  マージに失敗しました")
    
    return result


def test_validation():
    """データ検証のテスト"""
    print("\n=== データ検証のテスト ===")
    
    # テストファイルのパス
    test_file = "test_data/sample_gps.csv"
    if not Path(test_file).exists():
        print(f"エラー: テストファイル {test_file} が見つかりません")
        return
    
    # CSVインポーターを使用してデータをインポート
    importer = CSVImporter({
        'date_format': '%Y-%m-%dT%H:%M:%S' # ISO8601形式を指定
    })
    container = importer.import_data(test_file)
    
    if container is None:
        print("インポートに失敗しました")
        return
    
    # データ検証器を作成
    validator = DataValidator()
    
    # 検証を実行
    valid, results = validator.validate(container)
    
    print(f"検証結果: {'成功' if valid else '失敗'}")
    
    # 検証結果の詳細を表示
    print("\n検証ルールの結果:")
    for result in results:
        status = "✅" if result["is_valid"] else "❌"
        severity = result["severity"]
        name = result["rule_name"]
        description = result["description"]
        
        print(f"  {status} [{severity}] {name}: {description}")
        
        if not result["is_valid"]:
            print(f"    - 詳細: {result['details']}")
    
    # 問題点のみを表示
    issues = validator.get_issues(include_warnings=True)
    if issues:
        print("\n検出された問題:")
        for issue in issues:
            severity = issue["severity"]
            name = issue["rule_name"]
            print(f"  [{severity}] {name}")
    else:
        print("\n問題は検出されませんでした")
    
    return valid, results


def main():
    """メイン関数"""
    # テストディレクトリの存在確認
    test_dir = Path("test_data")
    if not test_dir.exists():
        print(f"テストディレクトリが存在しません: {test_dir}")
        print("テストデータを含むディレクトリを作成してください")
        return
    
    # 各テストを実行
    test_csv_importer()
    test_importer_factory()
    test_column_mapping()
    test_batch_importer()
    test_validation()
    
    print("\nすべてのテストが完了しました")


if __name__ == "__main__":
    main()
