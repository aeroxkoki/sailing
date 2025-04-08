"""
sailing_data_processor.exporters.exporter_factory

エクスポーターを生成するファクトリークラスを提供するモジュール
"""

from typing import Dict, Any, Optional, Type

from sailing_data_processor.exporters.session_exporter import SessionExporter
from sailing_data_processor.exporters.pdf_exporter import PDFExporter
from sailing_data_processor.exporters.html_exporter import HTMLExporter
from sailing_data_processor.exporters.csv_exporter import CSVExporter
from sailing_data_processor.exporters.json_exporter import JSONExporter
from sailing_data_processor.exporters.template_manager import TemplateManager


class ExporterFactory:
    """
    エクスポーターを生成するファクトリークラス
    
    指定された形式に対応するエクスポーターを作成・管理します。
    """
    
    EXPORTERS = {
        'pdf': PDFExporter,
        'html': HTMLExporter,
        'csv': CSVExporter,
        'json': JSONExporter
    }
    
    def __init__(self, template_manager: Optional[TemplateManager] = None, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        template_manager : Optional[TemplateManager], optional
            テンプレート管理クラスのインスタンス, by default None
        config : Optional[Dict[str, Any]], optional
            エクスポーター設定, by default None
        """
        self.template_manager = template_manager
        self.config = config or {}
        self._exporters = {}  # キャッシュされたエクスポーターインスタンス
    
    def get_exporter(self, format_name: str) -> SessionExporter:
        """
        指定された形式のエクスポーターを取得
        
        Parameters
        ----------
        format_name : str
            エクスポート形式名 ('pdf', 'html', 'csv', 'json')
            
        Returns
        -------
        SessionExporter
            エクスポーターインスタンス
            
        Raises
        ------
        ValueError
            サポートされていない形式が指定された場合
        """
        format_name = format_name.lower()
        
        # サポートされていない形式の場合はエラー
        if format_name not in self.EXPORTERS:
            supported_formats = ", ".join(self.EXPORTERS.keys())
            raise ValueError(f"Unsupported export format: {format_name}. Supported formats: {supported_formats}")
        
        # キャッシュにない場合は新しいインスタンスを作成
        if format_name not in self._exporters:
            exporter_class = self.EXPORTERS[format_name]
            format_config = self.config.get(format_name, {})
            self._exporters[format_name] = exporter_class(self.template_manager, format_config)
        
        return self._exporters[format_name]
    
    def get_supported_formats(self) -> Dict[str, str]:
        """
        サポートされているエクスポート形式を取得
        
        Returns
        -------
        Dict[str, str]
            {形式名: 説明}の辞書
        """
        return {
            'pdf': "PDF文書 (ポータブルドキュメント形式)",
            'html': "HTMLウェブページ",
            'csv': "CSV (カンマ区切りテキスト)",
            'json': "JSON (JavaScriptオブジェクト表記)"
        }
    
    def register_exporter(self, format_name: str, exporter_class: Type[SessionExporter]) -> None:
        """
        カスタムエクスポーターを登録
        
        Parameters
        ----------
        format_name : str
            エクスポート形式名
        exporter_class : Type[SessionExporter]
            エクスポータークラス（SessionExporterのサブクラス）
            
        Raises
        ------
        TypeError
            指定されたクラスがSessionExporterのサブクラスでない場合
        """
        # クラスの型チェック
        if not issubclass(exporter_class, SessionExporter):
            raise TypeError(f"Exporter class must be a subclass of SessionExporter, got {exporter_class.__name__}")
        
        # エクスポーターを登録
        self.EXPORTERS[format_name.lower()] = exporter_class
        
        # キャッシュから削除（次回取得時に再作成される）
        if format_name.lower() in self._exporters:
            del self._exporters[format_name.lower()]
    
    def create_all_exporters(self) -> Dict[str, SessionExporter]:
        """
        すべてのエクスポーターインスタンスを作成
        
        Returns
        -------
        Dict[str, SessionExporter]
            {形式名: エクスポーターインスタンス}の辞書
        """
        # すべての形式に対応するエクスポーターを作成
        for format_name in self.EXPORTERS:
            self.get_exporter(format_name)
        
        return self._exporters.copy()
