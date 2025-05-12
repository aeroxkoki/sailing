# -*- coding: utf-8 -*-
"""
Performance Calculator Module - Provides functionality for performance calculations.
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np

from sailing_data_processor.reporting.data_processing.base_calculator import BaseCalculator


class PerformanceCalculator(BaseCalculator):
    """
    パフォーマンス指標計算
    
    セーリングのパフォーマンス指標を計算します。
    VMG（風上/風下方向の有効速度）、対ターゲット速度比率、タッキング効率などを計算します。
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        params : Optional[Dict[str, Any]], optional
            計算パラメータ, by default None
            
            speed_column: str
                速度の列名
            direction_column: str
                方向の列名
            wind_direction_column: str
                風向の列名
            wind_speed_column: str
                風速の列名
            target_speeds: Dict[float, float]
                風速に対するターゲット速度の辞書
            metrics: List[str]
                計算する指標のリスト ('vmg', 'target_ratio', 'tacking_efficiency')
        """
        super().__init__(params)
        
        # デフォルトパラメータの設定
        if 'speed_column' not in self.params:
            self.params['speed_column'] = 'speed'
        
        if 'direction_column' not in self.params:
            self.params['direction_column'] = 'direction'
        
        if 'wind_direction_column' not in self.params:
            self.params['wind_direction_column'] = 'wind_direction'
        
        if 'wind_speed_column' not in self.params:
            self.params['wind_speed_column'] = 'wind_speed'
        
        if 'metrics' not in self.params:
            self.params['metrics'] = ['vmg', 'target_ratio']
    
    def _calculate_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameのパフォーマンス指標を計算
        
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
        
        # VMGの計算には風向と艇の進行方向が必要
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            # 欠損列がある場合は、その指標の計算をスキップ
            if 'vmg' in self.params['metrics']:
                print(f"Warning: Cannot calculate VMG due to missing columns: {missing_columns}")
            required_for_vmg = False
        else:
            required_for_vmg = True
        
        # ターゲット速度比の計算には風速と艇速が必要
        if (self.params['speed_column'] not in df.columns or 
            self.params['wind_speed_column'] not in df.columns):
            if 'target_ratio' in self.params['metrics']:
                print(f"Warning: Cannot calculate target ratio due to missing columns: {self.params['speed_column']} or {self.params['wind_speed_column']}")
            required_for_target = False
        else:
            required_for_target = True
        
        # 指標の計算
        metrics = self.params['metrics']
        
        # VMG（Velocity Made Good）の計算
        if 'vmg' in metrics and required_for_vmg:
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
            
            # 正のVMG値は風上方向、負のVMG値は風下方向の効率を表す
            result_df['vmg'] = result_df['vmg_upwind']
            
            # VMG効率（実際のVMGと理論上の最大VMGの比率）
            # 風上と風下の区別
            upwind_mask = result_df['wind_angle'] <= 90
            downwind_mask = ~upwind_mask
            
            # 理論上の最大VMG（仮の値、実際はボートの極曲線から導出）
            # 風上：45度で最大VMG、風下：135度で最大VMG
            optimal_upwind_angle = 45  # 実際のボートによって異なる
            optimal_downwind_angle = 135  # 実際のボートによって異なる
            
            # VMG効率の計算
            # 風上の場合
            if 'vmg_efficiency' not in result_df.columns:
                result_df['vmg_efficiency'] = np.nan
                
            upwind_optimal_vmg = result_df.loc[upwind_mask, speed_col] * np.cos(np.radians(optimal_upwind_angle))
            result_df.loc[upwind_mask, 'vmg_efficiency'] = (
                result_df.loc[upwind_mask, 'vmg_upwind'] / upwind_optimal_vmg
            )
            
            # 風下の場合
            downwind_optimal_vmg = result_df.loc[downwind_mask, speed_col] * np.cos(np.radians(180 - optimal_downwind_angle))
            result_df.loc[downwind_mask, 'vmg_efficiency'] = (
                result_df.loc[downwind_mask, 'vmg_downwind'] / downwind_optimal_vmg
            )
        
        # ターゲット速度比の計算
        if 'target_ratio' in metrics and required_for_target:
            speed_col = self.params['speed_column']
            wind_speed_col = self.params['wind_speed_column']
            target_speeds = self.params.get('target_speeds', {})
            
            # ターゲット速度を計算
            result_df['target_speed'] = np.nan
            
            # ターゲット速度が指定されている場合
            if target_speeds:
                # 風速ごとのターゲット速度を設定
                for wind_speed, target_speed in target_speeds.items():
                    result_df.loc[result_df[wind_speed_col] == wind_speed, 'target_speed'] = target_speed
                
                # 未設定の風速に対して補間
                # ソートされた風速のリスト
                wind_speeds = sorted(target_speeds.keys())
                
                for i, row in result_df.iterrows():
                    wind_speed = row[wind_speed_col]
                    if np.isnan(row['target_speed']):
                        # 補間
                        if wind_speed < wind_speeds[0]:
                            # 最小風速以下の場合
                            ratio = wind_speed / wind_speeds[0]
                            result_df.loc[i, 'target_speed'] = target_speeds[wind_speeds[0]] * ratio
                        elif wind_speed > wind_speeds[-1]:
                            # 最大風速以上の場合
                            result_df.loc[i, 'target_speed'] = target_speeds[wind_speeds[-1]]
                        else:
                            # 中間の風速の場合、線形補間
                            lower_idx = next(j for j, ws in enumerate(wind_speeds) if ws > wind_speed) - 1
                            upper_idx = lower_idx + 1
                            
                            lower_wind = wind_speeds[lower_idx]
                            upper_wind = wind_speeds[upper_idx]
                            
                            # 線形補間
                            ratio = (wind_speed - lower_wind) / (upper_wind - lower_wind)
                            lower_target = target_speeds[lower_wind]
                            upper_target = target_speeds[upper_wind]
                            
                            result_df.loc[i, 'target_speed'] = lower_target + ratio * (upper_target - lower_target)
            
            # ターゲット速度が指定されていない場合は、風速の一定割合をターゲットとして設定
            else:
                # 仮のターゲット速度として風速の70%を設定
                result_df['target_speed'] = result_df[wind_speed_col] * 0.7
            
            # ターゲット速度比の計算
            result_df['target_ratio'] = result_df[speed_col] / result_df['target_speed']
        
        # タッキング効率の計算
        if 'tacking_efficiency' in metrics:
            # タッキングの検出とその効率計算は複雑なため、別途実装
            # ここでは簡略的な実装として、方向の変化が大きい箇所をタッキングとして検出
            
            # direction_colが存在する場合のみ計算
            if self.params['direction_column'] in df.columns:
                direction_col = self.params['direction_column']
                speed_col = self.params['speed_column']
                
                # 方向の変化を計算
                result_df['direction_diff'] = result_df[direction_col].diff().abs()
                
                # 方向の変化が大きい箇所（例：60度以上）をタッキングとして検出
                tacking_threshold = self.params.get('tacking_threshold', 60)
                result_df['is_tacking'] = result_df['direction_diff'] > tacking_threshold
                
                # タッキング前後の速度の比率を計算
                result_df['speed_after_tack'] = np.nan
                result_df['tacking_efficiency'] = np.nan
                
                # タッキング位置を特定
                tack_indices = result_df.index[result_df['is_tacking']]
                
                # 各タッキングの効率を計算
                for tack_idx in tack_indices:
                    if tack_idx > 0 and tack_idx < len(result_df) - 1:
                        # タッキング前の速度（数ポイントの平均）
                        pre_indices = range(max(0, tack_idx - 5), tack_idx)
                        speed_before = result_df.loc[pre_indices, speed_col].mean()
                        
                        # タッキング後の速度（数ポイントの平均）
                        post_indices = range(tack_idx + 1, min(len(result_df), tack_idx + 6))
                        speed_after = result_df.loc[post_indices, speed_col].mean()
                        
                        # タッキング後の速度を記録
                        result_df.loc[tack_idx, 'speed_after_tack'] = speed_after
                        
                        # タッキング効率を計算（タッキング後の速度 / タッキング前の速度）
                        if speed_before > 0:
                            result_df.loc[tack_idx, 'tacking_efficiency'] = speed_after / speed_before
        
        return result_df
    
    def _calculate_dict_list(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        辞書のリストのパフォーマンス指標を計算
        
        Parameters
        ----------
        data : List[Dict[str, Any]]
            計算対象の辞書リスト
            
        Returns
        -------
        List[Dict[str, Any]]
            計算結果の辞書リスト
        """
        if not data:
            return data
        
        # DataFrameに変換して処理
        df = pd.DataFrame(data)
        result_df = self._calculate_dataframe(df)
        
        # 再度リストに変換
        return result_df.to_dict('records')
