# -*- coding: utf-8 -*-
"""
Test module: sailing_data_processor.project.project_storage (Basic operations)
Test target: ProjectStorage class basic functionalities
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


class TestProjectStorageBasic:
    """
    Test for ProjectStorage class basic operations
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
