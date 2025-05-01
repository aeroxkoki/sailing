# -*- coding: utf-8 -*-
"""
PDFエクスポーターモジュール

セーリングデータ分析結果を高品質なPDFレポートとして出力するための機能を提供します。
"""

import os
import logging
from pathlib import Path
import datetime
import tempfile
from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO, Tuple
import io

# 追加のライブラリ
try:
    import reportlab
    from reportlab.lib.pagesizes import A4, letter, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch, cm
    from reportlab.pdfgen import canvas
    from reportlab.platypus.flowables import KeepTogether
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# ベースクラスのインポート
from sailing_data_processor.reporting.exporters.base_exporter import BaseExporter
from sailing_data_processor.reporting.exporters.pdf_generator import PDFGenerator

logger = logging.getLogger(__name__)

class PDFExporter(BaseExporter):
    """
    PDFエクスポーター
    
    セーリングデータ分析結果を高品質なPDFレポートとして出力します。
    """
    
    def __init__(self, **options):
        """初期化"""
        super().__init__(**options)
        
        # PDFデフォルトオプション
        pdf_defaults = {
            "page_size": "A4",
            "orientation": "portrait",
            "margin": {"top": 2.5, "right": 2.5, "bottom": 2.5, "left": 2.5},
            "header": True,
            "footer": True,
            "page_numbers": True,
            "toc": False,
            "compression": True,
            "font": "Helvetica",
            "font_size": 11,
            "title": "",
            "author": "",
            "subject": "",
            "watermark": "",
            "render_method": "reportlab"  # 'reportlab' または 'weasyprint'
        }
        
        self.options.update(pdf_defaults)
        self.options.update(options)
        
        # PDFジェネレータ
        self.pdf_generator = PDFGenerator(self.options)
        
        # レンダリング方法の確認と設定
        self._setup_renderer()
    
    def _setup_renderer(self):
        """レンダラーの設定"""
        render_method = self.options.get("render_method", "reportlab")
        
        if render_method == "reportlab" and not REPORTLAB_AVAILABLE:
            self.add_warning("ReportLabが利用できないため、WeasyPrintを使用します。")
            render_method = "weasyprint"
        
        if render_method == "weasyprint" and not WEASYPRINT_AVAILABLE:
            self.add_warning("WeasyPrintが利用できないため、ReportLabを使用します。")
            render_method = "reportlab"
        
        if not REPORTLAB_AVAILABLE and not WEASYPRINT_AVAILABLE:
            self.add_error("PDF生成に必要なライブラリがインストールされていません。pip install reportlab weasyprint を実行してください。")
            return
        
        self.options["render_method"] = render_method
        self.pdf_generator.options["render_method"] = render_method
    
    def export(self, data, template=None, **kwargs):
        """
        データをPDFとしてエクスポート
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        template : Optional[str]
            使用するテンプレート名（または直接HTMLテンプレート）
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
            output_path = os.path.join(
                tempfile.mkdtemp(),
                self.generate_filename(data, 'pdf')
            )
        
        # ディレクトリの存在確認と作成
        self.ensure_directory(output_path)
        
        try:
            # PDFの生成方法の選択
            render_method = self.options.get("render_method", "reportlab")
            
            if render_method == "reportlab":
                pdf_content = self.pdf_generator.generate_reportlab_pdf(data, template, **kwargs)
            elif render_method == "weasyprint":
                pdf_content = self.pdf_generator.generate_weasyprint_pdf(data, template, **kwargs)
            else:
                self.add_error(f"未対応のレンダリング方法: {render_method}")
                return None
            
            if pdf_content is None:
                self.add_error("PDFコンテンツの生成に失敗しました。")
                return None
                
            # ファイルに書き込む場合
            if isinstance(output_path, (str, Path)):
                with open(output_path, "wb") as f:
                    f.write(pdf_content)
                return str(output_path)
            elif hasattr(output_path, "write"):
                # ファイルオブジェクトに直接書き込む
                output_path.write(pdf_content)
                return None
            
        except Exception as e:
            self.add_error(f"PDF生成中にエラーが発生しました: {str(e)}")
            logger.error(f"PDF generation failed: {str(e)}", exc_info=True)
            return None
    
    def validate_options(self):
        """
        オプションの検証
        
        Returns
        -------
        bool
            検証結果
        """
        # PDFライブラリの確認
        if not REPORTLAB_AVAILABLE and not WEASYPRINT_AVAILABLE:
            self.add_error("PDF生成には少なくとも一つのライブラリが必要です。pip install reportlab weasyprint のいずれかを実行してください。")
            return False
        
        # ページサイズの検証
        page_size = self.options.get("page_size", "A4")
        if page_size not in ["A4", "letter"]:
            self.add_warning(f"未対応のページサイズ: {page_size}, 'A4'を使用します。")
            self.options["page_size"] = "A4"
        
        # 向きの検証
        orientation = self.options.get("orientation", "portrait")
        if orientation not in ["portrait", "landscape"]:
            self.add_warning(f"未対応の向き: {orientation}, 'portrait'を使用します。")
            self.options["orientation"] = "portrait"
        
        # マージンの検証
        margin = self.options.get("margin", {})
        if not isinstance(margin, dict):
            self.add_warning("無効なマージン設定です。デフォルト値を使用します。")
            self.options["margin"] = {"top": 2.5, "right": 2.5, "bottom": 2.5, "left": 2.5}
        
        return True
    
    def get_supported_formats(self):
        """
        サポートするフォーマットのリストを取得
        
        Returns
        -------
        List[str]
            サポートするフォーマットのリスト
        """
        return ["pdf", "pdf_report", "pdf_detailed", "pdf_summary"]