"""
ui.components.session.session_detail

»Ã·çós0h:nUI³óÝüÍóÈ
"""

import streamlit as st
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime

from sailing_data_processor.project.project_manager import ProjectManager, Session
from sailing_data_processor.project.session_manager import SessionManager
from sailing_data_processor.project.session_model import SessionModel, SessionResult


def format_datetime(iso_datetime: str) -> str:
    """ISObnåB’­„YDbk	Û"""
    try:
        dt = datetime.fromisoformat(iso_datetime)
        return dt.strftime("%Y/%m/%d %H:%M")
    except (ValueError, TypeError):
        return iso_datetime


class SessionDetailComponent:
    """
    á5UŒ_»Ã·çós0³óÝüÍóÈ
    
    Parameters
    ----------
    key : str, optional
        ³óÝüÍóÈ­ü, by default "session_detail"
    session_manager : SessionManager, optional
        »Ã·çó¡¯é¹n¤ó¹¿ó¹, by default None
    project_manager : ProjectManager, optional
        ×í¸§¯È¡¯é¹n¤ó¹¿ó¹, by default None
    on_edit : Callable[[str], None], optional
        èÆÜ¿ó¼Bn³üëÐÃ¯¢p, by default None
    on_delete : Callable[[str], None], optional
        JdÜ¿ó¼Bn³üëÐÃ¯¢p, by default None
    on_close : Callable[[], None], optional
        ‰X‹Ü¿ó¼Bn³üëÐÃ¯¢p, by default None
    on_result_select : Callable[[str], None], optional
        PœxžBn³üëÐÃ¯¢p, by default None
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
        ¤Ë·ãé¤¶
        
        Parameters
        ----------
        key : str, optional
            ³óÝüÍóÈ­ü, by default "session_detail"
        session_manager : SessionManager, optional
            »Ã·çó¡¯é¹n¤ó¹¿ó¹, by default None
        project_manager : ProjectManager, optional
            ×í¸§¯È¡¯é¹n¤ó¹¿ó¹, by default None
        on_edit : Callable[[str], None], optional
            èÆÜ¿ó¼Bn³üëÐÃ¯¢p, by default None
        on_delete : Callable[[str], None], optional
            JdÜ¿ó¼Bn³üëÐÃ¯¢p, by default None
        on_close : Callable[[], None], optional
            ‰X‹Ü¿ó¼Bn³üëÐÃ¯¢p, by default None
        on_result_select : Callable[[str], None], optional
            PœxžBn³üëÐÃ¯¢p, by default None
        """
        self.key = key
        self.session_manager = session_manager
        self.project_manager = project_manager or (session_manager.project_manager if session_manager else None)
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_close = on_close
        self.on_result_select = on_result_select
        
        # »Ã·çó¶Kn
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
        »Ã·çóL¢#ØQ‰ŒfD‹×í¸§¯Ènê¹È’Ö—
        
        Parameters
        ----------
        session_id : str
            »Ã·çóID
            
        Returns
        -------
        List[Dict[str, Any]]
            ¢#×í¸§¯ÈÅ1nê¹È
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
        á¿Çü¿¨Ç£¿nìóÀêó°
        
        Parameters
        ----------
        session : Session
            »Ã·çóªÖ¸§¯È
        """
        with st.expander("»Ã·çóÅ1", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**M:** {session.name}")
                st.markdown(f"**¬:** {session.description}" if session.description else "**¬:** *jW*")
                st.markdown(f"**«Æ´ê:** {session.category}" if hasattr(session, 'category') and session.category else "**«Æ´ê:** **-š*")
                st.markdown(f"**¹Æü¿¹:** {session.status}" if hasattr(session, 'status') and session.status else "**¹Æü¿¹:** **-š*")
                
                # U¡nh:
                rating = getattr(session, 'rating', 0)
                stars = "" * rating + "" * (5 - rating)
                st.markdown(f"**U¡:** {stars} ({rating}/5)")
                
                # ¤ÙóÈåBnh:
                event_date = None
                if hasattr(session, 'event_date') and session.event_date:
                    event_date = format_datetime(session.event_date)
                elif 'event_date' in session.metadata and session.metadata['event_date']:
                    event_date = format_datetime(session.metadata['event_date'])
                
                if event_date:
                    st.markdown(f"**¤ÙóÈåB:** {event_date}")
                else:
                    st.markdown("**¤ÙóÈåB:** **-š*")
                
                # MnÅ1nh:
                location = None
                if hasattr(session, 'location') and session.location:
                    location = session.location
                elif 'location' in session.metadata and session.metadata['location']:
                    location = session.metadata['location']
                
                if location:
                    st.markdown(f"**MnÅ1:** {location}")
                else:
                    st.markdown("**MnÅ1:** **-š*")
                
                # »Ã·çóIDh\å
                st.markdown(f"**»Ã·çóID:** `{session.session_id}`")
                st.markdown(f"**\å:** {format_datetime(session.created_at)}")
                st.markdown(f"**ô°å:** {format_datetime(session.updated_at)}")
                
                if session.source_file:
                    st.markdown(f"**½ü¹Õ¡¤ë:** {session.source_file}")
                if session.source_type:
                    st.markdown(f"**½ü¹¿¤×:** {session.source_type}")
            
            with col2:
                # ¿°
                tags_str = ", ".join(session.tags) if session.tags else "jW"
                st.markdown(f"**¿°:** {tags_str}")
                
                # á¿Çü¿h:event_datehlocationo%h:Y‹_d	
                for key, value in session.metadata.items():
                    if key not in ["created_by", "related_sessions", "event_date", "location"] and value:
                        st.markdown(f"**{key}:** {value}")
    
    def render_tags_editor(self, session_id: str, current_tags: List[str]) -> None:
        """
        ¿°¨Ç£¿nìóÀêó°
        
        Parameters
        ----------
        session_id : str
            »Ã·çóID
        current_tags : List[str]
            þ(n¿°ê¹È
        """
        if not self.session_manager:
            return
        
        with st.expander("¿°¡", expanded=False):
            # )(ïýj¿°nÖ—
            all_tags = self.session_manager.get_available_tags()
            
            # ¿°xž
            selected_tags = st.multiselect(
                "¿°",
                options=all_tags,
                default=current_tags,
                key=f"{self.key}_edit_tags"
            )
            
            # °WD¿°ný 
            new_tag = st.text_input(
                "°WD¿°’ý «óÞ:Šgpšïý	",
                key=f"{self.key}_new_tag"
            )
            
            # ô°Ü¿ó
            if st.button("¿°’ô°", key=f"{self.key}_update_tags", use_container_width=True):
                final_tags = selected_tags.copy()
                
                # °WD¿°næ
                if new_tag:
                    additional_tags = [tag.strip() for tag in new_tag.split(",") if tag.strip()]
                    final_tags.extend(additional_tags)
                    # Í’Jd
                    final_tags = list(set(final_tags))
                
                # ¿°ô°
                if self.session_manager.update_session_tags(session_id, final_tags):
                    st.success("¿°’ô°W~W_")
                    st.rerun()
                else:
                    st.error("¿°nô°k1WW~W_")
    
    def render_rating_editor(self, session_id: str, current_rating: int) -> None:
        """
        U¡¨Ç£¿nìóÀêó°
        
        Parameters
        ----------
        session_id : str
            »Ã·çóID
        current_rating : int
            þ(nU¡$
        """
        if not self.session_manager:
            return
        
        with st.expander("U¡", expanded=False):
            # U¡nèÆ
            new_rating = st.slider(
                "»Ã·çóU¡",
                min_value=0,
                max_value=5,
                value=current_rating,
                step=1,
                key=f"{self.key}_edit_rating"
            )
            
            # ô°Ü¿ó
            if st.button("U¡’ô°", key=f"{self.key}_update_rating", use_container_width=True):
                if self.session_manager.update_session_rating(session_id, new_rating):
                    st.success("U¡’ô°W~W_")
                    st.rerun()
                else:
                    st.error("U¡nô°k1WW~W_")
    
    def render_related_sessions(self, session_id: str) -> None:
        """
        ¢#»Ã·çónìóÀêó°
        
        Parameters
        ----------
        session_id : str
            »Ã·çóID
        """
        if not self.session_manager:
            return
        
        # ¢#»Ã·çónÖ—
        parent_sessions = self.session_manager.get_related_sessions(session_id, "parent")
        child_sessions = self.session_manager.get_related_sessions(session_id, "child")
        related_sessions = self.session_manager.get_related_sessions(session_id, "related")
        
        # ¢#»Ã·çón	!Á§Ã¯
        has_related = bool(parent_sessions or child_sessions or related_sessions)
        
        # ¢#»Ã·çóLjD4
        if not has_related:
            st.info("Sn»Ã·çóko~`¢#»Ã·çóLBŠ~[“")
        
        # ª»Ã·çónh:
        if parent_sessions:
            st.markdown("#### ª»Ã·çó")
            for session in parent_sessions:
                self._render_related_session_card(session, session_id, "parent")
        
        # P»Ã·çónh:
        if child_sessions:
            st.markdown("#### P»Ã·çó")
            for session in child_sessions:
                self._render_related_session_card(session, session_id, "child")
        
        # ¢#»Ã·çónh:
        if related_sessions:
            st.markdown("#### ]nÖn¢#»Ã·çó")
            for session in related_sessions:
                self._render_related_session_card(session, session_id, "related")
        
        # ¢#»Ã·çóý Ü¿ó
        if st.button("¢#»Ã·çó’ý ", key=f"{self.key}_add_relation_btn"):
            st.session_state[f"{self.key}_add_relation"] = True
        
        # ¢#»Ã·çóý Õ©üà
        if st.session_state[f"{self.key}_add_relation"]:
            st.markdown("#### ¢#»Ã·çóný ")
            
            # ¢#¿¤×xž
            relation_type = st.selectbox(
                "¢#¿¤×",
                options=["parent", "child", "related"],
                format_func=lambda x: {"parent": "ª»Ã·çó", "child": "P»Ã·çó", "related": "]nÖn¢#"}.get(x, x),
                key=f"{self.key}_relation_type"
            )
            
            # ¢#ØQ‹»Ã·çónxž
            all_sessions = self.session_manager.get_all_sessions()
            # êê«’d
            all_sessions = [s for s in all_sessions if s.session_id != session_id]
            
            if not all_sessions:
                st.warning("¢#ØQ‹»Ã·çóLBŠ~[“")
            else:
                related_session_id = st.selectbox(
                    "¢#ØQ‹»Ã·çó",
                    options=[s.session_id for s in all_sessions],
                    format_func=lambda x: next((s.name for s in all_sessions if s.session_id == x), x),
                    key=f"{self.key}_related_session_id"
                )
                
                # ý Ü¿ó
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("ý ", key=f"{self.key}_add_relation_submit", use_container_width=True):
                        if self.session_manager.add_related_session(session_id, related_session_id, relation_type):
                            st.success("¢#»Ã·çó’ý W~W_")
                            st.session_state[f"{self.key}_add_relation"] = False
                            st.rerun()
                        else:
                            st.error("¢#»Ã·çóný k1WW~W_")
                
                with col2:
                    if st.button("­ãó»ë", key=f"{self.key}_add_relation_cancel", use_container_width=True):
                        st.session_state[f"{self.key}_add_relation"] = False
                        st.rerun()
    
    def _render_related_session_card(self, session: Session, current_session_id: str, relation_type: str) -> None:
        """
        ¢#»Ã·çó«üÉnìóÀêó°
        
        Parameters
        ----------
        session : Session
            »Ã·çóªÖ¸§¯È
        current_session_id : str
            þ(n»Ã·çóID
        relation_type : str
            ¢#¿¤×
        """
        # «üÉ¹¿¤ën³óÆÊ
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{session.name}**")
                if session.description:
                    st.markdown(f"{session.description[:50]}..." if len(session.description) > 50 else session.description)
                
                # ¿°h«Æ´ênh:
                tags_str = ", ".join(session.tags) if session.tags else "jW"
                st.markdown(f"¿°: {tags_str}")
                
                if hasattr(session, 'category') and session.category:
                    st.markdown(f"«Æ´ê: {session.category}")
            
            with col2:
                # h:Ü¿ó
                if st.button("h:", key=f"{self.key}_view_related_{session.session_id}", use_container_width=True):
                    # »Ã·çó¶KkxžUŒ_»Ã·çóID’»ÃÈ
                    st.session_state.selected_session_id = session.session_id
                    st.rerun()
                
                # JdÜ¿ó
                if st.button("¢#Jd", key=f"{self.key}_remove_related_{session.session_id}", use_container_width=True):
                    if self.session_manager.remove_related_session(current_session_id, session.session_id, relation_type):
                        st.success("¢#’JdW~W_")
                        st.rerun()
                    else:
                        st.error("¢#nJdk1WW~W_")
    
    def render_results_section(self, session_id: str) -> None:
        """
        Pœ»¯·çónìóÀêó°
        
        Parameters
        ----------
        session_id : str
            »Ã·çóID
        """
        if not self.session_manager:
            return
        
        # »Ã·çónPœ’Ö—
        results = self.session_manager.get_session_results(session_id)
        
        if not results:
            st.info("Sn»Ã·çóko~`PœLBŠ~[“")
            return
        
        # Pœ¿¤×g°ëü×
        result_types = {}
        for result in results:
            if result.result_type not in result_types:
                result_types[result.result_type] = []
            result_types[result.result_type].append(result)
        
        # Pœ¿¤×Thkh:
        for result_type, type_results in result_types.items():
            st.markdown(f"#### {self._format_result_type(result_type)}")
            
            for result in type_results:
                self._render_result_card(result)
    
    def _format_result_type(self, result_type: str) -> str:
        """
        Pœ¿¤×nh:’Ö—
        
        Parameters
        ----------
        result_type : str
            Pœ¿¤×
            
        Returns
        -------
        str
            h:(nPœ¿¤×
        """
        # Pœ¿¤×nh:ÞÃÔó°
        type_names = {
            "wind_estimation": "¨¨¨š",
            "strategy_points": "&eÝ¤óÈ",
            "performance": "ÑÕ©üÞó¹",
            "data_cleaning": "Çü¿¯êüËó°",
            "general": " ,",
            "simulation": "·ßåìü·çó",
            "optimization": " i"
        }
        
        return type_names.get(result_type, result_type)
    
    def _render_result_card(self, result: SessionResult) -> None:
        """
        Pœ«üÉnìóÀêó°
        
        Parameters
        ----------
        result : SessionResult
            PœªÖ¸§¯È
        """
        # «üÉ¹¿¤ën³óÆÊ
        with st.container(border=True):
            # ØÃÀüè
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                # Pœ~_o¬
                result_name = result.metadata.get("name", f"Pœ v{result.version}")
                st.markdown(f"**{result_name}**")
                
                # \åB
                st.markdown(f"\åB: {format_datetime(result.created_at)}")
            
            with col2:
                # ý ná¿Çü¿h:
                if "description" in result.metadata:
                    st.markdown(f"¬: {result.metadata['description']}")
                
                # ¿°LBŒph:
                if "tags" in result.metadata and result.metadata["tags"]:
                    tags_str = ", ".join(result.metadata["tags"])
                    st.markdown(f"¿°: {tags_str}")
            
            with col3:
                # Ðü¸çóh:
                st.markdown(f"Ðü¸çó: {result.version}")
                
                # þ(nÐü¸çóKiFK
                if result.is_current:
                    st.markdown("**[ °]**")
                
                # ÖnÐü¸çóh:Ü¿ó
                if st.button("s0h:", key=f"{self.key}_view_result_{result.result_id}", use_container_width=True):
                    if self.on_result_select:
                        self.on_result_select(result.result_id)
                
                # Ðü¸çóeth:Ü¿ó
                if st.button("Ðü¸çóet", key=f"{self.key}_versions_{result.result_id}", use_container_width=True):
                    # È°ë¶K’Íâ
                    current = st.session_state[f"{self.key}_show_versions"].get(result.result_id, False)
                    st.session_state[f"{self.key}_show_versions"][result.result_id] = not current
            
            # Ðü¸çóeth:ß
            if st.session_state[f"{self.key}_show_versions"].get(result.result_id, False):
                # PœnÐü¸çóê¹È’Ö—
                versions = self.session_manager.get_result_versions(result.session_id, result.result_id)
                
                if versions:
                    st.markdown("#### Ðü¸çóet")
                    
                    for version in versions:
                        with st.container(border=True):
                            vcol1, vcol2 = st.columns([3, 1])
                            
                            with vcol1:
                                st.markdown(f"**Ðü¸çó {version.version}**")
                                st.markdown(f"\åB: {format_datetime(version.created_at)}")
                                
                                # á¿Çü¿nh:
                                if "description" in version.metadata:
                                    st.markdown(f"¬: {version.metadata['description']}")
                            
                            with vcol2:
                                if version.is_current:
                                    st.markdown("**[þ(nH]**")
                                else:
                                    # SnÐü¸çó’þ(nÐü¸çóhWf-šY‹Ü¿ó
                                    if st.button("SnH’(", key=f"{self.key}_use_version_{result.result_id}_{version.version}", use_container_width=True):
                                        # ÖnÐü¸çó’Yyf^¢¯Æ£Ök-š
                                        for v in versions:
                                            v.mark_as_current(False)
                                        
                                        # SnÐü¸çó’¢¯Æ£Ök-š
                                        version.mark_as_current(True)
                                        
                                        # ô°
                                        st.success(f"Ðü¸çó {version.version} ’þ(nHk-šW~W_")
                                        st.rerun()
    
    def render_actions(self, session_id: str) -> None:
        """
        ¢¯·çóÜ¿ónìóÀêó°
        
        Parameters
        ----------
        session_id : str
            »Ã·çóID
        """
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("èÆ", key=f"{self.key}_edit_btn", use_container_width=True):
                if self.on_edit:
                    self.on_edit(session_id)
        
        with col2:
            if st.button("Jd", key=f"{self.key}_delete_btn", use_container_width=True):
                # JdºÀ¤¢í°
                st.session_state[f"{self.key}_confirm_delete"] = True
        
        with col3:
            if st.button("‰X‹", key=f"{self.key}_close_btn", use_container_width=True):
                if self.on_close:
                    self.on_close()
        
        # JdºÀ¤¢í°
        if st.session_state[f"{self.key}_confirm_delete"]:
            st.warning("Sn»Ã·çó’JdW~YKSnÍ\oCk;[~[“")
            
            conf_col1, conf_col2 = st.columns(2)
            
            with conf_col1:
                if st.button("Jd’ºš", key=f"{self.key}_confirm_delete_yes", use_container_width=True):
                    if self.on_delete:
                        self.on_delete(session_id)
                    st.session_state[f"{self.key}_confirm_delete"] = False
            
            with conf_col2:
                if st.button("­ãó»ë", key=f"{self.key}_confirm_delete_no", use_container_width=True):
                    st.session_state[f"{self.key}_confirm_delete"] = False
                    st.rerun()
    
    def render(self, session_id: str) -> None:
        """
        ³óÝüÍóÈnìóÀêó°
        
        Parameters
        ----------
        session_id : str
            h:Y‹»Ã·çónID
        """
        if not self.project_manager:
            st.error("×í¸§¯È¡¯é¹L-šUŒfD~[“")
            return
        
        # »Ã·çónÖ—
        session = self.project_manager.get_session(session_id)
        if not session:
            st.error(f"»Ã·çóL‹dKŠ~[“: {session_id}")
            return
        
        # »Ã·çóØÃÀü
        self._render_header(session)
        
        # ¢¯·çóÜ¿ó
        self.render_actions(session_id)
        
        # ¿Öh:
        tabs = ["á¿Çü¿", "Pœ", "¢#»Ã·çó"]
        active_tab = st.radio(
            "»¯·çó",
            options=tabs,
            index=tabs.index(self._get_active_tab_name()),
            horizontal=True,
            key=f"{self.key}_tab_select"
        )
        
        # ¢¯Æ£Ö¿Ön¶K’ô°
        if active_tab == "á¿Çü¿":
            st.session_state[f"{self.key}_active_tab"] = "metadata"
        elif active_tab == "Pœ":
            st.session_state[f"{self.key}_active_tab"] = "results"
        elif active_tab == "¢#»Ã·çó":
            st.session_state[f"{self.key}_active_tab"] = "related"
            
        # ¿Ön…¹’h:
        if st.session_state[f"{self.key}_active_tab"] == "metadata":
            self._render_metadata_tab(session)
        elif st.session_state[f"{self.key}_active_tab"] == "results":
            self._render_results_tab(session)
        elif st.session_state[f"{self.key}_active_tab"] == "related":
            self._render_related_tab(session)
    
    def _render_header(self, session: SessionModel) -> None:
        """
        »Ã·çóØÃÀünìóÀêó°
        
        Parameters
        ----------
        session : SessionModel
            »Ã·çóªÖ¸§¯È
        """
        # ØÃÀü
        st.subheader(f"»Ã·çó: {session.name}")
        
        # »Ã·çóú,Å1nµÞêü
        header_col1, header_col2, header_col3 = st.columns([1, 1, 1])
        
        with header_col1:
            # ¹Æü¿¹h:
            status = getattr(session, 'status', 'active')
            
            status_colors = {
                "active": "blue",
                "in_progress": "orange",
                "completed": "green",
                "archived": "gray"
            }
            
            status_display = {
                "active": "¢¯Æ£Ö",
                "in_progress": "2L-",
                "completed": "Œ†",
                "archived": "¢ü«¤Ö"
            }
            
            status_color = status_colors.get(status, "blue")
            status_text = status_display.get(status, status)
            
            st.markdown(f"**¹Æü¿¹:** :{status_color}[{status_text}]")
        
        with header_col2:
            # «Æ´êh:
            category = getattr(session, 'category', 'analysis')
            category_display = {
                "analysis": "",
                "training": "ÈìüËó°",
                "race": "ìü¹",
                "simulation": "·ßåìü·çó",
                "other": "]nÖ"
            }
            category_text = category_display.get(category, category)
            
            st.markdown(f"**«Æ´ê:** {category_text}")
        
        with header_col3:
            # U¡h:
            rating = getattr(session, 'rating', 0)
            stars = "" * rating + "" * (5 - rating)
            
            st.markdown(f"**U¡:** {stars}")
        
        # ¿°h:Yyfn¿Ögh:	
        if session.tags and len(session.tags) > 0:
            tag_html = ""
            for tag in session.tags:
                tag_html += f'<span style="background-color: #e1e1e1; padding: 2px 8px; border-radius: 10px; margin-right: 5px; font-size: 0.8em;">{tag}</span>'
            st.markdown(f"<div>{tag_html}</div>", unsafe_allow_html=True)
    
    def _render_metadata_tab(self, session: SessionModel) -> None:
        """
        á¿Çü¿¿ÖnìóÀêó°
        
        Parameters
        ----------
        session : SessionModel
            »Ã·çóªÖ¸§¯È
        """
        # èÆâüÉnŠÿH
        edit_mode = st.toggle("èÆâüÉ", value=st.session_state.get(f"{self.key}_edit_mode", False))
        st.session_state[f"{self.key}_edit_mode"] = edit_mode
        
        if edit_mode:
            self._render_metadata_editor(session)
        else:
            self._render_metadata_view(session)
        
        # ¿°hU¡o8kh:/èÆïý
        st.markdown("---")
        
        # ¿°¡
        self.render_tags_editor(session.session_id, session.tags or [])
        
        # U¡èÆ
        rating = getattr(session, 'rating', 0)
        self.render_rating_editor(session.session_id, rating)
        
        # ¢#×í¸§¯È
        associated_projects = self.get_associated_projects(session.session_id)
        with st.expander("¢#×í¸§¯È", expanded=False):
            if not associated_projects:
                st.info("Sn»Ã·çóoin×í¸§¯Èk‚¢#ØQ‰ŒfD~[“")
            else:
                # ×í¸§¯È §nh:
                st.markdown("Sn»Ã·çóoån×í¸§¯Èk¢#ØQ‰ŒfD~Y:")
                
                for project in associated_projects:
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{project['name']}**")
                            st.markdown(f"{project['description'][:50]}..." if len(project['description']) > 50 else project['description'])
                        
                        with col2:
                            if st.button("ûÕ", key=f"goto_project_{project['id']}", use_container_width=True):
                                # ×í¸§¯È;bxnwû
                                st.session_state.selected_project_id = project['id']
                                st.rerun()
    
    def _render_metadata_editor(self, session: SessionModel) -> None:
        """
        á¿Çü¿¨Ç£¿nìóÀêó°
        
        Parameters
        ----------
        session : SessionModel
            »Ã·çóªÖ¸§¯È
        """
        with st.form(key=f"{self.key}_metadata_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # ú,Å1
                name = st.text_input("M", value=session.name)
                description = st.text_area("¬", value=session.description)
                purpose = st.text_input("î„", value=getattr(session, 'purpose', session.metadata.get('purpose', '')))
                
                # «Æ´êh¹Æü¿¹
                categories = ["analysis", "training", "race", "simulation", "other"]
                category_display = {
                    "analysis": "",
                    "training": "ÈìüËó°",
                    "race": "ìü¹", 
                    "simulation": "·ßåìü·çó",
                    "other": "]nÖ"
                }
                
                current_category = getattr(session, 'category', 'analysis')
                category = st.selectbox(
                    "«Æ´ê",
                    options=categories,
                    format_func=lambda x: category_display.get(x, x),
                    index=categories.index(current_category) if current_category in categories else 0
                )
                
                statuses = ["active", "in_progress", "completed", "archived"]
                status_display = {
                    "active": "¢¯Æ£Ö",
                    "in_progress": "2L-",
                    "completed": "Œ†",
                    "archived": "¢ü«¤Ö"
                }
                
                current_status = getattr(session, 'status', 'active')
                status = st.selectbox(
                    "¹Æü¿¹",
                    options=statuses,
                    format_func=lambda x: status_display.get(x, x),
                    index=statuses.index(current_status) if current_status in statuses else 0
                )
            
            with col2:
                # MnÅ1
                location = st.text_input("MnÅ1", 
                                         value=getattr(session, 'location', '') or session.metadata.get('location', ''))
                
                # G.
                boat_type = st.text_input("G.", value=session.metadata.get('boat_type', ''))
                
                # ¯ëüÅ1
                crew_info = st.text_input("¯ëüÅ1", value=session.metadata.get('crew_info', ''))
                
                # Í¦
                importance_options = ["low", "normal", "high", "critical"]
                importance_display = {
                    "low": "N",
                    "normal": "n",
                    "high": "Ø",
                    "critical": " Í"
                }
                
                current_importance = getattr(session, 'importance', 'normal')
                importance = st.selectbox(
                    "Í¦",
                    options=importance_options,
                    format_func=lambda x: importance_display.get(x, x),
                    index=importance_options.index(current_importance) if current_importance in importance_options else 1
                )
                
                # Œ†‡
                completion = st.slider(
                    "Œ†‡", 
                    min_value=0, 
                    max_value=100, 
                    value=getattr(session, 'completion_percentage', 0),
                    step=5
                )
            
            # ¤ÙóÈåB
            # þ(nåB’Ö—BŒp	
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
                    "¤ÙóÈå",
                    value=event_date.date() if event_date else None
                )
            
            with col_date2:
                event_time_input = st.time_input(
                    "¤ÙóÈB;",
                    value=event_date.time() if event_date else datetime.now().time()
                )
            
            # ô°Ü¿ó
            submit = st.form_submit_button("á¿Çü¿’ô°", use_container_width=True)
            
            if submit:
                # ô°…¹n–™
                combined_event_date = None
                if event_date_input:
                    combined_event_date = datetime.combine(
                        event_date_input,
                        event_time_input
                    )
                
                # á¿Çü¿nô°
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
                
                # »Ã·çóÅ1nô°
                try:
                    # ú,Å1nô°
                    success = True
                    
                    # Mh¬nô°
                    if session.name != name or session.description != description:
                        session.name = name
                        session.description = description
                        self.project_manager.save_session(session)
                    
                    # «Æ´êh¹Æü¿¹nô°
                    if hasattr(session, 'category') and session.category != category:
                        self.session_manager.update_session_category(session.session_id, category)
                    
                    if hasattr(session, 'status') and session.status != status:
                        self.session_manager.update_session_status(session.session_id, status)
                    
                    # á¿Çü¿nô°
                    if self.session_manager.update_session_metadata(session.session_id, metadata_updates):
                        st.success("»Ã·çóÅ1’ô°W~W_")
                        st.rerun()
                    else:
                        st.error("á¿Çü¿nô°k1WW~W_")
                
                except Exception as e:
                    st.error(f"ô°¨éü: {str(e)}")
    
    def _render_metadata_view(self, session: SessionModel) -> None:
        """
        á¿Çü¿h:
        
        Parameters
        ----------
        session : SessionModel
            »Ã·çóªÖ¸§¯È
        """
        # ú,Å1há5Å1nh:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**M:** {session.name}")
            st.markdown(f"**¬:** {session.description}" if session.description else "**¬:** *jW*")
            st.markdown(f"**î„:** {getattr(session, 'purpose', session.metadata.get('purpose', ''))}" 
                       if getattr(session, 'purpose', session.metadata.get('purpose', '')) else "**î„:** **-š*")
            
            # «Æ´êh¹Æü¿¹
            category = getattr(session, 'category', 'analysis')
            category_display = {
                "analysis": "",
                "training": "ÈìüËó°",
                "race": "ìü¹",
                "simulation": "·ßåìü·çó",
                "other": "]nÖ"
            }
            st.markdown(f"**«Æ´ê:** {category_display.get(category, category)}")
            
            status = getattr(session, 'status', 'active')
            status_display = {
                "active": "¢¯Æ£Ö",
                "in_progress": "2L-",
                "completed": "Œ†",
                "archived": "¢ü«¤Ö"
            }
            st.markdown(f"**¹Æü¿¹:** {status_display.get(status, status)}")
            
            # Í¦
            importance = getattr(session, 'importance', 'normal')
            importance_display = {
                "low": "N",
                "normal": "n",
                "high": "Ø",
                "critical": " Í"
            }
            st.markdown(f"**Í¦:** {importance_display.get(importance, importance)}")
            
            # Œ†‡
            completion = getattr(session, 'completion_percentage', 0)
            st.markdown(f"**Œ†‡:** {completion}%")
            
            #  Bô°
            st.markdown(f"** Bô°:** {format_datetime(session.updated_at)}")
        
        with col2:
            # ¤ÙóÈåBnh:
            event_date = None
            if hasattr(session, 'event_date') and session.event_date:
                event_date = format_datetime(session.event_date)
            elif 'event_date' in session.metadata and session.metadata['event_date']:
                event_date = format_datetime(session.metadata['event_date'])
            
            if event_date:
                st.markdown(f"**¤ÙóÈåB:** {event_date}")
            else:
                st.markdown("**¤ÙóÈåB:** **-š*")
            
            # MnÅ1nh:
            location = ""
            if hasattr(session, 'location') and session.location:
                location = session.location
            elif 'location' in session.metadata and session.metadata['location']:
                location = session.metadata['location']
            
            if location:
                st.markdown(f"**MnÅ1:** {location}")
            else:
                st.markdown("**MnÅ1:** **-š*")
            
            # G.
            boat_type = session.metadata.get('boat_type', '')
            if boat_type:
                st.markdown(f"**G.:** {boat_type}")
            else:
                st.markdown("**G.:** **-š*")
            
            # ¯ëüÅ1
            crew_info = session.metadata.get('crew_info', '')
            if crew_info:
                st.markdown(f"**¯ëüÅ1:** {crew_info}")
            else:
                st.markdown("**¯ëüÅ1:** **-š*")
            
            # »Ã·çóID
            st.markdown(f"**»Ã·çóID:** `{session.session_id}`")
            st.markdown(f"**\å:** {format_datetime(session.created_at)}")
            
            # ½ü¹Õ¡¤ëÅ1BŒp	
            if hasattr(session, 'source_file') and session.source_file:
                st.markdown(f"**½ü¹Õ¡¤ë:** {session.source_file}")
            if hasattr(session, 'source_type') and session.source_type:
                st.markdown(f"**½ü¹¿¤×:** {session.source_type}")
        
        # ]nÖná¿Çü¿h:
        other_metadata = {}
        for key, value in session.metadata.items():
            if key not in ["created_by", "related_sessions", "event_date", "location", 
                          "boat_type", "crew_info", "purpose", "importance", 
                          "completion_percentage"] and value:
                other_metadata[key] = value
        
        if other_metadata:
            st.markdown("### ]nÖná¿Çü¿")
            for key, value in other_metadata.items():
                st.markdown(f"**{key}:** {value}")
    
    def _render_results_tab(self, session: SessionModel) -> None:
        """
        Pœ¿ÖnìóÀêó°
        
        Parameters
        ----------
        session : SessionModel
            »Ã·çóªÖ¸§¯È
        """
        self.render_results_section(session.session_id)
    
    def _render_related_tab(self, session: SessionModel) -> None:
        """
        ¢#»Ã·çó¿ÖnìóÀêó°
        
        Parameters
        ----------
        session : SessionModel
            »Ã·çóªÖ¸§¯È
        """
        self.render_related_sessions(session.session_id)
    
    def _get_active_tab_name(self) -> str:
        """
        ¢¯Æ£Ö¿ÖnM’Ö—
        
        Returns
        -------
        str
            ¿Önh:
        """
        tab_mapping = {
            "metadata": "á¿Çü¿",
            "results": "Pœ",
            "related": "¢#»Ã·çó"
        }
        return tab_mapping.get(st.session_state.get(f"{self.key}_active_tab", "metadata"), "á¿Çü¿")


class SessionDetailView:
    """
    »Ã·çós0h:³óÝüÍóÈì¬·üAPI’Û	
    
    xžUŒ_»Ã·çóns0Å1’h:W
    èÆJd×í¸§¯È¡jin_ý’Ð›W~Y
    
    Parameters
    ----------
    project_manager : ProjectManager
        ×í¸§¯È¡¯é¹n¤ó¹¿ó¹
    session_manager : SessionManager
        »Ã·çó¡¯é¹n¤ó¹¿ó¹
    on_edit : Callable[[str], None], optional
        èÆÜ¿ó¼Bn³üëÐÃ¯¢p, by default None
    on_delete : Callable[[str], None], optional
        JdÜ¿ó¼Bn³üëÐÃ¯¢p, by default None
    on_close : Callable[[], None], optional
        ‰X‹Ü¿ó¼Bn³üëÐÃ¯¢p, by default None
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
            ×í¸§¯È¡¯é¹n¤ó¹¿ó¹
        session_manager : SessionManager
            »Ã·çó¡¯é¹n¤ó¹¿ó¹
        on_edit : Optional[Callable[[str], None]], optional
            èÆÜ¿ó¼Bn³üëÐÃ¯¢p, by default None
        on_delete : Optional[Callable[[str], None]], optional
            JdÜ¿ó¼Bn³üëÐÃ¯¢p, by default None
        on_close : Optional[Callable[[], None]], optional
            ‰X‹Ü¿ó¼Bn³üëÐÃ¯¢p, by default None
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
        ³óÝüÍóÈnìóÀêó°
        
        Parameters
        ----------
        session_id : str
            h:Y‹»Ã·çónID
        """
        self.component.render(session_id)


def edit_session_metadata(project_manager: ProjectManager,
                          session_manager: SessionManager,
                          session_id: str) -> bool:
    """
    »Ã·çóá¿Çü¿nèÆÕ©üàì¬·üAPI’Û	
    
    Parameters
    ----------
    project_manager : ProjectManager
        ×í¸§¯È¡¯é¹n¤ó¹¿ó¹
    session_manager : SessionManager
        »Ã·çó¡¯é¹n¤ó¹¿ó¹
    session_id : str
        èÆY‹»Ã·çónID
        
    Returns
    -------
    bool
        ô°kŸW_4True
    """
    session = project_manager.get_session(session_id)
    if not session:
        st.error(f"»Ã·çóL‹dKŠ~[“: {session_id}")
        return False
    
    st.subheader(f"»Ã·çó '{session.name}' nèÆ")
    
    # ú,Å1nèÆ
    with st.form("edit_session_form"):
        name = st.text_input("»Ã·çó", value=session.name)
        description = st.text_area("¬", value=session.description)
        
        # þ(n¿°’Ö—
        current_tags = session.tags if session.tags else []
        
        # )(ïýj¿°nÖ—âXn¿°hþ(n¿°’Þü¸	
        available_tags = session_manager.get_available_tags()
        all_tags = list(set(available_tags + current_tags))
        
        # ¿°nxž
        selected_tags = st.multiselect(
            "¿°",
            options=all_tags,
            default=current_tags
        )
        
        # °WD¿°ný 
        new_tag = st.text_input("°WD¿°’ý  («óÞ:Šgpšïý)")
        
        # «Æ´êxž
        categories = ["general", "race", "training", "analysis", "other"]
        current_category = getattr(session, 'category', 'general')
        if current_category and current_category not in categories:
            categories.append(current_category)
        
        category = st.selectbox(
            "«Æ´ê",
            options=categories,
            index=categories.index(current_category) if current_category in categories else 0
        )
        
        # ¹Æü¿¹xž
        statuses = ["active", "in_progress", "completed", "archived"]
        current_status = getattr(session, 'status', 'active')
        if current_status and current_status not in statuses:
            statuses.append(current_status)
        
        status = st.selectbox(
            "¹Æü¿¹",
            options=statuses,
            index=statuses.index(current_status) if current_status in statuses else 0
        )
        
        # U¡
        current_rating = getattr(session, 'rating', 0)
        rating = st.slider(
            "U¡",
            min_value=0,
            max_value=5,
            value=current_rating,
            step=1
        )
        
        # á¿Çü¿nèÆ
        st.subheader("á¿Çü¿")
        
        col1, col2 = st.columns(2)
        
        with col1:
            location = st.text_input("MnÅ1", value=session.metadata.get("location", ""))
            boat_type = st.text_input("G.", value=session.metadata.get("boat_type", ""))
        
        with col2:
            event_date = st.date_input(
                "¤ÙóÈå",
                value=None  # ,eosession.metadata.get("event_date")’	ÛWf(
            )
            crew_info = st.text_input("¯ëüÅ1", value=session.metadata.get("crew_info", ""))
        
        # ]nÖná¿Çü¿nh:hèÆ
        other_metadata = {}
        for key, value in session.metadata.items():
            if key not in ["location", "boat_type", "event_date", "crew_info", "created_by", "related_sessions"]:
                other_metadata[key] = value
        
        if other_metadata:
            st.subheader("]nÖná¿Çü¿")
            for key, value in other_metadata.items():
                other_metadata[key] = st.text_input(key, value, key=f"metadata_{key}")
        
        submitted = st.form_submit_button("ô°")
        
        if submitted:
            # ú,Å1nô°
            session.name = name
            session.description = description
            
            # á5^'nô°
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
            
            # ¿°næ
            final_tags = selected_tags
            if new_tag:
                # «óÞg:‰Œ_pn¿°’æ
                additional_tags = [tag.strip() for tag in new_tag.split(",") if tag.strip()]
                final_tags.extend(additional_tags)
                # Í’Jd
                final_tags = list(set(final_tags))
            
            session.tags = final_tags
            
            # á¿Çü¿nô°
            updated_metadata = {}
            
            # ú,á¿Çü¿
            updated_metadata["location"] = location
            updated_metadata["boat_type"] = boat_type
            updated_metadata["crew_info"] = crew_info
            
            # ¤ÙóÈånæ
            if event_date:
                updated_metadata["event_date"] = event_date.isoformat()
            
            # ]nÖná¿Çü¿næ
            for key, value in other_metadata.items():
                updated_metadata[key] = value
            
            # á¿Çü¿’ ìô°
            session_manager.update_session_metadata(session_id, updated_metadata)
            
            # »Ã·çó’ÝX
            project_manager.save_session(session)
            
            st.success("»Ã·çóÅ1’ô°W~W_")
            return True
    
    return False


def create_session_annotation(session_manager: SessionManager, session_id: str) -> bool:
    """
    »Ã·çóèÈn\Õ©üàì¬·üAPI’Û	
    
    Parameters
    ----------
    session_manager : SessionManager
        »Ã·çó¡¯é¹n¤ó¹¿ó¹
    session_id : str
        èÈ’ý Y‹»Ã·çónID
        
    Returns
    -------
    bool
        \kŸW_4True
    """
    st.subheader("°WDèÈ’ý ")
    
    with st.form("new_annotation_form"):
        title = st.text_input("¿¤Èë", key="annotation_title")
        content = st.text_area("…¹", key="annotation_content")
        
        col1, col2 = st.columns(2)
        
        with col1:
            latitude = st.number_input("ï¦ (ª×·çó)", min_value=-90.0, max_value=90.0, value=None, key="annotation_lat")
        
        with col2:
            longitude = st.number_input("L¦ (ª×·çó)", min_value=-180.0, max_value=180.0, value=None, key="annotation_lon")
        
        annotation_type = st.selectbox(
            "¿¤×",
            options=["text", "waypoint", "mark", "tack", "gybe", "strategy", "other"],
            key="annotation_type"
        )
        
        submitted = st.form_submit_button("ý ")
        
        if submitted:
            if not title:
                st.error("¿¤ÈëoÅgY")
                return False
            
            if not content:
                st.error("…¹oÅgY")
                return False
            
            # MnÅ1næ
            position = None
            if latitude is not None and longitude is not None:
                position = (latitude, longitude)
            
            # èÈn\
            try:
                annotation = session_manager.create_annotation(
                    session_id=session_id,
                    title=title,
                    content=content,
                    position=position,
                    annotation_type=annotation_type
                )
                
                st.success("èÈ’ý W~W_")
                return True
            
            except Exception as e:
                st.error(f"èÈný k1WW~W_: {str(e)}")
                return False
    
    return False