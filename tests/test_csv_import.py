#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSVインポーターテスト用のシンプルなスクリプト
"""

import os
import sys
from pathlib import Path

# レポジトリのルートパスを追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    # インポーターモジュールをインポート
    from sailing_data_processor.importers.csv_importer import CSVImporter
    
    print("CSVImporterのインポートに成功しました")
    
    # テスト用ファイルパスを設定
    test_file = Path("test_data/sample.csv")
    
    if not test_file.exists():
        print(f"テストファイルが見つかりません: {test_file}")
        sys.exit(1)
    
    print(f"テストファイル: {test_file}")
    
    # CSVインポーターを作成
    importer = CSVImporter({
        'auto_detect_columns': True  # 自動列マッピングを有効化
    })
    
    # インポート可能かどうかをチェック
    if importer.can_import(test_file):
        print("ファイルをインポート可能と判定されました")
        
        # CSVファイルの構造分析
        structure = importer.analyze_csv_structure(test_file)
        
        print("\n=== CSVファイル構造分析結果 ===")
        print(f"区切り文字: '{structure.get('delimiter', '')}'")
        print(f"ヘッダー有無: {structure.get('has_header', False)}")
        print(f"カラム: {structure.get('columns', [])}")
        
        print("\n推奨マッピング:")
        for target, source in structure.get('suggested_mapping', {}).items():
            print(f"  {target}: {source}")
        
        # データをインポート
        container = importer.import_data(test_file)
        
        if container:
            df = container.data
            print("\n=== インポート結果 ===")
            print(f"行数: {len(df)}")
            print(f"列: {df.columns.tolist()}")
            print(f"\n最初の3行:")
            print(df.head(3))
            
            # 時間範囲
            time_range = container.get_time_range()
            print(f"\n期間: {time_range['start']} ～ {time_range['end']}")
            print(f"時間幅: {time_range['duration_seconds']}秒")
            
            # メタデータ
            print("\nメタデータ:")
            for key, value in container.metadata.items():
                # dict型の場合は省略表示
                if isinstance(value, dict) and len(str(value)) > 100:
                    print(f"  {key}: {type(value).__name__} ({len(value)} 項目)")
                else:
                    print(f"  {key}: {value}")
        else:
            print("インポートに失敗しました")
            print("エラー:", importer.get_errors())
    else:
        print("ファイルをインポート可能と判定されませんでした")
        print("エラー:", importer.get_errors())
    
except ImportError as e:
    print(f"インポートエラー: {e}")
except Exception as e:
    print(f"エラー: {e}")
