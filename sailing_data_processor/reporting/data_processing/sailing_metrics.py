"""
sailing_data_processor.reporting.data_processing.sailing_metrics

セーリング特化型の指標計算機能を提供するモジュールです。
VMG、タッキング効率、ポイント到達時間などのセーリング特有の指標を計算します。
"""

from typing import Dict, List, Any, Optional, Union, Tuple, Callable
import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta

from sailing_data_processor.reporting.data_processing.calculators import BaseCalculator


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
            self._calculate_wind_vmg(result_df)
        
        # 目標地点へのVMGの計算
        if 'target_vmg' in metrics:
            self._calculate_target_vmg(result_df)
        
        # タッキング効率の計算
        if 'tacking_efficiency' in metrics:
            self._calculate_tacking_efficiency(result_df)
        
        # レグ（コースの区間）分析
        if 'leg_analysis' in metrics:
            self._calculate_leg_analysis(result_df)
        
        # 対ターゲット速度比の計算
        if 'target_speed_ratio' in metrics:
            self._calculate_target_speed_ratio(result_df)
        
        # 風向による速度効率の計算
        if 'wind_angle_efficiency' in metrics:
            self._calculate_wind_angle_efficiency(result_df)
        
        return result_df
    
    def _calculate_wind_vmg(self, df: pd.DataFrame) -> None:
        """
        風上/風下VMGを計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
        """
        # 必要な列の存在を確認
        required_columns = [
            self.params['speed_column'],
            self.params['direction_column'],
            self.params['wind_direction_column']
        ]
        
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Cannot calculate VMG due to missing columns")
            return
        
        speed_col = self.params['speed_column']
        direction_col = self.params['direction_column']
        wind_direction_col = self.params['wind_direction_column']
        
        # 風向と艇の進行方向の差（角度）を計算
        df['wind_angle'] = (df[wind_direction_col] - df[direction_col]) % 360
        
        # 180度を超える角度は反対側からの角度として調整
        df.loc[df['wind_angle'] > 180, 'wind_angle'] = 360 - df.loc[df['wind_angle'] > 180, 'wind_angle']
        
        # VMGの計算
        # 風上方向のVMG: speed * cos(wind_angle)
        # 風下方向のVMG: speed * cos(180 - wind_angle)
        df['vmg_upwind'] = df[speed_col] * np.cos(np.radians(df['wind_angle']))
        df['vmg_downwind'] = df[speed_col] * np.cos(np.radians(180 - df['wind_angle']))
        
        # 風上/風下タイプの判定（45度を境界とする）
        df['sailing_type'] = 'reaching'
        df.loc[df['wind_angle'] <= 45, 'sailing_type'] = 'upwind'
        df.loc[df['wind_angle'] >= 135, 'sailing_type'] = 'downwind'
        
        # 総合VMG（風上セーリング時は風上VMG、風下セーリング時は風下VMG）
        df['vmg'] = np.where(df['sailing_type'] == 'upwind', df['vmg_upwind'], 
                         np.where(df['sailing_type'] == 'downwind', df['vmg_downwind'], 0))
        
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
        upwind_mask = df['sailing_type'] == 'upwind'
        if upwind_mask.any():
            optimal_upwind_vmg = df.loc[upwind_mask, speed_col] * np.cos(np.radians(optimal_upwind_angle))
            df.loc[upwind_mask, 'vmg_efficiency'] = (df.loc[upwind_mask, 'vmg_upwind'] / optimal_upwind_vmg)
        
        # 風下セーリング時の効率
        downwind_mask = df['sailing_type'] == 'downwind'
        if downwind_mask.any():
            optimal_downwind_vmg = df.loc[downwind_mask, speed_col] * np.cos(np.radians(180 - optimal_downwind_angle))
            df.loc[downwind_mask, 'vmg_efficiency'] = (df.loc[downwind_mask, 'vmg_downwind'] / optimal_downwind_vmg)
    
    def _calculate_target_vmg(self, df: pd.DataFrame) -> None:
        """
        目標地点へのVMGを計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
        """
        # 必要な列の存在を確認
        required_columns = [
            self.params['speed_column'],
            self.params['direction_column']
        ]
        
        position_columns = self.params['position_columns']
        target_position = self.params.get('target_position')
        
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Cannot calculate target VMG due to missing columns")
            return
        
        if not target_position or len(target_position) != 2 or not all(col in df.columns for col in position_columns):
            print(f"Warning: Cannot calculate target VMG due to missing target position or position columns")
            return
        
        speed_col = self.params['speed_column']
        direction_col = self.params['direction_column']
        lat_col, lng_col = position_columns
        target_lat, target_lng = target_position
        
        # 各ポイントから目標地点への方位角を計算
        df['target_bearing'] = df.apply(
            lambda row: self._calculate_bearing(row[lat_col], row[lng_col], target_lat, target_lng),
            axis=1
        )
        
        # 艇の進行方向と目標地点への方位角の差を計算
        df['target_angle'] = (df['target_bearing'] - df[direction_col]) % 360
        
        # 180度を超える角度は反対側からの角度として調整
        df.loc[df['target_angle'] > 180, 'target_angle'] = 360 - df.loc[df['target_angle'] > 180, 'target_angle']
        
        # 目標地点へのVMGを計算
        df['target_vmg'] = df[speed_col] * np.cos(np.radians(df['target_angle']))
        
        # 目標地点への距離を計算
        df['target_distance'] = df.apply(
            lambda row: self._calculate_distance(row[lat_col], row[lng_col], target_lat, target_lng),
            axis=1
        )
        
        # 推定到達時間を計算（現在の速度と方向が変わらないと仮定）
        df['estimated_arrival_time'] = np.nan
        
        # 時間列があり、目標VMGが正の場合のみ計算
        time_col = self.params['time_column']
        if time_col in df.columns and pd.api.types.is_datetime64_any_dtype(df[time_col]):
            positive_vmg_mask = df['target_vmg'] > 0
            if positive_vmg_mask.any():
                # 時間（秒）= 距離（m）/ VMG（m/s）
                # 速度の単位がノットの場合は、m/sに変換（1ノット ≈ 0.51444 m/s）
                speed_factor = 0.51444 if self.params.get('speed_unit', 'knot') == 'knot' else 1.0
                
                # 推定到達時間 = 現在時刻 + 距離/VMG
                estimated_seconds = df.loc[positive_vmg_mask, 'target_distance'] / (df.loc[positive_vmg_mask, 'target_vmg'] * speed_factor)
                df.loc[positive_vmg_mask, 'estimated_arrival_time'] = df.loc[positive_vmg_mask, time_col] + pd.to_timedelta(estimated_seconds, unit='s')
    
    def _calculate_tacking_efficiency(self, df: pd.DataFrame) -> None:
        """
        タッキング効率を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
        """
        # 必要な列の存在を確認
        required_columns = [
            self.params['speed_column'],
            self.params['direction_column']
        ]
        
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Cannot calculate tacking efficiency due to missing columns")
            return
        
        direction_col = self.params['direction_column']
        speed_col = self.params['speed_column']
        
        # 方向の変化を計算
        df['direction_diff'] = df[direction_col].diff().abs()
        
        # 方向の変化が大きい箇所（例：45度以上）をタッキング/ジャイブとして検出
        tacking_threshold = self.params.get('tacking_threshold', 45)
        df['is_tack_or_jibe'] = df['direction_diff'] > tacking_threshold
        
        # タッキングとジャイブを区別（風向があれば）
        wind_direction_col = self.params['wind_direction_column']
        if wind_direction_col in df.columns:
            # マニューバの前後で風の相対角度が反転するかどうかを確認
            df['wind_relative_angle'] = (df[wind_direction_col] - df[direction_col]) % 360
            
            # 風の相対角度が反転するタッキングを特定
            df['wind_relative_angle_change'] = df['wind_relative_angle'].diff().abs()
            
            # タッキングは風の相対角度が大きく変化（通常は約90度×2）
            df['is_tacking'] = (df['is_tack_or_jibe']) & (df['wind_relative_angle_change'] > 150)
            
            # ジャイブは方向変化が大きいがタッキングではない
            df['is_jibing'] = (df['is_tack_or_jibe']) & (~df['is_tacking'])
        else:
            # 風向データがない場合は区別できないのでタッキングとして扱う
            df['is_tacking'] = df['is_tack_or_jibe']
            df['is_jibing'] = False
        
        # タッキング前後の速度比率を計算
        df['speed_after_maneuver'] = np.nan
        df['maneuver_efficiency'] = np.nan
        
        # タッキング/ジャイブのインデックスを取得
        maneuver_indices = df.index[df['is_tack_or_jibe']].tolist()
        
        # 前後の期間（秒）
        before_period = self.params.get('before_period', 10)  # タッキング前の期間（秒）
        after_period = self.params.get('after_period', 30)    # タッキング後の期間（秒）
        
        time_col = self.params['time_column']
        has_time = time_col in df.columns and pd.api.types.is_datetime64_any_dtype(df[time_col])
        
        for idx in maneuver_indices:
            if idx > 0 and idx < len(df) - 1:
                # 時間データがある場合は、時間ベースでサンプリング
                if has_time:
                    maneuver_time = df.loc[idx, time_col]
                    
                    # タッキング前のデータ（指定期間内）
                    before_data = df[(df[time_col] < maneuver_time) & 
                                     (df[time_col] >= maneuver_time - pd.Timedelta(seconds=before_period))]
                    
                    # タッキング後のデータ（指定期間内）
                    after_data = df[(df[time_col] > maneuver_time) & 
                                    (df[time_col] <= maneuver_time + pd.Timedelta(seconds=after_period))]
                
                else:
                    # 時間データがない場合は、インデックスベースでサンプリング
                    before_range = range(max(0, idx - before_period), idx)
                    after_range = range(idx + 1, min(len(df), idx + after_period + 1))
                    
                    before_data = df.iloc[before_range]
                    after_data = df.iloc[after_range]
                
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
                    df.loc[idx, 'speed_before_maneuver'] = speed_before
                    df.loc[idx, 'speed_after_maneuver'] = speed_after
                    df.loc[idx, 'maneuver_efficiency'] = speed_after / speed_before if speed_before > 0 else np.nan
                    
                    if recovery_time is not None:
                        df.loc[idx, 'recovery_time'] = recovery_time
        
        # タッキングとジャイブで分けた効率値も計算
        if 'is_tacking' in df.columns and 'is_jibing' in df.columns:
            # タッキング効率
            tacking_indices = df.index[df['is_tacking']].tolist()
            if tacking_indices:
                df.loc[tacking_indices, 'tacking_efficiency'] = df.loc[tacking_indices, 'maneuver_efficiency']
            
            # ジャイブ効率
            jibing_indices = df.index[df['is_jibing']].tolist()
            if jibing_indices:
                df.loc[jibing_indices, 'jibing_efficiency'] = df.loc[jibing_indices, 'maneuver_efficiency']
    
    def _calculate_leg_analysis(self, df: pd.DataFrame) -> None:
        """
        レグ（コースの区間）分析
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
        """
        # 必要な列の存在を確認
        required_columns = [self.params['time_column']]
        
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Cannot calculate leg analysis due to missing columns")
            return
        
        # レグ情報がある場合のみ計算
        leg_column = self.params.get('leg_column', 'leg')
        if leg_column not in df.columns:
            print(f"Warning: Cannot calculate leg analysis due to missing leg column")
            return
        
        time_col = self.params['time_column']
        
        # 時間型であることを確認
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            try:
                df[time_col] = pd.to_datetime(df[time_col])
            except:
                print(f"Warning: Cannot convert {time_col} to datetime")
                return
        
        # レグごとにグループ化して計算
        leg_groups = df.groupby(leg_column)
        
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
            if speed_col in df.columns:
                leg_data['avg_speed'] = group[speed_col].mean()
                leg_data['max_speed'] = group[speed_col].max()
                leg_data['min_speed'] = group[speed_col].min()
                leg_data['speed_std'] = group[speed_col].std()
            
            # VMG情報がある場合
            if 'vmg' in df.columns:
                leg_data['avg_vmg'] = group['vmg'].mean()
                leg_data['max_vmg'] = group['vmg'].max()
                leg_data['min_vmg'] = group['vmg'].min()
            
            # タッキング情報がある場合
            if 'is_tacking' in df.columns:
                leg_data['tack_count'] = group['is_tacking'].sum()
                
                # タッキング効率情報がある場合
                if 'tacking_efficiency' in df.columns:
                    tacking_efficiencies = group['tacking_efficiency'].dropna()
                    if not tacking_efficiencies.empty:
                        leg_data['avg_tacking_efficiency'] = tacking_efficiencies.mean()
            
            # ジャイブ情報がある場合
            if 'is_jibing' in df.columns:
                leg_data['jibe_count'] = group['is_jibing'].sum()
                
                # ジャイブ効率情報がある場合
                if 'jibing_efficiency' in df.columns:
                    jibing_efficiencies = group['jibing_efficiency'].dropna()
                    if not jibing_efficiencies.empty:
                        leg_data['avg_jibing_efficiency'] = jibing_efficiencies.mean()
            
            # 風向風速情報がある場合
            wind_direction_col = self.params['wind_direction_column']
            wind_speed_col = self.params['wind_speed_column']
            
            if wind_direction_col in df.columns:
                leg_data['avg_wind_direction'] = self._calculate_circular_mean(group[wind_direction_col])
                leg_data['wind_direction_std'] = self._calculate_circular_std(group[wind_direction_col])
            
            if wind_speed_col in df.columns:
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
                leg_mask = df[leg_column] == leg_id_value
                
                # 各分析値をレグ内の全行に複製
                for col in leg_analysis.columns:
                    if col != 'leg_id' and not col.startswith('start_') and not col.startswith('end_'):
                        df.loc[leg_mask, f'leg_{col}'] = leg_row[col]
    
    def _calculate_target_speed_ratio(self, df: pd.DataFrame) -> None:
        """
        対ターゲット速度比を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
        """
        # 必要な列の存在を確認
        required_columns = [
            self.params['speed_column'],
            self.params['wind_speed_column']
        ]
        
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Cannot calculate target speed ratio due to missing columns")
            return
        
        speed_col = self.params['speed_column']
        wind_speed_col = self.params['wind_speed_column']
        
        # ターゲット速度の設定
        target_speeds = self.params.get('target_speeds', {})
        
        # ターゲット速度列を初期化
        df['target_speed'] = np.nan
        
        # ターゲット速度が指定されている場合
        if target_speeds:
            # 風速ごとのターゲット速度を設定
            for wind_speed, target_speed in target_speeds.items():
                wind_speed_float = float(wind_speed)
                df.loc[df[wind_speed_col] == wind_speed_float, 'target_speed'] = target_speed
            
            # 未設定の風速に対して補間
            # 指定された風速値をソート
            wind_speeds = sorted([float(ws) for ws in target_speeds.keys()])
            
            for i, row in df.iterrows():
                wind_speed = row[wind_speed_col]
                if np.isnan(row.get('target_speed', np.nan)):
                    # 補間
                    if wind_speed <= wind_speeds[0]:
                        # 最小風速以下の場合
                        ratio = wind_speed / wind_speeds[0] if wind_speeds[0] > 0 else 0
                        df.loc[i, 'target_speed'] = float(target_speeds[str(wind_speeds[0])]) * ratio
                    elif wind_speed >= wind_speeds[-1]:
                        # 最大風速以上の場合
                        df.loc[i, 'target_speed'] = float(target_speeds[str(wind_speeds[-1])])
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
                                
                                df.loc[i, 'target_speed'] = lower_target + ratio * (upper_target - lower_target)
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
            if 'wind_angle' in df.columns:
                # 風向に応じた係数を初期化
                df['speed_factor'] = speed_factor
                
                # 風上（0-45度）では係数を下げる
                upwind_mask = df['wind_angle'] <= 45
                if upwind_mask.any():
                    df.loc[upwind_mask, 'speed_factor'] = speed_factor * 0.9
                
                # 風下（135-180度）では係数を下げる
                downwind_mask = df['wind_angle'] >= 135
                if downwind_mask.any():
                    df.loc[downwind_mask, 'speed_factor'] = speed_factor * 0.85
                
                # リーチング（45-135度）では係数を上げる
                reaching_mask = (df['wind_angle'] > 45) & (df['wind_angle'] < 135)
                if reaching_mask.any():
                    df.loc[reaching_mask, 'speed_factor'] = speed_factor * 1.1
                
                # ターゲット速度を計算
                df['target_speed'] = df[wind_speed_col] * df['speed_factor']
                
                # 一時的な係数列を削除
                df.drop('speed_factor', axis=1, inplace=True)
            else:
                # 風角度情報がない場合は一律の係数を適用
                df['target_speed'] = df[wind_speed_col] * speed_factor
        
        # ターゲット速度比の計算
        df['target_speed_ratio'] = df[speed_col] / df['target_speed']
        
        # 無効な値（0除算など）を処理
        df['target_speed_ratio'] = df['target_speed_ratio'].replace([np.inf, -np.inf], np.nan)
    
    def _calculate_wind_angle_efficiency(self, df: pd.DataFrame) -> None:
        """
        風向による速度効率を計算
        
        Parameters
        ----------
        df : pd.DataFrame
            計算対象DataFrame
        """
        # 必要な列の存在を確認
        required_columns = [
            self.params['speed_column'],
            self.params['direction_column'],
            self.params['wind_direction_column']
        ]
        
        if not all(col in df.columns for col in required_columns):
            print(f"Warning: Cannot calculate wind angle efficiency due to missing columns")
            return
        
        # 風角度が計算済みかどうか確認
        if 'wind_angle' not in df.columns:
            # 風向と艇の進行方向の差（角度）を計算
            speed_col = self.params['speed_column']
            direction_col = self.params['direction_column']
            wind_direction_col = self.params['wind_direction_column']
            
            df['wind_angle'] = (df[wind_direction_col] - df[direction_col]) % 360
            
            # 180度を超える角度は反対側からの角度として調整
            df.loc[df['wind_angle'] > 180, 'wind_angle'] = 360 - df.loc[df['wind_angle'] > 180, 'wind_angle']
        
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
        df['wind_angle_theoretical_efficiency'] = df['wind_angle'].apply(get_efficiency_for_angle)
        
        # 風速情報がある場合、理論的な速度を計算
        wind_speed_col = self.params['wind_speed_column']
        speed_col = self.params['speed_column']
        
        if wind_speed_col in df.columns:
            # 理論的な艇速を計算（風速 × 効率係数）
            df['theoretical_speed'] = df[wind_speed_col] * df['wind_angle_theoretical_efficiency']
            
            # 実際の速度と理論的な速度の比率
            df['wind_angle_efficiency'] = df[speed_col] / df['theoretical_speed']
            
            # 無効な値（0除算など）を処理
            df['wind_angle_efficiency'] = df['wind_angle_efficiency'].replace([np.inf, -np.inf], np.nan)
    
    def _calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
    
    def _calculate_circular_mean(self, angles: pd.Series) -> float:
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
    
    def _calculate_circular_std(self, angles: pd.Series) -> float:
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
