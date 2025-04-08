"""
エクスポート/インポートモジュール

このモジュールはセーリング戦略分析システムのデータをエクスポートおよびインポートするための
機能を提供します。ユーザーはセッションやプロジェクト、分析結果などのデータをファイルとして
保存したり、ファイルから読み込んだりすることができます。
"""

import json
import base64
import gzip
import io
import datetime
from typing import Any, Dict, List, Optional, Union, BinaryIO, Tuple

import streamlit as st
import pandas as pd

from .storage_interface import StorageError


class ExportImportManager:
    """
    データのエクスポートとインポートを管理するクラス。
    
    このクラスはユーザーデータのエクスポートとインポート機能を提供します。
    エクスポート時にはデータを圧縮し、インポート時には検証と適切な変換を行います。
    """
    
    # エクスポートファイルのバージョン
    CURRENT_VERSION = "1.0.0"
    
    # エクスポートファイルのヘッダー識別子
    FILE_HEADER = "SAILING_ANALYZER_EXPORT"
    
    def __init__(self):
        """初期化"""
        pass
    
    def export_data(self, data: Dict[str, Any], export_name: str = "sailing_data_export") -> Tuple[bytes, str]:
        """
        データをエクスポート用のバイナリデータに変換する。
        
        Args:
            data: エクスポートするデータ（JSON化可能なオブジェクト）
            export_name: エクスポートファイルのベース名
            
        Returns:
            Tuple[bytes, str]: エクスポートデータのバイト列とファイル名
            
        Raises:
            StorageError: エクスポート処理中のエラー
        """
        try:
            # エクスポートメタデータを作成
            export_metadata = {
                "header": self.FILE_HEADER,
                "version": self.CURRENT_VERSION,
                "timestamp": datetime.datetime.now().isoformat(),
                "name": export_name
            }
            
            # エクスポートデータを構成
            export_data = {
                "metadata": export_metadata,
                "content": data
            }
            
            # JSON文字列に変換
            json_data = json.dumps(export_data)
            
            # GZIPで圧縮
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            # ファイル名を生成
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{export_name}_{timestamp}.saildata"
            
            return compressed_data, filename
            
        except Exception as e:
            raise StorageError(f"データのエクスポートに失敗しました: {str(e)}")
    
    def import_data(self, file_data: Union[bytes, BinaryIO]) -> Dict[str, Any]:
        """
        エクスポートファイルからデータをインポートする。
        
        Args:
            file_data: インポートするファイルデータ（バイト列またはファイルオブジェクト）
            
        Returns:
            Dict[str, Any]: インポートしたデータ
            
        Raises:
            StorageError: インポート処理中のエラーや無効なファイル形式
        """
        try:
            # ファイルオブジェクトの場合はバイト列に変換
            if hasattr(file_data, 'read'):
                file_data = file_data.read()
            
            # GZIPで展開
            try:
                decompressed_data = gzip.decompress(file_data)
            except Exception:
                # 圧縮されていない可能性があるため、そのまま試す
                decompressed_data = file_data
            
            # JSON形式に変換
            import_data = json.loads(decompressed_data.decode('utf-8'))
            
            # ファイル形式を検証
            metadata = import_data.get("metadata", {})
            if metadata.get("header") != self.FILE_HEADER:
                raise StorageError("無効なファイル形式です。セーリング分析システムのエクスポートファイルではありません。")
            
            # バージョン互換性チェック（必要に応じて変換処理を追加）
            version = metadata.get("version")
            if version != self.CURRENT_VERSION:
                # バージョンが異なる場合は変換処理を行う（今回はサポートしない）
                st.warning(f"異なるバージョン（{version}）のエクスポートファイルです。データの互換性に問題が生じる可能性があります。")
            
            # コンテンツを返す
            return import_data.get("content", {})
            
        except json.JSONDecodeError:
            raise StorageError("無効なJSONデータ形式です。ファイルが破損している可能性があります。")
        except Exception as e:
            raise StorageError(f"データのインポートに失敗しました: {str(e)}")
    
    def create_download_link(self, data: bytes, filename: str) -> str:
        """
        ダウンロード用のHTMLリンクを生成する。
        
        Args:
            data: ダウンロードするバイトデータ
            filename: ダウンロードファイル名
            
        Returns:
            str: HTML download属性を持つaタグ
        """
        b64_data = base64.b64encode(data).decode()
        download_link = f'<a href="data:application/octet-stream;base64,{b64_data}" download="{filename}">ダウンロード</a>'
        return download_link
    
    def export_session_to_file(self, session_data: Dict[str, Any], name: str = "session") -> Tuple[bytes, str]:
        """
        セッションデータをエクスポートファイルに変換する。
        
        Args:
            session_data: エクスポートするセッションデータ
            name: セッション名
            
        Returns:
            Tuple[bytes, str]: エクスポートデータのバイト列とファイル名
        """
        export_data = {
            "type": "session",
            "session": session_data
        }
        return self.export_data(export_data, f"sailing_session_{name}")
    
    def export_project_to_file(self, project_data: Dict[str, Any], include_sessions: bool = True) -> Tuple[bytes, str]:
        """
        プロジェクトデータをエクスポートファイルに変換する。
        
        Args:
            project_data: エクスポートするプロジェクトデータ
            include_sessions: 関連セッションを含めるかどうか
            
        Returns:
            Tuple[bytes, str]: エクスポートデータのバイト列とファイル名
        """
        project_name = project_data.get("name", "project")
        export_data = {
            "type": "project",
            "project": project_data,
            "include_sessions": include_sessions
        }
        return self.export_data(export_data, f"sailing_project_{project_name}")
    
    def export_multiple_items(self, items: Dict[str, Dict[str, Any]], export_type: str) -> Tuple[bytes, str]:
        """
        複数のアイテムをバッチエクスポートする。
        
        Args:
            items: エクスポートするアイテムの辞書 (id -> データ)
            export_type: エクスポートの種類（"sessions", "projects"など）
            
        Returns:
            Tuple[bytes, str]: エクスポートデータのバイト列とファイル名
        """
        export_data = {
            "type": export_type,
            "items": items
        }
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.export_data(export_data, f"sailing_{export_type}_{timestamp}")
    
    def get_import_info(self, file_data: Union[bytes, BinaryIO]) -> Dict[str, Any]:
        """
        インポートファイルの基本情報を取得する。
        
        Args:
            file_data: インポートするファイルデータ
            
        Returns:
            Dict[str, Any]: インポートファイルの情報
                - type: ファイルタイプ (session, project, etc.)
                - version: ファイルバージョン
                - timestamp: エクスポート日時
                - name: エクスポート名
                - item_count: 含まれるアイテム数
        """
        try:
            # ファイルオブジェクトの場合はバイト列に変換し、位置をリセット
            if hasattr(file_data, 'read'):
                file_content = file_data.read()
                if hasattr(file_data, 'seek'):
                    file_data.seek(0)
            else:
                file_content = file_data
            
            # GZIPで展開してメタデータのみ解析
            try:
                decompressed_data = gzip.decompress(file_content)
            except Exception:
                # 圧縮されていない可能性があるため、そのまま試す
                decompressed_data = file_content
            
            # JSONデータの解析
            import_data = json.loads(decompressed_data.decode('utf-8'))
            metadata = import_data.get("metadata", {})
            content = import_data.get("content", {})
            
            # 基本情報を収集
            info = {
                "type": content.get("type", "unknown"),
                "version": metadata.get("version", "unknown"),
                "timestamp": metadata.get("timestamp", ""),
                "name": metadata.get("name", ""),
            }
            
            # タイプ別の追加情報
            if info["type"] == "session":
                info["session_name"] = content.get("session", {}).get("name", "")
            elif info["type"] == "project":
                info["project_name"] = content.get("project", {}).get("name", "")
                info["has_sessions"] = content.get("include_sessions", False)
            elif info["type"] in ["sessions", "projects"]:
                info["item_count"] = len(content.get("items", {}))
            
            return info
            
        except Exception as e:
            return {
                "type": "error",
                "error": str(e)
            }


def convert_df_to_csv_download(df: pd.DataFrame, filename: str = "data.csv") -> Tuple[bytes, str]:
    """
    DataFrameをCSVダウンロード用に変換する便利関数。
    
    Args:
        df: 変換するDataFrame
        filename: ダウンロードファイル名
        
    Returns:
        Tuple[bytes, str]: CSVデータのバイト列とファイル名
    """
    csv = df.to_csv(index=False).encode('utf-8')
    return csv, filename
