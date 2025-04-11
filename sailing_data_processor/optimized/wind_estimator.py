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
        ベクトル化演算と効率的なメモリ管理を利用して計算量を削減
        
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
        if df is None or df.empty or len(df) < 10:
            return pd.DataFrame()
        
        # 必要なカラムが存在するか確認
        required_columns = ['timestamp', 'latitude', 'longitude']
        
        # course列がなくても bearing列があれば使用
        course_col = 'course' if 'course' in df.columns else ('bearing' if 'bearing' in df.columns else None)
        speed_col = 'speed' if 'speed' in df.columns else None
        
        if course_col is None or speed_col is None:
            missing_columns = []
            if course_col is None:
                missing_columns.append('course/bearing')
            if speed_col is None:
                missing_columns.append('speed')
            
            warn_msg = f"データに必要なカラムがありません: {missing_columns}"
            warnings.warn(warn_msg)
            return pd.DataFrame()
        
        # 必須カラムと選択されたカラムの組み合わせ
        used_columns = required_columns + [course_col, speed_col]
        
        # 必要なカラムのみをコピー（メモリ効率向上）
        df_subset = df[used_columns].copy()
        
        # 時間順にソート（インプレース操作）
        df_subset.sort_values('timestamp', inplace=True)
        df_subset.reset_index(drop=True, inplace=True)
        
        # NumPy配列に変換して高速化（メモリ効率のため、一度に一つの配列だけを作成）
        timestamps = df_subset['timestamp'].values
        courses = df_subset[course_col].values
        speeds = df_subset[speed_col].values
        
        # 方位の差分を一括計算（ベクトル化）- メモリ効率のために関数を単純化
        # 角度差分を連続して計算（リストコンプリヘンションを避ける）
        bearing_changes = np.zeros_like(courses)
        for i in range(1, len(courses)):
            # 角度差を計算（-180〜180度の範囲）
            diff = ((courses[i] - courses[i-1] + 180) % 360) - 180
            bearing_changes[i] = diff
        
        # 速度の変化率を計算（メモリ効率のために最小限の操作）
        speed_ratios = np.ones_like(speeds)  # 1で初期化（デフォルト値）
        
        # 変化率を直接計算（安全なゼロ除算）
        for i in range(1, len(speeds)):
            prev_speed = speeds[i-1]
            if prev_speed > 0.01:  # 除算が安全かチェック
                speed_ratios[i] = speeds[i] / prev_speed
            else:
                speed_ratios[i] = 1.0  # デフォルト値
        
        # 極端な値を除外（インプレース操作）
        speed_ratios[speed_ratios > 5] = 1
        
        # 小さなウィンドウサイズを使用（パフォーマンス向上）
        window_size = min(self.params.get("maneuver_window_size", 7), 7)
        min_angle_change = self.params.get("min_tack_angle_change", 30)
        
        # 移動ウィンドウでの方位変化の合計を計算（より効率的に）
        bearing_change_sum = np.zeros_like(bearing_changes)
        
        # 効率的な移動窓の実装
        for i in range(len(bearing_changes)):
            # 小さなウィンドウの端を計算
            start_idx = max(0, i - window_size // 2)
            end_idx = min(len(bearing_changes), i + window_size // 2 + 1)
            
            # 合計のみを計算
            window_sum = 0
            for j in range(start_idx, end_idx):
                window_sum += bearing_changes[j]
            
            bearing_change_sum[i] = window_sum
        
        # 方向転換の検出（累積変化がmin_angle_changeを超える場合）
        is_maneuver = bearing_change_sum > min_angle_change
        
        # 連続する方向転換を1つのイベントとしてグループ化
        # メモリ効率のための最適化されたグループ化ロジック
        maneuver_groups = np.zeros_like(is_maneuver, dtype=np.int32)
        group_id = 0
        
        for i in range(1, len(is_maneuver)):
            if is_maneuver[i] != is_maneuver[i-1]:
                group_id += 1
            maneuver_groups[i] = group_id
        
        # 方向転換グループごとに最適な転換点を見つける
        maneuver_points = []
        
        # メモリ効率のための辞書作成を避け、ループを一度だけ実行
        # マニューバーの位置とタイプを検出
        for group_id in range(np.max(maneuver_groups) + 1):
            # 現在のグループの全インデックスを取得
            indices = np.where((maneuver_groups == group_id) & is_maneuver)[0]
            
            if len(indices) == 0:
                continue
            
            # 方位変化が最大の地点（絶対値）
            max_change_idx = indices[np.argmax(np.abs(bearing_changes[indices]))]
            
            # 速度低下の検出（0.9未満のポイントがあるか）
            speed_drop_indices = indices[speed_ratios[indices] < 0.9]
            has_speed_drop = len(speed_drop_indices) > 0
            
            # 中心インデックスの決定
            central_idx = max_change_idx
            
            if has_speed_drop:
                # 速度減少の最大ポイント
                min_ratio_idx = indices[np.argmin(speed_ratios[indices])]
                
                # 方位変化と速度変化の両方がある場合の処理
                idx_diff = abs(max_change_idx - min_ratio_idx)
                
                if idx_diff <= 5:  # 近接イベントの場合
                    t1 = timestamps[max_change_idx]
                    t2 = timestamps[min_ratio_idx]
                    
                    if t1 <= t2:
                        # 通常は方位変化が先
                        central_idx = max_change_idx
                    else:
                        # 速度低下が先の場合、中間点を選択
                        central_idx = (max_change_idx + min_ratio_idx) // 2
            
            # 端すぎる場合はスキップ（データ不足でエラーになるのを防止）
            if central_idx < 5 or central_idx >= len(timestamps) - 5:
                continue
            
            # 緯度・経度の取得（必要な時だけDF参照してメモリ効率向上）
            lat = df_subset.iloc[central_idx]['latitude']
            lon = df_subset.iloc[central_idx]['longitude']
            ts = timestamps[central_idx]
            
            # 前後のウィンドウ（サイズを小さくして効率化）
            before_start = max(0, central_idx - 8)
            before_end = central_idx
            after_start = central_idx + 1
            after_end = min(len(timestamps), central_idx + 9)
            
            # 前後の平均方位と速度
            before_bearing = np.mean(courses[before_start:before_end])
            after_bearing = np.mean(courses[after_start:after_end])
            bearing_change = self._calculate_angle_difference(after_bearing, before_bearing)
            
            speed_before = np.mean(speeds[before_start:before_end])
            speed_after = np.mean(speeds[after_start:after_end])
            speed_ratio = speed_after / max(0.1, speed_before)  # 安全な除算
            
            # マニューバー時間を計算（値が有効な場合のみ）
            if after_start < len(timestamps) and before_end > 0 and before_end < len(timestamps):
                maneuver_duration = (timestamps[after_start] - timestamps[before_end - 1]).total_seconds()
            else:
                # 安全なフォールバック
                maneuver_duration = 0.0
            
            # 結果が有効な場合のみ追加
            if abs(bearing_change) >= min_angle_change:
                # マニューバーエントリーの作成
                maneuver_entry = {
                    'timestamp': ts,
                    'latitude': lat,
                    'longitude': lon,
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
        if not maneuver_points:
            return pd.DataFrame()  # 空の結果
            
        result_df = pd.DataFrame(maneuver_points)
        
        # フィルタリング基準を取得
        min_duration = self.params.get("min_maneuver_duration", 1.0)
        max_duration = self.params.get("max_maneuver_duration", 20.0)
        min_angle = self.params.get("min_tack_angle_change", 30.0)
        
        # 有効な所要時間のフィルタリング（インプレース）
        result_df = result_df[
            (abs(result_df['bearing_change']) >= min_angle) &
            (result_df['maneuver_duration'] >= min_duration) &
            (result_df['maneuver_duration'] <= max_duration)
        ]
        
        # 検出結果を保存
        if not result_df.empty:
            self.detected_maneuvers = result_df.to_dict('records')
        else:
            self.detected_maneuvers = []
        
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
