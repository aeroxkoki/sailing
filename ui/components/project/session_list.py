"""
ui.components.project.session_list

プロジェクト用のセッションリストを表示するコンポーネント
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple, Callable

from sailing_data_processor.project.project_model import Project, Session
from sailing_data_processor.project.session_manager import SessionManager


def format_datetime(iso_datetime: str) -> str:
    """ISO形式の日時を表示用にフォーマット"""
    try:
        dt = datetime.fromisoformat(iso_datetime)
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return iso_datetime


def session_list_component(
    session_manager: SessionManager,
    project_id: str,
    on_select: Optional[Callable[[str], None]] = None,
    on_add: Optional[Callable[[], None]] = None,
    on_remove: Optional[Callable[[str], None]] = None,
    compact: bool = False
) -> Optional[str]:
    """
    プロジェクト内のセッションリストを表示するコンポーネント
    
    Parameters
    ----------
    session_manager : SessionManager
        セッション管理クラスのインスタンス
    project_id : str
        プロジェクトID
    on_select : Optional[Callable[[str], None]], optional
        セッション選択時のコールバック, by default None
    on_add : Optional[Callable[[], None]], optional
        セッション追加ボタン押下時のコールバック, by default None
    on_remove : Optional[Callable[[str], None]], optional
        セッション削除ボタン押下時のコールバック, by default None
    compact : bool, optional
        コンパクト表示かどうか, by default False
        
    Returns
    -------
    Optional[str]
        選択されたセッションID
    """
    # セッション一覧を取得
    sessions = session_manager.get_project_sessions(project_id)
    
    if not sessions:
        st.info("このプロジェクトにはまだセッションがありません。")
        
        if on_add:
            if st.button("セッションを追加", key="add_session_to_project_btn"):
                on_add()
        
        return None
    
    # 検索/フィルタリング
    if not compact:
        with st.expander("検索フィルター", expanded=False):
            search_term = st.text_input("検索キーワード", key="session_list_search")
            
            col1, col2 = st.columns(2)
            
            with col1:
                status_options = ["すべてのステータス", "new", "validated", "analyzed", "completed"]
                status_filter = st.selectbox(
                    "ステータス",
                    options=status_options,
                    key="session_list_status_filter"
                )
            
            with col2:
                all_tags = set()
                for session in sessions:
                    if session.tags:
                        all_tags.update(session.tags)
                
                selected_tags = st.multiselect(
                    "タグ",
                    options=sorted(list(all_tags)),
                    key="session_list_tag_filter"
                )
            
            apply_filter = st.button("フィルター適用", key="apply_session_filter_btn")
    else:
        search_term = ""
        status_filter = "すべてのステータス"
        selected_tags = []
        apply_filter = False
    
    # フィルタリング処理
    if (search_term or status_filter != "すべてのステータス" or selected_tags) and (apply_filter or "filtered_sessions" in st.session_state):
        filtered_sessions = []
        
        for session in sessions:
            # 検索キーワードで絞り込み
            if search_term:
                if (search_term.lower() not in session.name.lower() and 
                    search_term.lower() not in session.description.lower()):
                    # タグも検索
                    tag_match = False
                    for tag in session.tags:
                        if search_term.lower() in tag.lower():
                            tag_match = True
                            break
                    if not tag_match:
                        continue
            
            # ステータスで絞り込み
            if status_filter != "すべてのステータス" and session.status != status_filter:
                continue
            
            # タグで絞り込み
            if selected_tags:
                if not all(tag in session.tags for tag in selected_tags):
                    continue
            
            filtered_sessions.append(session)
        
        st.session_state.filtered_sessions = filtered_sessions
        sessions = filtered_sessions
        
        if not sessions:
            st.warning("条件に合うセッションがありません。")
            if st.button("フィルターをクリア", key="clear_filter_btn"):
                if "filtered_sessions" in st.session_state:
                    del st.session_state.filtered_sessions
                st.rerun()
            return None
    
    # ソート機能
    sort_options = {
        "name_asc": "セッション名 (昇順)",
        "name_desc": "セッション名 (降順)",
        "date_asc": "イベント日 (昇順)",
        "date_desc": "イベント日 (降順)",
        "created_asc": "作成日 (昇順)",
        "created_desc": "作成日 (降順)",
        "updated_asc": "更新日 (昇順)",
        "updated_desc": "更新日 (降順)"
    }
    
    sort_option = "date_desc"  # デフォルト値
    
    if not compact:
        col1, col2 = st.columns([3, 1])
        with col1:
            sort_option = st.selectbox(
                "並び替え:",
                options=list(sort_options.keys()),
                format_func=lambda x: sort_options[x],
                index=list(sort_options.keys()).index(sort_option),
                key="session_list_sort_option"
            )
    
    # セッション表示用のデータフレームを作成
    sessions_data = []
    
    for session in sessions:
        # タグの表示形式を調整
        tags_str = ", ".join(session.tags) if session.tags else ""
        
        # 位置情報を取得
        location = session.metadata.get("location", "")
        
        # イベント日を取得
        event_date = session.metadata.get("event_date", "")
        if event_date:
            try:
                event_date = format_datetime(event_date)
            except:
                pass
        
        # 風速を取得（ある場合）
        wind_speed = session.metadata.get("avg_wind_speed", "")
        
        # コース種類を取得
        course_type = session.metadata.get("course_type", "")
        
        sessions_data.append({
            "セッション名": session.name,
            "説明": session.description[:30] + "..." if len(session.description) > 30 else session.description,
            "タグ": tags_str,
            "位置情報": location,
            "イベント日": event_date,
            "作成日時": format_datetime(session.created_at),
            "更新日時": format_datetime(session.updated_at),
            "ステータス": session.status,
            "風速": wind_speed,
            "コース種類": course_type,
            "カテゴリ": session.category,
            "セッションID": session.session_id
        })
    
    # セッションデータの並び替え
    if sessions_data:
        df = pd.DataFrame(sessions_data)
        
        # 並び替え
        if sort_option.startswith("name_"):
            df = df.sort_values("セッション名", ascending=sort_option.endswith("_asc"))
        elif sort_option.startswith("date_"):
            df = df.sort_values("イベント日", ascending=sort_option.endswith("_asc"))
        elif sort_option.startswith("created_"):
            df = df.sort_values("作成日時", ascending=sort_option.endswith("_asc"))
        elif sort_option.startswith("updated_"):
            df = df.sort_values("更新日時", ascending=sort_option.endswith("_asc"))
        
        # 表示列の設定（コンパクトモードかどうかで変更）
        if compact:
            display_columns = ["セッション名", "イベント日", "ステータス"]
        else:
            display_columns = ["セッション名", "説明", "タグ", "位置情報", "イベント日", "ステータス", "カテゴリ"]
        
        # 追加列の設定（データがある場合のみ）
        if not compact:
            if "風速" in df.columns and df["風速"].any():
                display_columns.append("風速")
            if "コース種類" in df.columns and df["コース種類"].any():
                display_columns.append("コース種類")
        
        # インタラクティブなテーブルの表示
        selection = st.dataframe(
            df[display_columns],
            hide_index=True,
            use_container_width=True,
            key="session_list_table"
        )
        
        # セッション選択用のセレクトボックス
        selected_session_id = st.selectbox(
            "セッションを選択:",
            options=[s.session_id for s in sessions],
            format_func=lambda x: next((s.name for s in sessions if s.session_id == x), x),
            key="session_list_selected_id"
        )
        
        # アクションボタン
        if not compact:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("詳細を表示", key="view_session_detail_btn", use_container_width=True):
                    if on_select and selected_session_id:
                        on_select(selected_session_id)
            
            with col2:
                if st.button("セッションを追加", key="add_more_sessions_btn", use_container_width=True):
                    if on_add:
                        on_add()
            
            with col3:
                if st.button("セッションを削除", key="remove_session_btn", use_container_width=True):
                    if on_remove and selected_session_id:
                        # 削除確認ダイアログ
                        session_name = next((s.name for s in sessions if s.session_id == selected_session_id), "")
                        
                        st.warning(f"セッション '{session_name}' をプロジェクトから削除しますか？")
                        confirm_col1, confirm_col2 = st.columns(2)
                        
                        with confirm_col1:
                            if st.button("キャンセル", key="cancel_remove_btn"):
                                st.rerun()
                        
                        with confirm_col2:
                            if st.button("削除する", key="confirm_remove_btn", type="primary"):
                                on_remove(selected_session_id)
        else:
            # コンパクトモードの場合は詳細表示ボタンのみ
            if st.button("詳細を表示", key="view_session_detail_compact_btn"):
                if on_select and selected_session_id:
                    on_select(selected_session_id)
        
        return selected_session_id
    
    return None


def session_summary_component(session_manager: SessionManager, project_id: str) -> None:
    """
    セッションの概要情報を表示するコンポーネント
    
    Parameters
    ----------
    session_manager : SessionManager
        セッション管理クラスのインスタンス
    project_id : str
        プロジェクトID
    """
    sessions = session_manager.get_project_sessions(project_id)
    
    if not sessions:
        return
    
    # 各種カウント
    total_sessions = len(sessions)
    status_counts = {"new": 0, "validated": 0, "analyzed": 0, "completed": 0, "その他": 0}
    category_counts = {}
    tags = set()
    
    for session in sessions:
        # ステータスカウント
        status = session.status if session.status in status_counts else "その他"
        status_counts[status] += 1
        
        # カテゴリカウント
        category = session.category or "未分類"
        if category not in category_counts:
            category_counts[category] = 0
        category_counts[category] += 1
        
        # タグ収集
        if session.tags:
            tags.update(session.tags)
    
    # サマリー表示
    st.subheader("セッション概要")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("総セッション数", total_sessions)
        
        # ステータス内訳
        st.write("**ステータス内訳:**")
        status_df = pd.DataFrame({
            "ステータス": list(status_counts.keys()),
            "セッション数": list(status_counts.values())
        })
        st.dataframe(status_df, hide_index=True, use_container_width=True)
    
    with col2:
        # カテゴリ内訳（上位5件のみ）
        st.write("**カテゴリ内訳:**")
        category_items = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        category_df = pd.DataFrame({
            "カテゴリ": [item[0] for item in category_items],
            "セッション数": [item[1] for item in category_items]
        })
        st.dataframe(category_df, hide_index=True, use_container_width=True)
        
        # タグクラウド（タグ数が多い場合は省略）
        st.write("**使用タグ:**")
        if tags:
            st.write(", ".join(sorted(tags)[:10]) + ("..." if len(tags) > 10 else ""))
        else:
            st.write("タグなし")


def detailed_session_list_view(
    session_manager: SessionManager,
    project_id: str,
    on_select: Optional[Callable[[str], None]] = None,
    on_add: Optional[Callable[[], None]] = None,
    on_remove: Optional[Callable[[str], None]] = None
) -> None:
    """
    セッションリストの詳細表示ビュー
    
    Parameters
    ----------
    session_manager : SessionManager
        セッション管理クラスのインスタンス
    project_id : str
        プロジェクトID
    on_select : Optional[Callable[[str], None]], optional
        セッション選択時のコールバック, by default None
    on_add : Optional[Callable[[], None]], optional
        セッション追加ボタン押下時のコールバック, by default None
    on_remove : Optional[Callable[[str], None]], optional
        セッション削除ボタン押下時のコールバック, by default None
    """
    # セッション概要を表示
    session_summary_component(session_manager, project_id)
    
    st.markdown("---")
    
    # セッションリストを表示
    st.subheader("セッションリスト")
    selected_id = session_list_component(
        session_manager,
        project_id,
        on_select=on_select,
        on_add=on_add,
        on_remove=on_remove,
        compact=False
    )
