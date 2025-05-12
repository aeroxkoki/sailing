# -*- coding: utf-8 -*-
"""
Base module for sailing metrics calculation.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np

from sailing_data_processor.reporting.data_processing.calculators import BaseCalculator
from sailing_data_processor.reporting.data_processing.metrics.vmg import VMGCalculator
from sailing_data_processor.reporting.data_processing.metrics.maneuver import ManeuverEfficiencyCalculator
from sailing_data_processor.reporting.data_processing.metrics.leg import LegAnalysisCalculator
from sailing_data_processor.reporting.data_processing.metrics.speed import SpeedMetricsCalculator
from sailing_data_processor.reporting.data_processing.metrics.wind_angle import WindAngleCalculator


class SailingMetricsCalculator(BaseCalculator):
    """
    セーリング特化型指標計算
    
    セーリング競技特有の指標を計算するためのクラスです。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            計算パラメータ, by default None
            
            metrics: List[str]
                計算する指標のリスト
            speed_column: str
                速度の列名
            direction_column: str
                方向の列名
            wind_direction_column: str
                風向の列名
            wind_speed_column: str
                風速の列名
            position_columns: List[str]
                位置情報の列名 [緯度, 経度]
            target_position: List[float]
                目標地点の位置 [緯度, 経度]
            boat_class: str
                艇種
            time_column: str
                時間の列名
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'metrics' not in self.params:
            self.params['metrics'] = ['vmg', 'target_vmg', 'tacking_efficiency']
        
        if 'speed_column' not in self.params:
            self.params['speed_column'] = 'speed'
        
        if 'direction_column' not in self.params:
            self.params['direction_column'] = 'direction'
        
        if 'wind_direction_column' not in self.params:
            self.params['wind_direction_column'] = 'wind_direction'
        
        if 'wind_speed_column' not in self.params:
            self.params['wind_speed_column'] = 'wind_speed'
        
        if 'position_columns' not in self.params:
            self.params['position_columns'] = ['latitude', 'longitude']
        
        if 'boat_class' not in self.params:
            self.params['boat_class'] = None
        
        if 'time_column' not in self.params:
            self.params['time_column'] = 'timestamp'
        
        # 各メトリクス計算機を初期化
        self.calculators = {
            'vmg': VMGCalculator(self.params),
            'target_vmg': VMGCalculator(self.params),
            'tacking_efficiency': ManeuverEfficiencyCalculator(self.params),
            'leg_analysis': LegAnalysisCalculator(self.params),
            'target_speed_ratio': SpeedMetricsCalculator(self.params),
            'wind_angle_efficiency': WindAngleCalculator(self.params)
        }
    
    def _calculate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameのセーリング指標を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
            
        Returns
        -------
        pd.DataFrame
            計算結果のDataFrame
        """
        # 結果用のDataFrameを作成（元のデータをコピー）
        result_df = df.copy()
        
        # 計算する指標を取得
        metrics = self.params['metrics']
        
        # 風上/風下VMGの計算
        if 'vmg' in metrics:
            result_df = self.calculators['vmg'].calculate_wind_vmg(result_df)
        
        # 目標地点へのVMGの計算
        if 'target_vmg' in metrics:
            result_df = self.calculators['vmg'].calculate_target_vmg(result_df)
        
        # タッキング効率の計算
        if 'tacking_efficiency' in metrics:
            result_df = self.calculators['tacking_efficiency'].calculate_tacking_efficiency(result_df)
        
        # レグ（コースの区間）分析
        if 'leg_analysis' in metrics:
            result_df = self.calculators['leg_analysis'].calculate_leg_analysis(result_df)
        
        # 対ターゲット速度比の計算
        if 'target_speed_ratio' in metrics:
            result_df = self.calculators['target_speed_ratio'].calculate_target_speed_ratio(result_df)
        
        # 風向による速度効率の計算
        if 'wind_angle_efficiency' in metrics:
            result_df = self.calculators['wind_angle_efficiency'].calculate_wind_angle_efficiency(result_df)
        
        return result_df
