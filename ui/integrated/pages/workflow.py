# -*- coding: utf-8 -*-
"""
ワークフロー管理ページ

このモジュールは分析ワークフローを管理するためのStreamlitページを提供します。
分析ワークフローの概要表示、ステップ実行制御、パラメータ調整などの機能を含みます。
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import logging
from typing import Dict, List, Any, Optional, Tuple

from sailing_data_processor.analysis.analysis_workflow import AnalysisWorkflowController, AnalysisStep, AnalysisStatus
from sailing_data_processor.analysis.analysis_parameters import ParametersManager, ParameterNamespace
from sailing_data_processor.analysis.analysis_cache import AnalysisCache
from ui.components.workflow_components import (
    workflow_step_indicator, workflow_progress_bar, parameter_adjustment_panel,
    step_execution_panel, result_display_panel, create_default_analysis_workflow
)

# ロガーの設定
logger = logging.getLogger(__name__)

def initialize_workflow_state(session_data: Dict[str, Any]) -> None:
    """
    ワークフローの状態を初期化する
    
    Parameters:
    -----------
    session_data : Dict[str, Any]
        セッションデータ
    """
    if 'workflow' not in st.session_state:
        if 'current_session_df' not in session_data or session_data['current_session_df'] is None:
            st.warning("分析するデータが選択されていません。プロジェクトからセッションを選択してください。")
            return
        
        # パラメータマネージャーの取得またはデフォルト作成
        params_manager = session_data.get('params_manager')
        if params_manager is None:
            params_manager = ParametersManager()
        
        # キャッシュの取得またはデフォルト作成
        cache = session_data.get('analysis_cache')
        if cache is None:
            cache = AnalysisCache()
        
        # セッションデータからデータフレームを取得
        df = session_data['current_session_df']
        
        # ワークフローの作成
        st.session_state.workflow = create_default_analysis_workflow(df, params_manager, cache)
        st.session_state.active_step_id = None
        st.session_state.active_tab = "workflow"
        
        logger.info("ワークフロー状態を初期化しました")


def workflow_main_view() -> None:
    """
    ワークフロー管理のメインビュー
    
    セッションを選択してワークフローを開始するための画面を提供します。
    """
    st.title("分析ワークフロー")
    
    # セッションデータの取得
    session_data = st.session_state.get('session_data', {})
    
    # 選択されたセッションの情報表示
    current_session = session_data.get('current_session')
    
    if current_session:
        st.subheader(f"選択中のセッション: {current_session.get('name', '名称未設定')}")
        
        # メタデータの表示
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("データポイント数", session_data.get('data_points', 0))
        
        with col2:
            # 開始時間と終了時間から期間を計算して表示
            start_time = session_data.get('start_time')
            end_time = session_data.get('end_time')
            
            if start_time and end_time:
                duration_seconds = (end_time - start_time).total_seconds()
                duration_str = f"{int(duration_seconds // 3600)}時間 {int((duration_seconds % 3600) // 60)}分"
                st.metric("走行時間", duration_str)
            else:
                st.metric("走行時間", "不明")
        
        with col3:
            # タグやカテゴリなどの表示
            tags = current_session.get('tags', [])
            if tags:
                st.metric("タグ", ", ".join(tags))
            else:
                st.metric("タグ", "なし")
        
        # ワークフロー状態の初期化
        initialize_workflow_state(session_data)
        
        # ワークフローが初期化されていれば表示
        if 'workflow' in st.session_state:
            display_workflow_panel()
    else:
        st.info("分析を開始するには、プロジェクトからセッションを選択してください。")
        
        # プロジェクトへのリンク
        st.write("1. [プロジェクト一覧](/project_list)でプロジェクトを選択")
        st.write("2. プロジェクト詳細で分析するセッションを選択")
        st.write("3. このページに戻って分析を開始")
        
        # サンプルデータの使用オプション
        if st.button("サンプルデータを使用", key="use_sample"):
            # サンプルデータの生成とセッションへの登録は別途実装
            st.info("サンプルデータ機能は現在準備中です。")


def display_workflow_panel() -> None:
    """
    ワークフローパネルの表示
    """
    # ワークフローの取得
    workflow = st.session_state.workflow
    
    # タブの作成
    tab_workflow, tab_params, tab_results = st.tabs([
        "ワークフロー実行", "パラメータ調整", "分析結果"
    ])
    
    # ワークフロー実行タブ
    with tab_workflow:
        display_workflow_execution_panel(workflow)
    
    # パラメータ調整タブ
    with tab_params:
        display_parameter_adjustment_panel(workflow)
    
    # 分析結果タブ
    with tab_results:
        display_results_panel(workflow)


def display_workflow_execution_panel(workflow: AnalysisWorkflowController) -> None:
    """
    ワークフロー実行パネルの表示
    
    Parameters:
    -----------
    workflow : AnalysisWorkflowController
        ワークフローコントローラー
    """
    st.header("ワークフロー実行")
    
    # ワークフローの概要説明
    with st.expander("ワークフローについて", expanded=False):
        st.write("""
        このワークフローでは、以下のステップを順に実行して分析を行います：
        
        1. **データ前処理**: データのクリーニングと前処理を行います。
        2. **風向風速推定**: GPSデータから風向風速を推定します。
        3. **戦略ポイント検出**: 重要な戦略的判断ポイントを検出します。
        4. **パフォーマンス分析**: セーリングパフォーマンスの評価を行います。
        5. **レポート作成**: 分析結果をレポートにまとめます。
        
        各ステップは個別に実行することも、すべてのステップを一度に実行することもできます。
        """)
    
    # ワークフローステップインジケーター
    workflow_step_indicator(workflow, st.session_state.get('active_step_id'))
    
    # 進捗バー
    workflow_progress_bar(workflow)
    
    # ステップ選択UI
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # ステップ選択
        step_options = [(step.step_id, f"{step.name} ({step.status.value})") 
                        for step_id, step in workflow.steps.items()]
        step_keys = [option[0] for option in step_options]
        step_labels = [option[1] for option in step_options]
        
        selected_index = step_keys.index(st.session_state.get('active_step_id')) if st.session_state.get('active_step_id') in step_keys else 0
        
        selected_step = st.selectbox(
            "ステップを選択:",
            options=step_keys,
            format_func=lambda x: step_labels[step_keys.index(x)],
            index=selected_index
        )
        
        st.session_state.active_step_id = selected_step
    
    with col2:
        # 全ステップ実行ボタン
        st.write("##")  # スペースを追加して位置を調整
        if st.button("すべてのステップを実行", key="run_all", use_container_width=True):
            with st.spinner("すべてのステップを実行中..."):
                result = workflow.run_workflow()
                if result["success_rate"] == 1.0:
                    st.success("すべてのステップが正常に完了しました。")
                else:
                    st.warning(
                        f"一部のステップが失敗しました。成功率: {result['success_rate']:.1%}, "
                        f"成功: {result['completed_steps']}/{result['total_steps']}, "
                        f"失敗: {result['failed_steps']}/{result['total_steps']}"
                    )
    
    # 選択されたステップの実行パネル
    step_execution_panel(workflow, selected_step)
    
    # リセットボタン
    if st.button("ワークフローをリセット", key="reset_workflow"):
        # 入力データの保持
        input_df = workflow.get_data("input_df")
        
        # ワークフローのリセット
        workflow.reset_workflow()
        
        # 入力データの再設定
        if input_df is not None:
            workflow.set_data("input_df", input_df)
        
        st.success("ワークフローがリセットされました。")
        st.experimental_rerun()


def display_parameter_adjustment_panel(workflow: AnalysisWorkflowController) -> None:
    """
    パラメータ調整パネルの表示
    
    Parameters:
    -----------
    workflow : AnalysisWorkflowController
        ワークフローコントローラー
    """
    st.header("パラメータ調整")
    
    # パラメータマネージャーの取得
    session_data = st.session_state.get('session_data', {})
    params_manager = session_data.get('params_manager')
    
    if params_manager is None:
        st.warning("パラメータ管理システムが初期化されていません。")
        return
    
    # パラメータ調整用のタブ
    param_tab1, param_tab2, param_tab3 = st.tabs([
        "風推定パラメータ", 
        "戦略検出パラメータ", 
        "パフォーマンス分析パラメータ"
    ])
    
    with param_tab1:
        # 風推定パラメータの調整
        wind_params = parameter_adjustment_panel(
            params_manager, 
            ParameterNamespace.WIND_ESTIMATION,
            on_change=lambda changes: handle_parameter_changes(changes, "wind_estimation", workflow)
        )
    
    with param_tab2:
        # 戦略検出パラメータの調整
        strategy_params = parameter_adjustment_panel(
            params_manager, 
            ParameterNamespace.STRATEGY_DETECTION,
            on_change=lambda changes: handle_parameter_changes(changes, "strategy_detection", workflow)
        )
    
    with param_tab3:
        # パフォーマンス分析パラメータの調整
        performance_params = parameter_adjustment_panel(
            params_manager, 
            ParameterNamespace.PERFORMANCE_ANALYSIS,
            on_change=lambda changes: handle_parameter_changes(changes, "performance_analysis", workflow)
        )
    
    # プリセットの保存UI
    st.subheader("プリセットの保存")
    
    preset_namespace = st.selectbox(
        "保存するパラメータセット:",
        [
            ("wind_estimation", "風推定パラメータ"),
            ("strategy_detection", "戦略検出パラメータ"),
            ("performance_analysis", "パフォーマンス分析パラメータ")
        ],
        format_func=lambda x: x[1]
    )[0]
    
    preset_name = st.text_input("プリセット名:")
    
    if st.button("プリセットを保存", key="save_preset"):
        if not preset_name:
            st.error("プリセット名を入力してください。")
        else:
            # パラメータネームスペースを選択
            namespace = getattr(ParameterNamespace, preset_namespace.upper())
            
            # プリセットの保存
            preset_id = params_manager.create_preset(preset_name, namespace)
            
            if preset_id:
                st.success(f"プリセット '{preset_name}' を保存しました。")
            else:
                st.error("プリセットの保存に失敗しました。")


def handle_parameter_changes(changes: Dict[str, Any], change_type: str, workflow: AnalysisWorkflowController) -> None:
    """
    パラメータ変更時のハンドラー
    
    Parameters:
    -----------
    changes : Dict[str, Any]
        変更されたパラメータのキーと値
    change_type : str
        変更されたパラメータの種類
    workflow : AnalysisWorkflowController
        ワークフローコントローラー
    """
    # リセットの場合
    if "reset" in changes:
        # 関連するステップのリセット
        if change_type == "wind_estimation":
            workflow.steps["wind_estimation"].reset()
        elif change_type == "strategy_detection":
            workflow.steps["strategy_detection"].reset()
        elif change_type == "performance_analysis":
            workflow.steps["performance_analysis"].reset()
        
        # レポート作成ステップもリセット
        workflow.steps["report_creation"].reset()
        
        # ログに記録
        logger.info(f"{change_type}パラメータがリセットされました")
        return
    
    # 値の変更の場合
    for key, value in changes.items():
        # キャッシュのクリア（簡易実装）
        if change_type == "wind_estimation":
            workflow.steps["wind_estimation"].reset()
        elif change_type == "strategy_detection":
            workflow.steps["strategy_detection"].reset()
        elif change_type == "performance_analysis":
            workflow.steps["performance_analysis"].reset()
        
        # レポート作成ステップもリセット
        workflow.steps["report_creation"].reset()
        
        # ログに記録
        logger.info(f"パラメータ '{key}' が {value} に変更されました")


def display_results_panel(workflow: AnalysisWorkflowController) -> None:
    """
    分析結果パネルの表示
    
    Parameters:
    -----------
    workflow : AnalysisWorkflowController
        ワークフローコントローラー
    """
    st.header("分析結果")
    
    # 結果タブの作成
    result_tab1, result_tab2, result_tab3, result_tab4, result_tab5 = st.tabs([
        "データ概要", 
        "風推定結果", 
        "戦略検出結果", 
        "パフォーマンス分析", 
        "レポート"
    ])
    
    # データ概要タブ
    with result_tab1:
        st.subheader("データ概要")
        
        # 前処理統計情報の表示
        stats = workflow.get_data("stats")
        processed_df = workflow.get_data("processed_df")
        
        if stats:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("元データ行数", stats.get('original_rows', 0))
            
            with col2:
                st.metric("処理後行数", stats.get('processed_rows', 0))
            
            with col3:
                st.metric("除外された行", stats.get('removed_rows', 0))
        
        # データプレビューの表示
        if processed_df is not None:
            st.subheader("処理済みデータプレビュー")
            st.dataframe(processed_df.head(10))
            
            # 全データの表示（展開可能）
            if len(processed_df) > 10:
                with st.expander("すべてのデータを表示", expanded=False):
                    st.dataframe(processed_df)
        else:
            st.info("前処理ステップを実行すると、データの概要が表示されます。")
    
    # 風推定結果タブ
    with result_tab2:
        # 風推定結果の表示
        result_display_panel(
            workflow, 
            "wind_result", 
            "風推定結果"
        )
    
    # 戦略検出結果タブ
    with result_tab3:
        # 戦略検出結果の表示
        result_display_panel(
            workflow, 
            "strategy_result", 
            "戦略検出結果"
        )
    
    # パフォーマンス分析タブ
    with result_tab4:
        # パフォーマンス分析結果の表示
        result_display_panel(
            workflow, 
            "performance_result", 
            "パフォーマンス分析結果"
        )
    
    # レポートタブ
    with result_tab5:
        # レポートの表示
        report = workflow.get_data("report")
        
        if report:
            st.subheader("分析レポート")
            
            # レポートの基本情報
            st.write(f"作成日時: {report.get('timestamp', '')}")
            
            # データサマリー
            data_summary = report.get("data_summary", {})
            st.write(f"分析データポイント数: {data_summary.get('points', 0)}")
            
            duration = data_summary.get("duration_seconds", 0)
            hours = int(duration / 3600)
            minutes = int((duration % 3600) / 60)
            seconds = int(duration % 60)
            st.write(f"データ期間: {hours}時間 {minutes}分 {seconds}秒")
            
            # 風サマリー
            wind_summary = report.get("wind_summary", {})
            st.write(f"平均風向: {wind_summary.get('direction', 0):.1f}°")
            st.write(f"平均風速: {wind_summary.get('speed', 0):.1f}ノット")
            
            # 戦略サマリー
            strategy_summary = report.get("strategy_summary", {})
            st.write(f"検出された戦略ポイント: {strategy_summary.get('point_count', 0)}件")
            st.write(f"風向シフト: {strategy_summary.get('wind_shift_count', 0)}件")
            st.write(f"タックポイント: {strategy_summary.get('tack_point_count', 0)}件")
            st.write(f"レイライン: {strategy_summary.get('layline_count', 0)}件")
            
            # パフォーマンスサマリー
            performance_summary = report.get("performance_summary", {})
            st.write(f"パフォーマンススコア: {performance_summary.get('score', 0):.1f}/100 ({performance_summary.get('rating', '')})")
            
            if "summary" in performance_summary:
                st.write("パフォーマンス評価:")
                st.info(performance_summary["summary"])
            
            # レポートのエクスポート
            if st.button("レポートをエクスポート", key="export_report"):
                # ここでエクスポート処理を実装（今回は省略）
                st.info("エクスポート機能は現在準備中です。")
        else:
            st.info("レポートデータが見つかりません。レポート作成ステップを実行してください。")


def workflow_page() -> None:
    """
    ワークフロー管理ページのメインエントリーポイント
    """
    workflow_main_view()


if __name__ == "__main__":
    workflow_page()
