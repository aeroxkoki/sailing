# -*- coding: utf-8 -*-
"""
ui.components.session.session_detail

�÷��s0h:nUI�������
"""

import streamlit as st
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime

from sailing_data_processor.project.project_manager import ProjectManager, Session
from sailing_data_processor.project.session_manager import SessionManager
from sailing_data_processor.project.session_model import SessionModel, SessionResult


def format_datetime(iso_datetime: str) -> str:
    """ISObn�B���YDbk	�"""
    try:
        dt = datetime.fromisoformat(iso_datetime)
        return dt.strftime("%Y/%m/%d %H:%M")
    except (ValueError, TypeError):
        return iso_datetime


class SessionDetailComponent:
    """
    �5U�_�÷��s0�������
    
    Parameters
    ----------
    key : str, optional
        ������ȭ�, by default "session_detail"
    session_manager : SessionManager, optional
        �÷����n���, by default None
    project_manager : ProjectManager, optional
        �����ȡ��n���, by default None
    on_edit : Callable[[str], None], optional
        ��ܿ�Bn����ï�p, by default None
    on_delete : Callable[[str], None], optional
        Jdܿ�Bn����ï�p, by default None
    on_close : Callable[[], None], optional
        �X�ܿ�Bn����ï�p, by default None
    on_result_select : Callable[[str], None], optional
        P�x�Bn����ï�p, by default None
    """
    
    def __init__(
        self,
        key: str = "session_detail",
        session_manager: SessionManager = None,
        project_manager: ProjectManager = None,
        on_edit: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
        on_result_select: Optional[Callable[[str], None]] = None
    ):
        """
        �˷�餶
        
        Parameters
        ----------
        key : str, optional
            ������ȭ�, by default "session_detail"
        session_manager : SessionManager, optional
            �÷����n���, by default None
        project_manager : ProjectManager, optional
            �����ȡ��n���, by default None
        on_edit : Callable[[str], None], optional
            ��ܿ�Bn����ï�p, by default None
        on_delete : Callable[[str], None], optional
            Jdܿ�Bn����ï�p, by default None
        on_close : Callable[[], None], optional
            �X�ܿ�Bn����ï�p, by default None
        on_result_select : Callable[[str], None], optional
            P�x�Bn����ï�p, by default None
        """
        self.key = key
        self.session_manager = session_manager
        self.project_manager = project_manager or (session_manager.project_manager if session_manager else None)
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_close = on_close
        self.on_result_select = on_result_select
        
        # �÷��Kn
        if f"{key}_confirm_delete" not in st.session_state:
            st.session_state[f"{key}_confirm_delete"] = False
        
        if f"{key}_add_relation" not in st.session_state:
            st.session_state[f"{key}_add_relation"] = False
        
        if f"{key}_show_versions" not in st.session_state:
            st.session_state[f"{key}_show_versions"] = {}
            
        if f"{key}_active_tab" not in st.session_state:
            st.session_state[f"{key}_active_tab"] = "metadata"
            
        if f"{key}_edit_mode" not in st.session_state:
            st.session_state[f"{key}_edit_mode"] = False
    
    def get_associated_projects(self, session_id: str) -> List[Dict[str, Any]]:
        """
        �÷��L�#�Q��fD�������n�Ȓ֗
        
        Parameters
        ----------
        session_id : str
            �÷��ID
            
        Returns
        -------
        List[Dict[str, Any]]
            �#�������1n��
        """
        if not self.project_manager:
            return []
        
        projects = self.project_manager.get_projects()
        associated_projects = []
        
        for project in projects:
            if session_id in project.sessions:
                associated_projects.append({
                    "id": project.project_id,
                    "name": project.name,
                    "description": project.description,
                    "created_at": format_datetime(project.created_at)
                })
        
        return associated_projects
    
    def render_metadata_editor(self, session: Session) -> None:
        """
        �����ǣ�n�����
        
        Parameters
        ----------
        session : Session
            �÷��ָ���
        """
        with st.expander("�÷���1", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**
M:** {session.name}")
                st.markdown(f"**�:** {session.description}" if session.description else "**�:** *jW*")
                st.markdown(f"**�ƴ�:** {session.category}" if hasattr(session, 'category') and session.category else "**�ƴ�:** **-�*")
                st.markdown(f"**�����:** {session.status}" if hasattr(session, 'status') and session.status else "**�����:** **-�*")
                
                # U�nh:
                rating = getattr(session, 'rating', 0)
                stars = "" * rating + "" * (5 - rating)
                st.markdown(f"**U�:** {stars} ({rating}/5)")
                
                # �����Bnh:
                event_date = None
                if hasattr(session, 'event_date') and session.event_date:
                    event_date = format_datetime(session.event_date)
                elif 'event_date' in session.metadata and session.metadata['event_date']:
                    event_date = format_datetime(session.metadata['event_date'])
                
                if event_date:
                    st.markdown(f"**�����B:** {event_date}")
                else:
                    st.markdown("**�����B:** **-�*")
                
                # Mn�1nh:
                location = None
                if hasattr(session, 'location') and session.location:
                    location = session.location
                elif 'location' in session.metadata and session.metadata['location']:
                    location = session.metadata['location']
                
                if location:
                    st.markdown(f"**Mn�1:** {location}")
                else:
                    st.markdown("**Mn�1:** **-�*")
                
                # �÷��IDh\�
                st.markdown(f"**�÷��ID:** `{session.session_id}`")
                st.markdown(f"**\�:** {format_datetime(session.created_at)}")
                st.markdown(f"**���:** {format_datetime(session.updated_at)}")
                
                if session.source_file:
                    st.markdown(f"**���ա��:** {session.source_file}")
                if session.source_type:
                    st.markdown(f"**������:** {session.source_type}")
            
            with col2:
                # ��
                tags_str = ", ".join(session.tags) if session.tags else "jW"
                st.markdown(f"**��:** {tags_str}")
                
                # ����h:event_datehlocationo%h:Y�_�d	
                for key, value in session.metadata.items():
                    if key not in ["created_by", "related_sessions", "event_date", "location"] and value:
                        st.markdown(f"**{key}:** {value}")
    
    def render_tags_editor(self, session_id: str, current_tags: List[str]) -> None:
        """
        ���ǣ�n�����
        
        Parameters
        ----------
        session_id : str
            �÷��ID
        current_tags : List[str]
            �(n����
        """
        if not self.session_manager:
            return
        
        with st.expander("���", expanded=False):
            # )(��j��n֗
            all_tags = self.session_manager.get_available_tags()
            
            # ��x�
            selected_tags = st.multiselect(
                "��",
                options=all_tags,
                default=current_tags,
                key=f"{self.key}_edit_tags"
            )
            
            # �WD��n��
            new_tag = st.text_input(
                "�WD��������:�gp���	",
                key=f"{self.key}_new_tag"
            )
            
            # ��ܿ�
            if st.button("�����", key=f"{self.key}_update_tags", use_container_width=True):
                final_tags = selected_tags.copy()
                
                # �WD��n�
                if new_tag:
                    additional_tags = [tag.strip() for tag in new_tag.split(",") if tag.strip()]
                    final_tags.extend(additional_tags)
                    # ��Jd
                    final_tags = list(set(final_tags))
                
                # ����
                if self.session_manager.update_session_tags(session_id, final_tags):
                    st.success("�����W~W_")
                    st.rerun()
                else:
                    st.error("��n��k1WW~W_")
    
    def render_rating_editor(self, session_id: str, current_rating: int) -> None:
        """
        U��ǣ�n�����
        
        Parameters
        ----------
        session_id : str
            �÷��ID
        current_rating : int
            �(nU�$
        """
        if not self.session_manager:
            return
        
        with st.expander("U�", expanded=False):
            # U�n��
            new_rating = st.slider(
                "�÷��U�",
                min_value=0,
                max_value=5,
                value=current_rating,
                step=1,
                key=f"{self.key}_edit_rating"
            )
            
            # ��ܿ�
            if st.button("U����", key=f"{self.key}_update_rating", use_container_width=True):
                if self.session_manager.update_session_rating(session_id, new_rating):
                    st.success("U����W~W_")
                    st.rerun()
                else:
                    st.error("U�n��k1WW~W_")
    
    def render_related_sessions(self, session_id: str) -> None:
        """
        �#�÷��n�����
        
        Parameters
        ----------
        session_id : str
            �÷��ID
        """
        if not self.session_manager:
            return
        
        # �#�÷��n֗
        parent_sessions = self.session_manager.get_related_sessions(session_id, "parent")
        child_sessions = self.session_manager.get_related_sessions(session_id, "child")
        related_sessions = self.session_manager.get_related_sessions(session_id, "related")
        
        # �#�÷��n	!��ï
        has_related = bool(parent_sessions or child_sessions or related_sessions)
        
        # �#�÷��LjD4
        if not has_related:
            st.info("Sn�÷��ko~`�#�÷��LB�~[�")
        
        # ��÷��nh:
        if parent_sessions:
            st.markdown("#### ��÷��")
            for session in parent_sessions:
                self._render_related_session_card(session, session_id, "parent")
        
        # P�÷��nh:
        if child_sessions:
            st.markdown("#### P�÷��")
            for session in child_sessions:
                self._render_related_session_card(session, session_id, "child")
        
        # �#�÷��nh:
        if related_sessions:
            st.markdown("#### ]n�n�#�÷��")
            for session in related_sessions:
                self._render_related_session_card(session, session_id, "related")
        
        # �#�÷����ܿ�
        if st.button("�#�÷����", key=f"{self.key}_add_relation_btn"):
            st.session_state[f"{self.key}_add_relation"] = True
        
        # �#�÷����թ��
        if st.session_state[f"{self.key}_add_relation"]:
            st.markdown("#### �#�÷��n��")
            
            # �#���x�
            relation_type = st.selectbox(
                "�#���",
                options=["parent", "child", "related"],
                format_func=lambda x: {"parent": "��÷��", "child": "P�÷��", "related": "]n�n�#"}.get(x, x),
                key=f"{self.key}_relation_type"
            )
            
            # �#�Q��÷��nx�
            all_sessions = self.session_manager.get_all_sessions()
            # �꫒d
            all_sessions = [s for s in all_sessions if s.session_id != session_id]
            
            if not all_sessions:
                st.warning("�#�Q��÷��LB�~[�")
            else:
                related_session_id = st.selectbox(
                    "�#�Q��÷��",
                    options=[s.session_id for s in all_sessions],
                    format_func=lambda x: next((s.name for s in all_sessions if s.session_id == x), x),
                    key=f"{self.key}_related_session_id"
                )
                
                # ��ܿ�
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("��", key=f"{self.key}_add_relation_submit", use_container_width=True):
                        if self.session_manager.add_related_session(session_id, related_session_id, relation_type):
                            st.success("�#�÷����W~W_")
                            st.session_state[f"{self.key}_add_relation"] = False
                            st.rerun()
                        else:
                            st.error("�#�÷��n��k1WW~W_")
                
                with col2:
                    if st.button("����", key=f"{self.key}_add_relation_cancel", use_container_width=True):
                        st.session_state[f"{self.key}_add_relation"] = False
                        st.rerun()
    
    def _render_related_session_card(self, session: Session, current_session_id: str, relation_type: str) -> None:
        """
        �#�÷����n�����
        
        Parameters
        ----------
        session : Session
            �÷��ָ���
        current_session_id : str
            �(n�÷��ID
        relation_type : str
            �#���
        """
        # ��ɹ���n����
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{session.name}**")
                if session.description:
                    st.markdown(f"{session.description[:50]}..." if len(session.description) > 50 else session.description)
                
                # ��h�ƴ�nh:
                tags_str = ", ".join(session.tags) if session.tags else "jW"
                st.markdown(f"��: {tags_str}")
                
                if hasattr(session, 'category') and session.category:
                    st.markdown(f"�ƴ�: {session.category}")
            
            with col2:
                # h:ܿ�
                if st.button("h:", key=f"{self.key}_view_related_{session.session_id}", use_container_width=True):
                    # �÷��Kkx�U�_�÷��ID����
                    st.session_state.selected_session_id = session.session_id
                    st.rerun()
                
                # Jdܿ�
                if st.button("�#Jd", key=f"{self.key}_remove_related_{session.session_id}", use_container_width=True):
                    if self.session_manager.remove_related_session(current_session_id, session.session_id, relation_type):
                        st.success("�#�JdW~W_")
                        st.rerun()
                    else:
                        st.error("�#nJdk1WW~W_")
    
    def render_results_section(self, session_id: str) -> None:
        """
        P������n�����
        
        Parameters
        ----------
        session_id : str
            �÷��ID
        """
        if not self.session_manager:
            return
        
        # �÷��nP��֗
        results = self.session_manager.get_session_results(session_id)
        
        if not results:
            st.info("Sn�÷��ko~`�P�LB�~[�")
            return
        
        # P����g����
        result_types = {}
        for result in results:
            if result.result_type not in result_types:
                result_types[result.result_type] = []
            result_types[result.result_type].append(result)
        
        # P����Thkh:
        for result_type, type_results in result_types.items():
            st.markdown(f"#### {self._format_result_type(result_type)}")
            
            for result in type_results:
                self._render_result_card(result)
    
    def _format_result_type(self, result_type: str) -> str:
        """
        P����nh:
�֗
        
        Parameters
        ----------
        result_type : str
            P����
            
        Returns
        -------
        str
            h:(nP����
        """
        # P����nh:
����
        type_names = {
            "wind_estimation": "����",
            "strategy_points": "&eݤ��",
            "performance": "�թ����",
            "data_cleaning": "��������",
            "general": ",�",
            "simulation": "��������",
            "optimization": "i"
        }
        
        return type_names.get(result_type, result_type)
    
    def _render_result_card(self, result: SessionResult) -> None:
        """
        P����n�����
        
        Parameters
        ----------
        result : SessionResult
            P��ָ���
        """
        # ��ɹ���n����
        with st.container(border=True):
            # �����
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # P�
~_o�
                result_name = result.metadata.get("name", f"�P� v{result.version}")
                st.markdown(f"**{result_name}**")
                
                # \�B
                st.markdown(f"\�B: {format_datetime(result.created_at)}")
            
            with col2:
                # ��n����h:
                if "description" in result.metadata:
                    st.markdown(f"�: {result.metadata['description']}")
                
                # ��LB�ph:
                if "tags" in result.metadata and result.metadata["tags"]:
                    tags_str = ", ".join(result.metadata["tags"])
                    st.markdown(f"��: {tags_str}")
            
            with col3:
                # �����h:
                st.markdown(f"�����: {result.version}")
                
                # �(n�����KiFK
                if result.is_current:
                    st.markdown("**[�]**")
                
                # �n�����h:ܿ�
                if st.button("s0h:", key=f"{self.key}_view_result_{result.result_id}", use_container_width=True):
                    if self.on_result_select:
                        self.on_result_select(result.result_id)
                
                # �����eth:ܿ�
                if st.button("�����et", key=f"{self.key}_versions_{result.result_id}", use_container_width=True):
                    # Ȱ�K���
                    current = st.session_state[f"{self.key}_show_versions"].get(result.result_id, False)
                    st.session_state[f"{self.key}_show_versions"][result.result_id] = not current
            
            # �����eth:�
            if st.session_state[f"{self.key}_show_versions"].get(result.result_id, False):
                # P�n������Ȓ֗
                versions = self.session_manager.get_result_versions(result.session_id, result.result_id)
                
                if versions:
                    st.markdown("#### �����et")
                    
                    for version in versions:
                        with st.container(border=True):
                            vcol1, vcol2 = st.columns([3, 1])
                            
                            with vcol1:
                                st.markdown(f"**����� {version.version}**")
                                st.markdown(f"\�B: {format_datetime(version.created_at)}")
                                
                                # ����nh:
                                if "description" in version.metadata:
                                    st.markdown(f"�: {version.metadata['description']}")
                            
                            with vcol2:
                                if version.is_current:
                                    st.markdown("**[�(nH]**")
                                else:
                                    # Sn������(n�����hWf-�Y�ܿ�
                                    if st.button("SnH�(", key=f"{self.key}_use_version_{result.result_id}_{version.version}", use_container_width=True):
                                        # �n�����Yyf^��ƣ�k-�
                                        for v in versions:
                                            v.mark_as_current(False)
                                        
                                        # Sn����󒢯ƣ�k-�
                                        version.mark_as_current(True)
                                        
                                        # ��
                                        st.success(f"����� {version.version} ��(nHk-�W~W_")
                                        st.rerun()
    
    def render_actions(self, session_id: str) -> None:
        """
        �����ܿ�n�����
        
        Parameters
        ----------
        session_id : str
            �÷��ID
        """
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("��", key=f"{self.key}_edit_btn", use_container_width=True):
                if self.on_edit:
                    self.on_edit(session_id)
        
        with col2:
            if st.button("Jd", key=f"{self.key}_delete_btn", use_container_width=True):
                # Jd�������
                st.session_state[f"{self.key}_confirm_delete"] = True
        
        with col3:
            if st.button("�X�", key=f"{self.key}_close_btn", use_container_width=True):
                if self.on_close:
                    self.on_close()
        
        # Jd�������
        if st.session_state[f"{self.key}_confirm_delete"]:
            st.warning("Sn�÷��JdW~YKSn�\oCk;[~[�")
            
            conf_col1, conf_col2 = st.columns(2)
            
            with conf_col1:
                if st.button("Jd���", key=f"{self.key}_confirm_delete_yes", use_container_width=True):
                    if self.on_delete:
                        self.on_delete(session_id)
                    st.session_state[f"{self.key}_confirm_delete"] = False
            
            with conf_col2:
                if st.button("����", key=f"{self.key}_confirm_delete_no", use_container_width=True):
                    st.session_state[f"{self.key}_confirm_delete"] = False
                    st.rerun()
    
    def render(self, session_id: str) -> None:
        """
        �������n�����
        
        Parameters
        ----------
        session_id : str
            h:Y��÷��nID
        """
        if not self.project_manager:
            st.error("�����ȡ��L-�U�fD~[�")
            return
        
        # �÷��n֗
        session = self.project_manager.get_session(session_id)
        if not session:
            st.error(f"�÷��L�dK�~[�: {session_id}")
            return
        
        # �÷������
        self._render_header(session)
        
        # �����ܿ�
        self.render_actions(session_id)
        
        # ��h:
        tabs = ["����", "P�", "�#�÷��"]
        active_tab = st.radio(
            "�����",
            options=tabs,
            index=tabs.index(self._get_active_tab_name()),
            horizontal=True,
            key=f"{self.key}_tab_select"
        )
        
        # ��ƣֿ�n�K���
        if active_tab == "����":
            st.session_state[f"{self.key}_active_tab"] = "metadata"
        elif active_tab == "P�":
            st.session_state[f"{self.key}_active_tab"] = "results"
        elif active_tab == "�#�÷��":
            st.session_state[f"{self.key}_active_tab"] = "related"
            
        # ��n���h:
        if st.session_state[f"{self.key}_active_tab"] == "metadata":
            self._render_metadata_tab(session)
        elif st.session_state[f"{self.key}_active_tab"] == "results":
            self._render_results_tab(session)
        elif st.session_state[f"{self.key}_active_tab"] == "related":
            self._render_related_tab(session)
    
    def _render_header(self, session: SessionModel) -> None:
        """
        �÷������n�����
        
        Parameters
        ----------
        session : SessionModel
            �÷��ָ���
        """
        # ����
        st.subheader(f"�÷��: {session.name}")
        
        # �÷���,�1n����
        header_col1, header_col2, header_col3 = st.columns([1, 1, 1])
        
        with header_col1:
            # �����h:
            status = getattr(session, 'status', 'active')
            
            status_colors = {
                "active": "blue",
                "in_progress": "orange",
                "completed": "green",
                "archived": "gray"
            }
            
            status_display = {
                "active": "��ƣ�",
                "in_progress": "2L-",
                "completed": "��",
                "archived": "�����"
            }
            
            status_color = status_colors.get(status, "blue")
            status_text = status_display.get(status, status)
            
            st.markdown(f"**�����:** :{status_color}[{status_text}]")
        
        with header_col2:
            # �ƴ�h:
            category = getattr(session, 'category', 'analysis')
            category_display = {
                "analysis": "�",
                "training": "�����",
                "race": "���",
                "simulation": "��������",
                "other": "]n�"
            }
            category_text = category_display.get(category, category)
            
            st.markdown(f"**�ƴ�:** {category_text}")
        
        with header_col3:
            # U�h:
            rating = getattr(session, 'rating', 0)
            stars = "" * rating + "" * (5 - rating)
            
            st.markdown(f"**U�:** {stars}")
        
        # ��h:Yyfn��gh:	
        if session.tags and len(session.tags) > 0:
            tag_html = ""
            for tag in session.tags:
                tag_html += f'<span style="background-color: #e1e1e1; padding: 2px 8px; border-radius: 10px; margin-right: 5px; font-size: 0.8em;">{tag}</span>'
            st.markdown(f"<div>{tag_html}</div>", unsafe_allow_html=True)
    
    def _render_metadata_tab(self, session: SessionModel) -> None:
        """
        ������n�����
        
        Parameters
        ----------
        session : SessionModel
            �÷��ָ���
        """
        # �����n��H
        edit_mode = st.toggle("�����", value=st.session_state.get(f"{self.key}_edit_mode", False))
        st.session_state[f"{self.key}_edit_mode"] = edit_mode
        
        if edit_mode:
            self._render_metadata_editor(session)
        else:
            self._render_metadata_view(session)
        
        # ��hU�o8kh:/����
        st.markdown("---")
        
        # ���
        self.render_tags_editor(session.session_id, session.tags or [])
        
        # U���
        rating = getattr(session, 'rating', 0)
        self.render_rating_editor(session.session_id, rating)
        
        # �#������
        associated_projects = self.get_associated_projects(session.session_id)
        with st.expander("�#������", expanded=False):
            if not associated_projects:
                st.info("Sn�÷��oin������k��#�Q��fD~[�")
            else:
                # �����ȧnh:
                st.markdown("Sn�÷��o�n������k�#�Q��fD~Y:")
                
                for project in associated_projects:
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{project['name']}**")
                            st.markdown(f"{project['description'][:50]}..." if len(project['description']) > 50 else project['description'])
                        
                        with col2:
                            if st.button("��", key=f"goto_project_{project['id']}", use_container_width=True):
                                # ������;bxnw�
                                st.session_state.selected_project_id = project['id']
                                st.rerun()
    
    def _render_metadata_editor(self, session: SessionModel) -> None:
        """
        �����ǣ�n�����
        
        Parameters
        ----------
        session : SessionModel
            �÷��ָ���
        """
        with st.form(key=f"{self.key}_metadata_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # �,�1
                name = st.text_input("
M", value=session.name)
                description = st.text_area("�", value=session.description)
                purpose = st.text_input("�", value=getattr(session, 'purpose', session.metadata.get('purpose', '')))
                
                # �ƴ�h�����
                categories = ["analysis", "training", "race", "simulation", "other"]
                category_display = {
                    "analysis": "�",
                    "training": "�����",
                    "race": "���", 
                    "simulation": "��������",
                    "other": "]n�"
                }
                
                current_category = getattr(session, 'category', 'analysis')
                category = st.selectbox(
                    "�ƴ�",
                    options=categories,
                    format_func=lambda x: category_display.get(x, x),
                    index=categories.index(current_category) if current_category in categories else 0
                )
                
                statuses = ["active", "in_progress", "completed", "archived"]
                status_display = {
                    "active": "��ƣ�",
                    "in_progress": "2L-",
                    "completed": "��",
                    "archived": "�����"
                }
                
                current_status = getattr(session, 'status', 'active')
                status = st.selectbox(
                    "�����",
                    options=statuses,
                    format_func=lambda x: status_display.get(x, x),
                    index=statuses.index(current_status) if current_status in statuses else 0
                )
            
            with col2:
                # Mn�1
                location = st.text_input("Mn�1", 
                                         value=getattr(session, 'location', '') or session.metadata.get('location', ''))
                
                # G.
                boat_type = st.text_input("G.", value=session.metadata.get('boat_type', ''))
                
                # ����1
                crew_info = st.text_input("����1", value=session.metadata.get('crew_info', ''))
                
                # ́�
                importance_options = ["low", "normal", "high", "critical"]
                importance_display = {
                    "low": "N",
                    "normal": "n",
                    "high": "�",
                    "critical": "́"
                }
                
                current_importance = getattr(session, 'importance', 'normal')
                importance = st.selectbox(
                    "́�",
                    options=importance_options,
                    format_func=lambda x: importance_display.get(x, x),
                    index=importance_options.index(current_importance) if current_importance in importance_options else 1
                )
                
                # ���
                completion = st.slider(
                    "���", 
                    min_value=0, 
                    max_value=100, 
                    value=getattr(session, 'completion_percentage', 0),
                    step=5
                )
            
            # �����B
            # �(n�B�֗B�p	
            event_date_str = getattr(session, 'event_date', None) or session.metadata.get('event_date', None)
            event_date = None
            
            if event_date_str:
                try:
                    event_date = datetime.fromisoformat(event_date_str)
                except (ValueError, TypeError):
                    pass
            
            col_date1, col_date2 = st.columns(2)
            
            with col_date1:
                event_date_input = st.date_input(
                    "�����",
                    value=event_date.date() if event_date else None
                )
            
            with col_date2:
                event_time_input = st.time_input(
                    "����B;",
                    value=event_date.time() if event_date else datetime.now().time()
                )
            
            # ��ܿ�
            submit = st.form_submit_button("�������", use_container_width=True)
            
            if submit:
                # ����n��
                combined_event_date = None
                if event_date_input:
                    combined_event_date = datetime.combine(
                        event_date_input,
                        event_time_input
                    )
                
                # ����n��
                metadata_updates = {
                    "location": location,
                    "boat_type": boat_type,
                    "crew_info": crew_info,
                    "purpose": purpose,
                    "importance": importance,
                    "completion_percentage": completion
                }
                
                if combined_event_date:
                    metadata_updates["event_date"] = combined_event_date.isoformat()
                
                # �÷���1n��
                try:
                    # �,�1n��
                    success = True
                    
                    # 
Mh�n��
                    if session.name != name or session.description != description:
                        session.name = name
                        session.description = description
                        self.project_manager.save_session(session)
                    
                    # �ƴ�h�����n��
                    if hasattr(session, 'category') and session.category != category:
                        self.session_manager.update_session_category(session.session_id, category)
                    
                    if hasattr(session, 'status') and session.status != status:
                        self.session_manager.update_session_status(session.session_id, status)
                    
                    # ����n��
                    if self.session_manager.update_session_metadata(session.session_id, metadata_updates):
                        st.success("�÷���1���W~W_")
                        st.rerun()
                    else:
                        st.error("����n��k1WW~W_")
                
                except Exception as e:
                    st.error(f"�����: {str(e)}")
    
    def _render_metadata_view(self, session: SessionModel) -> None:
        """
        ����h:
        
        Parameters
        ----------
        session : SessionModel
            �÷��ָ���
        """
        # �,�1h�5�1nh:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**
M:** {session.name}")
            st.markdown(f"**�:** {session.description}" if session.description else "**�:** *jW*")
            st.markdown(f"**�:** {getattr(session, 'purpose', session.metadata.get('purpose', ''))}" 
                       if getattr(session, 'purpose', session.metadata.get('purpose', '')) else "**�:** **-�*")
            
            # �ƴ�h�����
            category = getattr(session, 'category', 'analysis')
            category_display = {
                "analysis": "�",
                "training": "�����",
                "race": "���",
                "simulation": "��������",
                "other": "]n�"
            }
            st.markdown(f"**�ƴ�:** {category_display.get(category, category)}")
            
            status = getattr(session, 'status', 'active')
            status_display = {
                "active": "��ƣ�",
                "in_progress": "2L-",
                "completed": "��",
                "archived": "�����"
            }
            st.markdown(f"**�����:** {status_display.get(status, status)}")
            
            # ́�
            importance = getattr(session, 'importance', 'normal')
            importance_display = {
                "low": "N",
                "normal": "n",
                "high": "�",
                "critical": "́"
            }
            st.markdown(f"**́�:** {importance_display.get(importance, importance)}")
            
            # ���
            completion = getattr(session, 'completion_percentage', 0)
            st.markdown(f"**���:** {completion}%")
            
            # B��
            st.markdown(f"**B��:** {format_datetime(session.updated_at)}")
        
        with col2:
            # �����Bnh:
            event_date = None
            if hasattr(session, 'event_date') and session.event_date:
                event_date = format_datetime(session.event_date)
            elif 'event_date' in session.metadata and session.metadata['event_date']:
                event_date = format_datetime(session.metadata['event_date'])
            
            if event_date:
                st.markdown(f"**�����B:** {event_date}")
            else:
                st.markdown("**�����B:** **-�*")
            
            # Mn�1nh:
            location = ""
            if hasattr(session, 'location') and session.location:
                location = session.location
            elif 'location' in session.metadata and session.metadata['location']:
                location = session.metadata['location']
            
            if location:
                st.markdown(f"**Mn�1:** {location}")
            else:
                st.markdown("**Mn�1:** **-�*")
            
            # G.
            boat_type = session.metadata.get('boat_type', '')
            if boat_type:
                st.markdown(f"**G.:** {boat_type}")
            else:
                st.markdown("**G.:** **-�*")
            
            # ����1
            crew_info = session.metadata.get('crew_info', '')
            if crew_info:
                st.markdown(f"**����1:** {crew_info}")
            else:
                st.markdown("**����1:** **-�*")
            
            # �÷��ID
            st.markdown(f"**�÷��ID:** `{session.session_id}`")
            st.markdown(f"**\�:** {format_datetime(session.created_at)}")
            
            # ���ա���1B�p	
            if hasattr(session, 'source_file') and session.source_file:
                st.markdown(f"**���ա��:** {session.source_file}")
            if hasattr(session, 'source_type') and session.source_type:
                st.markdown(f"**������:** {session.source_type}")
        
        # ]n�n����h:
        other_metadata = {}
        for key, value in session.metadata.items():
            if key not in ["created_by", "related_sessions", "event_date", "location", 
                          "boat_type", "crew_info", "purpose", "importance", 
                          "completion_percentage"] and value:
                other_metadata[key] = value
        
        if other_metadata:
            st.markdown("### ]n�n����")
            for key, value in other_metadata.items():
                st.markdown(f"**{key}:** {value}")
    
    def _render_results_tab(self, session: SessionModel) -> None:
        """
        P���n�����
        
        Parameters
        ----------
        session : SessionModel
            �÷��ָ���
        """
        self.render_results_section(session.session_id)
    
    def _render_related_tab(self, session: SessionModel) -> None:
        """
        �#�÷���n�����
        
        Parameters
        ----------
        session : SessionModel
            �÷��ָ���
        """
        self.render_related_sessions(session.session_id)
    
    def _get_active_tab_name(self) -> str:
        """
        ��ƣֿ�n
M�֗
        
        Returns
        -------
        str
            ��nh:
        """
        tab_mapping = {
            "metadata": "����",
            "results": "P�",
            "related": "�#�÷��"
        }
        return tab_mapping.get(st.session_state.get(f"{self.key}_active_tab", "metadata"), "����")


class SessionDetailView:
    """
    �÷��s0h:�������쬷�API��	
    
    x�U�_�÷��ns0�1�h:W
    ��Jd�����ȡjin_��ЛW~Y
    
    Parameters
    ----------
    project_manager : ProjectManager
        �����ȡ��n���
    session_manager : SessionManager
        �÷����n���
    on_edit : Callable[[str], None], optional
        ��ܿ�Bn����ï�p, by default None
    on_delete : Callable[[str], None], optional
        Jdܿ�Bn����ï�p, by default None
    on_close : Callable[[], None], optional
        �X�ܿ�Bn����ï�p, by default None
    """
    
    def __init__(
        self,
        project_manager: ProjectManager,
        session_manager: SessionManager,
        on_edit: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        """
        
        
        Parameters
        ----------
        project_manager : ProjectManager
            �����ȡ��n���
        session_manager : SessionManager
            �÷����n���
        on_edit : Optional[Callable[[str], None]], optional
            ��ܿ�Bn����ï�p, by default None
        on_delete : Optional[Callable[[str], None]], optional
            Jdܿ�Bn����ï�p, by default None
        on_close : Optional[Callable[[], None]], optional
            �X�ܿ�Bn����ï�p, by default None
        """
        self.component = SessionDetailComponent(
            key="legacy_session_detail",
            project_manager=project_manager,
            session_manager=session_manager,
            on_edit=on_edit,
            on_delete=on_delete,
            on_close=on_close
        )
    
    def render(self, session_id: str) -> None:
        """
        �������n�����
        
        Parameters
        ----------
        session_id : str
            h:Y��÷��nID
        """
        self.component.render(session_id)


def edit_session_metadata(project_manager: ProjectManager,
                          session_manager: SessionManager,
                          session_id: str) -> bool:
    """
    �÷������n��թ��쬷�API��	
    
    Parameters
    ----------
    project_manager : ProjectManager
        �����ȡ��n���
    session_manager : SessionManager
        �÷����n���
    session_id : str
        ��Y��÷��nID
        
    Returns
    -------
    bool
        ��k�W_4True
    """
    session = project_manager.get_session(session_id)
    if not session:
        st.error(f"�÷��L�dK�~[�: {session_id}")
        return False
    
    st.subheader(f"�÷�� '{session.name}' n��")
    
    # �,�1n��
    with st.form("edit_session_form"):
        name = st.text_input("�÷��
", value=session.name)
        description = st.text_area("�", value=session.description)
        
        # �(n���֗
        current_tags = session.tags if session.tags else []
        
        # )(��j��n֗�Xn��h�(n������	
        available_tags = session_manager.get_available_tags()
        all_tags = list(set(available_tags + current_tags))
        
        # ��nx�
        selected_tags = st.multiselect(
            "��",
            options=all_tags,
            default=current_tags
        )
        
        # �WD��n��
        new_tag = st.text_input("�WD����� (���:�gp���)")
        
        # �ƴ�x�
        categories = ["general", "race", "training", "analysis", "other"]
        current_category = getattr(session, 'category', 'general')
        if current_category and current_category not in categories:
            categories.append(current_category)
        
        category = st.selectbox(
            "�ƴ�",
            options=categories,
            index=categories.index(current_category) if current_category in categories else 0
        )
        
        # �����x�
        statuses = ["active", "in_progress", "completed", "archived"]
        current_status = getattr(session, 'status', 'active')
        if current_status and current_status not in statuses:
            statuses.append(current_status)
        
        status = st.selectbox(
            "�����",
            options=statuses,
            index=statuses.index(current_status) if current_status in statuses else 0
        )
        
        # U�
        current_rating = getattr(session, 'rating', 0)
        rating = st.slider(
            "U�",
            min_value=0,
            max_value=5,
            value=current_rating,
            step=1
        )
        
        # ����n��
        st.subheader("����")
        
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.text_input("Mn�1", value=session.metadata.get("location", ""))
            boat_type = st.text_input("G.", value=session.metadata.get("boat_type", ""))
        
        with col2:
            event_date = st.date_input(
                "�����",
                value=None  # ,eosession.metadata.get("event_date")�	�Wf(
            )
            crew_info = st.text_input("����1", value=session.metadata.get("crew_info", ""))
        
        # ]n�n����nh:h��
        other_metadata = {}
        for key, value in session.metadata.items():
            if key not in ["location", "boat_type", "event_date", "crew_info", "created_by", "related_sessions"]:
                other_metadata[key] = value
        
        if other_metadata:
            st.subheader("]n�n����")
            for key, value in other_metadata.items():
                other_metadata[key] = st.text_input(key, value, key=f"metadata_{key}")
        
        submitted = st.form_submit_button("��")
        
        if submitted:
            # �,�1n��
            session.name = name
            session.description = description
            
            # �5^'n��
            if hasattr(session, 'category'):
                session.category = category
            else:
                session.metadata['category'] = category
            
            if hasattr(session, 'status'):
                session.status = status
            else:
                session.metadata['status'] = status
            
            if hasattr(session, 'update_rating'):
                session.update_rating(rating)
            elif hasattr(session, 'rating'):
                session.rating = rating
            else:
                session.metadata['rating'] = rating
            
            # ��n�
            final_tags = selected_tags
            if new_tag:
                # ���g:��_pn����
                additional_tags = [tag.strip() for tag in new_tag.split(",") if tag.strip()]
                final_tags.extend(additional_tags)
                # ��Jd
                final_tags = list(set(final_tags))
            
            session.tags = final_tags
            
            # ����n��
            updated_metadata = {}
            
            # �,����
            updated_metadata["location"] = location
            updated_metadata["boat_type"] = boat_type
            updated_metadata["crew_info"] = crew_info
            
            # �����n�
            if event_date:
                updated_metadata["event_date"] = event_date.isoformat()
            
            # ]n�n����n�
            for key, value in other_metadata.items():
                updated_metadata[key] = value
            
            # ��������
            session_manager.update_session_metadata(session_id, updated_metadata)
            
            # �÷���X
            project_manager.save_session(session)
            
            st.success("�÷���1���W~W_")
            return True
    
    return False


def create_session_annotation(session_manager: SessionManager, session_id: str) -> bool:
    """
    �÷����n\թ��쬷�API��	
    
    Parameters
    ----------
    session_manager : SessionManager
        �÷����n���
    session_id : str
        �Ȓ��Y��÷��nID
        
    Returns
    -------
    bool
        \k�W_4True
    """
    st.subheader("�WD�Ȓ��")
    
    with st.form("new_annotation_form"):
        title = st.text_input("����", key="annotation_title")
        content = st.text_area("��", key="annotation_content")
        
        col1, col2 = st.columns(2)
        
        with col1:
            latitude = st.number_input("� (�׷��)", min_value=-90.0, max_value=90.0, value=None, key="annotation_lat")
        
        with col2:
            longitude = st.number_input("L� (�׷��)", min_value=-180.0, max_value=180.0, value=None, key="annotation_lon")
        
        annotation_type = st.selectbox(
            "���",
            options=["text", "waypoint", "mark", "tack", "gybe", "strategy", "other"],
            key="annotation_type"
        )
        
        submitted = st.form_submit_button("��")
        
        if submitted:
            if not title:
                st.error("����o�gY")
                return False
            
            if not content:
                st.error("��o�gY")
                return False
            
            # Mn�1n�
            position = None
            if latitude is not None and longitude is not None:
                position = (latitude, longitude)
            
            # ��n\
            try:
                annotation = session_manager.create_annotation(
                    session_id=session_id,
                    title=title,
                    content=content,
                    position=position,
                    annotation_type=annotation_type
                )
                
                st.success("�Ȓ��W~W_")
                return True
            
            except Exception as e:
                st.error(f"��n��k1WW~W_: {str(e)}")
                return False
    
    return False