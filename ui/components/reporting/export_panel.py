"""
ui.components.reporting.export_panel

レポートのエクスポート設定パネルモジュール
"""

import streamlit as st
import os
import datetime
import tempfile
from typing import Dict, Any, List, Optional, Callable, Union
import logging

# 必要なモジュールのインポート
try:
    from sailing_data_processor.reporting.exporters.base_exporter import BaseExporter
    from sailing_data_processor.reporting.exporters.pdf_exporter import PDFExporter
    from sailing_data_processor.reporting.exporters.html_exporter import HTMLExporter
    from sailing_data_processor.reporting.exporters.excel_exporter import ExcelExporter
    from sailing_data_processor.reporting.exporters.image_exporter import ImageExporter
    from sailing_data_processor.reporting.exporters.data_exporter import DataExporter
except ImportError:
    # 開発中の例外処理
    logging.warning("エクスポーターモジュールのインポートに失敗しました。モックオブジェクトを使用します。")
    class BaseExporter:
        def __init__(self, **options):
            self.options = options
        def export(self, data, template=None, **kwargs):
            return None
    
    class PDFExporter(BaseExporter): pass
    class HTMLExporter(BaseExporter): pass
    class ExcelExporter(BaseExporter): pass
    class ImageExporter(BaseExporter): pass
    class DataExporter(BaseExporter): pass


