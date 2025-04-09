"""
ワークフローコントローラーモジュール

このモジュールはUI層と分析ワークフローエンジンを結合し、
分析ワークフローの制御と状態管理を行います。
"""

import logging
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime
import json
import copy

import streamlit as st
import pandas as pd

from sailing_data_processor.analysis.analysis_workflow import (
    AnalysisWorkflowController, AnalysisStep, AnalysisStatus
)
from sailing_data_processor.analysis.analysis_parameters import ParametersManager, ParameterNamespace
from sailing_data_processor.analysis.analysis_cache import AnalysisCache
from sailing_data_processor.analysis.integrated_wind_estimator import IntegratedWindEstimator
from sailing_data_processor.analysis.integrated_strategy_detector import IntegratedStrategyDetector
from sailing_data_processor.analysis.integrated_performance_analyzer import IntegratedPerformanceAnalyzer
from sailing_data_processor.storage.storage_interface import StorageInterface
from sailing_data_processor.storage.browser_storage import BrowserStorage


logger = logging.getLogger(__name__)


class IntegratedWorkflowController:
    """
    統合ワークフローコントローラークラス
    
    UI層と分析エンジンを結合し、ワークフローの実行と状態管理を行います。
    """
    
    def __init__(self, 
                 storage: Optional[StorageInterface] = None,
                 namespace: str = "integrated_workflow"):
        """
        初期化
        
        Parameters:
        -----------
        storage : StorageInterface, optional
            ストレージインターフェース
        namespace : str, optional
            コントローラーの名前空間
        """
        self.namespace = namespace
        self.storage = storage
        
        # パラメータとキャッシュの初期化
        self.params_manager = ParametersManager(storage_interface=storage)
        self.analysis_cache = AnalysisCache(storage_interface=storage)
        
        # 分析モジュールのインスタンス
        self.wind_estimator = IntegratedWindEstimator(self.params_manager, self.analysis_cache)
        self.strategy_detector = IntegratedStrategyDetector(self.params_manager, self.analysis_cache, self.wind_estimator)
        self.performance_analyzer = IntegratedPerformanceAnalyzer(self.params_manager, self.analysis_cache, self.wind_estimator)
        
        # ワークフローコントローラー
        self.workflow = None
        
        # バックグラウンド実行のためのスレッド
        self.background_thread = None
        self.background_status = {}
        
        # 状態フラグ
        self.is_initialized = False
        self.is_running = False
        
        # 進捗コールバック
        self.progress_callback = None
        
        logger.info(f"統合ワークフローコントローラーを初期化しました (namespace: {namespace})")
    
    def initialize(self, session_data: Dict[str, Any]) -> bool:
        """
        ワークフローを初期化
        
        Parameters:
        -----------
        session_data : Dict[str, Any]
            セッションデータ（必要なデータフレームを含む）
            
        Returns:
        --------
        bool
            初期化が成功したか
        """
        try:
            # セッションデータの検証
            if 'current_session_df' not in session_data or session_data['current_session_df'] is None:
                logger.warning("セッションデータが見つからないため初期化できません")
                return False
            
            # データフレームの取得
            df = session_data['current_session_df']
            
            # ストレージからパラメータをロード（必要に応じて）
            if self.storage and hasattr(self.params_manager, 'load_from_storage'):
                self.params_manager.load_from_storage()
            
            # ワークフローの作成
            self.workflow = self._create_workflow(df)
            
            # 状態を更新
            self.is_initialized = True
            
            logger.info("ワークフローを初期化しました")
            return True
            
        except Exception as e:
            logger.exception(f"ワークフロー初期化中にエラーが発生しました: {str(e)}")
            return False
    
    def _create_workflow(self, df: pd.DataFrame) -> AnalysisWorkflowController:
        """
        ワークフローオブジェクトを作成
        
        Parameters:
        -----------
        df : pd.DataFrame
            分析対象のデータフレーム
            
        Returns:
        --------
        AnalysisWorkflowController
            作成されたワークフローコントローラー
        """
        # ワークフローコントローラーの作成
        workflow = AnalysisWorkflowController(namespace=self.namespace)
        
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
            result = self.wind_estimator.estimate_wind(processed_df)
            return {"wind_result": result}
        
        # 戦略検出ステップの定義
        def detect_strategy_points(processed_df, wind_result):
            """戦略的判断ポイントを検出する"""
            result = self.strategy_detector.detect_strategy_points(processed_df)
            return {"strategy_result": result}
        
        # パフォーマンス分析ステップの定義
        def analyze_performance(processed_df, wind_result):
            """パフォーマンス分析を実行する"""
            result = self.performance_analyzer.analyze_performance(processed_df)
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
            logger.warning(f"ワークフロー依存関係の問題: {issues}")
        
        # ワークフロー順序の最適化
        workflow.optimize_step_order()
        
        return workflow
    
    def run_step(self, step_id: str, force: bool = False) -> Dict[str, Any]:
        """
        特定のステップを実行
        
        Parameters:
        -----------
        step_id : str
            実行するステップID
        force : bool, optional
            前提条件を無視して強制実行するか
            
        Returns:
        --------
        Dict[str, Any]
            実行結果
        """
        if not self.is_initialized or self.workflow is None:
            logger.warning("ワークフローが初期化されていないため実行できません")
            return {"error": "ワークフローが初期化されていません"}
        
        if self.is_running:
            logger.warning("別のワークフロー処理が実行中です")
            return {"error": "別の処理が実行中です"}
        
        try:
            # 実行状態を更新
            self.is_running = True
            
            # ステップの実行
            success = self.workflow.run_step(step_id, force=force)
            
            # ステップ状態の取得
            step_status = self.workflow.get_step_status(step_id)
            
            # 実行状態を更新
            self.is_running = False
            
            # 結果をキャッシュ（必要に応じて）
            self._save_workflow_state()
            
            return {
                "success": success,
                "step_status": step_status,
                "workflow_status": self.workflow.get_workflow_status()
            }
            
        except Exception as e:
            logger.exception(f"ステップ'{step_id}'の実行中にエラーが発生しました: {str(e)}")
            self.is_running = False
            return {
                "success": False,
                "error": str(e),
                "workflow_status": self.workflow.get_workflow_status() if self.workflow else {}
            }
    
    def run_workflow_in_background(self, 
                                  start_from: str = None, 
                                  stop_at: str = None, 
                                  progress_callback: Callable = None) -> bool:
        """
        ワークフロー全体をバックグラウンドで実行
        
        Parameters:
        -----------
        start_from : str, optional
            開始するステップID
        stop_at : str, optional
            終了するステップID
        progress_callback : Callable, optional
            進捗を報告するコールバック関数
            
        Returns:
        --------
        bool
            実行開始が成功したか
        """
        if not self.is_initialized or self.workflow is None:
            logger.warning("ワークフローが初期化されていないため実行できません")
            return False
        
        if self.is_running or (self.background_thread is not None and self.background_thread.is_alive()):
            logger.warning("すでにバックグラウンド処理が実行中です")
            return False
        
        # コールバックの設定
        self.progress_callback = progress_callback
        
        # バックグラウンド状態の初期化
        self.background_status = {
            "running": True,
            "step_id": None,
            "progress": 0.0,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "result": None,
            "error": None
        }
        
        # バックグラウンドスレッドの開始
        self.background_thread = threading.Thread(
            target=self._run_workflow_thread,
            args=(start_from, stop_at),
            daemon=True  # バックグラウンドスレッドとして実行
        )
        self.background_thread.start()
        
        logger.info(f"ワークフローのバックグラウンド実行を開始しました (start={start_from}, stop={stop_at})")
        return True
    
    def _run_workflow_thread(self, start_from: str = None, stop_at: str = None) -> None:
        """
        ワークフローを別スレッドで実行するための内部メソッド
        
        Parameters:
        -----------
        start_from : str, optional
            開始するステップID
        stop_at : str, optional
            終了するステップID
        """
        try:
            # 実行状態を更新
            self.is_running = True
            
            # 開始位置の設定
            if start_from and start_from in self.workflow.step_order:
                start_idx = self.workflow.step_order.index(start_from)
            else:
                start_idx = 0
                
            # 終了位置の設定
            if stop_at and stop_at in self.workflow.step_order:
                stop_idx = self.workflow.step_order.index(stop_at)
            else:
                stop_idx = len(self.workflow.step_order) - 1
            
            # 実行するステップの範囲を抽出
            steps_to_run = self.workflow.step_order[start_idx:stop_idx+1]
            total_steps = len(steps_to_run)
            completed_steps = 0
            
            # 各ステップを実行
            for i, step_id in enumerate(steps_to_run):
                # 現在のステップを状態に記録
                self.background_status["step_id"] = step_id
                self.background_status["progress"] = i / total_steps
                
                # 進捗をコールバック（設定されている場合）
                if self.progress_callback:
                    self.progress_callback(self.background_status)
                
                # ステップの実行
                success = self.workflow.run_step(step_id)
                
                if success:
                    completed_steps += 1
                else:
                    # エラー情報を記録
                    step = self.workflow.steps.get(step_id)
                    if step:
                        self.background_status["error"] = step.error_message
                    else:
                        self.background_status["error"] = f"ステップ '{step_id}' の実行に失敗しました"
                    
                    # 進捗をコールバック（設定されている場合）
                    if self.progress_callback:
                        self.progress_callback(self.background_status)
                    
                    break
            
            # 実行結果の記録
            self.background_status["running"] = False
            self.background_status["progress"] = 1.0
            self.background_status["end_time"] = datetime.now().isoformat()
            self.background_status["result"] = {
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "success_rate": completed_steps / total_steps if total_steps > 0 else 0,
                "workflow_status": self.workflow.get_workflow_status()
            }
            
            # 最終進捗をコールバック（設定されている場合）
            if self.progress_callback:
                self.progress_callback(self.background_status)
            
            # 結果をキャッシュ（必要に応じて）
            self._save_workflow_state()
            
        except Exception as e:
            logger.exception(f"バックグラウンドワークフロー実行中にエラーが発生しました: {str(e)}")
            
            # エラー情報を記録
            self.background_status["running"] = False
            self.background_status["end_time"] = datetime.now().isoformat()
            self.background_status["error"] = str(e)
            
            # エラー進捗をコールバック（設定されている場合）
            if self.progress_callback:
                self.progress_callback(self.background_status)
                
        finally:
            # 実行状態を更新
            self.is_running = False
    
    def get_background_status(self) -> Dict[str, Any]:
        """
        バックグラウンド実行の状態を取得
        
        Returns:
        --------
        Dict[str, Any]
            バックグラウンド実行の状態情報
        """
        # スレッドがアクティブかどうかを確認
        if self.background_thread is not None:
            self.background_status["thread_alive"] = self.background_thread.is_alive()
        else:
            self.background_status["thread_alive"] = False
        
        return self.background_status
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        ワークフローの状態を取得
        
        Returns:
        --------
        Dict[str, Any]
            ワークフローの状態情報
        """
        if not self.is_initialized or self.workflow is None:
            return {"initialized": False}
        
        return {
            "initialized": True,
            "running": self.is_running,
            "workflow": self.workflow.get_workflow_status()
        }
    
    def reset_workflow(self) -> bool:
        """
        ワークフローの状態をリセット
        
        Returns:
        --------
        bool
            リセットが成功したか
        """
        if not self.is_initialized or self.workflow is None:
            logger.warning("ワークフローが初期化されていないためリセットできません")
            return False
        
        if self.is_running:
            logger.warning("実行中のワークフローはリセットできません")
            return False
        
        try:
            # 入力データの保持
            input_df = self.workflow.get_data("input_df")
            
            # ワークフローのリセット
            self.workflow.reset_workflow()
            
            # 入力データの再設定
            if input_df is not None:
                self.workflow.set_data("input_df", input_df)
            
            logger.info("ワークフローをリセットしました")
            return True
            
        except Exception as e:
            logger.exception(f"ワークフローのリセット中にエラーが発生しました: {str(e)}")
            return False
    
    def _save_workflow_state(self) -> None:
        """ワークフローの状態を保存（内部メソッド）"""
        if self.storage and hasattr(self.params_manager, 'save_to_storage'):
            try:
                # パラメータの保存
                self.params_manager.save_to_storage()
                
                # ワークフロー状態のシリアライズと保存（必要に応じて）
                if hasattr(self.storage, 'set_item'):
                    workflow_status = self.workflow.get_workflow_status()
                    self.storage.set_item(f"{self.namespace}_workflow_status", json.dumps(workflow_status))
                
                logger.debug("ワークフロー状態を保存しました")
                
            except Exception as e:
                logger.warning(f"ワークフロー状態の保存中にエラーが発生しました: {str(e)}")
    
    def get_results(self) -> Dict[str, Any]:
        """
        ワークフローから得られた結果を取得
        
        Returns:
        --------
        Dict[str, Any]
            各ステップの結果
        """
        if not self.is_initialized or self.workflow is None:
            return {}
        
        # 結果の取得
        results = {}
        
        # 各データキーの値を取得
        for key in self.workflow.get_available_data_keys():
            # レポートと結果系のキーのみを取得
            if key.endswith('_result') or key == 'report' or key == 'stats':
                results[key] = self.workflow.get_data(key)
        
        # 処理済みデータフレームも取得（オプション）
        processed_df = self.workflow.get_data("processed_df")
        if processed_df is not None:
            # データフレームはそのまま返すとサイズが大きくなるため、
            # 必要に応じて簡略化した情報のみを返す
            results["processed_df_info"] = {
                "rows": len(processed_df),
                "columns": list(processed_df.columns),
                "start_time": processed_df['timestamp'].min().isoformat() if 'timestamp' in processed_df.columns else None,
                "end_time": processed_df['timestamp'].max().isoformat() if 'timestamp' in processed_df.columns else None
            }
        
        return results
