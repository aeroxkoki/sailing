"""
sailing_data_processor.exporters.base_exporter

データエクスポートの基底クラスを提供するモジュール
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
import pandas as pd
from pathlib import Path
import io
import os

from sailing_data_processor.data_model.container import GPSDataContainer


class BaseExporter(ABC):
    """
    データエクスポートの基底クラス
    
    このクラスを継承して、各種データフォーマット用のエクスポーターを実装します。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        config : Optional[Dict[str, Any]], optional
            エクスポーター設定
        """
        self.config = config or {}
        self.errors = []
        self.warnings = []
    
    @abstractmethod
    def export_data(self, container: GPSDataContainer, 
                    output_path: Optional[Union[str, Path, BinaryIO, TextIO]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[Union[str, bytes]]:
        """
        データをエクスポート
        
        Parameters
        ----------
        container : GPSDataContainer
            エクスポート対象のデータコンテナ
        output_path : Optional[Union[str, Path, BinaryIO, TextIO]], optional
            出力先のパスまたはファイルオブジェクト, by default None
            Noneの場合は文字列またはバイトで返す
        metadata : Optional[Dict[str, Any]], optional
            追加のメタデータ, by default None
            
        Returns
        -------
        Optional[Union[str, bytes]]
            エクスポートされたデータ（output_pathがNoneの場合）
            または None（output_pathが指定された場合）
        """
        pass
    
    def get_default_filename(self, container: GPSDataContainer) -> str:
        """
        デフォルトのファイル名を取得
        
        Parameters
        ----------
        container : GPSDataContainer
            対象のデータコンテナ
            
        Returns
        -------
        str
            デフォルトのファイル名（拡張子なし）
        """
        # メタデータからファイル名を生成
        parts = []
        
        # セーリング日時があれば使用
        if 'date' in container.metadata:
            date_str = container.metadata['date']
            if isinstance(date_str, str):
                parts.append(date_str.replace('/', '-').replace(' ', '_'))
        
        # 場所があれば使用
        if 'location' in container.metadata:
            parts.append(container.metadata['location'])
        
        # ボート名があれば使用
        if 'boat_name' in container.metadata:
            parts.append(container.metadata['boat_name'])
        
        # セーラー名があれば使用
        if 'sailor_name' in container.metadata:
            parts.append(container.metadata['sailor_name'])
        
        # 時刻範囲を使用
        if len(container.data) > 0:
            try:
                start_time = pd.to_datetime(container.data['timestamp'].min()).strftime('%Y%m%d_%H%M')
                end_time = pd.to_datetime(container.data['timestamp'].max()).strftime('%H%M')
                if not parts:
                    parts.append(f"{start_time}-{end_time}")
            except (KeyError, ValueError):
                pass
        
        if not parts:
            return "sailing_data_export"
        
        return "_".join(parts)
    
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
