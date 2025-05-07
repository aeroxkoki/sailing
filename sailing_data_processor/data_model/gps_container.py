# -*- coding: utf-8 -*-
"""
sailing_data_processor.data_model.gps_container

GPSデータコンテナの実装を提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union
import numpy as np
import pandas as pd
import warnings
from datetime import datetime

from sailing_data_processor.data_model.base_container import DataContainer

class GPSDataContainer(DataContainer[pd.DataFrame]):
    """
    GPS位置データを格納するコンテナ
    
    Parameters
    ----------
    data : pd.DataFrame
        GPS位置データ（必須カラム: timestamp, latitude, longitude）
    metadata : Dict[str, Any], optional
        関連するメタデータ
    """
    
    def __init__(self, data: pd.DataFrame, metadata: Optional[Dict[str, Any]] = None):
        super().__init__(data, metadata)
        
        # データ型の検証
        if not isinstance(data, pd.DataFrame):
            raise TypeError("GPSデータはpd.DataFrame型である必要があります")
        
        # 必須カラムの検証
        self._validate_columns()
        
        # データの前処理
        self._preprocess_data()
    
    def _validate_columns(self) -> None:
        """必須カラムの検証"""
        required_columns = ['timestamp', 'latitude', 'longitude']
        missing_columns = [col for col in required_columns if col not in self._data.columns]
        
        if missing_columns:
            raise ValueError(f"必須カラムがありません: {', '.join(missing_columns)}")
    
    def _preprocess_data(self) -> None:
        """データの前処理"""
        # timestampがdatetime型でない場合は変換
        if not pd.api.types.is_datetime64_any_dtype(self._data['timestamp']):
            try:
                self._data['timestamp'] = pd.to_datetime(self._data['timestamp'])
            except Exception as e:
                warnings.warn(f"タイムスタンプ変換エラー: {e}")
        
        # 時間順にソート
        self._data = self._data.sort_values('timestamp').reset_index(drop=True)
        
        # メタデータに時間範囲を追加
        if len(self._data) > 0:
            self._metadata['time_range'] = {
                'start': self._data['timestamp'].min().isoformat(),
                'end': self._data['timestamp'].max().isoformat(),
                'duration_seconds': (self._data['timestamp'].max() - self._data['timestamp'].min()).total_seconds()
            }
    
    def validate(self) -> bool:
        """
        GPSデータの正当性を検証
        
        Returns
        -------
        bool
            検証結果（True: 正当、False: 不正）
        """
        if not super().validate():
            return False
        
        # データフレームが空でないか
        if len(self._data) == 0:
            return False
        
        # 必須カラムが存在するか
        try:
            self._validate_columns()
        except ValueError:
            return False
        
        # 緯度・経度の値域チェック
        lat_valid = (-90 <= self._data['latitude']).all() and (self._data['latitude'] <= 90).all()
        lon_valid = (-180 <= self._data['longitude']).all() and (self._data['longitude'] <= 180).all()
        
        return lat_valid and lon_valid
    
    def get_time_range(self) -> Dict[str, Any]:
        """
        データの時間範囲を取得
        
        Returns
        -------
        Dict[str, Any]
            開始時刻、終了時刻、期間（秒）を含む辞書
        """
        if 'time_range' in self._metadata:
            return self._metadata['time_range']
        
        if len(self._data) == 0:
            return {'start': None, 'end': None, 'duration_seconds': 0}
        
        return {
            'start': self._data['timestamp'].min().isoformat(),
            'end': self._data['timestamp'].max().isoformat(),
            'duration_seconds': (self._data['timestamp'].max() - self._data['timestamp'].min()).total_seconds()
        }
    
    def to_numpy(self) -> Dict[str, np.ndarray]:
        """
        NumPy配列に変換
        
        Returns
        -------
        Dict[str, np.ndarray]
            各カラムのNumPy配列を格納した辞書
        """
        result = {
            'timestamps': np.array([ts.timestamp() for ts in self._data['timestamp']]),
            'latitudes': self._data['latitude'].values,
            'longitudes': self._data['longitude'].values
        }
        
        # その他の数値カラムも追加
        for col in self._data.columns:
            if col not in ['timestamp', 'latitude', 'longitude'] and pd.api.types.is_numeric_dtype(self._data[col]):
                result[col] = self._data[col].values
        
        return result
    
    def filter_time_range(self, start_time: Union[datetime, str], end_time: Union[datetime, str]) -> 'GPSDataContainer':
        """
        時間範囲でフィルタリング
        
        Parameters
        ----------
        start_time : Union[datetime, str]
            開始時刻
        end_time : Union[datetime, str]
            終了時刻
            
        Returns
        -------
        GPSDataContainer
            フィルタリング後のデータコンテナ
        """
        # 文字列の場合はdatetimeに変換
        if isinstance(start_time, str):
            start_time = pd.to_datetime(start_time)
        if isinstance(end_time, str):
            end_time = pd.to_datetime(end_time)
        
        # 時間範囲でフィルタリング
        filtered_data = self._data[(self._data['timestamp'] >= start_time) & 
                                   (self._data['timestamp'] <= end_time)].copy()
        
        # 新しいメタデータを作成（元のメタデータをコピーして更新）
        new_metadata = self._metadata.copy()
        new_metadata['filtered_from'] = self.get_time_range()
        
        return GPSDataContainer(filtered_data, new_metadata)
    
    def resample(self, freq: str = '1S') -> 'GPSDataContainer':
        """
        データを一定間隔でリサンプリング
        
        Parameters
        ----------
        freq : str, optional
            リサンプリング間隔（デフォルト: '1S'=1秒）
            
        Returns
        -------
        GPSDataContainer
            リサンプリング後のデータコンテナ
        """
        # 時間インデックスに設定して一定間隔でリサンプリング
        df_indexed = self._data.set_index('timestamp')
        
        # 線形補間でリサンプリング
        resampled = df_indexed.resample(freq).interpolate(method='linear')
        
        # timestampカラムを復元
        resampled_df = resampled.reset_index()
        
        # 新しいメタデータを作成
        new_metadata = self._metadata.copy()
        new_metadata['resampled'] = {
            'original_points': len(self._data),
            'resampled_points': len(resampled_df),
            'frequency': freq
        }
        
        return GPSDataContainer(resampled_df, new_metadata)