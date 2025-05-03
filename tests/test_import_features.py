#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
インポート機能のテスト
"""

import sys
import os
import pandas as pd
from pathlib import Path
import pytest

# レポジトリのルートパスを追加
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def test_csv_importer():
    """CSVインポーターのテスト"""
    from sailing_data_processor.importers.csv_importer import CSVImporter
    
    csv_path = os.path.join("test_data", "sample.csv")
    csv_importer = CSVImporter()
    
    # ファイルがインポート可能か確認
    can_import = csv_importer.can_import(csv_path)
    assert can_import, f"CSVインポーターがファイル {csv_path} をインポートできません"
    
    # データをインポート
    container = csv_importer.import_data(csv_path)
    assert container is not None, "CSVインポーターがコンテナを返しませんでした"
    assert len(container.data) > 0, "インポートされたデータが空です"
    assert 'timestamp' in container.data.columns, "タイムスタンプ列が見つかりません"

def test_importer_factory():
    """インポーターファクトリーのテスト"""
    from sailing_data_processor.importers.importer_factory import ImporterFactory
    
    csv_path = os.path.join("test_data", "sample.csv")
    importer = ImporterFactory.get_importer(csv_path)
    
    assert importer is not None, "インポーターファクトリーがインポーターを見つけられませんでした"
    assert importer.__class__.__name__ == "CSVImporter", "期待されたインポーターが返されませんでした"

def test_data_validator():
    """データ検証のテスト"""
    from sailing_data_processor.importers.csv_importer import CSVImporter
    from sailing_data_processor.validation.data_validator import DataValidator
    
    csv_path = os.path.join("test_data", "sample.csv")
    csv_importer = CSVImporter()
    container = csv_importer.import_data(csv_path)
    
    # データ検証器を作成
    validator = DataValidator()
    
    # データを検証
    is_valid, results = validator.validate(container)
    
    assert isinstance(is_valid, bool), "検証結果が真偽値ではありません"
    assert isinstance(results, list), "検証結果がリストではありません"
    assert len(results) > 0, "検証結果が空です"

def test_batch_importer():
    """バッチインポートのテスト"""
    from sailing_data_processor.importers.batch_importer import BatchImporter
    
    csv_path = os.path.join("test_data", "sample.csv")
    
    # バッチインポーターを作成
    batch_importer = BatchImporter()
    
    # 単一ファイルでバッチインポートをテスト
    result = batch_importer.import_files([csv_path])
    
    # 結果サマリーを取得
    summary = result.get_summary()
    
    assert summary['total_files'] == 1, "総ファイル数が正しくありません"
    assert summary['successful_count'] == 1, "成功ファイル数が正しくありません"
    assert summary['failed_count'] == 0, "失敗ファイル数が正しくありません"

@pytest.mark.skipif(not os.path.exists("test_data/sample.csv"), reason="テストデータが存在しません")
def test_merge_containers():
    """コンテナのマージテスト"""
    from sailing_data_processor.importers.batch_importer import BatchImporter
    
    csv_path = os.path.join("test_data", "sample.csv")
    batch_importer = BatchImporter()
    result = batch_importer.import_files([csv_path])
    
    # マージテスト
    merged = result.merge_containers()
    assert merged is not None, "マージ結果がNullです"
    assert len(merged.data) > 0, "マージされたデータが空です"
