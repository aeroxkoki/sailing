# -*- coding: utf-8 -*-
"""
ui.components.project.project_form

プロジェクトの作成と編集用フォームコンポーネント
"""

import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime

from ui.components.project.project_manager import initialize_project_manager
from sailing_data_processor.project.project_model import Project


def project_form(project: Optional[Project] = None, key_prefix: str = "new") -> Optional[Dict[str, Any]]:
    """
    プロジェクト作成・編集フォームを表示する
    
    Parameters
    ----------
    project : Optional[Project]
        編集する既存のプロジェクト、新規作成の場合はNone
    key_prefix : str
        フォーム要素のキープレフィックス
    
    Returns
    -------
    Optional[Dict[str, Any]]
        フォームから収集されたプロジェクトデータ。キャンセルされた場合はNone
    """
    pm = initialize_project_manager()
    is_edit_mode = project is not None
    
    if is_edit_mode:
        form_title = "プロジェクトの編集"
        submit_label = "更新"
    else:
        form_title = "新規プロジェクト作成"
        submit_label = "作成"
    
    with st.form(key=f"{key_prefix}_project_form"):
        st.subheader(form_title)
        
        # 基本情報
        name = st.text_input(
            "プロジェクト名 *", 
            value=project.name if is_edit_mode else "",
            key=f"{key_prefix}_name"
        )
        
        description = st.text_area(
            "プロジェクト説明",
            value=project.description if is_edit_mode else "",
            key=f"{key_prefix}_description"
        )
        
        # メタデータセクション
        st.subheader("メタデータ")
        
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input(
                "場所",
                value=project.metadata.get("location", "") if is_edit_mode else "",
                key=f"{key_prefix}_location"
            )
            
            event_date = st.date_input(
                "イベント日",
                value=datetime.now(),
                key=f"{key_prefix}_event_date"
            )
        
        with col2:
            weather = st.text_input(
                "天候",
                value=project.metadata.get("weather_conditions", "") if is_edit_mode else "",
                key=f"{key_prefix}_weather"
            )
            
            boat_type = st.text_input(
                "艇種",
                value=project.metadata.get("boat_type", "") if is_edit_mode else "",
                key=f"{key_prefix}_boat_type"
            )
        
        # タグ
        tags_str = st.text_input(
            "タグ（カンマ区切り）",
            value=", ".join(project.tags) if is_edit_mode and project.tags else "",
            key=f"{key_prefix}_tags",
            help="例: 練習, レース, 強風"
        )
        
        # 色とアイコン
        st.subheader("表示設定")
        col1, col2 = st.columns(2)
        
        with col1:
            color = st.color_picker(
                "プロジェクトの色",
                value=project.color if is_edit_mode else "#4A90E2",
                key=f"{key_prefix}_color"
            )
        
        with col2:
            icon_options = ["folder", "map", "flag", "anchor", "compass", "boat", "wind", "star"]
            selected_icon = st.selectbox(
                "アイコン",
                options=icon_options,
                index=icon_options.index(project.icon) if is_edit_mode and project.icon in icon_options else 0,
                key=f"{key_prefix}_icon"
            )
        
        # カテゴリ
        category_options = ["general", "training", "race", "analysis", "other"]
        selected_category = st.selectbox(
            "カテゴリ",
            options=category_options,
            index=category_options.index(project.category) if is_edit_mode and project.category in category_options else 0,
            key=f"{key_prefix}_category"
        )
        
        # 親プロジェクト選択（編集モードでない場合または親がない場合）
        if not is_edit_mode or not project.parent_id:
            all_projects = pm.get_projects()
            
            # 編集モードの場合、自分自身を選択肢から除外
            if is_edit_mode:
                parent_options = [p for p in all_projects if p.project_id != project.project_id]
            else:
                parent_options = all_projects
            
            # 選択肢に「なし」を追加
            parent_options_with_none = [None] + parent_options
            
            parent_project = st.selectbox(
                "親プロジェクト",
                options=parent_options_with_none,
                format_func=lambda p: "なし" if p is None else p.name,
                index=0,  # デフォルトは「なし」
                key=f"{key_prefix}_parent"
            )
            
            parent_id = parent_project.project_id if parent_project else None
        else:
            # 現在の親プロジェクトを表示
            parent = pm.get_project(project.parent_id)
            if parent:
                st.info(f"親プロジェクト: {parent.name}")
            else:
                st.warning("親プロジェクトが見つかりません")
            parent_id = project.parent_id
        
        # 送信ボタン
        col1, col2 = st.columns([3, 1])
        with col2:
            submitted = st.form_submit_button(submit_label)
        with col1:
            cancelled = st.form_submit_button("キャンセル")
        
        if cancelled:
            return None
        
        if submitted:
            # フォームのバリデーション
            if not name:
                st.error("プロジェクト名は必須です")
                return None
            
            # タグの処理
            tags_list = [tag.strip() for tag in tags_str.split(",") if tag.strip()]
            
            # プロジェクトデータの準備
            project_data = {
                "name": name,
                "description": description,
                "tags": tags_list,
                "metadata": {
                    "location": location,
                    "event_date": event_date.isoformat() if event_date else "",
                    "weather_conditions": weather,
                    "boat_type": boat_type
                },
                "color": color,
                "icon": selected_icon,
                "category": selected_category,
                "parent_id": parent_id
            }
            
            # 編集モードの場合はプロジェクトIDを追加
            if is_edit_mode:
                project_data["project_id"] = project.project_id
            
            return project_data
    
    return None


