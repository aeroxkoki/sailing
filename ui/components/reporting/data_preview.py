"""
ui.components.reporting.data_preview

データプレビューを提供するモジュールです。
データの内容や構造を対話的に表示するためのStreamlitコンポーネントを実装しています。
"""

from typing import Dict, List, Any, Optional, Callable, Union, Tuple
import streamlit as st
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta


class DataPreviewComponent:
    """
    データプレビューコンポーネント
    
    データの内容や構造を可視化するためのコンポーネントです。
    """
    
    def __init__(self, on_selection: Optional[Callable[[str, Any], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        on_selection : Optional[Callable[[str, Any], None]], optional
            データ選択時のコールバック, by default None
            - 第1引数: 選択されたデータパス
            - 第2引数: 選択されたデータ
        """
        self.on_selection = on_selection
        self.selected_data = None
    
    def render(self, data: Any, title: str = "データプレビュー") -> None:
        """
        データプレビューを描画
        
        Parameters
        ----------
        data : Any
            プレビュー対象データ
        title : str, optional
            プレビュータイトル, by default "データプレビュー"
        """
        st.subheader(title)
        
        # データ型の判定
        data_type = self._determine_data_type(data)
        
        # 描画方法の選択
        view_mode = st.radio(
            "表示モード",
            options=["テーブル", "構造", "統計情報", "可視化"],
            horizontal=True
        )
        
        # 表示モードに応じたプレビュー表示
        if view_mode == "テーブル":
            self._render_table_view(data, data_type)
        elif view_mode == "構造":
            self._render_structure_view(data, data_type)
        elif view_mode == "統計情報":
            self._render_statistics_view(data, data_type)
        elif view_mode == "可視化":
            self._render_visualization_view(data, data_type)
    
    def _determine_data_type(self, data: Any) -> str:
        """
        データ型を判定
        
        Parameters
        ----------
        data : Any
            判定対象データ
            
        Returns
        -------
        str
            データ型（"dataframe", "dict_list", "dict", "list", "geo", "time_series", "unknown"）
        """
        if isinstance(data, pd.DataFrame):
            # DataFrameの場合、さらに特殊タイプを判別
            if any(col.lower() in ["lat", "latitude", "lng", "longitude", "lon"] for col in data.columns):
                return "geo"
            elif any(col.lower() in ["time", "timestamp", "date", "datetime"] for col in data.columns):
                return "time_series"
            return "dataframe"
        
        elif isinstance(data, list):
            if len(data) > 0:
                if isinstance(data[0], dict):
                    # 辞書のリストの場合、特殊タイプを判別
                    first_item = data[0]
                    if any(key.lower() in ["lat", "latitude", "lng", "longitude", "lon"] for key in first_item.keys()):
                        return "geo"
                    elif any(key.lower() in ["time", "timestamp", "date", "datetime"] for key in first_item.keys()):
                        return "time_series"
                    return "dict_list"
                else:
                    return "list"
            else:
                return "list"
        
        elif isinstance(data, dict):
            # GeoJSONなどの特殊形式の確認
            if "type" in data and data["type"] in ["FeatureCollection", "Feature", "Point", "LineString", "Polygon"]:
                return "geo"
            return "dict"
        
        else:
            return "unknown"
    
    def _render_table_view(self, data: Any, data_type: str) -> None:
        """
        テーブル形式でデータを表示
        
        Parameters
        ----------
        data : Any
            表示対象データ
        data_type : str
            データ型
        """
        # データ型に応じた表示
        if data_type in ["dataframe", "geo", "time_series"]:
            # DataFrameの場合
            df = data
            
            # ページング機能
            total_rows = len(df)
            rows_per_page = st.slider("1ページあたりの行数", min_value=5, max_value=100, value=10)
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page
            
            if total_pages > 1:
                page = st.number_input("ページ", min_value=1, max_value=total_pages, value=1)
                start_idx = (page - 1) * rows_per_page
                end_idx = min(start_idx + rows_per_page, total_rows)
                
                st.write(f"表示: {start_idx+1}～{end_idx} / 全{total_rows}行")
                st.dataframe(df.iloc[start_idx:end_idx])
            else:
                st.dataframe(df)
                
            # カラム情報
            with st.expander("カラム情報", expanded=False):
                self._show_column_info(df)
        
        elif data_type == "dict_list":
            # 辞書のリストの場合、DataFrameに変換して表示
            df = pd.DataFrame(data)
            
            # ページング機能
            total_rows = len(df)
            rows_per_page = st.slider("1ページあたりの行数", min_value=5, max_value=100, value=10)
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page
            
            if total_pages > 1:
                page = st.number_input("ページ", min_value=1, max_value=total_pages, value=1)
                start_idx = (page - 1) * rows_per_page
                end_idx = min(start_idx + rows_per_page, total_rows)
                
                st.write(f"表示: {start_idx+1}～{end_idx} / 全{total_rows}行")
                st.dataframe(df.iloc[start_idx:end_idx])
            else:
                st.dataframe(df)
                
            # カラム情報
            with st.expander("カラム情報", expanded=False):
                self._show_column_info(df)
        
        elif data_type == "list":
            # リストの場合
            if len(data) > 0:
                if all(isinstance(item, (int, float, str, bool)) for item in data):
                    # プリミティブ型のリスト
                    
                    # ページング機能
                    total_items = len(data)
                    items_per_page = st.slider("1ページあたりの項目数", min_value=10, max_value=200, value=50)
                    total_pages = (total_items + items_per_page - 1) // items_per_page
                    
                    if total_pages > 1:
                        page = st.number_input("ページ", min_value=1, max_value=total_pages, value=1)
                        start_idx = (page - 1) * items_per_page
                        end_idx = min(start_idx + items_per_page, total_items)
                        
                        st.write(f"表示: {start_idx+1}～{end_idx} / 全{total_items}項目")
                        
                        # 表形式で表示
                        data_dict = {"インデックス": list(range(start_idx, end_idx)), "値": data[start_idx:end_idx]}
                        st.dataframe(pd.DataFrame(data_dict))
                    else:
                        # 表形式で表示
                        data_dict = {"インデックス": list(range(len(data))), "値": data}
                        st.dataframe(pd.DataFrame(data_dict))
                else:
                    # 複雑なオブジェクトのリスト
                    st.write("複雑なオブジェクトを含むリスト（最初の10項目）")
                    for i, item in enumerate(data[:10]):
                        st.write(f"{i}: {str(item)}")
                    
                    if len(data) > 10:
                        st.write("...")
            else:
                st.write("空のリストです")
        
        elif data_type == "dict":
            # 辞書の場合
            st.write(f"辞書: {len(data)}キー")
            
            # キーのリスト
            keys = list(data.keys())
            
            # ページング機能
            total_keys = len(keys)
            keys_per_page = st.slider("1ページあたりのキー数", min_value=5, max_value=50, value=10)
            total_pages = (total_keys + keys_per_page - 1) // keys_per_page
            
            if total_pages > 1:
                page = st.number_input("ページ", min_value=1, max_value=total_pages, value=1)
                start_idx = (page - 1) * keys_per_page
                end_idx = min(start_idx + keys_per_page, total_keys)
                
                st.write(f"表示: {start_idx+1}～{end_idx} / 全{total_keys}キー")
                
                # 表形式で表示
                preview_data = {}
                for key in keys[start_idx:end_idx]:
                    value = data[key]
                    if isinstance(value, list):
                        preview_data[key] = f"リスト ({len(value)}件)"
                    elif isinstance(value, dict):
                        preview_data[key] = f"辞書 ({len(value)}キー)"
                    else:
                        preview_data[key] = str(value)
                
                # 表示
                for key, value in preview_data.items():
                    st.write(f"**{key}**: {value}")
            else:
                # 表形式で表示
                preview_data = {}
                for key in keys:
                    value = data[key]
                    if isinstance(value, list):
                        preview_data[key] = f"リスト ({len(value)}件)"
                    elif isinstance(value, dict):
                        preview_data[key] = f"辞書 ({len(value)}キー)"
                    else:
                        preview_data[key] = str(value)
                
                # 表示
                for key, value in preview_data.items():
                    st.write(f"**{key}**: {value}")
        
        else:
            # その他のデータ型
            st.write(f"データ型: {type(data).__name__}")
            st.write(str(data)[:1000])
            if len(str(data)) > 1000:
                st.write("...")
    
    def _render_structure_view(self, data: Any, data_type: str) -> None:
        """
        データ構造を表示
        
        Parameters
        ----------
        data : Any
            表示対象データ
        data_type : str
            データ型
        """
        # データ型に応じた表示
        if data_type in ["dataframe", "geo", "time_series"]:
            # DataFrameの場合
            st.write(f"データ形式: DataFrame ({len(data)}行 × {len(data.columns)}列)")
            
            # 基本情報
            st.write("基本情報:")
            st.code(str(data.info()))
            
            # データ型
            st.write("データ型:")
            st.dataframe(pd.DataFrame({"カラム": data.columns, "データ型": data.dtypes}))
            
            # 最初の数行
            with st.expander("先頭5行", expanded=True):
                st.dataframe(data.head())
            
            # スキーマ情報（時系列や空間データの場合）
            if data_type in ["geo", "time_series"]:
                with st.expander("特殊カラム情報", expanded=True):
                    if data_type == "geo":
                        # 緯度経度カラムを表示
                        lat_cols = [col for col in data.columns if col.lower() in ["lat", "latitude"]]
                        lng_cols = [col for col in data.columns if col.lower() in ["lng", "lon", "longitude"]]
                        
                        if lat_cols and lng_cols:
                            st.write(f"緯度カラム: {lat_cols[0]}")
                            st.write(f"経度カラム: {lng_cols[0]}")
                            
                            # 位置データの範囲
                            lat_col = lat_cols[0]
                            lng_col = lng_cols[0]
                            
                            st.write(f"緯度範囲: {data[lat_col].min():.6f} ～ {data[lat_col].max():.6f}")
                            st.write(f"経度範囲: {data[lng_col].min():.6f} ～ {data[lng_col].max():.6f}")
                    
                    elif data_type == "time_series":
                        # 時間カラムを表示
                        time_cols = [col for col in data.columns if col.lower() in ["time", "timestamp", "date", "datetime"]]
                        
                        if time_cols:
                            time_col = time_cols[0]
                            st.write(f"時間カラム: {time_col}")
                            
                            # 時間範囲
                            try:
                                if pd.api.types.is_datetime64_any_dtype(data[time_col]):
                                    st.write(f"時間範囲: {data[time_col].min()} ～ {data[time_col].max()}")
                                else:
                                    st.write(f"時間範囲: {min(data[time_col])} ～ {max(data[time_col])}")
                            except:
                                st.write("時間範囲を取得できません")
        
        elif data_type == "dict_list":
            # 辞書のリストの場合
            st.write(f"データ形式: 辞書リスト ({len(data)}件)")
            
            if len(data) > 0:
                # 最初の辞書からキーを取得
                first_item = data[0]
                keys = list(first_item.keys())
                
                st.write(f"キー: {', '.join(keys)}")
                
                # 値のサンプル
                st.write("最初の要素:")
                st.json(first_item)
                
                # 特殊フィールド情報（時系列や空間データの場合）
                if data_type in ["geo", "time_series"]:
                    with st.expander("特殊フィールド情報", expanded=True):
                        if "geo" in data_type:
                            # 緯度経度フィールドを表示
                            lat_keys = [key for key in keys if key.lower() in ["lat", "latitude"]]
                            lng_keys = [key for key in keys if key.lower() in ["lng", "lon", "longitude"]]
                            
                            if lat_keys and lng_keys:
                                st.write(f"緯度フィールド: {lat_keys[0]}")
                                st.write(f"経度フィールド: {lng_keys[0]}")
                                
                                # 位置データの範囲
                                lat_key = lat_keys[0]
                                lng_key = lng_keys[0]
                                
                                lat_values = [item[lat_key] for item in data if lat_key in item]
                                lng_values = [item[lng_key] for item in data if lng_key in item]
                                
                                if lat_values and lng_values:
                                    st.write(f"緯度範囲: {min(lat_values):.6f} ～ {max(lat_values):.6f}")
                                    st.write(f"経度範囲: {min(lng_values):.6f} ～ {max(lng_values):.6f}")
                        
                        elif "time_series" in data_type:
                            # 時間フィールドを表示
                            time_keys = [key for key in keys if key.lower() in ["time", "timestamp", "date", "datetime"]]
                            
                            if time_keys:
                                time_key = time_keys[0]
                                st.write(f"時間フィールド: {time_key}")
                                
                                # 時間範囲
                                time_values = [item[time_key] for item in data if time_key in item]
                                if time_values:
                                    st.write(f"時間範囲: {min(time_values)} ～ {max(time_values)}")
        
        elif data_type == "list":
            # リストの場合
            st.write(f"データ形式: リスト ({len(data)}件)")
            
            if len(data) > 0:
                # 要素のタイプ
                element_type = type(data[0]).__name__
                st.write(f"要素のタイプ: {element_type}")
                
                # 最初の要素
                st.write("最初の要素:")
                st.write(str(data[0]))
                
                # 統計情報（数値リストの場合）
                if all(isinstance(item, (int, float)) for item in data):
                    with st.expander("統計情報", expanded=True):
                        st.write(f"最小値: {min(data)}")
                        st.write(f"最大値: {max(data)}")
                        st.write(f"平均値: {sum(data) / len(data)}")
                        
                        # 中央値
                        sorted_data = sorted(data)
                        middle = len(sorted_data) // 2
                        if len(sorted_data) % 2 == 0:
                            median = (sorted_data[middle - 1] + sorted_data[middle]) / 2
                        else:
                            median = sorted_data[middle]
                        st.write(f"中央値: {median}")
        
        elif data_type == "dict":
            # 辞書の場合
            st.write(f"データ形式: 辞書 ({len(data)}キー)")
            
            # キーのリスト
            keys = list(data.keys())
            st.write(f"キー: {', '.join(str(key) for key in keys[:20])}")
            if len(keys) > 20:
                st.write(f"... 他 {len(keys) - 20} キー")
            
            # 値のタイプ
            value_types = {}
            for key, value in data.items():
                value_type = type(value).__name__
                if value_type not in value_types:
                    value_types[value_type] = 0
                value_types[value_type] += 1
            
            st.write("値のタイプ:")
            for vtype, count in value_types.items():
                st.write(f"- {vtype}: {count}個")
            
            # 特殊形式の確認
            if "type" in data:
                st.write(f"データタイプ: {data['type']}")
                
                if data["type"] in ["FeatureCollection", "Feature", "Point", "LineString", "Polygon"]:
                    st.write("GeoJSON形式のデータです")
        
        else:
            # その他のデータ型
            st.write(f"データ型: {type(data).__name__}")
            st.write(str(data)[:1000])
            if len(str(data)) > 1000:
                st.write("...")
    
    def _render_statistics_view(self, data: Any, data_type: str) -> None:
        """
        統計情報を表示
        
        Parameters
        ----------
        data : Any
            表示対象データ
        data_type : str
            データ型
        """
        # データ型に応じた表示
        if data_type in ["dataframe", "geo", "time_series"]:
            # DataFrameの場合
            st.write(f"データ形式: DataFrame ({len(data)}行 × {len(data.columns)}列)")
            
            # 数値列のみの統計情報
            numeric_df = data.select_dtypes(include=[np.number])
            
            if not numeric_df.empty:
                st.write("数値データの統計情報:")
                st.dataframe(numeric_df.describe())
                
                # 欠損値の割合
                st.write("欠損値の割合:")
                missing_ratio = (numeric_df.isna().sum() / len(numeric_df) * 100).round(2)
                st.dataframe(pd.DataFrame({
                    "カラム": missing_ratio.index,
                    "欠損値数": numeric_df.isna().sum().values,
                    "欠損率(%)": missing_ratio.values
                }))
                
                # 外れ値の検出（IQR法）
                st.write("外れ値の検出（IQR法）:")
                outlier_counts = {}
                
                for col in numeric_df.columns:
                    q1 = numeric_df[col].quantile(0.25)
                    q3 = numeric_df[col].quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    
                    outliers = numeric_df[(numeric_df[col] < lower_bound) | (numeric_df[col] > upper_bound)][col]
                    outlier_counts[col] = len(outliers)
                
                st.dataframe(pd.DataFrame({
                    "カラム": outlier_counts.keys(),
                    "外れ値の数": outlier_counts.values(),
                    "外れ値の割合(%)": [round(count / len(numeric_df) * 100, 2) for count in outlier_counts.values()]
                }))
            
            # カテゴリ列の統計情報
            categorical_cols = data.select_dtypes(include=["object", "category"]).columns
            
            if not categorical_cols.empty:
                st.write("カテゴリデータの統計情報:")
                
                for col in categorical_cols:
                    value_counts = data[col].value_counts()
                    if len(value_counts) <= 10:  # 値が多すぎる場合は表示を制限
                        st.write(f"{col}の頻度:")
                        st.dataframe(pd.DataFrame({
                            "値": value_counts.index,
                            "頻度": value_counts.values,
                            "割合(%)": (value_counts.values / len(data) * 100).round(2)
                        }))
                    else:
                        st.write(f"{col}: {len(value_counts)}個の一意な値（上位10件表示）")
                        value_counts = value_counts.head(10)
                        st.dataframe(pd.DataFrame({
                            "値": value_counts.index,
                            "頻度": value_counts.values,
                            "割合(%)": (value_counts.values / len(data) * 100).round(2)
                        }))
            
            # 時系列データの場合の追加統計
            if data_type == "time_series":
                st.write("時系列データの統計情報:")
                
                # 時間カラムを特定
                time_cols = [col for col in data.columns if col.lower() in ["time", "timestamp", "date", "datetime"]]
                
                if time_cols and pd.api.types.is_datetime64_any_dtype(data[time_cols[0]]):
                    time_col = time_cols[0]
                    time_diff = data[time_col].diff()
                    
                    st.write(f"時間間隔の統計:")
                    st.write(f"最小間隔: {time_diff.min()}")
                    st.write(f"最大間隔: {time_diff.max()}")
                    st.write(f"平均間隔: {time_diff.mean()}")
                    st.write(f"中央間隔: {time_diff.median()}")
                    
                    # 時系列の長さ
                    total_duration = data[time_col].max() - data[time_col].min()
                    st.write(f"総期間: {total_duration}")
            
            # 空間データの場合の追加統計
            if data_type == "geo":
                st.write("空間データの統計情報:")
                
                # 緯度経度カラムを特定
                lat_cols = [col for col in data.columns if col.lower() in ["lat", "latitude"]]
                lng_cols = [col for col in data.columns if col.lower() in ["lng", "lon", "longitude"]]
                
                if lat_cols and lng_cols:
                    lat_col = lat_cols[0]
                    lng_col = lng_cols[0]
                    
                    st.write(f"位置データの統計:")
                    st.write(f"緯度範囲: {data[lat_col].min():.6f} ～ {data[lat_col].max():.6f}")
                    st.write(f"経度範囲: {data[lng_col].min():.6f} ～ {data[lng_col].max():.6f}")
                    
                    # 簡易的な空間分布の表示
                    st.write("格子分布（緯度・経度をビンに分割）:")
                    lat_bins = pd.cut(data[lat_col], bins=5)
                    lng_bins = pd.cut(data[lng_col], bins=5)
                    grid_counts = pd.crosstab(lat_bins, lng_bins)
                    st.dataframe(grid_counts)
        
        elif data_type == "dict_list":
            # 辞書のリストをDataFrameに変換
            df = pd.DataFrame(data)
            data_type_converted = self._determine_data_type(df)
            
            # 再帰的に呼び出し
            self._render_statistics_view(df, data_type_converted)
        
        elif data_type == "list":
            # リストの場合
            st.write(f"データ形式: リスト ({len(data)}件)")
            
            # 数値リストの場合の統計情報
            if all(isinstance(item, (int, float)) for item in data):
                st.write("数値リストの統計情報:")
                
                # 基本統計量
                stat_df = pd.DataFrame({
                    "統計量": ["データ数", "平均値", "標準偏差", "最小値", "25%", "中央値", "75%", "最大値"],
                    "値": [
                        len(data),
                        np.mean(data),
                        np.std(data),
                        np.min(data),
                        np.percentile(data, 25),
                        np.median(data),
                        np.percentile(data, 75),
                        np.max(data)
                    ]
                })
                
                st.dataframe(stat_df)
                
                # ヒストグラムの表示
                fig, ax = plt.subplots()
                ax.hist(data, bins=20, alpha=0.7)
                ax.grid(True, linestyle="--", alpha=0.7)
                ax.set_title("ヒストグラム")
                st.pyplot(fig)
            
            # 文字列リストの場合
            elif all(isinstance(item, str) for item in data):
                st.write("文字列リストの統計情報:")
                
                # 基本統計量
                lengths = [len(item) for item in data]
                stat_df = pd.DataFrame({
                    "統計量": ["データ数", "平均文字数", "最小文字数", "最大文字数"],
                    "値": [
                        len(data),
                        np.mean(lengths),
                        np.min(lengths),
                        np.max(lengths)
                    ]
                })
                
                st.dataframe(stat_df)
                
                # 頻度分析（上位10件）
                from collections import Counter
                counter = Counter(data)
                most_common = counter.most_common(10)
                
                if most_common:
                    st.write("最も頻出する値（上位10件）:")
                    freq_df = pd.DataFrame({
                        "値": [item[0] for item in most_common],
                        "頻度": [item[1] for item in most_common],
                        "割合(%)": [(item[1] / len(data) * 100) for item in most_common]
                    })
                    st.dataframe(freq_df)
            
            else:
                st.write("このデータタイプの統計分析はサポートされていません")
        
        elif data_type == "dict":
            # 辞書の場合
            st.write(f"データ形式: 辞書 ({len(data)}キー)")
            
            # 値の型の分布
            value_types = {}
            for key, value in data.items():
                value_type = type(value).__name__
                if value_type not in value_types:
                    value_types[value_type] = 0
                value_types[value_type] += 1
            
            st.write("値の型の分布:")
            st.dataframe(pd.DataFrame({
                "型": value_types.keys(),
                "数": value_types.values(),
                "割合(%)": [(count / len(data) * 100) for count in value_types.values()]
            }))
            
            # リスト値の長さ分布
            list_lengths = {}
            for key, value in data.items():
                if isinstance(value, list):
                    list_lengths[key] = len(value)
            
            if list_lengths:
                st.write("リスト値の長さ:")
                st.dataframe(pd.DataFrame({
                    "キー": list_lengths.keys(),
                    "リスト長": list_lengths.values()
                }))
            
            # 辞書値のキー数分布
            dict_sizes = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    dict_sizes[key] = len(value)
            
            if dict_sizes:
                st.write("辞書値のキー数:")
                st.dataframe(pd.DataFrame({
                    "キー": dict_sizes.keys(),
                    "キー数": dict_sizes.values()
                }))
        
        else:
            # その他のデータ型
            st.write(f"データ型 {type(data).__name__} の統計分析はサポートされていません")
    
    def _render_visualization_view(self, data: Any, data_type: str) -> None:
        """
        可視化ビューを表示
        
        Parameters
        ----------
        data : Any
            表示対象データ
        data_type : str
            データ型
        """
        # データ型に応じた表示
        if data_type in ["dataframe", "geo", "time_series"]:
            # DataFrameの場合
            st.write(f"データ形式: DataFrame ({len(data)}行 × {len(data.columns)}列)")
            
            # グラフタイプの選択
            chart_type = st.selectbox(
                "グラフの種類",
                options=["ヒストグラム", "散布図", "折れ線グラフ", "箱ひげ図", "ヒートマップ", "棒グラフ", "円グラフ"]
            )
            
            # 数値列の抽出
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            
            if not numeric_cols:
                st.warning("数値データがありません")
                return
            
            if chart_type == "ヒストグラム":
                # 列の選択
                column = st.selectbox("カラム", options=numeric_cols)
                
                # ビン数の設定
                bins = st.slider("ビン数", min_value=5, max_value=100, value=20)
                
                # ヒストグラムの描画
                fig, ax = plt.subplots()
                ax.hist(data[column].dropna(), bins=bins, alpha=0.7)
                ax.set_title(f"{column}のヒストグラム")
                ax.set_xlabel(column)
                ax.set_ylabel("頻度")
                ax.grid(True, linestyle="--", alpha=0.7)
                st.pyplot(fig)
            
            elif chart_type == "散布図":
                # X軸とY軸の列の選択
                x_column = st.selectbox("X軸", options=numeric_cols, index=0)
                y_column = st.selectbox("Y軸", options=numeric_cols, index=min(1, len(numeric_cols) - 1))
                
                # カテゴリ列があれば色分け用に選択可能に
                categorical_cols = data.select_dtypes(include=["object", "category"]).columns.tolist()
                color_column = None
                if categorical_cols:
                    use_color = st.checkbox("カテゴリで色分け")
                    if use_color:
                        color_column = st.selectbox("色分け用カラム", options=categorical_cols)
                
                # 散布図の描画
                fig, ax = plt.subplots()
                if color_column:
                    categories = data[color_column].unique()
                    for category in categories:
                        subset = data[data[color_column] == category]
                        ax.scatter(subset[x_column], subset[y_column], alpha=0.7, label=category)
                    ax.legend()
                else:
                    ax.scatter(data[x_column], data[y_column], alpha=0.7)
                
                ax.set_title(f"{x_column} vs {y_column}")
                ax.set_xlabel(x_column)
                ax.set_ylabel(y_column)
                ax.grid(True, linestyle="--", alpha=0.7)
                st.pyplot(fig)
            
            elif chart_type == "折れ線グラフ":
                # 時系列データの場合
                if data_type == "time_series":
                    # 時間列を特定
                    time_cols = [col for col in data.columns if col.lower() in ["time", "timestamp", "date", "datetime"]]
                    time_column = st.selectbox("時間軸", options=time_cols) if time_cols else None
                    
                    if time_column:
                        # 時間でソート
                        if pd.api.types.is_datetime64_any_dtype(data[time_column]):
                            sorted_data = data.sort_values(by=time_column)
                        else:
                            try:
                                sorted_data = data.copy()
                                sorted_data[time_column] = pd.to_datetime(sorted_data[time_column])
                                sorted_data = sorted_data.sort_values(by=time_column)
                            except:
                                sorted_data = data
                        
                        # Y軸の列の選択（複数選択可能）
                        y_columns = st.multiselect("Y軸", options=numeric_cols, default=[numeric_cols[0]])
                        
                        if y_columns:
                            # 折れ線グラフの描画
                            fig, ax = plt.subplots()
                            
                            for y_column in y_columns:
                                ax.plot(sorted_data[time_column], sorted_data[y_column], marker="o", markersize=3, alpha=0.7, label=y_column)
                            
                            ax.set_title("時系列データ")
                            ax.set_xlabel(time_column)
                            ax.set_ylabel("値")
                            ax.grid(True, linestyle="--", alpha=0.7)
                            ax.legend()
                            
                            # X軸の日付フォーマットを調整
                            fig.autofmt_xdate()
                            
                            st.pyplot(fig)
                        else:
                            st.warning("Y軸のカラムを選択してください")
                    else:
                        st.warning("時間カラムが見つかりません")
                
                # 一般的なデータの場合
                else:
                    # X軸とY軸の列の選択
                    x_column = st.selectbox("X軸", options=numeric_cols, index=0)
                    y_columns = st.multiselect("Y軸", options=numeric_cols, default=[numeric_cols[min(1, len(numeric_cols) - 1)]])
                    
                    if y_columns:
                        # X軸でソート
                        sorted_data = data.sort_values(by=x_column)
                        
                        # 折れ線グラフの描画
                        fig, ax = plt.subplots()
                        
                        for y_column in y_columns:
                            ax.plot(sorted_data[x_column], sorted_data[y_column], marker="o", markersize=3, alpha=0.7, label=y_column)
                        
                        ax.set_title(f"{x_column}に対する値の変化")
                        ax.set_xlabel(x_column)
                        ax.set_ylabel("値")
                        ax.grid(True, linestyle="--", alpha=0.7)
                        ax.legend()
                        
                        st.pyplot(fig)
                    else:
                        st.warning("Y軸のカラムを選択してください")
            
            elif chart_type == "箱ひげ図":
                # Y軸の列の選択（複数選択可能）
                y_columns = st.multiselect("カラム", options=numeric_cols, default=[numeric_cols[0]])
                
                # カテゴリ列があればグループ化用に選択可能に
                categorical_cols = data.select_dtypes(include=["object", "category"]).columns.tolist()
                group_column = None
                if categorical_cols:
                    use_group = st.checkbox("カテゴリでグループ化")
                    if use_group:
                        group_column = st.selectbox("グループ化用カラム", options=categorical_cols)
                
                if y_columns:
                    # 箱ひげ図の描画
                    if group_column:
                        # グループごとの箱ひげ図
                        melted_data = pd.melt(data, id_vars=[group_column], value_vars=y_columns, var_name="カラム", value_name="値")
                        fig, ax = plt.subplots()
                        sns.boxplot(x="カラム", y="値", hue=group_column, data=melted_data, ax=ax)
                        ax.set_title("グループ別の箱ひげ図")
                        ax.grid(True, linestyle="--", alpha=0.7)
                        plt.xticks(rotation=45)
                        st.pyplot(fig)
                    else:
                        # 単純な箱ひげ図
                        melted_data = pd.melt(data, value_vars=y_columns, var_name="カラム", value_name="値")
                        fig, ax = plt.subplots()
                        sns.boxplot(x="カラム", y="値", data=melted_data, ax=ax)
                        ax.set_title("箱ひげ図")
                        ax.grid(True, linestyle="--", alpha=0.7)
                        plt.xticks(rotation=45)
                        st.pyplot(fig)
                else:
                    st.warning("カラムを選択してください")
            
            elif chart_type == "ヒートマップ":
                # 相関行列の表示
                st.write("数値カラム間の相関行列:")
                
                # 相関行列の計算
                corr_matrix = data[numeric_cols].corr()
                
                # ヒートマップの描画
                fig, ax = plt.subplots(figsize=(10, 8))
                sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
                ax.set_title("相関行列ヒートマップ")
                st.pyplot(fig)
            
            elif chart_type == "棒グラフ":
                # カテゴリ列があれば選択可能に
                categorical_cols = data.select_dtypes(include=["object", "category"]).columns.tolist()
                
                if categorical_cols:
                    # X軸のカテゴリ列
                    x_column = st.selectbox("X軸（カテゴリ）", options=categorical_cols)
                    
                    # Y軸の数値列
                    y_column = st.selectbox("Y軸（数値）", options=numeric_cols)
                    
                    # 集計方法
                    agg_method = st.selectbox(
                        "集計方法",
                        options=["合計", "平均", "カウント", "最大", "最小"],
                        format_func=lambda x: {
                            "合計": "合計 (sum)", "平均": "平均 (mean)",
                            "カウント": "カウント (count)", "最大": "最大 (max)",
                            "最小": "最小 (min)"
                        }.get(x, x)
                    )
                    
                    # 集計関数のマッピング
                    agg_func_map = {
                        "合計": "sum", "平均": "mean", "カウント": "count",
                        "最大": "max", "最小": "min"
                    }
                    
                    # 上位N件表示
                    show_top = st.checkbox("上位N件のみ表示")
                    top_n = None
                    if show_top:
                        top_n = st.number_input("表示件数", min_value=1, max_value=50, value=10)
                    
                    # カテゴリ別に集計
                    grouped = data.groupby(x_column)[y_column].agg(agg_func_map[agg_method]).reset_index()
                    
                    # ソート
                    grouped = grouped.sort_values(by=y_column, ascending=False)
                    
                    # 上位N件の抽出
                    if show_top and top_n is not None:
                        grouped = grouped.head(top_n)
                    
                    # 棒グラフの描画
                    fig, ax = plt.subplots()
                    ax.bar(grouped[x_column], grouped[y_column], alpha=0.7)
                    ax.set_title(f"{x_column}別の{y_column}（{agg_method}）")
                    ax.set_xlabel(x_column)
                    ax.set_ylabel(f"{y_column}（{agg_method}）")
                    ax.grid(True, linestyle="--", alpha=0.7)
                    plt.xticks(rotation=45)
                    st.pyplot(fig)
                else:
                    st.warning("カテゴリカラムがありません")
            
            elif chart_type == "円グラフ":
                # カテゴリ列があれば選択可能に
                categorical_cols = data.select_dtypes(include=["object", "category"]).columns.tolist()
                
                if categorical_cols:
                    # カテゴリ列
                    category_column = st.selectbox("カテゴリ", options=categorical_cols)
                    
                    # 値の列（オプション）
                    use_value = st.checkbox("集計値を使用")
                    value_column = None
                    agg_method = None
                    
                    if use_value:
                        value_column = st.selectbox("値", options=numeric_cols)
                        agg_method = st.selectbox(
                            "集計方法",
                            options=["合計", "平均", "カウント"],
                            format_func=lambda x: {
                                "合計": "合計 (sum)", "平均": "平均 (mean)",
                                "カウント": "カウント (count)"
                            }.get(x, x)
                        )
                    
                    # 集計関数のマッピング
                    agg_func_map = {
                        "合計": "sum", "平均": "mean", "カウント": "count"
                    }
                    
                    # 上位N件表示
                    show_top = st.checkbox("上位N件のみ表示（その他はまとめる）")
                    top_n = None
                    if show_top:
                        top_n = st.number_input("表示件数", min_value=1, max_value=20, value=5)
                    
                    # データの集計
                    if use_value and value_column:
                        grouped = data.groupby(category_column)[value_column].agg(agg_func_map[agg_method]).reset_index()
                        values = grouped[value_column]
                        labels = grouped[category_column]
                    else:
                        # 単純なカウント
                        value_counts = data[category_column].value_counts()
                        values = value_counts.values
                        labels = value_counts.index
                    
                    # 上位N件のみ表示し、残りは「その他」としてまとめる
                    if show_top and top_n is not None and len(labels) > top_n:
                        top_values = values[:top_n]
                        top_labels = labels[:top_n]
                        other_value = sum(values[top_n:])
                        
                        values = np.append(top_values, other_value)
                        labels = np.append(top_labels, "その他")
                    
                    # 円グラフの描画
                    fig, ax = plt.subplots()
                    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, shadow=True)
                    ax.axis("equal")  # 円を正円に
                    
                    if use_value and value_column:
                        ax.set_title(f"{category_column}別の{value_column}（{agg_method}）")
                    else:
                        ax.set_title(f"{category_column}の分布")
                    
                    st.pyplot(fig)
                else:
                    st.warning("カテゴリカラムがありません")
        
        elif data_type == "dict_list":
            # 辞書のリストをDataFrameに変換
            df = pd.DataFrame(data)
            data_type_converted = self._determine_data_type(df)
            
            # 再帰的に呼び出し
            self._render_visualization_view(df, data_type_converted)
        
        elif data_type == "list":
            # リストの場合
            st.write(f"データ形式: リスト ({len(data)}件)")
            
            # 数値リストの場合
            if all(isinstance(item, (int, float)) for item in data):
                # グラフタイプの選択
                chart_type = st.selectbox(
                    "グラフの種類",
                    options=["ヒストグラム", "線グラフ", "散布図", "箱ひげ図"]
                )
                
                if chart_type == "ヒストグラム":
                    # ビン数の設定
                    bins = st.slider("ビン数", min_value=5, max_value=100, value=20)
                    
                    # ヒストグラムの描画
                    fig, ax = plt.subplots()
                    ax.hist(data, bins=bins, alpha=0.7)
                    ax.set_title("ヒストグラム")
                    ax.set_xlabel("値")
                    ax.set_ylabel("頻度")
                    ax.grid(True, linestyle="--", alpha=0.7)
                    st.pyplot(fig)
                
                elif chart_type == "線グラフ":
                    # 線グラフの描画
                    fig, ax = plt.subplots()
                    ax.plot(range(len(data)), data, marker="o", markersize=3, alpha=0.7)
                    ax.set_title("データの推移")
                    ax.set_xlabel("インデックス")
                    ax.set_ylabel("値")
                    ax.grid(True, linestyle="--", alpha=0.7)
                    st.pyplot(fig)
                
                elif chart_type == "散布図":
                    # 散布図の描画
                    fig, ax = plt.subplots()
                    ax.scatter(range(len(data)), data, alpha=0.7)
                    ax.set_title("散布図")
                    ax.set_xlabel("インデックス")
                    ax.set_ylabel("値")
                    ax.grid(True, linestyle="--", alpha=0.7)
                    st.pyplot(fig)
                
                elif chart_type == "箱ひげ図":
                    # 箱ひげ図の描画
                    fig, ax = plt.subplots()
                    ax.boxplot(data, vert=True)
                    ax.set_title("箱ひげ図")
                    ax.set_ylabel("値")
                    ax.grid(True, linestyle="--", alpha=0.7)
                    st.pyplot(fig)
            
            # 文字列リストの場合
            elif all(isinstance(item, str) for item in data):
                st.write("文字列データの可視化:")
                
                # 文字列の長さ分布
                lengths = [len(item) for item in data]
                
                fig, ax = plt.subplots()
                ax.hist(lengths, bins=20, alpha=0.7)
                ax.set_title("文字列長の分布")
                ax.set_xlabel("文字列の長さ")
                ax.set_ylabel("頻度")
                ax.grid(True, linestyle="--", alpha=0.7)
                st.pyplot(fig)
                
                # 頻度分析（上位10件）
                from collections import Counter
                counter = Counter(data)
                most_common = counter.most_common(10)
                
                if most_common:
                    st.write("最も頻出する値（上位10件）:")
                    
                    # 頻度グラフの描画
                    fig, ax = plt.subplots()
                    ax.barh([item[0] for item in most_common], [item[1] for item in most_common])
                    ax.set_title("上位10件の頻度")
                    ax.set_xlabel("頻度")
                    ax.set_ylabel("値")
                    ax.grid(True, linestyle="--", alpha=0.7)
                    st.pyplot(fig)
            
            else:
                st.warning("このリストタイプの可視化はサポートされていません")
        
        elif data_type == "dict":
            # 辞書の場合
            st.write(f"データ形式: 辞書 ({len(data)}キー)")
            
            # 値の型の分布
            value_types = {}
            for key, value in data.items():
                value_type = type(value).__name__
                if value_type not in value_types:
                    value_types[value_type] = 0
                value_types[value_type] += 1
            
            # 型分布の円グラフ
            fig, ax = plt.subplots()
            ax.pie(value_types.values(), labels=value_types.keys(), autopct="%1.1f%%", startangle=90, shadow=True)
            ax.axis("equal")  # 円を正円に
            ax.set_title("値の型の分布")
            st.pyplot(fig)
            
            # 数値値のみを抽出
            numeric_values = {}
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    numeric_values[key] = value
            
            if numeric_values:
                st.write("数値値の分布:")
                
                # 棒グラフの描画
                fig, ax = plt.subplots()
                ax.bar(numeric_values.keys(), numeric_values.values(), alpha=0.7)
                ax.set_title("数値値の分布")
                ax.set_xlabel("キー")
                ax.set_ylabel("値")
                ax.grid(True, linestyle="--", alpha=0.7)
                plt.xticks(rotation=45)
                st.pyplot(fig)
            
            # リスト値の長さ分布
            list_lengths = {}
            for key, value in data.items():
                if isinstance(value, list):
                    list_lengths[key] = len(value)
            
            if list_lengths:
                st.write("リスト値の長さ分布:")
                
                # 棒グラフの描画
                fig, ax = plt.subplots()
                ax.bar(list_lengths.keys(), list_lengths.values(), alpha=0.7)
                ax.set_title("リスト値の長さ分布")
                ax.set_xlabel("キー")
                ax.set_ylabel("リスト長")
                ax.grid(True, linestyle="--", alpha=0.7)
                plt.xticks(rotation=45)
                st.pyplot(fig)
        
        else:
            # その他のデータ型
            st.write(f"データ型 {type(data).__name__} の可視化はサポートされていません")
    
    def _show_column_info(self, df: pd.DataFrame) -> None:
        """
        DataFrameのカラム情報を表示
        
        Parameters
        ----------
        df : pd.DataFrame
            カラム情報を表示するDataFrame
        """
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
                "NULL率(%)": round(null_count / len(df) * 100, 2) if len(df) > 0 else 0,
                "ユニーク値数": unique_count,
                "サンプル値": sample
            })
        
        col_df = pd.DataFrame(col_info)
        st.dataframe(col_df)
