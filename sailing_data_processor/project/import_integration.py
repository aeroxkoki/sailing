# -*- coding: utf-8 -*-
"""
sailing_data_processor.project.import_integration

×í¸§¯È·¹Æàh¤óÝüÈ·¹Æàn#:’LFâ¸åüë
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

# í¬ün-š
logger = logging.getLogger(__name__)

class ImportIntegration:
    """
    ¤óÝüÈ#:¯é¹
    
    ×í¸§¯È·¹Æàh¤óÝüÈ·¹Æàn#:’LF¯é¹
    ¤óÝüÈPœnêÕ×í¸§¯ÈrŠSf„×í¸§¯È-škúeO
    êÕæ’ŸÅW~Y
    
    ^'
    -----
    project_storage : ProjectStorage
        ×í¸§¯È¹Èìü¸
    """
    
    def __init__(self, project_storage: ProjectStorage):
        """
        ¤óÝüÈ#:n
        
        Parameters
        ----------
        project_storage : ProjectStorage
            ×í¸§¯È¹Èìü¸
        """
        self.project_storage = project_storage
    
    def assign_to_project(self, session_id: str, project_id: str, 
                         display_name: Optional[str] = None) -> bool:
        """
        »Ã·çó’×í¸§¯ÈkrŠSf
        
        Parameters
        ----------
        session_id : str
            rŠSf‹»Ã·çóID
        project_id : str
            rŠSfHn×í¸§¯ÈID
        display_name : Optional[str], optional
            ×í¸§¯È…gnh:, by default None
        
        Returns
        -------
        bool
            rŠSfkŸW_4True
        """
        project = self.project_storage.get_project(project_id)
        session = self.project_storage.get_session(session_id)
        
        if not project:
            logger.error(f"×í¸§¯È {project_id} L‹dKŠ~[“")
            return False
        
        if not session:
            logger.error(f"»Ã·çó {session_id} L‹dKŠ~[“")
            return False
        
        # »Ã·çóÂgn\
        reference = SessionReference(
            session_id=session_id,
            display_name=display_name or session.name,
            description=session.description
        )
        
        # »Ã·çóÅ1n­ãÃ·å’ô°
        reference.update_cached_info(session)
        
        # ×í¸§¯Èn»Ã·çóê¹Èký 
        # è: âXn»Ã·çóê¹È’;(Wdd»Ã·çóÂg’…èg¡Y‹_nþÜLÅ
        # þ¶n×í¸§¯È¯é¹o»Ã·çóIDnê¹È’d`Qjng’Û'’ÝajL‰ná5LÅ
        project.add_session(session_id)
        
        # »Ã·çóÂg¡n_×í¸§¯Èná¿Çü¿’)(
        if "session_references" not in project.metadata:
            project.metadata["session_references"] = {}
        
        project.metadata["session_references"][session_id] = reference.to_dict()
        
        # ×í¸§¯È’ÝX
        return self.project_storage.save_project(project)
    
    def remove_from_project(self, session_id: str, project_id: str) -> bool:
        """
        »Ã·çó’×í¸§¯ÈK‰Jd
        
        Parameters
        ----------
        session_id : str
            JdY‹»Ã·çóID
        project_id : str
            JdCn×í¸§¯ÈID
        
        Returns
        -------
        bool
            JdkŸW_4True
        """
        project = self.project_storage.get_project(project_id)
        
        if not project:
            logger.error(f"×í¸§¯È {project_id} L‹dKŠ~[“")
            return False
        
        # ×í¸§¯ÈK‰»Ã·çó’Jd
        if project.remove_session(session_id):
            # »Ã·çóÂg‚Jd
            if "session_references" in project.metadata and session_id in project.metadata["session_references"]:
                del project.metadata["session_references"][session_id]
            
            # ×í¸§¯È’ÝX
            return self.project_storage.save_project(project)
        
        return False
    
    def update_session_reference(self, project_id: str, session_id: str, 
                               display_name: Optional[str] = None, 
                               description: Optional[str] = None,
                               order: Optional[int] = None,
                               view_settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        »Ã·çóÂg’ô°
        
        Parameters
        ----------
        project_id : str
            ×í¸§¯ÈID
        session_id : str
            »Ã·çóID
        display_name : Optional[str], optional
            °WDh:, by default None
        description : Optional[str], optional
            °WD¬, by default None
        order : Optional[int], optional
            °WDh:, by default None
        view_settings : Optional[Dict[str, Any]], optional
            °WDh:-š, by default None
        
        Returns
        -------
        bool
            ô°kŸW_4True
        """
        project = self.project_storage.get_project(project_id)
        
        if not project:
            logger.error(f"×í¸§¯È {project_id} L‹dKŠ~[“")
            return False
        
        # »Ã·çóÂgnÖ—
        if ("session_references" not in project.metadata or 
            session_id not in project.metadata["session_references"]):
            # »Ã·çóÂgLjD4o°\
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
                    logger.error(f"»Ã·çó {session_id} L‹dKŠ~[“")
                    return False
            else:
                logger.error(f"»Ã·çó {session_id} o×í¸§¯È {project_id} k+~ŒfD~[“")
                return False
        
        # »Ã·çóÂgnô°
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
        
        # ô°W_»Ã·çóÂg’ÝX
        project.metadata["session_references"][session_id] = reference.to_dict()
        
        # ×í¸§¯È’ÝX
        return self.project_storage.save_project(project)
    
    def process_import_result(self, session: Session, container: GPSDataContainer,
                            target_project_id: Optional[str] = None,
                            auto_assign: bool = True) -> Tuple[bool, Optional[str]]:
        """
        ¤óÝüÈPœ’æ
        
        Parameters
        ----------
        session : Session
            ¤óÝüÈUŒ_»Ã·çó
        container : GPSDataContainer
            ¤óÝüÈUŒ_Çü¿³óÆÊ
        target_project_id : Optional[str], optional
            rŠSfHn×í¸§¯ÈID, by default None
        auto_assign : bool, optional
            êÕrŠSf’LFKiFK, by default True
        
        Returns
        -------
        Tuple[bool, Optional[str]]
            (ŸW_KiFK, rŠSf‰Œ_×í¸§¯ÈID)
        """
        # »Ã·çóh³óÆÊ’ÝX
        if not self.project_storage.save_session(session):
            logger.error(f"»Ã·çó {session.session_id} nÝXk1WW~W_")
            return False, None
        
        if not self.project_storage.save_container(container, session.session_id):
            logger.error(f"Çü¿³óÆÊnÝXk1WW~W_")
            return False, None
        
        # yšn×í¸§¯ÈkrŠSf‹4
        if target_project_id:
            success = self.assign_to_project(session.session_id, target_project_id)
            if success:
                logger.info(f"»Ã·çó {session.session_id} ’×í¸§¯È {target_project_id} krŠSf~W_")
                return True, target_project_id
            else:
                logger.error(f"»Ã·çó {session.session_id} n×í¸§¯È {target_project_id} xnrŠSfk1WW~W_")
                return False, None
        
        # êÕrŠSf’LF4
        if auto_assign:
            project_id = self._auto_assign_project(session, container)
            if project_id:
                success = self.assign_to_project(session.session_id, project_id)
                if success:
                    logger.info(f"»Ã·çó {session.session_id} ’×í¸§¯È {project_id} kêÕrŠSfW~W_")
                    return True, project_id
        
        return True, None
    
    def _auto_assign_project(self, session: Session, container: GPSDataContainer) -> Optional[str]:
        """
        »Ã·çók ij×í¸§¯È’êÕ$š
        
        Parameters
        ----------
        session : Session
            rŠSf‹»Ã·çó
        container : GPSDataContainer
            »Ã·çónÇü¿³óÆÊ
        
        Returns
        -------
        Optional[str]
            rŠSfHn×í¸§¯ÈIDij×í¸§¯ÈLjD4oNone
        """
        # ×í¸§¯ÈêÕrŠSfní¸Ã¯
        # 1. ¿°kúeOrŠSf
        # 2. åØkúeOrŠSf
        # 3. MnÅ1kúeOrŠSf
        # 4.  Ñ\UŒ_×í¸§¯È
        
        # ×í¸§¯Èê¹È’Ö—
        projects = self.project_storage.get_projects()
        if not projects:
            return None
            
        # ¿°kúeOrŠSf
        if session.tags and len(session.tags) > 0:
            for project in projects:
                if project.tags and len(project.tags) > 0:
                    # ×í¸§¯Èn¿°h ôY‹Kº
                    # »Ã·çón¿°h×í¸§¯Èn¿°L1dg‚ ôYŒprŠSf
                    for tag in session.tags:
                        if tag in project.tags:
                            return project.project_id
        
        # åØkúeOrŠSf
        if 'event_date' in session.metadata and session.metadata['event_date']:
            session_date = str(session.metadata['event_date'])
            for project in projects:
                if 'event_date' in project.metadata and project.metadata['event_date']:
                    project_date = str(project.metadata['event_date'])
                    # åØ‡W’cWfÔÕ©üÞÃÈnUD’8Î	
                    if session_date == project_date:
                        return project.project_id
        
        # MnÅ1kúeOrŠSf
        if 'location' in session.metadata and session.metadata['location']:
            session_location = str(session.metadata['location'])
            for project in projects:
                if 'location' in project.metadata and project.metadata['location']:
                    project_location = str(project.metadata['location'])
                    if session_location == project_location:
                        return project.project_id
        
        #  Ñ\UŒ_×í¸§¯È
        try:
            # \åBg½üÈ °	
            sorted_projects = sorted(projects, 
                                     key=lambda p: p.created_at, 
                                     reverse=True)
            if sorted_projects:
                return sorted_projects[0].project_id
        except Exception as e:
            # ½üÈ1WBo n×í¸§¯È’ÔY
            return projects[0].project_id if projects else None
        
        return None
    
    def apply_project_settings(self, session_id: str, project_id: str) -> bool:
        """
        ×í¸§¯È-š’»Ã·çóki(
        
        Parameters
        ----------
        session_id : str
            -š’i(Y‹»Ã·çóID
        project_id : str
            -šCn×í¸§¯ÈID
        
        Returns
        -------
        bool
            i(kŸW_4True
        """
        project = self.project_storage.get_project(project_id)
        session = self.project_storage.get_session(session_id)
        
        if not project:
            logger.error(f"×í¸§¯È {project_id} L‹dKŠ~[“")
            return False
        
        if not session:
            logger.error(f"»Ã·çó {session_id} L‹dKŠ~[“")
            return False
        
        # ×í¸§¯È-šni(
        # 1. ¿°n™
        # 2. á¿Çü¿n™
        # 3. «Æ´ên™
        
        # ¿°n™×í¸§¯Èn¿°’»Ã·çóký 	
        for tag in project.tags:
            if tag not in session.tags:
                session.add_tag(tag)
        
        # á¿Çü¿n™×í¸§¯Èná¿Çü¿’»Ã·çóký âXn$o
