"""
ui.components.project.project_list

プロジェクト一覧を表示するコンポーネント
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, List

from ui.components.project.project_manager import initialize_project_manager
from sailing_data_processor.project.project_manager import Project


def project_list_view() -> Optional[str]:
    """
    プロジェクト一覧を表示するコンポーネント
    
    Returns
    -------
    Optional[str]
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


def search_projects(query: str = "", tags: Optional[List[str]] = None) -> List[Project]:
    """
    プロジェクトを検索する
    
    Parameters
    ----------
    query : str
        検索キーワード
    tags : Optional[List[str]]
        フィルタリングするタグのリスト
        
    Returns
    -------
    List[Project]
        検索結果のプロジェクトリスト
    """
    pm = initialize_project_manager()
    
    if not query and not tags:
        return pm.get_projects()
    else:
        return pm.search_projects(query, tags)
