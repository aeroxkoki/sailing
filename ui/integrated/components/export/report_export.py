# -*- coding: utf-8 -*-
"""
ui.integrated.components.export.report_export

レポートエクスポートコンポーネント
セッションデータや分析結果をレポート形式でエクスポートする機能を提供します。
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import base64
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))


class ReportExportComponent:
    """レポートエクスポートコンポーネント"""
    
    def __init__(self, key_prefix: str = "report_export"):
        """
        初期化
        
        Parameters
        ----------
        key_prefix : str, optional
            Streamlitコンポーネントキーのプレフィックス, by default "report_export"
        """
        self.key_prefix = key_prefix
        
        # サポートするレポート形式
        self.supported_formats = {
            "pdf": "PDF文書 (.pdf)",
            "html": "HTMLレポート (.html)",
            "markdown": "マークダウン文書 (.md)"
        }
        
        # サポートするレポートテンプレート
        self.templates = {
            "standard": "標準レポート",
            "detailed": "詳細分析レポート",
            "summary": "サマリーレポート",
            "coach": "コーチング用レポート",
            "team": "チーム共有用レポート"
        }
    
    def render(self, session_data=None, analysis_results=None) -> Optional[Dict[str, Any]]:
        """
        レポートエクスポートUIの表示
        
        Parameters
        ----------
        session_data : Optional[Dict[str, Any]], optional
            レポート対象のセッションデータ, by default None
        analysis_results : Optional[Dict[str, Any]], optional
            レポート対象の分析結果, by default None
            
        Returns
        -------
        Optional[Dict[str, Any]]
            エクスポート結果情報（実行された場合）
        """
        st.subheader("レポートエクスポート")
        
        # レポート対象の選択
        if session_data is None and analysis_results is None:
            st.markdown("### レポート対象の選択")
            
            # セッション選択（サンプルデータ）
            sessions = [
                "2025/03/27 レース練習",
                "2025/03/25 風向変化トレーニング", 
                "2025/03/20 スピードテスト", 
                "2025/03/15 戦術練習"
            ]
            
            selected_session = st.selectbox(
                "レポート対象のセッション",
                options=sessions,
                key=f"{self.key_prefix}_session"
            )
            
            # 分析結果の選択（サンプルデータ）
            analysis_types = [
                "風向変化分析",
                "戦略ポイント分析",
                "パフォーマンス分析",
                "全ての分析結果を含める"
            ]
            
            selected_analysis = st.multiselect(
                "含める分析結果",
                options=analysis_types,
                default=["全ての分析結果を含める"],
                key=f"{self.key_prefix}_analysis"
            )
        
        # レポート設定
        st.markdown("### レポート設定")
        
        # 2列レイアウト
        col1, col2 = st.columns(2)
        
        with col1:
            # レポートテンプレートの選択
            template = st.selectbox(
                "レポートテンプレート",
                options=list(self.templates.keys()),
                format_func=lambda x: self.templates.get(x, x),
                key=f"{self.key_prefix}_template"
            )
            
            # レポート形式の選択
            export_format = st.selectbox(
                "レポート形式",
                options=list(self.supported_formats.keys()),
                format_func=lambda x: self.supported_formats.get(x, x),
                key=f"{self.key_prefix}_format"
            )
            
            # レポートタイトル
            default_title = "セーリング分析レポート"
            if 'selected_session' in locals():
                default_title = f"セーリング分析レポート - {selected_session}"
                
            report_title = st.text_input(
                "レポートタイトル",
                value=default_title,
                key=f"{self.key_prefix}_title"
            )
            
            # ファイル名の設定
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"sailing_report_{timestamp}"
            
            filename = st.text_input(
                "ファイル名",
                value=default_filename,
                key=f"{self.key_prefix}_filename"
            )
        
        with col2:
            # レポート内容の設定
            st.markdown("#### レポート内容")
            
            include_summary = st.checkbox(
                "サマリーセクションを含める",
                value=True,
                key=f"{self.key_prefix}_include_summary"
            )
            
            include_charts = st.checkbox(
                "グラフとチャートを含める",
                value=True,
                key=f"{self.key_prefix}_include_charts"
            )
            
            include_map = st.checkbox(
                "マップと航跡を含める",
                value=True,
                key=f"{self.key_prefix}_include_map"
            )
            
            include_raw_data = st.checkbox(
                "生データセクションを含める",
                value=False,
                key=f"{self.key_prefix}_include_raw_data"
            )
            
            # PDFの場合の特別な設定
            if export_format == "pdf":
                st.markdown("#### PDF設定")
                
                paper_size = st.selectbox(
                    "用紙サイズ",
                    options=["A4", "A3", "Letter", "Legal"],
                    index=0,
                    key=f"{self.key_prefix}_paper_size"
                )
                
                orientation = st.radio(
                    "向き",
                    options=["縦向き", "横向き"],
                    index=0,
                    horizontal=True,
                    key=f"{self.key_prefix}_orientation"
                )
                
                include_toc = st.checkbox(
                    "目次を含める",
                    value=True,
                    key=f"{self.key_prefix}_include_toc"
                )
        
        # 詳細設定
        with st.expander("詳細設定", expanded=False):
            # レポートのスタイル設定
            st.markdown("#### スタイル設定")
            
            # カラーテーマ
            color_theme = st.selectbox(
                "カラーテーマ",
                options=["スタンダード", "モダン", "クラシック", "マリンブルー", "ハイコントラスト"],
                index=0,
                key=f"{self.key_prefix}_color_theme"
            )
            
            # フォント
            font_family = st.selectbox(
                "フォント",
                options=["デフォルト", "Arial", "Helvetica", "Times New Roman", "Georgia", "Courier New"],
                index=0,
                key=f"{self.key_prefix}_font_family"
            )
            
            # ヘッダーとフッター
            include_header = st.checkbox(
                "ヘッダーを含める",
                value=True,
                key=f"{self.key_prefix}_include_header"
            )
            
            include_footer = st.checkbox(
                "フッターを含める",
                value=True,
                key=f"{self.key_prefix}_include_footer"
            )
            
            if include_footer:
                footer_text = st.text_input(
                    "フッターテキスト",
                    value="セーリング戦略分析システム生成レポート",
                    key=f"{self.key_prefix}_footer_text"
                )
            
            # ページ番号
            include_page_numbers = st.checkbox(
                "ページ番号を含める",
                value=True,
                key=f"{self.key_prefix}_include_page_numbers"
            )
            
            # 日時と生成情報
            include_timestamp = st.checkbox(
                "生成日時を含める",
                value=True,
                key=f"{self.key_prefix}_include_timestamp"
            )
            
            # カスタムCSS (HTMLの場合)
            if export_format == "html":
                use_custom_css = st.checkbox(
                    "カスタムCSSを使用",
                    value=False,
                    key=f"{self.key_prefix}_use_custom_css"
                )
                
                if use_custom_css:
                    custom_css = st.text_area(
                        "カスタムCSS",
                        value="""
                        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; }
                        h1 { color: #2c3e50; }
                        h2 { color: #3498db; }
                        .chart-container { margin: 20px 0; }
                        """,
                        height=200,
                        key=f"{self.key_prefix}_custom_css"
                    )
            
            # マークダウンの場合の設定
            if export_format == "markdown":
                md_format = st.selectbox(
                    "マークダウン形式",
                    options=["GitHub", "Standard", "CommonMark"],
                    index=0,
                    key=f"{self.key_prefix}_md_format"
                )
                
                include_frontmatter = st.checkbox(
                    "FrontMatterを含める (Jekyll/Hugo対応)",
                    value=False,
                    key=f"{self.key_prefix}_include_frontmatter"
                )
        
        # レポートのプレビュー
        if st.checkbox("プレビューを表示", value=False, key=f"{self.key_prefix}_show_preview"):
            st.markdown("### レポートプレビュー")
            
            # プレビュータブ
            if export_format == "markdown":
                with st.container():
                    st.markdown("#### マークダウンプレビュー")
                    st.markdown(self._generate_markdown_preview(
                        title=report_title,
                        template=template,
                        include_summary=include_summary,
                        include_charts=include_charts,
                        include_map=include_map
                    ))
            else:
                st.info(f"{export_format.upper()}形式はプレビューできません。レポートをエクスポートして確認してください。")
        
        # エクスポート実行ボタン
        if st.button("レポート生成", key=f"{self.key_prefix}_export_btn", use_container_width=True):
            # レポート生成処理（実際の実装ではセッションデータと分析結果を使用）
            export_data, exported_filename = self._generate_report(
                format_type=export_format,
                template=template,
                title=report_title,
                filename=filename,
                include_summary=include_summary,
                include_charts=include_charts,
                include_map=include_map,
                include_raw_data=include_raw_data,
                # その他の設定
                paper_size=locals().get("paper_size", "A4"),
                orientation=locals().get("orientation", "縦向き"),
                include_toc=locals().get("include_toc", True),
                color_theme=locals().get("color_theme", "スタンダード"),
                font_family=locals().get("font_family", "デフォルト"),
                include_header=locals().get("include_header", True),
                include_footer=locals().get("include_footer", True),
                footer_text=locals().get("footer_text", ""),
                include_page_numbers=locals().get("include_page_numbers", True),
                include_timestamp=locals().get("include_timestamp", True)
            )
            
            if export_data:
                # ダウンロードリンクの作成
                download_link = self._create_download_link(export_data, exported_filename, export_format)
                st.success(f"レポートの生成が完了しました。")
                st.markdown(download_link, unsafe_allow_html=True)
                
                # エクスポート結果情報の返却
                return {
                    "type": "report",
                    "report_template": template,
                    "format": export_format,
                    "filename": exported_filename,
                    "timestamp": datetime.now().isoformat(),
                    "download_link": download_link,
                    "size": self._get_file_size_str(len(export_data))
                }
        
        return None
    
    def _generate_markdown_preview(self, title, template, include_summary, include_charts, include_map):
        """
        マークダウンプレビューの生成
        
        Parameters
        ----------
        title : str
            レポートタイトル
        template : str
            レポートテンプレート
        include_summary : bool
            サマリーセクションを含めるかどうか
        include_charts : bool
            チャートを含めるかどうか
        include_map : bool
            マップを含めるかどうか
            
        Returns
        -------
        str
            マークダウンプレビュー
        """
        markdown = f"""
        # {title}
        
        **生成日時**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
        **テンプレート**: {self.templates.get(template, template)}
        
        ## 概要
        
        このレポートはセーリングセッションの分析結果をまとめたものです。
        """
        
        if include_summary:
            markdown += """
        ## サマリー
        
        | 指標 | 値 |
        |------|-----|
        | 総距離 | 15.3 km |
        | 平均速度 | 6.2 knots |
        | 最高速度 | 8.7 knots |
        | トータル時間 | 2時間30分 |
        | タック回数 | 12回 |
        | ジャイブ回数 | 8回 |
        
        ### 主な結果
        
        * 風向変化に適切に対応できていました
        * スタート直後の加速が優れていました
        * マーク付近での戦略ポイントでの判断が適切でした
        """
        
        if include_charts:
            markdown += """
        ## チャート
        
        ### 速度プロファイル
        
        ```
        [速度グラフのプレースホルダー]
        ```
        
        ### 風向と方位の関係
        
        ```
        [風向グラフのプレースホルダー]
        ```
        """
        
        if include_map:
            markdown += """
        ## 航跡マップ
        
        ```
        [マップのプレースホルダー]
        ```
        
        ### 戦略ポイント
        
        * ポイント1 (35.302, 139.485): 風向変化に対応したタック
        * ポイント2 (35.307, 139.490): マーク回航前の減速を最小化
        * ポイント3 (35.299, 139.488): 最適なレイラインへの進入
        """
        
        markdown += """
        ## 結論と推奨事項
        
        セッション全体の評価としては、優れたパフォーマンスが見られました。
        特に風向変化への対応と戦略的判断ポイントでの意思決定が高く評価できます。
        
        ### 改善点
        
        1. マーク回航後の加速をより迅速に行う
        2. 風下帆走時の安定性を向上させる
        3. タック時のスピードロスを最小化する
        
        ### 次回のセッションに向けて
        
        * 風下帆走のテクニックに焦点を当てる
        * タックの効率性向上に取り組む
        * 風向変化の予測と早期対応を練習する
        """
        
        return markdown
    
    def _generate_report(self, format_type, template, title, filename, 
                       include_summary, include_charts, include_map, include_raw_data,
                       **kwargs) -> Tuple[bytes, str]:
        """
        レポートの生成
        
        Parameters
        ----------
        format_type : str
            レポート形式
        template : str
            レポートテンプレート
        title : str
            レポートタイトル
        filename : str
            ファイル名
        include_summary : bool
            サマリーセクションを含めるかどうか
        include_charts : bool
            チャートを含めるかどうか
        include_map : bool
            マップを含めるかどうか
        include_raw_data : bool
            生データを含めるかどうか
        **kwargs : dict
            その他の設定パラメータ
            
        Returns
        -------
        Tuple[bytes, str]
            レポートデータのバイト列とファイル名
        """
        # ファイル拡張子の設定
        if format_type == "markdown":
            file_ext = "md"
        else:
            file_ext = format_type
        
        # 完全なファイル名
        full_filename = f"{filename}.{file_ext}"
        
        # バッファの作成
        buffer = io.BytesIO()
        
        # レポート生成処理（形式に応じた処理）
        if format_type == "pdf":
            # PDFレポートの生成（実際の実装ではpdfkitなどのライブラリを使用）
            # ここではサンプルデータ
            buffer.write(b"PDF report placeholder")
            
        elif format_type == "html":
            # HTMLレポートの生成
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #2c3e50; }}
                    h2 {{ color: #3498db; }}
                    .section {{ margin: 20px 0; padding: 15px; border-radius: 5px; background-color: #f8f9fa; }}
                    .chart-container {{ margin: 20px 0; }}
                    .map-container {{ margin: 20px 0; height: 400px; background-color: #e9ecef; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    table, th, td {{ border: 1px solid #ddd; }}
                    th, td {{ padding: 12px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    footer {{ margin-top: 30px; padding-top: 10px; border-top: 1px solid #ddd; color: #777; }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <p><strong>生成日時:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                
                <div class="section">
                    <h2>概要</h2>
                    <p>このレポートはセーリングセッションの分析結果をまとめたものです。</p>
                </div>
            """
            
            if include_summary:
                html_content += """
                <div class="section">
                    <h2>サマリー</h2>
                    <table>
                        <tr><th>指標</th><th>値</th></tr>
                        <tr><td>総距離</td><td>15.3 km</td></tr>
                        <tr><td>平均速度</td><td>6.2 knots</td></tr>
                        <tr><td>最高速度</td><td>8.7 knots</td></tr>
                        <tr><td>トータル時間</td><td>2時間30分</td></tr>
                        <tr><td>タック回数</td><td>12回</td></tr>
                        <tr><td>ジャイブ回数</td><td>8回</td></tr>
                    </table>
                    
                    <h3>主な結果</h3>
                    <ul>
                        <li>風向変化に適切に対応できていました</li>
                        <li>スタート直後の加速が優れていました</li>
                        <li>マーク付近での戦略ポイントでの判断が適切でした</li>
                    </ul>
                </div>
                """
            
            if include_charts:
                html_content += """
                <div class="section">
                    <h2>チャート</h2>
                    
                    <h3>速度プロファイル</h3>
                    <div class="chart-container">
                        <p>[速度グラフのプレースホルダー]</p>
                    </div>
                    
                    <h3>風向と方位の関係</h3>
                    <div class="chart-container">
                        <p>[風向グラフのプレースホルダー]</p>
                    </div>
                </div>
                """
            
            if include_map:
                html_content += """
                <div class="section">
                    <h2>航跡マップ</h2>
                    <div class="map-container">
                        <p>[マップのプレースホルダー]</p>
                    </div>
                    
                    <h3>戦略ポイント</h3>
                    <ul>
                        <li>ポイント1 (35.302, 139.485): 風向変化に対応したタック</li>
                        <li>ポイント2 (35.307, 139.490): マーク回航前の減速を最小化</li>
                        <li>ポイント3 (35.299, 139.488): 最適なレイラインへの進入</li>
                    </ul>
                </div>
                """
            
            if include_raw_data:
                html_content += """
                <div class="section">
                    <h2>生データ</h2>
                    <p>詳細なデータテーブルは省略されています。</p>
                </div>
                """
            
            # 結論部分
            html_content += """
            <div class="section">
                <h2>結論と推奨事項</h2>
                <p>セッション全体の評価としては、優れたパフォーマンスが見られました。
                特に風向変化への対応と戦略的判断ポイントでの意思決定が高く評価できます。</p>
                
                <h3>改善点</h3>
                <ol>
                    <li>マーク回航後の加速をより迅速に行う</li>
                    <li>風下帆走時の安定性を向上させる</li>
                    <li>タック時のスピードロスを最小化する</li>
                </ol>
                
                <h3>次回のセッションに向けて</h3>
                <ul>
                    <li>風下帆走のテクニックに焦点を当てる</li>
                    <li>タックの効率性向上に取り組む</li>
                    <li>風向変化の予測と早期対応を練習する</li>
                </ul>
            </div>
            """
            
            # フッター
            if kwargs.get("include_footer", True):
                footer_text = kwargs.get("footer_text", "セーリング戦略分析システム生成レポート")
                html_content += f"""
                <footer>
                    <p>{footer_text}</p>
                    <p>生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </footer>
                """
            
            html_content += """
            </body>
            </html>
            """
            
            buffer.write(html_content.encode("utf-8"))
            
        elif format_type == "markdown":
            # マークダウンレポートの生成
            md_content = self._generate_markdown_preview(
                title=title,
                template=template,
                include_summary=include_summary,
                include_charts=include_charts,
                include_map=include_map
            )
            
            buffer.write(md_content.encode("utf-8"))
        
        # バッファを先頭に戻す
        buffer.seek(0)
        
        # バイト列として返す
        return buffer.read(), full_filename
    
    def _create_download_link(self, data: bytes, filename: str, format_type: str) -> str:
        """
        ダウンロードリンクの生成
        
        Parameters
        ----------
        data : bytes
            ダウンロードするデータ
        filename : str
            ファイル名
        format_type : str
            ファイル形式
            
        Returns
        -------
        str
            HTMLダウンロードリンク
        """
        b64 = base64.b64encode(data).decode()
        
        # MIMEタイプの設定
        mime_types = {
            "pdf": "application/pdf",
            "html": "text/html",
            "markdown": "text/markdown"
        }
        
        mime_type = mime_types.get(format_type, "application/octet-stream")
        
        # スタイル付きのダウンロードボタン
        styled_link = f"""
        <div style="text-align: center; margin: 10px 0;">
            <a href="data:{mime_type};base64,{b64}" 
               download="{filename}" 
               style="display: inline-block; 
                      background-color: #4CAF50; 
                      color: white; 
                      padding: 10px 20px; 
                      text-align: center; 
                      text-decoration: none; 
                      font-size: 16px; 
                      margin: 4px 2px; 
                      cursor: pointer; 
                      border-radius: 4px;">
                <span>レポートをダウンロード ({format_type.upper()})</span>
            </a>
        </div>
        """
        
        return styled_link
    
    def _get_file_size_str(self, size_bytes: int) -> str:
        """
        ファイルサイズの文字列表現を取得
        
        Parameters
        ----------
        size_bytes : int
            バイト単位のサイズ
            
        Returns
        -------
        str
            人間が読みやすい形式のサイズ表現
        """
        # サイズの単位変換
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
