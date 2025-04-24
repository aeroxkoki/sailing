# -*- coding: utf-8 -*-
"""
プロジェクト管理UIコンポーネント

プロジェクトの作成、編集、削除、およびセッションの割り当てを行うためのStreamlitコンポーネントを提供します。
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
from pathlib import Path
import uuid

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# 自作モジュールのインポート
from sailing_data_processor.project.project_manager import ProjectManager
from sailing_data_processor.project.project_model import Project
from ui.components.common.alerts import alert


def initialize_project_manager():
    """
    プロジェクトマネージャーの初期化
    
    Returns
    -------
    ProjectManager
        初期化されたプロジェクトマネージャーオブジェクト
    """
    if 'project_manager' not in st.session_state:
        # プロジェクトデータ保存用のディレクトリ
        projects_dir = Path("projects")
        if not projects_dir.exists():
            projects_dir.mkdir(parents=True, exist_ok=True)
        
        # プロジェクトマネージャーの初期化
        st.session_state.project_manager = ProjectManager(str(projects_dir))
    
    return st.session_state.project_manager


def project_list_view():
    """
    プロジェクト一覧を表示するコンポーネント
    
    Returns
    -------
    str or None
        選択されたプロジェクトID（選択されていない場合はNone）
    """
    pm = initialize_project_manager()
    projects = pm.get_projects()
    
    if not projects:
        st.info("プロジェクトがまだ作成されていません。新しいプロジェクトを作成してください。")
        return None
    
    # プロジェクト表示用のデータフレームを作成
    projects_data = []
    for project in projects:
        # セッション数を取得
        session_count = len(project.sessions)
        
        # 作成日と更新日の表示形式を調整
        try:
            created_at = datetime.fromisoformat(project.created_at).strftime("%Y-%m-%d %H:%M")
        except:
            created_at = project.created_at
            
        try:
            updated_at = datetime.fromisoformat(project.updated_at).strftime("%Y-%m-%d %H:%M")
        except:
            updated_at = project.updated_at
        
        projects_data.append({
            "プロジェクト名": project.name,
            "説明": project.description,
            "セッション数": session_count,
            "作成日時": created_at,
            "更新日時": updated_at,
            "タグ": ", ".join(project.tags) if project.tags else "",
            "プロジェクトID": project.project_id
        })
    
    # データフレームとして表示
    if projects_data:
        df = pd.DataFrame(projects_data)
        
        # ユーザーが選択できる行を表示
        st.dataframe(
            df.drop(columns=["プロジェクトID"]),
            use_container_width=True,
            column_config={
                "セッション数": st.column_config.NumberColumn(format="%d"),
            }
        )
        
        # プロジェクト選択
        selected_project_id = st.selectbox(
            "詳細を表示するプロジェクトを選択:",
            options=[p.project_id for p in projects],
            format_func=lambda x: next((p.name for p in projects if p.project_id == x), x),
            key="selected_project_id"
        )
        
        return selected_project_id
    
    return None


def project_detail_view(project_id):
    """
    プロジェクト詳細を表示するコンポーネント
    
    Parameters
    ----------
    project_id : str
        表示するプロジェクトのID
    """
    pm = initialize_project_manager()
    project = pm.get_project(project_id)
    
    if not project:
        st.error(f"プロジェクトID {project_id} が見つかりません。")
        return
    
    # プロジェクト情報の表示
    st.subheader(f"プロジェクト: {project.name}")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write(f"**説明**: {project.description}")
        st.write(f"**作成日時**: {datetime.fromisoformat(project.created_at).strftime('%Y-%m-%d %H:%M')}")
        st.write(f"**更新日時**: {datetime.fromisoformat(project.updated_at).strftime('%Y-%m-%d %H:%M')}")
        
        if project.tags:
            st.write("**タグ**:")
            st.write(", ".join(project.tags))
    
    with col2:
        # 各種アクションボタン
        if st.button("プロジェクトを編集", key=f"edit_project_{project.project_id}"):
            st.session_state.edit_project_id = project.project_id
        
        if st.button("プロジェクトを削除", key=f"delete_project_{project.project_id}"):
            st.session_state.delete_project_id = project.project_id
    
    # セッション一覧の表示
    st.write("### プロジェクトのセッション")
    sessions = pm.get_project_sessions(project_id)
    
    if not sessions:
        st.info("このプロジェクトにはまだセッションが追加されていません。")
    else:
        sessions_data = []
        for session in sessions:
            try:
                created_at = datetime.fromisoformat(session.created_at).strftime("%Y-%m-%d %H:%M")
            except:
                created_at = session.created_at
                
            try:
                updated_at = datetime.fromisoformat(session.updated_at).strftime("%Y-%m-%d %H:%M")
            except:
                updated_at = session.updated_at
            
            sessions_data.append({
                "セッション名": session.name,
                "説明": session.description,
                "作成日時": created_at,
                "更新日時": updated_at,
                "タグ": ", ".join(session.tags) if session.tags else "",
                "セッションID": session.session_id
            })
        
        # セッションデータフレームとして表示
        if sessions_data:
            df = pd.DataFrame(sessions_data)
            st.dataframe(
                df.drop(columns=["セッションID"]),
                use_container_width=True
            )
    
    # セッション管理セクション
    with st.expander("セッションの管理", expanded=False):
        # プロジェクトに追加可能なセッション一覧
        all_sessions = pm.get_sessions()
        # すでにプロジェクトに属しているセッションを除外
        available_sessions = [s for s in all_sessions if s.session_id not in project.sessions]
        
        if available_sessions:
            st.write("#### セッションの追加")
            
            selected_session_id = st.selectbox(
                "追加するセッションを選択:",
                options=[s.session_id for s in available_sessions],
                format_func=lambda x: next((s.name for s in available_sessions if s.session_id == x), x),
                key=f"add_session_select_{project.project_id}"
            )
            
            if st.button("セッションを追加", key=f"add_session_btn_{project.project_id}"):
                if pm.add_session_to_project(project.project_id, selected_session_id):
                    alert(f"セッションをプロジェクトに追加しました。", "success")
                    st.experimental_rerun()
                else:
                    alert("セッションの追加に失敗しました。", "error")
        else:
            st.info("追加可能なセッションがありません。セッション管理で新しいセッションを作成してください。")
        
        # セッションの削除
        if sessions:
            st.write("#### セッションの削除")
            
            session_to_remove = st.selectbox(
                "プロジェクトから削除するセッションを選択:",
                options=[s.session_id for s in sessions],
                format_func=lambda x: next((s.name for s in sessions if s.session_id == x), x),
                key=f"remove_session_select_{project.project_id}"
            )
            
            if st.button("セッションを削除", key=f"remove_session_btn_{project.project_id}"):
                if pm.remove_session_from_project(project.project_id, session_to_remove):
                    alert(f"セッションをプロジェクトから削除しました。", "success")
                    st.experimental_rerun()
                else:
                    alert("セッションの削除に失敗しました。", "error")


def create_project_form():
    """
    新規プロジェクト作成フォーム
    """
    with st.form("create_project_form"):
        st.write("### 新規プロジェクト作成")
        
        name = st.text_input("プロジェクト名 *", key="new_project_name")
        description = st.text_area("説明", key="new_project_description")
        
        # タグ入力（カンマ区切り）
        tags_input = st.text_input(
            "タグ (カンマ区切り)", 
            key="new_project_tags",
            help="複数のタグを入力する場合はカンマで区切ってください。例: 練習,レース,強風"
        )
        
        # 追加メタデータ（オプション）
        with st.expander("追加情報", expanded=False):
            location = st.text_input("場所", key="new_project_location")
            boat_type = st.text_input("艇種", key="new_project_boat_type")
            team = st.text_input("チーム", key="new_project_team")
            custom_field = st.text_input("その他情報", key="new_project_custom")
        
        submitted = st.form_submit_button("プロジェクトを作成")
        
        if submitted:
            if not name:
                alert("プロジェクト名は必須項目です。", "error")
                return
            
            # タグのリスト化
            tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
            
            # メタデータの設定
            metadata = {}
            if location:
                metadata["location"] = location
            if boat_type:
                metadata["boat_type"] = boat_type
            if team:
                metadata["team"] = team
            if custom_field:
                metadata["custom"] = custom_field
            
            # プロジェクトを作成
            pm = initialize_project_manager()
            new_project = pm.create_project(name, description, tags, metadata)
            
            if new_project:
                alert(f"プロジェクト「{name}」を作成しました。", "success")
                # フォーム入力をクリア
                for key in st.session_state.keys():
                    if key.startswith("new_project_"):
                        st.session_state[key] = ""
                # 画面を再表示
                st.experimental_rerun()
            else:
                alert("プロジェクトの作成に失敗しました。", "error")


def edit_project_form(project_id):
    """
    プロジェクト編集フォーム
    
    Parameters
    ----------
    project_id : str
        編集するプロジェクトのID
    """
    pm = initialize_project_manager()
    project = pm.get_project(project_id)
    
    if not project:
        st.error(f"プロジェクトID {project_id} が見つかりません。")
        return
    
    with st.form(f"edit_project_form_{project_id}"):
        st.write(f"### プロジェクト編集: {project.name}")
        
        # フォーム入力の初期化
        if f"edit_project_name_{project_id}" not in st.session_state:
            st.session_state[f"edit_project_name_{project_id}"] = project.name
        if f"edit_project_description_{project_id}" not in st.session_state:
            st.session_state[f"edit_project_description_{project_id}"] = project.description
        if f"edit_project_tags_{project_id}" not in st.session_state:
            st.session_state[f"edit_project_tags_{project_id}"] = ", ".join(project.tags) if project.tags else ""
        
        # 各種メタデータの初期化
        if f"edit_project_location_{project_id}" not in st.session_state:
            st.session_state[f"edit_project_location_{project_id}"] = project.metadata.get("location", "")
        if f"edit_project_boat_type_{project_id}" not in st.session_state:
            st.session_state[f"edit_project_boat_type_{project_id}"] = project.metadata.get("boat_type", "")
        if f"edit_project_team_{project_id}" not in st.session_state:
            st.session_state[f"edit_project_team_{project_id}"] = project.metadata.get("team", "")
        if f"edit_project_custom_{project_id}" not in st.session_state:
            st.session_state[f"edit_project_custom_{project_id}"] = project.metadata.get("custom", "")
        
        # 編集フォーム
        name = st.text_input("プロジェクト名 *", key=f"edit_project_name_{project_id}")
        description = st.text_area("説明", key=f"edit_project_description_{project_id}")
        
        # タグ入力（カンマ区切り）
        tags_input = st.text_input(
            "タグ (カンマ区切り)", 
            key=f"edit_project_tags_{project_id}",
            help="複数のタグを入力する場合はカンマで区切ってください。例: 練習,レース,強風"
        )
        
        # 追加メタデータ（オプション）
        with st.expander("追加情報", expanded=True):
            location = st.text_input("場所", key=f"edit_project_location_{project_id}")
            boat_type = st.text_input("艇種", key=f"edit_project_boat_type_{project_id}")
            team = st.text_input("チーム", key=f"edit_project_team_{project_id}")
            custom_field = st.text_input("その他情報", key=f"edit_project_custom_{project_id}")
        
        # ボタン
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("変更を保存")
        with col2:
            cancelled = st.form_submit_button("キャンセル")
        
        if submitted:
            if not name:
                alert("プロジェクト名は必須項目です。", "error")
                return
            
            # 元のプロジェクト情報を保持
            project.name = name
            project.description = description
            
            # タグのリスト化
            project.tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []
            
            # メタデータの更新
            if location:
                project.metadata["location"] = location
            elif "location" in project.metadata:
                del project.metadata["location"]
                
            if boat_type:
                project.metadata["boat_type"] = boat_type
            elif "boat_type" in project.metadata:
                del project.metadata["boat_type"]
                
            if team:
                project.metadata["team"] = team
            elif "team" in project.metadata:
                del project.metadata["team"]
                
            if custom_field:
                project.metadata["custom"] = custom_field
            elif "custom" in project.metadata:
                del project.metadata["custom"]
            
            # プロジェクトを更新
            if pm.update_project(project):
                alert(f"プロジェクト「{name}」を更新しました。", "success")
                # 編集モードを終了
                st.session_state.pop('edit_project_id', None)
                # 画面を再表示
                st.experimental_rerun()
            else:
                alert("プロジェクトの更新に失敗しました。", "error")
        
        elif cancelled:
            # 編集モードを終了
            st.session_state.pop('edit_project_id', None)
            st.experimental_rerun()


def delete_project_confirm(project_id):
    """
    プロジェクト削除の確認ダイアログ
    
    Parameters
    ----------
    project_id : str
        削除するプロジェクトのID
    """
    pm = initialize_project_manager()
    project = pm.get_project(project_id)
    
    if not project:
        st.error(f"プロジェクトID {project_id} が見つかりません。")
        return
    
    st.warning(f"プロジェクト「{project.name}」を削除しようとしています。この操作は元に戻せません。")
    
    # セッションも削除するかどうかのチェックボックス
    delete_sessions = st.checkbox(
        "関連するセッションも削除する", 
        value=False,
        help="チェックした場合、このプロジェクトに関連するセッションも削除されます。チェックしない場合、セッションはシステムに残りますが、このプロジェクトとの関連付けは解除されます。",
        key=f"delete_sessions_{project_id}"
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("はい、削除します", key=f"confirm_delete_{project_id}"):
            if pm.delete_project(project_id, delete_sessions):
                alert(f"プロジェクト「{project.name}」を削除しました。", "success")
                # 削除確認モードを終了
                st.session_state.pop('delete_project_id', None)
                # 画面を再表示
                st.experimental_rerun()
            else:
                alert("プロジェクトの削除に失敗しました。", "error")
    
    with col2:
        if st.button("キャンセル", key=f"cancel_delete_{project_id}"):
            # 削除確認モードを終了
            st.session_state.pop('delete_project_id', None)
            st.experimental_rerun()


def search_projects_form():
    """
    プロジェクト検索フォーム
    """
    pm = initialize_project_manager()
    
    st.write("### プロジェクト検索")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input(
            "検索キーワード", 
            key="search_project_query",
            help="プロジェクト名や説明に含まれるキーワードを入力してください"
        )
    
    with col2:
        search_button = st.button("検索", key="search_project_button")
    
    # タグによるフィルタリング
    all_tags = list(pm.get_project_tags())
    if all_tags:
        selected_tags = st.multiselect(
            "タグでフィルタ", 
            options=all_tags,
            key="search_project_tags"
        )
    else:
        selected_tags = []
    
    # 検索実行
    if search_button or search_query or selected_tags:
        if not search_query and not selected_tags:
            projects = pm.get_projects()
        else:
            projects = pm.search_projects(search_query, selected_tags)
        
        if not projects:
            st.info("検索条件に一致するプロジェクトがありません。")
        else:
            st.write(f"検索結果: {len(projects)}件のプロジェクトが見つかりました")
            
            # 検索結果の表示
            projects_data = []
            for project in projects:
                try:
                    created_at = datetime.fromisoformat(project.created_at).strftime("%Y-%m-%d %H:%M")
                except:
                    created_at = project.created_at
                    
                try:
                    updated_at = datetime.fromisoformat(project.updated_at).strftime("%Y-%m-%d %H:%M")
                except:
                    updated_at = project.updated_at
                
                projects_data.append({
                    "プロジェクト名": project.name,
                    "説明": project.description,
                    "セッション数": len(project.sessions),
                    "作成日時": created_at,
                    "更新日時": updated_at,
                    "タグ": ", ".join(project.tags) if project.tags else "",
                    "プロジェクトID": project.project_id
                })
            
            if projects_data:
                df = pd.DataFrame(projects_data)
                
                # 検索結果を表示
                st.dataframe(
                    df.drop(columns=["プロジェクトID"]),
                    use_container_width=True
                )
                
                # 詳細表示用のプロジェクト選択
                selected_project_id = st.selectbox(
                    "詳細を表示するプロジェクトを選択:",
                    options=[p.project_id for p in projects],
                    format_func=lambda x: next((p.name for p in projects if p.project_id == x), x),
                    key="search_result_select"
                )
                
                if selected_project_id:
                    st.session_state.selected_project_id = selected_project_id
                    st.experimental_rerun()
    

def project_manager_page():
    """
    プロジェクト管理ページのメイン関数
    """
    st.title("プロジェクト管理")
    
    # タブで分けて表示
    tabs = st.tabs(["プロジェクト一覧", "プロジェクト作成", "プロジェクト検索"])
    
    with tabs[0]:  # プロジェクト一覧タブ
        st.write("### プロジェクト一覧")
        
        # 編集または削除モードの場合
        if 'edit_project_id' in st.session_state:
            edit_project_form(st.session_state.edit_project_id)
        elif 'delete_project_id' in st.session_state:
            delete_project_confirm(st.session_state.delete_project_id)
        else:
            # 通常のプロジェクト一覧と詳細表示
            selected_project_id = project_list_view()
            
            if selected_project_id:
                st.markdown("---")
                project_detail_view(selected_project_id)
    
    with tabs[1]:  # プロジェクト作成タブ
        create_project_form()
    
    with tabs[2]:  # プロジェクト検索タブ
        search_projects_form()


if __name__ == "__main__":
    # Streamlitアプリとして直接実行される場合
    st.set_page_config(page_title="プロジェクト管理", layout="wide")
    project_manager_page()
