# -*- coding: utf-8 -*-
"""
ui.components.session.session_assignment

セッション割り当てのUIコンポーネント
"""

import streamlit as st
from typing import Optional, List, Dict, Any, Callable
import pandas as pd
import copy

from sailing_data_processor.project.project_manager import ProjectManager, Project, Session
from sailing_data_processor.session.session_manager import SessionManager


def session_assignment_view(project_manager: ProjectManager,
                           session_manager: SessionManager,
                           project_id: Optional[str] = None) -> bool:
    """
    セッションの割り当て画面
    
    Parameters
    ----------
    project_manager : ProjectManager
        プロジェクト管理クラスのインスタンス
    session_manager : SessionManager
        セッション管理クラスのインスタンス
    project_id : Optional[str], optional
        割り当て先のプロジェクトID (指定されない場合は選択UI表示), by default None
        
    Returns
    -------
    bool
        割り当て処理が実行された場合True
    """
    if not project_id:
        # プロジェクトの選択UI
        projects = project_manager.get_projects()
        
        if not projects:
            st.info("先にプロジェクトを作成してください。")
            return False
        
        project_options = {p.project_id: p.name for p in projects}
        selected_project_id = st.selectbox(
            "セッションを割り当てるプロジェクトを選択:",
            options=list(project_options.keys()),
            format_func=lambda x: project_options[x],
            key="assign_to_project"
        )
        
        project_id = selected_project_id
    
    # プロジェクトの取得
    project = project_manager.get_project(project_id)
    if not project:
        st.error(f"プロジェクトが見つかりません: {project_id}")
        return False
    
    st.header(f"セッション割り当て: {project.name}")
    st.markdown("このページでは、プロジェクトへのセッションの追加、削除、移動ができます。")
    
    # セッション状態の初期化
    if "session_assignment_tab" not in st.session_state:
        st.session_state.session_assignment_tab = "現在のセッション"
    
    # タブ作成
    tabs = st.tabs(["現在のセッション", "追加可能なセッション", "セッション移動"])
    tab_index = ["現在のセッション", "追加可能なセッション", "セッション移動"].index(st.session_state.session_assignment_tab)
    
    # 現在のプロジェクトに含まれるセッションを取得
    current_sessions = session_manager.get_project_sessions(project_id)
    
    # タブ1: 現在のセッション
    with tabs[0]:
        st.session_state.session_assignment_tab = "現在のセッション"
        st.subheader("現在のセッション")
        
        if not current_sessions:
            st.info("このプロジェクトにはまだセッションがありません。")
        else:
            # 現在のセッションの表示
            sessions_data = []
            for session in current_sessions:
                # タグの表示形式を調整
                tags_str = ", ".join(session.tags) if session.tags else ""
                
                sessions_data.append({
                    "セッション名": session.name,
                    "説明": session.description[:30] + "..." if len(session.description) > 30 else session.description,
                    "タグ": tags_str,
                    "ステータス": session.status,
                    "イベント日": session.metadata.get("event_date", ""),
                    "セッションID": session.session_id
                })
            
            # データフレームとして表示
            current_df = pd.DataFrame(sessions_data)
            
            # インタラクティブな表示と選択
            with st.container():
                st.markdown("#### 以下のセッションがプロジェクトに含まれています")
                
                # 表示列の設定
                display_columns = ["セッション名", "説明", "タグ", "ステータス", "イベント日"]
                
                # データテーブルとして表示（選択可能）
                selection = st.data_editor(
                    current_df[display_columns],
                    hide_index=True,
                    use_container_width=True,
                    key="current_sessions_table"
                )
                
                st.markdown("#### セッション操作")
                
                # セッションの選択
                remove_session_ids = st.multiselect(
                    "プロジェクトから削除するセッションを選択:",
                    options=[s.session_id for s in current_sessions],
                    format_func=lambda x: next((s.name for s in current_sessions if s.session_id == x), x),
                    key="remove_sessions"
                )
                
                # 削除ボタン
                col1, col2 = st.columns([1, 3])
                with col1:
                    if remove_session_ids and st.button("削除", key="remove_sessions_btn", use_container_width=True):
                        success_count = 0
                        for session_id in remove_session_ids:
                            if project_manager.remove_session_from_project(project_id, session_id):
                                success_count += 1
                        
                        if success_count > 0:
                            st.success(f"{success_count}個のセッションをプロジェクトから削除しました。")
                            st.rerun()  # UIを更新
                        else:
                            st.error("セッションの削除に失敗しました。")
                
                # セッションの詳細表示へのリンク
                with col2:
                    if remove_session_ids and len(remove_session_ids) == 1:
                        if st.button("詳細表示", key="view_session_details", use_container_width=True):
                            st.session_state.selected_session_id = remove_session_ids[0]
                            st.session_state.session_management_tab = "詳細"
                            st.rerun()
    
    # タブ2: 追加可能なセッション
    with tabs[1]:
        st.session_state.session_assignment_tab = "追加可能なセッション"
        st.subheader("追加可能なセッション")
    
        # 現在のプロジェクトに含まれていないセッションを取得
        available_sessions = session_manager.get_sessions_not_in_project(project_id)
    
        if not available_sessions:
            st.info("追加可能なセッションがありません。")
        else:
            # フィルタリング
            with st.expander("検索フィルター"):
                col1, col2 = st.columns(2)
                
                with col1:
                    search_query = st.text_input("セッション名で検索:", key="search_available_sessions")
                    
                    # タグによるフィルタリング
                    all_tags = session_manager.get_available_tags()
                    filter_tags = st.multiselect(
                        "タグでフィルタリング:",
                        options=all_tags,
                        key="filter_available_sessions_tags"
                    )
                
                with col2:
                    statuses = ["", "new", "validated", "analyzed", "completed"]
                    status_filter = st.selectbox(
                        "ステータス:",
                        options=statuses,
                        key="filter_available_sessions_status"
                    )
                    
                    categories = ["", "general", "race", "training", "analysis", "other"]
                    category_filter = st.selectbox(
                        "カテゴリ:",
                        options=categories,
                        key="filter_available_sessions_category"
                    )
                
                apply_filter = st.button("フィルター適用", key="apply_available_filter", use_container_width=True)
            
            # フィルタリング適用
            filtered_available_sessions = available_sessions
            if apply_filter and (search_query or filter_tags or status_filter or category_filter):
                # 検索条件の準備
                advanced_filters = {}
                if status_filter:
                    advanced_filters["status"] = status_filter
                if category_filter:
                    advanced_filters["category"] = category_filter
                
                filtered_session_ids = session_manager.search_sessions(
                    query=search_query,
                    tags=filter_tags if filter_tags else None,
                    **advanced_filters
                )
                
                # プロジェクトに含まれていないセッションのみに絞り込み
                filtered_available_sessions = [
                    session for session in available_sessions 
                    if session.session_id in filtered_session_ids
                ]
            
            # 利用可能なセッションの表示
            sessions_to_add = []
            for session in filtered_available_sessions:
                # タグの表示形式を調整
                tags_str = ", ".join(session.tags) if session.tags else ""
                
                # イベント日を取得
                event_date = session.metadata.get("event_date", "")
                
                sessions_to_add.append({
                    "セッション名": session.name,
                    "説明": session.description[:30] + "..." if len(session.description) > 30 else session.description,
                    "タグ": tags_str,
                    "ステータス": session.status,
                    "カテゴリ": session.category or "",
                    "イベント日": event_date,
                    "セッションID": session.session_id
                })
            
            # データフレームとして表示
            available_df = pd.DataFrame(sessions_to_add) if sessions_to_add else pd.DataFrame()
            
            if available_df.empty:
                st.info("フィルター条件に一致するセッションがありません。")
            else:
                # 表示列の設定
                display_columns = ["セッション名", "説明", "タグ", "ステータス", "カテゴリ", "イベント日"]
                
                # インタラクティブな表示
                st.markdown("#### 以下のセッションをプロジェクトに追加できます")
                st.data_editor(
                    available_df[display_columns],
                    hide_index=True,
                    use_container_width=True,
                    key="available_sessions_table"
                )
                
                st.markdown("#### セッション追加")
                
                # セッションの追加機能
                # 追加するセッションの選択
                add_session_ids = st.multiselect(
                    "プロジェクトに追加するセッションを選択:",
                    options=[s.session_id for s in filtered_available_sessions],
                    format_func=lambda x: next((s.name for s in filtered_available_sessions if s.session_id == x), x),
                    key="add_sessions"
                )
                
                # 追加ボタン
                st.markdown("")  # スペース追加
                if add_session_ids and st.button("選択したセッションをプロジェクトに追加", key="add_sessions_btn", use_container_width=True):
                    success_count = 0
                    for session_id in add_session_ids:
                        if project_manager.add_session_to_project(project_id, session_id):
                            success_count += 1
                    
                    if success_count > 0:
                        st.success(f"{success_count}個のセッションをプロジェクトに追加しました。")
                        st.rerun()  # UIを更新
                    else:
                        st.error("セッションの追加に失敗しました。")
    
    # タブ3: セッション移動
    with tabs[2]:
        st.session_state.session_assignment_tab = "セッション移動"
        st.subheader("セッション移動")
        
        # Visual project-to-project transfer
        st.markdown("#### プロジェクト間でセッションを移動")
        
        # プロジェクトリストの取得
        all_projects = project_manager.get_projects()
        other_projects = [p for p in all_projects if p.project_id != project_id]
        
        if not other_projects:
            st.info("他のプロジェクトがありません。移動するには最低2つのプロジェクトが必要です。")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**現在のプロジェクト: {project.name}**")
                
                if not current_sessions:
                    st.info("このプロジェクトにはセッションがありません。")
                else:
                    # 移動するセッションの選択
                    move_from_ids = st.multiselect(
                        "移動するセッションを選択:",
                        options=[s.session_id for s in current_sessions],
                        format_func=lambda x: next((s.name for s in current_sessions if s.session_id == x), x),
                        key="move_from_sessions"
                    )
            
            with col2:
                st.markdown("**移動先プロジェクト**")
                
                # 移動先プロジェクトの選択
                target_project_id = st.selectbox(
                    "移動先を選択:",
                    options=[p.project_id for p in other_projects],
                    format_func=lambda x: next((p.name for p in other_projects if p.project_id == x), x),
                    key="move_target_project"
                )
                
                # 移動先プロジェクトの情報表示
                target_project = project_manager.get_project(target_project_id)
                if target_project:
                    st.markdown(f"**説明**: {target_project.description[:50]}..." if len(target_project.description) > 50 else f"**説明**: {target_project.description}")
            
            # 中央に移動ボタン
            if move_from_ids and st.button("→ 選択したセッションを移動 →", key="move_sessions_btn", use_container_width=True):
                success_count = 0
                for session_id in move_from_ids:
                    if session_manager.move_session(session_id, project_id, target_project_id):
                        success_count += 1
                
                if success_count > 0:
                    st.success(f"{success_count}個のセッションを移動しました。")
                    st.rerun()  # UIを更新
                else:
                    st.error("セッションの移動に失敗しました。")
            
            # 逆方向の移動
            st.markdown("---")
            st.markdown("#### 他のプロジェクトからセッションを移動")
            
            source_project_id = st.selectbox(
                "移動元プロジェクト:",
                options=[p.project_id for p in other_projects],
                format_func=lambda x: next((p.name for p in other_projects if p.project_id == x), x),
                key="move_source_project"
            )
            
            # 移動元プロジェクトのセッションを取得
            source_sessions = session_manager.get_project_sessions(source_project_id)
            
            if not source_sessions:
                st.info("移動元プロジェクトにはセッションがありません。")
            else:
                # 移動元プロジェクトのセッションを表示
                source_data = []
                for session in source_sessions:
                    # タグの表示形式を調整
                    tags_str = ", ".join(session.tags) if session.tags else ""
                    
                    source_data.append({
                        "セッション名": session.name,
                        "説明": session.description[:30] + "..." if len(session.description) > 30 else session.description,
                        "タグ": tags_str,
                        "セッションID": session.session_id
                    })
                
                # データテーブル表示
                st.markdown(f"**移動元プロジェクトのセッション: {project_manager.get_project(source_project_id).name}**")
                source_df = pd.DataFrame(source_data)
                
                # 表示列の設定
                display_columns = ["セッション名", "説明", "タグ"]
                
                st.dataframe(
                    source_df[display_columns],
                    hide_index=True,
                    use_container_width=True
                )
                
                # 移動するセッションの選択
                move_to_ids = st.multiselect(
                    "移動するセッションを選択:",
                    options=[s.session_id for s in source_sessions],
                    format_func=lambda x: next((s.name for s in source_sessions if s.session_id == x), x),
                    key="move_to_sessions"
                )
                
                # 移動ボタン
                if move_to_ids and st.button("選択したセッションを現在のプロジェクトに移動", key="move_to_btn", use_container_width=True):
                    success_count = 0
                    for session_id in move_to_ids:
                        if session_manager.move_session(session_id, source_project_id, project_id):
                            success_count += 1
                    
                    if success_count > 0:
                        st.success(f"{success_count}個のセッションを移動しました。")
                        st.rerun()  # UIを更新
                    else:
                        st.error("セッションの移動に失敗しました。")
    
    return True


