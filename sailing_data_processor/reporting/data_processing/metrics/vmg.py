# -*- coding: utf-8 -*-
"""
Module for VMG (Velocity Made Good) calculations.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sailing_data_processor.reporting.data_processing.calculators import BaseCalculator
from sailing_data_processor.reporting.data_processing.metrics.utils import MetricsUtils


class VMGCalculator(BaseCalculator):
    """
    風上/風下VMGおよび目標地点へのVMGを計算するクラス
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            計算パラメータ, by default None
        """
        super().__init__(params)
    
    def calculate_wind_vmg(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        風上/風下VMGを計算
        
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
        
        # 必要な列の存在を確認
        required_columns = [
            self.params['speed_column'],
            self.params['direction_column'],
            self.params['wind_direction_column']
        ]
        
        if not all(col in result_df.columns for col in required_columns):
            print(f"Warning: Cannot calculate VMG due to missing columns")
            return result_df
        
        speed_col = self.params['speed_column']
        direction_col = self.params['direction_column']
        wind_direction_col = self.params['wind_direction_column']
        
        # 風向と艇の進行方向の差（角度）を計算
        result_df['wind_angle'] = (result_df[wind_direction_col] - result_df[direction_col]) % 360
        
        # 180度を超える角度は反対側からの角度として調整
        result_df.loc[result_df['wind_angle'] > 180, 'wind_angle'] = 360 - result_df.loc[result_df['wind_angle'] > 180, 'wind_angle']
        
        # VMGの計算
        # 風上方向のVMG: speed * cos(wind_angle)
        # 風下方向のVMG: speed * cos(180 - wind_angle)
        result_df['vmg_upwind'] = result_df[speed_col] * np.cos(np.radians(result_df['wind_angle']))
        result_df['vmg_downwind'] = result_df[speed_col] * np.cos(np.radians(180 - result_df['wind_angle']))
        
        # 風上/風下タイプの判定（45度を境界とする）
        result_df['sailing_type'] = 'reaching'
        result_df.loc[result_df['wind_angle'] <= 45, 'sailing_type'] = 'upwind'
        result_df.loc[result_df['wind_angle'] >= 135, 'sailing_type'] = 'downwind'
        
        # 総合VMG（風上セーリング時は風上VMG、風下セーリング時は風下VMG）
        result_df['vmg'] = np.where(result_df['sailing_type'] == 'upwind', result_df['vmg_upwind'], 
                             np.where(result_df['sailing_type'] == 'downwind', result_df['vmg_downwind'], 0))
        
        # VMG効率（実際のVMGと理論上の最大VMGの比率）
        # 理論的な最適風角度を定義
        optimal_upwind_angle = 45  # 風上最適角度（艇種によって異なる）
        optimal_downwind_angle = 135  # 風下最適角度（艇種によって異なる）
        
        # 艇種が指定されている場合は、その艇種に合った最適角度を使用
        boat_class = self.params.get('boat_class')
        if boat_class:
            if boat_class == '470':
                optimal_upwind_angle = 42
                optimal_downwind_angle = 140
            elif boat_class == '49er':
                optimal_upwind_angle = 38
                optimal_downwind_angle = 145
            elif boat_class == 'finn':
                optimal_upwind_angle = 45
                optimal_downwind_angle = 140
            elif boat_class == 'laser':
                optimal_upwind_angle = 45
                optimal_downwind_angle = 135
            elif boat_class == 'nacra17':
                optimal_upwind_angle = 40
                optimal_downwind_angle = 150
        
        # VMG効率の計算
        # 風上セーリング時の効率
        upwind_mask = result_df['sailing_type'] == 'upwind'
        if upwind_mask.any():
            optimal_upwind_vmg = result_df.loc[upwind_mask, speed_col] * np.cos(np.radians(optimal_upwind_angle))
            result_df.loc[upwind_mask, 'vmg_efficiency'] = (result_df.loc[upwind_mask, 'vmg_upwind'] / optimal_upwind_vmg)
        
        # 風下セーリング時の効率
        downwind_mask = result_df['sailing_type'] == 'downwind'
        if downwind_mask.any():
            optimal_downwind_vmg = result_df.loc[downwind_mask, speed_col] * np.cos(np.radians(180 - optimal_downwind_angle))
            result_df.loc[downwind_mask, 'vmg_efficiency'] = (result_df.loc[downwind_mask, 'vmg_downwind'] / optimal_downwind_vmg)
        
        return result_df
    
    def calculate_target_vmg(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        目標地点へのVMGを計算
        
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
        
        # 必要な列の存在を確認
        required_columns = [
            self.params['speed_column'],
            self.params['direction_column']
        ]
        
        position_columns = self.params['position_columns']
        target_position = self.params.get('target_position')
        
        if not all(col in result_df.columns for col in required_columns):
            print(f"Warning: Cannot calculate target VMG due to missing columns")
            return result_df
        
        if not target_position or len(target_position) != 2 or not all(col in result_df.columns for col in position_columns):
            print(f"Warning: Cannot calculate target VMG due to missing target position or position columns")
            return result_df
        
        speed_col = self.params['speed_column']
        direction_col = self.params['direction_column']
        lat_col, lng_col = position_columns
        target_lat, target_lng = target_position
        
        # 各ポイントから目標地点への方位角を計算
        result_df['target_bearing'] = result_df.apply(
            lambda row: MetricsUtils.calculate_bearing(row[lat_col], row[lng_col], target_lat, target_lng),
            axis=1
        )
        
        # 艇の進行方向と目標地点への方位角の差を計算
        result_df['target_angle'] = (result_df['target_bearing'] - result_df[direction_col]) % 360
        
        # 180度を超える角度は反対側からの角度として調整
        result_df.loc[result_df['target_angle'] > 180, 'target_angle'] = 360 - result_df.loc[result_df['target_angle'] > 180, 'target_angle']
        
        # 目標地点へのVMGを計算
        result_df['target_vmg'] = result_df[speed_col] * np.cos(np.radians(result_df['target_angle']))
        
        # 目標地点への距離を計算
        result_df['target_distance'] = result_df.apply(
            lambda row: MetricsUtils.calculate_distance(row[lat_col], row[lng_col], target_lat, target_lng),
            axis=1
        )
        
        # 推定到達時間を計算（現在の速度と方向が変わらないと仮定）
        result_df['estimated_arrival_time'] = np.nan
        
        # 時間列があり、目標VMGが正の場合のみ計算
        time_col = self.params['time_column']
        if time_col in result_df.columns and pd.api.types.is_datetime64_any_dtype(result_df[time_col]):
            positive_vmg_mask = result_df['target_vmg'] > 0
            if positive_vmg_mask.any():
                # 時間（秒）= 距離（m）/ VMG（m/s）
                # 速度の単位がノットの場合は、m/sに変換（1ノット ≈ 0.51444 m/s）
                speed_factor = 0.51444 if self.params.get('speed_unit', 'knot') == 'knot' else 1.0
                
                # 推定到達時間 = 現在時刻 + 距離/VMG
                estimated_seconds = result_df.loc[positive_vmg_mask, 'target_distance'] / (result_df.loc[positive_vmg_mask, 'target_vmg'] * speed_factor)
                result_df.loc[positive_vmg_mask, 'estimated_arrival_time'] = result_df.loc[positive_vmg_mask, time_col] + pd.to_timedelta(estimated_seconds, unit='s')
        
        return result_df