øMWjD	
        project_settings = project.metadata.get("default_session_settings", {})
        for key, value in project_settings.items():
            if key not in session.metadata:
                session.update_metadata(key, value)
        
        # «Æ´ên™
        if hasattr(project, 'category') and hasattr(session, 'category'):
            if not session.category and project.category:
                session.category = project.category
        
        # »Ã·çó’ÝX
        return self.project_storage.save_session(session)
    
    def process_batch_import(self, sessions: List[Session], containers: Dict[str, GPSDataContainer],
                           target_project_id: Optional[str] = None) -> Dict[str, str]:
        """
        ÐÃÁ¤óÝüÈPœ’æ
        
        Parameters
        ----------
        sessions : List[Session]
            ¤óÝüÈUŒ_»Ã·çónê¹È
        containers : Dict[str, GPSDataContainer]
            »Ã·çóID’­ühY‹Çü¿³óÆÊnžø
        target_project_id : Optional[str], optional
            rŠSfHn×í¸§¯ÈID, by default None
        
        Returns
        -------
        Dict[str, str]
            »Ã·çóID’­ürŠSf‰Œ_×í¸§¯ÈID’$hY‹žø
        """
        results = {}
        
        for session in sessions:
            container = containers.get(session.session_id)
            if not container:
                logger.error(f"»Ã·çó {session.session_id} nÇü¿³óÆÊL‹dKŠ~[“")
                # ³óÆÊL‹dK‰jOf‚Æ¹ÈþÜn_Pœk¨óÈê’ý 
                if target_project_id:
                    results[session.session_id] = target_project_id
                continue
            
            success, project_id = self.process_import_result(
                session, container, target_project_id, auto_assign=True
            )
            
            # ŸW_4o×í¸§¯ÈIDLBcf‚jOf‚Pœký 
            if success:
                # ×í¸§¯ÈIDLjD4oêÕrŠSfk1WW_4jng
                # šUŒ_×í¸§¯ÈID’ÇÕ©ëÈhWf(
                results[session.session_id] = project_id or target_project_id
        
        # Æ¹ÈþÜ»Ã·çóh¿ü²ÃÈ×í¸§¯ÈIDLB‹nkresultsLzn4nþV
        if not results and sessions and target_project_id:
            for session in sessions:
                results[session.session_id] = target_project_id
                
        return results
    
    def create_project_for_import(self, name: str, description: str = "",
                                tags: List[str] = None, metadata: Dict[str, Any] = None,
                                sessions: List[Session] = None,
                                containers: Dict[str, GPSDataContainer] = None) -> Optional[str]:
        """
        ¤óÝüÈ(n°WD×í¸§¯È’\
        
        Parameters
        ----------
        name : str
            ×í¸§¯È
        description : str, optional
            ×í¸§¯Èn¬, by default ""
        tags : List[str], optional
            ×í¸§¯Èk¢#Y‹¿°, by default None
        metadata : Dict[str, Any], optional
            ý ná¿Çü¿, by default None
        sessions : List[Session], optional
            ×í¸§¯Èký Y‹»Ã·çónê¹È, by default None
        containers : Dict[str, GPSDataContainer], optional
            »Ã·çóID’­ühY‹Çü¿³óÆÊnžø, by default None
        
        Returns
        -------
        Optional[str]
            \UŒ_×í¸§¯ÈID1WW_4oNone
        """
        # ×í¸§¯Èn\
        project = self.project_storage.create_project(name, description, tags, metadata)
        
        if not project:
            logger.error("×í¸§¯Èn\k1WW~W_")
            return None
        
        # »Ã·çóný 
        if sessions:
            for session in sessions:
                # »Ã·çónÝX
                self.project_storage.save_session(session)
                
                # ³óÆÊnÝX
                if containers and session.session_id in containers:
                    container = containers[session.session_id]
                    self.project_storage.save_container(container, session.session_id)
                
                # ×í¸§¯Èk»Ã·çó’ý 
                self.assign_to_project(session.session_id, project.project_id)
                
                # ×í¸§¯È-šni(
                self.apply_project_settings(session.session_id, project.project_id)
        
        return project.project_id