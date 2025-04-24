"""
sailing_data_processor.validation.data_validator

GPSデータの検証を行うモジュール
"""

from typing import Dict, List, Any, Optional, Callable, Tuple, Set
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

from sailing_data_processor.data_model.container import GPSDataContainer

# ロガーの設定
logger = logging.getLogger(__name__)


class ValidationRule:
    """
    データ検証ルールの基底クラス
    
    Parameters
    ----------
    name : str
        ルール名
    description : str
        ルールの説明
    severity : str
        重要度（'error', 'warning', 'info'）
    """
    
    def __init__(self, name: str, description: str, severity: str = 'error'):
        self.name = name
        self.description = description
        self.severity = severity
    
    def validate(self, data: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        データを検証
        
        Parameters
        ----------
        data : pd.DataFrame
            検証するデータフレーム
            
        Returns
        -------
        Tuple[bool, Dict[str, Any]]
            検証結果（True: 検証成功、False: 検証失敗）と詳細情報の辞書
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def __str__(self) -> str:
        return f"{self.name} ({self.severity}): {self.description}"


class RequiredColumnsRule(ValidationRule):
    """
    必須カラムの存在を検証するルール
    
    Parameters
    ----------
    required_columns : List[str]
        必須カラムのリスト
    name : str, optional
        ルール名
    description : str, optional
        ルールの説明
    severity : str, optional
        重要度
    """
    
    def __init__(self, required_columns: List[str], 
                 name: str = "Required Columns Check", 
                 description: str = "必須カラムが存在するか確認",
                 severity: str = 'error'):
        super().__init__(name, description, severity)
        self.required_columns = required_columns
    
    def validate(self, data: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        必須カラムの存在を検証
        
        Parameters
        ----------
        data : pd.DataFrame
            検証するデータフレーム
            
        Returns
        -------
        Tuple[bool, Dict[str, Any]]
            検証結果と詳細情報
        """
        missing_columns = [col for col in self.required_columns if col not in data.columns]
        
        is_valid = len(missing_columns) == 0
        
        details = {
            "missing_columns": missing_columns,
            "found_columns": [col for col in self.required_columns if col in data.columns],
            "all_columns": list(data.columns)
        
        return is_valid, details


class ValueRangeRule(ValidationRule):
    """
    値の範囲を検証するルール
    
    Parameters
    ----------
    column : str
        検証対象のカラム名
    min_value : Any, optional
        最小値
    max_value : Any, optional
        最大値
    name : str, optional
        ルール名
    description : str, optional
        ルールの説明
    severity : str, optional
        重要度
    """
    
    def __init__(self, column: str, min_value: Any = None, max_value: Any = None,
                 name: str = None, description: str = None, severity: str = 'error'):
        if name is None:
            name = f"Value Range Check for {column}"
        if description is None:
            if min_value is not None and max_value is not None:
                description = f"{column}の値が{min_value}から{max_value}の範囲内か確認"
            elif min_value is not None:
                description = f"{column}の値が{min_value}以上か確認"
            elif max_value is not None:
                description = f"{column}の値が{max_value}以下か確認"
            else:
                description = f"{column}の値範囲を確認"
        
        super().__init__(name, description, severity)
        self.column = column
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, data: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        値の範囲を検証
        
        Parameters
        ----------
        data : pd.DataFrame
            検証するデータフレーム
            
        Returns
        -------
        Tuple[bool, Dict[str, Any]]
            検証結果と詳細情報
        """
        if self.column not in data.columns:
            return False, {"error": f"カラム {self.column} が存在しません"}
        
        out_of_range_indices = []
        
        if self.min_value is not None and self.max_value is not None:
            # 最小値と最大値の両方が指定されている場合
            mask = (data[self.column] < self.min_value) | (data[self.column] > self.max_value)
            out_of_range_indices = data.index[mask].tolist()
        elif self.min_value is not None:
            # 最小値のみ指定されている場合
            mask = data[self.column] < self.min_value
            out_of_range_indices = data.index[mask].tolist()
        elif self.max_value is not None:
            # 最大値のみ指定されている場合
            mask = data[self.column] > self.max_value
            out_of_range_indices = data.index[mask].tolist()
        
        is_valid = len(out_of_range_indices) == 0
        
        details = {
            "column": self.column,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "out_of_range_count": len(out_of_range_indices),
            "out_of_range_indices": out_of_range_indices[:100],  # 最初の100個まで表示
            "actual_min": data[self.column].min() if len(data) > 0 else None,
            "actual_max": data[self.column].max() if len(data) > 0 else None
        
        return is_valid, details


class NoNullValuesRule(ValidationRule):
    """
    欠損値がないことを検証するルール
    
    Parameters
    ----------
    columns : List[str], optional
        検証対象のカラムリスト（指定しない場合はすべてのカラム）
    name : str, optional
        ルール名
    description : str, optional
        ルールの説明
    severity : str, optional
        重要度
    """
    
    def __init__(self, columns: Optional[List[str]] = None, 
                 name: str = "No Null Values Check", 
                 description: str = "欠損値がないか確認",
                 severity: str = 'warning'):
        super().__init__(name, description, severity)
        self.columns = columns
    
    def validate(self, data: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        欠損値がないことを検証
        
        Parameters
        ----------
        data : pd.DataFrame
            検証するデータフレーム
            
        Returns
        -------
        Tuple[bool, Dict[str, Any]]
            検証結果と詳細情報
        """
        if self.columns is None:
            # すべてのカラムを対象
            target_columns = data.columns
        else:
            # 指定されたカラムのうち、存在するものを対象
            target_columns = [col for col in self.columns if col in data.columns]
        
        if not target_columns:
            return False, {"error": "対象カラムが存在しません"}
        
        # 各カラムの欠損値数を計算
        null_counts = {col: data[col].isnull().sum() for col in target_columns}
        
        # 欠損値を含む行のインデックス
        null_indices = {}
        for col in target_columns:
            col_null_indices = data.index[data[col].isnull()].tolist()
            if col_null_indices:
                null_indices[col] = col_null_indices[:100]  # 最初の100個まで
        
        is_valid = all(count == 0 for count in null_counts.values())
        
        details = {
            "columns": list(target_columns),
            "null_counts": null_counts,
            "null_indices": null_indices,
            "total_null_count": sum(null_counts.values())
        
        return is_valid, details


class DuplicateTimestampRule(ValidationRule):
    """
    タイムスタンプの重複がないことを検証するルール
    
    Parameters
    ----------
    timestamp_column : str
        タイムスタンプカラム名
    name : str, optional
        ルール名
    description : str, optional
        ルールの説明
    severity : str, optional
        重要度
    """
    
    def __init__(self, timestamp_column: str = 'timestamp', 
                 name: str = "No Duplicate Timestamps", 
                 description: str = "タイムスタンプの重複がないか確認",
                 severity: str = 'warning'):
        super().__init__(name, description, severity)
        self.timestamp_column = timestamp_column
    
    def validate(self, data: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        タイムスタンプの重複がないことを検証
        
        Parameters
        ----------
        data : pd.DataFrame
            検証するデータフレーム
            
        Returns
        -------
        Tuple[bool, Dict[str, Any]]
            検証結果と詳細情報
        """
        if self.timestamp_column not in data.columns:
            return False, {"error": f"タイムスタンプカラム {self.timestamp_column} が存在しません"}
        
        # 重複するタイムスタンプを検出
        duplicate_mask = data[self.timestamp_column].duplicated()
        duplicate_timestamps = data.loc[duplicate_mask, self.timestamp_column].unique()
        
        is_valid = len(duplicate_timestamps) == 0
        
        # 重複インデックスグループの作成
        duplicate_indices = {}
        for ts in duplicate_timestamps[:20]:  # 最初の20個まで
            ts_mask = data[self.timestamp_column] == ts
            duplicate_indices[str(ts)] = data.index[ts_mask].tolist()
        
        details = {
            "duplicate_count": len(duplicate_timestamps),
            "duplicate_timestamps": [str(ts) for ts in duplicate_timestamps[:20]],
            "duplicate_indices": duplicate_indices
        
        return is_valid, details


class SpatialConsistencyRule(ValidationRule):
    """
    位置データの空間的整合性を検証するルール
    
    連続するポイント間の最大速度を超える移動がないことを確認
    
    Parameters
    ----------
    max_speed_knots : float
        最大許容速度（ノット）
    timestamp_column : str, optional
        タイムスタンプカラム名
    latitude_column : str, optional
        緯度カラム名
    longitude_column : str, optional
        経度カラム名
    name : str, optional
        ルール名
    description : str, optional
        ルールの説明
    severity : str, optional
        重要度
    """
    
    def __init__(self, max_speed_knots: float = 100.0, 
                 timestamp_column: str = 'timestamp',
                 latitude_column: str = 'latitude',
                 longitude_column: str = 'longitude',
                 name: str = "Spatial Consistency Check", 
                 description: str = "位置データの空間的整合性を確認",
                 severity: str = 'warning'):
        super().__init__(name, description, severity)
        self.max_speed_knots = max_speed_knots
        self.timestamp_column = timestamp_column
        self.latitude_column = latitude_column
        self.longitude_column = longitude_column
    
    def validate(self, data: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        位置データの空間的整合性を検証
        
        Parameters
        ----------
        data : pd.DataFrame
            検証するデータフレーム
            
        Returns
        -------
        Tuple[bool, Dict[str, Any]]
            検証結果と詳細情報
        """
        # 必要なカラムが存在するか確認
        required_columns = [self.timestamp_column, self.latitude_column, self.longitude_column]
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            return False, {"error": f"必要なカラムがありません: {', '.join(missing_columns)}"}
        
        if len(data) < 2:
            return True, {"message": "データポイントが不足しているため検証をスキップします"}
        
        # タイムスタンプでソート
        sorted_data = data.sort_values(self.timestamp_column).copy()
        
        # 距離と時間差を計算
        from geopy.distance import great_circle
        
        distances = []
        time_diffs = []
        speeds = []
        
        prev_lat = sorted_data[self.latitude_column].iloc[0]
        prev_lon = sorted_data[self.longitude_column].iloc[0]
        prev_time = sorted_data[self.timestamp_column].iloc[0]
        
        for i in range(1, len(sorted_data)):
            curr_lat = sorted_data[self.latitude_column].iloc[i]
            curr_lon = sorted_data[self.longitude_column].iloc[i]
            curr_time = sorted_data[self.timestamp_column].iloc[i]
            
            # 座標値がNaNや無限大でないか確認
            if (np.isfinite(prev_lat) and np.isfinite(prev_lon) and 
                np.isfinite(curr_lat) and np.isfinite(curr_lon)):
                try:
                    # 距離の計算（メートル単位）
                    distance = great_circle((prev_lat, prev_lon), (curr_lat, curr_lon)).meters
                    distances.append(distance)
                    
                    # 時間差の計算（秒単位）
                    time_diff = (curr_time - prev_time).total_seconds()
                    time_diffs.append(time_diff)
                    
                    # 速度の計算（ノット単位、1ノット = 0.514444 m/s）
                    if time_diff > 0:
                        speed = (distance / time_diff) / 0.514444
                    else:
                        speed = float('inf')
                    speeds.append(speed)
                except ValueError as e:
                    # 座標値が有効な範囲外の場合（例：緯度が±90度を超える場合）
                    logger.warning(f"無効な座標値でのdistance計算をスキップ: {e}")
                    # 計算をスキップ（次の点へ）
                    continue
            else:
                # 無効な座標値をスキップ
                logger.warning(f"無効な座標値をスキップ: prev({prev_lat}, {prev_lon}), curr({curr_lat}, {curr_lon})")
                continue
            
            prev_lat, prev_lon, prev_time = curr_lat, curr_lon, curr_time
        
        # 異常な速度を検出
        anomaly_indices = [i + 1 for i, speed in enumerate(speeds) if speed > self.max_speed_knots]
        
        is_valid = len(anomaly_indices) == 0
        
        # 異常詳細の作成
        anomaly_details = []
        for idx in anomaly_indices[:20]:  # 最初の20個まで
            anomaly_details.append({
                "index": idx,
                "original_index": sorted_data.index[idx],
                "timestamp": sorted_data[self.timestamp_column].iloc[idx],
                "position": (sorted_data[self.latitude_column].iloc[idx], 
                             sorted_data[self.longitude_column].iloc[idx]),
                "distance_meters": distances[idx - 1],
                "time_diff_seconds": time_diffs[idx - 1],
                "speed_knots": speeds[idx - 1]
            })
        
        details = {
            "anomaly_count": len(anomaly_indices),
            "anomaly_indices": anomaly_indices[:100],
            "max_calculated_speed": max(speeds) if speeds else 0,
            "min_calculated_speed": min(speeds) if speeds else 0,
            "avg_calculated_speed": sum(speeds) / len(speeds) if speeds else 0,
            "anomaly_details": anomaly_details
        
        return is_valid, details


class TemporalConsistencyRule(ValidationRule):
    """
    タイムスタンプの時間的整合性を検証するルール
    
    Parameters
    ----------
    timestamp_column : str, optional
        タイムスタンプカラム名
    max_time_gap : Optional[timedelta], optional
        最大許容時間ギャップ
    name : str, optional
        ルール名
    description : str, optional
        ルールの説明
    severity : str, optional
        重要度
    """
    
    def __init__(self, timestamp_column: str = 'timestamp', 
                 max_time_gap: Optional[timedelta] = None,
                 name: str = "Temporal Consistency Check", 
                 description: str = "タイムスタンプの時間的整合性を確認",
                 severity: str = 'warning'):
        super().__init__(name, description, severity)
        self.timestamp_column = timestamp_column
        self.max_time_gap = max_time_gap or timedelta(minutes=5)
    
    def validate(self, data: pd.DataFrame) -> Tuple[bool, Dict[str, Any]]:
        """
        タイムスタンプの時間的整合性を検証
        
        Parameters
        ----------
        data : pd.DataFrame
            検証するデータフレーム
            
        Returns
        -------
        Tuple[bool, Dict[str, Any]]
            検証結果と詳細情報
        """
        if self.timestamp_column not in data.columns:
            return False, {"error": f"タイムスタンプカラム {self.timestamp_column} が存在しません"}
        
        if len(data) < 2:
            return True, {"message": "データポイントが不足しているため検証をスキップします"}
        
        # タイムスタンプでソート
        sorted_data = data.sort_values(self.timestamp_column).copy()
        
        # 時間差を計算
        time_diffs = []
        prev_time = sorted_data[self.timestamp_column].iloc[0]
        
        for i in range(1, len(sorted_data)):
            curr_time = sorted_data[self.timestamp_column].iloc[i]
            time_diff = curr_time - prev_time
            time_diffs.append(time_diff)
            prev_time = curr_time
        
        # 異常な時間差を検出
        max_time_gap_seconds = self.max_time_gap.total_seconds()
        gap_indices = [i + 1 for i, diff in enumerate(time_diffs) 
                      if diff.total_seconds() > max_time_gap_seconds]
        
        # 逆行（前の時刻より前の時刻）を検出
        reverse_indices = [i + 1 for i, diff in enumerate(time_diffs) 
                          if diff.total_seconds() < 0]
        
        is_valid = len(gap_indices) == 0 and len(reverse_indices) == 0
        
        # ギャップ詳細の作成
        gap_details = []
        for idx in gap_indices[:20]:  # 最初の20個まで
            gap_details.append({
                "index": idx,
                "original_index": sorted_data.index[idx],
                "prev_timestamp": sorted_data[self.timestamp_column].iloc[idx - 1],
                "curr_timestamp": sorted_data[self.timestamp_column].iloc[idx],
                "gap_seconds": time_diffs[idx - 1].total_seconds()
            })
        
        # 逆行詳細の作成
        reverse_details = []
        for idx in reverse_indices[:20]:  # 最初の20個まで
            reverse_details.append({
                "index": idx,
                "original_index": sorted_data.index[idx],
                "prev_timestamp": sorted_data[self.timestamp_column].iloc[idx - 1],
                "curr_timestamp": sorted_data[self.timestamp_column].iloc[idx],
                "diff_seconds": time_diffs[idx - 1].total_seconds()
            })
        
        details = {
            "gap_count": len(gap_indices),
            "gap_indices": gap_indices[:100],
            "gap_details": gap_details,
            "reverse_count": len(reverse_indices),
            "reverse_indices": reverse_indices[:100],
            "reverse_details": reverse_details,
            "max_time_gap": max_time_gap_seconds,
            "max_actual_gap": max([diff.total_seconds() for diff in time_diffs]) if time_diffs else 0,
            "min_actual_gap": min([diff.total_seconds() for diff in time_diffs]) if time_diffs else 0,
            "avg_actual_gap": sum([diff.total_seconds() for diff in time_diffs]) / len(time_diffs) if time_diffs else 0
        
        return is_valid, details


class DataValidator:
    """
    GPSデータ検証クラス
    
    Parameters
    ----------
    rules : Optional[List[ValidationRule]], optional
        検証ルールのリスト
    """
    
    def __init__(self, rules: Optional[List[ValidationRule]] = None):
        self.rules = rules or []
        self.validation_results = []
    
    def add_rule(self, rule: ValidationRule) -> None:
        """
        検証ルールを追加
        
        Parameters
        ----------
        rule : ValidationRule
            追加する検証ルール
        """
        self.rules.append(rule)
    
    def validate(self, container: GPSDataContainer) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        GPSデータコンテナを検証
        
        Parameters
        ----------
        container : GPSDataContainer
            検証するGPSデータコンテナ
            
        Returns
        -------
        Tuple[bool, List[Dict[str, Any]]]
            検証結果（True: すべて成功、False: 一部失敗）と詳細情報のリスト
        """
        if not self.rules:
            # デフォルトルールを追加
            self._add_default_rules()
        
        data = container.data
        self.validation_results = []
        
        for rule in self.rules:
            is_valid, details = rule.validate(data)
            
            result = {
                "rule_name": rule.name,
                "description": rule.description,
                "severity": rule.severity,
                "is_valid": is_valid,
                "details": details
            
            self.validation_results.append(result)
        
        # 少なくとも1つのエラー（severity='error'）があれば検証失敗
        has_error = any(
            not result["is_valid"] and result["severity"] == 'error' 
            for result in self.validation_results
        )
        
        return not has_error, self.validation_results
    
    def get_issues(self, include_warnings: bool = True, include_info: bool = False) -> List[Dict[str, Any]]:
        """
        検証で見つかった問題を取得
        
        Parameters
        ----------
        include_warnings : bool, optional
            警告を含めるかどうか
        include_info : bool, optional
            情報を含めるかどうか
            
        Returns
        -------
        List[Dict[str, Any]]
            問題のリスト
        """
        issues = []
        
        for result in self.validation_results:
            if not result["is_valid"]:
                severity = result["severity"]
                
                if severity == 'error' or \
                   (severity == 'warning' and include_warnings) or \
                   (severity == 'info' and include_info):
                    issues.append(result)
        
        return issues
    
    def fix_common_issues(self, container: GPSDataContainer) -> Tuple[GPSDataContainer, List[Dict[str, Any]]]:
        """
        一般的な問題を自動修正
        
        Parameters
        ----------
        container : GPSDataContainer
            修正するGPSデータコンテナ
            
        Returns
        -------
        Tuple[GPSDataContainer, List[Dict[str, Any]]]
            修正後のGPSデータコンテナと修正内容のリスト
        """
        # まず検証を実行
        self.validate(container)
        
        data = container.data.copy()
        fixes = []
        
        # 重複タイムスタンプの修正
        duplicate_results = [r for r in self.validation_results 
                            if "No Duplicate Timestamps" in r["rule_name"] and not r["is_valid"]]
        
        if duplicate_results:
            # 重複タイムスタンプを持つ行を少しずつずらす
            timestamp_col = 'timestamp'
            for result in duplicate_results:
                duplicate_timestamps = result["details"].get("duplicate_timestamps", [])
                for ts_str in duplicate_timestamps:
                    try:
                        ts = pd.to_datetime(ts_str)
                        duplicates = data[data[timestamp_col] == ts].index.tolist()
                        
                        if len(duplicates) <= 1:
                            continue
                        
                        # 最初の行は保持し、残りは1ミリ秒ずつずらす
                        for i, idx in enumerate(duplicates[1:], 1):
                            data.loc[idx, timestamp_col] = ts + pd.Timedelta(milliseconds=i)
                        
                        fixes.append({
                            "type": "duplicate_timestamp_fix",
                            "timestamp": ts_str,
                            "affected_indices": duplicates[1:],
                            "description": f"{len(duplicates) - 1}個の重複タイムスタンプを修正しました"
                        })
                    except Exception as e:
                        fixes.append({
                            "type": "error",
                            "timestamp": ts_str,
                            "description": f"重複タイムスタンプの修正に失敗しました: {e}"
                        })
        
        # 欠損値の修正
        null_results = [r for r in self.validation_results 
                       if "No Null Values Check" in r["rule_name"] and not r["is_valid"]]
        
        if null_results:
            for result in null_results:
                null_counts = result["details"].get("null_counts", {})
                
                for col, count in null_counts.items():
                    if count == 0:
                        continue
                    
                    # 位置情報（緯度・経度）の欠損値は線形補間
                    if col in ['latitude', 'longitude'] and count < len(data) * 0.2:  # 20%未満の場合のみ
                        data[col] = data[col].interpolate(method='linear')
                        
                        fixes.append({
                            "type": "null_value_fix",
                            "column": col,
                            "method": "linear_interpolation",
                            "count": count,
                            "description": f"カラム '{col}' の欠損値 {count}個を線形補間で修正しました"
                        })
                    
                    # その他の数値カラムの欠損値も線形補間
                    elif pd.api.types.is_numeric_dtype(data[col]) and count < len(data) * 0.2:
                        data[col] = data[col].interpolate(method='linear')
                        
                        fixes.append({
                            "type": "null_value_fix",
                            "column": col,
                            "method": "linear_interpolation",
                            "count": count,
                            "description": f"カラム '{col}' の欠損値 {count}個を線形補間で修正しました"
                        })
        
        # 空間的整合性の問題（異常な速度）を修正
        spatial_results = [r for r in self.validation_results 
                         if "Spatial Consistency Check" in r["rule_name"] and not r["is_valid"]]
        
        if spatial_results:
            for result in spatial_results:
                anomaly_indices = result["details"].get("anomaly_indices", [])
                
                if anomaly_indices:
                    # 異常値を含む行を削除
                    original_len = len(data)
                    data = data.drop(data.index[anomaly_indices])
                    
                    fixes.append({
                        "type": "spatial_anomaly_fix",
                        "method": "remove_anomalies",
                        "removed_count": len(anomaly_indices),
                        "description": f"空間的に整合性のない {len(anomaly_indices)}個のポイントを削除しました"
                    })
        
        # 時間的整合性の問題を修正
        temporal_results = [r for r in self.validation_results 
                          if "Temporal Consistency Check" in r["rule_name"] and not r["is_valid"]]
        
        if temporal_results:
            for result in temporal_results:
                reverse_indices = result["details"].get("reverse_indices", [])
                
                if reverse_indices:
                    # 時間的に逆行している行を削除
                    original_len = len(data)
                    data = data.drop(data.index[reverse_indices])
                    
                    fixes.append({
                        "type": "temporal_anomaly_fix",
                        "method": "remove_reverse_time",
                        "removed_count": len(reverse_indices),
                        "description": f"時間的に逆行している {len(reverse_indices)}個のポイントを削除しました"
                    })
        
        # ソートとインデックスのリセット
        data = data.sort_values('timestamp').reset_index(drop=True)
        
        # 修正したデータで新しいコンテナを作成
        new_container = GPSDataContainer(data, container.metadata.copy())
        
        # 修正情報をメタデータに追加
        if fixes:
            new_container.add_metadata("auto_fixes", fixes)
            new_container.add_metadata("fix_timestamp", datetime.now().isoformat())
        
        return new_container, fixes
    
    def _add_default_rules(self) -> None:
        """デフォルトの検証ルールを追加"""
        # 必須カラム検証
        self.add_rule(RequiredColumnsRule(['timestamp', 'latitude', 'longitude']))
        
        # 値範囲検証
        self.add_rule(ValueRangeRule('latitude', -90, 90))
        self.add_rule(ValueRangeRule('longitude', -180, 180))
        
        # 欠損値検証
        self.add_rule(NoNullValuesRule(['timestamp', 'latitude', 'longitude']))
        
        # タイムスタンプ重複チェック
        self.add_rule(DuplicateTimestampRule())
        
        # 空間的整合性チェック
        self.add_rule(SpatialConsistencyRule(max_speed_knots=100.0))
        
        # 時間的整合性チェック
        self.add_rule(TemporalConsistencyRule(max_time_gap=timedelta(minutes=5)))
