# -*- coding: utf-8 -*-
# sailing_data_processor/core.py
"""
セーリングデータ処理の統合モジュール

SailingDataProcessorクラスを提供し、GPSデータから風推定、
パフォーマンス最適化、戦略分析を統合的に実行する。
"""

from typing import Dict, List, Tuple, Optional, Union, Any
import pandas as pd
import gc
import io
from datetime import datetime, timedelta

# 内部モジュールのインポート
from .core_io import SailingDataIO
from .core_analysis import SailingDataAnalyzer


class SailingDataProcessor(SailingDataIO, SailingDataAnalyzer):
    """セーリングデータ処理の統合クラス - GPSデータから風推定・戦略分析を実行"""
    
    def __init__(self):
        """初期化"""
        # 親クラスの初期化
        SailingDataIO.__init__(self)
        SailingDataAnalyzer.__init__(self)
        
        # 共有データ属性は統一する（両方の親クラスで使用される属性）
        self.boat_data = {}  # boat_id: DataFrameの辞書
        self.synced_data = {}  # 同期済みデータ
    
    def process_multiple_boats(self) -> Dict[str, Any]:
        """
        複数のボートデータを一括処理する関数

        Returns:
        --------
        Dict[str, Any]
            処理済みデータと統計情報を含む辞書
            {
                'data': {boat_id: DataFrame, ...},
                'stats': {boat_id: stats_dict, ...}
            }
        """
        if not self.boat_data:
            return {'data': {}, 'stats': {}}
        
        processed_data = {}
        stats = {}
        
        for boat_id, df in self.boat_data.items():
            try:
                # 不足しているカラムがある場合は追加
                if 'speed' not in df.columns:
                    df['speed'] = float('nan')
                if 'course' not in df.columns:
                    df['course'] = float('nan')
                
                # 異常値を検出・修正
                processed_df = self.detect_and_fix_gps_anomalies(boat_id)
                
                # 基本統計の計算
                stats[boat_id] = {
                    'point_count': len(processed_df),
                    'distance': processed_df['distance'].max() if 'distance' in processed_df.columns else 0,
                    'avg_speed': processed_df['speed'].mean() if 'speed' in processed_df.columns else 0,
                    'max_speed': processed_df['speed'].max() if 'speed' in processed_df.columns else 0,
                    'start_time': processed_df['timestamp'].min() if 'timestamp' in processed_df.columns else None,
                    'end_time': processed_df['timestamp'].max() if 'timestamp' in processed_df.columns else None
                }
                
                # 処理済みデータを格納
                processed_data[boat_id] = processed_df
                
            except Exception as e:
                print(f"警告: ボート {boat_id} の処理中にエラーが発生しました: {e}")
                # エラー時は元のデータをそのまま使用
                processed_data[boat_id] = df
                stats[boat_id] = {'error': str(e)}
        
        return {
            'data': processed_data,
            'stats': stats
        }

    def detect_and_fix_gps_anomalies(self, boat_id: str, max_speed_knots: float = 40.0) -> pd.DataFrame:
        """
        GPSデータの異常値を検出し修正する

        Parameters:
        -----------
        boat_id : str
            処理するボートのID
        max_speed_knots : float
            最大速度の閾値（ノット）

        Returns:
        --------
        pd.DataFrame
            修正済みのデータフレーム
        """
        if boat_id not in self.boat_data:
            raise ValueError(f"ボートID {boat_id} が見つかりません")
        
        df = self.boat_data[boat_id].copy()
        
        # GPSAnomalyDetectorを使用して異常値を検出
        from .anomaly import GPSAnomalyDetector
        detector = GPSAnomalyDetector()
        detector.detection_config['speed_multiplier'] = max_speed_knots / 15.0  # デフォルト閾値の調整
        
        # 必要なカラムの確認と追加
        required_columns = ['timestamp', 'latitude', 'longitude']
        for col in required_columns:
            if col not in df.columns:
                if col == 'timestamp' and 'time' in df.columns:
                    df['timestamp'] = df['time']
                elif col == 'latitude' and 'lat' in df.columns:
                    df['latitude'] = df['lat']
                elif col == 'longitude' and 'lon' in df.columns:
                    df['longitude'] = df['lon']
                else:
                    raise ValueError(f"必須カラム {col} がデータフレームにありません")
        
        # 異常値の検出
        result_df = detector.detect_anomalies(df, methods=['z_score', 'speed', 'acceleration'])
        
        # 異常値の修正（補間）
        if 'is_anomaly' in result_df.columns and result_df['is_anomaly'].any():
            # 異常と判定された行をマスク
            anomaly_mask = result_df['is_anomaly']
            
            # 異常値を含む数値カラムの特定
            numeric_columns = result_df.select_dtypes(include=['number']).columns
            columns_to_interpolate = [col for col in numeric_columns 
                                     if col not in ['is_anomaly', 'anomaly_score']]
            
            # 異常値を線形補間で修正
            for col in columns_to_interpolate:
                # 異常値をNaNに置き換え
                result_df.loc[anomaly_mask, col] = float('nan')
                # 線形補間
                result_df[col] = result_df[col].interpolate(method='linear')
            
            print(f"ボート {boat_id} の異常値 {anomaly_mask.sum()} 件を修正しました")
        
        return result_df

    def get_common_timeframe(self) -> Tuple[datetime, datetime]:
        """
        全ボートデータの共通時間枠を取得する

        Returns:
        --------
        Tuple[datetime, datetime]
            (開始時刻, 終了時刻)のタプル
        """
        if not self.boat_data:
            raise ValueError("ボートデータがありません")
        
        start_times = []
        end_times = []
        
        for boat_id, df in self.boat_data.items():
            time_col = 'timestamp' if 'timestamp' in df.columns else 'time'
            
            if time_col not in df.columns or df[time_col].empty:
                print(f"警告: ボート {boat_id} の時間データがありません")
                continue
            
            # 日時型かどうか確認し、必要に応じて変換
            if not pd.api.types.is_datetime64_dtype(df[time_col]):
                try:
                    time_data = pd.to_datetime(df[time_col], errors='coerce')
                    time_data = time_data.dropna()
                except Exception as e:
                    print(f"警告: ボート {boat_id} の時間データ変換に失敗しました: {e}")
                    continue
            else:
                time_data = df[time_col]
            
            if not time_data.empty:
                start_times.append(time_data.min())
                end_times.append(time_data.max())
        
        if not start_times or not end_times:
            raise ValueError("有効な時間データがありません")
        
        # 共通の開始・終了時刻
        common_start = max(start_times)
        common_end = min(end_times)
        
        return common_start, common_end

    def get_data_quality_report(self) -> Dict[str, Dict[str, Any]]:
        """
        全ボートデータの品質レポートを生成する

        Returns:
        --------
        Dict[str, Dict[str, Any]]
            ボートIDをキーとするレポート辞書
        """
        if not self.boat_data:
            return {}
        
        quality_report = {}
        
        for boat_id, df in self.boat_data.items():
            # 基本指標の計算
            total_points = len(df)
            
            # 時間データの確認
            time_col = 'timestamp' if 'timestamp' in df.columns else 'time'
            has_time_data = time_col in df.columns and not df[time_col].empty
            
            if has_time_data:
                # 時間データのギャップ検出
                sorted_df = df.sort_values(by=time_col)
                time_diffs = sorted_df[time_col].diff().dropna()
                
                if not time_diffs.empty:
                    avg_interval = time_diffs.mean().total_seconds()
                    max_gap = time_diffs.max().total_seconds()
                    time_regularity = 1.0 - (time_diffs.std().total_seconds() / (avg_interval + 1e-6))
                    time_regularity = max(0.0, min(1.0, time_regularity))  # 0～1に正規化
                else:
                    avg_interval = 0
                    max_gap = 0
                    time_regularity = 0
            else:
                avg_interval = 0
                max_gap = 0
                time_regularity = 0
            
            # 位置データの確認
            has_position_data = ('latitude' in df.columns or 'lat' in df.columns) and \
                               ('longitude' in df.columns or 'lon' in df.columns)
            
            if has_position_data:
                lat_col = 'latitude' if 'latitude' in df.columns else 'lat'
                lon_col = 'longitude' if 'longitude' in df.columns else 'lon'
                
                # 位置の飛び検出
                lat_diffs = df[lat_col].diff().abs().dropna()
                lon_diffs = df[lon_col].diff().abs().dropna()
                
                if not lat_diffs.empty and not lon_diffs.empty:
                    max_position_jump = max(lat_diffs.max(), lon_diffs.max())
                    position_regularity = 1.0 - (
                        (lat_diffs.std() / (lat_diffs.mean() + 1e-6) + 
                         lon_diffs.std() / (lon_diffs.mean() + 1e-6)) / 2
                    )
                    position_regularity = max(0.0, min(1.0, position_regularity))  # 0～1に正規化
                else:
                    max_position_jump = 0
                    position_regularity = 0
            else:
                max_position_jump = 0
                position_regularity = 0
            
            # スコア計算
            data_completeness = sum([has_time_data, has_position_data]) / 2.0
            
            # 欠損値の確認
            missing_rate = df.isna().mean().mean() if not df.empty else 1.0
            data_integrity = 1.0 - missing_rate
            
            # 総合品質スコア
            quality_score = 0.4 * data_completeness + 0.3 * data_integrity + \
                            0.15 * time_regularity + 0.15 * position_regularity
            
            # 品質評価
            if quality_score >= 0.8:
                quality_rating = 'Excellent'
            elif quality_score >= 0.6:
                quality_rating = 'Good'
            elif quality_score >= 0.4:
                quality_rating = 'Fair'
            elif quality_score >= 0.2:
                quality_rating = 'Poor'
            else:
                quality_rating = 'Very Poor'
            
            # レポート作成
            quality_report[boat_id] = {
                'quality_score': quality_score,
                'quality_rating': quality_rating,
                'total_points': total_points,
                'data_completeness': data_completeness,
                'data_integrity': data_integrity,
                'time_regularity': time_regularity,
                'position_regularity': position_regularity,
                'avg_time_interval': avg_interval,
                'max_time_gap': max_gap,
                'max_position_jump': max_position_jump,
                'missing_rate': missing_rate
            }
        
        return quality_report
    
    def cleanup(self):
        """メモリをクリーンアップする"""
        # SailingDataIOからの属性
        self.boat_data.clear()
        self.synced_data.clear()
        
        # SailingDataAnalyzerからの属性
        self.processed_data.clear()
        self.wind_estimates.clear()
        self.wind_field_data.clear()
        
        gc.collect()