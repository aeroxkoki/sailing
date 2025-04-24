# -*- coding: utf-8 -*-
"""
ui.components.sharing.team_panel

���UI�������
"""

import streamlit as st
from typing import Dict, Any, List, Optional, Callable
import datetime

from sailing_data_processor.sharing import TeamManager


class TeamPanelComponent:
    """
    ���UI�������
    
    ���n\��������q	jin_��ЛY�UI�������gY
    �÷���������P�����gq	Y�_�n_��ЛW~Y
    """
    
    def __init__(self, key="team_panel", 
                 team_manager: Optional[TeamManager] = None, 
                 user_id: Optional[str] = None,
                 user_name: Optional[str] = None,
                 on_team_created: Optional[Callable] = None,
                 on_resource_shared: Optional[Callable] = None):
        """
        
        
        Parameters
        ----------
        key : str, optional
            �������n��, by default "team_panel"
        team_manager : Optional[TeamManager], optional
            �����, by default None
        user_id : Optional[str], optional
            �(n����ID, by default None
        user_name : Optional[str], optional
            ����
, by default None
        on_team_created : Optional[Callable], optional
            ���\Bn����ï, by default None
        on_resource_shared : Optional[Callable], optional
            ���q	Bn����ï, by default None
        """
        self.key = key
        self.team_manager = team_manager
        self.user_id = user_id
        self.user_name = user_name or user_id
        self.on_team_created = on_team_created
        self.on_resource_shared = on_resource_shared
        
        # �Kn
        if f"{key}_active_tab" not in st.session_state:
            st.session_state[f"{key}_active_tab"] = "my_teams"
        if f"{key}_selected_team" not in st.session_state:
            st.session_state[f"{key}_selected_team"] = None
        if f"{key}_show_create_form" not in st.session_state:
            st.session_state[f"{key}_show_create_form"] = False
        if f"{key}_show_invite_form" not in st.session_state:
            st.session_state[f"{key}_show_invite_form"] = False
            
    def render(self, resource_id: Optional[str] = None, resource_type: Optional[str] = None):
        """
        �������n�����
        
        Parameters
        ----------
        resource_id : Optional[str], optional
            q	�a���ID, by default None
        resource_type : Optional[str], optional
            q	�a������, by default None
        """
        st.subheader("���")
        
        # ����鹄����IDLjD4o���h:
        if not self.team_manager or not self.user_id:
            st.error("���L-�U�fDjDK����IDL
gY")
            return
        
        # ��nh:
        tab_labels = ["ޤ���", "ۅ", "���\"]
        tab_keys = ["my_teams", "invitations", "create_team"]
        
        # �÷��IDh���LB�4oq	�֒��
        if resource_id and resource_type:
            tab_labels.append("���q	")
            tab_keys.append("share")
        
        # �(n��ƣֿ�n���ï��֗
        active_tab = st.session_state[f"{self.key}_active_tab"]
        active_index = tab_keys.index(active_tab) if active_tab in tab_keys else 0
        
        tabs = st.tabs(tab_labels)
        
        # ޤ����
        with tabs[0]:
            if active_index == 0:
                self._render_my_teams_tab()
        
        # ۅ��
        with tabs[1]:
            if active_index == 1:
                self._render_invitations_tab()
        
        # ���\��
        with tabs[2]:
            if active_index == 2:
                self._render_create_team_tab()
        
        # ���q	�����IDh���LB�4n	
        if resource_id and resource_type:
            with tabs[3]:
                if active_index == 3:
                    self._render_share_tab(resource_id, resource_type)
        
        # ����H�
        if active_index != tab_keys.index(active_tab):
            st.session_state[f"{self.key}_active_tab"] = tab_keys[active_index]
            st.experimental_rerun()
    
    def _render_my_teams_tab(self):
        """ޤ����nh:"""
        st.write("### ޤ���")
        
        # ����n����֗
        user_teams = self.team_manager.get_user_teams(self.user_id)
        
        if not user_teams:
            st.info("Bj_o~`���k@^WfD~[�����\Y�Kۅ��QfO`UD")
            
            # ���\��xn��
            if st.button("�WD����\", key=f"{self.key}_create_team_btn"):
                st.session_state[f"{self.key}_active_tab"] = "create_team"
                st.experimental_rerun()
            
            return
        
        # ���h:
        st.write(f"@^���p: {len(user_teams)}")
        
        # ���x�
        team_options = {team.team_id: team.name for team in user_teams}
        selected_team_id = st.selectbox(
            "����x�",
            options=list(team_options.keys()),
            format_func=lambda x: team_options.get(x, x),
            key=f"{self.key}_team_selector"
        )
        
        # �÷��Kkx������X
        st.session_state[f"{self.key}_selected_team"] = selected_team_id
        
        # x�W_���ns0h:
        selected_team = next((t for t in user_teams if t.team_id == selected_team_id), None)
        
        if selected_team:
            self._render_team_details(selected_team)
    
    def _render_team_details(self, team):
        """
        ���s0nh:
        
        Parameters
        ----------
        team : Team
            ����1
        """
        st.write("---")
        st.write(f"## {team.name}")
        
        if team.description:
            st.write(team.description)
        
        # ����,�1
        col1, col2 = st.columns(2)
        
        with col1:
            created_at = datetime.datetime.fromisoformat(team.created_at)
            st.write(f"**\�:** {created_at.strftime('%Yt%m%d�')}")
            
            # �����1
            if team.owner_id:
                st.write(f"**����:** {team.owner_id}")
        
        with col2:
            # ����p
            st.write(f"**����p:** {len(team.members)}")
            
            # q	���p
            project_count = len(team.projects)
            session_count = len(team.sessions)
            st.write(f"**q	������:** {project_count}")
            st.write(f"**q	�÷��:** {session_count}")
        
        # �����
        st.write("### ����")
        
        # �nyr���
        user_role = team.members[self.user_id].role if self.user_id in team.members else None
        is_admin = user_role == "owner" or user_role == "admin"
        
        # ����������h:
        member_data = []
        for user_id, member in team.members.items():
            member_data.append({
                "����ID": member.user_id,
                "
M": member.name,
                "���": member.email or "-",
                "yr": self._format_role(member.role),
                "���": datetime.datetime.fromisoformat(member.added_at).strftime("%Y/%m/%d")
            })
        
        if member_data:
            # DataFramek	�Wf����h:
            import pandas as pd
            member_df = pd.DataFrame(member_data)
            st.dataframe(member_df, use_container_width=True)
        
        # �~_o��n4n�\ܿ�
        if is_admin:
            st.write("### ���")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # ����ۅܿ�
                if st.button("�����ۅ", key=f"{self.key}_invite_btn"):
                    st.session_state[f"{self.key}_show_invite_form"] = True
                    st.experimental_rerun()
            
            with col2:
                # ���-���ܿ�
                if st.button("���-����", key=f"{self.key}_edit_team_btn"):
                    st.session_state[f"{self.key}_show_edit_form"] = True
                    st.experimental_rerun()
            
            # ۅթ��nh:
            if st.session_state.get(f"{self.key}_show_invite_form", False):
                self._render_invite_form(team)
            
            # �����թ��nh:
            if st.session_state.get(f"{self.key}_show_edit_form", False):
                self._render_edit_team_form(team)
        
        # q	����
        st.write("### q	���")
        
        # �����ȧ
        if team.projects:
            st.write("#### ������")
            for project_id in team.projects:
                st.write(f"- {project_id}")
        
        # �÷��
        if team.sessions:
            st.write("#### �÷��")
            for session_id in team.sessions:
                st.write(f"- {session_id}")
        
        if not team.projects and not team.sessions:
            st.info("Sn���ko~`q	���LB�~[�")
    
    def _render_invite_form(self, team):
        """
        ����ۅթ��nh:
        
        Parameters
        ----------
        team : Team
            ����1
        """
        st.write("### �����ۅ")
        
        with st.form(key=f"{self.key}_invite_form"):
            # �����e�
            email = st.text_input("�����", key=f"{self.key}_invite_email")
            
            # h:
e�
            name = st.text_input("h:
", key=f"{self.key}_invite_name")
            
            # yrx�
            role_options = {
                "viewer": "����n��	",
                "editor": "���Ƃ��	",
                "admin": "���������	"
            }
            role = st.selectbox(
                "yr",
                options=list(role_options.keys()),
                format_func=lambda x: role_options.get(x, x),
                key=f"{self.key}_invite_role"
            )
            
            # �û��e�
            message = st.text_area("ۅ�û���׷��	", key=f"{self.key}_invite_message")
            
            # �ܿ�
            submit = st.form_submit_button("ۅ��")
            cancel = st.form_submit_button("����")
            
            if cancel:
                st.session_state[f"{self.key}_show_invite_form"] = False
                st.experimental_rerun()
            
            if submit and email and name:
                try:
                    # ۅ�
                    invitation = self.team_manager.create_invitation(
                        team_id=team.team_id,
                        creator_id=self.user_id,
                        email=email,
                        role=role,
                        message=message
                    )
                    
                    if invitation:
                        st.success(f"{email} kۅ��W~W_")
                        st.session_state[f"{self.key}_show_invite_form"] = False
                        st.experimental_rerun()
                    else:
                        st.error("ۅn�k1WW~W_")
                except Exception as e:
                    st.error(f"���LzW~W_: {str(e)}")
    
    def _render_edit_team_form(self, team):
        """
        �����թ��nh:
        
        Parameters
        ----------
        team : Team
            ����1
        """
        st.write("### ���-�n��")
        
        with st.form(key=f"{self.key}_edit_team_form"):
            # ���
e�
            name = st.text_input("���
", value=team.name, key=f"{self.key}_edit_name")
            
            # �e�
            description = st.text_area("�", value=team.description, key=f"{self.key}_edit_description")
            
            # �ܿ�
            submit = st.form_submit_button("��")
            cancel = st.form_submit_button("����")
            
            if cancel:
                st.session_state[f"{self.key}_show_edit_form"] = False
                st.experimental_rerun()
            
            if submit and name:
                try:
                    # ����1��
                    success = self.team_manager.update_team(
                        team_id=team.team_id,
                        name=name,
                        description=description
                    )
                    
                    if success:
                        st.success("����1���W~W_")
                        st.session_state[f"{self.key}_show_edit_form"] = False
                        st.experimental_rerun()
                    else:
                        st.error("����1n��k1WW~W_")
                except Exception as e:
                    st.error(f"���LzW~W_: {str(e)}")
    
    def _render_invitations_tab(self):
        """ۅ��nh:"""
        st.write("### ۅ�")
        
        # ����nۅ�����g"	
        user_email = f"{self.user_id}@example.com"  # �n�����
        
        # pending_invitations = self.team_manager.get_pending_invitations_by_email(user_email)
        # FIXME: 
n�pL��gM�~g�n����(
        pending_invitations = []
        
        if not pending_invitations:
            st.info("�(Bj_�nۅoB�~[�")
            return
        
        # ۅ�h:
        for invitation in pending_invitations:
            with st.container():
                st.write("---")
                
                # ۅ�1
                st.write(f"**���:** {invitation.get('team_name', '
j���')}")
                st.write(f"**ۅ:** {invitation.get('creator_id', '
')}")
                
                # yr
                role = invitation.get('role', 'viewer')
                st.write(f"**yr:** {self._format_role(role)}")
                
                # 	�P
                expires_at = datetime.datetime.fromisoformat(invitation.get('expires_at', datetime.datetime.now().isoformat()))
                days_remaining = (expires_at - datetime.datetime.now()).days
                st.write(f"**	�P:** Bh{days_remaining}�")
                
                # �û��
                message = invitation.get('message', '')
                if message:
                    st.write(f"**�û��:** {message}")
                
                # �����ܿ�
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("�", key=f"{self.key}_accept_{invitation['invitation_id']}"):
                        try:
                            success = self.team_manager.accept_invitation(invitation['invitation_id'], self.user_id)
                            if success:
                                st.success("ۅ��W~W_")
                                st.experimental_rerun()
                            else:
                                st.error("ۅn�k1WW~W_")
                        except Exception as e:
                            st.error(f"���LzW~W_: {str(e)}")
                
                with col2:
                    if st.button("�&", key=f"{self.key}_reject_{invitation['invitation_id']}"):
                        try:
                            success = self.team_manager.reject_invitation(invitation['invitation_id'])
                            if success:
                                st.success("ۅ��&W~W_")
                                st.experimental_rerun()
                            else:
                                st.error("ۅn�&k1WW~W_")
                        except Exception as e:
                            st.error(f"���LzW~W_: {str(e)}")
    
    def _render_create_team_tab(self):
        """���\��nh:"""
        st.write("### �WD����\")
        
        with st.form(key=f"{self.key}_create_team_form"):
            # ���
e�
            name = st.text_input("���
", key=f"{self.key}_team_name")
            
            # �e�
            description = st.text_area("��׷��	", key=f"{self.key}_team_description")
            
            # �ܿ�
            submit = st.form_submit_button("����\")
            
            if submit and name:
                try:
                    # ���\
                    team = self.team_manager.create_team(
                        name=name,
                        description=description,
                        owner_id=self.user_id
                    )
                    
                    if team:
                        st.success(f"���{name}
�\W~W_")
                        
                        # ����ï�p�|s�W
                        if self.on_team_created:
                            try:
                                self.on_team_created(team.team_id)
                            except Exception as e:
                                st.error(f"����ï�L-k���LzW~W_: {str(e)}")
                        
                        # ޤ����k��H
                        st.session_state[f"{self.key}_active_tab"] = "my_teams"
                        st.session_state[f"{self.key}_selected_team"] = team.team_id
                        st.experimental_rerun()
                    else:
                        st.error("���n\k1WW~W_")
                except Exception as e:
                    st.error(f"���LzW~W_: {str(e)}")
    
    def _render_share_tab(self, resource_id: str, resource_type: str):
        """
        ���q	��nh:
        
        Parameters
        ----------
        resource_id : str
            q	�a���ID
        resource_type : str
            q	�a������
        """
        st.write(f"### ���k{self._format_resource_type(resource_type)}�q	")
        st.write(f"**{resource_type}ID:** {resource_id}")
        
        # ����n����֗
        user_teams = self.team_manager.get_user_teams(self.user_id)
        
        if not user_teams:
            st.info("Bj_o~`���k@^WfD~[�����\Y�Kۅ��QfO`UD")
            
            # ���\��xn��
            if st.button("�WD����\", key=f"{self.key}_create_team_btn2"):
                st.session_state[f"{self.key}_active_tab"] = "create_team"
                st.experimental_rerun()
            
            return
        
        # ���x�
        team_options = {}
        for team in user_teams:
            # ����nyr�֗
            user_role = team.members.get(self.user_id).role if self.user_id in team.members else None
            # ���
n)P�d���nh:
            if user_role in ["owner", "admin", "editor"]:
                team_options[team.team_id] = team.name
        
        if not team_options:
            st.warning("q	gM����LB�~[�q	Y�ko���n��K�gB�ŁLB�~Y")
            return
        
        selected_team_id = st.selectbox(
            "q	H���",
            options=list(team_options.keys()),
            format_func=lambda x: team_options.get(x, x),
            key=f"{self.key}_share_team_selector"
        )
        
        # q	K��ï
        selected_team = next((t for t in user_teams if t.team_id == selected_team_id), None)
        
        if selected_team:
            already_shared = False
            if resource_type == "project" and resource_id in selected_team.projects:
                already_shared = True
            elif resource_type == "session" and resource_id in selected_team.sessions:
                already_shared = True
            
            if already_shared:
                st.info(f"Sn���o�k���{selected_team.name}
hq	U�fD~Y")
                
                # q	�dܿ�
                if st.button("q	��d", key=f"{self.key}_unshare_btn"):
                    try:
                        success = False
                        if resource_type == "project":
                            success = self.team_manager.remove_project_from_team(selected_team_id, resource_id)
                        elif resource_type == "session":
                            success = self.team_manager.remove_session_from_team(selected_team_id, resource_id)
                        
                        if success:
                            st.success("q	��dW~W_")
                            st.experimental_rerun()
                        else:
                            st.error("q	n�dk1WW~W_")
                    except Exception as e:
                        st.error(f"���LzW~W_: {str(e)}")
            else:
                # q	ܿ�
                if st.button("q	Y�", key=f"{self.key}_share_btn"):
                    try:
                        success = False
                        if resource_type == "project":
                            success = self.team_manager.add_project_to_team(selected_team_id, resource_id)
                        elif resource_type == "session":
                            success = self.team_manager.add_session_to_team(selected_team_id, resource_id)
                        
                        if success:
                            st.success(f"���{selected_team.name}
hq	W~W_")
                            
                            # ����ï�p�|s�W
                            if self.on_resource_shared:
                                try:
                                    self.on_resource_shared(selected_team_id, resource_id, resource_type)
                                except Exception as e:
                                    st.error(f"����ï�L-k���LzW~W_: {str(e)}")
                            
                            st.experimental_rerun()
                        else:
                            st.error("q	k1WW~W_")
                    except Exception as e:
                        st.error(f"���LzW~W_: {str(e)}")
    
    def _format_role(self, role: str) -> str:
        """
        yrnh:
�֗
        
        Parameters
        ----------
        role : str
            yr���
            
        Returns
        -------
        str
            yrnh:
        """
        role_map = {
            "owner": "����",
            "admin": "�",
            "editor": "��",
            "viewer": "��"
        }
        return role_map.get(role, role)
    
    def _format_resource_type(self, resource_type: str) -> str:
        """
        ������nh:
�֗
        
        Parameters
        ----------
        resource_type : str
            �����׳��
            
        Returns
        -------
        str
            ������nh:
        """
        type_map = {
            "project": "������",
            "session": "�÷��",
            "export": "������P�",
            "result": "�P�"
        }
        return type_map.get(resource_type, resource_type)


# ��!Xk(Y�_�nAPI�����p
def TeamPanel(team_manager=None, user_id=None, user_name=None, 
             resource_id=None, resource_type=None, 
             on_team_created=None, on_resource_shared=None, key="team_panel"):
    """
    ������n�����
    
    Parameters
    ----------
    team_manager : optional
        �����, by default None
    user_id : optional
        �(n����ID, by default None
    user_name : optional
        ����
, by default None
    resource_id : optional
        q	�a���ID, by default None
    resource_type : optional
        q	�a������, by default None
    on_team_created : optional
        ���\Bn����ï, by default None
    on_resource_shared : optional
        ���q	Bn����ï, by default None
    key : str, optional
        �������n��, by default "team_panel"
    """
    component = TeamPanelComponent(
        key=key,
        team_manager=team_manager,
        user_id=user_id,
        user_name=user_name,
        on_team_created=on_team_created,
        on_resource_shared=on_resource_shared
    )
    component.render(resource_id, resource_type)
