"""
ui.components.forms.data_cleaning.components.problem_list

問題リストを表示するコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Tuple
import altair as alt

from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator


class ProblemListComponent:
    """
    データ検証問題リストコンポーネント
    
    検出された問題をインタラクティブに表示するための UI コンポーネント
    """
    
    def __init__(self, key: str = "problem_list"):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "problem_list"
        """
        self.key = key
        
        # セッション状態の初期化
        if f"{self.key}_selected_problems" not in st.session_state:
            st.session_state[f"{self.key}_selected_problems"] = []
        
        if f"{self.key}_filter_config" not in st.session_state:
            st.session_state[f"{self.key}_filter_config"] = {
                "problem_types": [],
                "severity": ["error", "warning", "info"],
                "min_score": 0
            }
    
    def render(self, 
              problem_records: pd.DataFrame,
              on_select: Optional[Callable[[List[int]], None]] = None) -> Tuple[pd.DataFrame, List[int]]:
        """
        問題リストをレンダリング
        
        Parameters
        ----------
        problem_records : pd.DataFrame
            問題レコードのデータフレーム
        on_select : Optional[Callable[[List[int]], None]], optional
            問題選択時のコールバック関数, by default None
            
        Returns
        -------
        Tuple[pd.DataFrame, List[int]]
            フィルタリングされた問題レコードのデータフレームと選択された問題インデックスのリスト
        """
        if problem_records.empty:
            st.info("検出された問題はありません。")
            return problem_records, []
        
        # フィルタリングコントロールを表示
        self._render_filters(problem_records)
        
        # フィルタを適用
        filtered_records = self._apply_filters(problem_records)
        
        if filtered_records.empty:
            st.info("フィルター条件に一致する問題はありません。")
            return filtered_records, []
        
        # 問題レコードの表示
        st.write(f"**{len(filtered_records)}件の問題が見つかりました**")
        
        # 重要度に応じた色を設定
        def highlight_severity(row):
            """重要度によるスタイリング"""
            severity = row["重要度"]
            if severity == "error":
                return ["background-color: #ffcccc"] * len(row)
            elif severity == "warning":
                return ["background-color: #fff2cc"] * len(row)
            elif severity == "info":
                return ["background-color: #e6f2ff"] * len(row)
            return [""] * len(row)
        
        # 選択可能なインデックスリストの表示
        with st.expander("問題リスト", expanded=True):
            # スタイルを適用して表示
            styled_df = filtered_records.style.apply(highlight_severity, axis=1)
            st.dataframe(styled_df, use_container_width=True)
            
            # 選択コントロール
            select_all = st.checkbox("すべての問題を選択", key=f"{self.key}_select_all")
            
            if select_all:
                st.session_state[f"{self.key}_selected_problems"] = filtered_records["インデックス"].tolist()
            else:
                # 選択コントロール
                selected_indices = st.multiselect(
                    "修正する問題を選択:",
                    options=filtered_records["インデックス"].tolist(),
                    default=st.session_state[f"{self.key}_selected_problems"],
                    key=f"{self.key}_selected_indices"
                )
                
                # 選択状態を更新
                st.session_state[f"{self.key}_selected_problems"] = selected_indices
        
        # 選択されたインデックスを取得
        selected_problems = st.session_state[f"{self.key}_selected_problems"]
        
        # 選択結果を表示
        if selected_problems:
            st.write(f"選択された問題: {len(selected_problems)}件")
            
            # 選択されたレコードを表示
            selected_records = filtered_records[filtered_records["インデックス"].isin(selected_problems)]
            st.dataframe(selected_records, use_container_width=True)
            
            # コールバック関数を呼び出し
            if on_select:
                on_select(selected_problems)
        
        return filtered_records, selected_problems
    
    def _render_filters(self, problem_records: pd.DataFrame) -> None:
        """
        フィルタリングコントロールをレンダリング
        
        Parameters
        ----------
        problem_records : pd.DataFrame
            問題レコードのデータフレーム
        """
        st.write("**問題フィルタリング**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 問題タイプフィルタ
            if "問題タイプ" in problem_records.columns:
                # 問題タイプのユニークな値を抽出
                all_types = []
                for type_str in problem_records["問題タイプ"].dropna().unique():
                    if isinstance(type_str, str):
                        all_types.extend([t.strip() for t in type_str.split(",")])
                
                unique_types = sorted(list(set(all_types)))
                
                if unique_types:
                    selected_types = st.multiselect(
                        "問題タイプでフィルタリング:",
                        options=unique_types,
                        default=st.session_state[f"{self.key}_filter_config"]["problem_types"],
                        key=f"{self.key}_filter_type"
                    )
                    
                    st.session_state[f"{self.key}_filter_config"]["problem_types"] = selected_types
        
        with col2:
            # 重要度フィルタ
            if "重要度" in problem_records.columns:
                severity_mapping = {
                    "error": "エラー",
                    "warning": "警告",
                    "info": "情報"
                }
                
                severity_options = ["error", "warning", "info"]
                
                selected_severity = st.multiselect(
                    "重要度でフィルタリング:",
                    options=severity_options,
                    default=st.session_state[f"{self.key}_filter_config"]["severity"],
                    format_func=lambda x: severity_mapping.get(x, x),
                    key=f"{self.key}_filter_severity"
                )
                
                if not selected_severity:  # 何も選択されていない場合はデフォルトに戻す
                    selected_severity = ["error", "warning", "info"]
                
                st.session_state[f"{self.key}_filter_config"]["severity"] = selected_severity
    
    def _apply_filters(self, problem_records: pd.DataFrame) -> pd.DataFrame:
        """
        フィルタを適用
        
        Parameters
        ----------
        problem_records : pd.DataFrame
            問題レコードのデータフレーム
            
        Returns
        -------
        pd.DataFrame
            フィルタリングされたデータフレーム
        """
        if problem_records.empty:
            return problem_records
        
        filtered_records = problem_records.copy()
        
        # 問題タイプフィルタを適用
        problem_types = st.session_state[f"{self.key}_filter_config"]["problem_types"]
        if problem_types and "問題タイプ" in filtered_records.columns:
            mask = filtered_records["問題タイプ"].apply(
                lambda x: any(pt in str(x) for pt in problem_types) if pd.notna(x) else False
            )
            filtered_records = filtered_records[mask]
        
        # 重要度フィルタを適用
        severity = st.session_state[f"{self.key}_filter_config"]["severity"]
        if severity and "重要度" in filtered_records.columns and severity != ["error", "warning", "info"]:
            filtered_records = filtered_records[filtered_records["重要度"].isin(severity)]
        
        return filtered_records
    
    def get_selected_problems(self) -> List[int]:
        """
        選択された問題インデックスを取得
        
        Returns
        -------
        List[int]
            選択された問題インデックスのリスト
        """
        return st.session_state.get(f"{self.key}_selected_problems", [])
    
    def clear_selection(self) -> None:
        """選択をクリア"""
        st.session_state[f"{self.key}_selected_problems"] = []
    
    def add_to_selection(self, indices: List[int]) -> None:
        """
        選択に問題インデックスを追加
        
        Parameters
        ----------
        indices : List[int]
            追加する問題インデックスのリスト
        """
        current = set(st.session_state.get(f"{self.key}_selected_problems", []))
        current.update(indices)
        st.session_state[f"{self.key}_selected_problems"] = list(current)
    
    def remove_from_selection(self, indices: List[int]) -> None:
        """
        選択から問題インデックスを削除
        
        Parameters
        ----------
        indices : List[int]
            削除する問題インデックスのリスト
        """
        current = set(st.session_state.get(f"{self.key}_selected_problems", []))
        current = current - set(indices)
        st.session_state[f"{self.key}_selected_problems"] = list(current)
