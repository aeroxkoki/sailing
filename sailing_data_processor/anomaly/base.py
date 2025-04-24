# -*- coding: utf-8 -*-
"""
異常値検出と修正の基底クラス

このモジュールは異常値検出と修正のための基底クラスと共通ユーティリティを提供します。
"""

import numpy as np
import pandas as pd
import math
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from datetime import datetime, timedelta

class BaseAnomalyDetector:
    """
    異常値検出と修正のための基底クラス
    
    異常値検出と修正に関する共通機能を提供し、派生クラスで具体的なアルゴリズムを実装するための
    抽象基底クラスです。
    """
    
    def __init__(self):
        """初期化"""
        # 検出設定のデフォルト値
        self.detection_config = {
            'z_score_threshold': 3.0,       # Z-score閾値
            'mad_threshold': 3.5,           # MAD閾値
            'isolation_forest_threshold': 0.9,  # Isolation Forest異常度閾値
            'lof_threshold': 1.5,           # LOF異常度閾値
            'speed_multiplier': 3.0,        # 速度異常判定の乗数
            'acceleration_threshold': 5.0,  # 加速度異常閾値
            'distance_threshold': 100,      # 距離異常閾値（メートル）
            'time_gap_threshold': 30        # 時間ギャップ閾値（秒）
        }
        
        # 補間設定のデフォルト値
        self.interpolation_config = {
            'default_method': 'linear',     # デフォルト補間方法
            'window_size': 5,               # 移動平均ウィンドウサイズ
            'smooth_factor': 0.5,           # スムージング係数
            'extrapolation_method': 'nearest'  # 外挿方法
        }
    
    def configure(self, detection_params: Optional[Dict] = None, interpolation_params: Optional[Dict] = None) -> 'BaseAnomalyDetector':
        """
        検出と補間のパラメータを設定
        
        Parameters:
        -----------
        detection_params : Dict, optional
            検出設定の更新パラメータ
        interpolation_params : Dict, optional
            補間設定の更新パラメータ
            
        Returns:
        --------
        BaseAnomalyDetector
            設定更新後の自身のインスタンス（メソッドチェーン用）
        """
        if detection_params:
            self.detection_config.update(detection_params)
        
        if interpolation_params:
            self.interpolation_config.update(interpolation_params)
            
        return self
    
    def detect_anomalies(self, df: pd.DataFrame, methods: Optional[List[str]] = None) -> pd.DataFrame:
        """
        異常値を検出
        
        この基底メソッドは派生クラスでオーバーライドする必要があります。
        
        Parameters:
        -----------
        df : pd.DataFrame
            異常値検出対象のデータフレーム
        methods : List[str], optional
            使用する検出方法のリスト
            
        Returns:
        --------
        pd.DataFrame
            異常値フラグが追加されたデータフレーム
        
        Raises:
        -------
        NotImplementedError
            派生クラスで実装されていない場合
        """
        raise NotImplementedError("派生クラスでこのメソッドを実装する必要があります")
    
    def fix_anomalies(self, df: pd.DataFrame, method: str = 'linear') -> pd.DataFrame:
        """
        検出された異常値を修正
        
        この基底メソッドは派生クラスでオーバーライドする必要があります。
        
        Parameters:
        -----------
        df : pd.DataFrame
            異常値修正対象のデータフレーム（is_anomalyカラムが必要）
        method : str
            使用する修正方法
            
        Returns:
        --------
        pd.DataFrame
            異常値が修正されたデータフレーム
            
        Raises:
        -------
        NotImplementedError
            派生クラスで実装されていない場合
        """
        raise NotImplementedError("派生クラスでこのメソッドを実装する必要があります")
    
    def validate_data(self, df: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        データフレームが必要なカラムを持っているかを検証
        
        Parameters:
        -----------
        df : pd.DataFrame
            検証対象のデータフレーム
        required_columns : List[str]
            必要なカラムのリスト
            
        Returns:
        --------
        bool
            すべての必要カラムが存在すればTrue
            
        Raises:
        -------
        ValueError
            必要なカラムが不足している場合
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"必要なカラムが不足しています: {', '.join(missing_columns)}")
        return True
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        2点間のHaversine距離を計算（メートル）
        
        Parameters:
        -----------
        lat1, lon1 : float
            始点の緯度・経度
        lat2, lon2 : float
            終点の緯度・経度
            
        Returns:
        --------
        float
            距離（メートル）
        """
        # 地球の半径（メートル）
        R = 6371000
        
        # 緯度・経度をラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 差分
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # Haversine公式
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _haversine_distance_vectorized(self, lats1: np.ndarray, lons1: np.ndarray, 
                                       lats2: np.ndarray, lons2: np.ndarray) -> np.ndarray:
        """
        複数の位置ペア間のHaversine距離をベクトル化計算（メートル）
        
        Parameters:
        -----------
        lats1, lons1 : np.ndarray
            始点の緯度・経度の配列
        lats2, lons2 : np.ndarray
            終点の緯度・経度の配列
            
        Returns:
        --------
        np.ndarray
            距離の配列（メートル）
        """
        # 地球の半径（メートル）
        R = 6371000.0
        
        # 緯度・経度をラジアンに変換
        lats1_rad = np.radians(lats1)
        lons1_rad = np.radians(lons1)
        lats2_rad = np.radians(lats2)
        lons2_rad = np.radians(lons2)
        
        # 差分
        dlat = lats2_rad - lats1_rad
        dlon = lons2_rad - lons1_rad
        
        # Haversine公式
        a = np.sin(dlat/2)**2 + np.cos(lats1_rad) * np.cos(lats2_rad) * np.sin(dlon/2)**2
        
        # 数値誤差対策
        a = np.clip(a, 0, 1)
        
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distance = R * c
        
        return distance
    
    def _vector_distance(self, p1: np.ndarray, p2: np.ndarray) -> float:
        """
        2点間のユークリッド距離を計算
        
        Parameters:
        -----------
        p1, p2 : np.ndarray
            位置ベクトル
            
        Returns:
        --------
        float
            距離
        """
        return np.sqrt(np.sum((p2 - p1) ** 2))
    
    def _vector_distance_vectorized(self, points1: np.ndarray, points2: np.ndarray) -> np.ndarray:
        """
        複数の位置ペア間のユークリッド距離をベクトル化計算
        
        Parameters:
        -----------
        points1, points2 : np.ndarray
            位置ベクトルの配列
            
        Returns:
        --------
        np.ndarray
            距離の配列
        """
        return np.sqrt(np.sum((points2 - points1) ** 2, axis=1))
    
    def _ensure_datetime(self, timestamps: pd.Series) -> pd.Series:
        """
        タイムスタンプをdatetimeに変換（必要な場合）
        
        Parameters:
        -----------
        timestamps : pd.Series
            タイムスタンプシリーズ
            
        Returns:
        --------
        pd.Series
            datetime型に変換されたタイムスタンプシリーズ
        """
        if pd.api.types.is_datetime64_any_dtype(timestamps):
            return timestamps
        else:
            return pd.to_datetime(timestamps)
    
    def _datetime_to_seconds(self, timestamps: Union[pd.Series, np.ndarray]) -> np.ndarray:
        """
        datetime型のタイムスタンプを秒数（float）に変換
        
        Parameters:
        -----------
        timestamps : Union[pd.Series, np.ndarray]
            タイムスタンプのシリーズまたは配列
            
        Returns:
        --------
        np.ndarray
            秒数に変換された配列
        """
        if isinstance(timestamps, pd.Series):
            if pd.api.types.is_datetime64_any_dtype(timestamps):
                # Pandasのapplyを使ってベクトル化変換
                return timestamps.apply(lambda ts: ts.timestamp()).values
            else:
                # すでに数値の場合はそのまま返す
                return timestamps.values
        else:
            # NumPy配列の場合
            if isinstance(timestamps[0], (datetime, pd.Timestamp)):
                return np.array([ts.timestamp() for ts in timestamps])
            else:
                return timestamps
    
    def process_data(self, df: pd.DataFrame, detection_methods: List[str] = None, 
                     correction_method: str = 'linear') -> pd.DataFrame:
        """
        検出と修正を一度に行うユーティリティメソッド
        
        Parameters:
        -----------
        df : pd.DataFrame
            処理対象のデータフレーム
        detection_methods : List[str], optional
            使用する検出方法のリスト
        correction_method : str, optional
            使用する修正方法
            
        Returns:
        --------
        pd.DataFrame
            処理済みデータフレーム
        """
        # 検出
        result_df = self.detect_anomalies(df, methods=detection_methods)
        
        # 異常値の数を確認
        anomaly_count = result_df['is_anomaly'].sum() if 'is_anomaly' in result_df.columns else 0
        
        # 異常値がない場合は元のデータを返す
        if anomaly_count == 0:
            return result_df
        
        # 修正
        return self.fix_anomalies(result_df, method=correction_method)


def create_anomaly_detector(detector_type: str = 'standard', **config) -> BaseAnomalyDetector:
    """
    異常値検出器のファクトリー関数
    
    Parameters:
    -----------
    detector_type : str
        作成する検出器の種類
        'base': 基底クラス（テスト用）
        'standard': 標準異常値検出器
        'gps': GPS特化型異常値検出器
        'advanced': 高度なアルゴリズムを含むGPS異常値検出器
    **config : dict
        検出器の設定パラメータ
        
    Returns:
    --------
    BaseAnomalyDetector
        指定された種類の異常値検出器のインスタンス
        
    Raises:
    -------
    ValueError
        不明な検出器タイプが指定された場合
    """
    # 基底クラスは直接インスタンス化できないので、サブクラスをインポート
    if detector_type == 'standard':
        from .standard import StandardAnomalyDetector
        return StandardAnomalyDetector().configure(**config)
    elif detector_type == 'gps':
        from .gps import GPSAnomalyDetector
        return GPSAnomalyDetector().configure(**config)
    elif detector_type == 'advanced':
        from .advanced import AdvancedGPSAnomalyDetector
        return AdvancedGPSAnomalyDetector().configure(**config)
    else:
        raise ValueError(f"不明な検出器タイプ: {detector_type}")
