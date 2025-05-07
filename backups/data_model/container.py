# -*- coding: utf-8 -*-
"""
sailing_data_processor.data_model.container

データコンテナの実装を提供するモジュール
"""

from typing import Dict, List, Any, Optional, TypeVar, Generic, Union, Callable
import numpy as np
import pandas as pd
import json
from datetime import datetime
import warnings
import hashlib
import functools  # これを追加

# 型変数の定義
T = TypeVar('T')

class DataContainer(Generic[T]):
    """
    すべてのデータコンテナの基底クラス
    
    Parameters
    ----------
    data : T
        格納するデータ
    metadata : Dict[str, Any], optional
        関連するメタデータ
    """
    def __init__(self, data: T, metadata: Optional[Dict[str, Any]] = None):
        self._data = data
        self._metadata = metadata or {}
        
        # データの作成・更新時刻を自動的に記録
        if 'created_at' not in self._metadata:
            self._metadata['created_at'] = datetime.now().isoformat()
        self._metadata['updated_at'] = datetime.now().isoformat()
        
    @property
    def data(self) -> T:
        """格納データへのアクセサ"""
        return self._data
    
    @data.setter
    def data(self, value: T) -> None:
        """データの更新"""
        self._data = value
        self._metadata['updated_at'] = datetime.now().isoformat()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """メタデータへのアクセサ"""
        return self._metadata
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        メタデータの追加
        
        Parameters
        ----------
        key : str
            メタデータのキー
        value : Any
            メタデータの値
        """
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        メタデータの取得
        
        Parameters
        ----------
        key : str
            メタデータのキー
        default : Any, optional
            キーが存在しない場合のデフォルト値
            
        Returns
        -------
        Any
            メタデータの値
        """
        return self._metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換
        
        Returns
        -------
        Dict[str, Any]
            データとメタデータを含む辞書
        """
        try:
            # データ部分をシリアライズ可能な形式に変換
            if isinstance(self._data, pd.DataFrame):
                data_dict = self._data.to_dict(orient='records')
            elif isinstance(self._data, np.ndarray):
                data_dict = self._data.tolist()
            else:
                data_dict = self._data
                
            return {
                'data': data_dict,
                'metadata': self._metadata,
                'type': self.__class__.__name__
            }
        except Exception as e:
            warnings.warn(f"辞書変換エラー: {e}")
            return {
                'data': str(self._data),
                'metadata': self._metadata,
                'type': self.__class__.__name__
            }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """
        JSON形式に変換
        
        Parameters
        ----------
        indent : int, optional
            JSONインデント（整形用）
            
        Returns
        -------
        str
            JSON文字列
        """
        try:
            return json.dumps(self.to_dict(), indent=indent, default=str)
        except Exception as e:
            warnings.warn(f"JSON変換エラー: {e}")
            return json.dumps({
                'error': str(e),
                'metadata': self._metadata,
                'type': self.__class__.__name__
            }, default=str)
    
    def apply(self, func: Callable[[T], T]) -> 'DataContainer[T]':
        """
        データに関数を適用
        
        Parameters
        ----------
        func : Callable[[T], T]
            データに適用する関数
            
        Returns
        -------
        DataContainer[T]
            処理後のコンテナ（自身のインスタンス）
        """
        try:
            self._data = func(self._data)
            self._metadata['updated_at'] = datetime.now().isoformat()
            self._metadata['processed_by'] = func.__name__
            return self
        except Exception as e:
            warnings.warn(f"データ処理エラー: {e}")
            return self
    
    def validate(self) -> bool:
        """
        データの正当性を検証
        
        Returns
        -------
        bool
            検証結果（True: 正当、False: 不正）
        """
        # 基底クラスでは最小限のチェックのみ
        return self._data is not None
    
    def get_hash(self) -> str:
        """
        データのハッシュ値を計算
        
        Returns
        -------
        str
            MD5ハッシュ値
        """
        hash_obj = hashlib.md5()
        
        try:
            # データのハッシュ計算
            if isinstance(self._data, pd.DataFrame):
                # DataFrameの各列を文字列化して結合
                for col in self._data.columns:
                    hash_obj.update(str(self._data[col].tolist()).encode('utf-8'))
            elif isinstance(self._data, np.ndarray):
                hash_obj.update(str(self._data.tolist()).encode('utf-8'))
            else:
                hash_obj.update(str(self._data).encode('utf-8'))
                
            return hash_obj.hexdigest()
        except Exception as e:
            warnings.warn(f"ハッシュ計算エラー: {e}")
            return hashlib.md5(str(id(self)).encode('utf-8')).hexdigest()
    
    def __str__(self) -> str:
        """文字列表現"""
        data_type = type(self._data).__name__
        meta_str = ', '.join(f"{k}: {v}" for k, v in list(self._metadata.items())[:3])
        if len(self._metadata) > 3:
            meta_str += f" ... ({len(self._metadata) - 3} more)"
        return f"{self.__class__.__name__}({data_type}, metadata={{{meta_str}}})"
    
    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return self.__str__()


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


class WindDataContainer(DataContainer[Dict[str, Any]]):
    """
    風向風速データを格納するコンテナ
    
    Parameters
    ----------
    data : Dict[str, Any]
        風データを格納した辞書
        必須キー: direction, speed, timestamp
    metadata : Dict[str, Any], optional
        関連するメタデータ
    """
    
    def __init__(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        super().__init__(data, metadata)
        
        # データ型の検証
        if not isinstance(data, dict):
            raise TypeError("風データはDict型である必要があります")
        
        # 必須キーの検証
        self._validate_keys()
    
    def _validate_keys(self) -> None:
        """必須キーの検証"""
        required_keys = ['direction', 'speed', 'timestamp']
        missing_keys = [key for key in required_keys if key not in self._data]
        
        if missing_keys:
            raise ValueError(f"必須キーがありません: {', '.join(missing_keys)}")
    
    def validate(self) -> bool:
        """
        風データの正当性を検証
        
        Returns
        -------
        bool
            検証結果（True: 正当、False: 不正）
        """
        if not super().validate():
            return False
        
        # 必須キーが存在するか
        try:
            self._validate_keys()
        except ValueError:
            return False
        
        # 値の範囲チェック
        direction_valid = 0 <= self._data.get('direction', 0) <= 360
        speed_valid = self._data.get('speed', -1) >= 0
        
        return direction_valid and speed_valid
    
    @property
    def direction(self) -> float:
        """風向（度、0-360）"""
        return self._data.get('direction', 0.0)
    
    @property
    def speed(self) -> float:
        """風速（ノット）"""
        return self._data.get('speed', 0.0)
    
    @property
    def timestamp(self) -> datetime:
        """タイムスタンプ"""
        ts = self._data.get('timestamp')
        if isinstance(ts, datetime):
            return ts
        elif isinstance(ts, str):
            return pd.to_datetime(ts)
        return datetime.now()
    
    @property
    def confidence(self) -> float:
        """信頼度（0-1）"""
        return self._data.get('confidence', 0.0)
    
    def to_vector(self) -> np.ndarray:
        """
        風向風速をベクトル形式に変換
        
        Returns
        -------
        np.ndarray
            風ベクトル [x, y] 
            x: 東西成分（東が正）
            y: 南北成分（北が正）
        """
        # 風向を数学的な角度（ラジアン）に変換
        # 気象学的風向: 北が0度、時計回り
        # 数学的角度: 東が0度、反時計回り
        direction_rad = np.radians((90 - self.direction) % 360)
        
        # 風速を考慮したベクトル
        x = self.speed * np.cos(direction_rad)
        y = self.speed * np.sin(direction_rad)
        
        return np.array([x, y])
    
    @classmethod
    def from_vector(cls, vector: np.ndarray, timestamp: Union[datetime, str], 
                   confidence: float = 0.0, metadata: Optional[Dict[str, Any]] = None) -> 'WindDataContainer':
        """
        ベクトルから風データコンテナを作成
        
        Parameters
        ----------
        vector : np.ndarray
            風ベクトル [x, y]
        timestamp : Union[datetime, str]
            タイムスタンプ
        confidence : float, optional
            信頼度（0-1）
        metadata : Dict[str, Any], optional
            メタデータ
            
        Returns
        -------
        WindDataContainer
            風データコンテナ
        """
        x, y = vector
        
        # ベクトルから風向風速に変換
        speed = np.sqrt(x**2 + y**2)
        direction_rad = np.arctan2(y, x)
        
        # ラジアンから気象学的風向に変換
        direction = (90 - np.degrees(direction_rad)) % 360
        
        # データの作成
        data = {
            'direction': float(direction),
            'speed': float(speed),
            'timestamp': timestamp,
            'confidence': confidence
        }
        
        return cls(data, metadata)


class StrategyPointContainer(DataContainer[Dict[str, Any]]):
    """
    戦略ポイントデータを格納するコンテナ
    
    Parameters
    ----------
    data : Dict[str, Any]
        戦略ポイントデータを格納した辞書
        必須キー: type, position, timestamp
    metadata : Dict[str, Any], optional
        関連するメタデータ
    """
    
    def __init__(self, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        super().__init__(data, metadata)
        
        # データ型の検証
        if not isinstance(data, dict):
            raise TypeError("戦略ポイントデータはDict型である必要があります")
        
        # 必須キーの検証
        self._validate_keys()
    
    def _validate_keys(self) -> None:
        """必須キーの検証"""
        required_keys = ['type', 'position', 'timestamp']
        missing_keys = [key for key in required_keys if key not in self._data]
        
        if missing_keys:
            raise ValueError(f"必須キーがありません: {', '.join(missing_keys)}")
        
        # positionの必須キー
        if isinstance(self._data.get('position'), dict):
            pos_required = ['latitude', 'longitude']
            pos_missing = [key for key in pos_required if key not in self._data['position']]
            
            if pos_missing:
                raise ValueError(f"位置情報に必須キーがありません: {', '.join(pos_missing)}")
    
    def validate(self) -> bool:
        """
        戦略ポイントデータの正当性を検証
        
        Returns
        -------
        bool
            検証結果（True: 正当、False: 不正）
        """
        if not super().validate():
            return False
        
        # 必須キーが存在するか
        try:
            self._validate_keys()
        except ValueError:
            return False
        
        # 値のチェック
        type_valid = self._data.get('type') in ['tack', 'jibe', 'layline', 'wind_shift', 'start', 'finish', 'mark', 'other']
        
        # 位置情報のチェック
        position = self._data.get('position', {})
        lat = position.get('latitude', 0)
        lon = position.get('longitude', 0)
        
        pos_valid = -90 <= lat <= 90 and -180 <= lon <= 180
        
        return type_valid and pos_valid
    
    @property
    def point_type(self) -> str:
        """ポイントタイプ"""
        return self._data.get('type', 'other')
    
    @property
    def latitude(self) -> float:
        """緯度"""
        position = self._data.get('position', {})
        return position.get('latitude', 0.0)
    
    @property
    def longitude(self) -> float:
        """経度"""
        position = self._data.get('position', {})
        return position.get('longitude', 0.0)
    
    @property
    def timestamp(self) -> datetime:
        """タイムスタンプ"""
        ts = self._data.get('timestamp')
        if isinstance(ts, datetime):
            return ts
        elif isinstance(ts, str):
            return pd.to_datetime(ts)
        return datetime.now()
    
    @property
    def importance(self) -> float:
        """重要度（0-1）"""
        return self._data.get('importance', 0.5)
    
    @classmethod
    def from_coordinates(cls, point_type: str, latitude: float, longitude: float, 
                        timestamp: Union[datetime, str], importance: float = 0.5,
                        details: Optional[Dict[str, Any]] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> 'StrategyPointContainer':
        """
        座標から戦略ポイントコンテナを作成
        
        Parameters
        ----------
        point_type : str
            ポイントタイプ
        latitude : float
            緯度
        longitude : float
            経度
        timestamp : Union[datetime, str]
            タイムスタンプ
        importance : float, optional
            重要度（0-1）
        details : Dict[str, Any], optional
            詳細情報
        metadata : Dict[str, Any], optional
            メタデータ
            
        Returns
        -------
        StrategyPointContainer
            戦略ポイントコンテナ
        """
        # データの作成
        data = {
            'type': point_type,
            'position': {
                'latitude': latitude,
                'longitude': longitude
            },
            'timestamp': timestamp,
            'importance': importance
        }
        
        # 詳細情報があれば追加
        if details:
            data['details'] = details
        
        return cls(data, metadata)
