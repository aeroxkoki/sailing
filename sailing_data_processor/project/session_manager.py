# -*- coding: utf-8 -*-
"""
sailing_data_processor.project.session_manager

Session management class implementation.
"""

from typing import Dict, List, Any, Optional, Union, Set, Tuple
import os
import json
from datetime import datetime
import uuid
from pathlib import Path
import re
import logging

from sailing_data_processor.project.project_manager import Project, Session

logger = logging.getLogger(__name__)


class SessionResult:
    """
    Represents a result attached to a session, such as analysis or processing results.
    
    Parameters
    ----------
    name : str
        Name of the result
    result_type : str
        Type of the result (e.g., "wind_analysis", "strategy_detection")
    data : Dict[str, Any]
        Result data
    metadata : Dict[str, Any], optional
        Additional metadata, by default {}
    result_id : str, optional
        Result ID, by default None (auto-generated)
    """
    
    def __init__(self, 
                 name: str, 
                 result_type: str,
                 data: Dict[str, Any],
                 metadata: Dict[str, Any] = None,
                 result_id: str = None):
        """
        Initialize a new session result
        
        Parameters
        ----------
        name : str
            Name of the result
        result_type : str
            Type of the result (e.g., "wind_analysis", "strategy_detection")
        data : Dict[str, Any]
            Result data
        metadata : Dict[str, Any], optional
            Additional metadata, by default {}
        result_id : str, optional
            Result ID, by default None (auto-generated)
        """
        self.name = name
        self.result_type = result_type
        self.data = data
        self.metadata = metadata or {}
        self.result_id = result_id or str(uuid.uuid4())
        self.version = 1
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    def update(self, data: Dict[str, Any], name: Optional[str] = None, 
              metadata_updates: Dict[str, Any] = None) -> None:
        """
        Update the result data and metadata
        
        Parameters
        ----------
        data : Dict[str, Any]
            New result data
        name : Optional[str], optional
            New name for the result, by default None (unchanged)
        metadata_updates : Dict[str, Any], optional
            Metadata updates, by default None
        """
        self.data = data
        if name is not None:
            self.name = name
        if metadata_updates:
            self.metadata.update(metadata_updates)
        
        self.version += 1
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the result to a dictionary
        
        Returns
        -------
        Dict[str, Any]
            Dictionary representation of the result
        """
        return {
            "result_id": self.result_id,
            "name": self.name,
            "result_type": self.result_type,
            "data": self.data,
            "metadata": self.metadata,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionResult':
        """
        Create a result from a dictionary
        
        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary representation of the result
            
        Returns
        -------
        SessionResult
            Session result instance
        """
        result = cls(
            name=data["name"],
            result_type=data["result_type"],
            data=data["data"],
            metadata=data.get("metadata", {}),
            result_id=data.get("result_id")
        )
        
        result.version = data.get("version", 1)
        result.created_at = data.get("created_at", result.created_at)
        result.updated_at = data.get("updated_at", result.updated_at)
        
        return result


class SessionManager:
    """
    Session management class
    
    Manages sessions, their states, tags, metadata, and relationships with projects.
    Provides methods for searching, filtering, and organizing sessions.
    
    Parameters
    ----------
    project_manager : Any
        Project manager instance
    """
    
    def __init__(self, project_manager):
        """
        Initialize the session manager
        
        Parameters
        ----------
        project_manager : Any
            Project manager instance that handles project and session storage
        """
        self.project_manager = project_manager
        self.base_path = Path(project_manager.base_path) if project_manager else Path("session_data")
        self.results_path = self.base_path / "results"
        
        # Create required directories
        self.results_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize search and cache systems
        self._search_index = {}  # keyword -> {session_ids}
        self._session_metadata_cache = {}  # session_id -> metadata
        self._session_tags_cache = {}  # tag -> {session_ids}
        self._session_results_cache = {}  # session_id -> {result_id -> SessionResult}
        
        # Initialize the cache
        self._initialize_cache()
    
    def _initialize_cache(self):
        """Initialize and load all cache data"""
        self._load_results()
        self._build_search_index()
        self._build_tags_cache()
        self._build_metadata_cache()
        
    def _build_search_index(self):
        """Build the search index for all sessions"""
        self._search_index = {}
        
        for session in self.get_all_sessions():
            self._update_search_index(session)
    
    def _build_tags_cache(self):
        """Build the tags cache for all sessions"""
        self._session_tags_cache = {}
        
        for session in self.get_all_sessions():
            for tag in session.tags:
                if tag not in self._session_tags_cache:
                    self._session_tags_cache[tag] = set()
                self._session_tags_cache[tag].add(session.session_id)
    
    def _build_metadata_cache(self):
        """Build the metadata cache for all sessions"""
        self._session_metadata_cache = {}
        
        for session in self.get_all_sessions():
            self._session_metadata_cache[session.session_id] = session.metadata
    
    def _load_results(self):
        """Load all session results"""
        self._session_results_cache = {}
        
        # Check if results directory exists
        if not self.results_path.exists():
            return
        
        # Load results for each session
        for session_dir in self.results_path.glob("*"):
            if session_dir.is_dir():
                session_id = session_dir.name
                self._session_results_cache[session_id] = {}
                
                # Load all result files
                for result_file in session_dir.glob("*.json"):
                    try:
                        with open(result_file, 'r', encoding='utf-8') as f:
                            result_data = json.load(f)
                            result = SessionResult.from_dict(result_data)
                            self._session_results_cache[session_id][result.result_id] = result
                    except Exception as e:
                        logger.error(f"Failed to load result file {result_file}: {e}")
    
    def _update_search_index(self, session):
        """
        Update the search index for a session
        
        Parameters
        ----------
        session : Session
            Session to update in the index
        """
        # Extract keywords from session name and description
        keywords = self._extract_keywords(session.name + " " + session.description)
        
        # Add session tags to keywords
        keywords.extend(session.tags)
        
        # Add metadata values to keywords
        for value in session.metadata.values():
            if isinstance(value, str):
                keywords.extend(self._extract_keywords(value))
        
        # Update the search index
        for keyword in set(keywords):  # use set to remove duplicates
            if keyword not in self._search_index:
                self._search_index[keyword] = set()
            self._search_index[keyword].add(session.session_id)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract keywords from text
        
        Parameters
        ----------
        text : str
            Text to extract keywords from
            
        Returns
        -------
        List[str]
            List of keywords
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into words
        words = text.split()
        
        # Remove stop words and short words
        stop_words = {"a", "an", "the", "and", "or", "but", "is", "are", "was", "were", "in", "on", "at", "to", "for"}
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _update_session_tags(self, session_id: str, old_tags: List[str], new_tags: List[str]) -> None:
        """
        Update session tags in the cache
        
        Parameters
        ----------
        session_id : str
            Session ID
        old_tags : List[str]
            Old tags
        new_tags : List[str]
            New tags
        """
        # Remove session from old tags
        for tag in old_tags:
            if tag in self._session_tags_cache and session_id in self._session_tags_cache[tag]:
                self._session_tags_cache[tag].remove(session_id)
        
        # Add session to new tags
        for tag in new_tags:
            if tag not in self._session_tags_cache:
                self._session_tags_cache[tag] = set()
            self._session_tags_cache[tag].add(session_id)
    
    def get_all_sessions(self) -> List[Session]:
        """
        Get all sessions
        
        Returns
        -------
        List[Session]
            List of all sessions
        """
        return self.project_manager.get_all_sessions()
    
    def get_project_sessions(self, project_id: str) -> List[Session]:
        """
        Get sessions in a project
        
        Parameters
        ----------
        project_id : str
            Project ID
            
        Returns
        -------
        List[Session]
            List of sessions in the project
        """
        return self.project_manager.get_project_sessions(project_id)
    
    def get_sessions_not_in_project(self, project_id: str) -> List[Session]:
        """
        Get sessions not in a project
        
        Parameters
        ----------
        project_id : str
            Project ID
            
        Returns
        -------
        List[Session]
            List of sessions not in the project
        """
        # Get the project
        project = self.project_manager.get_project(project_id)
        if not project:
            return []
        
        # Get all sessions
        all_sessions = self.get_all_sessions()
        
        # Filter out sessions in the project
        return [session for session in all_sessions if session.session_id not in project.sessions]
    
    def add_session_to_project(self, project_id: str, session_id: str) -> bool:
        """
        Add a session to a project
        
        Parameters
        ----------
        project_id : str
            Project ID
        session_id : str
            Session ID
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Get the project
        project = self.project_manager.get_project(project_id)
        if not project:
            return False
        
        # Add the session to the project
        project.add_session(session_id)
        
        # Save the project
        self.project_manager.save_project(project)
        
        return True
    
    def remove_session_from_project(self, project_id: str, session_id: str) -> bool:
        """
        Remove a session from a project
        
        Parameters
        ----------
        project_id : str
            Project ID
        session_id : str
            Session ID
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Get the project
        project = self.project_manager.get_project(project_id)
        if not project:
            return False
        
        # Remove the session from the project
        project.remove_session(session_id)
        
        # Save the project
        self.project_manager.save_project(project)
        
        return True
    
    def move_session(self, session_id: str, source_project_id: str, target_project_id: str) -> bool:
        """
        Move a session from one project to another
        
        Parameters
        ----------
        session_id : str
            Session ID
        source_project_id : str
            Source project ID
        target_project_id : str
            Target project ID
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Get the source and target projects
        source_project = self.project_manager.get_project(source_project_id)
        target_project = self.project_manager.get_project(target_project_id)
        
        if not source_project or not target_project:
            return False
        
        # Remove the session from the source project
        source_project.remove_session(session_id)
        
        # Add the session to the target project
        target_project.add_session(session_id)
        
        # Save both projects
        self.project_manager.save_project(source_project)
        self.project_manager.save_project(target_project)
        
        return True
    
    def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update session metadata
        
        Parameters
        ----------
        session_id : str
            Session ID
        metadata : Dict[str, Any]
            Metadata to update
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Get the session
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        # Update the session metadata
        for key, value in metadata.items():
            session.metadata[key] = value
        
        # Update the metadata cache
        if session_id not in self._session_metadata_cache:
            self._session_metadata_cache[session_id] = {}
        self._session_metadata_cache[session_id].update(metadata)
        
        # Update the search index
        self._update_search_index(session)
        
        # Save the session
        self.project_manager.save_session(session)
        
        return True
    
    def update_session_status(self, session_id: str, status: str) -> bool:
        """
        Update session status
        
        Parameters
        ----------
        session_id : str
            Session ID
        status : str
            New status
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Get the session
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            # Sessionオブジェクトにupdate_statusメソッドがあればそれを使用
            if hasattr(session, 'update_status') and callable(getattr(session, 'update_status')):
                session.update_status(status)
            else:
                # 直接属性として設定
                session.status = status
            
            # Update the search index
            self._update_search_index(session)
            
            # Save the session
            self.project_manager.save_session(session)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update session status: {e}")
            return False
    
    def update_session_category(self, session_id: str, category: str) -> bool:
        """
        Update session category
        
        Parameters
        ----------
        session_id : str
            Session ID
        category : str
            New category
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Get the session
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        try:
            # Sessionオブジェクトにupdate_categoryメソッドがあればそれを使用
            if hasattr(session, 'update_category') and callable(getattr(session, 'update_category')):
                session.update_category(category)
            else:
                # 直接属性として設定
                session.category = category
            
            # Update the search index
            self._update_search_index(session)
            
            # Save the session
            self.project_manager.save_session(session)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update session category: {e}")
            return False
    
    def update_session_tags(self, session_id: str, tags: List[str]) -> bool:
        """
        Update session tags
        
        Parameters
        ----------
        session_id : str
            Session ID
        tags : List[str]
            New tags
            
        Returns
        -------
        bool
            True if successful, False otherwise
        """
        # Get the session
        session = self.project_manager.get_session(session_id)
        if not session:
            return False
        
        # Store old tags for the update
        old_tags = session.tags.copy()
        
        # Update the session tags
        session.tags = tags
        
        # Update the tags cache
        self._update_session_tags(session_id, old_tags, tags)
        
        # Update the search index
        self._update_search_index(session)
        
        # Save the session
        self.project_manager.save_session(session)
        
        return True
    
    def search_sessions(self, query: str = None, tags: List[str] = None) -> List[str]:
        """
        Search for sessions
        
        Parameters
        ----------
        query : str, optional
            Search query, by default None
        tags : List[str], optional
            Tags to filter by, by default None
            
        Returns
        -------
        List[str]
            List of matching session IDs
        """
        if not query and not tags:
            return [session.session_id for session in self.get_all_sessions()]
        
        matching_sessions = set()
        
        # Search by query
        if query:
            keywords = self._extract_keywords(query)
            for keyword in keywords:
                if keyword in self._search_index:
                    if not matching_sessions:
                        matching_sessions = self._search_index[keyword].copy()
                    else:
                        matching_sessions &= self._search_index[keyword]
        
        # Filter by tags
        if tags:
            tag_matches = set()
            for tag in tags:
                if tag in self._session_tags_cache:
                    if not tag_matches:
                        tag_matches = self._session_tags_cache[tag].copy()
                    else:
                        tag_matches &= self._session_tags_cache[tag]
            
            if query:
                matching_sessions &= tag_matches
            else:
                matching_sessions = tag_matches
        
        return list(matching_sessions)
    
    def get_available_tags(self) -> List[str]:
        """
        Get all available tags
        
        Returns
        -------
        List[str]
            List of all tags
        """
        return list(self._session_tags_cache.keys())
    
    def get_sessions_by_tag(self, tag: str) -> List[str]:
        """
        Get sessions with a specific tag
        
        Parameters
        ----------
        tag : str
            Tag to filter by
            
        Returns
        -------
        List[str]
            List of matching session IDs
        """
        if tag not in self._session_tags_cache:
            return []
        
        return list(self._session_tags_cache[tag])
    
    def get_sessions_by_multiple_tags(self, tags: List[str], match_all: bool = False) -> List[str]:
        """
        Get sessions matching multiple tags
        
        Parameters
        ----------
        tags : List[str]
            Tags to filter by
        match_all : bool, optional
            If True, sessions must match all tags (AND), otherwise match any tag (OR), by default False
            
        Returns
        -------
        List[str]
            List of matching session IDs
        """
        if not tags:
            return []
        
        matching_sessions = set()
        
        for tag in tags:
            if tag in self._session_tags_cache:
                tag_matches = self._session_tags_cache[tag]
                if not matching_sessions:
                    matching_sessions = tag_matches.copy()
                elif match_all:
                    matching_sessions &= tag_matches  # Intersection (AND)
                else:
                    matching_sessions |= tag_matches  # Union (OR)
        
        return list(matching_sessions)
