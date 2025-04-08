"""
sailing_data_processor.importers.csv_importer

CSVファイルからGPSデータをインポートするモジュール
"""

from typing import Dict, List, Any, Optional, Union, BinaryIO, TextIO, Tuple
import pandas as pd
from pathlib import Path
import io
import os
import csv
import re

from .base_importer import BaseImporter
from sailing_data_processor.data_model.container import GPSDataContainer

# 列マッピングの自動提案用パターン定義
DEFAULT_COLUMN_PATTERNS = {
    "timestamp": [
        "time", "date", "timestamp", "datetime", "recorded", "created", 
        "time_utc", "utc_time", "gps_time", "time_stamp", "時刻", "日時",
        "dt", "date_time", "gps_datetime", "log_time", "log_datetime",
        "time_stamp", "record_time", "sample_time", "測定時間", "計測時間",
        "timeStamp", "dateTime", "recordTime", "logTime"
    ],
    "latitude": [
        "lat", "latitude", "緯度", "緯度（度）", "y", "lat_deg", "纬度",
        "gps_lat", "latitude_deg", "lat_degrees", "緯度", "緯度(度)",
        "position_lat", "position_latitude", "gps_latitude", "y_coord",
        "northing", "緯度座標", "gps緯度"
    ],
    "longitude": [
        "lon", "lng", "longitude", "経度", "経度（度）", "x", "lon_deg", "经度",
        "gps_lon", "longitude_deg", "lon_degrees", "経度", "経度(度)",
        "position_lon", "position_longitude", "gps_longitude", "x_coord",
        "easting", "経度座標", "gps経度"
    ],
    "speed": [
        "speed", "velocity", "spd", "速度", "speed (m/s)", "speed_kph", "speed_knots",
        "ground_speed", "船速", "対地速度", "速度(kt)", "knots", "kph", "mph",
        "sog", "speed_over_ground", "gps_speed", "boat_speed", "船舶速度", 
        "対水速度", "speed_kn", "speed_ms", "speed_mps", "speed_unit"
    ],
    "course": [
        "course", "heading", "direction", "track", "bearing", "cog", "進行方向", "方位",
        "direction_deg", "heading_deg", "course_over_ground", "方向", "船首方位",
        "true_heading", "magnetic_heading", "hdg", "船頭方位", "進路", "コース", 
        "true_course", "真方位", "relative_direction", "absolute_direction",
        "track_angle", "track_direction", "船舶進行方向"
    ],
    "elevation": [
        "ele", "elev", "elevation", "altitude", "高度", "高さ", "alt", "height",
        "gps_alt", "gps_altitude", "gps_elevation", "altitude_m", "altitude_meters",
        "height_m", "height_meters", "海抜", "標高", "水面からの高さ"
    ],
    "heart_rate": [
        "hr", "heart", "心拍", "心拍数", "pulse", "heart_rate", "bpm",
        "heart_beat", "heart_beats_per_minute", "heartrate"
    ],
    "cadence": [
        "cad", "cadence", "ケイデンス", "回転数", "stroke_rate",
        "strokes_per_minute", "rpm", "revolutions_per_minute",
        "pedal_cadence", "rowing_cadence", "stroke_cadence"
    ],
    "power": [
        "power", "pwr", "pow", "パワー", "出力", "watts",
        "power_output", "watt", "power_w", "engine_power", "motor_power"
    ],
    "distance": [
        "dist", "distance", "距離", "cumulative_distance", "total_distance", "odometer",
        "distance_m", "distance_meters", "distance_travelled", "trip_distance",
        "accumulated_distance", "leg_distance", "trip_meter", "走行距離"
    ],
    "temperature": [
        "temp", "temperature", "気温", "温度", "water_temp", "water_temperature", "水温",
        "air_temp", "air_temperature", "outside_temp", "ambient_temp", "環境温度",
        "temp_c", "temp_f", "temperature_celsius", "temperature_fahrenheit"
    ],
    "wind_speed": [
        "wind_speed", "wind_velocity", "風速", "gust", "wind_gust", "apparent_wind_speed",
        "true_wind_speed", "wind_knots", "wind_kph", "wind_mps", "風の強さ"
    ],
    "wind_direction": [
        "wind_dir", "wind_direction", "風向", "wind_angle", "wind_deg", "wind_degrees",
        "true_wind_direction", "apparent_wind_direction", "wind_heading", "風向角度"
    ]
}


