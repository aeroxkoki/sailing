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
        project1 = Project(
            name="Test Project 1",
            description="Project for testing",
            tags=["test", "sailing"]
        )
        
        project2 = Project(
            name="Test Project 2",
            description="Another project for testing",
            tags=["test", "racing"]
        )
        
        # Sample sessions
        session1 = Session(
            name="Test Session 1",
            description="Session for testing",
            tags=["test", "practice"],
            metadata={"location": "Tokyo Bay", "boat_type": "470", "event_date": "2023-05-15"}
        )
        session1.status = "completed"
        session1.category = "practice"
        
        session2 = Session(
            name="Test Session 2",
            description="Race session for testing",
            tags=["test", "race"],
            metadata={"location": "Hayama", "boat_type": "49er", "event_date": "2023-05-20"}
        )
        session2.status = "in_progress"
        session2.category = "race"
        
        session3 = Session(
            name="Test Session 3",
            description="Analysis session",
            tags=["test", "analysis"],
            metadata={"location": "Yokohama", "boat_type": "470", "event_date": "2023-05-25"}
        )
        session3.status = "planned"
        session3.category = "analysis"
        
        # Setup project-session relationships
        project1.add_session(session1.session_id)
        project1.add_session(session2.session_id)
        project2.add_session(session3.session_id)
        
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
        
        # Ensure required methods exist
        if not hasattr(manager, 'save_project'):
            manager.save_project = MagicMock()
        
        if not hasattr(manager, 'save_session'):
            manager.save_session = MagicMock()
        
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
        
        # Verify _initialize_cache was called
        session_manager._initialize_cache.assert_called_once()
    
    def test_get_all_sessions(self, session_manager, mock_project_manager):
        """Test for getting all sessions"""
        pm, data = mock_project_manager
        
        # Manually set up needed caches
        session_manager._session_metadata_cache = {}
        session_manager._session_tags_cache = {}
        
        # Call get_all_sessions
        sessions = session_manager.get_all_sessions()
        
        # Verify project manager's get_all_sessions was called
        pm.get_all_sessions.assert_called_once()
        
        # Verify return value
        assert sessions == [
            data["sessions"]["session1"],
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
    
    def test_update_session_metadata(self, session_manager, mock_project_manager):
        """Test for updating session metadata"""
        pm, data = mock_project_manager
        session1 = data["sessions"]["session1"]
        
        # Setup test data
        session_manager._session_metadata_cache = {session1.session_id: {}}
        session_manager._update_search_index = MagicMock()
        
        # New metadata
        new_metadata = {
            "boat_type": "Laser",
            "crew_info": "Solo",
            "wind_speed": 12
        }
        
        # Call update_session_metadata
        result = session_manager.update_session_metadata(session1.session_id, new_metadata)
        
        # Verify project manager's get_session was called
        pm.get_session.assert_called_with(session1.session_id)
        
        # Verify metadata was updated
        for key, value in new_metadata.items():
            assert session1.metadata[key] == value
        
        # Verify cache was updated
        assert session_manager._session_metadata_cache[session1.session_id] == new_metadata
        
        # Verify search index was updated
        session_manager._update_search_index.assert_called_with(session1)
        
        # Verify session was saved
        pm.save_session.assert_called_with(session1)
        
        # Verify return value
        assert result is True
    
    def test_search_sessions_by_query(self, session_manager, mock_project_manager):
        """Test for searching sessions by query"""
        _, data = mock_project_manager
        session1 = data["sessions"]["session1"]
        session2 = data["sessions"]["session2"]
        
        # Setup search index
        session_manager._search_index = {
            "test": {session1.session_id, session2.session_id},
            "practice": {session1.session_id},
            "race": {session2.session_id}
        }
        
        # Mock _extract_keywords to simplify testing
        session_manager._extract_keywords = lambda text: text.lower().split()
        
        # Call search_sessions with query
        results = session_manager.search_sessions(query="practice")
        
        # Verify results contain only session1
        assert results == [session1.session_id]
        
        # Call search_sessions with different query
        results = session_manager.search_sessions(query="race")
        
        # Verify results contain only session2
        assert results == [session2.session_id]
    
    def test_search_sessions_by_tags(self, session_manager, mock_project_manager):
        """Test for searching sessions by tags"""
        _, data = mock_project_manager
        session1 = data["sessions"]["session1"]
        session2 = data["sessions"]["session2"]
        
        # Setup session tags cache
        session_manager._session_tags_cache = {
            "test": {session1.session_id, session2.session_id},
            "practice": {session1.session_id},
            "race": {session2.session_id}
        }
        
        # Call search_sessions with tags
        results = session_manager.search_sessions(tags=["practice"])
        
        # Verify results contain only session1
        assert results == [session1.session_id]
        
        # Call search_sessions with different tags
        results = session_manager.search_sessions(tags=["race"])
        
        # Verify results contain only session2
        assert results == [session2.session_id]
    
    def test_get_available_tags(self, session_manager):
        """Test for getting available tags"""
        # Setup session tags cache
        session_manager._session_tags_cache = {
            "test": set(),
            "practice": set(),
            "race": set(),
            "analysis": set()
        }
        
        # Call get_available_tags
        tags = session_manager.get_available_tags()
        
        # Verify results
        expected_tags = ["test", "practice", "race", "analysis"]
        assert sorted(tags) == sorted(expected_tags)
    
    def test_get_sessions_by_tag(self, session_manager, mock_project_manager):
        """Test for getting sessions by tag"""
        _, data = mock_project_manager
        session1 = data["sessions"]["session1"]
        session2 = data["sessions"]["session2"]
        
        # Setup session tags cache
        session_manager._session_tags_cache = {
            "test": {session1.session_id, session2.session_id},
            "practice": {session1.session_id},
            "race": {session2.session_id}
        }
        
        # Call get_sessions_by_tag
        results = session_manager.get_sessions_by_tag("practice")
        
        # Verify results
        assert sorted(results) == sorted([session1.session_id])
        
        # Call with non-existent tag
        results = session_manager.get_sessions_by_tag("nonexistent")
        
        # Verify empty results
        assert results == []
    
    def test_get_sessions_by_multiple_tags_and(self, session_manager, mock_project_manager):
        """Test for getting sessions by multiple tags (AND)"""
        _, data = mock_project_manager
        session1 = data["sessions"]["session1"]
        session2 = data["sessions"]["session2"]
        session3 = data["sessions"]["session3"]
        
        # Setup session tags cache
        session_manager._session_tags_cache = {
            "test": {session1.session_id, session2.session_id, session3.session_id},
            "practice": {session1.session_id, session3.session_id},
            "race": {session2.session_id},
            "analysis": {session3.session_id}
        }
        
        # Call get_sessions_by_multiple_tags with AND logic
        results = session_manager.get_sessions_by_multiple_tags(["test", "practice"], match_all=True)
        
        # Verify results contain session1 and session3
        assert sorted(results) == sorted([session1.session_id, session3.session_id])
    
    def test_get_sessions_by_multiple_tags_or(self, session_manager, mock_project_manager):
        """Test for getting sessions by multiple tags (OR)"""
        _, data = mock_project_manager
        session1 = data["sessions"]["session1"]
        session2 = data["sessions"]["session2"]
        session3 = data["sessions"]["session3"]
        
        # Setup session tags cache
        session_manager._session_tags_cache = {
            "test": {session1.session_id, session2.session_id, session3.session_id},
            "practice": {session1.session_id},
            "race": {session2.session_id},
            "analysis": {session3.session_id}
        }
        
        # Call get_sessions_by_multiple_tags with OR logic
        results = session_manager.get_sessions_by_multiple_tags(["race", "analysis"], match_all=False)
        
        # Verify results contain session2 and session3
        assert sorted(results) == sorted([session2.session_id, session3.session_id])
    
    def test_update_session_status(self, session_manager, mock_project_manager):
        """Test for updating session status"""
        pm, data = mock_project_manager
        session1 = data["sessions"]["session1"]
        
        # Mock _update_search_index method
        session_manager._update_search_index = MagicMock()
        
        # Call update_session_status
        result = session_manager.update_session_status(session1.session_id, "archived")
        
        # Verify project manager's get_session was called
        pm.get_session.assert_called_with(session1.session_id)
        
        # Verify session's status was updated
        assert session1.status == "archived"
        
        # Verify search index was updated
        session_manager._update_search_index.assert_called_with(session1)
        
        # Verify session was saved
        pm.save_session.assert_called_with(session1)
        
        # Verify return value
        assert result is True
    
    def test_update_session_category(self, session_manager, mock_project_manager):
        """Test for updating session category"""
        pm, data = mock_project_manager
        session1 = data["sessions"]["session1"]
        
        # Mock _update_search_index method
        session_manager._update_search_index = MagicMock()
        
        # Call update_session_category
        result = session_manager.update_session_category(session1.session_id, "training")
        
        # Verify project manager's get_session was called
        pm.get_session.assert_called_with(session1.session_id)
        
        # Verify session's category was updated
        assert session1.category == "training"
        
        # Verify search index was updated
        session_manager._update_search_index.assert_called_with(session1)
        
        # Verify session was saved
        pm.save_session.assert_called_with(session1)
        
        # Verify return value
        assert result is True
    
    def test_update_session_tags(self, session_manager, mock_project_manager):
        """Test for updating session tags"""
        pm, data = mock_project_manager
        session1 = data["sessions"]["session1"]
        
        # Setup test data
        old_tags = session1.tags.copy()
        session_manager._update_session_tags = MagicMock()
        session_manager._update_search_index = MagicMock()
        
        # New tags
        new_tags = ["advanced", "windy", "test"]
        
        # Call update_session_tags
        result = session_manager.update_session_tags(session1.session_id, new_tags)
        
        # Verify project manager's get_session was called
        pm.get_session.assert_called_with(session1.session_id)
        
        # Verify session's tags were updated
        assert session1.tags == new_tags
        
        # Verify tags cache was updated
        session_manager._update_session_tags.assert_called_with(session1.session_id, old_tags, new_tags)
        
        # Verify search index was updated
        session_manager._update_search_index.assert_called_with(session1)
        
        # Verify session was saved
        pm.save_session.assert_called_with(session1)
        
        # Verify return value
        assert result is True
