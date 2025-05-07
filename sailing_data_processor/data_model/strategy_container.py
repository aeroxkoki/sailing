# -*- coding: utf-8 -*-
"""
sailing_data_processor.data_model.strategy_container

戦略ポイントデータコンテナの実装を提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
from datetime import datetime

from sailing_data_processor.data_model.base_container import DataContainer

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