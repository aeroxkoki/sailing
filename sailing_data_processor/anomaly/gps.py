# -*- coding: utf-8 -*-
"""
GPS特化型の異常値検出と修正の実装

このモジュールはGPSデータに特化した異常値検出と修正機能を提供します。
速度、加速度、時間ギャップなどの検出アルゴリズムを実装しています。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from scipy.spatial import cKDTree
import math
from datetime import datetime, timedelta

from .standard import StandardAnomalyDetector

class GPSAnomalyDetector(StandardAnomalyDetector):
    """
    GPS特化型の異常値検出と修正の実装
    
    GPSデータに特化した異常値検出と修正機能を提供します。
    特に時間経過に伴う移動パターンの分析に焦点を当てています。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__()
        # maneuver_confidence属性を追加
        self.maneuver_confidence = 0.0
        
    def detect(self, df: pd.DataFrame, methods: Optional[List[str]] = None) -> pd.DataFrame:
        """
        後方互換性のためのメソッド - detect_anomaliesの別名
        
        Parameters:
        -----------
        df : pd.DataFrame
            検出対象のデータフレーム
        methods : List[str], optional
            使用する検出方法のリスト
            
        Returns:
        --------
        pd.DataFrame
            異常値フラグを追加したデータフレーム
        """
        return self.detect_anomalies(df, methods)
    
    def detect_anomalies(self, df: pd.DataFrame, methods: Optional[List[str]] = None) -> pd.DataFrame:
        """
        複数の方法を組み合わせて異常値を検出
        
        Parameters:
        -----------
        df : pd.DataFrame
            検出対象のデータフレーム
            必要なカラム: latitude, longitude, timestamp
        methods : List[str], optional
            使用する検出方法のリスト
            デフォルト: ['z_score', 'speed', 'acceleration', 'distance']
            'z_score': Z-scoreベース検出
            'mad': 中央絶対偏差ベース検出
            'speed': 速度ベース検出
            'acceleration': 加速度ベース検出
            'distance': 距離ベース検出
            'time_gap': 時間ギャップベース検出
            'isolation_forest': Isolation Forestベース検出
            'lof': Local Outlier Factorベース検出
            
        Returns:
        --------
        pd.DataFrame
            異常値フラグを追加したデータフレーム
        
        Raises:
        -------
        ValueError
            必要なカラムが不足している場合
        """
        # デフォルトの検出方法を設定
        if methods is None:
            methods = ['z_score', 'speed', 'acceleration', 'distance']
        
        # 必要なカラムを検証
        required_columns = ['latitude', 'longitude']
        if any(method in ['speed', 'acceleration', 'time_gap'] for method in methods):
            required_columns.append('timestamp')
        
        self.validate_data(df, required_columns)
        
        # 入力データをコピー
        result_df = df.copy()
        
        # 異常値フラグを初期化
        result_df['is_anomaly'] = False
        result_df['anomaly_method'] = np.nan  # object型として初期化
        result_df['anomaly_score'] = 0.0
        
        # anomaly_methodカラムをobject型に変換（文字列を格納するため）
        result_df['anomaly_method'] = result_df['anomaly_method'].astype('object')
        
        # 各検出方法を適用
        for method in methods:
            # 既に異常としてマークされていないポイントのみを対象
            non_anomaly_mask = ~result_df['is_anomaly']
            
            # 検出方法に基づいて処理
            if method in ['z_score', 'mad', 'distance']:
                # 位置ベースの検出（StandardAnomalyDetectorの実装を使用）
                anomalies, scores = self._detect_by_position(
                    result_df.loc[non_anomaly_mask, 'latitude'],
                    result_df.loc[non_anomaly_mask, 'longitude'],
                    method=method
                )
            
            elif method == 'speed':
                # 速度ベースの検出
                if 'timestamp' in result_df.columns:
                    anomalies, scores = self._detect_by_speed(
                        result_df.loc[non_anomaly_mask, 'latitude'],
                        result_df.loc[non_anomaly_mask, 'longitude'],
                        result_df.loc[non_anomaly_mask, 'timestamp']
                    )
                else:
                    print("timestampカラムが必要なため、speedによる検出はスキップします")
                    continue
                    
            elif method == 'acceleration':
                # 加速度ベースの検出
                if 'timestamp' in result_df.columns:
                    anomalies, scores = self._detect_by_acceleration(
                        result_df.loc[non_anomaly_mask, 'latitude'],
                        result_df.loc[non_anomaly_mask, 'longitude'],
                        result_df.loc[non_anomaly_mask, 'timestamp']
                    )
                else:
                    print("timestampカラムが必要なため、accelerationによる検出はスキップします")
                    continue
                    
            elif method == 'time_gap':
                # 時間ギャップベースの検出
                if 'timestamp' in result_df.columns:
                    anomalies, scores = self._detect_by_time_gap(
                        result_df.loc[non_anomaly_mask, 'timestamp']
                    )
                else:
                    print("timestampカラムが必要なため、time_gapによる検出はスキップします")
                    continue
                    
            elif method in ['isolation_forest', 'lof']:
                # 機械学習ベースの検出（拡張された特徴量作成）
                try:
                    features = self._create_features_for_ml(
                        result_df.loc[non_anomaly_mask, 'latitude'],
                        result_df.loc[non_anomaly_mask, 'longitude'],
                        result_df.loc[non_anomaly_mask, 'timestamp'] if 'timestamp' in result_df.columns else None
                    )
                    
                    # 検出実行（StandardAnomalyDetectorのメソッドを使用）
                    anomalies, scores = self._detect_by_machine_learning(features, method=method)
                    
                except ImportError:
                    print(f"scikit-learnライブラリがインストールされていないため、{method}検出はスキップします")
                    continue
            
            else:
                # 未知の方法はスキップ
                print(f"未知の検出方法: {method}")
                continue
            
            # 異常値として検出されたポイントをマーク
            if len(anomalies) > 0:
                # 検出された異常値のインデックスを取得
                non_anomaly_indices = result_df.index[non_anomaly_mask]
                anomaly_indices = [non_anomaly_indices[i] for i in anomalies if i < len(non_anomaly_indices)]
                
                # 異常値フラグを設定
                result_df.loc[anomaly_indices, 'is_anomaly'] = True
                result_df.loc[anomaly_indices, 'anomaly_method'] = method
                
                # 異常度スコアを設定（スコアがあれば）
                if scores is not None:
                    for i, idx in enumerate(anomaly_indices):
                        if i < len(scores):
                            result_df.loc[idx, 'anomaly_score'] = scores[i]
        
        return result_df
    
    def _detect_by_speed_original(self, latitudes: pd.Series, longitudes: pd.Series, timestamps: pd.Series) -> Tuple[List[int], List[float]]:
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
        
    def _detect_by_speed_optimized(self, latitudes: pd.Series, longitudes: pd.Series, timestamps: pd.Series) -> Tuple[List[int], List[float]]:
        """
        速度ベースの異常値検出（最適化版）
        
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
                original_indices.append(original_position)
        
        # スコアを計算（閾値との比率）
        anomaly_scores = [float(speeds[pos] / speed_threshold) for pos in anomaly_positions if pos < len(speeds)]
        
        return original_indices, anomaly_scores[:len(original_indices)]
    
    def _detect_by_speed(self, latitudes: pd.Series, longitudes: pd.Series, timestamps: pd.Series) -> Tuple[List[int], List[float]]:
        """
        速度ベースの異常値検出
        
        注: このメソッドは最適化バージョンを呼び出すためのラッパーです
        
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
        return self._detect_by_speed_optimized(latitudes, longitudes, timestamps)
    
    def _detect_by_acceleration(self, latitudes: pd.Series, longitudes: pd.Series, timestamps: pd.Series) -> Tuple[List[int], List[float]]:
        """
        加速度ベースの異常値検出
        
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
        # データポイント数が3未満の場合は空のリストを返す
        if len(latitudes) < 3:
            return [], []
        
        # 速度の計算から始める（速度検出と同様の最適化処理）
        # 時間順にソート
        time_values = self._datetime_to_seconds(timestamps)
        sorted_indices = np.argsort(time_values)
        
        # ソートされたデータを取得
        sorted_times = time_values[sorted_indices]
        sorted_lats = latitudes.values[sorted_indices]
        sorted_lons = longitudes.values[sorted_indices]
        
        # 時間差を計算
        time_diffs = np.zeros(len(sorted_times))
        time_diffs[1:] = np.diff(sorted_times)
        time_diffs[0] = 1.0
        time_diffs = np.maximum(time_diffs, 0.1)  # 0除算を防ぐ
        
        # 距離を計算（ベクトル化したハーバーサイン公式）
        distances = np.zeros(len(sorted_lats))
        
        # 地球の半径（メートル）
        R = 6371000.0
        
        # 位置データをラジアンに変換
        lats_rad = np.radians(sorted_lats)
        lons_rad = np.radians(sorted_lons)
        
        # 差分を計算
        dlat = np.zeros(len(lats_rad))
        dlon = np.zeros(len(lons_rad))
        dlat[1:] = lats_rad[1:] - lats_rad[:-1]
        dlon[1:] = lons_rad[1:] - lons_rad[:-1]
        
        # cosの配列を用意
        cos_lats1 = np.cos(lats_rad[:-1])
        cos_lats2 = np.cos(lats_rad[1:])
        
        # Haversine公式の計算
        a = np.zeros(len(lats_rad))
        a[1:] = np.sin(dlat[1:]/2)**2 + cos_lats1 * cos_lats2 * np.sin(dlon[1:]/2)**2
        a = np.clip(a, 0, 1)  # 数値誤差対策
        
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        distances = R * c
        
        # 速度を計算（m/s）
        speeds = distances / time_diffs
        
        # 加速度の計算（速度の変化率）
        accelerations = np.zeros(len(speeds))
        accelerations[1:] = np.diff(speeds) / time_diffs[1:]
        
        # 加速度の絶対値を取る
        abs_accelerations = np.abs(accelerations)
        
        # 異常な加速度を検出
        threshold = self.detection_config['acceleration_threshold']
        anomaly_mask = abs_accelerations > threshold
        anomaly_positions = np.where(anomaly_mask)[0]
        
        # 元のインデックスに戻す
        indices = latitudes.index
        original_indices = []
        for pos in anomaly_positions:
            if pos < len(sorted_indices):
                original_position = sorted_indices[pos]
                if original_position < len(indices):
                    original_indices.append(original_position)
        
        # スコアを計算（閾値との比率）
        anomaly_scores = []
        for pos in anomaly_positions:
            if pos < len(abs_accelerations):
                anomaly_scores.append(float(abs_accelerations[pos] / threshold))
        
        return original_indices, anomaly_scores[:len(original_indices)]
    
    def _detect_by_time_gap(self, timestamps: pd.Series) -> Tuple[List[int], List[float]]:
        """
        時間ギャップベースの異常値検出
        
        Parameters:
        -----------
        timestamps : pd.Series
            タイムスタンプデータ
            
        Returns:
        --------
        Tuple[List[int], List[float]]
            異常値のインデックスリストとスコアリスト
        """
        # データポイント数が2未満の場合は空のリストを返す
        if len(timestamps) < 2:
            return [], []
        
        # 元のインデックスを保存
        indices = timestamps.index
        
        # タイムスタンプを数値に変換
        time_values = self._datetime_to_seconds(timestamps)
        
        # 時間順にソート
        sorted_indices = np.argsort(time_values)
        sorted_times = time_values[sorted_indices]
        
        # 時間差を計算
        time_diffs = np.zeros(len(sorted_times))
        time_diffs[1:] = np.diff(sorted_times)
        
        # タイムスタンプ間の時間差の統計量を計算
        median_diff = np.median(time_diffs[1:])  # 先頭の0を除く
        threshold = max(self.detection_config['time_gap_threshold'], median_diff * 3)
        
        # 閾値を超える時間差を持つ点を検出
        anomaly_mask = time_diffs > threshold
        anomaly_positions = np.where(anomaly_mask)[0]
        
        # 異常後の点をマーク（時間ギャップの後の点）
        # 本質的には位置[0]は経過時間が計算できないのでスキップ
        original_indices = []
        for pos in anomaly_positions:
            if pos > 0 and pos < len(sorted_indices):
                original_position = sorted_indices[pos]
                if original_position < len(indices):
                    original_indices.append(original_position)
        
        # スコアを計算（閾値との比率）
        anomaly_scores = []
        for pos in anomaly_positions:
            if pos < len(time_diffs):
                anomaly_scores.append(float(time_diffs[pos] / threshold))
        
        return original_indices, anomaly_scores[:len(original_indices)]
    
    def _create_features_for_ml(self, latitudes: pd.Series, longitudes: pd.Series, 
                              timestamps: Optional[pd.Series] = None) -> np.ndarray:
        """
        機械学習用の特徴量を作成
        
        Parameters:
        -----------
        latitudes : pd.Series
            緯度データ
        longitudes : pd.Series
            経度データ
        timestamps : pd.Series, optional
            タイムスタンプデータ
            
        Returns:
        --------
        np.ndarray
            特徴量行列
        """
        # 基本特徴量: 緯度と経度
        features = [latitudes.values, longitudes.values]
        
        # タイムスタンプがある場合は追加特徴量を作成
        if timestamps is not None:
            # タイムスタンプを数値化
            time_values = self._datetime_to_seconds(timestamps)
            
            # タイムスタンプ自体を特徴量に追加
            features.append(time_values)
            
            # 時間順にソート
            sorted_indices = np.argsort(time_values)
            sorted_times = time_values[sorted_indices]
            sorted_lats = latitudes.values[sorted_indices]
            sorted_lons = longitudes.values[sorted_indices]
            
            # 時間差を計算
            time_diffs = np.zeros(len(time_values))
            time_diffs[sorted_indices[1:]] = np.diff(sorted_times)
            
            # 時間差を特徴量に追加
            features.append(time_diffs)
            
            # 速度特徴量の計算
            if len(sorted_times) >= 2:
                # 距離を計算
                distances = np.zeros(len(time_values))
                
                # 隣接点間の距離をハーバーサイン公式で計算
                lats_rad = np.radians(sorted_lats)
                lons_rad = np.radians(sorted_lons)
                
                dlat = np.zeros(len(lats_rad))
                dlon = np.zeros(len(lons_rad))
                dlat[1:] = lats_rad[1:] - lats_rad[:-1]
                dlon[1:] = lons_rad[1:] - lons_rad[:-1]
                
                cos_lats1 = np.cos(lats_rad[:-1])
                cos_lats2 = np.cos(lats_rad[1:])
                
                a = np.zeros(len(lats_rad))
                a[1:] = np.sin(dlat[1:]/2)**2 + cos_lats1 * cos_lats2 * np.sin(dlon[1:]/2)**2
                a = np.clip(a, 0, 1)
                
                c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
                R = 6371000.0
                
                # 並びを元に戻す
                dist_sorted = R * c
                distances[sorted_indices] = dist_sorted
                
                # 時間差が0の場合に備える
                safe_time_diffs = np.maximum(time_diffs, 0.1)
                
                # 速度を計算（m/s）
                speeds = distances / safe_time_diffs
                
                # 速度を特徴量に追加
                features.append(speeds)
                
                # 加速度特徴量の計算（可能であれば）
                if len(sorted_times) >= 3:
                    # ソート済みの速度を計算
                    sorted_speeds = dist_sorted / np.maximum(np.diff(sorted_times), 0.1)
                    sorted_speeds = np.insert(sorted_speeds, 0, 0)  # 先頭に0を追加
                    
                    # 加速度を計算
                    sorted_accels = np.zeros(len(sorted_speeds))
                    sorted_accels[1:] = np.diff(sorted_speeds) / np.maximum(np.diff(sorted_times), 0.1)
                    
                    # 並びを元に戻す
                    accelerations = np.zeros(len(time_values))
                    accelerations[sorted_indices] = sorted_accels
                    
                    # 加速度を特徴量に追加
                    features.append(accelerations)
        
        # 全ての特徴量を結合
        return np.column_stack(features)
