# -*- coding: utf-8 -*-
"""
Excel形式のエクスポーターモジュール。
セーリングデータ分析結果をExcelレポートとして出力する機能を提供します。
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
                # XlsxWriterエンジンの処理を外部モジュールから読み込む
                try:
                    from sailing_data_processor.reporting.exporters.excel_exporter_xlsx import export_xlsxwriter
                    return export_xlsxwriter(self, data, output_path, template, **kwargs)
                except ImportError:
                    self.add_warning("XlsxWriterエクスポーター拡張モジュールが見つかりません。代替エンジンを使用します。")
                    engine = "openpyxl" if OPENPYXL_AVAILABLE else "pandas"
            
            if engine == "openpyxl":
                # OpenPyXLエンジンの処理を外部モジュールから読み込む
                try:
                    from sailing_data_processor.reporting.exporters.excel_exporter_openpyxl import export_openpyxl
                    return export_openpyxl(self, data, output_path, template, **kwargs)
                except ImportError:
                    self.add_warning("OpenPyXLエクスポーター拡張モジュールが見つかりません。代替エンジンを使用します。")
                    engine = "pandas"
            
            # 上記のいずれでもない場合はPandasのシンプルなExcelエクスポートを使用
            return self._export_pandas(data, output_path, template, **kwargs)
                
        except Exception as e:
            self.add_error(f"Excel生成中にエラーが発生しました: {str(e)}")
            logger.error(f"Excel generation failed: {str(e)}", exc_info=True)
            return None

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
