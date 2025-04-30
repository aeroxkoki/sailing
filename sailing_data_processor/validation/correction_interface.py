# -*- coding: utf-8 -*-
"""
Interactive correction interface module.
This module provides an interface for interactive data correction.
"""

from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
from datetime import datetime

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.validation.data_validator import DataValidator
from sailing_data_processor.validation.data_cleaner import DataCleaner
from sailing_data_processor.validation.correction import CorrectionProcessor
from sailing_data_processor.validation.correction_suggester import CorrectionSuggester


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
        }
    
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
            }
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
        }
        return mapping.get(issue_type, "other")
