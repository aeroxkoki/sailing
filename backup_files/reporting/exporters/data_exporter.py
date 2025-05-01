# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
"""

import os
import logging
from pathlib import Path
import datetime
import tempfile
from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
import io
import json
import csv

# ベースクラスのインポート
from sailing_data_processor.reporting.exporters.base_exporter import BaseExporter

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import xml.etree.ElementTree as ET
    from xml.dom import minidom
except ImportError:
    pass

logger = logging.getLogger(__name__)

class DataExporter(BaseExporter):
    """
    データエクスポーター
    
    データを様々な形式（CSV、JSON、XML等）でエクスポートします。
    """
    
    def __init__(self, **options):
        """初期化"""
        super().__init__(**options)
        
        # データエクスポートのデフォルトオプション
        data_defaults = {
            "format": "csv",  # 'csv', 'json', 'xml'
            "delimiter": ",",  # CSVの区切り文字
            "encoding": "utf-8",
            "include_header": True,
            "include_metadata": True,
            "include_index": False,
            "pretty_print": True,  # JSON/XMLの整形
            "quote_strings": True,  # 文字列をクォートするか
            "escape_char": '"',  # エスケープ文字
            "date_format": "%Y-%m-%d %H:%M:%S",
            "float_format": "%.6f",
            "na_rep": "",  # 欠損値の表現
            "columns": None,  # エクスポートする列（Noneの場合は全列）
            "rows": None,  # エクスポートする行（Noneの場合は全行）
            "filters": None,  # データフィルタリング条件
            "transformations": None,  # データ変換設定
            "include_bom": False,  # BOMを含めるか（CSV UTF-8）
            "xml_root": "data",  # XMLのルート要素名
            "xml_row": "row",  # XMLの行要素名
            "json_orient": "records",  # JSONのフォーマット
            "compress": False,  # 圧縮するか
            "compression_format": "zip",  # 圧縮形式
        }
        
        self.options.update(data_defaults)
        self.options.update(options)
    
    def export(self, data, template=None, **kwargs):
        """
        データをエクスポート
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        template : Optional[str]
            使用するテンプレート（データエクスポートの場合は無視される）
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        str
            出力ファイルのパス
        """
        if not self.validate_options():
            self.add_error("無効なオプションが指定されています。")
            return None
        
        # 出力パスの処理
        output_path = kwargs.get("output_path", self.options.get("output_path", ""))
        if not output_path:
            # パスが指定されていない場合は一時ファイルを作成
            output_format = self.options.get("format", "csv")
            output_path = os.path.join(
                tempfile.mkdtemp(),
                self.generate_filename(data, output_format)
            )
        
        # ディレクトリの存在確認と作成
        self.ensure_directory(output_path)
        
        try:
            # データフォーマットに応じたエクスポート
            output_format = self.options.get("format", "csv")
            
            if output_format == "csv":
                # CSVエクスポート
                result = self._export_csv(data, output_path, **kwargs)
            elif output_format == "json":
                # JSONエクスポート
                result = self._export_json(data, output_path, **kwargs)
            elif output_format == "xml":
                # XMLエクスポート
                result = self._export_xml(data, output_path, **kwargs)
            else:
                self.add_error(f"未対応のデータ形式: {output_format}")
                return None
            
            # 圧縮オプションの処理
            if result and self.options.get("compress", False):
                result = self._compress_file(result, **kwargs)
            
            return result
            
        except Exception as e:
            self.add_error(f"データエクスポート中にエラーが発生しました: {str(e)}")
            logger.error(f"Data export failed: {str(e)}", exc_info=True)
            return None
    
    def _export_csv(self, data, output_path, **kwargs):
        """
        データをCSV形式でエクスポート
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        output_path : str
            出力ファイルパス
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        str
            出力ファイルのパス
        """
        # データチェック
        if not hasattr(data, 'data'):
            self.add_error("エクスポート対象のデータにDataFrameが含まれていません。")
            return None
        
        df = self._prepare_dataframe(data)
        if df is None:
            return None
        
        # CSVエクスポートオプションの準備
        csv_options = {
            "sep": self.options.get("delimiter", ","),
            "encoding": self.options.get("encoding", "utf-8"),
            "index": self.options.get("include_index", False),
            "header": self.options.get("include_header", True),
            "date_format": self.options.get("date_format", "%Y-%m-%d %H:%M:%S"),
            "float_format": self.options.get("float_format", "%.6f"),
            "na_rep": self.options.get("na_rep", ""),
        }
        
        # UTF-8 BOMの追加
        if self.options.get("include_bom", False) and csv_options["encoding"].lower() == "utf-8":
            csv_options["encoding"] = "utf-8-sig"
        
        # ファイルに書き込む場合
        if isinstance(output_path, (str, Path)):
            # pandasが利用可能な場合はto_csvを使用
            if PANDAS_AVAILABLE:
                df.to_csv(output_path, **csv_options)
            else:
                # pandasが利用できない場合は標準のcsvモジュールを使用
                with open(output_path, 'w', newline='', encoding=self.options.get("encoding", "utf-8")) as f:
                    writer = csv.writer(
                        f, 
                        delimiter=self.options.get("delimiter", ","),
                        quotechar=self.options.get("escape_char", '"'),
                        quoting=csv.QUOTE_NONNUMERIC if self.options.get("quote_strings", True) else csv.QUOTE_MINIMAL
                    )
                    
                    # ヘッダーの出力
                    if self.options.get("include_header", True):
                        writer.writerow(df.columns)
                    
                    # データの出力
                    for _, row in df.iterrows():
                        writer.writerow(row)
            
            return str(output_path)
            
        # ファイルオブジェクトに直接書き込む場合
        elif hasattr(output_path, "write"):
            # 文字列バッファを使用
            buffer = io.StringIO()
            
            if PANDAS_AVAILABLE:
                df.to_csv(buffer, **csv_options)
                buffer.seek(0)
                
                # エンコーディングの適用
                output_text = buffer.getvalue()
                
                # UTF-8 BOMの追加
                if self.options.get("include_bom", False) and self.options.get("encoding", "utf-8").lower() == "utf-8":
                    # BOM付きUTF-8
                    if hasattr(output_path, "buffer"):
                        # バイナリ書き込み（TextIOWrapper経由）
                        output_path.buffer.write(b'\xef\xbb\xbf')
                        output_path.buffer.write(output_text.encode(self.options.get("encoding", "utf-8")))
                    else:
                        # 通常書き込み
                        output_path.write('\ufeff' + output_text)
                else:
                    # 通常の書き込み
                    if isinstance(output_path, io.TextIOBase):
                        output_path.write(output_text)
                    else:
                        output_path.write(output_text.encode(self.options.get("encoding", "utf-8")))
            else:
                # pandasが利用できない場合
                writer = csv.writer(
                    buffer, 
                    delimiter=self.options.get("delimiter", ","),
                    quotechar=self.options.get("escape_char", '"'),
                    quoting=csv.QUOTE_NONNUMERIC if self.options.get("quote_strings", True) else csv.QUOTE_MINIMAL
                )
                
                # ヘッダーの出力
                if self.options.get("include_header", True):
                    writer.writerow(df.columns)
                
                # データの出力
                for _, row in df.iterrows():
                    writer.writerow(row)
                
                buffer.seek(0)
                output_text = buffer.getvalue()
                
                # UTF-8 BOMの追加と書き込み
                if isinstance(output_path, io.TextIOBase):
                    if self.options.get("include_bom", False) and self.options.get("encoding", "utf-8").lower() == "utf-8":
                        output_path.write('\ufeff' + output_text)
                    else:
                        output_path.write(output_text)
                else:
                    if self.options.get("include_bom", False) and self.options.get("encoding", "utf-8").lower() == "utf-8":
                        output_path.write(b'\xef\xbb\xbf')
                    output_path.write(output_text.encode(self.options.get("encoding", "utf-8")))
            
            return None

# 拡張機能を読み込み
try:
    from sailing_data_processor.reporting.exporters.data_exporter_part2 import add_methods_to_data_exporter
except ImportError:
    logger.warning("データエクスポータ拡張機能の読み込みに失敗しました。一部機能が利用できない可能性があります。")