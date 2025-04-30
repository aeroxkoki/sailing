# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
Part 2 of data exporter implementation with json, xml and other utility methods.
"""

import os
import logging
from pathlib import Path
import datetime
import io
import json
from typing import Dict, List, Any, Optional, Union

# ベースクラスのインポート
from sailing_data_processor.reporting.exporters.base_exporter import BaseExporter
from sailing_data_processor.reporting.exporters.data_exporter import DataExporter, PANDAS_AVAILABLE

try:
    import pandas as pd
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import xml.etree.ElementTree as ET
    from xml.dom import minidom
except ImportError:
    pass

logger = logging.getLogger(__name__)

class DataExporterExtensions:
    """データエクスポーター拡張機能（インポート用）"""
    pass

def add_methods_to_data_exporter():
    """DataExporterクラスにメソッドを追加"""
    
    def _export_json(self, data, output_path, **kwargs):
        """
        データをJSON形式でエクスポート
        
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
        
        # メタデータの取得
        metadata = None
        if self.options.get("include_metadata", True) and hasattr(data, 'metadata'):
            metadata = data.metadata
        
        # JSONオブジェクトの作成
        json_data = {}
        
        # メタデータの追加
        if metadata:
            json_data["metadata"] = metadata
        
        # データの追加
        orient = self.options.get("json_orient", "records")
        
        if PANDAS_AVAILABLE:
            # pandasのto_jsonを使用
            if orient == "records":
                # レコード形式（リスト形式）
                data_json = df.to_json(orient="records", date_format="iso")
                json_data["data"] = json.loads(data_json)
            else:
                # その他の形式
                data_json = df.to_json(orient=orient, date_format="iso")
                json_data["data"] = json.loads(data_json)
        else:
            # pandasが利用できない場合は手動変換
            if orient == "records":
                # レコード形式（リスト形式）
                records = []
                for _, row in df.iterrows():
                    record = {}
                    for col in df.columns:
                        value = row[col]
                        # 日付型の処理
                        if hasattr(value, 'strftime'):
                            value = value.strftime(self.options.get("date_format", "%Y-%m-%d %H:%M:%S"))
                        # NumPy型の処理
                        elif hasattr(value, 'item'):
                            value = value.item()
                        record[col] = value
                    records.append(record)
                json_data["data"] = records
            else:
                # columnsまたはsplit形式
                column_data = {}
                for col in df.columns:
                    column_data[col] = df[col].tolist()
                json_data["data"] = column_data
        
        # JSON文字列化
        if self.options.get("pretty_print", True):
            json_str = json.dumps(json_data, indent=2, ensure_ascii=False, default=self._json_serializer)
        else:
            json_str = json.dumps(json_data, ensure_ascii=False, default=self._json_serializer)
        
        # ファイルに書き込む場合
        if isinstance(output_path, (str, Path)):
            with open(output_path, 'w', encoding=self.options.get("encoding", "utf-8")) as f:
                f.write(json_str)
            return str(output_path)
            
        # ファイルオブジェクトに直接書き込む場合
        elif hasattr(output_path, "write"):
            if isinstance(output_path, io.TextIOBase):
                output_path.write(json_str)
            else:
                output_path.write(json_str.encode(self.options.get("encoding", "utf-8")))
            return None
    
    def _export_xml(self, data, output_path, **kwargs):
        """
        データをXML形式でエクスポート
        
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
        
        # XML要素名の設定
        root_element = self.options.get("xml_root", "data")
        row_element = self.options.get("xml_row", "row")
        
        # XML構造の作成
        root = ET.Element(root_element)
        
        # メタデータの追加
        if self.options.get("include_metadata", True) and hasattr(data, 'metadata'):
            metadata_elem = ET.SubElement(root, "metadata")
            for key, value in data.metadata.items():
                meta_item = ET.SubElement(metadata_elem, "item")
                meta_item.set("name", str(key))
                meta_item.text = str(value)
        
        # データセクションの作成
        data_elem = ET.SubElement(root, "data")
        
        # ヘッダー情報の追加（オプション）
        if self.options.get("include_header", True):
            headers_elem = ET.SubElement(data_elem, "headers")
            for col in df.columns:
                header_elem = ET.SubElement(headers_elem, "header")
                header_elem.set("name", str(col))
        
        # 行データの追加
        for _, row in df.iterrows():
            row_elem = ET.SubElement(data_elem, row_element)
            
            # インデックスの追加（オプション）
            if self.options.get("include_index", False):
                row_elem.set("index", str(_.item() if hasattr(_, 'item') else _))
            
            # 列データの追加
            for col in df.columns:
                value = row[col]
                
                # 特殊型の処理
                if pd.isna(value):
                    # 欠損値
                    field_elem = ET.SubElement(row_elem, "field")
                    field_elem.set("name", str(col))
                    field_elem.set("null", "true")
                elif hasattr(value, 'strftime'):
                    # 日時型
                    field_elem = ET.SubElement(row_elem, "field")
                    field_elem.set("name", str(col))
                    field_elem.set("type", "datetime")
                    field_elem.text = value.strftime(self.options.get("date_format", "%Y-%m-%d %H:%M:%S"))
                elif isinstance(value, (int, float)):
                    # 数値型
                    field_elem = ET.SubElement(row_elem, "field")
                    field_elem.set("name", str(col))
                    field_elem.set("type", "number")
                    field_elem.text = str(value)
                else:
                    # その他（文字列として）
                    field_elem = ET.SubElement(row_elem, "field")
                    field_elem.set("name", str(col))
                    field_elem.text = str(value)
        
        # XMLの整形
        if self.options.get("pretty_print", True):
            xml_str = minidom.parseString(ET.tostring(root, encoding='unicode')).toprettyxml(indent="  ")
        else:
            xml_str = ET.tostring(root, encoding='unicode')
        
        # XMLヘッダーの追加
        xml_str = '<?xml version="1.0" encoding="{}"?>\n'.format(self.options.get("encoding", "utf-8")) + xml_str
        
        # ファイルに書き込む場合
        if isinstance(output_path, (str, Path)):
            with open(output_path, 'w', encoding=self.options.get("encoding", "utf-8")) as f:
                f.write(xml_str)
            return str(output_path)
            
        # ファイルオブジェクトに直接書き込む場合
        elif hasattr(output_path, "write"):
            if isinstance(output_path, io.TextIOBase):
                output_path.write(xml_str)
            else:
                output_path.write(xml_str.encode(self.options.get("encoding", "utf-8")))
            return None
    
    def _prepare_dataframe(self, data):
        """
        データフレームの準備（フィルタリングや変換を適用）
        
        Parameters
        ----------
        data : Any
            処理するデータ
            
        Returns
        -------
        pandas.DataFrame
            処理されたデータフレーム
        """
        if not PANDAS_AVAILABLE:
            self.add_error("データ処理にはpandasライブラリが必要です。pip install pandas を実行してください。")
            return None
        
        # DataFrameでない場合はDataFrameに変換
        if not isinstance(data.data, pd.DataFrame):
            try:
                df = pd.DataFrame(data.data)
            except Exception as e:
                self.add_error(f"データをDataFrameに変換できません: {str(e)}")
                return None
        else:
            # コピーして元のデータを変更しない
            df = data.data.copy()
        
        # 列の選択
        columns = self.options.get("columns", None)
        if columns is not None:
            valid_columns = [col for col in columns if col in df.columns]
            if not valid_columns:
                self.add_warning("指定された列がデータに存在しません。全ての列を使用します。")
            else:
                df = df[valid_columns]
        
        # 行の選択（サンプリング）
        rows = self.options.get("rows", None)
        if rows is not None:
            if isinstance(rows, int) and rows > 0:
                # 先頭から指定行数を選択
                df = df.head(rows)
            elif isinstance(rows, list) and all(isinstance(idx, int) for idx in rows):
                # インデックスリストで選択
                df = df.iloc[rows]
            elif isinstance(rows, tuple) and len(rows) == 2:
                # 範囲で選択（開始、終了）
                start, end = rows
                df = df.iloc[start:end]
        
        # フィルタリング条件の適用
        filters = self.options.get("filters", None)
        if filters is not None:
            if isinstance(filters, dict):
                # 辞書形式のフィルタ
                for column, condition in filters.items():
                    if column in df.columns:
                        if isinstance(condition, dict):
                            # 複合条件
                            for op, value in condition.items():
                                if op == "eq":
                                    df = df[df[column] == value]
                                elif op == "ne":
                                    df = df[df[column] != value]
                                elif op == "gt":
                                    df = df[df[column] > value]
                                elif op == "lt":
                                    df = df[df[column] < value]
                                elif op == "ge":
                                    df = df[df[column] >= value]
                                elif op == "le":
                                    df = df[df[column] <= value]
                                elif op == "in":
                                    df = df[df[column].isin(value)]
                                elif op == "not_in":
                                    df = df[~df[column].isin(value)]
                                elif op == "contains":
                                    df = df[df[column].astype(str).str.contains(str(value))]
                                elif op == "starts_with":
                                    df = df[df[column].astype(str).str.startswith(str(value))]
                                elif op == "ends_with":
                                    df = df[df[column].astype(str).str.endswith(str(value))]
                        else:
                            # 単純な等価条件
                            df = df[df[column] == condition]
            elif callable(filters):
                # コールバック関数
                df = df[filters(df)]
        
        # データ変換の適用
        transformations = self.options.get("transformations", None)
        if transformations is not None:
            if isinstance(transformations, dict):
                # 辞書形式の変換
                for column, transform in transformations.items():
                    if column in df.columns:
                        if callable(transform):
                            # 関数による変換
                            df[column] = df[column].apply(transform)
                        elif isinstance(transform, dict):
                            # 置換マップ
                            df[column] = df[column].map(transform).fillna(df[column])
                        elif isinstance(transform, str) and transform.startswith("lambda"):
                            # ラムダ式（非推奨）
                            try:
                                lambda_func = eval(transform)
                                df[column] = df[column].apply(lambda_func)
                            except Exception as e:
                                self.add_warning(f"ラムダ式の評価に失敗しました: {str(e)}")
                        else:
                            # 単純な値置換
                            df[column] = transform
            elif callable(transformations):
                # DataFrameに対するコールバック関数
                df = transformations(df)
        
        return df
    
    def _compress_file(self, file_path, **kwargs):
        """
        ファイルを圧縮
        
        Parameters
        ----------
        file_path : str
            圧縮するファイルのパス
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        str
            圧縮されたファイルのパス
        """
        if not file_path or not isinstance(file_path, str):
            return file_path
        
        compression_format = self.options.get("compression_format", "zip")
        
        try:
            import zipfile
            import gzip
            
            # 元のファイル名
            original_name = os.path.basename(file_path)
            
            if compression_format == "zip":
                # ZIP圧縮
                zip_path = f"{file_path}.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    zip_file.write(file_path, arcname=original_name)
                
                # 元のファイルを削除（オプション）
                if self.options.get("remove_original", True):
                    os.remove(file_path)
                
                return zip_path
                
            elif compression_format == "gzip":
                # GZIP圧縮
                gz_path = f"{file_path}.gz"
                with open(file_path, 'rb') as f_in:
                    with gzip.open(gz_path, 'wb') as f_out:
                        f_out.writelines(f_in)
                
                # 元のファイルを削除（オプション）
                if self.options.get("remove_original", True):
                    os.remove(file_path)
                
                return gz_path
            
            else:
                self.add_warning(f"未対応の圧縮形式: {compression_format}")
                return file_path
                
        except Exception as e:
            self.add_warning(f"圧縮中にエラーが発生しました: {str(e)}")
            return file_path
    
    def _json_serializer(self, obj):
        """
        JSON変換できないオブジェクトのシリアライザ
        
        Parameters
        ----------
        obj : Any
            シリアライズするオブジェクト
            
        Returns
        -------
        Any
            シリアライズ可能な値
        """
        # 日時オブジェクト
        if hasattr(obj, 'strftime'):
            return obj.strftime(self.options.get("date_format", "%Y-%m-%d %H:%M:%S"))
        
        # NumPy型
        if hasattr(obj, 'item'):
            return obj.item()
        
        # その他の型
        return str(obj)
    
    def validate_options(self):
        """
        オプションの検証
        
        Returns
        -------
        bool
            検証結果
        """
        # フォーマットの検証
        output_format = self.options.get("format", "csv")
        if output_format not in ["csv", "json", "xml"]:
            self.add_warning(f"未対応のデータ形式: {output_format}, 'csv'を使用します。")
            self.options["format"] = "csv"
        
        # CSVオプションの検証
        if output_format == "csv":
            delimiter = self.options.get("delimiter", ",")
            if len(delimiter) != 1:
                self.add_warning(f"区切り文字は1文字である必要があります: {delimiter}, ','を使用します。")
                self.options["delimiter"] = ","
        
        # JSONオプションの検証
        if output_format == "json":
            json_orient = self.options.get("json_orient", "records")
            if json_orient not in ["records", "columns", "index", "split", "values"]:
                self.add_warning(f"未対応のJSONフォーマット: {json_orient}, 'records'を使用します。")
                self.options["json_orient"] = "records"
        
        # 変換とフィルタリングの検証
        transformations = self.options.get("transformations", None)
        if transformations is not None and not (isinstance(transformations, (dict, list)) or callable(transformations)):
            self.add_warning("変換設定は辞書、リスト、または関数である必要があります。無視します。")
            self.options["transformations"] = None
        
        filters = self.options.get("filters", None)
        if filters is not None and not (isinstance(filters, dict) or callable(filters)):
            self.add_warning("フィルタ設定は辞書または関数である必要があります。無視します。")
            self.options["filters"] = None
        
        # 圧縮オプションの検証
        if self.options.get("compress", False):
            compression_format = self.options.get("compression_format", "zip")
            if compression_format not in ["zip", "gzip"]:
                self.add_warning(f"未対応の圧縮形式: {compression_format}, 'zip'を使用します。")
                self.options["compression_format"] = "zip"
        
        return True
    
    def get_supported_formats(self):
        """
        サポートするフォーマットのリストを取得
        
        Returns
        -------
        List[str]
            サポートするフォーマットのリスト
        """
        return ["csv", "json", "xml", "data", "text"]
    
    # メソッドをDataExporterクラスに追加
    DataExporter._export_json = _export_json
    DataExporter._export_xml = _export_xml
    DataExporter._prepare_dataframe = _prepare_dataframe
    DataExporter._compress_file = _compress_file
    DataExporter._json_serializer = _json_serializer
    DataExporter.validate_options = validate_options
    DataExporter.get_supported_formats = get_supported_formats

# 起動時にメソッド追加を実行
add_methods_to_data_exporter()