class CSVImporter(BaseImporter):
    """
    CSVファイルからGPSデータをインポートするクラス
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初期化
        
        Parameters
        ----------
        config : Optional[Dict[str, Any]], optional
            インポーター設定（列マッピング、区切り文字など）
        """
        super().__init__(config)
        
        # デフォルト設定
        if 'delimiter' not in self.config:
            self.config['delimiter'] = ','
        
        if 'column_mapping' not in self.config:
            self.config['column_mapping'] = {
                'timestamp': 'timestamp',
                'latitude': 'latitude',
                'longitude': 'longitude'
            }
        
        if 'encoding' not in self.config:
            self.config['encoding'] = 'utf-8'
            
        if 'header_row' not in self.config:
            self.config['header_row'] = 0
            
        if 'skip_rows' not in self.config:
            self.config['skip_rows'] = None
            
        if 'date_format' not in self.config:
            self.config['date_format'] = None
            
        if 'auto_detect_columns' not in self.config:
            self.config['auto_detect_columns'] = True
        
        if 'skiprows' not in self.config:
            self.config['skiprows'] = 0
    
    def can_import(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> bool:
        """
        ファイルがCSVとしてインポート可能かどうかを判定
        
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
        if extension.lower() == 'csv':
            return True
        
        # ファイル内容による判定（一部を読み込んでCSVとして解析できるか）
        try:
            if isinstance(file_path, (str, Path)):
                with open(file_path, 'r', encoding=self.config['encoding']) as f:
                    sample = f.read(1024)
            else:
                # ファイルオブジェクトの場合、現在位置を保存して先頭に戻す
                if hasattr(file_path, 'tell') and hasattr(file_path, 'seek'):
                    pos = file_path.tell()
                    file_path.seek(0)
                    sample = file_path.read(1024)
                    file_path.seek(pos)
                else:
                    sample = file_path.read(1024)
                
                if isinstance(sample, bytes):
                    sample = sample.decode(self.config['encoding'])
            
            # CSVとして解析できるかチェック
            dialect = csv.Sniffer().sniff(sample)
            return True
        except Exception as e:
            self.errors.append(f"CSVファイルの検証に失敗しました: {e}")
            return False
    
    def import_data(self, file_path: Union[str, Path, BinaryIO, TextIO], 
                   metadata: Optional[Dict[str, Any]] = None) -> Optional[GPSDataContainer]:
        """
        CSVからデータをインポート
        
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
            self.errors.append("CSVファイルとして認識できません")
            return None
        
        try:
            # CSVファイルの読み込み
            df = self._read_csv_file(file_path)
            if df is None:
                return None
            
            # CSVファイルの概要情報をメタデータに追加
            if metadata is None:
                metadata = {}
            
            metadata.update({
                'csv_info': {
                    'columns': list(df.columns),
                    'rows': len(df),
                    'delimiter': self.config.get('delimiter', ','),
                    'encoding': self.config.get('encoding', 'utf-8')
                }
            })
            
            # 列マッピングの適用
            df = self._apply_column_mapping(df)
            if df is None:
                return None
            
            # 必須列の検証
            if not self.validate_dataframe(df):
                return None
            
            # タイムスタンプの変換
            df = self._convert_timestamp(df)
            if df is None:
                return None
            
            # メタデータの準備
            if 'boat_name' not in metadata:
                metadata['boat_name'] = self.get_file_name(file_path)
            
            if 'source' not in metadata:
                metadata['source'] = 'csv_import'
            
            # 元の列名も保存
            if 'original_columns' not in metadata:
                metadata['original_columns'] = list(df.columns)
            
            # GPSデータコンテナの作成
            container = GPSDataContainer(df, metadata)
            
            return container
        
        except Exception as e:
            self.errors.append(f"CSVファイルの読み込みに失敗しました: {e}")
            return None
    
    def _read_csv_file(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> Optional[pd.DataFrame]:
        """
        CSVファイルを読み込み、DataFrameを返す
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            インポート対象ファイルのパスまたはファイルオブジェクト
            
        Returns
        -------
        Optional[pd.DataFrame]
            読み込んだDataFrame（失敗した場合はNone）
        """
        try:
            # 読み込みオプションの設定
            read_options = {
                'delimiter': self.config['delimiter'],
                'encoding': self.config['encoding'],
                'skiprows': self.config['skiprows'],
                'on_bad_lines': 'warn'  # 不正な行があっても警告のみ
            }
            
            # ヘッダー行の設定
            if 'header_row' in self.config:
                read_options['header'] = self.config['header_row']
            
            # スキップする行の設定
            if 'skip_rows' in self.config and self.config['skip_rows'] is not None:
                read_options['skiprows'] = self.config['skip_rows']
            
            # ファイルの読み込み方法を決定
            if isinstance(file_path, (str, Path)):
                df = pd.read_csv(file_path, **read_options)
            else:
                # ファイルオブジェクトの場合、現在位置を保存して先頭に戻す
                if hasattr(file_path, 'tell') and hasattr(file_path, 'seek'):
                    pos = file_path.tell()
                    file_path.seek(0)
                    
                if isinstance(file_path.read(1), bytes):
                    # バイナリモードの場合
                    file_path.seek(0)
                    content = file_path.read()
                    try:
                        text_content = content.decode(self.config['encoding'])
                        df = pd.read_csv(io.StringIO(text_content), **read_options)
                    except UnicodeDecodeError:
                        # エンコーディングが違う場合、他の一般的なエンコーディングを試す
                        # 一般的なエンコーディングリスト（日本語対応を含む）
                        common_encodings = [
                            'utf-8', 'utf-8-sig',  # UTF-8（BOMあり/なし）
                            'latin1', 'cp1252',    # 欧米言語
                            'shift-jis', 'cp932',  # 日本語
                            'euc-jp', 'iso-2022-jp', # 日本語
                            'gb2312', 'gbk', 'gb18030',  # 中国語
                            'euc-kr', 'cp949',     # 韓国語
                            'utf-16', 'utf-16-le', 'utf-16-be'  # その他のUnicode
                        ]
                        
                        for encoding in common_encodings:
                            try:
                                text_content = content.decode(encoding)
                                df = pd.read_csv(io.StringIO(text_content), **read_options)
                                self.warnings.append(f"エンコーディングを {encoding} に変更しました")
                                self.config['encoding'] = encoding
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                        else:
                            self.errors.append("ファイルのエンコーディングを認識できません")
                            return None
                else:
                    # テキストモードの場合
                    file_path.seek(0)
                    df = pd.read_csv(file_path, **read_options)
                
                # 読み込み位置を元に戻す
                if hasattr(file_path, 'seek'):
                    file_path.seek(pos)
            
            # データフレームの前処理
            # 列名の先頭と末尾の空白を削除
            df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
            
            # データフレームが空でないことを確認
            if len(df) == 0:
                self.errors.append("CSVファイルにデータがありません")
                return None
            
            return df
            
        except Exception as e:
            self.errors.append(f"CSVファイルの読み込みに失敗しました: {e}")
            return None
    
    def _apply_column_mapping(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        列マッピングを適用
        
        Parameters
        ----------
        df : pd.DataFrame
            マッピング前のDataFrame
            
        Returns
        -------
        Optional[pd.DataFrame]
            マッピング後のDataFrame（失敗した場合はNone）
        """
        try:
            column_mapping = self.config['column_mapping']
            
            # 自動マッピングのフラグがあれば自動マッピングを試行
            if self.config.get('auto_detect_columns', False) or not column_mapping:
                suggested_mapping = self.suggest_column_mapping(df.columns)
                
                # 既存のマッピングと提案されたマッピングをマージ
                for target, source in suggested_mapping.items():
                    if target not in column_mapping or column_mapping[target] not in df.columns:
                        column_mapping[target] = source
            
            # マッピングに存在するカラムだけを適用
            rename_dict = {}
            for target_col, source_col in column_mapping.items():
                if source_col in df.columns:
                    rename_dict[source_col] = target_col
            
            # 列名を変更
            if rename_dict:
                # マッピングされていない元の列も保持
                df = df.rename(columns=rename_dict)
            
            # 必須列がマッピングされているか確認
            required_columns = ['timestamp', 'latitude', 'longitude']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                missing_cols_str = ', '.join(missing_columns)
                self.errors.append(f"必須列がマッピングされていません: {missing_cols_str}")
                return None
            
            return df
            
        except Exception as e:
            self.errors.append(f"列マッピングの適用に失敗しました: {e}")
            return None
    
    def _convert_timestamp(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        タイムスタンプカラムを変換
        
        Parameters
        ----------
        df : pd.DataFrame
            変換前のDataFrame
            
        Returns
        -------
        Optional[pd.DataFrame]
            変換後のDataFrame（失敗した場合はNone）
        """
        try:
            # タイムスタンプがdatetimeでない場合は変換
            if df['timestamp'].dtype == 'object':
                # 指定された日付フォーマットがあれば使用
                date_format = self.config.get('date_format')
                
                if date_format:
                    try:
                        df['timestamp'] = pd.to_datetime(df['timestamp'], format=date_format, errors='coerce')
                    except Exception as e:
                        self.warnings.append(f"指定された日付フォーマットでの変換に失敗しました: {e}")
                        # フォーマット指定なしで再試行
                        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                else:
                    # まず自動検出で試みる（強制的にエラーをcoerceに設定）
                    print(f"タイムスタンプカラムのデータ型: {df['timestamp'].dtype}")
                    print(f"タイムスタンプのサンプル: {df['timestamp'].head().tolist()}")
                    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                    
                    # 変換失敗が多い場合は一般的なフォーマットを順に試す
                    null_count = df['timestamp'].isnull().sum()
                    if null_count > 0 and (null_count / len(df)) > 0.1:  # 10%以上が変換失敗
                        # 一般的な日付形式のリスト
                        common_formats = [
                            # ISO形式
                            '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f',
                            # 日付のみ
                            '%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y',
                            # 日本の形式
                            '%Y年%m月%d日', '%Y年%m月%d日%H時%M分%S秒',
                            # 時刻付き
                            '%Y/%m/%d %H:%M:%S', '%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S',
                            # UNIXタイムスタンプ（もしテキスト形式なら）
                            '%s'
                        ]
                        
                        # 各フォーマットを試す
                        for fmt in common_formats:
                            try:
                                # 念のため必ずerrors='coerce'を指定
                                temp_df = pd.to_datetime(df['timestamp'], format=fmt, errors='coerce')
                                new_null_count = temp_df.isnull().sum()
                                
                                # 以前より変換できた行が増えたら採用
                                if new_null_count < null_count:
                                    df['timestamp'] = temp_df
                                    self.warnings.append(f"フォーマット '{fmt}' で日付変換を行いました")
                                    null_count = new_null_count
                                    
                                    # すべてが変換できたら終了
                                    if null_count == 0:
                                        break
                            except Exception as e:
                                # エラーログを追加
                                self.warnings.append(f"フォーマット '{fmt}' での変換中にエラー: {e}")
                                continue
                
                # タイムスタンプが数値の場合（UNIXタイムスタンプなど）
                try:
                    numeric_timestamps = pd.to_numeric(df['timestamp'], errors='coerce')
                    if numeric_timestamps.notnull().all():
                        # 数値の大きさでUNIXタイムスタンプかミリ秒タイムスタンプかを判断
                        try:
                            if (numeric_timestamps > 1e10).any():  # ミリ秒タイムスタンプ
                                df['timestamp'] = pd.to_datetime(numeric_timestamps, unit='ms', errors='coerce')
                                self.warnings.append("タイムスタンプをミリ秒単位のUNIXタイムスタンプとして変換しました")
                            else:  # 秒タイムスタンプ
                                df['timestamp'] = pd.to_datetime(numeric_timestamps, unit='s', errors='coerce')
                                self.warnings.append("タイムスタンプを秒単位のUNIXタイムスタンプとして変換しました")
                        except Exception as e:
                            self.warnings.append(f"タイムスタンプの数値変換中にエラー: {e}")
                except Exception as e:
                    self.warnings.append(f"タイムスタンプの数値解析に失敗しました: {e}")
                
                # 変換できなかったレコードをチェック
                null_timestamps = df['timestamp'].isnull().sum()
                if null_timestamps > 0:
                    self.warnings.append(f"{null_timestamps}行のタイムスタンプを変換できませんでした")
                    
                    # nullの割合が大きい場合はエラー
                    if null_timestamps / len(df) > 0.9:  # 90%以上が変換できない場合
                        self.errors.append("タイムスタンプの変換に失敗したレコードが多すぎます")
                        return None
                    
                    # null値を含む行を削除
                    df = df.dropna(subset=['timestamp']).reset_index(drop=True)
                
                # 時間順にソート
                try:
                    df = df.sort_values('timestamp').reset_index(drop=True)
                except Exception as e:
                    self.warnings.append(f"時間順ソートに失敗しました: {e}")
            
            return df
            
        except Exception as e:
            self.errors.append(f"タイムスタンプの変換に失敗しました: {e}")
            return None
    
    def suggest_column_mapping(self, columns: List[str]) -> Dict[str, str]:
        """
        列名のパターンに基づいて自動マッピングを提案
        
        Parameters
        ----------
        columns : List[str]
            入力ファイルの列名リスト
            
        Returns
        -------
        Dict[str, str]
            提案されたマッピング（ターゲット列: ソース列）
        """
        suggested_mapping = {}
        
        # 列名の正規化とケース変換
        normalized_columns = []
        for col in columns:
            if not isinstance(col, str):
                col = str(col)
            
            # 正規化された列名と元の列名のマッピング
            normalized = self._normalize_column_name(col)
            normalized_columns.append((normalized, col))
        
        # 各ターゲットフィールドに対してマッピングを探す
        for target_field, patterns in DEFAULT_COLUMN_PATTERNS.items():
            best_match = None
            best_match_score = 0
            
            # 各パターンを正規化
            normalized_patterns = [self._normalize_column_name(pattern) for pattern in patterns]
            
            # 各列に対して各パターンをテスト
            for normalized_col, original_col in normalized_columns:
                # 完全一致をチェック（最高優先度）
                if normalized_col in normalized_patterns:
                    suggested_mapping[target_field] = original_col
                    best_match = original_col
                    break
                
                # 部分一致評価スコア計算
                for pattern in normalized_patterns:
                    # スコアリング基準（0-10のスケール）
                    score = 0
                    
                    # 正規化後の完全一致は高スコア
                    if normalized_col == pattern:
                        score = 10
                    # 先頭一致は次に高いスコア
                    elif normalized_col.startswith(pattern):
                        score = 8
                    # 末尾一致
                    elif normalized_col.endswith(pattern):
                        score = 7
                    # '_'区切りで完全一致する部分がある場合 (e.g. gps_lat in gps_lat_degrees)
                    elif f"_{pattern}" in normalized_col or f"{pattern}_" in normalized_col:
                        score = 6
                    # 部分一致
                    elif pattern in normalized_col:
                        # パターンの長さが長いほど高スコア（より具体的なマッチ）
                        pattern_length_ratio = len(pattern) / len(normalized_col) if len(normalized_col) > 0 else 0
                        score = 3 + (pattern_length_ratio * 2)  # 3-5のスコア範囲
                    
                    # 名詞の複数形など、minor variantsも考慮（例：longitude vs longitudes）
                    if score == 0:
                        if (pattern.endswith('s') and normalized_col == pattern[:-1]) or \
                           (normalized_col.endswith('s') and pattern == normalized_col[:-1]):
                            score = 5
                    
                    if score > best_match_score:
                        best_match_score = score
                        best_match = original_col
            
            # スコアが閾値以上なら採用
            if best_match is not None and (best_match_score >= 3 or best_match in suggested_mapping.values()):
                suggested_mapping[target_field] = best_match
        
        return suggested_mapping
    
    def _normalize_column_name(self, column_name: str) -> str:
        """
        列名を正規化（小文字化、特殊文字除去、複数の区切り文字の統一など）
        
        Parameters
        ----------
        column_name : str
            正規化する列名
            
        Returns
        -------
        str
            正規化された列名
        """
        if not isinstance(column_name, str):
            column_name = str(column_name)
        
        # 小文字に変換
        name = column_name.lower()
        
        # 括弧や特殊文字の除去
        name = re.sub(r'[\(\)\[\]\{\}\<\>\'\"\/\\]', '', name)
        
        # キャメルケースをスネークケースに変換 (e.g., "timeStamp" -> "time_stamp")
        name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
        
        # ケバブケース、スペース区切りをアンダースコアに統一
        name = re.sub(r'[-\s]+', '_', name)
        
        # 複数のアンダースコアを単一に
        name = re.sub(r'_+', '_', name)
        
        # 前後の空白とアンダースコアを削除
        name = name.strip('_').strip()
        
        # 単位の除去 (例: "speed_kn" -> "speed", "temp_c" -> "temp")
        name = re.sub(r'_(m|cm|km|kn|knots|kt|mph|kph|ms|mps|deg|degrees|c|f|g|meter|meters|sec|seconds|min|mins|hr|hrs)$', '', name)
        
        return name
    
    def analyze_csv_structure(self, file_path: Union[str, Path, BinaryIO, TextIO]) -> Dict[str, Any]:
        """
        CSVファイルの構造を分析
        
        Parameters
        ----------
        file_path : Union[str, Path, BinaryIO, TextIO]
            分析対象ファイルのパスまたはファイルオブジェクト
            
        Returns
        -------
        Dict[str, Any]
            CSVの構造情報（区切り文字、列名、サンプルデータなど）
        """
        self.clear_messages()
        
        if not self.can_import(file_path):
            self.errors.append("CSVファイルとして認識できません")
            return {}
        
        try:
            # サンプルデータの取得
            if isinstance(file_path, (str, Path)):
                with open(file_path, 'r', encoding=self.config['encoding']) as f:
                    sample = f.read(4096)  # 最初の4KBを読み込む
            else:
                # ファイルオブジェクトの場合
                if hasattr(file_path, 'tell') and hasattr(file_path, 'seek'):
                    pos = file_path.tell()
                    file_path.seek(0)
                    sample = file_path.read(4096)
                    file_path.seek(pos)
                else:
                    sample = file_path.read(4096)
                
                if isinstance(sample, bytes):
                    sample = sample.decode(self.config['encoding'])
            
            # 区切り文字の検出
            try:
                # CSV Snifferを使用して区切り文字を検出
                dialect = csv.Sniffer().sniff(sample)
                delimiter = dialect.delimiter
                self.config['delimiter'] = delimiter
            except Exception as dialect_error:
                # Snifferが失敗した場合、頻出区切り文字で内容チェック
                common_delimiters = [',', ';', '\t', '|', ' ']
                best_delimiter = None
                max_columns = 0
                
                # 各区切り文字でサンプルの最初の行を分割し、列数が最大のものを選択
                for delim in common_delimiters:
                    try:
                        lines = sample.split('\n')[:5]  # 最初の5行を使用
                        if not lines:
                            continue
                            
                        # 各行を分割した列数を計算
                        columns_counts = []
                        for line in lines:
                            if line.strip():  # 空行をスキップ
                                cols = len(line.split(delim))
                                columns_counts.append(cols)
                        
                        # 列数の平均
                        if columns_counts:
                            avg_columns = sum(columns_counts) / len(columns_counts)
                            
                            # 列数が3以上かつ最大の場合、このデリミタを採用
                            if avg_columns >= 3 and avg_columns > max_columns:
                                max_columns = avg_columns
                                best_delimiter = delim
                    except:
                        continue
                
                # 最適な区切り文字が見つかれば設定
                if best_delimiter:
                    delimiter = best_delimiter
                    self.config['delimiter'] = delimiter
                    self.warnings.append(f"区切り文字を自動検出しました: '{delimiter}'")
                else:
                    # 見つからなければデフォルト設定を使用
                    delimiter = self.config['delimiter']
                    self.warnings.append(f"区切り文字の自動検出に失敗しました。デフォルト '{delimiter}' を使用します。")
            
            # ヘッダーの有無を検出
            try:
                has_header = csv.Sniffer().has_header(sample)
            except:
                has_header = True
            
            # 列名の取得
            try:
                df_sample = pd.read_csv(
                    io.StringIO(sample), 
                    delimiter=delimiter,
                    nrows=5,
                    encoding=self.config['encoding']
                )
                columns = list(df_sample.columns)
                
                # データ型の推定
                dtypes = {}
                for col in df_sample.columns:
                    if pd.api.types.is_numeric_dtype(df_sample[col]):
                        dtypes[col] = 'numeric'
                    elif pd.api.types.is_datetime64_dtype(df_sample[col]):
                        dtypes[col] = 'datetime'
                    else:
                        # 日付形式を推定
                        try:
                            pd.to_datetime(df_sample[col], errors='raise')
                            dtypes[col] = 'datetime'
                        except:
                            dtypes[col] = 'string'
                
                # 自動マッピングの提案
                suggested_mapping = self.suggest_column_mapping(columns)
                
                return {
                    'delimiter': delimiter,
                    'has_header': has_header,
                    'columns': columns,
                    'dtypes': dtypes,
                    'sample_data': df_sample.to_dict(orient='records'),
                    'suggested_mapping': suggested_mapping,
                    'encoding': self.config['encoding']
                }
            except Exception as e:
                self.warnings.append(f"サンプルデータの解析に失敗しました: {e}")
                return {
                    'delimiter': delimiter,
                    'has_header': has_header,
                    'error': str(e)
                }
            
        except Exception as e:
            self.errors.append(f"CSVファイルの構造分析に失敗しました: {e}")
            return {}
