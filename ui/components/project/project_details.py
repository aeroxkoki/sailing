# -*- coding: utf-8 -*-
"""
ui.components.project.project_details

プロジェクト詳細を表示するコンポーネント
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import pandas as pd

from ui.components.project.project_manager import initialize_project_manager
from sailing_data_processor.project.project_model import Project, Session
from sailing_data_processor.project.session_manager import SessionManager
from ui.components.project.session_list import detailed_session_list_view, session_list_component


def project_details_view(project_id: str) -> Tuple[bool, Optional[str]]:
    """
    プロジェクト詳細を表示するコンポーネント
    
    Parameters
    ----------
    project_id : str
        表示するプロジェクトのID
    
    Returns
    -------
    Tuple[bool, Optional[str]]
        (編集ボタンが押されたかどうか, 選択されたセッションID)
    """
    pm = initialize_project_manager()
    project = pm.get_project(project_id)
    
    if not project:
        st.error(f"プロジェクト ID: {project_id} が見つかりません。")
        return False, None
    
    # プロジェクトヘッダー部分
    col1, col2, col3 = st.columns([6, 2, 2])
    
    with col1:
        st.title(f"{project.name}")
    
    with col2:
        edit_button = st.button("編集", key="edit_project_button")
    
    with col3:
        delete_button = st.button("削除", key="delete_project_button", type="primary", use_container_width=True)
    
    # 削除確認処理
    if delete_button:
        st.warning(f"プロジェクト '{project.name}' を削除しますか？この操作は元に戻せません。")
        col1, col2 = st.columns([1, 1])
        with col1:
            cancel_delete = st.button("キャンセル", key="cancel_delete")
        with col2:
            confirm_delete = st.button("削除する", key="confirm_delete", type="primary")
            
        if confirm_delete:
            # 削除処理
            # セッションも削除するオプションの提供
            delete_sessions = st.checkbox("関連するセッションも削除", value=False, key="delete_sessions_checkbox")
            if pm.delete_project(project_id, delete_sessions=delete_sessions):
                st.success(f"プロジェクト '{project.name}' を削除しました。")
                # セッションステートをクリア
                if "selected_project_id" in st.session_state:
                    del st.session_state["selected_project_id"]
                # 1秒後にリロード
                st.rerun()
            else:
                st.error(f"プロジェクト '{project.name}' の削除に失敗しました。")
            
            return False, None
    
    # プロジェクト詳細情報
    with st.expander("詳細情報", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**説明:** {project.description}")
            st.markdown(f"**カテゴリ:** {project.category}")
            st.markdown(f"**タグ:** {', '.join(project.tags) if project.tags else '-'}")
            
            # 親プロジェクト情報
            if project.parent_id:
                parent = pm.get_project(project.parent_id)
                if parent:
                    st.markdown(f"**親プロジェクト:** {parent.name}")
                else:
                    st.markdown("**親プロジェクト:** 不明")
        
        with col2:
            try:
                created_at = datetime.fromisoformat(project.created_at).strftime("%Y-%m-%d %H:%M")
            except:
                created_at = project.created_at
                
            try:
                updated_at = datetime.fromisoformat(project.updated_at).strftime("%Y-%m-%d %H:%M")
            except:
                updated_at = project.updated_at
            
            st.markdown(f"**作成日時:** {created_at}")
            st.markdown(f"**更新日時:** {updated_at}")
            st.markdown(f"**場所:** {project.metadata.get('location', '-')}")
            st.markdown(f"**イベント日:** {project.metadata.get('event_date', '-')}")
            st.markdown(f"**天候:** {project.metadata.get('weather_conditions', '-')}")
            st.markdown(f"**艇種:** {project.metadata.get('boat_type', '-')}")
    
    # 関連するセッション一覧
    st.subheader("関連セッション")
    
    # SessionManagerの初期化
    from sailing_data_processor.project.project_manager import ProjectManager
    project_manager = ProjectManager(pm.storage)
    session_manager = SessionManager(project_manager)
    
    # 新規セッション作成ボタン
    col1, col2 = st.columns([4, 1])
    with col2:
        create_session_button = st.button("新規セッション作成", key="create_session_button")
    
    # セッション作成処理
    if create_session_button:
        st.session_state["current_tab"] = "session_create"
        st.session_state["parent_project_id"] = project_id
        return False, None
    
    # セッション選択ハンドラー
    def handle_session_select(session_id: str):
        if "selected_session_id" not in st.session_state:
            st.session_state["selected_session_id"] = session_id
    
    # セッション削除ハンドラー
    def handle_session_remove(session_id: str):
        if session_manager.remove_session_from_project(project_id, session_id):
            st.success(f"セッションをプロジェクトから削除しました。")
            st.rerun()
        else:
            st.error(f"セッションの削除に失敗しました。")
    
    # セッション追加ハンドラー
    def handle_session_add():
        st.session_state["current_tab"] = "session_create"
        st.session_state["parent_project_id"] = project_id
    
    # 詳細なセッションリスト表示
    detailed_session_list_view(
        session_manager,
        project_id,
        on_select=handle_session_select,
        on_add=handle_session_add,
        on_remove=handle_session_remove
    )
    
    # 選択されたセッションIDを取得
    selected_session_id = st.session_state.get("selected_session_id", None)
    
    return edit_button, selected_session_id
    
    return edit_button, None


def format_metadata_for_display(metadata: Dict[str, Any]) -> Dict[str, str]:
    """
    メタデータを表示用にフォーマットする
    
    Parameters
    ----------
    metadata : Dict[str, Any]
        元のメタデータ
    
    Returns
    -------
    Dict[str, str]
        表示用にフォーマットされたメタデータ
    """
    formatted = {}
    
    for key, value in metadata.items():
        if key == 'created_by':
            formatted["作成者"] = str(value)
        elif key == 'location':
            formatted["場所"] = str(value)
        elif key == 'event_date':
            formatted["イベント日"] = str(value)
        elif key == 'weather_conditions':
            formatted["天候"] = str(value)
        elif key == 'boat_type':
            formatted["艇種"] = str(value)
        elif key == 'crew_info':
            formatted["クルー情報"] = str(value)
        else:
            # その他のメタデータ
            formatted[key] = str(value)
    
    return formatted


def get_session_summary(sessions: List[Session]) -> Dict[str, Any]:
    """
    セッションの概要情報を取得する
    
    Parameters
    ----------
    sessions : List[Session]
        セッションのリスト
    
    Returns
    -------
    Dict[str, Any]
        セッション概要情報の辞書
    """
    total_sessions = len(sessions)
    
    status_counts = {
        "new": 0,
        "validated": 0,
        "analyzed": 0,
        "completed": 0
    }
    
    category_counts = {}
    
    total_analysis_results = 0
    
    for session in sessions:
        # ステータスカウント
        status = session.status or "new"
        status_counts[status] = status_counts.get(status, 0) + 1
        
        # カテゴリカウント
        category = session.category or "general"
        category_counts[category] = category_counts.get(category, 0) + 1
        
        # 分析結果の数
        total_analysis_results += len(session.analysis_results)
    
    # 最新のセッション
    latest_session = None
    if sessions:
        latest_session = max(sessions, key=lambda s: s.created_at)
    
    return {
        "total_sessions": total_sessions,
        "status_counts": status_counts,
        "category_counts": category_counts,
        "total_analysis_results": total_analysis_results,
        "latest_session": latest_session
    }
