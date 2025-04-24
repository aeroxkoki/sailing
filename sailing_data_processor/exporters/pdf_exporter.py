# -*- coding: utf-8 -*-
"""
sailing_data_processor.exporters.pdf_exporter

セッション結果をPDF形式でエクスポートするモジュール
"""

import os
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import datetime

from fpdf import FPDF

from sailing_data_processor.project.session_model import SessionModel, SessionResult
from sailing_data_processor.exporters.session_exporter import SessionExporter


class PDFExporter(SessionExporter):
    """
    PDF形式でセッション結果をエクスポートするクラス
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
        単一セッションをPDFでエクスポート
        
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
                template_data = self.template_manager.get_template(template, "pdf")
            except Exception as e:
                self.warnings.append(f"テンプレートの読み込みに失敗しました: {e}")
                # デフォルト設定で続行
        
        # 出力先ディレクトリの確認
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # PDFの設定
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # フォント設定
        font_family = template_data.get("styles", {}).get("font_family", "Arial")
        if "," in font_family:
            # 複数のフォントが指定されている場合は最初のものを使用
            font_family = font_family.split(",")[0].strip()
        
        # 標準フォントのみサポート（Arial, Courier, Helvetica, Times, Symbol, ZapfDingbats）
        if font_family.lower() not in ["arial", "courier", "helvetica", "times", "symbol", "zapfdingbats"]:
            font_family = "Arial"
        
        pdf.set_font(font_family, size=template_data.get("styles", {}).get("base_font_size", 10))
        
        # カラー設定
        colors = template_data.get("styles", {}).get("colors", {})
        primary_color = colors.get("primary", "#1565C0")
        text_color = colors.get("text", "#212121")
        
        # HEX色をRGBに変換
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        primary_rgb = hex_to_rgb(primary_color)
        text_rgb = hex_to_rgb(text_color)
        
        # ヘッダーを追加
        self._add_header(pdf, session, template_data, options)
        
        # メタデータセクションを追加
        if "include_metadata" not in options or options["include_metadata"]:
            self._add_metadata_section(pdf, session, template_data, options)
        
        # 結果セクションを追加
        if "include_results" not in options or options["include_results"]:
            self._add_results_section(pdf, session, template_data, options)
        
        # フッターを追加
        self._add_footer(pdf, session, template_data, options)
        
        # PDFを保存
        try:
            pdf.output(output_path)
        except Exception as e:
            self.errors.append(f"PDFの保存に失敗しました: {e}")
            raise
        
        return output_path
    
    def export_multiple_sessions(self, sessions: List[SessionModel], output_dir: str,
                                template: str = "default", options: Dict[str, Any] = None) -> List[str]:
        """
        複数セッションをPDFでエクスポート
        
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
        
        # 各セッションをエクスポート
        for session in sessions:
            try:
                # ファイル名の生成
                filename = self.generate_export_filename(session, "pdf")
                output_path = os.path.join(output_dir, filename)
                
                # エクスポート実行
                exported_file = self.export_session(session, output_path, template, options)
                export_files.append(exported_file)
            except Exception as e:
                self.errors.append(f"セッション '{session.name}' のエクスポートに失敗しました: {e}")
        
        return export_files
    
    def _add_header(self, pdf: FPDF, session: SessionModel, template_data: Dict[str, Any], options: Dict[str, Any]) -> None:
        """
        ヘッダーを追加
        
        Parameters
        ----------
        pdf : FPDF
            PDFオブジェクト
        session : SessionModel
            セッション
        template_data : Dict[str, Any]
            テンプレートデータ
        options : Dict[str, Any]
            エクスポートオプション
        """
        # テンプレートからヘッダー設定を取得
        header_config = template_data.get("metadata", {}).get("header", {})
        
        # タイトルを追加
        if header_config.get("include_title", True):
            pdf.set_font("", "B", 16)
            pdf.cell(0, 10, session.name, ln=True, align="C")
            pdf.ln(5)
        
        # 日付を追加
        if header_config.get("include_date", True):
            date_str = ""
            if session.event_date:
                try:
                    if isinstance(session.event_date, str):
                        event_date = datetime.datetime.fromisoformat(session.event_date)
                        date_str = event_date.strftime("%Y年%m月%d日")
                    else:
                        date_str = session.event_date.strftime("%Y年%m月%d日")
                except (ValueError, AttributeError):
                    pass
            
            if date_str:
                pdf.set_font("", "", 10)
                pdf.cell(0, 6, f"セッション日: {date_str}", ln=True, align="R")
        
        # 区切り線
        pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
        pdf.ln(5)
    
    def _add_metadata_section(self, pdf: FPDF, session: SessionModel, template_data: Dict[str, Any], options: Dict[str, Any]) -> None:
        """
        メタデータセクションを追加
        
        Parameters
        ----------
        pdf : FPDF
            PDFオブジェクト
        session : SessionModel
            セッション
        template_data : Dict[str, Any]
            テンプレートデータ
        options : Dict[str, Any]
            エクスポートオプション
        """
        # テンプレートからセクション設定を取得
        section_enabled = True
        for section in template_data.get("sections", []):
            if section["name"] == "metadata":
                section_enabled = section.get("enabled", True)
                break
        
        if not section_enabled:
            return
        
        # セクションタイトル
        pdf.set_font("", "B", 14)
        pdf.cell(0, 10, "セッション情報", ln=True, align="L")
        pdf.ln(2)
        
        # メタデータ項目
        pdf.set_font("", "", 10)
        
        # 基本情報
        self._add_metadata_item(pdf, "説明", session.description)
        self._add_metadata_item(pdf, "目的", session.purpose)
        self._add_metadata_item(pdf, "ステータス", session.status)
        self._add_metadata_item(pdf, "カテゴリ", session.category)
        self._add_metadata_item(pdf, "場所", session.location)
        
        # 評価
        rating_stars = "★" * session.rating + "☆" * (5 - session.rating)
        self._add_metadata_item(pdf, "評価", rating_stars)
        
        # タグ
        if session.tags:
            tags_text = ", ".join(session.tags)
            self._add_metadata_item(pdf, "タグ", tags_text)
        
        # 重要度
        importance_map = {
            "low": "低",
            "normal": "普通",
            "high": "高",
            "critical": "最重要"
        }
        importance_text = importance_map.get(session.importance, session.importance)
        self._add_metadata_item(pdf, "重要度", importance_text)
        
        # 完了率
        if hasattr(session, "completion_percentage"):
            self._add_metadata_item(pdf, "完了率", f"{session.completion_percentage}%")
        
        # 追加のメタデータ（船種など）
        if "boat_type" in session.metadata:
            self._add_metadata_item(pdf, "船種", session.metadata["boat_type"])
        
        if "course_type" in session.metadata:
            self._add_metadata_item(pdf, "コース種類", session.metadata["course_type"])
        
        if "wind_condition" in session.metadata:
            self._add_metadata_item(pdf, "風の状態", session.metadata["wind_condition"])
        
        if "avg_wind_speed" in session.metadata:
            self._add_metadata_item(pdf, "平均風速", f"{session.metadata['avg_wind_speed']} ノット")
        
        # 区切り線
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
    
    def _add_metadata_item(self, pdf: FPDF, label: str, value: str) -> None:
        """
        メタデータ項目を追加
        
        Parameters
        ----------
        pdf : FPDF
            PDFオブジェクト
        label : str
            ラベル
        value : str
            値
        """
        if not value:
            return
        
        pdf.set_font("", "B", 10)
        pdf.cell(30, 6, f"{label}:", 0, 0)
        pdf.set_font("", "", 10)
        pdf.multi_cell(0, 6, str(value), 0, "L")
    
    def _add_results_section(self, pdf: FPDF, session: SessionModel, template_data: Dict[str, Any], options: Dict[str, Any]) -> None:
        """
        結果セクションを追加
        
        Parameters
        ----------
        pdf : FPDF
            PDFオブジェクト
        session : SessionModel
            セッション
        template_data : Dict[str, Any]
            テンプレートデータ
        options : Dict[str, Any]
            エクスポートオプション
        """
        # 結果がない場合はスキップ
        if not hasattr(session, "results") or not session.results:
            return
        
        # セクションタイトル
        pdf.set_font("", "B", 14)
        pdf.cell(0, 10, "分析結果", ln=True, align="L")
        pdf.ln(2)
        
        # 結果がある場合はここに表示（例えば結果の数や種類など）
        pdf.set_font("", "", 10)
        pdf.cell(0, 6, f"分析結果数: {len(session.results)}", ln=True)
        
        # 結果の詳細は実際のデータがないとここには表示できません
        # 実際の結果データがあれば、それぞれのタイプに応じた表示が可能
        
        # 区切り線
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
    
    def _add_footer(self, pdf: FPDF, session: SessionModel, template_data: Dict[str, Any], options: Dict[str, Any]) -> None:
        """
        フッターを追加
        
        Parameters
        ----------
        pdf : FPDF
            PDFオブジェクト
        session : SessionModel
            セッション
        template_data : Dict[str, Any]
            テンプレートデータ
        options : Dict[str, Any]
            エクスポートオプション
        """
        # テンプレートからフッター設定を取得
        footer_config = template_data.get("metadata", {}).get("footer", {})
        
        # カスタムフッターの設定
        def footer():
            # フッターの位置
            pdf.set_y(-15)
            pdf.set_font("Arial", "I", 8)
            
            # タイムスタンプ
            if footer_config.get("include_timestamp", True):
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                pdf.cell(0, 10, f"出力日時: {timestamp}", 0, 0, "L")
            
            # ページ番号
            if footer_config.get("include_page_number", True):
                pdf.cell(0, 10, f"ページ {pdf.page_no()}", 0, 0, "R")
        
        # フッター関数を設定
        pdf.set_footer_func(footer)
