# -*- coding: utf-8 -*-
"""
テスト: アプリケーションの主要ワークフローのテスト

このモジュールでは、アプリケーションの主要なワークフローに関するテストを提供します。
実際のStreamlitアプリケーションを実行せずにコア機能をテストします。
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path
import json

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# モジュールのインポート
from sailing_data_processor.project.project import Project
from sailing_data_processor.project.session import Session
from sailing_data_processor.storage.local_storage import LocalStorageManager
from sailing_data_processor.importers.csv_importer import CSVImporter
from sailing_data_processor.importers.gpx_importer import GPXImporter
from sailing_data_processor.analysis.wind_estimator import WindEstimator
from sailing_data_processor.analysis.strategy_detector import StrategyDetector
from sailing_data_processor.exporters.csv_exporter import CSVExporter
from sailing_data_processor.exporters.json_exporter import JSONExporter


class TestAppWorkflow:
    """アプリケーションのワークフロー統合テスト"""
    
    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリを作成して提供するフィクスチャ"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # テスト後にディレクトリを削除
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_project(self, temp_dir):
        """テスト用のプロジェクトを作成"""
        project = Project(
            name="テストプロジェクト",
            description="テスト用プロジェクト",
            created_date="2023-04-09",
            last_modified="2023-04-09",
            tags=["テスト", "統合"],
            storage_path=temp_dir
        )
        return project
    
    @pytest.fixture
    def sample_session(self, sample_project):
        """テスト用のセッションを作成"""
        session = Session(
            name="テストセッション",
            description="テスト用セッション",
            date="2023-04-09",
            boat_type="テスト艇",
            location="テスト湾",
            tags=["テスト", "セッション"],
            project_id=sample_project.id
        )
        return session
    
    @pytest.fixture
    def sample_data(self):
        """テスト用のデータフレームを作成"""
        # タイムスタンプ、位置、速度を含むサンプルデータ
        data = {
            'timestamp': pd.date_range(start='2023-04-09 10:00:00', periods=100, freq='10s'),
            'latitude': np.linspace(35.45, 35.46, 100),
            'longitude': np.linspace(139.65, 139.67, 100),
            'speed': np.random.uniform(4.0, 8.0, 100),
            'course': np.random.uniform(0, 360, 100)
        }
        return pd.DataFrame(data)
    
    def test_full_workflow(self, temp_dir, sample_project, sample_session, sample_data):
        """完全なワークフローのテスト: インポート→分析→エクスポート"""
        # 1. ストレージマネージャーの初期化
        storage = LocalStorageManager(base_path=temp_dir)
        
        # 2. プロジェクトの保存
        storage.save_project(sample_project)
        
        # 3. セッションの保存とプロジェクトへの紐付け
        sample_project.add_session(sample_session)
        storage.save_session(sample_session)
        
        # 4. サンプルデータのCSV生成
        csv_path = os.path.join(temp_dir, "sample_data.csv")
        sample_data.to_csv(csv_path, index=False)
        
        # 5. CSVインポーター使用
        importer = CSVImporter()
        imported_data = importer.import_file(
            file_path=csv_path,
            column_mapping={
                'timestamp': 'timestamp',
                'latitude': 'latitude', 
                'longitude': 'longitude',
                'speed': 'speed',
                'course': 'course'
            }
        )
        
        # 6. セッションへのデータ格納
        sample_session.set_data(imported_data)
        storage.save_session(sample_session)
        
        # 7. 風推定実行
        wind_estimator = WindEstimator()
        wind_data = wind_estimator.estimate_wind(sample_session.get_data())
        
        # 8. 戦略検出実行
        strategy_detector = StrategyDetector()
        strategy_points = strategy_detector.detect_strategy_points(wind_data)
        
        # 9. 分析結果のセッションへの保存
        sample_session.set_data(wind_data)
        sample_session.set_metadata('strategy_points', strategy_points)
        storage.save_session(sample_session)
        
        # 10. データのエクスポート
        export_path = os.path.join(temp_dir, "exported_data.csv")
        exporter = CSVExporter()
        exporter.export(wind_data, export_path)
        
        # 11. 結果の検証
        assert os.path.exists(export_path), "エクスポートファイルが存在しません"
        
        # プロジェクトの取得と検証
        loaded_project = storage.load_project(sample_project.id)
        assert loaded_project.name == sample_project.name
        
        # セッションの取得と検証
        loaded_session = storage.load_session(sample_session.id)
        assert loaded_session.name == sample_session.name
        
        # 戦略ポイントのメタデータを検証
        assert 'strategy_points' in loaded_session.metadata
        
        # エクスポートされたデータを検証
        exported_data = pd.read_csv(export_path)
        assert len(exported_data) == len(sample_data)
        
        print("完全なワークフローのテストが成功しました")

    def test_project_management(self, temp_dir):
        """プロジェクト管理機能のテスト"""
        # ストレージマネージャーの初期化
        storage = LocalStorageManager(base_path=temp_dir)
        
        # 複数のプロジェクト作成
        projects = []
        for i in range(3):
            project = Project(
                name=f"プロジェクト {i+1}",
                description=f"プロジェクト {i+1} の説明",
                created_date="2023-04-09",
                tags=[f"タグ{i+1}"]
            )
            storage.save_project(project)
            projects.append(project)
        
        # プロジェクト一覧の取得と検証
        project_list = storage.list_projects()
        assert len(project_list) == 3
        
        # プロジェクトの更新
        projects[0].name = "更新されたプロジェクト"
        storage.save_project(projects[0])
        
        # 更新の検証
        updated_project = storage.load_project(projects[0].id)
        assert updated_project.name == "更新されたプロジェクト"
        
        # プロジェクトの削除
        storage.delete_project(projects[2].id)
        
        # 削除の検証
        remaining_projects = storage.list_projects()
        assert len(remaining_projects) == 2
        
        print("プロジェクト管理機能のテストが成功しました")

    def test_data_import_export(self, temp_dir, sample_project, sample_session, sample_data):
        """データのインポートとエクスポートのテスト"""
        # ストレージマネージャーの初期化
        storage = LocalStorageManager(base_path=temp_dir)
        
        # プロジェクトとセッションの保存
        storage.save_project(sample_project)
        sample_project.add_session(sample_session)
        storage.save_session(sample_session)
        
        # CSVエクスポートとインポート
        csv_path = os.path.join(temp_dir, "test_data.csv")
        sample_data.to_csv(csv_path, index=False)
        
        # インポート
        importer = CSVImporter()
        imported_data = importer.import_file(
            file_path=csv_path,
            column_mapping={
                'timestamp': 'timestamp',
                'latitude': 'latitude', 
                'longitude': 'longitude',
                'speed': 'speed',
                'course': 'course'
            }
        )
        
        # セッションへのデータ格納
        sample_session.set_data(imported_data)
        storage.save_session(sample_session)
        
        # JSONエクスポート
        json_path = os.path.join(temp_dir, "test_data.json")
        exporter = JSONExporter()
        exporter.export(imported_data, json_path)
        
        # 検証
        assert os.path.exists(csv_path), "CSVファイルが存在しません"
        assert os.path.exists(json_path), "JSONファイルが存在しません"
        
        # JSONファイルの内容検証
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        assert len(json_data) == len(sample_data)
        
        print("データのインポートとエクスポートのテストが成功しました")