class ExportPanel:
    """
    レポートのエクスポート設定パネル
    
    各種形式（PDF、HTML、Excel、画像、データ）のエクスポート設定UIを提供します。
    """
    
    def __init__(self, key="export_panel", on_export=None):
        """
        初期化
        
        Parameters
        ----------
        key : str, optional
            コンポーネントのキー
        on_export : Callable, optional
            エクスポート実行時のコールバック関数
        """
        self.key = key
        self.on_export = on_export
        
        # セッション状態の初期化
        if f"{key}_format" not in st.session_state:
            st.session_state[f"{key}_format"] = "pdf"
        if f"{key}_options" not in st.session_state:
            st.session_state[f"{key}_options"] = {}
        if f"{key}_template" not in st.session_state:
            st.session_state[f"{key}_template"] = "default"
        if f"{key}_filename" not in st.session_state:
            st.session_state[f"{key}_filename"] = f"report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if f"{key}_output_path" not in st.session_state:
            st.session_state[f"{key}_output_path"] = ""
        if f"{key}_preview_data" not in st.session_state:
            st.session_state[f"{key}_preview_data"] = None
    
    def render(self, data=None):
        """
        コンポーネントのレンダリング
        
        Parameters
        ----------
        data : Any, optional
            エクスポート対象のデータ
        
        Returns
        -------
        Dict
            現在のエクスポート設定
        """
        # 現在のエクスポート形式
        current_format = st.session_state[f"{self.key}_format"]
        
        # 形式選択UI
        st.subheader("エクスポート形式")
        
        # 形式選択タブ
        format_tabs = st.tabs(["PDF", "HTML", "Excel", "画像", "データ"])
        
        # 形式タブの選択
        with format_tabs[0]:  # PDF
            if st.button("PDF形式を選択", key=f"{self.key}_select_pdf", use_container_width=True):
                st.session_state[f"{self.key}_format"] = "pdf"
                st.experimental_rerun()
        
        with format_tabs[1]:  # HTML
            if st.button("HTML形式を選択", key=f"{self.key}_select_html", use_container_width=True):
                st.session_state[f"{self.key}_format"] = "html"
                st.experimental_rerun()
        
        with format_tabs[2]:  # Excel
            if st.button("Excel形式を選択", key=f"{self.key}_select_excel", use_container_width=True):
                st.session_state[f"{self.key}_format"] = "excel"
                st.experimental_rerun()
        
        with format_tabs[3]:  # 画像
            if st.button("画像形式を選択", key=f"{self.key}_select_image", use_container_width=True):
                st.session_state[f"{self.key}_format"] = "image"
                st.experimental_rerun()
        
        with format_tabs[4]:  # データ
            if st.button("データ形式を選択", key=f"{self.key}_select_data", use_container_width=True):
                st.session_state[f"{self.key}_format"] = "data"
                st.experimental_rerun()
        
        # 選択された形式に応じたオプション表示
        st.subheader(f"{current_format.upper()}エクスポート設定")
        
        # 共通設定
        output_path = st.text_input(
            "出力先パス（空欄で自動生成）",
            value=st.session_state[f"{self.key}_output_path"],
            key=f"{self.key}_output_path_input",
            help="エクスポートファイルを保存するパス。空欄の場合は一時ディレクトリに保存されます。"
        )
        st.session_state[f"{self.key}_output_path"] = output_path
        
        filename = st.text_input(
            "ファイル名（拡張子なし）",
            value=st.session_state[f"{self.key}_filename"],
            key=f"{self.key}_filename_input",
            help="エクスポートファイルのファイル名（拡張子なし）"
        )
        st.session_state[f"{self.key}_filename"] = filename
        
        # 形式別オプション表示
        options = st.session_state[f"{self.key}_options"]
        updated_options = self._render_format_options(current_format, options)
        st.session_state[f"{self.key}_options"] = updated_options
        
        # プレビューとエクスポートボタン
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("プレビュー", key=f"{self.key}_preview_button", use_container_width=True):
                if data is not None:
                    preview_data = self._generate_preview(data, current_format, updated_options)
                    st.session_state[f"{self.key}_preview_data"] = preview_data
                    
                    # プレビューが生成された場合、サクセスメッセージを表示
                    if preview_data:
                        st.success("プレビューが生成されました。")
                else:
                    st.warning("プレビュー対象のデータがありません。")
        
        with col2:
            if st.button("エクスポート", key=f"{self.key}_export_button", use_container_width=True):
                if data is not None:
                    # エクスポート処理
                    result = self._export_data(data, current_format, updated_options)
                    
                    if result:
                        st.success(f"エクスポートが完了しました: {result}")
                        
                        # コールバック関数の呼び出し
                        if self.on_export:
                            self.on_export(result, current_format, updated_options)
                else:
                    st.warning("エクスポート対象のデータがありません。")
        
        # プレビュー表示
        preview_data = st.session_state.get(f"{self.key}_preview_data")
        if preview_data:
            with st.expander("プレビュー", expanded=True):
                self._render_preview(preview_data, current_format)
        
        # 現在の設定を返す
        return {
            "format": current_format,
            "options": updated_options,
            "filename": filename,
            "output_path": output_path
        }
    
    def _render_format_options(self, format_type, current_options):
        """
        形式ごとのオプションUI表示
        
        Parameters
        ----------
        format_type : str
            エクスポート形式
        current_options : Dict
            現在のオプション設定
        
        Returns
        -------
        Dict
            更新されたオプション設定
        """
        # 形式ごとのオプションUIを表示
        options = current_options.copy()
        
        # テンプレート選択 (共通)
        template_options = ["default", "detailed", "summary"]
        template = st.selectbox(
            "テンプレート",
            options=template_options,
            index=template_options.index(options.get("template", "default")) if options.get("template", "default") in template_options else 0,
            key=f"{self.key}_{format_type}_template"
        )
        options["template"] = template
        
        # メタデータの表示 (共通)
        include_metadata = st.checkbox(
            "メタデータを含める",
            value=options.get("include_metadata", True),
            key=f"{self.key}_{format_type}_metadata"
        )
        options["include_metadata"] = include_metadata
        
        # 形式別の詳細オプション
        with st.expander("詳細オプション", expanded=False):
            if format_type == "pdf":
                # PDF固有オプション
                col1, col2 = st.columns(2)
                
                with col1:
                    page_size = st.selectbox(
                        "ページサイズ",
                        options=["A4", "Letter", "Legal"],
                        index=["A4", "Letter", "Legal"].index(options.get("page_size", "A4")),
                        key=f"{self.key}_pdf_page_size"
                    )
                    options["page_size"] = page_size
                
                with col2:
                    orientation = st.selectbox(
                        "向き",
                        options=["portrait", "landscape"],
                        index=["portrait", "landscape"].index(options.get("orientation", "portrait")),
                        format_func=lambda x: "縦向き" if x == "portrait" else "横向き",
                        key=f"{self.key}_pdf_orientation"
                    )
                    options["orientation"] = orientation
                
                include_toc = st.checkbox(
                    "目次を含める",
                    value=options.get("toc", False),
                    key=f"{self.key}_pdf_toc"
                )
                options["toc"] = include_toc
                
                include_page_numbers = st.checkbox(
                    "ページ番号を含める",
                    value=options.get("page_numbers", True),
                    key=f"{self.key}_pdf_page_numbers"
                )
                options["page_numbers"] = include_page_numbers
                
                compression = st.checkbox(
                    "圧縮する",
                    value=options.get("compression", True),
                    key=f"{self.key}_pdf_compression"
                )
                options["compression"] = compression
                
                font = st.selectbox(
                    "フォント",
                    options=["Helvetica", "Times", "Courier"],
                    index=["Helvetica", "Times", "Courier"].index(options.get("font", "Helvetica")),
                    key=f"{self.key}_pdf_font"
                )
                options["font"] = font
                
                font_size = st.slider(
                    "フォントサイズ",
                    min_value=8,
                    max_value=16,
                    value=options.get("font_size", 11),
                    key=f"{self.key}_pdf_font_size"
                )
                options["font_size"] = font_size
                
                title = st.text_input(
                    "タイトル",
                    value=options.get("title", "セーリングデータ分析レポート"),
                    key=f"{self.key}_pdf_title"
                )
                options["title"] = title
                
                author = st.text_input(
                    "作成者",
                    value=options.get("author", ""),
                    key=f"{self.key}_pdf_author"
                )
                options["author"] = author
                
                render_method = st.radio(
                    "レンダリング方法",
                    options=["reportlab", "weasyprint"],
                    index=0 if options.get("render_method", "reportlab") == "reportlab" else 1,
                    key=f"{self.key}_pdf_render_method",
                    horizontal=True
                )
                options["render_method"] = render_method
                
            elif format_type == "html":
                # HTML固有オプション
                theme = st.selectbox(
                    "テーマ",
                    options=["default", "dark", "light", "blue", "green"],
                    index=["default", "dark", "light", "blue", "green"].index(options.get("theme", "default")),
                    key=f"{self.key}_html_theme"
                )
                options["theme"] = theme
                
                include_interactive = st.checkbox(
                    "インタラクティブ要素を含める",
                    value=options.get("include_interactive", True),
                    key=f"{self.key}_html_interactive"
                )
                options["include_interactive"] = include_interactive
                
                include_charts = st.checkbox(
                    "チャートを含める",
                    value=options.get("include_charts", True),
                    key=f"{self.key}_html_charts"
                )
                options["include_charts"] = include_charts
                
                include_map = st.checkbox(
                    "マップを含める",
                    value=options.get("include_map", True),
                    key=f"{self.key}_html_map"
                )
                options["include_map"] = include_map
                
                include_navbar = st.checkbox(
                    "ナビゲーションバーを含める",
                    value=options.get("include_navbar", True),
                    key=f"{self.key}_html_navbar"
                )
                options["include_navbar"] = include_navbar
                
                css_framework = st.selectbox(
                    "CSSフレームワーク",
                    options=["bootstrap", "bulma", "tailwind", "none"],
                    index=["bootstrap", "bulma", "tailwind", "none"].index(options.get("css_framework", "bootstrap")),
                    key=f"{self.key}_html_css_framework"
                )
                options["css_framework"] = css_framework
                
                self_contained = st.checkbox(
                    "自己完結型HTML（1ファイル）",
                    value=options.get("self_contained", True),
                    key=f"{self.key}_html_self_contained"
                )
                options["self_contained"] = self_contained
                
            elif format_type == "excel":
                # Excel固有オプション
                engine = st.radio(
                    "Excelエンジン",
                    options=["auto", "openpyxl", "xlsxwriter"],
                    index=0 if options.get("engine", "auto") == "auto" else 1 if options.get("engine", "auto") == "openpyxl" else 2,
                    key=f"{self.key}_excel_engine",
                    horizontal=True
                )
                options["engine"] = engine
                
                include_charts = st.checkbox(
                    "チャートを含める",
                    value=options.get("include_charts", True),
                    key=f"{self.key}_excel_charts"
                )
                options["include_charts"] = include_charts
                
                include_formulas = st.checkbox(
                    "数式を含める",
                    value=options.get("include_formulas", True),
                    key=f"{self.key}_excel_formulas"
                )
                options["include_formulas"] = include_formulas
                
                freeze_panes = st.checkbox(
                    "ペインを固定",
                    value=options.get("freeze_panes", True),
                    key=f"{self.key}_excel_freeze_panes"
                )
                options["freeze_panes"] = freeze_panes
                
                auto_filter = st.checkbox(
                    "自動フィルターを有効化",
                    value=options.get("auto_filter", True),
                    key=f"{self.key}_excel_auto_filter"
                )
                options["auto_filter"] = auto_filter
                
            elif format_type == "image":
                # 画像固有オプション
                image_format = st.selectbox(
                    "画像形式",
                    options=["png", "jpeg", "svg"],
                    index=["png", "jpeg", "svg"].index(options.get("format", "png")),
                    key=f"{self.key}_image_format"
                )
                options["format"] = image_format
                
                dpi = st.slider(
                    "DPI（解像度）",
                    min_value=72,
                    max_value=600,
                    value=options.get("dpi", 300),
                    key=f"{self.key}_image_dpi"
                )
                options["dpi"] = dpi
                
                col1, col2 = st.columns(2)
                
                with col1:
                    width = st.number_input(
                        "幅（ピクセル）",
                        min_value=100,
                        max_value=3000,
                        value=options.get("width", 1200),
                        key=f"{self.key}_image_width"
                    )
                    options["width"] = width
                
                with col2:
                    height = st.number_input(
                        "高さ（ピクセル）",
                        min_value=100,
                        max_value=3000,
                        value=options.get("height", 800),
                        key=f"{self.key}_image_height"
                    )
                    options["height"] = height
                
                content_type = st.radio(
                    "画像内容",
                    options=["chart", "map", "combined"],
                    index=["chart", "map", "combined"].index(options.get("content_type", "chart")),
                    format_func=lambda x: "チャート" if x == "chart" else "マップ" if x == "map" else "複合",
                    key=f"{self.key}_image_content_type",
                    horizontal=True
                )
                options["content_type"] = content_type
                
                if content_type == "chart":
                    chart_type = st.selectbox(
                        "チャートタイプ",
                        options=["line", "bar", "scatter", "pie"],
                        index=["line", "bar", "scatter", "pie"].index(options.get("chart_type", "line")),
                        format_func=lambda x: "線グラフ" if x == "line" else "棒グラフ" if x == "bar" else "散布図" if x == "scatter" else "円グラフ",
                        key=f"{self.key}_image_chart_type"
                    )
                    options["chart_type"] = chart_type
                
                elif content_type == "map":
                    map_type = st.selectbox(
                        "マップタイプ",
                        options=["track", "heatmap"],
                        index=["track", "heatmap"].index(options.get("map_type", "track")),
                        format_func=lambda x: "トラック" if x == "track" else "ヒートマップ",
                        key=f"{self.key}_image_map_type"
                    )
                    options["map_type"] = map_type
                
                background_color = st.color_picker(
                    "背景色",
                    value=options.get("background_color", "#FFFFFF"),
                    key=f"{self.key}_image_background_color"
                )
                options["background_color"] = background_color
                
                transparent = st.checkbox(
                    "透過背景",
                    value=options.get("transparent", False),
                    key=f"{self.key}_image_transparent"
                )
                options["transparent"] = transparent
                
                style = st.selectbox(
                    "スタイル",
                    options=["default", "seaborn", "ggplot", "dark_background", "fivethirtyeight"],
                    index=["default", "seaborn", "ggplot", "dark_background", "fivethirtyeight"].index(options.get("style", "default")),
                    key=f"{self.key}_image_style"
                )
                options["style"] = style
                
            elif format_type == "data":
                # データ固有オプション
                data_format = st.selectbox(
                    "データ形式",
                    options=["csv", "json", "xml"],
                    index=["csv", "json", "xml"].index(options.get("format", "csv")),
                    key=f"{self.key}_data_format"
                )
                options["format"] = data_format
                
                if data_format == "csv":
                    delimiter = st.selectbox(
                        "区切り文字",
                        options=[",", ";", "\\t"],
                        index=[",", ";", "\\t"].index(options.get("delimiter", ",")),
                        format_func=lambda x: "カンマ (,)" if x == "," else "セミコロン (;)" if x == ";" else "タブ (\\t)",
                        key=f"{self.key}_data_delimiter"
                    )
                    options["delimiter"] = delimiter
                    
                    encoding = st.selectbox(
                        "エンコーディング",
                        options=["utf-8", "shift-jis", "euc-jp"],
                        index=["utf-8", "shift-jis", "euc-jp"].index(options.get("encoding", "utf-8")),
                        key=f"{self.key}_data_encoding"
                    )
                    options["encoding"] = encoding
                    
                    include_header = st.checkbox(
                        "ヘッダーを含める",
                        value=options.get("include_header", True),
                        key=f"{self.key}_data_header"
                    )
                    options["include_header"] = include_header
                    
                    include_bom = st.checkbox(
                        "BOMを含める（Excel対応）",
                        value=options.get("include_bom", True),
                        key=f"{self.key}_data_bom"
                    )
                    options["include_bom"] = include_bom
                
                elif data_format == "json":
                    pretty_print = st.checkbox(
                        "整形して出力 (Pretty Print)",
                        value=options.get("pretty_print", True),
                        key=f"{self.key}_data_pretty"
                    )
                    options["pretty_print"] = pretty_print
                    
                    json_orient = st.radio(
                        "JSON形式",
                        options=["records", "columns", "split"],
                        index=["records", "columns", "split"].index(options.get("json_orient", "records")),
                        format_func=lambda x: "レコード形式" if x == "records" else "列形式" if x == "columns" else "分割形式",
                        key=f"{self.key}_data_json_orient",
                        horizontal=True
                    )
                    options["json_orient"] = json_orient
                
                elif data_format == "xml":
                    xml_root = st.text_input(
                        "XMLルート要素名",
                        value=options.get("xml_root", "data"),
                        key=f"{self.key}_data_xml_root"
                    )
                    options["xml_root"] = xml_root
                    
                    xml_row = st.text_input(
                        "XMLレコード要素名",
                        value=options.get("xml_row", "row"),
                        key=f"{self.key}_data_xml_row"
                    )
                    options["xml_row"] = xml_row
                
                # データフィルタリングオプション
                with st.expander("フィルタリングオプション", expanded=False):
                    include_nulls = st.checkbox(
                        "NULL値を含める",
                        value=options.get("include_nulls", False),
                        key=f"{self.key}_data_nulls"
                    )
                    options["include_nulls"] = include_nulls
                    
                    date_format = st.text_input(
                        "日付フォーマット",
                        value=options.get("date_format", "%Y-%m-%d %H:%M:%S"),
                        key=f"{self.key}_data_date_format"
                    )
                    options["date_format"] = date_format
                    
                    float_format = st.text_input(
                        "数値フォーマット",
                        value=options.get("float_format", "%.6f"),
                        key=f"{self.key}_data_float_format"
                    )
                    options["float_format"] = float_format
                
                # 圧縮オプション
                compress = st.checkbox(
                    "圧縮する",
                    value=options.get("compress", False),
                    key=f"{self.key}_data_compress"
                )
                options["compress"] = compress
                
                if compress:
                    compression_format = st.radio(
                        "圧縮形式",
                        options=["zip", "gzip"],
                        index=0 if options.get("compression_format", "zip") == "zip" else 1,
                        key=f"{self.key}_data_compression_format",
                        horizontal=True
                    )
                    options["compression_format"] = compression_format
        
        return options
    
    def _generate_preview(self, data, format_type, options):
        """
        プレビューの生成
        
        Parameters
        ----------
        data : Any
            プレビュー対象のデータ
        format_type : str
            エクスポート形式
        options : Dict
            エクスポートオプション
        
        Returns
        -------
        Any
            プレビューデータ
        """
        try:
            # 一時ファイルでエクスポートしてプレビュー生成
            temp_dir = tempfile.TemporaryDirectory()
            temp_path = os.path.join(temp_dir.name, f"preview.{format_type}")
            
            # エクスポーター選択とプレビュー生成
            exporter = self._get_exporter(format_type, options)
            if exporter:
                # プレビュー用オプションの調整
                preview_options = options.copy()
                preview_options["output_path"] = temp_path
                
                # エクスポート実行
                result_path = exporter.export(data, template=options.get("template"), **preview_options)
                
                if result_path and os.path.exists(result_path):
                    # プレビューデータの読み込み
                    with open(result_path, "rb") as f:
                        preview_data = f.read()
                    
                    # プレビューデータを返す
                    return {
                        "data": preview_data,
                        "format": format_type,
                        "path": result_path
                    }
            
            return None
        
        except Exception as e:
            st.error(f"プレビュー生成中にエラーが発生しました: {str(e)}")
            return None
    
    def _render_preview(self, preview_data, format_type):
        """
        プレビューの表示
        
        Parameters
        ----------
        preview_data : Dict
            プレビューデータ
        format_type : str
            エクスポート形式
        """
        if not preview_data or "data" not in preview_data:
            st.warning("プレビューデータがありません。")
            return
        
        data = preview_data["data"]
        
        if format_type == "pdf":
            # PDFプレビュー
            st.download_button(
                label="PDFをダウンロード",
                data=data,
                file_name=f"preview.pdf",
                mime="application/pdf"
            )
            st.info("PDFプレビューはダウンロードして確認してください。")
            
        elif format_type == "html":
            # HTMLプレビュー
            try:
                html_str = data.decode("utf-8")
                st.components.v1.html(html_str, height=500, scrolling=True)
            except:
                st.download_button(
                    label="HTMLをダウンロード",
                    data=data,
                    file_name=f"preview.html",
                    mime="text/html"
                )
                st.info("HTMLプレビューはダウンロードして確認してください。")
            
        elif format_type == "excel":
            # Excelプレビュー
            st.download_button(
                label="Excelファイルをダウンロード",
                data=data,
                file_name=f"preview.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.info("Excelプレビューはダウンロードして確認してください。")
            
        elif format_type == "image":
            # 画像プレビュー
            st.image(data)
            
        elif format_type == "data":
            # データプレビュー（CSVやJSON）
            try:
                if preview_data.get("format") == "csv":
                    text_data = data.decode("utf-8")
                    st.text_area("CSVプレビュー", text_data, height=300)
                elif preview_data.get("format") == "json":
                    text_data = data.decode("utf-8")
                    st.json(text_data)
                elif preview_data.get("format") == "xml":
                    text_data = data.decode("utf-8")
                    st.text_area("XMLプレビュー", text_data, height=300)
                else:
                    st.text_area("データプレビュー", data.decode("utf-8"), height=300)
            except:
                st.download_button(
                    label="データファイルをダウンロード",
                    data=data,
                    file_name=f"preview.{preview_data.get('format', 'txt')}",
                    mime="text/plain"
                )
                st.info("データプレビューはダウンロードして確認してください。")
    
    def _export_data(self, data, format_type, options):
        """
        データのエクスポート
        
        Parameters
        ----------
        data : Any
            エクスポート対象のデータ
        format_type : str
            エクスポート形式
        options : Dict
            エクスポートオプション
        
        Returns
        -------
        str
            エクスポートされたファイルのパス
        """
        try:
            # 出力パスの設定
            output_path = st.session_state[f"{self.key}_output_path"]
            filename = st.session_state[f"{self.key}_filename"]
            
            if not output_path:
                # 出力パスが指定されていない場合は一時ディレクトリを使用
                temp_dir = tempfile.mkdtemp()
                format_ext = options.get("format", format_type)
                output_path = os.path.join(temp_dir, f"{filename}.{format_ext}")
            elif os.path.isdir(output_path):
                # 出力パスがディレクトリの場合はファイル名を追加
                format_ext = options.get("format", format_type)
                output_path = os.path.join(output_path, f"{filename}.{format_ext}")
            elif not output_path.endswith(f".{format_type}") and not "." in os.path.basename(output_path):
                # 拡張子がない場合は追加
                format_ext = options.get("format", format_type)
                output_path = f"{output_path}.{format_ext}"
            
            # 出力ディレクトリの作成
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # エクスポーター選択とエクスポート実行
            exporter = self._get_exporter(format_type, options)
            if exporter:
                # エクスポートオプションの設定
                export_options = options.copy()
                export_options["output_path"] = output_path
                
                # エクスポート実行
                result_path = exporter.export(data, template=options.get("template"), **export_options)
                
                if result_path and os.path.exists(result_path):
                    return result_path
            
            return None
        
        except Exception as e:
            st.error(f"エクスポート中にエラーが発生しました: {str(e)}")
            return None
    
    def _get_exporter(self, format_type, options):
        """
        形式に応じたエクスポーターの取得
        
        Parameters
        ----------
        format_type : str
            エクスポート形式
        options : Dict
            エクスポートオプション
        
        Returns
        -------
        BaseExporter
            エクスポーターオブジェクト
        """
        try:
            if format_type == "pdf":
                return PDFExporter(**options)
            elif format_type == "html":
                return HTMLExporter(**options)
            elif format_type == "excel":
                return ExcelExporter(**options)
            elif format_type == "image":
                return ImageExporter(**options)
            elif format_type == "data":
                return DataExporter(**options)
            else:
                st.error(f"未サポートのエクスポート形式: {format_type}")
                return None
        except Exception as e:
            st.error(f"エクスポーター初期化中にエラーが発生しました: {str(e)}")
            return None
