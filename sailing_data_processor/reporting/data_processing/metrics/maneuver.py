# -*- coding: utf-8 -*-
"""
Module for maneuver efficiency calculations.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sailing_data_processor.reporting.data_processing.calculators import BaseCalculator


class ManeuverEfficiencyCalculator(BaseCalculator):
    """
    タッキング/ジャイブ効率を計算するクラス
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
    
    def calculate_tacking_efficiency(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        タッキング効率を計算
        
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
        
        if not all(col in result_df.columns for col in required_columns):
            print(f"Warning: Cannot calculate tacking efficiency due to missing columns")
            return result_df
        
        direction_col = self.params['direction_column']
        speed_col = self.params['speed_column']
        
        # 方向の変化を計算
        result_df['direction_diff'] = result_df[direction_col].diff().abs()
        
        # 方向の変化が大きい箇所（例：45度以上）をタッキング/ジャイブとして検出
        tacking_threshold = self.params.get('tacking_threshold', 45)
        result_df['is_tack_or_jibe'] = result_df['direction_diff'] > tacking_threshold
        
        # タッキングとジャイブを区別（風向があれば）
        wind_direction_col = self.params['wind_direction_column']
        if wind_direction_col in result_df.columns:
            # マニューバの前後で風の相対角度が反転するかどうかを確認
            result_df['wind_relative_angle'] = (result_df[wind_direction_col] - result_df[direction_col]) % 360
            
            # 風の相対角度が反転するタッキングを特定
            result_df['wind_relative_angle_change'] = result_df['wind_relative_angle'].diff().abs()
            
            # タッキングは風の相対角度が大きく変化（通常は約90度×2）
            result_df['is_tacking'] = (result_df['is_tack_or_jibe']) & (result_df['wind_relative_angle_change'] > 150)
            
            # ジャイブは方向変化が大きいがタッキングではない
            result_df['is_jibing'] = (result_df['is_tack_or_jibe']) & (~result_df['is_tacking'])
        else:
            # 風向データがない場合は区別できないのでタッキングとして扱う
            result_df['is_tacking'] = result_df['is_tack_or_jibe']
            result_df['is_jibing'] = False
        
        # タッキング前後の速度比率を計算
        result_df['speed_after_maneuver'] = np.nan
        result_df['maneuver_efficiency'] = np.nan
        
        # タッキング/ジャイブのインデックスを取得
        maneuver_indices = result_df.index[result_df['is_tack_or_jibe']].tolist()
        
        # 前後の期間（秒）
        before_period = self.params.get('before_period', 10)  # タッキング前の期間（秒）
        after_period = self.params.get('after_period', 30)    # タッキング後の期間（秒）
        
        time_col = self.params['time_column']
        has_time = time_col in result_df.columns and pd.api.types.is_datetime64_any_dtype(result_df[time_col])
        
        for idx in maneuver_indices:
            if idx > 0 and idx < len(result_df) - 1:
                # 時間データがある場合は、時間ベースでサンプリング
                if has_time:
                    maneuver_time = result_df.loc[idx, time_col]
                    
                    # タッキング前のデータ（指定期間内）
                    before_data = result_df[(result_df[time_col] < maneuver_time) & 
                                     (result_df[time_col] >= maneuver_time - pd.Timedelta(seconds=before_period))]
                    
                    # タッキング後のデータ（指定期間内）
                    after_data = result_df[(result_df[time_col] > maneuver_time) & 
                                    (result_df[time_col] <= maneuver_time + pd.Timedelta(seconds=after_period))]
                
                else:
                    # 時間データがない場合は、インデックスベースでサンプリング
                    before_range = range(max(0, idx - before_period), idx)
                    after_range = range(idx + 1, min(len(result_df), idx + after_period + 1))
                    
                    before_data = result_df.iloc[before_range]
                    after_data = result_df.iloc[after_range]
                
                # タッキング前後の平均速度を計算
                if not before_data.empty and not after_data.empty:
                    speed_before = before_data[speed_col].mean()
                    speed_after = after_data[speed_col].mean()
                    
                    # 最速速度の到達時間（マニューバ後）
                    recovery_time = None
                    if has_time and not after_data.empty:
                        # 速度回復の閾値（マニューバ前の速度の95%）
                        recovery_threshold = speed_before * 0.95
                        
                        # 閾値を超えた最初の時間を特定
                        recovery_points = after_data[after_data[speed_col] >= recovery_threshold]
                        if not recovery_points.empty:
                            recovery_time = (recovery_points.iloc[0][time_col] - maneuver_time).total_seconds()
                    
                    # 結果をDataFrameに保存
                    result_df.loc[idx, 'speed_before_maneuver'] = speed_before
                    result_df.loc[idx, 'speed_after_maneuver'] = speed_after
                    result_df.loc[idx, 'maneuver_efficiency'] = speed_after / speed_before if speed_before > 0 else np.nan
                    
                    if recovery_time is not None:
                        result_df.loc[idx, 'recovery_time'] = recovery_time
        
        # タッキングとジャイブで分けた効率値も計算
        if 'is_tacking' in result_df.columns and 'is_jibing' in result_df.columns:
            # タッキング効率
            tacking_indices = result_df.index[result_df['is_tacking']].tolist()
            if tacking_indices:
                result_df.loc[tacking_indices, 'tacking_efficiency'] = result_df.loc[tacking_indices, 'maneuver_efficiency']
            
            # ジャイブ効率
            jibing_indices = result_df.index[result_df['is_jibing']].tolist()
            if jibing_indices:
                result_df.loc[jibing_indices, 'jibing_efficiency'] = result_df.loc[jibing_indices, 'maneuver_efficiency']
        
        return result_df
