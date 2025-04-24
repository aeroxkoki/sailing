# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.exporters.excel_exporter

Excelレポートを生成するエクスポーターモジュール
"""

import os
import logging
from pathlib import Path
import datetime
import tempfile
from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO

# ベースクラスのインポート
from sailing_data_processor.reporting.exporters.base_exporter import BaseExporter

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import xlsxwriter
    XLSXWRITER_AVAILABLE = True
except ImportError:
    XLSXWRITER_AVAILABLE = False

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import LineChart, Reference, BarChart, PieChart
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

logger = logging.getLogger(__name__)

class ExcelExporter(BaseExporter):
    """
    Excelエクスポーター
    
    セーリングデータ分析結果をExcelレポートとして出力します。
    """
    
    def __init__(self, **options):
        """初期化"""
        super().__init__(**options)
        
        # Excelデフォルトオプション
        excel_defaults = {
            "engine": "auto",  # 'openpyxl', 'xlsxwriter', 'auto'
            "include_metadata": True,
            "include_summary": True,
            "include_charts": True,
            "include_data": True,
            "include_formulas": True,
            "freeze_panes": True,
            "auto_filter": True,
            "sheet_layout": [
                "metadata",
                "summary",
                "charts",
                "data",
                "wind_data",
                "strategy_points"
            ],
            "format": {
                "header": {
                    "bold": True,
                    "bg_color": "#4F81BD",
                    "font_color": "#FFFFFF",
                    "border": True
                },
                "title": {
                    "bold": True,
                    "font_size": 14,
                    "bg_color": "#D3D3D3"
                },
                "subtotal": {
                    "bold": True,
                    "bg_color": "#F2F2F2",
                    "border": True
                }
            }
        }
        
        self.options.update(excel_defaults)
        self.options.update(options)
        
        # エンジンの設定
        self._setup_engine()
    
    def _setup_engine(self):
        """Excelエンジンの設定"""
        engine = self.options.get("engine", "auto")
        
        # 自動検出
        if engine == "auto":
            if XLSXWRITER_AVAILABLE:
                engine = "xlsxwriter"
            elif OPENPYXL_AVAILABLE:
                engine = "openpyxl"
            else:
                engine = "pandas"
        
        # 選択されたエンジンが利用可能か確認
        if engine == "xlsxwriter" and not XLSXWRITER_AVAILABLE:
            self.add_warning("XlsxWriterが利用できないため、代替エンジンを使用します。")
            if OPENPYXL_AVAILABLE:
                engine = "openpyxl"
            else:
                engine = "pandas"
        
        if engine == "openpyxl" and not OPENPYXL_AVAILABLE:
            self.add_warning("OpenPyXLが利用できないため、代替エンジンを使用します。")
            if XLSXWRITER_AVAILABLE:
                engine = "xlsxwriter"
            else:
                engine = "pandas"
        
        if engine == "pandas" and not PANDAS_AVAILABLE:
            self.add_error("Excel出力に必要なライブラリがインストールされていません。pip install pandas openpyxl xlsxwriter のいずれかを実行してください。")
            return
        
        self.options["engine"] = engine
    
    def export(self, data, template=None, **kwargs):
        """
        データをExcelとしてエクスポート
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        template : Optional[str]
            使用するテンプレート名または直接テンプレートファイルのパス
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
        
        if not PANDAS_AVAILABLE:
            self.add_error("Excelエクスポートにはpandasライブラリが必要です。pip install pandas を実行してください。")
            return None
        
        # 出力パスの処理
        output_path = kwargs.get("output_path", self.options.get("output_path", ""))
        if not output_path:
            # パスが指定されていない場合は一時ファイルを作成
            output_path = os.path.join(
                tempfile.mkdtemp(),
                self.generate_filename(data, 'xlsx')
            )
        
        # ディレクトリの存在確認と作成
        self.ensure_directory(output_path)
        
        try:
            # データがDataFrameを持っているか確認
            if not hasattr(data, 'data') or not isinstance(data.data, pd.DataFrame):
                self.add_error("エクスポート対象のデータにpandas.DataFrameが含まれていません。")
                return None
            
            # Excelエンジンを選択して処理
            engine = self.options.get("engine", "openpyxl")
            
            if engine == "xlsxwriter":
                return self._export_xlsxwriter(data, output_path, template, **kwargs)
            elif engine == "openpyxl":
                return self._export_openpyxl(data, output_path, template, **kwargs)
            else:
                return self._export_pandas(data, output_path, template, **kwargs)
                
        except Exception as e:
            self.add_error(f"Excel生成中にエラーが発生しました: {str(e)}")
            logger.error(f"Excel generation failed: {str(e)}", exc_info=True)
            return None
    
    def _export_pandas(self, data, output_path, template=None, **kwargs):
        """
        pandasを使用してExcelを出力
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        output_path : str
            出力ファイルパス
        template : Optional[str]
            テンプレートファイルのパス
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        str
            出力ファイルのパス
        """
        # メタデータと本体データを取得
        metadata = {}
        if hasattr(data, 'metadata') and isinstance(data.metadata, dict):
            metadata = data.metadata
        
        df = data.data
        
        # ExcelWriterを作成
        with pd.ExcelWriter(output_path) as writer:
            # データシートの出力
            if self.options.get("include_data", True):
                df.to_excel(writer, sheet_name='Data', index=False)
            
            # メタデータシートの出力
            if self.options.get("include_metadata", True) and metadata:
                # メタデータをDataFrameに変換
                metadata_df = pd.DataFrame({
                    'Key': list(metadata.keys()),
                    'Value': list(metadata.values())
                })
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            # サマリーシートの出力
            if self.options.get("include_summary", True):
                summary_data = self._create_summary_data(df)
                summary_df = pd.DataFrame({
                    'Item': list(summary_data.keys()),
                    'Value': list(summary_data.values())
                })
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # 風データの分離（風向・風速がある場合）
            if 'wind_speed' in df.columns and 'wind_direction' in df.columns:
                wind_df = df[['timestamp', 'wind_speed', 'wind_direction']].copy()
                wind_df.to_excel(writer, sheet_name='Wind Data', index=False)
            
            # 戦略ポイントの分離（ある場合）
            if 'strategy_point' in df.columns:
                try:
                    strategy_df = df[df['strategy_point'] == True].copy()
                    if not strategy_df.empty:
                        strategy_df.to_excel(writer, sheet_name='Strategy Points', index=False)
                except:
                    pass
        
        return output_path
    
    def _export_xlsxwriter(self, data, output_path, template=None, **kwargs):
        """
        XlsxWriterを使用してExcelを出力
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        output_path : str
            出力ファイルパス
        template : Optional[str]
            テンプレートファイルのパス
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        str
            出力ファイルのパス
        """
        if not XLSXWRITER_AVAILABLE:
            self.add_error("XlsxWriterがインストールされていません。pip install xlsxwriter を実行してください。")
            return None
        
        # メタデータと本体データを取得
        metadata = {}
        if hasattr(data, 'metadata') and isinstance(data.metadata, dict):
            metadata = data.metadata
        
        df = data.data
        
        # ExcelWriterを作成
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # ワークブックとフォーマットの取得
            workbook = writer.book
            
            # フォーマットの設定
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4F81BD',
                'font_color': 'white',
                'border': 1
            })
            
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'bg_color': '#D3D3D3'
            })
            
            # データシートの出力
            if self.options.get("include_data", True):
                df.to_excel(writer, sheet_name='Data', index=False)
                worksheet = writer.sheets['Data']
                
                # ヘッダーフォーマットの適用
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # 自動フィルターの設定
                if self.options.get("auto_filter", True):
                    worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
                
                # 枠の固定
                if self.options.get("freeze_panes", True):
                    worksheet.freeze_panes(1, 0)
            
            # メタデータシートの出力
            if self.options.get("include_metadata", True) and metadata:
                # メタデータをDataFrameに変換
                metadata_df = pd.DataFrame({
                    'Key': list(metadata.keys()),
                    'Value': list(metadata.values())
                })
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
                worksheet = writer.sheets['Metadata']
                
                # ヘッダーフォーマットの適用
                for col_num, value in enumerate(metadata_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # シート幅の調整
                worksheet.set_column(0, 0, 30)
                worksheet.set_column(1, 1, 50)
            
            # サマリーシートの出力
            if self.options.get("include_summary", True):
                summary_data = self._create_summary_data(df)
                summary_df = pd.DataFrame({
                    'Item': list(summary_data.keys()),
                    'Value': list(summary_data.values())
                })
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                worksheet = writer.sheets['Summary']
                
                # ヘッダーフォーマットの適用
                for col_num, value in enumerate(summary_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # シート幅の調整
                worksheet.set_column(0, 0, 30)
                worksheet.set_column(1, 1, 30)
            
            # 風データの分離（風向・風速がある場合）
            if 'wind_speed' in df.columns and 'wind_direction' in df.columns:
                # 風データを抽出
                wind_df = df[['timestamp']].copy()
                wind_df['wind_speed'] = df['wind_speed']
                wind_df['wind_direction'] = df['wind_direction']
                
                # 新しいシートに書き込み
                wind_df.to_excel(writer, sheet_name='Wind Data', index=False)
                worksheet = writer.sheets['Wind Data']
                
                # ヘッダーフォーマットの適用
                for col_num, value in enumerate(wind_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # 自動フィルターの設定
                if self.options.get("auto_filter", True):
                    worksheet.autofilter(0, 0, len(wind_df), len(wind_df.columns) - 1)
                
                # 枠の固定
                if self.options.get("freeze_panes", True):
                    worksheet.freeze_panes(1, 0)
                
                # チャートの追加（風速の時系列）
                if self.options.get("include_charts", True):
                    chart = workbook.add_chart({'type': 'line'})
                    
                    # データ範囲の設定
                    chart.add_series({
                        'name': 'Wind Speed',
                        'categories': ['Wind Data', 1, 0, len(wind_df), 0],
                        'values': ['Wind Data', 1, 1, len(wind_df), 1],
                    })
                    
                    # チャートタイトルと軸ラベルの設定
                    chart.set_title({'name': 'Wind Speed Over Time'})
                    chart.set_x_axis({'name': 'Time'})
                    chart.set_y_axis({'name': 'Speed'})
                    
                    # チャートの挿入
                    worksheet.insert_chart('E2', chart, {'x_offset': 10, 'y_offset': 10})
            
            # 戦略ポイントの分離（ある場合）
            if 'strategy_point' in df.columns:
                try:
                    strategy_df = df[df['strategy_point'] == True].copy()
                    
                    if not strategy_df.empty:
                        # 新しいシートに書き込み
                        strategy_df.to_excel(writer, sheet_name='Strategy Points', index=False)
                        worksheet = writer.sheets['Strategy Points']
                        
                        # ヘッダーフォーマットの適用
                        for col_num, value in enumerate(strategy_df.columns.values):
                            worksheet.write(0, col_num, value, header_format)
                        
                        # 自動フィルターの設定
                        if self.options.get("auto_filter", True):
                            worksheet.autofilter(0, 0, len(strategy_df), len(strategy_df.columns) - 1)
                except:
                    pass
            
            # チャートシートの出力
            if self.options.get("include_charts", True):
                # 速度チャート（時系列）
                if 'timestamp' in df.columns and 'speed' in df.columns:
                    # 速度データを抽出
                    speed_df = df[['timestamp', 'speed']].copy()
                    
                    # 新しいシートに書き込み
                    speed_df.to_excel(writer, sheet_name='Speed Chart Data', index=False)
                    worksheet = writer.sheets['Speed Chart Data']
                    
                    # チャートの作成
                    chart = workbook.add_chart({'type': 'line'})
                    
                    # データ範囲の設定
                    chart.add_series({
                        'name': 'Speed',
                        'categories': ['Speed Chart Data', 1, 0, len(speed_df), 0],
                        'values': ['Speed Chart Data', 1, 1, len(speed_df), 1],
                    })
                    
                    # チャートタイトルと軸ラベルの設定
                    chart.set_title({'name': 'Speed Over Time'})
                    chart.set_x_axis({'name': 'Time'})
                    chart.set_y_axis({'name': 'Speed'})
                    
                    # チャートシートの作成と挿入
                    chart_sheet = workbook.add_chartsheet('Speed Chart')
                    chart_sheet.set_chart(chart)
        
        return output_path
    
    def _export_openpyxl(self, data, output_path, template=None, **kwargs):
        """
        OpenPyXLを使用してExcelを出力
        
        Parameters
        ----------
        data : Any
            エクスポートするデータ
        output_path : str
            出力ファイルパス
        template : Optional[str]
            テンプレートファイルのパス
        **kwargs : dict
            追加のパラメータ
            
        Returns
        -------
        str
            出力ファイルのパス
        """
        if not OPENPYXL_AVAILABLE:
            self.add_error("OpenPyXLがインストールされていません。pip install openpyxl を実行してください。")
            return None
        
        # テンプレートを使用する場合
        if template and os.path.exists(template):
            try:
                # テンプレートファイルを開く
                import shutil
                shutil.copy(template, output_path)
                workbook = openpyxl.load_workbook(output_path)
            except Exception as e:
                self.add_warning(f"テンプレートの読み込みに失敗しました: {str(e)}")
                workbook = openpyxl.Workbook()
        else:
            # 新規ワークブック作成
            workbook = openpyxl.Workbook()
            
            # デフォルトシートの名前変更
            if "Sheet" in workbook.sheetnames:
                workbook.active.title = "Data"
            elif "Sheet1" in workbook.sheetnames:
                workbook.active.title = "Data"
        
        # メタデータと本体データを取得
        metadata = {}
        if hasattr(data, 'metadata') and isinstance(data.metadata, dict):
            metadata = data.metadata
        
        df = data.data
        
        # スタイルの設定
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        header_border = Border(
            left=Side(style='thin'), 
            right=Side(style='thin'), 
            top=Side(style='thin'), 
            bottom=Side(style='thin')
        )
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        
        title_font = Font(bold=True, size=14)
        title_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
        
        # シート順序の決定
        sheet_layout = self.options.get("sheet_layout", ["metadata", "summary", "data", "wind_data", "strategy_points"])
        
        # データシートの出力
        if "data" in sheet_layout and self.options.get("include_data", True):
            if "Data" not in workbook.sheetnames:
                worksheet = workbook.create_sheet("Data")
            else:
                worksheet = workbook["Data"]
            
            # ヘッダーの書き込み
            for col_num, column_name in enumerate(df.columns, 1):
                cell = worksheet.cell(row=1, column=col_num, value=column_name)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = header_border
                cell.alignment = header_alignment
            
            # データの書き込み
            for row_idx, row in enumerate(df.itertuples(index=False), 2):
                for col_idx, value in enumerate(row, 1):
                    worksheet.cell(row=row_idx, column=col_idx, value=value)
            
            # 自動フィルターの設定
            if self.options.get("auto_filter", True):
                worksheet.auto_filter.ref = f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}"
            
            # 枠の固定
            if self.options.get("freeze_panes", True):
                worksheet.freeze_panes = "A2"
            
            # 列幅の調整
            for col_num, column_name in enumerate(df.columns, 1):
                column_width = max(len(str(column_name)), 10)
                worksheet.column_dimensions[get_column_letter(col_num)].width = column_width
        
        # メタデータシートの出力
        if "metadata" in sheet_layout and self.options.get("include_metadata", True) and metadata:
            if "Metadata" not in workbook.sheetnames:
                worksheet = workbook.create_sheet("Metadata")
            else:
                worksheet = workbook["Metadata"]
            
            # ヘッダーの書き込み
            header_cells = ["Key", "Value"]
            for col_num, header in enumerate(header_cells, 1):
                cell = worksheet.cell(row=1, column=col_num, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = header_border
                cell.alignment = header_alignment
            
            # メタデータの書き込み
            row_num = 2
            for key, value in metadata.items():
                worksheet.cell(row=row_num, column=1, value=key)
                worksheet.cell(row=row_num, column=2, value=str(value))
                row_num += 1
            
            # 列幅の調整
            worksheet.column_dimensions["A"].width = 30
            worksheet.column_dimensions["B"].width = 50
        
        # サマリーシートの出力
        if "summary" in sheet_layout and self.options.get("include_summary", True):
            if "Summary" not in workbook.sheetnames:
                worksheet = workbook.create_sheet("Summary")
            else:
                worksheet = workbook["Summary"]
            
            # ヘッダーの書き込み
            header_cells = ["Item", "Value"]
            for col_num, header in enumerate(header_cells, 1):
                cell = worksheet.cell(row=1, column=col_num, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = header_border
                cell.alignment = header_alignment
            
            # サマリーデータの作成と書き込み
            summary_data = self._create_summary_data(df)
            row_num = 2
            for key, value in summary_data.items():
                worksheet.cell(row=row_num, column=1, value=key)
                worksheet.cell(row=row_num, column=2, value=value)
                row_num += 1
            
            # 列幅の調整
            worksheet.column_dimensions["A"].width = 30
            worksheet.column_dimensions["B"].width = 30
        
        # 風データシートの出力
        if "wind_data" in sheet_layout and 'wind_speed' in df.columns and 'wind_direction' in df.columns:
            if "Wind Data" not in workbook.sheetnames:
                worksheet = workbook.create_sheet("Wind Data")
            else:
                worksheet = workbook["Wind Data"]
            
            # 風データの抽出
            wind_columns = ['timestamp', 'wind_speed', 'wind_direction']
            wind_data = df[wind_columns].copy()
            
            # ヘッダーの書き込み
            for col_num, column_name in enumerate(wind_columns, 1):
                cell = worksheet.cell(row=1, column=col_num, value=column_name)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = header_border
                cell.alignment = header_alignment
            
            # データの書き込み
            for row_idx, row in enumerate(wind_data.itertuples(index=False), 2):
                for col_idx, value in enumerate(row, 1):
                    worksheet.cell(row=row_idx, column=col_idx, value=value)
            
            # 自動フィルターの設定
            if self.options.get("auto_filter", True):
                worksheet.auto_filter.ref = f"A1:{get_column_letter(len(wind_columns))}{len(wind_data) + 1}"
            
            # 枠の固定
            if self.options.get("freeze_panes", True):
                worksheet.freeze_panes = "A2"
            
            # 列幅の調整
            for col_num, column_name in enumerate(wind_columns, 1):
                column_width = max(len(str(column_name)), 12)
                worksheet.column_dimensions[get_column_letter(col_num)].width = column_width
            
            # チャートの追加（風速の時系列）
            if self.options.get("include_charts", True):
                try:
                    # チャートシートの作成
                    if "Wind Chart" not in workbook.sheetnames:
                        chart_sheet = workbook.create_sheet("Wind Chart")
                    else:
                        chart_sheet = workbook["Wind Chart"]
                    
                    # チャートの作成
                    chart = LineChart()
                    chart.title = "Wind Speed Over Time"
                    chart.x_axis.title = "Time"
                    chart.y_axis.title = "Wind Speed"
                    
                    # データ範囲
                    data = Reference(worksheet, min_col=2, min_row=1, max_row=len(wind_data) + 1, max_col=2)
                    categories = Reference(worksheet, min_col=1, min_row=2, max_row=len(wind_data) + 1)
                    
                    chart.add_data(data, titles_from_data=True)
                    chart.set_categories(categories)
                    
                    # チャートの追加
                    chart_sheet.add_chart(chart, "A1")
                except Exception as e:
                    self.add_warning(f"風チャートの作成に失敗しました: {str(e)}")
        
        # 戦略ポイントシートの出力
        if "strategy_points" in sheet_layout and 'strategy_point' in df.columns:
            try:
                strategy_df = df[df['strategy_point'] == True].copy()
                
                if not strategy_df.empty:
                    if "Strategy Points" not in workbook.sheetnames:
                        worksheet = workbook.create_sheet("Strategy Points")
                    else:
                        worksheet = workbook["Strategy Points"]
                    
                    # ヘッダーの書き込み
                    for col_num, column_name in enumerate(strategy_df.columns, 1):
                        cell = worksheet.cell(row=1, column=col_num, value=column_name)
                        cell.font = header_font
                        cell.fill = header_fill
                        cell.border = header_border
                        cell.alignment = header_alignment
                    
                    # データの書き込み
                    for row_idx, row in enumerate(strategy_df.itertuples(index=False), 2):
                        for col_idx, value in enumerate(row, 1):
                            worksheet.cell(row=row_idx, column=col_idx, value=value)
                    
                    # 自動フィルターの設定
                    if self.options.get("auto_filter", True):
                        worksheet.auto_filter.ref = f"A1:{get_column_letter(len(strategy_df.columns))}{len(strategy_df) + 1}"
                    
                    # 枠の固定
                    if self.options.get("freeze_panes", True):
                        worksheet.freeze_panes = "A2"
                    
                    # 列幅の調整
                    for col_num, column_name in enumerate(strategy_df.columns, 1):
                        column_width = max(len(str(column_name)), 12)
                        worksheet.column_dimensions[get_column_letter(col_num)].width = column_width
            except Exception as e:
                self.add_warning(f"戦略ポイントシートの作成に失敗しました: {str(e)}")
        
        # 速度チャートシートの出力
        if self.options.get("include_charts", True) and 'timestamp' in df.columns and 'speed' in df.columns:
            try:
                # チャートシートの作成
                if "Speed Chart" not in workbook.sheetnames:
                    chart_sheet = workbook.create_sheet("Speed Chart")
                else:
                    chart_sheet = workbook["Speed Chart"]
                
                # データシートの作成（必要に応じて）
                if "Speed Data" not in workbook.sheetnames:
                    data_sheet = workbook.create_sheet("Speed Data")
                else:
                    data_sheet = workbook["Speed Data"]
                
                # ヘッダーの書き込み
                data_sheet.cell(row=1, column=1, value="Time")
                data_sheet.cell(row=1, column=2, value="Speed")
                
                # データの書き込み
                speed_df = df[['timestamp', 'speed']].copy()
                for row_idx, (_, time, speed) in enumerate(speed_df.itertuples(), 2):
                    data_sheet.cell(row=row_idx, column=1, value=time)
                    data_sheet.cell(row=row_idx, column=2, value=speed)
                
                # チャートの作成
                chart = LineChart()
                chart.title = "Speed Over Time"
                chart.x_axis.title = "Time"
                chart.y_axis.title = "Speed"
                
                # データ範囲
                data = Reference(data_sheet, min_col=2, min_row=1, max_row=len(speed_df) + 1, max_col=2)
                categories = Reference(data_sheet, min_col=1, min_row=2, max_row=len(speed_df) + 1)
                
                chart.add_data(data, titles_from_data=True)
                chart.set_categories(categories)
                
                # チャートの追加
                chart_sheet.add_chart(chart, "A1")
            except Exception as e:
                self.add_warning(f"速度チャートの作成に失敗しました: {str(e)}")
        
        # シート順序の最適化
        try:
            # シート順序のマップ作成
            sheet_order_map = {sheet_type: idx for idx, sheet_type in enumerate(sheet_layout)}
            
            # 既存のシートのうち、レイアウトに含まれるものをソート
            sheet_order = []
            for sheet_name in workbook.sheetnames:
                sheet_type = sheet_name.lower().replace(" ", "_")
                if sheet_type in sheet_order_map:
                    sheet_order.append((sheet_name, sheet_order_map[sheet_type]))
                else:
                    # 不明なシートは最後に配置
                    sheet_order.append((sheet_name, 999))
            
            # ソート
            sheet_order.sort(key=lambda x: x[1])
            
            # シート順序を再構成
            workbook._sheets = [workbook[sheet_name] for sheet_name, _ in sheet_order]
        except Exception as e:
            self.add_warning(f"シート順序の最適化に失敗しました: {str(e)}")
        
        # ファイルの保存
        workbook.save(output_path)
        
        return output_path
    
    def _create_summary_data(self, df):
        """
        サマリーデータを作成
        
        Parameters
        ----------
        df : pandas.DataFrame
            データフレーム
            
        Returns
        -------
        dict
            サマリーデータ
        """
        summary = {}
        
        # データポイント数
        summary["Data Points"] = len(df)
        
        # 時間範囲（あれば）
        if 'timestamp' in df.columns:
            try:
                start_time = pd.to_datetime(df['timestamp'].min())
                end_time = pd.to_datetime(df['timestamp'].max())
                duration = end_time - start_time
                
                summary["Start Time"] = start_time.strftime('%Y-%m-%d %H:%M:%S')
                summary["End Time"] = end_time.strftime('%Y-%m-%d %H:%M:%S')
                summary["Duration"] = str(duration)
                summary["Duration (seconds)"] = duration.total_seconds()
            except:
                pass
        
        # 位置範囲（あれば）
        if 'latitude' in df.columns and 'longitude' in df.columns:
            summary["Latitude Range"] = f"{df['latitude'].min():.6f} - {df['latitude'].max():.6f}"
            summary["Longitude Range"] = f"{df['longitude'].min():.6f} - {df['longitude'].max():.6f}"
        
        # 速度統計（あれば）
        if 'speed' in df.columns:
            summary["Average Speed"] = f"{df['speed'].mean():.2f}"
            summary["Maximum Speed"] = f"{df['speed'].max():.2f}"
            summary["Minimum Speed"] = f"{df['speed'].min():.2f}"
        
        # 風統計（あれば）
        if 'wind_speed' in df.columns:
            summary["Average Wind Speed"] = f"{df['wind_speed'].mean():.2f}"
            summary["Maximum Wind Speed"] = f"{df['wind_speed'].max():.2f}"
            summary["Minimum Wind Speed"] = f"{df['wind_speed'].min():.2f}"
        
        # 戦略ポイント（あれば）
        if 'strategy_point' in df.columns:
            try:
                strategy_count = df[df['strategy_point'] == True].shape[0]
                summary["Strategy Points"] = strategy_count
            except:
                pass
        
        return summary
    
    def validate_options(self):
        """
        オプションの検証
        
        Returns
        -------
        bool
            検証結果
        """
        # エンジンの検証
        engine = self.options.get("engine", "auto")
        
        if engine == "auto":
            if not (XLSXWRITER_AVAILABLE or OPENPYXL_AVAILABLE or PANDAS_AVAILABLE):
                self.add_error("Excel出力に必要なライブラリがインストールされていません。pip install pandas openpyxl xlsxwriter のいずれかを実行してください。")
                return False
        elif engine == "xlsxwriter" and not XLSXWRITER_AVAILABLE:
            self.add_error("XlsxWriterがインストールされていません。pip install xlsxwriter を実行してください。")
            return False
        elif engine == "openpyxl" and not OPENPYXL_AVAILABLE:
            self.add_error("OpenPyXLがインストールされていません。pip install openpyxl を実行してください。")
            return False
        elif engine == "pandas" and not PANDAS_AVAILABLE:
            self.add_error("pandasがインストールされていません。pip install pandas を実行してください。")
            return False
        
        return True
    
    def get_supported_formats(self):
        """
        サポートするフォーマットのリストを取得
        
        Returns
        -------
        List[str]
            サポートするフォーマットのリスト
        """
        return ["excel", "xlsx", "excel_report", "excel_data"]
