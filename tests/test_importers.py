# -*- coding: utf-8 -*-
"""
インポーターのテストスクリプト

このスクリプトは各種インポーターが正しく機能するかテストします。
テスト用のサンプルデータを用意して実行してください。
"""

import os
import sys
import pandas as pd
from pathlib import Path

from sailing_data_processor.importers.importer_factory import ImporterFactory
from sailing_data_processor.importers.csv_importer import CSVImporter
from sailing_data_processor.importers.gpx_importer import GPXImporter
from sailing_data_processor.importers.tcx_importer import TCXImporter
from sailing_data_processor.importers.fit_importer import FITImporter
from sailing_data_processor.importers.batch_importer import BatchImporter

def test_importer(importer, file_path, expected_success=True):
    """インポーターをテスト"""
    print(f"[1] CSVインポーターのテスト - {importer.__class__.__name__} - {file_path}")
    print(f"ファイル存在チェック: {file_path} - {os.path.exists(str(file_path))}")
    
    # インポート可能かチェック
    print("インポート可能性チェック中...")
    can_import = importer.can_import(file_path)
    print(f"インポート可能: {can_import}")
    
    if not can_import and expected_success:
        print(f"[エラー] ファイルを認識できませんでした")
        errors = importer.get_errors()
        for err in errors:
            print(f"  - {err}")
        return False
    
    # データインポート
    print(f"テスト用ファイルを見つけました: {file_path}")
    try:
        container = importer.import_data(file_path)
    except Exception as e:
        print(f"インポート中に例外が発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    if container is None and expected_success:
        print(f"[エラー] インポートに失敗しました")
        errors = importer.get_errors()
        for err in errors:
            print(f"  - {err}")
        return False
    elif container is not None and not expected_success:
        print(f"[エラー] インポートが成功してしまいました（失敗を期待）")
        return False
    
    # 警告があれば表示
    warnings = importer.get_warnings()
    if warnings:
        print(f"  [警告] {len(warnings)}件の警告があります")
        for warn in warnings[:3]:  # 最初の3件のみ表示
            print(f"    - {warn}")
        if len(warnings) > 3:
            print(f"    - ...他 {len(warnings) - 3}件")
    
    # 成功した場合はデータの確認
    if container is not None:
        df = container.data
        print(f"  [成功] {len(df)}行のデータをインポートしました")
        print(f"  タイムスタンプ範囲: {df['timestamp'].min()} ～ {df['timestamp'].max()}")
        print(f"  カラム: {', '.join(df.columns)}")
        
        # メタデータ
        meta_keys = list(container.metadata.keys())
        print(f"  メタデータキー: {', '.join(meta_keys[:5])}{' ...' if len(meta_keys) > 5 else ''}")
    
    return True

def test_factory_detection(file_path, expected_importer_name=None):
    """インポーターファクトリーのテスト"""
    print(f"[2] インポーターファクトリーのテスト: {file_path}")
    print(f"ファイル存在チェック: {file_path} - {os.path.exists(str(file_path))}")
    
    # インポーターの取得
    try:
        importer = ImporterFactory.get_importer(file_path)
    except Exception as e:
        print(f"インポーター取得中に例外が発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    if importer is None:
        print(f"[エラー] 適切なインポーターが見つかりませんでした")
        return False
    
    importer_name = importer.__class__.__name__
    print(f"検出されたインポーター: {importer_name}")
    
    if expected_importer_name and importer_name != expected_importer_name:
        print(f"[エラー] 期待されたインポーター({expected_importer_name})と異なります")
        return False
    
    return True

def test_batch_importer(file_paths):
    """バッチインポーターのテスト"""
    print(f"[3] バッチインポートのテスト: {len(file_paths)}ファイル")
    
    # ファイルの存在確認
    for file_path in file_paths:
        print(f"ファイル存在チェック: {file_path} - {os.path.exists(str(file_path))}")
    
    # バッチインポーター設定
    config = {
        'parallel': False,  # テスト時はシリアル実行に変更（エラー追跡を容易にするため）
        'max_workers': 1
    }
    
    try:
        batch_importer = BatchImporter(config)
        print("バッチインポーター作成成功")
    except Exception as e:
        print(f"バッチインポーター作成中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # インポート実行
    try:
        result = batch_importer.import_files(file_paths)
        print("インポート実行成功")
    except Exception as e:
        print(f"インポート実行中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 結果表示
    try:
        summary = result.get_summary()
        print(f"総ファイル数: {summary['total_files']}")
        print(f"成功: {summary['successful_count']}")
        print(f"失敗: {summary['failed_count']}")
        if 'warning_count' in summary:
            print(f"警告あり: {summary['warning_count']}")
    except Exception as e:
        print(f"結果表示中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 成功したファイル
    try:
        if summary['successful_count'] > 0:
            print(f"成功したファイル:")
            for i, (file_name, container) in enumerate(result.successful.items()):
                print(f"  {i+1}. {file_name} - {len(container.data)}行")
                if i >= 2:  # 最初の3つのみ表示
                    print(f"  ... 他 {summary['successful_count'] - 3}ファイル")
                    break
    except Exception as e:
        print(f"成功したファイル表示中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    # 失敗したファイル
    try:
        if summary['failed_count'] > 0:
            print(f"失敗したファイル:")
            for i, (file_name, errors) in enumerate(result.failed.items()):
                print(f"  {i+1}. {file_name} - {len(errors)}エラー")
                for j, err in enumerate(errors[:3]):  # 最初の3つのエラーのみ表示
                    print(f"    - {err}")
                if len(errors) > 3:
                    print(f"    ... 他 {len(errors) - 3}件のエラー")
                if i >= 2:  # 最初の3つのみ表示
                    print(f"  ... 他 {summary['failed_count'] - 3}ファイル")
                    break
    except Exception as e:
        print(f"失敗したファイル表示中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    # マージテスト
    if summary['successful_count'] > 1:
        try:
            print("マージテスト実行中...")
            merged = result.merge_containers()
            if merged:
                print(f"マージ結果: {len(merged.data)}行 ({summary['successful_count']}ファイルを結合)")
            else:
                print(f"[エラー] マージに失敗しました")
        except Exception as e:
            print(f"マージテスト中にエラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
    
    return summary['successful_count'] > 0

def main():
    # カレントディレクトリの確認
    cwd = os.getcwd()
    print(f"Current directory: {cwd}")
    
    # テスト用ファイルパスを設定（複数の可能性を確認）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Script directory: {script_dir}")
    
    # スクリプトの場所からの相対パス（pytest実行時）と
    # カレントディレクトリからの相対パス（直接実行時）の両方を確認
    test_dirs = [
        Path("test_data"), 
        Path("resources"),
        Path("tests/test_data"), 
        Path("tests/resources"),
        Path(os.path.join(script_dir, "test_data")),
        Path(os.path.join(script_dir, "resources")),
        Path(os.path.join(os.path.dirname(script_dir), "tests/test_data")),
        Path(os.path.join(os.path.dirname(script_dir), "tests/resources"))
    ]
    
    # すべての検索パスを表示
    print("検索パス:")
    for i, p in enumerate(test_dirs):
        print(f"  {i+1}. {p} (存在: {p.exists()})")
    
    # 有効なテストディレクトリを探す
    valid_test_dir = None
    for test_dir in test_dirs:
        if test_dir.exists():
            valid_test_dir = test_dir
            print(f"テストディレクトリが見つかりました: {test_dir}")
            break
    
    if valid_test_dir is None:
        print("テストディレクトリが見つかりません。以下のいずれかのパスにテストデータを配置してください:")
        for d in test_dirs:
            print(f"  - {d}")
        return
    
    # 各形式のテストファイルパス
    csv_file = valid_test_dir / "sample.csv"
    gpx_file = valid_test_dir / "sample.gpx"
    tcx_file = valid_test_dir / "sample.tcx"
    fit_file = valid_test_dir / "sample.fit"
    
    # バックアップパスを設定（明示的なパスも試す）
    backup_csv_files = [
        Path(os.path.join(script_dir, "test_data", "sample.csv")),
        Path(os.path.join(script_dir, "resources", "sample.csv")),
        Path("/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/tests/test_data/sample.csv"),
        Path("/Users/koki_air/Documents/GitHub/sailing-strategy-analyzer/tests/resources/sample.csv")
    ]
    
    # 存在確認
    test_files = []
    
    # メインパスでの確認
    if csv_file.exists(): 
        print(f"CSV file found at primary path: {csv_file}")
        test_files.append(csv_file)
    else:
        # バックアップパスから探す
        print("Primary CSV path not found, trying backup paths...")
        for backup_path in backup_csv_files:
            if backup_path.exists():
                print(f"CSV file found at backup path: {backup_path}")
                test_files.append(backup_path)
                break
    
    if not test_files:
        print("テスト用ファイルが見つかりません")
        print("以下のファイルをtest_dataディレクトリに配置してください:")
        print("  - sample.csv")
        print("  - sample.gpx")
        print("  - sample.tcx")
        print("  - sample.fit")
        return
    
    print(f"テストファイル: {[f.name for f in test_files]}")
    print("=" * 50)
    
    # 各インポーターのテスト
    print("\n1. 個別インポーターテスト")
    print("-" * 30)
    
    if csv_file.exists():
        csv_importer = CSVImporter()
        test_importer(csv_importer, csv_file)
    
    if gpx_file.exists():
        gpx_importer = GPXImporter()
        test_importer(gpx_importer, gpx_file)
    
    if tcx_file.exists():
        tcx_importer = TCXImporter()
        test_importer(tcx_importer, tcx_file)
    
    if fit_file.exists():
        fit_importer = FITImporter()
        test_importer(fit_importer, fit_file)
    
    # インポーターファクトリーのテスト
    print("\n2. インポーターファクトリーテスト")
    print("-" * 30)
    
    for file_path in test_files:
        expected_type = file_path.suffix[1:].upper() + "Importer"
        test_factory_detection(file_path, expected_type)
    
    # バッチインポーターのテスト
    if len(test_files) >= 2:
        print("\n3. バッチインポーターテスト")
        print("-" * 30)
        test_batch_importer(test_files)
    
    print("\nテスト完了")

if __name__ == "__main__":
    main()
