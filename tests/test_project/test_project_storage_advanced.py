# -*- coding: utf-8 -*-
"""
Test module: sailing_data_processor.project.project_storage (Advanced operations)
Test target: ProjectStorage class advanced functionalities
"""

import os
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from sailing_data_processor.project.project_model import Project, Session, AnalysisResult
from sailing_data_processor.project.project_storage import ProjectStorage
from sailing_data_processor.project.exceptions import ProjectError, ProjectNotFoundError, ProjectStorageError, InvalidProjectData


class TestProjectStorageAdvanced:
    """
    Test for ProjectStorage class advanced operations
    """
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage(self, temp_dir):
        """Create ProjectStorage instance for testing"""
        return ProjectStorage(temp_dir)
    
    @pytest.fixture
    def sample_project(self):
        """Create sample project"""
        project = Project(
            name="Test Project",
            description="Project for testing",
            tags=["test", "sample"],
            metadata={"purpose": "testing"}
        )
        return project
    
    @pytest.fixture
    def sample_session(self):
        """Create sample session"""
        session = Session(
            name="Test Session",
            description="Session for testing",
            tags=["test", "session"],
            metadata={"location": "tokyo bay"}
        )
        return session
    
    @pytest.fixture
    def sample_result(self):
        """Create sample analysis result"""
        data = {"values": [1, 2, 3], "average": 2.0}
        result = AnalysisResult(
            name="Test Result",
            result_type="test_analysis",
            data=data,
            description="Analysis result for testing",
            metadata={"algorithm": "test"}
        )
        return result
    
    def test_get_project_sessions(self, storage, sample_project, sample_session):
        """Test for getting sessions related to project"""
        # プロジェクトとセッションを保存
        storage.save_project(sample_project)
        storage.save_session(sample_session)
        
        # セッションをプロジェクトに追加
        storage.add_session_to_project(
            project_id=sample_project.project_id,
            session_id=sample_session.session_id
        )
        
        # プロジェクトに関連するセッションを取得
        sessions = storage.get_project_sessions(sample_project.project_id)
        
        assert len(sessions) == 1
        assert sessions[0].session_id == sample_session.session_id
        assert sessions[0].name == "Test Session"
    
    def test_get_session_results(self, storage, sample_session, sample_result):
        """Test for getting analysis results related to session"""
        # セッションと分析結果を保存
        storage.save_session(sample_session)
        storage.save_result(sample_result)
        
        # 分析結果をセッションに追加
        storage.add_result_to_session(
            session_id=sample_session.session_id,
            result_id=sample_result.result_id
        )
        
        # セッションに関連する分析結果を取得
        results = storage.get_session_results(sample_session.session_id)
        
        assert len(results) == 1
        assert results[0].result_id == sample_result.result_id
        assert results[0].name == "Test Result"
    
    def test_delete_project(self, storage, sample_project, sample_session):
        """Test for deleting project"""
        # プロジェクトとセッションを保存
        storage.save_project(sample_project)
        storage.save_session(sample_session)
        
        # セッションをプロジェクトに追加
        storage.add_session_to_project(
            project_id=sample_project.project_id,
            session_id=sample_session.session_id
        )
        
        # プロジェクトファイルパスを記憶
        project_file = os.path.join(storage.projects_path, f"{sample_project.project_id}.json")
        
        # プロジェクトを削除（関連セッションは削除しない）
        success = storage.delete_project(
            project_id=sample_project.project_id,
            delete_sessions=False
        )
        
        assert success is True
        
        # プロジェクトがキャッシュから削除されていることを確認
        assert sample_project.project_id not in storage.projects
        
        # プロジェクトファイルが削除されていることを確認
        assert not os.path.exists(project_file)
        
        # セッションは削除されていないことを確認
        assert sample_session.session_id in storage.sessions
    
    def test_delete_session(self, storage, sample_project, sample_session, sample_result):
        """Test for deleting session"""
        # プロジェクト、セッション、分析結果を保存
        storage.save_project(sample_project)
        storage.save_session(sample_session)
        storage.save_result(sample_result)
        
        # セッションをプロジェクトに追加
        storage.add_session_to_project(
            project_id=sample_project.project_id,
            session_id=sample_session.session_id
        )
        
        # 分析結果をセッションに追加
        storage.add_result_to_session(
            session_id=sample_session.session_id,
            result_id=sample_result.result_id
        )
        
        # セッションファイルパスを記憶
        session_file = os.path.join(storage.sessions_path, f"{sample_session.session_id}.json")
        
        # セッションを削除（関連データは削除しない）
        success = storage.delete_session(
            session_id=sample_session.session_id,
            delete_data=False
        )
        
        assert success is True
        
        # セッションがキャッシュから削除されていることを確認
        assert sample_session.session_id not in storage.sessions
        
        # セッションファイルが削除されていることを確認
        assert not os.path.exists(session_file)
        
        # セッションがプロジェクトから削除されていることを確認
        project = storage.get_project(sample_project.project_id)
        assert sample_session.session_id not in project.sessions
        
        # 分析結果は削除されていないことを確認
        assert sample_result.result_id in storage.results
    
    def test_search_projects(self, storage):
        """Test for searching projects"""
        # 複数のプロジェクトを作成
        project1 = storage.create_project(
            name="Sailing Competition",
            description="Race in Tokyo Bay",
            tags=["race", "tokyo"]
        )
        
        project2 = storage.create_project(
            name="Practice Session",
            description="Practice in Yokohama",
            tags=["practice", "yokohama"]
        )
        
        project3 = storage.create_project(
            name="Analysis Project",
            description="Wind direction analysis",
            tags=["analysis", "wind", "tokyo"]
        )
        
        # 名前・説明による検索
        results = storage.search_projects(query="tokyo")
        assert len(results) == 1
        assert results[0].project_id == project1.project_id
        
        # タグによる検索
        results = storage.search_projects(tags=["tokyo"])
        assert len(results) == 2
        project_ids = [p.project_id for p in results]
        assert project1.project_id in project_ids
        assert project3.project_id in project_ids
        
        # 複合検索
        results = storage.search_projects(query="分析", tags=["wind"])
        assert len(results) == 1
        assert results[0].project_id == project3.project_id
    
    def test_get_all_tags(self, storage):
        """Test for getting all tags"""
        # タグを持つプロジェクトとセッションを作成
        storage.create_project(
            name="Project 1",
            tags=["tag1", "tag2"]
        )
        
        storage.create_project(
            name="Project 2",
            tags=["tag2", "tag3"]
        )
        
        storage.create_session(
            name="Session 1",
            tags=["tag3", "tag4"]
        )
        
        # すべてのタグを取得
        tags = storage.get_all_tags()
        
        assert isinstance(tags, set)
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags
        assert "tag4" in tags
        assert len(tags) == 4
    
    def test_get_root_projects(self, storage):
        """Test for getting root projects"""
        # 親子関係のあるプロジェクトを作成
        parent = storage.create_project(
            name="Parent Project"
        )
        
        child = storage.create_project(
            name="Child Project",
            parent_id=parent.project_id
        )
        
        another_root = storage.create_project(
            name="Another Root Project"
        )
        
        # ルートプロジェクトを取得
        root_projects = storage.get_root_projects()
        
        assert len(root_projects) == 2
        root_ids = [p.project_id for p in root_projects]
        assert parent.project_id in root_ids
        assert another_root.project_id in root_ids
        assert child.project_id not in root_ids
    
    def test_get_sub_projects(self, storage):
        """Test for getting sub-projects"""
        # Parent Projectを作成
        parent = storage.create_project(
            name="Parent Project"
        )
        
        # Child Projectを作成
        child1 = storage.create_project(
            name="子Project 1",
            parent_id=parent.project_id
        )
        
        child2 = storage.create_project(
            name="子Project 2",
            parent_id=parent.project_id
        )
        
        # Parent Projectのサブプロジェクトリストを確認
        parent_refreshed = storage.get_project(parent.project_id)
        assert len(parent_refreshed.sub_projects) == 2
        assert child1.project_id in parent_refreshed.sub_projects
        assert child2.project_id in parent_refreshed.sub_projects
        
        # サブプロジェクトを取得
        sub_projects = storage.get_sub_projects(parent.project_id)
        
        assert len(sub_projects) == 2
        sub_ids = [p.project_id for p in sub_projects]
        assert child1.project_id in sub_ids
        assert child2.project_id in sub_ids
