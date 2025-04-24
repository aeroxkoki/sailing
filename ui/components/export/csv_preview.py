# -*- coding: utf-8 -*-
"""
ui.components.export.csv_preview

CSVデータのプレビュー表示コンポーネント
"""

import streamlit as st
import pandas as pd
import io
from typing import Dict, List, Any, Optional, Union, Callable


class CSVPreviewComponent:
    """
    CSVデータのプレビュー表示コンポーネント
    
    エクスポート対象のCSVデータをプレビュー表示するためのUIコンポーネント。
    フィルタリング、ソート、ページネーション機能を提供。
    """
    
    def __init__(self, key: str = "csv_preview"):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "csv_preview"
        """
        self.key = key
        
        # ステート管理
        if f"{key}_data" not in st.session_state:
            st.session_state[f"{key}_data"] = None
        if f"{key}_page" not in st.session_state:
            st.session_state[f"{key}_page"] = 0
        if f"{key}_page_size" not in st.session_state:
            st.session_state[f"{key}_page_size"] = 10
        if f"{key}_sort_by" not in st.session_state:
            st.session_state[f"{key}_sort_by"] = None
        if f"{key}_sort_ascending" not in st.session_state:
            st.session_state[f"{key}_sort_ascending"] = True
        if f"{key}_filters" not in st.session_state:
            st.session_state[f"{key}_filters"] = {}
    
    def load_data(self, data: Union[pd.DataFrame, str, bytes, io.StringIO, io.BytesIO],
                 delimiter: str = ",", encoding: str = "utf-8") -> None:
        """
        データを読み込む
        
        Parameters
        ----------
        data : Union[pd.DataFrame, str, bytes, io.StringIO, io.BytesIO]
            DataFrameまたはCSVデータ
        delimiter : str, optional
            区切り文字, by default ","
        encoding : str, optional
            エンコーディング, by default "utf-8"
        """
        try:
            if isinstance(data, pd.DataFrame):
                # すでにDataFrameの場合はそのまま使用
                df = data
            elif isinstance(data, (str, bytes, io.StringIO, io.BytesIO)):
                # CSV文字列またはファイルオブジェクトからDataFrameを作成
                if isinstance(data, bytes):
                    data = data.decode(encoding)
                if isinstance(data, str):
                    data = io.StringIO(data)
                
                # CSVの読み込み
                df = pd.read_csv(data, delimiter=delimiter)
            else:
                raise ValueError("サポートされていない入力形式です")
            
            # データを保存
            st.session_state[f"{self.key}_data"] = df
            
            # ページを初期化
            st.session_state[f"{self.key}_page"] = 0
            
            # フィルタも初期化
            st.session_state[f"{self.key}_filters"] = {}
            
        except Exception as e:
            st.error(f"データの読み込みに失敗しました: {str(e)}")
    
    def render(self):
        """コンポーネントを表示"""
        df = st.session_state.get(f"{self.key}_data")
        
        if df is None or len(df) == 0:
            st.warning("プレビューするデータがありません。")
            return
        
        # データ概要
        st.write(f"レコード数: {len(df)}, カラム数: {len(df.columns)}")
        
        # データ操作エリア
        with st.expander("データフィルタリング・ソート", expanded=False):
            self._render_data_controls(df)
        
        # 表示設定
        page_size = st.session_state[f"{self.key}_page_size"]
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("表示行数:")
        with col2:
            page_size = st.select_slider(
                "表示行数", 
                options=[5, 10, 20, 50], 
                value=page_size,
                key=f"{self.key}_page_size_slider",
                label_visibility="collapsed"
            )
            st.session_state[f"{self.key}_page_size"] = page_size
        
        # フィルタ・ソートの適用
        filtered_df = self._apply_filters(df)
        sorted_df = self._apply_sorting(filtered_df)
        
        # ページネーション
        total_pages = max(1, (len(sorted_df) + page_size - 1) // page_size)
        current_page = st.session_state[f"{self.key}_page"]
        
        # ページ番号が範囲外の場合は調整
        if current_page >= total_pages:
            current_page = total_pages - 1
            st.session_state[f"{self.key}_page"] = current_page
        
        # ページネーションUI
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if st.button("前へ", key=f"{self.key}_prev_btn", disabled=current_page == 0):
                    st.session_state[f"{self.key}_page"] = max(0, current_page - 1)
                    st.experimental_rerun()
            
            with col2:
                page_nums = [f"{i+1}" for i in range(total_pages)]
                current_page_str = f"{current_page + 1}"
                selected_page = st.select_slider(
                    "ページ", 
                    options=page_nums,
                    value=current_page_str,
                    key=f"{self.key}_page_slider",
                    label_visibility="collapsed"
                )
                # ページの変更を検出
                if selected_page != current_page_str:
                    st.session_state[f"{self.key}_page"] = int(selected_page) - 1
                    st.experimental_rerun()
            
            with col3:
                if st.button("次へ", key=f"{self.key}_next_btn", disabled=current_page >= total_pages - 1):
                    st.session_state[f"{self.key}_page"] = min(total_pages - 1, current_page + 1)
                    st.experimental_rerun()
        
        # 現在のページのデータを表示
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, len(sorted_df))
        page_df = sorted_df.iloc[start_idx:end_idx]
        
        # データ表示
        st.dataframe(page_df, use_container_width=True)
        
        # ページ情報の表示
        if len(sorted_df) > 0:
            st.write(f"{start_idx + 1}～{end_idx} 件目 / 全{len(sorted_df)}件 (フィルタ前: {len(df)}件)")
        else:
            st.info("フィルタ条件に一致するデータがありません。")
        
        # CSV形式での表示オプション
        with st.expander("CSV形式で表示", expanded=False):
            # 表示用にCSV文字列に変換
            csv_str = filtered_df.to_csv(index=False)
            st.code(csv_str, language="text")
    
    def _render_data_controls(self, df):
        """
        データ操作コントロールの表示
        
        Parameters
        ----------
        df : pd.DataFrame
            操作対象のデータフレーム
        """
        # ソート設定
        st.write("**ソート設定**")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            sort_options = ["なし"] + list(df.columns)
            sort_index = 0
            if st.session_state[f"{self.key}_sort_by"] in df.columns:
                sort_index = list(df.columns).index(st.session_state[f"{self.key}_sort_by"]) + 1
            
            sort_col = st.selectbox(
                "並び替え列",
                options=sort_options,
                index=sort_index,
                key=f"{self.key}_sort_select"
            )
            
            if sort_col == "なし":
                st.session_state[f"{self.key}_sort_by"] = None
            else:
                st.session_state[f"{self.key}_sort_by"] = sort_col
        
        with col2:
            if st.session_state[f"{self.key}_sort_by"] is not None:
                sort_order = st.radio(
                    "順序",
                    options=["昇順", "降順"],
                    index=0 if st.session_state[f"{self.key}_sort_ascending"] else 1,
                    horizontal=True,
                    key=f"{self.key}_sort_order"
                )
                st.session_state[f"{self.key}_sort_ascending"] = (sort_order == "昇順")
        
        # フィルタ設定
        st.write("**フィルタ設定**")
        
        # 数値列と文字列列で別々の処理
        for col in df.columns:
            # 型に応じたフィルタを表示
            if pd.api.types.is_numeric_dtype(df[col]):
                self._render_numeric_filter(df, col)
            else:
                self._render_categorical_filter(df, col)
    
    def _render_numeric_filter(self, df, column):
        """
        数値列のフィルタUI表示
        
        Parameters
        ----------
        df : pd.DataFrame
            データフレーム
        column : str
            カラム名
        """
        # 現在の設定を取得
        current_filter = st.session_state[f"{self.key}_filters"].get(column, {})
        min_val = current_filter.get("min", df[column].min())
        max_val = current_filter.get("max", df[column].max())
        
        # フィルタ有効か
        is_active = current_filter.get("active", False)
        filter_active = st.checkbox(
            f"{column} フィルタ",
            value=is_active,
            key=f"{self.key}_filter_{column}_active"
        )
        
        if filter_active:
            col1, col2 = st.columns(2)
            with col1:
                min_input = st.number_input(
                    f"{column} 最小値",
                    value=float(min_val),
                    min_value=float(df[column].min()),
                    max_value=float(df[column].max()),
                    key=f"{self.key}_filter_{column}_min"
                )
            with col2:
                max_input = st.number_input(
                    f"{column} 最大値",
                    value=float(max_val),
                    min_value=float(df[column].min()),
                    max_value=float(df[column].max()),
                    key=f"{self.key}_filter_{column}_max"
                )
            
            # フィルタ設定を保存
            st.session_state[f"{self.key}_filters"][column] = {
                "active": True,
                "type": "numeric",
                "min": min_input,
                "max": max_input
            }
        elif column in st.session_state[f"{self.key}_filters"]:
            # フィルタを解除
            st.session_state[f"{self.key}_filters"][column]["active"] = False
    
    def _render_categorical_filter(self, df, column):
        """
        カテゴリ列のフィルタUI表示
        
        Parameters
        ----------
        df : pd.DataFrame
            データフレーム
        column : str
            カラム名
        """
        # 現在の設定を取得
        current_filter = st.session_state[f"{self.key}_filters"].get(column, {})
        is_active = current_filter.get("active", False)
        
        filter_active = st.checkbox(
            f"{column} フィルタ",
            value=is_active,
            key=f"{self.key}_filter_{column}_active"
        )
        
        if filter_active:
            # ユニーク値を取得
            unique_values = df[column].dropna().unique()
            if len(unique_values) <= 10:  # 値が少ない場合はチェックボックス
                selected_values = current_filter.get("values", list(unique_values))
                
                # チェックボックスで選択する値
                st.write(f"{column} の値を選択:")
                selected = []
                for val in unique_values:
                    is_selected = val in selected_values
                    if st.checkbox(
                        str(val),
                        value=is_selected,
                        key=f"{self.key}_filter_{column}_val_{val}"
                    ):
                        selected.append(val)
                
                # フィルタ設定を保存
                st.session_state[f"{self.key}_filters"][column] = {
                    "active": True,
                    "type": "categorical",
                    "values": selected
                }
            else:  # 値が多い場合はマルチセレクトの使用
                selected_values = current_filter.get("values", list(unique_values))
                
                # マルチセレクトで選択する値
                selected = st.multiselect(
                    f"{column} の値を選択:",
                    options=unique_values,
                    default=selected_values,
                    key=f"{self.key}_filter_{column}_multiselect"
                )
                
                # フィルタ設定を保存
                st.session_state[f"{self.key}_filters"][column] = {
                    "active": True,
                    "type": "categorical",
                    "values": selected
                }
        elif column in st.session_state[f"{self.key}_filters"]:
            # フィルタを解除
            st.session_state[f"{self.key}_filters"][column]["active"] = False
    
    def _apply_filters(self, df):
        """
        フィルタを適用
        
        Parameters
        ----------
        df : pd.DataFrame
            元のデータフレーム
            
        Returns
        -------
        pd.DataFrame
            フィルタ適用後のデータフレーム
        """
        filtered_df = df.copy()
        
        # 各フィルタを適用
        for column, filter_settings in st.session_state[f"{self.key}_filters"].items():
            if not filter_settings.get("active", False):
                continue
                
            if column not in filtered_df.columns:
                continue
                
            filter_type = filter_settings.get("type")
            
            if filter_type == "numeric":
                min_val = filter_settings.get("min")
                max_val = filter_settings.get("max")
                
                if min_val is not None:
                    filtered_df = filtered_df[filtered_df[column] >= min_val]
                if max_val is not None:
                    filtered_df = filtered_df[filtered_df[column] <= max_val]
                    
            elif filter_type == "categorical":
                values = filter_settings.get("values", [])
                if values:  # 値が選択されている場合のみフィルタリング
                    filtered_df = filtered_df[filtered_df[column].isin(values)]
        
        return filtered_df
    
    def _apply_sorting(self, df):
        """
        ソートを適用
        
        Parameters
        ----------
        df : pd.DataFrame
            元のデータフレーム
            
        Returns
        -------
        pd.DataFrame
            ソート適用後のデータフレーム
        """
        if st.session_state[f"{self.key}_sort_by"] is not None:
            sort_column = st.session_state[f"{self.key}_sort_by"]
            ascending = st.session_state[f"{self.key}_sort_ascending"]
            
            if sort_column in df.columns:
                return df.sort_values(by=sort_column, ascending=ascending)
        
        return df
    
    def reset_filters(self):
        """フィルタをリセット"""
        st.session_state[f"{self.key}_filters"] = {}
        st.session_state[f"{self.key}_page"] = 0
    
    def reset_sorting(self):
        """ソートをリセット"""
        st.session_state[f"{self.key}_sort_by"] = None
        st.session_state[f"{self.key}_sort_ascending"] = True
    
    def reset_all(self):
        """全ての設定をリセット"""
        self.reset_filters()
        self.reset_sorting()
        st.session_state[f"{self.key}_page_size"] = 10