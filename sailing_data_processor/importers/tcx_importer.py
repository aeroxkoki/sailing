"""
sailing_data_processor.importers.tcx_importer

TCXファイルからGPSデータをインポートするモジュール
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
import pandas as pd
from pathlib import Path
import io
import os
from datetime import datetime
import re
import xml.etree.ElementTree as ET

from .base_importer import BaseImporter
from sailing_data_processor.data_model.container import GPSDataContainer


class TCXImporter(BaseImporter):
    """
    TCX (Training Center XML) ファイルからGPSデータをインポートするクラス
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        config : Optional[Dict[str, Any]], optional
            インポーター設定
        """
        super().__init__(config)
        self.ns = {
            'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
            'tpx': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2'
        }
    
    def can_import(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> bool:
        """
        ファイルがTCXとしてインポート可能かどうかを判定
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            インポート対象ファイルのパスまたはファイルオブジェクト
            
        Returns
        -------
        bool
            インポート可能な場合はTrue
        """
        # 拡張子による判定
        extension = self.get_file_extension(file_path)
        if extension.lower() == 'tcx':
            return True
        
        # ファイル内容による判定（XMLとしてパースしてTCXのルート要素を確認）
        try:
            # ファイルを読み込む
            if isinstance(file_path, (str, Path)):
                with open(file_path, 'r') as f:
                    content = f.read(1024)
            else:
                # ファイルオブジェクトの場合、現在位置を保存して先頭に戻す
                if hasattr(file_path, 'tell') and hasattr(file_path, 'seek'):
                    pos = file_path.tell()
                    file_path.seek(0)
                    content = file_path.read(1024)
                    file_path.seek(pos)
                else:
                    content = file_path.read(1024)
                
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
            
            # TCXファイルかどうかを正規表現で確認
            return re.search(r'<TrainingCenterDatabase\b', content) is not None
            
        except Exception as e:
            self.errors.append(f"TCXファイルの検証に失敗しました: {e}")
            return False
    
    def import_data(self, file_path: Union[str, Path, BinaryIO, TextIO], 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[GPSDataContainer]:
        """
        TCXからデータをインポート
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            インポート対象ファイルのパスまたはファイルオブジェクト
        metadata : Optional[Dict[str, Any]], optional
            メタデータ
            
        Returns
        -------
        Optional[GPSDataContainer]
            インポートしたデータのコンテナ（失敗した場合はNone）
        """
        self.clear_messages()
        
        if not self.can_import(file_path):
            self.errors.append("TCXファイルとして認識できません")
            return None
        
        try:
            # ファイルをパース
            if isinstance(file_path, (str, Path)):
                tree = ET.parse(file_path)
                root = tree.getroot()
            else:
                # ファイルオブジェクトの場合
                if hasattr(file_path, 'tell') and hasattr(file_path, 'seek'):
                    pos = file_path.tell()
                    file_path.seek(0)
                
                content = file_path.read()
                
                if hasattr(file_path, 'seek'):
                    file_path.seek(pos)
                
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                
                root = ET.fromstring(content)
            
            # トラックポイントデータを収集
            points = []
            
            # アクティビティを探索
            for activity in root.findall('.//tcx:Activity', self.ns):
                # アクティビティタイプを取得
                activity_type = activity.get('Sport', 'Unknown')
                
                for lap in activity.findall('.//tcx:Lap', self.ns):
                    # ラップのトラックポイントを収集
                    for trackpoint in lap.findall('.//tcx:Trackpoint', self.ns):
                        point = self._parse_trackpoint(trackpoint, activity_type)
                        if point:
                            points.append(point)
            
            if not points:
                self.errors.append("TCXファイルにポイントデータが見つかりません")
                return None
            
            # DataFrameに変換
            df = pd.DataFrame(points)
            
            # 必須列の検証
            if not self.validate_dataframe(df):
                return None
            
            # 時間順にソート
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            # メタデータの準備
            if metadata is None:
                metadata = {}
            
            if 'boat_name' not in metadata:
                metadata['boat_name'] = self.get_file_name(file_path)
            
            if 'source' not in metadata:
                metadata['source'] = 'tcx_import'
            
            # TCXファイルのメタデータを追加
            tcx_metadata = self._extract_tcx_metadata(root)
            if tcx_metadata:
                for key, value in tcx_metadata.items():
                    if key not in metadata:
                        metadata[key] = value
            
            # GPSデータコンテナの作成
            container = GPSDataContainer(df, metadata)
            
            return container
        
        except Exception as e:
            self.errors.append(f"TCXファイルの読み込みに失敗しました: {e}")
            return None
    
    def _parse_trackpoint(self, point_element, activity_type: str) -> Optional[Dict[str, Any]]:
        """
        トラックポイント要素をパース
        
        Parameters
        ----------
        point_element : xml.etree.ElementTree.Element
            トラックポイント要素
        activity_type : str
            アクティビティタイプ
            
        Returns
        -------
        Optional[Dict[str, Any]]
            パースしたポイントデータ（失敗した場合はNone）
        """
        try:
            # 位置情報を取得
            position = point_element.find('.//tcx:Position', self.ns)
            if position is None:
                return None  # 位置情報がないポイントはスキップ
            
            lat_element = position.find('tcx:LatitudeDegrees', self.ns)
            lon_element = position.find('tcx:LongitudeDegrees', self.ns)
            
            if lat_element is None or lon_element is None or not lat_element.text or not lon_element.text:
                return None
            
            lat = float(lat_element.text)
            lon = float(lon_element.text)
            
            # タイムスタンプの取得
            time_element = point_element.find('tcx:Time', self.ns)
            if time_element is not None and time_element.text:
                timestamp = pd.to_datetime(time_element.text)
            else:
                # タイムスタンプがない場合は現在時刻を使用
                timestamp = pd.Timestamp.now()
            
            # 基本データの作成
            point_data = {
                'timestamp': timestamp,
                'latitude': lat,
                'longitude': lon,
                'activity_type': activity_type
            }
            
            # 高度の取得
            alt_element = point_element.find('tcx:AltitudeMeters', self.ns)
            if alt_element is not None and alt_element.text:
                point_data['elevation'] = float(alt_element.text)
            
            # 距離の取得
            dist_element = point_element.find('tcx:DistanceMeters', self.ns)
            if dist_element is not None and dist_element.text:
                point_data['distance'] = float(dist_element.text)
            
            # 心拍数の取得
            hr_element = point_element.find('.//tcx:HeartRateBpm/tcx:Value', self.ns)
            if hr_element is not None and hr_element.text:
                point_data['heart_rate'] = float(hr_element.text)
            
            # 拡張データの取得
            extensions = point_element.find('.//tcx:Extensions', self.ns)
            if extensions is not None:
                # 速度
                speed_element = extensions.find('.//tpx:Speed', self.ns)
                if speed_element is not None and speed_element.text:
                    point_data['speed'] = float(speed_element.text)
                
                # ケイデンス（拡張）
                cad_element = extensions.find('.//tpx:RunCadence', self.ns) or extensions.find('.//tpx:Cadence', self.ns)
                if cad_element is not None and cad_element.text:
                    point_data['cadence'] = float(cad_element.text)
                
                # パワー
                power_element = extensions.find('.//tpx:Watts', self.ns)
                if power_element is not None and power_element.text:
                    point_data['power'] = float(power_element.text)
            
            # 標準のケイデンス
            cad_element = point_element.find('tcx:Cadence', self.ns)
            if cad_element is not None and cad_element.text:
                point_data['cadence'] = float(cad_element.text)
            
            return point_data
            
        except Exception as e:
            self.warnings.append(f"ポイントデータの解析に失敗しました: {e}")
            return None
    
    def _extract_tcx_metadata(self, root) -> Dict[str, Any]:
        """
        TCXファイルからメタデータを抽出
        
        Parameters
        ----------
        root : xml.etree.ElementTree.Element
            TCXファイルのルート要素
            
        Returns
        -------
        Dict[str, Any]
            メタデータの辞書
        """
        metadata = {}
        
        try:
            # アクティビティを取得
            activity = root.find('.//tcx:Activity', self.ns)
            if activity is not None:
                # アクティビティタイプ
                activity_type = activity.get('Sport')
                if activity_type:
                    metadata['activity_type'] = activity_type
                
                # アクティビティID（開始時刻）
                id_element = activity.find('tcx:Id', self.ns)
                if id_element is not None and id_element.text:
                    metadata['activity_id'] = id_element.text
                
                # 作者情報
                author = root.find('.//tcx:Author', self.ns)
                if author is not None:
                    name = author.find('tcx:Name', self.ns)
                    if name is not None and name.text:
                        metadata['author'] = name.text
            
            # 最初のラップから情報を取得
            lap = root.find('.//tcx:Lap', self.ns)
            if lap is not None:
                # 開始時刻
                start_time = lap.get('StartTime')
                if start_time:
                    metadata['start_time'] = start_time
                
                # 合計距離
                distance = lap.find('tcx:DistanceMeters', self.ns)
                if distance is not None and distance.text:
                    metadata['total_distance'] = float(distance.text)
                
                # 合計時間
                total_time = lap.find('tcx:TotalTimeSeconds', self.ns)
                if total_time is not None and total_time.text:
                    metadata['total_time'] = float(total_time.text)
                
                # 最大速度
                max_speed = lap.find('tcx:MaximumSpeed', self.ns)
                if max_speed is not None and max_speed.text:
                    metadata['max_speed'] = float(max_speed.text)
                
                # 平均心拍数
                avg_hr = lap.find('.//tcx:AverageHeartRateBpm/tcx:Value', self.ns)
                if avg_hr is not None and avg_hr.text:
                    metadata['avg_heart_rate'] = float(avg_hr.text)
                
                # 最大心拍数
                max_hr = lap.find('.//tcx:MaximumHeartRateBpm/tcx:Value', self.ns)
                if max_hr is not None and max_hr.text:
                    metadata['max_heart_rate'] = float(max_hr.text)
        
        except Exception as e:
            self.warnings.append(f"メタデータの抽出に失敗しました: {e}")
        
        return metadata
