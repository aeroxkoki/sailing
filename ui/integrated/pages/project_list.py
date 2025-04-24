# -*- coding: utf-8 -*-
"""
ui.integrated.pages.project_list

セーリング戦略分析システムのプロジェクト一覧ページ
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# 自作モジュールのインポート
from sailing_data_processor.project.project_manager import ProjectManager
from ui.components.project.project_manager import initialize_project_manager
from ui.integrated.components.search_filter import render_search_filter

def render_page():
    """
    プロジェクト一覧ページを表示する
    """
    # ヘッダー
    st.markdown("<div class='main-header'>プロジェクト一覧</div>", unsafe_allow_html=True)
    
    # 検索フィルターパネル
    with st.expander("検索とフィルター", expanded=False):
        search_query, selected_tags, apply_filter = render_search_filter()
    
    # プロジェクトマネージャーの初期化
    pm = initialize_project_manager()
    
    # プロジェクトの取得（検索/フィルタ条件がある場合は絞り込み）
    if apply_filter and (search_query or selected_tags):
        projects = pm.search_projects(search_query, selected_tags)
        st.info(f"検索条件に一致する {len(projects)} 件のプロジェクトが見つかりました。")
    else:
        projects = pm.get_projects()
    
    # プロジェクトがない場合
    if not projects:
        st.warning("プロジェクトがまだ作成されていません。新しいプロジェクトを作成してください。")
        
        # 新規プロジェクト作成ボタン
        st.button("新規プロジェクト作成", 
                 on_click=lambda: st.session_state.update({"current_page": "project_create"}),
                 use_container_width=True)
        return
    
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
            "説明": project.description[:50] + "..." if len(project.description) > 50 else project.description,
            "セッション数": session_count,
            "作成日時": created_at,
            "更新日時": updated_at,
            "タグ": ", ".join(project.tags) if project.tags else "",
            "プロジェクトID": project.project_id
        })
    
    # データフレームとして表示
    if projects_data:
        df = pd.DataFrame(projects_data)
        
        # アクション列を追加したデータフレームを作成
        st.dataframe(
            df.drop(columns=["プロジェクトID"]),
            use_container_width=True,
            column_config={
                "セッション数": st.column_config.NumberColumn(format="%d"),
            }
        )
    
    # プロジェクト操作セクション
    st.markdown("### プロジェクト操作")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        # プロジェクト選択
        selected_project_id = st.selectbox(
            "詳細を表示するプロジェクトを選択:",
            options=[p.project_id for p in projects],
            format_func=lambda x: next((p.name for p in projects if p.project_id == x), x),
        )
    
    with col2:
        # 詳細表示ボタン
        if st.button("詳細を表示", type="primary", use_container_width=True):
            st.session_state.selected_project_id = selected_project_id
            st.session_state.current_page = "project_detail"
            st.rerun()
            
    with col3:
        # 新規プロジェクト作成ボタン
        if st.button("新規作成", use_container_width=True):
            st.session_state.current_page = "project_create"
            st.rerun()
    
    # 統計情報
    st.markdown("### プロジェクト統計")
    
    stat1, stat2, stat3, stat4 = st.columns(4)
    
    # 全プロジェクト数
    with stat1:
        st.metric("プロジェクト数", len(projects))
    
    # セッション総数
    total_sessions = sum(len(p.sessions) for p in projects)
    with stat2:
        st.metric("セッション総数", total_sessions)
    
    # 直近1週間の更新数（仮の実装）
    recent_updates = 0  # 実際には日付比較で算出
    with stat3:
        st.metric("最近の更新", recent_updates)
    
    # タグの種類数
    all_tags = set()
    for p in projects:
        if p.tags:
            all_tags.update(p.tags)
            
    with stat4:
        st.metric("タグの種類", len(all_tags))
    
    # タグクラウド（簡易版）
    if all_tags:
        st.markdown("### タグ一覧")
        tags_html = " ".join([f"<span style='background-color: #E3F2FD; padding: 5px 10px; margin: 5px; border-radius: 15px;'>{tag}</span>" for tag in all_tags])
        st.markdown(f"<div style='line-height: 2.5;'>{tags_html}</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    render_page()
