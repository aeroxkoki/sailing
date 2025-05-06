# -*- coding: ascii -*-
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
        
        # Project and session init
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
        
        # Mock setup
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
        # Test execution
        result = integration.assign_to_project(
            self.session1.session_id,
            self.project1.project_id
        )
        
        # Result verification
        assert result is True
        assert self.session1.session_id in self.project1.sessions
        mock_project_storage.save_project.assert_called_once()
        
        # Verify session reference
        assert "session_references" in self.project1.metadata
        assert self.session1.session_id in self.project1.metadata["session_references"]
        
        reference_data = self.project1.metadata["session_references"][self.session1.session_id]
        assert reference_data["session_id"] == self.session1.session_id
        assert reference_data["display_name"] == self.session1.name