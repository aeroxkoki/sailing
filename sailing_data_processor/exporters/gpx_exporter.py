# -*- coding: utf-8 -*-
"""
sailing_data_processor.exporters.gpx_exporter

GPXフォーマットのエクスポータークラスを提供するモジュール
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
import pandas as pd
from pathlib import Path
import io
import os
from datetime import datetime
import xml.dom.minidom
import xml.etree.ElementTree as ET

from sailing_data_processor.data_model.container import GPSDataContainer
from sailing_data_processor.exporters.base_exporter import BaseExporter


class GPXExporter(BaseExporter):
    """
    GPXフォーマットのエクスポータークラス
    
    Parameters
    ----------
    config : Optional[Dict[str, Any]], optional
        エクスポーター設定, by default None
        
        - 'pretty_print': XMLを整形するかどうか (デフォルト: True)
        - 'include_speed': 速度データを含めるかどうか (デフォルト: True)
        - 'include_elevation': 高度データを含めるかどうか (デフォルト: True)
        - 'track_name': トラック名 (デフォルト: 'Sailing Track')
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
        self.pretty_print = self.config.get('pretty_print', True)
        self.include_speed = self.config.get('include_speed', True)
        self.include_elevation = self.config.get('include_elevation', True)
        self.track_name = self.config.get('track_name', 'Sailing Track')
    
    def export_data(self, container: GPSDataContainer, 
                    output_path: Optional[Union[str, Path, BinaryIO, TextIO]] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[Union[str, bytes]]:
        """
        データをGPX形式でエクスポート
        
        Parameters
        ----------
        container : GPSDataContainer
            エクスポート対象のデータコンテナ
        output_path : Optional[Union[str, Path, BinaryIO, TextIO]], optional
            出力先のパスまたはファイルオブジェクト, by default None
            Noneの場合は文字列で返す
        metadata : Optional[Dict[str, Any]], optional
            追加のメタデータ, by default None
            
        Returns
        -------
        Optional[Union[str, bytes]]
            エクスポートされたGPXデータ（output_pathがNoneの場合）
            または None（output_pathが指定された場合）
        """
        try:
            # DataFrameの確認
            if len(container.data) == 0:
                self.errors.append("エクスポートするデータがありません")
                return None
            
            # 必須カラムの確認
            required_columns = ['timestamp', 'latitude', 'longitude']
            missing_columns = [col for col in required_columns if col not in container.data.columns]
            if missing_columns:
                self.errors.append(f"必須カラムがありません: {', '.join(missing_columns)}")
                return None
            
            # データフレームをコピー
            df = container.data.copy()
            
            # GPXルートドキュメントの作成
            gpx = ET.Element('gpx')
            gpx.set('version', '1.1')
            gpx.set('creator', 'Sailing Strategy Analyzer')
            gpx.set('xmlns', 'http://www.topografix.com/GPX/1/1')
            gpx.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
            gpx.set('xsi:schemaLocation', 'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd')
            
            # メタデータの追加
            metadata_elem = ET.SubElement(gpx, 'metadata')
            
            # ドキュメント名の設定
            name_elem = ET.SubElement(metadata_elem, 'name')
            
            # タイトルの設定
            track_name = self.track_name
            if metadata and 'track_name' in metadata:
                track_name = metadata['track_name']
            elif 'name' in container.metadata:
                track_name = container.metadata['name']
            name_elem.text = track_name
            
            # 日時の設定
            time_elem = ET.SubElement(metadata_elem, 'time')
            time_elem.text = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # 拡張メタデータの追加
            extensions_elem = ET.SubElement(metadata_elem, 'extensions')
            
            # コンテナのメタデータを追加
            for key, value in container.metadata.items():
                if key not in ['name', 'time']:  # 既に使用したメタデータは除外
                    meta_elem = ET.SubElement(extensions_elem, key.replace(' ', '_'))
                    meta_elem.text = str(value)
            
            # 追加メタデータを追加
            if metadata:
                for key, value in metadata.items():
                    if key not in ['name', 'time', 'track_name']:  # 既に使用したメタデータは除外
                        meta_elem = ET.SubElement(extensions_elem, key.replace(' ', '_'))
                        meta_elem.text = str(value)
            
            # トラックの追加
            trk_elem = ET.SubElement(gpx, 'trk')
            
            # トラック名の設定
            trk_name_elem = ET.SubElement(trk_elem, 'name')
            trk_name_elem.text = track_name
            
            # トラックセグメントの追加
            trkseg_elem = ET.SubElement(trk_elem, 'trkseg')
            
            # DataFrameの各行をトラックポイントとして追加
            for idx, row in df.iterrows():
                trkpt_elem = ET.SubElement(trkseg_elem, 'trkpt')
                trkpt_elem.set('lat', str(row['latitude']))
                trkpt_elem.set('lon', str(row['longitude']))
                
                # 高度データがあれば追加
                if self.include_elevation and 'elevation' in df.columns and pd.notna(row['elevation']):
                    ele_elem = ET.SubElement(trkpt_elem, 'ele')
                    ele_elem.text = str(row['elevation'])
                
                # タイムスタンプの追加
                time_elem = ET.SubElement(trkpt_elem, 'time')
                if pd.api.types.is_datetime64_any_dtype(row['timestamp']):
                    time_text = row['timestamp'].strftime('%Y-%m-%dT%H:%M:%SZ')
                else:
                    time_text = str(row['timestamp'])
                time_elem.text = time_text
                
                # 拡張データの追加
                extensions_elem = None
                
                # 速度データがあれば追加
                if self.include_speed and 'speed' in df.columns and pd.notna(row['speed']):
                    if extensions_elem is None:
                        extensions_elem = ET.SubElement(trkpt_elem, 'extensions')
                    speed_elem = ET.SubElement(extensions_elem, 'speed')
                    speed_elem.text = str(row['speed'])
                
                # その他の列があれば拡張データとして追加
                other_columns = [col for col in df.columns if col not in ['timestamp', 'latitude', 'longitude', 'elevation', 'speed']]
                for col in other_columns:
                    if pd.notna(row[col]):
                        if extensions_elem is None:
                            extensions_elem = ET.SubElement(trkpt_elem, 'extensions')
                        col_elem = ET.SubElement(extensions_elem, col.replace(' ', '_'))
                        col_elem.text = str(row[col])
            
            # XMLツリーを文字列に変換
            xml_str = ET.tostring(gpx, encoding='utf-8', method='xml')
            
            # 整形オプションが有効ならXMLを整形
            if self.pretty_print:
                dom = xml.dom.minidom.parseString(xml_str)
                xml_str = dom.toprettyxml(indent="  ", encoding='utf-8')
            
            # ファイルに書き込む場合
            if output_path is not None:
                if isinstance(output_path, (str, Path)):
                    # ファイルパスが指定された場合
                    file_path = Path(output_path)
                    
                    # 親ディレクトリの作成
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # ファイルに書き込み
                    with open(file_path, 'wb') as f:
                        f.write(xml_str)
                else:
                    # ファイルオブジェクトが指定された場合
                    if hasattr(output_path, 'buffer'):
                        # TextIOラッパーの場合は内部のバイナリバッファに書き込み
                        output_path.buffer.write(xml_str)
                    else:
                        # バイナリ出力の場合はそのまま書き込み
                        output_path.write(xml_str)
                
                return None
            else:
                # バイト列で返す場合
                return xml_str
            
        except Exception as e:
            self.errors.append(f"GPXエクスポート中にエラーが発生しました: {str(e)}")
            return None
    
    def get_file_extension(self) -> str:
        """
        GPXファイルの拡張子を取得
        
        Returns
        -------
        str
            ファイル拡張子
        """
        return "gpx"
