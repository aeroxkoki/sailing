# -*- coding: utf-8 -*-
"""
ui.integrated.pages.data_validation

データ検証ページ - インポートされたデータの品質を検証し、問題を修正する機能
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
import json
import io
import time

# セッション状態キー
SESSION_STATE_KEY = "data_validation_state"

def initialize_session_state():
    """セッション状態を初期化"""
    if SESSION_STATE_KEY not in st.session_state:
        st.session_state[SESSION_STATE_KEY] = {
            "container": None,
            "validation_results": None,
            "metrics_calculator": None,
            "problematic_indices": {},
            "selected_problem_type": None,
            "selected_index": None,
            "auto_fix_applied": False,
            "fixed_container": None
        }

def render_page():
    """データ検証ページをレンダリング"""
    st.title("データ検証")
    
    # セッション状態を初期化
    initialize_session_state()
    
    # メインコンテンツ
    st.write("""
    インポートされたデータの品質を検証し、問題を検出・修正します。
    データの信頼性を確保するためのステップです。
    """)
    
    # インポートコントローラーを取得
    from ui.integrated.controllers.import_controller import ImportController
    controller = ImportController()
    
    # アクティブなコンテナの取得
    state = st.session_state[SESSION_STATE_KEY]
    container = controller.get_imported_container()
    
    if container is not None:
        # コンテナが変わった場合は状態をリセット
        if state.get("container") is not container:
            state["container"] = container
            state["validation_results"] = None
            state["metrics_calculator"] = None
            state["problematic_indices"] = {}
            state["selected_problem_type"] = None
            state["selected_index"] = None
            state["auto_fix_applied"] = False
            state["fixed_container"] = None
        
        # 検証実行ボタン
        if st.button("データ検証を実行", key="run_validation_btn", type="primary", disabled=state.get("validation_results") is not None):
            with st.spinner("データを検証しています..."):
                # 検証の実行
                validation_results = controller.run_validation_after_import(container)
                state["validation_results"] = validation_results
                
                # 品質メトリクス計算機の初期化
                from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
                metrics_calculator = QualityMetricsCalculator(container)
                metrics_calculator.calculate_all_metrics()
                state["metrics_calculator"] = metrics_calculator
                
                # 問題のあるインデックスを取得
                state["problematic_indices"] = metrics_calculator.problematic_indices
        
        # 検証結果がある場合は表示
        if state.get("validation_results") is not None:
            render_validation_results()
    else:
        # コンテナがない場合のメッセージ
        st.info("検証するデータがありません。まずデータをインポートしてください。")
        
        if st.button("データインポートページへ", key="goto_import_btn"):
            st.session_state.current_page = "data_import"
            st.rerun()

def render_validation_results():
    """検証結果の表示"""
    state = st.session_state[SESSION_STATE_KEY]
    validation_passed, validation_details = state["validation_results"]
    metrics_calculator = state["metrics_calculator"]
    
    # 検証サマリーコンポーネントの表示
    with st.container():
        from ui.components.validation.validation_summary import ValidationSummary
        validation_summary = ValidationSummary(
            metrics_calculator=metrics_calculator,
            container=state["container"],
            key_prefix="validation_summary",
            on_fix_button_click=lambda: auto_fix_problems()
        )
        validation_summary.render()
    
    # 問題カテゴリごとの詳細表示
    render_problem_categories()
    
    # 問題修正UI
    if state.get("selected_problem_type") and state.get("selected_index") is not None:
        render_problem_correction()
    
    # 検証後のナビゲーションオプション
    st.subheader("次のステップ")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("分析ページへ進む", key="goto_analysis_btn", use_container_width=True):
            st.session_state.current_page = "wind_analysis"
            st.rerun()
    
    with col2:
        if st.button("プロジェクト管理へ戻る", key="goto_projects_btn", use_container_width=True):
            st.session_state.current_page = "projects"
            st.rerun()
    
    with col3:
        if st.button("データインポートに戻る", key="back_to_import_btn", use_container_width=True):
            st.session_state.current_page = "data_import"
            st.rerun()

def render_problem_categories():
    """問題カテゴリごとの詳細表示"""
    state = st.session_state[SESSION_STATE_KEY]
    problematic_indices = state["problematic_indices"]
    container = state["container"]
    
    st.header("検出された問題")
    
    # 問題がない場合
    if not problematic_indices or not any(len(indices) for indices in problematic_indices.values() if isinstance(indices, list)):
        st.success("問題は検出されませんでした。データは良好な状態です。")
        return
    
    # 問題タイプごとのタブを表示
    problem_types = {
        "missing_data": "欠損値",
        "out_of_range": "範囲外の値",
        "duplicates": "重複データ",
        "spatial_anomalies": "空間的異常",
        "temporal_anomalies": "時間的異常"
    }
    
    # 各問題タイプの件数を取得
    problem_counts = {
        problem_type: len(indices) 
        for problem_type, indices in problematic_indices.items() 
        if problem_type != "all" and isinstance(indices, list) and len(indices) > 0
    }
    
    # 問題タイプのリストを作成（件数付き）
    problem_tabs = {
        problem_type: f"{problem_types.get(problem_type, problem_type)} ({count}件)"
        for problem_type, count in problem_counts.items()
        if count > 0
    }
    
    if not problem_tabs:
        st.info("修正が必要な問題は検出されませんでした。")
        return
    
    # タブを作成
    tab_list = list(problem_tabs.keys())
    tab_labels = list(problem_tabs.values())
    
    # 選択されているタブのインデックスを決定
    selected_tab_index = 0
    if state.get("selected_problem_type") in tab_list:
        selected_tab_index = tab_list.index(state["selected_problem_type"])
    
    tabs = st.tabs(tab_labels)
    
    # 各タブの内容を表示
    for i, (problem_type, tab) in enumerate(zip(tab_list, tabs)):
        with tab:
            indices = problematic_indices[problem_type]
            if indices and len(indices) > 0:
                render_problem_list(problem_type, indices)
            else:
                st.info(f"{problem_types.get(problem_type, problem_type)}の問題は検出されませんでした。")
    
    # 選択されたタブに基づいて問題タイプを更新
    state["selected_problem_type"] = tab_list[selected_tab_index]

def render_problem_list(problem_type: str, indices: List[int]):
    """問題リストの表示"""
    state = st.session_state[SESSION_STATE_KEY]
    container = state["container"]
    df = container.data
    
    # 問題タイプの日本語名
    problem_type_names = {
        "missing_data": "欠損値",
        "out_of_range": "範囲外の値",
        "duplicates": "重複データ",
        "spatial_anomalies": "空間的異常",
        "temporal_anomalies": "時間的異常"
    }
    
    # 問題タイプに応じた説明
    problem_descriptions = {
        "missing_data": "データ内の欠損値（NaN）は、分析の質と信頼性に影響します。補間や適切な値での置換が必要です。",
        "out_of_range": "通常の範囲から逸脱した値は、センサーエラーや記録ミスの可能性があります。適切な範囲内に修正する必要があります。",
        "duplicates": "重複したデータポイントは分析結果を歪める可能性があります。重複の除去または調整が必要です。",
        "spatial_anomalies": "位置データの急激な変化や不自然な移動は、GPSエラーの可能性があります。スムージングや補間が必要です。",
        "temporal_anomalies": "時間順序の問題や不自然な時間間隔は、記録システムの問題を示している可能性があります。修正が必要です。"
    }
    
    # 問題の説明を表示
    st.info(problem_descriptions.get(problem_type, "データ検証で検出された問題です。"))
    
    # 問題のデータを表示
    if len(indices) > 100:
        st.warning(f"多数の問題が検出されました（{len(indices)}件）。最初の100件のみ表示します。")
        display_indices = indices[:100]
    else:
        display_indices = indices
    
    # 問題データの表示
    problem_df = df.iloc[display_indices].copy()
    
    # インデックスを保持して表示
    problem_df['row_index'] = display_indices
    
    # 問題タイプに応じたハイライト関数
    def highlight_problem_cells(row):
        """問題のセルをハイライト"""
        styles = [''] * len(row)
        
        if problem_type == "missing_data":
            # 欠損値をハイライト
            for i, v in enumerate(row):
                if pd.isna(v):
                    styles[i] = 'background-color: #ffcccc'
        
        elif problem_type == "out_of_range":
            # 範囲外の値の場合、特定のカラムをハイライト
            highlight_cols = ["speed", "course", "latitude", "longitude"]
            for col in highlight_cols:
                if col in problem_df.columns:
                    col_idx = problem_df.columns.get_loc(col)
                    styles[col_idx] = 'background-color: #ffcccc'
        
        elif problem_type == "duplicates":
            # 重複の場合、タイムスタンプをハイライト
            if "timestamp" in problem_df.columns:
                ts_idx = problem_df.columns.get_loc("timestamp")
                styles[ts_idx] = 'background-color: #ffcccc'
        
        elif problem_type == "spatial_anomalies":
            # 空間異常の場合、位置情報をハイライト
            highlight_cols = ["latitude", "longitude"]
            for col in highlight_cols:
                if col in problem_df.columns:
                    col_idx = problem_df.columns.get_loc(col)
                    styles[col_idx] = 'background-color: #ffcccc'
        
        elif problem_type == "temporal_anomalies":
            # 時間異常の場合、タイムスタンプをハイライト
            if "timestamp" in problem_df.columns:
                ts_idx = problem_df.columns.get_loc("timestamp")
                styles[ts_idx] = 'background-color: #ffcccc'
        
        return styles
    
    # 列がタイムスタンプの場合、読みやすい形式に変換
    if "timestamp" in problem_df.columns and pd.api.types.is_datetime64_any_dtype(problem_df["timestamp"]):
        problem_df["timestamp"] = problem_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    
    # 選択可能なデータフレームを表示
    st.dataframe(
        problem_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "row_index": st.column_config.Column(
                "行番号",
                help="データセット内の行インデックス",
                width="small"
            )
        }
    )
    
    # 問題の行を選択
    selected_row = st.selectbox(
        "修正する問題の行を選択してください:",
        options=display_indices,
        format_func=lambda x: f"行 {x}",
        key=f"select_row_{problem_type}"
    )
    
    # 選択された行をセッション状態に保存
    if selected_row is not None:
        state["selected_index"] = selected_row

def render_problem_correction():
    """問題修正UIの表示"""
    state = st.session_state[SESSION_STATE_KEY]
    container = state["container"]
    problem_type = state["selected_problem_type"]
    selected_index = state["selected_index"]
    
    # 問題データを取得
    df = container.data
    problem_row = df.iloc[selected_index].copy()
    
    st.header("問題の修正")
    
    # 問題タイプに応じた修正UI
    if problem_type == "missing_data":
        render_missing_data_correction(problem_row, selected_index)
    elif problem_type == "out_of_range":
        render_out_of_range_correction(problem_row, selected_index)
    elif problem_type == "duplicates":
        render_duplicate_correction(problem_row, selected_index)
    elif problem_type == "spatial_anomalies":
        render_spatial_anomaly_correction(problem_row, selected_index)
    elif problem_type == "temporal_anomalies":
        render_temporal_anomaly_correction(problem_row, selected_index)
    else:
        st.warning("この問題タイプの修正UIはまだ実装されていません。")

def render_missing_data_correction(row, index):
    """欠損値修正UIの表示"""
    state = st.session_state[SESSION_STATE_KEY]
    container = state["container"]
    df = container.data
    
    st.subheader("欠損値の修正")
    
    # 欠損値を含むカラムを特定
    missing_cols = [col for col in row.index if pd.isna(row[col])]
    
    if not missing_cols:
        st.info("この行には欠損値がありません。")
        return
    
    st.write(f"行 {index} には以下のカラムに欠損値があります:")
    
    # 各欠損値に対する修正オプション
    corrections = {}
    
    for col in missing_cols:
        st.write(f"**{col}**:")
        
        # 前後の値を取得して補間のオプションを提案
        if index > 0 and index < len(df) - 1:
            prev_value = df.iloc[index-1][col]
            next_value = df.iloc[index+1][col]
            
            # 前後の値が数値で欠損していない場合、線形補間値を計算
            if (not pd.isna(prev_value) and not pd.isna(next_value) and 
                pd.api.types.is_numeric_dtype(df[col])):
                interp_value = (prev_value + next_value) / 2
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"前の値: {prev_value}")
                
                with col2:
                    st.write(f"補間値: {interp_value:.4f}")
                
                with col3:
                    st.write(f"次の値: {next_value}")
                
                # 修正方法の選択
                correction_method = st.radio(
                    "修正方法を選択:",
                    options=["線形補間", "前の値を使用", "次の値を使用", "手動入力"],
                    key=f"correction_method_{col}",
                    horizontal=True
                )
                
                if correction_method == "線形補間":
                    corrections[col] = interp_value
                elif correction_method == "前の値を使用":
                    corrections[col] = prev_value
                elif correction_method == "次の値を使用":
                    corrections[col] = next_value
                else:  # 手動入力
                    manual_value = st.number_input(
                        "値を入力:",
                        value=float(interp_value) if not pd.isna(interp_value) else 0.0,
                        key=f"manual_value_{col}"
                    )
                    corrections[col] = manual_value
            else:
                # 数値以外または前後の値が欠損している場合
                correction_method = st.radio(
                    "修正方法を選択:",
                    options=["削除", "手動入力"],
                    key=f"correction_method_{col}",
                    horizontal=True
                )
                
                if correction_method == "手動入力":
                    # カラムの型に応じた入力UI
                    if pd.api.types.is_numeric_dtype(df[col]):
                        manual_value = st.number_input(
                            "値を入力:",
                            value=0.0,
                            key=f"manual_value_{col}"
                        )
                    else:
                        manual_value = st.text_input(
                            "値を入力:",
                            value="",
                            key=f"manual_value_{col}"
                        )
                    
                    corrections[col] = manual_value
                else:  # 削除を選択
                    corrections[col] = None  # Noneは行の削除を示す
        else:
            # 最初または最後の行の場合
            st.warning("この行は最初または最後の行のため、補間オプションが限られています。")
            
            # 修正方法の選択
            correction_method = st.radio(
                "修正方法を選択:",
                options=["削除", "手動入力"],
                key=f"correction_method_{col}",
                horizontal=True
            )
            
            if correction_method == "手動入力":
                # カラムの型に応じた入力UI
                if pd.api.types.is_numeric_dtype(df[col]):
                    manual_value = st.number_input(
                        "値を入力:",
                        value=0.0,
                        key=f"manual_value_{col}"
                    )
                else:
                    manual_value = st.text_input(
                        "値を入力:",
                        value="",
                        key=f"manual_value_{col}"
                    )
                
                corrections[col] = manual_value
            else:  # 削除を選択
                corrections[col] = None  # Noneは行の削除を示す
    
    # 修正を適用するボタン
    if st.button("修正を適用", key="apply_missing_correction"):
        modified_df = df.copy()
        
        # 修正を適用
        delete_row = False
        for col, value in corrections.items():
            if value is None:
                delete_row = True
                break
            else:
                modified_df.at[index, col] = value
        
        if delete_row:
            # 行を削除
            modified_df = modified_df.drop(index).reset_index(drop=True)
            st.success(f"行 {index} を削除しました。")
        else:
            st.success(f"行 {index} の欠損値を修正しました。")
        
        # 修正後のコンテナを更新
        update_data_container(modified_df)
        
        # 検証結果の更新
        st.info("データが更新されました。再検証を実行してください。")
        
        # 検証結果をリセット
        state["validation_results"] = None

def render_out_of_range_correction(row, index):
    """範囲外の値修正UIの表示"""
    state = st.session_state[SESSION_STATE_KEY]
    container = state["container"]
    df = container.data
    metrics_calculator = state["metrics_calculator"]
    
    st.subheader("範囲外の値の修正")
    
    # 範囲外の値を含むカラムとその範囲を特定
    problem_cols = []
    ranges = {}
    
    numerical_cols = df.select_dtypes(include=np.number).columns
    
    for col in numerical_cols:
        # メトリクス計算機から適切な範囲を取得（実装に応じて変更）
        try:
            # 簡易的な範囲計算（本来はメトリクス計算機から取得）
            q1 = df[col].quantile(0.05)
            q3 = df[col].quantile(0.95)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            if row[col] < lower_bound or row[col] > upper_bound:
                problem_cols.append(col)
                ranges[col] = (lower_bound, upper_bound)
        except:
            continue
    
    if not problem_cols:
        st.info("この行には範囲外の値はありません。")
        return
    
    st.write(f"行 {index} には以下のカラムに範囲外の値があります:")
    
    # 各範囲外の値に対する修正オプション
    corrections = {}
    
    for col in problem_cols:
        lower_bound, upper_bound = ranges[col]
        current_value = row[col]
        
        st.write(f"**{col}**:")
        st.write(f"現在の値: {current_value} (許容範囲: {lower_bound:.4f} ~ {upper_bound:.4f})")
        
        # 修正方法の選択
        correction_method = st.radio(
            "修正方法を選択:",
            options=["範囲内にクリップ", "前後の値から補間", "手動入力"],
            key=f"correction_method_{col}",
            horizontal=True
        )
        
        if correction_method == "範囲内にクリップ":
            # 最小値か最大値にクリップ
            if current_value < lower_bound:
                corrections[col] = lower_bound
                st.write(f"修正後の値: {lower_bound}")
            else:
                corrections[col] = upper_bound
                st.write(f"修正後の値: {upper_bound}")
        
        elif correction_method == "前後の値から補間":
            # 前後の値を取得して補間
            if index > 0 and index < len(df) - 1:
                prev_value = df.iloc[index-1][col]
                next_value = df.iloc[index+1][col]
                interp_value = (prev_value + next_value) / 2
                
                # 補間値が範囲内かチェック
                if interp_value < lower_bound:
                    interp_value = lower_bound
                elif interp_value > upper_bound:
                    interp_value = upper_bound
                
                corrections[col] = interp_value
                st.write(f"修正後の値: {interp_value}")
            else:
                st.warning("この行は最初または最後の行のため、補間できません。範囲内にクリップします。")
                # 最小値か最大値にクリップ
                if current_value < lower_bound:
                    corrections[col] = lower_bound
                    st.write(f"修正後の値: {lower_bound}")
                else:
                    corrections[col] = upper_bound
                    st.write(f"修正後の値: {upper_bound}")
        
        else:  # 手動入力
            # 範囲内の値を提案
            suggested_value = min(max(current_value, lower_bound), upper_bound)
            
            manual_value = st.number_input(
                "値を入力:",
                value=float(suggested_value),
                key=f"manual_value_{col}"
            )
            
            # 入力値が範囲内かチェック
            if manual_value < lower_bound or manual_value > upper_bound:
                st.warning("入力された値は依然として範囲外です。")
            
            corrections[col] = manual_value
    
    # 修正を適用するボタン
    if st.button("修正を適用", key="apply_range_correction"):
        modified_df = df.copy()
        
        # 修正を適用
        for col, value in corrections.items():
            modified_df.at[index, col] = value
        
        st.success(f"行 {index} の範囲外の値を修正しました。")
        
        # 修正後のコンテナを更新
        update_data_container(modified_df)
        
        # 検証結果の更新
        st.info("データが更新されました。再検証を実行してください。")
        
        # 検証結果をリセット
        state["validation_results"] = None

def render_duplicate_correction(row, index):
    """重複データ修正UIの表示"""
    state = st.session_state[SESSION_STATE_KEY]
    container = state["container"]
    df = container.data
    
    st.subheader("重複データの修正")
    
    # 重複を検出（タイムスタンプが同じ行を探す）
    timestamp_col = "timestamp"
    
    if timestamp_col not in df.columns:
        st.error("タイムスタンプ列がデータに存在しません。")
        return
    
    current_timestamp = row[timestamp_col]
    
    # 同じタイムスタンプを持つ行を検索
    duplicate_indices = df[df[timestamp_col] == current_timestamp].index.tolist()
    
    if len(duplicate_indices) <= 1:
        st.info("この行には重複がありません。")
        return
    
    st.write(f"行 {index} は以下の行と重複しています:")
    
    # 重複行の表示
    duplicate_df = df.iloc[duplicate_indices].copy()
    duplicate_df['row_index'] = duplicate_indices
    
    st.dataframe(
        duplicate_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "row_index": st.column_config.Column(
                "行番号",
                help="データセット内の行インデックス",
                width="small"
            )
        }
    )
    
    # 修正方法の選択
    correction_method = st.radio(
        "修正方法を選択:",
        options=["1つを残して削除", "タイムスタンプをオフセット", "手動マージ"],
        key="duplicate_correction_method",
        horizontal=True
    )
    
    if correction_method == "1つを残して削除":
        keep_index = st.selectbox(
            "保持する行を選択:",
            options=duplicate_indices,
            format_func=lambda x: f"行 {x}",
            key="keep_duplicate_index"
        )
        
        # 修正を適用するボタン
        if st.button("修正を適用", key="apply_duplicate_correction_delete"):
            modified_df = df.copy()
            
            # 選択した行以外の重複行を削除
            rows_to_delete = [idx for idx in duplicate_indices if idx != keep_index]
            modified_df = modified_df.drop(rows_to_delete).reset_index(drop=True)
            
            st.success(f"重複行を削除しました。行 {keep_index} を保持しました。")
            
            # 修正後のコンテナを更新
            update_data_container(modified_df)
            
            # 検証結果をリセット
            state["validation_results"] = None
    
    elif correction_method == "タイムスタンプをオフセット":
        offset_seconds = st.number_input(
            "オフセット秒数 (1, 2, 3, ...):",
            min_value=1,
            value=1,
            key="timestamp_offset_seconds"
        )
        
        # 修正を適用するボタン
        if st.button("修正を適用", key="apply_duplicate_correction_offset"):
            modified_df = df.copy()
            
            # タイムスタンプをオフセット
            for i, idx in enumerate(duplicate_indices[1:], 1):
                # i番目の重複行のタイムスタンプを i*offset_seconds 秒ずらす
                current_time = modified_df.at[idx, timestamp_col]
                
                if pd.api.types.is_datetime64_any_dtype(modified_df[timestamp_col]):
                    # datetime型の場合
                    from datetime import timedelta
                    new_time = current_time + timedelta(seconds=i*offset_seconds)
                else:
                    # 文字列型の場合（簡易的な処理）
                    st.warning("タイムスタンプが日時型ではありません。datetime型に変換して処理します。")
                    try:
                        temp_df = modified_df.copy()
                        temp_df[timestamp_col] = pd.to_datetime(temp_df[timestamp_col])
                        current_time = temp_df.at[idx, timestamp_col]
                        from datetime import timedelta
                        new_time = current_time + timedelta(seconds=i*offset_seconds)
                        # 元の形式に戻す
                        if isinstance(modified_df.at[idx, timestamp_col], str):
                            new_time = new_time.strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        st.error("タイムスタンプの変換に失敗しました。")
                        return
                
                modified_df.at[idx, timestamp_col] = new_time
            
            st.success(f"重複行のタイムスタンプをオフセットしました。")
            
            # 修正後のコンテナを更新
            update_data_container(modified_df)
            
            # 検証結果をリセット
            state["validation_results"] = None
    
    else:  # 手動マージ
        st.warning("手動マージ機能は現在実装中です。別の修正方法を選択してください。")

def render_spatial_anomaly_correction(row, index):
    """空間的異常修正UIの表示"""
    state = st.session_state[SESSION_STATE_KEY]
    container = state["container"]
    df = container.data
    
    st.subheader("空間的異常の修正")
    
    # 位置データの列を確認
    lat_col = "latitude"
    lon_col = "longitude"
    
    if lat_col not in df.columns or lon_col not in df.columns:
        st.error("位置データ（緯度・経度）の列がデータに存在しません。")
        return
    
    # 現在の位置と前後の位置を取得
    current_lat = row[lat_col]
    current_lon = row[lon_col]
    
    # 前後の行の取得
    prev_row = df.iloc[index-1] if index > 0 else None
    next_row = df.iloc[index+1] if index < len(df) - 1 else None
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if prev_row is not None:
            st.write("**前の位置:**")
            st.write(f"緯度: {prev_row[lat_col]}")
            st.write(f"経度: {prev_row[lon_col]}")
        else:
            st.write("**前の位置:** なし")
    
    with col2:
        st.write("**現在の位置:**")
        st.write(f"緯度: {current_lat}")
        st.write(f"経度: {current_lon}")
    
    with col3:
        if next_row is not None:
            st.write("**次の位置:**")
            st.write(f"緯度: {next_row[lat_col]}")
            st.write(f"経度: {next_row[lon_col]}")
        else:
            st.write("**次の位置:** なし")
    
    # マップ表示（可能であれば）
    # 注: ここでは簡易的なマップ表示を行っています
    try:
        map_data = []
        
        if prev_row is not None:
            map_data.append({"lat": prev_row[lat_col], "lon": prev_row[lon_col], "label": "前"})
        
        map_data.append({"lat": current_lat, "lon": current_lon, "label": "現在"})
        
        if next_row is not None:
            map_data.append({"lat": next_row[lat_col], "lon": next_row[lon_col], "label": "次"})
        
        map_df = pd.DataFrame(map_data)
        
        st.map(map_df.rename(columns={"lat": "latitude", "lon": "longitude"}))
    except:
        st.warning("マップの表示に失敗しました。")
    
    # 修正方法の選択
    correction_method = st.radio(
        "修正方法を選択:",
        options=["線形補間", "前の位置を使用", "次の位置を使用", "手動入力", "この行を削除"],
        key="spatial_correction_method",
        horizontal=True
    )
    
    new_lat = current_lat
    new_lon = current_lon
    delete_row = False
    
    if correction_method == "線形補間":
        if prev_row is not None and next_row is not None:
            new_lat = (prev_row[lat_col] + next_row[lat_col]) / 2
            new_lon = (prev_row[lon_col] + next_row[lon_col]) / 2
            
            st.write(f"補間後の位置: 緯度 {new_lat}, 経度 {new_lon}")
        else:
            st.warning("前後の位置データがないため、補間できません。")
    
    elif correction_method == "前の位置を使用":
        if prev_row is not None:
            new_lat = prev_row[lat_col]
            new_lon = prev_row[lon_col]
            
            st.write(f"修正後の位置: 緯度 {new_lat}, 経度 {new_lon}")
        else:
            st.warning("前の位置データがありません。")
    
    elif correction_method == "次の位置を使用":
        if next_row is not None:
            new_lat = next_row[lat_col]
            new_lon = next_row[lon_col]
            
            st.write(f"修正後の位置: 緯度 {new_lat}, 経度 {new_lon}")
        else:
            st.warning("次の位置データがありません。")
    
    elif correction_method == "手動入力":
        new_lat = st.number_input("新しい緯度:", value=float(current_lat), key="manual_lat")
        new_lon = st.number_input("新しい経度:", value=float(current_lon), key="manual_lon")
    
    elif correction_method == "この行を削除":
        delete_row = True
    
    # 修正を適用するボタン
    if st.button("修正を適用", key="apply_spatial_correction"):
        modified_df = df.copy()
        
        if delete_row:
            # 行を削除
            modified_df = modified_df.drop(index).reset_index(drop=True)
            st.success(f"行 {index} を削除しました。")
        else:
            # 位置を更新
            modified_df.at[index, lat_col] = new_lat
            modified_df.at[index, lon_col] = new_lon
            
            st.success(f"行 {index} の位置を修正しました。")
        
        # 修正後のコンテナを更新
        update_data_container(modified_df)
        
        # 検証結果をリセット
        state["validation_results"] = None

def render_temporal_anomaly_correction(row, index):
    """時間的異常修正UIの表示"""
    state = st.session_state[SESSION_STATE_KEY]
    container = state["container"]
    df = container.data
    
    st.subheader("時間的異常の修正")
    
    # タイムスタンプ列を確認
    timestamp_col = "timestamp"
    
    if timestamp_col not in df.columns:
        st.error("タイムスタンプ列がデータに存在しません。")
        return
    
    # 現在のタイムスタンプと前後のタイムスタンプを取得
    current_timestamp = row[timestamp_col]
    
    # 前後の行の取得
    prev_row = df.iloc[index-1] if index > 0 else None
    next_row = df.iloc[index+1] if index < len(df) - 1 else None
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if prev_row is not None:
            st.write("**前のタイムスタンプ:**")
            st.write(f"{prev_row[timestamp_col]}")
        else:
            st.write("**前のタイムスタンプ:** なし")
    
    with col2:
        st.write("**現在のタイムスタンプ:**")
        st.write(f"{current_timestamp}")
    
    with col3:
        if next_row is not None:
            st.write("**次のタイムスタンプ:**")
            st.write(f"{next_row[timestamp_col]}")
        else:
            st.write("**次のタイムスタンプ:** なし")
    
    # 問題の分析
    problems = []
    
    # タイムスタンプが日時型でない場合は変換
    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
        st.warning("タイムスタンプが日時型ではありません。分析のため一時的に変換します。")
        try:
            temp_df = df.copy()
            temp_df[timestamp_col] = pd.to_datetime(temp_df[timestamp_col])
            
            current_ts = temp_df.iloc[index][timestamp_col]
            prev_ts = temp_df.iloc[index-1][timestamp_col] if index > 0 else None
            next_ts = temp_df.iloc[index+1][timestamp_col] if index < len(temp_df) - 1 else None
        except:
            st.error("タイムスタンプの変換に失敗しました。")
            return
    else:
        current_ts = current_timestamp
        prev_ts = prev_row[timestamp_col] if prev_row is not None else None
        next_ts = next_row[timestamp_col] if next_row is not None else None
    
    # 時間の逆行をチェック
    if prev_ts is not None and current_ts < prev_ts:
        problems.append("時間の逆行: 現在のタイムスタンプが前のタイムスタンプよりも前になっています。")
    
    if next_ts is not None and current_ts > next_ts:
        problems.append("時間の逆行: 現在のタイムスタンプが次のタイムスタンプよりも後になっています。")
    
    # 時間間隔の異常をチェック
    if prev_ts is not None and next_ts is not None:
        interval_prev = (current_ts - prev_ts).total_seconds()
        interval_next = (next_ts - current_ts).total_seconds()
        
        # 通常の間隔を計算（データセット全体の平均）
        if pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
            avg_interval = df[timestamp_col].diff().mean().total_seconds()
        else:
            temp_df = df.copy()
            temp_df[timestamp_col] = pd.to_datetime(temp_df[timestamp_col])
            avg_interval = temp_df[timestamp_col].diff().mean().total_seconds()
        
        # 異常な間隔の検出（平均の10倍以上または1/10以下）
        if interval_prev > avg_interval * 10:
            problems.append(f"異常な時間間隔: 前のデータポイントとの間隔が大きすぎます ({interval_prev:.2f}秒)。")
        elif interval_prev < avg_interval / 10 and interval_prev > 0:
            problems.append(f"異常な時間間隔: 前のデータポイントとの間隔が小さすぎます ({interval_prev:.2f}秒)。")
        
        if interval_next > avg_interval * 10:
            problems.append(f"異常な時間間隔: 次のデータポイントとの間隔が大きすぎます ({interval_next:.2f}秒)。")
        elif interval_next < avg_interval / 10 and interval_next > 0:
            problems.append(f"異常な時間間隔: 次のデータポイントとの間隔が小さすぎます ({interval_next:.2f}秒)。")
    
    # 問題の表示
    if problems:
        st.warning("検出された時間的問題:")
        for problem in problems:
            st.write(f"- {problem}")
    else:
        st.info("具体的な時間的問題は検出されませんでした。")
    
    # 修正方法の選択
    correction_method = st.radio(
        "修正方法を選択:",
        options=["時間補間", "前後の中間に設定", "手動入力", "この行を削除"],
        key="temporal_correction_method",
        horizontal=True
    )
    
    new_timestamp = current_timestamp
    delete_row = False
    
    if correction_method == "時間補間":
        if prev_ts is not None and next_ts is not None:
            # 前後の中間のタイムスタンプを計算
            if pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
                from datetime import timedelta
                time_diff = (next_ts - prev_ts).total_seconds()
                mid_ts = prev_ts + timedelta(seconds=time_diff/2)
                new_timestamp = mid_ts
            else:
                st.warning("タイムスタンプの自動補間には日時型が必要です。手動で入力してください。")
        else:
            st.warning("前後のタイムスタンプがないため、補間できません。")
    
    elif correction_method == "前後の中間に設定":
        if prev_ts is not None and next_ts is not None:
            if pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
                from datetime import timedelta
                mid_ts = prev_ts + (next_ts - prev_ts) / 2
                new_timestamp = mid_ts
            else:
                st.warning("タイムスタンプの自動補間には日時型が必要です。手動で入力してください。")
        else:
            st.warning("前後のタイムスタンプがないため、中間点を計算できません。")
    
    elif correction_method == "手動入力":
        if pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
            import datetime
            default_date = pd.Timestamp(current_timestamp).date()
            default_time = pd.Timestamp(current_timestamp).time()
            
            date_input = st.date_input(
                "日付:",
                value=default_date,
                key="manual_date"
            )
            
            time_input = st.time_input(
                "時刻:",
                value=default_time,
                key="manual_time"
            )
            
            # 日付と時刻を結合
            new_timestamp = datetime.datetime.combine(date_input, time_input)
        else:
            new_timestamp = st.text_input(
                "新しいタイムスタンプ (YYYY-MM-DD HH:MM:SS):",
                value=str(current_timestamp),
                key="manual_timestamp"
            )
    
    elif correction_method == "この行を削除":
        delete_row = True
    
    # 修正を適用するボタン
    if st.button("修正を適用", key="apply_temporal_correction"):
        modified_df = df.copy()
        
        if delete_row:
            # 行を削除
            modified_df = modified_df.drop(index).reset_index(drop=True)
            st.success(f"行 {index} を削除しました。")
        else:
            # タイムスタンプを更新
            modified_df.at[index, timestamp_col] = new_timestamp
            
            st.success(f"行 {index} のタイムスタンプを修正しました。")
        
        # 修正後のコンテナを更新
        update_data_container(modified_df)
        
        # 検証結果をリセット
        state["validation_results"] = None

def auto_fix_problems():
    """問題の自動修正を実行"""
    state = st.session_state[SESSION_STATE_KEY]
    container = state["container"]
    
    if not container:
        st.error("修正するデータコンテナがありません。")
        return
    
    # 自動修正を適用
    st.write("### 問題の自動修正を実行中...")
    
    from sailing_data_processor.validation.correction import DataCorrector
    corrector = DataCorrector()
    
    # 自動修正の適用
    with st.spinner("データを修正しています..."):
        time.sleep(1)  # 処理を視覚化するための遅延
        fixed_container = corrector.auto_fix(container)
    
    # 修正結果の表示
    if fixed_container:
        st.success("自動修正が完了しました！")
        
        # 修正された行数を表示
        original_rows = len(container.data)
        fixed_rows = len(fixed_container.data)
        
        if original_rows != fixed_rows:
            st.info(f"{original_rows - fixed_rows}行のデータが削除されました。")
        
        # 修正後のコンテナを更新
        state["fixed_container"] = fixed_container
        state["container"] = fixed_container
        state["auto_fix_applied"] = True
        
        # インポートコントローラーにも反映
        from ui.integrated.controllers.import_controller import ImportController
        controller = ImportController()
        controller.set_imported_container(fixed_container)
        
        # 再検証を促す
        st.info("自動修正後のデータを検証するには、再度データ検証を実行してください。")
        
        # 検証結果をリセット
        state["validation_results"] = None
    else:
        st.error("自動修正に失敗しました。")

def update_data_container(df):
    """データコンテナの更新"""
    state = st.session_state[SESSION_STATE_KEY]
    container = state["container"]
    
    # 新しいデータフレームでコンテナを更新
    container.data = df
    
    # 修正されたコンテナを保存
    state["container"] = container
    
    # インポートコントローラーにも反映
    from ui.integrated.controllers.import_controller import ImportController
    controller = ImportController()
    controller.set_imported_container(container)

if __name__ == "__main__":
    render_page()
