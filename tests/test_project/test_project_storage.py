# -*- coding: utf-8 -*-
"""
Test module: sailing_data_processor.project.project_storage
Test target: ProjectStorage class
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


class TestProjectStorage:
    """
    Test for ProjectStorage class
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
    
    def test_create_directories(self, temp_dir):
        """Test for directory creation"""
        storage = ProjectStorage(temp_dir)
        
        # 必要なディレクトリが作成されていることを確認
        assert os.path.exists(os.path.join(temp_dir, "projects"))
        assert os.path.exists(os.path.join(temp_dir, "sessions"))
        assert os.path.exists(os.path.join(temp_dir, "results"))
        assert os.path.exists(os.path.join(temp_dir, "data"))
        assert os.path.exists(os.path.join(temp_dir, "states"))
    
    def test_save_load_project(self, storage, sample_project):
        """Test for saving and loading project"""
        # プロジェクトを保存
        success = storage.save_project(sample_project)
        assert success is True
        
        # キャッシュに追加されていることを確認
        assert sample_project.project_id in storage.projects
        
        # 保存されたファイルが存在することを確認
        project_file = os.path.join(storage.projects_path, f"{sample_project.project_id}.json")
        assert os.path.exists(project_file)
        
        # プロジェクトをキャッシュから削除してから読み込みtest
        project_id = sample_project.project_id
        storage.projects = {}
        storage._load_projects()
        
        # 読み込まれたプロジェクトを確認
        loaded_project = storage.get_project(project_id)
        assert loaded_project is not None
        assert loaded_project.name == "Test Project"
        assert loaded_project.description == "Project for testing"
        assert "test" in loaded_project.tags
        assert loaded_project.metadata["purpose"] == "testing"
    
    def test_save_load_session(self, storage, sample_session):
        """Test for saving and loading session"""
        # セッションを保存
        success = storage.save_session(sample_session)
        assert success is True
        
        # キャッシュに追加されていることを確認
        assert sample_session.session_id in storage.sessions
        
        # 保存されたファイルが存在することを確認
        session_file = os.path.join(storage.sessions_path, f"{sample_session.session_id}.json")
        assert os.path.exists(session_file)
        
        # セッションをキャッシュから削除してから読み込みtest
        session_id = sample_session.session_id
        storage.sessions = {}
        storage._load_sessions()
        
        # 読み込まれたセッションを確認
        loaded_session = storage.get_session(session_id)
        assert loaded_session is not None
        assert loaded_session.name == "Test Session"
        assert loaded_session.description == "Session for testing"
        assert "session" in loaded_session.tags
        assert loaded_session.metadata["location"] == "tokyo bay"
    
    def test_save_load_result(self, storage, sample_result):
        """Test for saving and loading analysis result"""
        # 分析結果を保存
        success = storage.save_result(sample_result)
        assert success is True
        
        # キャッシュに追加されていることを確認
        assert sample_result.result_id in storage.results
        
        # 保存されたファイルが存在することを確認
        result_file = os.path.join(storage.results_path, f"{sample_result.result_id}.json")
        assert os.path.exists(result_file)
        
        # 分析結果をキャッシュから削除してから読み込みtest
        result_id = sample_result.result_id
        storage.results = {}
        storage._load_results()
        
        # 読み込まれた分析結果を確認
        loaded_result = storage.get_result(result_id)
        assert loaded_result is not None
        assert loaded_result.name == "Test Result"
        assert loaded_result.result_type == "test_analysis"
        assert loaded_result.data["average"] == 2.0
        assert loaded_result.metadata["algorithm"] == "test"
    
    def test_create_project(self, storage):
        """Test for creating project"""
        # プロジェクトを作成
        project = storage.create_project(
            name="New Project",
            description="Newly created project",
            tags=["new", "test"],
            metadata={"status": "active"}
        )
        
        assert project is not None
        assert project.name == "New Project"
        assert "new" in project.tags
        
        # プロジェクトが保存されていることを確認
        project_id = project.project_id
        assert project_id in storage.projects
        
        # ファイルが作成されていることを確認
        project_file = os.path.join(storage.projects_path, f"{project_id}.json")
        assert os.path.exists(project_file)
    
    def test_create_session(self, storage):
        """Test for creating session"""
        # セッションを作成
        session = storage.create_session(
            name="New Session",
            description="Newly created session",
            tags=["new", "test"],
            metadata={"weather": "sunny"},
            category="training"
        )
        
        assert session is not None
        assert session.name == "New Session"
        assert session.category == "training"
        assert "new" in session.tags
        
        # セッションが保存されていることを確認
        session_id = session.session_id
        assert session_id in storage.sessions
        
        # ファイルが作成されていることを確認
        session_file = os.path.join(storage.sessions_path, f"{session_id}.json")
        assert os.path.exists(session_file)
    
    def test_create_result(self, storage):
        """Test for creating analysis result"""
        # 分析結果を作成
        data = {"max_speed": 15.5, "avg_speed": 10.2}
        result = storage.create_result(
            name="New Analysis Result",
            result_type="speed_analysis",
            data=data,
            description="Result of speed analysis",
            metadata={"units": "knots"}
        )
        
        assert result is not None
        assert result.name == "New Analysis Result"
        assert result.result_type == "speed_analysis"
        assert result.data["max_speed"] == 15.5
        
        # 分析結果が保存されていることを確認
        result_id = result.result_id
        assert result_id in storage.results
        
        # ファイルが作成されていることを確認
        result_file = os.path.join(storage.results_path, f"{result_id}.json")
        assert os.path.exists(result_file)
    
    def test_add_session_to_project(self, storage, sample_project, sample_session):
        """Test for adding session to project"""
        # プロジェクトとセッションを保存
        storage.save_project(sample_project)
        storage.save_session(sample_session)
        
        # セッションをプロジェクトに追加
        success = storage.add_session_to_project(
            project_id=sample_project.project_id,
            session_id=sample_session.session_id
        )
        
        assert success is True
        
        # プロジェクトのセッションリストを確認
        project = storage.get_project(sample_project.project_id)
        assert sample_session.session_id in project.sessions
    
    def test_add_result_to_session(self, storage, sample_session, sample_result):
        """Test for adding analysis result to session"""
        # セッションと分析結果を保存
        storage.save_session(sample_session)
        storage.save_result(sample_result)
        
        # 分析結果をセッションに追加
        success = storage.add_result_to_session(
            session_id=sample_session.session_id,
            result_id=sample_result.result_id
        )
        
        assert success is True
        
        # セッションの分析結果リストを確認
        session = storage.get_session(sample_session.session_id)
        assert sample_result.result_id in session.analysis_results
    
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
        results = storage.search_projects(query="東京")
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