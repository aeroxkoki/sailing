# -*- coding: utf-8 -*-
"""
sailing_data_processor.data_model.base_container

データコンテナの基底クラスの実装を提供するモジュール
"""

from typing import Dict, List, Any, Optional, TypeVar, Generic, Union, Callable
import numpy as np
import pandas as pd
import json
from datetime import datetime
import warnings
import hashlib
import functools

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