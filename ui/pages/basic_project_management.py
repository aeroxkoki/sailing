# -*- coding: utf-8 -*-
"""
ui.pages.basic_project_management

プロジェクト管理の基本的なUIを提供するページ
"""

import streamlit as st
from typing import Optional, Dict, Any, List
import time

from ui.components.project.project_manager import initialize_project_manager
from ui.components.project.project_list import project_list_view
from ui.components.project.project_details import project_details_view
from ui.components.project.project_form import project_form, create_or_update_project
from sailing_data_processor.project.project_model import Project


def render_page():
    """
    プロジェクト管理ページを表示する
    """
    st.title("プロジェクト管理")
    
    # プロジェクトマネージャーの初期化
    pm = initialize_project_manager()
    
    # セッション状態の初期化
    if "current_tab" not in st.session_state:
        st.session_state["current_tab"] = "project_list"
    
    # サイドバーのナビゲーション
    with st.sidebar:
        st.header("プロジェクト管理")
        
        # タブ選択ボタン
        st.button("プロジェクト一覧", 
                 on_click=set_tab, 
                 args=("project_list",),
                 use_container_width=True,
                 type="primary" if st.session_state["current_tab"] == "project_list" else "secondary")
        
        st.button("新規プロジェクト作成", 
                 on_click=set_tab, 
                 args=("project_create",),
                 use_container_width=True,
                 type="primary" if st.session_state["current_tab"] == "project_create" else "secondary")
        
        # 選択中のプロジェクトがある場合、そのプロジェクト詳細へのボタンを表示
        if "selected_project_id" in st.session_state:
            project = pm.get_project(st.session_state["selected_project_id"])
            if project:
                st.button(f"プロジェクト: {project.name}", 
                         on_click=set_tab, 
                         args=("project_details",),
                         use_container_width=True,
                         type="primary" if st.session_state["current_tab"] == "project_details" else "secondary")
        
        # プロジェクト検索
        st.subheader("プロジェクト検索")
        search_query = st.text_input("検索キーワード", key="search_query")
        
        all_tags = sorted(list(pm.get_all_tags()))
        selected_tags = st.multiselect("タグで絞り込み", options=all_tags, key="selected_tags")
        
        if search_query or selected_tags:
            if st.button("検索", key="search_button", use_container_width=True):
                # 検索処理
                st.session_state["search_results"] = pm.search_projects(search_query, selected_tags)
                st.session_state["current_tab"] = "search_results"
    
    # メインコンテンツ領域
    current_tab = st.session_state["current_tab"]
    
    if current_tab == "project_list":
        render_project_list()
    elif current_tab == "project_create":
        render_project_create()
    elif current_tab == "project_details":
        render_project_details()
    elif current_tab == "project_edit":
        render_project_edit()
    elif current_tab == "search_results":
        render_search_results()


def set_tab(tab_name: str):
    """
    表示するタブを設定する
    
    Parameters
    ----------
    tab_name : str
        タブ名
    """
    st.session_state["current_tab"] = tab_name


def render_project_list():
    """
    プロジェクト一覧ページを表示する
    """
    st.subheader("プロジェクト一覧")
    
    selected_project_id = project_list_view()
    
    if selected_project_id:
        st.session_state["selected_project_id"] = selected_project_id
        st.session_state["current_tab"] = "project_details"
        st.rerun()


def render_project_create():
    """
    プロジェクト作成ページを表示する
    """
    st.subheader("新規プロジェクト作成")
    
    # プロジェクト作成フォームの表示
    project_data = project_form()
    
    if project_data:
        # プロジェクトの作成
        project = create_or_update_project(project_data, is_edit_mode=False)
        
        if project:
            # 作成成功
            st.session_state["selected_project_id"] = project.project_id
            st.session_state["current_tab"] = "project_details"
            st.rerun()


def render_project_details():
    """
    プロジェクト詳細ページを表示する
    """
    if "selected_project_id" not in st.session_state:
        st.error("プロジェクトが選択されていません。")
        st.session_state["current_tab"] = "project_list"
        st.rerun()
        return
    
    project_id = st.session_state["selected_project_id"]
    edit_clicked, selected_session_id = project_details_view(project_id)
    
    if edit_clicked:
        st.session_state["current_tab"] = "project_edit"
        st.rerun()
    
    if selected_session_id:
        st.session_state["selected_session_id"] = selected_session_id
        st.session_state["current_tab"] = "session_details"
        st.rerun()


def render_project_edit():
    """
    プロジェクト編集ページを表示する
    """
    st.subheader("プロジェクト編集")
    
    if "selected_project_id" not in st.session_state:
        st.error("編集するプロジェクトが選択されていません。")
        st.session_state["current_tab"] = "project_list"
        st.rerun()
        return
    
    # プロジェクトマネージャーの初期化
    pm = initialize_project_manager()
    
    # 選択中のプロジェクトを取得
    project_id = st.session_state["selected_project_id"]
    project = pm.get_project(project_id)
    
    if not project:
        st.error(f"プロジェクト ID: {project_id} が見つかりません。")
        st.session_state["current_tab"] = "project_list"
        st.rerun()
        return
    
    # プロジェクト編集フォームの表示
    project_data = project_form(project, key_prefix="edit")
    
    if project_data:
        # 戻るボタンが押された場合
        if project_data == "back":
            st.session_state["current_tab"] = "project_details"
            st.rerun()
            return
        
        # プロジェクトの更新
        project_data["project_id"] = project_id
        updated_project = create_or_update_project(project_data, is_edit_mode=True)
        
        if updated_project:
            # 更新成功
            st.session_state["current_tab"] = "project_details"
            st.rerun()


def render_search_results():
    """
    検索結果ページを表示する
    """
    st.subheader("検索結果")
    
    if "search_results" not in st.session_state:
        st.info("検索結果がありません。")
        return
    
    search_results = st.session_state["search_results"]
    
    if not search_results:
        st.info("条件に一致するプロジェクトが見つかりませんでした。")
        return
    
    # 検索結果の表示
    st.write(f"{len(search_results)}件のプロジェクトが見つかりました。")
    
    for project in search_results:
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(project.name)
                st.write(project.description)
                st.write(f"タグ: {', '.join(project.tags) if project.tags else '-'}")
            
            with col2:
                if st.button("詳細を表示", key=f"view_{project.project_id}"):
                    st.session_state["selected_project_id"] = project.project_id
                    st.session_state["current_tab"] = "project_details"
                    st.rerun()
            
            st.divider()


if __name__ == "__main__":
    render_page()
