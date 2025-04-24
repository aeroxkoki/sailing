# -*- coding: utf-8 -*-
"""
sailing_data_processor.exporters.session_exporter

セッション結果をエクスポートするための基底クラスを提供するモジュール
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
from pathlib import Path
import os
import json
import datetime
import uuid

from sailing_data_processor.project.session_model import SessionModel, SessionResult


class SessionExporter(ABC):
    """
    セッション結果エクスポートの基底クラス
    
    このクラスを継承して、各種データフォーマット用のエクスポーターを実装します。
    """
    
    def __init__(self, template_manager=None, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        template_manager : Optional[TemplateManager]
            テンプレート管理クラスのインスタンス
        config : Optional[Dict[str, Any]]
            エクスポーター設定
        """
        self.template_manager = template_manager
        self.config = config or {}
        self.errors = []
        self.warnings = []
    
    @abstractmethod
    def export_session(self, session: SessionModel, output_path: str, 
                       template: str = "default", options: Dict[str, Any] = None) -> str:
        """
        単一セッションをエクスポート
        
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
        pass
    
    @abstractmethod
    def export_multiple_sessions(self, sessions: List[SessionModel], output_dir: str,
                                template: str = "default", options: Dict[str, Any] = None) -> List[str]:
        """
        複数セッションをエクスポート
        
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
        pass
    
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
    
    def generate_export_filename(self, session: SessionModel, extension: str, timestamp: bool = True) -> str:
        """
        エクスポートファイル名を生成
        
        Parameters
        ----------
        session : SessionModel
            ファイル名を生成するセッション
        extension : str
            ファイル拡張子 (.pdfなど)
        timestamp : bool, optional
            タイムスタンプを含めるかどうか, by default True
            
        Returns
        -------
        str
            生成されたファイル名
        """
        # ベースファイル名
        filename = f"{session.name.replace(' ', '_')}"
        
        # 日付情報を追加
        if session.event_date:
            try:
                # ISO形式の文字列からdatetimeオブジェクトに変換
                if isinstance(session.event_date, str):
                    event_date = datetime.datetime.fromisoformat(session.event_date)
                    date_str = event_date.strftime("%Y%m%d")
                    filename = f"{date_str}_{filename}"
                else:
                    # すでにdatetimeオブジェクトの場合
                    date_str = session.event_date.strftime("%Y%m%d")
                    filename = f"{date_str}_{filename}"
            except (ValueError, AttributeError):
                # 日付変換エラーの場合はスキップ
                pass
        
        # タイムスタンプを追加（現在の時刻）
        if timestamp:
            time_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename}_{time_str}"
        
        # 拡張子を追加
        if not extension.startswith('.'):
            extension = f".{extension}"
        filename = f"{filename}{extension}"
        
        return filename
