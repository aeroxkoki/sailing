# -*- coding: utf-8 -*-
"""
sailing_data_processor.analysis.wind_pattern_analyzer モジュール

長期的な風向パターンを分析し、レース戦略に活用できる洞察を提供します。
風向の周期性、トレンド、特定地域での傾向などを分析します。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
from scipy import signal
from scipy.stats import circmean, circstd
from scipy import stats
import warnings
import logging
from collections import defaultdict

class WindPatternAnalyzer:
    """
    風向パターン分析クラス
    
    長期的な風向データを分析し、周期性や傾向を見つけることで
    セーリングのレース戦略に役立つ洞察を提供します。
    """
    
    def __init__(self, min_data_points=30, max_pattern_period=120, **kwargs):
        """
        初期化
        
        Parameters
        ----------
        min_data_points : int, optional
            有効な分析に必要な最小データポイント数, by default 30
        max_pattern_period : int, optional
            検出する最大周期（分）, by default 120
        **kwargs : dict
            追加のパラメータ
        """
        # 分析パラメータ
        self.min_data_points = min_data_points
        self.max_pattern_period = max_pattern_period
        
        # 追加パラメータ
        self.params = {
            "min_period": kwargs.get("min_period", 10),  # 検出する最小周期（分）
            "confidence_threshold": kwargs.get("confidence_threshold", 0.6),  # 検出結果の信頼度閾値
            "geographical_analysis": kwargs.get("geographical_analysis", False),  # 地理的分析の有効化
            "use_clustering": kwargs.get("use_clustering", True),  # クラスタリングを使用するか
            "smooth_window": kwargs.get("smooth_window", 5),  # 平滑化ウィンドウサイズ
        }
        
        # 最新の分析結果
        self.analysis_results = {}
        self.last_analysis_time = None
        
        # ロギング設定
        self.logger = logging.getLogger("WindPatternAnalyzer")
    
    def analyze_patterns(self, wind_data: pd.DataFrame, location_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        風向パターンを分析する
        
        Parameters
        ----------
        wind_data : pd.DataFrame
            風向風速データ
            必要なカラム:
            - timestamp: 時刻
            - wind_direction: 風向（度）
            - wind_speed: 風速（ノット、オプション）
        location_data : pd.DataFrame, optional
            位置データ, by default None
            地理的分析を行う場合に使用
            必要なカラム:
            - timestamp: 時刻
            - latitude, longitude: 位置
            
        Returns
        -------
        Dict[str, Any]
            分析結果を含む辞書:
            - periodicity: 周期性分析結果
            - trends: トレンド分析結果
            - oscillations: 振動パターン分析結果
            - geographical: 地理的パターン分析結果（位置データがある場合）
            - recommendations: 戦略的推奨事項
        """
        # 入力データの検証
        if not self._validate_data(wind_data):
            return self._create_empty_result()
            
        # データの前処理
        processed_data = self._preprocess_data(wind_data)
        
        # 位置データの統合（利用可能な場合）
        if location_data is not None and self.params["geographical_analysis"]:
            processed_data = self._integrate_location_data(processed_data, location_data)
            
        # 周期性の分析
        periodicity_result = self._analyze_periodicity(processed_data)
        
        # トレンドの分析
        trend_result = self._analyze_trend(processed_data)
        
        # 振動パターンの分析
        oscillation_result = self._analyze_oscillations(processed_data)
        
        # 地理的パターンの分析
        geographical_result = {}
        if location_data is not None and self.params["geographical_analysis"]:
            geographical_result = self._analyze_geographical_patterns(processed_data)
            
        # 総合的な分析結果のまとめ
        aggregate_result = self._aggregate_results(
            periodicity_result, trend_result, oscillation_result, geographical_result)
            
        # 戦略的推奨事項の生成
        recommendations = self._generate_recommendations(
            periodicity_result, trend_result, oscillation_result, geographical_result)
            
        # 結果を統合
        result = {
            "periodicity": periodicity_result,
            "trend": trend_result,
            "oscillations": oscillation_result,
            "geographical": geographical_result,
            "aggregate": aggregate_result,
            "recommendations": recommendations,
            "analysis_time": datetime.now(),
            "data_length": len(processed_data),
            "time_range": (processed_data["timestamp"].min(), processed_data["timestamp"].max())
        }
        
        # 結果を保存
        self.analysis_results = result
        self.last_analysis_time = datetime.now()
        
        return result
        
    def get_period_forecast(self, current_time: datetime = None) -> Dict[str, Any]:
        """
        周期分析に基づいた風向予測を取得
        
        Parameters
        ----------
        current_time : datetime, optional
            予測の基準時間, by default None
            Noneの場合は現在時刻を使用
            
        Returns
        -------
        Dict[str, Any]
            周期に基づく予測:
            - predicted_direction: 予測風向
            - confidence: 予測信頼度
            - next_shift_time: 次のシフト予測時刻
            - shift_direction: シフト方向（時計回り/反時計回り）
        """
        # 前回の分析結果がない場合
        if not self.analysis_results or "periodicity" not in self.analysis_results:
            return {
                "status": "no_analysis",
                "predicted_direction": None,
                "confidence": 0.0,
                "next_shift_time": None,
                "shift_direction": None
            }
            
        # 周期性が検出されていない場合
        periodicity = self.analysis_results.get("periodicity", {})
        if not periodicity.get("has_periodicity", False):
            return {
                "status": "no_periodicity",
                "predicted_direction": None,
                "confidence": 0.0,
                "next_shift_time": None,
                "shift_direction": None
            }
            
        # 予測のための基準時間の設定
        if current_time is None:
            current_time = datetime.now()
            
        # 周期分析情報を取得
        period_minutes = periodicity.get("main_period_minutes", 0)
        if period_minutes <= 0:
            return {
                "status": "invalid_period",
                "predicted_direction": None,
                "confidence": 0.0,
                "next_shift_time": None,
                "shift_direction": None
            }
            
        # 周期的なパターンに基づく予測
        time_series = self.analysis_results.get("time_range", (None, None))
        if None in time_series:
            return {
                "status": "invalid_time_range",
                "predicted_direction": None,
                "confidence": 0.0,
                "next_shift_time": None,
                "shift_direction": None
            }
            
        start_time, end_time = time_series
        
        # 現在時刻からの経過時間（分）を計算
        delta_minutes = (current_time - start_time).total_seconds() / 60
        
        # 周期内の位置（0-1）を計算
        cycle_position = (delta_minutes % period_minutes) / period_minutes
        
        # 周期パターンから現在の予測風向を取得
        pattern = periodicity.get("direction_pattern", [])
        if not pattern:
            return {
                "status": "no_pattern",
                "predicted_direction": None,
                "confidence": 0.0,
                "next_shift_time": None,
                "shift_direction": None
            }
            
        # パターン内の対応する位置の値を取得
        pattern_idx = int(cycle_position * len(pattern))
        if pattern_idx >= len(pattern):
            pattern_idx = len(pattern) - 1
            
        predicted_direction = pattern[pattern_idx]
        
        # 信頼度は経過時間と周期的強度に応じて低下
        time_factor = min(1.0, 2 * period_minutes / max(1, (current_time - end_time).total_seconds() / 60))
        pattern_strength = periodicity.get("pattern_strength", 0.0)
        confidence = time_factor * pattern_strength
        
        # 次のシフトポイントを予測
        shift_points = periodicity.get("shift_points", [])
        next_shift_time = None
        shift_direction = None
        
        if shift_points:
            # 現在の周期位置から最も近い将来のシフトポイントを見つける
            next_shift_pos = None
            min_distance = float('inf')
            
            for pos, direction in shift_points:
                # シフトポイントまでの距離（周期内の位置で計算）
                if pos > cycle_position:
                    dist = pos - cycle_position
                else:
                    dist = 1 + pos - cycle_position
                    
                if dist < min_distance:
                    min_distance = dist
                    next_shift_pos = pos
                    shift_direction = direction
                    
            if next_shift_pos is not None:
                # 次のシフトまでの時間（分）
                time_to_shift = min_distance * period_minutes
                next_shift_time = current_time + timedelta(minutes=time_to_shift)
        
        return {
            "status": "success",
            "predicted_direction": predicted_direction,
            "confidence": confidence,
            "next_shift_time": next_shift_time,
            "shift_direction": shift_direction,
            "cycle_position": cycle_position,
            "period_minutes": period_minutes
        }
    
    def get_location_based_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        位置に基づいた風向予測を取得
        
        Parameters
        ----------
        latitude : float
            緯度
        longitude : float
            経度
            
        Returns
        -------
        Dict[str, Any]
            位置に基づく予測:
            - predicted_direction: 予測風向
            - confidence: 予測信頼度
            - local_pattern: 局所的なパターン情報
        """
        # 前回の分析結果がない場合
        if not self.analysis_results or "geographical" not in self.analysis_results:
            return {
                "status": "no_analysis",
                "predicted_direction": None,
                "confidence": 0.0,
                "local_pattern": None
            }
            
        # 地理的分析が有効でない場合
        geographical = self.analysis_results.get("geographical", {})
        if not geographical:
            return {
                "status": "no_geographical_analysis",
                "predicted_direction": None,
                "confidence": 0.0,
                "local_pattern": None
            }
            
        # 地域クラスタが定義されていない場合
        region_clusters = geographical.get("region_clusters", [])
        if not region_clusters:
            return {
                "status": "no_region_clusters",
                "predicted_direction": None,
                "confidence": 0.0,
                "local_pattern": None
            }
            
        # 最も近いクラスタを見つける
        closest_cluster = None
        min_distance = float('inf')
        
        for cluster in region_clusters:
            cluster_lat = cluster.get("center_latitude", 0)
            cluster_lon = cluster.get("center_longitude", 0)
            
            # クラスタ中心との距離を計算
            distance = self._calculate_distance(latitude, longitude, cluster_lat, cluster_lon)
            
            if distance < min_distance:
                min_distance = distance
                closest_cluster = cluster
                
        # 近いクラスタが見つからない場合
        if closest_cluster is None:
            return {
                "status": "no_nearby_cluster",
                "predicted_direction": None,
                "confidence": 0.0,
                "local_pattern": None
            }
            
        # 距離による信頼度の計算（500mを超えると信頼度が低下）
        distance_factor = max(0.0, min(1.0, 1.0 - (min_distance - 100) / 400)) if min_distance > 100 else 1.0
        
        # クラスタの風向と信頼度
        predicted_direction = closest_cluster.get("mean_direction", 0)
        cluster_confidence = closest_cluster.get("confidence", 0.0)
        
        # 総合的な信頼度
        confidence = distance_factor * cluster_confidence
        
        return {
            "status": "success",
            "predicted_direction": predicted_direction,
            "confidence": confidence,
            "local_pattern": closest_cluster.get("pattern", "stable"),
            "distance": min_distance,
            "cluster_info": closest_cluster
        }
    
    def get_trend_forecast(self, current_time: datetime = None, horizon_minutes: int = 30) -> Dict[str, Any]:
        """
        トレンド分析に基づいた風向予測を取得
        
        Parameters
        ----------
        current_time : datetime, optional
            予測の基準時間, by default None
            Noneの場合は現在時刻を使用
        horizon_minutes : int, optional
            予測時間（分）, by default 30
            
        Returns
        -------
        Dict[str, Any]
            トレンドに基づく予測:
            - predicted_direction: 予測風向
            - direction_trend: 方向の変化率（度/分）
            - confidence: 予測信頼度
        """
        # 前回の分析結果がない場合
        if not self.analysis_results or "trend" not in self.analysis_results:
            return {
                "status": "no_analysis",
                "predicted_direction": None,
                "direction_trend": 0.0,
                "confidence": 0.0
            }
            
        # トレンド情報を取得
        trend = self.analysis_results.get("trend", {})
        
        # トレンドがない場合
        if not trend.get("has_trend", False):
            return {
                "status": "no_trend",
                "predicted_direction": None,
                "direction_trend": 0.0,
                "confidence": 0.0
            }
            
        # 予測のための基準時間の設定
        if current_time is None:
            current_time = datetime.now()
            
        # トレンド係数を取得
        trend_rate = trend.get("direction_trend_rate", 0.0)  # 度/分
        last_direction = trend.get("last_direction", 0.0)
        last_time = trend.get("last_time")
        
        if last_time is None:
            return {
                "status": "invalid_last_time",
                "predicted_direction": None,
                "direction_trend": trend_rate,
                "confidence": 0.0
            }
            
        # 最新データからの経過時間（分）
        time_diff_minutes = (current_time - last_time).total_seconds() / 60
        
        # トレンドに基づく予測
        predicted_direction = (last_direction + trend_rate * (time_diff_minutes + horizon_minutes)) % 360
        
        # 信頼度は経過時間とトレンド強度に応じて低下
        # 時間が経つほど、また予測が長期になるほど信頼度は低下
        time_factor = max(0.0, min(1.0, 1.0 - (time_diff_minutes / 120)))  # 2時間経過で信頼度0
        horizon_factor = max(0.0, min(1.0, 1.0 - (horizon_minutes / 60)))  # 1時間先の予測で信頼度半減
        
        trend_strength = trend.get("trend_strength", 0.0)
        confidence = time_factor * horizon_factor * trend_strength
        
        return {
            "status": "success",
            "predicted_direction": predicted_direction,
            "direction_trend": trend_rate,
            "confidence": confidence,
            "time_diff_minutes": time_diff_minutes,
            "horizon_minutes": horizon_minutes
        }
    
    def get_strategic_insights(self) -> Dict[str, Any]:
        """
        戦略的洞察を取得
        
        Returns
        -------
        Dict[str, Any]
            戦略的洞察:
            - pattern_type: パターンタイプ
            - stability: 風の安定性（0-1）
            - predictability: 予測可能性（0-1）
            - key_insights: 主要な洞察のリスト
            - recommendations: 戦略的推奨事項
        """
        # 前回の分析結果がない場合
        if not self.analysis_results:
            return {
                "status": "no_analysis",
                "pattern_type": "unknown",
                "stability": 0.0,
                "predictability": 0.0,
                "key_insights": [],
                "recommendations": []
            }
            
        # 集約結果から情報を取得
        aggregate = self.analysis_results.get("aggregate", {})
        recommendations = self.analysis_results.get("recommendations", {})
        
        return {
            "status": "success",
            "pattern_type": aggregate.get("pattern_type", "unknown"),
            "stability": aggregate.get("stability", 0.0),
            "predictability": aggregate.get("predictability", 0.0),
            "key_insights": aggregate.get("key_insights", []),
            "recommendations": recommendations.get("strategy_recommendations", [])
        }
    
    def _validate_data(self, wind_data: pd.DataFrame) -> bool:
        """
        入力データが有効かどうかを検証
        
        Parameters
        ----------
        wind_data : pd.DataFrame
            風向風速データ
            
        Returns
        -------
        bool
            データが有効な場合はTrue
        """
        # 必要なカラムをチェック
        required_columns = ['timestamp', 'wind_direction']
        if not all(col in wind_data.columns for col in required_columns):
            self.logger.warning("必要なカラムがありません: %s", 
                              [col for col in required_columns if col not in wind_data.columns])
            return False
            
        # データサイズのチェック
        if len(wind_data) < self.min_data_points:
            self.logger.warning("データポイントが不足しています: %d < %d", 
                              len(wind_data), self.min_data_points)
            return False
            
        # タイムスタンプの妥当性チェック
        if not pd.api.types.is_datetime64_any_dtype(wind_data['timestamp']):
            self.logger.warning("timestampカラムが日時型ではありません")
            return False
            
        # 風向の妥当性チェック
        invalid_dirs = wind_data['wind_direction'].isnull().sum()
        if invalid_dirs > len(wind_data) * 0.1:  # 10%以上の欠損値がある場合
            self.logger.warning("風向に多数の欠損値があります: %.1f%%", 
                              (invalid_dirs / len(wind_data)) * 100)
            return False
            
        return True
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """
        空の分析結果を作成
        
        Returns
        -------
        Dict[str, Any]
            空の分析結果
        """
        return {
            "periodicity": {
                "has_periodicity": False,
                "main_period_minutes": 0,
                "pattern_strength": 0.0
            },
            "trend": {
                "has_trend": False,
                "direction_trend_rate": 0.0,
                "trend_strength": 0.0
            },
            "oscillations": {
                "has_oscillations": False,
                "oscillation_amplitude": 0.0,
                "oscillation_frequency": 0.0
            },
            "geographical": {},
            "aggregate": {
                "pattern_type": "unknown",
                "stability": 0.0,
                "predictability": 0.0,
                "key_insights": []
            },
            "recommendations": {
                "strategy_recommendations": []
            },
            "analysis_time": datetime.now(),
            "data_length": 0,
            "time_range": (None, None)
        }
    
    def _preprocess_data(self, wind_data: pd.DataFrame) -> pd.DataFrame:
        """
        データの前処理
        
        Parameters
        ----------
        wind_data : pd.DataFrame
            風向風速データ
            
        Returns
        -------
        pd.DataFrame
            前処理済みデータ
        """
        # コピーを作成
        df = wind_data.copy()
        
        # 時間順にソート
        df = df.sort_values('timestamp')
        
        # 欠損値の補間
        if df['wind_direction'].isnull().any():
            # 風向は角度なので単純な線形補間は使用できない
            # sin/cosに分解して補間
            sin_vals = np.sin(np.radians(df['wind_direction']))
            cos_vals = np.cos(np.radians(df['wind_direction']))
            
            # 欠損値の補間
            sin_interp = sin_vals.interpolate(method='linear')
            cos_interp = cos_vals.interpolate(method='linear')
            
            # 角度に戻す
            df['wind_direction'] = np.degrees(np.arctan2(sin_interp, cos_interp)) % 360
        
        # 風速の欠損値補間（存在する場合）
        if 'wind_speed' in df.columns and df['wind_speed'].isnull().any():
            df['wind_speed'] = df['wind_speed'].interpolate(method='linear')
        
        # 時間間隔の正規化（必要な場合）
        time_diffs = df['timestamp'].diff().dt.total_seconds()
        if time_diffs.std() > time_diffs.mean() * 0.5:  # 不規則なサンプリング
            # 一定間隔の時間軸を作成
            start_time = df['timestamp'].min()
            end_time = df['timestamp'].max()
            duration = (end_time - start_time).total_seconds()
            
            # 平均サンプリング間隔で新しい時間軸を作成
            avg_sampling = duration / (len(df) - 1)
            new_timestamps = [start_time + timedelta(seconds=i * avg_sampling) 
                             for i in range(len(df))]
            
            # 元のデータを新しい時間軸に再サンプリング
            df['timestamp'] = new_timestamps
        
        # 風向の平滑化
        window_size = self.params["smooth_window"]
        if window_size > 1 and len(df) > window_size:
            # sin/cosに分解して移動平均
            sin_vals = np.sin(np.radians(df['wind_direction']))
            cos_vals = np.cos(np.radians(df['wind_direction']))
            
            sin_smooth = sin_vals.rolling(window=window_size, center=True).mean()
            cos_smooth = cos_vals.rolling(window=window_size, center=True).mean()
            
            # 両端の欠損値を補完
            sin_smooth.iloc[:window_size//2] = sin_vals.iloc[:window_size//2]
            sin_smooth.iloc[-window_size//2:] = sin_vals.iloc[-window_size//2:]
            cos_smooth.iloc[:window_size//2] = cos_vals.iloc[:window_size//2]
            cos_smooth.iloc[-window_size//2:] = cos_vals.iloc[-window_size//2:]
            
            # 角度に戻す
            df['wind_direction_smooth'] = np.degrees(np.arctan2(sin_smooth, cos_smooth)) % 360
        else:
            df['wind_direction_smooth'] = df['wind_direction']
        
        # 分析用の追加特徴量を計算
        self._add_analysis_features(df)
        
        return df
    
    def _add_analysis_features(self, df: pd.DataFrame) -> None:
        """
        分析用の特徴量を追加
        
        Parameters
        ----------
        df : pd.DataFrame
            データフレーム（変更される）
        """
        # 時間特徴量
        df['seconds_from_start'] = (df['timestamp'] - df['timestamp'].min()).dt.total_seconds()
        df['minutes_from_start'] = df['seconds_from_start'] / 60
        
        # 時刻特徴量
        df['hour_of_day'] = df['timestamp'].dt.hour + df['timestamp'].dt.minute / 60
        df['day_of_year'] = df['timestamp'].dt.dayofyear
        
        # 風向の変化率
        df['direction_prev'] = df['wind_direction_smooth'].shift(1)
        df['direction_change'] = df.apply(
            lambda row: self._calculate_angle_difference(
                row['wind_direction_smooth'], row['direction_prev']),
            axis=1
        )
        
        # 変化率を度/分に正規化
        time_diff_minutes = df['minutes_from_start'].diff()
        df['direction_change_rate'] = df['direction_change'] / time_diff_minutes.replace(0, np.nan)
        df['direction_change_rate'] = df['direction_change_rate'].fillna(0)
        
        # 移動標準偏差（風の不安定さの指標）
        if len(df) >= 10:
            # 角度データなので円形統計を使用
            df['direction_rolling_std'] = df['wind_direction_smooth'].rolling(
                window=10).apply(lambda x: circstd(np.radians(x)) * 180 / np.pi)
            
            # 端の欠損値を埋める
            df['direction_rolling_std'] = df['direction_rolling_std'].fillna(method='bfill').fillna(method='ffill')
        else:
            df['direction_rolling_std'] = circstd(np.radians(df['wind_direction_smooth'])) * 180 / np.pi
    
    def _integrate_location_data(self, wind_df: pd.DataFrame, location_df: pd.DataFrame) -> pd.DataFrame:
        """
        風データと位置データを統合
        
        Parameters
        ----------
        wind_df : pd.DataFrame
            風データ
        location_df : pd.DataFrame
            位置データ
            
        Returns
        -------
        pd.DataFrame
            統合されたデータ
        """
        # 必要なカラムがあることを確認
        if not all(col in location_df.columns for col in ['timestamp', 'latitude', 'longitude']):
            self.logger.warning("位置データに必要なカラムがありません")
            return wind_df
            
        # 位置データを時間でソート
        location_df = location_df.sort_values('timestamp')
        
        # 風データの各時点に最も近い位置データを結合
        result_df = wind_df.copy()
        
        # 位置カラムを追加
        if 'latitude' not in result_df.columns:
            result_df['latitude'] = None
        if 'longitude' not in result_df.columns:
            result_df['longitude'] = None
            
        # 各風データポイントに対応する位置を検索
        for idx, row in result_df.iterrows():
            wind_time = row['timestamp']
            
            # 時間差の計算
            time_diffs = abs((location_df['timestamp'] - wind_time).dt.total_seconds())
            
            # 最も近い位置データポイント
            min_diff_idx = time_diffs.idxmin()
            
            # 3分以内なら位置データを使用
            if time_diffs.loc[min_diff_idx] <= 180:
                result_df.at[idx, 'latitude'] = location_df.loc[min_diff_idx, 'latitude']
                result_df.at[idx, 'longitude'] = location_df.loc[min_diff_idx, 'longitude']
                
        return result_df
    
    def _analyze_periodicity(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        風向の周期性を分析
        
        Parameters
        ----------
        df : pd.DataFrame
            前処理済みデータ
            
        Returns
        -------
        Dict[str, Any]
            周期性分析結果
        """
        # データが少なすぎる場合
        if len(df) < self.min_data_points:
            return {
                "has_periodicity": False,
                "main_period_minutes": 0,
                "pattern_strength": 0.0
            }
            
        # 時間軸とデータの準備
        times = df['minutes_from_start'].values
        
        # 風向をsin/cosに分解
        directions = df['wind_direction_smooth'].values
        sin_vals = np.sin(np.radians(directions))
        cos_vals = np.cos(np.radians(directions))
        
        # FFTの適用（sin成分）
        if len(sin_vals) >= 10:
            # FFTパラメータ
            n = len(sin_vals)
            sampling_freq = n / (times[-1] - times[0])  # サンプリング周波数（分）
            
            # FFTの実行
            sin_fft = np.fft.rfft(sin_vals)
            cos_fft = np.fft.rfft(cos_vals)
            
            # パワースペクトル
            sin_power = np.abs(sin_fft) ** 2
            cos_power = np.abs(cos_fft) ** 2
            
            # 合計パワー
            total_power = sin_power + cos_power
            
            # 周波数軸
            freqs = np.fft.rfftfreq(n, d=1/sampling_freq)
            
            # 最小・最大周期の設定
            min_period = self.params["min_period"]  # 分
            max_period = self.max_pattern_period  # 分
            
            # 対応する周波数インデックス
            min_freq_idx = np.searchsorted(freqs, 1/max_period)
            max_freq_idx = np.searchsorted(freqs, 1/min_period, side='right')
            
            # 検索範囲の制限
            min_freq_idx = max(1, min_freq_idx)  # DCコンポーネント（0Hz）は除外
            max_freq_idx = min(len(freqs) - 1, max_freq_idx)
            
            # 有効な周波数範囲がない場合
            if min_freq_idx >= max_freq_idx:
                return {
                    "has_periodicity": False,
                    "main_period_minutes": 0,
                    "pattern_strength": 0.0
                }
                
            # 周波数範囲内のピークを検出
            search_range = slice(min_freq_idx, max_freq_idx)
            peaks, _ = signal.find_peaks(total_power[search_range], height=0.1*np.max(total_power[search_range]))
            
            # ピークが見つからない場合
            if len(peaks) == 0:
                return {
                    "has_periodicity": False,
                    "main_period_minutes": 0,
                    "pattern_strength": 0.0
                }
                
            # 最も強いピークを選択
            strongest_peak_idx = peaks[np.argmax(total_power[search_range][peaks])]
            strongest_peak_idx += min_freq_idx  # 元の配列インデックスに変換
            
            # 周期（分）に変換
            peak_freq = freqs[strongest_peak_idx]
            peak_period = 1 / peak_freq if peak_freq > 0 else 0
            
            # パターンの強さ（主要ピークのパワーの相対的な強さ）
            total_signal_power = np.sum(total_power[1:])  # DCコンポーネントを除外
            peak_power = total_power[strongest_peak_idx]
            pattern_strength = peak_power / total_signal_power if total_signal_power > 0 else 0
            
            # 強度が閾値を超える場合のみ周期性ありと判定
            has_periodicity = pattern_strength > 0.1
            
            # 追加のピーク（第2、第3の周期性）
            additional_peaks = []
            for p in peaks:
                p_idx = p + min_freq_idx
                if p_idx != strongest_peak_idx:  # 最強ピーク以外
                    p_freq = freqs[p_idx]
                    p_period = 1 / p_freq if p_freq > 0 else 0
                    p_power = total_power[p_idx]
                    p_strength = p_power / total_signal_power if total_signal_power > 0 else 0
                    
                    if p_strength > 0.05:  # 一定の強度を持つもののみ
                        additional_peaks.append({
                            "period_minutes": p_period,
                            "strength": p_strength
                        })
                        
            # 追加のピークを強度でソート
            additional_peaks.sort(key=lambda x: x["strength"], reverse=True)
            
            # 周期パターンの抽出
            direction_pattern = []
            shift_points = []
            
            if has_periodicity and peak_period > 0:
                # 1周期分のデータポイント数
                cycle_points = int(peak_period * sampling_freq)
                
                if cycle_points > 0:
                    # 周期の平均パターンを計算
                    n_cycles = len(directions) // cycle_points
                    
                    if n_cycles > 0:
                        cycles = []
                        for i in range(n_cycles):
                            start_idx = i * cycle_points
                            end_idx = start_idx + cycle_points
                            if end_idx <= len(directions):
                                cycle = directions[start_idx:end_idx]
                                cycles.append(cycle)
                        
                        # 複数周期のデータがあれば平均パターンを計算
                        if cycles:
                            # 周期長を統一（最短のものに合わせる）
                            min_len = min(len(c) for c in cycles)
                            cycles = [c[:min_len] for c in cycles]
                            
                            # sin/cosに分解して平均（円形データ）
                            sin_avg = np.zeros(min_len)
                            cos_avg = np.zeros(min_len)
                            
                            for cycle in cycles:
                                sin_avg += np.sin(np.radians(cycle))
                                cos_avg += np.cos(np.radians(cycle))
                            
                            sin_avg /= len(cycles)
                            cos_avg /= len(cycles)
                            
                            # 平均パターン
                            avg_pattern = np.degrees(np.arctan2(sin_avg, cos_avg)) % 360
                            direction_pattern = avg_pattern.tolist()
                            
                            # シフトポイントの検出
                            shifts = []
                            for i in range(1, len(avg_pattern)):
                                diff = self._calculate_angle_difference(avg_pattern[i], avg_pattern[i-1])
                                if abs(diff) >= 5.0:  # 5度以上の変化をシフトとみなす
                                    shift_pos = i / len(avg_pattern)
                                    shift_dir = "clockwise" if diff > 0 else "counter_clockwise"
                                    shifts.append((shift_pos, shift_dir))
                            
                            shift_points = shifts
            
            # 分析結果
            return {
                "has_periodicity": has_periodicity,
                "main_period_minutes": peak_period,
                "pattern_strength": pattern_strength,
                "additional_peaks": additional_peaks[:2],  # 上位2つまで
                "direction_pattern": direction_pattern,
                "shift_points": shift_points
            }
        
        # データ不足の場合
        return {
            "has_periodicity": False,
            "main_period_minutes": 0,
            "pattern_strength": 0.0
        }
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        風向のトレンドを分析
        
        Parameters
        ----------
        df : pd.DataFrame
            前処理済みデータ
            
        Returns
        -------
        Dict[str, Any]
            トレンド分析結果
        """
        # データが少なすぎる場合
        if len(df) < self.min_data_points:
            return {
                "has_trend": False,
                "direction_trend_rate": 0.0,
                "trend_strength": 0.0
            }
            
        # 線形回帰用のデータ準備
        times = df['minutes_from_start'].values
        
        # 風向をsin/cosに分解して線形回帰
        directions = df['wind_direction_smooth'].values
        sin_vals = np.sin(np.radians(directions))
        cos_vals = np.cos(np.radians(directions))
        
        # sin成分の線形回帰
        try:
            sin_slope, sin_intercept, sin_r, sin_p, sin_stderr = stats.linregress(times, sin_vals)
            
            # cos成分の線形回帰
            cos_slope, cos_intercept, cos_r, cos_p, cos_stderr = stats.linregress(times, cos_vals)
            
            # 統計的有意性
            significant = (sin_p < 0.05) or (cos_p < 0.05)
            
            # トレンドの強度
            sin_r_squared = sin_r ** 2
            cos_r_squared = cos_r ** 2
            trend_strength = (sin_r_squared + cos_r_squared) / 2
            
            # 一定の強度を持つ場合のみトレンドありと判定
            has_trend = significant and trend_strength > 0.1
            
            if has_trend:
                # 開始・終了時点での方向を計算
                start_sin = sin_intercept
                start_cos = cos_intercept
                start_dir = np.degrees(np.arctan2(start_sin, start_cos)) % 360
                
                end_sin = sin_intercept + sin_slope * times[-1]
                end_cos = cos_intercept + cos_slope * times[-1]
                end_dir = np.degrees(np.arctan2(end_sin, end_cos)) % 360
                
                # 合計変化量
                total_change = self._calculate_angle_difference(end_dir, start_dir)
                
                # 変化率（度/分）
                if times[-1] > 0:
                    trend_rate = total_change / times[-1]
                else:
                    trend_rate = 0.0
                    
                # 最新の風向
                last_direction = directions[-1]
                last_time = df['timestamp'].iloc[-1]
                
                return {
                    "has_trend": True,
                    "direction_trend_rate": trend_rate,
                    "trend_strength": trend_strength,
                    "total_direction_change": total_change,
                    "sin_r_squared": sin_r_squared,
                    "cos_r_squared": cos_r_squared,
                    "last_direction": last_direction,
                    "last_time": last_time
                }
            
        except Exception as e:
            self.logger.warning("トレンド分析中にエラーが発生しました: %s", str(e))
            
        # トレンドなしの場合
        return {
            "has_trend": False,
            "direction_trend_rate": 0.0,
            "trend_strength": 0.0
        }
    
    def _analyze_oscillations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        風向の振動パターンを分析
        
        Parameters
        ----------
        df : pd.DataFrame
            前処理済みデータ
            
        Returns
        -------
        Dict[str, Any]
            振動パターン分析結果
        """
        # データが少なすぎる場合
        if len(df) < self.min_data_points:
            return {
                "has_oscillations": False,
                "oscillation_amplitude": 0.0,
                "oscillation_frequency": 0.0
            }
            
        # 風向の変化データ
        directions = df['wind_direction_smooth'].values
        changes = df['direction_change'].values
        
        # 振動の検出（正と負の変化の交代）
        sign_changes = 0
        for i in range(1, len(changes)):
            if changes[i] * changes[i-1] < 0 and abs(changes[i]) > 1.0 and abs(changes[i-1]) > 1.0:
                sign_changes += 1
                
        # 全データ長に対する符号変化の割合
        change_rate = sign_changes / len(df) if len(df) > 0 else 0
        
        # 一定以上の変化率があれば振動と判定
        has_oscillations = change_rate > 0.1  # 10ポイントに1回以上の符号変化
        
        if has_oscillations:
            # 風向の標準偏差（振幅の指標）
            direction_std = circstd(np.radians(directions)) * 180 / np.pi
            
            # 変化の大きさの平均（振幅の指標）
            abs_changes = np.abs(changes)
            mean_change = np.mean(abs_changes[abs_changes > 1.0])  # 1度以上の変化のみ考慮
            
            # 振動の振幅
            amplitude = max(direction_std, mean_change)
            
            # 振動の頻度（1分あたりの符号変化回数）
            total_minutes = df['minutes_from_start'].max() - df['minutes_from_start'].min()
            frequency = sign_changes / total_minutes if total_minutes > 0 else 0
            
            # 振動の検出（ウェーブレット解析等のより高度な手法も可能）
            
            return {
                "has_oscillations": True,
                "oscillation_amplitude": amplitude,
                "oscillation_frequency": frequency,
                "sign_changes": sign_changes,
                "direction_std": direction_std,
                "mean_abs_change": mean_change
            }
            
        # 振動なしの場合
        return {
            "has_oscillations": False,
            "oscillation_amplitude": 0.0,
            "oscillation_frequency": 0.0
        }
    
    def _analyze_geographical_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        地理的なパターンを分析
        
        Parameters
        ----------
        df : pd.DataFrame
            前処理済みデータ（位置情報を含む）
            
        Returns
        -------
        Dict[str, Any]
            地理的パターン分析結果
        """
        # 位置データがない場合
        if 'latitude' not in df.columns or 'longitude' not in df.columns:
            return {}
            
        # 位置データがあるレコードのみ抽出
        location_df = df.dropna(subset=['latitude', 'longitude'])
        
        # 位置データが少なすぎる場合
        if len(location_df) < 10:
            return {}
            
        # 単純なエリア分割による分析
        result = {}
        
        # 領域の境界を計算
        min_lat = location_df['latitude'].min()
        max_lat = location_df['latitude'].max()
        min_lon = location_df['longitude'].min()
        max_lon = location_df['longitude'].max()
        
        # クラスタリングを使用する場合
        if self.params["use_clustering"] and len(location_df) >= 20:
            try:
                from sklearn.cluster import DBSCAN
                
                # 位置データの準備
                coords = location_df[['latitude', 'longitude']].values
                
                # 適切なepsパラメータの推定
                lat_range = max_lat - min_lat
                lon_range = max_lon - min_lon
                avg_range = (lat_range + lon_range) / 2
                eps = avg_range / 10  # 領域の1/10を目安
                
                # DBSCANクラスタリング
                clustering = DBSCAN(eps=eps, min_samples=5).fit(coords)
                
                # クラスタラベル
                labels = clustering.labels_
                
                # クラスタごとの統計
                location_df['cluster'] = labels
                
                # 有効なクラスタ（-1はノイズ）
                valid_clusters = [label for label in set(labels) if label >= 0]
                
                # クラスタ情報
                clusters_info = []
                
                for cluster_id in valid_clusters:
                    cluster_data = location_df[location_df['cluster'] == cluster_id]
                    
                    # クラスタの中心
                    center_lat = cluster_data['latitude'].mean()
                    center_lon = cluster_data['longitude'].mean()
                    
                    # クラスタの半径（最大距離）
                    max_dist = 0
                    for _, row in cluster_data.iterrows():
                        dist = self._calculate_distance(
                            row['latitude'], row['longitude'], center_lat, center_lon)
                        max_dist = max(max_dist, dist)
                    
                    # クラスタ内の風向の分析
                    mean_direction = circmean(np.radians(cluster_data['wind_direction_smooth'])) * 180 / np.pi
                    direction_std = circstd(np.radians(cluster_data['wind_direction_smooth'])) * 180 / np.pi
                    
                    # 風向の安定性
                    stability = 1.0 - min(1.0, direction_std / 45)  # 45度以上のばらつきで最小安定性
                    
                    # 風の特性
                    if 'direction_change_rate' in cluster_data.columns:
                        # 変化率の分析
                        change_rates = cluster_data['direction_change_rate'].abs()
                        median_change = change_rates.median()
                        high_change_ratio = sum(change_rates > 1.0) / len(change_rates) if len(change_rates) > 0 else 0
                        
                        # パターンの特定
                        if high_change_ratio > 0.3:
                            pattern = "unstable"
                        elif median_change > 0.5:
                            pattern = "shifting"
                        elif stability > 0.8:
                            pattern = "stable"
                        else:
                            pattern = "moderate"
                    else:
                        median_change = 0
                        high_change_ratio = 0
                        pattern = "unknown"
                    
                    # クラスタ情報
                    cluster_info = {
                        "cluster_id": int(cluster_id),
                        "center_latitude": center_lat,
                        "center_longitude": center_lon,
                        "radius_meters": max_dist,
                        "point_count": len(cluster_data),
                        "mean_direction": mean_direction,
                        "direction_std": direction_std,
                        "stability": stability,
                        "pattern": pattern,
                        "median_change_rate": median_change,
                        "confidence": min(1.0, len(cluster_data) / 20) * stability
                    }
                    
                    clusters_info.append(cluster_info)
                
                # クラスタリング結果を返す
                if clusters_info:
                    result["region_clusters"] = clusters_info
                    return result
                    
            except Exception as e:
                self.logger.warning("地理的クラスタリング中にエラーが発生しました: %s", str(e))
        
        # クラスタリングが失敗または無効な場合は単純なグリッド分析
        # 2x2グリッドの作成
        grid_results = []
        lat_mid = (min_lat + max_lat) / 2
        lon_mid = (min_lon + max_lon) / 2
        
        # 各グリッドセルの分析
        for lat_range in [(min_lat, lat_mid), (lat_mid, max_lat)]:
            for lon_range in [(min_lon, lon_mid), (lon_mid, max_lon)]:
                # グリッドセル内のデータ
                cell_data = location_df[
                    (location_df['latitude'] >= lat_range[0]) &
                    (location_df['latitude'] < lat_range[1]) &
                    (location_df['longitude'] >= lon_range[0]) &
                    (location_df['longitude'] < lon_range[1])
                ]
                
                # データが十分にある場合のみ分析
                if len(cell_data) >= 5:
                    # セルの中心
                    center_lat = (lat_range[0] + lat_range[1]) / 2
                    center_lon = (lon_range[0] + lon_range[1]) / 2
                    
                    # 風向の分析
                    mean_direction = circmean(np.radians(cell_data['wind_direction_smooth'])) * 180 / np.pi
                    direction_std = circstd(np.radians(cell_data['wind_direction_smooth'])) * 180 / np.pi
                    
                    # グリッド情報
                    grid_info = {
                        "cell_id": len(grid_results),
                        "lat_range": lat_range,
                        "lon_range": lon_range,
                        "center_latitude": center_lat,
                        "center_longitude": center_lon,
                        "point_count": len(cell_data),
                        "mean_direction": mean_direction,
                        "direction_std": direction_std,
                        "confidence": min(1.0, len(cell_data) / 20)
                    }
                    
                    grid_results.append(grid_info)
        
        # グリッド分析結果を返す
        if grid_results:
            result["grid_analysis"] = grid_results
            
        return result
    
    def _aggregate_results(self, periodicity, trend, oscillation, geographical) -> Dict[str, Any]:
        """
        各分析結果を集約
        
        Parameters
        ----------
        periodicity : Dict[str, Any]
            周期性分析結果
        trend : Dict[str, Any]
            トレンド分析結果
        oscillation : Dict[str, Any]
            振動パターン分析結果
        geographical : Dict[str, Any]
            地理的パターン分析結果
            
        Returns
        -------
        Dict[str, Any]
            集約結果
        """
        # パターンの特性を判定
        has_periodicity = periodicity.get("has_periodicity", False)
        has_trend = trend.get("has_trend", False)
        has_oscillations = oscillation.get("has_oscillations", False)
        
        # パターンタイプの判定
        if has_periodicity and periodicity.get("pattern_strength", 0.0) > 0.3:
            pattern_type = "periodic"
        elif has_trend and trend.get("trend_strength", 0.0) > 0.3:
            pattern_type = "trending"
        elif has_oscillations and oscillation.get("oscillation_amplitude", 0.0) > 10.0:
            pattern_type = "oscillating"
        elif has_periodicity and has_oscillations:
            pattern_type = "complex"
        elif has_trend and has_oscillations:
            pattern_type = "trend_with_oscillations"
        elif not has_periodicity and not has_trend and not has_oscillations:
            pattern_type = "stable"
        else:
            pattern_type = "mixed"
            
        # 安定性の指標
        stability_factors = []
        
        # 周期性がある場合は高い安定性
        if has_periodicity:
            stability_factors.append(0.7 + 0.3 * periodicity.get("pattern_strength", 0.0))
            
        # トレンドがある場合は中程度の安定性
        if has_trend:
            trend_factor = 0.6 - 0.3 * min(1.0, abs(trend.get("direction_trend_rate", 0.0)))
            stability_factors.append(trend_factor)
            
        # 振動がある場合は低い安定性
        if has_oscillations:
            osc_amplitude = oscillation.get("oscillation_amplitude", 0.0)
            osc_factor = 0.5 - 0.3 * min(1.0, osc_amplitude / 30.0)
            stability_factors.append(osc_factor)
            
        # 安定性の総合評価（0-1）
        stability = min(1.0, sum(stability_factors) / max(1, len(stability_factors)))
        
        # デフォルトは中程度の安定性
        if not stability_factors:
            stability = 0.5
            
        # 予測可能性の指標
        predictability_factors = []
        
        # 周期性は高い予測可能性
        if has_periodicity:
            predictability_factors.append(0.8 + 0.2 * periodicity.get("pattern_strength", 0.0))
            
        # トレンドは中程度の予測可能性
        if has_trend:
            predictability_factors.append(0.6 + 0.3 * trend.get("trend_strength", 0.0))
            
        # 振動は低い予測可能性
        if has_oscillations:
            osc_frequency = oscillation.get("oscillation_frequency", 0.0)
            if osc_frequency > 0:
                predictability_factors.append(0.4 + 0.2 * min(1.0, 1.0 / (osc_frequency * 5.0)))
            else:
                predictability_factors.append(0.4)
                
        # 予測可能性の総合評価（0-1）
        predictability = min(1.0, sum(predictability_factors) / max(1, len(predictability_factors)))
        
        # デフォルトは中程度の予測可能性
        if not predictability_factors:
            predictability = 0.5
            
        # 主要な洞察のリスト
        key_insights = []
        
        # 周期性の洞察
        if has_periodicity:
            period_mins = periodicity.get("main_period_minutes", 0)
            if period_mins > 0:
                insight = f"風向に{period_mins:.1f}分周期のパターンが見られます。"
                key_insights.append(insight)
                
        # トレンドの洞察
        if has_trend:
            trend_rate = trend.get("direction_trend_rate", 0)
            if abs(trend_rate) > 0.1:
                direction = "右回り" if trend_rate > 0 else "左回り"
                insight = f"風向は{direction}に平均{abs(trend_rate):.1f}度/分の速度で変化しています。"
                key_insights.append(insight)
                
        # 振動の洞察
        if has_oscillations:
            amp = oscillation.get("oscillation_amplitude", 0)
            freq = oscillation.get("oscillation_frequency", 0)
            if amp > 5.0:
                insight = f"風向に±{amp:.1f}度の振動があり、約{60/freq if freq > 0 else 0:.1f}秒ごとに方向が変わります。"
                key_insights.append(insight)
                
        # 地理的洞察
        if geographical and "region_clusters" in geographical:
            clusters = geographical["region_clusters"]
            if clusters:
                # 最も安定したクラスタと最も不安定なクラスタを見つける
                stable_cluster = max(clusters, key=lambda c: c.get("stability", 0))
                unstable_cluster = min(clusters, key=lambda c: c.get("stability", 0))
                
                if stable_cluster["stability"] > 0.7 and unstable_cluster["stability"] < 0.5:
                    insight = f"コースの一部（緯度：{stable_cluster['center_latitude']:.6f}、経度：{stable_cluster['center_longitude']:.6f}）では風が安定しています。"
                    key_insights.append(insight)
                    
                    insight = f"一方、別のエリア（緯度：{unstable_cluster['center_latitude']:.6f}、経度：{unstable_cluster['center_longitude']:.6f}）では風が不安定です。"
                    key_insights.append(insight)
        
        # 集約結果
        return {
            "pattern_type": pattern_type,
            "stability": stability,
            "predictability": predictability,
            "key_insights": key_insights,
            "has_periodicity": has_periodicity,
            "has_trend": has_trend,
            "has_oscillations": has_oscillations
        }
    
    def _generate_recommendations(self, periodicity, trend, oscillation, geographical) -> Dict[str, Any]:
        """
        戦略的推奨事項を生成
        
        Parameters
        ----------
        periodicity : Dict[str, Any]
            周期性分析結果
        trend : Dict[str, Any]
            トレンド分析結果
        oscillation : Dict[str, Any]
            振動パターン分析結果
        geographical : Dict[str, Any]
            地理的パターン分析結果
            
        Returns
        -------
        Dict[str, Any]
            推奨事項
        """
        # 戦略的推奨事項のリスト
        recommendations = []
        
        # 特性に基づく推奨事項
        has_periodicity = periodicity.get("has_periodicity", False)
        has_trend = trend.get("has_trend", False)
        has_oscillations = oscillation.get("has_oscillations", False)
        
        # 周期性に基づく推奨事項
        if has_periodicity:
            period_mins = periodicity.get("main_period_minutes", 0)
            if period_mins > 0:
                # シフトポイント情報
                shift_points = periodicity.get("shift_points", [])
                
                if shift_points:
                    rec = f"風向の{period_mins:.1f}分周期パターンに注意し、周期内の予測可能なシフトポイント（"
                    shift_desc = []
                    
                    for pos, direction in shift_points:
                        time_in_cycle = pos * period_mins
                        dir_text = "右" if direction == "clockwise" else "左"
                        shift_desc.append(f"周期開始から{time_in_cycle:.1f}分で{dir_text}シフト")
                    
                    rec += "、".join(shift_desc) + "）を活用して戦略を立てましょう。"
                    recommendations.append(rec)
                else:
                    rec = f"風向には{period_mins:.1f}分周期のパターンがあります。このパターンをレースに活用しましょう。"
                    recommendations.append(rec)
        
        # トレンドに基づく推奨事項
        if has_trend:
            trend_rate = trend.get("direction_trend_rate", 0)
            if abs(trend_rate) > 0.1:
                direction = "右回り" if trend_rate > 0 else "左回り"
                
                # 適応戦略
                if abs(trend_rate) > 0.5:  # 速いトレンド
                    rec = f"風向は{direction}に速い速度（{abs(trend_rate):.1f}度/分）で変化しています。この持続的なシフトを見越したコース選択が重要です。"
                else:  # 遅いトレンド
                    rec = f"風向は{direction}に緩やかに（{abs(trend_rate):.1f}度/分）変化しています。レース戦略において、この徐々に進行するシフトを考慮しましょう。"
                    
                recommendations.append(rec)
                
                # シフト方向に基づく戦略
                if trend_rate > 0:  # 右シフト
                    rec = "右シフトトレンドでは、スタート後に右側のコースが有利になる傾向があります。"
                else:  # 左シフト
                    rec = "左シフトトレンドでは、スタート後に左側のコースが有利になる傾向があります。"
                    
                recommendations.append(rec)
        
        # 振動に基づく推奨事項
        if has_oscillations:
            amp = oscillation.get("oscillation_amplitude", 0)
            freq = oscillation.get("oscillation_frequency", 0)
            
            if amp > 5.0 and freq > 0:
                time_between = 60 / freq if freq > 0 else 0
                
                rec = f"風向は±{amp:.1f}度の範囲で振動しており、約{time_between:.1f}秒ごとに向きが変わっています。"
                recommendations.append(rec)
                
                # 振動の大きさによる戦略
                if amp > 15.0:  # 大きな振動
                    rec = "風向の大きな振動に対応するため、急激な風向変化に迅速に対応できるようセールトリムに注意を払いましょう。"
                    recommendations.append(rec)
                else:  # 小さな振動
                    rec = "風向の小さな振動に過剰反応せず、平均的な風向に合わせたコース取りを維持しましょう。"
                    recommendations.append(rec)
        
        # 地理的分析に基づく推奨事項
        if geographical and "region_clusters" in geographical:
            clusters = geographical["region_clusters"]
            if len(clusters) >= 2:
                # 風が最も安定したエリアと最も不安定なエリア
                stable_clusters = sorted(clusters, key=lambda c: c.get("stability", 0), reverse=True)
                
                if stable_clusters:
                    stable = stable_clusters[0]
                    if stable["stability"] > 0.7:
                        lat, lon = stable["center_latitude"], stable["center_longitude"]
                        rec = f"コースの一部（緯度：{lat:.6f}、経度：{lon:.6f}付近）では風が比較的安定しています。可能であればこのエリアを活用しましょう。"
                        recommendations.append(rec)
        
        # 総合的な戦略推奨
        overall_rec = "総合的な風分析に基づく戦略推奨: "
        
        if has_periodicity and periodicity.get("pattern_strength", 0) > 0.5:
            overall_rec += "周期的なパターンを活用し、予測可能なシフトを先読みしましょう。"
        elif has_trend and abs(trend.get("direction_trend_rate", 0)) > 0.3:
            overall_rec += "持続的なシフトトレンドを考慮したコース選択が重要です。"
        elif has_oscillations and oscillation.get("oscillation_amplitude", 0) > 10.0:
            overall_rec += "風向の振動に注意し、短期的な変動よりも長期的な傾向に注目しましょう。"
        else:
            overall_rec += "風の特性が複雑なため、柔軟な戦略と素早い対応が重要です。"
            
        recommendations.append(overall_rec)
        
        return {
            "strategy_recommendations": recommendations
        }
    
    def _calculate_angle_difference(self, angle1: float, angle2: float) -> float:
        """
        2つの角度の差を計算（-180〜180度の範囲で返す）
        
        Parameters
        ----------
        angle1 : float
            1つ目の角度（度、0-360）
        angle2 : float
            2つ目の角度（度、0-360）
            
        Returns
        -------
        float
            角度差（度、-180〜180）
        """
        # 角度が無効な場合は0を返す
        if not isinstance(angle1, (int, float)) or not isinstance(angle2, (int, float)):
            return 0
        
        # 角度を0-360の範囲に正規化
        a1 = angle1 % 360
        a2 = angle2 % 360
        
        # 角度差を計算（-180〜180度の範囲）
        diff = ((a1 - a2 + 180) % 360) - 180
        
        return diff
        
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        2点間の距離を計算（ヒュベニの公式、単位: メートル）
        
        Parameters
        ----------
        lat1 : float
            地点1の緯度
        lon1 : float
            地点1の経度
        lat2 : float
            地点2の緯度
        lon2 : float
            地点2の経度
            
        Returns
        -------
        float
            距離（メートル）
        """
        # 地球半径（メートル）
        earth_radius = 6371000
        
        # 緯度経度をラジアンに変換
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 緯度と経度の差
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        # ヒュベニの公式
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = earth_radius * c
        
        return distance
