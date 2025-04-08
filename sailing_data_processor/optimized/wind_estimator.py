"""
sailing_data_processor.optimized.wind_estimator

WindEstimatorの最適化バージョン - データモデルの最適化とベクトル化演算を活用
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
import math
import warnings

# 内部モジュールのインポート
from ..wind_estimator import WindEstimator as OriginalWindEstimator
from ..data_model import (
    DataContainer, GPSDataContainer, WindDataContainer, 
    cached, memoize
)

class OptimizedWindEstimator(OriginalWindEstimator):
    """
    風向風速推定クラスの最適化バージョン
    
    GPSデータから艇の動きを分析し、風向風速を推定するためのクラス。
    オリジナルの機能を継承しつつ、パフォーマンスとデータアクセスパターンを改善。
    """
    
    def __init__(self, boat_type: str = "default"):
        """
        初期化
        
        Parameters:
        -----------
        boat_type : str, optional
            艇種（デフォルト: "default"）
        """
        super().__init__(boat_type)
        
        # 最適化バージョン情報
        self.version = "3.0.0"  # 最適化バージョン
        self.name = "OptimizedWindEstimator"
    
    def detect_maneuvers_optimized(self, data: Union[pd.DataFrame, GPSDataContainer]) -> pd.DataFrame:
        """
        航跡データからマニューバー（タック・ジャイブ）を検出する最適化バージョン
        ベクトル化演算を利用して計算量を削減
        
        Parameters:
        -----------
        data : Union[pd.DataFrame, GPSDataContainer]
            GPS時系列データフレームまたはGPSデータコンテナ
            必要なカラム：
            - timestamp: 時刻
            - latitude, longitude: 位置
            - course: 進行方位（度）
            - speed: 速度（ノット）
            
        Returns:
        --------
        pd.DataFrame
            検出されたマニューバーのデータフレーム
        """
        # GPSDataContainerからDataFrameを取得
        if isinstance(data, GPSDataContainer):
            df = data.data
        else:
            df = data
        
        # データ確認
        if df.empty or len(df) < 10:
            return pd.DataFrame()
        
        # 必要なカラムが存在するか確認
        required_columns = ['timestamp', 'latitude', 'longitude', 'course', 'speed']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            warn_msg = f"データに必要なカラムがありません: {missing_columns}"
            warnings.warn(warn_msg)
            return pd.DataFrame()
        
        # 時間順にソート
        df_sorted = df.sort_values('timestamp').reset_index(drop=True)
        
        # NumPy配列に変換して高速化
        timestamps = df_sorted['timestamp'].values
        latitudes = df_sorted['latitude'].values
        longitudes = df_sorted['longitude'].values
        courses = df_sorted['course'].values
        speeds = df_sorted['speed'].values
        
        # 方位の差分を一括計算（ベクトル化）
        # 角度の差分計算用の関数
        def angle_diff(angles):
            # シフトして差分を計算
            angles1 = angles[:-1]
            angles2 = angles[1:]
            
            # 角度差を計算（-180〜180度の範囲）
            diff = ((angles2 - angles1 + 180) % 360) - 180
            
            # 最初のポイントの差分は0に設定
            all_diffs = np.zeros_like(angles)
            all_diffs[1:] = diff
            
            return all_diffs
        
        # 方位の差分を計算
        bearing_changes = angle_diff(courses)
        
        # 速度の変化率を計算
        speed_ratios = np.zeros_like(speeds)
        speed_ratios[1:] = speeds[1:] / np.maximum(speeds[:-1], 0.01)  # 0除算防止
        
        # 極端な値を除外
        speed_ratios[speed_ratios > 5] = 1
        
        # 移動ウィンドウでの方位変化の合計（マニューバー検出用）
        window_size = self.params["maneuver_window_size"]
        min_angle_change = self.params["min_tack_angle_change"]
        
        # 移動ウィンドウでの方位変化の合計を計算
        bearing_change_sum = np.zeros_like(bearing_changes)
        for i in range(len(bearing_changes)):
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(bearing_changes), i + window_size // 2 + 1)
            bearing_change_sum[i] = np.sum(bearing_changes[start_idx:end_idx])
        
        # 方向転換の検出（累積変化がmin_angle_changeを超える場合）
        is_maneuver = bearing_change_sum > min_angle_change
        
        # 連続する方向転換を1つのイベントとしてグループ化
        maneuver_groups = np.zeros_like(is_maneuver, dtype=int)
        group_id = 0
        
        for i in range(1, len(is_maneuver)):
            if is_maneuver[i] \!= is_maneuver[i-1]:
                group_id += 1
            maneuver_groups[i] = group_id
        
        # 方向転換グループごとに最適な転換点を見つける
        maneuver_points = []
        
        # グループIDと対応するインデックスの辞書を作成
        grouped_indices = {}
        for i, group_id in enumerate(maneuver_groups):
            if is_maneuver[i]:
                if group_id not in grouped_indices:
                    grouped_indices[group_id] = []
                grouped_indices[group_id].append(i)
        
        # 各グループの最適なマニューバーポイントを見つける
        for group_id, indices in grouped_indices.items():
            if not indices:
                continue
            
            # 方位変化が最大の地点
            bearing_changes_in_group = np.abs(bearing_changes[indices])
            max_change_idx_in_group = np.argmax(bearing_changes_in_group)
            max_change_idx = indices[max_change_idx_in_group]
            
            # 速度変化がある場合は考慮
            has_speed_drop = np.any(speed_ratios[indices] < 0.9)
            
            if has_speed_drop:
                # 速度降下が最大の地点
                speed_ratios_in_group = speed_ratios[indices]
                min_ratio_idx_in_group = np.argmin(speed_ratios_in_group)
                min_ratio_idx = indices[min_ratio_idx_in_group]
                
                # 方位変化と速度変化の両方がある場合
                idx_diff = abs(max_change_idx - min_ratio_idx)
                
                if idx_diff <= 5:  # 5ポイント以内なら関連していると判断
                    # 2つの地点の時間差
                    t1 = timestamps[max_change_idx]
                    t2 = timestamps[min_ratio_idx]
                    
                    if t1 <= t2:
                        # 通常は方位変化が先、速度低下が後
                        central_idx = max_change_idx
                    else:
                        # 中間点を計算
                        central_time = t1 - (t1 - t2) / 2
                        time_diffs = np.abs([ts - central_time for ts in timestamps[indices]])
                        central_idx = indices[np.argmin(time_diffs)]
                else:
                    central_idx = max_change_idx
            else:
                central_idx = max_change_idx
            
            # 前後のデータを取得してマニューバー情報を作成
            if central_idx < 5 or central_idx >= len(timestamps) - 5:
                continue  # 端すぎる場合はスキップ
            
            # 前後のウィンドウ
            before_window = slice(max(0, central_idx - 10), central_idx)
            after_window = slice(central_idx + 1, min(len(timestamps), central_idx + 11))
            
            # 前後の平均方位と速度
            before_bearing = np.mean(courses[before_window])
            after_bearing = np.mean(courses[after_window])
            bearing_change = self._calculate_angle_difference(after_bearing, before_bearing)
            
            speed_before = np.mean(speeds[before_window])
            speed_after = np.mean(speeds[after_window])
            speed_ratio = speed_after / speed_before if speed_before > 0 else 1.0
            
            # マニューバー時間の長さ
            maneuver_duration = (timestamps[after_window][0] - timestamps[before_window][-1]).total_seconds()
            
            # マニューバーエントリーの作成
            maneuver_entry = {
                'timestamp': timestamps[central_idx],
                'latitude': latitudes[central_idx],
                'longitude': longitudes[central_idx],
                'before_bearing': before_bearing,
                'after_bearing': after_bearing,
                'bearing_change': bearing_change,
                'speed_before': speed_before,
                'speed_after': speed_after,
                'speed_ratio': speed_ratio,
                'maneuver_duration': maneuver_duration,
                'maneuver_type': 'unknown'  # 初期値
            }
            
            maneuver_points.append(maneuver_entry)
        
        # 結果をデータフレームに変換
        result_df = pd.DataFrame(maneuver_points)
        
        # 必要なマニューバー属性がない場合は空のデータフレームを返す
        if result_df.empty or 'bearing_change' not in result_df.columns:
            return pd.DataFrame()
        
        # 極端な値のフィルタリング
        min_duration = self.params["min_maneuver_duration"]
        max_duration = self.params["max_maneuver_duration"]
        
        # 方位変化と所要時間でフィルタリング
        result_df = result_df[
            (abs(result_df['bearing_change']) >= self.params["min_tack_angle_change"]) &
            (result_df['maneuver_duration'] >= min_duration) &
            (result_df['maneuver_duration'] <= max_duration)
        ]
        
        # 検出結果を保存
        self.detected_maneuvers = result_df.to_dict('records')
        
        return result_df
    
    def detect_maneuvers(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        元のメソッドをオーバーライドして最適化バージョンを呼び出す
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPS時系列データフレーム
            
        Returns:
        --------
        pd.DataFrame
            検出されたマニューバーのデータフレーム
        """
        return self.detect_maneuvers_optimized(df)
    
    @cached('wind_direction_name')
    def get_wind_direction_name(self, wind_direction: float) -> str:
        """
        風向を方位名に変換（キャッシュ機能付き）
        
        Parameters:
        -----------
        wind_direction : float
            風向（度、0-360、風が吹いてくる方向）
            
        Returns:
        --------
        str
            風向の方位名（例: "北東", "南南西"）
        """
        return super().get_wind_direction_name(wind_direction)
    
    def estimate_wind_from_gps_data(self, data: Union[pd.DataFrame, GPSDataContainer]) -> WindDataContainer:
        """
        GPSデータから風向風速を推定し、WindDataContainerを返す
        
        Parameters:
        -----------
        data : Union[pd.DataFrame, GPSDataContainer]
            GPS位置データ
            
        Returns:
        --------
        WindDataContainer
            推定された風データ
        """
        # GPSDataContainerからDataFrameを取得
        if isinstance(data, GPSDataContainer):
            df = data.data
        else:
            df = data
        
        # 従来の推定メソッドを使用
        wind_dict = self.estimate_wind_from_maneuvers(df)
        
        # 結果をWindDataContainerに変換
        metadata = {
            'estimation_method': wind_dict['method'],
            'source_data_points': len(df),
            'boat_type': self.boat_type
        }
        
        return WindDataContainer(wind_dict, metadata)
    
    def categorize_maneuvers_optimized(self, maneuvers_df: pd.DataFrame, full_df: pd.DataFrame) -> pd.DataFrame:
        """
        検出されたマニューバーをタック/ジャイブに分類（最適化バージョン）
        
        Parameters:
        -----------
        maneuvers_df : pd.DataFrame
            検出されたマニューバーのデータフレーム
        full_df : pd.DataFrame
            完全な航跡データフレーム
            
        Returns:
        --------
        pd.DataFrame
            タイプ分類されたマニューバーのデータフレーム
        """
        if maneuvers_df.empty or len(maneuvers_df) == 0:
            return maneuvers_df
        
        # コピーを作成
        result_df = maneuvers_df.copy()
        
        # 風向を推定
        estimated_wind = self.estimate_wind_from_course_speed(full_df)
        wind_direction = estimated_wind['direction']
        
        # 各マニューバーを分類（ベクトル化）
        # 風向に対する相対角度を計算（ベクトル化）
        result_df['before_rel_wind'] = result_df['before_bearing'].apply(
            lambda bearing: self._calculate_angle_difference(bearing, wind_direction)
        )
        result_df['after_rel_wind'] = result_df['after_bearing'].apply(
            lambda bearing: self._calculate_angle_difference(bearing, wind_direction)
        )
        
        # 風上/風下判定の閾値
        upwind_threshold = self.params["upwind_threshold"]
        downwind_threshold = self.params["downwind_threshold"]
        
        # 風上/風下の判定（ベクトル化）
        result_df['before_is_upwind'] = abs(result_df['before_rel_wind']) <= upwind_threshold
        result_df['before_is_downwind'] = abs(result_df['before_rel_wind']) >= downwind_threshold
        
        result_df['after_is_upwind'] = abs(result_df['after_rel_wind']) <= upwind_threshold
        result_df['after_is_downwind'] = abs(result_df['after_rel_wind']) >= downwind_threshold
        
        # タックの判定条件（ベクトル化）
        result_df['is_possible_tack'] = (
            # 両方風上、または風上→クローズリーチ、またはクローズリーチ→風上
            ((result_df['before_is_upwind'] | (abs(result_df['before_rel_wind']) <= 60)) &
             (result_df['after_is_upwind'] | (abs(result_df['after_rel_wind']) <= 60))) &
            # 方位変化が60〜180度
            (abs(result_df['bearing_change']) >= 60) & 
            (abs(result_df['bearing_change']) <= 180) &
            # タック時は通常速度が落ちる
            ((result_df['speed_ratio'] < 0.9) | (result_df['speed_ratio'] > 1.3))
        )
        
        # ジャイブの判定条件（ベクトル化）
        result_df['is_possible_jibe'] = (
            # 両方風下、または風下→ブロードリーチ、またはブロードリーチ→風下
            ((result_df['before_is_downwind'] | (abs(result_df['before_rel_wind']) >= 120)) &
             (result_df['after_is_downwind'] | (abs(result_df['after_rel_wind']) >= 120))) &
            # 方位変化が60〜180度
            (abs(result_df['bearing_change']) >= 60) & 
            (abs(result_df['bearing_change']) <= 180)
        )
        
        # 分類結果をセット
        result_df['maneuver_type'] = 'unknown'
        result_df.loc[result_df['is_possible_tack'], 'maneuver_type'] = 'tack'
        result_df.loc[result_df['is_possible_jibe'], 'maneuver_type'] = 'jibe'
        
        # 風情報を追加
        result_df['wind_direction'] = wind_direction
        
        # 不要な列を削除
        result_df = result_df.drop(columns=[
            'is_possible_tack', 'is_possible_jibe', 
            'before_is_upwind', 'before_is_downwind',
            'after_is_upwind', 'after_is_downwind'
        ])
        
        return result_df
    
    def categorize_maneuvers(self, maneuvers_df: pd.DataFrame, full_df: pd.DataFrame) -> pd.DataFrame:
        """
        元のメソッドをオーバーライドして最適化バージョンを呼び出す
        
        Parameters:
        -----------
        maneuvers_df : pd.DataFrame
            検出されたマニューバーのデータフレーム
        full_df : pd.DataFrame
            完全な航跡データフレーム
            
        Returns:
        --------
        pd.DataFrame
            タイプ分類されたマニューバーのデータフレーム
        """
        return self.categorize_maneuvers_optimized(maneuvers_df, full_df)
    
    @cached('optimal_vmg_angles')
    def get_optimal_vmg_angles(self, wind_speed: float, boat_type: str = None) -> Dict[str, float]:
        """
        指定風速での最適VMG角度を計算（キャッシュ機能付き）
        
        Parameters:
        -----------
        wind_speed : float
            風速（ノット）
        boat_type : str, optional
            艇種（デフォルト: インスタンス初期化時の設定）

        Returns:
        --------
        Dict[str, float]
            風上・風下のVMG最適角度と速度
        """
        return super().get_optimal_vmg_angles(wind_speed, boat_type)
