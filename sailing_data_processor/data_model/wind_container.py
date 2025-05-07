# -*- coding: utf-8 -*-
"""
sailing_data_processor.data_model.wind_container

風向風速データコンテナの実装を提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union
import numpy as np
import pandas as pd
from datetime import datetime

from sailing_data_processor.data_model.base_container import DataContainer

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