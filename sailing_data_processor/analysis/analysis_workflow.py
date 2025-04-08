"""
分析ワークフローコントローラーモジュール

このモジュールは分析ステップの定義と管理、前提条件のチェック、
処理状態の追跡と管理機能を提供します。分析モジュール間の連携と
一貫したワークフローの実現を可能にします。
"""

import logging
import inspect
from typing import Dict, List, Tuple, Any, Optional, Callable, Union, Set
from enum import Enum
import time
from datetime import datetime
import pandas as pd

# ステータスの定義
class AnalysisStatus(Enum):
    """分析ステップの状態を表す列挙型"""
    NOT_STARTED = "未開始"
    IN_PROGRESS = "処理中"
    COMPLETED = "完了"
    FAILED = "失敗"
    SKIPPED = "スキップ"

class AnalysisStep:
    """
    分析ステップを表すクラス
    
    各分析ステップの情報と状態を管理します。
    """
    
    def __init__(self, 
                 step_id: str, 
                 name: str, 
                 description: str,
                 function: Callable,
                 required_input_keys: List[str] = None,
                 produces_output_keys: List[str] = None,
                 dependencies: List[str] = None):
        """
        初期化
        
        Parameters:
        -----------
        step_id : str
            ステップID
        name : str
            ステップ名
        description : str
            ステップの説明
        function : Callable
            ステップを実行する関数
        required_input_keys : List[str], optional
            必要な入力キーのリスト
        produces_output_keys : List[str], optional
            生成する出力キーのリスト
        dependencies : List[str], optional
            依存するステップIDのリスト
        """
        self.step_id = step_id
        self.name = name
        self.description = description
        self.function = function
        self.required_input_keys = required_input_keys or []
        self.produces_output_keys = produces_output_keys or []
        self.dependencies = dependencies or []
        
        # 状態情報
        self.status = AnalysisStatus.NOT_STARTED
        self.start_time = None
        self.end_time = None
        self.runtime_seconds = None
        self.error_message = None
        self.warnings = []
        
    def reset(self):
        """ステップの状態をリセット"""
        self.status = AnalysisStatus.NOT_STARTED
        self.start_time = None
        self.end_time = None
        self.runtime_seconds = None
        self.error_message = None
        self.warnings = []
        
    def to_dict(self) -> Dict[str, Any]:
        """ステップ情報を辞書に変換"""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "required_input_keys": self.required_input_keys,
            "produces_output_keys": self.produces_output_keys,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "runtime_seconds": self.runtime_seconds,
            "error_message": self.error_message,
            "warnings": self.warnings
        }

