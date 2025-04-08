"""
sailing_data_processor.exporters.report_exporter

レポート生成用エクスポータークラスを提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
import pandas as pd
from pathlib import Path
import io
import os
from datetime import datetime
import tempfile
import json
import shutil

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.exporters.base_exporter import BaseExporter


class ReportExporter(BaseExporter):
    """
    レポート生成用エクスポータークラス
    
    Parameters
    ----------
    config : Optional[Dict[str, Any]], optional
        エクスポーター設定, by default None
        
        - 'format': レポート形式 ('pdf', 'html', 'markdown') (デフォルト: 'html')
        - 'template': テンプレート名またはパス (デフォルト: 'default')
        - 'include_charts': チャートを含めるかどうか (デフォルト: True)
        - 'include_map': マップを含めるかどうか (デフォルト: True)
        - 'include_summary': サマリーを含めるかどうか (デフォルト: True)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        config : Optional[Dict[str, Any]], optional
            エクスポーター設定, by default None
        """
        super().__init__(config)
        
        # デフォルト設定
        self.format = self.config.get('format', 'html')
        self.template = self.config.get('template', 'default')
        self.include_charts = self.config.get('include_charts', True)
        self.include_map = self.config.get('include_map', True)
        self.include_summary = self.config.get('include_summary', True)
        
        # フォーマットの検証
        if self.format not in ['pdf', 'html', 'markdown']:
            self.warnings.append(f"未対応のレポート形式: {self.format}, 'html'を使用します")
            self.format = 'html'
    
    def export_data(self, container: GPSDataContainer, 
                    output_path: Optional[Union[str, Path, BinaryIO, TextIO]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[Union[str, bytes]]:
        """
        データをレポート形式でエクスポート
        
        Parameters
        ----------
        container : GPSDataContainer
            エクスポート対象のデータコンテナ
        output_path : Optional[Union[str, Path, BinaryIO, TextIO]], optional
            出力先のパスまたはファイルオブジェクト, by default None
            Noneの場合は文字列またはバイトで返す
        metadata : Optional[Dict[str, Any]], optional
            追加のメタデータ, by default None
            
        Returns
        -------
        Optional[Union[str, bytes]]
            エクスポートされたレポートデータ（output_pathがNoneの場合）
            または None（output_pathが指定された場合）
        """
        try:
            # DataFrameの確認
            if len(container.data) == 0:
                self.errors.append("エクスポートするデータがありません")
                return None
            
            # メタデータの結合
            combined_metadata = {}
            combined_metadata.update(container.metadata)
            if metadata:
                combined_metadata.update(metadata)
            
            # レポートタイトルの設定
            report_title = combined_metadata.get('report_title', '航海データレポート')
            
            # フォーマットに応じたレポート生成
            if self.format == 'html':
                return self._generate_html_report(container, output_path, combined_metadata, report_title)
            elif self.format == 'markdown':
                return self._generate_markdown_report(container, output_path, combined_metadata, report_title)
            elif self.format == 'pdf':
                return self._generate_pdf_report(container, output_path, combined_metadata, report_title)
            else:
                self.errors.append(f"未対応のレポート形式: {self.format}")
                return None
            
        except Exception as e:
            self.errors.append(f"レポート生成中にエラーが発生しました: {str(e)}")
            import traceback
            self.errors.append(traceback.format_exc())
            return None
    
    def _generate_html_report(self, container: GPSDataContainer,
                             output_path: Optional[Union[str, Path, BinaryIO, TextIO]],
                             metadata: Dict[str, Any],
                             report_title: str) -> Optional[Union[str, bytes]]:
        """
        HTMLレポートを生成
        
        Parameters
        ----------
        container : GPSDataContainer
            データコンテナ
        output_path : Optional[Union[str, Path, BinaryIO, TextIO]]
            出力先
        metadata : Dict[str, Any]
            メタデータ
        report_title : str
            レポートタイトル
            
        Returns
        -------
        Optional[Union[str, bytes]]
            HTML形式のレポート
        """
        # 基本的なHTMLテンプレート
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report_title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1, h2, h3 {{ color: #2c3e50; }}
        h1 {{ border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .metadata-table {{ width: 100%; }}
        .metadata-table th {{ width: 30%; }}
        .summary-table {{ width: 100%; }}
        .summary-table th {{ width: 40%; }}
        .chart-container {{ margin: 20px 0; }}
        .map-container {{ height: 500px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{report_title}</h1>
        <p>生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
        
        # メタデータセクション
        html_content += """
        <h2>メタデータ</h2>
        <table class="metadata-table">
            <tr>
                <th>項目</th>
                <th>値</th>
            </tr>
