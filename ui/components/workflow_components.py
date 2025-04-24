# -*- coding: utf-8 -*-
"""
ワークフローUIコンポーネントモジュール

このモジュールは分析ワークフローのユーザーインターフェースコンポーネントを提供します。
ステップバイステップのナビゲーション、パラメータ調整、進捗表示などの機能を含みます。
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
import json
from typing import Dict, List, Any, Optional, Callable, Union
import logging
from datetime import datetime

from sailing_data_processor.analysis.analysis_workflow import AnalysisWorkflowController, AnalysisStep, AnalysisStatus
from sailing_data_processor.analysis.analysis_parameters import ParametersManager, ParameterNamespace
from sailing_data_processor.analysis.analysis_cache import AnalysisCache
from sailing_data_processor.analysis.integrated_wind_estimator import IntegratedWindEstimator
from sailing_data_processor.analysis.integrated_strategy_detector import IntegratedStrategyDetector
from sailing_data_processor.analysis.integrated_performance_analyzer import IntegratedPerformanceAnalyzer


def workflow_step_indicator(workflow: AnalysisWorkflowController, 
                           active_step: Optional[str] = None) -> None:
    """
    ワークフローステップを視覚的に表示するインジケーター
    
    Parameters:
    -----------
    workflow : AnalysisWorkflowController
        ワークフローコントローラー
    active_step : str, optional
        現在のアクティブステップID
    """
    if not workflow.steps:
        st.warning("ワークフローに定義されたステップがありません。")
        return
    
    # ワークフローから順序付きステップリストを取得
    ordered_steps = [workflow.steps[step_id] for step_id in workflow.step_order if step_id in workflow.steps]
    
    # 表示用のカラム
    cols = st.columns(len(ordered_steps))
    
    for i, step in enumerate(ordered_steps):
        with cols[i]:
            # ステップのステータスに応じた色の設定
            status_colors = {
                AnalysisStatus.COMPLETED: "green",
                AnalysisStatus.IN_PROGRESS: "blue",
                AnalysisStatus.FAILED: "red",
                AnalysisStatus.SKIPPED: "orange",
                AnalysisStatus.NOT_STARTED: "gray"
            }
            
            color = status_colors.get(step.status, "gray")
            
            # アクティブステップの強調
            is_active = active_step == step.step_id
            font_weight = "bold" if is_active else "normal"
            border = f"2px solid {color}" if is_active else "1px solid lightgray"
            
            # ステップの表示
            step_html = f"""
            <div style="text-align: center; padding: 10px; 
                        border: {border}; border-radius: 5px;
                        background-color: {'#f0f0f0' if is_active else 'white'}">
                <div style="color: {color}; font-weight: {font_weight};">{step.name}</div>
                <div style="font-size: 0.8em; color: {color};">{step.status.value}</div>
            </div>
            """
            st.markdown(step_html, unsafe_allow_html=True)


def workflow_progress_bar(workflow: AnalysisWorkflowController) -> None:
    """
    ワークフロー全体の進捗バーを表示
    
    Parameters:
    -----------
    workflow : AnalysisWorkflowController
        ワークフローコントローラー
    """
    status = workflow.get_workflow_status()
    
    # 進捗率の計算
    progress_pct = status.get("progress_percentage", 0) / 100
    
    # 進捗バーの表示
    st.progress(progress_pct)
    
    # 詳細情報の表示
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("完了ステップ", f"{status.get('completed', 0)}/{status.get('total_steps', 0)}")
    
    with col2:
        if status.get("runtime_seconds") is not None:
            st.metric("実行時間", f"{status.get('runtime_seconds', 0):.1f}秒")
        else:
            st.metric("実行時間", "未実行")
    
    with col3:
        error_count = status.get("failed", 0)
        error_color = "normal" if error_count == 0 else "inverse"
        st.metric("エラー", f"{error_count}", delta_color=error_color)


def parameter_adjustment_panel(params_manager: ParametersManager, 
                              namespace: str,
                              on_change: Optional[Callable] = None) -> Dict[str, Any]:
    """
    パラメータ調整パネルを表示
    
    Parameters:
    -----------
    params_manager : ParametersManager
        パラメータ管理オブジェクト
    namespace : str
        表示するパラメータの名前空間
    on_change : Callable, optional
        値変更時のコールバック関数
        
    Returns:
    --------
    Dict[str, Any]
        調整されたパラメータ値
    """
    # 名前空間のパラメータを取得
    params = params_manager.get_parameters_by_namespace(namespace)
    
    # 名前空間のパラメータ定義を取得
    param_definitions = []
    for key, definition in params_manager.parameter_definitions.items():
        if definition.namespace == namespace:
            param_definitions.append(definition)
    
    # UIの順序でソート
    param_definitions.sort(key=lambda d: d.ui_order)
    
    # セッションステートキーの接頭辞
    prefix = f"param_{namespace}_"
    
    # パラメータの値を変更する関数
    def update_parameter(key, value):
        params_manager.set_parameter(key, value)
        if on_change:
            on_change({key: value})
    
    # パラメータパネルの見出し
    namespace_labels = {
        ParameterNamespace.WIND_ESTIMATION: "風推定パラメータ",
        ParameterNamespace.STRATEGY_DETECTION: "戦略検出パラメータ",
        ParameterNamespace.PERFORMANCE_ANALYSIS: "パフォーマンス分析パラメータ",
        ParameterNamespace.DATA_PROCESSING: "データ処理パラメータ",
        ParameterNamespace.VISUALIZATION: "可視化パラメータ",
        ParameterNamespace.GENERAL: "一般パラメータ"
    }
    
    st.subheader(namespace_labels.get(namespace, namespace))
    
    # プリセットの選択
    presets = params_manager.get_presets_by_namespace(namespace)
    if presets:
        preset_options = ["カスタム"] + [preset.name for preset in presets]
        preset_index = 0
        
        selected_preset = st.selectbox(
            "プリセット",
            options=preset_options,
            index=preset_index,
            key=f"{prefix}preset"
        )
        
        if selected_preset != "カスタム":
            # 選択されたプリセットを適用
            for preset in presets:
                if preset.name == selected_preset:
                    params_manager.apply_preset(preset.preset_id)
                    # 更新後のパラメータを取得
                    params = params_manager.get_parameters_by_namespace(namespace)
                    break
    
    # 詳細/基本モードの切り替え
    show_advanced = st.checkbox("詳細設定を表示", key=f"{prefix}show_advanced")
    
    # パラメータUIの表示
    for definition in param_definitions:
        # 詳細設定のフィルタリング
        if definition.ui_advanced and not show_advanced:
            continue
        
        # 非表示パラメータのスキップ
        if definition.ui_hidden:
            continue
        
        # 現在値の取得
        current_value = params.get(definition.key, definition.default_value)
        
        # ラベルの作成（単位を含む）
        label = definition.name
        if definition.unit:
            label += f" ({definition.unit})"
        
        # パラメータタイプに応じたUIの表示
        session_key = f"{prefix}{definition.key}"
        
        if definition.value_type == "int":
            value = st.slider(
                label,
                min_value=definition.min_value if definition.min_value is not None else 0,
                max_value=definition.max_value if definition.max_value is not None else 100,
                value=int(current_value),
                key=session_key
            )
            
            if value != current_value:
                update_parameter(definition.key, value)
        
        elif definition.value_type == "float":
            value = st.slider(
                label,
                min_value=float(definition.min_value if definition.min_value is not None else 0.0),
                max_value=float(definition.max_value if definition.max_value is not None else 10.0),
                value=float(current_value),
                step=0.1,
                key=session_key
            )
            
            if value != current_value:
                update_parameter(definition.key, value)
        
        elif definition.value_type == "bool":
            value = st.checkbox(
                label,
                value=bool(current_value),
                key=session_key
            )
            
            if value != current_value:
                update_parameter(definition.key, value)
        
        elif definition.value_type == "str":
            if definition.allowed_values:
                # 選択肢がある場合はセレクトボックス
                value = st.selectbox(
                    label,
                    options=definition.allowed_values,
                    index=definition.allowed_values.index(current_value) if current_value in definition.allowed_values else 0,
                    key=session_key
                )
            else:
                # 自由入力
                value = st.text_input(
                    label,
                    value=str(current_value),
                    key=session_key
                )
            
            if value != current_value:
                update_parameter(definition.key, value)
        
        # パラメータの説明（情報アイコン）
        if definition.description:
            st.caption(definition.description)
    
    # リセットボタン
    if st.button("パラメータをリセット", key=f"{prefix}reset"):
        params_manager.reset_namespace_parameters(namespace)
        if on_change:
            on_change({"reset": namespace})
        st.success(f"{namespace_labels.get(namespace, namespace)}をリセットしました。")
    
    # 最新のパラメータ値を返す
    return params_manager.get_parameters_by_namespace(namespace)


def step_execution_panel(workflow: AnalysisWorkflowController, 
                        step_id: str) -> Dict[str, Any]:
    """
    特定のワークフローステップを実行するパネルを表示
    
    Parameters:
    -----------
    workflow : AnalysisWorkflowController
        ワークフローコントローラー
    step_id : str
        実行するステップID
        
    Returns:
    --------
    Dict[str, Any]
        ステップの実行結果
    """
    if step_id not in workflow.steps:
        st.error(f"ステップID '{step_id}' はワークフローに存在しません。")
        return {"error": f"ステップID '{step_id}' は存在しません"}
    
    step = workflow.steps[step_id]
    
    # ステップの状態
    status = step.status
    
    # ステップの情報表示
    st.subheader(f"ステップ: {step.name}")
    st.write(step.description)
    
    # ステップの状態表示
    status_colors = {
        AnalysisStatus.COMPLETED: "success",
        AnalysisStatus.IN_PROGRESS: "info",
        AnalysisStatus.FAILED: "error",
        AnalysisStatus.SKIPPED: "warning",
        AnalysisStatus.NOT_STARTED: "primary"
    }
    
    status_label = status.value
    status_color = status_colors.get(status, "primary")
    
    st.write(f"状態: :{status_color}[{status_label}]")
    
    # 前提条件のチェック
    prerequisites_ok, missing = workflow.check_prerequisites(step_id)
    
    if not prerequisites_ok:
        st.warning("このステップを実行するための前提条件が満たされていません:")
        for msg in missing:
            st.write(f"- {msg}")
    
    # 実行ボタン
    col1, col2 = st.columns([1, 1])
    
    with col1:
        execute = st.button(
            "ステップを実行",
            disabled=status == AnalysisStatus.IN_PROGRESS,
            key=f"execute_{step_id}"
        )
    
    with col2:
        force_execute = st.button(
            "強制実行 (前提条件無視)",
            disabled=status == AnalysisStatus.IN_PROGRESS,
            key=f"force_{step_id}"
        )
    
    # 実行結果の表示領域
    result_container = st.container()
    
    # ステップの実行
    if execute:
        with st.spinner(f"ステップ '{step.name}' を実行中..."):
            with result_container:
                success = workflow.run_step(step_id)
                if success:
                    st.success(f"ステップ '{step.name}' が正常に完了しました。")
                else:
                    st.error(f"ステップ '{step.name}' の実行中にエラーが発生しました: {step.error_message}")
    
    elif force_execute:
        with st.spinner(f"ステップ '{step.name}' を強制実行中..."):
            with result_container:
                success = workflow.run_step(step_id, force=True)
                if success:
                    st.success(f"ステップ '{step.name}' が正常に完了しました。")
                else:
                    st.error(f"ステップ '{step.name}' の実行中にエラーが発生しました: {step.error_message}")
    
    # 実行後の状態を取得
    step_data = workflow.get_step_status(step_id)
    
    # 前回の実行情報
    if step.start_time:
        st.write(f"開始時間: {step.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if step.end_time:
        st.write(f"終了時間: {step.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if step.runtime_seconds:
        st.write(f"実行時間: {step.runtime_seconds:.2f}秒")
    
    # エラーメッセージの表示
    if step.error_message:
        with st.expander("エラー詳細", expanded=True):
            st.error(step.error_message)
    
    # 警告メッセージの表示
    if step.warnings:
        with st.expander("警告", expanded=False):
            for warning in step.warnings:
                st.warning(warning)
    
    return step_data


def result_display_panel(workflow: AnalysisWorkflowController,
                        result_key: str,
                        title: str = "結果",
                        formatter: Optional[Callable] = None) -> None:
    """
    ワークフロー結果を表示するパネル
    
    Parameters:
    -----------
    workflow : AnalysisWorkflowController
        ワークフローコントローラー
    result_key : str
        表示する結果データのキー
    title : str, optional
        表示タイトル
    formatter : Callable, optional
        結果データの表示形式を整える関数
    """
    st.subheader(title)
    
    # 結果の取得
    result = workflow.get_data(result_key)
    
    if result is None:
        st.info(f"データ '{result_key}' が見つかりません。前のステップを実行してください。")
        return
    
    # フォーマッタが指定されている場合は適用
    if formatter:
        try:
            formatter(result)
            return
        except Exception as e:
            st.error(f"結果の表示中にエラーが発生しました: {str(e)}")
    
    # デフォルトの表示形式
    if isinstance(result, pd.DataFrame):
        st.dataframe(result)
    elif isinstance(result, dict) or isinstance(result, list):
        st.json(result)
    else:
        st.write(result)


def wind_estimation_result_formatter(result: Dict[str, Any]) -> None:
    """
    風推定結果のフォーマッタ
    
    Parameters:
    -----------
    result : Dict[str, Any]
        風推定結果
    """
    if "error" in result:
        st.error(f"風推定エラー: {result['error']}")
        return
    
    # 基本的な風情報の表示
    wind = result.get("wind", {})
    st.metric("風向", f"{wind.get('direction', 0):.1f}°")
    st.metric("風速", f"{wind.get('speed', 0):.1f}ノット")
    st.metric("信頼度", f"{wind.get('confidence', 0):.2f}")
    st.write(f"推定方法: {wind.get('method', '不明')}")
    
    # マニューバー情報
    maneuvers = result.get("detected_maneuvers", [])
    
    if maneuvers:
        st.subheader(f"検出されたマニューバー ({len(maneuvers)}件)")
        
        # 簡易表示（最初の5件）
        maneuver_df = pd.DataFrame(maneuvers)
        st.dataframe(maneuver_df.head(5))
        
        # 全データの表示（展開可能）
        with st.expander("すべてのマニューバーを表示", expanded=False):
            st.dataframe(maneuver_df)
    else:
        st.info("マニューバーは検出されませんでした。")


def strategy_detection_result_formatter(result: Dict[str, Any]) -> None:
    """
    戦略検出結果のフォーマッタ
    
    Parameters:
    -----------
    result : Dict[str, Any]
        戦略検出結果
    """
    if "error" in result:
        st.error(f"戦略検出エラー: {result['error']}")
        return
    
    # 検出されたポイント情報
    all_points = result.get("all_points", [])
    wind_shifts = result.get("wind_shifts", [])
    tack_points = result.get("tack_points", [])
    layline_points = result.get("layline_points", [])
    
    # サマリー表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("検出ポイント合計", len(all_points))
    
    with col2:
        st.metric("風向シフト", len(wind_shifts))
    
    with col3:
        st.metric("タックポイント", len(tack_points))
    
    with col4:
        st.metric("レイライン", len(layline_points))
    
    # 重要ポイントの表示
    if all_points:
        st.subheader("重要な戦略ポイント")
        
        # 重要度でソート
        important_points = sorted(
            all_points, 
            key=lambda p: p.get("strategic_score", 0), 
            reverse=True
        )[:5]  # 上位5件
        
        for i, point in enumerate(important_points):
            point_type = point.get("type", "Unknown")
            score = point.get("strategic_score", 0)
            
            with st.expander(
                f"{i+1}. {point_type} (重要度: {score:.2f})",
                expanded=i == 0  # 最初のポイントは展開
            ):
                # ポイントの詳細表示
                if point_type == "WindShiftPoint":
                    st.write(f"シフト角度: {point.get('shift_angle', 0):.1f}°")
                    st.write(f"シフト前風向: {point.get('before_direction', 0):.1f}°")
                    st.write(f"シフト後風向: {point.get('after_direction', 0):.1f}°")
                    st.write(f"風速: {point.get('wind_speed', 0):.1f}ノット")
                
                elif point_type == "TackPoint":
                    st.write(f"タックタイプ: {point.get('tack_type', '不明')}")
                    st.write(f"推奨タック: {point.get('suggested_tack', '不明')}")
                    st.write(f"VMG改善: {point.get('vmg_gain', 0):.3f}")
                
                elif point_type == "LaylinePoint":
                    st.write(f"マークID: {point.get('mark_id', '不明')}")
                    st.write(f"マークまでの距離: {point.get('distance_to_mark', 0):.1f}m")
                    st.write(f"進入角度: {point.get('approach_angle', 0):.1f}°")
                
                # 共通情報
                st.write(f"メモ: {point.get('note', '情報なし')}")
                
                # 位置情報があれば表示
                lat = point.get("latitude")
                lon = point.get("longitude")
                if lat and lon:
                    st.write(f"位置: {lat:.6f}, {lon:.6f}")
    else:
        st.info("戦略ポイントは検出されませんでした。")


def performance_analysis_result_formatter(result: Dict[str, Any]) -> None:
    """
    パフォーマンス分析結果のフォーマッタ
    
    Parameters:
    -----------
    result : Dict[str, Any]
        パフォーマンス分析結果
    """
    if "error" in result:
        st.error(f"パフォーマンス分析エラー: {result['error']}")
        return
    
    # 総合評価の表示
    overall = result.get("overall_performance", {})
    
    score = overall.get("score", 0)
    rating = overall.get("rating", "評価なし")
    
    st.metric("総合パフォーマンススコア", f"{score:.1f}/100")
    st.info(f"評価: {rating}")
    
    if "summary" in overall:
        st.write(overall["summary"])
    
    # 基本統計情報
    basic_stats = result.get("basic_stats", {})
    
    with st.expander("基本統計情報", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if "speed" in basic_stats:
                speed_stats = basic_stats["speed"]
                st.metric("平均速度", f"{speed_stats.get('mean', 0):.1f}ノット")
                st.metric("最大速度", f"{speed_stats.get('max', 0):.1f}ノット")
        
        with col2:
            if "sailing_mode_percentage" in basic_stats:
                modes = basic_stats["sailing_mode_percentage"]
                st.metric("風上時間", f"{modes.get('upwind', 0):.1f}%")
                st.metric("風下時間", f"{modes.get('downwind', 0):.1f}%")
        
        with col3:
            if "vmg" in basic_stats:
                vmg_stats = basic_stats["vmg"]
                upwind_vmg = vmg_stats.get("upwind_mean")
                downwind_vmg = vmg_stats.get("downwind_mean")
                
                if upwind_vmg:
                    st.metric("風上VMG平均", f"{upwind_vmg:.2f}ノット")
                
                if downwind_vmg:
                    st.metric("風下VMG平均", f"{downwind_vmg:.2f}ノット")
    
    # VMG分析
    vmg_analysis = result.get("vmg_analysis", {})
    
    with st.expander("VMG分析", expanded=False):
        # 風上VMG
        upwind = vmg_analysis.get("upwind", {})
        if upwind and not upwind.get("insufficient_data", False):
            st.subheader("風上VMG分析")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("平均VMG", f"{upwind.get('mean_vmg', 0):.2f}ノット")
                st.metric("最大VMG", f"{upwind.get('max_vmg', 0):.2f}ノット")
            
            with col2:
                st.metric("平均角度", f"{upwind.get('mean_angle', 0):.1f}°")
                
                # 最適値との比較
                if upwind.get("optimal_vmg") and upwind.get("performance_ratio"):
                    st.metric("最適VMG比", f"{upwind.get('performance_ratio', 0):.1%}")
        
        # 風下VMG
        downwind = vmg_analysis.get("downwind", {})
        if downwind and not downwind.get("insufficient_data", False):
            st.subheader("風下VMG分析")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("平均VMG", f"{downwind.get('mean_vmg', 0):.2f}ノット")
                st.metric("最大VMG", f"{downwind.get('max_vmg', 0):.2f}ノット")
            
            with col2:
                st.metric("平均角度", f"{downwind.get('mean_angle', 0):.1f}°")
                
                # 最適値との比較
                if downwind.get("optimal_vmg") and downwind.get("performance_ratio"):
                    st.metric("最適VMG比", f"{downwind.get('performance_ratio', 0):.1%}")
    
    # マニューバー分析
    maneuver_analysis = result.get("maneuver_analysis", {})
    
    with st.expander("マニューバー分析", expanded=False):
        if not maneuver_analysis.get("insufficient_data", False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("タック分析")
                tacks = maneuver_analysis.get("tacks", {})
                
                if tacks:
                    st.metric("タック数", maneuver_analysis.get("tack_count", 0))
                    st.metric("平均所要時間", f"{tacks.get('avg_duration', 0):.1f}秒")
                    st.metric("速度損失", f"{tacks.get('avg_speed_loss', 0):.1%}")
                else:
                    st.info("タックデータがありません")
            
            with col2:
                st.subheader("ジャイブ分析")
                gybes = maneuver_analysis.get("gybes", {})
                
                if gybes:
                    st.metric("ジャイブ数", maneuver_analysis.get("gybe_count", 0))
                    st.metric("平均所要時間", f"{gybes.get('avg_duration', 0):.1f}秒")
                    st.metric("速度損失", f"{gybes.get('avg_speed_loss', 0):.1%}")
                else:
                    st.info("ジャイブデータがありません")
        else:
            st.info("マニューバーデータが不足しています")


def create_default_analysis_workflow(df: pd.DataFrame,
                                    params_manager: ParametersManager,
                                    cache: AnalysisCache) -> AnalysisWorkflowController:
    """
    デフォルトの分析ワークフローを作成
    
    Parameters:
    -----------
    df : pd.DataFrame
        分析対象のデータフレーム
    params_manager : ParametersManager
        パラメータ管理オブジェクト
    cache : AnalysisCache
        キャッシュ管理オブジェクト
        
    Returns:
    --------
    AnalysisWorkflowController
        作成されたワークフローコントローラー
    """
    # 統合モジュールの初期化
    wind_estimator = IntegratedWindEstimator(params_manager, cache)
    strategy_detector = IntegratedStrategyDetector(params_manager, cache, wind_estimator)
    performance_analyzer = IntegratedPerformanceAnalyzer(params_manager, cache, wind_estimator)
    
    # ワークフローコントローラーの作成
    workflow = AnalysisWorkflowController(namespace="sailing_analysis")
    
    # 前処理ステップの定義
    def preprocess_data(input_df):
        """データの前処理を行う"""
        # タイムスタンプのソート
        processed_df = input_df.sort_values('timestamp').copy()
        
        # 基本的な検証
        required_cols = ['timestamp', 'latitude', 'longitude', 'course', 'speed']
        for col in required_cols:
            if col not in processed_df.columns:
                raise ValueError(f"必要なカラム '{col}' がデータに含まれていません")
        
        # 時間差分の計算（秒）
        processed_df['time_diff'] = processed_df['timestamp'].diff().dt.total_seconds()
        
        # 最初の行の時間差分はNaNになるので0に設定
        processed_df.loc[processed_df.index[0], 'time_diff'] = 0
        
        # 異常値の除去（極端な外れ値）
        speed_mean = processed_df['speed'].mean()
        speed_std = processed_df['speed'].std()
        
        # 平均±3σの範囲外を除外
        processed_df = processed_df[
            (processed_df['speed'] > speed_mean - 3 * speed_std) &
            (processed_df['speed'] < speed_mean + 3 * speed_std)
        ]
        
        return {
            "processed_df": processed_df,
            "stats": {
                "original_rows": len(input_df),
                "processed_rows": len(processed_df),
                "removed_rows": len(input_df) - len(processed_df)
            }
        }
    
    # 風推定ステップの定義
    def estimate_wind(processed_df):
        """風推定を実行する"""
        result = wind_estimator.estimate_wind(processed_df)
        return {"wind_result": result}
    
    # 戦略検出ステップの定義
    def detect_strategy_points(processed_df, wind_result):
        """戦略的判断ポイントを検出する"""
        result = strategy_detector.detect_strategy_points(processed_df)
        return {"strategy_result": result}
    
    # パフォーマンス分析ステップの定義
    def analyze_performance(processed_df, wind_result):
        """パフォーマンス分析を実行する"""
        result = performance_analyzer.analyze_performance(processed_df)
        return {"performance_result": result}
    
    # レポート作成ステップの定義
    def create_report(processed_df, wind_result, strategy_result, performance_result):
        """分析レポートを作成する"""
        # レポートデータの構築
        report = {
            "timestamp": datetime.now().isoformat(),
            "data_summary": {
                "points": len(processed_df),
                "duration_seconds": (processed_df['timestamp'].max() - processed_df['timestamp'].min()).total_seconds(),
                "distance_nm": None  # 距離計算はここでは省略
            },
            "wind_summary": {
                "direction": wind_result.get("wind", {}).get("direction"),
                "speed": wind_result.get("wind", {}).get("speed"),
                "confidence": wind_result.get("wind", {}).get("confidence")
            },
            "strategy_summary": {
                "point_count": strategy_result.get("point_count", 0),
                "wind_shift_count": strategy_result.get("wind_shift_count", 0),
                "tack_point_count": strategy_result.get("tack_point_count", 0),
                "layline_count": strategy_result.get("layline_count", 0)
            },
            "performance_summary": {
                "score": performance_result.get("overall_performance", {}).get("score"),
                "rating": performance_result.get("overall_performance", {}).get("rating"),
                "summary": performance_result.get("overall_performance", {}).get("summary")
            }
        }
        
        return {"report": report}
    
    # ステップをワークフローに追加
    workflow.add_step(
        AnalysisStep(
            step_id="preprocess",
            name="データ前処理",
            description="データのクリーニングと前処理を行います",
            function=preprocess_data,
            required_input_keys=["input_df"],
            produces_output_keys=["processed_df", "stats"]
        )
    )
    
    workflow.add_step(
        AnalysisStep(
            step_id="wind_estimation",
            name="風向風速推定",
            description="GPSデータから風向風速を推定します",
            function=estimate_wind,
            required_input_keys=["processed_df"],
            produces_output_keys=["wind_result"],
            dependencies=["preprocess"]
        )
    )
    
    workflow.add_step(
        AnalysisStep(
            step_id="strategy_detection",
            name="戦略ポイント検出",
            description="重要な戦略的判断ポイントを検出します",
            function=detect_strategy_points,
            required_input_keys=["processed_df", "wind_result"],
            produces_output_keys=["strategy_result"],
            dependencies=["preprocess", "wind_estimation"]
        )
    )
    
    workflow.add_step(
        AnalysisStep(
            step_id="performance_analysis",
            name="パフォーマンス分析",
            description="セーリングパフォーマンスの評価を行います",
            function=analyze_performance,
            required_input_keys=["processed_df", "wind_result"],
            produces_output_keys=["performance_result"],
            dependencies=["preprocess", "wind_estimation"]
        )
    )
    
    workflow.add_step(
        AnalysisStep(
            step_id="report_creation",
            name="レポート作成",
            description="分析結果をレポートにまとめます",
            function=create_report,
            required_input_keys=["processed_df", "wind_result", "strategy_result", "performance_result"],
            produces_output_keys=["report"],
            dependencies=["preprocess", "wind_estimation", "strategy_detection", "performance_analysis"]
        )
    )
    
    # 入力データの設定
    workflow.set_data("input_df", df)
    
    # 依存関係のバリデーション
    issues = workflow.validate_dependencies()
    if issues:
        logging.warning(f"ワークフロー依存関係の問題: {issues}")
    
    # ワークフロー順序の最適化
    workflow.optimize_step_order()
    
    return workflow


def complete_workflow_panel(df: pd.DataFrame,
                           params_manager: ParametersManager,
                           cache: AnalysisCache) -> None:
    """
    完全な分析ワークフローパネルを表示
    
    Parameters:
    -----------
    df : pd.DataFrame
        分析対象のデータフレーム
    params_manager : ParametersManager
        パラメータ管理オブジェクト
    cache : AnalysisCache
        キャッシュ管理オブジェクト
    """
    # セッション状態の初期化
    if 'workflow' not in st.session_state:
        st.session_state.workflow = create_default_analysis_workflow(df, params_manager, cache)
        st.session_state.active_step_id = None
        st.session_state.active_tab = "workflow"
    
    # ワークフローの取得
    workflow = st.session_state.workflow
    
    # タブの作成
    tab_workflow, tab_params, tab_results = st.tabs(["ワークフロー", "パラメータ", "結果"])
    
    # ワークフロータブ
    with tab_workflow:
        st.header("分析ワークフロー")
        
        # ワークフローステップインジケーター
        workflow_step_indicator(workflow, st.session_state.active_step_id)
        
        # 進捗バー
        workflow_progress_bar(workflow)
        
        # ステップ選択
        step_options = [(step.step_id, f"{step.name} ({step.status.value})") 
                        for step_id, step in workflow.steps.items()]
        step_keys = [option[0] for option in step_options]
        step_labels = [option[1] for option in step_options]
        
        selected_index = step_keys.index(st.session_state.active_step_id) if st.session_state.active_step_id in step_keys else 0
        
        selected_step = st.selectbox(
            "ステップを選択:",
            options=step_keys,
            format_func=lambda x: step_labels[step_keys.index(x)],
            index=selected_index
        )
        
        st.session_state.active_step_id = selected_step
        
        # 選択されたステップの実行パネル
        step_execution_panel(workflow, selected_step)
        
        # 全ステップ実行ボタン
        all_steps_col1, all_steps_col2 = st.columns([1, 1])
        
        with all_steps_col1:
            if st.button("すべてのステップを実行", key="run_all"):
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
        
        with all_steps_col2:
            if st.button("ワークフローをリセット", key="reset_workflow"):
                workflow.reset_workflow()
                workflow.set_data("input_df", df)
                st.success("ワークフローがリセットされました。")
    
    # パラメータタブ
    with tab_params:
        st.header("分析パラメータ")
        
        # パラメータ調整用のタブ
        param_tab1, param_tab2, param_tab3 = st.tabs([
            "風推定パラメータ", 
            "戦略検出パラメータ", 
            "パフォーマンス分析パラメータ"
        ])
        
        with param_tab1:
            parameter_adjustment_panel(
                params_manager, 
                ParameterNamespace.WIND_ESTIMATION
            )
        
        with param_tab2:
            parameter_adjustment_panel(
                params_manager, 
                ParameterNamespace.STRATEGY_DETECTION
            )
        
        with param_tab3:
            parameter_adjustment_panel(
                params_manager, 
                ParameterNamespace.PERFORMANCE_ANALYSIS
            )
    
    # 結果タブ
    with tab_results:
        st.header("分析結果")
        
        result_tab1, result_tab2, result_tab3, result_tab4, result_tab5 = st.tabs([
            "データ概要", 
            "風推定結果", 
            "戦略検出結果", 
            "パフォーマンス分析", 
            "レポート"
        ])
        
        with result_tab1:
            stats = workflow.get_data("stats")
            processed_df = workflow.get_data("processed_df")
            
            if stats:
                st.subheader("データ統計")
                st.write(f"元データ行数: {stats.get('original_rows', 0)}")
                st.write(f"処理後行数: {stats.get('processed_rows', 0)}")
                st.write(f"除外された行: {stats.get('removed_rows', 0)}")
            
            if processed_df is not None:
                st.subheader("処理済みデータプレビュー")
                st.dataframe(processed_df.head(10))
                
                if len(processed_df) > 10:
                    with st.expander("すべてのデータを表示", expanded=False):
                        st.dataframe(processed_df)
        
        with result_tab2:
            result_display_panel(
                workflow, 
                "wind_result", 
                "風推定結果", 
                wind_estimation_result_formatter
            )
        
        with result_tab3:
            result_display_panel(
                workflow, 
                "strategy_result", 
                "戦略検出結果", 
                strategy_detection_result_formatter
            )
        
        with result_tab4:
            result_display_panel(
                workflow, 
                "performance_result", 
                "パフォーマンス分析結果", 
                performance_analysis_result_formatter
            )
        
        with result_tab5:
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
                
                # レポートのエクスポート（JSONとしてダウンロード）
                if st.button("レポートをダウンロード", key="download_report"):
                    # レポートをJSON文字列に変換
                    report_json = json.dumps(report, indent=2)
                    
                    # ダウンロードリンクの生成
                    st.download_button(
                        label="JSONとして保存",
                        data=report_json,
                        file_name=f"sailing_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
            else:
                st.info("レポートデータが見つかりません。レポート作成ステップを実行してください。")
