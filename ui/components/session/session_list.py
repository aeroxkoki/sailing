# -*- coding: utf-8 -*-
"""
ui.components.session.session_list

�÷����h:nUI�������
"""

import streamlit as st
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime

from sailing_data_processor.project.project_manager import ProjectManager
from sailing_data_processor.project.session_manager import SessionManager
from sailing_data_processor.project.session_model import SessionModel

def format_datetime(iso_datetime: str) -> str:
    """ISObn�B���YDbk	�"""
    try:
        dt = datetime.fromisoformat(iso_datetime)
        return dt.strftime("%Y/%m/%d %H:%M")
    except (ValueError, TypeError):
        return iso_datetime


class SessionListComponent:
    """
    �5U�_�÷���ȳ������
    
    Parameters
    ----------
    key : str, optional
        ������ȭ�, by default "session_list"
    session_manager : SessionManager, optional
        �÷����n���, by default None
    on_session_select : Callable[[str], None], optional
        �÷��x�Bn����ï�p, by default None
    on_session_action : Callable[[str, str], None], optional
        �÷��k�Y������LBn����ï�p, by default None
    """
    
    def __init__(self, key: str = "session_list", 
                 session_manager: SessionManager = None,
                 on_session_select: Callable[[str], None] = None,
                 on_session_action: Callable[[str, str], None] = None):
        """
        �˷�餶
        
        Parameters
        ----------
        key : str, optional
            ������ȭ�, by default "session_list"
        session_manager : SessionManager, optional
            �÷����n���, by default None
        on_session_select : Callable[[str], None], optional
            �÷��x�Bn����ï�p, by default None
        on_session_action : Callable[[str, str], None], optional
            �÷��k�Y������LBn����ï�p, by default None
        """
        self.key = key
        self.session_manager = session_manager
        self.on_session_select = on_session_select
        self.on_session_action = on_session_action
        
        # �÷��Kn
        if f"{key}_filter_tags" not in st.session_state:
            st.session_state[f"{key}_filter_tags"] = []
        if f"{key}_filter_category" not in st.session_state:
            st.session_state[f"{key}_filter_category"] = "all"
        if f"{key}_filter_status" not in st.session_state:
            st.session_state[f"{key}_filter_status"] = "all"
        if f"{key}_filter_rating" not in st.session_state:
            st.session_state[f"{key}_filter_rating"] = 0
        if f"{key}_selected_sessions" not in st.session_state:
            st.session_state[f"{key}_selected_sessions"] = []
        if f"{key}_view_type" not in st.session_state:
            st.session_state[f"{key}_view_type"] = "card" # "card" or "list"
        if f"{key}_sort_by" not in st.session_state:
            st.session_state[f"{key}_sort_by"] = "updated_at"
        if f"{key}_sort_order" not in st.session_state:
            st.session_state[f"{key}_sort_order"] = "desc"
    
    def render(self) -> None:
        """
        �5U�_�÷����h:
        """
        st.subheader("�÷��")
        
        # գ��������
        self._render_filters()
        
        # �÷����֗h���
        sessions = self._get_filtered_sessions()
        
        # ����\������
        self._render_batch_controls()
        
        # �÷����h:
        if not sessions:
            st.info("a�k�Y��÷��LB�~[�")
            return
        
        # h:��n��H
        view_col1, view_col2 = st.columns([3, 1])
        with view_col1:
            st.write(f"h {len(sessions)} �")
        
        with view_col2:
            view_type = st.selectbox(
                "h:��",
                options=["���h:", "��h:"],
                index=0 if st.session_state[f"{self.key}_view_type"] == "card" else 1,
                key=f"{self.key}_view_type_selector"
            )
            st.session_state[f"{self.key}_view_type"] = "card" if view_type == "���h:" else "list"
        
        # �÷��nh:
        if st.session_state[f"{self.key}_view_type"] == "card":
            self._render_session_cards(sessions)
        else:
            self._render_session_list(sessions)
    
    def _render_filters(self) -> None:
        """
        գ��������n�����
        """
        with st.expander("գ��", expanded=False):
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                # �ƴ�k��գ���
                categories = ["all", "analysis", "training", "race", "simulation", "other"]
                category_display = {
                    "all": "Yyf", 
                    "analysis": "�", 
                    "training": "�����", 
                    "race": "���", 
                    "simulation": "��������", 
                    "other": "]n�"
                }
                
                selected_category = st.selectbox(
                    "�ƴ�",
                    options=categories,
                    format_func=lambda x: category_display.get(x, x),
                    index=categories.index(st.session_state[f"{self.key}_filter_category"]),
                    key=f"{self.key}_category_filter"
                )
                st.session_state[f"{self.key}_filter_category"] = selected_category
                
                # �����k��գ���
                statuses = ["all", "active", "in_progress", "completed", "archived"]
                status_display = {
                    "all": "Yyf", 
                    "active": "��ƣ�", 
                    "in_progress": "2L-", 
                    "completed": "��", 
                    "archived": "�����"
                }
                
                selected_status = st.selectbox(
                    "�����",
                    options=statuses,
                    format_func=lambda x: status_display.get(x, x),
                    index=statuses.index(st.session_state[f"{self.key}_filter_status"]),
                    key=f"{self.key}_status_filter"
                )
                st.session_state[f"{self.key}_filter_status"] = selected_status
            
            with filter_col2:
                # U�k��գ���
                rating_options = [(0, "Yyf"), (1, "�
"), (2, "�
"), (3, "�
"), (4, "�
"), (5, "")]
                selected_rating_index = next((i for i, (val, _) in enumerate(rating_options) if val == st.session_state[f"{self.key}_filter_rating"]), 0)
                
                selected_rating = st.selectbox(
                    "U�",
                    options=range(len(rating_options)),
                    format_func=lambda i: rating_options[i][1],
                    index=selected_rating_index,
                    key=f"{self.key}_rating_filter"
                )
                st.session_state[f"{self.key}_filter_rating"] = rating_options[selected_rating][0]
                
                # ��k��գ���
                if self.session_manager:
                    available_tags = self.session_manager.get_available_tags()
                    selected_tags = st.multiselect(
                        "��",
                        options=available_tags,
                        default=st.session_state[f"{self.key}_filter_tags"],
                        key=f"{self.key}_tags_filter"
                    )
                    st.session_state[f"{self.key}_filter_tags"] = selected_tags
            
            # ���
            sort_col1, sort_col2 = st.columns(2)
            
            with sort_col1:
                sort_options = {
                    "updated_at": "���B",
                    "created_at": "\�B",
                    "name": "
M",
                    "rating": "U�"
                }
                
                sort_by = st.selectbox(
                    "&s",
                    options=list(sort_options.keys()),
                    format_func=lambda x: sort_options.get(x, x),
                    index=list(sort_options.keys()).index(st.session_state[f"{self.key}_sort_by"]),
                    key=f"{self.key}_sort_by_selector"
                )
                st.session_state[f"{self.key}_sort_by"] = sort_by
            
            with sort_col2:
                order_options = {
                    "asc": "",
                    "desc": "M"
                }
                
                sort_order = st.selectbox(
                    "�",
                    options=list(order_options.keys()),
                    format_func=lambda x: order_options.get(x, x),
                    index=list(order_options.keys()).index(st.session_state[f"{self.key}_sort_order"]),
                    key=f"{self.key}_sort_order_selector"
                )
                st.session_state[f"{self.key}_sort_order"] = sort_order
            
            # գ�����ܿ�
            if st.button("գ������", key=f"{self.key}_reset_filters"):
                st.session_state[f"{self.key}_filter_tags"] = []
                st.session_state[f"{self.key}_filter_category"] = "all"
                st.session_state[f"{self.key}_filter_status"] = "all"
                st.session_state[f"{self.key}_filter_rating"] = 0
                st.session_state[f"{self.key}_sort_by"] = "updated_at"
                st.session_state[f"{self.key}_sort_order"] = "desc"
                st.rerun()
    
    def _get_filtered_sessions(self) -> List[SessionModel]:
        """
        գ��a�k�eDf�÷��գ���
        
        Returns
        -------
        List[SessionModel]
            գ���U�_�÷��n��
        """
        if not self.session_manager:
            return []
        
        # Yyfn�÷��֗
        all_sessions = self.session_manager.get_all_sessions()
        filtered_sessions = []
        
        for session in all_sessions:
            # �ƴ�gգ���
            if st.session_state[f"{self.key}_filter_category"] != "all":
                if not hasattr(session, 'category') or session.category != st.session_state[f"{self.key}_filter_category"]:
                    continue
            
            # �����gգ���
            if st.session_state[f"{self.key}_filter_status"] != "all":
                if not hasattr(session, 'status') or session.status != st.session_state[f"{self.key}_filter_status"]:
                    continue
            
            # U�gգ���
            rating_filter = st.session_state[f"{self.key}_filter_rating"]
            if rating_filter > 0:
                session_rating = getattr(session, 'rating', 0)
                if session_rating < rating_filter:
                    continue
            
            # ��gգ���
            filter_tags = st.session_state[f"{self.key}_filter_tags"]
            if filter_tags:
                if not session.tags or not all(tag in session.tags for tag in filter_tags):
                    continue
            
            filtered_sessions.append(session)
        
        # �÷����
        sort_by = st.session_state[f"{self.key}_sort_by"]
        sort_order = st.session_state[f"{self.key}_sort_order"]
        
        if sort_by == "name":
            filtered_sessions.sort(key=lambda s: s.name.lower())
        elif sort_by == "rating":
            filtered_sessions.sort(key=lambda s: getattr(s, 'rating', 0))
        elif sort_by == "created_at":
            filtered_sessions.sort(key=lambda s: s.created_at if s.created_at else "")
        else:  # updated_at
            filtered_sessions.sort(key=lambda s: s.updated_at if s.updated_at else "")
        
        # Łk�Xf�Ȓ��
        if sort_order == "desc":
            filtered_sessions.reverse()
        
        return filtered_sessions
    
    def _render_batch_controls(self) -> None:
        """
        ����\������n�����
        """
        selected_sessions = st.session_state[f"{self.key}_selected_sessions"]
        selection_count = len(selected_sessions)
        
        if selection_count > 0:
            st.markdown(f"**{selection_count}** n�÷��x�-")
            
            # px�n4n�\
            batch_col1, batch_col2, batch_col3 = st.columns(3)
            
            with batch_col1:
                status_options = ["active", "in_progress", "completed", "archived"]
                status_display = {
                    "active": "��ƣ�", 
                    "in_progress": "2L-",
                    "completed": "��", 
                    "archived": "�����"
                }
                
                new_status = st.selectbox(
                    "�����	�",
                    options=status_options,
                    format_func=lambda x: status_display.get(x, x),
                    key=f"{self.key}_batch_status"
                )
                
                if st.button("�������", key=f"{self.key}_update_status_batch"):
                    self._batch_update_status(selected_sessions, new_status)
            
            with batch_col2:
                if self.session_manager:
                    available_tags = self.session_manager.get_available_tags()
                    new_tags = st.multiselect(
                        "����",
                        options=available_tags,
                        key=f"{self.key}_batch_tags"
                    )
                    
                    if st.button("����", key=f"{self.key}_add_tags_batch"):
                        self._batch_add_tags(selected_sessions, new_tags)
            
            with batch_col3:
                # ���x�n��
                if st.button("x��d", key=f"{self.key}_clear_selection", use_container_width=True):
                    st.session_state[f"{self.key}_selected_sessions"] = []
                    st.rerun()
    
    def _batch_update_status(self, session_ids: List[str], new_status: str) -> None:
        """
        p�÷��n���������
        
        Parameters
        ----------
        session_ids : List[str]
            ���an�÷��ID��
        new_status : str
            �WD�����
        """
        if not self.session_manager:
            st.error("�÷����L-�U�fD~[�")
            return
        
        success_count = 0
        for session_id in session_ids:
            if self.session_manager.update_session_status(session_id, new_status):
                success_count += 1
        
        if success_count > 0:
            st.success(f"{success_count}�n�÷��n��������W~W_")
            st.rerun()
        else:
            st.error("�����n��k1WW~W_")
    
    def _batch_add_tags(self, session_ids: List[str], new_tags: List[str]) -> None:
        """
        p�÷��k������
        
        Parameters
        ----------
        session_ids : List[str]
            ���an�÷��ID��
        new_tags : List[str]
            ��Y���n��
        """
        if not self.session_manager or not new_tags:
            st.error("�÷����L-�U�fDjDK��Lx�U�fD~[�")
            return
        
        success_count = 0
        for session_id in session_ids:
            session = self.session_manager.project_manager.get_session(session_id)
            if session:
                # �Xn��h�WD������
                current_tags = session.tags.copy() if session.tags else []
                merged_tags = list(set(current_tags + new_tags))  # ��Jd
                
                if self.session_manager.update_session_tags(session_id, merged_tags):
                    success_count += 1
        
        if success_count > 0:
            st.success(f"{success_count}�n�÷��k�����W~W_")
            st.rerun()
        else:
            st.error("��n��k1WW~W_")
    
    def _render_session_cards(self, sessions: List[SessionModel]) -> None:
        """
        �÷����bgh:
        
        Parameters
        ----------
        sessions : List[SessionModel]
            h:Y��÷��n��
        """
        # 3n����줢��
        session_rows = [sessions[i:i+3] for i in range(0, len(sessions), 3)]
        
        for row in session_rows:
            cols = st.columns(3)
            
            for i, session in enumerate(row):
                with cols[i]:
                    self._render_session_card(session)
    
    def _render_session_list(self, sessions: List[SessionModel]) -> None:
        """
        �÷����bgh:
        
        Parameters
        ----------
        sessions : List[SessionModel]
            h:Y��÷��n��
        """
        for session in sessions:
            self._render_session_list_item(session)
    
    def _render_session_card(self, session: SessionModel) -> None:
        """
        �÷����n�����
        
        Parameters
        ----------
        session : SessionModel
            h:Y��÷��
        """
        # �÷��Lx���k+~�fD�K���ï
        is_selected = session.session_id in st.session_state[f"{self.key}_selected_sessions"]
        
        # ���n����
        card_border = True
        with st.container(border=card_border):
            # ��ï�ï�h
M
            col1, col2 = st.columns([0.1, 0.9])
            
            with col1:
                selected = st.checkbox(
                    "",
                    value=is_selected,
                    key=f"{self.key}_select_{session.session_id}"
                )
                
                # �÷��x��Kn��
                if selected and not is_selected:
                    st.session_state[f"{self.key}_selected_sessions"].append(session.session_id)
                elif not selected and is_selected:
                    st.session_state[f"{self.key}_selected_sessions"].remove(session.session_id)
            
            with col2:
                # �÷��
��ïgx���	
                if st.button(
                    session.name,
                    key=f"{self.key}_name_{session.session_id}",
                    use_container_width=True
                ):
                    if self.on_session_select:
                        self.on_session_select(session.session_id)
            
            # �÷���1
            # �
            if session.description:
                description = session.description
                if len(description) > 100:
                    description = description[:97] + "..."
                st.markdown(f"*{description}*")
            
            # ����h�B
            meta_col1, meta_col2 = st.columns(2)
            
            with meta_col1:
                # �����hU��h:
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
                
                st.markdown(f"�����: :{status_color}[{status_text}]")
                
                # �ƴ�
                category = getattr(session, 'category', 'analysis')
                category_display = {
                    "analysis": "�",
                    "training": "�����",
                    "race": "���",
                    "simulation": "��������",
                    "other": "]n�"
                }
                category_text = category_display.get(category, category)
                st.markdown(f"�ƴ�: {category_text}")
            
            with meta_col2:
                # U�nh:
                rating = getattr(session, 'rating', 0)
                stars = "" * rating + "" * (5 - rating)
                st.markdown(f"U�: {stars}")
                
                # ���B
                st.markdown(f"��: {format_datetime(session.updated_at)}")
            
            # ��h:
            if session.tags and len(session.tags) > 0:
                tag_html = ""
                for tag in session.tags:
                    tag_html += f'<span style="background-color: #e1e1e1; padding: 2px 8px; border-radius: 10px; margin-right: 5px; font-size: 0.8em;">{tag}</span>'
                st.markdown(f"<div>{tag_html}</div>", unsafe_allow_html=True)
            
            # �����ܿ�
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button("s0", key=f"{self.key}_detail_{session.session_id}", use_container_width=True):
                    if self.on_session_select:
                        self.on_session_select(session.session_id)
            
            with action_col2:
                if st.button("��", key=f"{self.key}_edit_{session.session_id}", use_container_width=True):
                    if self.on_session_action:
                        self.on_session_action(session.session_id, "edit")
            
            with action_col3:
                if st.button("Jd", key=f"{self.key}_delete_{session.session_id}", use_container_width=True):
                    if self.on_session_action:
                        self.on_session_action(session.session_id, "delete")
    
    def _render_session_list_item(self, session: SessionModel) -> None:
        """
        �÷���Ȣ���hWfh:
        
        Parameters
        ----------
        session : SessionModel
            h:Y��÷��
        """
        # �÷��Lx���k+~�fD�K���ï
        is_selected = session.session_id in st.session_state[f"{self.key}_selected_sessions"]
        
        # �Ȣ���n����
        with st.container(border=True):
            row_col1, row_col2, row_col3, row_col4 = st.columns([0.05, 0.45, 0.3, 0.2])
            
            with row_col1:
                selected = st.checkbox(
                    "",
                    value=is_selected,
                    key=f"{self.key}_list_select_{session.session_id}"
                )
                
                # �÷��x��Kn��
                if selected and not is_selected:
                    st.session_state[f"{self.key}_selected_sessions"].append(session.session_id)
                elif not selected and is_selected:
                    st.session_state[f"{self.key}_selected_sessions"].remove(session.session_id)
            
            with row_col2:
                if st.button(
                    session.name,
                    key=f"{self.key}_list_name_{session.session_id}",
                    use_container_width=True
                ):
                    if self.on_session_select:
                        self.on_session_select(session.session_id)
                
                # ��O	
                if session.description:
                    description = session.description
                    if len(description) > 50:
                        description = description[:47] + "..."
                    st.markdown(f"<small>{description}</small>", unsafe_allow_html=True)
            
            with row_col3:
                # �����hU�
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
                
                # �ƴ�
                category = getattr(session, 'category', 'analysis')
                category_display = {
                    "analysis": "�",
                    "training": "�����",
                    "race": "���",
                    "simulation": "��������",
                    "other": "]n�"
                }
                category_text = category_display.get(category, category)
                
                # U�
                rating = getattr(session, 'rating', 0)
                stars = "" * rating + "" * (5 - rating)
                
                st.markdown(f":{status_color}[{status_text}] | {category_text}")
                st.markdown(f"U�: {stars}")
                
                # ��n1-2n	
                if session.tags and len(session.tags) > 0:
                    display_tags = session.tags[:2]
                    tag_html = ""
                    for tag in display_tags:
                        tag_html += f'<span style="background-color: #e1e1e1; padding: 2px 5px; border-radius: 10px; margin-right: 5px; font-size: 0.7em;">{tag}</span>'
                    
                    if len(session.tags) > 2:
                        tag_html += f'<span style="font-size: 0.7em;">+{len(session.tags) - 2}</span>'
                    
                    st.markdown(f"<div>{tag_html}</div>", unsafe_allow_html=True)
            
            with row_col4:
                # ���B
                st.markdown(f"<small>��: {format_datetime(session.updated_at)}</small>", unsafe_allow_html=True)
                
                # �����ܿ�
                action_col1, action_col2 = st.columns(2)
                
                with action_col1:
                    if st.button("s0", key=f"{self.key}_list_detail_{session.session_id}", use_container_width=True):
                        if self.on_session_select:
                            self.on_session_select(session.session_id)
                
                with action_col2:
                    if st.button("��", key=f"{self.key}_list_edit_{session.session_id}", use_container_width=True):
                        if self.on_session_action:
                            self.on_session_action(session.session_id, "edit")


class SessionListView:
    """
    �÷����h:�������쬷�API��	
    
    Parameters
    ----------
    project_manager : ProjectManager
        �����ȡ��n���
    session_manager : SessionManager
        �÷����n���
    on_select : Callable[[str], None], optional
        �÷��x�Bn����ï�p, by default None
    on_edit : Callable[[str], None], optional
        ��ܿ�Bn����ï�p, by default None
    on_delete : Callable[[str], None], optional
        Jdܿ�Bn����ï�p, by default None
    """
    
    def __init__(
        self,
        project_manager: ProjectManager,
        session_manager: SessionManager,
        on_select: Optional[Callable[[str], None]] = None,
        on_edit: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
    ):
        """
        
        
        Parameters
        ----------
        project_manager : ProjectManager
            �����ȡ��n���
        session_manager : SessionManager
            �÷����n���
        on_select : Optional[Callable[[str], None]], optional
            �÷��x�Bn����ï�p, by default None
        on_edit : Optional[Callable[[str], None]], optional
            ��ܿ�Bn����ï�p, by default None
        on_delete : Optional[Callable[[str], None]], optional
            Jdܿ�Bn����ï�p, by default None
        """
        def on_action(session_id: str, action: str) -> None:
            if action == "edit" and on_edit:
                on_edit(session_id)
            elif action == "delete" and on_delete:
                on_delete(session_id)
        
        self.component = SessionListComponent(
            key="legacy_session_list",
            session_manager=session_manager,
            on_session_select=on_select,
            on_session_action=on_action
        )
    
    def render(self) -> None:
        """�������n�����"""
        self.component.render()
