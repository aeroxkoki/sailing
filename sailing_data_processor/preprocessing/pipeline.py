"""
sailing_data_processor.preprocessing.pipeline

データ前処理パイプラインの実装
"""

from typing import Dict, List, Any, Optional, Callable, Tuple, Set, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import DataContainer, GPSDataContainer
from .base_processor import BaseProcessor


class ProcessingPipeline:
    """
    データ前処理パイプライン
    
    Parameters
    ----------
    name : str
        パイプライン名
    description : str, optional
        パイプラインの説明
    processors : List[BaseProcessor], optional
        パイプラインに追加する前処理プロセッサのリスト
    config : Dict[str, Any], optional
        設定パラメータ
    """
    
    def __init__(self, name: str, description: str = "", 
                 processors: Optional[List[BaseProcessor]] = None,
                 config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.processors = processors or []
        self.config = config or {}
        self.errors = []
        self.warnings = []
        self.info = []
        self.processing_history = []
    
    def add_processor(self, processor: BaseProcessor) -> None:
        """
        プロセッサを追加
        
        Parameters
        ----------
        processor : BaseProcessor
            追加する前処理プロセッサ
        """
        self.processors.append(processor)
    
    def remove_processor(self, index: int) -> Optional[BaseProcessor]:
        """
        プロセッサを削除
        
        Parameters
        ----------
        index : int
            削除するプロセッサのインデックス
            
        Returns
        -------
        Optional[BaseProcessor]
            削除されたプロセッサ（存在しない場合はNone）
        """
        if 0 <= index < len(self.processors):
            return self.processors.pop(index)
        return None
    
    def clear_processors(self) -> None:
        """プロセッサをすべて削除"""
        self.processors = []
    
    def reorder_processors(self, new_order: List[int]) -> bool:
        """
        プロセッサの順序を変更
        
        Parameters
        ----------
        new_order : List[int]
            新しい順序を表すインデックスリスト
            
        Returns
        -------
        bool
            成功した場合はTrue
        """
        if len(new_order) != len(self.processors):
            return False
        
        try:
            # 新しい順序で処理器を並べ替え
            new_processors = [self.processors[i] for i in new_order]
            self.processors = new_processors
            return True
        except IndexError:
            return False
    
    def get_processor(self, index: int) -> Optional[BaseProcessor]:
        """
        指定したインデックスのプロセッサを取得
        
        Parameters
        ----------
        index : int
            プロセッサのインデックス
            
        Returns
        -------
        Optional[BaseProcessor]
            指定したプロセッサ（存在しない場合はNone）
        """
        if 0 <= index < len(self.processors):
            return self.processors[index]
        return None
    
    def get_processors(self) -> List[BaseProcessor]:
        """
        すべてのプロセッサを取得
        
        Returns
        -------
        List[BaseProcessor]
            プロセッサのリスト
        """
        return self.processors
    
    def process(self, container: DataContainer, 
                stop_on_error: bool = False) -> DataContainer:
        """
        データコンテナを処理
        
        Parameters
        ----------
        container : DataContainer
            処理するデータコンテナ
        stop_on_error : bool, optional
            エラーで処理を中止するかどうか, by default False
            
        Returns
        -------
        DataContainer
            処理後のデータコンテナ
        """
        # メッセージとヒストリーをクリア
        self.clear_messages()
        self.processing_history = []
        
        # メタデータに処理情報を追加
        processing_info = {
            'pipeline_name': self.name,
            'start_time': datetime.now().isoformat(),
            'processors': [p.name for p in self.processors],
            'steps_completed': 0,
            'steps_failed': 0
        }
        
        # プロセッサがない場合はそのまま返す
        if not self.processors:
            self.info.append("前処理プロセッサが登録されていません")
            
            # 処理情報をメタデータに追加
            container.add_metadata('processing_info', processing_info)
            return container
        
        # 現在の処理対象を追跡
        current = container
        
        # プロセッサを順番に適用
        for i, processor in enumerate(self.processors):
            step_info = {
                'step': i + 1,
                'processor': processor.name,
                'status': 'pending',
                'start_time': datetime.now().isoformat()
            }
            
            try:
                # 処理可能かどうかをチェック
                if not processor.can_process(current):
                    message = f"プロセッサ '{processor.name}' はこのデータタイプを処理できません"
                    step_info['status'] = 'skipped'
                    step_info['message'] = message
                    self.warnings.append(message)
                    self.processing_history.append(step_info)
                    continue
                
                # 処理実行
                result = processor.process(current)
                
                # 結果の検証
                if result is None:
                    message = f"プロセッサ '{processor.name}' が無効な結果を返しました"
                    step_info['status'] = 'failed'
                    step_info['message'] = message
                    self.errors.append(message)
                    self.processing_history.append(step_info)
                    
                    if stop_on_error:
                        break
                    
                    continue
                
                # 処理後のデータに更新
                current = result
                
                # プロセッサのメッセージを収集
                self.errors.extend([f"[{processor.name}] {msg}" for msg in processor.get_errors()])
                self.warnings.extend([f"[{processor.name}] {msg}" for msg in processor.get_warnings()])
                self.info.extend([f"[{processor.name}] {msg}" for msg in processor.get_info()])
                
                # 成功情報
                step_info['status'] = 'completed'
                processing_info['steps_completed'] += 1
                
            except Exception as e:
                # エラー情報
                message = f"プロセッサ '{processor.name}' が例外を発生させました: {str(e)}"
                step_info['status'] = 'failed'
                step_info['message'] = message
                step_info['exception'] = str(e)
                self.errors.append(message)
                processing_info['steps_failed'] += 1
                
                if stop_on_error:
                    break
            
            finally:
                # 終了時間を追加
                step_info['end_time'] = datetime.now().isoformat()
                self.processing_history.append(step_info)
        
        # 処理情報を更新
        processing_info['end_time'] = datetime.now().isoformat()
        processing_info['total_steps'] = len(self.processors)
        processing_info['successful'] = len(self.errors) == 0
        
        # 処理情報をメタデータに追加
        current.add_metadata('processing_info', processing_info)
        current.add_metadata('processing_history', self.processing_history)
        
        return current
    
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
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        処理履歴を取得
        
        Returns
        -------
        List[Dict[str, Any]]
            処理ステップの履歴情報のリスト
        """
        return self.processing_history
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"ProcessingPipeline({self.name}): {len(self.processors)}プロセッサ"
