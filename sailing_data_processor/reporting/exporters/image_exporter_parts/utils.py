# -*- coding: utf-8 -*-
"""
Utility functions for image exporters

This module provides utility functions for use with the image exporter
"""

from typing import List, Dict, Any, Optional, Tuple, Union

def calculate_color_scale(values: List[float], 
                        min_value: Optional[float] = None, 
                        max_value: Optional[float] = None,
                        cmap_name: str = "viridis") -> List[str]:
    """
    値に基づいたカラースケールを計算
    
    Parameters
    ----------
    values : List[float]
        色分けする値のリスト
    min_value : Optional[float], optional
        最小値, by default None
    max_value : Optional[float], optional
        最大値, by default None
    cmap_name : str, optional
        カラーマップ名, by default "viridis"
    
    Returns
    -------
    List[str]
        色コードのリスト
    """
    # スタブ実装
    return ["#000000"] * len(values)

def format_timestamp(timestamp, format_str="%Y-%m-%d %H:%M:%S"):
    """
    タイムスタンプを指定形式でフォーマット
    
    Parameters
    ----------
    timestamp : datetime or str
        フォーマットするタイムスタンプ
    format_str : str, optional
        フォーマット文字列, by default "%Y-%m-%d %H:%M:%S"
    
    Returns
    -------
    str
        フォーマットされたタイムスタンプ
    """
    # スタブ実装
    return str(timestamp)
