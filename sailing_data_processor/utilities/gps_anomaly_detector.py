# -*- coding: utf-8 -*-
"""
GPSデータの異常値検出と修正機能（互換レイヤー）

このモジュールは後方互換性のためのものです。
新しいアプリケーションは sailing_data_processor.anomaly パッケージを使用してください。
"""

import warnings
from typing import Dict, List, Optional, Union, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

# 新しい実装をインポート
from sailing_data_processor.anomaly.base import create_anomaly_detector

# 警告を表示
warnings.warn(
    "このモジュールは後方互換性のために提供されています。"
    "新しいアプリケーションでは sailing_data_processor.anomaly パッケージを使用してください。",
    DeprecationWarning,
    stacklevel=2
)

class AnomalyDetector:
    """
    GPSデータの異常値検出クラス（互換レイヤー）
    
    このクラスは後方互換性のために提供されています。
    新しいアプリケーションでは sailing_data_processor.anomaly パッケージを使用してください。
    """
    
    def __init__(self):
        """初期化"""
        # 新しい実装のインスタンスを作成（GPS対応版を使用）
        self._detector = create_anomaly_detector('gps')
        
        # 互換性のために元のインターフェースの設定を保持
        self.detection_config = self._detector.detection_config
        self.interpolation_config = self._detector.interpolation_config
    
    def detect_anomalies(self, df: pd.DataFrame, methods: Optional[List[str]] = None) -> pd.DataFrame:
        """
        複数の方法を組み合わせて異常値を検出
        
        Parameters:
        -----------
        df : pd.DataFrame
            検出対象のGPSデータフレーム
            必要なカラム: latitude, longitude, timestamp
        methods : List[str], optional
            使用する検出方法のリスト
            
        Returns:
        --------
        pd.DataFrame
            異常値フラグを追加したデータフレーム
        """
        # デフォルト値の設定（元の実装と同じ）
        if methods is None:
            methods = ['z_score', 'speed']
        
        # 新しい実装に委譲
        return self._detector.detect_anomalies(df, methods=methods)
    
    def fix_anomalies(self, df: pd.DataFrame, method: str = 'linear') -> pd.DataFrame:
        """
        異常値を修正する
        
        Parameters:
        -----------
        df : pd.DataFrame
            修正対象のGPSデータフレーム
            'is_anomaly'カラムが必要
        method : str
            修正方法
            
        Returns:
        --------
        pd.DataFrame
            修正済みデータフレーム
        """
        # 新しい実装に委譲
        return self._detector.fix_anomalies(df, method=method)
    
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
        # 新しい実装に委譲
        return self._detector._haversine_distance(lat1, lon1, lat2, lon2)
    
    def _detect_by_speed_original(self, latitudes: pd.Series, longitudes: pd.Series, timestamps: pd.Series):
        """
        速度ベースの異常値検出（オリジナル実装）
        パフォーマンス比較用に残されている旧実装
        
        Parameters:
        -----------
        latitudes : pd.Series
            緯度データ
        longitudes : pd.Series
            経度データ
        timestamps : pd.Series
            タイムスタンプデータ
            
        Returns:
        --------
        Tuple[List[int], List[float]]
            異常値のインデックスリストとスコアリスト
        """
        # データポイント数が2未満の場合は空のリストを返す
        if len(latitudes) < 2:
            return [], []
        
        # インデックスのリストを保存
        indices = latitudes.index.tolist()
        positions = {idx: i for i, idx in enumerate(indices)}
        
        # タイムスタンプを数値化
        try:
            time_values = []
            for ts in timestamps:
                if isinstance(ts, (datetime, pd.Timestamp)):
                    time_values.append(ts.timestamp())
                else:
                    time_values.append(float(ts))
        except:
            # 数値化できない場合はインデックスを時間とみなす
            time_values = list(range(len(timestamps)))
        
        # 時間順にソート
        sorted_indices = sorted(indices, key=lambda idx: time_values[positions[idx]])
        
        # 距離と時間差を計算
        distances = []
        time_diffs = []
        
        for i in range(1, len(sorted_indices)):
            idx1 = sorted_indices[i-1]
            idx2 = sorted_indices[i]
            
            lat1, lon1 = latitudes[idx1], longitudes[idx1]
            lat2, lon2 = latitudes[idx2], longitudes[idx2]
            
            # Haversine距離を計算
            distance = self._haversine_distance(lat1, lon1, lat2, lon2)
            distances.append(distance)
            
            # 時間差を計算
            time_diff = time_values[positions[idx2]] - time_values[positions[idx1]]
            time_diff = max(0.1, time_diff)  # 0割り防止
            time_diffs.append(time_diff)
        
        # 速度を計算
        speeds = [d / t for d, t in zip(distances, time_diffs)]
        
        # 平均と標準偏差を計算
        if speeds:
            mean_speed = sum(speeds) / len(speeds)
            squared_diffs = [(s - mean_speed) ** 2 for s in speeds]
            variance = sum(squared_diffs) / len(squared_diffs) if squared_diffs else 0
            std_speed = max(0.1, (variance ** 0.5))  # 小さな値の場合は最小値を設定
        else:
            mean_speed = 0
            std_speed = 0.1
        
        # 閾値を計算
        threshold = mean_speed + self.detection_config['speed_multiplier'] * std_speed
        
        # 異常値を検出
        anomaly_indices = []
        anomaly_scores = []
        
        for i in range(len(speeds)):
            if speeds[i] > threshold:
                idx = sorted_indices[i+1]  # 速度は2点間なので、2点目を異常とマーク
                anomaly_indices.append(idx)
                anomaly_scores.append(speeds[i] / threshold)
        
        return anomaly_indices, anomaly_scores
    
    def _detect_by_speed_optimized(self, latitudes: pd.Series, longitudes: pd.Series, timestamps: pd.Series):
        """
        速度ベースの異常値検出（最適化版）
        O(n)の時間計算量を実現するためにベクトル化演算を使用
        
        Parameters:
        -----------
        latitudes : pd.Series
            緯度データ
        longitudes : pd.Series
            経度データ
        timestamps : pd.Series
            タイムスタンプデータ
            
        Returns:
        --------
        Tuple[List[int], List[float]]
            異常値のインデックスリストとスコアリスト
        """
        # データポイント数が2未満の場合は空のリストを返す
        if len(latitudes) < 2:
            return [], []
        
        # オリジナルのインデックスを保存
        indices = latitudes.index
        
        # 時間順にソート（NumPy配列を使用）
        # 1. データとインデックスを一緒に配列化
        data_with_indices = np.column_stack([
            np.arange(len(timestamps)),  # ソート前の位置
            self._datetime_to_seconds(timestamps),
            latitudes.values,
            longitudes.values
        ])
        
        # 2. タイムスタンプでソート
        sorted_indices = np.argsort(data_with_indices[:, 1])
        sorted_data = data_with_indices[sorted_indices]
        
        # 3. ソートされたデータから各配列を抽出
        orig_positions = sorted_data[:, 0].astype(int)
        sorted_timestamps = sorted_data[:, 1]
        sorted_lats = sorted_data[:, 2]
        sorted_lons = sorted_data[:, 3]
        
        # 時間差を一括計算（シフトして引き算）
        time_diffs = np.zeros(len(sorted_timestamps))
        time_diffs[1:] = np.diff(sorted_timestamps)
        time_diffs[0] = 1.0  # 最初の点の時間差
        
        # 0除算を防ぐ（最小値を0.1秒に設定）
        time_diffs = np.maximum(time_diffs, 0.1)
        
        # 位置データをラジアンに変換（距離計算用）
        lats_rad = np.radians(sorted_lats)
        lons_rad = np.radians(sorted_lons)
        
        # 隣接点間の距離を一括計算
        distances = np.zeros(len(lats_rad))
        
        # 地球の半径（メートル）
        R = 6371000.0
        
        # Haversine公式を完全にベクトル化
        # 差分を計算（シフトして減算）
        dlat = np.zeros(len(lats_rad))
        dlon = np.zeros(len(lons_rad))
        
        # 次の点との差分を計算（最後の点以外）
        dlat[1:] = lats_rad[1:] - lats_rad[:-1]
        dlon[1:] = lons_rad[1:] - lons_rad[:-1]
        
        # cosの配列を用意
        cos_lats1 = np.cos(lats_rad[:-1])
        cos_lats2 = np.cos(lats_rad[1:])
        
        # Haversine公式の計算
        a = np.zeros(len(lats_rad))
        a[1:] = np.sin(dlat[1:]/2)**2 + cos_lats1 * cos_lats2 * np.sin(dlon[1:]/2)**2
        
        # 1を超える値をクリップ（数値誤差対策）
        a = np.clip(a, 0, 1)
        
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distances = R * c
        
        # 速度を計算（m/s）
        speeds = distances / time_diffs
        
        # 平均速度と標準偏差を計算（0より大きい速度のみ）
        positive_speeds = speeds[speeds > 0]
        if len(positive_speeds) > 0:
            mean_speed = np.mean(positive_speeds)
            std_speed = np.std(positive_speeds)
            
            # 非常に小さな標準偏差を避ける
            if std_speed < 0.1:
                std_speed = 0.1
        else:
            mean_speed = 0
            std_speed = 0.1
        
        # 異常速度の閾値を計算
        speed_threshold = mean_speed + self.detection_config['speed_multiplier'] * std_speed
        
        # 異常値のインデックスを特定
        anomaly_mask = speeds > speed_threshold
        anomaly_positions = np.where(anomaly_mask)[0]
        
        # 元のインデックスに戻す
        original_indices = []
        for pos in anomaly_positions:
            original_position = sorted_indices[pos]
            if original_position < len(indices):
                original_indices.append(indices[original_position])
        
        # スコアを計算（閾値との比率）
        anomaly_scores = [float(speeds[pos] / speed_threshold) for pos in anomaly_positions if pos < len(speeds)]
        
        return original_indices, anomaly_scores[:len(original_indices)]
    
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
