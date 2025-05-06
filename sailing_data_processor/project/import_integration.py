# -*- coding: utf-8 -*-
"""
sailing_data_processor.project.import_integration

���ȷ���h����ȷ���n#:�LF����
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

# ��n-�
logger = logging.getLogger(__name__)

class ImportIntegration:
    """
    �����#:��
    
    ���ȷ���h����ȷ���n#:�LF��
    �����P�n������r�Sf�����-�k�eO
    ������W~Y
    
    ^'
    -----
    project_storage : ProjectStorage
        ���ȹ����
    """
    
    def __init__(self, project_storage: ProjectStorage):
        """
        �����#:n
        
        Parameters
        ----------
        project_storage : ProjectStorage
            ���ȹ����
        """
        self.project_storage = project_storage
    
    def assign_to_project(self, session_id: str, project_id: str, 
                         display_name: Optional[str] = None) -> bool:
        """
        �÷������kr�Sf
        
        Parameters
        ----------
        session_id : str
            r�Sf��÷��ID
        project_id : str
            r�SfHn����ID
        display_name : Optional[str], optional
            ���ȅgnh:, by default None
        
        Returns
        -------
        bool
            r�Sfk�W_4True
        """
        project = self.project_storage.get_project(project_id)
        session = self.project_storage.get_session(session_id)
        
        if not project:
            logger.error(f"���� {project_id} L�dK�~[�")
            return False
        
        if not session:
            logger.error(f"�÷�� {session_id} L�dK�~[�")
            return False
        
        # �÷���gn\
        reference = SessionReference(
            session_id=session_id,
            display_name=display_name or session.name,
            description=session.description
        )
        
        # �÷���1n��÷���
        reference.update_cached_info(session)
        
        # ����n�÷����k��
        # �: �Xn�÷���Ȓ;(Wdd�÷���g���g�Y�_�n��LŁ
        # ��n���ȯ�o�÷��IDn�Ȓd`Qjng��'��ajL�n�5LŁ
        project.add_session(session_id)
        
        # �÷���g�n_�����n�����)(
        if "session_references" not in project.metadata:
            project.metadata["session_references"] = {}
        
        project.metadata["session_references"][session_id] = reference.to_dict()
        
        # ���Ȓ�X
        return self.project_storage.save_project(project)
    
    def remove_from_project(self, session_id: str, project_id: str) -> bool:
        """
        �÷������K�Jd
        
        Parameters
        ----------
        session_id : str
            JdY��÷��ID
        project_id : str
            JdCn����ID
        
        Returns
        -------
        bool
            Jdk�W_4True
        """
        project = self.project_storage.get_project(project_id)
        
        if not project:
            logger.error(f"���� {project_id} L�dK�~[�")
            return False
        
        # ����K��÷��Jd
        if project.remove_session(session_id):
            # �÷���g�Jd
            if "session_references" in project.metadata and session_id in project.metadata["session_references"]:
                del project.metadata["session_references"][session_id]
            
            # ���Ȓ�X
            return self.project_storage.save_project(project)
        
        return False
    
    def update_session_reference(self, project_id: str, session_id: str, 
                               display_name: Optional[str] = None, 
                               description: Optional[str] = None,
                               order: Optional[int] = None,
                               view_settings: Optional[Dict[str, Any]] = None) -> bool:
        """
        �÷���g���
        
        Parameters
        ----------
        project_id : str
            ����ID
        session_id : str
            �÷��ID
        display_name : Optional[str], optional
            �WDh:, by default None
        description : Optional[str], optional
            �WD�, by default None
        order : Optional[int], optional
            �WDh:�, by default None
        view_settings : Optional[Dict[str, Any]], optional
            �WDh:-�, by default None
        
        Returns
        -------
        bool
            ��k�W_4True
        """
        project = self.project_storage.get_project(project_id)
        
        if not project:
            logger.error(f"���� {project_id} L�dK�~[�")
            return False
        
        # �÷���gn֗
        if ("session_references" not in project.metadata or 
            session_id not in project.metadata["session_references"]):
            # �÷���gLjD4o��\
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
                    logger.error(f"�÷�� {session_id} L�dK�~[�")
                    return False
            else:
                logger.error(f"�÷�� {session_id} o���� {project_id} k+~�fD~[�")
                return False
        
        # �÷���gn��
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
        
        # ��W_�÷���g��X
        project.metadata["session_references"][session_id] = reference.to_dict()
        
        # ���Ȓ�X
        return self.project_storage.save_project(project)
    
    def process_import_result(self, session: Session, container: GPSDataContainer,
                            target_project_id: Optional[str] = None,
                            auto_assign: bool = True) -> Tuple[bool, Optional[str]]:
        """
        �����P���
        
        Parameters
        ----------
        session : Session
            �����U�_�÷��
        container : GPSDataContainer
            �����U�_�������
        target_project_id : Optional[str], optional
            r�SfHn����ID, by default None
        auto_assign : bool, optional
            ��r�Sf�LFKiFK, by default True
        
        Returns
        -------
        Tuple[bool, Optional[str]]
            (�W_KiFK, r�Sf��_����ID)
        """
        # �÷��h���ʒ�X
        if not self.project_storage.save_session(session):
            logger.error(f"�÷�� {session.session_id} n�Xk1WW~W_")
            return False, None
        
        if not self.project_storage.save_container(container, session.session_id):
            logger.error(f"�������n�Xk1WW~W_")
            return False, None
        
        # y�n����kr�Sf�4
        if target_project_id:
            success = self.assign_to_project(session.session_id, target_project_id)
            if success:
                logger.info(f"�÷�� {session.session_id} ����� {target_project_id} kr�Sf~W_")
                return True, target_project_id
            else:
                logger.error(f"�÷�� {session.session_id} n���� {target_project_id} xnr�Sfk1WW~W_")
                return False, None
        
        # ��r�Sf�LF4
        if auto_assign:
            project_id = self._auto_assign_project(session, container)
            if project_id:
                success = self.assign_to_project(session.session_id, project_id)
                if success:
                    logger.info(f"�÷�� {session.session_id} ����� {project_id} k��r�SfW~W_")
                    return True, project_id
        
        return True, None
    
    def _auto_assign_project(self, session: Session, container: GPSDataContainer) -> Optional[str]:
        """
        �÷��k ij���Ȓ��$�
        
        Parameters
        ----------
        session : Session
            r�Sf��÷��
        container : GPSDataContainer
            �÷��n�������
        
        Returns
        -------
        Optional[str]
            r�SfHn����IDij����LjD4oNone
        """
        # ������r�Sfn�ï
        # 1. ��k�eOr�Sf
        # 2. ��k�eOr�Sf
        # 3. Mn�1k�eOr�Sf
        # 4.  �\U�_����
        
        # �����Ȓ֗
        projects = self.project_storage.get_projects()
        if not projects:
            return None
            
        # ��k�eOr�Sf
        if session.tags and len(session.tags) > 0:
            for project in projects:
                if project.tags and len(project.tags) > 0:
                    # ����n��h �Y�K��
                    # �÷��n��h����n��L1dg� �Y�pr�Sf
                    for tag in session.tags:
                        if tag in project.tags:
                            return project.project_id
        
        # ��k�eOr�Sf
        if 'event_date' in session.metadata and session.metadata['event_date']:
            session_date = str(session.metadata['event_date'])
            for project in projects:
                if 'event_date' in project.metadata and project.metadata['event_date']:
                    project_date = str(project.metadata['event_date'])
                    # �؇W�c�Wf�թ����nUD�8�	
                    if session_date == project_date:
                        return project.project_id
        
        # Mn�1k�eOr�Sf
        if 'location' in session.metadata and session.metadata['location']:
            session_location = str(session.metadata['location'])
            for project in projects:
                if 'location' in project.metadata and project.metadata['location']:
                    project_location = str(project.metadata['location'])
                    if session_location == project_location:
                        return project.project_id
        
        #  �\U�_����
        try:
            # \�Bg��� �	
            sorted_projects = sorted(projects, 
                                     key=lambda p: p.created_at, 
                                     reverse=True)
            if sorted_projects:
                return sorted_projects[0].project_id
        except Exception as e:
            # ���1WBo n���Ȓ�Y
            return projects[0].project_id if projects else None
        
        return None
    
    def apply_project_settings(self, session_id: str, project_id: str) -> bool:
        """
        ����-���÷��ki(
        
        Parameters
        ----------
        session_id : str
            -��i(Y��÷��ID
        project_id : str
            -�Cn����ID
        
        Returns
        -------
        bool
            i(k�W_4True
        """
        project = self.project_storage.get_project(project_id)
        session = self.project_storage.get_session(session_id)
        
        if not project:
            logger.error(f"���� {project_id} L�dK�~[�")
            return False
        
        if not session:
            logger.error(f"�÷�� {session_id} L�dK�~[�")
            return False
        
        # ����-�ni(
        # 1. ��n�
        # 2. ����n�
        # 3. �ƴ�n�
        
        # ��n�����n����÷��k��	
        for tag in project.tags:
            if tag not in session.tags:
                session.add_tag(tag)
        
        # ����n�����n������÷��k���Xn$o
�MWjD	
        project_settings = project.metadata.get("default_session_settings", {})
        for key, value in project_settings.items():
            if key not in session.metadata:
                session.update_metadata(key, value)
        
        # �ƴ�n�
        if hasattr(project, 'category') and hasattr(session, 'category'):
            if not session.category and project.category:
                session.category = project.category
        
        # �÷���X
        return self.project_storage.save_session(session)
    
    def process_batch_import(self, sessions: List[Session], containers: Dict[str, GPSDataContainer],
                           target_project_id: Optional[str] = None) -> Dict[str, str]:
        """
        ��������P���
        
        Parameters
        ----------
        sessions : List[Session]
            �����U�_�÷��n��
        containers : Dict[str, GPSDataContainer]
            �÷��ID���hY��������n��
        target_project_id : Optional[str], optional
            r�SfHn����ID, by default None
        
        Returns
        -------
        Dict[str, str]
            �÷��ID���r�Sf��_����ID�$hY���
        """
        results = {}
        
        for session in sessions:
            container = containers.get(session.session_id)
            if not container:
                logger.error(f"�÷�� {session.session_id} n�������L�dK�~[�")
                # ����L�dK�jOf�ƹ���n_�P�k������
                if target_project_id:
                    results[session.session_id] = target_project_id
                continue
            
            success, project_id = self.process_import_result(
                session, container, target_project_id, auto_assign=True
            )
            
            # �W_4o����IDLBcf�jOf�P�k��
            if success:
                # ����IDLjD4o��r�Sfk1WW_4jng
                # �U�_����ID��թ��hWf(
                results[session.session_id] = project_id or target_project_id
        
        # ƹ����÷��h���������IDLB�nkresultsLzn4n�V
        if not results and sessions and target_project_id:
            for session in sessions:
                results[session.session_id] = target_project_id
                
        return results
    
    def create_project_for_import(self, name: str, description: str = "",
                                tags: List[str] = None, metadata: Dict[str, Any] = None,
                                sessions: List[Session] = None,
                                containers: Dict[str, GPSDataContainer] = None) -> Optional[str]:
        """
        �����(n�WD���Ȓ\
        
        Parameters
        ----------
        name : str
            ����
        description : str, optional
            ����n�, by default ""
        tags : List[str], optional
            ����k�#Y���, by default None
        metadata : Dict[str, Any], optional
            ��n����, by default None
        sessions : List[Session], optional
            ����k��Y��÷��n��, by default None
        containers : Dict[str, GPSDataContainer], optional
            �÷��ID���hY��������n��, by default None
        
        Returns
        -------
        Optional[str]
            \U�_����ID1WW_4oNone
        """
        # ����n\
        project = self.project_storage.create_project(name, description, tags, metadata)
        
        if not project:
            logger.error("����n\k1WW~W_")
            return None
        
        # �÷��n��
        if sessions:
            for session in sessions:
                # �÷��n�X
                self.project_storage.save_session(session)
                
                # ����n�X
                if containers and session.session_id in containers:
                    container = containers[session.session_id]
                    self.project_storage.save_container(container, session.session_id)
                
                # ����k�÷����
                self.assign_to_project(session.session_id, project.project_id)
                
                # ����-�ni(
                self.apply_project_settings(session.session_id, project.project_id)
        
        return project.project_id