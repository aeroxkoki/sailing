#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSVインポーターテスト
"""

import os
import sys
from pathlib import Path
import pytest

# レポジトリのルートパスを追加
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

try:
    # インポーターモジュールをインポート
    from sailing_data_processor.importers.csv_importer import CSVImporter
    
    print("CSVImporterのインポートに成功しました")
except ImportError as e:
    print(f"インポートエラー: {e}")
    pytest.skip("CSVImporterのインポートに失敗しました", allow_module_level=True)


class TestCSVImporter:
    """CSVインポーターのテストクラス"""
    
    @pytest.fixture
    def test_file(self):
        """テスト用ファイルパスを取得するフィクスチャ"""
        # 現在のファイルからの相対パスを計算するために __file__ を使用
        current_dir = Path(__file__).parent
        project_root = Path(os.path.abspath(os.path.join(current_dir, "..")))
        
        test_file_paths = [
            # 相対パス（テストファイルからの相対）
            current_dir / "test_data" / "sample.csv",
            current_dir / "resources" / "sample.csv",
            # プロジェクトルートからの相対パス
            project_root / "tests" / "test_data" / "sample.csv",
            project_root / "tests" / "resources" / "sample.csv",
            # 絶対パス（変わらないパス）
            Path("test_data/sample.csv"),
            Path("resources/sample.csv"),
            Path("tests/test_data/sample.csv"),
            Path("tests/resources/sample.csv")
        ]
        
        # 有効なファイルパスを検索
        test_file = None
        for path in test_file_paths:
            if path.exists():
                test_file = path
                break
        
        if test_file is None:
            # 絶対パスも試してみる
            abs_test_paths = [
                os.path.join(os.getcwd(), "tests", "test_data", "sample.csv"),
                os.path.join(os.getcwd(), "tests", "resources", "sample.csv"),
                os.path.join(os.getcwd(), "test_data", "sample.csv"),
                os.path.join(os.getcwd(), "resources", "sample.csv")
            ]
            
            for path in abs_test_paths:
                if os.path.exists(path):
                    test_file = Path(path)
                    break
        
        if test_file is None:
            pytest.skip("テストファイルが見つかりません")
        
        return test_file
    
    def test_csv_importer_can_import(self, test_file):
        """CSVインポーターがファイルをインポート可能と判定できるかをテスト"""
        importer = CSVImporter({
            'auto_detect_columns': True  # 自動列マッピングを有効化
        })
        
        # インポート可能かどうかをチェック
        assert importer.can_import(test_file), "ファイルをインポート可能と判定されるべきです"
    
    def test_csv_structure_analysis(self, test_file):
        """CSVファイルの構造分析が正しく動作するかをテスト"""
        importer = CSVImporter({
            'auto_detect_columns': True  # 自動列マッピングを有効化
        })
        
        # CSVファイルの構造分析
        structure = importer.analyze_csv_structure(test_file)
        
        assert 'delimiter' in structure, "区切り文字の情報が含まれるべきです"
        assert 'has_header' in structure, "ヘッダー有無の情報が含まれるべきです"
        assert 'columns' in structure, "カラム情報が含まれるべきです"
        assert 'suggested_mapping' in structure, "推奨マッピング情報が含まれるべきです"
    
    def test_csv_data_import(self, test_file):
        """CSVデータのインポートが正しく動作するかをテスト"""
        importer = CSVImporter({
            'auto_detect_columns': True  # 自動列マッピングを有効化
        })
        
        # データをインポート
        container = importer.import_data(test_file)
        
        assert container is not None, "コンテナが返されるべきです"
        assert not container.data.empty, "データが空であってはいけません"
        
        # 必要なカラムが存在することを確認
        assert 'timestamp' in container.data.columns, "タイムスタンプカラムが必要です"
        assert 'latitude' in container.data.columns, "緯度カラムが必要です"
        assert 'longitude' in container.data.columns, "経度カラムが必要です"
        
        # 時間範囲の取得
        time_range = container.get_time_range()
        assert 'start' in time_range, "開始時刻が必要です"
        assert 'end' in time_range, "終了時刻が必要です"
        assert 'duration_seconds' in time_range, "期間（秒）が必要です"
        
        # メタデータの確認
        assert container.metadata is not None, "メタデータが必要です"
        assert 'csv_info' in container.metadata, "CSV情報が必要です"
