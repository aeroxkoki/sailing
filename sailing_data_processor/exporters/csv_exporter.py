# -*- coding: utf-8 -*-
"""
sailing_data_processor.exporters.csv_exporter

セッション結果をCSV形式でエクスポートするモジュール
"""

import os
import csv
import io
from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
from pathlib import Path
import datetime
import pandas as pd

from sailing_data_processor.project.session_model import SessionModel, SessionResult
from sailing_data_processor.exporters.session_exporter import SessionExporter


class CSVExporter(SessionExporter):
    """
    CSV形式でセッション結果をエクスポートするクラス
    """
    
    def __init__(self, template_manager=None, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        template_manager : Optional, default=None
            テンプレート管理クラスのインスタンス
        config : Optional[Dict[str, Any]], default=None
            エクスポーター設定
        """
        super().__init__(template_manager, config)
    
    def export_session(self, session: SessionModel, output_path: str, 
                       template: str = "default", options: Dict[str, Any] = None) -> str:
        """
        単一セッションをCSVでエクスポート
        
        Parameters
        ----------
        session : SessionModel
            エクスポートするセッション
        output_path : str
            出力先パス
        template : str, optional
            使用するテンプレート名, by default "default"
        options : Dict[str, Any], optional
            エクスポートオプション, by default None
            
        Returns
        -------
        str
            エクスポートされたファイルのパス
        """
        options = options or {}
        
        # テンプレートの取得
        template_data = {}
        if self.template_manager:
            try:
                template_data = self.template_manager.get_template(template, "csv")
            except Exception as e:
                self.warnings.append(f"テンプレートの読み込みに失敗しました: {e}")
                # デフォルト設定で続行
        
        # 出力先ディレクトリの確認
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # CSVエクスポート設定
        csv_metadata = template_data.get("metadata", {})
        include_headers = csv_metadata.get("include_headers", True)
        delimiter = csv_metadata.get("delimiter", ",")
        quotechar = csv_metadata.get("quotechar", '"')
        encoding = csv_metadata.get("encoding", "utf-8")
        include_bom = csv_metadata.get("include_bom", True)
        
        # オプションで上書き
        if "include_headers" in options:
            include_headers = options["include_headers"]
        if "delimiter" in options:
            delimiter = options["delimiter"]
        if "quotechar" in options:
            quotechar = options["quotechar"]
        if "encoding" in options:
            encoding = options["encoding"]
        if "include_bom" in options:
            include_bom = options["include_bom"]
        
        # エクスポート対象のセクションを取得
        export_sections = []
        for section in template_data.get("sections", []):
            if section.get("enabled", True):
                export_sections.append(section)
        
        # オプションによるセクション指定
        if "sections" in options and options["sections"]:
            export_sections = []
            for section_name in options["sections"]:
                for section in template_data.get("sections", []):
                    if section.get("name") == section_name and section.get("enabled", True):
                        export_sections.append(section)
                        break
        
        # メタデータセクションのエクスポート
        if any(section.get("name") == "metadata" for section in export_sections):
            metadata_fields = []
            for section in export_sections:
                if section.get("name") == "metadata":
                    metadata_fields = section.get("fields", [])
                    break
            
            if metadata_fields:
                metadata_output_path = output_path
                if len(export_sections) > 1:
                    # 複数セクションがある場合は別ファイルに出力
                    metadata_output_path = self._get_section_output_path(output_path, "metadata")
                
                # メタデータをエクスポート
                self._export_metadata_csv(session, metadata_output_path, metadata_fields, 
                                         include_headers, delimiter, quotechar, encoding, include_bom)
        
        # 結果データのエクスポート
        for section in export_sections:
            if section.get("name") in ["wind_data", "strategy_points", "performance_data"]:
                section_name = section.get("name")
                section_fields = section.get("fields", [])
                
                if section_fields:
                    section_output_path = output_path
                    if len(export_sections) > 1:
                        # 複数セクションがある場合は別ファイルに出力
                        section_output_path = self._get_section_output_path(output_path, section_name)
                    
                    # 結果データをエクスポート
                    self._export_results_csv(session, section_output_path, section_name, section_fields,
                                           include_headers, delimiter, quotechar, encoding, include_bom)
        
        return output_path
    
    def export_multiple_sessions(self, sessions: List[SessionModel], output_dir: str,
                                template: str = "default", options: Dict[str, Any] = None) -> List[str]:
        """
        複数セッションをCSVでエクスポート
        
        Parameters
        ----------
        sessions : List[SessionModel]
            エクスポートするセッションのリスト
        output_dir : str
            出力先ディレクトリ
        template : str, optional
            使用するテンプレート名, by default "default"
        options : Dict[str, Any], optional
            エクスポートオプション, by default None
            
        Returns
        -------
        List[str]
            エクスポートされたファイルのパスのリスト
        """
        options = options or {}
        export_files = []
        
        # 出力ディレクトリの確認
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 各セッションを個別にエクスポート
        for session in sessions:
            try:
                # ファイル名の生成
                filename = self.generate_export_filename(session, "csv")
                output_path = os.path.join(output_dir, filename)
                
                # エクスポート実行
                exported_file = self.export_session(session, output_path, template, options)
                export_files.append(exported_file)
            except Exception as e:
                self.errors.append(f"セッション '{session.name}' のエクスポートに失敗しました: {e}")
        
        # メタデータの一括エクスポート
        if "export_metadata_summary" in options and options["export_metadata_summary"]:
            try:
                summary_path = os.path.join(output_dir, f"sessions_summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                self._export_metadata_summary(sessions, summary_path, options)
                export_files.append(summary_path)
            except Exception as e:
                self.errors.append(f"メタデータサマリーのエクスポートに失敗しました: {e}")
        
        return export_files
    
    def _get_section_output_path(self, output_path: str, section_name: str) -> str:
        """
        セクション別の出力パスを取得
        
        Parameters
        ----------
        output_path : str
            基本出力パス
        section_name : str
            セクション名
            
        Returns
        -------
        str
            セクション別の出力パス
        """
        path = Path(output_path)
        stem = path.stem
        suffix = path.suffix
        
        # セクション名を含む新しいファイル名を生成
        new_filename = f"{stem}_{section_name}{suffix}"
        return str(path.parent / new_filename)
    
    def _export_metadata_csv(self, session: SessionModel, output_path: str, 
                            metadata_fields: List[str], include_headers: bool, 
                            delimiter: str, quotechar: str, encoding: str, include_bom: bool) -> None:
        """
        セッションメタデータをCSVでエクスポート
        
        Parameters
        ----------
        session : SessionModel
            エクスポートするセッション
        output_path : str
            出力先パス
        metadata_fields : List[str]
            エクスポートするメタデータフィールドのリスト
        include_headers : bool
            ヘッダーを含めるかどうか
        delimiter : str
            区切り文字
        quotechar : str
            引用符
        encoding : str
            エンコーディング
        include_bom : bool
            BOMを含めるかどうか
        """
        # メタデータの取得
        metadata = {}
        
        # セッションの基本属性
        for field in metadata_fields:
            if hasattr(session, field):
                value = getattr(session, field)
                # リストや辞書の場合は文字列に変換
                if isinstance(value, (list, dict)):
                    value = str(value)
                metadata[field] = value
            elif field in session.metadata:
                value = session.metadata[field]
                # リストや辞書の場合は文字列に変換
                if isinstance(value, (list, dict)):
                    value = str(value)
                metadata[field] = value
        
        # メタデータをDataFrameに変換
        df = pd.DataFrame([metadata])
        
        # CSVファイルの出力
        mode = 'wb' if include_bom else 'w'
        encoding_with_bom = f"{encoding}-sig" if include_bom and encoding.lower() == "utf-8" else encoding
        
        if include_bom and encoding.lower() == "utf-8":
            with open(output_path, mode, newline='') as f:
                # BOMを手動で追加
                f.write(b'\xef\xbb\xbf')
                df.to_csv(f, index=False, header=include_headers, sep=delimiter, quotechar=quotechar, 
                          quoting=csv.QUOTE_MINIMAL, encoding=encoding)
        else:
            df.to_csv(output_path, index=False, header=include_headers, sep=delimiter, quotechar=quotechar, 
                      quoting=csv.QUOTE_MINIMAL, encoding=encoding)
    
    def _export_results_csv(self, session: SessionModel, output_path: str, section_name: str,
                          section_fields: List[str], include_headers: bool, 
                          delimiter: str, quotechar: str, encoding: str, include_bom: bool) -> None:
        """
        セッション結果データをCSVでエクスポート
        
        Parameters
        ----------
        session : SessionModel
            エクスポートするセッション
        output_path : str
            出力先パス
        section_name : str
            セクション名
        section_fields : List[str]
            エクスポートするフィールドのリスト
        include_headers : bool
            ヘッダーを含めるかどうか
        delimiter : str
            区切り文字
        quotechar : str
            引用符
        encoding : str
            エンコーディング
        include_bom : bool
            BOMを含めるかどうか
        """
        # 結果データの取得 (現在はダミーデータ)
        # 実際の実装では、セッション結果マネージャーからデータを取得する
        
        # ダミーデータの生成
        data = []
        
        # 実際のデータが存在すれば、それを使用
        # 例えば風データ、戦略ポイントデータなど
        # ここでは簡単なダミーデータを作成
        
        # DataFrameに変換
        df = pd.DataFrame(data)
        
        # 指定されたフィールドのみを選択
        if section_fields and not df.empty:
            available_fields = [field for field in section_fields if field in df.columns]
            if available_fields:
                df = df[available_fields]
        
        # CSVファイルの出力
        mode = 'wb' if include_bom else 'w'
        encoding_with_bom = f"{encoding}-sig" if include_bom and encoding.lower() == "utf-8" else encoding
        
        if include_bom and encoding.lower() == "utf-8":
            with open(output_path, mode, newline='') as f:
                # BOMを手動で追加
                f.write(b'\xef\xbb\xbf')
                df.to_csv(f, index=False, header=include_headers, sep=delimiter, quotechar=quotechar, 
                          quoting=csv.QUOTE_MINIMAL, encoding=encoding)
        else:
            df.to_csv(output_path, index=False, header=include_headers, sep=delimiter, quotechar=quotechar, 
                      quoting=csv.QUOTE_MINIMAL, encoding=encoding)
    
    def _export_metadata_summary(self, sessions: List[SessionModel], output_path: str, options: Dict[str, Any]) -> None:
        """
        複数セッションのメタデータサマリーをCSVでエクスポート
        
        Parameters
        ----------
        sessions : List[SessionModel]
            エクスポートするセッションのリスト
        output_path : str
            出力先パス
        options : Dict[str, Any]
            エクスポートオプション
        """
        # CSVエクスポート設定
        include_headers = options.get("include_headers", True)
        delimiter = options.get("delimiter", ",")
        quotechar = options.get("quotechar", '"')
        encoding = options.get("encoding", "utf-8")
        include_bom = options.get("include_bom", True)
        
        # 共通のメタデータフィールド
        metadata_fields = [
            "session_id", "name", "description", "purpose", "category", 
            "status", "tags", "rating", "event_date", "location", 
            "importance", "created_at", "updated_at", "completion_percentage"
        ]
        
        # オプションで上書き
        if "metadata_fields" in options:
            metadata_fields = options["metadata_fields"]
        
        # 各セッションのメタデータを収集
        metadata_list = []
        
        for session in sessions:
            metadata = {}
            
            # セッションの基本属性
            for field in metadata_fields:
                if hasattr(session, field):
                    value = getattr(session, field)
                    # リストや辞書の場合は文字列に変換
                    if isinstance(value, (list, dict)):
                        value = str(value)
                    metadata[field] = value
                elif field in session.metadata:
                    value = session.metadata[field]
                    # リストや辞書の場合は文字列に変換
                    if isinstance(value, (list, dict)):
                        value = str(value)
                    metadata[field] = value
            
            metadata_list.append(metadata)
        
        # メタデータをDataFrameに変換
        df = pd.DataFrame(metadata_list)
        
        # CSVファイルの出力
        mode = 'wb' if include_bom else 'w'
        encoding_with_bom = f"{encoding}-sig" if include_bom and encoding.lower() == "utf-8" else encoding
        
        if include_bom and encoding.lower() == "utf-8":
            with open(output_path, mode, newline='') as f:
                # BOMを手動で追加
                f.write(b'\xef\xbb\xbf')
                df.to_csv(f, index=False, header=include_headers, sep=delimiter, quotechar=quotechar, 
                          quoting=csv.QUOTE_MINIMAL, encoding=encoding)
        else:
            df.to_csv(output_path, index=False, header=include_headers, sep=delimiter, quotechar=quotechar, 
                      quoting=csv.QUOTE_MINIMAL, encoding=encoding)