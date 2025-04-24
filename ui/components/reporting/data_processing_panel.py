# -*- coding: utf-8 -*-
"""
ui.components.reporting.data_processing_panel

データ処理設定を行うためのパネルを提供するモジュールです。
データの変換、集計、計算を対話的に設定するためのStreamlitコンポーネントを実装しています。
"""

from typing import Dict, List, Any, Optional, Callable, Union, Tuple
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

from sailing_data_processor.reporting.data_processing.transforms import (
    DataTransformer, SmoothingTransform, ResamplingTransform, NormalizationTransform
)
from sailing_data_processor.reporting.data_processing.aggregators import (
    DataAggregator, TimeAggregator, SpatialAggregator, CategoryAggregator
)
from sailing_data_processor.reporting.data_processing.calculators import (
    BaseCalculator, PerformanceCalculator, StatisticalCalculator, CustomFormulaCalculator
)


class DataProcessingPanel:
    """
    データ処理パネルコンポーネント
    
    データの変換、集計、計算を行うためのパネルを提供するStreamlitコンポーネントです。
    """
    
    def __init__(self, on_processing: Optional[Callable[[Dict[str, Any], Any], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        on_processing : Optional[Callable[[Dict[str, Any], Any], None]], optional
            処理実行時のコールバック, by default None
            - 第1引数: 処理設定
            - 第2引数: 処理結果
        """
        self.on_processing = on_processing
    
    def render(self, data: Any = None, data_id: str = "data") -> Any:
        """
        データ処理パネルを描画
        
        Parameters
        ----------
        data : Any, optional
            処理対象データ, by default None
        data_id : str, optional
            データID, by default "data"
            
        Returns
        -------
        Any
            処理結果データ（処理を実行した場合）
        """
        if data is None:
            st.info("処理対象データがありません。")
            return None
        
        st.subheader("データ処理パネル")
        
        # データ型の判定
        data_type = self._determine_data_type(data)
        
        # データのプレビュー
        with st.expander("データプレビュー", expanded=True):
            self._render_data_preview(data, data_type)
        
        # データ処理タイプの選択
        processing_type = st.selectbox(
            "処理タイプ",
            options=["変換処理", "集計処理", "指標計算"],
            format_func=lambda x: {
                "変換処理": "データ変換（スムージング、リサンプリング、正規化など）",
                "集計処理": "データ集計（時間別、カテゴリ別、空間別集計など）",
                "指標計算": "指標計算（パフォーマンス指標、統計値、カスタム計算など）"
            }.get(x, x)
        )
        
        # 処理タイプに応じたUIを表示
        processed_data = None
        
        if processing_type == "変換処理":
            processed_data = self._render_transformation_panel(data, data_type, data_id)
        elif processing_type == "集計処理":
            processed_data = self._render_aggregation_panel(data, data_type, data_id)
        elif processing_type == "指標計算":
            processed_data = self._render_calculation_panel(data, data_type, data_id)
        
        # プレビューと適用ボタン
        if processed_data is not None:
            with st.expander("処理結果プレビュー", expanded=True):
                self._render_data_preview(processed_data, self._determine_data_type(processed_data))
            
            if st.button("この処理を適用"):
                if self.on_processing:
                    # 処理設定を取得
                    processing_settings = {
                        "processing_type": processing_type,
                        "data_id": data_id,
                        # 各処理タイプによって追加の設定が含まれる
                    }
                    self.on_processing(processing_settings, processed_data)
        
        return processed_data
    
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
            データ型（"dataframe", "dict_list", "dict", "list", "unknown"）
        """
        if isinstance(data, pd.DataFrame):
            return "dataframe"
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return "dict_list"
            else:
                return "list"
        elif isinstance(data, dict):
            return "dict"
        else:
            return "unknown"
    
    def _render_data_preview(self, data: Any, data_type: str) -> None:
        """
        データプレビューを描画
        
        Parameters
        ----------
        data : Any
            プレビュー対象データ
        data_type : str
            データ型
        """
        if data_type == "dataframe":
            # DataFrameの先頭10行を表示
            st.write(f"データ形式: DataFrame ({len(data)}行 x {len(data.columns)}列)")
            st.dataframe(data.head(10))
            
            # カラム情報
            st.write("カラム情報:")
            col_info = []
            for col in data.columns:
                col_info.append({
                    "カラム名": col,
                    "データ型": str(data[col].dtype),
                    "欠損値": data[col].isna().sum(),
                    "ユニーク値": data[col].nunique()
                })
            st.dataframe(pd.DataFrame(col_info))
        
        elif data_type == "dict_list":
            # 辞書リストの先頭10件を表示
            st.write(f"データ形式: 辞書リスト ({len(data)}件)")
            
            if len(data) > 0:
                # pandas DataFrameに変換して表示
                df = pd.DataFrame(data[:10])
                st.dataframe(df)
                
                # キー情報
                st.write("キー情報:")
                st.write(", ".join(data[0].keys()))
            else:
                st.write("空のリストです")
        
        elif data_type == "dict":
            # 辞書のキーと値を表示
            st.write(f"データ形式: 辞書 ({len(data)}キー)")
            
            # キーと値の一部を表示
            preview_data = {}
            for key, value in list(data.items())[:10]:  # 最初の10キーのみ
                if isinstance(value, list):
                    if len(value) > 3:
                        preview_data[key] = f"リスト ({len(value)}件) [最初の3件: {value[:3]}...]"
                    else:
                        preview_data[key] = f"リスト ({len(value)}件) {value}"
                elif isinstance(value, dict):
                    preview_data[key] = f"辞書 ({len(value)}キー)"
                else:
                    preview_data[key] = str(value)
            
            st.json(preview_data)
        
        elif data_type == "list":
            # リストの内容を表示
            st.write(f"データ形式: リスト ({len(data)}件)")
            
            if len(data) > 0:
                if all(isinstance(item, (int, float, str, bool)) for item in data):
                    # プリミティブ型のリスト
                    preview = data[:20]  # 最初の20件
                    st.write(preview)
                    if len(data) > 20:
                        st.write("...")
                else:
                    # 複雑なオブジェクトのリスト
                    st.write("複雑なオブジェクトを含むリスト")
            else:
                st.write("空のリストです")
        
        else:
            # その他のデータ型
            st.write(f"データ形式: {type(data).__name__}")
            st.write(str(data)[:1000])  # 最初の1000文字まで
    
    def _render_transformation_panel(self, data: Any, data_type: str, data_id: str) -> Any:
        """
        変換処理パネルを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
        data_id : str
            データID
            
        Returns
        -------
        Any
            処理結果データ（処理を実行した場合）
        """
        st.subheader("データ変換設定")
        
        # 変換タイプの選択
        transform_type = st.selectbox(
            "変換タイプ",
            options=["smoothing", "resampling", "normalization"],
            format_func=lambda x: {
                "smoothing": "スムージング（平滑化）",
                "resampling": "リサンプリング（時間間隔変更）",
                "normalization": "正規化（値の範囲変換）"
            }.get(x, x)
        )
        
        # 変換パラメータの設定
        transform_params = {}
        
        if transform_type == "smoothing":
            # スムージングパラメータ
            transform_params = self._render_smoothing_params(data, data_type)
        
        elif transform_type == "resampling":
            # リサンプリングパラメータ
            transform_params = self._render_resampling_params(data, data_type)
        
        elif transform_type == "normalization":
            # 正規化パラメータ
            transform_params = self._render_normalization_params(data, data_type)
        
        # 変換の実行
        processed_data = None
        
        if st.button("変換を実行", key=f"transform_{data_id}"):
            # 選択した変換タイプに応じた変換器を作成
            transformer = None
            
            if transform_type == "smoothing":
                transformer = SmoothingTransform(transform_params)
            elif transform_type == "resampling":
                transformer = ResamplingTransform(transform_params)
            elif transform_type == "normalization":
                transformer = NormalizationTransform(transform_params)
            
            if transformer:
                # 変換を実行
                with st.spinner("変換処理中..."):
                    try:
                        processed_data = transformer.transform(data)
                        st.success("変換が完了しました")
                    except Exception as e:
                        st.error(f"変換エラー: {str(e)}")
        
        return processed_data
    
    def _render_smoothing_params(self, data: Any, data_type: str) -> Dict[str, Any]:
        """
        スムージングパラメータ設定UIを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
            
        Returns
        -------
        Dict[str, Any]
            スムージングパラメータ
        """
        params = {}
        
        # スムージング方法
        method = st.selectbox(
            "スムージング方法",
            options=["moving_avg", "exponential", "median", "gaussian"],
            format_func=lambda x: {
                "moving_avg": "移動平均",
                "exponential": "指数平滑化",
                "median": "メディアンフィルタ",
                "gaussian": "ガウシアンフィルタ"
            }.get(x, x)
        )
        params["method"] = method
        
        # 窓サイズ（移動平均、メディアンフィルタ、ガウシアンフィルタ用）
        if method in ["moving_avg", "median", "gaussian"]:
            window_size = st.slider("窓サイズ", min_value=3, max_value=31, value=5, step=2)
            params["window_size"] = window_size
        
        # α値（指数平滑化用）
        if method == "exponential":
            alpha = st.slider("α値", min_value=0.1, max_value=1.0, value=0.3, step=0.1)
            params["alpha"] = alpha
        
        # σ値（ガウシアンフィルタ用）
        if method == "gaussian":
            sigma = st.slider("σ値", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
            params["sigma"] = sigma
        
        # 対象カラムの選択（DataFrame、辞書リストの場合）
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # 数値型カラムのフィルタリング
            if data_type == "dataframe":
                numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
            else:  # dict_list
                numeric_columns = []
                if len(data) > 0:
                    for key, value in data[0].items():
                        if isinstance(value, (int, float)):
                            numeric_columns.append(key)
            
            # カラム選択
            selected_columns = st.multiselect(
                "対象カラム",
                options=columns,
                default=numeric_columns
            )
            
            if selected_columns:
                params["columns"] = selected_columns
        
        return params
    
    def _render_resampling_params(self, data: Any, data_type: str) -> Dict[str, Any]:
        """
        リサンプリングパラメータ設定UIを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
            
        Returns
        -------
        Dict[str, Any]
            リサンプリングパラメータ
        """
        params = {}
        
        # リサンプリング方法
        method = st.selectbox(
            "リサンプリング方法",
            options=["downsample", "upsample"],
            format_func=lambda x: {
                "downsample": "ダウンサンプリング（間引き）",
                "upsample": "アップサンプリング（補間）"
            }.get(x, x)
        )
        params["method"] = method
        
        # 時間列の選択（DataFrame、辞書リストの場合）
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # 時間カラム候補の検出
            time_column_candidates = [col for col in columns if col.lower() in ["time", "timestamp", "date", "datetime"]]
            
            # 時間カラムの選択
            time_column = st.selectbox(
                "時間カラム",
                options=columns,
                index=columns.index(time_column_candidates[0]) if time_column_candidates and time_column_candidates[0] in columns else 0
            )
            params["time_column"] = time_column
        
        # 時間間隔
        rule_options = [
            "1s", "5s", "10s", "30s",  # 秒
            "1min", "5min", "10min", "30min",  # 分
            "1h", "2h", "6h", "12h",  # 時間
            "1D", "1W", "1M"  # 日、週、月
        ]
        rule_labels = {
            "1s": "1秒", "5s": "5秒", "10s": "10秒", "30s": "30秒",
            "1min": "1分", "5min": "5分", "10min": "10分", "30min": "30分",
            "1h": "1時間", "2h": "2時間", "6h": "6時間", "12h": "12時間",
            "1D": "1日", "1W": "1週間", "1M": "1ヶ月"
        }
        
        rule = st.selectbox(
            "時間間隔",
            options=rule_options,
            format_func=lambda x: rule_labels.get(x, x)
        )
        params["rule"] = rule
        
        # 補間方法（アップサンプリングの場合）
        if method == "upsample":
            interpolation_options = ["linear", "cubic", "nearest", "quadratic", "slinear"]
            interpolation_labels = {
                "linear": "線形補間",
                "cubic": "3次スプライン補間",
                "nearest": "最近傍補間",
                "quadratic": "2次スプライン補間",
                "slinear": "区分線形スプライン"
            }
            
            interpolation = st.selectbox(
                "補間方法",
                options=interpolation_options,
                format_func=lambda x: interpolation_labels.get(x, x)
            )
            params["interpolation"] = interpolation
        
        return params
    
    def _render_normalization_params(self, data: Any, data_type: str) -> Dict[str, Any]:
        """
        正規化パラメータ設定UIを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
            
        Returns
        -------
        Dict[str, Any]
            正規化パラメータ
        """
        params = {}
        
        # 正規化方法
        method = st.selectbox(
            "正規化方法",
            options=["min_max", "z_score", "robust"],
            format_func=lambda x: {
                "min_max": "最小-最大正規化",
                "z_score": "Z-スコア正規化",
                "robust": "ロバスト正規化"
            }.get(x, x)
        )
        params["method"] = method
        
        # 最小-最大正規化の範囲
        if method == "min_max":
            col1, col2 = st.columns(2)
            with col1:
                target_min = st.number_input("最小値", value=0.0, format="%.2f")
                params["target_min"] = target_min
            
            with col2:
                target_max = st.number_input("最大値", value=1.0, format="%.2f")
                params["target_max"] = target_max
        
        # 対象カラムの選択（DataFrame、辞書リストの場合）
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # 数値型カラムのフィルタリング
            if data_type == "dataframe":
                numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
            else:  # dict_list
                numeric_columns = []
                if len(data) > 0:
                    for key, value in data[0].items():
                        if isinstance(value, (int, float)):
                            numeric_columns.append(key)
            
            # カラム選択
            selected_columns = st.multiselect(
                "対象カラム",
                options=columns,
                default=numeric_columns
            )
            
            if selected_columns:
                params["columns"] = selected_columns
        
        return params
    
    def _render_aggregation_panel(self, data: Any, data_type: str, data_id: str) -> Any:
        """
        集計処理パネルを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
        data_id : str
            データID
            
        Returns
        -------
        Any
            処理結果データ（処理を実行した場合）
        """
        st.subheader("データ集計設定")
        
        # 集計タイプの選択
        aggregation_type = st.selectbox(
            "集計タイプ",
            options=["time", "spatial", "category"],
            format_func=lambda x: {
                "time": "時間別集計",
                "spatial": "空間別集計",
                "category": "カテゴリ別集計"
            }.get(x, x)
        )
        
        # 集計パラメータの設定
        aggregation_params = {}
        
        if aggregation_type == "time":
            # 時間別集計パラメータ
            aggregation_params = self._render_time_aggregation_params(data, data_type)
        
        elif aggregation_type == "spatial":
            # 空間別集計パラメータ
            aggregation_params = self._render_spatial_aggregation_params(data, data_type)
        
        elif aggregation_type == "category":
            # カテゴリ別集計パラメータ
            aggregation_params = self._render_category_aggregation_params(data, data_type)
        
        # 集計の実行
        processed_data = None
        
        if st.button("集計を実行", key=f"aggregate_{data_id}"):
            # 選択した集計タイプに応じた集計器を作成
            aggregator = None
            
            if aggregation_type == "time":
                aggregator = TimeAggregator(aggregation_params)
            elif aggregation_type == "spatial":
                aggregator = SpatialAggregator(aggregation_params)
            elif aggregation_type == "category":
                aggregator = CategoryAggregator(aggregation_params)
            
            if aggregator:
                # 集計を実行
                with st.spinner("集計処理中..."):
                    try:
                        processed_data = aggregator.aggregate(data)
                        st.success("集計が完了しました")
                    except Exception as e:
                        st.error(f"集計エラー: {str(e)}")
        
        return processed_data
    
    def _render_time_aggregation_params(self, data: Any, data_type: str) -> Dict[str, Any]:
        """
        時間別集計パラメータ設定UIを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
            
        Returns
        -------
        Dict[str, Any]
            時間別集計パラメータ
        """
        params = {}
        
        # 時間列の選択
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # 時間カラム候補の検出
            time_column_candidates = [col for col in columns if col.lower() in ["time", "timestamp", "date", "datetime"]]
            
            # 時間カラムの選択
            time_column = st.selectbox(
                "時間カラム",
                options=columns,
                index=columns.index(time_column_candidates[0]) if time_column_candidates and time_column_candidates[0] in columns else 0
            )
            params["time_column"] = time_column
        
        # 時間単位の選択
        time_unit_options = [
            "1s", "5s", "10s", "30s",  # 秒
            "1min", "5min", "10min", "30min",  # 分
            "1h", "2h", "6h", "12h",  # 時間
            "1D", "1W", "1M"  # 日、週、月
        ]
        time_unit_labels = {
            "1s": "1秒", "5s": "5秒", "10s": "10秒", "30s": "30秒",
            "1min": "1分", "5min": "5分", "10min": "10分", "30min": "30分",
            "1h": "1時間", "2h": "2時間", "6h": "6時間", "12h": "12時間",
            "1D": "1日", "1W": "1週間", "1M": "1ヶ月"
        }
        
        time_unit = st.selectbox(
            "時間単位",
            options=time_unit_options,
            format_func=lambda x: time_unit_labels.get(x, x)
        )
        params["time_unit"] = time_unit
        
        # 集計関数の設定
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # 数値型カラムの検出
            if data_type == "dataframe":
                numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
            else:  # dict_list
                numeric_columns = []
                if len(data) > 0:
                    for key, value in data[0].items():
                        if isinstance(value, (int, float)):
                            numeric_columns.append(key)
            
            # 集計対象カラムの選択
            selected_columns = st.multiselect(
                "集計対象カラム",
                options=columns,
                default=numeric_columns
            )
            
            if selected_columns:
                # 各カラムの集計関数
                aggregation_funcs = {}
                
                st.write("各カラムの集計関数:")
                for col in selected_columns:
                    func = st.selectbox(
                        f"{col}の集計関数",
                        options=["mean", "sum", "min", "max", "count", "median"],
                        format_func=lambda x: {
                            "mean": "平均", "sum": "合計", "min": "最小値",
                            "max": "最大値", "count": "カウント", "median": "中央値"
                        }.get(x, x),
                        key=f"time_agg_func_{col}"
                    )
                    aggregation_funcs[col] = func
                
                params["aggregation_funcs"] = aggregation_funcs
        
        return params
    
    def _render_spatial_aggregation_params(self, data: Any, data_type: str) -> Dict[str, Any]:
        """
        空間別集計パラメータ設定UIを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
            
        Returns
        -------
        Dict[str, Any]
            空間別集計パラメータ
        """
        params = {}
        
        # 空間列の選択
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # 緯度・経度カラム候補の検出
            lat_column_candidates = [col for col in columns if col.lower() in ["lat", "latitude"]]
            lng_column_candidates = [col for col in columns if col.lower() in ["lng", "lon", "longitude"]]
            
            # 緯度カラムの選択
            lat_column = st.selectbox(
                "緯度カラム",
                options=columns,
                index=columns.index(lat_column_candidates[0]) if lat_column_candidates and lat_column_candidates[0] in columns else 0
            )
            params["lat_column"] = lat_column
            
            # 経度カラムの選択
            lng_column = st.selectbox(
                "経度カラム",
                options=columns,
                index=columns.index(lng_column_candidates[0]) if lng_column_candidates and lng_column_candidates[0] in columns else 0
            )
            params["lng_column"] = lng_column
        
        # 集計方法
        method = st.selectbox(
            "集計方法",
            options=["grid", "distance"],
            format_func=lambda x: {
                "grid": "グリッド方式（格子状に分割）",
                "distance": "距離方式（近接ポイントをグループ化）"
            }.get(x, x)
        )
        params["method"] = method
        
        # グリッドサイズ（グリッド方式の場合）
        if method == "grid":
            grid_size = st.number_input(
                "グリッドサイズ（度単位、約100mは0.001度）",
                min_value=0.0001,
                max_value=0.1,
                value=0.001,
                format="%.5f",
                step=0.0001
            )
            params["grid_size"] = grid_size
        
        # 距離閾値（距離方式の場合）
        if method == "distance":
            distance_threshold = st.number_input(
                "距離閾値（メートル単位）",
                min_value=10.0,
                max_value=1000.0,
                value=100.0,
                step=10.0
            )
            params["distance_threshold"] = distance_threshold
        
        # 集計関数の設定
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # 緯度・経度カラムを除外
            columns = [col for col in columns if col not in [lat_column, lng_column]]
            
            # 数値型カラムの検出
            if data_type == "dataframe":
                numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
                numeric_columns = [col for col in numeric_columns if col not in [lat_column, lng_column]]
            else:  # dict_list
                numeric_columns = []
                if len(data) > 0:
                    for key, value in data[0].items():
                        if isinstance(value, (int, float)) and key not in [lat_column, lng_column]:
                            numeric_columns.append(key)
            
            # 集計対象カラムの選択
            selected_columns = st.multiselect(
                "集計対象カラム",
                options=columns,
                default=numeric_columns
            )
            
            if selected_columns:
                # 各カラムの集計関数
                aggregation_funcs = {}
                
                st.write("各カラムの集計関数:")
                for col in selected_columns:
                    func = st.selectbox(
                        f"{col}の集計関数",
                        options=["mean", "sum", "min", "max", "count", "median"],
                        format_func=lambda x: {
                            "mean": "平均", "sum": "合計", "min": "最小値",
                            "max": "最大値", "count": "カウント", "median": "中央値"
                        }.get(x, x),
                        key=f"spatial_agg_func_{col}"
                    )
                    aggregation_funcs[col] = func
                
                params["aggregation_funcs"] = aggregation_funcs
        
        return params
    
    def _render_category_aggregation_params(self, data: Any, data_type: str) -> Dict[str, Any]:
        """
        カテゴリ別集計パラメータ設定UIを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
            
        Returns
        -------
        Dict[str, Any]
            カテゴリ別集計パラメータ
        """
        params = {}
        
        # カテゴリ列の選択
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # カテゴリカラムの選択
            category_columns = st.multiselect(
                "カテゴリカラム",
                options=columns
            )
            
            if category_columns:
                params["category_columns"] = category_columns
            else:
                st.warning("少なくとも1つのカテゴリカラムを選択してください")
        
        # 集計関数の設定
        if data_type in ["dataframe", "dict_list"] and "category_columns" in params:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # カテゴリカラムを除外
            columns = [col for col in columns if col not in params["category_columns"]]
            
            # 数値型カラムの検出
            if data_type == "dataframe":
                numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
                numeric_columns = [col for col in numeric_columns if col not in params["category_columns"]]
            else:  # dict_list
                numeric_columns = []
                if len(data) > 0:
                    for key, value in data[0].items():
                        if isinstance(value, (int, float)) and key not in params["category_columns"]:
                            numeric_columns.append(key)
            
            # 集計対象カラムの選択
            selected_columns = st.multiselect(
                "集計対象カラム",
                options=columns,
                default=numeric_columns
            )
            
            if selected_columns:
                # 各カラムの集計関数
                aggregation_funcs = {}
                
                st.write("各カラムの集計関数:")
                for col in selected_columns:
                    func = st.selectbox(
                        f"{col}の集計関数",
                        options=["mean", "sum", "min", "max", "count", "median"],
                        format_func=lambda x: {
                            "mean": "平均", "sum": "合計", "min": "最小値",
                            "max": "最大値", "count": "カウント", "median": "中央値"
                        }.get(x, x),
                        key=f"category_agg_func_{col}"
                    )
                    aggregation_funcs[col] = func
                
                params["aggregation_funcs"] = aggregation_funcs
        
        return params
    
    def _render_calculation_panel(self, data: Any, data_type: str, data_id: str) -> Any:
        """
        指標計算パネルを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
        data_id : str
            データID
            
        Returns
        -------
        Any
            処理結果データ（処理を実行した場合）
        """
        st.subheader("指標計算設定")
        
        # 計算タイプの選択
        calculation_type = st.selectbox(
            "計算タイプ",
            options=["performance", "statistical", "custom"],
            format_func=lambda x: {
                "performance": "パフォーマンス指標計算",
                "statistical": "統計値計算",
                "custom": "カスタム計算式"
            }.get(x, x)
        )
        
        # 計算パラメータの設定
        calculation_params = {}
        
        if calculation_type == "performance":
            # パフォーマンス指標計算パラメータ
            calculation_params = self._render_performance_calculation_params(data, data_type)
        
        elif calculation_type == "statistical":
            # 統計値計算パラメータ
            calculation_params = self._render_statistical_calculation_params(data, data_type)
        
        elif calculation_type == "custom":
            # カスタム計算式パラメータ
            calculation_params = self._render_custom_calculation_params(data, data_type)
        
        # 計算の実行
        processed_data = None
        
        if st.button("計算を実行", key=f"calculate_{data_id}"):
            # 選択した計算タイプに応じた計算器を作成
            calculator = None
            
            if calculation_type == "performance":
                calculator = PerformanceCalculator(calculation_params)
            elif calculation_type == "statistical":
                calculator = StatisticalCalculator(calculation_params)
            elif calculation_type == "custom":
                calculator = CustomFormulaCalculator(calculation_params)
            
            if calculator:
                # 計算を実行
                with st.spinner("計算処理中..."):
                    try:
                        processed_data = calculator.calculate(data)
                        st.success("計算が完了しました")
                    except Exception as e:
                        st.error(f"計算エラー: {str(e)}")
        
        return processed_data
    
    def _render_performance_calculation_params(self, data: Any, data_type: str) -> Dict[str, Any]:
        """
        パフォーマンス指標計算パラメータ設定UIを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
            
        Returns
        -------
        Dict[str, Any]
            パフォーマンス指標計算パラメータ
        """
        params = {}
        
        # カラムの特定（DataFrame、辞書リストの場合）
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # 速度カラム候補
            speed_columns = [col for col in columns if col.lower() in ["speed", "velocity", "boat_speed"]]
            direction_columns = [col for col in columns if col.lower() in ["direction", "heading", "course", "cog"]]
            wind_direction_columns = [col for col in columns if "wind" in col.lower() and "direction" in col.lower()]
            wind_speed_columns = [col for col in columns if "wind" in col.lower() and ("speed" in col.lower() or "velocity" in col.lower())]
            
            # 速度カラム
            speed_column = st.selectbox(
                "速度カラム",
                options=columns,
                index=columns.index(speed_columns[0]) if speed_columns and speed_columns[0] in columns else 0
            )
            params["speed_column"] = speed_column
            
            # 方向カラム
            direction_column = st.selectbox(
                "方向カラム",
                options=columns,
                index=columns.index(direction_columns[0]) if direction_columns and direction_columns[0] in columns else 0
            )
            params["direction_column"] = direction_column
            
            # 風向カラム
            wind_direction_column = st.selectbox(
                "風向カラム",
                options=columns,
                index=columns.index(wind_direction_columns[0]) if wind_direction_columns and wind_direction_columns[0] in columns else 0
            )
            params["wind_direction_column"] = wind_direction_column
            
            # 風速カラム
            wind_speed_column = st.selectbox(
                "風速カラム",
                options=columns,
                index=columns.index(wind_speed_columns[0]) if wind_speed_columns and wind_speed_columns[0] in columns else 0
            )
            params["wind_speed_column"] = wind_speed_column
        
        # 計算する指標
        metrics = st.multiselect(
            "計算する指標",
            options=["vmg", "target_ratio", "tacking_efficiency"],
            format_func=lambda x: {
                "vmg": "VMG（風上/風下方向の有効速度）",
                "target_ratio": "対ターゲット速度比率",
                "tacking_efficiency": "タッキング効率"
            }.get(x, x),
            default=["vmg", "target_ratio"]
        )
        params["metrics"] = metrics
        
        # ターゲット速度の設定（対ターゲット速度比率の場合）
        if "target_ratio" in metrics:
            with st.expander("ターゲット速度設定"):
                # ポーラーデータの選択またはカスタム入力
                polar_type = st.radio(
                    "ポーラーデータタイプ",
                    options=["preset", "custom"],
                    format_func=lambda x: {
                        "preset": "プリセット",
                        "custom": "カスタム"
                    }.get(x, x)
                )
                
                if polar_type == "preset":
                    # プリセットポーラーの選択
                    polar_preset = st.selectbox(
                        "ポーラーデータ",
                        options=["470", "49er", "finn", "laser", "nacra17"],
                        format_func=lambda x: {
                            "470": "470級",
                            "49er": "49er級",
                            "finn": "Finn級",
                            "laser": "Laser級",
                            "nacra17": "Nacra 17"
                        }.get(x, x)
                    )
                    params["polar_preset"] = polar_preset
                
                else:  # custom
                    # カスタムターゲット速度の設定
                    st.write("風速別ターゲット速度（ノット）:")
                    target_speeds = {}
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        target_speeds["5"] = st.number_input("風速5ノット", min_value=0.0, max_value=20.0, value=3.5, format="%.1f")
                        target_speeds["10"] = st.number_input("風速10ノット", min_value=0.0, max_value=20.0, value=5.0, format="%.1f")
                        target_speeds["15"] = st.number_input("風速15ノット", min_value=0.0, max_value=20.0, value=6.0, format="%.1f")
                    
                    with col2:
                        target_speeds["20"] = st.number_input("風速20ノット", min_value=0.0, max_value=20.0, value=6.5, format="%.1f")
                        target_speeds["25"] = st.number_input("風速25ノット", min_value=0.0, max_value=20.0, value=7.0, format="%.1f")
                    
                    params["target_speeds"] = target_speeds
        
        # タッキング効率設定（タッキング効率の場合）
        if "tacking_efficiency" in metrics:
            with st.expander("タッキング効率設定"):
                tacking_threshold = st.slider(
                    "タッキング検出閾値（度）",
                    min_value=30,
                    max_value=120,
                    value=60
                )
                params["tacking_threshold"] = tacking_threshold
        
        return params
    
    def _render_statistical_calculation_params(self, data: Any, data_type: str) -> Dict[str, Any]:
        """
        統計値計算パラメータ設定UIを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
            
        Returns
        -------
        Dict[str, Any]
            統計値計算パラメータ
        """
        params = {}
        
        # 計算する統計指標
        metrics = st.multiselect(
            "計算する統計指標",
            options=["mean", "median", "std", "min", "max", "percentile", "trend", "moving"],
            format_func=lambda x: {
                "mean": "平均値",
                "median": "中央値",
                "std": "標準偏差",
                "min": "最小値",
                "max": "最大値",
                "percentile": "パーセンタイル",
                "trend": "トレンド",
                "moving": "移動統計値"
            }.get(x, x),
            default=["mean", "median", "std", "min", "max"]
        )
        params["metrics"] = metrics
        
        # パーセンタイル設定
        if "percentile" in metrics:
            percentiles_str = st.text_input("パーセンタイル値（カンマ区切り）", value="25, 50, 75")
            percentiles = [float(p.strip()) for p in percentiles_str.split(",") if p.strip()]
            params["percentiles"] = percentiles
        
        # 移動統計値設定
        if "moving" in metrics:
            window_size = st.slider("窓サイズ", min_value=3, max_value=100, value=10, step=1)
            params["window_size"] = window_size
        
        # トレンド設定
        if "trend" in metrics:
            trend_method = st.selectbox(
                "トレンド計算方法",
                options=["linear", "polynomial"],
                format_func=lambda x: {
                    "linear": "線形トレンド",
                    "polynomial": "多項式トレンド"
                }.get(x, x)
            )
            params["trend_method"] = trend_method
            
            if trend_method == "polynomial":
                trend_degree = st.slider("多項式次数", min_value=2, max_value=5, value=2)
                params["trend_degree"] = trend_degree
        
        # 対象カラムの選択（DataFrame、辞書リストの場合）
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            # 数値型カラムのフィルタリング
            if data_type == "dataframe":
                numeric_columns = data.select_dtypes(include=[np.number]).columns.tolist()
            else:  # dict_list
                numeric_columns = []
                if len(data) > 0:
                    for key, value in data[0].items():
                        if isinstance(value, (int, float)):
                            numeric_columns.append(key)
            
            # カラム選択
            selected_columns = st.multiselect(
                "対象カラム",
                options=columns,
                default=numeric_columns
            )
            
            if selected_columns:
                params["columns"] = selected_columns
        
        return params
    
    def _render_custom_calculation_params(self, data: Any, data_type: str) -> Dict[str, Any]:
        """
        カスタム計算式パラメータ設定UIを描画
        
        Parameters
        ----------
        data : Any
            処理対象データ
        data_type : str
            データ型
            
        Returns
        -------
        Dict[str, Any]
            カスタム計算式パラメータ
        """
        params = {}
        
        # 安全モード設定
        safe_mode = st.checkbox("安全モード（危険な関数の使用を制限）", value=True)
        params["safe_mode"] = safe_mode
        
        # DataFrame、辞書リストの場合
        if data_type in ["dataframe", "dict_list"]:
            # カラムの取得
            if data_type == "dataframe":
                columns = data.columns.tolist()
            else:  # dict_list
                columns = list(data[0].keys()) if len(data) > 0 else []
            
            st.write("利用可能なカラム:")
            st.write(", ".join(columns))
            
            # 計算式の設定
            st.write("計算式の設定:")
            st.info("カラム名をそのまま数式で利用できます。例: `speed * 0.5` や `sin(direction * 3.14 / 180)`")
            
            formulas = {}
            formula_count = st.number_input("計算式の数", min_value=1, max_value=10, value=1)
            
            for i in range(formula_count):
                st.subheader(f"計算式 {i+1}")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    result_column = st.text_input(f"結果カラム名", value=f"result_{i+1}", key=f"custom_result_col_{i}")
                
                with col2:
                    formula = st.text_input(f"計算式", value="", key=f"custom_formula_{i}")
                
                if result_column and formula:
                    formulas[result_column] = formula
            
            params["formulas"] = formulas
        
        # リストや辞書の場合
        else:
            st.write("カスタム計算式の設定:")
            
            formulas = {}
            formula_count = st.number_input("計算式の数", min_value=1, max_value=5, value=1)
            
            for i in range(formula_count):
                st.subheader(f"計算式 {i+1}")
                
                col1, col2 = st.columns([1, 3])
                with col1:
                    result_key = st.text_input(f"結果キー名", value=f"result_{i+1}", key=f"custom_result_key_{i}")
                
                with col2:
                    formula = st.text_input(f"計算式", value="", key=f"custom_formula_{i}")
                
                if result_key and formula:
                    formulas[result_key] = formula
            
            params["formulas"] = formulas
        
        return params
