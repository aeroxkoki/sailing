# -*- coding: utf-8 -*-
"""
sailing_data_processor.validation.correction

データ修正操作を実装するモジュール
"""

from typing import Dict, List, Any, Optional, Tuple, Union, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import uuid
from copy import deepcopy

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.data_cleaner import FixProposal, DataCleaner
try:
    # 拡張されたメトリクス計算器を優先的に使用
    from sailing_data_processor.validation.quality_metrics_integration import EnhancedQualityMetricsCalculator as MetricsCalculator
except ImportError:
    # フォールバックとして基本メトリクス計算器を使用
    from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator as MetricsCalculator


class CorrectionProcessor:
    """
    高度なデータ修正処理を実行するクラス
    
    DataCleanerと連携して修正処理を視覚的にサポートし、インタラクティブな修正インターフェースを提供します。
    """
    
    def __init__(self, cleaner: Optional[DataCleaner] = None):
        """
        初期化
        
        Parameters
        ----------
        cleaner : Optional[DataCleaner]
            データクリーナーオブジェクト
        """
        self.cleaner = cleaner
        self.last_correction = None
        self.correction_history = []
    
    def set_cleaner(self, cleaner: DataCleaner) -> None:
        """
        データクリーナーを設定
        
        Parameters
        ----------
        cleaner : DataCleaner
            データクリーナーオブジェクト
        """
        self.cleaner = cleaner
    
    def get_correction_options(self, problem_type: str) -> List[Dict[str, Any]]:
        """
        問題タイプに基づいた修正オプションを取得
        
        Parameters
        ----------
        problem_type : str
            問題タイプ ('missing_data', 'out_of_range', 'duplicates', 'spatial_anomalies', 'temporal_anomalies')
            
        Returns
        -------
        List[Dict[str, Any]]
            修正オプションのリスト
        """
        if self.cleaner is None:
            return []
        
        # 問題タイプに対応する修正オプションのマッピング
        options_mapping = {
            "missing_data": [
                {
                    "id": "interpolate_linear",
                    "name": "線形補間",
                    "description": "前後の値から欠損値を補間します",
                    "fix_type": "interpolate",
                    "params": {"method": "linear"}
                },
                {
                    "id": "interpolate_time",
                    "name": "時間ベース補間",
                    "description": "時間の経過に基づいて補間します",
                    "fix_type": "interpolate",
                    "params": {"method": "time"}
                },
                {
                    "id": "fill_forward",
                    "name": "前方向に埋める",
                    "description": "直前の値で欠損値を埋めます",
                    "fix_type": "interpolate",
                    "params": {"method": "ffill"}
                },
                {
                    "id": "fill_backward",
                    "name": "後方向に埋める",
                    "description": "直後の値で欠損値を埋めます",
                    "fix_type": "interpolate",
                    "params": {"method": "bfill"}
                },
                {
                    "id": "remove_rows",
                    "name": "行を削除",
                    "description": "欠損値を含む行を削除します",
                    "fix_type": "remove",
                    "params": {}
            ],
            "out_of_range": [
                {
                    "id": "clip_values",
                    "name": "値を制限",
                    "description": "範囲外の値を最小値または最大値に制限します",
                    "fix_type": "replace",
                    "params": {"method": "clip"}
                },
                {
                    "id": "replace_with_null",
                    "name": "NULLに置換",
                    "description": "範囲外の値をNULLに置き換えます",
                    "fix_type": "replace",
                    "params": {"method": "null"}
                },
                {
                    "id": "remove_rows",
                    "name": "行を削除",
                    "description": "範囲外の値を含む行を削除します",
                    "fix_type": "remove",
                    "params": {}
            ],
            "duplicates": [
                {
                    "id": "offset_timestamps",
                    "name": "タイムスタンプをずらす",
                    "description": "重複するタイムスタンプを少しずつずらします",
                    "fix_type": "adjust",
                    "params": {"method": "offset"}
                },
                {
                    "id": "keep_first",
                    "name": "最初の行を保持",
                    "description": "重複するうち最初の行のみを保持します",
                    "fix_type": "remove",
                    "params": {"method": "keep_first"}
                },
                {
                    "id": "remove_all",
                    "name": "すべて削除",
                    "description": "重複するタイムスタンプを持つ行をすべて削除します",
                    "fix_type": "remove",
                    "params": {"method": "remove_all"}
            ],
            "spatial_anomalies": [
                {
                    "id": "spatial_interpolate",
                    "name": "位置を補間",
                    "description": "異常な位置を前後のポイントから補間します",
                    "fix_type": "interpolate",
                    "params": {"columns": ["latitude", "longitude"]}
                },
                {
                    "id": "spatial_remove",
                    "name": "異常ポイントを削除",
                    "description": "空間的に異常なポイントを削除します",
                    "fix_type": "remove",
                    "params": {}
            ],
            "temporal_anomalies": [
                {
                    "id": "remove_reverse",
                    "name": "逆行を削除",
                    "description": "タイムスタンプが逆行しているポイントを削除します",
                    "fix_type": "remove",
                    "params": {"filter": "reverse"}
                },
                {
                    "id": "fix_timestamps",
                    "name": "タイムスタンプを修正",
                    "description": "タイムスタンプが逆行している場合に修正します",
                    "fix_type": "adjust",
                    "params": {"method": "fix_reverse"}
                },
                {
                    "id": "mark_gaps",
                    "name": "ギャップをマーク",
                    "description": "大きな時間ギャップをメタデータにマークします",
                    "fix_type": "metadata",
                    "params": {"method": "mark_gaps"}
            ]
        
        # 問題タイプに対応するオプションを返す
        return options_mapping.get(problem_type, [])
    
    def apply_correction(self, 
                        problem_type: str, 
                        option_id: str, 
                        target_indices: List[int],
                        target_columns: Optional[List[str]] = None,
                        custom_params: Optional[Dict[str, Any]] = None) -> Optional[GPSDataContainer]:
        """
        選択された修正オプションを適用
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        option_id : str
            修正オプションID
        target_indices : List[int]
            対象のインデックスリスト
        target_columns : Optional[List[str]], optional
            対象のカラムリスト
        custom_params : Optional[Dict[str, Any]], optional
            カスタムパラメータ
            
        Returns
        -------
        Optional[GPSDataContainer]
            修正後のデータコンテナ（失敗した場合はNone）
        """
        if self.cleaner is None:
            return None
        
        # オプションの詳細を取得
        options = self.get_correction_options(problem_type)
        selected_option = next((opt for opt in options if opt["id"] == option_id), None)
        
        if selected_option is None:
            return None
        
        # パラメータをマージ
        params = selected_option["params"].copy()
        if custom_params:
            params.update(custom_params)
        
        # 修正対象のカラムを設定
        columns = target_columns or []
        if "columns" in params and not columns:
            columns = params["columns"]
        
        # FixProposalを作成
        description = f"{selected_option['name']} - {selected_option['description']}"
        proposal = FixProposal(
            fix_type=selected_option["fix_type"],
            target_indices=target_indices,
            columns=columns,
            description=description,
            severity="medium",
            auto_fixable=True,
            metadata=params
        )
        
        # 修正を適用
        try:
            fixed_container = self.cleaner.apply_fix(proposal)
            
            # 修正履歴に追加
            self.last_correction = {
                "problem_type": problem_type,
                "option_id": option_id,
                "target_indices": target_indices,
                "target_columns": columns,
                "params": params,
                "proposal": proposal.to_dict(),
                "timestamp": datetime.now().isoformat()
            self.correction_history.append(self.last_correction)
            
            return fixed_container
        except Exception as e:
            print(f"修正適用中にエラーが発生しました: {e}")
            return None
    
    def batch_correct(self, corrections: List[Dict[str, Any]]) -> Optional[GPSDataContainer]:
        """
        バッチ修正を実行
        
        Parameters
        ----------
        corrections : List[Dict[str, Any]]
            修正指定のリスト。各辞書は以下のキーを含む:
            - problem_type: 問題タイプ
            - option_id: 修正オプションID
            - target_indices: 対象のインデックスリスト
            - target_columns (optional): 対象のカラムリスト
            - custom_params (optional): カスタムパラメータ
            
        Returns
        -------
        Optional[GPSDataContainer]
            最終的に修正されたデータコンテナ（失敗した場合はNone）
        """
        if self.cleaner is None:
            return None
        
        fixed_container = self.cleaner.container
        
        for correction in corrections:
            problem_type = correction.get("problem_type")
            option_id = correction.get("option_id")
            target_indices = correction.get("target_indices", [])
            target_columns = correction.get("target_columns")
            custom_params = correction.get("custom_params")
            
            if not problem_type or not option_id or not target_indices:
                continue
            
            # 修正を適用
            temp_cleaner = DataCleaner(self.cleaner.validator, fixed_container)
            processor = CorrectionProcessor(temp_cleaner)
            result = processor.apply_correction(
                problem_type=problem_type,
                option_id=option_id,
                target_indices=target_indices,
                target_columns=target_columns,
                custom_params=custom_params
            )
            
            if result:
                fixed_container = result
            else:
                print(f"修正の適用に失敗しました: {problem_type}, {option_id}")
                # 続行するが、失敗を記録
                self.correction_history.append({
                    "problem_type": problem_type,
                    "option_id": option_id,
                    "target_indices": target_indices,
                    "target_columns": target_columns,
                    "params": custom_params,
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                })
        
        return fixed_container
    
    def get_correction_history(self) -> List[Dict[str, Any]]:
        """
        修正履歴を取得
        
        Returns
        -------
        List[Dict[str, Any]]
            修正履歴のリスト
        """
        return self.correction_history
    
    def get_last_correction(self) -> Optional[Dict[str, Any]]:
        """
        最後に適用された修正を取得
        
        Returns
        -------
        Optional[Dict[str, Any]]
            最後の修正情報（なければNone）
        """
        return self.last_correction


class CorrectionSuggester:
    """
    データ問題に対する修正提案を生成するクラス
    """
    
    def __init__(self, data_validator: DataValidator, container: GPSDataContainer):
        """
        初期化
        
        Parameters
        ----------
        data_validator : DataValidator
            データ検証器
        container : GPSDataContainer
            GPSデータコンテナ
        """
        self.validator = data_validator
        self.container = container
        self.processor = None
        self.cleaner = None
        
        # クリーナーとプロセッサを初期化
        if not self.validator.validation_results:
            self.validator.validate(container)
        
        self.cleaner = DataCleaner(self.validator, container)
        self.processor = CorrectionProcessor(self.cleaner)
        
        # 品質メトリクス計算機を初期化
        self.metrics_calculator = MetricsCalculator(
            validation_results=self.validator.validation_results,
            data=container.data
        )
        # メトリクス計算器はコンストラクタで自動的に初期化されるため、
        # calculate_metrics()の呼び出しは必要ありません
        # ゲッター/セッターメソッドを使用してメトリクスにアクセスします
    
    def generate_fix_proposals(self) -> List[Dict[str, Any]]:
        """
        データ問題に対する修正提案を生成
        
        Returns
        -------
        List[Dict[str, Any]]
            修正提案のリスト
        """
        if not self.cleaner or not self.container:
            return []
        
        proposals = []
        
        # クリーナーから問題情報を取得
        if not hasattr(self.cleaner.cleaner, 'record_issues') or not self.cleaner.cleaner.record_issues:
            return []
        
        record_issues = self.cleaner.cleaner.record_issues
        
        # 問題タイプごとに処理
        problem_types = {
            "missing_data": "欠損値",
            "out_of_range": "範囲外の値",
            "duplicates": "重複タイムスタンプ",
            "spatial_anomalies": "空間的異常",
            "temporal_anomalies": "時間的異常"
        
        for problem_type, display_name in problem_types.items():
            # 問題タイプに対応する問題インデックスを取得
            indices = []
            for idx, issue_data in record_issues.items():
                issue_types = issue_data.get("issues", [])
                if display_name in issue_types:
                    indices.append(idx)
            
            if indices:
                # 同じタイプの問題をバッチ処理するための提案を生成
                batch_proposals = self._generate_batch_proposals(problem_type, indices)
                proposals.extend(batch_proposals)
                
                # 個々の問題に対する提案を生成
                for idx in indices[:10]:  # 最大10件まで個別提案を生成
                    issue = record_issues.get(idx, {})
                    if issue:
                        individual_proposals = self.generate_proposal_for_issue({
                            "index": idx,
                            "type": problem_type,
                            "data": issue
                        })
                        proposals.extend(individual_proposals)
        
        # 優先度でソート
        proposals.sort(key=lambda x: {
            "error": 0,
            "warning": 1,
            "info": 2
        }.get(x.get("severity", "info"), 3))
        
        return proposals
    
    def generate_proposal_for_issue(self, issue: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        特定の問題に対する修正提案を生成
        
        Parameters
        ----------
        issue : Dict[str, Any]
            問題情報
            
        Returns
        -------
        List[Dict[str, Any]]
            修正提案のリスト
        """
        proposals = []
        problem_type = issue.get("type")
        idx = issue.get("index")
        issue_data = issue.get("data", {})
        
        if not problem_type or idx is None:
            return []
        
        # 問題タイプに応じた修正オプションを取得
        correction_options = self.processor.get_correction_options(problem_type)
        
        current_quality = self.metrics_calculator.get_total_quality_score()
        
        # 各修正オプションに対する提案を生成
        for option in correction_options:
            # 提案ID生成
            proposal_id = f"fix_{problem_type}_{option['id']}_{uuid.uuid4().hex[:8]}"
            
            # 適用されるインデックス
            affected_indices = [idx]
            
            # オプションの詳細に基づいて影響を受けるカラムを特定
            affected_column = None
            if problem_type == "missing_data":
                # 欠損値の場合、欠損しているカラムを特定
                if idx < len(self.container.data):
                    record = self.container.data.iloc[idx]
                    missing_cols = record.index[record.isna()].tolist()
                    if missing_cols:
                        affected_column = missing_cols[0]
            elif problem_type == "out_of_range":
                # 範囲外値の場合、問題のあるカラムを特定
                # ここでは簡単のため、問題の説明から推測
                description = issue_data.get("description", "")
                for col in self.container.data.columns:
                    if col in description:
                        affected_column = col
                        break
            
            # 修正方法ごとの提案を生成
            methods = []
            for method_type, method_info in self._get_fix_methods(problem_type, option, affected_column).items():
                # 提案を適用した場合の品質スコアを予測
                preview_container, _ = self.preview_fix_application({
                    "problem_type": problem_type,
                    "option_id": option["id"],
                    "target_indices": affected_indices,
                    "method": method_type,
                    "parameters": method_info.get("parameters", {})
                })
                
                quality_after = current_quality
                if preview_container:
                    # 品質スコアを計算
                    # 正しいコンストラクタパラメータでMetricsCalculatorを初期化
                    preview_validator = DataValidator()
                    preview_validator.validate(preview_container)
                    preview_calculator = MetricsCalculator(
                        validation_results=preview_validator.validation_results,
                        data=preview_container.data
                    )
                    # メトリクス計算器はコンストラクタで自動的に初期化されます
                    quality_after = preview_calculator.get_total_quality_score()
                
                # 修正方法情報を追加
                methods.append({
                    "type": method_type,
                    "description": method_info.get("description", ""),
                    "confidence": method_info.get("confidence", 0.7),
                    "parameters": method_info.get("parameters", {}),
                    "quality_impact": {
                        "before": current_quality,
                        "after": quality_after,
                        "change": quality_after - current_quality
                })
            
            # 推奨される修正方法を決定
            recommended_method = None
            if methods:
                # 品質向上が最大の方法を選択
                methods.sort(key=lambda x: x["quality_impact"]["change"], reverse=True)
                recommended_method = methods[0]["type"]
            
            # 提案を生成
            if methods:
                proposals.append({
                    "id": proposal_id,
                    "issue_type": problem_type,
                    "affected_column": affected_column,
                    "affected_indices": affected_indices,
                    "severity": issue_data.get("severity", "info"),
                    "description": f"{option['name']} - {option['description']}",
                    "methods": methods,
                    "recommended_method": recommended_method
                })
        
        return proposals
    
    def _generate_batch_proposals(self, problem_type: str, indices: List[int]) -> List[Dict[str, Any]]:
        """
        同じタイプの問題に対するバッチ処理提案を生成
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        indices : List[int]
            問題インデックスのリスト
            
        Returns
        -------
        List[Dict[str, Any]]
            バッチ処理提案のリスト
        """
        if not indices:
            return []
        
        proposals = []
        
        # 問題タイプに応じた修正オプションを取得
        correction_options = self.processor.get_correction_options(problem_type)
        
        # バッチ処理に適したオプションを選択
        batch_options = [opt for opt in correction_options if opt["id"] not in ["remove_rows"]]
        
        current_quality = self.metrics_calculator.get_total_quality_score()
        
        # バッチ処理提案を生成
        for option in batch_options:
            # 提案ID生成
            proposal_id = f"batch_{problem_type}_{option['id']}_{uuid.uuid4().hex[:8]}"
            
            # 影響を受けるカラムを特定（問題タイプに応じて）
            affected_columns = set()
            if problem_type == "missing_data":
                for idx in indices:
                    if idx < len(self.container.data):
                        record = self.container.data.iloc[idx]
                        missing_cols = record.index[record.isna()].tolist()
                        affected_columns.update(missing_cols)
            
            affected_columns = list(affected_columns)
            affected_column = affected_columns[0] if affected_columns else None
            
            # 修正方法ごとの提案を生成
            methods = []
            for method_type, method_info in self._get_fix_methods(problem_type, option, affected_column).items():
                # バッチ処理の場合の品質スコアを予測
                preview_container, _ = self.preview_fix_application({
                    "problem_type": problem_type,
                    "option_id": option["id"],
                    "target_indices": indices,
                    "method": method_type,
                    "parameters": method_info.get("parameters", {})
                })
                
                quality_after = current_quality
                if preview_container:
                    # 品質スコアを計算
                    # 正しいコンストラクタパラメータでMetricsCalculatorを初期化
                    preview_validator = DataValidator()
                    preview_validator.validate(preview_container)
                    preview_calculator = MetricsCalculator(
                        validation_results=preview_validator.validation_results,
                        data=preview_container.data
                    )
                    # メトリクス計算器はコンストラクタで自動的に初期化されます
                    quality_after = preview_calculator.get_total_quality_score()
                
                # 修正方法情報を追加
                methods.append({
                    "type": method_type,
                    "description": f"{len(indices)}件のレコードに対して{method_info.get('description', '')}",
                    "confidence": method_info.get("confidence", 0.7),
                    "parameters": method_info.get("parameters", {}),
                    "quality_impact": {
                        "before": current_quality,
                        "after": quality_after,
                        "change": quality_after - current_quality
                })
            
            # 推奨される修正方法を決定
            recommended_method = None
            if methods:
                # 品質向上が最大の方法を選択
                methods.sort(key=lambda x: x["quality_impact"]["change"], reverse=True)
                recommended_method = methods[0]["type"]
            
            # バッチ提案を生成
            if methods:
                proposals.append({
                    "id": proposal_id,
                    "issue_type": problem_type,
                    "affected_column": affected_column,
                    "affected_indices": indices,
                    "severity": "batch",
                    "description": f"【バッチ処理】 {len(indices)}件のレコードに対して {option['name']}",
                    "methods": methods,
                    "recommended_method": recommended_method
                })
        
        return proposals
    
    def _get_fix_methods(self, problem_type: str, option: Dict[str, Any], affected_column: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        問題タイプとオプションに基づいて修正方法を取得
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        option : Dict[str, Any]
            修正オプション
        affected_column : Optional[str]
            影響を受けるカラム
            
        Returns
        -------
        Dict[str, Dict[str, Any]]
            修正方法の辞書
        """
        methods = {}
        
        if problem_type == "missing_data":
            if option["id"] == "interpolate_linear":
                methods["linear"] = {
                    "description": "線形補間で欠損値を埋める",
                    "confidence": 0.9,
                    "parameters": {"method": "linear", "columns": [affected_column] if affected_column else []}
            elif option["id"] == "interpolate_time":
                methods["time"] = {
                    "description": "時間ベースの補間で欠損値を埋める",
                    "confidence": 0.85,
                    "parameters": {"method": "time", "columns": [affected_column] if affected_column else []}
            elif option["id"] == "fill_forward":
                methods["ffill"] = {
                    "description": "直前の値で欠損値を埋める",
                    "confidence": 0.8,
                    "parameters": {"method": "ffill", "columns": [affected_column] if affected_column else []}
            elif option["id"] == "fill_backward":
                methods["bfill"] = {
                    "description": "直後の値で欠損値を埋める",
                    "confidence": 0.8,
                    "parameters": {"method": "bfill", "columns": [affected_column] if affected_column else []}
        
        elif problem_type == "out_of_range":
            if option["id"] == "clip_values":
                # カラムのデータ型に応じて適切な範囲を設定
                min_val, max_val = self._get_column_range(affected_column)
                methods["clip"] = {
                    "description": "有効範囲内に設定",
                    "confidence": 0.9,
                    "parameters": {
                        "method": "clip",
                        "min_value": min_val,
                        "max_value": max_val,
                        "column": affected_column
            elif option["id"] == "replace_with_null":
                methods["null"] = {
                    "description": "問題のある値をNULLに置換",
                    "confidence": 0.7,
                    "parameters": {"method": "null", "column": affected_column}
        
        elif problem_type == "duplicates":
            if option["id"] == "offset_timestamps":
                methods["offset"] = {
                    "description": "タイムスタンプを少しずらす",
                    "confidence": 0.85,
                    "parameters": {"offset_ms": 1}
            elif option["id"] == "keep_first":
                methods["keep_first"] = {
                    "description": "最初のレコードのみを保持",
                    "confidence": 0.9,
                    "parameters": {"method": "keep_first"}
        
        elif problem_type == "spatial_anomalies":
            if option["id"] == "spatial_interpolate":
                methods["spatial"] = {
                    "description": "位置を前後のポイントから補間",
                    "confidence": 0.8,
                    "parameters": {"method": "linear", "columns": ["latitude", "longitude"]}
        
        elif problem_type == "temporal_anomalies":
            if option["id"] == "fix_timestamps":
                methods["increment"] = {
                    "description": "タイムスタンプを修正",
                    "confidence": 0.85,
                    "parameters": {"method": "increment", "seconds_offset": 1.0}
        
        # デフォルトとして削除を追加
        if "remove" not in methods and option["id"] == "remove_rows":
            methods["remove"] = {
                "description": "問題のある行を削除",
                "confidence": 0.7,
                "parameters": {}
        
        return methods
    
    def _get_column_range(self, column_name: Optional[str]) -> Tuple[float, float]:
        """
        カラムの適切な範囲を取得
        
        Parameters
        ----------
        column_name : Optional[str]
            カラム名
            
        Returns
        -------
        Tuple[float, float]
            最小値と最大値
        """
        if not column_name or column_name not in self.container.data.columns:
            return (-float('inf'), float('inf'))
        
        series = self.container.data[column_name]
        
        if pd.api.types.is_numeric_dtype(series):
            # 標準的な変数の範囲を計算
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            return (lower_bound, upper_bound)
        
        # 特定のカラムに対する範囲を設定
        if column_name == "latitude":
            return (-90.0, 90.0)
        elif column_name == "longitude":
            return (-180.0, 180.0)
        
        return (-float('inf'), float('inf'))
    
    def preview_fix_application(self, fix_proposal: Dict[str, Any]) -> Tuple[Optional[GPSDataContainer], Dict[str, Any]]:
        """
        修正適用のプレビューを生成
        
        Parameters
        ----------
        fix_proposal : Dict[str, Any]
            適用する修正提案
            
        Returns
        -------
        Tuple[Optional[GPSDataContainer], Dict[str, Any]]
            修正適用後のコンテナとメタ情報
        """
        if not self.processor or not self.cleaner:
            return None, {}
        
        # プレビュー用にコンテナをコピー
        preview_container = deepcopy(self.container)
        
        # 修正プロセッサを初期化
        preview_validator = deepcopy(self.validator)
        preview_validator.validate(preview_container)
        preview_cleaner = DataCleaner(preview_validator, preview_container)
        preview_processor = CorrectionProcessor(preview_cleaner)
        
        # 提案から修正情報を抽出
        problem_type = fix_proposal.get("problem_type")
        option_id = fix_proposal.get("option_id")
        target_indices = fix_proposal.get("target_indices", [])
        method = fix_proposal.get("method")
        parameters = fix_proposal.get("parameters", {})
        
        # パラメータにメソッドを追加
        custom_params = parameters.copy()
        if method:
            custom_params["method"] = method
        
        # 修正を適用
        try:
            fixed_container = preview_processor.apply_correction(
                problem_type=problem_type,
                option_id=option_id,
                target_indices=target_indices,
                custom_params=custom_params
            )
            
            if fixed_container:
                # 修正後の変更点を計算
                meta_info = {
                    "affected_indices": target_indices,
                    "changed_columns": [],
                    "before_values": {},
                    "after_values": {}
                
                # 変更点を特定
                for idx in target_indices:
                    if idx < len(self.container.data) and idx < len(fixed_container.data):
                        before_row = self.container.data.iloc[idx].copy()
                        after_row = fixed_container.data.iloc[idx].copy()
                        
                        # 変更があったカラムを特定
                        for col in self.container.data.columns:
                            if col in after_row and col in before_row:
                                before_val = before_row[col]
                                after_val = after_row[col]
                                
                                # 値が変更された場合
                                if (pd.isna(before_val) and not pd.isna(after_val)) or \
                                   (not pd.isna(before_val) and pd.isna(after_val)) or \
                                   (not pd.isna(before_val) and not pd.isna(after_val) and before_val != after_val):
                                    
                                    if col not in meta_info["changed_columns"]:
                                        meta_info["changed_columns"].append(col)
                                    
                                    if idx not in meta_info["before_values"]:
                                        meta_info["before_values"][idx] = {}
                                        meta_info["after_values"][idx] = {}
                                    
                                    meta_info["before_values"][idx][col] = str(before_val) if not pd.isna(before_val) else "NULL"
                                    meta_info["after_values"][idx][col] = str(after_val) if not pd.isna(after_val) else "NULL"
                
                return fixed_container, meta_info
        except Exception as e:
            print(f"プレビュー生成中にエラーが発生しました: {e}")
        
        return None, {}


class InteractiveCorrectionInterface:
    """
    インタラクティブな修正インターフェース
    
    バックエンド向けの修正インターフェースを提供するクラス。
    UIコンポーネントとの連携を容易にします。
    """
    
    def __init__(self, 
                processor: Optional[CorrectionProcessor] = None, 
                container: Optional[GPSDataContainer] = None,
                validator: Optional[DataValidator] = None):
        """
        初期化
        
        Parameters
        ----------
        processor : Optional[CorrectionProcessor], optional
            修正プロセッサ, by default None
        container : Optional[GPSDataContainer], optional
            GPSデータコンテナ, by default None
        validator : Optional[DataValidator], optional
            データ検証器, by default None
        """
        self.processor = processor
        self.container = container
        self.validator = validator or DataValidator()
        self.cleaner = None
        self.suggester = None
        
        if container is not None and validator is not None:
            self.setup(container, validator)
    
    def setup(self, container: GPSDataContainer, validator: Optional[DataValidator] = None) -> None:
        """
        コンテナとバリデータを設定
        
        Parameters
        ----------
        container : GPSDataContainer
            GPSデータコンテナ
        validator : Optional[DataValidator], optional
            データ検証器, by default None
        """
        self.container = container
        self.validator = validator or self.validator or DataValidator()
        
        # 検証結果を更新
        if not self.validator.validation_results:
            self.validator.validate(container)
        
        # クリーナーとプロセッサを初期化
        self.cleaner = DataCleaner(self.validator, container)
        self.processor = CorrectionProcessor(self.cleaner)
        
        # 修正提案生成器を初期化
        self.suggester = CorrectionSuggester(self.validator, container)
    
    def get_problem_categories(self) -> Dict[str, int]:
        """
        問題カテゴリとその件数を取得
        
        Returns
        -------
        Dict[str, int]
            問題カテゴリとその件数のマッピング
        """
        if not self.cleaner:
            return {}
        
        problem_indices = self.cleaner.cleaner.metrics_calculator.problematic_indices
        
        return {
            "missing_data": len(problem_indices.get("missing_data", [])),
            "out_of_range": len(problem_indices.get("out_of_range", [])),
            "duplicates": len(problem_indices.get("duplicates", [])),
            "spatial_anomalies": len(problem_indices.get("spatial_anomalies", [])),
            "temporal_anomalies": len(problem_indices.get("temporal_anomalies", [])),
            "all": len(problem_indices.get("all", []))
    
    def get_problem_records(self, problem_type: str = "all") -> pd.DataFrame:
        """
        問題レコードのデータフレームを取得
        
        Parameters
        ----------
        problem_type : str, optional
            問題タイプ（"all"はすべてのタイプ）, by default "all"
            
        Returns
        -------
        pd.DataFrame
            問題レコードのデータフレーム
        """
        if not self.cleaner or not self.container:
            return pd.DataFrame()
        
        # クリーナーからレコードの問題情報を取得
        record_issues = self.cleaner.cleaner.record_issues
        
        if not record_issues:
            return pd.DataFrame()
        
        # 問題レコードの情報を抽出
        problem_records = []
        
        for idx, issue_data in record_issues.items():
            # 問題タイプでフィルタリング
            issue_types = issue_data.get("issues", [])
            
            if problem_type != "all" and problem_type not in [self._map_issue_type(it) for it in issue_types]:
                continue
            
            record = {
                "インデックス": idx,
                "タイムスタンプ": issue_data.get("timestamp"),
                "緯度": issue_data.get("latitude"),
                "経度": issue_data.get("longitude"),
                "問題数": issue_data.get("issue_count", 0),
                "重要度": issue_data.get("severity", "info"),
                "問題タイプ": ", ".join(issue_data.get("issues", [])),
                "説明": issue_data.get("description", "")
            problem_records.append(record)
        
        # DataFrameに変換
        df = pd.DataFrame(problem_records)
        
        # 重要度でソート
        severity_order = {"error": 0, "warning": 1, "info": 2}
        if not df.empty and "重要度" in df.columns:
            df["severity_order"] = df["重要度"].map(severity_order)
            df = df.sort_values(["severity_order", "問題数"], ascending=[True, False])
            df = df.drop(columns=["severity_order"])
        
        return df
    
    def get_correction_options(self, problem_type: str) -> List[Dict[str, Any]]:
        """
        問題タイプに基づいた修正オプションを取得
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
            
        Returns
        -------
        List[Dict[str, Any]]
            修正オプションのリスト
        """
        if not self.processor:
            return []
        
        return self.processor.get_correction_options(problem_type)
    
    def apply_correction(self, 
                        problem_type: str, 
                        option_id: str, 
                        target_indices: List[int],
                        target_columns: Optional[List[str]] = None,
                        custom_params: Optional[Dict[str, Any]] = None) -> Optional[GPSDataContainer]:
        """
        修正を適用
        
        Parameters
        ----------
        problem_type : str
            問題タイプ
        option_id : str
            修正オプションID
        target_indices : List[int]
            対象のインデックスリスト
        target_columns : Optional[List[str]], optional
            対象のカラムリスト
        custom_params : Optional[Dict[str, Any]], optional
            カスタムパラメータ
            
        Returns
        -------
        Optional[GPSDataContainer]
            修正後のデータコンテナ
        """
        if not self.processor:
            return None
        
        fixed_container = self.processor.apply_correction(
            problem_type=problem_type,
            option_id=option_id,
            target_indices=target_indices,
            target_columns=target_columns,
            custom_params=custom_params
        )
        
        if fixed_container:
            # コンテナを更新
            self.container = fixed_container
            
            # 検証を再実行
            self.validator.validate(self.container)
            
            # クリーナーとプロセッサを更新
            self.cleaner = DataCleaner(self.validator, self.container)
            self.processor = CorrectionProcessor(self.cleaner)
        
        return fixed_container
    
    def auto_fix_all(self) -> Optional[GPSDataContainer]:
        """
        自動修正機能ですべての問題を修正
        
        Returns
        -------
        Optional[GPSDataContainer]
            修正後のデータコンテナ
        """
        if not self.validator or not self.container:
            return None
        
        try:
            # 自動修正を実行
            fixed_container, fixes = self.validator.fix_common_issues(self.container)
            
            if fixed_container:
                # コンテナを更新
                self.container = fixed_container
                
                # 検証を再実行
                self.validator.validate(self.container)
                
                # クリーナーとプロセッサを更新
                self.cleaner = DataCleaner(self.validator, self.container)
                self.processor = CorrectionProcessor(self.cleaner)
                
                return fixed_container
        except Exception as e:
            print(f"自動修正中にエラーが発生しました: {e}")
        
        return None
    
    def get_fix_proposals(self) -> List[Dict[str, Any]]:
        """
        修正提案を取得
        
        Returns
        -------
        List[Dict[str, Any]]
            修正提案のリスト
        """
        if not self.suggester:
            self.suggester = CorrectionSuggester(self.validator, self.container)
        
        return self.suggester.generate_fix_proposals()
    
    def get_proposal_for_issue(self, issue: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        特定の問題に対する修正提案を取得
        
        Parameters
        ----------
        issue : Dict[str, Any]
            問題情報
            
        Returns
        -------
        List[Dict[str, Any]]
            修正提案のリスト
        """
        if not self.suggester:
            self.suggester = CorrectionSuggester(self.validator, self.container)
        
        return self.suggester.generate_proposal_for_issue(issue)
    
    def apply_fix_proposal(self, proposal_id: str, method_type: str) -> Optional[GPSDataContainer]:
        """
        修正提案を適用
        
        Parameters
        ----------
        proposal_id : str
            提案ID
        method_type : str
            修正方法タイプ
            
        Returns
        -------
        Optional[GPSDataContainer]
            修正後のデータコンテナ
        """
        if not self.suggester:
            return None
        
        # 提案リストを取得
        proposals = self.suggester.generate_fix_proposals()
        
        # 適用する提案を特定
        selected_proposal = next((p for p in proposals if p["id"] == proposal_id), None)
        
        if not selected_proposal:
            print(f"提案 {proposal_id} が見つかりません。")
            return None
        
        # 選択された修正方法を特定
        selected_method = next((m for m in selected_proposal["methods"] if m["type"] == method_type), None)
        
        if not selected_method:
            print(f"修正方法 {method_type} が見つかりません。")
            return None
        
        # 修正を適用
        problem_type = selected_proposal["issue_type"]
        affected_indices = selected_proposal["affected_indices"]
        
        # 提案が解析した問題から修正オプションIDを特定
        # 例: 'fix_missing_data_interpolate_linear_abc123' から 'interpolate_linear' を抽出
        parts = proposal_id.split("_")
        if parts[0] == "batch":
            # batch_missing_data_interpolate_linear_abc123
            option_id = "_".join(parts[2:4]) if len(parts) >= 4 else ""
        else:
            # fix_missing_data_interpolate_linear_abc123
            option_id = "_".join(parts[2:4]) if len(parts) >= 4 else ""
        
        # パラメータを取得
        parameters = selected_method["parameters"]
        
        # 修正を適用
        fixed_container = self.apply_correction(
            problem_type=problem_type,
            option_id=option_id,
            target_indices=affected_indices,
            custom_params=parameters
        )
        
        return fixed_container
    
    def preview_fix_proposal(self, proposal_id: str, method_type: str) -> Tuple[Optional[GPSDataContainer], Dict[str, Any]]:
        """
        修正提案のプレビューを生成
        
        Parameters
        ----------
        proposal_id : str
            提案ID
        method_type : str
            修正方法タイプ
            
        Returns
        -------
        Tuple[Optional[GPSDataContainer], Dict[str, Any]]
            修正適用後のコンテナとメタ情報
        """
        if not self.suggester:
            return None, {}
        
        # 提案リストを取得
        proposals = self.suggester.generate_fix_proposals()
        
        # 適用する提案を特定
        selected_proposal = next((p for p in proposals if p["id"] == proposal_id), None)
        
        if not selected_proposal:
            print(f"提案 {proposal_id} が見つかりません。")
            return None, {}
        
        # 選択された修正方法を特定
        selected_method = next((m for m in selected_proposal["methods"] if m["type"] == method_type), None)
        
        if not selected_method:
            print(f"修正方法 {method_type} が見つかりません。")
            return None, {}
        
        # プレビューを生成
        problem_type = selected_proposal["issue_type"]
        affected_indices = selected_proposal["affected_indices"]
        
        # 提案が解析した問題から修正オプションIDを特定
        parts = proposal_id.split("_")
        if parts[0] == "batch":
            # batch_missing_data_interpolate_linear_abc123
            option_id = "_".join(parts[2:4]) if len(parts) >= 4 else ""
        else:
            # fix_missing_data_interpolate_linear_abc123
            option_id = "_".join(parts[2:4]) if len(parts) >= 4 else ""
        
        # パラメータを取得
        parameters = selected_method["parameters"]
        
        # プレビューを生成
        return self.suggester.preview_fix_application({
            "problem_type": problem_type,
            "option_id": option_id,
            "target_indices": affected_indices,
            "method": method_type,
            "parameters": parameters
        })
    
    def _map_issue_type(self, issue_type: str) -> str:
        """内部的な問題タイプのマッピング"""
        mapping = {
            "欠損値": "missing_data",
            "範囲外の値": "out_of_range",
            "重複": "duplicates",
            "重複タイムスタンプ": "duplicates",
            "空間的異常": "spatial_anomalies",
            "時間的異常": "temporal_anomalies"
        return mapping.get(issue_type, "other")
