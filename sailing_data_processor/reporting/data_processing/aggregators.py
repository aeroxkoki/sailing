# -*- coding: utf-8 -*-
"""
Module for data aggregation base classes.
This module provides base classes and functions for data aggregation.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class DataAggregator:
    """
    データ集約の基底クラス
    
    様々なデータ集約処理の基底となるクラスを提供します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            集約パラメータ, by default None
        """
        self.params = params or {}
    
    def aggregate(self, data: Any) -> Any:
        """
        データを集約
        
        Parameters
        ----------
        data : Any
            集約対象データ
            
        Returns
        -------
        Any
            集約後のデータ
        """
        # 特定のデータ型に対応した集約処理を呼び出す
        if isinstance(data, pd.DataFrame):
            return self._aggregate_dataframe(data)
        elif isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                return self._aggregate_dict_list(data)
            else:
                return self._aggregate_list(data)
        elif isinstance(data, dict):
            return self._aggregate_dict(data)
        else:
            return data
    
    def _aggregate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameを集約
        
        Parameters
        ----------
        df : pd.DataFrame
            集約対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            集約後のDataFrame
        """
        # 具体的な集約はサブクラスで実装
        return df
    
    def _aggregate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストを集約
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            集約対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            集約後の辞書リスト
        """
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        result_df = self._aggregate_dataframe(df)
        return result_df.to_dict('records')
    
    def _aggregate_list(self, data: List[Any]) -> List[Any]:
        """
        リストを集約
        
        Parameters
        ----------
        data : List[Any]
            集約対象のリスト
            
        Returns
        -------
        List[Any]
            集約後のリスト
        """
        # 具体的な集約はサブクラスで実装
        return data
    
    def _aggregate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        辞書を集約
        
        Parameters
        ----------
        data : Dict[str, Any]
            集約対象の辞書
            
        Returns
        -------
        Dict[str, Any]
            集約後の辞書
        """
        # 具体的な集約はサブクラスで実装
        return data


# Import specialized aggregators from separate module
from .specialized_aggregators import TimeAggregator, SpatialAggregator, CategoryAggregator
