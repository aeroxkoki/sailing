# -*- coding: ascii -*-
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
        
        # Verify required directories are created
        assert os.path.exists(os.path.join(temp_dir, "projects"))
        assert os.path.exists(os.path.join(temp_dir, "sessions"))
        assert os.path.exists(os.path.join(temp_dir, "results"))
        assert os.path.exists(os.path.join(temp_dir, "data"))
        assert os.path.exists(os.path.join(temp_dir, "states"))
    
    def test_save_load_project(self, storage, sample_project):
        """Test for saving and loading project"""
        # Save project
        success = storage.save_project(sample_project)
        assert success is True
        
        # Verify added to cache
        assert sample_project.project_id in storage.projects
        
        # Verify file exists
        project_file = os.path.join(storage.projects_path, f"{sample_project.project_id}.json")
        assert os.path.exists(project_file)
        
        # Remove from cache and test loading
        project_id = sample_project.project_id
        storage.projects = {}
        storage._load_projects()
        
        # Verify loaded project
        loaded_project = storage.get_project(project_id)
        assert loaded_project is not None
        assert loaded_project.name == "Test Project"
        assert loaded_project.description == "Project for testing"
        assert "test" in loaded_project.tags
        assert loaded_project.metadata["purpose"] == "testing"