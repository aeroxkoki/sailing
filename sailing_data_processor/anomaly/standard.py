# -*- coding: utf-8 -*-
"""
標準的な異常値検出と修正の実装

このモジュールは基本的な異常値検出・修正機能を提供する標準的なアルゴリズムを実装します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from scipy.spatial import cKDTree
from scipy.interpolate import splev, splrep, CubicSpline
from scipy.signal import savgol_filter
import math
from datetime import datetime, timedelta

from .base import BaseAnomalyDetector

class StandardAnomalyDetector(BaseAnomalyDetector):
    """
    標準的な異常値検出と修正の実装
    
    基本的なZ-score、MAD、距離ベースなどの異常値検出アルゴリズムと
    線形補間、スプライン補間などの修正アルゴリズムを提供します。
    """
    
    def __init__(self):
        """初期化"""
        super().__init__()
    
    def detect_anomalies(self, df: pd.DataFrame, methods: Optional[List[str]] = None) -> pd.DataFrame:
        """
        複数の方法を組み合わせて異常値を検出
        
        Parameters:
        -----------
        df : pd.DataFrame
            検出対象のデータフレーム
            必要なカラム: latitude, longitude, (timestamp)
        methods : List[str], optional
            使用する検出方法のリスト
            デフォルト: ['z_score', 'distance']
            'z_score': Z-scoreベース検出
            'mad': 中央絶対偏差ベース検出
            'distance': 距離ベース検出
            'isolation_forest': Isolation Forestベース検出
            'lof': Local Outlier Factorベース検出
            
        Returns:
        --------
        pd.DataFrame
            異常値フラグを追加したデータフレーム
            新しいカラム:
            - is_anomaly: 異常値フラグ（True/False）
            - anomaly_method: 検出に使用した方法
            - anomaly_score: 異常度スコア
        """
        # デフォルトの検出方法を設定
        if methods is None:
            methods = ['z_score', 'distance']
        
        # 必要なカラムを検証
        required_columns = ['latitude', 'longitude']
        self.validate_data(df, required_columns)
        
        # 入力データをコピー
        result_df = df.copy()
        
        # 異常値フラグを初期化
        result_df['is_anomaly'] = False
        result_df['anomaly_method'] = np.nan
        result_df['anomaly_score'] = 0.0
        
        # 各検出方法を適用
        for method in methods:
            # 既に異常としてマークされていないポイントのみを対象
            non_anomaly_mask = ~result_df['is_anomaly']
            
            # 検出方法に基づいて処理
            if method == 'z_score':
                # Z-scoreベース検出
                anomalies, scores = self._detect_by_position(
                    result_df.loc[non_anomaly_mask, 'latitude'],
                    result_df.loc[non_anomaly_mask, 'longitude'],
                    method='z_score'
                )
            
            elif method == 'mad':
                # MADベース検出
                anomalies, scores = self._detect_by_position(
                    result_df.loc[non_anomaly_mask, 'latitude'],
                    result_df.loc[non_anomaly_mask, 'longitude'],
                    method='mad'
                )
            
            elif method == 'distance':
                # 距離ベース検出
                anomalies, scores = self._detect_by_position(
                    result_df.loc[non_anomaly_mask, 'latitude'],
                    result_df.loc[non_anomaly_mask, 'longitude'],
                    method='distance'
                )
            
            elif method in ['isolation_forest', 'lof']:
                # 機械学習ベースの検出
                try:
                    # 機械学習ライブラリを動的にインポート
                    if method == 'isolation_forest':
                        from sklearn.ensemble import IsolationForest
                    else:  # method == 'lof'
                        from sklearn.neighbors import LocalOutlierFactor
                    
                    # 特徴量の作成
                    features = np.column_stack([
                        result_df.loc[non_anomaly_mask, 'latitude'],
                        result_df.loc[non_anomaly_mask, 'longitude']
                    ])
                    
                    # 検出実行
                    anomalies, scores = self._detect_by_machine_learning(
                        features, method=method
                    )
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
                anomaly_indices = [non_anomaly_indices[i] for i in anomalies]
                
                # 異常値フラグを設定
                result_df.loc[anomaly_indices, 'is_anomaly'] = True
                result_df.loc[anomaly_indices, 'anomaly_method'] = method
                
                # 異常度スコアを設定（スコアがあれば）
                if scores is not None and len(scores) == len(anomalies):
                    for i, idx in enumerate(anomalies):
                        if i < len(scores):  # インデックスエラー対策
                            result_df.loc[anomaly_indices[i], 'anomaly_score'] = scores[i]
        
        return result_df
    
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
            
        Returns:
        --------
        pd.DataFrame
            修正済みデータフレーム
        
        Raises:
        -------
        ValueError
            is_anomalyカラムが存在しない場合
        """
        # 異常値フラグがない場合はエラー
        if 'is_anomaly' not in df.columns:
            raise ValueError("'is_anomaly'カラムが必要です。先にdetect_anomalies()を実行してください。")
        
        # 入力データをコピー
        result_df = df.copy()
        
        # 異常値のインデックス
        anomaly_indices = result_df.index[result_df['is_anomaly']].tolist()
        
        # 異常値がない場合は元のデータフレームを返す
        if len(anomaly_indices) == 0:
            return result_df
        
        # タイムスタンプをdatetimeに変換（必要な場合）
        if 'timestamp' in result_df.columns and not pd.api.types.is_datetime64_any_dtype(result_df['timestamp']):
            result_df['timestamp'] = pd.to_datetime(result_df['timestamp'])
        
        # 修正方法によって処理を分岐
        if method == 'linear':
            result_df = self._fix_by_linear_interpolation(result_df, anomaly_indices)
        elif method == 'spline':
            result_df = self._fix_by_spline_interpolation(result_df, anomaly_indices)
        elif method == 'cubic':
            result_df = self._fix_by_cubic_interpolation(result_df, anomaly_indices)
        elif method == 'nearest':
            result_df = self._fix_by_nearest_interpolation(result_df, anomaly_indices)
        elif method == 'moving_average':
            result_df = self._fix_by_moving_average(result_df, anomaly_indices)
        elif method == 'savgol':
            result_df = self._fix_by_savgol_filter(result_df, anomaly_indices)
        else:
            # 未知の方法の場合はデフォルトの線形補間を使用
            print(f"未知の修正方法: {method} - 線形補間を使用します")
            result_df = self._fix_by_linear_interpolation(result_df, anomaly_indices)
        
        return result_df
    
    def _detect_by_position(self, lat: pd.Series, lon: pd.Series, method: str = 'z_score') -> Tuple[List[int], Optional[List[float]]]:
        """
        位置ベースの異常値検出（Z-score, MAD, 距離）
        
        Parameters:
        -----------
        lat : pd.Series
            緯度データ
        lon : pd.Series
            経度データ
        method : str
            検出方法 ('z_score', 'mad', 'distance')
            
        Returns:
        --------
        Tuple[List[int], Optional[List[float]]]
            異常値のインデックスとスコアのタプル
        """
        if method == 'z_score':
            # Z-scoreベースの検出
            # 緯度・経度の標準化されたZ-scoreを計算
            z_lat = (lat - lat.mean()) / (lat.std() or 1e-10)
            z_lon = (lon - lon.mean()) / (lon.std() or 1e-10)
            
            # 合成Z-score
            z_combined = np.sqrt(z_lat**2 + z_lon**2)
            
            # Z-score閾値を超えるポイントを異常値とする
            threshold = self.detection_config['z_score_threshold']
            anomalies = np.where(z_combined > threshold)[0].tolist()
            scores = z_combined.iloc[anomalies].tolist() if isinstance(z_combined, pd.Series) else z_combined[anomalies].tolist()
            
            return anomalies, scores
            
        elif method == 'mad':
            # MADベースの検出
            # 緯度・経度の中央値を計算
            med_lat = lat.median()
            med_lon = lon.median()
            
            # 中央値からの差を計算
            diff_lat = np.abs(lat - med_lat)
            diff_lon = np.abs(lon - med_lon)
            
            # MADを計算
            mad_lat = diff_lat.median()
            mad_lon = diff_lon.median()
            
            # MADが0に近い場合は小さな値に置き換え
            mad_lat = mad_lat if mad_lat > 1e-10 else 1e-10
            mad_lon = mad_lon if mad_lon > 1e-10 else 1e-10
            
            # MADで標準化
            mad_scores_lat = diff_lat / mad_lat
            mad_scores_lon = diff_lon / mad_lon
            
            # 合成MADスコア
            mad_combined = np.sqrt(mad_scores_lat**2 + mad_scores_lon**2)
            
            # MAD閾値を超えるポイントを異常値とする
            threshold = self.detection_config['mad_threshold']
            anomalies = np.where(mad_combined > threshold)[0].tolist()
            scores = mad_combined.iloc[anomalies].tolist() if isinstance(mad_combined, pd.Series) else mad_combined[anomalies].tolist()
            
            return anomalies, scores
            
        elif method == 'distance':
            # 距離ベースの検出
            # ポイント数が少ない場合は空のリストを返す
            if len(lat) <= 2:
                return [], None
            
            # 座標を配列に変換
            points = np.column_stack([lat, lon])
            
            # KD-Treeを作成
            tree = cKDTree(points)
            
            # 各ポイントの最近接点との距離を計算
            distances, _ = tree.query(points, k=2)  # k=2で自分自身と最近接点を取得
            nearest_distances = distances[:, 1]  # 最近接点との距離（0列目は自分自身）
            
            # 閾値以上離れたポイントを異常値とする
            threshold = self.detection_config['distance_threshold']
            
            # 実際の距離をメートルに変換するための準備
            # 近傍ポイントのインデックスを取得
            _, nearest_indices = tree.query(points, k=2)
            nearest_indices = nearest_indices[:, 1]  # 最近接点のインデックス
            
            # 実際の距離を計算（ハーバーサイン距離）
            actual_distances = []
            for i in range(len(points)):
                actual_distances.append(self._haversine_distance(
                    points[i, 0], points[i, 1],
                    points[nearest_indices[i], 0], points[nearest_indices[i], 1]
                ))
            
            # 閾値を超える距離を持つポイントを特定
            anomalies = []
            scores = []
            
            for i, dist in enumerate(actual_distances):
                if dist > threshold:
                    anomalies.append(i)
                    scores.append(dist / threshold)
            
            return anomalies, scores
        
        else:
            # 未知の方法
            return [], None
    
    def _detect_by_machine_learning(self, features: np.ndarray, method: str = 'isolation_forest') -> Tuple[List[int], Optional[List[float]]]:
        """
        機械学習ベースの異常値検出
        
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
                
                # モデルの初期化
                model = IsolationForest(
                    contamination=0.05,  # データの5%が異常値と仮定
                    random_state=42,
                    n_estimators=100
                )
                
                # 訓練と予測
                model.fit(features)
                
                # 異常スコアを計算
                decision_scores = model.decision_function(features)
                # スコアが小さいほど異常（決定関数の出力が小さいほど異常）
                anomaly_scores = -decision_scores
                
                # 閾値を設定
                threshold = np.percentile(anomaly_scores, 95)  # 上位5%を異常とみなす
                
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
                
                # モデルの初期化
                model = LocalOutlierFactor(
                    n_neighbors=20,
                    contamination=0.05  # データの5%が異常値と仮定
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
    
    def _fix_by_linear_interpolation(self, df: pd.DataFrame, anomaly_indices: List[int]) -> pd.DataFrame:
        """
        線形補間で異常値を修正
        
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
        """
        # 入力データをコピー
        result_df = df.copy()
        
        # 緯度・経度を修正
        if 'latitude' in result_df.columns and 'longitude' in result_df.columns:
            # 異常値でないポイントのインデックス
            normal_indices = result_df.index[~result_df['is_anomaly']].tolist()
            
            # 時間軸でソートされていない場合の処理
            if 'timestamp' in result_df.columns:
                sorted_df = result_df.sort_values('timestamp')
                
                # タイムスタンプを数値化
                timestamps = self._datetime_to_seconds(sorted_df['timestamp'])
                
                # 正常なポイントのタイムスタンプと座標を取得
                normal_mask = sorted_df.index.isin(normal_indices)
                x_normal = timestamps[normal_mask]
                y_lat_normal = sorted_df.loc[normal_mask, 'latitude'].values
                y_lon_normal = sorted_df.loc[normal_mask, 'longitude'].values
                
                # 異常なポイントのタイムスタンプを取得
                anomaly_mask = sorted_df.index.isin(anomaly_indices)
                x_anomaly = timestamps[anomaly_mask]
                
                # 線形補間を適用
                try:
                    interpolated_lat = np.interp(x_anomaly, x_normal, y_lat_normal)
                    interpolated_lon = np.interp(x_anomaly, x_normal, y_lon_normal)
                    
                    # 補間結果を設定
                    for i, idx in enumerate(sorted_df.index[anomaly_mask]):
                        result_df.loc[idx, 'latitude'] = interpolated_lat[i]
                        result_df.loc[idx, 'longitude'] = interpolated_lon[i]
                        result_df.loc[idx, 'is_anomaly_fixed'] = True
                except Exception as e:
                    print(f"線形補間中にエラーが発生しました: {e}")
            else:
                # 時間情報がない場合は位置情報で補間
                all_indices = result_df.index.tolist()
                
                for idx in anomaly_indices:
                    # 前後の正常ポイントを探す
                    idx_pos = all_indices.index(idx)
                    
                    prev_normal_idx = None
                    next_normal_idx = None
                    
                    # 前の正常ポイントを探す
                    for i in range(idx_pos - 1, -1, -1):
                        if all_indices[i] not in anomaly_indices:
                            prev_normal_idx = all_indices[i]
                            break
                    
                    # 次の正常ポイントを探す
                    for i in range(idx_pos + 1, len(all_indices)):
                        if all_indices[i] not in anomaly_indices:
                            next_normal_idx = all_indices[i]
                            break
                    
                    # 補間処理
                    if prev_normal_idx is not None and next_normal_idx is not None:
                        # 両側のポイントから線形補間
                        weight = 0.5  # 中間点と仮定
                        
                        result_df.loc[idx, 'latitude'] = (
                            result_df.loc[prev_normal_idx, 'latitude'] * (1 - weight) +
                            result_df.loc[next_normal_idx, 'latitude'] * weight
                        )
                        
                        result_df.loc[idx, 'longitude'] = (
                            result_df.loc[prev_normal_idx, 'longitude'] * (1 - weight) +
                            result_df.loc[next_normal_idx, 'longitude'] * weight
                        )
                        
                        result_df.loc[idx, 'is_anomaly_fixed'] = True
                        
                    elif prev_normal_idx is not None:
                        # 前のポイントの値を使用
                        result_df.loc[idx, 'latitude'] = result_df.loc[prev_normal_idx, 'latitude']
                        result_df.loc[idx, 'longitude'] = result_df.loc[prev_normal_idx, 'longitude']
                        result_df.loc[idx, 'is_anomaly_fixed'] = True
                        
                    elif next_normal_idx is not None:
                        # 次のポイントの値を使用
                        result_df.loc[idx, 'latitude'] = result_df.loc[next_normal_idx, 'latitude']
                        result_df.loc[idx, 'longitude'] = result_df.loc[next_normal_idx, 'longitude']
                        result_df.loc[idx, 'is_anomaly_fixed'] = True
        
        return result_df
    
    def _fix_by_spline_interpolation(self, df: pd.DataFrame, anomaly_indices: List[int]) -> pd.DataFrame:
        """
        スプライン補間で異常値を修正
        
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
        """
        # 入力データをコピー
        result_df = df.copy()
        
        # 'timestamp'カラムが必要
        if 'timestamp' not in result_df.columns:
            # 時間情報がない場合は線形補間を使用
            return self._fix_by_linear_interpolation(df, anomaly_indices)
        
        # 異常値でないポイントのインデックス
        normal_indices = result_df.index[~result_df['is_anomaly']].tolist()
        
        # 時間軸でソート
        sorted_df = result_df.sort_values('timestamp')
        
        # タイムスタンプを数値に変換
        timestamps = self._datetime_to_seconds(sorted_df['timestamp'])
        
        # 正常なポイントのタイムスタンプと座標を取得
        normal_mask = sorted_df.index.isin(normal_indices)
        x_normal = timestamps[normal_mask]
        y_lat_normal = sorted_df.loc[normal_mask, 'latitude'].values
        y_lon_normal = sorted_df.loc[normal_mask, 'longitude'].values
        
        # 異常なポイントのタイムスタンプを取得
        anomaly_mask = sorted_df.index.isin(anomaly_indices)
        x_anomaly = timestamps[anomaly_mask]
        
        # ポイント数が少ない場合はスプライン補間が使えないので線形補間を使用
        if len(x_normal) < 4:
            return self._fix_by_linear_interpolation(df, anomaly_indices)
        
        try:
            # スプライン補間を計算
            tck_lat = splrep(x_normal, y_lat_normal, s=self.interpolation_config['smooth_factor'])
            tck_lon = splrep(x_normal, y_lon_normal, s=self.interpolation_config['smooth_factor'])
            
            # 補間値を計算
            interpolated_lat = splev(x_anomaly, tck_lat)
            interpolated_lon = splev(x_anomaly, tck_lon)
            
            # 補間結果を設定
            for i, idx in enumerate(sorted_df.index[anomaly_mask]):
                result_df.loc[idx, 'latitude'] = interpolated_lat[i]
                result_df.loc[idx, 'longitude'] = interpolated_lon[i]
                result_df.loc[idx, 'is_anomaly_fixed'] = True
                
        except Exception as e:
            # スプライン補間が失敗した場合は線形補間を使用
            print(f"スプライン補間エラー: {e}")
            return self._fix_by_linear_interpolation(df, anomaly_indices)
        
        return result_df
    
    def _fix_by_cubic_interpolation(self, df: pd.DataFrame, anomaly_indices: List[int]) -> pd.DataFrame:
        """
        3次スプライン補間で異常値を修正
        
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
        """
        # 入力データをコピー
        result_df = df.copy()
        
        # 'timestamp'カラムが必要
        if 'timestamp' not in result_df.columns:
            # 時間情報がない場合は線形補間を使用
            return self._fix_by_linear_interpolation(df, anomaly_indices)
        
        # 異常値でないポイントのインデックス
        normal_indices = result_df.index[~result_df['is_anomaly']].tolist()
        
        # 時間軸でソート
        sorted_df = result_df.sort_values('timestamp')
        
        # タイムスタンプを数値に変換
        timestamps = self._datetime_to_seconds(sorted_df['timestamp'])
        
        # 正常なポイントのタイムスタンプと座標を取得
        normal_mask = sorted_df.index.isin(normal_indices)
        x_normal = timestamps[normal_mask]
        y_lat_normal = sorted_df.loc[normal_mask, 'latitude'].values
        y_lon_normal = sorted_df.loc[normal_mask, 'longitude'].values
        
        # 異常なポイントのタイムスタンプを取得
        anomaly_mask = sorted_df.index.isin(anomaly_indices)
        x_anomaly = timestamps[anomaly_mask]
        
        # ポイント数が少ない場合は3次スプライン補間が使えないので線形補間を使用
        if len(x_normal) < 4:
            return self._fix_by_linear_interpolation(df, anomaly_indices)
        
        try:
            # 3次スプラインを計算
            cs_lat = CubicSpline(x_normal, y_lat_normal)
            cs_lon = CubicSpline(x_normal, y_lon_normal)
            
            # 補間値を計算
            interpolated_lat = cs_lat(x_anomaly)
            interpolated_lon = cs_lon(x_anomaly)
            
            # 補間結果を設定
            for i, idx in enumerate(sorted_df.index[anomaly_mask]):
                result_df.loc[idx, 'latitude'] = interpolated_lat[i]
                result_df.loc[idx, 'longitude'] = interpolated_lon[i]
                result_df.loc[idx, 'is_anomaly_fixed'] = True
                
        except Exception as e:
            # 3次スプライン補間が失敗した場合は線形補間を使用
            print(f"3次スプライン補間エラー: {e}")
            return self._fix_by_linear_interpolation(df, anomaly_indices)
        
        return result_df
    
    def _fix_by_nearest_interpolation(self, df: pd.DataFrame, anomaly_indices: List[int]) -> pd.DataFrame:
        """
        最近傍補間で異常値を修正
        
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
        """
        # 入力データをコピー
        result_df = df.copy()
        
        # 異常値でないポイントのインデックス
        normal_indices = result_df.index[~result_df['is_anomaly']].tolist()
        
        # 正常ポイントがない場合は元のデータフレームを返す
        if len(normal_indices) == 0:
            return result_df
        
        # 正常ポイントの座標を取得
        normal_points = result_df.loc[normal_indices, ['latitude', 'longitude']].values
        
        # 異常ポイントの座標を取得
        anomaly_points = result_df.loc[anomaly_indices, ['latitude', 'longitude']].values
        
        try:
            # K-D Treeを使用して最近傍点を高速に検索
            tree = cKDTree(normal_points)
            
            # 各異常ポイントに対して最近傍の正常ポイントを検索
            _, nearest_indices = tree.query(anomaly_points, k=1)
            
            # 最近傍値を設定
            for i, idx in enumerate(anomaly_indices):
                nearest_idx = normal_indices[nearest_indices[i]]
                
                result_df.loc[idx, 'latitude'] = result_df.loc[nearest_idx, 'latitude']
                result_df.loc[idx, 'longitude'] = result_df.loc[nearest_idx, 'longitude']
                result_df.loc[idx, 'is_anomaly_fixed'] = True
                
        except Exception as e:
            # 最近傍検索が失敗した場合は線形補間を使用
            print(f"最近傍補間エラー: {e}")
            return self._fix_by_linear_interpolation(df, anomaly_indices)
        
        return result_df
    
    def _fix_by_moving_average(self, df: pd.DataFrame, anomaly_indices: List[int]) -> pd.DataFrame:
        """
        移動平均で異常値を修正
        
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
        """
        # 入力データをコピー
        result_df = df.copy()
        
        # すべてのインデックス
        all_indices = result_df.index.tolist()
        
        # ウィンドウサイズ
        window_size = self.interpolation_config['window_size']
        
        for idx in anomaly_indices:
            # インデックスの位置を取得
            if idx not in all_indices:
                continue
                
            idx_pos = all_indices.index(idx)
            
            # ウィンドウ内のインデックスを取得
            window_start = max(0, idx_pos - window_size)
            window_end = min(len(all_indices) - 1, idx_pos + window_size)
            window_indices = all_indices[window_start:window_end+1]
            
            # 異常値でないウィンドウ内のポイントを取得
            normal_window_indices = [i for i in window_indices if i not in anomaly_indices]
            
            # 正常ポイントが2つ以上ある場合は平均を取る
            if len(normal_window_indices) >= 2:
                avg_lat = result_df.loc[normal_window_indices, 'latitude'].mean()
                avg_lon = result_df.loc[normal_window_indices, 'longitude'].mean()
                
                result_df.loc[idx, 'latitude'] = avg_lat
                result_df.loc[idx, 'longitude'] = avg_lon
                result_df.loc[idx, 'is_anomaly_fixed'] = True
            
            elif len(normal_window_indices) == 1:
                # 正常ポイントが1つしかない場合はその値を使用
                normal_idx = normal_window_indices[0]
                result_df.loc[idx, 'latitude'] = result_df.loc[normal_idx, 'latitude']
                result_df.loc[idx, 'longitude'] = result_df.loc[normal_idx, 'longitude']
                result_df.loc[idx, 'is_anomaly_fixed'] = True
        
        return result_df
    
    def _fix_by_savgol_filter(self, df: pd.DataFrame, anomaly_indices: List[int]) -> pd.DataFrame:
        """
        Savitzky-Golayフィルタで異常値を修正
        
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
        """
        # 入力データをコピー
        result_df = df.copy()
        
        # 時間軸でソート（タイムスタンプがある場合）
        if 'timestamp' in result_df.columns:
            result_df = result_df.sort_values('timestamp')
        
        # フィルタリングの準備
        window_length = min(self.interpolation_config['window_size'] * 2 + 1, len(result_df) - 2)
        
        # ウィンドウサイズが奇数であることを確認
        if window_length % 2 == 0:
            window_length -= 1
        
        # ウィンドウサイズが3以上であることを確認
        if window_length < 3:
            # データが少なすぎる場合は線形補間を使用
            return self._fix_by_linear_interpolation(df, anomaly_indices)
        
        # 多項式の次数を設定（ウィンドウサイズより小さい必要がある）
        polyorder = min(3, window_length - 1)
        
        try:
            # フィルタリング適用
            lat_filtered = savgol_filter(result_df['latitude'].values, window_length, polyorder)
            lon_filtered = savgol_filter(result_df['longitude'].values, window_length, polyorder)
            
            # 異常値の位置を特定
            anomaly_mask = result_df.index.isin(anomaly_indices)
            
            # フィルタリング結果を異常値のみに適用
            for i, idx in enumerate(result_df.index):
                if idx in anomaly_indices:
                    result_df.loc[idx, 'latitude'] = lat_filtered[i]
                    result_df.loc[idx, 'longitude'] = lon_filtered[i]
                    result_df.loc[idx, 'is_anomaly_fixed'] = True
            
        except Exception as e:
            # フィルタリングが失敗した場合は線形補間を使用
            print(f"Savitzky-Golayフィルタエラー: {e}")
            return self._fix_by_linear_interpolation(df, anomaly_indices)
        
        return result_df
