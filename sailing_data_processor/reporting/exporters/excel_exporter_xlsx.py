# -*- coding: utf-8 -*-
"""
XlsxWriter エンジンを使用したExcelエクスポーターの実装。
ExcelExporterクラスから使用されます。
"""

import logging
import pandas as pd

logger = logging.getLogger(__name__)

def export_xlsxwriter(exporter, data, output_path, template=None, **kwargs):
    """
    XlsxWriterを使用してExcelを出力
    
    Parameters
    ----------
    exporter : ExcelExporter
        エクスポーターインスタンス
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
    try:
        import xlsxwriter
    except ImportError:
        exporter.add_error("XlsxWriterがインストールされていません。pip install xlsxwriter を実行してください。")
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
        if exporter.options.get("include_data", True):
            df.to_excel(writer, sheet_name='Data', index=False)
            worksheet = writer.sheets['Data']
            
            # ヘッダーフォーマットの適用
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # 自動フィルターの設定
            if exporter.options.get("auto_filter", True):
                worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
            
            # 枠の固定
            if exporter.options.get("freeze_panes", True):
                worksheet.freeze_panes(1, 0)
        
        # メタデータシートの出力
        if exporter.options.get("include_metadata", True) and metadata:
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
        if exporter.options.get("include_summary", True):
            summary_data = exporter._create_summary_data(df)
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
            if exporter.options.get("auto_filter", True):
                worksheet.autofilter(0, 0, len(wind_df), len(wind_df.columns) - 1)
            
            # 枠の固定
            if exporter.options.get("freeze_panes", True):
                worksheet.freeze_panes(1, 0)
            
            # チャートの追加（風速の時系列）
            if exporter.options.get("include_charts", True):
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
                    if exporter.options.get("auto_filter", True):
                        worksheet.autofilter(0, 0, len(strategy_df), len(strategy_df.columns) - 1)
            except Exception as e:
                exporter.add_warning(f"戦略ポイントシートの作成に失敗しました: {str(e)}")
        
        # チャートシートの出力
        if exporter.options.get("include_charts", True):
            # 速度チャート（時系列）
            if 'timestamp' in df.columns and 'speed' in df.columns:
                try:
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
                except Exception as e:
                    exporter.add_warning(f"速度チャートの作成に失敗しました: {str(e)}")
    
    return output_path
