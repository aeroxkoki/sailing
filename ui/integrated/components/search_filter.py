"""
ui.integrated.components.search_filter

検索・フィルタリング用のコンポーネント
"""

import streamlit as st
import os
import sys

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# 自作モジュールのインポート
from ui.components.project.project_manager import initialize_project_manager

def render_search_filter(key_prefix=""):
    """
    検索・フィルタリング用のUIコンポーネントを表示

    Parameters
    ----------
    key_prefix : str, optional
        Streamlitのキー名のプレフィックス, by default ""

    Returns
    -------
    tuple
        (search_query, selected_tags, apply_filter)
    """
    # プロジェクトマネージャーの初期化
    pm = initialize_project_manager()
    
    # セッション状態の初期化
    if f"{key_prefix}search_query" not in st.session_state:
        st.session_state[f"{key_prefix}search_query"] = ""
    if f"{key_prefix}selected_tags" not in st.session_state:
        st.session_state[f"{key_prefix}selected_tags"] = []
    
    # レイアウト
    col1, col2 = st.columns([3, 1])
    
    # 検索クエリ入力
    with col1:
        search_query = st.text_input(
            "検索キーワード",
            value=st.session_state[f"{key_prefix}search_query"],
            key=f"{key_prefix}search_query_input",
            placeholder="プロジェクト名や説明で検索...",
            help="プロジェクト名や説明に含まれるキーワードを入力してください"
        )
    
    # 検索ボタン
    with col2:
        apply_filter = st.button(
            "検索",
            key=f"{key_prefix}search_button",
            use_container_width=True
        )
    
    # タグによるフィルタリング
    all_tags = sorted(list(pm.get_all_tags()))
    
    if all_tags:
        selected_tags = st.multiselect(
            "タグでフィルタ",
            options=all_tags,
            default=st.session_state[f"{key_prefix}selected_tags"],
            key=f"{key_prefix}tag_filter"
        )
    else:
        selected_tags = []
    
    # 状態を更新
    st.session_state[f"{key_prefix}search_query"] = search_query
    st.session_state[f"{key_prefix}selected_tags"] = selected_tags
    
    return search_query, selected_tags, apply_filter
