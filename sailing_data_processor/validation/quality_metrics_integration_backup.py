# -*- coding: utf-8 -*-
"""
sailing_data_processor.validation.quality_metrics_integration

既存のQualityMetricsCalculatorクラスを拡張する統合モジュール
"""

from typing import Dict, List, Any, Optional, Tuple, Set
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import importlib

from sailing_data_processor.validation.quality_metrics import QualityMetricsCalculator
from sailing_data_processor.validation.quality_metrics_improvements import QualityMetricsCalculatorExtension

# QualityMetricsCalculatorの機能を拡張したEnhancedQualityMetricsCalculatorクラスを定義
class EnhancedQualityMetricsCalculator(QualityMetricsCalculator):
    """
    既存のQualityMetricsCalculatorクラスを拡張し、新たな品質メトリクス計算機能を追加したクラス
    
    Parameters
    ----------
    validation_results : List[Dict[str, Any]]
        DataValidatorから得られた検証結果
    data : pd.DataFrame
        検証されたデータフレーム
    """
    
    def __init__(self, validation_results: List[Dict[str, Any]], data: pd.DataFrame):
        """
        初期化メソッド
        親クラスのコンストラクタを呼び出した後、追加の初期化を行う
        
        Parameters
        ----------
        validation_results : List[Dict[str, Any]]
            DataValidatorから得られた検証結果
        data : pd.DataFrame
            検証されたデータフレーム
        """
        # 親クラスのコンストラクタを呼び出す
        super().__init__(validation_results, data)
        
        # 拡張機能のオブジェクトを作成
        # 内部では使用せず、後で機能コピーのみに利用
        self._extension = QualityMetricsCalculatorExtension()
        
        # 拡張クラスから機能をコピー
        # Python動的特性を利用して拡張メソッドを現在のクラスに追加
        # 実際の環境では、メソッドを直接定義する方が望ましい
        
        # 拡張クラスのすべてのメソッドをこのクラスにコピー
        extension_methods = [method for method in dir(self._extension) 
                            if not method.startswith('__') and callable(getattr(self._extension, method))]
        
        # このファイルに移動する必要がないメソッドのフィルタリング
        skip_methods = ['__init__']
        
        for method_name in extension_methods:
            if method_name not in skip_methods:
                # メソッドを取得
                method = getattr(self._extension, method_name)
                # このクラスにメソッドをコピー
                setattr(self.__class__, method_name, method)
    
    def _calculate_problem_type_distribution_for_period(self, period_indices: List[int]) -> Dict[str, int]:
        """
        特定の期間における問題タイプの分布を計算

        Parameters
        ----------
        period_indices : List[int]
            期間内のレコードインデックス

        Returns
        -------
        Dict[str, int]
            問題タイプ別のカウント
        """
        problem_type_counts = {}
            "missing_data": 0,
            "out_of_range": 0,
            "duplicates": 0,
            "spatial_anomalies": 0,
            "temporal_anomalies": 0
        
        # 期間内の各問題タイプのカウントを計算
        for problem_type, indices in self.problematic_indices.items():
            if problem_type != "all":
                # 期間内のインデックスと問題タイプのインデックスの交差を計算
                intersection = set(period_indices).intersection(set(indices))
                problem_type_counts[problem_type] = len(intersection)
        
        return problem_type_counts
