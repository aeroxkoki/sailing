"""
sailing_data_processor.importers.optimized_batch_importer

最適化された複数ファイルの一括インポートを行うバッチインポーター
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO, Tuple, Callable
from pathlib import Path
import pandas as pd
import os
import tempfile
import shutil
import concurrent.futures
import time
import psutil
import gc
import logging
from tqdm import tqdm

from .importer_factory import ImporterFactory
from .base_importer import BaseImporter
from sailing_data_processor.data_model.container import GPSDataContainer


# ロガーの設定
logger = logging.getLogger(__name__)


class BatchProcessStatus:
    """
    バッチ処理の進捗状況を管理するクラス
    
    Parameters
    ----------
    total_files : int
        処理するファイルの総数
    """
    
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.processed_files = 0
        self.successful_count = 0
        self.failed_count = 0
        self.warning_count = 0
        self.start_time = time.time()
        self.processing_files = set()
    
    def start_file(self, file_name: str) -> None:
        """
        ファイル処理の開始を記録
        
        Parameters
        ----------
        file_name : str
            処理を開始するファイル名
        """
        self.processing_files.add(file_name)
    
    def complete_file(self, file_name: str, success: bool, has_warnings: bool) -> None:
        """
        ファイル処理の完了を記録
        
        Parameters
        ----------
        file_name : str
            処理が完了したファイル名
        success : bool
            処理が成功したかどうか
        has_warnings : bool
            警告があったかどうか
        """
        self.processed_files += 1
        if success:
            self.successful_count += 1
        else:
            self.failed_count += 1
        if has_warnings:
            self.warning_count += 1
        
        if file_name in self.processing_files:
            self.processing_files.remove(file_name)
    
    def get_progress(self) -> Dict[str, Any]:
        """
        現在の進捗状況を取得
        
        Returns
        -------
        Dict[str, Any]
            進捗情報を含む辞書
        """
        elapsed_time = time.time() - self.start_time
        
        # 平均処理速度（ファイル/秒）
        if elapsed_time > 0:
            files_per_second = self.processed_files / elapsed_time
        else:
            files_per_second = 0
        
        # 残り時間の推定（秒）
        remaining_files = self.total_files - self.processed_files
        if files_per_second > 0:
            eta = remaining_files / files_per_second
        else:
            eta = 0
        
        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "successful_count": self.successful_count,
            "failed_count": self.failed_count,
            "warning_count": self.warning_count,
            "progress_percent": (self.processed_files / self.total_files * 100) if self.total_files > 0 else 0,
            "elapsed_time": elapsed_time,
            "files_per_second": files_per_second,
            "eta": eta,
            "processing_files": list(self.processing_files)
        }


class OptimizedBatchImportResult:
    """
    最適化されたバッチインポート結果を格納するクラス
    
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
        self.performance_metrics: Dict[str, Any] = {}
    
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
    
    def set_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        パフォーマンスメトリクスを設定
        
        Parameters
        ----------
        metrics : Dict[str, Any]
            パフォーマンスメトリクス
        """
        self.performance_metrics = metrics
    
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
            "warning_files": list(self.warnings.keys()),
            "performance_metrics": self.performance_metrics
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
        
        # メモリ効率の良い処理のために分割してマージ
        merged_df = None
        chunk_size = 5  # 一度に結合するコンテナの数
        
        try:
            # コンテナリストを取得
            containers = list(self.successful.values())
            
            # チャンクに分割して処理
            for i in range(0, len(containers), chunk_size):
                chunk = containers[i:i+chunk_size]
                
                # チャンク内のDataFrameを結合
                chunk_dfs = [container.data for container in chunk]
                chunk_df = pd.concat(chunk_dfs, ignore_index=True)
                
                # 結合結果にマージ
                if merged_df is None:
                    merged_df = chunk_df
                else:
                    merged_df = pd.concat([merged_df, chunk_df], ignore_index=True)
                
                # 使わなくなった変数をクリアしてメモリを解放
                del chunk_dfs
                del chunk_df
                gc.collect()
            
            # 時間順にソート
            if merged_df is not None:
                merged_df = merged_df.sort_values('timestamp').reset_index(drop=True)
            
            # メタデータの結合
            merged_metadata = {
                "source_files": list(self.successful.keys()),
                "batch_import": True,
                "original_containers": len(self.successful)
            }
            
            # 共通メタデータの継承
            if self.successful:
                first_container = next(iter(self.successful.values()))
                for key, value in first_container.metadata.items():
                    if key not in ['created_at', 'updated_at', 'time_range']:
                        merged_metadata[key] = value
            
            return GPSDataContainer(merged_df, merged_metadata)
        
        except MemoryError:
            # メモリエラーが発生した場合はログに記録
            logger.error("メモリ不足エラーが発生しました。結合処理を中止します。")
            return None
        except Exception as e:
            logger.error(f"コンテナ結合中にエラーが発生しました: {e}")
            return None


class OptimizedBatchImporter:
    """
    最適化された複数ファイルの一括インポートを行うバッチインポーター
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
        self.max_memory_percent = self.config.get('max_memory_percent', 80)  # 最大メモリ使用率（%）
        self.chunk_size = self.config.get('chunk_size', 10)  # 一度に処理するファイル数
        self.auto_adaptive = self.config.get('auto_adaptive', True)  # 自動適応モード
        self.progress_callback = self.config.get('progress_callback')  # 進捗コールバック
    
    def import_files(self, file_paths: List[Union[str, Path, BinaryIO, TextIO]],
                    metadata: Optional[Dict[str, Any]] = None,
                    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> OptimizedBatchImportResult:
        """
        複数ファイルをインポート
        
        Parameters
        ----------
        file_paths : List[Union[str, Path, BinaryIO, TextIO]]
            インポート対象ファイルのパスまたはファイルオブジェクトのリスト
        metadata : Optional[Dict[str, Any]], optional
            共通メタデータ
        progress_callback : Optional[Callable[[Dict[str, Any]], None]], optional
            進捗状況を受け取るコールバック関数
            
        Returns
        -------
        OptimizedBatchImportResult
            インポート結果
        """
        # 進捗コールバックの設定
        if progress_callback:
            self.progress_callback = progress_callback
        
        result = OptimizedBatchImportResult()
        
        # ファイルが存在しない場合は空の結果を返す
        if not file_paths:
            return result
        
        # 処理開始時間
        start_time = time.time()
        
        # メタデータの準備
        metadata = metadata or {}
        metadata['batch_import'] = True
        
        # 進捗状況の初期化
        status = BatchProcessStatus(len(file_paths))
        
        # 現在のシステムリソース状況を確認
        init_memory_percent = psutil.virtual_memory().percent
        cpu_count = psutil.cpu_count()
        
        # 自動適応モードの場合、システムリソースに基づいてパラメータを調整
        if self.auto_adaptive:
            # 利用可能なメモリに基づいて並列ワーカー数を調整
            available_memory_percent = self.max_memory_percent - init_memory_percent
            
            if available_memory_percent < 20:
                # メモリが少ない場合は並列処理を無効化
                self.parallel = False
                logger.warning("メモリ使用率が高いため、並列処理を無効化します")
            elif available_memory_percent < 40:
                # メモリが中程度の場合はワーカー数を制限
                self.max_workers = min(2, cpu_count)
                logger.info(f"メモリ使用率に基づき、ワーカー数を {self.max_workers} に制限します")
            else:
                # メモリが十分ある場合はCPUコア数に基づいてワーカー数を設定
                self.max_workers = min(cpu_count, self.max_workers)
        
        # 初期パフォーマンスメトリクスを記録
        performance_metrics = {
            "start_time": start_time,
            "initial_memory_percent": init_memory_percent,
            "cpu_count": cpu_count,
            "parallel_enabled": self.parallel,
            "max_workers": self.max_workers,
            "max_memory_percent": self.max_memory_percent,
            "file_count": len(file_paths),
            "memory_usage": []
        }
        
        # ファイルをチャンクに分割
        file_chunks = [file_paths[i:i+self.chunk_size] for i in range(0, len(file_paths), self.chunk_size)]
        
        try:
            # チャンクごとに処理
            for chunk_index, chunk in enumerate(file_chunks):
                # メモリ使用状況を記録
                current_memory_percent = psutil.virtual_memory().percent
                performance_metrics["memory_usage"].append(current_memory_percent)
                
                # メモリ使用率が上限を超えている場合は一時停止して整理
                if current_memory_percent > self.max_memory_percent:
                    logger.warning(f"メモリ使用率が高いため ({current_memory_percent}%)、ガベージコレクションを実行します")
                    gc.collect()
                    time.sleep(1)  # 少し待ってリソースを解放
                
                # 進捗状況の更新と通知
                progress = status.get_progress()
                progress["current_chunk"] = chunk_index + 1
                progress["total_chunks"] = len(file_chunks)
                
                if self.progress_callback:
                    self.progress_callback(progress)
                
                # 並列処理の場合
                if self.parallel and len(chunk) > 1:
                    self._process_chunk_parallel(chunk, metadata, result, status)
                else:
                    # 逐次処理の場合
                    self._process_chunk_sequential(chunk, metadata, result, status)
                
                # 中間メモリ整理
                gc.collect()
        
        except Exception as e:
            logger.error(f"バッチインポート中にエラーが発生しました: {e}")
            # 未処理のファイルを失敗としてマーク
            remaining_files = [f for f in file_paths if self._get_file_name(f) not in result.successful and self._get_file_name(f) not in result.failed]
            for file in remaining_files:
                file_name = self._get_file_name(file)
                result.add_failure(file_name, [f"バッチ処理エラーにより処理されませんでした: {e}"])
        
        finally:
            # 最終のパフォーマンスメトリクスを記録
            performance_metrics["end_time"] = time.time()
            performance_metrics["total_duration"] = performance_metrics["end_time"] - performance_metrics["start_time"]
            performance_metrics["files_per_second"] = len(file_paths) / performance_metrics["total_duration"] if performance_metrics["total_duration"] > 0 else 0
            performance_metrics["final_memory_percent"] = psutil.virtual_memory().percent
            performance_metrics["peak_memory_percent"] = max(performance_metrics["memory_usage"]) if performance_metrics["memory_usage"] else 0
            
            # 結果にパフォーマンスメトリクスを設定
            result.set_performance_metrics(performance_metrics)
            
            # 最終進捗状況の通知
            if self.progress_callback:
                self.progress_callback(status.get_progress())
        
        return result
    
    def _process_chunk_parallel(self, chunk: List[Union[str, Path, BinaryIO, TextIO]],
                               metadata: Dict[str, Any],
                               result: OptimizedBatchImportResult,
                               status: BatchProcessStatus) -> None:
        """
        チャンクを並列処理
        
        Parameters
        ----------
        chunk : List[Union[str, Path, BinaryIO, TextIO]]
            処理するファイルのチャンク
        metadata : Dict[str, Any]
            メタデータ
        result : OptimizedBatchImportResult
            結果オブジェクト
        status : BatchProcessStatus
            処理状態
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {}
            
            # 各ファイルの処理を投入
            for file_path in chunk:
                file_name = self._get_file_name(file_path)
                status.start_file(file_name)
                
                future = executor.submit(self._import_single_file, file_path, metadata)
                future_to_file[future] = (file_path, file_name)
            
            # 結果を収集
            for future in concurrent.futures.as_completed(future_to_file):
                file_path, file_name = future_to_file[future]
                
                try:
                    container, errors, warnings = future.result()
                    
                    if container:
                        result.add_success(file_name, container)
                        status.complete_file(file_name, True, bool(warnings))
                    else:
                        result.add_failure(file_name, errors)
                        status.complete_file(file_name, False, bool(warnings))
                    
                    if warnings:
                        result.add_warning(file_name, warnings)
                
                except Exception as e:
                    logger.error(f"ファイル {file_name} の処理中にエラーが発生: {e}")
                    result.add_failure(file_name, [f"処理中に例外が発生: {str(e)}"])
                    status.complete_file(file_name, False, False)
                
                # 進捗状況の通知
                if self.progress_callback:
                    self.progress_callback(status.get_progress())
    
    def _process_chunk_sequential(self, chunk: List[Union[str, Path, BinaryIO, TextIO]],
                                 metadata: Dict[str, Any],
                                 result: OptimizedBatchImportResult,
                                 status: BatchProcessStatus) -> None:
        """
        チャンクを逐次処理
        
        Parameters
        ----------
        chunk : List[Union[str, Path, BinaryIO, TextIO]]
            処理するファイルのチャンク
        metadata : Dict[str, Any]
            メタデータ
        result : OptimizedBatchImportResult
            結果オブジェクト
        status : BatchProcessStatus
            処理状態
        """
        for file_path in chunk:
            file_name = self._get_file_name(file_path)
            status.start_file(file_name)
            
            try:
                container, errors, warnings = self._import_single_file(file_path, metadata)
                
                if container:
                    result.add_success(file_name, container)
                    status.complete_file(file_name, True, bool(warnings))
                else:
                    result.add_failure(file_name, errors)
                    status.complete_file(file_name, False, bool(warnings))
                
                if warnings:
                    result.add_warning(file_name, warnings)
            
            except Exception as e:
                logger.error(f"ファイル {file_name} の処理中にエラーが発生: {e}")
                result.add_failure(file_name, [f"処理中に例外が発生: {str(e)}"])
                status.complete_file(file_name, False, False)
            
            # 進捗状況の通知
            if self.progress_callback:
                self.progress_callback(status.get_progress())
    
    def _import_single_file(self, file_path: Union[str, Path, BinaryIO, TextIO],
                           metadata: Dict[str, Any]) -> Tuple[Optional[GPSDataContainer], List[str], List[str]]:
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
        Tuple[Optional[GPSDataContainer], List[str], List[str]]
            (コンテナ, エラーリスト, 警告リスト)のタプル
        """
        # 適切なインポーターを取得
        file_extension = self._get_file_extension(file_path).lower()
        importer = self._get_importer_for_extension(file_extension)
        
        if not importer:
            # ファクトリーを使用して自動検出
            importer = ImporterFactory.get_importer(file_path, self.config)
        
        if not importer:
            return None, [f"サポートされていないファイル形式: {file_path}"], []
        
        # メタデータの拡張
        file_metadata = metadata.copy()
        file_name = self._get_file_name(file_path)
        file_metadata['source_file'] = file_name
        
        # インポート実行
        container = importer.import_data(file_path, file_metadata)
        errors = importer.get_errors()
        warnings = importer.get_warnings()
        
        return container, errors, warnings
    
    def _get_importer_for_extension(self, extension: str) -> Optional[BaseImporter]:
        """
        拡張子に基づいてインポーターを取得
        
        Parameters
        ----------
        extension : str
            ファイル拡張子
            
        Returns
        -------
        Optional[BaseImporter]
            インポーターのインスタンス（対応するものがなければNone）
        """
        # 拡張子に応じたインポーター設定
        extension_to_importer = {
            'csv': 'csv',
            'gpx': 'gpx',
            'tcx': 'tcx',
            'fit': 'fit'
        }
        
        importer_type = extension_to_importer.get(extension)
        if not importer_type:
            return None
        
        # 対応するインポーターの設定を取得
        config = self.config.get(extension, {})
        
        # インポーターを作成
        try:
            return ImporterFactory.get_importer_by_name(importer_type, config)
        except Exception:
            return None
    
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
    
    def _get_file_extension(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> str:
        """
        ファイル拡張子を取得
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            ファイルパスまたはファイルオブジェクト
            
        Returns
        -------
        str
            拡張子（ピリオドなし）
        """
        if isinstance(file_path, (str, Path)):
            return os.path.splitext(str(file_path))[1].lower().lstrip('.')
        elif hasattr(file_path, 'name'):
            return os.path.splitext(getattr(file_path, 'name'))[1].lower().lstrip('.')
        return ""
