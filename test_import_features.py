#!/usr/bin/env python3
"""
インポート機能のテスト用スクリプト
"""

import sys
import os
import pandas as pd
from pathlib import Path

# 現在のパスを表示
print("Current directory:", os.getcwd())

# レポジトリのルートパスを追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    # インポーターをインポート
    from sailing_data_processor.importers.csv_importer import CSVImporter
    from sailing_data_processor.importers.importer_factory import ImporterFactory
    from sailing_data_processor.importers.batch_importer import BatchImporter
    from sailing_data_processor.validation.data_validator import DataValidator
    from sailing_data_processor.data_model.container import GPSDataContainer
    
    print("モジュールのインポートに成功しました")
    
    # テスト用のCSVファイルパス
    csv_path = os.path.join("test_data", "sample.csv")
    
    print(f"\n[1] CSVインポーターのテスト - {csv_path}")
    
    # CSVインポーターを作成
    csv_importer = CSVImporter()
    
    # ファイルがインポート可能か確認
    can_import = csv_importer.can_import(csv_path)
    print(f"インポート可能: {can_import}")
    
    if can_import:
        # データをインポート
        container = csv_importer.import_data(csv_path)
        
        if container:
            print(f"インポート成功: {len(container.data)} 行のデータ")
            print(f"タイムスタンプ範囲: {container.data['timestamp'].min()} ～ {container.data['timestamp'].max()}")
            print("\nデータサンプル:")
            print(container.data.head(3))
            
            # メタデータを表示
            print("\nメタデータ:")
            for key, value in container.metadata.items():
                print(f"  {key}: {value}")
        else:
            print("インポート失敗")
            for error in csv_importer.get_errors():
                print(f"  エラー: {error}")
    
    print("\n[2] インポーターファクトリーのテスト")
    
    # インポーターファクトリーからインポーターを取得
    importer = ImporterFactory.get_importer(csv_path)
    
    if importer:
        print(f"検出されたインポーター: {importer.__class__.__name__}")
        
        # データをインポート
        container = importer.import_data(csv_path)
        
        if container:
            print(f"インポート成功: {len(container.data)} 行のデータ")
        else:
            print("インポート失敗")
    else:
        print("適切なインポーターが見つかりませんでした")
    
    print("\n[3] データ検証のテスト")
    
    if 'container' in locals() and container:
        # データ検証器を作成
        validator = DataValidator()
        
        # データを検証
        is_valid, results = validator.validate(container)
        
        print(f"検証結果: {'成功' if is_valid else '失敗'}")
        
        print("\n検証詳細:")
        for result in results:
            status = "✓" if result["is_valid"] else "✗"
            print(f"  {status} {result['rule_name']} ({result['severity']}): {result['description']}")
            if not result["is_valid"]:
                print(f"    詳細: {result['details']}")
    
    print("\n[4] バッチインポートのテスト")
    
    # バッチインポーターを作成
    batch_importer = BatchImporter()
    
    # 単一ファイルでバッチインポートをテスト
    result = batch_importer.import_files([csv_path])
    
    # 結果サマリーを表示
    summary = result.get_summary()
    print(f"総ファイル数: {summary['total_files']}")
    print(f"成功: {summary['successful_count']}")
    print(f"失敗: {summary['failed_count']}")
    
    if summary['successful_count'] > 0:
        print("\n成功したファイル:")
        for i, (file_name, container) in enumerate(result.successful.items()):
            print(f"  {i+1}. {file_name} - {len(container.data)}行")
    
    if summary['failed_count'] > 0:
        print("\n失敗したファイル:")
        for i, (file_name, errors) in enumerate(result.failed.items()):
            print(f"  {i+1}. {file_name} - {len(errors)}エラー")
            for error in errors:
                print(f"    - {error}")
    
    # マージテスト
    if summary['successful_count'] > 0:
        merged = result.merge_containers()
        if merged:
            print(f"\nマージ結果: {len(merged.data)}行")
        else:
            print("\nマージに失敗しました")
    
    print("\nテスト完了")

except ImportError as e:
    print(f"モジュールのインポートに失敗しました: {e}")
except Exception as e:
    print(f"エラーが発生しました: {e}")