class AnalysisWorkflowController:
    """
    分析ワークフローコントローラー
    
    分析ステップを管理し、依存関係を考慮した実行制御を行います。
    """
    
    def __init__(self, namespace: str = "analysis_workflow"):
        """
        初期化
        
        Parameters:
        -----------
        namespace : str, optional
            データ保存に使用する名前空間
        """
        self.namespace = namespace
        self.steps: Dict[str, AnalysisStep] = {}
        self.step_order: List[str] = []
        self.data_context: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"{__name__}.{namespace}")
        
        # 実行状態
        self.current_step_id = None
        self.start_time = None
        self.end_time = None
        self.execution_logs = []
    
    def add_step(self, step: AnalysisStep) -> None:
        """
        ワークフローにステップを追加
        
        Parameters:
        -----------
        step : AnalysisStep
            追加するステップ
        """
        if step.step_id in self.steps:
            self.logger.warning(f"ステップID '{step.step_id}'は既に存在します。上書きします。")
        
        self.steps[step.step_id] = step
        
        # 明示的に順序が設定されていなければステップを末尾に追加
        if step.step_id not in self.step_order:
            self.step_order.append(step.step_id)
    
    def set_step_order(self, step_ids: List[str]) -> None:
        """
        ステップの実行順序を設定
        
        Parameters:
        -----------
        step_ids : List[str]
            ステップIDの順序付きリスト
        """
        # 全てのステップが存在するか確認
        missing_steps = [step_id for step_id in step_ids if step_id not in self.steps]
        if missing_steps:
            raise ValueError(f"存在しないステップが指定されています: {missing_steps}")
        
        # 全てのステップが含まれているか確認
        all_steps = set(self.steps.keys())
        ordered_steps = set(step_ids)
        
        if all_steps != ordered_steps:
            missing = all_steps - ordered_steps
            self.logger.warning(f"一部のステップが順序指定に含まれていません: {missing}")
        
        # 順序を更新
        self.step_order = step_ids
    
    def validate_dependencies(self) -> List[str]:
        """
        ステップの依存関係を検証
        
        Returns:
        --------
        List[str]
            見つかった問題点のリスト
        """
        issues = []
        
        # 依存関係の循環検出
        visited = set()
        temp_marked = set()
        
        # トポロジカルソートの実装
        def visit(step_id: str) -> bool:
            if step_id in temp_marked:
                # 循環依存を検出
                issues.append(f"循環依存が検出されました: {step_id}")
                return False
                
            if step_id in visited:
                return True
                
            temp_marked.add(step_id)
            
            # 依存するステップを確認
            for dep_id in self.steps[step_id].dependencies:
                if dep_id not in self.steps:
                    issues.append(f"ステップ '{step_id}' は存在しないステップ '{dep_id}' に依存しています")
                else:
                    visit(dep_id)
            
            temp_marked.remove(step_id)
            visited.add(step_id)
            return True
        
        # 全てのステップの依存関係を検証
        for step_id in self.steps:
            if step_id not in visited:
                visit(step_id)
        
        # 出力と入力の整合性を検証
        for step_id, step in self.steps.items():
            # 依存するステップの出力が、このステップの入力として使用できるか検証
            required_inputs = set(step.required_input_keys)
            available_outputs = set()
            
            # 依存するステップの出力を収集
            for dep_id in step.dependencies:
                if dep_id in self.steps:
                    available_outputs.update(self.steps[dep_id].produces_output_keys)
            
            # 入力が満たされるか確認
            missing_inputs = required_inputs - available_outputs
            if missing_inputs:
                issues.append(f"ステップ '{step_id}' には依存関係から提供されない入力があります: {missing_inputs}")
        
        return issues
    
    def optimize_step_order(self) -> None:
        """依存関係に基づいてステップの実行順序を最適化"""
        # 依存関係からトポロジカルソートを実施
        visited = set()
        temp_marked = set()
        ordered_steps = []
        
        def visit(step_id: str) -> None:
            if step_id in temp_marked:
                raise ValueError(f"循環依存が検出されました: {step_id}")
                
            if step_id in visited:
                return
                
            temp_marked.add(step_id)
            
            # 依存するステップを先に処理
            for dep_id in self.steps[step_id].dependencies:
                if dep_id in self.steps:
                    visit(dep_id)
            
            temp_marked.remove(step_id)
            visited.add(step_id)
            ordered_steps.append(step_id)
        
        # 全てのステップをトポロジカルソート
        for step_id in self.steps:
            if step_id not in visited:
                visit(step_id)
        
        # 最適化された順序を設定
        self.step_order = ordered_steps
    
    def check_prerequisites(self, step_id: str) -> Tuple[bool, List[str]]:
        """
        ステップの前提条件を確認
        
        Parameters:
        -----------
        step_id : str
            確認するステップID
            
        Returns:
        --------
        Tuple[bool, List[str]]
            (前提条件を満たすか, 満たさない前提条件のリスト)
        """
        if step_id not in self.steps:
            return False, [f"ステップ '{step_id}' は存在しません"]
        
        step = self.steps[step_id]
        missing_prerequisites = []
        
        # 依存するステップが完了しているか確認
        for dep_id in step.dependencies:
            if dep_id not in self.steps:
                missing_prerequisites.append(f"依存ステップ '{dep_id}' は存在しません")
            elif self.steps[dep_id].status != AnalysisStatus.COMPLETED:
                missing_prerequisites.append(f"依存ステップ '{dep_id}' は完了していません (現在の状態: {self.steps[dep_id].status.value})")
        
        # 必要な入力データがあるか確認
        for input_key in step.required_input_keys:
            if input_key not in self.data_context:
                missing_prerequisites.append(f"必要な入力データ '{input_key}' がありません")
        
        return len(missing_prerequisites) == 0, missing_prerequisites
    
    def run_step(self, step_id: str, force: bool = False) -> bool:
        """
        個別のステップを実行
        
        Parameters:
        -----------
        step_id : str
            実行するステップID
        force : bool, optional
            前提条件を無視して強制実行するか
            
        Returns:
        --------
        bool
            実行が成功したかどうか
        """
        if step_id not in self.steps:
            self.logger.error(f"ステップ '{step_id}' は存在しません")
            return False
        
        step = self.steps[step_id]
        
        # すでに完了している場合はスキップ（forceが指定されていない場合）
        if step.status == AnalysisStatus.COMPLETED and not force:
            self.logger.info(f"ステップ '{step_id}' はすでに完了しています。スキップします。")
            return True
        
        # 前提条件の確認
        prerequisites_ok, missing = self.check_prerequisites(step_id)
        if not prerequisites_ok and not force:
            self.logger.warning(f"ステップ '{step_id}' の前提条件が満たされていません: {missing}")
            step.status = AnalysisStatus.SKIPPED
            step.error_message = f"前提条件が満たされていません: {missing}"
            return False
        
        # ステップの実行開始
        step.reset()
        step.status = AnalysisStatus.IN_PROGRESS
        step.start_time = datetime.now()
        self.current_step_id = step_id
        
        self.logger.info(f"ステップ '{step_id}: {step.name}' を開始します")
        
        try:
            # 関数の引数を準備
            func_params = self._prepare_function_params(step.function, self.data_context)
            
            # 関数を実行
            result = step.function(**func_params)
            
            # 結果を処理
            if isinstance(result, dict):
                # 辞書の場合はデータコンテキストに追加
                for key, value in result.items():
                    self.data_context[key] = value
            elif result is not None:
                # 単一の値の場合はステップIDをキーとして保存
                self.data_context[step_id] = result
            
            # ステップを完了としてマーク
            step.status = AnalysisStatus.COMPLETED
            step.end_time = datetime.now()
            step.runtime_seconds = (step.end_time - step.start_time).total_seconds()
            
            self.logger.info(f"ステップ '{step_id}: {step.name}' が完了しました (所要時間: {step.runtime_seconds:.2f}秒)")
            return True
            
        except Exception as e:
            # エラー処理
            step.status = AnalysisStatus.FAILED
            step.end_time = datetime.now()
            step.runtime_seconds = (step.end_time - step.start_time).total_seconds()
            step.error_message = str(e)
            
            self.logger.exception(f"ステップ '{step_id}: {step.name}' が失敗しました: {e}")
            return False
        finally:
            # 実行情報を記録
            self.execution_logs.append({
                "step_id": step_id,
                "status": step.status.value,
                "time": datetime.now().isoformat(),
                "runtime_seconds": step.runtime_seconds
            })
            self.current_step_id = None
    
    def run_workflow(self, start_from: str = None, stop_at: str = None, ignore_errors: bool = False) -> Dict[str, Any]:
        """
        ワークフロー全体を実行
        
        Parameters:
        -----------
        start_from : str, optional
            開始するステップID
        stop_at : str, optional
            終了するステップID
        ignore_errors : bool, optional
            エラーを無視して続行するか
            
        Returns:
        --------
        Dict[str, Any]
            実行結果の概要
        """
        # ワークフロー実行開始
        self.start_time = datetime.now()
        self.logger.info(f"ワークフロー '{self.namespace}' の実行を開始します")
        
        # 開始位置の設定
        if start_from and start_from in self.step_order:
            start_idx = self.step_order.index(start_from)
        else:
            start_idx = 0
            
        # 終了位置の設定
        if stop_at and stop_at in self.step_order:
            stop_idx = self.step_order.index(stop_at)
        else:
            stop_idx = len(self.step_order) - 1
        
        # 実行するステップの範囲を抽出
        steps_to_run = self.step_order[start_idx:stop_idx+1]
        total_steps = len(steps_to_run)
        completed_steps = 0
        failed_steps = 0
        
        # 各ステップを実行
        for i, step_id in enumerate(steps_to_run):
            self.logger.info(f"ワークフロー進捗: {i+1}/{total_steps} - ステップ '{step_id}'")
            
            success = self.run_step(step_id)
            
            if success:
                completed_steps += 1
            else:
                failed_steps += 1
                if not ignore_errors:
                    self.logger.error(f"エラーが発生したためワークフローを停止します (ステップ '{step_id}')")
                    break
        
        # ワークフロー実行完了
        self.end_time = datetime.now()
        runtime_seconds = (self.end_time - self.start_time).total_seconds()
        
        self.logger.info(f"ワークフロー '{self.namespace}' の実行が完了しました "
                         f"(所要時間: {runtime_seconds:.2f}秒, "
                         f"完了: {completed_steps}/{total_steps}, "
                         f"失敗: {failed_steps}/{total_steps})")
        
        # 結果の概要を返す
        return {
            "namespace": self.namespace,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "runtime_seconds": runtime_seconds,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "success_rate": completed_steps / total_steps if total_steps > 0 else 0,
            "steps_summary": {step_id: self.steps[step_id].status.value for step_id in steps_to_run}
        }
    
    def get_step_status(self, step_id: str) -> Optional[Dict[str, Any]]:
        """
        ステップの状態を取得
        
        Parameters:
        -----------
        step_id : str
            ステップID
            
        Returns:
        --------
        Optional[Dict[str, Any]]
            ステップの状態情報
        """
        if step_id not in self.steps:
            return None
        
        return self.steps[step_id].to_dict()
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        ワークフロー全体の状態を取得
        
        Returns:
        --------
        Dict[str, Any]
            ワークフローの状態情報
        """
        completed = sum(1 for step in self.steps.values() if step.status == AnalysisStatus.COMPLETED)
        failed = sum(1 for step in self.steps.values() if step.status == AnalysisStatus.FAILED)
        in_progress = sum(1 for step in self.steps.values() if step.status == AnalysisStatus.IN_PROGRESS)
        not_started = sum(1 for step in self.steps.values() if step.status == AnalysisStatus.NOT_STARTED)
        skipped = sum(1 for step in self.steps.values() if step.status == AnalysisStatus.SKIPPED)
        
        total = len(self.steps)
        
        return {
            "namespace": self.namespace,
            "total_steps": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "not_started": not_started,
            "skipped": skipped,
            "progress_percentage": (completed / total) * 100 if total > 0 else 0,
            "current_step": self.current_step_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "runtime_seconds": (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else None,
            "execution_logs": self.execution_logs[-10:] if self.execution_logs else []  # 最新の10件のログ
        }
    
    def reset_workflow(self) -> None:
        """ワークフローの状態をリセット"""
        for step in self.steps.values():
            step.reset()
        
        self.data_context = {}
        self.current_step_id = None
        self.start_time = None
        self.end_time = None
        self.execution_logs = []
        
        self.logger.info(f"ワークフロー '{self.namespace}' をリセットしました")
    
    def get_data(self, key: str) -> Any:
        """
        データコンテキストから値を取得
        
        Parameters:
        -----------
        key : str
            データキー
            
        Returns:
        --------
        Any
            データ値
        """
        return self.data_context.get(key)
    
    def set_data(self, key: str, value: Any) -> None:
        """
        データコンテキストに値を設定
        
        Parameters:
        -----------
        key : str
            データキー
        value : Any
            データ値
        """
        self.data_context[key] = value
    
    def get_available_data_keys(self) -> List[str]:
        """
        利用可能なデータキーのリストを取得
        
        Returns:
        --------
        List[str]
            データキーのリスト
        """
        return list(self.data_context.keys())
    
    def _prepare_function_params(self, func: Callable, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        関数の引数を準備
        
        Parameters:
        -----------
        func : Callable
            対象の関数
        data_context : Dict[str, Any]
            データコンテキスト
            
        Returns:
        --------
        Dict[str, Any]
            関数に渡す引数の辞書
        """
        params = {}
        
        # 関数の引数情報を取得
        sig = inspect.signature(func)
        
        for param_name, param in sig.parameters.items():
            if param_name in data_context:
                params[param_name] = data_context[param_name]
            elif param.default is not inspect.Parameter.empty:
                # デフォルト値がある場合はスキップ
                continue
            else:
                # 必須パラメータが見つからない場合は警告
                self.logger.warning(f"関数 {func.__name__} の必須パラメータ '{param_name}' がデータコンテキストに見つかりません")
        
        return params
