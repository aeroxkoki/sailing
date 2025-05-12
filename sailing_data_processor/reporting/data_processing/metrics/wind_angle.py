# -*- coding: utf-8 -*-
"""
Module for wind angle efficiency calculations.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from sailing_data_processor.reporting.data_processing.calculators import BaseCalculator


class WindAngleCalculator(BaseCalculator):
    """
    風向角度に基づく効率を計算するクラス
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
    
    def calculate_wind_angle_efficiency(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        風向による速度効率を計算
        
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
            print(f"Warning: Cannot calculate wind angle efficiency due to missing columns")
            return result_df
        
        # 風角度が計算済みかどうか確認
        if 'wind_angle' not in result_df.columns:
            # 風向と艇の進行方向の差（角度）を計算
            speed_col = self.params['speed_column']
            direction_col = self.params['direction_column']
            wind_direction_col = self.params['wind_direction_column']
            
            result_df['wind_angle'] = (result_df[wind_direction_col] - result_df[direction_col]) % 360
            
            # 180度を超える角度は反対側からの角度として調整
            result_df.loc[result_df['wind_angle'] > 180, 'wind_angle'] = 360 - result_df.loc[result_df['wind_angle'] > 180, 'wind_angle']
        
        # 風角度による艇速の理論曲線
        # 風角度ごとの速度効率を設定（多項式フィットなどで近似）
        # 角度：効率のペア（角度: 風速に対する艇速の比率）
        angles = np.arange(0, 181, 5)
        
        # 一般的な艇の極曲線から推定した効率係数
        # 風上（0度）から風下（180度）までの効率値
        # 角度による速度のピークを表現
        efficiency_values = [
            0.10, 0.25, 0.35, 0.45, 0.52,  # 0-20度
            0.57, 0.62, 0.65, 0.67, 0.69,  # 25-45度
            0.71, 0.74, 0.78, 0.82, 0.85,  # 50-70度
            0.87, 0.89, 0.90, 0.91, 0.90,  # 75-95度
            0.89, 0.87, 0.85, 0.82, 0.79,  # 100-120度
            0.76, 0.72, 0.68, 0.64, 0.60,  # 125-145度
            0.56, 0.53, 0.50, 0.47, 0.45,  # 150-170度
            0.43                           # 175-180度
        ]
        
        # 艇種別に効率テーブルを調整
        boat_class = self.params.get('boat_class')
        if boat_class:
            if boat_class == '49er' or boat_class == 'nacra17':
                # より高速な艇種は風下での効率が高い
                for i in range(20, 37):  # 100-180度
                    efficiency_values[i] += 0.05
            elif boat_class == 'finn':
                # より安定した艇種は風上での効率が高い
                for i in range(0, 10):  # 0-45度
                    efficiency_values[i] += 0.03
        
        # 風角度から効率を補間する関数
        def get_efficiency_for_angle(angle):
            # 角度のインデックスを計算（5度単位でサンプリング）
            idx = int(angle / 5)
            
            # インデックスが範囲内かチェック
            if idx >= len(efficiency_values) - 1:
                return efficiency_values[-1]
            
            # 線形補間
            frac = (angle % 5) / 5
            return efficiency_values[idx] * (1 - frac) + efficiency_values[idx + 1] * frac
        
        # 風角度ごとの理論的な速度効率を計算
        result_df['wind_angle_theoretical_efficiency'] = result_df['wind_angle'].apply(get_efficiency_for_angle)
        
        # 風速情報がある場合、理論的な速度を計算
        wind_speed_col = self.params['wind_speed_column']
        speed_col = self.params['speed_column']
        
        if wind_speed_col in result_df.columns:
            # 理論的な艇速を計算（風速 × 効率係数）
            result_df['theoretical_speed'] = result_df[wind_speed_col] * result_df['wind_angle_theoretical_efficiency']
            
            # 実際の速度と理論的な速度の比率
            result_df['wind_angle_efficiency'] = result_df[speed_col] / result_df['theoretical_speed']
            
            # 無効な値（0除算など）を処理
            result_df['wind_angle_efficiency'] = result_df['wind_angle_efficiency'].replace([np.inf, -np.inf], np.nan)
        
        return result_df
