"""
ui.components.search.search_bar

検索バーコンポーネントを提供するモジュール
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable, Union

class SearchBar:
    """
    検索バーコンポーネント
    
    検索入力、フィルターオプション、ソートオプションを提供するUIコンポーネント
    """
    
    def __init__(self, 
                key: str = "search", 
                placeholder: str = "検索...",
                search_callback: Optional[Callable[[str], None]] = None,
                show_filters: bool = True,
                available_tags: Optional[List[str]] = None,
                available_categories: Optional[List[str]] = None):
        """
        検索バーの初期化
        
        Parameters
        ----------
        key : str, optional
            Streamlitウィジェットのキー, by default "search"
        placeholder : str, optional
            検索プレースホルダーテキスト, by default "検索..."
        search_callback : Optional[Callable[[str], None]], optional
            検索実行時のコールバック関数, by default None
        show_filters : bool, optional
            フィルタオプションの表示フラグ, by default True
        available_tags : Optional[List[str]], optional
            選択可能なタグのリスト, by default None
        available_categories : Optional[List[str]], optional
            選択可能なカテゴリのリスト, by default None
        """
        self.key = key
        self.placeholder = placeholder
        self.search_callback = search_callback
        self.show_filters = show_filters
        self.available_tags = available_tags or []
        self.available_categories = available_categories or []
        
        # セッション状態の初期化
        if f"{key}_query" not in st.session_state:
            st.session_state[f"{key}_query"] = ""
        if f"{key}_tags" not in st.session_state:
            st.session_state[f"{key}_tags"] = []
        if f"{key}_categories" not in st.session_state:
            st.session_state[f"{key}_categories"] = []
        if f"{key}_date_range" not in st.session_state:
            st.session_state[f"{key}_date_range"] = {"start": None, "end": None}
        if f"{key}_sort_by" not in st.session_state:
            st.session_state[f"{key}_sort_by"] = "relevance"
        if f"{key}_sort_order" not in st.session_state:
            st.session_state[f"{key}_sort_order"] = "desc"
        if f"{key}_expanded" not in st.session_state:
            st.session_state[f"{key}_expanded"] = False
    
    def render(self) -> Dict[str, Any]:
        """
        検索バーをレンダリング
        
        Returns
        -------
        Dict[str, Any]
            検索設定を含む辞書
        """
        # 検索セクションのスタイル
        st.markdown("""
        <style>
        .search-container {
            margin-bottom: 1rem;
        }
        .filter-expander {
            margin-top: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # コンテナの開始
        with st.container():
            # 検索バー
            search_col, button_col = st.columns([5, 1])
            
            with search_col:
                query = st.text_input(
                    "検索",
                    value=st.session_state[f"{self.key}_query"],
                    placeholder=self.placeholder,
                    key=f"{self.key}_input"
                )
                st.session_state[f"{self.key}_query"] = query
            
            with button_col:
                st.markdown("<br>", unsafe_allow_html=True)
                search_clicked = st.button("検索", key=f"{self.key}_button")
            
            # フィルターオプション
            if self.show_filters:
                with st.expander("詳細検索", expanded=st.session_state[f"{self.key}_expanded"]):
                    st.session_state[f"{self.key}_expanded"] = True
                    
                    # タグによるフィルタ
                    if self.available_tags:
                        selected_tags = st.multiselect(
                            "タグでフィルタ",
                            options=self.available_tags,
                            default=st.session_state[f"{self.key}_tags"],
                            key=f"{self.key}_tags_select"
                        )
                        st.session_state[f"{self.key}_tags"] = selected_tags
                    
                    # カテゴリによるフィルタ
                    if self.available_categories:
                        selected_categories = st.multiselect(
                            "カテゴリでフィルタ",
                            options=self.available_categories,
                            default=st.session_state[f"{self.key}_categories"],
                            key=f"{self.key}_categories_select"
                        )
                        st.session_state[f"{self.key}_categories"] = selected_categories
                    
                    # 日付範囲によるフィルタ
                    col1, col2 = st.columns(2)
                    with col1:
                        start_date = st.date_input(
                            "開始日",
                            value=st.session_state[f"{self.key}_date_range"]["start"],
                            key=f"{self.key}_start_date"
                        )
                        st.session_state[f"{self.key}_date_range"]["start"] = start_date
                    
                    with col2:
                        end_date = st.date_input(
                            "終了日",
                            value=st.session_state[f"{self.key}_date_range"]["end"],
                            key=f"{self.key}_end_date"
                        )
                        st.session_state[f"{self.key}_date_range"]["end"] = end_date
                    
                    # ソートオプション
                    col1, col2 = st.columns(2)
                    with col1:
                        sort_by = st.selectbox(
                            "並び替え",
                            options=["関連度", "名前", "作成日", "更新日"],
                            index=["関連度", "名前", "作成日", "更新日"].index(self._get_sort_by_display()),
                            key=f"{self.key}_sort_by_select"
                        )
                        st.session_state[f"{self.key}_sort_by"] = self._get_sort_by_value(sort_by)
                    
                    with col2:
                        sort_order = st.selectbox(
                            "順序",
                            options=["降順", "昇順"],
                            index=0 if st.session_state[f"{self.key}_sort_order"] == "desc" else 1,
                            key=f"{self.key}_sort_order_select"
                        )
                        st.session_state[f"{self.key}_sort_order"] = "desc" if sort_order == "降順" else "asc"
                    
                    # 詳細検索ボタン
                    advanced_search = st.button("詳細検索を実行", key=f"{self.key}_advanced_search")
                    
                    if advanced_search and self.search_callback:
                        self.search_callback(self.get_search_params())
            
            # 通常の検索ボタンが押された場合
            if search_clicked and self.search_callback:
                self.search_callback(self.get_search_params())
        
        # 検索パラメータを返す
        return self.get_search_params()
    
    def get_search_params(self) -> Dict[str, Any]:
        """
        現在の検索パラメータを取得
        
        Returns
        -------
        Dict[str, Any]
            検索パラメータを含む辞書
        """
        date_range = {}
        
        if st.session_state[f"{self.key}_date_range"]["start"]:
            date_range["start"] = st.session_state[f"{self.key}_date_range"]["start"].isoformat()
        
        if st.session_state[f"{self.key}_date_range"]["end"]:
            date_range["end"] = st.session_state[f"{self.key}_date_range"]["end"].isoformat()
        
        return {
            "query": st.session_state[f"{self.key}_query"],
            "tags": st.session_state[f"{self.key}_tags"],
            "categories": st.session_state[f"{self.key}_categories"],
            "date_range": date_range if date_range else None,
            "sort_by": st.session_state[f"{self.key}_sort_by"],
            "sort_order": st.session_state[f"{self.key}_sort_order"]
        }
    
    def update_available_tags(self, tags: List[str]) -> None:
        """
        選択可能なタグリストを更新
        
        Parameters
        ----------
        tags : List[str]
            新しいタグリスト
        """
        self.available_tags = tags
    
    def update_available_categories(self, categories: List[str]) -> None:
        """
        選択可能なカテゴリリストを更新
        
        Parameters
        ----------
        categories : List[str]
            新しいカテゴリリスト
        """
        self.available_categories = categories
    
    def _get_sort_by_display(self) -> str:
        """ソート項目の表示名を取得"""
        mapping = {
            "relevance": "関連度",
            "name": "名前",
            "created_at": "作成日",
            "updated_at": "更新日"
        }
        return mapping.get(st.session_state[f"{self.key}_sort_by"], "関連度")
    
    def _get_sort_by_value(self, display_name: str) -> str:
        """表示名からソート項目の値を取得"""
        mapping = {
            "関連度": "relevance",
            "名前": "name",
            "作成日": "created_at",
            "更新日": "updated_at"
        }
        return mapping.get(display_name, "relevance")


def search_bar(key: str = "search", 
              placeholder: str = "検索...",
              search_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
              show_filters: bool = True,
              available_tags: Optional[List[str]] = None,
              available_categories: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    検索バーコンポーネントの簡易関数

    Parameters
    ----------
    key : str, optional
        Streamlitウィジェットのキー, by default "search"
    placeholder : str, optional
        検索プレースホルダーテキスト, by default "検索..."
    search_callback : Optional[Callable[[Dict[str, Any]], None]], optional
        検索実行時のコールバック関数, by default None
    show_filters : bool, optional
        フィルタオプションの表示フラグ, by default True
    available_tags : Optional[List[str]], optional
        選択可能なタグのリスト, by default None
    available_categories : Optional[List[str]], optional
        選択可能なカテゴリのリスト, by default None

    Returns
    -------
    Dict[str, Any]
        検索パラメータを含む辞書
    """
    search_component = SearchBar(
        key=key,
        placeholder=placeholder,
        search_callback=search_callback,
        show_filters=show_filters,
        available_tags=available_tags,
        available_categories=available_categories
    )
    
    return search_component.render()
