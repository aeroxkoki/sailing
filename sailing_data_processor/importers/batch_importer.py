# -*- coding: utf-8 -*-
"""
sailing_data_processor.importers.batch_importer

複数ファイルの一括インポートを行うバッチインポーターの実装
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO, Tuple
from pathlib import Path
import pandas as pd
import os
import tempfile
import shutil
import concurrent.futures
from tqdm import tqdm

from .importer_factory import ImporterFactory
from sailing_data_processor.data_model.container import GPSDataContainer


class BatchImportResult:
    """
    バッチインポート結果を格納するクラス
    
    Parameters
    ----------
    successful : Dict[str, GPSDataContainer]
        正常にインポートできたファイルとそのコンテナのマッピング
    failed : Dict[str, List[str]]
        インポートに失敗したファイルとエラーメッセージのマッピング
    warnings : Dict[str, List[str]]
        警告が発生したファイルと警告メッセージのマッピング
    """
    
    def __init__(self):
        """初期化"""
        self.successful: Dict[str, GPSDataContainer] = {}
        self.failed: Dict[str, List[str]] = {}
        self.warnings: Dict[str, List[str]] = {}
    
    def add_success(self, file_name: str, container: GPSDataContainer) -> None:
        """
        正常にインポートできたファイルを追加
        
        Parameters
        ----------
        file_name : str
            ファイル名
        container : GPSDataContainer
            インポートしたデータコンテナ
        """
        self.successful[file_name] = container
    
    def add_failure(self, file_name: str, errors: List[str]) -> None:
        """
        インポートに失敗したファイルを追加
        
        Parameters
        ----------
        file_name : str
            ファイル名
        errors : List[str]
            エラーメッセージのリスト
        """
        self.failed[file_name] = errors
    
    def add_warning(self, file_name: str, warnings: List[str]) -> None:
        """
        警告が発生したファイルを追加
        
        Parameters
        ----------
        file_name : str
            ファイル名
        warnings : List[str]
            警告メッセージのリスト
        """
        self.warnings[file_name] = warnings
    
    def get_summary(self) -> Dict[str, Any]:
        """
        結果サマリーを取得
        
        Returns
        -------
        Dict[str, Any]
            サマリー情報
        """
        return {
            "total_files": len(self.successful) + len(self.failed),
            "successful_count": len(self.successful),
            "failed_count": len(self.failed),
            "warning_count": len(self.warnings),
            "successful_files": list(self.successful.keys()),
            "failed_files": list(self.failed.keys()),
            "warning_files": list(self.warnings.keys())
        }
    
    def merge_containers(self) -> Optional[GPSDataContainer]:
        """
        すべての成功したコンテナを結合
        
        Returns
        -------
        Optional[GPSDataContainer]
            結合されたコンテナ（データがない場合はNone）
        """
        if not self.successful:
            return None
        
        # すべてのDataFrameを結合
        dfs = [container.data for container in self.successful.values()]
        merged_df = pd.concat(dfs, ignore_index=True).sort_values('timestamp').reset_index(drop=True)
        
        # メタデータの結合
        merged_metadata = {
            "source_files": list(self.successful.keys()),
            "batch_import": True,
            "original_containers": len(self.successful)
        }
        
        # 共通メタデータの継承
        first_container = next(iter(self.successful.values()))
        for key, value in first_container.metadata.items():
            if key not in ['created_at', 'updated_at', 'time_range']:
                merged_metadata[key] = value
        
        return GPSDataContainer(merged_df, merged_metadata)


class BatchImporter:
    """
    複数ファイルの一括インポートを行うバッチインポーター
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        config : Optional[Dict[str, Any]], optional
            バッチインポート設定
        """
        self.config = config or {}
        self.parallel = self.config.get('parallel', True)  # デフォルトで並列処理を有効化
        self.max_workers = self.config.get('max_workers', 4)  # デフォルトの並列ワーカー数
    
    def import_files(self, file_paths: List[Union[str, Path, BinaryIO, TextIO]],
                    metadata: Optional[Dict[str, Any]] = None) -> BatchImportResult:
        """
        複数ファイルをインポート
        
        Parameters
        ----------
        file_paths : List[Union[str, Path, BinaryIO, TextIO]]
            インポート対象ファイルのパスまたはファイルオブジェクトのリスト
        metadata : Optional[Dict[str, Any]], optional
            共通メタデータ
            
        Returns
        -------
        BatchImportResult
            インポート結果
        """
        result = BatchImportResult()
        
        # ファイルが存在しない場合は空の結果を返す
        if not file_paths:
            return result
        
        # メタデータの準備
        metadata = metadata or {}
        metadata['batch_import'] = True
        
        # 並列処理の場合
        if self.parallel and len(file_paths) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(self._import_single_file, file_path, metadata): file_path
                    for file_path in file_paths
                }
                
                for future in tqdm(concurrent.futures.as_completed(future_to_file), 
                                  total=len(file_paths), 
                                  desc="インポート中"):
                    file_path = future_to_file[future]
                    try:
                        file_name, container, errors, warnings = future.result()
                        
                        if container:
                            result.add_success(file_name, container)
                        
                        if errors:
                            result.add_failure(file_name, errors)
                        
                        if warnings:
                            result.add_warning(file_name, warnings)
                    
                    except Exception as e:
                        file_name = self._get_file_name(file_path)
                        result.add_failure(file_name, [f"インポート中に例外が発生: {str(e)}"])
        
        # 逐次処理の場合
        else:
            for file_path in tqdm(file_paths, desc="インポート中"):
                try:
                    file_name, container, errors, warnings = self._import_single_file(file_path, metadata)
                    
                    if container:
                        result.add_success(file_name, container)
                    
                    if errors:
                        result.add_failure(file_name, errors)
                    
                    if warnings:
                        result.add_warning(file_name, warnings)
                
                except Exception as e:
                    file_name = self._get_file_name(file_path)
                    result.add_failure(file_name, [f"インポート中に例外が発生: {str(e)}"])
        
        return result
    
    def _import_single_file(self, file_path: Union[str, Path, BinaryIO, TextIO],
                           metadata: Dict[str, Any]) -> Tuple[str, Optional[GPSDataContainer], List[str], List[str]]:
        """
        単一ファイルをインポート
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            インポート対象ファイルのパスまたはファイルオブジェクト
        metadata : Dict[str, Any]
            メタデータ
            
        Returns
        -------
        Tuple[str, Optional[GPSDataContainer], List[str], List[str]]
            (ファイル名, コンテナ, エラーリスト, 警告リスト)のタプル
        """
        file_name = self._get_file_name(file_path)
        
        # 適切なインポーターを取得
        importer = ImporterFactory.get_importer(file_path, self.config)
        
        if not importer:
            return file_name, None, [f"サポートされていないファイル形式: {file_name}"], []
        
        # メタデータの拡張
        file_metadata = metadata.copy()
        file_metadata['source_file'] = file_name
        
        # インポート実行
        container = importer.import_data(file_path, file_metadata)
        errors = importer.get_errors()
        warnings = importer.get_warnings()
        
        return file_name, container, errors, warnings
    
    def _get_file_name(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> str:
        """
        ファイル名を取得
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            ファイルパスまたはファイルオブジェクト
            
        Returns
        -------
        str
            ファイル名
        """
        if isinstance(file_path, (str, Path)):
            return os.path.basename(str(file_path))
        elif hasattr(file_path, 'name'):
            return os.path.basename(getattr(file_path, 'name'))
        return "unnamed_file"
