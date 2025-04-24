# -*- coding: utf-8 -*-
"""
ui.components.visualizations.validation_dashboard

データ検証結果のダッシュボード表示コンポーネント
"""

import streamlit as st
from typing import Dict, List, Any, Optional, Callable, Union
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.visualization import ValidationVisualization
from sailing_data_processor.validation.data_cleaner import DataCleaner


class ValidationDashboard:
    """
    データ検証ダッシュボードコンポーネント
    
    データ検証結果を視覚的にダッシュボード形式で表示するコンポーネント
    """
    
    def __init__(self, 
                key: str = "validation_dashboard", 
                container: Optional[GPSDataContainer] = None,
                validator: Optional[DataValidator] = None,
                on_clean_data: Optional[Callable[[Dict[str, Any]], None]] = None,
                on_export: Optional[Callable[[str], None]] = None):
        """
        データ検証ダッシュボードの初期化
        
        Parameters
        ----------
        key : str, optional
            Streamlitウィジェットのキー, by default "validation_dashboard"
        container : Optional[GPSDataContainer], optional
            検証対象のGPSデータコンテナ, by default None
        validator : Optional[DataValidator], optional
            データ検証器, by default None
        on_clean_data : Optional[Callable[[Dict[str, Any]], None]], optional
            データクリーニング実行時のコールバック関数, by default None
        on_export : Optional[Callable[[str], None]], optional
            レポートエクスポート時のコールバック関数, by default None
        """
        self.key = key
        self.container = container
        self.validator = validator
        self.on_clean_data = on_clean_data
        self.on_export = on_export
        
        # 視覚化モジュールの初期化
        self.visualization = None
        
        # セッション状態の初期化
        if f"{self.key}_tab" not in st.session_state:
            st.session_state[f"{self.key}_tab"] = "overview"
        if f"{self.key}_selected_issue" not in st.session_state:
            st.session_state[f"{self.key}_selected_issue"] = None
        if f"{self.key}_auto_fixes" not in st.session_state:
            st.session_state[f"{self.key}_auto_fixes"] = []
        
        # スタイル定義
        self.HIGHLIGHT_COLORS = {
            "missing_data": "#e6ccff",     # 薄い紫
            "out_of_range": "#ffcccc",     # 薄い赤
            "duplicates": "#ffffcc",       # 薄い黄
            "spatial_anomalies": "#ccffcc", # 薄い緑
            "temporal_anomalies": "#ccf2ff" # 薄い青
        }
        
        # 重要度ごとの不透明度
        self.SEVERITY_OPACITY = {
            "error": 1.0,
            "warning": 0.7,
            "info": 0.4
        }
        
    def set_container(self, container: GPSDataContainer):
        """
        データコンテナをセット
        
        Parameters
        ----------
        container : GPSDataContainer
            検証対象のGPSデータコンテナ
        """
        self.container = container
        
    def set_validator(self, validator: DataValidator):
        """
        データ検証器をセット
        
        Parameters
        ----------
        validator : DataValidator
            データ検証器
        """
        self.validator = validator
        
    def render(self) -> Dict[str, Any]:
        """
        ダッシュボードをレンダリング
        
        Returns
        -------
        Dict[str, Any]
            レンダリング状態と選択情報を含む辞書
        """
        # データが未設定の場合は何もしない
        if self.container is None or self.validator is None:
            st.warning("データまたは検証器が設定されていません。")
            return {"status": "not_ready"}
        
        # 視覚化モジュールの初期化（未初期化の場合）
        if self.visualization is None:
            self.visualization = ValidationVisualization(self.validator, self.container.data)
        
        # タブの表示
        tabs = ["overview", "data_issues", "spatial_issues", "temporal_issues", "fixes", "report"]
        tab_labels = ["概要", "データ問題", "空間的問題", "時間的問題", "修正候補", "レポート"]
        
        st.write("## データ検証ダッシュボード")
        
        tab_cols = st.columns(len(tabs))
        for i, (tab, label) in enumerate(zip(tabs, tab_labels)):
            is_active = st.session_state[f"{self.key}_tab"] == tab
            tab_style = "font-weight: bold;" if is_active else ""
            
            if tab_cols[i].button(
                label, 
                key=f"{self.key}_{tab}_btn",
                type="primary" if is_active else "secondary",
                use_container_width=True
            ):
                st.session_state[f"{self.key}_tab"] = tab
                st.rerun()
        
        st.divider()
        
        # 選択されたタブの内容を表示
        if st.session_state[f"{self.key}_tab"] == "overview":
            self._render_overview_tab()
        elif st.session_state[f"{self.key}_tab"] == "data_issues":
            self._render_data_issues_tab()
        elif st.session_state[f"{self.key}_tab"] == "spatial_issues":
            self._render_spatial_issues_tab()
        elif st.session_state[f"{self.key}_tab"] == "temporal_issues":
            self._render_temporal_issues_tab()
        elif st.session_state[f"{self.key}_tab"] == "fixes":
            self._render_fixes_tab()
        elif st.session_state[f"{self.key}_tab"] == "report":
            self._render_report_tab()
        
        # 選択された修正情報を含む状態を返す
        return {
            "status": "rendered",
            "selected_tab": st.session_state[f"{self.key}_tab"],
            "selected_issue": st.session_state[f"{self.key}_selected_issue"],
            "auto_fixes": st.session_state[f"{self.key}_auto_fixes"]
        }
    
    def _render_overview_tab(self) -> None:
        """データ検証の概要タブをレンダリング"""
        st.header("データ品質概要")
        
        # 品質スコアの表示
        quality_score = self.visualization.calculate_quality_score()
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.metric("総合品質スコア", f"{quality_score:.1f}/10.0")
            
            # スコアに基づく評価
            if quality_score >= 8.0:
                st.success("データ品質は優れています")
            elif quality_score >= 6.0:
                st.info("データ品質は良好です")
            elif quality_score >= 4.0:
                st.warning("データ品質に改善の余地があります")
            else:
                st.error("データ品質に重大な問題があります")
        
        with col2:
            # 品質スコアの視覚化
            fig = self.visualization.generate_quality_gauge(quality_score)
            st.plotly_chart(fig, use_container_width=True)
        
        with col3:
            # 問題サマリの表示
            issues_summary = self.visualization.get_issues_summary()
            
            total_issues = issues_summary["total_issues"]
            st.metric("検出された問題", total_issues)
            
            if total_issues > 0:
                st.write(f"- エラー: {issues_summary['error_count']}")
                st.write(f"- 警告: {issues_summary['warning_count']}")
                st.write(f"- 情報: {issues_summary['info_count']}")
                
        # 質の詳細スコア
        st.subheader("品質カテゴリ別スコア")
        quality_categories = self.visualization.get_quality_categories()
        
        # カテゴリ別バーチャートの表示
        st.bar_chart(quality_categories)
        
        # レポート生成ボタン
        if st.button("詳細レポートを生成", key=f"{self.key}_generate_report"):
            report_data = self.visualization.generate_full_report()
            # レポートデータをセッションに保存
            st.session_state[f"{self.key}_report_data"] = report_data
            st.session_state[f"{self.key}_tab"] = "report"
            st.rerun()
    
    def _highlight_problem_cells(self, df: pd.DataFrame, problem_info: List[Dict[str, Any]]) -> pd.DataFrame.style:
        """
        問題のあるセルをハイライト表示するスタイルを適用
        
        Parameters
        ----------
        df : pd.DataFrame
            スタイルを適用するデータフレーム
        problem_info : List[Dict[str, Any]]
            問題情報のリスト
            
        Returns
        -------
        pd.DataFrame.style
            スタイル適用済みのデータフレーム
        """
        # デフォルトスタイルを設定
        styler = df.style
        
        # 問題ごとにスタイルを適用
        for problem in problem_info:
            row_idx = problem["index"]
            col_name = problem["column"]
            problem_type = problem.get("problem_type", "other")
            severity = problem.get("severity", "info")
            
            # カラムが存在するか確認（インデックスが範囲内か確認）
            if row_idx >= 0 and row_idx < len(df) and col_name in df.columns:
                # 問題タイプに応じた色を取得
                color = self.HIGHLIGHT_COLORS.get(problem_type, "#f0f0f0")  # デフォルトは薄いグレー
                
                # 重要度に応じた不透明度を適用
                opacity = self.SEVERITY_OPACITY.get(severity, 0.5)
                
                # 背景色とスタイルの定義
                background_color = f"rgba({int(int(color[1:3], 16)*opacity)}, {int(int(color[3:5], 16)*opacity)}, {int(int(color[5:7], 16)*opacity)}, {opacity})"
                
                # セルスタイルの適用
                styler = styler.applymap(
                    lambda _: f"background-color: {background_color}; font-weight: bold;",
                    subset=pd.IndexSlice[row_idx:row_idx, col_name:col_name]
                )
                
                # 問題カウントに基づく行全体の背景色も設定
                row_style = f"background-color: rgba(240, 240, 240, 0.2);"
                styler = styler.apply(
                    lambda _: [row_style if i == row_idx else "" for i in range(len(df))],
                    axis=1
                )
                
        return styler
    
    def _create_problem_navigation(self, problem_info: List[Dict[str, Any]]) -> None:
        """
        問題箇所へのナビゲーションUI要素を作成
        
        Parameters
        ----------
        problem_info : List[Dict[str, Any]]
            問題情報のリスト
        """
        # セッション状態の初期化
        if f"{self.key}_problem_filter_type" not in st.session_state:
            st.session_state[f"{self.key}_problem_filter_type"] = "すべて"
        if f"{self.key}_problem_filter_severity" not in st.session_state:
            st.session_state[f"{self.key}_problem_filter_severity"] = "すべて"
        if f"{self.key}_problem_filter_column" not in st.session_state:
            st.session_state[f"{self.key}_problem_filter_column"] = "すべて"
        if f"{self.key}_current_problem_index" not in st.session_state:
            st.session_state[f"{self.key}_current_problem_index"] = 0
            
        # 問題タイプ、重要度、カラムのリストを生成
        problem_types = ["すべて"] + list(set([p.get("problem_type", "その他") for p in problem_info]))
        severities = ["すべて", "error", "warning", "info"]
        columns = ["すべて"] + list(set([p["column"] for p in problem_info]))
        
        # フィルタリングセクション
        st.subheader("問題フィルタ")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_type = st.selectbox(
                "問題タイプ",
                options=problem_types,
                key=f"{self.key}_problem_type_filter"
            )
            st.session_state[f"{self.key}_problem_filter_type"] = selected_type
            
        with col2:
            selected_severity = st.selectbox(
                "重要度",
                options=severities,
                key=f"{self.key}_problem_severity_filter"
            )
            st.session_state[f"{self.key}_problem_filter_severity"] = selected_severity
            
        with col3:
            selected_column = st.selectbox(
                "カラム",
                options=columns,
                key=f"{self.key}_problem_column_filter"
            )
            st.session_state[f"{self.key}_problem_filter_column"] = selected_column
        
        # フィルタリングされた問題リストを生成
        filtered_problems = problem_info.copy()
        
        if selected_type != "すべて":
            filtered_problems = [p for p in filtered_problems if p.get("problem_type", "その他") == selected_type]
            
        if selected_severity != "すべて":
            filtered_problems = [p for p in filtered_problems if p.get("severity", "info") == selected_severity]
            
        if selected_column != "すべて":
            filtered_problems = [p for p in filtered_problems if p["column"] == selected_column]
        
        # フィルタリング結果の表示
        st.write(f"**フィルタ後の問題件数:** {len(filtered_problems)}件")
        
        # 問題が存在する場合にナビゲーションを表示
        if filtered_problems:
            # 現在のインデックスをフィルタリング後のリストの範囲内に調整
            current_index = st.session_state[f"{self.key}_current_problem_index"]
            current_index = min(current_index, len(filtered_problems) - 1)
            st.session_state[f"{self.key}_current_problem_index"] = current_index
            
            # ナビゲーションボタン
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                if st.button(
                    "◀ 前へ",
                    key=f"{self.key}_prev_problem",
                    disabled=current_index == 0
                ):
                    st.session_state[f"{self.key}_current_problem_index"] = max(0, current_index - 1)
                    st.rerun()
                    
            with col2:
                st.write(f"問題 {current_index + 1} / {len(filtered_problems)}")
                
            with col3:
                if st.button(
                    "次へ ▶",
                    key=f"{self.key}_next_problem",
                    disabled=current_index >= len(filtered_problems) - 1
                ):
                    st.session_state[f"{self.key}_current_problem_index"] = min(
                        len(filtered_problems) - 1,
                        current_index + 1
                    )
                    st.rerun()
            
            # 現在選択されている問題の詳細表示
            current_problem = filtered_problems[current_index]
            st.session_state[f"{self.key}_selected_issue"] = current_problem
            
            self._show_problem_detail_popup(current_problem)
        else:
            st.info("フィルタ条件に一致する問題が見つかりませんでした。")
    
    def _show_problem_detail_popup(self, problem_info: Dict[str, Any]) -> None:
        """
        問題の詳細情報ポップアップを表示
        
        Parameters
        ----------
        problem_info : Dict[str, Any]
            表示する問題の詳細情報
        """
        # 問題情報の表示
        with st.expander("問題の詳細情報", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**問題タイプ:** {problem_info.get('problem_type', 'その他')}")
                st.markdown(f"**カラム:** {problem_info['column']}")
                st.markdown(f"**インデックス:** {problem_info['index']}")
                st.markdown(f"**重要度:** {problem_info.get('severity', 'info')}")
                
            with col2:
                st.markdown(f"**説明:** {problem_info.get('description', '詳細情報なし')}")
                
                # 問題値の表示
                value = problem_info.get('value', None)
                if value is not None:
                    st.markdown(f"**問題値:** {value}")
                
                # 有効範囲の表示
                valid_range = problem_info.get('valid_range', None)
                if valid_range is not None:
                    st.markdown(f"**有効範囲:** {valid_range[0]} ～ {valid_range[1]}")
            
            # 修正提案がある場合は表示
            fix_suggestions = problem_info.get('fix_suggestions', [])
            if fix_suggestions:
                st.subheader("修正提案")
                
                for i, suggestion in enumerate(fix_suggestions):
                    fix_type = suggestion.get('type', 'unknown')
                    fix_value = suggestion.get('value', None)
                    fix_description = suggestion.get('description', '説明なし')
                    
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**提案 {i+1}:** {fix_description}")
                    
                    with col2:
                        if fix_value is not None:
                            st.write(f"新しい値: {fix_value}")
                    
                    with col3:
                        if st.button(
                            "適用",
                            key=f"{self.key}_apply_fix_{i}",
                            type="primary",
                            use_container_width=True
                        ):
                            # 選択された修正を記録
                            st.session_state[f"{self.key}_auto_fixes"].append({
                                "problem": problem_info,
                                "fix": suggestion
                            })
                            
                            # コールバックがある場合は実行
                            if self.on_clean_data:
                                self.on_clean_data({
                                    "type": "single_fix",
                                    "problem": problem_info,
                                    "fix": suggestion
                                })
                            
                            st.success(f"修正が適用されました: {fix_description}")
                            st.rerun()
            
            # コンテキスト情報（周辺データ）の表示
            st.subheader("コンテキスト情報")
            
            # インデックスが有効範囲内か確認
            row_idx = problem_info['index']
            if 0 <= row_idx < len(self.container.data):
                # 前後2行を含めて表示（存在する場合）
                start_idx = max(0, row_idx - 2)
                end_idx = min(len(self.container.data) - 1, row_idx + 2)
                
                context_df = self.container.data.iloc[start_idx:end_idx + 1].copy()
                
                # 現在の行をハイライト
                context_styler = context_df.style.apply(
                    lambda x: ['background-color: #e6f7ff; font-weight: bold;' if i == row_idx - start_idx else '' 
                               for i in range(len(context_df))],
                    axis=0
                )
                
                st.dataframe(context_styler)
            else:
                st.warning(f"インデックス {row_idx} はデータの範囲外です。")
    
    def _render_data_issues_tab(self) -> None:
        """
        問題のあるデータを表示するタブを強化する
        
        ハイライト表示とインタラクティブ機能を追加
        """
        st.header("データ品質問題")
        
        # 問題のあるレコードを取得
        problem_records = self.visualization.get_problem_records_table()
        
        if problem_records.empty:
            st.success("データ品質問題は検出されませんでした。")
            return
        
        st.write(f"**検出された問題レコード:** {len(problem_records)}件")
        
        # 問題カテゴリ別の集計と視覚化
        st.subheader("問題タイプの分析")
        
        col1, col2 = st.columns(2)
        
        problem_info = self.visualization.get_problem_info()
        
        # 問題箇所へのナビゲーション機能を追加
        self._create_problem_navigation(problem_info)
        
        # 問題のあるデータテーブルの表示（ハイライト付き）
        st.subheader("問題箇所のハイライト表示")
        
        # 表示するデータの範囲を制限（パフォーマンスのため）
        max_rows = 1000
        if len(problem_records) > max_rows:
            st.warning(f"表示件数が多いため、先頭{max_rows}件のみ表示します。")
            display_df = problem_records.head(max_rows)
        else:
            display_df = problem_records.copy()
        
        # ハイライト表示を適用
        styled_df = self._highlight_problem_cells(display_df, problem_info)
        
        # データフレームの表示
        st.dataframe(styled_df, use_container_width=True)
        
        # 一括修正機能
        with st.expander("一括修正オプション"):
            st.write("複数の問題を一度に修正する場合は、以下のオプションから選択してください。")
            
            fix_options = [
                "範囲外の値をクリップ",
                "欠損値を補間",
                "重複を削除",
                "異常値を平滑化"
            ]
            
            selected_fix = st.selectbox(
                "一括修正方法",
                options=fix_options,
                key=f"{self.key}_batch_fix_method"
            )
            
            if st.button("選択した方法で一括修正", key=f"{self.key}_apply_batch_fix"):
                # 一括修正のコールバック
                if self.on_clean_data:
                    self.on_clean_data({
                        "type": "batch_fix",
                        "method": selected_fix
                    })
                    
                st.success(f"一括修正が適用されました: {selected_fix}")
                st.rerun()
    
    def _render_spatial_issues_tab(self) -> None:
        """空間的問題の表示タブをレンダリング"""
        st.header("空間的問題")
        
        # 空間的問題の検出結果を取得
        spatial_issues = self.visualization.get_spatial_issues()
        
        if not spatial_issues:
            st.success("空間的な問題は検出されませんでした。")
            return
        
        st.write(f"**検出された空間的問題:** {len(spatial_issues)}件")
        
        # 空間的問題の地図表示
        st.subheader("空間的問題の視覚化")
        
        map_fig = self.visualization.generate_spatial_issues_map()
        st.plotly_chart(map_fig, use_container_width=True)
        
        # 空間的問題の一覧表示
        st.subheader("空間的問題の一覧")
        
        # 問題情報をデータフレームに変換
        spatial_df = pd.DataFrame(spatial_issues)
        
        # 必要な列のみ選択
        if not spatial_df.empty:
            display_cols = ['index', 'problem_type', 'severity', 'description', 'latitude', 'longitude']
            display_cols = [col for col in display_cols if col in spatial_df.columns]
            st.dataframe(spatial_df[display_cols], use_container_width=True)
    
    def _render_temporal_issues_tab(self) -> None:
        """時間的問題の表示タブをレンダリング"""
        st.header("時間的問題")
        
        # 時間的問題の検出結果を取得
        temporal_issues = self.visualization.get_temporal_issues()
        
        if not temporal_issues:
            st.success("時間的な問題は検出されませんでした。")
            return
        
        st.write(f"**検出された時間的問題:** {len(temporal_issues)}件")
        
        # 時間的問題のタイムライン表示
        st.subheader("時間的問題の視覚化")
        
        timeline_fig = self.visualization.generate_temporal_issues_timeline()
        st.plotly_chart(timeline_fig, use_container_width=True)
        
        # 時間的問題の一覧表示
        st.subheader("時間的問題の一覧")
        
        # 問題情報をデータフレームに変換
        temporal_df = pd.DataFrame(temporal_issues)
        
        # 必要な列のみ選択
        if not temporal_df.empty:
            display_cols = ['index', 'problem_type', 'severity', 'description', 'timestamp']
            display_cols = [col for col in display_cols if col in temporal_df.columns]
            st.dataframe(temporal_df[display_cols], use_container_width=True)
    
    def _render_fixes_tab(self) -> None:
        """修正候補の表示タブをレンダリング"""
        st.header("修正候補")
        
        # 自動修正候補の取得
        auto_fixes = self.visualization.get_auto_fixes()
        
        if not auto_fixes:
            st.info("自動修正候補はありません。")
            return
        
        st.write(f"**利用可能な自動修正候補:** {len(auto_fixes)}件")
        
        # 修正候補のカテゴリ別集計
        fix_types = {}
        for fix in auto_fixes:
            fix_type = fix.get("type", "その他")
            if fix_type in fix_types:
                fix_types[fix_type] += 1
            else:
                fix_types[fix_type] = 1
        
        # カテゴリ別の集計を表示
        st.subheader("修正タイプ別の集計")
        
        fix_type_df = pd.DataFrame({
            "修正タイプ": list(fix_types.keys()),
            "件数": list(fix_types.values())
        })
        
        st.bar_chart(fix_type_df.set_index("修正タイプ"))
        
        # 修正候補の一覧表示
        st.subheader("修正候補の一覧")
        
        for i, fix in enumerate(auto_fixes):
            with st.expander(f"修正候補 {i+1}: {fix.get('description', '詳細なし')}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**問題詳細:**")
                    st.write(f"- タイプ: {fix.get('problem_type', 'その他')}")
                    st.write(f"- 対象: {fix.get('target', '不明')}")
                    st.write(f"- 影響範囲: {fix.get('scope', '不明')}")
                
                with col2:
                    st.write("**修正内容:**")
                    st.write(f"- 修正方法: {fix.get('method', '不明')}")
                    st.write(f"- 修正値: {fix.get('value', '自動計算')}")
                    
                    # 適用ボタン
                    if st.button("この修正を適用", key=f"{self.key}_apply_fix_{i}"):
                        # コールバックがある場合は実行
                        if self.on_clean_data:
                            self.on_clean_data({
                                "type": "auto_fix",
                                "fix": fix
                            })
                            
                        st.success("修正を適用しました。")
                        st.rerun()
    
    def _render_report_tab(self) -> None:
        """レポートタブをレンダリング"""
        st.header("データ品質レポート")
        
        # レポートデータがセッションに保存されているか確認
        if f"{self.key}_report_data" not in st.session_state:
            # レポートデータがない場合は生成
            report_data = self.visualization.generate_full_report()
            st.session_state[f"{self.key}_report_data"] = report_data
        else:
            # セッションからレポートデータを取得
            report_data = st.session_state[f"{self.key}_report_data"]
        
        # レポートの表示
        st.subheader("概要")
        st.write(report_data["summary"])
        
        st.subheader("データ品質スコア")
        st.write(f"**総合スコア:** {report_data['overall_score']:.1f}/10.0")
        
        # カテゴリ別スコアの表示
        category_scores = report_data["category_scores"]
        category_df = pd.DataFrame({
            "カテゴリ": list(category_scores.keys()),
            "スコア": list(category_scores.values())
        })
        
        st.bar_chart(category_df.set_index("カテゴリ"))
        
        # 詳細な問題リスト
        st.subheader("検出された問題の詳細")
        
        issues_df = pd.DataFrame(report_data["issues"])
        if not issues_df.empty:
            st.dataframe(issues_df, use_container_width=True)
        else:
            st.success("問題は検出されませんでした。")
        
        # エクスポートオプション
        st.subheader("レポートのエクスポート")
        
        export_format = st.selectbox(
            "エクスポート形式",
            options=["PDF", "HTML", "CSV"],
            key=f"{self.key}_export_format"
        )
        
        if st.button("レポートをエクスポート", key=f"{self.key}_export_report"):
            # エクスポートコールバックがある場合は実行
            if self.on_export:
                self.on_export(export_format.lower())
                st.success(f"レポートを{export_format}形式でエクスポートしました。")
            else:
                st.warning("エクスポート機能は実装されていません。")
