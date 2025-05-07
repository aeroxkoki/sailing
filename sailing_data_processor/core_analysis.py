# -*- coding: utf-8 -*-
# sailing_data_processor/core_analysis.py
"""
セーリングデータ分析機能の実装

SailingDataProcessorクラスの分析関連機能を提供。
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import warnings
import gc
import io

# 内部モジュールのインポート
from sailing_data_processor.wind_estimator import WindEstimator
from sailing_data_processor.performance_optimizer import PerformanceOptimizer
from sailing_data_processor.boat_data_fusion import BoatDataFusionModel
from sailing_data_processor.wind_field_interpolator import WindFieldInterpolator


class SailingDataAnalyzer:
    """セーリングデータ分析クラス"""
    
    def __init__(self):
        """初期化"""
        self.boat_data = {}  # boat_id: DataFrameの辞書
        self.processed_data = {}  # 処理済みデータ
        self.synced_data = {}  # 同期済みデータ
        
        # コンポーネントのインスタンス化
        self._wind_estimator = WindEstimator()
        self._optimizer = PerformanceOptimizer()
        
        # オプショナルなモジュール（使用時にインスタンス化）
        self._fusion_model = None
        self._interpolator = None
        
        # 結果保存用の辞書
        self.wind_estimates = {}  # boat_id: 風向風速DataFrameの辞書
        self.wind_field_data = {}  # 時刻: 風場データの辞書
    
    def estimate_wind(self, boat_id: str, **kwargs) -> pd.DataFrame:
        """
        指定した艇のデータから風向風速を推定する
        
        Parameters:
        -----------
        boat_id : str
            艇の識別ID
        **kwargs : 
            wind_estimatorに渡す追加パラメータ
            
        Returns:
        --------
        pd.DataFrame
            風向風速推定結果
        """
        if boat_id not in self.boat_data:
            raise ValueError(f"Boat ID '{boat_id}' not found")
        
        df = self.boat_data[boat_id]
        
        # 風推定の実行
        from .core_io import SailingDataIO
        processor = SailingDataIO()
        processed_df = processor.process_data(df)
        wind_estimates = self._wind_estimator.estimate_wind(processed_df, **kwargs)
        
        # 結果の保存
        self.wind_estimates[boat_id] = wind_estimates
        
        return wind_estimates
    
    def create_wind_field(self, time_range: Optional[Tuple[datetime, datetime]] = None,
                         spatial_resolution: float = 0.001) -> Dict[str, Any]:
        """
        複数艇のデータから風場を生成する
        
        Parameters:
        -----------
        time_range : Optional[Tuple[datetime, datetime]]
            解析する時間範囲
        spatial_resolution : float
            空間解像度（度）
            
        Returns:
        --------
        Dict[str, Any]
            風場データ
        """
        if not self.wind_estimates:
            raise ValueError("No wind estimates available. Run estimate_wind() first.")
        
        # 融合モデルとインターポレータの初期化
        if self._fusion_model is None:
            self._fusion_model = BoatDataFusionModel()
        if self._interpolator is None:
            self._interpolator = WindFieldInterpolator()
        
        # データの同期
        if not self.synced_data:
            from .core_io import SailingDataIO
            processor = SailingDataIO()
            processor.boat_data = self.boat_data
            self.synced_data = processor.sync_boat_data()
        
        # 風場データの生成
        wind_field = self._fusion_model.fuse_boat_data(
            self.synced_data,
            self.wind_estimates,
            time_range=time_range
        )
        
        # 結果の保存
        self.wind_field_data = wind_field
        
        return wind_field
    
    def optimize_performance(self, boat_id: str) -> Dict[str, Any]:
        """
        指定した艇のパフォーマンスを最適化分析する
        
        Parameters:
        -----------
        boat_id : str
            艇の識別ID
            
        Returns:
        --------
        Dict[str, Any]
            パフォーマンス分析結果
        """
        if boat_id not in self.boat_data:
            raise ValueError(f"Boat ID '{boat_id}' not found")
        
        if boat_id not in self.wind_estimates:
            self.estimate_wind(boat_id)
        
        # パフォーマンス分析の実行
        optimization_result = self._optimizer.optimize(
            self.boat_data[boat_id],
            self.wind_estimates[boat_id]
        )
        
        return optimization_result
    
    def generate_report(self, boat_id: Optional[str] = None) -> Dict[str, Any]:
        """
        分析レポートを生成する
        
        Parameters:
        -----------
        boat_id : Optional[str]
            特定の艇のレポート（省略時は全体レポート）
            
        Returns:
        --------
        Dict[str, Any]
            分析レポート
        """
        report = {
            'summary': {
                'total_boats': len(self.boat_data),
                'analysis_time': datetime.now().isoformat()
            }
        }
        
        if boat_id:
            # 個別艇のレポート
            if boat_id not in self.boat_data:
                raise ValueError(f"Boat ID '{boat_id}' not found")
            
            report['boat_data'] = {
                'boat_id': boat_id,
                'data_points': len(self.boat_data[boat_id]),
                'time_range': {
                    'start': self.boat_data[boat_id]['time'].min().isoformat(),
                    'end': self.boat_data[boat_id]['time'].max().isoformat()
                }
            }
            
            if boat_id in self.wind_estimates:
                wind_data = self.wind_estimates[boat_id]
                report['wind_analysis'] = {
                    'average_wind_speed': wind_data['wind_speed'].mean(),
                    'average_wind_direction': wind_data['wind_dir'].mean(),
                    'wind_variability': wind_data['wind_speed'].std()
                }
        else:
            # 全体レポート
            report['boats'] = {}
            for bid in self.boat_data:
                report['boats'][bid] = {
                    'data_points': len(self.boat_data[bid]),
                    'has_wind_estimates': bid in self.wind_estimates
                }
        
        return report
    
    def get_data_quality_report(self) -> Dict[str, Dict[str, Any]]:
        """
        データ品質レポートを生成する
        
        Returns:
        --------
        Dict[str, Dict[str, Any]]
            艇ごとの品質レポート
        """
        report = {}
        
        for boat_id, df in self.boat_data.items():
            # 品質スコアの計算
            completeness = 1.0 - df.isnull().sum().sum() / (len(df) * len(df.columns))
            
            # データポイント数
            total_points = len(df)
            
            # 速度の異常値割合（20ノット以上を異常とする）
            if 'speed' in df.columns:
                speed_anomalies = (df['speed'] > 20.0).sum() / len(df)
            else:
                speed_anomalies = 0.0
            
            # 品質スコア（完全性、データ数、異常値の少なさを考慮）
            quality_score = completeness * 0.5 + \
                           min(total_points / 100, 1.0) * 0.3 + \
                           (1.0 - speed_anomalies) * 0.2
            
            # 品質評価（5段階）
            if quality_score >= 0.9:
                quality_rating = "Excellent"
            elif quality_score >= 0.8:
                quality_rating = "Good"
            elif quality_score >= 0.7:
                quality_rating = "Fair"
            elif quality_score >= 0.6:
                quality_rating = "Poor"
            else:
                quality_rating = "Critical"
            
            report[boat_id] = {
                'quality_score': quality_score,
                'quality_rating': quality_rating,
                'total_points': total_points,
                'completeness': completeness,
                'speed_anomalies_ratio': speed_anomalies
            }
        
        return report
    
    
    def process_multiple_boats(self) -> Dict[str, Any]:
        """
        複数艇のデータを処理する
        
        Returns:
        --------
        Dict[str, Any]
            処理結果（dataとstatsのキーを持つ）
        """
        result = {
            'data': {},
            'stats': {}
        }
        
        from .core_io import SailingDataIO
        processor = SailingDataIO()
        
        for boat_id, df in self.boat_data.items():
            # データの処理
            processed_df = processor.process_data(df)
            result['data'][boat_id] = processed_df
            
            # 統計情報の生成
            stats = {
                'total_points': len(processed_df),
                'avg_speed': processed_df['speed'].mean() if 'speed' in processed_df.columns else 0.0,
                'max_speed': processed_df['speed'].max() if 'speed' in processed_df.columns else 0.0,
                'total_distance': processed_df['distance'].max() if 'distance' in processed_df.columns else 0.0
            }
            result['stats'][boat_id] = stats
        
        return result
    
    def get_common_timeframe(self) -> Tuple[datetime, datetime]:
        """
        複数艇データの共通時間枠を検出する
        
        Returns:
        --------
        Tuple[datetime, datetime]
            (共通開始時刻, 共通終了時刻)
        """
        if not self.boat_data:
            raise ValueError("No boat data available")
        
        start_times = []
        end_times = []
        
        for boat_id, df in self.boat_data.items():
            time_col = 'timestamp' if 'timestamp' in df.columns else 'time'
            if time_col in df.columns:
                start_times.append(df[time_col].min())
                end_times.append(df[time_col].max())
        
        if not start_times or not end_times:
            raise ValueError("No valid time data found in boats")
        
        # 共通時間枠 = 最遅開始時刻 〜 最早終了時刻
        common_start = max(start_times)
        common_end = min(end_times)
        
        if common_start >= common_end:
            raise ValueError("No common time frame found")
        
        return common_start, common_end
    
    def detect_and_fix_gps_anomalies(self, boat_id: str, 
                                    max_speed_knots: float = 20.0,
                                    max_acceleration: float = 5.0,
                                    method: str = 'linear') -> pd.DataFrame:
        """
        GPS異常値を検出して修正する
        
        Parameters:
        -----------
        boat_id : str
            艇の識別ID
        max_speed_knots : float
            最大速度（ノット）
        max_acceleration : float
            最大加速度（m/s^2）
        method : str
            修正方法 ('linear' or 'kalman')
        
        Returns:
        --------
        pd.DataFrame
            修正されたデータ
        """
        if boat_id not in self.boat_data:
            raise ValueError(f"Boat ID '{boat_id}' not found")
        
        df = self.boat_data[boat_id].copy()
        
        # 異常な速度を検出し修正
        anomaly_mask = df['speed'] > max_speed_knots
        
        # 異常値を修正
        if anomaly_mask.any():
            # 前後の値の平均で補間
            for idx in df[anomaly_mask].index:
                prev_idx = idx - 1 if idx > 0 else idx
                next_idx = idx + 1 if idx < len(df) - 1 else idx
                
                if prev_idx == idx and next_idx == idx:
                    # 最初か最後の点の場合
                    df.loc[idx, 'speed'] = max_speed_knots - 1.0  # 最大速度より少し小さい値
                else:
                    # 前後の平均値（最大でもmax_speed_knotsを超えないようにする）
                    new_speed = (df.loc[prev_idx, 'speed'] + df.loc[next_idx, 'speed']) / 2
                    df.loc[idx, 'speed'] = min(new_speed, max_speed_knots - 0.1)
        
        # データを更新
        self.boat_data[boat_id] = df
        
        return df
    
    def process_multiple_boats(self) -> Dict[str, Any]:
        """
        複数艇のデータを処理する
        
        Returns:
        --------
        Dict[str, Any]
            処理結果
        """
        result = {
            'data': {},
            'stats': {}
        }
        
        for boat_id, df in self.boat_data.items():
            # データ処理
            processed_df = self._preprocess_data(df)
            
            # 統計情報計算
            stats = {
                'total_points': len(processed_df),
                'avg_speed': processed_df['speed'].mean() if 'speed' in processed_df.columns else None,
                'max_speed': processed_df['speed'].max() if 'speed' in processed_df.columns else None,
                'time_range': {
                    'start': processed_df['timestamp'].min() if 'timestamp' in processed_df.columns else None,
                    'end': processed_df['timestamp'].max() if 'timestamp' in processed_df.columns else None
                }
            }
            
            result['data'][boat_id] = processed_df
            result['stats'][boat_id] = stats
        
        return result
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データの前処理
        
        Parameters:
        -----------
        df : pd.DataFrame
            入力データ
        
        Returns:
        --------
        pd.DataFrame
            処理されたデータ
        """
        processed_df = df.copy()
        
        # 必要な列がない場合は計算
        if 'speed' not in processed_df.columns and 'latitude' in processed_df.columns and 'longitude' in processed_df.columns:
            # 速度計算
            from scipy.spatial.distance import cdist
            
            coords = processed_df[['latitude', 'longitude']].values
            if len(coords) > 1:
                dists = np.concatenate(([0], np.sqrt(np.sum(np.diff(coords, axis=0)**2, axis=1))))
                times = processed_df['timestamp'].diff().dt.total_seconds().fillna(0).values
                speeds = np.divide(dists, times, where=times!=0)
                speeds = np.nan_to_num(speeds, 0)
                processed_df['speed'] = speeds * 60 * 60 / 1852  # m/s to knots
            else:
                processed_df['speed'] = 0
        
        return processed_df
