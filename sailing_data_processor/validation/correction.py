# -*- coding: utf-8 -*-
"""
Data correction module for handling data issues.
This module provides functions for correcting detected data issues.
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

from sailing_data_processor.validation.correction_options import get_correction_options


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
        
        return get_correction_options(problem_type)
    
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
            }
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
