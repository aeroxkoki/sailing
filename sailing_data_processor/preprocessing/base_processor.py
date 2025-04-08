"""
sailing_data_processor.preprocessing.base_processor

データ前処理の基底クラスを提供するモジュール
"""

from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer, DataContainer


class BaseProcessor(ABC):
    """
    データ前処理の基底クラス
    
    Parameters
    ----------
    name : str
        処理の名前
    description : str
        処理の説明
    config : Dict[str, Any], optional
        設定パラメータ
    """
    
    def __init__(self, name: str, description: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.config = config or {}
        self.errors = []
        self.warnings = []
        self.info = []
    
    @abstractmethod
    def process(self, container: DataContainer) -> DataContainer:
        """
        データを処理
        
        Parameters
        ----------
        container : DataContainer
            処理するデータコンテナ
            
        Returns
        -------
        DataContainer
            処理後のデータコンテナ
        """
        pass
    
    def get_errors(self) -> List[str]:
        """
        エラーメッセージを取得
        
        Returns
        -------
        List[str]
            発生したエラーメッセージのリスト
        """
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """
        警告メッセージを取得
        
        Returns
        -------
        List[str]
            発生した警告メッセージのリスト
        """
        return self.warnings
    
    def get_info(self) -> List[str]:
        """
        情報メッセージを取得
        
        Returns
        -------
        List[str]
            発生した情報メッセージのリスト
        """
        return self.info
    
    def clear_messages(self) -> None:
        """メッセージをクリア"""
        self.errors = []
        self.warnings = []
        self.info = []
    
    def can_process(self, container: DataContainer) -> bool:
        """
        処理可能かどうかを判定
        
        Parameters
        ----------
        container : DataContainer
            判定するデータコンテナ
            
        Returns
        -------
        bool
            処理可能な場合はTrue
        """
        # デフォルトでは常にTrue、子クラスでオーバーライド可能
        return True
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.name}: {self.description}"


class GPSProcessor(BaseProcessor):
    """
    GPS位置データ専用の前処理基底クラス
    
    Parameters
    ----------
    name : str
        処理の名前
    description : str
        処理の説明
    config : Dict[str, Any], optional
        設定パラメータ
    """
    
    def can_process(self, container: DataContainer) -> bool:
        """
        処理可能かどうかを判定
        
        Parameters
        ----------
        container : DataContainer
            判定するデータコンテナ
            
        Returns
        -------
        bool
            処理可能な場合はTrue
        """
        return isinstance(container, GPSDataContainer)
    
    def process(self, container: DataContainer) -> DataContainer:
        """
        データを処理
        
        Parameters
        ----------
        container : DataContainer
            処理するデータコンテナ
            
        Returns
        -------
        DataContainer
            処理後のデータコンテナ
        """
        if not self.can_process(container):
            self.errors.append(f"{self.name}はGPSDataContainerのみ処理可能です")
            return container
        
        return self._process_gps(container)
    
    @abstractmethod
    def _process_gps(self, container: GPSDataContainer) -> GPSDataContainer:
        """
        GPS位置データを処理
        
        Parameters
        ----------
        container : GPSDataContainer
            処理するGPSデータコンテナ
            
        Returns
        -------
        GPSDataContainer
            処理後のGPSデータコンテナ
        """
        pass
