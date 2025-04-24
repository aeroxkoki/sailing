# -*- coding: utf-8 -*-
"""
ui.components.project.project_create

プロジェクト作成・編集のUIコンポーネント
"""

import streamlit as st
from typing import Callable, Optional, Dict, Any, List, Union
import re

from sailing_data_processor.project.project_manager import Project, ProjectManager


class ProjectCreateView:
    """
    プロジェクト作成・編集コンポーネント
    
    新規プロジェクトの作成と既存プロジェクトの編集を行うためのUIコンポーネント。
    
    Parameters
    ----------
    project_manager : ProjectManager
        プロジェクト管理クラスのインスタンス
    on_save : Callable[[str], None], optional
        保存完了時のコールバック関数, by default None
    on_cancel : Callable[[], None], optional
        キャンセル時のコールバック関数, by default None
    """
    
    def __init__(
        self,
        project_manager: ProjectManager,
        on_save: Optional[Callable[[str], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        self.project_manager = project_manager
        self.on_save = on_save
        self.on_cancel = on_cancel
        
        # フォーム初期状態管理
        if "project_form_data" not in st.session_state:
            st.session_state.project_form_data = {
                "name": "",
                "description": "",
                "tags": [],
                "metadata": {}
            }
    
    def _validate_project_name(self, name: str) -> Union[str, None]:
        """
        プロジェクト名のバリデーション
        
        Parameters
        ----------
        name : str
            バリデーションするプロジェクト名
            
        Returns
        -------
        Union[str, None]
            エラーメッセージ。問題なければNone
        """
        if not name:
            return "プロジェクト名は必須です"
        
        if len(name) < 3:
            return "プロジェクト名は3文字以上である必要があります"
        
        # 禁止文字のチェック
        if re.search(r'[<>:"/\\|?*]', name):
            return "プロジェクト名に次の文字は使用できません: < > : \" / \\ | ? *"
        
        return None
    
    def render(self, project_id: Optional[str] = None):
        """
        コンポーネントのレンダリング
        
        Parameters
        ----------
        project_id : Optional[str], optional
            編集するプロジェクトのID (Noneの場合は新規作成), by default None
        """
        # モードの決定（新規作成 or 編集）
        is_edit_mode = project_id is not None
        
        # 編集モードの場合、既存プロジェクトのデータを読み込む
        if is_edit_mode:
            project = self.project_manager.get_project(project_id)
            if not project:
                st.error(f"プロジェクトが見つかりません: {project_id}")
                return
            
            # 初期データの読み込み（最初の1回だけ）
            if st.session_state.project_form_data.get("initialized_for_edit") != project_id:
                st.session_state.project_form_data = {
                    "name": project.name,
                    "description": project.description,
                    "tags": project.tags.copy() if project.tags else [],
                    "metadata": project.metadata.copy() if project.metadata else {},
                    "initialized_for_edit": project_id  # フラグ：このプロジェクトIDで初期化済み
                }
        
        # タイトル
        if is_edit_mode:
            st.subheader(f"プロジェクトの編集: {st.session_state.project_form_data['name']}")
        else:
            st.subheader("新規プロジェクトの作成")
        
        # フォーム
        with st.form(key="project_form"):
            # プロジェクト名
            name = st.text_input(
                "プロジェクト名 *",
                value=st.session_state.project_form_data["name"],
                key="project_name_input"
            )
            
            # 名前のバリデーション
            name_error = self._validate_project_name(name)
            if name_error:
                st.error(name_error)
            
            # プロジェクト説明
            description = st.text_area(
                "説明",
                value=st.session_state.project_form_data["description"],
                height=100,
                key="project_description_input"
            )
            
            # タグ
            # 新規タグの入力UI
            new_tag = st.text_input(
                "新しいタグ（カンマ区切りで複数入力可）",
                key="new_tag_input"
            )
            
            # 既存のタグ一覧
            existing_tags = sorted(list(self.project_manager.get_project_tags()))
            
            # タグの選択UI
            selected_tags = st.multiselect(
                "タグ",
                options=existing_tags,
                default=st.session_state.project_form_data["tags"],
                key="project_tags_input"
            )
            
            # メタデータ編集のオプション
            st.subheader("メタデータ", help="プロジェクトに関する追加情報")
            
            # メタデータの管理
            current_metadata = st.session_state.project_form_data.get("metadata", {})
            new_metadata = current_metadata.copy()
            
            # 既存のメタデータ表示
            for key, value in current_metadata.items():
                col1, col2, col3 = st.columns([2, 5, 1])
                with col1:
                    st.text(key)
                with col2:
                    new_value = st.text_input(
                        f"Value for {key}",
                        value=value,
                        label_visibility="collapsed",
                        key=f"metadata_value_{key}"
                    )
                    new_metadata[key] = new_value
                with col3:
                    if st.button("削除", key=f"delete_metadata_{key}"):
                        del new_metadata[key]
                        st.rerun()
            
            # 新しいメタデータの追加
            with st.expander("メタデータを追加"):
                col1, col2 = st.columns(2)
                with col1:
                    new_key = st.text_input("キー", key="new_metadata_key")
                with col2:
                    new_value = st.text_input("値", key="new_metadata_value")
                
                if st.button("追加", key="add_metadata_btn", disabled=not new_key):
                    if new_key:
                        new_metadata[new_key] = new_value
                        st.rerun()
            
            # フォームボタン
            col1, col2 = st.columns(2)
            with col1:
                cancel_btn = st.form_submit_button("キャンセル", use_container_width=True)
            with col2:
                submit_btn = st.form_submit_button("保存", use_container_width=True)
        
        # フォーム送信処理
        if cancel_btn and self.on_cancel:
            st.session_state.project_form_data = {
                "name": "",
                "description": "",
                "tags": [],
                "metadata": {}
            }
            self.on_cancel()
        
        if submit_btn:
            # 入力値の検証
            if name_error:
                st.error("入力エラーがあります。修正してください。")
                return
            
            # 新しいタグの処理
            all_tags = selected_tags.copy()
            if new_tag:
                # カンマ区切りのタグを分割
                additional_tags = [tag.strip() for tag in new_tag.split(",") if tag.strip()]
                all_tags.extend(additional_tags)
                # 重複の削除
                all_tags = list(set(all_tags))
            
            # 保存処理
            if is_edit_mode:
                # 既存プロジェクトの更新
                project = self.project_manager.get_project(project_id)
                if project:
                    project.name = name
                    project.description = description
                    project.tags = all_tags
                    project.metadata = new_metadata
                    
                    success = self.project_manager.update_project(project)
                    if success:
                        st.success("プロジェクトを更新しました")
                        if self.on_save:
                            self.on_save(project_id)
                    else:
                        st.error("プロジェクトの更新に失敗しました")
            else:
                # 新規プロジェクトの作成
                try:
                    project = self.project_manager.create_project(
                        name=name,
                        description=description,
                        tags=all_tags,
                        metadata=new_metadata
                    )
                    st.success("プロジェクトを作成しました")
                    if self.on_save:
                        self.on_save(project.project_id)
                except Exception as e:
                    st.error(f"プロジェクトの作成に失敗しました: {str(e)}")
            
            # フォームデータのリセット
            st.session_state.project_form_data = {
                "name": "",
                "description": "",
                "tags": [],
                "metadata": {}
            }
