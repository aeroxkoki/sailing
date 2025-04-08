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
    print(f"テスト: {importer.__class__.__name__} - {file_path}")
    
    # インポート可能かチェック
    can_import = importer.can_import(file_path)
    print(f"  インポート可能: {can_import}")
    
    if not can_import and expected_success:
        print(f"  [エラー] ファイルを認識できませんでした")
        for err in importer.get_errors():
            print(f"    - {err}")
        return False
    
    # データインポート
    container = importer.import_data(file_path)
    
    if container is None and expected_success:
        print(f"  [エラー] インポートに失敗しました")
        for err in importer.get_errors():
            print(f"    - {err}")
        return False
    elif container is not None and not expected_success:
        print(f"  [エラー] インポートが成功してしまいました（失敗を期待）")
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
    print(f"ファクトリーテスト: {file_path}")
    
    # インポーターの取得
    importer = ImporterFactory.get_importer(file_path)
    
    if importer is None:
        print(f"  [エラー] 適切なインポーターが見つかりませんでした")
        return False
    
    importer_name = importer.__class__.__name__
    print(f"  検出されたインポーター: {importer_name}")
    
    if expected_importer_name and importer_name != expected_importer_name:
        print(f"  [エラー] 期待されたインポーター({expected_importer_name})と異なります")
        return False
    
    return True

def test_batch_importer(file_paths):
    """バッチインポーターのテスト"""
    print(f"バッチインポーターテスト: {len(file_paths)}ファイル")
    
    # バッチインポーター設定
    config = {
        'parallel': True,
        'max_workers': 2
    }
    batch_importer = BatchImporter(config)
    
    # インポート実行
    result = batch_importer.import_files(file_paths)
    
    # 結果表示
    summary = result.get_summary()
    print(f"  総ファイル数: {summary['total_files']}")
    print(f"  成功: {summary['successful_count']}")
    print(f"  失敗: {summary['failed_count']}")
    print(f"  警告あり: {summary['warning_count']}")
    
    # 成功したファイル
    if summary['successful_count'] > 0:
        print(f"  成功したファイル:")
        for i, (file_name, container) in enumerate(result.successful.items()):
            print(f"    {i+1}. {file_name} - {len(container.data)}行")
            if i >= 2:  # 最初の3つのみ表示
                print(f"    ... 他 {summary['successful_count'] - 3}ファイル")
                break
    
    # 失敗したファイル
    if summary['failed_count'] > 0:
        print(f"  失敗したファイル:")
        for i, (file_name, errors) in enumerate(result.failed.items()):
            print(f"    {i+1}. {file_name} - {len(errors)}エラー")
            if i >= 2:  # 最初の3つのみ表示
                print(f"    ... 他 {summary['failed_count'] - 3}ファイル")
                break
    
    # マージテスト
    if summary['successful_count'] > 1:
        merged = result.merge_containers()
        if merged:
            print(f"  マージ結果: {len(merged.data)}行 ({summary['successful_count']}ファイルを結合)")
        else:
            print(f"  [エラー] マージに失敗しました")
    
    return summary['successful_count'] > 0

def main():
    # テスト用ファイルパスを設定
    test_dir = Path("test_data")
    if not test_dir.exists():
        print(f"テストディレクトリが存在しません: {test_dir}")
        print("サンプルデータを含むテストディレクトリを作成してください")
        return
    
    # 各形式のテストファイルパス
    csv_file = test_dir / "sample.csv"
    gpx_file = test_dir / "sample.gpx"
    tcx_file = test_dir / "sample.tcx"
    fit_file = test_dir / "sample.fit"
    
    # 存在確認
    test_files = []
    if csv_file.exists(): test_files.append(csv_file)
    if gpx_file.exists(): test_files.append(gpx_file)
    if tcx_file.exists(): test_files.append(tcx_file)
    if fit_file.exists(): test_files.append(fit_file)
    
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
