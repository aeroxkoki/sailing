# -*- coding: utf-8 -*-
"""
sailing_data_processor.importers.importer_factory

ファイル形式に応じたインポーターを作成するファクトリークラス
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO, Type
from pathlib import Path

from .base_importer import BaseImporter
from .csv_importer import CSVImporter
from .gpx_importer import GPXImporter
from .tcx_importer import TCXImporter
from .fit_importer import FITImporter


class ImporterFactory:
    """
    ファイル形式に応じたインポーターを作成するファクトリークラス
    """
    
    # 登録されたインポーター
    _importers: Dict[str, Type[BaseImporter]] = {}
    
    @classmethod
    def register_importer(cls, name: str, importer_class: Type[BaseImporter]) -> None:
        """
        インポーターを登録
        
        Parameters
        ----------
        name : str
            インポーター名
        importer_class : Type[BaseImporter]
            インポータークラス
        """
        cls._importers[name] = importer_class
    
    @classmethod
    def get_importer(cls, file_path: Union[str, Path, BinaryIO, TextIO], 
                    config: Optional[Dict[str, Any]] = None) -> Optional[BaseImporter]:
        """
        ファイル形式に応じたインポーターを取得
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            インポート対象ファイルのパスまたはファイルオブジェクト
        config : Optional[Dict[str, Any]], optional
            インポーター設定
            
        Returns
        -------
        Optional[BaseImporter]
            適切なインポーターのインスタンス（見つからない場合はNone）
        """
        # 各インポーターで試す
        for importer_class in cls._importers.values():
            importer = importer_class(config)
            if importer.can_import(file_path):
                return importer
        
        # 対応するインポーターが見つからない場合
        return None
    
    @classmethod
    def get_all_importers(cls, config: Optional[Dict[str, Any]] = None) -> List[BaseImporter]:
        """
        すべての登録済みインポーターを取得
        
        Parameters
        ----------
        config : Optional[Dict[str, Any]], optional
            インポーター設定
            
        Returns
        -------
        List[BaseImporter]
            インポーターのリスト
        """
        return [importer_class(config) for importer_class in cls._importers.values()]
    
    @classmethod
    def get_supported_formats(cls) -> List[str]:
        """
        サポートしているファイル形式を取得
        
        Returns
        -------
        List[str]
            サポートしているファイル形式のリスト
        """
        return list(cls._importers.keys())


# デフォルトのインポーターを登録
ImporterFactory.register_importer('csv', CSVImporter)
ImporterFactory.register_importer('gpx', GPXImporter)
ImporterFactory.register_importer('tcx', TCXImporter)
ImporterFactory.register_importer('fit', FITImporter)
