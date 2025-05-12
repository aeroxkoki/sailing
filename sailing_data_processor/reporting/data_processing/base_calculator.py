# -*- coding: utf-8 -*-
"""
Base Calculator Module - Provides base functionality for data calculations.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np


class BaseCalculator:
    """
    計算処理の基底クラス
    
    様々な計算処理の基底となるクラスを提供します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            計算パラメータ, by default None
        """
        self.params = params or {}
    
    def calculate(self, data: Any) -> Any:
        """
        データを計算
        
        Parameters
        ----------
        data : Any
            計算対象データ
            
        Returns
        -------
        Any
            計算結果
        """
        # 特定のデータ型に対応した計算処理を呼び出す
        if isinstance(data, pd.DataFrame):
            return self._calculate_dataframe(data)
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return self._calculate_dict_list(data)
            else:
                return self._calculate_list(data)
        elif isinstance(data, dict):
            return self._calculate_dict(data)
        else:
            return data
    
    def _calculate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameの計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            計算結果のDataFrame
        """
        # 具体的な計算はサブクラスで実装
        return df
    
    def _calculate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストの計算
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            計算対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            計算結果の辞書リスト
        """
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        result_df = self._calculate_dataframe(df)
        return result_df.to_dict('records')
    
    def _calculate_list(self, data: List[Any]) -> List[Any]:
        """
        リストの計算
        
        Parameters
        ----------
        data : List[Any]
            計算対象のリスト
            
        Returns
        -------
        List[Any]
            計算結果のリスト
        """
        # 具体的な計算はサブクラスで実装
        return data
    
    def _calculate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        辞書の計算
        
        Parameters
        ----------
        data : Dict[str, Any]
            計算対象の辞書
            
        Returns
        -------
        Dict[str, Any]
            計算結果の辞書
        """
        # 具体的な計算はサブクラスで実装
        return data
