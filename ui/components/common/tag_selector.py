# -*- coding: utf-8 -*-
"""
ui.components.common.tag_selector

タグ選択UIコンポーネント
"""

import streamlit as st
from typing import List, Callable, Optional, Set

from ..styles import Colors


class TagSelector:
    """
    タグ選択コンポーネント
    
    Parameters
    ----------
    key : str
        コンポーネントの一意のキー
    available_tags : List[str]
        選択可能なタグのリスト
    selected_tags : List[str]
        初期選択されているタグのリスト
    on_change : Optional[Callable[[List[str]], None]]
        タグ選択変更時のコールバック関数
    add_new_tag : bool
        新しいタグの追加を許可するかどうか
    placeholder : str
        プレースホルダーテキスト
    label : str
        ラベルテキスト
    """
    
    def __init__(
        self,
        key: str,
        available_tags: List[str] = None,
        selected_tags: List[str] = None,
        on_change: Optional[Callable[[List[str]], None]] = None,
        add_new_tag: bool = True,
        placeholder: str = "タグを選択...",
        label: str = "タグ"
    ):
        """
        初期化
        
        Parameters
        ----------
        key : str
            コンポーネントの一意のキー
        available_tags : List[str], optional
            選択可能なタグのリスト, by default None
        selected_tags : List[str], optional
            初期選択されているタグのリスト, by default None
        on_change : Optional[Callable[[List[str]], None]], optional
            タグ選択変更時のコールバック関数, by default None
        add_new_tag : bool, optional
            新しいタグの追加を許可するかどうか, by default True
        placeholder : str, optional
            プレースホルダーテキスト, by default "タグを選択..."
        label : str, optional
            ラベルテキスト, by default "タグ"
        """
        self.key = key
        self.available_tags = available_tags or []
        self.selected_tags = selected_tags or []
        self.on_change = on_change
        self.add_new_tag = add_new_tag
        self.placeholder = placeholder
        self.label = label
        
        # セッション状態の初期化
        if f"{key}_selected" not in st.session_state:
            st.session_state[f"{key}_selected"] = set(self.selected_tags)
        
        if f"{key}_new_tag" not in st.session_state:
            st.session_state[f"{key}_new_tag"] = ""
    
    def render(self) -> List[str]:
        """
        タグ選択コンポーネントをレンダリング
        
        Returns
        -------
        List[str]
            選択されたタグのリスト
        """
        # 利用可能なすべてのタグ（選択中のタグを含む）
        all_tags = list(set(self.available_tags + list(st.session_state[f"{self.key}_selected"])))
        
        # マルチセレクトによるタグ選択
        selected = st.multiselect(
            self.label,
            options=all_tags,
            default=list(st.session_state[f"{self.key}_selected"]),
            placeholder=self.placeholder,
            key=f"{self.key}_multiselect"
        )
        
        # 選択状態を更新
        st.session_state[f"{self.key}_selected"] = set(selected)
        
        # 新しいタグの追加機能
        if self.add_new_tag:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                new_tag = st.text_input(
                    "新しいタグを追加",
                    key=f"{self.key}_new_tag_input",
                    value=st.session_state[f"{self.key}_new_tag"]
                )
                st.session_state[f"{self.key}_new_tag"] = new_tag
            
            with col2:
                st.write("")  # 垂直方向の位置調整
                st.write("")
                if st.button("追加", key=f"{self.key}_add_new_tag_btn"):
                    if new_tag and new_tag not in st.session_state[f"{self.key}_selected"]:
                        st.session_state[f"{self.key}_selected"].add(new_tag)
                        st.session_state[f"{self.key}_new_tag"] = ""
                        st.rerun()
        
        # 選択されたタグを表示
        if st.session_state[f"{self.key}_selected"]:
            st.caption("選択中のタグ:")
            cols = st.columns(min(4, len(st.session_state[f"{self.key}_selected"])))
            
            for i, tag in enumerate(sorted(st.session_state[f"{self.key}_selected"])):
                with cols[i % len(cols)]:
                    # タグと削除ボタンを表示
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.code(tag, language=None)
                    with col2:
                        if st.button("×", key=f"{self.key}_remove_{i}"):
                            st.session_state[f"{self.key}_selected"].remove(tag)
                            st.rerun()
        
        # コールバック関数を呼び出し
        if self.on_change:
            self.on_change(list(st.session_state[f"{self.key}_selected"]))
        
        return list(st.session_state[f"{self.key}_selected"])


def render_tag_selector(
    key: str,
    available_tags: List[str] = None,
    selected_tags: List[str] = None,
    add_new_tag: bool = True,
    placeholder: str = "タグを選択...",
    label: str = "タグ"
) -> List[str]:
    """
    タグ選択コンポーネントのレンダリング関数
    
    Parameters
    ----------
    key : str
        コンポーネントの一意のキー
    available_tags : List[str], optional
        選択可能なタグのリスト, by default None
    selected_tags : List[str], optional
        初期選択されているタグのリスト, by default None
    add_new_tag : bool, optional
        新しいタグの追加を許可するかどうか, by default True
    placeholder : str, optional
        プレースホルダーテキスト, by default "タグを選択..."
    label : str, optional
        ラベルテキスト, by default "タグ"
        
    Returns
    -------
    List[str]
        選択されたタグのリスト
    """
    selector = TagSelector(
        key=key,
        available_tags=available_tags or [],
        selected_tags=selected_tags or [],
        add_new_tag=add_new_tag,
        placeholder=placeholder,
        label=label
    )
    
    return selector.render()
