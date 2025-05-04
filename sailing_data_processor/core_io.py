# -*- coding: utf-8 -*-
# sailing_data_processor/core_io.py
"""
セーリングデータI/O機能の実装

SailingDataProcessorクラスのデータ入出力関連機能を提供。
"""

import pandas as pd
import numpy as np
import gpxpy
import io
import math
import os
import gc
from geopy.distance import geodesic
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any


class SailingDataIO:
    """セーリングデータI/Oクラス"""
    
    def __init__(self):
        """初期化"""
        self.boat_data = {}  # boat_id: DataFrameの辞書
        self.synced_data = {}  # 同期済みデータ
        self.max_boats = 100  # 最大艇数制限
    
    def load_data(self, file_path: str, boat_id: Optional[str] = None, 
                  file_type: str = 'gpx') -> pd.DataFrame:
        """
        GPSデータをファイルから読み込む
        
        Parameters:
        -----------
        file_path : str
            ファイルパス
        boat_id : Optional[str]
            艇の識別ID（省略時は自動生成）
        file_type : str
            ファイルタイプ ('gpx' または 'csv')
            
        Returns:
        --------
        pd.DataFrame
            読み込んだデータ
        """
        if file_type == 'gpx':
            df = self._load_gpx(file_path)
        elif file_type == 'csv':
            df = self._load_csv(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # 艇IDの生成または使用
        if boat_id is None:
            boat_id = f"boat_{len(self.boat_data) + 1}"
        
        # 艇数制限のチェック
        if len(self.boat_data) >= self.max_boats:
            raise ValueError(f"Maximum number of boats ({self.max_boats}) exceeded")
        
        # データの保存
        self.boat_data[boat_id] = df
        return df
    
    def _load_gpx(self, file_path: str) -> pd.DataFrame:
        """GPXファイルを読み込む（内部メソッド）"""
        with open(file_path, 'r') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
        
        data = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    data.append({
                        'time': point.time,
                        'lat': point.latitude,
                        'lon': point.longitude
                    })
        
        return pd.DataFrame(data)
    
    def _load_csv(self, file_path: str) -> pd.DataFrame:
        """CSVファイルを読み込む（内部メソッド）"""
        df = pd.read_csv(file_path)
        
        # 必須カラムのチェック
        required_columns = ['time', 'lat', 'lon']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in CSV")
        
        # 時刻データの変換
        df['time'] = pd.to_datetime(df['time'])
        
        return df
    
    def load_multiple_files(self, file_contents: List[Tuple[str, Union[str, io.BytesIO], str]], 
                          auto_id: bool = True, manual_ids: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        複数のファイルを同時に読み込む
        
        Parameters:
        -----------
        file_contents : List[Tuple[str, Union[str, io.BytesIO], str]]
            (ファイル名, コンテンツ, タイプ)のリスト
        auto_id : bool
            自動でIDを生成するかどうか
        manual_ids : Optional[List[str]]
            手動で指定するID（auto_id=Falseの場合に使用）
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            艇ID: データフレームの辞書
        """
        result = {}
        
        for i, (filename, content, file_type) in enumerate(file_contents):
            if auto_id:
                # ファイル名からボートIDを生成
                boat_id = os.path.splitext(filename)[0]
            else:
                if manual_ids and i < len(manual_ids):
                    boat_id = manual_ids[i]
                else:
                    boat_id = f"boat_{i+1}"
            
            # コンテンツからDataFrameを作成
            if file_type == 'csv':
                if isinstance(content, str):
                    df = pd.read_csv(io.StringIO(content))
                else:
                    df = pd.read_csv(content)
                
                # 必須カラムのチェック
                required_columns = ['timestamp', 'latitude', 'longitude', 'speed']
                for col in required_columns:
                    if col not in df.columns:
                        raise ValueError(f"Required column '{col}' not found in file {filename}")
                
                # timestampを正しい型に変換
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                result[boat_id] = df
                self.boat_data[boat_id] = df
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        
        return result
    
    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        GPSデータを処理し、速度・コース・距離を計算する
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPSデータ
            
        Returns:
        --------
        pd.DataFrame
            処理済みデータ
        """
        df = df.copy()
        
        # カラム名の正規化
        if 'timestamp' in df.columns:
            df['time'] = df['timestamp']
        if 'latitude' in df.columns:
            df['lat'] = df['latitude']
        if 'longitude' in df.columns:
            df['lon'] = df['longitude']
        
        df = df.sort_values('time').reset_index(drop=True)
        
        # 速度と距離の計算
        df['speed'] = 0.0
        df['course'] = 0.0
        df['distance'] = 0.0
        
        for i in range(1, len(df)):
            # 距離計算（測地線距離）
            dist = geodesic(
                (df.loc[i-1, 'lat'], df.loc[i-1, 'lon']),
                (df.loc[i, 'lat'], df.loc[i, 'lon'])
            ).meters
            
            # 時間差計算
            time_diff = (df.loc[i, 'time'] - df.loc[i-1, 'time']).total_seconds()
            
            # 速度計算（ノット）
            if time_diff > 0:
                speed_mps = dist / time_diff
                df.loc[i, 'speed'] = speed_mps * 1.94384  # m/s to knots
            
            # コース計算（真方位）
            lat1, lon1 = math.radians(df.loc[i-1, 'lat']), math.radians(df.loc[i-1, 'lon'])
            lat2, lon2 = math.radians(df.loc[i, 'lat']), math.radians(df.loc[i, 'lon'])
            
            dlon = lon2 - lon1
            y = math.sin(dlon) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
            course = math.degrees(math.atan2(y, x))
            df.loc[i, 'course'] = (course + 360) % 360
            
            # 累積距離
            df.loc[i, 'distance'] = df.loc[i-1, 'distance'] + dist
        
        # 最初のポイントの値を設定
        if len(df) > 1:
            df.loc[0, 'speed'] = df.loc[1, 'speed']
            df.loc[0, 'course'] = df.loc[1, 'course']
        
        return df
    
    def adjust_time(self, df: pd.DataFrame, offset_seconds: float) -> pd.DataFrame:
        """
        GPSデータの時間を調整する
        
        Parameters:
        -----------
        df : pd.DataFrame
            入力データ（timeカラムが必要）
        offset_seconds : float
            時間オフセット（秒）
            
        Returns:
        --------
        pd.DataFrame
            時間調整後のデータ
        """
        df_copy = df.copy()
        if 'time' in df_copy.columns:
            df_copy['time'] = df_copy['time'] + pd.Timedelta(seconds=offset_seconds)
        return df_copy
    
    def estimate_time_offset(self, df1: pd.DataFrame, df2: pd.DataFrame, max_offset: float = 300) -> float:
        """
        2つのGPSデータ間の時間オフセットを推定する
        
        Parameters:
        -----------
        df1, df2 : pd.DataFrame
            比較するGPSデータ
        max_offset : float
            最大オフセット（秒）
            
        Returns:
        --------
        float
            推定された時間オフセット（秒）
        """
        # コース相関に基づくオフセット推定
        correlations = []
        offsets = np.arange(-max_offset, max_offset + 1, 5)
        
        for offset in offsets:
            # df2の時間をオフセット
            df2_shifted = self.adjust_time(df2, offset)
            
            # 共通時間範囲でコース相関を計算
            merged = pd.merge_asof(
                df1.sort_values('time'),
                df2_shifted.sort_values('time'),
                on='time',
                direction='nearest',
                tolerance=pd.Timedelta('5s'),
                suffixes=('_1', '_2')
            )
            
            if len(merged) > 10:
                corr = merged['course_1'].corr(merged['course_2'])
                correlations.append(corr)
            else:
                correlations.append(0)
        
        # 最大相関を与えるオフセットを返す
        if correlations:
            best_offset_idx = np.argmax(correlations)
            return offsets[best_offset_idx]
        return 0
    
    def sync_boat_data(self) -> Dict[str, pd.DataFrame]:
        """
        複数艇のGPSデータを同期する
        
        Returns:
        --------
        Dict[str, pd.DataFrame]
            同期済みデータの辞書
        """
        if not self.boat_data:
            return {}
        
        # 基準艇を選択（データ点数が最も多い艇）
        reference_boat = max(self.boat_data.items(), key=lambda x: len(x[1]))[0]
        reference_df = self.boat_data[reference_boat]
        
        synced_data = {reference_boat: reference_df}
        
        # 他の艇のデータを基準艇に同期
        for boat_id, df in self.boat_data.items():
            if boat_id != reference_boat:
                offset = self.estimate_time_offset(reference_df, df)
                synced_data[boat_id] = self.adjust_time(df, offset)
        
        self.synced_data = synced_data
        return synced_data
    
    def synchronize_time(self, target_freq: str = '1s') -> Dict[str, pd.DataFrame]:
        """
        時間同期機能
        
        Parameters:
        -----------
        target_freq : str
            目標の時間間隔（デフォルト: 1秒）
            
        Returns:
        --------
        Dict[str, pd.DataFrame]
            同期済みデータの辞書
        """
        if not self.boat_data:
            return {}
        
        # 共通の時間範囲を見つける
        time_ranges = []
        for boat_id, df in self.boat_data.items():
            if 'timestamp' in df.columns:
                time_ranges.append((df['timestamp'].min(), df['timestamp'].max()))
            elif 'time' in df.columns:
                time_ranges.append((df['time'].min(), df['time'].max()))
        
        if not time_ranges:
            return {}
        
        # 共通の開始・終了時刻
        common_start = max(start for start, _ in time_ranges)
        common_end = min(end for _, end in time_ranges)
        
        # 共通の時間インデックスを作成
        time_index = pd.date_range(start=common_start, end=common_end, freq=target_freq)
        
        synced_data = {}
        for boat_id, df in self.boat_data.items():
            df_copy = df.copy()
            
            # timestampまたはtimeカラムを使用
            time_col = 'timestamp' if 'timestamp' in df.columns else 'time'
            df_copy = df_copy.set_index(time_col)
            
            # リサンプリングして同期
            synced_df = df_copy.resample(target_freq).mean()
            synced_df = synced_df.reindex(time_index)
            
            # インデックスを列に戻す
            synced_df.reset_index(inplace=True)
            synced_df.rename(columns={'index': 'timestamp'}, inplace=True)
            
            synced_data[boat_id] = synced_df
        
        self.synced_data = synced_data
        return synced_data
    
    def export_processed_data(self, boat_id: str, format_type: str = 'csv') -> Union[str, bytes]:
        """
        処理済みデータをエクスポートする
        
        Parameters:
        -----------
        boat_id : str
            艇の識別ID
        format_type : str
            エクスポート形式 ('csv' or 'json')
            
        Returns:
        --------
        Union[str, bytes]
            エクスポートしたデータ
        """
        if boat_id not in self.synced_data and boat_id not in self.boat_data:
            raise ValueError(f"Boat ID '{boat_id}' not found")
        
        # データソースの選択（同期済みデータ優先）
        df = self.synced_data.get(boat_id, self.boat_data.get(boat_id))
        
        if format_type == 'csv':
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            return csv_buffer.getvalue()
        
        elif format_type == 'json':
            return df.to_json(orient='records', date_format='iso')
        
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def cleanup(self):
        """メモリをクリーンアップする"""
        self.boat_data.clear()
        self.synced_data.clear()
        gc.collect()
