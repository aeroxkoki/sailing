#\!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
インポーターデバッグスクリプト
"""

import os
import sys
import traceback
from pathlib import Path
import logging

# ロギングの設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('debug_import')

# パスの追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# テスト対象のファイルパスを表示
print("現在のディレクトリ:", os.getcwd())
print("Pythonパス:")
for i, path in enumerate(sys.path):
    print(f"  {i+1}. {path}")

try:
    # sailing_data_processorのインポート
    print("\n=== モジュールのインポート ===")
    import sailing_data_processor
    print(f"sailing_data_processor: {sailing_data_processor.__file__}")
    print(f"バージョン: {sailing_data_processor.__version__}")
    
    # CSVインポーターのインポート
    print("\n=== CSVインポーターのインポート ===")
    from sailing_data_processor.importers.csv_importer import CSVImporter
    print("CSVImporterのインポートに成功しました")
    
    # ImporterFactoryのインポート
    print("\n=== ImporterFactoryのインポート ===")
    from sailing_data_processor.importers.importer_factory import ImporterFactory
    print("ImporterFactoryのインポートに成功しました")
    
    # BatchImporterのインポート
    print("\n=== BatchImporterのインポート ===")
    from sailing_data_processor.importers.batch_importer import BatchImporter
    print("BatchImporterのインポートに成功しました")
    
    # テストファイルのパスを探索
    print("\n=== テストファイルの探索 ===")
    test_dirs = [
        Path("test_data"),
        Path("resources"), 
        Path("tests/test_data"), 
        Path("tests/resources")
    ]
    
    # 絶対パスで確認
    absolute_test_dirs = [
        Path(os.path.join(current_dir, "test_data")),
        Path(os.path.join(current_dir, "resources")),
        Path(os.path.join(current_dir, "tests/test_data")),
        Path(os.path.join(current_dir, "tests/resources"))
    ]
    
    # すべての可能性を確認
    print("テストファイルのディレクトリ:", os.path.dirname(__file__))
    
    csv_file_paths = []
    for test_dir in test_dirs + absolute_test_dirs:
        file_path = test_dir / "sample.csv"
        exists = file_path.exists()
        print(f"  {file_path} (存在: {exists})")
        if exists:
            csv_file_paths.append(file_path)
    
    if not csv_file_paths:
        print("テスト用CSVファイルが見つかりません。")
        sys.exit(1)
    
    # 最初のCSVファイルを使用
    test_file = csv_file_paths[0]
    print(f"\nテストファイル: {test_file}")
    
    # CSVインポーターをテスト
    print("\n=== インポーターテスト ===")
    importer = CSVImporter()
    print(f"インポータークラス: {importer.__class__.__name__}")
    
    # ファイルが存在するか確認
    print(f"ファイル存在チェック: {test_file} - {os.path.exists(str(test_file))}")
    
    # インポート可能かチェック
    print("インポート可能性チェック中...")
    can_import = importer.can_import(test_file)
    print(f"ファイルをインポート可能と判定されました: {can_import}")
    
    if not can_import:
        errors = importer.get_errors()
        print(f"インポートエラー: {errors}")
        sys.exit(1)
    
    # CSVファイルの構造を解析
    print("\n=== CSVファイル構造分析結果 ===")
    file_info = importer.analyze_csv_structure(test_file)
    print(f"区切り文字: '{file_info['delimiter']}'")
    print(f"ヘッダー有無: {file_info['has_header']}")
    print(f"カラム: {file_info['columns']}")
    print("推奨マッピング:")
    for col, mapped in file_info.get('column_mapping', {}).items():
        print(f"  {col}: {mapped}")
    
    # データインポートを実行
    print("\n=== インポート結果 ===")
    container = importer.import_data(test_file)
    
    if container is not None:
        df = container.data
        print(f"行数: {len(df)}")
        print(f"列: {list(df.columns)}")
        print("最初の3行:")
        print(df.head(3))
        
        # タイムスタンプの範囲を表示
        if 'timestamp' in df.columns:
            print(f"期間: {df['timestamp'].min()} ～ {df['timestamp'].max()}")
            
            # 時間幅を計算（秒単位）
            time_diff = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
            print(f"時間幅: {time_diff}秒")
        
        # メタデータを表示
        print("メタデータ:")
        for key, value in container.metadata.items():
            if isinstance(value, dict):
                print(f"  {key}: dict ({len(value)} 項目)")
            else:
                print(f"  {key}: {value}")
    else:
        print("インポートに失敗しました")
        errors = importer.get_errors()
        for err in errors:
            print(f"  - {err}")
    
    # ファクトリー経由のインポーターも確認
    print("\n=== ファクトリー経由のインポーターテスト ===")
    factory_importer = ImporterFactory.get_importer(test_file)
    if factory_importer:
        print(f"ファクトリーから取得されたインポーター: {factory_importer.__class__.__name__}")
        
        # 簡易インポートテスト
        if factory_importer.can_import(test_file):
            print("ファイルをインポート可能と判定されました")
        else:
            print("ファイルをインポート不可と判定されました")
            errors = factory_importer.get_errors()
            for err in errors:
                print(f"  - {err}")
    else:
        print("適切なインポーターが見つかりませんでした")
    
    # バッチインポーターのテスト
    print("\n=== バッチインポーターテスト ===")
    batch_importer = BatchImporter({'parallel': False})  # シングルスレッドモードで実行
    result = batch_importer.import_files([test_file])
    
    # 結果表示
    summary = result.get_summary()
    print(f"総ファイル数: {summary['total_files']}")
    print(f"成功: {summary['successful_count']}")
    print(f"失敗: {summary['failed_count']}")
    
    print("\nテスト終了")
    
except Exception as e:
    print(f"エラーが発生しました: {e}")
    traceback.print_exc()
