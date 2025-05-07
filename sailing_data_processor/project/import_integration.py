# -*- coding: utf-8 -*-
"""
sailing_data_processor.project.import_integration

ImportIntegration class for project management and import processing.
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import os
import json
import logging
from datetime import datetime
from pathlib import Path

from sailing_data_processor.project.project_model import Project, Session
from sailing_data_processor.project.session_reference import SessionReference
from sailing_data_processor.project.project_storage import ProjectStorage
from sailing_data_processor.data_model.container import GPSDataContainer

# Module logger
logger = logging.getLogger(__name__)

class ImportIntegration:
    """
    Import integration class
    
    Manages the integration between project management and import processing.
    Provides functionality for adding imported sessions to projects, applying
    project settings, and more.
    
    Attributes
    ----------
    project_storage : ProjectStorage
        Project storage manager
    """
    
    def __init__(self, project_storage: ProjectStorage):
        """
        Initialize import integration
        
        Parameters
        ----------
        project_storage : ProjectStorage
            Project storage manager
        """
        self.project_storage = project_storage
    
    def assign_to_project(self, session_id: str, project_id: str, 
                         display_name: Optional[str] = None) -> bool:
        """
        Assign session to a project
        
        Parameters
        ----------
        session_id : str
            Session ID to assign
        project_id : str
            Project ID to assign to
        display_name : Optional[str], optional
            Custom display name, by default None
        
        Returns
        -------
        bool
            True if successful
        """
        project = self.project_storage.get_project(project_id)
        session = self.project_storage.get_session(session_id)
        
        if not project:
            logger.error(f"Project {project_id} not found")
            return False
        
        if not session:
            logger.error(f"Session {session_id} not found")
            return False
        
        # Create session reference
        reference = SessionReference(
            session_id=session_id,
            display_name=display_name or session.name,
            description=session.description
        )
        
        # Update cached info from session
        reference.update_cached_info(session)
        
        # Add session to project sessions list
        # Note: The session list is just a set of IDs, actual session references
        # with display names and settings are stored in metadata
        project.add_session(session_id)
        
        # Add session reference to project metadata
        if "session_references" not in project.metadata:
            project.metadata["session_references"] = {}
        
        project.metadata["session_references"][session_id] = reference.to_dict()
        
        # Save project
        return self.project_storage.save_project(project)
    
    def remove_from_project(self, session_id: str, project_id: str) -> bool:
        """
        Remove session from a project
        
        Parameters
        ----------
        session_id : str
            Session ID to remove
        project_id : str
            Project ID to remove from
        
        Returns
        -------
        bool
            True if successful
        """
        project = self.project_storage.get_project(project_id)
        
        if not project:
            logger.error(f"Project {project_id} not found")
            return False
        
        # Remove session from project
        if project.remove_session(session_id):
            # Remove session reference
            if "session_references" in project.metadata and session_id in project.metadata["session_references"]:
                del project.metadata["session_references"][session_id]
            
            # Save project
            return self.project_storage.save_project(project)
        
        return False
    
    def update_session_reference(self, project_id: str, session_id: str, 
                               display_name: Optional[str] = None, 
                               description: Optional[str] = None,
                               order: Optional[int] = None,
                               view_settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update session reference
        
        Parameters
        ----------
        project_id : str
            Project ID
        session_id : str
            Session ID
        display_name : Optional[str], optional
            New display name, by default None
        description : Optional[str], optional
            New description, by default None
        order : Optional[int], optional
            New display order, by default None
        view_settings : Optional[Dict[str, Any]], optional
            New view settings, by default None
        
        Returns
        -------
        bool
            True if successful
        """
        project = self.project_storage.get_project(project_id)
        
        if not project:
            logger.error(f"Project {project_id} not found")
            return False
        
        # Check if session reference exists
        if ("session_references" not in project.metadata or 
            session_id not in project.metadata["session_references"]):
            # If session reference doesn't exist, create it
            if session_id in project.sessions:
                session = self.project_storage.get_session(session_id)
                if session:
                    reference = SessionReference(
                        session_id=session_id,
                        display_name=session.name,
                        description=session.description
                    )
                    reference.update_cached_info(session)
                    
                    if "session_references" not in project.metadata:
                        project.metadata["session_references"] = {}
                    
                    project.metadata["session_references"][session_id] = reference.to_dict()
                else:
                    logger.error(f"Session {session_id} not found")
                    return False
            else:
                logger.error(f"Session {session_id} is not in project {project_id}")
                return False
        
        # Update session reference
        reference_dict = project.metadata["session_references"][session_id]
        reference = SessionReference.from_dict(reference_dict)
        
        if display_name is not None:
            reference.set_display_name(display_name)
        
        if description is not None:
            reference.description = description
        
        if order is not None:
            reference.set_order(order)
        
        if view_settings is not None:
            reference.update_view_settings(view_settings)
        
        # Update reference in project metadata
        project.metadata["session_references"][session_id] = reference.to_dict()
        
        # Save project
        return self.project_storage.save_project(project)
    
    def process_import_result(self, session: Session, container: GPSDataContainer,
                            target_project_id: Optional[str] = None,
                            auto_assign: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Process import result
        
        Parameters
        ----------
        session : Session
            Imported session
        container : GPSDataContainer
            Imported data container
        target_project_id : Optional[str], optional
            Target project ID to assign to, by default None
        auto_assign : bool, optional
            Enable auto-assignment feature, by default True
        
        Returns
        -------
        Tuple[bool, Optional[str]]
            (Success flag, assigned project ID)
        """
        # Save session and container
        if not self.project_storage.save_session(session):
            logger.error(f"Failed to save session {session.session_id}")
            return False, None
        
        if not self.project_storage.save_container(container, session.session_id):
            logger.error(f"Failed to save container")
            return False, None
        
        # If target project specified, assign to it
        if target_project_id:
            success = self.assign_to_project(session.session_id, target_project_id)
            if success:
                logger.info(f"Session {session.session_id} assigned to project {target_project_id}")
                return True, target_project_id
            else:
                logger.error(f"Failed to assign session {session.session_id} to project {target_project_id}")
                return False, None
        
        # Auto assignment feature
        if auto_assign:
            project_id = self._auto_assign_project(session, container)
            if project_id:
                success = self.assign_to_project(session.session_id, project_id)
                if success:
                    logger.info(f"Session {session.session_id} auto-assigned to project {project_id}")
                    return True, project_id
        
        return True, None
    
    def _auto_assign_project(self, session: Session, container: GPSDataContainer) -> Optional[str]:
        """
        Auto-assign session to an appropriate project
        
        Parameters
        ----------
        session : Session
            Session to assign
        container : GPSDataContainer
            Session's data container
        
        Returns
        -------
        Optional[str]
            Project ID to assign to, or None if no matching project
        """
        # Auto-assignment strategy:
        # 1. Tag-based matching
        # 2. Date-based matching
        # 3. Location-based matching
        # 4. Most recently created project
        
        # Get all projects
        projects = self.project_storage.get_projects()
        if not projects:
            return None
            
        # Tag-based matching
        if session.tags and len(session.tags) > 0:
            for project in projects:
                if project.tags and len(project.tags) > 0:
                    # Check for tag overlap
                    # If any tag in the session matches any tag in the project, assign to it
                    for tag in session.tags:
                        if tag in project.tags:
                            logger.info(f"Auto-assigning session {session.session_id} to project {project.project_id} based on matching tag: {tag}")
                            return project.project_id
        
        # Date-based matching
        if 'event_date' in session.metadata and session.metadata['event_date']:
            session_date = str(session.metadata['event_date']).strip()
            for project in projects:
                if 'event_date' in project.metadata and project.metadata['event_date']:
                    project_date = str(project.metadata['event_date']).strip()
                    # 単純な文字列比較
                    if session_date == project_date:
                        logger.info(f"Auto-assigning session {session.session_id} to project {project.project_id} based on exact date match: {session_date}")
                        return project.project_id
                    
                    # 異なる日付形式の比較
                    try:
                        # 日付形式が異なる場合に標準形式に変換して比較
                        # セッション日付の解析
                        session_datetime = None
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%m-%d-%Y', '%m/%d/%Y']:
                            try:
                                session_datetime = datetime.strptime(session_date, fmt)
                                logger.debug(f"Parsed session date {session_date} with format {fmt}")
                                break
                            except ValueError:
                                continue
                        
                        if not session_datetime:
                            logger.debug(f"Could not parse session date: {session_date}")
                            continue
                        
                        # プロジェクト日付の解析
                        project_datetime = None
                        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y', '%m-%d-%Y', '%m/%d/%Y']:
                            try:
                                project_datetime = datetime.strptime(project_date, fmt)
                                logger.debug(f"Parsed project date {project_date} with format {fmt}")
                                break
                            except ValueError:
                                continue
                        
                        if not project_datetime:
                            logger.debug(f"Could not parse project date: {project_date}")
                            continue
                        
                        # 日付が一致する場合
                        if session_datetime.date() == project_datetime.date():
                            logger.info(f"Auto-assigning session {session.session_id} to project {project.project_id} based on normalized date match: {session_datetime.date()}")
                            return project.project_id
                    except Exception as e:
                        logger.warning(f"Error during date comparison: {str(e)}")
                        # 日付変換に失敗した場合は単純比較の結果のみ使用
        
        # Location-based matching
        if 'location' in session.metadata and session.metadata['location']:
            session_location = str(session.metadata['location']).lower().strip()
            for project in projects:
                if 'location' in project.metadata and project.metadata['location']:
                    project_location = str(project.metadata['location']).lower().strip()
                    if session_location == project_location:
                        logger.info(f"Auto-assigning session {session.session_id} to project {project.project_id} based on location match: {session_location}")
                        return project.project_id
        
        # Most recently created project
        try:
            # Sort by creation time
            sorted_projects = sorted(projects, 
                                     key=lambda p: p.created_at, 
                                     reverse=True)
            if sorted_projects:
                logger.info(f"Auto-assigning session {session.session_id} to most recently created project {sorted_projects[0].project_id}")
                return sorted_projects[0].project_id
        except Exception as e:
            logger.warning(f"Error sorting projects by creation time: {str(e)}")
            # Fallback to first project
            if projects:
                logger.info(f"Falling back to first project {projects[0].project_id} for session {session.session_id}")
                return projects[0].project_id
        
        logger.info(f"No suitable project found for session {session.session_id}")
        return None
    
    def apply_project_settings(self, session_id: str, project_id: str) -> bool:
        """
        Apply project settings to session
        
        Parameters
        ----------
        session_id : str
            Session ID to apply settings to
        project_id : str
            Project ID to get settings from
        
        Returns
        -------
        bool
            True if successful
        """
        project = self.project_storage.get_project(project_id)
        session = self.project_storage.get_session(session_id)
        
        if not project:
            logger.error(f"Project {project_id} not found")
            return False
        
        if not session:
            logger.error(f"Session {session_id} not found")
            return False
        
        # Settings to apply:
        # 1. Tags inheritance
        # 2. Metadata inheritance
        # 3. Category inheritance
        
        # Tags inheritance (project tags are added to session tags)
        for tag in project.tags:
            if tag not in session.tags:
                session.add_tag(tag)
        
        # Metadata inheritance (project default settings are added to session metadata, if not already present)
        # ここが問題の箇所 - プロジェクト設定をセッションメタデータに正しく適用していない
        project_settings = project.metadata.get("default_session_settings", {})
        for key, value in project_settings.items():
            # 直接セッションメタデータに追加
            session.metadata[key] = value
        
        # Category inheritance
        if hasattr(project, 'category') and hasattr(session, 'category'):
            if not session.category and project.category:
                session.category = project.category
        
        # Save session
        return self.project_storage.save_session(session)
    
    def process_batch_import(self, sessions: List[Session], containers: Dict[str, GPSDataContainer],
                           target_project_id: Optional[str] = None) -> Dict[str, str]:
        """
        Process batch import
        
        Parameters
        ----------
        sessions : List[Session]
            List of imported sessions
        containers : Dict[str, GPSDataContainer]
            Dictionary of data containers, keyed by session ID
        target_project_id : Optional[str], optional
            Target project ID to assign to, by default None
        
        Returns
        -------
        Dict[str, str]
            Dictionary mapping session IDs to assigned project IDs
        """
        results = {}
        
        for session in sessions:
            container = containers.get(session.session_id)
            if not container:
                logger.error(f"Container for session {session.session_id} not found")
                # If container not found but target_project_id provided, still add to results
                if target_project_id:
                    results[session.session_id] = target_project_id
                continue
            
            success, project_id = self.process_import_result(
                session, container, target_project_id, auto_assign=True
            )
            
            # If successful, add to results
            if success:
                # If project_id is None but processing was successful,
                # use the target_project_id as fallback
                results[session.session_id] = project_id or target_project_id
        
        # If no results but sessions and target_project_id exist, use target_project_id for all
        if not results and sessions and target_project_id:
            for session in sessions:
                results[session.session_id] = target_project_id
                
        return results
    
    def create_project_for_import(self, name: str, description: str = "",
                                tags: List[str] = None, metadata: Dict[str, Any] = None,
                                sessions: List[Session] = None,
                                containers: Dict[str, GPSDataContainer] = None) -> Optional[str]:
        """
        Create a new project for import
        
        Parameters
        ----------
        name : str
            Project name
        description : str, optional
            Project description, by default ""
        tags : List[str], optional
            Project tags, by default None
        metadata : Dict[str, Any], optional
            Additional metadata, by default None
        sessions : List[Session], optional
            List of sessions to add to project, by default None
        containers : Dict[str, GPSDataContainer], optional
            Dictionary of data containers, keyed by session ID, by default None
        
        Returns
        -------
        Optional[str]
            Created project ID, or None if failed
        """
        # Create project
        project = self.project_storage.create_project(name, description, tags, metadata)
        
        if not project:
            logger.error("Failed to create project")
            return None
        
        # Process sessions
        if sessions:
            for session in sessions:
                # Save session
                self.project_storage.save_session(session)
                
                # Save container
                if containers and session.session_id in containers:
                    container = containers[session.session_id]
                    self.project_storage.save_container(container, session.session_id)
                
                # Assign to project
                self.assign_to_project(session.session_id, project.project_id)
                
                # Apply project settings
                self.apply_project_settings(session.session_id, project.project_id)
        
        return project.project_id