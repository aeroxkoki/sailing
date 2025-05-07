# -*- coding: utf-8 -*-
"""
Unit test for Import Integration class
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
        """Mock project storage"""
        storage = MagicMock()
        
        # プロジェクトとセッションの初期化
        self.project1 = Project("Test Project1")
        self.project1.tags = ["test", "race"]
        self.project1.metadata = {
            "event_date": "2023-12-01",
            "location": "Tokyo Bay"
        }
        
        self.project2 = Project("Test Project2")
        self.project2.tags = ["test", "practice"]
        
        self.session1 = Session("Test Session1")
        self.session1.tags = ["test"]
        
        self.session2 = Session("Test Session2")
        self.session2.tags = ["race"]
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
        """Import integration instance"""
        return ImportIntegration(mock_project_storage)
    
    @pytest.fixture
    def sample_container(self):
        """Sample GPS data container"""
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
        """Test for assigning session to project"""
        # test実行
        result = integration.assign_to_project(
            self.session1.session_id,
            self.project1.project_id
        )
        
        # 結果の検証
        assert result is True
        assert self.session1.session_id in self.project1.sessions
        mock_project_storage.save_project.assert_called_once()
        
        # Verify the session reference is correctly created
        assert "session_references" in self.project1.metadata
        assert self.session1.session_id in self.project1.metadata["session_references"]
        
        reference_data = self.project1.metadata["session_references"][self.session1.session_id]
        assert reference_data["session_id"] == self.session1.session_id
        assert reference_data["display_name"] == self.session1.name
    
    def test_assign_to_project_with_display_name(self, integration, mock_project_storage):
        """Custom Display NameでのTest for assigning session to project"""
        custom_name = "Custom Display Name"
        
        # test実行
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
        """Test for assigning non-existent session"""
        # モック設定を更新
        mock_project_storage.get_session.return_value = None
        
        # test実行
        result = integration.assign_to_project(
            "nonexistent_session",
            self.project1.project_id
        )
        
        # 結果の検証
        assert result is False
        mock_project_storage.save_project.assert_not_called()
    
    def test_assign_nonexistent_project(self, integration, mock_project_storage):
        """Test for assigning to non-existent project"""
        # モック設定を更新
        mock_project_storage.get_project.return_value = None
        
        # test実行
        result = integration.assign_to_project(
            self.session1.session_id,
            "nonexistent_project"
        )
        
        # 結果の検証
        assert result is False
        mock_project_storage.save_project.assert_not_called()
    
    def test_remove_from_project(self, integration, mock_project_storage):
        """Test for removing session from project"""
        # セッションを追加
        self.project1.add_session(self.session1.session_id)
        self.project1.metadata["session_references"] = {
            self.session1.session_id: SessionReference(
                self.session1.session_id,
                self.session1.name
            ).to_dict()
        }
        
        # test実行
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
        """Test for updating session reference"""
        # セッションを追加
        self.project1.add_session(self.session1.session_id)
        self.project1.metadata["session_references"] = {
            self.session1.session_id: SessionReference(
                self.session1.session_id,
                "Original Display Name"
            ).to_dict()
        }
        
        # test実行
        result = integration.update_session_reference(
            self.project1.project_id,
            self.session1.session_id,
            display_name="New Display Name",
            description="New Description",
            order=3,
            view_settings={"visible": False}
        )
        
        # 結果の検証
        assert result is True
        reference_data = self.project1.metadata["session_references"][self.session1.session_id]
        assert reference_data["display_name"] == "New Display Name"
        assert reference_data["description"] == "New Description"
        assert reference_data["order"] == 3
        assert reference_data["view_settings"]["visible"] is False
        mock_project_storage.save_project.assert_called_once()
    
    def test_update_nonexistent_reference(self, integration, mock_project_storage):
        """Test for updating non-existent session reference (auto-creation)"""
        # セッションをプロジェクトに追加（参照なし）
        self.project1.add_session(self.session1.session_id)
        
        # test実行
        result = integration.update_session_reference(
            self.project1.project_id,
            self.session1.session_id,
            display_name="New Display Name"
        )
        
        # 結果の検証
        assert result is True
        assert "session_references" in self.project1.metadata
        assert self.session1.session_id in self.project1.metadata["session_references"]
        reference_data = self.project1.metadata["session_references"][self.session1.session_id]
        assert reference_data["display_name"] == "New Display Name"
    
    def test_process_import_result(self, integration, mock_project_storage, sample_container):
        """Test for processing import result (specific project)"""
        # test用セッション
        session = Session("Import Session")
        
        # モックの設定：assign_to_projectの戻り値をTrueに設定
        mock_project_storage.get_project.return_value = self.project1
        mock_project_storage.get_session.return_value = session
        integration.assign_to_project = MagicMock(return_value=True)
        
        # test実行
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
        """Test for automatic project assignment by tag"""
        # タグ付きセッション
        session = Session("raceセッション")
        session.add_tag("race")
        
        # 自動割り当てのモック：常にproject1のIDを返すよう設定
        integration._auto_assign_project = MagicMock(return_value=self.project1.project_id)
        integration.assign_to_project = MagicMock(return_value=True)
        
        # test実行（自動割り当て）
        success, project_id = integration.process_import_result(
            session,
            sample_container,
            auto_assign=True
        )
        
        # 結果の検証
        assert success is True
        assert project_id == self.project1.project_id  # project1は"race"タグを持つ
        
        # _auto_assign_projectが呼ばれたことを確認
        integration._auto_assign_project.assert_called_once_with(session, sample_container)
    
    def test_auto_assign_project_by_date(self, integration, mock_project_storage, sample_container):
        """Test for automatic project assignment by date"""
        # 日付付きセッション
        session = Session("Date Session")
        session.metadata["event_date"] = "2023-12-01"
        
        # 自動割り当てのモック：常にproject1のIDを返すよう設定
        integration._auto_assign_project = MagicMock(return_value=self.project1.project_id)
        integration.assign_to_project = MagicMock(return_value=True)
        
        # test実行（自動割り当て）
        success, project_id = integration.process_import_result(
            session,
            sample_container,
            auto_assign=True
        )
        
        # 結果の検証
        assert success is True
        assert project_id == self.project1.project_id  # project1は同じイベント日を持つ
        
        # _auto_assign_projectが呼ばれたことを確認
        integration._auto_assign_project.assert_called_once_with(session, sample_container)
    
    def test_apply_project_settings(self, integration, mock_project_storage):
        """Test for applying project settings"""
        # プロジェクト設定
        self.project1.metadata["default_session_settings"] = {
            "boat_type": "J24",
            "crew_info": "4-person crew"
        }
        
        # test実行
        result = integration.apply_project_settings(
            self.session1.session_id,
            self.project1.project_id
        )
        
        # 結果の検証
        assert result is True
        assert "boat_type" in self.session1.metadata
        assert self.session1.metadata["boat_type"] == "J24"
        assert "crew_info" in self.session1.metadata
        assert self.session1.metadata["crew_info"] == "4-person crew"
        
        # Test for tag inheritance
        for tag in self.project1.tags:
            assert tag in self.session1.tags
    
    def test_process_batch_import(self, integration, mock_project_storage, sample_container):
        """Test for batch import processing"""
        # test用セッション
        session1 = Session("バッチSession 1")
        session1.add_tag("race")
        session2 = Session("Batch Session 2")
        
        # コンテナ辞書の作成
        containers = {
            session1.session_id: sample_container,
            session2.session_id: sample_container
        }
        
        # test実行
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
        """Test for creating project for import"""
        # test用セッション
        session = Session("New Projectセッション")
        
        # test実行
        project_id = integration.create_project_for_import(
            "New Project",
            description="Project created for import",
            tags=["import", "test"],
            sessions=[session],
            containers={session.session_id: sample_container}
        )
        
        # 結果の検証
        assert project_id is not None
        mock_project_storage.create_project.assert_called_once()
        mock_project_storage.save_session.assert_called_once_with(session)
        mock_project_storage.save_container.assert_called_once()