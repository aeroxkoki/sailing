"""
ui.pages.session_management

セッション管理ページ
"""

import streamlit as st
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime

from sailing_data_processor.project.project_manager import ProjectManager
from sailing_data_processor.project.session_manager import SessionManager
from ui.components.project.session_list import session_list_component, detailed_session_list_view
from ui.components.project.session_details import SessionDetailsView
from ui.components.project.session_editor import SessionEditorView

def session_management_page():
    """セッション管理ページ"""
    st.title("セッション管理")
    
    # プロジェクト管理クラスとセッション管理クラスのインスタンスを取得
    # 実際のアプリケーションでは、sessionや初期化スクリプトから取得する
    if "project_manager" not in st.session_state:
        st.session_state.project_manager = ProjectManager()
    
    if "session_manager" not in st.session_state:
        st.session_state.session_manager = SessionManager(st.session_state.project_manager)
    
    project_manager = st.session_state.project_manager
    session_manager = st.session_state.session_manager
    
    # 状態管理
    if "view_state" not in st.session_state:
        st.session_state.view_state = "list"  # list, details, edit
    
    if "selected_session_id" not in st.session_state:
        st.session_state.selected_session_id = None
    
    if "selected_project_id" not in st.session_state:
        # すべてのセッションを表示するための特殊なID
        st.session_state.selected_project_id = "all"
    
    # プロジェクト選択のサイドバー
    with st.sidebar:
        st.subheader("プロジェクト選択")
        
        # プロジェクト一覧を取得
        projects = project_manager.get_projects()
        project_options = {p.project_id: p.name for p in projects}
        project_options["all"] = "すべてのセッション"
        
        selected_project = st.selectbox(
            "プロジェクト:",
            options=list(project_options.keys()),
            format_func=lambda x: project_options[x],
            index=list(project_options.keys()).index(st.session_state.selected_project_id),
            key="project_selector"
        )
        
        st.session_state.selected_project_id = selected_project
        
        # 表示モード切り替えボタン
        if st.session_state.view_state != "list":
            if st.button("セッションリストに戻る", use_container_width=True):
                st.session_state.view_state = "list"
                st.session_state.selected_session_id = None
                st.rerun()
    
    # メイン表示エリア
    if st.session_state.view_state == "list":
        # セッションリスト表示
        if st.session_state.selected_project_id == "all":
            # すべてのセッション表示
            st.subheader("すべてのセッション")
            sessions = session_manager.get_all_sessions()
            
            if not sessions:
                st.info("セッションがありません。")
            else:
                # セッションリストをDataFrameで表示
                sessions_data = []
                for session in sessions:
                    sessions_data.append({
                        "セッションID": session.session_id,
                        "セッション名": session.name,
                        "説明": session.description,
                        "ステータス": session.status,
                        "カテゴリ": session.category,
                        "更新日時": session.updated_at
                    })
                
                df = pd.DataFrame(sessions_data)
                
                # 検索フィルタリング（簡易版）
                search_term = st.text_input("検索:", key="global_session_search")
                
                if search_term:
                    filtered_df = df[
                        df["セッション名"].str.contains(search_term, case=False, na=False) | 
                        df["説明"].str.contains(search_term, case=False, na=False)
                    ]
                    if filtered_df.empty:
                        st.warning("条件に合うセッションがありません。")
                    else:
                        df = filtered_df
                
                # テーブル表示
                selected_indices = st.dataframe(
                    df.drop(columns=["セッションID"]),
                    use_container_width=True,
                    column_config={
                        "更新日時": st.column_config.DatetimeColumn(
                            "更新日時",
                            format="YYYY-MM-DD HH:mm",
                            help="セッションの最終更新日時"
                        )
                    }
                )
                
                # セッション選択
                selected_session = st.selectbox(
                    "詳細を表示するセッション:",
                    options=df["セッションID"].tolist(),
                    format_func=lambda x: df.loc[df["セッションID"] == x, "セッション名"].iloc[0],
                    key="global_session_selector"
                )
                
                if st.button("詳細を表示", key="view_global_session_detail_btn"):
                    st.session_state.selected_session_id = selected_session
                    st.session_state.view_state = "details"
                    st.rerun()
        else:
            # プロジェクト内のセッション表示
            project = project_manager.get_project(st.session_state.selected_project_id)
            if project:
                st.subheader(f"{project.name} - セッション管理")
                
                # セッション追加ハンドラ
                def on_add_session():
                    st.session_state.view_state = "add_session"
                    st.rerun()
                
                # セッション削除ハンドラ
                def on_remove_session(session_id):
                    success = session_manager.remove_session_from_project(project.project_id, session_id)
                    if success:
                        st.success("セッションをプロジェクトから削除しました。")
                        st.rerun()
                    else:
                        st.error("セッションの削除に失敗しました。")
                
                # セッション選択ハンドラ
                def on_select_session(session_id):
                    st.session_state.selected_session_id = session_id
                    st.session_state.view_state = "details"
                    st.rerun()
                
                # 詳細セッションリスト表示
                detailed_session_list_view(
                    session_manager,
                    project.project_id,
                    on_select=on_select_session,
                    on_add=on_add_session,
                    on_remove=on_remove_session
                )
    
    elif st.session_state.view_state == "details":
        # セッション詳細表示
        if st.session_state.selected_session_id:
            # 編集ハンドラ
            def on_edit_session(session_id):
                st.session_state.view_state = "edit"
                st.rerun()
            
            # 削除ハンドラ
            def on_delete_session(session_id):
                # セッションの完全削除
                success = project_manager.delete_session(session_id)
                if success:
                    st.success("セッションを削除しました。")
                    st.session_state.view_state = "list"
                    st.session_state.selected_session_id = None
                    st.rerun()
                else:
                    st.error("セッションの削除に失敗しました。")
            
            # 戻るハンドラ
            def on_back_to_list():
                st.session_state.view_state = "list"
                st.session_state.selected_session_id = None
                st.rerun()
            
            # セッション詳細表示コンポーネント
            details_view = SessionDetailsView(
                project_manager=project_manager,
                session_manager=session_manager,
                on_edit=on_edit_session,
                on_delete=on_delete_session,
                on_back=on_back_to_list
            )
            
            details_view.render(st.session_state.selected_session_id)
    
    elif st.session_state.view_state == "edit":
        # セッション編集
        if st.session_state.selected_session_id:
            # 保存ハンドラ
            def on_save_session(session_id):
                st.success("変更を保存しました。")
                st.session_state.view_state = "details"
                st.rerun()
            
            # キャンセルハンドラ
            def on_cancel_edit():
                st.session_state.view_state = "details"
                st.rerun()
            
            # セッション編集コンポーネント
            editor_view = SessionEditorView(
                project_manager=project_manager,
                session_manager=session_manager,
                on_save=on_save_session,
                on_cancel=on_cancel_edit
            )
            
            editor_view.render(st.session_state.selected_session_id)
    
    elif st.session_state.view_state == "add_session":
        # セッション追加（プロジェクトへの割り当て）
        if st.session_state.selected_project_id != "all":
            st.subheader("プロジェクトにセッションを追加")
            
            # プロジェクトに割り当てられていないセッションを取得
            unassigned_sessions = session_manager.get_sessions_not_in_project(st.session_state.selected_project_id)
            
            if not unassigned_sessions:
                st.info("追加可能なセッションがありません。すべてのセッションは既にプロジェクトに割り当てられています。")
                
                if st.button("戻る"):
                    st.session_state.view_state = "list"
                    st.rerun()
            else:
                # セッション選択用のデータ
                sessions_data = []
                for session in unassigned_sessions:
                    sessions_data.append({
                        "選択": False,
                        "セッションID": session.session_id,
                        "セッション名": session.name,
                        "説明": session.description[:50] + "..." if len(session.description) > 50 else session.description,
                        "ステータス": session.status,
                        "カテゴリ": session.category
                    })
                
                df = pd.DataFrame(sessions_data)
                
                # フィルタリング
                search_term = st.text_input("検索:", key="add_session_search")
                
                if search_term:
                    filtered_df = df[
                        df["セッション名"].str.contains(search_term, case=False, na=False) | 
                        df["説明"].str.contains(search_term, case=False, na=False)
                    ]
                    if filtered_df.empty:
                        st.warning("条件に合うセッションがありません。")
                    else:
                        df = filtered_df
                
                # 選択用チェックボックスつきテーブル
                edited_df = st.data_editor(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    disabled=["セッションID", "セッション名", "説明", "ステータス", "カテゴリ"],
                    column_config={
                        "選択": st.column_config.CheckboxColumn(
                            "選択",
                            help="追加するセッションを選択"
                        )
                    }
                )
                
                # 選択されたセッション
                selected_sessions = edited_df[edited_df["選択"]]["セッションID"].tolist()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("選択したセッションを追加", use_container_width=True, disabled=len(selected_sessions) == 0):
                        # セッションをプロジェクトに追加
                        count = session_manager.bulk_add_sessions_to_project(
                            st.session_state.selected_project_id, 
                            selected_sessions
                        )
                        
                        if count > 0:
                            st.success(f"{count}件のセッションをプロジェクトに追加しました。")
                            st.session_state.view_state = "list"
                            st.rerun()
                        else:
                            st.error("セッションの追加に失敗しました。")
                
                with col2:
                    if st.button("キャンセル", use_container_width=True):
                        st.session_state.view_state = "list"
                        st.rerun()
