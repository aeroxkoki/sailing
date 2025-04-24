# -*- coding: utf-8 -*-
"""
ui.components.reporting.data_selection_panel

データソースの選択を行うためのパネルを提供するモジュールです。
可視化要素のデータソースを対話的に選択するためのStreamlitコンポーネントを実装しています。
"""

from typing import Dict, List, Any, Optional, Callable
import streamlit as st
import pandas as pd
import numpy as np
import json
import math


class DataSelectionPanel:
    """
    データ選択パネルコンポーネント
    
    可視化要素のデータソースを選択するためのパネルを提供するStreamlitコンポーネントです。
    """
    
    def __init__(self, on_data_selection: Optional[Callable[[str, Dict[str, Any]], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        on_data_selection : Optional[Callable[[str, Dict[str, Any]], None]], optional
            データ選択時のコールバック, by default None
        """
        self.on_data_selection = on_data_selection
    
    def render(self, available_data_sources: Dict[str, Any]) -> None:
        """
        データ選択パネルを描画
        
        Parameters
        ----------
        available_data_sources : Dict[str, Any]
            利用可能なデータソース
        """
        st.subheader("データソース選択")
        
        if not available_data_sources:
            st.info("利用可能なデータソースがありません。")
            return
        
        # データソース選択
        data_source_name = st.selectbox(
            "データソース",
            options=list(available_data_sources.keys()),
            index=0
        )
        
        if data_source_name and data_source_name in available_data_sources:
            data = available_data_sources[data_source_name]
            
            # データプレビュー
            st.subheader("データプレビュー")
            
            # データタイプの判定
            data_type = self._get_data_type(data)
            
            # データタイプに応じたプレビュー表示
            if data_type == "table":
                self._render_table_preview(data)
            elif data_type == "dict":
                self._render_dict_preview(data)
            elif data_type == "geo":
                self._render_geo_preview(data)
            elif data_type == "time_series":
                self._render_time_series_preview(data)
            else:
                # その他のデータタイプのプレビュー
                self._render_generic_preview(data)
            
            # データソース選択ボタン
            if st.button("このデータソースを使用", key=f"use_datasource_{data_source_name}"):
                if self.on_data_selection:
                    self.on_data_selection(data_source_name, data)
            
            # データソースのフィルタリングとカスタム変換オプション
            self._render_data_transformation_options(data, data_source_name, data_type)
    
    def _get_data_type(self, data: Any) -> str:
        """
        データタイプを判定
        
        Parameters
        ----------
        data : Any
            判定対象データ
            
        Returns
        -------
        str
            データタイプ（"table", "dict", "geo", "time_series", "other"）
        """
        # リスト形式
        if isinstance(data, list):
            if len(data) > 0:
                # 辞書のリスト
                if isinstance(data[0], dict):
                    # 位置情報を含む場合はGEOデータ
                    if any(key in data[0] for key in ["lat", "latitude", "lng", "longitude", "lon"]):
                        return "geo"
                    # 時間データを含む場合は時系列データ
                    elif any(key in data[0] for key in ["time", "timestamp", "date", "datetime"]):
                        return "time_series"
                    # その他の構造化データはテーブルとして扱う
                    else:
                        return "table"
                # その他のリストは汎用データとして扱う
                else:
                    return "other"
            else:
                return "other"
        
        # 辞書形式
        elif isinstance(data, dict):
            # 特定のキーパターンに基づいて判定
            if "coordinates" in data or "features" in data or "geometry" in data:
                return "geo"
            elif "time_series" in data or "timeseries" in data or "timestamp" in data:
                return "time_series"
            else:
                return "dict"
        
        # DataFrame
        elif isinstance(data, pd.DataFrame):
            return "table"
        
        # その他のデータ型
        else:
            return "other"
    
    def _render_table_preview(self, data: Any) -> None:
        """
        テーブル形式データのプレビューを描画
        
        Parameters
        ----------
        data : Any
            プレビュー対象データ
        """
        try:
            # DataFrameに変換
            if isinstance(data, pd.DataFrame):
                df = data
            elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame(data)
            
            # データが大きすぎる場合は先頭10行のみ表示
            if len(df) > 10:
                st.write(f"データサイズ: {len(df)}行 × {len(df.columns)}列（先頭10行を表示）")
                st.dataframe(df.head(10))
            else:
                st.dataframe(df)
            
            # 数値列のみの基本統計情報を表示
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                st.write("数値データの基本統計")
                st.dataframe(df[numeric_cols].describe())
            
            # カラム情報の表示
            self._show_column_info(df)
        
        except Exception as e:
            st.error(f"テーブルプレビューの表示に失敗しました: {str(e)}")
    
    def _render_dict_preview(self, data: Dict[str, Any]) -> None:
        """
        辞書形式データのプレビューを描画
        
        Parameters
        ----------
        data : Dict[str, Any]
            プレビュー対象データ
        """
        # 最大表示件数
        max_items = 20
        
        # 辞書のキーを表示
        st.write("データキー:")
        keys = list(data.keys())
        if len(keys) > max_items:
            st.write(f"{len(keys)}個のキー（先頭{max_items}個を表示）")
            st.write(", ".join(keys[:max_items]) + "...")
        else:
            st.write(", ".join(keys))
        
        # 主要なキーのデータを表示
        for key in keys[:5]:  # 主要な5つのキーのみ表示
            st.write(f"**{key}**:")
            
            value = data[key]
            if isinstance(value, list):
                if len(value) > 5:
                    st.write(f"リスト（{len(value)}項目、先頭5項目を表示）")
                    self._render_list_preview(value[:5])
                else:
                    self._render_list_preview(value)
            elif isinstance(value, dict):
                if len(value) > 5:
                    st.write(f"辞書（{len(value)}キー、先頭5キーを表示）")
                    sub_keys = list(value.keys())[:5]
                    for sub_key in sub_keys:
                        st.write(f"- {sub_key}: {str(value[sub_key])[:100]}")
                else:
                    for sub_key, sub_value in value.items():
                        st.write(f"- {sub_key}: {str(sub_value)[:100]}")
            else:
                st.write(str(value)[:200])
        
        # JSON形式で表示
        with st.expander("JSON形式で表示"):
            try:
                st.json(data)
            except Exception:
                st.code(str(data)[:1000] + "...", language="text")
    
    def _render_geo_preview(self, data: Any) -> None:
        """
        地理データのプレビューを描画
        
        Parameters
        ----------
        data : Any
            プレビュー対象データ
        """
        st.write("地理データのプレビュー")
        
        # テーブル形式で先頭部分を表示
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data[:10])
            st.dataframe(df)
            
            # 地理データの情報を抽出
            lat_key = next((key for key in ["latitude", "lat"] if key in df.columns), None)
            lng_key = next((key for key in ["longitude", "lng", "lon"] if key in df.columns), None)
            
            if lat_key and lng_key:
                st.write(f"位置情報: {lat_key}, {lng_key}")
                st.write(f"データポイント数: {len(data)}")
                
                # 範囲情報
                min_lat = min(point[lat_key] for point in data if lat_key in point)
                max_lat = max(point[lat_key] for point in data if lat_key in point)
                min_lng = min(point[lng_key] for point in data if lng_key in point)
                max_lng = max(point[lng_key] for point in data if lng_key in point)
                
                st.write(f"緯度範囲: {min_lat:.6f} ～ {max_lat:.6f}")
                st.write(f"経度範囲: {min_lng:.6f} ～ {max_lng:.6f}")
        
        elif isinstance(data, dict):
            # GeoJSONなどの辞書形式の地理データの情報表示
            st.write("形式: GeoJSON / 地理データ辞書")
            
            if "features" in data:
                st.write(f"フィーチャー数: {len(data['features'])}")
            
            # JSON形式の一部を表示
            with st.expander("JSON形式で表示"):
                st.json(data)
    
    def _render_time_series_preview(self, data: Any) -> None:
        """
        時系列データのプレビューを描画
        
        Parameters
        ----------
        data : Any
            プレビュー対象データ
        """
        st.write("時系列データのプレビュー")
        
        # テーブル形式で先頭部分を表示
        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data[:10])
            st.dataframe(df)
            
            # 時間データの情報を抽出
            time_key = next((key for key in ["timestamp", "time", "date", "datetime"] if key in df.columns), None)
            
            if time_key:
                st.write(f"時間キー: {time_key}")
                st.write(f"データポイント数: {len(data)}")
                
                # 数値パラメータを特定
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if numeric_cols:
                    st.write(f"数値パラメータ: {', '.join(numeric_cols)}")
                
                # 時間範囲情報
                try:
                    time_values = [point[time_key] for point in data if time_key in point]
                    if time_values:
                        min_time = min(time_values)
                        max_time = max(time_values)
                        st.write(f"時間範囲: {min_time} ～ {max_time}")
                except Exception:
                    st.write("時間範囲の取得に失敗しました")
        
        elif isinstance(data, dict):
            # 時系列辞書データの情報表示
            st.write("形式: 時系列データ辞書")
            
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    st.write(f"{key}: {len(value)}ポイント")
            
            # JSON形式の一部を表示
            with st.expander("JSON形式で表示"):
                # データサイズが大きすぎる場合は要約を表示
                try:
                    st.json(data)
                except:
                    st.code(str(data)[:1000] + "...", language="text")
    
    def _render_generic_preview(self, data: Any) -> None:
        """
        汎用データプレビューを描画
        
        Parameters
        ----------
        data : Any
            プレビュー対象データ
        """
        # データタイプの表示
        st.write(f"データタイプ: {type(data).__name__}")
        
        # リスト型
        if isinstance(data, list):
            st.write(f"リスト長: {len(data)}項目")
            if len(data) > 0:
                st.write(f"要素タイプ: {type(data[0]).__name__}")
                self._render_list_preview(data[:10])  # 最大10項目を表示
        
        # 辞書型
        elif isinstance(data, dict):
            st.write(f"辞書サイズ: {len(data)}キー")
            keys = list(data.keys())
            if len(keys) > 10:
                st.write("キー: " + ", ".join(str(key) for key in keys[:10]) + "...")
            else:
                st.write("キー: " + ", ".join(str(key) for key in keys))
            
            # JSON形式で表示
            with st.expander("JSON形式で表示"):
                try:
                    st.json(data)
                except:
                    st.code(str(data)[:1000] + "...", language="text")
        
        # その他のデータ型
        else:
            st.write(str(data)[:1000])
            if len(str(data)) > 1000:
                st.write("...")
    
    def _render_list_preview(self, data_list: List[Any]) -> None:
        """
        リストのプレビューを描画
        
        Parameters
        ----------
        data_list : List[Any]
            プレビュー対象リスト
        """
        # 各要素の型が同じか確認
        if len(data_list) > 0:
            all_same_type = all(isinstance(item, type(data_list[0])) for item in data_list)
            
            if all_same_type:
                if isinstance(data_list[0], dict):
                    # 辞書のリストはDataFrameで表示
                    try:
                        df = pd.DataFrame(data_list)
                        st.dataframe(df)
                    except:
                        for i, item in enumerate(data_list):
                            st.write(f"{i}: {str(item)[:100]}")
                
                elif isinstance(data_list[0], (int, float, str, bool)):
                    # プリミティブ型のリスト
                    if len(data_list) <= 20:
                        st.write(data_list)
                    else:
                        st.write(data_list[:20])
                        st.write("...")
                
                else:
                    # その他の型
                    for i, item in enumerate(data_list):
                        st.write(f"{i}: {str(item)[:100]}")
            else:
                # 異なる型が混在するリスト
                for i, item in enumerate(data_list):
                    st.write(f"{i}: ({type(item).__name__}) {str(item)[:100]}")
        else:
            st.write("空のリスト")
    
    def _show_column_info(self, df: pd.DataFrame) -> None:
        """
        DataFrameのカラム情報を表示
        
        Parameters
        ----------
        df : pd.DataFrame
            カラム情報を表示するDataFrame
        """
        with st.expander("カラム情報"):
            col_info = []
            for col in df.columns:
                dtype = df[col].dtype
                non_null = df[col].count()
                null_count = df[col].isna().sum()
                unique_count = df[col].nunique()
                
                # サンプル値
                try:
                    sample = str(df[col].iloc[0])
                    if len(sample) > 30:
                        sample = sample[:30] + "..."
                except:
                    sample = "N/A"
                
                col_info.append({
                    "カラム名": col,
                    "データ型": str(dtype),
                    "非NULL数": non_null,
                    "NULL数": null_count,
                    "ユニーク値数": unique_count,
                    "サンプル値": sample
                })
            
            col_df = pd.DataFrame(col_info)
            st.dataframe(col_df)
    
    def _render_data_transformation_options(self, data: Any, data_source_name: str, data_type: str) -> None:
        """
        データ変換オプションのUIを描画
        
        Parameters
        ----------
        data : Any
            変換対象データ
        data_source_name : str
            データソース名
        data_type : str
            データタイプ
        """
        with st.expander("データ変換オプション"):
            st.caption("データソースを選択する前に適用可能な変換オプション")
            
            # 変換前のデータを保持
            transformed_data = data
            
            # データタイプに応じた変換オプション
            if data_type == "table":
                transformed_data = self._render_table_transformation_options(transformed_data)
            elif data_type == "time_series":
                transformed_data = self._render_time_series_transformation_options(transformed_data)
            elif data_type == "geo":
                transformed_data = self._render_geo_transformation_options(transformed_data)
            
            # 変換後のデータを使用するオプション
            if transformed_data is not data:  # 変換が行われた場合
                if st.button("変換後のデータを使用", key=f"use_transformed_{data_source_name}"):
                    if self.on_data_selection:
                        self.on_data_selection(f"{data_source_name}_transformed", transformed_data)
    
    def _render_table_transformation_options(self, data: Any) -> Any:
        """
        テーブルデータの変換オプションを描画
        
        Parameters
        ----------
        data : Any
            変換対象データ
            
        Returns
        -------
        Any
            変換後のデータ
        """
        # DataFrameに変換
        if not isinstance(data, pd.DataFrame):
            if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                df = pd.DataFrame(data)
            else:
                try:
                    df = pd.DataFrame(data)
                except:
                    st.error("このデータはテーブル形式に変換できません")
                    return data
        else:
            df = data.copy()
        
        # カラム選択オプション
        st.subheader("カラム選択")
        all_columns = list(df.columns)
        selected_columns = st.multiselect(
            "表示するカラムを選択",
            options=all_columns,
            default=all_columns
        )
        
        if selected_columns and len(selected_columns) < len(all_columns):
            df = df[selected_columns]
            st.write(f"選択されたカラム: {len(selected_columns)}個")
        
        # フィルタリングオプション
        st.subheader("フィルタリング")
        filter_column = st.selectbox(
            "フィルタリングするカラムを選択",
            options=["なし"] + list(df.columns)
        )
        
        if filter_column != "なし":
            col_dtype = df[filter_column].dtype
            
            # 数値型カラムの場合は範囲指定
            if np.issubdtype(col_dtype, np.number):
                min_val = float(df[filter_column].min())
                max_val = float(df[filter_column].max())
                
                filter_range = st.slider(
                    f"{filter_column}の範囲",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val)
                )
                
                df = df[(df[filter_column] >= filter_range[0]) & (df[filter_column] <= filter_range[1])]
                st.write(f"フィルタリング後のデータ数: {len(df)}行")
            
            # カテゴリ型や文字列型の場合は選択肢
            elif np.issubdtype(col_dtype, np.object_) or pd.api.types.is_categorical_dtype(col_dtype):
                unique_values = df[filter_column].dropna().unique().tolist()
                if len(unique_values) <= 30:  # 選択肢が多すぎる場合は選択肢を制限
                    selected_values = st.multiselect(
                        f"{filter_column}の値を選択",
                        options=unique_values,
                        default=unique_values
                    )
                    
                    if selected_values and len(selected_values) < len(unique_values):
                        df = df[df[filter_column].isin(selected_values)]
                        st.write(f"フィルタリング後のデータ数: {len(df)}行")
                else:
                    st.info(f"{filter_column}の一意な値が多すぎます（{len(unique_values)}個）。テキスト検索を使用してください。")
                    filter_text = st.text_input(f"{filter_column}に含まれる文字列")
                    if filter_text:
                        df = df[df[filter_column].astype(str).str.contains(filter_text, na=False)]
                        st.write(f"フィルタリング後のデータ数: {len(df)}行")
            
            # 日付型の場合は日付範囲
            elif pd.api.types.is_datetime64_dtype(col_dtype):
                min_date = df[filter_column].min().date()
                max_date = df[filter_column].max().date()
                
                start_date = st.date_input(
                    "開始日",
                    value=min_date
                )
                end_date = st.date_input(
                    "終了日",
                    value=max_date
                )
                
                df = df[(df[filter_column].dt.date >= start_date) & (df[filter_column].dt.date <= end_date)]
                st.write(f"フィルタリング後のデータ数: {len(df)}行")
        
        # データ変換・集計オプション
        st.subheader("集計・変換")
        transform_option = st.selectbox(
            "変換タイプを選択",
            options=["なし", "グループ集計", "ピボットテーブル", "転置（行列入れ替え）"]
        )
        
        if transform_option == "グループ集計":
            # グループ集計
            group_cols = st.multiselect(
                "グループ化するカラムを選択",
                options=df.columns.tolist()
            )
            
            if group_cols:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                if not numeric_cols:
                    st.warning("集計可能な数値カラムがありません")
                else:
                    agg_cols = st.multiselect(
                        "集計するカラムを選択",
                        options=numeric_cols,
                        default=numeric_cols
                    )
                    
                    if agg_cols:
                        agg_funcs = st.multiselect(
                            "集計関数を選択",
                            options=["mean", "sum", "min", "max", "count"],
                            default=["mean"]
                        )
                        
                        if agg_funcs:
                            # 集計関数の辞書を作成
                            agg_dict = {col: agg_funcs for col in agg_cols}
                            
                            # グループ集計を実行
                            df = df.groupby(group_cols).agg(agg_dict).reset_index()
                            
                            # カラム名をフラット化
                            if len(agg_funcs) > 1:
                                df.columns = ["_".join(col).strip() if isinstance(col, tuple) else col for col in df.columns.values]
                            
                            st.write(f"集計後のデータ: {len(df)}行")
                            st.dataframe(df.head(5))
        
        elif transform_option == "ピボットテーブル":
            # ピボットテーブル
            index_cols = st.multiselect(
                "行インデックス（左側）に配置するカラムを選択",
                options=df.columns.tolist()
            )
            
            if index_cols:
                column_col = st.selectbox(
                    "列見出し（上側）に配置するカラムを選択",
                    options=["なし"] + [col for col in df.columns if col not in index_cols]
                )
                
                if column_col != "なし":
                    value_cols = [col for col in df.columns if col not in index_cols and col != column_col]
                    
                    numeric_value_cols = [col for col in value_cols if np.issubdtype(df[col].dtype, np.number)]
                    if not numeric_value_cols:
                        st.warning("集計可能な数値カラムがありません")
                    else:
                        value_col = st.selectbox(
                            "値として集計するカラムを選択",
                            options=numeric_value_cols
                        )
                        
                        if value_col:
                            agg_func = st.selectbox(
                                "集計関数を選択",
                                options=["mean", "sum", "min", "max", "count"],
                                index=0
                            )
                            
                            # ピボットテーブルを作成
                            pivot_df = pd.pivot_table(
                                df,
                                values=value_col,
                                index=index_cols,
                                columns=column_col,
                                aggfunc=agg_func
                            ).reset_index()
                            
                            st.write(f"ピボット後のデータ: {pivot_df.shape[0]}行 × {pivot_df.shape[1]}列")
                            st.dataframe(pivot_df.head(5))
                            
                            df = pivot_df
        
        elif transform_option == "転置（行列入れ替え）":
            # 転置
            if len(df) > 100:
                st.warning("データが大きすぎるため転置できません（100行以下にフィルタリングしてください）")
            else:
                index_col = st.selectbox(
                    "新しい列名に使用するカラムを選択",
                    options=["インデックス"] + df.columns.tolist()
                )
                
                if index_col != "インデックス":
                    # 指定されたカラムを新しいインデックスに設定
                    df_t = df.set_index(index_col).T.reset_index()
                    df_t = df_t.rename(columns={"index": "column_name"})
                else:
                    # インデックスを使用
                    df_t = df.T.reset_index()
                    df_t = df_t.rename(columns={"index": "column_name"})
                
                st.write(f"転置後のデータ: {df_t.shape[0]}行 × {df_t.shape[1]}列")
                st.dataframe(df_t.head(5))
                
                df = df_t
        
        return df
    
    def _render_time_series_transformation_options(self, data: Any) -> Any:
        """
        時系列データの変換オプションを描画
        
        Parameters
        ----------
        data : Any
            変換対象データ
            
        Returns
        -------
        Any
            変換後のデータ
        """
        # リスト形式のデータをDataFrameに変換
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            df = pd.DataFrame(data)
        else:
            # 変換できない形式の場合は元のデータを返す
            return data
        
        # 時間カラムを特定
        time_columns = [col for col in df.columns if col.lower() in ["time", "timestamp", "date", "datetime"]]
        if not time_columns:
            st.warning("時間カラムが見つかりません")
            return data
        
        # 時間カラムを選択
        time_column = st.selectbox(
            "時間カラムを選択",
            options=time_columns,
            index=0
        )
        
        # 時間範囲フィルタリング
        st.subheader("時間範囲フィルタリング")
        
        # 時間カラムを日時型に変換
        try:
            df[time_column] = pd.to_datetime(df[time_column])
            min_time = df[time_column].min()
            max_time = df[time_column].max()
            
            # 時間範囲選択（日付のみ）
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "開始日",
                    value=min_time.date()
                )
            
            with col2:
                end_date = st.date_input(
                    "終了日",
                    value=max_time.date()
                )
            
            # 日付範囲でフィルタリング
            df = df[(df[time_column].dt.date >= start_date) & (df[time_column].dt.date <= end_date)]
            st.write(f"フィルタリング後のデータポイント数: {len(df)}ポイント")
        
        except Exception as e:
            st.error(f"時間範囲フィルタリングに失敗しました: {str(e)}")
        
        # リサンプリングオプション
        st.subheader("リサンプリング")
        
        resample_option = st.selectbox(
            "リサンプリング周期",
            options=["なし", "1分", "5分", "10分", "30分", "1時間", "3時間", "日別", "週別", "月別"]
        )
        
        resample_map = {
            "1分": "1min", "5分": "5min", "10分": "10min", "30分": "30min",
            "1時間": "1h", "3時間": "3h", "日別": "D", "週別": "W", "月別": "M"
        }
        
        if resample_option != "なし":
            # 集計対象の数値カラムを選択
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                st.warning("リサンプリング可能な数値カラムがありません")
            else:
                agg_cols = st.multiselect(
                    "集計するカラムを選択",
                    options=numeric_cols,
                    default=numeric_cols
                )
                
                if agg_cols:
                    agg_func = st.selectbox(
                        "集計関数を選択",
                        options=["mean", "sum", "min", "max", "median"],
                        index=0
                    )
                    
                    # リサンプリングを実行
                    try:
                        # インデックスを時間に設定
                        df = df.set_index(time_column)
                        
                        # リサンプリング
                        resampled = df[agg_cols].resample(resample_map[resample_option]).agg(agg_func)
                        
                        # インデックスをリセット
                        resampled = resampled.reset_index()
                        
                        st.write(f"リサンプリング後のデータポイント数: {len(resampled)}ポイント")
                        st.dataframe(resampled.head(5))
                        
                        df = resampled
                    except Exception as e:
                        st.error(f"リサンプリングに失敗しました: {str(e)}")
                        return data
        
        # 移動平均オプション
        st.subheader("移動平均")
        
        rolling_window = st.number_input(
            "移動平均の窓サイズ (ポイント数、0=なし)",
            min_value=0,
            max_value=100,
            value=0
        )
        
        if rolling_window > 0:
            # 移動平均対象の数値カラムを選択
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                st.warning("移動平均計算可能な数値カラムがありません")
            else:
                rolling_cols = st.multiselect(
                    "移動平均を計算するカラムを選択",
                    options=numeric_cols,
                    default=numeric_cols
                )
                
                if rolling_cols:
                    # 移動平均の計算
                    try:
                        # インデックスが時間カラムの場合は維持
                        if isinstance(df.index, pd.DatetimeIndex):
                            for col in rolling_cols:
                                df[f"{col}_MA{rolling_window}"] = df[col].rolling(window=rolling_window, center=True).mean()
                        else:
                            for col in rolling_cols:
                                df[f"{col}_MA{rolling_window}"] = df[col].rolling(window=rolling_window, center=True).mean()
                        
                        st.write(f"移動平均カラム {len(rolling_cols)}個を追加しました")
                        st.dataframe(df.head(5))
                    except Exception as e:
                        st.error(f"移動平均の計算に失敗しました: {str(e)}")
        
        # DataFrameをリストに戻す（元の形式に合わせる）
        if isinstance(data, list):
            return df.to_dict('records')
        else:
            return df
    
    def _render_geo_transformation_options(self, data: Any) -> Any:
        """
        地理データの変換オプションを描画
        
        Parameters
        ----------
        data : Any
            変換対象データ
            
        Returns
        -------
        Any
            変換後のデータ
        """
        # リスト形式のデータをDataFrameに変換
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            df = pd.DataFrame(data)
        else:
            # 変換できない形式の場合は元のデータを返す
            return data
        
        # 緯度経度カラムを特定
        lat_columns = [col for col in df.columns if col.lower() in ["lat", "latitude"]]
        lng_columns = [col for col in df.columns if col.lower() in ["lng", "lon", "longitude"]]
        
        if not lat_columns or not lng_columns:
            st.warning("緯度経度カラムが見つかりません")
            return data
        
        # 緯度経度カラムを選択
        lat_column = st.selectbox("緯度カラムを選択", options=lat_columns, index=0)
        lng_column = st.selectbox("経度カラムを選択", options=lng_columns, index=0)
        
        # 空間フィルタリングオプション
        st.subheader("空間フィルタリング")
        
        # バウンディングボックスによるフィルタリング
        if st.checkbox("バウンディングボックスでフィルタリング"):
            min_lat = df[lat_column].min()
            max_lat = df[lat_column].max()
            min_lng = df[lng_column].min()
            max_lng = df[lng_column].max()
            
            col1, col2 = st.columns(2)
            with col1:
                lat_range = st.slider(
                    "緯度範囲",
                    min_value=float(min_lat),
                    max_value=float(max_lat),
                    value=(float(min_lat), float(max_lat)),
                    format="%.6f"
                )
            
            with col2:
                lng_range = st.slider(
                    "経度範囲",
                    min_value=float(min_lng),
                    max_value=float(max_lng),
                    value=(float(min_lng), float(max_lng)),
                    format="%.6f"
                )
            
            # バウンディングボックスでフィルタリング
            df = df[
                (df[lat_column] >= lat_range[0]) & (df[lat_column] <= lat_range[1]) &
                (df[lng_column] >= lng_range[0]) & (df[lng_column] <= lng_range[1])
            ]
            
            st.write(f"フィルタリング後のデータポイント数: {len(df)}ポイント")
        
        # ダウンサンプリングオプション
        st.subheader("ダウンサンプリング")
        
        sample_rate = st.slider(
            "サンプリング率 (1=全ポイント、0.1=10%のポイント)",
            min_value=0.01,
            max_value=1.0,
            value=1.0,
            step=0.01
        )
        
        if sample_rate < 1.0:
            # ランダムサンプリング
            sample_size = max(1, int(len(df) * sample_rate))
            df = df.sample(sample_size)
            
            st.write(f"ダウンサンプリング後のデータポイント数: {len(df)}ポイント")
        
        # 距離計算オプション
        st.subheader("距離と速度の計算")
        
        if st.checkbox("連続ポイント間の距離を計算"):
            # 時間カラムが存在するか確認
            time_columns = [col for col in df.columns if col.lower() in ["time", "timestamp", "date", "datetime"]]
            calculate_speed = False
            
            if time_columns:
                calculate_speed = st.checkbox("速度も計算する")
                if calculate_speed:
                    time_column = st.selectbox(
                        "時間カラムを選択",
                        options=time_columns,
                        index=0
                    )
                    
                    # 時間カラムを日時型に変換
                    try:
                        df[time_column] = pd.to_datetime(df[time_column])
                    except:
                        st.error("時間カラムの変換に失敗しました")
                        calculate_speed = False
            
            # ソート順を指定
            sort_column = None
            if time_columns:
                sort_column = st.selectbox(
                    "ソート基準カラム",
                    options=["なし"] + time_columns,
                    index=1 if time_columns else 0
                )
            
            if sort_column and sort_column != "なし":
                df = df.sort_values(by=sort_column)
            
            # 距離計算関数（ハバーサイン法）
            def haversine(lat1, lon1, lat2, lon2):
                # 地球の半径（km）
                R = 6371.0
                
                # 緯度経度をラジアンに変換
                lat1_rad = math.radians(lat1)
                lon1_rad = math.radians(lon1)
                lat2_rad = math.radians(lat2)
                lon2_rad = math.radians(lon2)
                
                # 差分
                dlat = lat2_rad - lat1_rad
                dlon = lon2_rad - lon1_rad
                
                # ハバーサイン公式
                a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                
                # 距離（km）
                distance = R * c
                
                return distance
            
            # 距離計算
            distances = [0]  # 最初のポイントの距離は0
            
            for i in range(1, len(df)):
                lat1 = df.iloc[i-1][lat_column]
                lon1 = df.iloc[i-1][lng_column]
                lat2 = df.iloc[i][lat_column]
                lon2 = df.iloc[i][lng_column]
                
                distance = haversine(lat1, lon1, lat2, lon2)
                distances.append(distance)
            
            # 距離カラムを追加
            df['distance_km'] = distances
            df['cumulative_distance_km'] = df['distance_km'].cumsum()
            
            # 速度計算（オプション）
            if calculate_speed:
                # 時間差を計算（秒単位）
                time_diffs = [0]  # 最初のポイントの時間差は0
                
                for i in range(1, len(df)):
                    time_diff = (df.iloc[i][time_column] - df.iloc[i-1][time_column]).total_seconds()
                    time_diffs.append(time_diff)
                
                df['time_diff_sec'] = time_diffs
                
                # 速度計算（km/h）
                speeds = [0]  # 最初のポイントの速度は0
                
                for i in range(1, len(df)):
                    if df.iloc[i]['time_diff_sec'] > 0:
                        speed = df.iloc[i]['distance_km'] / df.iloc[i]['time_diff_sec'] * 3600  # km/h
                    else:
                        speed = 0
                    speeds.append(speed)
                
                df['speed_kmh'] = speeds
                
                # 異常な速度値を処理（オプション）
                if st.checkbox("異常な速度値をフィルタリング"):
                    max_speed = st.number_input(
                        "最大速度（km/h）",
                        min_value=1.0,
                        max_value=200.0,
                        value=100.0
                    )
                    
                    outlier_count = (df['speed_kmh'] > max_speed).sum()
                    if outlier_count > 0:
                        st.write(f"{outlier_count}個の異常値を検出しました")
                        
                        # 異常値を置換または除外
                        replace_option = st.radio(
                            "異常値の処理方法",
                            options=["最大値で置換", "除外"]
                        )
                        
                        if replace_option == "最大値で置換":
                            df.loc[df['speed_kmh'] > max_speed, 'speed_kmh'] = max_speed
                        else:
                            df = df[df['speed_kmh'] <= max_speed]
                            st.write(f"フィルタリング後のデータポイント数: {len(df)}ポイント")
            
            st.write("距離計算を追加しました")
            st.dataframe(df.head(5))
        
        # DataFrameをリストに戻す（元の形式に合わせる）
        if isinstance(data, list):
            return df.to_dict('records')
        else:
            return df
