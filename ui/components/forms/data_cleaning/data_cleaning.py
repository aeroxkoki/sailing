# -*- coding: utf-8 -*-
"""
ui.components.forms.data_cleaning.data_cleaning

データクリーニングコンポーネント
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Callable, Tuple
import altair as alt
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator


class DataCleaning:
    """
    データクリーニングコンポーネント
    
    GPSデータの検証と修正を行うUIコンポーネント
    """
    
    def __init__(self, 
                 key: str = "data_cleaning", 
                 on_data_cleaned: Optional[Callable[[GPSDataContainer], None]] = None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントの一意のキー, by default "data_cleaning"
        on_data_cleaned : Optional[Callable[[GPSDataContainer], None]], optional
            データ修正完了時のコールバック関数, by default None
        """
        self.key = key
        self.on_data_cleaned = on_data_cleaned
        
        # セッション状態の初期化
        if f"{self.key}_container" not in st.session_state:
            st.session_state[f"{self.key}_container"] = None
        if f"{self.key}_validation_results" not in st.session_state:
            st.session_state[f"{self.key}_validation_results"] = None
        if f"{self.key}_fixed_container" not in st.session_state:
            st.session_state[f"{self.key}_fixed_container"] = None
        if f"{self.key}_fixes" not in st.session_state:
            st.session_state[f"{self.key}_fixes"] = []
        if f"{self.key}_view" not in st.session_state:
            st.session_state[f"{self.key}_view"] = "overview"
        if f"{self.key}_current_issue" not in st.session_state:
            st.session_state[f"{self.key}_current_issue"] = None
        if f"{self.key}_show_fixed" not in st.session_state:
            st.session_state[f"{self.key}_show_fixed"] = False
        if f"{self.key}_auto_fix_applied" not in st.session_state:
            st.session_state[f"{self.key}_auto_fix_applied"] = False
    
    def render(self, container: Optional[GPSDataContainer] = None):
        """
        コンポーネントをレンダリング
        
        Parameters
        ----------
        container : Optional[GPSDataContainer], optional
            表示・検証するGPSデータコンテナ, by default None
        """
        # コンテナが指定されていれば保存
        if container is not None:
            st.session_state[f"{self.key}_container"] = container
            # 新しいコンテナが指定された場合は状態をリセット
            st.session_state[f"{self.key}_validation_results"] = None
            st.session_state[f"{self.key}_fixed_container"] = None
            st.session_state[f"{self.key}_fixes"] = []
            st.session_state[f"{self.key}_view"] = "overview"
            st.session_state[f"{self.key}_current_issue"] = None
            st.session_state[f"{self.key}_show_fixed"] = False
            st.session_state[f"{self.key}_auto_fix_applied"] = False
        
        container = st.session_state.get(f"{self.key}_container")
        
        if container is None:
            st.info("データが読み込まれていません。まずデータをインポートしてください。")
            return
        
        # ビューに応じて表示を切り替え
        view = st.session_state[f"{self.key}_view"]
        
        if view == "overview":
            self._render_overview()
        elif view == "issue_detail":
            self._render_issue_detail()
        elif view == "fix_report":
            self._render_fix_report()
    
    def _render_overview(self):
        """データ概要と検証結果の表示"""
        container = st.session_state[f"{self.key}_container"]
        validation_results = st.session_state[f"{self.key}_validation_results"]
        fixed_container = st.session_state.get(f"{self.key}_fixed_container")
        show_fixed = st.session_state.get(f"{self.key}_show_fixed", False)
        
        # 表示するコンテナを選択
        display_container = fixed_container if show_fixed and fixed_container is not None else container
        
        # タブを設定
        tab1, tab2, tab3 = st.tabs(["データ検証", "データ可視化", "データプレビュー"])
        
        with tab1:
            st.header("データ検証")
            
            # データ検証ボタン（まだ検証が実行されていない場合）
            if validation_results is None:
                st.button("データを検証", key=f"{self.key}_validate_btn", on_click=self._validate_data)
            else:
                # 検証結果の表示
                self._render_validation_results()
                
                # 自動修正ボタン（修正が適用されていない場合）
                if not st.session_state.get(f"{self.key}_auto_fix_applied", False):
                    st.button("一般的な問題を自動修正", key=f"{self.key}_auto_fix_btn", on_click=self._auto_fix_issues)
                
                # 修正済みデータがある場合は切り替えボタンを表示
                if fixed_container is not None:
                    st.checkbox(
                        "修正済みデータを表示", 
                        key=f"{self.key}_show_fixed_checkbox",
                        value=show_fixed,
                        on_change=self._toggle_show_fixed
                    )
                
                # ユーザーが修正済みデータを確認したら、修正を確定するボタンを表示
                if fixed_container is not None and show_fixed:
                    st.button("修正を確定", key=f"{self.key}_confirm_fixes_btn", on_click=self._confirm_fixes)
        
        with tab2:
            st.header("データ可視化")
            
            # データの可視化表示
            self._render_data_visualization(display_container)
        
        with tab3:
            st.header("データプレビュー")
            
            # データのプレビュー表示
            self._render_data_preview(display_container)
    
    def _render_validation_results(self):
        """検証結果の表示"""
        validation_results = st.session_state[f"{self.key}_validation_results"]
        is_valid, results = validation_results
        
        # 検証結果のサマリー
        total_issues = len([r for r in results if not r["is_valid"]])
        error_issues = len([r for r in results if not r["is_valid"] and r["severity"] == "error"])
        warning_issues = len([r for r in results if not r["is_valid"] and r["severity"] == "warning"])
        info_issues = len([r for r in results if not r["is_valid"] and r["severity"] == "info"])
        
        if total_issues == 0:
            st.success("データは検証に合格しました。問題は見つかりませんでした。")
            return
        
        # 問題サマリーを表示
        st.write(f"**検証結果:** {total_issues}個の問題が見つかりました")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if error_issues > 0:
                st.error(f"エラー: {error_issues}件")
            else:
                st.info("エラー: 0件")
        with col2:
            if warning_issues > 0:
                st.warning(f"警告: {warning_issues}件")
            else:
                st.info("警告: 0件")
        with col3:
            if info_issues > 0:
                st.info(f"情報: {info_issues}件")
            else:
                st.info("情報: 0件")
        
        # 問題リストを表示
        st.subheader("検出された問題")
        
        issue_number = 0
        for result in results:
            if not result["is_valid"]:
                issue_number += 1
                
                # 重要度に応じて色を変える
                if result["severity"] == "error":
                    severity_color = "🔴"
                elif result["severity"] == "warning":
                    severity_color = "🟠"
                else:
                    severity_color = "🔵"
                
                # 問題の要約を作成
                summary = f"{severity_color} **問題 #{issue_number}:** {result['rule_name']} - {result['description']}"
                
                # 詳細の追加
                details = result["details"]
                if "error" in details:
                    summary += f"\n\n**エラー:** {details['error']}"
                elif "message" in details:
                    summary += f"\n\n**メッセージ:** {details['message']}"
                else:
                    # ルールタイプに応じた詳細の表示
                    rule_name = result["rule_name"]
                    
                    if "Required Columns" in rule_name:
                        missing = details.get("missing_columns", [])
                        if missing:
                            summary += f"\n\n**不足カラム:** {', '.join(missing)}"
                    elif "Value Range" in rule_name:
                        column = details.get("column", "")
                        count = details.get("out_of_range_count", 0)
                        actual_min = details.get("actual_min")
                        actual_max = details.get("actual_max")
                        
                        summary += f"\n\n**カラム:** {column}"
                        summary += f"\n**範囲外の値:** {count}個"
                        if actual_min is not None and actual_max is not None:
                            summary += f"\n**実際の範囲:** {actual_min} 〜 {actual_max}"
                    elif "No Null Values" in rule_name:
                        columns = list(details.get("null_counts", {}).items())
                        null_summary = [f"{col}: {count}個" for col, count in columns if count > 0]
                        
                        if null_summary:
                            summary += f"\n\n**欠損値:** {', '.join(null_summary)}"
                    elif "No Duplicate Timestamps" in rule_name:
                        count = details.get("duplicate_count", 0)
                        summary += f"\n\n**重複タイムスタンプ:** {count}個"
                    elif "Spatial Consistency" in rule_name:
                        count = details.get("anomaly_count", 0)
                        max_speed = details.get("max_calculated_speed", 0)
                        
                        summary += f"\n\n**異常な移動:** {count}個"
                        summary += f"\n**最大検出速度:** {max_speed:.1f} ノット"
                    elif "Temporal Consistency" in rule_name:
                        gap_count = details.get("gap_count", 0)
                        reverse_count = details.get("reverse_count", 0)
                        
                        if gap_count > 0:
                            summary += f"\n\n**大きな時間ギャップ:** {gap_count}個"
                        if reverse_count > 0:
                            summary += f"\n**時間逆行:** {reverse_count}個"
                
                # 問題の詳細を展開するエクスパンダー
                with st.expander(summary, expanded=False):
                    # 詳細情報を表示
                    st.write("### 詳細情報")
                    
                    for k, v in details.items():
                        if k not in ["error", "message"]:
                            if isinstance(v, list) and len(v) > 10:
                                st.write(f"**{k}:** {v[:10]} ... (他 {len(v) - 10} 項目)")
                            elif isinstance(v, dict) and len(v) > 10:
                                st.write(f"**{k}:** {dict(list(v.items())[:10])} ... (他 {len(v) - 10} 項目)")
                            else:
                                st.write(f"**{k}:** {v}")
                    
                    # 問題の詳細を見るボタン
                    st.button(
                        "この問題を詳しく見る",
                        key=f"{self.key}_view_issue_{issue_number}",
                        on_click=self._view_issue_detail,
                        args=(result,)
                    )
    
    def _render_data_visualization(self, container: GPSDataContainer):
        """データの可視化表示"""
        data = container.data
        
        # データポイント数を表示
        st.write(f"データポイント数: {len(data):,}")
        
        # 時間範囲を表示
        if len(data) > 0:
            time_range = container.get_time_range()
            st.write(f"開始時刻: {time_range['start']}")
            st.write(f"終了時刻: {time_range['end']}")
            st.write(f"期間: {time_range['duration_seconds'] / 60:.1f} 分")
        
        # 位置データのマップ表示
        st.subheader("位置データ")
        map_data = data[["latitude", "longitude"]].copy()
        st.map(map_data)
        
        # 時系列データの可視化
        if len(data) > 0:
            st.subheader("時系列データ")
            
            # 可視化するメトリクスを選択
            available_metrics = ["速度", "高度", "距離"]
            metric_cols = {
                "速度": "speed",
                "高度": "elevation",
                "距離": "distance"
            }
            
            # データに存在するメトリクスを特定
            available_metrics = [m for m in available_metrics if metric_cols[m] in data.columns]
            
            if available_metrics:
                selected_metric = st.selectbox(
                    "メトリクスを選択:",
                    available_metrics,
                    key=f"{self.key}_metric_select"
                )
                
                # 選択されたメトリクスの時系列チャートを作成
                metric_col = metric_cols[selected_metric]
                
                # データフレームを作成
                chart_data = pd.DataFrame({
                    "時刻": data["timestamp"],
                    selected_metric: data[metric_col]
                })
                
                # Altairでチャート作成
                chart = alt.Chart(chart_data).mark_line().encode(
                    x=alt.X('時刻:T', title='時刻'),
                    y=alt.Y(f'{selected_metric}:Q', title=selected_metric),
                    tooltip=['時刻:T', f'{selected_metric}:Q']
                ).interactive()
                
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("時系列で可視化できるメトリクスがありません。")
    
    def _render_data_preview(self, container: GPSDataContainer):
        """
        データのプレビュー表示
        
        問題箇所のハイライト機能を追加
        """
        data = container.data
        
        # 検証結果がある場合はハイライト表示
        if hasattr(self, "validator") and self.validator and hasattr(self.validator, "validation_results"):
            # 問題情報の取得
            problem_info = []
            for result in self.validator.validation_results:
                if not result["is_valid"]:
                    # 問題情報を追加
                    for issue in result["issues"]:
                        problem_info.append({
                            "index": issue.get("index", 0),
                            "column": issue.get("column", ""),
                            "problem_type": issue.get("problem_type", "other"),
                            "severity": issue.get("severity", "info"),
                            "description": issue.get("description", ""),
                            "value": issue.get("value", None),
                            "valid_range": issue.get("valid_range", None)
                        })
            
            if problem_info:
                st.subheader("問題箇所のハイライト表示")
                
                # ハイライトのための色定義
                highlight_colors = {
                    "missing_data": "#e6ccff",     # 薄い紫
                    "out_of_range": "#ffcccc",     # 薄い赤
                    "duplicates": "#ffffcc",       # 薄い黄
                    "spatial_anomalies": "#ccffcc", # 薄い緑
                    "temporal_anomalies": "#ccf2ff" # 薄い青
                }
                
                # 重要度ごとの不透明度
                severity_opacity = {
                    "error": 1.0,
                    "warning": 0.7,
                    "info": 0.4
                }
                
                # スタイルを適用
                styler = data.style
                
                # 問題ごとにスタイルを適用
                for problem in problem_info:
                    row_idx = problem["index"]
                    col_name = problem["column"]
                    problem_type = problem.get("problem_type", "other")
                    severity = problem.get("severity", "info")
                    
                    # カラムが存在するか確認（インデックスが範囲内か確認）
                    if row_idx >= 0 and row_idx < len(data) and col_name in data.columns:
                        # 問題タイプに応じた色を取得
                        color = highlight_colors.get(problem_type, "#f0f0f0")  # デフォルトは薄いグレー
                        
                        # 重要度に応じた不透明度を適用
                        opacity = severity_opacity.get(severity, 0.5)
                        
                        # 背景色とスタイルの定義
                        background_color = f"rgba({int(int(color[1:3], 16)*opacity)}, {int(int(color[3:5], 16)*opacity)}, {int(int(color[5:7], 16)*opacity)}, {opacity})"
                        
                        # セルスタイルの適用
                        styler = styler.applymap(
                            lambda _: f"background-color: {background_color}; font-weight: bold;",
                            subset=pd.IndexSlice[row_idx:row_idx, col_name:col_name]
                        )
                
                # ハイライト表示されたデータフレームを表示
                st.dataframe(styler, use_container_width=True)
                
                # 問題の統計情報を表示
                problem_types = {}
                for problem in problem_info:
                    p_type = problem.get("problem_type", "other")
                    if p_type in problem_types:
                        problem_types[p_type] += 1
                    else:
                        problem_types[p_type] = 1
                
                # 問題タイプ別の集計を表示
                st.subheader("問題タイプ別の集計")
                problem_df = pd.DataFrame({
                    "問題タイプ": list(problem_types.keys()),
                    "件数": list(problem_types.values())
                })
                st.dataframe(problem_df, use_container_width=True)
                
                # 問題箇所へのナビゲーションリンク
                st.info("問題箇所の詳細な分析や修正は、データ検証ダッシュボードの「データ問題」タブで行うことができます。")
                
            else:
                # 問題がない場合は通常のデータフレームを表示
                st.dataframe(data, use_container_width=True)
        else:
            # 検証結果がない場合は通常のデータフレームを表示
            st.dataframe(data, use_container_width=True)
        
        # データの要約統計量
        st.subheader("データの要約統計量")
        
        # 数値カラムの要約統計量を計算
        numeric_cols = data.select_dtypes(include=['number']).columns.tolist()
        if numeric_cols:
            stats = data[numeric_cols].describe().transpose()
            st.dataframe(stats, use_container_width=True)
        else:
            st.info("数値データがありません。")
        
        # メタデータ表示
        st.subheader("メタデータ")
        metadata = container.metadata
        
        for key, value in metadata.items():
            if isinstance(value, (dict, list)) and len(str(value)) > 100:
                with st.expander(f"{key}"):
                    st.write(value)
            else:
                st.write(f"**{key}:** {value}")
    
    def _render_issue_detail(self):
        """問題の詳細表示"""
        issue = st.session_state[f"{self.key}_current_issue"]
        container = st.session_state[f"{self.key}_container"]
        
        if issue is None or container is None:
            st.error("問題の詳細を表示できません。")
            st.button("戻る", key=f"{self.key}_back_from_detail", on_click=self._go_to_overview)
            return
        
        # 問題のタイプに応じたタイトル
        rule_name = issue["rule_name"]
        rule_severity = issue["severity"]
        
        # 重要度に応じて色を変える
        if rule_severity == "error":
            severity_badge = "🔴 エラー"
        elif rule_severity == "warning":
            severity_badge = "🟠 警告"
        else:
            severity_badge = "🔵 情報"
        
        st.header(f"{severity_badge}: {rule_name}")
        st.write(issue["description"])
        
        # 詳細データの表示
        details = issue["details"]
        
        # 戻るボタン
        st.button("← 検証結果一覧に戻る", key=f"{self.key}_back_to_overview", on_click=self._go_to_overview)
        
        # タブでデータと可視化を分ける
        tab1, tab2 = st.tabs(["問題の詳細", "データ可視化"])
        
        with tab1:
            # 問題タイプに応じた詳細表示とフィックスUI
            if "Required Columns" in rule_name:
                self._render_required_columns_detail(details)
            elif "Value Range" in rule_name:
                self._render_value_range_detail(details)
            elif "No Null Values" in rule_name:
                self._render_null_values_detail(details)
            elif "No Duplicate Timestamps" in rule_name:
                self._render_duplicate_timestamps_detail(details)
            elif "Spatial Consistency" in rule_name:
                self._render_spatial_consistency_detail(details)
            elif "Temporal Consistency" in rule_name:
                self._render_temporal_consistency_detail(details)
            else:
                # 汎用的な詳細表示
                for k, v in details.items():
                    if isinstance(v, (list, dict)) and len(str(v)) > 100:
                        with st.expander(f"{k}"):
                            st.write(v)
                    else:
                        st.write(f"**{k}:** {v}")
        
        with tab2:
            # 問題ポイントのデータ可視化
            if "Value Range" in rule_name:
                self._visualize_value_range_issue(details)
            elif "No Null Values" in rule_name:
                self._visualize_null_values_issue(details)
            elif "No Duplicate Timestamps" in rule_name:
                self._visualize_duplicate_timestamps_issue(details)
            elif "Spatial Consistency" in rule_name:
                self._visualize_spatial_consistency_issue(details)
            elif "Temporal Consistency" in rule_name:
                self._visualize_temporal_consistency_issue(details)
            else:
                st.info("この問題タイプには特別な可視化がありません。")
    
    def _render_required_columns_detail(self, details):
        """必須カラム問題の詳細表示"""
        missing_columns = details.get("missing_columns", [])
        found_columns = details.get("found_columns", [])
        all_columns = details.get("all_columns", [])
        
        st.subheader("問題の詳細")
        st.error(f"必須カラムが {len(missing_columns)}個 不足しています")
        
        if missing_columns:
            st.write("**不足しているカラム:**")
            for col in missing_columns:
                st.write(f"- {col}")
        
        if found_columns:
            st.write("**見つかったカラム:**")
            for col in found_columns:
                st.write(f"- {col}")
        
        st.write("**すべてのカラム:**")
        for col in all_columns:
            st.write(f"- {col}")
        
        st.subheader("解決方法")
        st.info("""
        この問題を解決するには、不足しているカラムをデータに追加する必要があります。
        
        例えば:
        - CSVファイルにカラムが存在するが、名前が異なる場合は、インポート時にカラムマッピングを修正してください
        - データソースに必須カラムがない場合は、別のデータソースを使用してください
        """)
    
    def _render_value_range_detail(self, details):
        """値範囲問題の詳細表示"""
        column = details.get("column", "")
        min_value = details.get("min_value")
        max_value = details.get("max_value")
        out_of_range_count = details.get("out_of_range_count", 0)
        out_of_range_indices = details.get("out_of_range_indices", [])
        actual_min = details.get("actual_min")
        actual_max = details.get("actual_max")
        
        st.subheader("問題の詳細")
        st.error(f"カラム '{column}' に範囲外の値が {out_of_range_count}個 あります")
        
        if min_value is not None and max_value is not None:
            st.write(f"**有効範囲:** {min_value} から {max_value}")
        elif min_value is not None:
            st.write(f"**最小値:** {min_value}")
        elif max_value is not None:
            st.write(f"**最大値:** {max_value}")
        
        if actual_min is not None and actual_max is not None:
            st.write(f"**実際の範囲:** {actual_min} から {actual_max}")
        
        # 問題のあるデータを表示
        if out_of_range_indices:
            data = st.session_state[f"{self.key}_container"].data
            problem_data = data.loc[out_of_range_indices]
            
            st.write("**範囲外のデータ:**")
            st.dataframe(problem_data)
        
        # 修正オプション
        st.subheader("修正オプション")
        
        fix_option = st.radio(
            "修正方法を選択:",
            ["クリッピング（境界値に置換）", "問題のあるデータを削除", "手動で値を編集"],
            key=f"{self.key}_value_range_fix_option"
        )
        
        if st.button("選択した方法で修正", key=f"{self.key}_fix_value_range"):
            if fix_option == "クリッピング（境界値に置換）":
                self._fix_value_range_clipping(column, min_value, max_value, out_of_range_indices)
            elif fix_option == "問題のあるデータを削除":
                self._fix_value_range_remove(out_of_range_indices)
            elif fix_option == "手動で値を編集":
                st.session_state[f"{self.key}_manual_edit_column"] = column
                st.session_state[f"{self.key}_manual_edit_indices"] = out_of_range_indices
                st.info("現在、手動編集機能は開発中です。")
                # 手動編集機能は将来追加
            
            # 修正後に検証を再実行
            self._validate_data()
    
    def _render_null_values_detail(self, details):
        """欠損値問題の詳細表示"""
        columns = details.get("columns", [])
        null_counts = details.get("null_counts", {})
        null_indices = details.get("null_indices", {})
        total_null_count = details.get("total_null_count", 0)
        
        st.subheader("問題の詳細")
        st.error(f"データに欠損値が {total_null_count}個 あります")
        
        if null_counts:
            st.write("**カラムごとの欠損値数:**")
            for col, count in null_counts.items():
                if count > 0:
                    st.write(f"- {col}: {count}個")
        
        # 問題のあるデータを表示
        if null_indices:
            data = st.session_state[f"{self.key}_container"].data
            
            all_indices = []
            for col, indices in null_indices.items():
                all_indices.extend(indices)
            
            all_indices = list(set(all_indices))  # 重複を削除
            
            if all_indices:
                problem_data = data.loc[all_indices]
                
                st.write("**欠損値を含むデータ:**")
                st.dataframe(problem_data)
        
        # 修正オプション
        st.subheader("修正オプション")
        
        # 欠損値を含むカラムを特定
        cols_with_nulls = [col for col, count in null_counts.items() if count > 0]
        
        # カラム選択（複数選択可能）
        selected_cols = st.multiselect(
            "修正するカラムを選択:",
            cols_with_nulls,
            default=cols_with_nulls,
            key=f"{self.key}_null_cols_select"
        )
        
        if selected_cols:
            fix_option = st.radio(
                "修正方法を選択:",
                ["線形補間", "前の値で埋める", "次の値で埋める", "平均値で埋める", "欠損値を含む行を削除"],
                key=f"{self.key}_null_fix_option"
            )
            
            if st.button("選択した方法で修正", key=f"{self.key}_fix_null_values"):
                # 選択されたカラムと方法で欠損値を修正
                if fix_option == "線形補間":
                    self._fix_null_values_interpolate(selected_cols)
                elif fix_option == "前の値で埋める":
                    self._fix_null_values_fillna(selected_cols, method="ffill")
                elif fix_option == "次の値で埋める":
                    self._fix_null_values_fillna(selected_cols, method="bfill")
                elif fix_option == "平均値で埋める":
                    self._fix_null_values_fillna(selected_cols, method="mean")
                elif fix_option == "欠損値を含む行を削除":
                    self._fix_null_values_dropna(selected_cols)
                
                # 修正後に検証を再実行
                self._validate_data()
    
    def _render_duplicate_timestamps_detail(self, details):
        """重複タイムスタンプ問題の詳細表示"""
        duplicate_count = details.get("duplicate_count", 0)
        duplicate_timestamps = details.get("duplicate_timestamps", [])
        duplicate_indices = details.get("duplicate_indices", {})
        
        st.subheader("問題の詳細")
        st.error(f"重複するタイムスタンプが {duplicate_count}個 あります")
        
        # 重複タイムスタンプのデータを表示
        if duplicate_indices:
            data = st.session_state[f"{self.key}_container"].data
            
            # 重複タイムスタンプごとにデータを表示
            for ts, indices in duplicate_indices.items():
                with st.expander(f"タイムスタンプ: {ts} ({len(indices)}個)"):
                    st.dataframe(data.loc[indices])
        
        # 修正オプション
        st.subheader("修正オプション")
        
        fix_option = st.radio(
            "修正方法を選択:",
            ["自動的に時間をずらす", "各重複グループから1つだけ残す", "すべての重複行を削除"],
            key=f"{self.key}_duplicate_fix_option"
        )
        
        if st.button("選択した方法で修正", key=f"{self.key}_fix_duplicates"):
            if fix_option == "自動的に時間をずらす":
                self._fix_duplicate_timestamps_offset(duplicate_indices)
            elif fix_option == "各重複グループから1つだけ残す":
                self._fix_duplicate_timestamps_keep_first(duplicate_indices)
            elif fix_option == "すべての重複行を削除":
                self._fix_duplicate_timestamps_remove_all(duplicate_indices)
            
            # 修正後に検証を再実行
            self._validate_data()
    
    def _render_spatial_consistency_detail(self, details):
        """空間的整合性問題の詳細表示"""
        anomaly_count = details.get("anomaly_count", 0)
        anomaly_indices = details.get("anomaly_indices", [])
        max_calculated_speed = details.get("max_calculated_speed", 0)
        min_calculated_speed = details.get("min_calculated_speed", 0)
        avg_calculated_speed = details.get("avg_calculated_speed", 0)
        anomaly_details = details.get("anomaly_details", [])
        
        st.subheader("問題の詳細")
        st.error(f"空間的に不自然な動きが {anomaly_count}個 検出されました")
        
        st.write(f"**最大検出速度:** {max_calculated_speed:.1f} ノット")
        st.write(f"**平均速度:** {avg_calculated_speed:.1f} ノット")
        st.write(f"**最小速度:** {min_calculated_speed:.1f} ノット")
        
        # 異常ポイントの詳細を表示
        if anomaly_details:
            st.write("**異常ポイントの詳細:**")
            
            for i, detail in enumerate(anomaly_details):
                with st.expander(f"異常ポイント #{i+1}: {detail.get('speed_knots', 0):.1f} ノット"):
                    for k, v in detail.items():
                        st.write(f"**{k}:** {v}")
        
        # 異常ポイントのデータを表示
        if anomaly_indices:
            data = st.session_state[f"{self.key}_container"].data
            problem_data = data.iloc[anomaly_indices]
            
            st.write("**異常ポイントのデータ:**")
            st.dataframe(problem_data)
        
        # 修正オプション
        st.subheader("修正オプション")
        
        fix_option = st.radio(
            "修正方法を選択:",
            ["異常ポイントを削除", "異常ポイントを補間"],
            key=f"{self.key}_spatial_fix_option"
        )
        
        if st.button("選択した方法で修正", key=f"{self.key}_fix_spatial"):
            if fix_option == "異常ポイントを削除":
                self._fix_spatial_consistency_remove(anomaly_indices)
            elif fix_option == "異常ポイントを補間":
                self._fix_spatial_consistency_interpolate(anomaly_indices)
            
            # 修正後に検証を再実行
            self._validate_data()
    
    def _render_temporal_consistency_detail(self, details):
        """時間的整合性問題の詳細表示"""
        gap_count = details.get("gap_count", 0)
        gap_indices = details.get("gap_indices", [])
        gap_details = details.get("gap_details", [])
        reverse_count = details.get("reverse_count", 0)
        reverse_indices = details.get("reverse_indices", [])
        reverse_details = details.get("reverse_details", [])
        max_time_gap = details.get("max_time_gap", 0)
        max_actual_gap = details.get("max_actual_gap", 0)
        min_actual_gap = details.get("min_actual_gap", 0)
        avg_actual_gap = details.get("avg_actual_gap", 0)
        
        st.subheader("問題の詳細")
        
        if gap_count > 0:
            st.error(f"大きな時間ギャップが {gap_count}個 検出されました")
            st.write(f"**許容ギャップ:** {max_time_gap:.1f} 秒")
            st.write(f"**最大ギャップ:** {max_actual_gap:.1f} 秒")
            
            # ギャップの詳細を表示
            if gap_details:
                st.write("**時間ギャップの詳細:**")
                
                for i, detail in enumerate(gap_details):
                    with st.expander(f"ギャップ #{i+1}: {detail.get('gap_seconds', 0):.1f} 秒"):
                        for k, v in detail.items():
                            st.write(f"**{k}:** {v}")
        
        if reverse_count > 0:
            st.error(f"時間が逆行している箇所が {reverse_count}個 検出されました")
            
            # 逆行の詳細を表示
            if reverse_details:
                st.write("**時間逆行の詳細:**")
                
                for i, detail in enumerate(reverse_details):
                    with st.expander(f"逆行 #{i+1}: {detail.get('diff_seconds', 0):.1f} 秒"):
                        for k, v in detail.items():
                            st.write(f"**{k}:** {v}")
        
        # 修正オプション
        st.subheader("修正オプション")
        
        if reverse_count > 0:
            st.write("**時間逆行の修正:**")
            reverse_fix_option = st.radio(
                "逆行している時間の修正方法:",
                ["逆行しているポイントを削除", "時間を自動修正"],
                key=f"{self.key}_reverse_fix_option"
            )
            
            if st.button("時間逆行を修正", key=f"{self.key}_fix_reverse"):
                if reverse_fix_option == "逆行しているポイントを削除":
                    self._fix_temporal_consistency_remove_reverse(reverse_indices)
                elif reverse_fix_option == "時間を自動修正":
                    self._fix_temporal_consistency_correct_reverse(reverse_details)
                
                # 修正後に検証を再実行
                self._validate_data()
        
        if gap_count > 0:
            st.write("**時間ギャップの修正:**")
            gap_fix_option = st.radio(
                "大きな時間ギャップの修正方法:",
                ["そのまま残す（修正不要）", "ギャップを補間する"],
                key=f"{self.key}_gap_fix_option"
            )
            
            if st.button("時間ギャップを修正", key=f"{self.key}_fix_gaps"):
                if gap_fix_option == "ギャップを補間する":
                    self._fix_temporal_consistency_interpolate_gaps(gap_details)
                
                # 修正後に検証を再実行
                self._validate_data()
    
    def _render_fix_report(self):
        """修正レポートの表示"""
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixed_container = st.session_state.get(f"{self.key}_fixed_container")
        
        if not fixes or fixed_container is None:
            st.error("修正レポートを表示できません。")
            st.button("戻る", key=f"{self.key}_back_from_report", on_click=self._go_to_overview)
            return
        
        st.header("データ修正レポート")
        
        # 修正サマリー
        total_fixes = len(fixes)
        st.write(f"**合計修正数:** {total_fixes}件")
        
        # 修正タイプ別の集計
        fix_types = {}
        for fix in fixes:
            fix_type = fix.get("type", "unknown")
            if fix_type in fix_types:
                fix_types[fix_type] += 1
            else:
                fix_types[fix_type] = 1
        
        # 修正タイプ別の表示
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("修正タイプ")
            for fix_type, count in fix_types.items():
                st.write(f"- {fix_type}: {count}件")
        
        with col2:
            # データサイズの変化を計算
            original_container = st.session_state.get(f"{self.key}_container")
            if original_container is not None:
                original_size = len(original_container.data)
                fixed_size = len(fixed_container.data)
                size_diff = fixed_size - original_size
                
                st.subheader("データサイズの変化")
                st.write(f"修正前: {original_size:,} ポイント")
                st.write(f"修正後: {fixed_size:,} ポイント")
                
                if size_diff < 0:
                    st.write(f"削減: {abs(size_diff):,} ポイント ({abs(size_diff) / original_size * 100:.1f}%)")
                elif size_diff > 0:
                    st.write(f"増加: {size_diff:,} ポイント ({size_diff / original_size * 100:.1f}%)")
                else:
                    st.write("変化なし")
        
        # 修正詳細
        st.subheader("修正の詳細")
        
        for i, fix in enumerate(fixes):
            fix_type = fix.get("type", "unknown")
            description = fix.get("description", "詳細情報なし")
            
            with st.expander(f"修正 #{i+1}: {fix_type}"):
                st.write(f"**説明:** {description}")
                
                # その他の詳細を表示
                for k, v in fix.items():
                    if k not in ["type", "description"]:
                        if isinstance(v, (list, dict)) and len(str(v)) > 100:
                            st.write(f"**{k}:**")
                            st.write(v)
                        else:
                            st.write(f"**{k}:** {v}")
        
        # 修正の確定または破棄
        col1, col2 = st.columns(2)
        
        with col1:
            st.button("修正を確定", key=f"{self.key}_confirm_report", on_click=self._confirm_fixes)
        
        with col2:
            st.button("修正を破棄", key=f"{self.key}_discard_report", on_click=self._discard_fixes)
    
    def _visualize_value_range_issue(self, details):
        """値範囲問題の可視化"""
        column = details.get("column", "")
        min_value = details.get("min_value")
        max_value = details.get("max_value")
        out_of_range_indices = details.get("out_of_range_indices", [])
        
        if not column or not out_of_range_indices:
            st.info("可視化するデータがありません。")
            return
        
        data = st.session_state[f"{self.key}_container"].data
        
        # カラム値の分布をヒストグラムで表示
        st.subheader(f"カラム '{column}' の値分布")
        
        if pd.api.types.is_numeric_dtype(data[column]):
            # 範囲外の値をマーキング
            valid_data = data[~data.index.isin(out_of_range_indices)][column]
            invalid_data = data.loc[out_of_range_indices, column]
            
            # ヒストグラムのデータフレームを作成
            hist_data = pd.DataFrame({
                "値": data[column],
                "状態": ["範囲外" if i in out_of_range_indices else "有効" for i in data.index]
            })
            
            # Altairでヒストグラム作成
            chart = alt.Chart(hist_data).mark_bar().encode(
                alt.X('値:Q', bin=alt.Bin(maxbins=50), title=column),
                alt.Y('count()', title='頻度'),
                alt.Color('状態:N', scale=alt.Scale(domain=['有効', '範囲外'], range=['#1f77b4', '#d62728']))
            ).properties(
                width=600,
                height=400
            )
            
            # 有効範囲を示す縦線
            if min_value is not None:
                min_rule = alt.Chart(pd.DataFrame({'min': [min_value]})).mark_rule(color='green').encode(
                    x='min:Q'
                )
                chart = chart + min_rule
            
            if max_value is not None:
                max_rule = alt.Chart(pd.DataFrame({'max': [max_value]})).mark_rule(color='red').encode(
                    x='max:Q'
                )
                chart = chart + max_rule
            
            st.altair_chart(chart, use_container_width=True)
            
            # 要約統計量
            st.write("**値の統計量:**")
            st.write(f"全体: 最小={data[column].min()}, 最大={data[column].max()}, 平均={data[column].mean():.2f}")
            
            if not valid_data.empty:
                st.write(f"有効値: 最小={valid_data.min()}, 最大={valid_data.max()}, 平均={valid_data.mean():.2f}")
            
            if not invalid_data.empty:
                st.write(f"範囲外値: 最小={invalid_data.min()}, 最大={invalid_data.max()}, 平均={invalid_data.mean():.2f}")
        else:
            st.info(f"カラム '{column}' は数値データではないため、ヒストグラムを表示できません。")
    
    def _visualize_null_values_issue(self, details):
        """欠損値問題の可視化"""
        null_counts = details.get("null_counts", {})
        null_indices = details.get("null_indices", {})
        
        if not null_counts:
            st.info("可視化するデータがありません。")
            return
        
        # 欠損値のバーチャート
        st.subheader("カラムごとの欠損値")
        
        # 欠損値の多いカラムでソート
        sorted_counts = sorted(null_counts.items(), key=lambda x: x[1], reverse=True)
        count_df = pd.DataFrame(sorted_counts, columns=["カラム", "欠損値数"])
        
        # Altairでバーチャート作成
        chart = alt.Chart(count_df).mark_bar().encode(
            alt.X('欠損値数:Q', title='欠損値数'),
            alt.Y('カラム:N', sort='-x', title='カラム名')
        ).properties(
            width=600,
            height=400
        )
        
        st.altair_chart(chart, use_container_width=True)
        
        # 欠損値の時系列分布
        if null_indices:
            st.subheader("欠損値の時系列分布")
            
            data = st.session_state[f"{self.key}_container"].data
            
            if 'timestamp' in data.columns:
                # 時間軸に沿った欠損値の分布を可視化
                time_chunks = pd.date_range(
                    start=data['timestamp'].min(),
                    end=data['timestamp'].max(),
                    periods=20
                )
                
                # 時間チャンクごとの欠損値数をカウント
                chunk_counts = {}
                
                for col, indices in null_indices.items():
                    if indices:
                        chunk_counts[col] = []
                        null_times = data.loc[indices, 'timestamp']
                        
                        for i in range(len(time_chunks) - 1):
                            start = time_chunks[i]
                            end = time_chunks[i + 1]
                            count = ((null_times >= start) & (null_times < end)).sum()
                            chunk_counts[col].append({
                                'chunk': i,
                                'start_time': start,
                                'end_time': end,
                                'count': count,
                                'column': col
                            })
                
                # 全カラムの時間チャンクデータを結合
                all_chunks = []
                for col, chunks in chunk_counts.items():
                    all_chunks.extend(chunks)
                
                if all_chunks:
                    # データフレームに変換
                    time_df = pd.DataFrame(all_chunks)
                    
                    # Altairでヒートマップ作成
                    heatmap = alt.Chart(time_df).mark_rect().encode(
                        alt.X('chunk:O', title='時間チャンク'),
                        alt.Y('column:N', title='カラム'),
                        alt.Color('count:Q', scale=alt.Scale(scheme='blues'), title='欠損値数')
                    ).properties(
                        width=600,
                        height=400
                    )
                    
                    st.altair_chart(heatmap, use_container_width=True)
                else:
                    st.info("時系列で可視化できる欠損値がありません。")
            else:
                st.info("タイムスタンプカラムがないため、時系列分布を表示できません。")
    
    def _visualize_duplicate_timestamps_issue(self, details):
        """重複タイムスタンプ問題の可視化"""
        duplicate_timestamps = details.get("duplicate_timestamps", [])
        duplicate_indices = details.get("duplicate_indices", {})
        
        if not duplicate_timestamps:
            st.info("可視化するデータがありません。")
            return
        
        # 重複数のヒストグラム
        st.subheader("重複タイムスタンプの分布")
        
        # 重複数をカウント
        dup_counts = [len(indices) for ts, indices in duplicate_indices.items()]
        
        if dup_counts:
            # データフレームに変換
            count_df = pd.DataFrame({
                "タイムスタンプ": list(duplicate_indices.keys()),
                "重複数": dup_counts
            })
            
            # Altairでヒストグラム作成
            hist = alt.Chart(count_df).mark_bar().encode(
                alt.X('重複数:Q', bin=True, title='重複数'),
                alt.Y('count()', title='頻度')
            ).properties(
                width=600,
                height=400
            )
            
            st.altair_chart(hist, use_container_width=True)
            
            # 重複数の統計
            st.write(f"**最小重複数:** {min(dup_counts)}")
            st.write(f"**最大重複数:** {max(dup_counts)}")
            st.write(f"**平均重複数:** {sum(dup_counts) / len(dup_counts):.2f}")
        
        # 重複タイムスタンプの時系列分布
        if duplicate_timestamps:
            st.subheader("重複タイムスタンプの時系列分布")
            
            # タイムスタンプを日時に変換
            try:
                times = pd.to_datetime(duplicate_timestamps)
                
                # データフレームに変換
                time_df = pd.DataFrame({
                    "タイムスタンプ": times,
                    "カウント": 1
                })
                
                # Altairでタイムラインチャート作成
                timeline = alt.Chart(time_df).mark_circle().encode(
                    alt.X('タイムスタンプ:T', title='時間'),
                    alt.Y('カウント:Q', title=''),
                    alt.Size('カウント:Q', legend=None)
                ).properties(
                    width=600,
                    height=200
                )
                
                st.altair_chart(timeline, use_container_width=True)
            except:
                st.info("タイムスタンプを日時形式に変換できないため、時系列分布を表示できません。")
    
    def _visualize_spatial_consistency_issue(self, details):
        """空間的整合性問題の可視化"""
        anomaly_indices = details.get("anomaly_indices", [])
        anomaly_details = details.get("anomaly_details", [])
        
        if not anomaly_indices:
            st.info("可視化するデータがありません。")
            return
        
        data = st.session_state[f"{self.key}_container"].data
        
        # 速度の分布を表示
        if 'speed' in data.columns:
            st.subheader("速度の分布")
            
            # 異常ポイントと正常ポイントを分ける
            speed_data = pd.DataFrame({
                "速度": data['speed'],
                "状態": ["異常" if i in anomaly_indices else "正常" for i in range(len(data))]
            })
            
            # Altairでヒストグラム作成
            speed_hist = alt.Chart(speed_data).mark_bar().encode(
                alt.X('速度:Q', bin=alt.Bin(maxbins=50), title='速度'),
                alt.Y('count()', title='頻度'),
                alt.Color('状態:N', scale=alt.Scale(domain=['正常', '異常'], range=['#1f77b4', '#d62728']))
            ).properties(
                width=600,
                height=400
            )
            
            st.altair_chart(speed_hist, use_container_width=True)
        
        # 位置データのマップ表示
        st.subheader("異常ポイントの位置")
        
        # マップデータ作成
        map_data = pd.DataFrame({
            "latitude": data['latitude'],
            "longitude": data['longitude'],
            "color": ["red" if i in anomaly_indices else "blue" for i in range(len(data))]
        })
        
        # マップ表示
        st.map(map_data)
        
        # 異常ポイントの詳細
        if anomaly_details:
            st.subheader("異常ポイントの速度分布")
            
            # 速度データを抽出
            speeds = [detail.get('speed_knots', 0) for detail in anomaly_details]
            
            if speeds:
                # データフレームに変換
                speed_df = pd.DataFrame({
                    "ポイント": range(1, len(speeds) + 1),
                    "速度": speeds
                })
                
                # Altairで棒グラフ作成
                speed_chart = alt.Chart(speed_df).mark_bar().encode(
                    alt.X('ポイント:O', title='異常ポイント'),
                    alt.Y('速度:Q', title='速度 (ノット)'),
                    alt.Color('速度:Q', scale=alt.Scale(scheme='reds'))
                ).properties(
                    width=600,
                    height=400
                )
                
                st.altair_chart(speed_chart, use_container_width=True)
                
                # 速度の統計
                st.write(f"**最小速度:** {min(speeds):.1f} ノット")
                st.write(f"**最大速度:** {max(speeds):.1f} ノット")
                st.write(f"**平均速度:** {sum(speeds) / len(speeds):.1f} ノット")
    
    def _visualize_temporal_consistency_issue(self, details):
        """時間的整合性問題の可視化"""
        gap_indices = details.get("gap_indices", [])
        gap_details = details.get("gap_details", [])
        reverse_indices = details.get("reverse_indices", [])
        reverse_details = details.get("reverse_details", [])
        
        if not gap_indices and not reverse_indices:
            st.info("可視化するデータがありません。")
            return
        
        data = st.session_state[f"{self.key}_container"].data
        
        # ギャップの分布
        if gap_details:
            st.subheader("時間ギャップの分布")
            
            # ギャップ秒数を抽出
            gaps = [detail.get('gap_seconds', 0) for detail in gap_details]
            
            if gaps:
                # データフレームに変換
                gap_df = pd.DataFrame({
                    "ギャップ": gaps
                })
                
                # Altairでヒストグラム作成
                gap_hist = alt.Chart(gap_df).mark_bar().encode(
                    alt.X('ギャップ:Q', bin=alt.Bin(maxbins=20), title='ギャップ (秒)'),
                    alt.Y('count()', title='頻度')
                ).properties(
                    width=600,
                    height=300
                )
                
                st.altair_chart(gap_hist, use_container_width=True)
                
                # ギャップの統計
                st.write(f"**最小ギャップ:** {min(gaps):.1f} 秒")
                st.write(f"**最大ギャップ:** {max(gaps):.1f} 秒")
                st.write(f"**平均ギャップ:** {sum(gaps) / len(gaps):.1f} 秒")
        
        # 逆行の分布
        if reverse_details:
            st.subheader("時間逆行の分布")
            
            # 逆行秒数を抽出
            reverses = [abs(detail.get('diff_seconds', 0)) for detail in reverse_details]
            
            if reverses:
                # データフレームに変換
                reverse_df = pd.DataFrame({
                    "逆行": reverses
                })
                
                # Altairでヒストグラム作成
                reverse_hist = alt.Chart(reverse_df).mark_bar().encode(
                    alt.X('逆行:Q', bin=alt.Bin(maxbins=20), title='逆行 (秒)'),
                    alt.Y('count()', title='頻度')
                ).properties(
                    width=600,
                    height=300
                )
                
                st.altair_chart(reverse_hist, use_container_width=True)
                
                # 逆行の統計
                st.write(f"**最小逆行:** {min(reverses):.1f} 秒")
                st.write(f"**最大逆行:** {max(reverses):.1f} 秒")
                st.write(f"**平均逆行:** {sum(reverses) / len(reverses):.1f} 秒")
        
        # 時間間隔の分布
        st.subheader("時間間隔の分布")
        
        if 'timestamp' in data.columns and len(data) > 1:
            # タイムスタンプでソート
            sorted_data = data.sort_values('timestamp').copy()
            
            # 時間差を計算
            time_diffs = []
            for i in range(1, len(sorted_data)):
                diff = (sorted_data['timestamp'].iloc[i] - sorted_data['timestamp'].iloc[i-1]).total_seconds()
                time_diffs.append(diff)
            
            if time_diffs:
                # データフレームに変換
                diff_df = pd.DataFrame({
                    "時間差": time_diffs
                })
                
                # 極端な値を除外（可視化用）
                filtered_diffs = [d for d in time_diffs if d < 600]  # 10分未満
                
                if filtered_diffs:
                    filtered_df = pd.DataFrame({
                        "時間差": filtered_diffs
                    })
                    
                    # Altairでヒストグラム作成
                    diff_hist = alt.Chart(filtered_df).mark_bar().encode(
                        alt.X('時間差:Q', bin=alt.Bin(maxbins=30), title='時間差 (秒)'),
                        alt.Y('count()', title='頻度')
                    ).properties(
                        width=600,
                        height=300
                    )
                    
                    st.altair_chart(diff_hist, use_container_width=True)
                
                # 時間差の統計（全データ）
                st.write(f"**最小時間差:** {min(time_diffs):.1f} 秒")
                st.write(f"**最大時間差:** {max(time_diffs):.1f} 秒")
                st.write(f"**平均時間差:** {sum(time_diffs) / len(time_diffs):.1f} 秒")
                st.write(f"**中央値時間差:** {sorted(time_diffs)[len(time_diffs)//2]:.1f} 秒")
    
    def _fix_value_range_clipping(self, column, min_value, max_value, indices):
        """値範囲問題をクリッピングで修正"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        # クリッピングを適用
        if min_value is not None:
            below_min = data.loc[data.index.isin(indices) & (data[column] < min_value), column]
            data.loc[below_min.index, column] = min_value
        
        if max_value is not None:
            above_max = data.loc[data.index.isin(indices) & (data[column] > max_value), column]
            data.loc[above_max.index, column] = max_value
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "value_range_clipping",
            "column": column,
            "min_value": min_value,
            "max_value": max_value,
            "fixed_count": len(indices),
            "description": f"カラム '{column}' の範囲外の値 {len(indices)}個 をクリッピングしました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_value_range_remove(self, indices):
        """値範囲問題を行削除で修正"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        # 問題の行を削除
        data = data.drop(indices)
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "value_range_remove",
            "removed_indices": indices,
            "removed_count": len(indices),
            "description": f"範囲外の値を持つ行 {len(indices)}個 を削除しました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_null_values_interpolate(self, columns):
        """欠損値を線形補間で修正"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        fixed_count = 0
        for col in columns:
            if col in data.columns:
                null_count = data[col].isnull().sum()
                if null_count > 0:
                    data[col] = data[col].interpolate(method='linear')
                    fixed_count += null_count
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "null_values_interpolate",
            "columns": columns,
            "fixed_count": fixed_count,
            "description": f"欠損値 {fixed_count}個 を線形補間で修正しました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_null_values_fillna(self, columns, method):
        """欠損値を埋める"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        fixed_count = 0
        for col in columns:
            if col in data.columns:
                null_count = data[col].isnull().sum()
                if null_count > 0:
                    if method == "ffill":
                        data[col] = data[col].fillna(method='ffill')
                        method_name = "前の値"
                    elif method == "bfill":
                        data[col] = data[col].fillna(method='bfill')
                        method_name = "次の値"
                    elif method == "mean" and pd.api.types.is_numeric_dtype(data[col]):
                        data[col] = data[col].fillna(data[col].mean())
                        method_name = "平均値"
                    else:
                        continue
                    
                    fixed_count += null_count
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": f"null_values_fill_{method}",
            "columns": columns,
            "fixed_count": fixed_count,
            "description": f"欠損値 {fixed_count}個 を{method_name}で埋めました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_null_values_dropna(self, columns):
        """欠損値を含む行を削除"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        # 削除前のサイズ
        original_size = len(data)
        
        # 指定されたカラムの欠損値を含む行を削除
        data = data.dropna(subset=columns)
        
        # 削除された行数
        removed_count = original_size - len(data)
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "null_values_dropna",
            "columns": columns,
            "removed_count": removed_count,
            "description": f"欠損値を含む行 {removed_count}個 を削除しました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_duplicate_timestamps_offset(self, duplicate_indices):
        """重複タイムスタンプをオフセットで修正"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        fixed_count = 0
        for ts, indices in duplicate_indices.items():
            if len(indices) > 1:
                # 最初のタイムスタンプは変更しない
                for i, idx in enumerate(indices[1:], 1):
                    # タイムスタンプに少しずつオフセットを加える
                    data.loc[idx, 'timestamp'] = pd.to_datetime(ts) + pd.Timedelta(milliseconds=i)
                    fixed_count += 1
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "duplicate_timestamps_offset",
            "fixed_count": fixed_count,
            "description": f"重複タイムスタンプ {fixed_count}個 をオフセット（時間をずらす）で修正しました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_duplicate_timestamps_keep_first(self, duplicate_indices):
        """重複タイムスタンプをグループごとに1つだけ残して修正"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        # 削除する行のインデックス
        to_remove = []
        for ts, indices in duplicate_indices.items():
            if len(indices) > 1:
                # 最初のインデックス以外をすべて削除
                to_remove.extend(indices[1:])
        
        # 重複行を削除
        data = data.drop(to_remove)
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "duplicate_timestamps_keep_first",
            "removed_count": len(to_remove),
            "description": f"重複タイムスタンプを持つ行 {len(to_remove)}個 を削除し、各タイムスタンプから1つだけ残しました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_duplicate_timestamps_remove_all(self, duplicate_indices):
        """重複タイムスタンプを持つ行をすべて削除"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        # 重複タイムスタンプを持つ行のインデックス
        all_indices = []
        for ts, indices in duplicate_indices.items():
            all_indices.extend(indices)
        
        # 重複行を削除
        data = data.drop(all_indices)
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "duplicate_timestamps_remove_all",
            "removed_count": len(all_indices),
            "description": f"重複タイムスタンプを持つ行 {len(all_indices)}個 をすべて削除しました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_spatial_consistency_remove(self, anomaly_indices):
        """空間的整合性問題を行削除で修正"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        # 問題のある行を削除
        original_size = len(data)
        data = data.drop(data.index[anomaly_indices])
        removed_count = original_size - len(data)
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "spatial_consistency_remove",
            "removed_count": removed_count,
            "description": f"空間的整合性のない {removed_count}個 のポイントを削除しました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_spatial_consistency_interpolate(self, anomaly_indices):
        """空間的整合性問題を補間で修正"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        # 異常ポイントを一時的にNaNに置き換える
        for i in anomaly_indices:
            if i < len(data):
                data.loc[data.index[i], ['latitude', 'longitude']] = np.nan
        
        # NaNを補間
        data['latitude'] = data['latitude'].interpolate(method='linear')
        data['longitude'] = data['longitude'].interpolate(method='linear')
        
        # speedカラムがあれば再計算
        if 'speed' in data.columns:
            # タイムスタンプでソート
            data = data.sort_values('timestamp')
            
            # 距離と時間差から速度を再計算
            from geopy.distance import great_circle
            
            speeds = []
            for i in range(1, len(data)):
                prev_lat = data['latitude'].iloc[i-1]
                prev_lon = data['longitude'].iloc[i-1]
                curr_lat = data['latitude'].iloc[i]
                curr_lon = data['longitude'].iloc[i]
                
                prev_time = data['timestamp'].iloc[i-1]
                curr_time = data['timestamp'].iloc[i]
                
                distance = great_circle((prev_lat, prev_lon), (curr_lat, curr_lon)).meters
                time_diff = (curr_time - prev_time).total_seconds()
                
                if time_diff > 0:
                    speed = (distance / time_diff) / 0.514444  # m/s to knots
                else:
                    speed = 0
                
                speeds.append(speed)
            
            # 最初の行の速度は2番目の値を使用
            speeds.insert(0, speeds[0] if speeds else 0)
            
            # 速度を更新
            data['speed'] = speeds
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "spatial_consistency_interpolate",
            "fixed_count": len(anomaly_indices),
            "description": f"空間的整合性のない {len(anomaly_indices)}個 のポイントを補間しました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_temporal_consistency_remove_reverse(self, reverse_indices):
        """時間的逆行問題を行削除で修正"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        # 問題のある行を削除
        original_size = len(data)
        data = data.drop(data.index[reverse_indices])
        removed_count = original_size - len(data)
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "temporal_consistency_remove_reverse",
            "removed_count": removed_count,
            "description": f"時間的に逆行する {removed_count}個 のポイントを削除しました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_temporal_consistency_correct_reverse(self, reverse_details):
        """時間的逆行問題を修正"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        data = container.data.copy()
        
        fixed_count = 0
        for detail in reverse_details:
            idx = detail.get("original_index")
            prev_ts = detail.get("prev_timestamp")
            curr_ts = detail.get("curr_timestamp")
            
            if idx is not None and prev_ts is not None:
                # 修正タイムスタンプを計算（前のタイムスタンプの1秒後）
                new_ts = prev_ts + pd.Timedelta(seconds=1)
                
                # タイムスタンプを修正
                data.loc[idx, 'timestamp'] = new_ts
                fixed_count += 1
        
        # タイムスタンプでソート
        data = data.sort_values('timestamp').reset_index(drop=True)
        
        # 修正結果を保存
        fixed_container = GPSDataContainer(data, container.metadata.copy())
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        
        # 修正を記録
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        fixes.append({
            "type": "temporal_consistency_correct_reverse",
            "fixed_count": fixed_count,
            "description": f"時間的に逆行する {fixed_count}個 のポイントのタイムスタンプを修正しました"
        })
        st.session_state[f"{self.key}_fixes"] = fixes
        
        # 修正済みフラグをセット
        st.session_state[f"{self.key}_show_fixed"] = True
    
    def _fix_temporal_consistency_interpolate_gaps(self, gap_details):
        """時間ギャップを補間で修正"""
        # この機能はまだ実装されていません
        st.info("時間ギャップの補間機能は現在開発中です。")
    
    def _validate_data(self):
        """データを検証"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        
        # データバリデータを作成
        validator = DataValidator()
        
        # 検証実行
        validation_results = validator.validate(container)
        
        # 検証結果を保存
        st.session_state[f"{self.key}_validation_results"] = validation_results
    
    def _auto_fix_issues(self):
        """一般的な問題を自動修正"""
        if f"{self.key}_container" not in st.session_state:
            return
        
        container = st.session_state[f"{self.key}_container"]
        
        # データバリデータを作成
        validator = DataValidator()
        
        # 検証して自動修正
        fixed_container, fixes = validator.fix_common_issues(container)
        
        # 修正結果を保存
        st.session_state[f"{self.key}_fixed_container"] = fixed_container
        st.session_state[f"{self.key}_fixes"] = fixes
        st.session_state[f"{self.key}_show_fixed"] = True
        st.session_state[f"{self.key}_auto_fix_applied"] = True
        
        # 修正済みデータを検証
        validator = DataValidator()
        validation_results = validator.validate(fixed_container)
        st.session_state[f"{self.key}_validation_results"] = validation_results
    
    def _toggle_show_fixed(self):
        """修正済みデータの表示切り替え"""
        st.session_state[f"{self.key}_show_fixed"] = not st.session_state.get(f"{self.key}_show_fixed", False)
    
    def _confirm_fixes(self):
        """修正を確定"""
        if f"{self.key}_fixed_container" not in st.session_state:
            return
        
        fixed_container = st.session_state[f"{self.key}_fixed_container"]
        fixes = st.session_state.get(f"{self.key}_fixes", [])
        
        # 元のコンテナを更新
        st.session_state[f"{self.key}_container"] = fixed_container
        
        # 修正情報をリセット
        st.session_state[f"{self.key}_fixed_container"] = None
        st.session_state[f"{self.key}_fixes"] = []
        st.session_state[f"{self.key}_show_fixed"] = False
        st.session_state[f"{self.key}_auto_fix_applied"] = False
        
        # コールバック関数を実行
        if self.on_data_cleaned:
            self.on_data_cleaned(fixed_container)
        
        # 修正確定メッセージを表示（再レンダリング時）
        st.session_state[f"{self.key}_fix_confirmed"] = True
    
    def _discard_fixes(self):
        """修正を破棄"""
        # 修正情報をリセット
        st.session_state[f"{self.key}_fixed_container"] = None
        st.session_state[f"{self.key}_fixes"] = []
        st.session_state[f"{self.key}_show_fixed"] = False
        st.session_state[f"{self.key}_auto_fix_applied"] = False
        
        # 修正破棄メッセージを表示（再レンダリング時）
        st.session_state[f"{self.key}_fix_discarded"] = True
    
    def _view_issue_detail(self, issue):
        """問題の詳細表示に切り替え"""
        st.session_state[f"{self.key}_current_issue"] = issue
        st.session_state[f"{self.key}_view"] = "issue_detail"
    
    def _go_to_overview(self):
        """概要表示に戻る"""
        st.session_state[f"{self.key}_view"] = "overview"
        st.session_state[f"{self.key}_current_issue"] = None
    
    def _go_to_fix_report(self):
        """修正レポート表示に切り替え"""
        st.session_state[f"{self.key}_view"] = "fix_report"
