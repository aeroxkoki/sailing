"""
風の場融合システムの改良版 - パフォーマンス最適化

このモジュールは、既存のWindFieldFusionSystemを拡張し、
大規模データ処理時のパフォーマンスと安定性を向上させる改良を加えています。
"""

# モジュールインポート
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
import math
from scipy.interpolate import griddata, NearestNDInterpolator
import warnings
from functools import lru_cache
import sys

# 内部モジュールのインポート
from sailing_data_processor.wind_field_fusion_system import WindFieldFusionSystem
from sailing_data_processor.wind_field_interpolator import WindFieldInterpolator
from sailing_data_processor.wind_propagation_model import WindPropagationModel

class OptimizedWindFieldFusionSystem(WindFieldFusionSystem):
    """
    最適化された風の場融合システム
    
    WindFieldFusionSystemのメモリ使用量とパフォーマンスを最適化し、
    大規模データセットでの処理効率を向上させる拡張クラス。
    
    主な改良点:
    - メモリ使用量の最適化（チャンク処理）
    - データ処理パイプラインの効率化
    - スケーリング処理の強化
    - 風の場補間の安定性向上
    - 並列処理のサポート（オプション）
    """
    
    def __init__(self, max_points_per_fusion=1000, enable_parallel=False):
        """
        初期化
        
        Parameters:
        -----------
        max_points_per_fusion : int
            融合処理時に一度に扱う最大データポイント数
        enable_parallel : bool
            並列処理を有効にするかどうか
        """
        # 親クラスの初期化
        super().__init__()
        
        # データポイント数の上限
        self.max_points_per_fusion = max_points_per_fusion
        
        # 並列処理設定
        self.enable_parallel = enable_parallel
        self.parallel_workers = 4 if enable_parallel else 1
        
        # メモリキャッシュとデータ管理
        self.point_cache = {}  # キャッシュデータ
        self.cache_expiry = 1800  # キャッシュ有効期間（秒）
        
        # 最適化設定
        self.optimization_config = {
            'adaptive_grid_size': True,  # データ量に応じたグリッドサイズ自動調整
            'use_data_reduction': True,  # 冗長データの削減
            'use_memory_efficient_arrays': True,  # メモリ効率の良い配列型を使用
            'estimate_memory_usage': True,  # メモリ使用量の推定と調整
            'spatial_partitioning': True,  # 空間パーティショニングによる処理効率化
            'time_partitioning': True  # 時間パーティショニングによる処理効率化
        }
    
    def update_with_boat_data(self, boats_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        複数の艇データから風の場を更新（最適化版）
        
        Parameters:
        -----------
        boats_data : Dict[str, pd.DataFrame]
            艇IDをキーとする艇データのデータフレームの辞書
            
        Returns:
        --------
        Dict[str, Any]
            更新された風の場
        """
        # データの前処理と点検（最適化: 早期フィルタリング）
        valid_boats_data = self._preprocess_boats_data(boats_data)
        
        # データポイント数が多い場合、チャンク処理
        if self._count_total_data_points(valid_boats_data) > self.max_points_per_fusion:
            return self._process_in_chunks(valid_boats_data)
        
        # データポイント数が少ない場合は通常処理
        return super().update_with_boat_data(valid_boats_data)
    
    def _preprocess_boats_data(self, boats_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """
        艇データの前処理と最適化
        
        Parameters:
        -----------
        boats_data : Dict[str, pd.DataFrame]
            艇データの辞書
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            前処理済みの艇データ
        """
        valid_boats_data = {}
        
        for boat_id, boat_df in boats_data.items():
            # 空のデータフレームはスキップ
            if boat_df.empty:
                continue
            
            # 必要なカラムがあるか確認
            required_columns = ['timestamp', 'latitude', 'longitude', 'wind_direction', 'wind_speed_knots']
            if not all(col in boat_df.columns for col in required_columns):
                warnings.warn(f"Boat {boat_id} data missing required columns")
                continue
            
            # タイムスタンプをdatetime型に変換
            if not pd.api.types.is_datetime64_any_dtype(boat_df['timestamp']):
                try:
                    boat_df['timestamp'] = pd.to_datetime(boat_df['timestamp'])
                except:
                    warnings.warn(f"Boat {boat_id} has invalid timestamp format")
                    continue
            
            # 最適化: 重複データの削除
            if self.optimization_config['use_data_reduction']:
                boat_df = boat_df.drop_duplicates(subset=['timestamp', 'latitude', 'longitude'])
            
            # 最適化: データの時間フィルタリング（直近30分のみ使用）
            if self.optimization_config['time_partitioning']:
                latest_time = boat_df['timestamp'].max()
                time_threshold = latest_time - timedelta(seconds=1800)
                boat_df = boat_df[boat_df['timestamp'] >= time_threshold]
            
            # 最適化: 空間間引き（データ密度が極端に高い箇所を適度に間引く）
            if self.optimization_config['spatial_partitioning'] and len(boat_df) > 100:
                # グリッド状に空間を分割
                lat_bins = pd.cut(boat_df['latitude'], 10)
                lon_bins = pd.cut(boat_df['longitude'], 10)
                
                # 各セルから最大10ポイントをサンプリング
                grouped = boat_df.groupby([lat_bins, lon_bins])
                samples = []
                
                for _, group in grouped:
                    # 各グループから最大10ポイントを取得
                    if len(group) > 10:
                        # タイムスタンプでソートして均等にサンプリング
                        sorted_group = group.sort_values('timestamp')
                        sampled = sorted_group.iloc[::len(sorted_group)//10][:10]
                        samples.append(sampled)
                    else:
                        samples.append(group)
                
                if samples:
                    boat_df = pd.concat(samples)
            
            valid_boats_data[boat_id] = boat_df
        
        return valid_boats_data
    
    def _count_total_data_points(self, boats_data: Dict[str, pd.DataFrame]) -> int:
        """
        全ての艇データの合計ポイント数を計算
        
        Parameters:
        -----------
        boats_data : Dict[str, pd.DataFrame]
            艇データの辞書
            
        Returns:
        --------
        int
            合計データポイント数
        """
        return sum(len(df) for df in boats_data.values())
    
    def _process_in_chunks(self, boats_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        大規模データをチャンクに分割して処理
        
        Parameters:
        -----------
        boats_data : Dict[str, pd.DataFrame]
            艇データの辞書
            
        Returns:
        --------
        Dict[str, Any]
            更新された風の場
        """
        # データを時間で分割
        all_timestamps = []
        for df in boats_data.values():
            all_timestamps.extend(df['timestamp'].tolist())
        
        all_timestamps = sorted(all_timestamps)
        
        # チャンクに分割する境界時間を決定
        num_chunks = max(2, len(all_timestamps) // self.max_points_per_fusion + 1)
        chunk_boundaries = []
        
        for i in range(1, num_chunks):
            idx = i * len(all_timestamps) // num_chunks
            if idx < len(all_timestamps):
                chunk_boundaries.append(all_timestamps[idx])
        
        # 最新の時間を追加
        chunk_boundaries.append(max(all_timestamps) + timedelta(seconds=1))
        
        # 各チャンクを処理
        wind_fields = []
        previous_boundary = min(all_timestamps) - timedelta(seconds=1)
        
        for boundary in chunk_boundaries:
            # このチャンクのデータを抽出
            chunk_data = {}
            for boat_id, df in boats_data.items():
                mask = (df['timestamp'] > previous_boundary) & (df['timestamp'] <= boundary)
                chunk_df = df[mask]
                if not chunk_df.empty:
                    chunk_data[boat_id] = chunk_df
            
            # チャンクデータがある場合は処理
            if chunk_data:
                # 親クラスのupdate_with_boat_dataを使って処理
                field = super().update_with_boat_data(chunk_data)
                if field:
                    wind_fields.append(field)
            
            previous_boundary = boundary
        
        # 処理した風の場がない場合
        if not wind_fields:
            return None
        
        # 最後に処理した風の場を返す（最新）
        return wind_fields[-1]
    
    def _scale_data_points(self, data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        風データポイントを適切にスケーリングして補間処理を安定化（最適化版）
        
        Parameters:
        -----------
        data_points : List[Dict]
            風データポイントのリスト
            
        Returns:
        --------
        List[Dict]
            スケーリングされたデータポイントのリスト
        """
        if not data_points:
            return []
        
        # 座標データの範囲を取得
        lats = np.array([p['latitude'] for p in data_points])
        lons = np.array([p['longitude'] for p in data_points])
        winds = np.array([p['wind_speed'] for p in data_points])
        
        # NumPyの高速関数を使用
        min_lat, max_lat = np.min(lats), np.max(lats)
        min_lon, max_lon = np.min(lons), np.max(lons)
        min_wind, max_wind = np.min(winds), np.max(winds)
        
        # スケーリング係数の計算（範囲が狭すぎる場合に対応）
        lat_range = max_lat - min_lat
        lon_range = max_lon - min_lon
        wind_range = max_wind - min_wind
        
        # 最小範囲の設定
        min_range = 0.005  # 約500mの最小範囲
        min_wind_range = 1.0  # 最小風速範囲
        
        # 必要に応じて範囲を拡大
        if lat_range < min_range:
            lat_padding = (min_range - lat_range) / 2 + 0.001
            min_lat -= lat_padding
            max_lat += lat_padding
            lat_range = min_range + 0.002
        
        if lon_range < min_range:
            lon_padding = (min_range - lon_range) / 2 + 0.001
            min_lon -= lon_padding
            max_lon += lon_padding
            lon_range = min_range + 0.002
        
        if wind_range < min_wind_range:
            wind_padding = (min_wind_range - wind_range) / 2 + 0.2
            min_wind = max(0, min_wind - wind_padding)
            max_wind += wind_padding
            wind_range = min_wind_range + 0.4
        
        # 最適化: NumPyのベクトル化を使用
        scale_lat = 1.0 / lat_range if lat_range > 0 else 1.0
        scale_lon = 1.0 / lon_range if lon_range > 0 else 1.0
        scale_wind = 1.0 / wind_range if wind_range > 0 else 1.0
        
        # データのコピー作成と高速なスケーリング処理
        scaled_data = []
        
        # 乱数生成を一度だけ行い再利用する（最適化）
        rand_lat = np.random.normal(0, 0.002, len(data_points))
        rand_lon = np.random.normal(0, 0.002, len(data_points))
        rand_wind = np.random.normal(0, 0.005, len(data_points))
        
        for i, point in enumerate(data_points):
            # 元のデータをコピー
            scaled_point = point.copy()
            
            # スケーリング処理
            norm_lat = (point['latitude'] - min_lat) * scale_lat
            norm_lon = (point['longitude'] - min_lon) * scale_lon
            norm_wind = (point['wind_speed'] - min_wind) * scale_wind
            
            # 事前生成した乱数を使用
            norm_lat += rand_lat[i]
            norm_lon += rand_lon[i]
            norm_wind += rand_wind[i]
            
            # スケーリングされた値を設定
            scaled_point['scaled_latitude'] = norm_lat
            scaled_point['scaled_longitude'] = norm_lon
            scaled_point['scaled_height'] = norm_wind
            
            # 元の値を保持
            scaled_point['original_latitude'] = point['latitude']
            scaled_point['original_longitude'] = point['longitude']
            
            # スケーリングされた値を使用
            scaled_point['latitude'] = norm_lat
            scaled_point['longitude'] = norm_lon
            scaled_point['height'] = norm_wind
            
            scaled_data.append(scaled_point)
        
        return scaled_data
    
    def fuse_wind_data(self):
        """
        風データポイントを融合して風の場を生成（最適化版）
        """
        if not self.wind_data_points:
            return
        
        # データポイント数の確認と調整（最適化）
        if len(self.wind_data_points) > self.max_points_per_fusion:
            # データポイントが多すぎる場合、最新のデータを優先
            sorted_data = sorted(self.wind_data_points, key=lambda x: x['timestamp'])
            self.wind_data_points = sorted_data[-self.max_points_per_fusion:]
        
        # 以降は親クラスの処理を呼び出す
        super().fuse_wind_data()
    
    def predict_wind_field(self, target_time: datetime, grid_resolution: int = 20) -> Optional[Dict[str, Any]]:
        """
        目標時間の風の場を予測（最適化版）
        
        Parameters:
        -----------
        target_time : datetime
            予測対象の時間
        grid_resolution : int
            グリッド解像度
            
        Returns:
        --------
        Dict[str, Any] or None
            予測された風の場
        """
        # 現在の風の場が利用可能かチェック
        if not self.current_wind_field:
            return None
        
        # 最適化: 解像度の動的調整
        if self.optimization_config['adaptive_grid_size']:
            adjusted_resolution = self._adjust_grid_resolution(grid_resolution)
        else:
            adjusted_resolution = grid_resolution
        
        # 親クラスの予測メソッドを呼び出し
        result = super().predict_wind_field(target_time, adjusted_resolution)
        
        return result
    
    def _adjust_grid_resolution(self, grid_resolution: int) -> int:
        """
        データ量と予測時間に基づいて解像度を動的に調整
        
        Parameters:
        -----------
        grid_resolution : int
            要求されたグリッド解像度
            
        Returns:
        --------
        int
            調整されたグリッド解像度
        """
        # 基本的な調整はメモリ使用状況に基づく
        try:
            import psutil
            memory_percent = psutil.virtual_memory().percent
            
            # メモリ使用率が高い場合は解像度を下げる
            if memory_percent > 90:
                return max(5, grid_resolution // 4)
            elif memory_percent > 75:
                return max(10, grid_resolution // 2)
        except:
            pass  # psutilが使用できない場合
        
        # データ量に基づく調整
        data_points_count = len(self.wind_data_points)
        
        if data_points_count > 500:
            # 大量データでは解像度を下げる
            return min(grid_resolution, 15)
        elif data_points_count < 10:
            # 少量データでは解像度を下げる（過適合防止）
            return min(grid_resolution, 10)
        
        return grid_resolution
    
    def clear_cache(self):
        """
        メモリキャッシュをクリア
        """
        self.point_cache = {}
