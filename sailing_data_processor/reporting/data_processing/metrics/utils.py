# -*- coding: utf-8 -*-
"""
Utility functions for sailing metrics calculations.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta


class MetricsUtils:
    """
    セーリングメトリクスの計算に必要なユーティリティ関数を提供するクラス
    """
    
    @staticmethod
    def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        2点間の方位角を計算
        
        Parameters
        ----------
        lat1 : float
            始点の緯度（度）
        lon1 : float
            始点の経度（度）
        lat2 : float
            終点の緯度（度）
        lon2 : float
            終点の経度（度）
            
        Returns
        -------
        float
            方位角（度、北を0度として時計回り）
        """
        # 緯度経度をラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 経度の差
        d_lon = lon2_rad - lon1_rad
        
        # 方位角の計算
        y = math.sin(d_lon) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(d_lon)
        bearing_rad = math.atan2(y, x)
        
        # ラジアンから度に変換し、0-360度の範囲に正規化
        bearing_deg = math.degrees(bearing_rad)
        bearing_deg = (bearing_deg + 360) % 360
        
        return bearing_deg
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        2点間の距離を計算（ハーバーサイン公式）
        
        Parameters
        ----------
        lat1 : float
            始点の緯度（度）
        lon1 : float
            始点の経度（度）
        lat2 : float
            終点の緯度（度）
        lon2 : float
            終点の経度（度）
            
        Returns
        -------
        float
            距離（メートル）
        """
        # 地球の半径（メートル）
        R = 6371000
        
        # 緯度経度をラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 緯度と経度の差
        d_lat = lat2_rad - lat1_rad
        d_lon = lon2_rad - lon1_rad
        
        # ハーバーサイン公式
        a = math.sin(d_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    @staticmethod
    def calculate_circular_mean(angles: pd.Series) -> float:
        """
        角度の平均を計算（円周統計）
        
        Parameters
        ----------
        angles : pd.Series
            角度の列（度）
            
        Returns
        -------
        float
            平均角度（度）
        """
        # 角度をラジアンに変換
        angles_rad = np.radians(angles)
        
        # 正弦と余弦の平均を計算
        sin_mean = np.mean(np.sin(angles_rad))
        cos_mean = np.mean(np.cos(angles_rad))
        
        # 平均角度を計算
        mean_rad = np.arctan2(sin_mean, cos_mean)
        
        # ラジアンから度に変換し、0-360度の範囲に正規化
        mean_deg = np.degrees(mean_rad)
        mean_deg = (mean_deg + 360) % 360
        
        return mean_deg
    
    @staticmethod
    def calculate_circular_std(angles: pd.Series) -> float:
        """
        角度の標準偏差を計算（円周統計）
        
        Parameters
        ----------
        angles : pd.Series
            角度の列（度）
            
        Returns
        -------
        float
            標準偏差（度）
        """
        # 角度をラジアンに変換
        angles_rad = np.radians(angles)
        
        # 正弦と余弦の平均を計算
        sin_mean = np.mean(np.sin(angles_rad))
        cos_mean = np.mean(np.cos(angles_rad))
        
        # 平均合成長を計算（分散の目安）
        R = np.sqrt(sin_mean**2 + cos_mean**2)
        
        # 円周標準偏差を計算
        std_rad = np.sqrt(-2 * np.log(R))
        
        # ラジアンから度に変換
        std_deg = np.degrees(std_rad)
        
        return std_deg
