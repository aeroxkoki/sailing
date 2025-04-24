# -*- coding: utf-8 -*-
"""
ui.components.project.project_detail

プロジェクト詳細表示のUIコンポーネント
"""

import streamlit as st
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime

from sailing_data_processor.project.project_manager import Project, ProjectManager


class ProjectDetailView:
    """
    プロジェクト詳細表示コンポーネント
    
    選択されたプロジェクトの詳細情報を表示し、
    編集、削除、セッション管理などの機能を提供します。
    
    Parameters
    ----------
    project_manager : ProjectManager
        プロジェクト管理クラスのインスタンス
    on_edit : Callable[[str], None], optional
        編集ボタン押下時のコールバック関数, by default None
    on_delete : Callable[[str], None], optional
        削除ボタン押下時のコールバック関数, by default None
    on_add_session : Callable[[str], None], optional
        セッション追加ボタン押下時のコールバック関数, by default None
    on_select_session : Callable[[str], None], optional
        セッション選択時のコールバック関数, by default None
    on_close : Callable[[], None], optional
        閉じるボタン押下時のコールバック関数, by default None
    """
    
    def __init__(
        self,
        project_manager: ProjectManager,
        on_edit: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        on_add_session: Optional[Callable[[str], None]] = None,
        on_select_session: Optional[Callable[[str], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
    ):
        self.project_manager = project_manager
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_add_session = on_add_session
        self.on_select_session = on_select_session
        self.on_close = on_close
    
    def format_datetime(self, iso_datetime: str) -> str:
        """
        ISO形式の日時文字列を読みやすい形式に変換
        
        Parameters
        ----------
        iso_datetime : str
            ISO形式の日時文字列
            
        Returns
        -------
        str
            フォーマットされた日時文字列
        """
        try:
            dt = datetime.fromisoformat(iso_datetime)
            return dt.strftime("%Y/%m/%d %H:%M")
        except (ValueError, TypeError):
            return iso_datetime
    
    def render(self, project_id: str):
        """
        コンポーネントのレンダリング
        
        Parameters
        ----------
        project_id : str
            表示するプロジェクトのID
        """
        project = self.project_manager.get_project(project_id)
        if not project:
            st.error(f"プロジェクトが見つかりません: {project_id}")
            return
        
        # タイトルとアクションボタン
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(f"プロジェクト: {project.name}")
        
        with col2:
            cols = st.columns(3)
            with cols[0]:
                if st.button("編集", key="project_edit_btn", use_container_width=True):
                    if self.on_edit:
                        self.on_edit(project_id)
            
            with cols[1]:
                if st.button("削除", key="project_delete_btn", use_container_width=True):
                    # 削除確認ダイアログ
                    if "confirm_delete_project" not in st.session_state:
                        st.session_state.confirm_delete_project = False
                    
                    st.session_state.confirm_delete_project = True
            
            with cols[2]:
                if st.button("閉じる", key="project_close_btn", use_container_width=True):
                    if self.on_close:
                        self.on_close()
        
        # 削除確認ダイアログ
        if st.session_state.get("confirm_delete_project", False):
            with st.container():
                st.warning(f"プロジェクト「{project.name}」を削除しますか？この操作は元に戻せません。")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("削除を確定", key="confirm_delete_yes", use_container_width=True):
                        if self.on_delete:
                            self.on_delete(project_id)
                        st.session_state.confirm_delete_project = False
                with col2:
                    if st.button("キャンセル", key="confirm_delete_no", use_container_width=True):
                        st.session_state.confirm_delete_project = False
                        st.rerun()
        
        # プロジェクト基本情報
        with st.expander("プロジェクト情報", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**説明:** {project.description}" if project.description else "**説明:** *なし*")
                st.markdown(f"**作成日:** {self.format_datetime(project.created_at)}")
                st.markdown(f"**更新日:** {self.format_datetime(project.updated_at)}")
            
            with col2:
                tags_str = ", ".join(project.tags) if project.tags else "なし"
                st.markdown(f"**タグ:** {tags_str}")
                
                # 追加のメタデータ表示
                if project.metadata:
                    st.markdown("**メタデータ:**")
                    for key, value in project.metadata.items():
                        st.markdown(f"- {key}: {value}")
        
        # セッション管理
        st.subheader("セッション")
        
        # セッション追加ボタン
        if self.on_add_session:
            if st.button("セッションを追加", key="add_session_btn"):
                self.on_add_session(project_id)
        
        # プロジェクトに関連するセッションの取得
        sessions = self.project_manager.get_project_sessions(project_id)
        
        if not sessions:
            st.info("このプロジェクトにはセッションがありません。")
            return
        
        # セッション一覧の表示
        import pandas as pd
        
        session_data = []
        for session in sessions:
            session_data.append({
                "ID": session.session_id,
                "名前": session.name,
                "説明": session.description[:30] + "..." if len(session.description) > 30 else session.description,
                "タグ": ", ".join(session.tags) if session.tags else "",
                "作成日": self.format_datetime(session.created_at),
                "更新日": self.format_datetime(session.updated_at)
            })
        
        if session_data:
            df = pd.DataFrame(session_data)
            
            # 表示カラムの設定
            display_columns = ["名前", "説明", "タグ", "更新日"]
            
            # インタラクティブなテーブルの表示
            selection = st.data_editor(
                df[display_columns],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "名前": st.column_config.TextColumn("名前", width="medium"),
                    "説明": st.column_config.TextColumn("説明", width="large"),
                    "タグ": st.column_config.TextColumn("タグ", width="medium"),
                    "更新日": st.column_config.TextColumn("更新日", width="medium"),
                },
                key="session_table"
            )
            
            # セッション選択処理
            if selection is not None and self.on_select_session is not None:
                selected_indices = selection.index
                if selected_indices is not None and len(selected_indices) > 0:
                    selected_index = selected_indices[0]
                    selected_session_id = df.loc[selected_index, "ID"]
                    self.on_select_session(selected_session_id)
