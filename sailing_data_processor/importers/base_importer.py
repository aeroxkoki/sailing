"""
sailing_data_processor.importers.base_importer

GPSデータインポートの基底クラスを提供するモジュール
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
import pandas as pd
from pathlib import Path
import io
import os

from sailing_data_processor.data_model.container import GPSDataContainer


class BaseImporter(ABC):
    """
    GPSデータインポートの基底クラス
    
    このクラスを継承して、各種データフォーマット用のインポーターを実装します。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        config : Optional[Dict[str, Any]], optional
            インポーター設定
        """
        self.config = config or {}
        self.errors = []
        self.warnings = []
    
    @abstractmethod
    def can_import(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> bool:
        """
        ファイルがインポート可能かどうかを判定
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            インポート対象ファイルのパスまたはファイルオブジェクト
            
        Returns
        -------
        bool
            インポート可能な場合はTrue
        """
        pass
    
    @abstractmethod
    def import_data(self, file_path: Union[str, Path, BinaryIO, TextIO], 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[GPSDataContainer]:
        """
        データをインポート
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            インポート対象ファイルのパスまたはファイルオブジェクト
        metadata : Optional[Dict[str, Any]], optional
            メタデータ
            
        Returns
        -------
        Optional[GPSDataContainer]
            インポートしたデータのコンテナ（失敗した場合はNone）
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
    
    def clear_messages(self) -> None:
        """エラーメッセージと警告メッセージをクリア"""
        self.errors = []
        self.warnings = []
    
    def get_file_extension(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> str:
        """
        ファイルの拡張子を取得
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            ファイルパスまたはファイルオブジェクト
            
        Returns
        -------
        str
            拡張子（ピリオドなし、小文字）
        """
        if isinstance(file_path, (str, Path)):
            return os.path.splitext(str(file_path))[1].lower().lstrip('.')
        elif hasattr(file_path, 'name'):
            return os.path.splitext(getattr(file_path, 'name'))[1].lower().lstrip('.')
        return ""
    
    def get_file_name(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> str:
        """
        ファイル名を取得
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            ファイルパスまたはファイルオブジェクト
            
        Returns
        -------
        str
            ファイル名（拡張子を除く）
        """
        if isinstance(file_path, (str, Path)):
            return os.path.splitext(os.path.basename(str(file_path)))[0]
        elif hasattr(file_path, 'name'):
            return os.path.splitext(os.path.basename(getattr(file_path, 'name')))[0]
        return "unnamed"
    
    def validate_dataframe(self, df: pd.DataFrame) -> bool:
        """
        DataFrameに必要な列があるかを検証
        
        Parameters
        ----------
        df : pd.DataFrame
            検証するDataFrame
            
        Returns
        -------
        bool
            検証結果
        """
        required_columns = ['timestamp', 'latitude', 'longitude']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            self.errors.append(f"必須列がありません: {', '.join(missing_columns)}")
            return False
        
        return True
