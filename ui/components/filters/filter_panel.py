"""
ui.components.filters.filter_panel

フィルターパネルコンポーネントを提供するモジュール
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable, Union
import json
import uuid
from datetime import datetime

from sailing_data_processor.filters.filter_system import (
    FilterCondition, FilterGroup, FilterSet, FilterManager,
    create_date_range_filter, create_tag_filter, create_text_search_filter
)


class FilterPanel:
    """
    フィルターパネルコンポーネント
    
    フィルター条件を作成、編集、保存するためのUIコンポーネント
    """
    
    def __init__(self, 
                key: str = "filter_panel", 
                filter_manager: Optional[FilterManager] = None,
                on_filter_change: Optional[Callable[[FilterSet], None]] = None,
                available_fields: Optional[Dict[str, str]] = None,
                available_operators: Optional[Dict[str, str]] = None,
                available_tags: Optional[List[str]] = None):
        """
        フィルターパネルの初期化
        
        Parameters
        ----------
        key : str, optional
            Streamlitウィジェットのキー, by default "filter_panel"
        filter_manager : Optional[FilterManager], optional
            フィルター管理インスタンス, by default None
        on_filter_change : Optional[Callable[[FilterSet], None]], optional
            フィルター変更時のコールバック関数, by default None
        available_fields : Optional[Dict[str, str]], optional
            利用可能なフィールドの辞書（キー：フィールド識別子、値：表示名）, by default None
        available_operators : Optional[Dict[str, str]], optional
            利用可能な演算子の辞書（キー：演算子識別子、値：表示名）, by default None
        available_tags : Optional[List[str]], optional
            利用可能なタグのリスト, by default None
        """
        self.key = key
        self.filter_manager = filter_manager or FilterManager()
        self.on_filter_change = on_filter_change
        
        # 利用可能なフィールド（デフォルト設定）
        self.available_fields = available_fields or {
            "name": "名前",
            "description": "説明",
            "created_at": "作成日",
            "updated_at": "更新日",
            "tags": "タグ",
            "category": "カテゴリ"
        }
        
        # 利用可能な演算子（デフォルト設定）
        self.available_operators = available_operators or {
            "eq": "等しい",
            "neq": "等しくない",
            "contains": "含む",
            "starts_with": "で始まる",
            "ends_with": "で終わる",
            "gt": "より大きい",
            "gte": "以上",
            "lt": "より小さい",
            "lte": "以下",
            "in": "リストに含まれる",
            "between": "範囲内",
            "exists": "存在する",
            "not_exists": "存在しない",
            "date_between": "日付が範囲内",
            "date_eq": "日付が等しい",
            "date_gt": "日付がより後",
            "date_lt": "日付がより前",
            "has_tag": "タグを持つ",
            "has_any_tag": "いずれかのタグを持つ",
            "has_all_tags": "すべてのタグを持つ"
        }
        
        # 利用可能なタグ
        self.available_tags = available_tags or []
        
        # セッション状態の初期化
        if f"{key}_active_filter" not in st.session_state:
            st.session_state[f"{key}_active_filter"] = None
        if f"{key}_edit_mode" not in st.session_state:
            st.session_state[f"{key}_edit_mode"] = False
        if f"{key}_tmp_conditions" not in st.session_state:
            st.session_state[f"{key}_tmp_conditions"] = []
        if f"{key}_tmp_filter_name" not in st.session_state:
            st.session_state[f"{key}_tmp_filter_name"] = ""
    
    def render(self) -> Optional[FilterSet]:
        """
        フィルターパネルをレンダリング
        
        Returns
        -------
        Optional[FilterSet]
            現在アクティブなフィルターセット、または None
        """
        st.markdown("### フィルタ管理")
        
        # フィルターの選択または新規作成
        col1, col2 = st.columns([3, 1])
        
        with col1:
            filter_sets = self.filter_manager.get_all_filter_sets()
            filter_names = ["新規フィルタ"] + [fs.name for fs in filter_sets]
            selected_filter = st.selectbox(
                "フィルタを選択",
                options=filter_names,
                index=0,
                key=f"{self.key}_filter_select"
            )
            
            if selected_filter != "新規フィルタ":
                selected_filter_set = next((fs for fs in filter_sets if fs.name == selected_filter), None)
                st.session_state[f"{self.key}_active_filter"] = selected_filter_set
                st.session_state[f"{self.key}_edit_mode"] = False
            else:
                st.session_state[f"{self.key}_active_filter"] = None
                st.session_state[f"{self.key}_edit_mode"] = True
                st.session_state[f"{self.key}_tmp_filter_name"] = f"新しいフィルタ {datetime.now().strftime('%Y-%m-%d')}"
                st.session_state[f"{self.key}_tmp_conditions"] = []
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.session_state[f"{self.key}_active_filter"] is not None:
                edit_button = st.button("編集", key=f"{self.key}_edit_button")
                if edit_button:
                    st.session_state[f"{self.key}_edit_mode"] = True
                    st.session_state[f"{self.key}_tmp_filter_name"] = st.session_state[f"{self.key}_active_filter"].name
                    
                    # 一時的な条件をセットアップ
                    tmp_conditions = []
                    for group in st.session_state[f"{self.key}_active_filter"].groups:
                        for condition in group.conditions:
                            tmp_conditions.append({
                                "id": str(uuid.uuid4()),
                                "field": condition.field,
                                "operator": condition.operator,
                                "value": condition.value,
                                "name": condition.name
                            })
                    st.session_state[f"{self.key}_tmp_conditions"] = tmp_conditions
            else:
                st.markdown("<div style='height: 38px;'></div>", unsafe_allow_html=True)
        
        # フィルター編集モード
        if st.session_state[f"{self.key}_edit_mode"]:
            with st.form(key=f"{self.key}_filter_form"):
                filter_name = st.text_input(
                    "フィルタ名",
                    value=st.session_state[f"{self.key}_tmp_filter_name"],
                    key=f"{self.key}_filter_name_input"
                )
                
                # 条件の編集
                st.markdown("#### フィルタ条件")
                
                # 既存の条件を表示
                for i, condition in enumerate(st.session_state[f"{self.key}_tmp_conditions"]):
                    cols = st.columns([3, 3, 3, 1])
                    with cols[0]:
                        field_options = list(self.available_fields.items())
                        field_index = next((i for i, (k, _) in enumerate(field_options) if k == condition["field"]), 0)
                        selected_field_tuple = st.selectbox(
                            "フィールド",
                            options=field_options,
                            index=field_index,
                            format_func=lambda x: x[1],
                            key=f"{self.key}_field_{i}"
                        )
                        condition["field"] = selected_field_tuple[0]
                    
                    with cols[1]:
                        operator_options = list(self.available_operators.items())
                        operator_index = next((i for i, (k, _) in enumerate(operator_options) if k == condition["operator"]), 0)
                        selected_operator_tuple = st.selectbox(
                            "演算子",
                            options=operator_options,
                            index=operator_index,
                            format_func=lambda x: x[1],
                            key=f"{self.key}_operator_{i}"
                        )
                        condition["operator"] = selected_operator_tuple[0]
                    
                    with cols[2]:
                        # 演算子に基づいて適切な入力フィールドを表示
                        if condition["operator"] in ["has_tag", "has_any_tag", "has_all_tags"]:
                            # タグ選択
                            if isinstance(condition["value"], list):
                                default_value = condition["value"]
                            elif condition["value"] is not None:
                                default_value = [condition["value"]]
                            else:
                                default_value = []
                            
                            condition["value"] = st.multiselect(
                                "値",
                                options=self.available_tags,
                                default=default_value,
                                key=f"{self.key}_value_{i}"
                            )
                        elif condition["operator"] in ["between", "date_between"]:
                            # 範囲入力
                            col1, col2 = st.columns(2)
                            with col1:
                                if isinstance(condition["value"], list) and len(condition["value"]) > 0:
                                    default_min = condition["value"][0]
                                else:
                                    default_min = ""
                                min_value = st.text_input(
                                    "最小値",
                                    value=default_min,
                                    key=f"{self.key}_min_{i}"
                                )
                            
                            with col2:
                                if isinstance(condition["value"], list) and len(condition["value"]) > 1:
                                    default_max = condition["value"][1]
                                else:
                                    default_max = ""
                                max_value = st.text_input(
                                    "最大値",
                                    value=default_max,
                                    key=f"{self.key}_max_{i}"
                                )
                            
                            condition["value"] = [min_value, max_value]
                        elif condition["operator"] in ["in", "not_in"]:
                            # リスト入力
                            if isinstance(condition["value"], list):
                                default_value = ", ".join(map(str, condition["value"]))
                            elif condition["value"] is not None:
                                default_value = str(condition["value"])
                            else:
                                default_value = ""
                            
                            list_value = st.text_input(
                                "値（カンマ区切り）",
                                value=default_value,
                                key=f"{self.key}_value_{i}"
                            )
                            condition["value"] = [item.strip() for item in list_value.split(",") if item.strip()]
                        elif condition["operator"] in ["exists", "not_exists"]:
                            # 値不要
                            st.markdown("値の入力は不要です")
                            condition["value"] = None
                        else:
                            # 通常の値入力
                            if condition["value"] is None:
                                default_value = ""
                            else:
                                default_value = str(condition["value"])
                            
                            condition["value"] = st.text_input(
                                "値",
                                value=default_value,
                                key=f"{self.key}_value_{i}"
                            )
                    
                    with cols[3]:
                        st.markdown("<br>", unsafe_allow_html=True)
                        remove_button = st.button("削除", key=f"{self.key}_remove_{i}")
                        if remove_button:
                            st.session_state[f"{self.key}_tmp_conditions"].pop(i)
                            st.rerun()
                
                # 新しい条件を追加するボタン
                add_condition = st.button("条件を追加", key=f"{self.key}_add_condition")
                if add_condition:
                    st.session_state[f"{self.key}_tmp_conditions"].append({
                        "id": str(uuid.uuid4()),
                        "field": list(self.available_fields.keys())[0],
                        "operator": "eq",
                        "value": "",
                        "name": "新しい条件"
                    })
                    st.rerun()
                
                # フッターボタン
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    save_button = st.form_submit_button("保存")
                with col2:
                    clear_button = st.form_submit_button("クリア")
                with col3:
                    cancel_button = st.form_submit_button("キャンセル")
                
                if save_button:
                    # フィルターセットを作成して保存
                    filter_set = self._create_filter_set_from_conditions(
                        filter_name, 
                        st.session_state[f"{self.key}_tmp_conditions"]
                    )
                    
                    if filter_set:
                        self.filter_manager.add_filter_set(filter_set)
                        st.session_state[f"{self.key}_active_filter"] = filter_set
                        st.session_state[f"{self.key}_edit_mode"] = False
                        
                        if self.on_filter_change:
                            self.on_filter_change(filter_set)
                        
                        st.success(f"フィルタ '{filter_name}' を保存しました")
                        st.rerun()
                    else:
                        st.warning("フィルタの作成に失敗しました。条件を正しく設定してください。")
                
                if clear_button:
                    st.session_state[f"{self.key}_tmp_conditions"] = []
                    st.rerun()
                
                if cancel_button:
                    st.session_state[f"{self.key}_edit_mode"] = False
                    st.rerun()
        
        # フィルター表示モード（編集モードでない場合）
        elif st.session_state[f"{self.key}_active_filter"] is not None:
            active_filter = st.session_state[f"{self.key}_active_filter"]
            
            st.markdown(f"#### フィルタ詳細: {active_filter.name}")
            
            # フィルター情報
            st.markdown(f"作成日: {active_filter.created_at[:10]}")
            st.markdown(f"更新日: {active_filter.updated_at[:10]}")
            
            # 条件の表示
            st.markdown("##### フィルタ条件")
            for i, group in enumerate(active_filter.groups):
                st.markdown(f"**グループ {i+1}: {group.name}** ({group.operator})")
                for j, condition in enumerate(group.conditions):
                    field_display = self.available_fields.get(condition.field, condition.field)
                    operator_display = self.available_operators.get(condition.operator, condition.operator)
                    
                    value_display = self._format_value_for_display(condition.value, condition.operator)
                    
                    st.markdown(f"{j+1}. {field_display} {operator_display} {value_display}")
            
            # フィルター操作ボタン
            col1, col2 = st.columns(2)
            with col1:
                apply_button = st.button("このフィルタを適用", key=f"{self.key}_apply_button")
                if apply_button and self.on_filter_change:
                    self.on_filter_change(active_filter)
                    st.success(f"フィルタ '{active_filter.name}' を適用しました")
            
            with col2:
                delete_button = st.button("このフィルタを削除", key=f"{self.key}_delete_button")
                if delete_button:
                    if self.filter_manager.remove_filter_set(active_filter.name):
                        st.session_state[f"{self.key}_active_filter"] = None
                        st.success(f"フィルタ '{active_filter.name}' を削除しました")
                        st.rerun()
                    else:
                        st.error(f"フィルタ '{active_filter.name}' の削除に失敗しました")
        
        return st.session_state[f"{self.key}_active_filter"]
    
    def _create_filter_set_from_conditions(self, 
                                          name: str, 
                                          conditions: List[Dict[str, Any]]) -> Optional[FilterSet]:
        """
        一時的な条件リストからフィルターセットを作成
        
        Parameters
        ----------
        name : str
            フィルター名
        conditions : List[Dict[str, Any]]
            条件のリスト
            
        Returns
        -------
        Optional[FilterSet]
            作成されたフィルターセット、失敗した場合はNone
        """
        if not conditions:
            return None
        
        if not name:
            name = f"Filter {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # グループを作成
        group = FilterGroup(name="メイングループ")
        
        # 条件を追加
        for condition_data in conditions:
            try:
                # 値を適切な型に変換
                value = self._convert_value_type(condition_data["value"], condition_data["operator"])
                
                # 条件を作成
                condition = FilterCondition(
                    name=condition_data.get("name", f"{condition_data['field']} {condition_data['operator']}"),
                    field=condition_data["field"],
                    operator=condition_data["operator"],
                    value=value
                )
                
                group.add_condition(condition)
            except Exception as e:
                print(f"条件の作成に失敗しました: {e}")
                continue
        
        # フィルターセットを作成
        filter_set = FilterSet(name=name)
        filter_set.add_group(group)
        
        return filter_set
    
    def _convert_value_type(self, value: Any, operator: str) -> Any:
        """
        操作に基づいて値を適切な型に変換
        
        Parameters
        ----------
        value : Any
            変換する値
        operator : str
            演算子
            
        Returns
        -------
        Any
            変換された値
        """
        if operator in ["exists", "not_exists"]:
            return None
        
        if operator in ["between", "date_between"] and isinstance(value, list):
            return value
        
        if operator in ["in", "not_in", "has_any_tag", "has_all_tags"] and isinstance(value, list):
            return value
        
        if operator in ["has_tag"] and isinstance(value, list) and len(value) > 0:
            return value[0]
        
        # 数値に変換を試みる
        if operator in ["gt", "gte", "lt", "lte"]:
            try:
                return float(value)
            except:
                return value
        
        return value
    
    def _format_value_for_display(self, value: Any, operator: str) -> str:
        """
        表示用に値をフォーマット
        
        Parameters
        ----------
        value : Any
            フォーマットする値
        operator : str
            演算子
            
        Returns
        -------
        str
            フォーマットされた値の文字列
        """
        if value is None:
            return "<なし>"
        
        if isinstance(value, list):
            if operator in ["between", "date_between"] and len(value) == 2:
                return f"{value[0]} から {value[1]}"
            else:
                return ", ".join(map(str, value))
        
        return str(value)
    
    def update_available_tags(self, tags: List[str]) -> None:
        """
        利用可能なタグのリストを更新
        
        Parameters
        ----------
        tags : List[str]
            新しいタグのリスト
        """
        self.available_tags = tags
    
    def update_available_fields(self, fields: Dict[str, str]) -> None:
        """
        利用可能なフィールドのマッピングを更新
        
        Parameters
        ----------
        fields : Dict[str, str]
            新しいフィールドのマッピング（キー：フィールド識別子、値：表示名）
        """
        self.available_fields = fields


def filter_panel(key: str = "filter_panel", 
                filter_manager: Optional[FilterManager] = None,
                on_filter_change: Optional[Callable[[FilterSet], None]] = None,
                available_fields: Optional[Dict[str, str]] = None,
                available_operators: Optional[Dict[str, str]] = None,
                available_tags: Optional[List[str]] = None) -> Optional[FilterSet]:
    """
    フィルターパネルコンポーネントの簡易関数

    Parameters
    ----------
    key : str, optional
        Streamlitウィジェットのキー, by default "filter_panel"
    filter_manager : Optional[FilterManager], optional
        フィルター管理インスタンス, by default None
    on_filter_change : Optional[Callable[[FilterSet], None]], optional
        フィルター変更時のコールバック関数, by default None
    available_fields : Optional[Dict[str, str]], optional
        利用可能なフィールドの辞書（キー：フィールド識別子、値：表示名）, by default None
    available_operators : Optional[Dict[str, str]], optional
        利用可能な演算子の辞書（キー：演算子識別子、値：表示名）, by default None
    available_tags : Optional[List[str]], optional
        利用可能なタグのリスト, by default None

    Returns
    -------
    Optional[FilterSet]
        現在アクティブなフィルターセット
    """
    panel = FilterPanel(
        key=key,
        filter_manager=filter_manager,
        on_filter_change=on_filter_change,
        available_fields=available_fields,
        available_operators=available_operators,
        available_tags=available_tags
    )
    
    return panel.render()
