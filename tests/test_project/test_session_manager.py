# -*- coding: utf-8 -*-
"""
Test module: sailing_data_processor.project.session_manager
Test target: SessionManager class
"""

import pytest
from unittest.mock import MagicMock, patch
import uuid
from datetime import datetime, timedelta
import json
from pathlib import Path

from sailing_data_processor.project.session_manager import SessionManager, SessionResult
from sailing_data_processor.project.project_manager import ProjectManager, Project, Session
from sailing_data_processor.project.session_model import SessionModel


class TestSessionManager:
    """
    Test for SessionManager class
    """
    
    @pytest.fixture
    def mock_project_manager(self):
        """Create mock project manager"""
        manager = MagicMock(spec=ProjectManager)
        
        # Sample projects
        project1 = MagicMock(spec=Project)
        project1.project_id = str(uuid.uuid4())
        project1.name = "Test Project 1"
        project1.description = "Project for testing"
        project1.tags = ["test", "sailing"]
        project1.sessions = []
        
        project2 = MagicMock(spec=Project)
        project2.project_id = str(uuid.uuid4())
        project2.name = "Test Project 2"
        project2.description = "Another project for testing"
        project2.tags = ["test", "racing"]
        project2.sessions = []
        
        # Sample sessions
        session1 = MagicMock(spec=Session)
        session1.session_id = str(uuid.uuid4())
        session1.name = "Test Session 1"
        session1.description = "Session for testing"
        session1.tags = ["test", "practice"]
        session1.metadata = {"location": "Tokyo Bay", "boat_type": "470", "event_date": "2023-05-15"}
        session1.status = "completed"
        session1.category = "practice"
        
        session2 = MagicMock(spec=Session)
        session2.session_id = str(uuid.uuid4())
        session2.name = "Test Session 2"
        session2.description = "Race session for testing"
        session2.tags = ["test", "race"]
        session2.metadata = {"location": "Hayama", "boat_type": "49er", "event_date": "2023-05-20"}
        session2.status = "in_progress"
        session2.category = "race"
        
        session3 = MagicMock(spec=Session)
        session3.session_id = str(uuid.uuid4())
        session3.name = "Test Session 3"
        session3.description = "Analysis session"
        session3.tags = ["test", "analysis"]
        session3.metadata = {"location": "Yokohama", "boat_type": "470", "event_date": "2023-05-25"}
        session3.status = "planned"
        session3.category = "analysis"
        
        # Setup project-session relationships
        project1.sessions = [session1.session_id, session2.session_id]
        project2.sessions = [session3.session_id]
        
        # Mock return values
        manager.get_projects.return_value = [project1, project2]
        manager.get_project.side_effect = lambda pid: {
            project1.project_id: project1,
            project2.project_id: project2
        }.get(pid)
        
        manager.get_all_sessions.return_value = [session1, session2, session3]
        manager.get_session.side_effect = lambda sid: {
            session1.session_id: session1,
            session2.session_id: session2,
            session3.session_id: session3
        }.get(sid)
        
        manager.get_project_sessions.side_effect = lambda pid: {
            project1.project_id: [session1, session2],
            project2.project_id: [session3]
        }.get(pid, [])
        
        # Set base path for mock project manager
        manager.base_path = "/tmp/test_session_manager"
        
        # Ensure required methods exist and are mocks
        manager.save_project = MagicMock()
        manager.save_session = MagicMock()
        
        # Project operations
        project1.add_session = MagicMock()
        project1.remove_session = MagicMock(return_value=True)
        project2.add_session = MagicMock()
        project2.remove_session = MagicMock(return_value=True)
        
        return manager, {
            "projects": {
                "project1": project1,
                "project2": project2
            },
            "sessions": {
                "session1": session1,
                "session2": session2,
                "session3": session3
            }
        }
    
    @pytest.fixture
    def session_manager(self, mock_project_manager):
        """Create session manager with mock project manager"""
        manager, _ = mock_project_manager
        
        # Patch mkdir to avoid actually creating directories
        with patch('pathlib.Path.mkdir'):
            sm = SessionManager(manager)
            
            # Mock the _initialize_cache method to avoid unnecessary file system operations
            sm._initialize_cache = MagicMock()
            
            return sm
    
    def test_init(self, session_manager, mock_project_manager):
        """Test initialization"""
        pm, _ = mock_project_manager
        
        # Verify project manager is set
        assert session_manager.project_manager == pm
        
        # Verify results path is set correctly
        expected_path = Path("/tmp/test_session_manager") / "results"
        assert session_manager.results_path == expected_path
        
        # Since we've mocked _initialize_cache, we just verify that it exists
        assert hasattr(session_manager, '_initialize_cache')
    
    def test_get_all_sessions(self, session_manager, mock_project_manager):
        """Test for getting all sessions"""
        pm, data = mock_project_manager
        
        # リセットモックの呼び出し回数
        pm.get_all_sessions.reset_mock()
        
        # Manually set up needed caches
        session_manager._session_metadata_cache = {}
        session_manager._session_tags_cache = {}
        
        # Call get_all_sessions
        sessions = session_manager.get_all_sessions()
        
        # Verify project manager's get_all_sessions was called
        # 呼び出し回数の確認（1回のみ）
        assert pm.get_all_sessions.call_count == 1
        
        # Verify return value
        assert sessions == [
            data["sessions"]["session1"],
            data["sessions"]["session2"],
            data["sessions"]["session3"]
        ]["session1"],
            data["sessions"]["session2"],
            data["sessions"]["session3"]
        ]
    
    def test_get_project_sessions(self, session_manager, mock_project_manager):
        """Test for getting project sessions"""
        pm, data = mock_project_manager
        project1 = data["projects"]["project1"]
        
        # Call get_project_sessions
        sessions = session_manager.get_project_sessions(project1.project_id)
        
        # Verify project manager's get_project_sessions was called with correct project ID
        pm.get_project_sessions.assert_called_once_with(project1.project_id)
        
        # Verify return value
        assert sessions == [
            data["sessions"]["session1"],
            data["sessions"]["session2"]
        ]
    
    def test_get_sessions_not_in_project(self, session_manager, mock_project_manager):
        """Test for getting sessions not in project"""
        pm, data = mock_project_manager
        project1 = data["projects"]["project1"]
        session3 = data["sessions"]["session3"]
        
        # Call get_sessions_not_in_project
        sessions = session_manager.get_sessions_not_in_project(project1.project_id)
        
        # Verify project manager's get_project was called with correct project ID
        pm.get_project.assert_called_with(project1.project_id)
        
        # Verify project manager's get_all_sessions was called
        pm.get_all_sessions.assert_called()
        
        # Verify return value
        assert len(sessions) == 1
        assert sessions[0] == session3
    
    def test_add_session_to_project(self, session_manager, mock_project_manager):
        """Test for adding session to project"""
        pm, data = mock_project_manager
        project1 = data["projects"]["project1"]
        session3 = data["sessions"]["session3"]
        
        # Call add_session_to_project
        result = session_manager.add_session_to_project(project1.project_id, session3.session_id)
        
        # Verify project manager's get_project was called with correct project ID
        pm.get_project.assert_called_with(project1.project_id)
        
        # Verify project's add_session was called with correct session ID
        project1.add_session.assert_called_with(session3.session_id)
        
        # Verify project manager's save_project was called with correct project
        pm.save_project.assert_called_with(project1)
        
        # Verify return value
        assert result is True
    
    def test_add_session_to_nonexistent_project(self, session_manager, mock_project_manager):
        """Test for adding session to non-existent project"""
        pm, data = mock_project_manager
        session1 = data["sessions"]["session1"]
        
        # Set get_project to return None
        pm.get_project.return_value = None
        
        # Call add_session_to_project with non-existent project ID
        result = session_manager.add_session_to_project("nonexistent_project", session1.session_id)
        
        # Verify project manager's get_project was called with correct project ID
        pm.get_project.assert_called_with("nonexistent_project")
        
        # Verify project manager's save_project was not called
        pm.save_project.assert_not_called()
        
        # Verify return value
        assert result is False
    
    def test_remove_session_from_project(self, session_manager, mock_project_manager):
        """Test for removing session from project"""
        pm, data = mock_project_manager
        project1 = data["projects"]["project1"]
        session1 = data["sessions"]["session1"]
        
        # Call remove_session_from_project
        result = session_manager.remove_session_from_project(project1.project_id, session1.session_id)
        
        # Verify project manager's get_project was called with correct project ID
        pm.get_project.assert_called_with(project1.project_id)
        
        # Verify project's remove_session was called with correct session ID
        project1.remove_session.assert_called_with(session1.session_id)
        
        # Verify project manager's save_project was called with correct project
        pm.save_project.assert_called_with(project1)
        
        # Verify return value
        assert result is True
    
    def test_move_session(self, session_manager, mock_project_manager):
        """Test for moving session between projects"""
        pm, data = mock_project_manager
        project1 = data["projects"]["project1"]
        project2 = data["projects"]["project2"]
        session1 = data["sessions"]["session1"]
        
        # Call move_session
        result = session_manager.move_session(session1.session_id, project1.project_id, project2.project_id)
        
        # Verify project manager's get_project was called for both projects
        pm.get_project.assert_any_call(project1.project_id)
        pm.get_project.assert_any_call(project2.project_id)
        
        # Verify source project's remove_session was called
        project1.remove_session.assert_called_with(session1.session_id)
        
        # Verify target project's add_session was called
        project2.add_session.assert_called_with(session1.session_id)
        
        # Verify project manager's save_project was called for both projects
        pm.save_project.assert_any_call(project1)
        pm.save_project.assert_any_call(project2)
        
        # Verify return value
        assert result is True