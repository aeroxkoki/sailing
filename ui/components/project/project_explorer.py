# -*- coding: utf-8 -*-
"""
ui.components.project.project_explorer

プロジェクトエクスプローラーコンポーネントを提供するモジュール
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable, Union
import pandas as pd
from datetime import datetime
import json

from sailing_data_processor.project.project_model import Project, Session
from sailing_data_processor.project.project_storage import ProjectStorage


class ProjectExplorer:
    """
    プロジェクトエクスプローラーコンポーネント
    
    プロジェクトとセッションをツリービュー形式で表示し、操作するためのUIコンポーネント
    """
    
    def __init__(self, 
                key: str = "project_explorer", 
                project_storage: Optional[ProjectStorage] = None,
                on_project_select: Optional[Callable[[str], None]] = None,
                on_session_select: Optional[Callable[[str], None]] = None,
                on_project_edit: Optional[Callable[[str], None]] = None,
                on_session_edit: Optional[Callable[[str], None]] = None):
        """
        プロジェクトエクスプローラーの初期化
        
        Parameters
        ----------
        key : str, optional
            Streamlitウィジェットのキー, by default "project_explorer"
        project_storage : Optional[ProjectStorage], optional
            プロジェクトストレージインスタンス, by default None
        on_project_select : Optional[Callable[[str], None]], optional
            プロジェクト選択時のコールバック関数（引数はプロジェクトID）, by default None
        on_session_select : Optional[Callable[[str], None]], optional
            セッション選択時のコールバック関数（引数はセッションID）, by default None
        on_project_edit : Optional[Callable[[str], None]], optional
            プロジェクト編集ボタン押下時のコールバック関数（引数はプロジェクトID）, by default None
        on_session_edit : Optional[Callable[[str], None]], optional
            セッション編集ボタン押下時のコールバック関数（引数はセッションID）, by default None
        """
        self.key = key
        self.project_storage = project_storage or ProjectStorage()
        self.on_project_select = on_project_select
        self.on_session_select = on_session_select
        self.on_project_edit = on_project_edit
        self.on_session_edit = on_session_edit
        
        # セッション状態の初期化
        if f"{key}_expanded" not in st.session_state:
            st.session_state[f"{key}_expanded"] = set()
        if f"{key}_selected" not in st.session_state:
            st.session_state[f"{key}_selected"] = None
        if f"{key}_selection_type" not in st.session_state:
            st.session_state[f"{key}_selection_type"] = None  # 'project' or 'session'
    
    def render(self) -> None:
        """
        プロジェクトエクスプローラーをレンダリング
        """
        # スタイル設定
        st.markdown("""
        <style>
        .project-tree {
            margin-left: 10px;
        }
        .project-node {
            margin-bottom: 5px;
            padding: 5px;
            border-radius: 3px;
        }
        .project-node:hover {
            background-color: #f0f0f0;
        }
        .session-node {
            margin-left: 20px;
            margin-bottom: 3px;
            padding: 3px;
            border-radius: 3px;
        }
        .session-node:hover {
            background-color: #f0f0f0;
        }
        .selected-node {
            background-color: #e0f7fa;
            font-weight: bold;
        }
        .expander-icon {
            cursor: pointer;
            margin-right: 5px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown("### プロジェクトエクスプローラー")
        
        # プロジェクトの読み込み（最新状態を確保するため）
        self.project_storage.reload()
        
        # プロジェクトツリーの取得
        tree = self.project_storage.get_project_tree()
        
        # ルートプロジェクトの表示
        self._render_project_tree(tree)
        
        # 操作ボタン
        st.markdown("### 操作")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("新規プロジェクト作成", key=f"{self.key}_new_project_btn"):
                if self.on_project_edit:
                    # 新規プロジェクト作成モードで編集画面を開く
                    self.on_project_edit("new")
        
        with col2:
            if st.button("新規セッション作成", key=f"{self.key}_new_session_btn"):
                if self.on_session_edit:
                    # 新規セッション作成モードで編集画面を開く
                    self.on_session_edit("new")
        
        # 現在の選択を表示
        if st.session_state[f"{self.key}_selected"]:
            selection_type = st.session_state[f"{self.key}_selection_type"]
            selected_id = st.session_state[f"{self.key}_selected"]
            
            if selection_type == "project":
                project = self.project_storage.get_project(selected_id)
                if project:
                    st.markdown(f"**選択中**: プロジェクト '{project.name}'")
            elif selection_type == "session":
                session = self.project_storage.get_session(selected_id)
                if session:
                    st.markdown(f"**選択中**: セッション '{session.name}'")
    
    def _render_project_tree(self, tree: Dict[str, Any]) -> None:
        """
        プロジェクトツリーを再帰的にレンダリング
        
        Parameters
        ----------
        tree : Dict[str, Any]
            プロジェクトツリー構造
        """
        if tree["type"] == "root":
            # ルートノードの子要素を表示
            for child in tree.get("children", []):
                self._render_project_node(child, level=0)
        else:
            # それ以外のノードはそのまま表示
            self._render_project_node(tree, level=0)
    
    def _render_project_node(self, node: Dict[str, Any], level: int = 0) -> None:
        """
        プロジェクトノードをレンダリング
        
        Parameters
        ----------
        node : Dict[str, Any]
            プロジェクトノード情報
        level : int, optional
            階層レベル, by default 0
        """
        project_id = node.get("id")
        node_key = f"project_{project_id}"
        
        # プロジェクトノードのコンテナ
        with st.container():
            is_expanded = node_key in st.session_state[f"{self.key}_expanded"]
            is_selected = (st.session_state[f"{self.key}_selected"] == project_id) and \
                         (st.session_state[f"{self.key}_selection_type"] == "project")
            
            # プロジェクトノードのレンダリング
            left_col, right_col = st.columns([9, 1])
            
            with left_col:
                # インデントと展開アイコン
                indent = "&nbsp;" * (level * 4)
                
                # 子ノードがある場合は展開/折りたたみアイコンを表示
                has_children = len(node.get("children", [])) > 0 or len(node.get("sessions", [])) > 0
                
                if has_children:
                    expander_icon = "▼" if is_expanded else "▶"
                    expander_html = f'<span class="expander-icon" id="{node_key}_expander">{expander_icon}</span>'
                else:
                    expander_html = f'<span style="margin-right: 15px;"></span>'
                
                # プロジェクト名とアイコン
                node_class = "project-node" + (" selected-node" if is_selected else "")
                project_html = f"""
                <div class="{node_class}" id="{node_key}">
                    {indent}{expander_html} 📁 {node.get("name", "Unnamed")}
                </div>
                """
                
                # HTMLの表示とクリックイベントの処理
                st.markdown(project_html, unsafe_allow_html=True)
                
                # JavaScriptを使用して、クリックイベントを処理
                st.markdown(f"""
                <script>
                    // プロジェクトノードのクリックイベント
                    document.getElementById("{node_key}").addEventListener("click", function(e) {{
                        // 親要素のクリックのみを処理
                        if (e.target.id === "{node_key}") {{
                            // Streamlitに選択状態を送信
                            window.parent.postMessage({{
                                type: "streamlit:setComponentValue",
                                value: {{"type": "project_select", "id": "{project_id}"}}
                            }}, "*");
                        }}
                    }});
                    
                    // 展開アイコンのクリックイベント
                    var expander = document.getElementById("{node_key}_expander");
                    if (expander) {{
                        expander.addEventListener("click", function(e) {{
                            // Streamlitに展開状態を送信
                            window.parent.postMessage({{
                                type: "streamlit:setComponentValue",
                                value: {{"type": "project_toggle", "id": "{node_key}"}}
                            }}, "*");
                            e.stopPropagation();
                        }});
                    }}
                </script>
                """, unsafe_allow_html=True)
            
            with right_col:
                # 編集ボタン
                if st.button("編集", key=f"{node_key}_edit"):
                    if self.on_project_edit:
                        self.on_project_edit(project_id)
            
            # 展開されている場合は子ノードとセッションを表示
            if is_expanded:
                # セッションの表示
                for session in node.get("sessions", []):
                    self._render_session_node(session, level + 1)
                
                # 子プロジェクトの表示
                for child in node.get("children", []):
                    self._render_project_node(child, level + 1)
    
    def _render_session_node(self, node: Dict[str, Any], level: int = 0) -> None:
        """
        セッションノードをレンダリング
        
        Parameters
        ----------
        node : Dict[str, Any]
            セッションノード情報
        level : int, optional
            階層レベル, by default 0
        """
        session_id = node.get("id")
        node_key = f"session_{session_id}"
        
        # セッションノードのコンテナ
        with st.container():
            is_selected = (st.session_state[f"{self.key}_selected"] == session_id) and \
                         (st.session_state[f"{self.key}_selection_type"] == "session")
            
            # セッションノードのレンダリング
            left_col, right_col = st.columns([9, 1])
            
            with left_col:
                # インデント
                indent = "&nbsp;" * (level * 4)
                
                # セッション名とアイコン
                node_class = "session-node" + (" selected-node" if is_selected else "")
                
                # カテゴリに基づいたアイコンの選択
                category = node.get("category", "general")
                icon = "📊"  # デフォルトアイコン
                
                if category == "race":
                    icon = "🏁"
                elif category == "training":
                    icon = "🏃"
                elif category == "analysis":
                    icon = "🔍"
                
                session_html = f"""
                <div class="{node_class}" id="{node_key}">
                    {indent}{icon} {node.get("name", "Unnamed")}
                </div>
                """
                
                # HTMLの表示とクリックイベントの処理
                st.markdown(session_html, unsafe_allow_html=True)
                
                # JavaScriptを使用して、クリックイベントを処理
                st.markdown(f"""
                <script>
                    // セッションノードのクリックイベント
                    document.getElementById("{node_key}").addEventListener("click", function() {{
                        // Streamlitに選択状態を送信
                        window.parent.postMessage({{
                            type: "streamlit:setComponentValue",
                            value: {{"type": "session_select", "id": "{session_id}"}}
                        }}, "*");
                    }});
                </script>
                """, unsafe_allow_html=True)
            
            with right_col:
                # 編集ボタン
                if st.button("編集", key=f"{node_key}_edit"):
                    if self.on_session_edit:
                        self.on_session_edit(session_id)
    
    def handle_frontend_event(self, event: Dict[str, Any]) -> None:
        """
        フロントエンドからのイベントを処理
        
        Parameters
        ----------
        event : Dict[str, Any]
            イベントデータ
        """
        event_type = event.get("type")
        
        if event_type == "project_select":
            project_id = event.get("id")
            st.session_state[f"{self.key}_selected"] = project_id
            st.session_state[f"{self.key}_selection_type"] = "project"
            
            if self.on_project_select:
                self.on_project_select(project_id)
            
            st.rerun()
        
        elif event_type == "session_select":
            session_id = event.get("id")
            st.session_state[f"{self.key}_selected"] = session_id
            st.session_state[f"{self.key}_selection_type"] = "session"
            
            if self.on_session_select:
                self.on_session_select(session_id)
            
            st.rerun()
        
        elif event_type == "project_toggle":
            node_key = event.get("id")
            expanded = st.session_state[f"{self.key}_expanded"]
            
            if node_key in expanded:
                expanded.remove(node_key)
            else:
                expanded.add(node_key)
            
            st.rerun()
    
    def get_selected_item(self) -> Optional[Dict[str, Any]]:
        """
        選択中のアイテム情報を取得
        
        Returns
        -------
        Optional[Dict[str, Any]]
            選択中のアイテム情報（存在しない場合はNone）
        """
        if not st.session_state[f"{self.key}_selected"]:
            return None
        
        selection_type = st.session_state[f"{self.key}_selection_type"]
        selected_id = st.session_state[f"{self.key}_selected"]
        
        if selection_type == "project":
            project = self.project_storage.get_project(selected_id)
            if project:
                return {
                    "type": "project",
                    "id": selected_id,
                    "project": project
                }
        elif selection_type == "session":
            session = self.project_storage.get_session(selected_id)
            if session:
                return {
                    "type": "session",
                    "id": selected_id,
                    "session": session
                }
        
        return None


def project_explorer(key: str = "project_explorer", 
                    project_storage: Optional[ProjectStorage] = None,
                    on_project_select: Optional[Callable[[str], None]] = None,
                    on_session_select: Optional[Callable[[str], None]] = None,
                    on_project_edit: Optional[Callable[[str], None]] = None,
                    on_session_edit: Optional[Callable[[str], None]] = None) -> Optional[Dict[str, Any]]:
    """
    プロジェクトエクスプローラーコンポーネントの簡易関数

    Parameters
    ----------
    key : str, optional
        Streamlitウィジェットのキー, by default "project_explorer"
    project_storage : Optional[ProjectStorage], optional
        プロジェクトストレージインスタンス, by default None
    on_project_select : Optional[Callable[[str], None]], optional
        プロジェクト選択時のコールバック関数, by default None
    on_session_select : Optional[Callable[[str], None]], optional
        セッション選択時のコールバック関数, by default None
    on_project_edit : Optional[Callable[[str], None]], optional
        プロジェクト編集ボタン押下時のコールバック関数, by default None
    on_session_edit : Optional[Callable[[str], None]], optional
        セッション編集ボタン押下時のコールバック関数, by default None

    Returns
    -------
    Optional[Dict[str, Any]]
        選択中のアイテム情報
    """
    explorer = ProjectExplorer(
        key=key,
        project_storage=project_storage,
        on_project_select=on_project_select,
        on_session_select=on_session_select,
        on_project_edit=on_project_edit,
        on_session_edit=on_session_edit
    )
    
    explorer.render()
    return explorer.get_selected_item()
