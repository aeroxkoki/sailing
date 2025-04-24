# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.renderer.base_renderer

レポートのレンダリングを担当する基底クラスを提供するモジュールです。
テンプレートをHTMLなどの出力形式に変換する機能を定義します。
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
from abc import ABC, abstractmethod
from pathlib import Path
import os
import json
import datetime

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.reporting.templates.template_model import (
    Template, Section, Element, TemplateOutputFormat
)


class BaseRenderer(ABC):
    """
    レポートレンダラーの基底クラス
    
    テンプレートを特定の出力形式にレンダリングするための基本機能を提供します。
    """
    
    def __init__(self, template: Template, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        template : Template
            レンダリング対象のテンプレート
        config : Optional[Dict[str, Any]], optional
            レンダラーの設定, by default None
        """
        self.template = template
        self.config = config or {}
        self.errors = []
        self.warnings = []
        
        # レンダリングコンテキスト
        self.context = {}
    
    def set_context(self, context: Dict[str, Any]) -> None:
        """
        レンダリングコンテキストを設定
        
        Parameters
        ----------
        context : Dict[str, Any]
            レンダリングコンテキスト
        """
        self.context = context
    
    def update_context(self, update_data: Dict[str, Any]) -> None:
        """
        レンダリングコンテキストを更新
        
        Parameters
        ----------
        update_data : Dict[str, Any]
            更新データ
        """
        self.context.update(update_data)
    
    def prepare_context(self, container: GPSDataContainer, 
                       additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        レンダリングコンテキストを準備
        
        Parameters
        ----------
        container : GPSDataContainer
            データコンテナ
        additional_context : Optional[Dict[str, Any]], optional
            追加のコンテキストデータ, by default None
        
        Returns
        -------
        Dict[str, Any]
            準備されたレンダリングコンテキスト
        """
        context = {}
        
        # コンテキストにコンテナデータを追加
        context["data"] = container.data
        context["metadata"] = container.metadata
        
        # 基本的なメタデータのショートカットを追加
        context["session_name"] = container.metadata.get("name", "")
        context["session_date"] = container.metadata.get("date", "")
        context["session_location"] = container.metadata.get("location", "")
        context["sailor_name"] = container.metadata.get("sailor_name", "")
        context["boat_name"] = container.metadata.get("boat_name", "")
        
        # 生成日時を追加
        context["generation_date"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 追加のコンテキストを適用
        if additional_context:
            context.update(additional_context)
        
        # 準備したコンテキストを保存
        self.set_context(context)
        
        return context
    
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
        """
        エラーメッセージと警告メッセージをクリア
        """
        self.errors = []
        self.warnings = []
    
    @abstractmethod
    def render(self) -> Any:
        """
        テンプレートをレンダリング
        
        Returns
        -------
        Any
            レンダリング結果
        """
        pass
    
    @abstractmethod
    def save(self, output_path: Union[str, Path, BinaryIO, TextIO]) -> bool:
        """
        レンダリング結果を保存
        
        Parameters
        ----------
        output_path : Union[str, Path, BinaryIO, TextIO]
            出力先
        
        Returns
        -------
        bool
            保存成功の場合はTrue
        """
        pass