def create_or_update_project(project_data: Dict[str, Any], is_edit_mode: bool = False) -> Optional[Project]:
    """
    プロジェクトの作成または更新を行う
    
    Parameters
    ----------
    project_data : Dict[str, Any]
        プロジェクトデータ
    is_edit_mode : bool
        編集モードかどうか
    
    Returns
    -------
    Optional[Project]
        作成または更新されたプロジェクト、失敗した場合はNone
    """
    pm = initialize_project_manager()
    
    if is_edit_mode:
        # 既存のプロジェクトを取得
        project_id = project_data.pop("project_id")
        project = pm.get_project(project_id)
        
        if not project:
            st.error(f"プロジェクト ID: {project_id} が見つかりません")
            return None
        
        # プロジェクトのプロパティを更新
        project.name = project_data["name"]
        project.description = project_data["description"]
        project.tags = project_data["tags"]
        project.metadata.update(project_data["metadata"])
        project.color = project_data["color"]
        project.icon = project_data["icon"]
        project.category = project_data["category"]
        
        # 親プロジェクトの変更処理（必要であれば）
        parent_id = project_data.get("parent_id")
        if parent_id != project.parent_id:
            # 親プロジェクトからの削除
            if project.parent_id:
                old_parent = pm.get_project(project.parent_id)
                if old_parent:
                    old_parent.remove_sub_project(project.project_id)
                    pm.update_project(old_parent)
            
            # 新しい親プロジェクトへの追加
            project.parent_id = parent_id
            if parent_id:
                new_parent = pm.get_project(parent_id)
                if new_parent:
                    new_parent.add_sub_project(project.project_id)
                    pm.update_project(new_parent)
        
        # プロジェクトの更新
        if pm.update_project(project):
            st.success(f"プロジェクト '{project.name}' を更新しました")
            return project
        else:
            st.error("プロジェクトの更新に失敗しました")
            return None
    else:
        # 新規プロジェクト作成
        project = Project(
            name=project_data["name"],
            description=project_data["description"],
            tags=project_data["tags"],
            metadata=project_data["metadata"],
            parent_id=project_data.get("parent_id")
        )
        
        # 追加プロパティの設定
        project.color = project_data["color"]
        project.icon = project_data["icon"]
        project.category = project_data["category"]
        
        # プロジェクトマネージャーにプロジェクトを追加
        pm.projects[project.project_id] = project
        
        # プロジェクトをファイルに保存
        if pm._save_project(project):
            # 親プロジェクトの更新
            parent_id = project_data.get("parent_id")
            if parent_id:
                parent = pm.get_project(parent_id)
                if parent:
                    parent.add_sub_project(project.project_id)
                    pm.update_project(parent)
            
            st.success(f"プロジェクト '{project.name}' を作成しました")
            return project
        else:
            st.error("プロジェクトの作成に失敗しました")
            return None
