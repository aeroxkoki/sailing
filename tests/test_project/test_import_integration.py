"""
インポート連携クラスのユニットテスト
"""

import pytest
from unittest.mock import MagicMock, patch
import uuid
from datetime import datetime

from sailing_data_processor.project.import_integration import ImportIntegration
from sailing_data_processor.project.project_model import Project, Session
from sailing_data_processor.project.session_reference import SessionReference
from sailing_data_processor.data_model.container import GPSDataContainer
import pandas as pd

class TestImportIntegration:
    
    @pytest.fixture
    def mock_project_storage(self):
        """モックプロジェクトストレージ"""
        storage = MagicMock()
        
        # プロジェクトとセッションの初期化
        self.project1 = Project("テストプロジェクト1")
        self.project1.tags = ["テスト", "レース"]
        self.project1.metadata = {
            "event_date": "2023-12-01",
            "location": "東京湾"
        }
        
        self.project2 = Project("テストプロジェクト2")
        self.project2.tags = ["テスト", "練習"]
        
        self.session1 = Session("テストセッション1")
        self.session1.tags = ["テスト"]
        
        self.session2 = Session("テストセッション2")
        self.session2.tags = ["レース"]
        self.session2.metadata = {
            "event_date": "2023-12-01"
        }
        
        # モックメソッドの設定
        storage.get_project.side_effect = lambda pid: {
            self.project1.project_id: self.project1,
            self.project2.project_id: self.project2
        }.get(pid)
        
        storage.get_session.side_effect = lambda sid: {
            self.session1.session_id: self.session1,
            self.session2.session_id: self.session2
        }.get(sid)
        
        storage.get_projects.return_value = [self.project1, self.project2]
        
        storage.save_project.return_value = True
        storage.save_session.return_value = True
        storage.save_container.return_value = True
        
        storage.create_project.side_effect = lambda name, desc, tags, metadata: Project(
            name, desc, tags, metadata
        )
        
        return storage
    
    @pytest.fixture
    def integration(self, mock_project_storage):
        """インポート連携インスタンス"""
        return ImportIntegration(mock_project_storage)
    
    @pytest.fixture
    def sample_container(self):
        """サンプルGPSデータコンテナ"""
        data = {
            'timestamp': pd.date_range(start='2023-12-01', periods=10, freq='1min'),
            'latitude': [35.65 + i*0.001 for i in range(10)],
            'longitude': [139.76 + i*0.001 for i in range(10)],
            'speed': [5.0 + i*0.1 for i in range(10)],
            'heading': [45.0 + i for i in range(10)]
        }
        df = pd.DataFrame(data)
        return GPSDataContainer(df)
    
    def test_assign_to_project(self, integration, mock_project_storage):
        """プロジェクトへのセッション割り当てテスト"""
        # テスト実行
        result = integration.assign_to_project(
            self.session1.session_id,
            self.project1.project_id
        )
        
        # 結果の検証
        assert result is True
        assert self.session1.session_id in self.project1.sessions
        mock_project_storage.save_project.assert_called_once()
        
        # セッション参照が正しく作成されたか確認
        assert "session_references" in self.project1.metadata
        assert self.session1.session_id in self.project1.metadata["session_references"]
        
        reference_data = self.project1.metadata["session_references"][self.session1.session_id]
        assert reference_data["session_id"] == self.session1.session_id
        assert reference_data["display_name"] == self.session1.name
    
    def test_assign_to_project_with_display_name(self, integration, mock_project_storage):
        """カスタム表示名でのプロジェクトへのセッション割り当てテスト"""
        custom_name = "カスタム表示名"
        
        # テスト実行
        result = integration.assign_to_project(
            self.session1.session_id,
            self.project1.project_id,
            display_name=custom_name
        )
        
        # 結果の検証
        assert result is True
        reference_data = self.project1.metadata["session_references"][self.session1.session_id]
        assert reference_data["display_name"] == custom_name
    
    def test_assign_nonexistent_session(self, integration, mock_project_storage):
        """存在しないセッションの割り当てテスト"""
        # モック設定を更新
        mock_project_storage.get_session.return_value = None
        
        # テスト実行
        result = integration.assign_to_project(
            "nonexistent_session",
            self.project1.project_id
        )
        
        # 結果の検証
        assert result is False
        mock_project_storage.save_project.assert_not_called()
    
    def test_assign_nonexistent_project(self, integration, mock_project_storage):
        """存在しないプロジェクトへの割り当てテスト"""
        # モック設定を更新
        mock_project_storage.get_project.return_value = None
        
        # テスト実行
        result = integration.assign_to_project(
            self.session1.session_id,
            "nonexistent_project"
        )
        
        # 結果の検証
        assert result is False
        mock_project_storage.save_project.assert_not_called()
    
    def test_remove_from_project(self, integration, mock_project_storage):
        """プロジェクトからのセッション削除テスト"""
        # セッションを追加
        self.project1.add_session(self.session1.session_id)
        self.project1.metadata["session_references"] = {
            self.session1.session_id: SessionReference(
                self.session1.session_id,
                self.session1.name
            ).to_dict()
        }
        
        # テスト実行
        result = integration.remove_from_project(
            self.session1.session_id,
            self.project1.project_id
        )
        
        # 結果の検証
        assert result is True
        assert self.session1.session_id not in self.project1.sessions
        assert self.session1.session_id not in self.project1.metadata["session_references"]
        mock_project_storage.save_project.assert_called_once()
    
    def test_update_session_reference(self, integration, mock_project_storage):
        """セッション参照更新テスト"""
        # セッションを追加
        self.project1.add_session(self.session1.session_id)
        self.project1.metadata["session_references"] = {
            self.session1.session_id: SessionReference(
                self.session1.session_id,
                "元の表示名"
            ).to_dict()
        }
        
        # テスト実行
        result = integration.update_session_reference(
            self.project1.project_id,
            self.session1.session_id,
            display_name="新しい表示名",
            description="新しい説明",
            order=3,
            view_settings={"visible": False}
        )
        
        # 結果の検証
        assert result is True
        reference_data = self.project1.metadata["session_references"][self.session1.session_id]
        assert reference_data["display_name"] == "新しい表示名"
        assert reference_data["description"] == "新しい説明"
        assert reference_data["order"] == 3
        assert reference_data["view_settings"]["visible"] is False
        mock_project_storage.save_project.assert_called_once()
    
    def test_update_nonexistent_reference(self, integration, mock_project_storage):
        """存在しないセッション参照の更新テスト（自動作成）"""
        # セッションをプロジェクトに追加（参照なし）
        self.project1.add_session(self.session1.session_id)
        
        # テスト実行
        result = integration.update_session_reference(
            self.project1.project_id,
            self.session1.session_id,
            display_name="新しい表示名"
        )
        
        # 結果の検証
        assert result is True
        assert "session_references" in self.project1.metadata
        assert self.session1.session_id in self.project1.metadata["session_references"]
        reference_data = self.project1.metadata["session_references"][self.session1.session_id]
        assert reference_data["display_name"] == "新しい表示名"
    
    def test_process_import_result(self, integration, mock_project_storage, sample_container):
        """インポート結果処理テスト（特定プロジェクト）"""
        # テスト用セッション
        session = Session("インポートセッション")
        
        # テスト実行
        success, project_id = integration.process_import_result(
            session,
            sample_container,
            target_project_id=self.project1.project_id
        )
        
        # 結果の検証
        assert success is True
        assert project_id == self.project1.project_id
        mock_project_storage.save_session.assert_called_once_with(session)
        mock_project_storage.save_container.assert_called_once()
    
    def test_auto_assign_project_by_tag(self, integration, mock_project_storage, sample_container):
        """タグによる自動プロジェクト割り当てテスト"""
        # タグ付きセッション
        session = Session("レースセッション")
        session.add_tag("レース")
        
        # テスト実行（自動割り当て）
        success, project_id = integration.process_import_result(
            session,
            sample_container,
            auto_assign=True
        )
        
        # 結果の検証
        assert success is True
        assert project_id == self.project1.project_id  # project1は"レース"タグを持つ
    
    def test_auto_assign_project_by_date(self, integration, mock_project_storage, sample_container):
        """日付による自動プロジェクト割り当てテスト"""
        # 日付付きセッション
        session = Session("日付セッション")
        session.metadata["event_date"] = "2023-12-01"
        
        # テスト実行（自動割り当て）
        success, project_id = integration.process_import_result(
            session,
            sample_container,
            auto_assign=True
        )
        
        # 結果の検証
        assert success is True
        assert project_id == self.project1.project_id  # project1は同じイベント日を持つ
    
    def test_apply_project_settings(self, integration, mock_project_storage):
        """プロジェクト設定の適用テスト"""
        # プロジェクト設定
        self.project1.metadata["default_session_settings"] = {
            "boat_type": "J24",
            "crew_info": "4人乗り"
        }
        
        # テスト実行
        result = integration.apply_project_settings(
            self.session1.session_id,
            self.project1.project_id
        )
        
        # 結果の検証
        assert result is True
        assert "boat_type" in self.session1.metadata
        assert self.session1.metadata["boat_type"] == "J24"
        assert "crew_info" in self.session1.metadata
        assert self.session1.metadata["crew_info"] == "4人乗り"
        
        # タグ継承のテスト
        for tag in self.project1.tags:
            assert tag in self.session1.tags
    
    def test_process_batch_import(self, integration, mock_project_storage, sample_container):
        """バッチインポート処理テスト"""
        # テスト用セッション
        session1 = Session("バッチセッション1")
        session1.add_tag("レース")
        session2 = Session("バッチセッション2")
        
        # コンテナ辞書の作成
        containers = {
            session1.session_id: sample_container,
            session2.session_id: sample_container
        }
        
        # テスト実行
        results = integration.process_batch_import(
            [session1, session2],
            containers,
            target_project_id=self.project2.project_id
        )
        
        # 結果の検証
        assert len(results) == 2
        assert session1.session_id in results
        assert session2.session_id in results
        assert results[session1.session_id] == self.project2.project_id
        assert results[session2.session_id] == self.project2.project_id
        assert mock_project_storage.save_session.call_count == 2
        assert mock_project_storage.save_container.call_count == 2
    
    def test_create_project_for_import(self, integration, mock_project_storage, sample_container):
        """インポート用プロジェクト作成テスト"""
        # テスト用セッション
        session = Session("新規プロジェクトセッション")
        
        # テスト実行
        project_id = integration.create_project_for_import(
            "新規プロジェクト",
            description="インポート用に作成されたプロジェクト",
            tags=["インポート", "テスト"],
            sessions=[session],
            containers={session.session_id: sample_container}
        )
        
        # 結果の検証
        assert project_id is not None
        mock_project_storage.create_project.assert_called_once()
        mock_project_storage.save_session.assert_called_once_with(session)
        mock_project_storage.save_container.assert_called_once()