"""
        
        # メタデータのテーブル行を追加
        for key, value in metadata.items():
            if key != 'report_title':  # レポートタイトルは除外
                html_content += f"""
            <tr>
                <td>{key}</td>
                <td>{value}</td>
            </tr>"""
        
        html_content += """
        </table>
"""
        
        # サマリーセクション
        if self.include_summary:
            html_content += """
        <h2>データサマリー</h2>
        <table class="summary-table">
            <tr>
                <th>項目</th>
                <th>値</th>
            </tr>
"""
            
            # データの基本統計量を追加
            if len(container.data) > 0:
                df = container.data
                
                # データポイント数
                html_content += f"""
            <tr>
                <td>データポイント数</td>
                <td>{len(df)}</td>
            </tr>"""
                
                # 時間範囲
                if 'timestamp' in df.columns:
                    start_time = pd.to_datetime(df['timestamp'].min())
                    end_time = pd.to_datetime(df['timestamp'].max())
                    duration = end_time - start_time
                    html_content += f"""
            <tr>
                <td>開始時刻</td>
                <td>{start_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
            <tr>
                <td>終了時刻</td>
                <td>{end_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
            <tr>
                <td>所要時間</td>
                <td>{duration}</td>
            </tr>"""
                
                # 位置範囲
                if 'latitude' in df.columns and 'longitude' in df.columns:
                    html_content += f"""
            <tr>
                <td>緯度範囲</td>
                <td>{df['latitude'].min():.6f} - {df['latitude'].max():.6f}</td>
            </tr>
            <tr>
                <td>経度範囲</td>
                <td>{df['longitude'].min():.6f} - {df['longitude'].max():.6f}</td>
            </tr>"""
                
                # 速度統計
                if 'speed' in df.columns:
                    html_content += f"""
            <tr>
                <td>平均速度</td>
                <td>{df['speed'].mean():.2f}</td>
            </tr>
            <tr>
                <td>最大速度</td>
                <td>{df['speed'].max():.2f}</td>
            </tr>"""
            
            html_content += """
        </table>
"""
        
        # チャートセクション
        if self.include_charts:
            html_content += """
        <h2>チャート</h2>
        <p>レポートにチャートを含める場合、HTMLファイルと共に配置するか、データURLとして埋め込む必要があります。</p>
        <div class="chart-container">
            <!-- チャートプレースホルダ -->
            <p>チャートを表示するには、Sailing Strategy Analyzerのインタラクティブビューをご利用ください。</p>
        </div>
"""
        
        # マップセクション
        if self.include_map:
            html_content += """
        <h2>航跡マップ</h2>
        <p>レポートにマップを含める場合、HTMLファイルと共に配置するか、インタラクティブマップを埋め込む必要があります。</p>
        <div class="map-container">
            <!-- マッププレースホルダ -->
            <p>マップを表示するには、Sailing Strategy Analyzerのインタラクティブビューをご利用ください。</p>
        </div>
"""
        
        # データテーブルセクション
        html_content += """
        <h2>データテーブル</h2>
        <p>以下は記録されたデータの最初の100行です。</p>
        <div style="overflow-x: auto;">
            <table>
                <tr>
"""
        
        # テーブルヘッダー
        columns = container.data.columns.tolist()
        for col in columns:
            html_content += f"                    <th>{col}</th>\n"
        
        html_content += "                </tr>\n"
        
        # テーブルデータ（最初の100行）
        for idx, row in container.data.head(100).iterrows():
            html_content += "                <tr>\n"
            for col in columns:
                value = row[col]
                if pd.api.types.is_datetime64_any_dtype(value):
                    value = pd.to_datetime(value).strftime('%Y-%m-%d %H:%M:%S')
                html_content += f"                    <td>{value}</td>\n"
            html_content += "                </tr>\n"
        
        # HTMLの終了
        html_content += """
            </table>
        </div>
        
        <h2>エクスポート情報</h2>
        <p>このレポートはSailing Strategy Analyzerによって生成されました。</p>
        <p>生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
        
        # ファイルに書き込む場合
        if output_path is not None:
            if isinstance(output_path, (str, Path)):
                # ファイルパスが指定された場合
                file_path = Path(output_path)
                
                # 親ディレクトリの作成
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # ファイルに書き込み
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            else:
                # ファイルオブジェクトが指定された場合
                output_path.write(html_content)
            
            return None
        else:
            # 文字列で返す場合
            return html_content
    
    def _generate_markdown_report(self, container: GPSDataContainer,
                                 output_path: Optional[Union[str, Path, BinaryIO, TextIO]],
                                 metadata: Dict[str, Any],
                                 report_title: str) -> Optional[Union[str, bytes]]:
        """
        Markdownレポートを生成
        
        Parameters
        ----------
        container : GPSDataContainer
            データコンテナ
        output_path : Optional[Union[str, Path, BinaryIO, TextIO]]
            出力先
        metadata : Dict[str, Any]
            メタデータ
        report_title : str
            レポートタイトル
            
        Returns
        -------
        Optional[Union[str, bytes]]
            Markdown形式のレポート
        """
        # 基本的なMarkdownテンプレート
        md_content = f"# {report_title}\n\n"
        md_content += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # メタデータセクション
        md_content += "## メタデータ\n\n"
        md_content += "| 項目 | 値 |\n"
        md_content += "|-----|----|\n"
        
        # メタデータのテーブル行を追加
        for key, value in metadata.items():
            if key != 'report_title':  # レポートタイトルは除外
                md_content += f"| {key} | {value} |\n"
        
        md_content += "\n"
        
        # サマリーセクション
        if self.include_summary:
            md_content += "## データサマリー\n\n"
            md_content += "| 項目 | 値 |\n"
            md_content += "|-----|----|\n"
            
            # データの基本統計量を追加
            if len(container.data) > 0:
                df = container.data
                
                # データポイント数
                md_content += f"| データポイント数 | {len(df)} |\n"
                
                # 時間範囲
                if 'timestamp' in df.columns:
                    start_time = pd.to_datetime(df['timestamp'].min())
                    end_time = pd.to_datetime(df['timestamp'].max())
                    duration = end_time - start_time
                    md_content += f"| 開始時刻 | {start_time.strftime('%Y-%m-%d %H:%M:%S')} |\n"
                    md_content += f"| 終了時刻 | {end_time.strftime('%Y-%m-%d %H:%M:%S')} |\n"
                    md_content += f"| 所要時間 | {duration} |\n"
                
                # 位置範囲
                if 'latitude' in df.columns and 'longitude' in df.columns:
                    md_content += f"| 緯度範囲 | {df['latitude'].min():.6f} - {df['latitude'].max():.6f} |\n"
                    md_content += f"| 経度範囲 | {df['longitude'].min():.6f} - {df['longitude'].max():.6f} |\n"
                
                # 速度統計
                if 'speed' in df.columns:
                    md_content += f"| 平均速度 | {df['speed'].mean():.2f} |\n"
                    md_content += f"| 最大速度 | {df['speed'].max():.2f} |\n"
            
            md_content += "\n"
        
        # チャートセクション
        if self.include_charts:
            md_content += "## チャート\n\n"
            md_content += "レポートにチャートを含める場合、別のファイルとして生成し参照する必要があります。\n"
            md_content += "チャートを表示するには、Sailing Strategy Analyzerのインタラクティブビューをご利用ください。\n\n"
        
        # マップセクション
        if self.include_map:
            md_content += "## 航跡マップ\n\n"
            md_content += "レポートにマップを含める場合、別のファイルとして生成し参照する必要があります。\n"
            md_content += "マップを表示するには、Sailing Strategy Analyzerのインタラクティブビューをご利用ください。\n\n"
        
        # データテーブルセクション
        md_content += "## データテーブル\n\n"
        md_content += "以下は記録されたデータの最初の10行です。\n\n"
        
        # テーブルヘッダー
        columns = container.data.columns.tolist()
        md_content += "| " + " | ".join(columns) + " |\n"
        md_content += "|" + "|".join(["---" for _ in columns]) + "|\n"
        
        # テーブルデータ（最初の10行）
        for idx, row in container.data.head(10).iterrows():
            values = []
            for col in columns:
                value = row[col]
                if pd.api.types.is_datetime64_any_dtype(value):
                    value = pd.to_datetime(value).strftime('%Y-%m-%d %H:%M:%S')
                values.append(str(value))
            md_content += "| " + " | ".join(values) + " |\n"
        
        md_content += "\n"
        
        # エクスポート情報
        md_content += "## エクスポート情報\n\n"
        md_content += "このレポートはSailing Strategy Analyzerによって生成されました。\n\n"
        md_content += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        # ファイルに書き込む場合
        if output_path is not None:
            if isinstance(output_path, (str, Path)):
                # ファイルパスが指定された場合
                file_path = Path(output_path)
                
                # 親ディレクトリの作成
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # ファイルに書き込み
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
            else:
                # ファイルオブジェクトが指定された場合
                output_path.write(md_content)
            
            return None
        else:
            # 文字列で返す場合
            return md_content
    
    def _generate_pdf_report(self, container: GPSDataContainer,
                            output_path: Optional[Union[str, Path, BinaryIO, TextIO]],
                            metadata: Dict[str, Any],
                            report_title: str) -> Optional[Union[str, bytes]]:
        """
        PDFレポートを生成
        
        Parameters
        ----------
        container : GPSDataContainer
            データコンテナ
        output_path : Optional[Union[str, Path, BinaryIO, TextIO]]
            出力先
        metadata : Dict[str, Any]
            メタデータ
        report_title : str
            レポートタイトル
            
        Returns
        -------
        Optional[Union[str, bytes]]
            PDF形式のレポート
        """
        try:
            # まずHTMLレポートを生成
            html_content = self._generate_html_report(container, None, metadata, report_title)
            
            if html_content is None:
                return None
            
            # PDFレンダリングにweasyprint
            try:
                import weasyprint
            except ImportError:
                self.errors.append("PDF生成にはweasyprintライブラリが必要です。pip install weasyprintでインストールしてください。")
                return None
            
            # HTMLからPDFを生成
            pdf_content = weasyprint.HTML(string=html_content).write_pdf()
            
            # ファイルに書き込む場合
            if output_path is not None:
                if isinstance(output_path, (str, Path)):
                    # ファイルパスが指定された場合
                    file_path = Path(output_path)
                    
                    # 親ディレクトリの作成
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # ファイルに書き込み
                    with open(file_path, 'wb') as f:
                        f.write(pdf_content)
                else:
                    # ファイルオブジェクトが指定された場合
                    if hasattr(output_path, 'buffer'):
                        # TextIOラッパーの場合は内部のバイナリバッファに書き込み
                        output_path.buffer.write(pdf_content)
                    else:
                        # バイナリ出力の場合はそのまま書き込み
                        output_path.write(pdf_content)
                
                return None
            else:
                # バイト列で返す場合
                return pdf_content
            
        except Exception as e:
            self.errors.append(f"PDF生成中にエラーが発生しました: {str(e)}")
            import traceback
            self.errors.append(traceback.format_exc())
            return None
    
    def get_file_extension(self) -> str:
        """
        レポートファイルの拡張子を取得
        
        Returns
        -------
        str
            ファイル拡張子
        """
        if self.format == 'html':
            return "html"
        elif self.format == 'markdown':
            return "md"
        elif self.format == 'pdf':
            return "pdf"
        else:
            return "html"
