"""
sailing_data_processor.importers.fit_importer

FITファイルからGPSデータをインポートするモジュール
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO
import pandas as pd
from pathlib import Path
import io
import os
from datetime import datetime

try:
    import fitparse
    FITPARSE_AVAILABLE = True
except ImportError:
    FITPARSE_AVAILABLE = False
    print("警告: fitparseライブラリがインストールされていません。FITファイルのインポートには「pip install fitparse」でインストールしてください。")

from .base_importer import BaseImporter
from sailing_data_processor.data_model.container import GPSDataContainer


class FITImporter(BaseImporter):
    """
    FIT (Flexible and Interoperable Data Transfer) ファイルからGPSデータをインポートするクラス
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
        if not FITPARSE_AVAILABLE:
            self.errors.append("fitparseライブラリがインストールされていません。pip install fitparseでインストールしてください。")
    
    def can_import(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> bool:
        """
        ファイルがFITとしてインポート可能かどうかを判定
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            インポート対象ファイルのパスまたはファイルオブジェクト
            
        Returns
        -------
        bool
            インポート可能な場合はTrue
        """
        if not FITPARSE_AVAILABLE:
            return False
        
        # 拡張子による判定
        extension = self.get_file_extension(file_path)
        if extension.lower() == 'fit':
            return True
        
        # ファイル内容によるFITフォーマットの判定
        try:
            if isinstance(file_path, (str, Path)):
                # ファイルパスの場合はfitparseに直接渡す
                fitparse.FitFile(file_path)
                return True
            else:
                # ファイルオブジェクトの場合、一時ファイルに保存して判定
                if hasattr(file_path, 'tell') and hasattr(file_path, 'seek'):
                    pos = file_path.tell()
                    file_path.seek(0)
                    content = file_path.read()
                    file_path.seek(pos)
                else:
                    content = file_path.read()
                
                if isinstance(content, str):
                    content = content.encode('utf-8')
                
                # バイナリデータをメモリ上で解析
                try:
                    fitparse.FitFile(io.BytesIO(content))
                    return True
                except Exception:
                    return False
            
        except Exception as e:
            self.errors.append(f"FITファイルの検証に失敗しました: {e}")
            return False
    
    def import_data(self, file_path: Union[str, Path, BinaryIO, TextIO], 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[GPSDataContainer]:
        """
        FITからデータをインポート
        
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
        
        if not FITPARSE_AVAILABLE:
            self.errors.append("fitparseライブラリがインストールされていません")
            return None
        
        if not self.can_import(file_path):
            self.errors.append("FITファイルとして認識できません")
            return None
        
        try:
            # FITファイルを解析
            if isinstance(file_path, (str, Path)):
                fit_file = fitparse.FitFile(file_path)
            else:
                # ファイルオブジェクトの場合
                if hasattr(file_path, 'tell') and hasattr(file_path, 'seek'):
                    pos = file_path.tell()
                    file_path.seek(0)
                    content = file_path.read()
                    file_path.seek(pos)
                else:
                    content = file_path.read()
                
                if isinstance(content, str):
                    content = content.encode('utf-8')
                
                fit_file = fitparse.FitFile(io.BytesIO(content))
            
            # レコードメッセージの取得
            points = []
            fit_messages = fit_file.get_messages('record')
            
            # 各レコードからポイントデータを抽出
            for record in fit_messages:
                point = self._parse_record(record)
                if point:
                    points.append(point)
            
            if not points:
                self.errors.append("FITファイルにポイントデータが見つかりません")
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
                metadata['source'] = 'fit_import'
            
            # FITファイルのメタデータを追加
            fit_metadata = self._extract_fit_metadata(fit_file)
            if fit_metadata:
                for key, value in fit_metadata.items():
                    if key not in metadata:
                        metadata[key] = value
            
            # GPSデータコンテナの作成
            container = GPSDataContainer(df, metadata)
            
            return container
        
        except Exception as e:
            self.errors.append(f"FITファイルの読み込みに失敗しました: {e}")
            return None
    
    def _parse_record(self, record) -> Optional[Dict[str, Any]]:
        """
        FITレコードをパース
        
        Parameters
        ----------
        record : fitparse.records.FitDataMessage
            FITレコードメッセージ
            
        Returns
        -------
        Optional[Dict[str, Any]]
            パースしたポイントデータ（失敗した場合はNone）
        """
        try:
            # 必須フィールドの取得
            fields = {}
            for field in record.fields:
                fields[field.name] = field.value
            
            # 緯度経度が存在するか確認
            if 'position_lat' not in fields or 'position_long' not in fields:
                return None
            
            # 緯度経度は半円（semicircles）形式なので変換が必要
            lat = fields.get('position_lat')
            lon = fields.get('position_long')
            
            # 値がNoneなら無効なポイント
            if lat is None or lon is None:
                return None
            
            # セミサークルから度への変換（180 / 2^31）
            lat = lat * (180.0 / 2147483648.0)
            lon = lon * (180.0 / 2147483648.0)
            
            # タイムスタンプ
            timestamp = fields.get('timestamp')
            if timestamp is None:
                # タイムスタンプがない場合は現在時刻を使用
                timestamp = pd.Timestamp.now()
            
            # 基本データの作成
            point_data = {
                'timestamp': timestamp,
                'latitude': lat,
                'longitude': lon
            }
            
            # その他のフィールドをポイントデータに追加
            for field_name, field_value in fields.items():
                if field_name not in ['position_lat', 'position_long', 'timestamp'] and field_value is not None:
                    # フィールド名を変換
                    if field_name == 'altitude':
                        point_data['elevation'] = field_value
                    elif field_name == 'heart_rate':
                        point_data['heart_rate'] = field_value
                    elif field_name == 'cadence':
                        point_data['cadence'] = field_value
                    elif field_name == 'speed':
                        # 速度はm/sなのでノット変換が必要な場合もある
                        point_data['speed'] = field_value
                    elif field_name == 'distance':
                        point_data['distance'] = field_value
                    elif field_name == 'power':
                        point_data['power'] = field_value
                    elif field_name == 'temperature':
                        point_data['temperature'] = field_value
                    else:
                        # その他のフィールドは直接追加
                        point_data[field_name] = field_value
            
            return point_data
            
        except Exception as e:
            self.warnings.append(f"レコードデータの解析に失敗しました: {e}")
            return None
    
    def _extract_fit_metadata(self, fit_file) -> Dict[str, Any]:
        """
        FITファイルからメタデータを抽出
        
        Parameters
        ----------
        fit_file : fitparse.FitFile
            FITファイルオブジェクト
            
        Returns
        -------
        Dict[str, Any]
            メタデータの辞書
        """
        metadata = {}
        
        try:
            # セッション情報の取得
            for session in fit_file.get_messages('session'):
                session_data = {}
                for field in session.fields:
                    session_data[field.name] = field.value
                
                # メタデータに変換
                if 'start_time' in session_data:
                    metadata['start_time'] = session_data['start_time'].isoformat()
                if 'total_elapsed_time' in session_data:
                    metadata['total_time'] = session_data['total_elapsed_time']
                if 'total_distance' in session_data:
                    metadata['total_distance'] = session_data['total_distance']
                if 'total_calories' in session_data:
                    metadata['total_calories'] = session_data['total_calories']
                if 'avg_speed' in session_data:
                    metadata['avg_speed'] = session_data['avg_speed']
                if 'max_speed' in session_data:
                    metadata['max_speed'] = session_data['max_speed']
                if 'avg_heart_rate' in session_data:
                    metadata['avg_heart_rate'] = session_data['avg_heart_rate']
                if 'max_heart_rate' in session_data:
                    metadata['max_heart_rate'] = session_data['max_heart_rate']
                if 'sport' in session_data:
                    metadata['activity_type'] = session_data['sport']
                
                # セッションは通常1つだけなので最初のものを使用
                break
            
            # アクティビティ情報の取得
            for activity in fit_file.get_messages('activity'):
                activity_data = {}
                for field in activity.fields:
                    activity_data[field.name] = field.value
                
                # メタデータに変換
                if 'timestamp' in activity_data:
                    metadata['activity_time'] = activity_data['timestamp'].isoformat()
                if 'num_sessions' in activity_data:
                    metadata['num_sessions'] = activity_data['num_sessions']
                if 'type' in activity_data:
                    metadata['activity_type'] = activity_data['type']
                
                # アクティビティは通常1つだけなので最初のものを使用
                break
            
            # デバイス情報の取得
            for device_info in fit_file.get_messages('device_info'):
                device_data = {}
                for field in device_info.fields:
                    device_data[field.name] = field.value
                
                # メタデータに変換
                if 'manufacturer' in device_data:
                    metadata['device_manufacturer'] = device_data['manufacturer']
                if 'product' in device_data:
                    metadata['device_product'] = device_data['product']
                if 'software_version' in device_data:
                    metadata['device_software'] = device_data['software_version']
                
                # 最初のデバイス情報のみ使用
                break
        
        except Exception as e:
            self.warnings.append(f"メタデータの抽出に失敗しました: {e}")
        
        return metadata
