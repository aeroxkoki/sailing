# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.exporters.base_exporter

高度なエクスポート機能の基底クラスを提供するモジュール
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
import os
from pathlib import Path
import datetime
import tempfile
import json
import logging

logger = logging.getLogger(__name__)

class BaseExporter:
    """
    エクスポーター基底クラス
    
    各種エクスポート機能の共通インターフェースを定義します。
    """
    
    def __init__(self, **options):
        """初期化"""
        self.options = {}
            # デフォルトオプション
            "output_path": "",
            "filename": f"report_datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "include_metadata": True,
            "include_timestamp": True,
            # 子クラスで上書き/追加されるオプション
        }
        
        # オプションの更新
        self.options.update(options)
        
        # エラーと警告のログ
        self.errors = []
        self.warnings = []
    
    def export(self, data, template=None, **kwargs):
        """
        データをエクスポート
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        template : Optional[str]
            使用するテンプレート
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        str
            出力ファイルのパス
        """
        # 各サブクラスで実装
        raise NotImplementedError("Subclasses must implement export()")
    
    def validate_options(self):
        """
        オプションの検証
        
        Returns
        -------
        bool
            検証結果（Trueは有効なオプション）
        """
        # 各サブクラスで実装
        return True
    
    def get_supported_formats(self):
        """
        サポートする形式のリストを取得
        
        Returns
        -------
        List[str]
            サポートする形式のリスト
        """
        # 各サブクラスで実装
        return []
    
    def export_batch(self, data_items, output_dir=None, template=None, **kwargs):
        """
        複数のデータをバッチエクスポート
        
        Parameters
        ----------
        data_items : List[Any]
            エクスポートするデータのリスト
        output_dir : Optional[str]
            出力先ディレクトリ
        template : Optional[str]
            使用するテンプレート
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        List[str]
            出力ファイルのパスリスト
        """
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
        
        output_paths = []
        
        for i, data in enumerate(data_items):
            try:
                # ファイル名の生成
                if "filename" in kwargs:
                    filename = kwargs["filename"]
                else:
                    filename = f"{self.options['filename']}_{i+1}"
                
                # 出力パスの生成
                output_path = os.path.join(output_dir, filename)
                
                # エクスポート
                result_path = self.export(data, template, output_path=output_path, **kwargs)
                
                if result_path:
                    output_paths.append(result_path)
            except Exception as e:
                self.errors.append(f"Item {i+1} export failed: {str(e)}")
                logger.error(f"Failed to export item {i+1}: {str(e)}", exc_info=True)
                }
                }
        
        return output_paths
    
    def generate_filename(self, data, extension):
        """
        データからファイル名を生成
        
        Parameters
        ----------
        data : Any
            データ
        extension : str
            ファイル拡張子
            
        Returns
        -------
        str
            生成されたファイル名
        """
        base_name = self.options["filename"]
        
        # メタデータからファイル名を生成する場合はここに実装
        if hasattr(data, 'metadata') and isinstance(data.metadata, dict):
            # メタデータから日付や名前などを取得
            if 'date' in data.metadata:
                date_str = data.metadata['date']
                if isinstance(date_str, str):
                    base_name = f"{base_name}_{date_str.replace('/', '-').replace(' ', '_')}"
            
            # 名前があれば使用
            if 'name' in data.metadata:
                base_name = f"{base_name}_{data.metadata['name']}"
        
        # タイムスタンプを追加
        if self.options.get("include_timestamp", True):
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = f"{base_name}_{timestamp}"
        
        # 拡張子を追加
        if not extension.startswith('.'):
            extension = f".{extension}"
        
        return f"{base_name}{extension}"
    
    def ensure_directory(self, path):
        """
        ディレクトリが存在することを確認し、必要に応じて作成
        
        Parameters
        ----------
        path : str
            ディレクトリパス
        """
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def add_error(self, message):
        """
        エラーメッセージを追加
        
        Parameters
        ----------
        message : str
            エラーメッセージ
        """
        self.errors.append(message)
        logger.error(message)
    
    def add_warning(self, message):
        """
        警告メッセージを追加
        
        Parameters
        ----------
        message : str
            警告メッセージ
        """
        self.warnings.append(message)
        logger.warning(message)
    
    def get_errors(self):
        """
        エラーメッセージを取得
        
        Returns
        -------
        List[str]
            エラーメッセージのリスト
        """
        return self.errors
    
    def get_warnings(self):
        """
        警告メッセージを取得
        
        Returns
        -------
        List[str]
            警告メッセージのリスト
        """
        return self.warnings
    
    def clear_messages(self):
        """
        エラーメッセージと警告メッセージをクリア
        """
        self.errors = []
        self.warnings = []
