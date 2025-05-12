# -*- coding: utf-8 -*-
"""
Module for leg analysis calculations.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sailing_data_processor.reporting.data_processing.calculators import BaseCalculator
from sailing_data_processor.reporting.data_processing.metrics.utils import MetricsUtils


class LegAnalysisCalculator(BaseCalculator):
    """
    レグ（コースの区間）分析を計算するクラス
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
    
    def calculate_leg_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        レグ（コースの区間）分析
        
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
        required_columns = [self.params['time_column']]
        
        if not all(col in result_df.columns for col in required_columns):
            print(f"Warning: Cannot calculate leg analysis due to missing columns")
            return result_df
        
        # レグ情報がある場合のみ計算
        leg_column = self.params.get('leg_column', 'leg')
        if leg_column not in result_df.columns:
            print(f"Warning: Cannot calculate leg analysis due to missing leg column")
            return result_df
        
        time_col = self.params['time_column']
        
        # 時間型であることを確認
        if not pd.api.types.is_datetime64_any_dtype(result_df[time_col]):
            try:
                result_df[time_col] = pd.to_datetime(result_df[time_col])
            except:
                print(f"Warning: Cannot convert {time_col} to datetime")
                return result_df
        
        # レグごとにグループ化して計算
        leg_groups = result_df.groupby(leg_column)
        
        # レグ分析結果を保存するDataFrame
        leg_analysis = pd.DataFrame()
        
        for leg, group in leg_groups:
            leg_data = {}
            
            # レグのID
            leg_data['leg_id'] = leg
            
            # レグの開始・終了時間
            leg_data['start_time'] = group[time_col].min()
            leg_data['end_time'] = group[time_col].max()
            
            # レグの所要時間（秒）
            leg_data['duration'] = (leg_data['end_time'] - leg_data['start_time']).total_seconds()
            
            # 速度情報がある場合
            speed_col = self.params['speed_column']
            if speed_col in result_df.columns:
                leg_data['avg_speed'] = group[speed_col].mean()
                leg_data['max_speed'] = group[speed_col].max()
                leg_data['min_speed'] = group[speed_col].min()
                leg_data['speed_std'] = group[speed_col].std()
            
            # VMG情報がある場合
            if 'vmg' in result_df.columns:
                leg_data['avg_vmg'] = group['vmg'].mean()
                leg_data['max_vmg'] = group['vmg'].max()
                leg_data['min_vmg'] = group['vmg'].min()
            
            # タッキング情報がある場合
            if 'is_tacking' in result_df.columns:
                leg_data['tack_count'] = group['is_tacking'].sum()
                
                # タッキング効率情報がある場合
                if 'tacking_efficiency' in result_df.columns:
                    tacking_efficiencies = group['tacking_efficiency'].dropna()
                    if not tacking_efficiencies.empty:
                        leg_data['avg_tacking_efficiency'] = tacking_efficiencies.mean()
            
            # ジャイブ情報がある場合
            if 'is_jibing' in result_df.columns:
                leg_data['jibe_count'] = group['is_jibing'].sum()
                
                # ジャイブ効率情報がある場合
                if 'jibing_efficiency' in result_df.columns:
                    jibing_efficiencies = group['jibing_efficiency'].dropna()
                    if not jibing_efficiencies.empty:
                        leg_data['avg_jibing_efficiency'] = jibing_efficiencies.mean()
            
            # 風向風速情報がある場合
            wind_direction_col = self.params['wind_direction_column']
            wind_speed_col = self.params['wind_speed_column']
            
            if wind_direction_col in result_df.columns:
                leg_data['avg_wind_direction'] = MetricsUtils.calculate_circular_mean(group[wind_direction_col])
                leg_data['wind_direction_std'] = MetricsUtils.calculate_circular_std(group[wind_direction_col])
            
            if wind_speed_col in result_df.columns:
                leg_data['avg_wind_speed'] = group[wind_speed_col].mean()
                leg_data['max_wind_speed'] = group[wind_speed_col].max()
                leg_data['min_wind_speed'] = group[wind_speed_col].min()
            
            # レグデータをDataFrameに追加
            leg_analysis = pd.concat([leg_analysis, pd.DataFrame([leg_data])], ignore_index=True)
        
        # 結果をDFに追加またはコンテキストに保存
        if self.params.get('save_leg_analysis_to_context', False):
            # コンテキストに保存する場合は、関数外部で対応する必要あり
            pass
        else:
            # 元のDataFrameに一意のレグIDごとに結果を追加
            for leg_id, leg_row in leg_analysis.iterrows():
                leg_id_value = leg_row['leg_id']
                
                # レグIDに一致する行にのみデータを反映
                leg_mask = result_df[leg_column] == leg_id_value
                
                # 各分析値をレグ内の全行に複製
                for col in leg_analysis.columns:
                    if col != 'leg_id' and not col.startswith('start_') and not col.startswith('end_'):
                        result_df.loc[leg_mask, f'leg_{col}'] = leg_row[col]
        
        return result_df
