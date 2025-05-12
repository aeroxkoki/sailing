# -*- coding: utf-8 -*-
"""
sailing_data_processor.boat_fusion.boat_data_fusion_base モジュール

複数船舶データを融合するための基本クラスと初期化メソッド
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math

from .boat_data_fusion_integration import fuse_wind_estimates
from .boat_data_fusion_analysis import calc_boat_reliability
from .boat_data_fusion_utils import bayesian_wind_integration, weighted_average_integration, update_time_change_model, create_spatiotemporal_wind_field, estimate_wind_field_at_time

class BoatDataFusionModel:
    """
    複数艇のデータを融合して風向風速場を推定するモデル
    """
    
    def __init__(self):
        """初期化"""
        # 艇のスキルレベルの辞書（0.0〜1.0のスコア、高いほど信頼度が高い）
        self.boat_skill_levels = {}
        
        # 艇種の特性辞書（デフォルト特性は基準値1.0）
        self.boat_type_characteristics = {
            'default': {'upwind_efficiency': 1.0, 'downwind_efficiency': 1.0, 'pointing_ability': 1.0},
            'laser': {'upwind_efficiency': 1.1, 'downwind_efficiency': 0.9, 'pointing_ability': 1.1},
            'ilca': {'upwind_efficiency': 1.1, 'downwind_efficiency': 0.9, 'pointing_ability': 1.1},
            '470': {'upwind_efficiency': 1.05, 'downwind_efficiency': 1.0, 'pointing_ability': 1.05},
            '49er': {'upwind_efficiency': 0.95, 'downwind_efficiency': 1.2, 'pointing_ability': 0.9},
            'finn': {'upwind_efficiency': 1.15, 'downwind_efficiency': 0.9, 'pointing_ability': 1.15},
            'nacra17': {'upwind_efficiency': 0.9, 'downwind_efficiency': 1.3, 'pointing_ability': 0.85},
            'star': {'upwind_efficiency': 1.2, 'downwind_efficiency': 0.85, 'pointing_ability': 1.2}
        }
        
        # 艇タイプの辞書
        self.boat_types = {}
        
        # 風向風速推定の履歴
        self.estimation_history = []
        
        # 風向の時間変化モデル
        self.direction_time_change = 0.0  # 度/分
        self.direction_time_change_std = 0.0  # 標準偏差
        
        # 風速の時間変化モデル
        self.speed_time_change = 0.0  # ノット/分
        self.speed_time_change_std = 0.0  # 標準偏差
        
        # ベイズ推定に使用するハイパーパラメータ
        self.wind_dir_prior_mean = None  # 風向の事前確率平均
        self.wind_dir_prior_std = 45.0  # 風向の事前確率標準偏差（度）
        self.wind_speed_prior_mean = None  # 風速の事前確率平均
        self.wind_speed_prior_std = 3.0  # 風速の事前確率標準偏差（ノット）
    
    def set_boat_skill_levels(self, skill_levels: Dict[str, float]):
        """
        各艇のスキルレベルを設定
        
        Parameters:
        -----------
        skill_levels : Dict[str, float]
            艇ID:スキルレベルの辞書（0.0〜1.0のスコア）
        """
        # 値の範囲を0.0〜1.0に制限
        for boat_id, level in skill_levels.items():
            self.boat_skill_levels[boat_id] = max(0.0, min(1.0, level))
    
    def set_boat_types(self, boat_types: Dict[str, str]):
        """
        各艇の艇種を設定
        
        Parameters:
        -----------
        boat_types : Dict[str, str]
            艇ID:艇種の辞書
        """
        self.boat_types = boat_types
    
    def set_wind_priors(self, direction_mean: float = None, direction_std: float = 45.0,
                      speed_mean: float = None, speed_std: float = 3.0):
        """
        風向風速の事前確率を設定
        
        Parameters:
        -----------
        direction_mean : float, optional
            風向の事前確率平均（度）
        direction_std : float
            風向の事前確率標準偏差（度）
        speed_mean : float, optional
            風速の事前確率平均（ノット）
        speed_std : float
            風速の事前確率標準偏差（ノット）
        """
        self.wind_dir_prior_mean = direction_mean
        self.wind_dir_prior_std = direction_std
        self.wind_speed_prior_mean = speed_mean
        self.wind_speed_prior_std = speed_std
    
    def calc_boat_reliability(self, boat_id: str, wind_estimates: pd.DataFrame) -> float:
        """
        各艇の信頼性係数を計算（艇のスキル、データの一貫性、過去の履歴に基づく）
        
        Parameters:
        -----------
        boat_id : str
            艇ID
        wind_estimates : pd.DataFrame
            艇の風向風速推定データ
            
        Returns:
        --------
        float
            信頼性係数（0.0〜1.0）
        """
        return calc_boat_reliability(self, boat_id, wind_estimates)
    
    def fuse_wind_estimates(self, boats_estimates: Dict[str, pd.DataFrame], 
                          time_point: datetime = None) -> Optional[Dict[str, Any]]:
        """
        複数艇からの風向風速推定を融合
        
        Parameters:
        -----------
        boats_estimates : Dict[str, pd.DataFrame]
            艇ID:風向風速推定DataFrameの辞書
        time_point : datetime, optional
            対象時間点（指定がない場合は最新の共通時間）
            
        Returns:
        --------
        Dict[str, Any] or None
            融合された風向風速データと信頼度
        """
        return fuse_wind_estimates(self, boats_estimates, time_point)
    
    def _bayesian_wind_integration(self, boat_data: List[Dict[str, Any]], 
                                 time_point: datetime) -> Dict[str, Any]:
        """
        ベイズ更新を使用した風向風速の統合
        
        Parameters:
        -----------
        boat_data : List[Dict[str, Any]]
            各艇の風推定データ
        time_point : datetime
            対象時間点
            
        Returns:
        --------
        Dict[str, Any]
            ベイズ更新された風向風速データ
        """
        return bayesian_wind_integration(self, boat_data, time_point)
    
    def _weighted_average_integration(self, boat_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        単純な重み付き平均による風向風速の統合
        
        Parameters:
        -----------
        boat_data : List[Dict[str, Any]]
            各艇の風推定データ
            
        Returns:
        --------
        Dict[str, Any]
            重み付き平均による風向風速データ
        """
        return weighted_average_integration(boat_data)
    
    def _update_time_change_model(self):
        """
        風向風速の時間変化モデルを更新
        """
        update_time_change_model(self)
    
    def create_spatiotemporal_wind_field(self, time_points: List[datetime], 
                                       grid_resolution: int = 20) -> Dict[datetime, Dict[str, Any]]:
        """
        時空間的な風の場を作成
        
        Parameters:
        -----------
        time_points : List[datetime]
            対象時間点のリスト
        grid_resolution : int
            空間グリッドの解像度
            
        Returns:
        --------
        Dict[datetime, Dict[str, Any]]
            時間点ごとの風の場データ
        """
        return create_spatiotemporal_wind_field(self, time_points, grid_resolution)
    
    def _estimate_wind_field_at_time(self, time_point: datetime, 
                                   grid_resolution: int = 20) -> Optional[Dict[str, Any]]:
        """
        特定時点での風の場を推定
        
        Parameters:
        -----------
        time_point : datetime
            対象時間点
        grid_resolution : int
            空間グリッドの解像度
            
        Returns:
        --------
        Dict[str, Any] or None
            風の場データ
        """
        return estimate_wind_field_at_time(self, time_point, grid_resolution)