def session_bulk_assignment(project_manager: ProjectManager,
                           session_manager: SessionManager) -> bool:
    """
    セッションの一括割り当て画面
    複数のセッションを複数のプロジェクトに一括で割り当てる
    
    Parameters
    ----------
    project_manager : ProjectManager
        プロジェクト管理クラスのインスタンス
    session_manager : SessionManager
        セッション管理クラスのインスタンス
        
    Returns
    -------
    bool
        割り当て処理が実行された場合True
    """
    st.subheader("セッションの一括割り当て")
    st.markdown("複数のセッションを複数のプロジェクトに一度に割り当てるための画面です。")
    
    # セッション検索と選択
    st.markdown("### ステップ1: セッションを選択")
    
    all_sessions = session_manager.get_all_sessions()
    
    if not all_sessions:
        st.info("セッションがありません。先にデータをインポートしてください。")
        return False
    
    # セッションのフィルタリング
    with st.expander("セッション検索", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_input("検索キーワード:", key="bulk_session_search")
            
            all_tags = session_manager.get_available_tags()
            selected_tags = st.multiselect(
                "タグ:",
                options=all_tags,
                key="bulk_session_tags"
            )
        
        with col2:
            statuses = ["", "new", "validated", "analyzed", "completed"]
            status_filter = st.selectbox(
                "ステータス:",
                options=statuses,
                key="bulk_filter_status"
            )
            
            categories = ["", "general", "race", "training", "analysis", "other"]
            category_filter = st.selectbox(
                "カテゴリ:",
                options=categories,
                key="bulk_filter_category"
            )
            
        col1, col2 = st.columns([3, 1])
        with col1:
            apply_filter = st.button("フィルター適用", key="bulk_apply_filter", use_container_width=True)
        with col2:
            clear_filter = st.button("クリア", key="bulk_clear_filter", use_container_width=True)
    
    # フィルタリングクリア
    if clear_filter:
        # すべてのフィルター関連のセッション状態をクリア
        for key in list(st.session_state.keys()):
            if key.startswith("bulk_filter_") or key in ["bulk_session_search", "bulk_session_tags"]:
                if key in st.session_state:
                    del st.session_state[key]
        st.rerun()
    
    # フィルタリング適用
    filtered_sessions = all_sessions
    if apply_filter and (search_query or selected_tags or status_filter or category_filter):
        # 検索条件の準備
        advanced_filters = {}
        if status_filter:
            advanced_filters["status"] = status_filter
        if category_filter:
            advanced_filters["category"] = category_filter
        
        session_ids = session_manager.search_sessions(
            query=search_query,
            tags=selected_tags if selected_tags else None,
            **advanced_filters
        )
        
        filtered_sessions = [
            session for session in all_sessions 
            if session.session_id in session_ids
        ]
    
    # フィルタリング結果の表示
    if not filtered_sessions:
        st.warning("条件に一致するセッションがありません。フィルター条件を変更してください。")
    else:
        # セッションデータの表示
        session_data = []
        for session in filtered_sessions:
            # タグの表示形式を調整
            tags_str = ", ".join(session.tags) if session.tags else ""
            
            session_data.append({
                "セッション名": session.name,
                "説明": session.description[:30] + "..." if len(session.description) > 30 else session.description,
                "タグ": tags_str,
                "ステータス": session.status,
                "カテゴリ": session.category or "",
                "セッションID": session.session_id
            })
        
        # データフレーム表示
        st.markdown("#### 検索結果")
        session_df = pd.DataFrame(session_data)
        
        # 表示列の設定
        display_columns = ["セッション名", "説明", "タグ", "ステータス", "カテゴリ"]
        
        st.dataframe(
            session_df[display_columns],
            hide_index=True,
            use_container_width=True
        )
        
        # セッションの選択
        st.markdown("#### 割り当て対象のセッション選択")
        
        # 選択オプション
        selection_method = st.radio(
            "選択方法:",
            options=["個別選択", "すべて選択", "フィルター結果をすべて選択"],
            horizontal=True,
            key="bulk_selection_method"
        )
        
        if selection_method == "すべて選択":
            selected_session_ids = [s.session_id for s in all_sessions]
        elif selection_method == "フィルター結果をすべて選択":
            selected_session_ids = [s.session_id for s in filtered_sessions]
        else:
            # 個別選択
            selected_session_ids = st.multiselect(
                "割り当てるセッションを選択:",
                options=[s.session_id for s in filtered_sessions],
                format_func=lambda x: next((s.name for s in filtered_sessions if s.session_id == x), x),
                key="bulk_selected_sessions"
            )
        
        if not selected_session_ids:
            st.info("割り当てるセッションを選択してください。")
            return False
        
        st.success(f"{len(selected_session_ids)}個のセッションが選択されています。")
    
        # プロジェクト選択
        st.markdown("### ステップ2: 割り当て先プロジェクトを選択")
        
        all_projects = project_manager.get_projects()
        
        if not all_projects:
            st.info("先にプロジェクトを作成してください。")
            return False
        
        # プロジェクトの表示
        project_data = []
        for project in all_projects:
            # セッション数を計算
            session_count = len(project.sessions) if project.sessions else 0
            
            project_data.append({
                "プロジェクト名": project.name,
                "説明": project.description[:50] + "..." if len(project.description) > 50 else project.description,
                "セッション数": session_count,
                "作成日": project.created_at,
                "プロジェクトID": project.project_id
            })
        
        # データフレーム表示
        project_df = pd.DataFrame(project_data)
        
        # 表示列の設定
        display_columns = ["プロジェクト名", "説明", "セッション数", "作成日"]
        
        st.dataframe(
            project_df[display_columns],
            hide_index=True,
            use_container_width=True
        )
        
        # プロジェクト選択用のマルチセレクト
        selected_project_ids = st.multiselect(
            "割り当て先のプロジェクトを選択:",
            options=[p.project_id for p in all_projects],
            format_func=lambda x: next((p.name for p in all_projects if p.project_id == x), x),
            key="bulk_selected_projects"
        )
        
        if not selected_project_ids:
            st.info("割り当て先のプロジェクトを選択してください。")
            return False
        
        # 割り当てモードの選択
        st.markdown("### ステップ3: 割り当てオプションを選択")
        
        assignment_mode = st.radio(
            "割り当てモード:",
            options=["追加", "移動 (現在の割り当てを解除して新しく割り当て)"],
            horizontal=True,
            key="bulk_assignment_mode"
        )
        
        is_move_mode = assignment_mode.startswith("移動")
        
        # サマリー表示
        st.markdown("### 操作サマリー")
        st.markdown(f"**{len(selected_session_ids)}個**のセッションを**{len(selected_project_ids)}個**のプロジェクトに**{assignment_mode}**します。")
        
        if is_move_mode:
            st.warning("移動モードでは、選択したセッションの現在の割り当てが解除され、新しく選択したプロジェクトにのみ割り当てられます。")
        
        # 割り当て実行ボタン
        if st.button("割り当てを実行", key="execute_bulk_assignment", use_container_width=True):
            success_count = 0
            session_count = len(selected_session_ids)
            project_count = len(selected_project_ids)
            
            # プログレスバーの表示
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                if is_move_mode:
                    # 現在の割り当てを解除
                    status_text.text("現在の割り当てを解除中...")
                    
                    for i, session_id in enumerate(selected_session_ids):
                        # セッションが割り当てられているすべてのプロジェクトを取得
                        for project in all_projects:
                            if session_id in project.sessions:
                                # 選択されたプロジェクトでない場合は削除
                                if project.project_id not in selected_project_ids:
                                    project_manager.remove_session_from_project(project.project_id, session_id)
                        
                        # プログレスバーの更新
                        progress_percent = (i + 1) / (session_count * 2)  # 解除と追加の2段階
                        progress_bar.progress(progress_percent)
                
                # 新しい割り当てを実行
                status_text.text("新しい割り当てを実行中...")
                
                operation_count = 0
                total_operations = len(selected_session_ids) * len(selected_project_ids)
                
                for session_id in selected_session_ids:
                    for project_id in selected_project_ids:
                        if project_manager.add_session_to_project(project_id, session_id):
                            success_count += 1
                        
                        operation_count += 1
                        
                        # プログレスバーの更新（移動モードの場合は前半が解除なので後半を使用）
                        if is_move_mode:
                            progress_percent = 0.5 + (operation_count / total_operations * 0.5)
                        else:
                            progress_percent = operation_count / total_operations
                        
                        progress_bar.progress(progress_percent)
                
                # 100%にする
                progress_bar.progress(1.0)
                status_text.text("完了しました！")
                
                # 結果表示
                st.success(f"{session_count}個のセッションを{project_count}個のプロジェクトに割り当てました。")
                
                # 「一覧に戻る」ボタン
                if st.button("セッション一覧に戻る", key="back_to_session_list"):
                    st.session_state.session_management_tab = "一覧"
                    st.rerun()
                
                return True
                
            except Exception as e:
                st.error(f"セッションの割り当てに失敗しました: {str(e)}")
                return False
    
    return False
