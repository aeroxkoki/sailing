"""
sailing_data_processor.importers.gpx_importer

GPXファイルからGPSデータをインポートするモジュール
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO, Set
import pandas as pd
from pathlib import Path
import io
import os
from datetime import datetime
import re
import xml.etree.ElementTree as ET

from .base_importer import BaseImporter
from sailing_data_processor.data_model.container import GPSDataContainer


class GPXImporter(BaseImporter):
    """
    GPXファイルからGPSデータをインポートするクラス
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
        
        # デフォルト設定
        if 'include_extensions' not in self.config:
            self.config['include_extensions'] = True
            
        if 'prefer_trkpt' not in self.config:
            self.config['prefer_trkpt'] = True
            
        if 'include_waypoints' not in self.config:
            self.config['include_waypoints'] = False
            
        # 名前空間定義
        self.ns = {
            'gpx': 'http://www.topografix.com/GPX/1/1',
            'gpxtpx': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1',
            'gpxx': 'http://www.garmin.com/xmlschemas/GpxExtensions/v3',
            'ns3': 'http://www.garmin.com/xmlschemas/TrackPointExtension/v1'
        }
        
        # サポートされている拡張データの設定
        self.supported_extensions = {
            'heart_rate': ['gpxtpx:hr', 'ns3:hr', 'hr'],
            'cadence': ['gpxtpx:cad', 'ns3:cad', 'cad'],
            'temperature': ['gpxtpx:atemp', 'ns3:atemp', 'atemp', 'temperature'],
            'speed': ['gpxtpx:speed', 'ns3:speed', 'speed'],
            'course': ['gpxtpx:course', 'ns3:course', 'course', 'direction', 'heading'],
            'battery': ['gpxtpx:batt', 'ns3:batt', 'batt', 'battery']
        }
    
    def can_import(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> bool:
        """
        ファイルがGPXとしてインポート可能かどうかを判定
        
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
        if extension.lower() == 'gpx':
            return True
        
        # ファイル内容による判定（XMLとしてパースしてGPXのルート要素を確認）
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
            
            # GPXファイルかどうかを正規表現で確認
            return re.search(r'<gpx\\b', content) is not None
            
        except Exception as e:
            self.errors.append(f"GPXファイルの検証に失敗しました: {e}")
            return False
    
    def import_data(self, file_path: Union[str, Path, BinaryIO, TextIO], 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[GPSDataContainer]:
        """
        GPXからデータをインポート
        
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
            self.errors.append("GPXファイルとして認識できません")
            return None
        
        try:
            # ファイルをパース
            root = self._parse_gpx_file(file_path)
            if root is None:
                return None
            
            # GPXファイルの情報を収集
            gpx_info = self._extract_gpx_info(root)
            
            # ポイントデータを収集
            points = self._collect_points(root)
            
            if not points:
                self.errors.append("GPXファイルにポイントデータが見つかりません")
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
                metadata['source'] = 'gpx_import'
            
            # GPXファイルの情報をメタデータに追加
            for key, value in gpx_info.items():
                if key not in metadata:
                    metadata[key] = value
            
            # GPSデータコンテナの作成
            container = GPSDataContainer(df, metadata)
            
            return container
        
        except Exception as e:
            self.errors.append(f"GPXファイルの読み込みに失敗しました: {e}")
            return None
    
    def _parse_gpx_file(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> Optional[ET.Element]:
        """
        GPXファイルをパースしてルート要素を返す
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            パースするファイルのパスまたはファイルオブジェクト
            
        Returns
        -------
        Optional[ET.Element]
            パースしたXMLのルート要素（失敗した場合はNone）
        """
        try:
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
            
            return root
        
        except Exception as e:
            self.errors.append(f"GPXファイルのパースに失敗しました: {e}")
            return None
    
    def _extract_gpx_info(self, root: ET.Element) -> Dict[str, Any]:
        """
        GPXファイルの基本情報を抽出
        
        Parameters
        ----------
        root : ET.Element
            GPXファイルのルート要素
            
        Returns
        -------
        Dict[str, Any]
            GPXファイルの情報を格納した辞書
        """
        gpx_info = {
            'gpx_version': root.attrib.get('version', 'unknown'),
            'creator': root.attrib.get('creator', 'unknown')
        }
        
        try:
            # メタデータ要素の取得
            meta_element = root.find('gpx:metadata', self.ns)
            if meta_element is not None:
                # 名前
                name_element = meta_element.find('gpx:name', self.ns)
                if name_element is not None and name_element.text:
                    gpx_info['name'] = name_element.text
                
                # 説明
                desc_element = meta_element.find('gpx:desc', self.ns)
                if desc_element is not None and desc_element.text:
                    gpx_info['description'] = desc_element.text
                
                # 作成者
                author_element = meta_element.find('gpx:author', self.ns)
                if author_element is not None:
                    author_name = author_element.find('gpx:name', self.ns)
                    if author_name is not None and author_name.text:
                        gpx_info['author'] = author_name.text
                
                # 作成日時
                time_element = meta_element.find('gpx:time', self.ns)
                if time_element is not None and time_element.text:
                    gpx_info['created'] = time_element.text
            
            # トラック情報
            tracks = []
            for trk in root.findall('gpx:trk', self.ns):
                track_info = {}
                
                # トラック名
                name_element = trk.find('gpx:name', self.ns)
                if name_element is not None and name_element.text:
                    track_info['name'] = name_element.text
                
                # トラック説明
                desc_element = trk.find('gpx:desc', self.ns)
                if desc_element is not None and desc_element.text:
                    track_info['description'] = desc_element.text
                
                # トラックタイプ
                type_element = trk.find('gpx:type', self.ns)
                if type_element is not None and type_element.text:
                    track_info['type'] = type_element.text
                
                # セグメント数
                segments = trk.findall('gpx:trkseg', self.ns)
                track_info['segments'] = len(segments)
                
                # ポイント数
                points_count = 0
                for seg in segments:
                    points_count += len(seg.findall('gpx:trkpt', self.ns))
                track_info['points'] = points_count
                
                tracks.append(track_info)
            
            if tracks:
                gpx_info['tracks'] = tracks
            
            # ルート情報
            routes = []
            for rte in root.findall('gpx:rte', self.ns):
                route_info = {}
                
                # ルート名
                name_element = rte.find('gpx:name', self.ns)
                if name_element is not None and name_element.text:
                    route_info['name'] = name_element.text
                
                # ルート説明
                desc_element = rte.find('gpx:desc', self.ns)
                if desc_element is not None and desc_element.text:
                    route_info['description'] = desc_element.text
                
                # ポイント数
                points = rte.findall('gpx:rtept', self.ns)
                route_info['points'] = len(points)
                
                routes.append(route_info)
            
            if routes:
                gpx_info['routes'] = routes
            
            # ウェイポイント数
            waypoints = root.findall('gpx:wpt', self.ns)
            if waypoints:
                gpx_info['waypoints_count'] = len(waypoints)
        
        except Exception as e:
            self.warnings.append(f"GPXメタデータの抽出中にエラーが発生しました: {e}")
        
        return gpx_info
    
    def _collect_points(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        GPXファイルからすべてのポイントデータを収集
        
        Parameters
        ----------
        root : ET.Element
            GPXファイルのルート要素
            
        Returns
        -------
        List[Dict[str, Any]]
            ポイントデータのリスト
        """
        points = []
        
        # トラックポイントの収集
        if self.config['prefer_trkpt']:
            # トラックポイントを優先的に収集
            track_points = self._collect_trackpoints(root)
            if track_points:
                # トラックポイントが見つかった場合は、他のポイントはスキップ
                return track_points
        
        # トラックポイントの収集（優先しない場合または見つからなかった場合）
        track_points = self._collect_trackpoints(root)
        if track_points:
            points.extend(track_points)
        
        # ルートポイントの収集
        route_points = self._collect_routepoints(root)
        if route_points:
            points.extend(route_points)
        
        # ウェイポイントの収集（設定で有効な場合）
        if self.config['include_waypoints']:
            waypoints = self._collect_waypoints(root)
            if waypoints:
                points.extend(waypoints)
        
        return points
    
    def _collect_trackpoints(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        トラックポイントの収集
        
        Parameters
        ----------
        root : ET.Element
            GPXファイルのルート要素
            
        Returns
        -------
        List[Dict[str, Any]]
            トラックポイントのリスト
        """
        points = []
        
        # 各トラックセグメントのトラックポイントを収集
        for trkseg in root.findall('.//gpx:trkseg', self.ns):
            # セグメント内のポイントを収集
            for trkpt in trkseg.findall('gpx:trkpt', self.ns):
                point = self._parse_point(trkpt, point_type='trackpoint')
                if point:
                    points.append(point)
        
        # トラック名やセグメント情報を追加
        if points:
            # 各トラックの情報を取得
            tracks = root.findall('gpx:trk', self.ns)
            if len(tracks) == 1:
                # 単一トラックの場合
                track = tracks[0]
                track_name = track.find('gpx:name', self.ns)
                if track_name is not None and track_name.text:
                    for point in points:
                        point['track_name'] = track_name.text
        
        return points
    
    def _collect_routepoints(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        ルートポイントの収集
        
        Parameters
        ----------
        root : ET.Element
            GPXファイルのルート要素
            
        Returns
        -------
        List[Dict[str, Any]]
            ルートポイントのリスト
        """
        points = []
        
        # 各ルートのルートポイントを収集
        for rte in root.findall('gpx:rte', self.ns):
            route_name = None
            name_elem = rte.find('gpx:name', self.ns)
            if name_elem is not None and name_elem.text:
                route_name = name_elem.text
            
            # ルート内のポイントを収集
            for rtept in rte.findall('gpx:rtept', self.ns):
                point = self._parse_point(rtept, point_type='routepoint')
                if point:
                    if route_name:
                        point['route_name'] = route_name
                    points.append(point)
        
        return points
    
    def _collect_waypoints(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        ウェイポイントの収集
        
        Parameters
        ----------
        root : ET.Element
            GPXファイルのルート要素
            
        Returns
        -------
        List[Dict[str, Any]]
            ウェイポイントのリスト
        """
        points = []
        
        # ウェイポイントを収集
        for wpt in root.findall('gpx:wpt', self.ns):
            point = self._parse_point(wpt, point_type='waypoint')
            if point:
                points.append(point)
        
        return points
    
    def _parse_point(self, point_element: ET.Element, point_type: str = '') -> Optional[Dict[str, Any]]:
        """
        ポイント要素をパース
        
        Parameters
        ----------
        point_element : ET.Element
            パースするポイント要素
        point_type : str, optional
            ポイントのタイプ
            
        Returns
        -------
        Optional[Dict[str, Any]]
            パースしたポイントデータ（失敗した場合はNone）
        """
        try:
            # 緯度・経度を取得
            lat = float(point_element.attrib.get('lat'))
            lon = float(point_element.attrib.get('lon'))
            
            # タイムスタンプの取得
            time_element = point_element.find('gpx:time', self.ns)
            if time_element is not None and time_element.text:
                timestamp = pd.to_datetime(time_element.text)
            else:
                # タイムスタンプがない場合は現在時刻を使用
                timestamp = pd.Timestamp.now()
                if point_type != 'trackpoint':  # トラックポイント以外の場合は警告
                    self.warnings.append(f"タイムスタンプがない{point_type}が見つかりました。現在時刻を使用します。")
            
            # 基本データの作成
            point_data = {
                'timestamp': timestamp,
                'latitude': lat,
                'longitude': lon,
                'point_type': point_type
            }
            
            # 高度の取得
            ele_element = point_element.find('gpx:ele', self.ns)
            if ele_element is not None and ele_element.text:
                point_data['elevation'] = float(ele_element.text)
            
            # 名前（主にウェイポイントで使用）
            name_element = point_element.find('gpx:name', self.ns)
            if name_element is not None and name_element.text:
                point_data['name'] = name_element.text
            
            # 説明
            desc_element = point_element.find('gpx:desc', self.ns)
            if desc_element is not None and desc_element.text:
                point_data['description'] = desc_element.text
            
            # 拡張データの取得
            if self.config['include_extensions']:
                extensions = point_element.find('gpx:extensions', self.ns)
                if extensions is not None:
                    self._parse_extensions(extensions, point_data)
            
            return point_data
            
        except Exception as e:
            self.warnings.append(f"ポイントデータの解析に失敗しました: {e}")
            return None
    
    def _parse_extensions(self, extensions: ET.Element, point_data: Dict[str, Any]) -> None:
        """
        拡張データを解析してポイントデータに追加
        
        Parameters
        ----------
        extensions : ET.Element
            拡張データ要素
        point_data : Dict[str, Any]
            追加先のポイントデータ
        """
        # サポートされている各拡張データタイプについて検索
        for target_field, xpath_patterns in self.supported_extensions.items():
            for pattern in xpath_patterns:
                # 様々な名前空間パターンで検索
                elem = extensions.find(f'.//{pattern}')
                if elem is None:
                    elem = extensions.find(f'.//gpxtpx:{pattern}', self.ns)
                if elem is None:
                    elem = extensions.find(f'.//ns3:{pattern}', self.ns)
                if elem is None:
                    elem = extensions.find(f'.//*[local-name()="{pattern}"]')
                
                if elem is not None and elem.text:
                    try:
                        point_data[target_field] = float(elem.text)
                        break  # このフィールドは処理完了
                    except ValueError:
                        # 数値に変換できない場合は文字列として追加
                        point_data[target_field] = elem.text
                        break
        
        # Garmin拡張がある場合は特別処理
        tpx = extensions.find('.//gpxtpx:TrackPointExtension', self.ns)
        if tpx is not None:
            self._parse_garmin_extensions(tpx, point_data)
    
    def _parse_garmin_extensions(self, tpx: ET.Element, point_data: Dict[str, Any]) -> None:
        """
        Garmin拡張データを解析
        
        Parameters
        ----------
        tpx : ET.Element
            TrackPointExtension要素
        point_data : Dict[str, Any]
            追加先のポイントデータ
        """
        # 心拍数
        hr_elem = tpx.find('gpxtpx:hr', self.ns)
        if hr_elem is not None and hr_elem.text:
            try:
                point_data['heart_rate'] = float(hr_elem.text)
            except ValueError:
                pass
        
        # ケイデンス
        cad_elem = tpx.find('gpxtpx:cad', self.ns)
        if cad_elem is not None and cad_elem.text:
            try:
                point_data['cadence'] = float(cad_elem.text)
            except ValueError:
                pass
        
        # 温度
        temp_elem = tpx.find('gpxtpx:atemp', self.ns)
        if temp_elem is not None and temp_elem.text:
            try:
                point_data['temperature'] = float(temp_elem.text)
            except ValueError:
                pass
        
        # 速度
        speed_elem = tpx.find('gpxtpx:speed', self.ns)
        if speed_elem is not None and speed_elem.text:
            try:
                point_data['speed'] = float(speed_elem.text)
            except ValueError:
                pass
        
        # コース（方向）
        course_elem = tpx.find('gpxtpx:course', self.ns)
        if course_elem is not None and course_elem.text:
            try:
                point_data['course'] = float(course_elem.text)
            except ValueError:
                pass
    
    def get_available_tracks(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> List[Dict[str, Any]]:
        """
        GPXファイル内のトラック情報を取得
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            GPXファイルのパスまたはファイルオブジェクト
            
        Returns
        -------
        List[Dict[str, Any]]
            トラック情報のリスト
        """
        self.clear_messages()
        
        if not self.can_import(file_path):
            self.errors.append("GPXファイルとして認識できません")
            return []
        
        try:
            # ファイルをパース
            root = self._parse_gpx_file(file_path)
            if root is None:
                return []
            
            # トラック情報の取得
            tracks = []
            for i, trk in enumerate(root.findall('gpx:trk', self.ns)):
                track_info = {
                    'index': i,
                    'id': f"track_{i}"
                }
                
                # トラック名
                name_element = trk.find('gpx:name', self.ns)
                if name_element is not None and name_element.text:
                    track_info['name'] = name_element.text
                else:
                    track_info['name'] = f"Track {i+1}"
                
                # トラック説明
                desc_element = trk.find('gpx:desc', self.ns)
                if desc_element is not None and desc_element.text:
                    track_info['description'] = desc_element.text
                
                # セグメント数
                segments = trk.findall('gpx:trkseg', self.ns)
                track_info['segments'] = len(segments)
                
                # ポイント数
                points_count = 0
                for seg in segments:
                    points_count += len(seg.findall('gpx:trkpt', self.ns))
                track_info['points'] = points_count
                
                # 時間範囲
                times = []
                for trkpt in trk.findall('.//gpx:trkpt/gpx:time', self.ns):
                    if trkpt.text:
                        try:
                            times.append(pd.to_datetime(trkpt.text))
                        except:
                            pass
                
                if times:
                    track_info['start_time'] = min(times).isoformat()
                    track_info['end_time'] = max(times).isoformat()
                    track_info['duration_seconds'] = (max(times) - min(times)).total_seconds()
                
                tracks.append(track_info)
            
            return tracks
            
        except Exception as e:
            self.errors.append(f"GPXファイルの解析に失敗しました: {e}")
            return []
    
    def import_specific_track(self, file_path: Union[str, Path, BinaryIO, TextIO], 
                             track_index: int, metadata: Optional[Dict[str, Any]] = None) -> Optional[GPSDataContainer]:
        """
        指定したトラックのみをインポート
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            GPXファイルのパスまたはファイルオブジェクト
        track_index : int
            インポートするトラックのインデックス
        metadata : Optional[Dict[str, Any]], optional
            メタデータ
            
        Returns
        -------
        Optional[GPSDataContainer]
            インポートしたデータのコンテナ（失敗した場合はNone）
        """
        self.clear_messages()
        
        if not self.can_import(file_path):
            self.errors.append("GPXファイルとして認識できません")
            return None
        
        try:
            # ファイルをパース
            root = self._parse_gpx_file(file_path)
            if root is None:
                return None
            
            # 指定されたトラックの取得
            tracks = root.findall('gpx:trk', self.ns)
            if not tracks:
                self.errors.append("GPXファイルにトラックが見つかりません")
                return None
            
            if track_index < 0 or track_index >= len(tracks):
                self.errors.append(f"指定されたトラックインデックス {track_index} が範囲外です (0-{len(tracks)-1})")
                return None
            
            track = tracks[track_index]
            
            # トラック情報の取得
            track_info = {}
            name_element = track.find('gpx:name', self.ns)
            if name_element is not None and name_element.text:
                track_info['track_name'] = name_element.text
            
            # ポイントの収集
            points = []
            for trkseg in track.findall('gpx:trkseg', self.ns):
                for trkpt in trkseg.findall('gpx:trkpt', self.ns):
                    point = self._parse_point(trkpt, point_type='trackpoint')
                    if point:
                        if 'track_name' in track_info:
                            point['track_name'] = track_info['track_name']
                        points.append(point)
            
            if not points:
                self.errors.append(f"トラック {track_index} にポイントデータが見つかりません")
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
                metadata['source'] = 'gpx_import'
            
            # トラック情報をメタデータに追加
            metadata['track_index'] = track_index
            for key, value in track_info.items():
                if key not in metadata:
                    metadata[key] = value
            
            # GPSデータコンテナの作成
            container = GPSDataContainer(df, metadata)
            
            return container
            
        except Exception as e:
            self.errors.append(f"GPXトラックのインポートに失敗しました: {e}")
            return None
