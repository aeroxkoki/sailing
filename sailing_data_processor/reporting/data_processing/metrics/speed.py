# -*- coding: utf-8 -*-
"""
Module for speed performance metrics calculations.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sailing_data_processor.reporting.data_processing.calculators import BaseCalculator


class SpeedMetricsCalculator(BaseCalculator):
    """
    速度メトリクスを計算するクラス
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
    
    def calculate_target_speed_ratio(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        対ターゲット速度比を計算
        
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
            self.params['wind_speed_column']
        ]
        
        if not all(col in result_df.columns for col in required_columns):
            print(f"Warning: Cannot calculate target speed ratio due to missing columns")
            return result_df
        
        speed_col = self.params['speed_column']
        wind_speed_col = self.params['wind_speed_column']
        
        # ターゲット速度の設定
        target_speeds = self.params.get('target_speeds', {})
        
        # ターゲット速度列を初期化
        result_df['target_speed'] = np.nan
        
        # ターゲット速度が指定されている場合
        if target_speeds:
            # 風速ごとのターゲット速度を設定
            for wind_speed, target_speed in target_speeds.items():
                wind_speed_float = float(wind_speed)
                result_df.loc[result_df[wind_speed_col] == wind_speed_float, 'target_speed'] = target_speed
            
            # 未設定の風速に対して補間
            # 指定された風速値をソート
            wind_speeds = sorted([float(ws) for ws in target_speeds.keys()])
            
            for i, row in result_df.iterrows():
                wind_speed = row[wind_speed_col]
                if np.isnan(row.get('target_speed', np.nan)):
                    # 補間
                    if wind_speed <= wind_speeds[0]:
                        # 最小風速以下の場合
                        ratio = wind_speed / wind_speeds[0] if wind_speeds[0] > 0 else 0
                        result_df.loc[i, 'target_speed'] = float(target_speeds[str(wind_speeds[0])]) * ratio
                    elif wind_speed >= wind_speeds[-1]:
                        # 最大風速以上の場合
                        result_df.loc[i, 'target_speed'] = float(target_speeds[str(wind_speeds[-1])])
                    else:
                        # 中間の風速の場合、線形補間
                        for j in range(len(wind_speeds) - 1):
                            if wind_speeds[j] <= wind_speed < wind_speeds[j + 1]:
                                lower_wind = wind_speeds[j]
                                upper_wind = wind_speeds[j + 1]
                                
                                # 線形補間
                                ratio = (wind_speed - lower_wind) / (upper_wind - lower_wind)
                                lower_target = float(target_speeds[str(lower_wind)])
                                upper_target = float(target_speeds[str(upper_wind)])
                                
                                result_df.loc[i, 'target_speed'] = lower_target + ratio * (upper_target - lower_target)
                                break
        
        # ターゲット速度が指定されていない場合は、風速の一定割合をターゲットとして設定
        else:
            # 艇種に応じたターゲット速度係数
            boat_class = self.params.get('boat_class')
            speed_factor = 0.7  # デフォルト係数
            
            if boat_class:
                if boat_class == '470':
                    speed_factor = 0.65
                elif boat_class == '49er':
                    speed_factor = 0.75
                elif boat_class == 'finn':
                    speed_factor = 0.65
                elif boat_class == 'laser':
                    speed_factor = 0.65
                elif boat_class == 'nacra17':
                    speed_factor = 0.8
            
            # 風角度がある場合、風上/風下で係数を調整
            if 'wind_angle' in result_df.columns:
                # 風向に応じた係数を初期化
                result_df['speed_factor'] = speed_factor
                
                # 風上（0-45度）では係数を下げる
                upwind_mask = result_df['wind_angle'] <= 45
                if upwind_mask.any():
                    result_df.loc[upwind_mask, 'speed_factor'] = speed_factor * 0.9
                
                # 風下（135-180度）では係数を下げる
                downwind_mask = result_df['wind_angle'] >= 135
                if downwind_mask.any():
                    result_df.loc[downwind_mask, 'speed_factor'] = speed_factor * 0.85
                
                # リーチング（45-135度）では係数を上げる
                reaching_mask = (result_df['wind_angle'] > 45) & (result_df['wind_angle'] < 135)
                if reaching_mask.any():
                    result_df.loc[reaching_mask, 'speed_factor'] = speed_factor * 1.1
                
                # ターゲット速度を計算
                result_df['target_speed'] = result_df[wind_speed_col] * result_df['speed_factor']
                
                # 一時的な係数列を削除
                result_df.drop('speed_factor', axis=1, inplace=True)
            else:
                # 風角度情報がない場合は一律の係数を適用
                result_df['target_speed'] = result_df[wind_speed_col] * speed_factor
        
        # ターゲット速度比の計算
        result_df['target_speed_ratio'] = result_df[speed_col] / result_df['target_speed']
        
        # 無効な値（0除算など）を処理
        result_df['target_speed_ratio'] = result_df['target_speed_ratio'].replace([np.inf, -np.inf], np.nan)
        
        return result_df
