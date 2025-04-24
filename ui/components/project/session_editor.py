# -*- coding: utf-8 -*-
"""
ui.components.project.session_editor

セッションメタデータ編集のUIコンポーネント
"""

import streamlit as st
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

from sailing_data_processor.project.project_manager import ProjectManager, Session
from sailing_data_processor.project.session_manager import SessionManager


class SessionEditorView:
    """
    セッションメタデータ編集コンポーネント
    
    セッションの基本情報、メタデータ、タグなどの編集機能を提供します。
    
    Parameters
    ----------
    project_manager : ProjectManager
        プロジェクト管理クラスのインスタンス
    session_manager : SessionManager
        セッション管理クラスのインスタンス
    on_save : Optional[Callable[[str], None]], optional
        保存時のコールバック関数, by default None
    on_cancel : Optional[Callable[[], None]], optional
        キャンセル時のコールバック関数, by default None
    """
    
    def __init__(
        self,
        project_manager: ProjectManager,
        session_manager: SessionManager,
        on_save: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        self.project_manager = project_manager
        self.session_manager = session_manager
        self.on_save = on_save
        self.on_cancel = on_cancel
    
    def render(self, session_id: str) -> bool:
        """
        コンポーネントのレンダリング
        
        Parameters
        ----------
        session_id : str
            編集するセッションのID
            
        Returns
        -------
        bool
            更新に成功した場合True
        """
        session = self.project_manager.get_session(session_id)
        if not session:
            st.error(f"セッションが見つかりません: {session_id}")
            return False
        
        st.title(f"セッション編集")
        st.subheader(f"{session.name}")
        st.caption(f"ID: {session_id}")
        
        # ステータスバッジの表示
        status_colors = {
            "new": "blue", 
            "validated": "green", 
            "analyzed": "violet", 
            "completed": "orange"
        }
        status_color = status_colors.get(session.status, "gray")
        st.markdown(
            f"<span style='background-color:{status_color};color:white;padding:0.2rem 0.5rem;border-radius:0.5rem;font-size:0.8rem;margin-right:0.5rem'>{session.status or 'なし'}</span>"
            f"<span style='background-color:#555;color:white;padding:0.2rem 0.5rem;border-radius:0.5rem;font-size:0.8rem'>{session.category or 'なし'}</span>",
            unsafe_allow_html=True
        )
        
        # タブの設定
        edit_tabs = st.tabs(["基本情報", "メタデータ", "タグ・カテゴリ", "高度な設定"])
        
        # イベント追跡用の状態
        if "session_edit_changes" not in st.session_state:
            st.session_state.session_edit_changes = {}
        
        current_changes = st.session_state.session_edit_changes
        
        with edit_tabs[0]:  # 基本情報タブ
            with st.form("edit_session_basic_form"):
                st.subheader("基本情報の編集")
                
                # 前回のフォーム値を保持するための状態
                form_key_prefix = "basic_"
                
                name = st.text_input(
                    "セッション名", 
                    value=st.session_state.get(f"{form_key_prefix}name", session.name),
                    key=f"{form_key_prefix}name",
                    help="セッションの識別名を入力してください"
                )
                
                description = st.text_area(
                    "説明", 
                    value=st.session_state.get(f"{form_key_prefix}description", session.description),
                    key=f"{form_key_prefix}description",
                    help="セッションの詳細説明"
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # ステータス選択
                    statuses = ["", "new", "validated", "analyzed", "completed"]
                    if session.status and session.status not in statuses:
                        statuses.append(session.status)
                    
                    status_descriptions = {
                        "": "未設定",
                        "new": "新規作成",
                        "validated": "検証済み",
                        "analyzed": "分析済み",
                        "completed": "完了"
                    }
                    
                    status = st.selectbox(
                        "ステータス",
                        options=statuses,
                        index=statuses.index(session.status) if session.status in statuses else 0,
                        format_func=lambda x: f"{x} - {status_descriptions.get(x, x)}" if x else "未設定",
                        key=f"{form_key_prefix}status",
                        help="セッションの現在の処理状態"
                    )
                
                with col2:
                    # カテゴリ選択
                    categories = ["", "general", "race", "training", "analysis", "other"]
                    if session.category and session.category not in categories:
                        categories.append(session.category)
                    
                    category_descriptions = {
                        "": "未設定",
                        "general": "一般",
                        "race": "レース",
                        "training": "トレーニング",
                        "analysis": "分析用",
                        "other": "その他"
                    }
                    
                    category = st.selectbox(
                        "カテゴリ",
                        options=categories,
                        index=categories.index(session.category) if session.category in categories else 0,
                        format_func=lambda x: f"{x} - {category_descriptions.get(x, x)}" if x else "未設定",
                        key=f"{form_key_prefix}category",
                        help="セッションの分類カテゴリ"
                    )
                
                # 変更内容の表示（変更があった場合のみ）
                name_changed = name != session.name
                desc_changed = description != session.description
                status_changed = status != session.status
                category_changed = category != session.category
                
                if name_changed or desc_changed or status_changed or category_changed:
                    st.markdown("---")
                    st.markdown("#### 変更内容プレビュー")
                    
                    if name_changed:
                        st.markdown(f"**名前**: {session.name} → **{name}**")
                    
                    if desc_changed:
                        st.markdown(f"**説明**: {session.description[:50]}... → **{description[:50]}...**")
                    
                    if status_changed:
                        st.markdown(f"**ステータス**: {session.status} → **{status}**")
                    
                    if category_changed:
                        st.markdown(f"**カテゴリ**: {session.category} → **{category}**")
                
                submitted_basic = st.form_submit_button("基本情報を更新", use_container_width=True)
                
                if submitted_basic:
                    # 変更内容を追跡
                    changes = {}
                    if name_changed:
                        changes["name"] = {"old": session.name, "new": name}
                    if desc_changed:
                        changes["description"] = {"old": session.description, "new": description}
                    if status_changed:
                        changes["status"] = {"old": session.status, "new": status}
                    if category_changed:
                        changes["category"] = {"old": session.category, "new": category}
                    
                    # 変更内容をセッション状態に追加
                    if changes:
                        current_changes.update(changes)
                    
                    # 基本情報の更新
                    session.name = name
                    session.description = description
                    session.status = status
                    session.category = category
                    
                    # セッションを保存
                    self.project_manager.save_session(session)
                    
                    st.success("基本情報を更新しました。")
                    if self.on_save:
                        self.on_save(session_id)
                    return True
        
        with edit_tabs[1]:  # メタデータタブ
            with st.form("edit_session_metadata_form"):
                st.subheader("メタデータ")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    location = st.text_input("位置情報", value=session.metadata.get("location", ""))
                    boat_type = st.text_input("艇種", value=session.metadata.get("boat_type", ""))
                    
                    # 風条件
                    wind_min = st.number_input(
                        "風速下限 (kt)",
                        min_value=0.0,
                        step=0.1,
                        value=float(session.metadata.get("wind_min", 0.0))
                    )
                    
                    wind_max = st.number_input(
                        "風速上限 (kt)",
                        min_value=0.0,
                        step=0.1,
                        value=float(session.metadata.get("wind_max", 0.0))
                    )
                
                with col2:
                    # イベント日の処理
                    event_date_str = session.metadata.get("event_date", "")
                    event_date = None
                    try:
                        if event_date_str:
                            event_date = datetime.fromisoformat(event_date_str)
                    except (ValueError, TypeError):
                        pass
                    
                    event_date = st.date_input(
                        "イベント日",
                        value=event_date.date() if event_date else None
                    )
                    
                    crew_info = st.text_input("クルー情報", value=session.metadata.get("crew_info", ""))
                    
                    # 天候
                    weather = st.text_input("天候", value=session.metadata.get("weather", ""))
                    
                    # 海況
                    sea_state = st.text_input("海況", value=session.metadata.get("sea_state", ""))
                
                # 備考
                notes = st.text_area("備考", value=session.metadata.get("notes", ""))
                
                # その他のメタデータの表示と編集
                other_metadata = {}
                exclude_keys = ["location", "boat_type", "event_date", "crew_info", "created_by", 
                               "wind_min", "wind_max", "weather", "sea_state", "notes"]
                
                for key, value in session.metadata.items():
                    if key not in exclude_keys:
                        other_metadata[key] = value
                
                if other_metadata:
                    st.subheader("その他のメタデータ")
                    st.markdown("以下のフィールドは自動生成されたメタデータまたは特殊な値です。変更する場合は注意してください。")
                    
                    for key, value in other_metadata.items():
                        if isinstance(value, (int, float, str, bool)) or value is None:
                            st.text_input(key, value, key=f"metadata_{key}")
                
                submitted_metadata = st.form_submit_button("メタデータを更新")
                
                if submitted_metadata:
                    # メタデータの更新
                    updated_metadata = {}
                    
                    # 基本メタデータ
                    updated_metadata["location"] = location
                    updated_metadata["boat_type"] = boat_type
                    updated_metadata["crew_info"] = crew_info
                    updated_metadata["wind_min"] = wind_min
                    updated_metadata["wind_max"] = wind_max
                    updated_metadata["weather"] = weather
                    updated_metadata["sea_state"] = sea_state
                    updated_metadata["notes"] = notes
                    
                    # イベント日の処理
                    if event_date:
                        updated_metadata["event_date"] = event_date.isoformat()
                    
                    # その他のメタデータの処理
                    for key, value in other_metadata.items():
                        form_key = f"metadata_{key}"
                        if form_key in st.session_state:
                            updated_metadata[key] = st.session_state[form_key]
                        else:
                            updated_metadata[key] = value
                    
                    # メタデータを一括更新
                    self.session_manager.update_session_metadata(session_id, updated_metadata)
                    
                    st.success("メタデータを更新しました。")
                    if self.on_save:
                        self.on_save(session_id)
                    return True
        
        with edit_tabs[2]:  # タグ・カテゴリタブ
            with st.form("edit_session_tags_form"):
                # 現在のタグを取得
                current_tags = session.tags if session.tags else []
                
                # 利用可能なタグの取得（既存のタグと現在のタグをマージ）
                available_tags = self.session_manager.get_available_tags()
                all_tags = list(set(available_tags + current_tags))
                
                # タグの選択
                selected_tags = st.multiselect(
                    "タグ",
                    options=all_tags,
                    default=current_tags
                )
                
                # 新しいタグの追加
                new_tag = st.text_input("新しいタグを追加 (カンマ区切りで複数指定可能)")
                
                # タグカラーのカスタマイズ
                st.subheader("タグの色設定")
                st.markdown("タグごとに色を設定できます（将来の機能）")
                
                if all_tags:
                    # タグ色のデモ表示
                    tag_colors = {}
                    for i, tag in enumerate(all_tags[:5]):  # 最初の5つのタグのみ表示
                        # カラーピッカー（実際の機能実装時は使用）
                        default_color = f"#{hash(tag) % 0xFFFFFF:06x}"  # タグ名からハッシュ値を生成
                        tag_colors[tag] = st.color_picker(f"タグ '{tag}' の色", default_color)
                
                # タグ自動提案機能
                if st.checkbox("タグの自動提案を有効にする"):
                    st.info("セッションの内容に基づいて、関連するタグを自動的に提案します（将来の機能）")
                    
                    # 自動提案の例（実際はこれをAIかルールベースで生成）
                    suggested_tags = ["sailing", "race", "training"]
                    st.write("提案タグ:", ", ".join(suggested_tags))
                    
                    if st.button("提案タグを追加"):
                        # 提案タグを選択済みタグに追加（実際の実装）
                        pass
                
                submitted_tags = st.form_submit_button("タグを更新")
                
                if submitted_tags:
                    # タグの処理
                    final_tags = selected_tags
                    if new_tag:
                        # カンマで区切られた複数のタグを処理
                        additional_tags = [tag.strip() for tag in new_tag.split(",") if tag.strip()]
                        final_tags.extend(additional_tags)
                        # 重複を削除
                        final_tags = list(set(final_tags))
                    
                    # タグを更新
                    success = self.session_manager.update_session_tags(session_id, final_tags)
                    
                    if success:
                        st.success("タグを更新しました。")
                        if self.on_save:
                            self.on_save(session_id)
                        return True
                    else:
                        st.error("タグの更新に失敗しました。")
                        return False
        
        with edit_tabs[3]:  # 高度な設定タブ
            # セッションのエクスポート設定
            st.subheader("セッションのエクスポート")
            
            export_format = st.selectbox(
                "エクスポート形式",
                options=["JSON", "CSV", "レポート (PDF)"]
            )
            
            if st.button("エクスポート", key="export_session_btn"):
                st.info(f"{export_format}形式でのエクスポート機能は開発中です。")
            
            # セッションの共有設定
            st.subheader("セッションの共有")
            
            share_options = st.multiselect(
                "共有オプション",
                options=["読み取り専用リンク", "編集可能リンク", "チームメンバーと共有", "公開"]
            )
            
            if st.button("共有設定を保存", key="save_share_settings"):
                st.info("共有機能は今後のアップデートで追加される予定です。")
            
            # セッションの削除
            st.subheader("セッションの削除")
            st.markdown("このセッションを完全に削除します。この操作は元に戻せません。")
            
            delete_data = st.checkbox("関連するデータファイルも削除する")
            
            if st.button("このセッションを削除", key="delete_session_btn", type="primary", help="セッションを完全に削除します"):
                # 削除確認ダイアログを表示するための状態を設定
                st.session_state.confirm_delete_session = True
                st.session_state.delete_data = delete_data
        
        # 削除確認ダイアログ
        if st.session_state.get("confirm_delete_session", False):
            with st.container():
                st.warning(f"セッション「{session.name}」を削除しますか？この操作は元に戻せません。")
                
                # 関連データファイルの削除チェックボックスが選択されていた場合
                if st.session_state.get("delete_data", False):
                    st.error("関連するデータファイルもすべて削除されます。")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("削除を確定", key="confirm_delete_yes", use_container_width=True):
                        # 削除処理
                        success = self.project_manager.delete_session(
                            session_id, 
                            delete_data=st.session_state.get("delete_data", False)
                        )
                        
                        if success:
                            st.success("セッションを削除しました。")
                            st.session_state.confirm_delete_session = False
                            
                            # 削除後に画面を戻る
                            if self.on_cancel:
                                self.on_cancel()
                            return True
                        else:
                            st.error("セッションの削除に失敗しました。")
                            st.session_state.confirm_delete_session = False
                            return False
                
                with col2:
                    if st.button("キャンセル", key="confirm_delete_no", use_container_width=True):
                        st.session_state.confirm_delete_session = False
                        st.session_state.delete_data = False
                        st.rerun()
        
        # ナビゲーションボタン
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("保存して終了", key="save_and_exit", use_container_width=True):
                # 全体の保存処理
                st.success("すべての変更を保存しました。")
                if self.on_save:
                    self.on_save(session_id)
                return True
        
        with col2:
            if st.button("キャンセル", key="cancel_edit", use_container_width=True):
                if self.on_cancel:
                    self.on_cancel()
                return False
        
        return False


def add_session_tag(session_manager: SessionManager, session_id: str, tag: str) -> bool:
    """
    セッションにタグを追加
    
    Parameters
    ----------
    session_manager : SessionManager
        セッション管理クラスのインスタンス
    session_id : str
        セッションID
    tag : str
        追加するタグ
        
    Returns
    -------
    bool
        成功した場合True
    """
    session = session_manager.project_manager.get_session(session_id)
    if not session:
        return False
    
    if not session.tags:
        session.tags = []
    
    if tag not in session.tags:
        session.tags.append(tag)
        session.updated_at = datetime.now().isoformat()
        session_manager.project_manager.save_session(session)
        return True
    
    return False


def remove_session_tag(session_manager: SessionManager, session_id: str, tag: str) -> bool:
    """
    セッションからタグを削除
    
    Parameters
    ----------
    session_manager : SessionManager
        セッション管理クラスのインスタンス
    session_id : str
        セッションID
    tag : str
        削除するタグ
        
    Returns
    -------
    bool
        成功した場合True
    """
    session = session_manager.project_manager.get_session(session_id)
    if not session or not session.tags:
        return False
    
    if tag in session.tags:
        session.tags.remove(tag)
        session.updated_at = datetime.now().isoformat()
        session_manager.project_manager.save_session(session)
        return True
    
    return False
