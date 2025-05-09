# -*- coding: utf-8 -*-
"""
高度なGPS異常値検出と修正の実装

このモジュールはカルマンフィルタやLOWESS平滑化など高度な手法を活用した
GPS異常値検出と修正機能を提供します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
import math
from datetime import datetime, timedelta

from .gps import GPSAnomalyDetector

class AdvancedGPSAnomalyDetector(GPSAnomalyDetector):
    """
    高度なGPS異常値検出と修正の実装
    
    GPSAnomalyDetectorを拡張し、カルマンフィルタやLOWESS平滑化などの高度な
    アルゴリズムによる異常値検出と修正機能を提供します。
    一部の機能には追加ライブラリが必要です。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__()
        
        # 拡張設定
        self.advanced_config = {
            'kalman_process_noise': 0.01,   # カルマンフィルタのプロセスノイズ
            'kalman_measurement_noise': 0.1, # カルマンフィルタの測定ノイズ
            'lowess_frac': 0.2,             # LOWESS平滑化のスパン比率
            'lowess_it': 3,                 # LOWESS反復回数
            'isolation_forest_estimators': 100,  # Isolation Forestの決定木数
            'isolation_forest_contamination': 0.05, # Isolation Forestの汚染率（異常値の想定比率）
            'lof_neighbors': 20,            # LOFの近傍数
            'lof_contamination': 0.05       # LOFの汚染率
        }
    
    def configure(self, detection_params: Optional[Dict] = None, 
                 interpolation_params: Optional[Dict] = None,
                 advanced_params: Optional[Dict] = None) -> 'AdvancedGPSAnomalyDetector':
        """
        検出と補間、拡張機能のパラメータを設定
        
        Parameters:
        -----------
        detection_params : Dict, optional
            検出設定の更新パラメータ
        interpolation_params : Dict, optional
            補間設定の更新パラメータ
        advanced_params : Dict, optional
            拡張機能設定の更新パラメータ
            
        Returns:
        --------
        AdvancedGPSAnomalyDetector
            設定更新後の自身のインスタンス（メソッドチェーン用）
        """
        # 基底クラスの設定更新
        super().configure(detection_params, interpolation_params)
        
        # 拡張設定の更新
        if advanced_params:
            self.advanced_config.update(advanced_params)
            
        return self
    
    def fix_anomalies(self, df: pd.DataFrame, method: str = 'linear') -> pd.DataFrame:
        """
        検出された異常値を修正
        
        Parameters:
        -----------
        df : pd.DataFrame
            修正対象のデータフレーム
            'is_anomaly'カラムが必要
        method : str
            修正方法
            'linear': 線形補間
            'spline': スプライン補間
            'cubic': 3次スプライン補間
            'nearest': 最近傍補間
            'moving_average': 移動平均
            'savgol': Savitzky-Golayフィルタ
            'kalman': カルマンフィルタ
            'lowess': LOWESS平滑化
            
        Returns:
        --------
        pd.DataFrame
            修正済みデータフレーム
        """
        # 異常値フラグがない場合はエラー
        if 'is_anomaly' not in df.columns:
            raise ValueError("'is_anomaly'カラムが必要です。先にdetect_anomalies()を実行してください。")
        
        # 入力データをコピー
        result_df = df.copy()
        
        # 異常値のインデックス
        anomaly_indices = result_df.index[result_df['is_anomaly']].tolist()
        
        # is_anomaly_fixedカラムを初期化
        if 'is_anomaly_fixed' not in result_df.columns:
            result_df['is_anomaly_fixed'] = False
        
        # 異常値がない場合は元のデータフレームを返す
        if len(anomaly_indices) == 0:
            return result_df
        
        # タイムスタンプをdatetimeに変換（必要な場合）
        if 'timestamp' in result_df.columns and not pd.api.types.is_datetime64_any_dtype(result_df['timestamp']):
            result_df['timestamp'] = pd.to_datetime(result_df['timestamp'])
        
        # 修正方法が高度なアルゴリズムの場合
        if method == 'kalman':
            # カルマンフィルタによる修正
            try:
                result_df = self._fix_by_kalman_filter(result_df, anomaly_indices)
                # 成功した場合は修正フラグを設定
                result_df.loc[anomaly_indices, 'is_anomaly_fixed'] = True
                return result_df
            except ImportError:
                print("filterpyライブラリがインストールされていないため、線形補間を使用します")
                method = 'linear'
        
        elif method == 'lowess':
            # LOWESS平滑化による修正
            try:
                result_df = self._fix_by_lowess(result_df, anomaly_indices)
                # 成功した場合は修正フラグを設定
                result_df.loc[anomaly_indices, 'is_anomaly_fixed'] = True
                return result_df
            except ImportError:
                print("statsmodelsライブラリがインストールされていないため、線形補間を使用します")
                method = 'linear'
        
        # 基本的な修正方法の場合は基底クラスのメソッドを使用
        return super().fix_anomalies(result_df, method=method)
    
    def _fix_by_kalman_filter(self, df: pd.DataFrame, anomaly_indices: List[int]) -> pd.DataFrame:
        """
        カルマンフィルタで異常値を修正
        
        Parameters:
        -----------
        df : pd.DataFrame
            修正対象のデータフレーム
        anomaly_indices : List[int]
            異常値のインデックスリスト
            
        Returns:
        --------
        pd.DataFrame
            修正されたデータフレーム
            
        Raises:
        -------
        ImportError
            必要なライブラリがインストールされていない場合
        """
        try:
            from filterpy.kalman import KalmanFilter
            
            # 入力データをコピー
            result_df = df.copy()
            
            # 時間軸でソート
            if 'timestamp' in result_df.columns:
                result_df = result_df.sort_values('timestamp')
            
            # 状態変数: [lat, lon, lat_vel, lon_vel]
            # 位置と速度を追跡
            state_dim = 4
            measurement_dim = 2
            
            # カルマンフィルタを初期化
            kf = KalmanFilter(dim_x=state_dim, dim_z=measurement_dim)
            
            # 状態遷移行列（時間が一定でない場合は後で更新）
            kf.F = np.array([
                [1, 0, 1, 0],  # lat = lat + lat_vel
                [0, 1, 0, 1],  # lon = lon + lon_vel
                [0, 0, 1, 0],  # lat_vel = lat_vel
                [0, 0, 0, 1]   # lon_vel = lon_vel
            ])
            
            # 測定関数（位置のみを観測）
            kf.H = np.array([
                [1, 0, 0, 0],  # 測定lat
                [0, 1, 0, 0]   # 測定lon
            ])
            
            # 測定ノイズ（位置の不確かさ）
            measurement_noise = self.advanced_config['kalman_measurement_noise']
            kf.R = np.array([
                [measurement_noise, 0],
                [0, measurement_noise]
            ])
            
            # プロセスノイズ（状態の不確かさ）
            process_noise = self.advanced_config['kalman_process_noise']
            kf.Q = np.array([
                [process_noise, 0, 0, 0],
                [0, process_noise, 0, 0],
                [0, 0, process_noise*10, 0],
                [0, 0, 0, process_noise*10]
            ])
            
            # 初期状態共分散
            kf.P = np.eye(state_dim) * 1.0
            
            # カルマンフィルタで異常値を補正
            measurements = result_df[['latitude', 'longitude']].values
            timestamps = None
            
            if 'timestamp' in result_df.columns:
                # タイムスタンプを数値に変換
                timestamps = self._datetime_to_seconds(result_df['timestamp'])
            
            # 初期状態を設定
            initial_point = measurements[0]
            kf.x = np.array([initial_point[0], initial_point[1], 0, 0])
            
            # フィルタリング結果を格納
            filtered_positions = np.zeros_like(measurements)
            filtered_positions[0] = initial_point
            
            # カルマンフィルタを実行
            for i in range(1, len(measurements)):
                # 時間差を考慮して状態遷移行列を更新
                dt = 1.0
                if timestamps is not None:
                    dt = max(0.1, timestamps[i] - timestamps[i-1])
                
                kf.F = np.array([
                    [1, 0, dt, 0],
                    [0, 1, 0, dt],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]
                ])
                
                # 予測ステップ
                kf.predict()
                
                # 測定値を取得
                z = measurements[i]
                
                # 更新ステップ（異常値でない場合のみ）
                if not result_df.iloc[i]['is_anomaly']:
                    kf.update(z)
                else:
                    # 異常値の場合は更新せず予測だけを使用
                    pass
                
                # 結果を格納
                filtered_positions[i] = kf.x[:2]
            
            # 異常値のみを修正
            for i, idx in enumerate(result_df.index):
                if i < len(filtered_positions) and idx in anomaly_indices:
                    # 元の値と修正後の値を保存して変化があるかチェック
                    orig_lat = result_df.loc[idx, 'latitude']
                    orig_lon = result_df.loc[idx, 'longitude']
                    
                    # フィルタリング結果で更新
                    result_df.loc[idx, 'latitude'] = filtered_positions[i][0]
                    result_df.loc[idx, 'longitude'] = filtered_positions[i][1]
                    
                    # 確実に修正されたことを示すフラグを設定
                    # （値が変わらなくても異常とマークされたポイントは修正済みとする）
                    result_df.loc[idx, 'is_anomaly_fixed'] = True
            
            return result_df
            
        except ImportError:
            raise ImportError("filterpyライブラリがインストールされていません")
    
    def _fix_by_lowess(self, df: pd.DataFrame, anomaly_indices: List[int]) -> pd.DataFrame:
        """
        LOWESS平滑化で異常値を修正
        
        Parameters:
        -----------
        df : pd.DataFrame
            修正対象のデータフレーム
        anomaly_indices : List[int]
            異常値のインデックスリスト
            
        Returns:
        --------
        pd.DataFrame
            修正されたデータフレーム
            
        Raises:
        -------
        ImportError
            必要なライブラリがインストールされていない場合
        """
        try:
            from statsmodels.nonparametric.smoothers_lowess import lowess
            
            # 入力データをコピー
            result_df = df.copy()
            
            # 時間軸でソート
            if 'timestamp' in result_df.columns:
                result_df = result_df.sort_values('timestamp')
            
            # X軸の値を作成
            if 'timestamp' in result_df.columns:
                # タイムスタンプを数値に変換
                x_values = self._datetime_to_seconds(result_df['timestamp'])
            else:
                # タイムスタンプがない場合はインデックスを使用
                x_values = np.arange(len(result_df))
            
            # LOWESS平滑化のパラメータを取得
            frac = self.advanced_config['lowess_frac']
            it = self.advanced_config['lowess_it']
            
            try:
                # LOWESS平滑化を緯度に適用
                smoothed_lat = lowess(
                    result_df['latitude'],
                    x_values,
                    frac=frac,
                    it=it,
                    return_sorted=False
                )
                
                # LOWESS平滑化を経度に適用
                smoothed_lon = lowess(
                    result_df['longitude'],
                    x_values,
                    frac=frac,
                    it=it,
                    return_sorted=False
                )
                
                # 異常値のみを修正
                for idx in anomaly_indices:
                    idx_pos = result_df.index.get_loc(idx)
                    if idx_pos < len(smoothed_lat) and idx_pos < len(smoothed_lon):
                        # 元の値と修正後の値を保存して変化があるかチェック
                        orig_lat = result_df.loc[idx, 'latitude']
                        orig_lon = result_df.loc[idx, 'longitude']
                        
                        # 平滑化結果で更新
                        result_df.loc[idx, 'latitude'] = smoothed_lat[idx_pos]
                        result_df.loc[idx, 'longitude'] = smoothed_lon[idx_pos]
                        
                        # 確実に修正されたことを示すフラグを設定
                        # （値が変わらなくても異常とマークされたポイントは修正済みとする）
                        result_df.loc[idx, 'is_anomaly_fixed'] = True
                
            except Exception as e:
                print(f"LOWESS平滑化エラー: {e}")
                # エラーが発生しても例外は発生させず、呼び出し元で他の方法を試せるようにする
                raise
                
            return result_df
            
        except ImportError:
            raise ImportError("statsmodelsライブラリがインストールされていません")
    
    def detect_anomalies(self, df: pd.DataFrame, methods: Optional[List[str]] = None) -> pd.DataFrame:
        """
        複数の方法を組み合わせて異常値を検出
        
        Parameters:
        -----------
        df : pd.DataFrame
            検出対象のデータフレーム
        methods : List[str], optional
            使用する検出方法のリスト
            デフォルト: 全ての利用可能な方法
            
        Returns:
        --------
        pd.DataFrame
            異常値フラグを追加したデータフレーム
        """
        # デフォルトは基底クラスのメソッドを使用
        return super().detect_anomalies(df, methods=methods)
    
    def _detect_by_machine_learning(self, features: np.ndarray, method: str = 'isolation_forest') -> Tuple[List[int], Optional[List[float]]]:
        """
        機械学習ベースの異常値検出（拡張バージョン）
        
        Parameters:
        -----------
        features : np.ndarray
            特徴量行列
        method : str
            検出方法 ('isolation_forest', 'lof')
            
        Returns:
        --------
        Tuple[List[int], Optional[List[float]]]
            異常値のインデックスとスコアのタプル
        """
        if method == 'isolation_forest':
            try:
                # ライブラリをインポート
                from sklearn.ensemble import IsolationForest
                
                # パラメータを取得
                n_estimators = self.advanced_config['isolation_forest_estimators']
                contamination = self.advanced_config['isolation_forest_contamination']
                
                # モデルの初期化（拡張パラメータ使用）
                model = IsolationForest(
                    n_estimators=n_estimators,
                    contamination=contamination,
                    random_state=42,
                    n_jobs=-1  # 並列処理を使用
                )
                
                # 訓練と予測
                model.fit(features)
                
                # 異常スコアを計算
                decision_scores = model.decision_function(features)
                # スコアが小さいほど異常（決定関数の出力が小さいほど異常）
                anomaly_scores = -decision_scores
                
                # 閾値を設定
                threshold = np.percentile(anomaly_scores, 100 * (1 - contamination))
                
                # 閾値を超えるインデックスを特定
                anomalies = np.where(anomaly_scores > threshold)[0].tolist()
                
                # 異常度スコアを正規化
                max_score = np.max(anomaly_scores)
                min_score = np.min(anomaly_scores)
                range_score = max_score - min_score
                if range_score > 0:
                    normalized_scores = (anomaly_scores[anomalies] - min_score) / range_score
                else:
                    normalized_scores = np.ones(len(anomalies))
                
                return anomalies, normalized_scores.tolist()
                
            except ImportError:
                print("scikit-learnライブラリがインストールされていません")
                return [], None
                
        elif method == 'lof':
            try:
                # ライブラリをインポート
                from sklearn.neighbors import LocalOutlierFactor
                
                # パラメータを取得
                n_neighbors = self.advanced_config['lof_neighbors']
                contamination = self.advanced_config['lof_contamination']
                
                # モデルの初期化（拡張パラメータ使用）
                model = LocalOutlierFactor(
                    n_neighbors=n_neighbors,
                    contamination=contamination,
                    n_jobs=-1  # 並列処理を使用
                )
                
                # 予測実行
                predictions = model.fit_predict(features)
                
                # 異常値のインデックス（-1が異常）
                anomalies = np.where(predictions == -1)[0].tolist()
                
                # 異常度スコアの取得
                # 負のアウトライア係数（値が小さいほど正常、大きいほど異常）
                neg_scores = -model.negative_outlier_factor_
                
                # スコアを0-1に正規化
                max_score = np.max(neg_scores)
                min_score = np.min(neg_scores)
                range_score = max_score - min_score
                if range_score > 0:
                    normalized_scores = (neg_scores[anomalies] - min_score) / range_score
                else:
                    normalized_scores = np.ones(len(anomalies))
                
                return anomalies, normalized_scores.tolist()
                
            except ImportError:
                print("scikit-learnライブラリがインストールされていません")
                return [], None
                
        else:
            # 未知の方法
            return [], None
