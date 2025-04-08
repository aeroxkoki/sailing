"""
ui.components.validation.issue_highlight

問題箇所をハイライト表示するコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional, Tuple, Set

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator


class IssueHighlight:
    """
    問題箇所をハイライト表示するコンポーネント
    
    Parameters
    ----------
    container : GPSDataContainer
        GPSデータコンテナ
    metrics_calculator : QualityMetricsCalculator
        品質メトリクス計算クラス
    key_prefix : str, optional
        Streamlitのキープレフィックス, by default "issue_highlight"
    """
    
    def __init__(self, 
                container: GPSDataContainer, 
                metrics_calculator: QualityMetricsCalculator,
                key_prefix: str = "issue_highlight"):
        """
        初期化
        
        Parameters
        ----------
        container : GPSDataContainer
            GPSデータコンテナ
        metrics_calculator : QualityMetricsCalculator
            品質メトリクス計算クラス
        key_prefix : str, optional
            Streamlitのキープレフィックス, by default "issue_highlight"
        """
        self.container = container
        self.data = container.data
        self.metrics_calculator = metrics_calculator
        self.key_prefix = key_prefix
        
        # 問題インデックスを取得
        self.problem_indices = self.metrics_calculator.problematic_indices
        
        # 問題カテゴリとその日本語名
        self.problem_type_names = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複データ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        }
        
        # 問題タイプの色
        self.problem_type_colors = {
            "missing_data": "blue",
            "out_of_range": "red",
            "duplicates": "green",
            "spatial_anomalies": "purple",
            "temporal_anomalies": "orange"
        }
        
        # セッション状態の初期化
        if f"{self.key_prefix}_selected_problem_type" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_problem_type"] = "all"
        
        if f"{self.key_prefix}_selected_records" not in st.session_state:
            st.session_state[f"{self.key_prefix}_selected_records"] = []
    
    def render(self):
        """
        問題箇所のハイライト表示を行うコンポーネントをレンダリング
        """
        with st.container():
            self._render_filter_section()
            self._render_highlight_section()
    
    def _render_filter_section(self):
        """
        フィルタリングセクションをレンダリング
        """
        st.markdown("## 問題箇所ハイライト")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 問題タイプの選択（Streamlitのフィルターウィジェット）
            problem_types = ["all"] + list(self.problem_type_names.keys())
            problem_type_labels = ["すべての問題"] + [self.problem_type_names[pt] for pt in self.problem_type_names]
            
            # 問題タイプマッピング
            type_mapping = {label: key for key, label in zip(problem_types, problem_type_labels)}
            
            selected_type_label = st.selectbox(
                "表示する問題タイプ",
                options=problem_type_labels,
                index=0,
                key=f"{self.key_prefix}_problem_type_filter"
            )
            
            # 選択した問題タイプを保存
            selected_type = type_mapping.get(selected_type_label, "all")
            st.session_state[f"{self.key_prefix}_selected_problem_type"] = selected_type
        
        with col2:
            # 問題レコード数とページングコントロール
            problem_count = len(self.get_filtered_indices())
            
            st.metric(
                label="問題件数", 
                value=problem_count,
                delta=None,
                help="現在のフィルターに一致する問題の数"
            )
            
            # 問題がない場合は通知
            if problem_count == 0:
                st.info(f"選択された問題タイプ「{selected_type_label}」に該当する問題はありません。")
    
    def _render_highlight_section(self):
        """
        ハイライト表示セクションをレンダリング
        """
        # フィルタリングされた問題インデックスを取得
        filtered_indices = self.get_filtered_indices()
        
        if not filtered_indices:
            return
        
        # タブでビューを切り替え
        tabs = st.tabs(["データテーブル", "マップビュー", "グラフビュー", "トラックビュー"])
        
        with tabs[0]:
            self._render_table_highlight(filtered_indices)
        
        with tabs[1]:
            self._render_map_highlight(filtered_indices)
        
        with tabs[2]:
            self._render_graph_highlight(filtered_indices)
        
        with tabs[3]:
            self._render_track_highlight(filtered_indices)
    
    def _render_table_highlight(self, filtered_indices: List[int]):
        """
        テーブル内の問題をハイライト表示
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        """
        st.markdown("### データテーブルの問題ハイライト")
        
        # データの表示件数を選択
        display_options = {"すべて": -1, "問題のみ": 0, "最初の100件": 100, "最初の50件": 50, "最初の20件": 20}
        
        # セッション状態から表示オプションを取得
        if f"{self.key_prefix}_display_option" not in st.session_state:
            st.session_state[f"{self.key_prefix}_display_option"] = "最初の20件"
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            display_option = st.selectbox(
                "表示オプション",
                options=list(display_options.keys()),
                index=list(display_options.keys()).index(st.session_state[f"{self.key_prefix}_display_option"]),
                key=f"{self.key_prefix}_display_option_selector"
            )
            
            # 表示オプションを保存
            st.session_state[f"{self.key_prefix}_display_option"] = display_option
        
        with col2:
            # 列表示オプション
            if f"{self.key_prefix}_show_all_columns" not in st.session_state:
                st.session_state[f"{self.key_prefix}_show_all_columns"] = False
            
            show_all_columns = st.checkbox(
                "すべての列を表示",
                value=st.session_state[f"{self.key_prefix}_show_all_columns"],
                key=f"{self.key_prefix}_show_all_columns_checkbox"
            )
            
            st.session_state[f"{self.key_prefix}_show_all_columns"] = show_all_columns
        
        # 表示するデータの準備
        display_df = self.data.copy()
        
        # 問題タイプカラムを追加
        problem_type_col = np.full(len(display_df), "", dtype=object)
        
        for idx in filtered_indices:
            if idx < len(display_df):
                problem_types = []
                
                for problem_type, indices in self.problem_indices.items():
                    if problem_type != "all" and idx in indices:
                        problem_types.append(self.problem_type_names.get(problem_type, problem_type))
                
                problem_type_col[idx] = ", ".join(problem_types)
        
        display_df["問題タイプ"] = problem_type_col
        
        # 表示オプションに基づいてデータをフィルタリング
        if display_options[display_option] == 0:  # 問題のみを表示
            display_df = display_df.loc[filtered_indices]
        elif display_options[display_option] > 0:  # 先頭N件を表示
            display_df = display_df.head(display_options[display_option])
        
        # 列の選択
        if not show_all_columns:
            # 基本カラム + 問題タイプ
            basic_columns = ["timestamp", "latitude", "longitude"]
            available_columns = [col for col in basic_columns if col in display_df.columns]
            display_df = display_df[available_columns + ["問題タイプ"]]
        
        # スタイル付きのテーブルを表示
        st.dataframe(
            self._style_dataframe(display_df, filtered_indices),
            use_container_width=True
        )
        
        # ページングコントロール
        if f"{self.key_prefix}_current_page" not in st.session_state:
            st.session_state[f"{self.key_prefix}_current_page"] = 0
        
        # 詳細表示
        st.markdown("### 選択した問題の詳細")
        
        if filtered_indices:
            # ページングがない場合は直接選択
            selected_index = st.selectbox(
                "詳細を表示する問題を選択",
                options=filtered_indices,
                format_func=lambda idx: f"問題 #{idx}: {self._get_problem_description(idx)}",
                key=f"{self.key_prefix}_selected_problem"
            )
            
            if selected_index is not None:
                self._display_problem_details(selected_index)
        else:
            st.info("表示する問題がありません。")
    
    def _render_map_highlight(self, filtered_indices: List[int]):
        """
        マップ上の問題をハイライト表示
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        """
        st.markdown("### マップ上の問題ハイライト")
        
        # 位置情報カラムがない場合はスキップ
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            st.info("位置情報カラム（latitude, longitude）がデータ内に存在しないため、マップを表示できません。")
            return
        
        # マップの表示
        with st.container():
            # マップのタイプ選択
            map_types = ["散布図", "ヒートマップ", "詳細マップ"]
            
            if f"{self.key_prefix}_map_type" not in st.session_state:
                st.session_state[f"{self.key_prefix}_map_type"] = "散布図"
            
            selected_map = st.radio(
                "マップタイプ",
                options=map_types,
                index=map_types.index(st.session_state[f"{self.key_prefix}_map_type"]),
                horizontal=True,
                key=f"{self.key_prefix}_map_type_selector"
            )
            
            st.session_state[f"{self.key_prefix}_map_type"] = selected_map
            
            # 選択したマップタイプに基づいてマップを表示
            if selected_map == "散布図":
                fig = self._create_scatter_map(filtered_indices)
            elif selected_map == "ヒートマップ":
                fig = self._create_heatmap(filtered_indices)
            else:  # 詳細マップ
                fig = self._create_detailed_map(filtered_indices)
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_graph_highlight(self, filtered_indices: List[int]):
        """
        グラフ上の問題をハイライト表示
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        """
        st.markdown("### グラフ上の問題ハイライト")
        
        # 時系列データと位置データがある場合のみ表示
        if "timestamp" not in self.data.columns:
            st.info("タイムスタンプカラム（timestamp）がデータ内に存在しないため、グラフを表示できません。")
            return
        
        # グラフタイプの選択
        graph_types = ["時系列プロット", "速度プロファイル", "カラム別プロット"]
        
        if f"{self.key_prefix}_graph_type" not in st.session_state:
            st.session_state[f"{self.key_prefix}_graph_type"] = "時系列プロット"
        
        selected_graph = st.radio(
            "グラフタイプ",
            options=graph_types,
            index=graph_types.index(st.session_state[f"{self.key_prefix}_graph_type"]),
            horizontal=True,
            key=f"{self.key_prefix}_graph_type_selector"
        )
        
        st.session_state[f"{self.key_prefix}_graph_type"] = selected_graph
        
        # カラム別プロットの場合はカラムを選択
        if selected_graph == "カラム別プロット":
            numeric_cols = self.data.select_dtypes(include=np.number).columns.tolist()
            
            if not numeric_cols:
                st.info("数値型のカラムがないため、プロットを作成できません。")
                return
            
            if f"{self.key_prefix}_plot_column" not in st.session_state:
                st.session_state[f"{self.key_prefix}_plot_column"] = numeric_cols[0] if numeric_cols else None
            
            selected_column = st.selectbox(
                "表示するカラム",
                options=numeric_cols,
                index=numeric_cols.index(st.session_state[f"{self.key_prefix}_plot_column"]) if st.session_state[f"{self.key_prefix}_plot_column"] in numeric_cols else 0,
                key=f"{self.key_prefix}_column_selector"
            )
            
            st.session_state[f"{self.key_prefix}_plot_column"] = selected_column
            
            # 選択したカラムのプロットを表示
            fig = self._create_column_plot(selected_column, filtered_indices)
            st.plotly_chart(fig, use_container_width=True)
        
        elif selected_graph == "時系列プロット":
            # 時系列プロットを表示
            fig = self._create_timeline_plot(filtered_indices)
            st.plotly_chart(fig, use_container_width=True)
        
        elif selected_graph == "速度プロファイル":
            # 速度プロファイルを表示
            fig = self._create_speed_profile(filtered_indices)
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_track_highlight(self, filtered_indices: List[int]):
        """
        トラック表示での問題をハイライト表示
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        """
        st.markdown("### トラック上の問題ハイライト")
        
        # 位置情報とタイムスタンプがある場合のみ表示
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns or "timestamp" not in self.data.columns:
            st.info("位置情報カラム（latitude, longitude）またはタイムスタンプカラム（timestamp）がデータ内に存在しないため、トラックを表示できません。")
            return
        
        # トラックの表示
        with st.container():
            # 表示タイプの選択
            track_types = ["3Dトラック", "2Dトラック", "セグメント分析"]
            
            if f"{self.key_prefix}_track_type" not in st.session_state:
                st.session_state[f"{self.key_prefix}_track_type"] = "2Dトラック"
            
            selected_track = st.radio(
                "トラックタイプ",
                options=track_types,
                index=track_types.index(st.session_state[f"{self.key_prefix}_track_type"]),
                horizontal=True,
                key=f"{self.key_prefix}_track_type_selector"
            )
            
            st.session_state[f"{self.key_prefix}_track_type"] = selected_track
            
            # 選択したトラックタイプに基づいて表示
            if selected_track == "3Dトラック":
                fig = self._create_3d_track(filtered_indices)
            elif selected_track == "2Dトラック":
                fig = self._create_2d_track(filtered_indices)
            else:  # セグメント分析
                fig = self._create_segment_analysis(filtered_indices)
            
            st.plotly_chart(fig, use_container_width=True)
    
    def get_filtered_indices(self) -> List[int]:
        """
        現在のフィルターに基づく問題インデックスを取得
        
        Returns
        -------
        List[int]
            フィルタリングされた問題インデックス
        """
        selected_type = st.session_state.get(f"{self.key_prefix}_selected_problem_type", "all")
        
        if selected_type == "all":
            return self.problem_indices["all"]
        else:
            return self.problem_indices.get(selected_type, [])
    
    def _style_dataframe(self, df: pd.DataFrame, highlight_indices: List[int]) -> pd.DataFrame:
        """
        問題のあるセルをハイライト表示するスタイルを適用
        
        Parameters
        ----------
        df : pd.DataFrame
            データフレーム
        highlight_indices : List[int]
            ハイライト表示するインデックス
        
        Returns
        -------
        pd.DataFrame
            スタイル適用後のデータフレーム
        """
        # 問題タイプごとのスタイル
        def apply_styles(row):
            if row.name in highlight_indices:
                # 行全体に背景色を適用
                return ['background-color: rgba(255, 200, 200, 0.5)'] * len(row)
            return [''] * len(row)
        
        # スタイルを適用
        return df.style.apply(apply_styles, axis=1)
    
    def _get_problem_description(self, index: int) -> str:
        """
        問題の説明を取得
        
        Parameters
        ----------
        index : int
            問題インデックス
        
        Returns
        -------
        str
            問題の説明
        """
        problem_types = []
        
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all" and index in indices:
                problem_types.append(self.problem_type_names.get(problem_type, problem_type))
        
        if problem_types:
            return f"{', '.join(problem_types)} (インデックス: {index})"
        else:
            return f"インデックス: {index}"
    
    def _display_problem_details(self, index: int):
        """
        選択された問題の詳細を表示
        
        Parameters
        ----------
        index : int
            問題インデックス
        """
        # インデックスが範囲内か確認
        if index >= len(self.data):
            st.error(f"インデックス {index} はデータの範囲外です。")
            return
        
        # 選択された行を取得
        row = self.data.iloc[index]
        
        # 問題タイプを収集
        problem_types = []
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all" and index in indices:
                problem_types.append(self.problem_type_names.get(problem_type, problem_type))
        
        # 問題タイプを人間が読みやすい形式で表示
        problem_str = ", ".join(problem_types) if problem_types else "なし"
        
        # 詳細情報のテーブル
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**問題タイプ:** {problem_str}")
            
            # タイムスタンプ
            if "timestamp" in row:
                st.markdown(f"**タイムスタンプ:** {row['timestamp']}")
            
            # 位置情報
            if "latitude" in row and "longitude" in row:
                st.markdown(f"**位置情報:** ({row['latitude']:.6f}, {row['longitude']:.6f})")
            
            # 速度情報
            if "speed" in row:
                st.markdown(f"**速度:** {row['speed']:.2f}")
        
        with col2:
            # 前後のレコードとの比較
            if index > 0 and index < len(self.data) - 1:
                prev_row = self.data.iloc[index - 1]
                next_row = self.data.iloc[index + 1]
                
                # タイムスタンプの差
                if "timestamp" in row and "timestamp" in prev_row and "timestamp" in next_row:
                    time_diff_prev = (row["timestamp"] - prev_row["timestamp"]).total_seconds()
                    time_diff_next = (next_row["timestamp"] - row["timestamp"]).total_seconds()
                    
                    st.markdown(f"**前のレコードとの時間差:** {time_diff_prev:.2f}秒")
                    st.markdown(f"**次のレコードとの時間差:** {time_diff_next:.2f}秒")
        
        # 全カラムの値を表示
        st.markdown("### レコードの全データ")
        
        # 行データを辞書に変換
        row_dict = row.to_dict()
        
        # きれいに整形して表示
        record_data = []
        for key, value in row_dict.items():
            record_data.append({"カラム": key, "値": value})
        
        record_df = pd.DataFrame(record_data)
        st.dataframe(record_df, use_container_width=True, hide_index=True)
        
        # 問題の詳細情報
        st.markdown("### 問題の詳細")
        
        # 検証結果から該当するレコードの詳細情報を抽出
        problem_details = self._get_validation_details(index)
        
        if problem_details:
            for problem_type, details in problem_details.items():
                with st.expander(f"{self.problem_type_names.get(problem_type, problem_type)} の詳細", expanded=True):
                    # 問題の詳細をわかりやすく表示
                    self._display_problem_type_details(problem_type, details, index)
        else:
            st.info("詳細な問題情報はありません。")
    
    def _get_validation_details(self, index: int) -> Dict[str, Any]:
        """
        インデックスに関連する検証の詳細を取得
        
        Parameters
        ----------
        index : int
            検査するインデックス
        
        Returns
        -------
        Dict[str, Any]
            問題タイプごとの詳細情報
        """
        # 問題タイプごとの詳細情報を収集
        details = {}
        
        # 検証結果から該当する問題を抽出
        for result in self.metrics_calculator.validation_results:
            if not result["is_valid"]:
                result_details = result["details"]
                problem_type = None
                
                # 問題タイプを判定
                if "No Null Values Check" in result["rule_name"]:
                    problem_type = "missing_data"
                elif "Value Range Check" in result["rule_name"]:
                    problem_type = "out_of_range"
                elif "No Duplicate Timestamps" in result["rule_name"]:
                    problem_type = "duplicates"
                elif "Spatial Consistency Check" in result["rule_name"]:
                    problem_type = "spatial_anomalies"
                elif "Temporal Consistency Check" in result["rule_name"]:
                    problem_type = "temporal_anomalies"
                
                if problem_type:
                    # 該当インデックスがこの問題に含まれているか確認
                    found = False
                    
                    if "null_indices" in result_details:
                        for col, indices in result_details["null_indices"].items():
                            if index in indices:
                                found = True
                                break
                    
                    if "out_of_range_indices" in result_details and index in result_details["out_of_range_indices"]:
                        found = True
                    
                    if "duplicate_indices" in result_details:
                        for ts, indices in result_details["duplicate_indices"].items():
                            if index in indices:
                                found = True
                                break
                    
                    if "anomaly_indices" in result_details and index in result_details["anomaly_indices"]:
                        found = True
                    
                    if "gap_indices" in result_details and index in result_details["gap_indices"]:
                        found = True
                    
                    if "reverse_indices" in result_details and index in result_details["reverse_indices"]:
                        found = True
                    
                    if found:
                        if problem_type not in details:
                            details[problem_type] = []
                        
                        details[problem_type].append({
                            "rule": result["rule_name"],
                            "severity": result["severity"],
                            "details": result_details
                        })
        
        return details
    
    def _display_problem_type_details(self, problem_type: str, details_list: List[Dict[str, Any]], index: int):
        """
        問題タイプごとの詳細を表示
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        details_list : List[Dict[str, Any]]
            詳細情報のリスト
        index : int
            問題のインデックス
        """
        for details_item in details_list:
            rule = details_item["rule"]
            severity = details_item["severity"]
            details = details_item["details"]
            
            st.markdown(f"**ルール:** {rule}")
            st.markdown(f"**重要度:** {severity}")
            
            # 問題タイプに応じた詳細表示
            if problem_type == "missing_data":
                # 欠損値の詳細
                if "null_counts" in details:
                    null_columns = []
                    for col, count in details["null_counts"].items():
                        if count > 0:
                            null_columns.append(col)
                    
                    st.markdown(f"**欠損しているカラム:** {', '.join(null_columns)}")
            
            elif problem_type == "out_of_range":
                # 範囲外の値の詳細
                if "column" in details:
                    col = details["column"]
                    min_val = details.get("min_value", "制限なし")
                    max_val = details.get("max_value", "制限なし")
                    actual_val = self.data.iloc[index][col] if col in self.data.columns else "不明"
                    
                    st.markdown(f"**カラム:** {col}")
                    st.markdown(f"**許容範囲:** {min_val} 〜 {max_val}")
                    st.markdown(f"**実際の値:** {actual_val}")
            
            elif problem_type == "duplicates":
                # 重複の詳細
                if "duplicate_timestamps" in details:
                    dupl_ts = details["duplicate_timestamps"]
                    if dupl_ts:
                        ts_str = self.data.iloc[index]["timestamp"] if "timestamp" in self.data.columns else "不明"
                        st.markdown(f"**重複しているタイムスタンプ:** {ts_str}")
                        
                        # 重複インデックスのリスト
                        if "duplicate_indices" in details:
                            for ts, indices in details["duplicate_indices"].items():
                                if index in indices:
                                    other_indices = [idx for idx in indices if idx != index]
                                    if other_indices:
                                        st.markdown(f"**重複しているレコード:** {', '.join(map(str, other_indices))}")
                                    break
            
            elif problem_type == "spatial_anomalies":
                # 空間的異常の詳細
                if "anomaly_details" in details:
                    for anomaly in details["anomaly_details"]:
                        if anomaly.get("original_index") == index:
                            st.markdown(f"**異常な移動距離:** {anomaly.get('distance_meters', 0):.2f}メートル")
                            st.markdown(f"**経過時間:** {anomaly.get('time_diff_seconds', 0):.2f}秒")
                            st.markdown(f"**計算された速度:** {anomaly.get('speed_knots', 0):.2f}ノット")
                            st.markdown(f"**最大許容速度:** {details.get('max_calculated_speed', 0):.2f}ノット")
                            break
            
            elif problem_type == "temporal_anomalies":
                # 時間的異常の詳細
                if "gap_details" in details:
                    for gap in details["gap_details"]:
                        if gap.get("original_index") == index:
                            prev_ts = gap.get("prev_timestamp", "不明")
                            curr_ts = gap.get("curr_timestamp", "不明")
                            gap_sec = gap.get("gap_seconds", 0)
                            
                            st.markdown(f"**時間ギャップ:** {gap_sec:.2f}秒")
                            st.markdown(f"**前のタイムスタンプ:** {prev_ts}")
                            st.markdown(f"**現在のタイムスタンプ:** {curr_ts}")
                            break
                
                if "reverse_details" in details:
                    for reverse in details["reverse_details"]:
                        if reverse.get("original_index") == index:
                            prev_ts = reverse.get("prev_timestamp", "不明")
                            curr_ts = reverse.get("curr_timestamp", "不明")
                            diff_sec = reverse.get("diff_seconds", 0)
                            
                            st.markdown(f"**時間逆行:** {abs(diff_sec):.2f}秒")
                            st.markdown(f"**前のタイムスタンプ:** {prev_ts}")
                            st.markdown(f"**現在のタイムスタンプ:** {curr_ts}")
                            break

    def _create_scatter_map(self, filtered_indices: List[int]) -> go.Figure:
        """
        問題を強調表示する散布図マップを作成
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        
        Returns
        -------
        go.Figure
            散布図マップ
        """
        # 位置情報がない場合は空のグラフを返す
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            fig = go.Figure()
            fig.update_layout(
                title="マップ表示 (位置情報なし)",
                height=400
            )
            return fig
        
        # タイムスタンプでソートされたデータを取得
        if "timestamp" in self.data.columns:
            sorted_data = self.data.sort_values("timestamp")
        else:
            sorted_data = self.data.copy()
        
        # 通常のトラックの線
        fig = go.Figure()
        
        # トラック全体のラインを追加
        fig.add_trace(go.Scattermapbox(
            lat=sorted_data["latitude"],
            lon=sorted_data["longitude"],
            mode="lines",
            line=dict(width=2, color="blue"),
            name="トラック",
            hoverinfo="none"
        ))
        
        # 問題ポイントを追加
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                # 現在のフィルタに含まれるインデックスのみ表示
                filtered_problem_indices = [idx for idx in indices if idx in filtered_indices]
                
                if filtered_problem_indices:
                    problem_df = self.data.iloc[filtered_problem_indices]
                    
                    fig.add_trace(go.Scattermapbox(
                        lat=problem_df["latitude"],
                        lon=problem_df["longitude"],
                        mode="markers",
                        marker=dict(
                            size=12,
                            color=self.problem_type_colors.get(problem_type, "red"),
                            symbol="circle"
                        ),
                        name=self.problem_type_names.get(problem_type, problem_type),
                        hovertemplate="インデックス: %{customdata}<br>緯度: %{lat:.6f}<br>経度: %{lon:.6f}<extra></extra>",
                        customdata=filtered_problem_indices
                    ))
        
        # マップの中心を設定
        center_lat = sorted_data["latitude"].mean()
        center_lon = sorted_data["longitude"].mean()
        
        # マップのレイアウト設定
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=12
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            height=500,
            title="問題ハイライト付きトラックマップ",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def _create_heatmap(self, filtered_indices: List[int]) -> go.Figure:
        """
        問題の密度を示すヒートマップを作成
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        
        Returns
        -------
        go.Figure
            ヒートマップ
        """
        # 位置情報がない場合は空のグラフを返す
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            fig = go.Figure()
            fig.update_layout(
                title="ヒートマップ表示 (位置情報なし)",
                height=400
            )
            return fig
        
        # 問題レコードを抽出
        problem_df = self.data.iloc[filtered_indices]
        
        # データがない場合は空のグラフを返す
        if problem_df.empty:
            fig = go.Figure()
            fig.update_layout(
                title="ヒートマップ表示 (問題レコードなし)",
                height=400
            )
            return fig
        
        # ヒートマップ用のデータフレームを作成
        fig = px.density_mapbox(
            problem_df,
            lat="latitude",
            lon="longitude",
            z=np.ones(len(problem_df)),  # 全ての点に同じ重みを与える
            radius=10,
            center=dict(lat=problem_df["latitude"].mean(), lon=problem_df["longitude"].mean()),
            zoom=11,
            mapbox_style="open-street-map",
            title="問題密度ヒートマップ"
        )
        
        # レイアウト調整
        fig.update_layout(
            margin=dict(l=0, r=0, t=30, b=0),
            height=500
        )
        
        return fig
    
    def _create_detailed_map(self, filtered_indices: List[int]) -> go.Figure:
        """
        詳細な問題情報付きのマップを作成
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        
        Returns
        -------
        go.Figure
            詳細マップ
        """
        # 位置情報がない場合は空のグラフを返す
        if "latitude" not in self.data.columns or "longitude" not in self.data.columns:
            fig = go.Figure()
            fig.update_layout(
                title="詳細マップ表示 (位置情報なし)",
                height=400
            )
            return fig
        
        # タイムスタンプでソートされたデータを取得
        if "timestamp" in self.data.columns:
            sorted_data = self.data.sort_values("timestamp")
        else:
            sorted_data = self.data.copy()
        
        # 図を初期化
        fig = go.Figure()
        
        # トラック全体のラインを追加（不透明度を下げて背景に）
        fig.add_trace(go.Scattermapbox(
            lat=sorted_data["latitude"],
            lon=sorted_data["longitude"],
            mode="lines",
            line=dict(width=2, color="blue", opacity=0.5),
            name="トラック",
            hoverinfo="none"
        ))
        
        # 問題ポイントを種類ごとにグループ化して追加
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                # 現在のフィルタに含まれるインデックスのみ表示
                filtered_problem_indices = [idx for idx in indices if idx in filtered_indices]
                
                if filtered_problem_indices:
                    problem_df = self.data.iloc[filtered_problem_indices]
                    
                    # 問題の詳細情報を作成
                    hover_texts = []
                    for idx in filtered_problem_indices:
                        row = self.data.iloc[idx]
                        
                        text = f"インデックス: {idx}<br>"
                        text += f"問題タイプ: {self.problem_type_names.get(problem_type, problem_type)}<br>"
                        
                        if "timestamp" in row:
                            text += f"タイムスタンプ: {row['timestamp']}<br>"
                        
                        if "speed" in row:
                            text += f"速度: {row['speed']:.2f}<br>"
                        
                        if "direction" in row:
                            text += f"方向: {row['direction']:.2f}<br>"
                        
                        hover_texts.append(text)
                    
                    # マーカーのスタイル設定
                    marker_style = {
                        "missing_data": dict(size=10, symbol="circle"),
                        "out_of_range": dict(size=10, symbol="triangle-up"),
                        "duplicates": dict(size=10, symbol="square"),
                        "spatial_anomalies": dict(size=10, symbol="diamond"),
                        "temporal_anomalies": dict(size=10, symbol="star")
                    }
                    
                    # マーカーのスタイル
                    marker = marker_style.get(problem_type, dict(size=10, symbol="circle"))
                    marker["color"] = self.problem_type_colors.get(problem_type, "red")
                    
                    # ポイント追加
                    fig.add_trace(go.Scattermapbox(
                        lat=problem_df["latitude"],
                        lon=problem_df["longitude"],
                        mode="markers",
                        marker=marker,
                        name=self.problem_type_names.get(problem_type, problem_type),
                        hoverinfo="text",
                        hovertext=hover_texts,
                        customdata=filtered_problem_indices
                    ))
        
        # マップの中心を設定
        center_lat = sorted_data["latitude"].mean()
        center_lon = sorted_data["longitude"].mean()
        
        # マップのレイアウト設定
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=center_lat, lon=center_lon),
                zoom=12
            ),
            margin=dict(l=0, r=0, t=30, b=0),
            height=500,
            title="詳細ハイライト付きトラックマップ",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def _create_timeline_plot(self, filtered_indices: List[int]) -> go.Figure:
        """
        時系列プロットを作成
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        
        Returns
        -------
        go.Figure
            時系列プロット
        """
        # タイムスタンプがない場合は空のグラフを返す
        if "timestamp" not in self.data.columns:
            fig = go.Figure()
            fig.update_layout(
                title="時系列プロット (タイムスタンプなし)",
                height=400
            )
            return fig
        
        # タイムスタンプでソートされたデータを取得
        sorted_data = self.data.sort_values("timestamp").copy()
        
        # プロット用の値を選択（速度があれば速度、なければ緯度）
        plot_col = "speed" if "speed" in sorted_data.columns else "latitude"
        y_title = "速度" if plot_col == "speed" else "緯度"
        
        # グラフを初期化
        fig = go.Figure()
        
        # 全データのラインを追加
        fig.add_trace(go.Scatter(
            x=sorted_data["timestamp"],
            y=sorted_data[plot_col],
            mode="lines",
            name=y_title,
            line=dict(color="blue", width=2)
        ))
        
        # 問題ポイントを種類ごとにグループ化して追加
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                # 現在のフィルタに含まれるインデックスのみ表示
                filtered_problem_indices = [idx for idx in indices if idx in filtered_indices]
                
                if filtered_problem_indices:
                    problem_df = self.data.iloc[filtered_problem_indices]
                    
                    # 問題の詳細情報を作成
                    hover_texts = []
                    for idx in filtered_problem_indices:
                        row = self.data.iloc[idx]
                        
                        text = f"インデックス: {idx}<br>"
                        text += f"問題タイプ: {self.problem_type_names.get(problem_type, problem_type)}<br>"
                        text += f"{y_title}: {row[plot_col]}<br>"
                        
                        if "timestamp" in row:
                            text += f"タイムスタンプ: {row['timestamp']}<br>"
                        
                        hover_texts.append(text)
                    
                    # マーカーを追加
                    fig.add_trace(go.Scatter(
                        x=problem_df["timestamp"],
                        y=problem_df[plot_col],
                        mode="markers",
                        name=self.problem_type_names.get(problem_type, problem_type),
                        marker=dict(
                            size=10,
                            color=self.problem_type_colors.get(problem_type, "red"),
                            symbol="circle"
                        ),
                        hoverinfo="text",
                        hovertext=hover_texts,
                        customdata=filtered_problem_indices
                    ))
        
        # レイアウト設定
        fig.update_layout(
            title=f"時系列{y_title}プロット",
            xaxis_title="時間",
            yaxis_title=y_title,
            height=400,
            margin=dict(l=30, r=30, t=50, b=30),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def _create_column_plot(self, column: str, filtered_indices: List[int]) -> go.Figure:
        """
        選択したカラムのプロットを作成
        
        Parameters
        ----------
        column : str
            プロットするカラム名
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        
        Returns
        -------
        go.Figure
            カラムプロット
        """
        # カラムがない場合は空のグラフを返す
        if column not in self.data.columns:
            fig = go.Figure()
            fig.update_layout(
                title=f"カラムプロット ({column} なし)",
                height=400
            )
            return fig
        
        # タイムスタンプでソートされたデータを取得
        if "timestamp" in self.data.columns:
            sorted_data = self.data.sort_values("timestamp").copy()
            x_values = sorted_data["timestamp"]
            x_title = "時間"
        else:
            sorted_data = self.data.copy()
            x_values = np.arange(len(sorted_data))
            x_title = "インデックス"
        
        # グラフを初期化
        fig = go.Figure()
        
        # 全データのラインを追加
        fig.add_trace(go.Scatter(
            x=x_values,
            y=sorted_data[column],
            mode="lines",
            name=column,
            line=dict(color="blue", width=2)
        ))
        
        # 問題ポイントを種類ごとにグループ化して追加
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                # 現在のフィルタに含まれるインデックスのみ表示
                filtered_problem_indices = [idx for idx in indices if idx in filtered_indices]
                
                if filtered_problem_indices:
                    problem_df = self.data.iloc[filtered_problem_indices]
                    
                    # X軸の値を取得
                    if "timestamp" in self.data.columns:
                        problem_x = problem_df["timestamp"]
                    else:
                        problem_x = filtered_problem_indices
                    
                    # 問題の詳細情報を作成
                    hover_texts = []
                    for idx in filtered_problem_indices:
                        row = self.data.iloc[idx]
                        
                        text = f"インデックス: {idx}<br>"
                        text += f"問題タイプ: {self.problem_type_names.get(problem_type, problem_type)}<br>"
                        text += f"{column}: {row[column]}<br>"
                        
                        if "timestamp" in row:
                            text += f"タイムスタンプ: {row['timestamp']}<br>"
                        
                        hover_texts.append(text)
                    
                    # マーカーを追加
                    fig.add_trace(go.Scatter(
                        x=problem_x,
                        y=problem_df[column],
                        mode="markers",
                        name=self.problem_type_names.get(problem_type, problem_type),
                        marker=dict(
                            size=10,
                            color=self.problem_type_colors.get(problem_type, "red"),
                            symbol="circle"
                        ),
                        hoverinfo="text",
                        hovertext=hover_texts,
                        customdata=filtered_problem_indices
                    ))
        
        # レイアウト設定
        fig.update_layout(
            title=f"{column} プロット",
            xaxis_title=x_title,
            yaxis_title=column,
            height=400,
            margin=dict(l=30, r=30, t=50, b=30),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def _create_speed_profile(self, filtered_indices: List[int]) -> go.Figure:
        """
        速度プロファイルのグラフを作成
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        
        Returns
        -------
        go.Figure
            速度プロファイルグラフ
        """
        # 速度とタイムスタンプがない場合は空のグラフを返す
        if "speed" not in self.data.columns or "timestamp" not in self.data.columns:
            fig = go.Figure()
            fig.update_layout(
                title="速度プロファイル (速度またはタイムスタンプなし)",
                height=400
            )
            return fig
        
        # タイムスタンプでソートされたデータを取得
        sorted_data = self.data.sort_values("timestamp").copy()
        
        # グラフを初期化
        fig = go.Figure()
        
        # 速度プロファイルの線を追加
        fig.add_trace(go.Scatter(
            x=sorted_data["timestamp"],
            y=sorted_data["speed"],
            mode="lines",
            name="速度",
            line=dict(color="blue", width=2)
        ))
        
        # 問題ポイントを種類ごとにグループ化して追加
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                # 現在のフィルタに含まれるインデックスのみ表示
                filtered_problem_indices = [idx for idx in indices if idx in filtered_indices]
                
                if filtered_problem_indices:
                    problem_df = self.data.iloc[filtered_problem_indices]
                    
                    # 問題の詳細情報を作成
                    hover_texts = []
                    for idx in filtered_problem_indices:
                        row = self.data.iloc[idx]
                        
                        text = f"インデックス: {idx}<br>"
                        text += f"問題タイプ: {self.problem_type_names.get(problem_type, problem_type)}<br>"
                        text += f"速度: {row['speed']:.2f}<br>"
                        
                        if "timestamp" in row:
                            text += f"タイムスタンプ: {row['timestamp']}<br>"
                        
                        if "direction" in row:
                            text += f"方向: {row['direction']:.2f}<br>"
                        
                        hover_texts.append(text)
                    
                    # マーカーを追加
                    fig.add_trace(go.Scatter(
                        x=problem_df["timestamp"],
                        y=problem_df["speed"],
                        mode="markers",
                        name=self.problem_type_names.get(problem_type, problem_type),
                        marker=dict(
                            size=10,
                            color=self.problem_type_colors.get(problem_type, "red"),
                            symbol="circle"
                        ),
                        hoverinfo="text",
                        hovertext=hover_texts,
                        customdata=filtered_problem_indices
                    ))
        
        # 平均速度の水平線を追加
        mean_speed = sorted_data["speed"].mean()
        fig.add_hline(
            y=mean_speed,
            line=dict(color="green", dash="dash"),
            annotation_text=f"平均速度: {mean_speed:.2f}",
            annotation_position="bottom right"
        )
        
        # 速度の標準偏差のバンドを追加
        std_speed = sorted_data["speed"].std()
        fig.add_hline(
            y=mean_speed + std_speed,
            line=dict(color="orange", dash="dot"),
            annotation_text=f"+1σ: {(mean_speed + std_speed):.2f}",
            annotation_position="bottom right"
        )
        
        fig.add_hline(
            y=max(0, mean_speed - std_speed),
            line=dict(color="orange", dash="dot"),
            annotation_text=f"-1σ: {max(0, mean_speed - std_speed):.2f}",
            annotation_position="top right"
        )
        
        # レイアウト設定
        fig.update_layout(
            title="速度プロファイル",
            xaxis_title="時間",
            yaxis_title="速度",
            height=400,
            margin=dict(l=30, r=30, t=50, b=30),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def _create_3d_track(self, filtered_indices: List[int]) -> go.Figure:
        """
        3Dトラックを作成
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        
        Returns
        -------
        go.Figure
            3Dトラック
        """
        # 必要なカラムがない場合は空のグラフを返す
        required_cols = ["latitude", "longitude", "timestamp"]
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        
        if missing_cols:
            fig = go.Figure()
            fig.update_layout(
                title=f"3Dトラック ({', '.join(missing_cols)} なし)",
                height=500
            )
            return fig
        
        # タイムスタンプでソートされたデータを取得
        sorted_data = self.data.sort_values("timestamp").copy()
        
        # Z軸の値として速度かタイムスタンプの通し番号を使用
        if "speed" in sorted_data.columns:
            z_values = sorted_data["speed"]
            z_title = "速度"
        else:
            # タイムスタンプを数値のシーケンスに変換
            timestamp_seconds = (sorted_data["timestamp"] - sorted_data["timestamp"].min()).dt.total_seconds()
            z_values = timestamp_seconds
            z_title = "経過時間 (秒)"
        
        # グラフを初期化
        fig = go.Figure()
        
        # 3Dトラックのラインを追加
        fig.add_trace(go.Scatter3d(
            x=sorted_data["longitude"],
            y=sorted_data["latitude"],
            z=z_values,
            mode="lines",
            line=dict(color="blue", width=4),
            name="トラック"
        ))
        
        # 問題ポイントを種類ごとにグループ化して追加
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                # 現在のフィルタに含まれるインデックスのみ表示
                filtered_problem_indices = [idx for idx in indices if idx in filtered_indices]
                
                if filtered_problem_indices:
                    problem_df = self.data.iloc[filtered_problem_indices]
                    
                    # Z軸の値を取得
                    if "speed" in problem_df.columns:
                        problem_z = problem_df["speed"]
                    else:
                        # タイムスタンプを数値のシーケンスに変換
                        problem_timestamp_seconds = (problem_df["timestamp"] - sorted_data["timestamp"].min()).dt.total_seconds()
                        problem_z = problem_timestamp_seconds
                    
                    # 問題の詳細情報を作成
                    hover_texts = []
                    for idx in filtered_problem_indices:
                        row = self.data.iloc[idx]
                        
                        text = f"インデックス: {idx}<br>"
                        text += f"問題タイプ: {self.problem_type_names.get(problem_type, problem_type)}<br>"
                        
                        if "timestamp" in row:
                            text += f"タイムスタンプ: {row['timestamp']}<br>"
                        
                        if "speed" in row:
                            text += f"速度: {row['speed']:.2f}<br>"
                        
                        if "direction" in row:
                            text += f"方向: {row['direction']:.2f}<br>"
                        
                        hover_texts.append(text)
                    
                    # マーカーを追加
                    fig.add_trace(go.Scatter3d(
                        x=problem_df["longitude"],
                        y=problem_df["latitude"],
                        z=problem_z,
                        mode="markers",
                        marker=dict(
                            size=6,
                            color=self.problem_type_colors.get(problem_type, "red"),
                            symbol="circle"
                        ),
                        name=self.problem_type_names.get(problem_type, problem_type),
                        hoverinfo="text",
                        hovertext=hover_texts,
                        customdata=filtered_problem_indices
                    ))
        
        # レイアウト設定
        fig.update_layout(
            title="3Dトラック",
            scene=dict(
                xaxis_title="経度",
                yaxis_title="緯度",
                zaxis_title=z_title,
                aspectmode="data"
            ),
            height=600,
            margin=dict(l=10, r=10, t=50, b=10),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def _create_2d_track(self, filtered_indices: List[int]) -> go.Figure:
        """
        2Dトラックを作成
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        
        Returns
        -------
        go.Figure
            2Dトラック
        """
        # 必要なカラムがない場合は空のグラフを返す
        required_cols = ["latitude", "longitude"]
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        
        if missing_cols:
            fig = go.Figure()
            fig.update_layout(
                title=f"2Dトラック ({', '.join(missing_cols)} なし)",
                height=500
            )
            return fig
        
        # タイムスタンプでソートされたデータを取得
        if "timestamp" in self.data.columns:
            sorted_data = self.data.sort_values("timestamp").copy()
        else:
            sorted_data = self.data.copy()
        
        # グラフを初期化
        fig = go.Figure()
        
        # 2Dトラックのラインを追加
        fig.add_trace(go.Scatter(
            x=sorted_data["longitude"],
            y=sorted_data["latitude"],
            mode="lines",
            line=dict(color="blue", width=2),
            name="トラック"
        ))
        
        # 問題ポイントを種類ごとにグループ化して追加
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                # 現在のフィルタに含まれるインデックスのみ表示
                filtered_problem_indices = [idx for idx in indices if idx in filtered_indices]
                
                if filtered_problem_indices:
                    problem_df = self.data.iloc[filtered_problem_indices]
                    
                    # 問題の詳細情報を作成
                    hover_texts = []
                    for idx in filtered_problem_indices:
                        row = self.data.iloc[idx]
                        
                        text = f"インデックス: {idx}<br>"
                        text += f"問題タイプ: {self.problem_type_names.get(problem_type, problem_type)}<br>"
                        
                        if "timestamp" in row:
                            text += f"タイムスタンプ: {row['timestamp']}<br>"
                        
                        if "speed" in row:
                            text += f"速度: {row['speed']:.2f}<br>"
                        
                        if "direction" in row:
                            text += f"方向: {row['direction']:.2f}<br>"
                        
                        hover_texts.append(text)
                    
                    # マーカーを追加
                    fig.add_trace(go.Scatter(
                        x=problem_df["longitude"],
                        y=problem_df["latitude"],
                        mode="markers",
                        marker=dict(
                            size=10,
                            color=self.problem_type_colors.get(problem_type, "red"),
                            symbol="circle"
                        ),
                        name=self.problem_type_names.get(problem_type, problem_type),
                        hoverinfo="text",
                        hovertext=hover_texts,
                        customdata=filtered_problem_indices
                    ))
        
        # レイアウト設定
        fig.update_layout(
            title="2Dトラック",
            xaxis_title="経度",
            yaxis_title="緯度",
            height=500,
            margin=dict(l=30, r=30, t=50, b=30),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def _create_segment_analysis(self, filtered_indices: List[int]) -> go.Figure:
        """
        セグメント分析グラフを作成
        
        Parameters
        ----------
        filtered_indices : List[int]
            フィルタリングされた問題インデックス
        
        Returns
        -------
        go.Figure
            セグメント分析グラフ
        """
        # 必要なカラムがない場合は空のグラフを返す
        required_cols = ["timestamp", "latitude", "longitude"]
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        
        if missing_cols:
            fig = go.Figure()
            fig.update_layout(
                title=f"セグメント分析 ({', '.join(missing_cols)} なし)",
                height=500
            )
            return fig
        
        # タイムスタンプでソートされたデータを取得
        sorted_data = self.data.sort_values("timestamp").copy()
        
        # サブプロットの作成（速度プロファイルと距離プロファイル）
        from plotly.subplots import make_subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("速度プロファイル", "距離プロファイル"),
            shared_xaxes=True,
            vertical_spacing=0.1
        )
        
        # サンプルインデックスを作成（X軸）
        x = np.arange(len(sorted_data))
        
        # 速度プロファイル（実際の速度またはGPSポイント間の計算された速度）
        if "speed" in sorted_data.columns:
            speed = sorted_data["speed"]
        else:
            # 速度がない場合、GPSポイント間の距離から計算
            from geopy.distance import geodesic
            
            speed = np.zeros(len(sorted_data))
            prev_pos = None
            prev_time = None
            
            for i, (_, row) in enumerate(sorted_data.iterrows()):
                if i > 0:
                    curr_pos = (row["latitude"], row["longitude"])
                    curr_time = row["timestamp"]
                    
                    dist = geodesic(prev_pos, curr_pos).meters
                    time_diff = (curr_time - prev_time).total_seconds()
                    
                    if time_diff > 0:
                        # m/s から ノットに変換（1ノット = 0.514444 m/s）
                        speed[i] = (dist / time_diff) / 0.514444
                    else:
                        speed[i] = 0
                
                prev_pos = (row["latitude"], row["longitude"])
                prev_time = row["timestamp"]
        
        # 距離の累積計算
        distance = np.zeros(len(sorted_data))
        
        if "distance" in sorted_data.columns:
            # 距離カラムがある場合はそれを使用
            distance = sorted_data["distance"]
        else:
            # 距離カラムがない場合はGPSポイント間の距離から計算
            from geopy.distance import geodesic
            
            prev_pos = None
            cum_dist = 0
            
            for i, (_, row) in enumerate(sorted_data.iterrows()):
                if i > 0:
                    curr_pos = (row["latitude"], row["longitude"])
                    dist = geodesic(prev_pos, curr_pos).meters
                    cum_dist += dist
                    distance[i] = cum_dist
                
                prev_pos = (row["latitude"], row["longitude"])
        
        # 速度プロファイルの追加
        fig.add_trace(
            go.Scatter(
                x=x,
                y=speed,
                mode="lines",
                name="速度",
                line=dict(color="blue", width=2)
            ),
            row=1, col=1
        )
        
        # 距離プロファイルの追加
        fig.add_trace(
            go.Scatter(
                x=x,
                y=distance,
                mode="lines",
                name="距離",
                line=dict(color="green", width=2)
            ),
            row=2, col=1
        )
        
        # 問題ポイントを種類ごとにグループ化して追加
        for problem_type, indices in self.problem_indices.items():
            if problem_type != "all":
                # 現在のフィルタに含まれるインデックスのみ表示
                filtered_problem_indices = [idx for idx in indices if idx in filtered_indices]
                
                if filtered_problem_indices:
                    # ソートされたデータでの位置を特定
                    problem_x = []
                    problem_speed = []
                    problem_distance = []
                    hover_texts = []
                    
                    for idx in filtered_problem_indices:
                        # ソートされたデータでの位置を検索
                        sorted_idx = sorted_data.index.get_indexer([idx])[0] if idx in sorted_data.index else -1
                        
                        if sorted_idx >= 0:
                            problem_x.append(sorted_idx)
                            problem_speed.append(speed[sorted_idx])
                            problem_distance.append(distance[sorted_idx])
                            
                            # ホバーテキスト
                            row = self.data.iloc[idx]
                            text = f"インデックス: {idx}<br>"
                            text += f"問題タイプ: {self.problem_type_names.get(problem_type, problem_type)}<br>"
                            
                            if "timestamp" in row:
                                text += f"タイムスタンプ: {row['timestamp']}<br>"
                            
                            if "speed" in row:
                                text += f"速度: {row['speed']:.2f}<br>"
                            
                            text += f"累積距離: {distance[sorted_idx]:.2f}m<br>"
                            
                            hover_texts.append(text)
                    
                    # 速度プロファイルに問題マーカーを追加
                    fig.add_trace(
                        go.Scatter(
                            x=problem_x,
                            y=problem_speed,
                            mode="markers",
                            name=f"{self.problem_type_names.get(problem_type, problem_type)}",
                            marker=dict(
                                size=10,
                                color=self.problem_type_colors.get(problem_type, "red"),
                                symbol="circle"
                            ),
                            hoverinfo="text",
                            hovertext=hover_texts
                        ),
                        row=1, col=1
                    )
                    
                    # 距離プロファイルに問題マーカーを追加
                    fig.add_trace(
                        go.Scatter(
                            x=problem_x,
                            y=problem_distance,
                            mode="markers",
                            name=f"{self.problem_type_names.get(problem_type, problem_type)}",
                            marker=dict(
                                size=10,
                                color=self.problem_type_colors.get(problem_type, "red"),
                                symbol="circle"
                            ),
                            hoverinfo="text",
                            hovertext=hover_texts,
                            showlegend=False  # 凡例は重複させない
                        ),
                        row=2, col=1
                    )
        
        # レイアウト設定
        fig.update_layout(
            title="セグメント分析",
            xaxis_title="サンプルインデックス",
            xaxis2_title="サンプルインデックス",
            yaxis_title="速度",
            yaxis2_title="距離 (m)",
            height=600,
            margin=dict(l=30, r=30, t=50, b=30),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
