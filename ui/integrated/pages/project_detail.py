# -*- coding: utf-8 -*-
"""
ui.integrated.pages.project_detail

セーリング戦略分析システムのプロジェクト詳細ページ
"""

import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# 自作モジュールのインポート
from ui.components.project.project_manager import initialize_project_manager

def render_page(project_id):
    """
    プロジェクト詳細ページを表示する
    
    Parameters
    ----------
    project_id : str
        表示するプロジェクトのID
    """
    # プロジェクトマネージャーの初期化
    pm = initialize_project_manager()
    
    # プロジェクトを取得
    project = pm.get_project(project_id)
    
    if not project:
        st.error(f"プロジェクトID {project_id} が見つかりません。")
        
        if st.button("プロジェクト一覧に戻る", use_container_width=True):
            st.session_state.current_page = "projects"
            st.rerun()
        return
    
    # ヘッダー：プロジェクト名
    st.markdown(f"<div class='main-header'>{project.name}</div>", unsafe_allow_html=True)
    
    # プロジェクト情報セクション
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        # 左側：プロジェクト詳細情報
        with col1:
            # 基本情報
            st.markdown("### 基本情報")
            
            # 説明文
            st.markdown(f"**説明**: {project.description}")
            
            # 作成日と更新日
            try:
                created_at = datetime.fromisoformat(project.created_at).strftime("%Y-%m-%d %H:%M")
            except:
                created_at = project.created_at
                
            try:
                updated_at = datetime.fromisoformat(project.updated_at).strftime("%Y-%m-%d %H:%M")
            except:
                updated_at = project.updated_at
                
            st.markdown(f"**作成日時**: {created_at}")
            st.markdown(f"**更新日時**: {updated_at}")
            
            # タグ
            if project.tags:
                tags_html = " ".join([f"<span style='background-color: #E3F2FD; padding: 5px 10px; margin: 5px; border-radius: 15px;'>{tag}</span>" for tag in project.tags])
                st.markdown("**タグ**:", unsafe_allow_html=True)
                st.markdown(f"<div style='line-height: 2.5;'>{tags_html}</div>", unsafe_allow_html=True)
                
            # メタデータ（追加情報）
            if project.metadata:
                st.markdown("### 追加情報")
                
                for key, value in project.metadata.items():
                    if value:  # 空でない場合のみ表示
                        st.markdown(f"**{key}**: {value}")
        
        # 右側：アクションパネル
        with col2:
            st.markdown("### アクション")
            
            st.button("プロジェクトを編集", 
                     key="edit_project_btn",
                     use_container_width=True,
                     on_click=lambda: st.session_state.update({"current_page": "project_edit"}))
            
            st.button("セッションを追加", 
                     key="add_session_btn",
                     use_container_width=True,
                     on_click=lambda: st.session_state.update({"current_page": "session_add"}))
            
            # 削除ボタン（確認ダイアログ付き）
            if "confirm_delete" not in st.session_state:
                st.session_state.confirm_delete = False
                
            if st.session_state.confirm_delete:
                st.warning("このプロジェクトを削除してもよろしいですか？この操作は元に戻せません。")
                
                delete_sessions = st.checkbox("関連するセッションも削除する", 
                                           value=False,
                                           help="チェックすると、このプロジェクトに関連付けられたセッションも削除されます。")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("はい、削除します", type="primary", use_container_width=True):
                        if pm.delete_project(project_id, delete_sessions):
                            st.success(f"プロジェクト「{project.name}」を削除しました。")
                            # セッション状態をクリアして一覧に戻る
                            st.session_state.selected_project_id = None
                            st.session_state.confirm_delete = False
                            st.session_state.current_page = "projects"
                            st.rerun()
                        else:
                            st.error("プロジェクトの削除に失敗しました。")
                
                with col2:
                    if st.button("キャンセル", use_container_width=True):
                        st.session_state.confirm_delete = False
                        st.rerun()
            else:
                if st.button("プロジェクトを削除", 
                           key="delete_project_btn",
                           use_container_width=True,
                           type="secondary"):
                    st.session_state.confirm_delete = True
                    st.rerun()
    
    # セッションセクション
    st.markdown("### プロジェクトのセッション")
    
    # セッション一覧
    sessions = pm.get_project_sessions(project_id)
    
    if not sessions:
        st.info("このプロジェクトにはまだセッションが追加されていません。")
        
        # セッション追加ボタン
        if st.button("新しいセッションを追加", key="add_session_empty_btn"):
            st.session_state.current_page = "session_add"
            st.rerun()
    else:
        # セッションのデータフレームを作成
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
                "説明": session.description[:50] + "..." if len(session.description) > 50 else session.description,
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
        
        # セッション選択
        selected_session_id = st.selectbox(
            "表示するセッションを選択:",
            options=[s.session_id for s in sessions],
            format_func=lambda x: next((s.name for s in sessions if s.session_id == x), x),
        )
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("セッション詳細を表示", type="primary", use_container_width=True):
                st.session_state.selected_session_id = selected_session_id
                st.session_state.current_page = "session_detail"
                st.rerun()
        
        with col2:
            if st.button("データ分析を開始", use_container_width=True):
                st.session_state.selected_session_id = selected_session_id
                st.session_state.current_page = "wind_analysis"  # 風向風速分析ページに遷移
                st.rerun()
        
        with col3:
            if st.button("結果を表示", use_container_width=True):
                st.session_state.selected_session_id = selected_session_id
                st.session_state.current_page = "map_view"  # マップビューページに遷移
                st.rerun()
    
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
                key="add_session_select"
            )
            
            if st.button("セッションを追加", key="add_session_btn_detail"):
                if pm.add_session_to_project(project.project_id, selected_session_id):
                    st.success("セッションをプロジェクトに追加しました。")
                    st.rerun()
                else:
                    st.error("セッションの追加に失敗しました。")
        else:
            st.info("追加可能なセッションがありません。セッション管理で新しいセッションを作成してください。")
        
        # セッションの削除
        if sessions:
            st.write("#### セッションの削除")
            
            session_to_remove = st.selectbox(
                "プロジェクトから削除するセッションを選択:",
                options=[s.session_id for s in sessions],
                format_func=lambda x: next((s.name for s in sessions if s.session_id == x), x),
                key="remove_session_select"
            )
            
            if st.button("セッションを削除", key="remove_session_btn"):
                if pm.remove_session_from_project(project.project_id, session_to_remove):
                    st.success("セッションをプロジェクトから削除しました。")
                    st.rerun()
                else:
                    st.error("セッションの削除に失敗しました。")
    
    # 戻るボタン
    st.markdown("---")
    if st.button("プロジェクト一覧に戻る", use_container_width=True):
        st.session_state.current_page = "projects"
        st.rerun()

if __name__ == "__main__":
    # テスト用のプロジェクトID
    test_project_id = "test_project_id"  # これは実際のIDに置き換える必要がある
    render_page(test_project_id)
