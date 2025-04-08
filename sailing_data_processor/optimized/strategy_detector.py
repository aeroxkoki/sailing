"""
sailing_data_processor.optimized.strategy_detector

StrategyDetectorの最適化バージョン - データモデルの最適化とベクトル化演算を活用
"""

import numpy as np
import pandas as pd
import math
import warnings
from typing import Dict, List, Tuple, Optional, Union, Any, Callable
from datetime import datetime, timedelta
from scipy.spatial import cKDTree

# 内部モジュールのインポート
from ..strategy.detector import StrategyDetector as OriginalStrategyDetector
from ..strategy.points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint
from ..data_model import (
    DataContainer, GPSDataContainer, WindDataContainer, StrategyPointContainer,
    cached, memoize
)

class OptimizedStrategyDetector(OriginalStrategyDetector):
    """
    戦略的判断ポイントの検出アルゴリズムを最適化したクラス
    
    オリジナルの機能を継承しつつ、パフォーマンスとデータアクセスパターンを改善。
    """
    
    def __init__(self, vmg_calculator=None, wind_field_interpolator=None):
        """
        初期化
        
        Parameters:
        -----------
        vmg_calculator
            VMG計算モジュール
        wind_field_interpolator
            風の場補間モジュール
        """
        super().__init__(vmg_calculator, wind_field_interpolator)
        
        # 検出設定はオリジナルから継承
    
    def _extract_wind_at_points_vectorized(self, lats: np.ndarray, lons: np.ndarray, 
                                         wind_field: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        複数地点の風データを風の場からベクトル化抽出
        
        Parameters:
        -----------
        lats : np.ndarray
            緯度の配列
        lons : np.ndarray
            経度の配列
        wind_field : Dict[str, Any]
            風の場データ
            
        Returns:
        --------
        Dict[str, np.ndarray]
            風向・風速・信頼度・変動性の配列を格納した辞書
        """
        try:
            # グリッドデータを取得
            lat_grid = wind_field["lat_grid"]
            lon_grid = wind_field["lon_grid"]
            wind_directions = wind_field["wind_direction"]
            wind_speeds = wind_field["wind_speed"]
            confidence = wind_field.get("confidence", np.ones_like(wind_directions) * 0.8)
            
            # 最寄りの格子点を効率的に探索するためにKDツリーを使用
            points = np.column_stack([lat_grid.flatten(), lon_grid.flatten()])
            tree = cKDTree(points)
            
            # クエリポイント
            query_points = np.column_stack([lats, lons])
            
            # 最近傍点を検索
            distances, indices = tree.query(query_points, k=1)
            
            # 風の場データの形状を取得
            grid_shape = wind_directions.shape
            
            # 1次元インデックスを2次元に変換
            idx_2d = np.unravel_index(indices, grid_shape)
            
            # 該当する風データを抽出
            extracted_directions = wind_directions[idx_2d]
            extracted_speeds = wind_speeds[idx_2d]
            extracted_confidence = confidence[idx_2d]
            
            # 風の変動性を計算
            variability = np.zeros_like(extracted_directions)
            
            # 各地点の変動性を計算
            for i, (row, col) in enumerate(zip(*idx_2d)):
                variability[i] = self._calculate_wind_variability_fast((row, col), wind_directions, wind_speeds)
            
            return {
                "direction": extracted_directions,
                "speed": extracted_speeds,
                "confidence": extracted_confidence,
                "variability": variability
            }
            
        except Exception as e:
            warnings.warn(f"風データベクトル抽出エラー: {e}")
            return {
                "direction": np.zeros_like(lats),
                "speed": np.zeros_like(lats),
                "confidence": np.zeros_like(lats),
                "variability": np.zeros_like(lats)
            }
    
    def _calculate_wind_variability_fast(self, center_idx: Tuple[int, int], 
                                      wind_directions: np.ndarray, 
                                      wind_speeds: np.ndarray) -> float:
        """
        特定地点周辺の風の変動性を高速計算
        
        Parameters:
        -----------
        center_idx : Tuple[int, int]
            中心点のインデックス
        wind_directions : np.ndarray
            風向の配列
        wind_speeds : np.ndarray
            風速の配列
            
        Returns:
        --------
        float
            変動性（0-1）
        """
        # グリッドサイズを取得
        grid_shape = wind_directions.shape
        i, j = center_idx
        
        # 近傍9点の範囲を定義
        i_min = max(0, i-1)
        i_max = min(grid_shape[0], i+2)
        j_min = max(0, j-1)
        j_max = min(grid_shape[1], j+2)
        
        # 近傍の風向風速を直接切り出す
        nearby_dirs = wind_directions[i_min:i_max, j_min:j_max].flatten()
        nearby_speeds = wind_speeds[i_min:i_max, j_min:j_max].flatten()
        
        # 風向の変動性（角度データなので特殊処理）
        dir_sin = np.sin(np.radians(nearby_dirs))
        dir_cos = np.cos(np.radians(nearby_dirs))
        
        # 平均ベクトルの長さを算出
        mean_sin = np.mean(dir_sin)
        mean_cos = np.mean(dir_cos)
        r = np.sqrt(mean_sin**2 + mean_cos**2)
        
        # r = 1 は完全に一定、r = 0 は完全にランダム
        dir_variability = 1.0 - r
        
        # 風速の変動性（変動係数 = 標準偏差/平均）
        speed_std = np.std(nearby_speeds)
        speed_mean = np.mean(nearby_speeds)
        
        if speed_mean > 0:
            speed_variability = speed_std / speed_mean
        else:
            speed_variability = 0.0
        
        # 総合変動性（風向の変動が主要因）
        variability = 0.7 * dir_variability + 0.3 * min(1.0, speed_variability)
        
        return min(1.0, max(0.0, variability))
    
    def detect_wind_shifts_optimized(self, course_data: pd.DataFrame, wind_field: Dict[str, Any], 
                               target_time: Union[datetime, None] = None) -> List[StrategyPointContainer]:
        """
        風向シフトポイントを検出する最適化バージョン
        
        Parameters:
        -----------
        course_data : pd.DataFrame
            コースデータ
        wind_field : Dict[str, Any]
            風の場データ
        target_time : datetime, optional
            目標時刻
            
        Returns:
        --------
        List[StrategyPointContainer]
            検出された風向シフトポイントのリスト
        """
        # 必要なデータがない場合
        if course_data.empty or not wind_field:
            return []
        
        # 必要なカラムがあるか確認
        required_columns = ['timestamp', 'latitude', 'longitude']
        if not all(col in course_data.columns for col in required_columns):
            warnings.warn("風向シフト検出に必要なカラムがありません")
            return []
        
        # NumPy配列に変換
        timestamps = course_data['timestamp'].values
        latitudes = course_data['latitude'].values
        longitudes = course_data['longitude'].values
        
        # 時間間隔（秒）
        interval = self.config["wind_forecast_interval"]
        
        # 予測期間（秒）
        max_horizon = self.config["max_wind_forecast_horizon"]
        
        # 最小風向シフト角度
        min_shift_angle = self.config["min_wind_shift_angle"]
        
        # 風向シフト検出結果
        shift_points = []
        
        # 目標時刻がない場合は最新時刻を使用
        if target_time is None and len(timestamps) > 0:
            target_time = timestamps[-1]
        
        # 風向風速を現在の地点から一括取得
        current_wind_data = self._extract_wind_at_points_vectorized(latitudes, longitudes, wind_field)
        
        # 各位置について風向シフトを予測
        for i in range(len(latitudes)):
            try:
                # 現在の風向風速
                current_direction = current_wind_data["direction"][i]
                current_speed = current_wind_data["speed"][i]
                current_confidence = current_wind_data["confidence"][i]
                current_variability = current_wind_data["variability"][i]
                
                # データ信頼性がない場合はスキップ
                if current_speed < 1.0 or current_confidence < 0.3:
                    continue
                
                # 変動性が高すぎる場合は信頼性が低いのでスキップ
                if current_variability > 0.5:
                    continue
                
                # 現在の位置
                lat = latitudes[i]
                lon = longitudes[i]
                
                # 予測時刻ポイント
                forecast_times = [
                    target_time + timedelta(seconds=t) 
                    for t in range(interval, max_horizon + 1, interval)
                ]
                
                # 各予測時刻の風向風速を取得
                forecasted_directions = []
                forecasted_speeds = []
                forecasted_confidences = []
                
                for t in forecast_times:
                    # 予測時刻の風向風速を取得
                    forecasted_wind = self._get_wind_at_position(lat, lon, t, wind_field)
                    
                    if forecasted_wind:
                        forecasted_directions.append(forecasted_wind["direction"])
                        forecasted_speeds.append(forecasted_wind["speed"])
                        forecasted_confidences.append(forecasted_wind.get("confidence", 0.5))
                    else:
                        forecasted_directions.append(current_direction)
                        forecasted_speeds.append(current_speed)
                        forecasted_confidences.append(0.3)  # 信頼度低め
                
                # 予測風向と現在風向の差を計算
                direction_diffs = np.array([
                    self._angle_difference(f_dir, current_direction) 
                    for f_dir in forecasted_directions
                ])
                
                # 最大の風向シフトを見つける
                abs_diffs = np.abs(direction_diffs)
                
                if np.any(abs_diffs >= min_shift_angle):
                    # 最大シフトのインデックス
                    max_shift_idx = np.argmax(abs_diffs)
                    max_shift_angle = direction_diffs[max_shift_idx]
                    max_shift_time = forecast_times[max_shift_idx]
                    max_shift_confidence = forecasted_confidences[max_shift_idx]
                    
                    # 風向シフトの方向（時計回り/反時計回り）
                    shift_type = "clockwise" if max_shift_angle > 0 else "counterclockwise"
                    
                    # シフト後の推定風向風速
                    new_direction = (current_direction + max_shift_angle) % 360
                    new_speed = forecasted_speeds[max_shift_idx]
                    
                    # シフトの重要度計算（シフト量と信頼度に基づく）
                    importance = min(1.0, (abs(max_shift_angle) / 90.0) * max_shift_confidence)
                    
                    # 詳細情報
                    details = {
                        "shift_angle": max_shift_angle,
                        "shift_type": shift_type,
                        "current_direction": current_direction,
                        "current_speed": current_speed,
                        "new_direction": new_direction,
                        "new_speed": new_speed,
                        "forecast_time": max_shift_time.isoformat(),
                        "confidence": max_shift_confidence
                    }
                    
                    # StrategyPointContainerの作成
                    shift_point = StrategyPointContainer.from_coordinates(
                        "wind_shift", lat, lon, timestamps[i],
                        importance=importance,
                        details=details
                    )
                    
                    shift_points.append(shift_point)
            
            except Exception as e:
                warnings.warn(f"風向シフト予測エラー（地点 {i}）: {e}")
                continue
        
        return shift_points
    
    def detect_wind_shifts(self, course_data: pd.DataFrame, wind_field: Dict[str, Any],
                        target_time: Union[datetime, None] = None) -> List[StrategyPointContainer]:
        """
        元のメソッドをオーバーライドして最適化バージョンを呼び出す
        
        Parameters:
        -----------
        course_data : pd.DataFrame
            コースデータ
        wind_field : Dict[str, Any]
            風の場データ
        target_time : datetime, optional
            目標時刻
            
        Returns:
        --------
        List[StrategyPointContainer]
            検出された風向シフトポイントのリスト
        """
        return self.detect_wind_shifts_optimized(course_data, wind_field, target_time)
    
    @cached('layline_calculations')
    def calculate_laylines(self, mark_lat: float, mark_lon: float, wind_direction: float,
                          upwind_angle: float = 42.0, safety_margin: float = 10.0) -> Dict[str, Any]:
        """
        マーク周りのレイラインを計算（キャッシュ機能付き）
        
        Parameters:
        -----------
        mark_lat : float
            マークの緯度
        mark_lon : float
            マークの経度
        wind_direction : float
            風向（度、0-360）
        upwind_angle : float, optional
            風上角度（度）、デフォルトは42度
        safety_margin : float, optional
            安全マージン（度）、デフォルトは10度
            
        Returns:
        --------
        Dict[str, Any]
            レイライン情報
        """
        # 風向から左右のレイライン方位を計算
        starboard_layline = (wind_direction - upwind_angle) % 360
        port_layline = (wind_direction + upwind_angle) % 360
        
        # 安全マージンを適用
        starboard_layline_safe = (starboard_layline - safety_margin) % 360
        port_layline_safe = (port_layline + safety_margin) % 360
        
        return {
            "mark_position": {"latitude": mark_lat, "longitude": mark_lon},
            "wind_direction": wind_direction,
            "upwind_angle": upwind_angle,
            "safety_margin": safety_margin,
            "starboard_layline": starboard_layline,
            "port_layline": port_layline,
            "starboard_layline_safe": starboard_layline_safe,
            "port_layline_safe": port_layline_safe
        }

    def detect_laylines_optimized(self, course_data: pd.DataFrame, wind_field: Dict[str, Any]) -> List[StrategyPointContainer]:
        """
        レイラインポイントを検出する最適化バージョン
        
        Parameters:
        -----------
        course_data : pd.DataFrame
            コースデータ
        wind_field : Dict[str, Any]
            風の場データ
            
        Returns:
        --------
        List[StrategyPointContainer]
            検出されたレイラインポイントのリスト
        """
        # VMGCalculatorが設定されていない場合
        if self.vmg_calculator is None:
            warnings.warn("VMGCalculatorが設定されていないため、レイラインポイントの検出ができません")
            return []
        
        # 必要なデータがない場合
        if course_data.empty or not wind_field:
            return []
        
        # 必要なカラムがあるか確認
        required_columns = ['timestamp', 'latitude', 'longitude']
        if not all(col in course_data.columns for col in required_columns):
            warnings.warn("レイライン検出に必要なカラムがありません")
            return []
        
        # マーク情報が必要
        if not hasattr(self.vmg_calculator, 'get_marks') or not callable(self.vmg_calculator.get_marks):
            warnings.warn("VMGCalculatorにマーク情報取得メソッドがありません")
            return []
        
        # マーク情報を取得
        marks = self.vmg_calculator.get_marks()
        if not marks:
            warnings.warn("マーク情報がありません")
            return []
        
        # NumPy配列に変換
        timestamps = course_data['timestamp'].values
        latitudes = course_data['latitude'].values
        longitudes = course_data['longitude'].values
        
        # 安全マージン
        safety_margin = self.config["layline_safety_margin"]
        
        # 最小マーク距離
        min_mark_distance = self.config["min_mark_distance"]
        
        # レイライン検出結果
        layline_points = []
        
        # 風向風速を現在の地点から一括取得
        current_wind_data = self._extract_wind_at_points_vectorized(latitudes, longitudes, wind_field)
        
        # 各マークについて処理
        for mark in marks:
            mark_lat = mark.get('latitude')
            mark_lon = mark.get('longitude')
            mark_name = mark.get('name', 'Unknown Mark')
            
            if mark_lat is None or mark_lon is None:
                continue
            
            # 各位置について処理
            for i in range(len(latitudes)):
                try:
                    # 現在の風向風速
                    current_direction = current_wind_data["direction"][i]
                    current_speed = current_wind_data["speed"][i]
                    current_confidence = current_wind_data["confidence"][i]
                    
                    # データ信頼性がない場合はスキップ
                    if current_speed < 1.0 or current_confidence < 0.3:
                        continue
                    
                    # 現在の位置
                    lat = latitudes[i]
                    lon = longitudes[i]
                    timestamp = timestamps[i]
                    
                    # マークまでの距離を計算
                    # シンプルなhaversine距離計算
                    # TODO: Math_utilsからインポートする場合はこの実装は不要
                    def haversine_distance(lat1, lon1, lat2, lon2):
                        R = 6371000  # 地球の半径 (m)
                        phi1 = np.radians(lat1)
                        phi2 = np.radians(lat2)
                        delta_phi = np.radians(lat2 - lat1)
                        delta_lambda = np.radians(lon2 - lon1)
                        
                        a = (np.sin(delta_phi/2) ** 2 + 
                             np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda/2) ** 2)
                        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
                        
                        return R * c
                    
                    mark_distance = haversine_distance(lat, lon, mark_lat, mark_lon)
                    
                    # 距離が近すぎる場合はスキップ
                    if mark_distance < min_mark_distance:
                        continue
                    
                    # 最適VMG角度を取得
                    if hasattr(self.vmg_calculator, 'get_optimal_vmg_angles') and callable(self.vmg_calculator.get_optimal_vmg_angles):
                        vmg_data = self.vmg_calculator.get_optimal_vmg_angles(current_speed)
                        upwind_angle = vmg_data.get('upwind_angle', 42.0)
                    else:
                        # デフォルト値
                        upwind_angle = 42.0
                    
                    # レイラインを計算
                    laylines = self.calculate_laylines(
                        mark_lat, mark_lon, current_direction, upwind_angle, safety_margin
                    )
                    
                    # マークに対する現在の方位を計算
                    # 北を0度とし、時計回りの角度（0-360度）
                    def calculate_bearing(lat1, lon1, lat2, lon2):
                        phi1 = np.radians(lat1)
                        phi2 = np.radians(lat2)
                        delta_lambda = np.radians(lon2 - lon1)
                        
                        y = np.sin(delta_lambda) * np.cos(phi2)
                        x = np.cos(phi1) * np.sin(phi2) - np.sin(phi1) * np.cos(phi2) * np.cos(delta_lambda)
                        
                        bearing = np.degrees(np.arctan2(y, x))
                        return (bearing + 360) % 360
                    
                    bearing_to_mark = calculate_bearing(lat, lon, mark_lat, mark_lon)
                    
                    # 風上マークかどうかの判定
                    bearing_to_wind = current_direction
                    wind_mark_angle = abs(self._angle_difference(bearing_to_mark, bearing_to_wind))
                    is_upwind_mark = wind_mark_angle <= 90
                    
                    # レイラインとの角度差
                    if is_upwind_mark:
                        starboard_diff = abs(self._angle_difference(bearing_to_mark, laylines["starboard_layline_safe"]))
                        port_diff = abs(self._angle_difference(bearing_to_mark, laylines["port_layline_safe"]))
                    else:
                        # 風下マークの場合はレイラインを反転
                        downwind_starboard = (laylines["starboard_layline"] + 180) % 360
                        downwind_port = (laylines["port_layline"] + 180) % 360
                        starboard_diff = abs(self._angle_difference(bearing_to_mark, downwind_starboard))
                        port_diff = abs(self._angle_difference(bearing_to_mark, downwind_port))
                    
                    # レイラインに近いかどうか判定
                    layline_threshold = 5.0  # 5度以内
                    
                    if starboard_diff <= layline_threshold or port_diff <= layline_threshold:
                        # レイラインの種類
                        layline_type = "starboard" if starboard_diff <= port_diff else "port"
                        
                        # 重要度計算（角度差と距離に基づく）
                        angle_factor = 1.0 - min(1.0, (starboard_diff if layline_type == "starboard" else port_diff) / layline_threshold)
                        distance_factor = min(1.0, mark_distance / 1000.0)  # 1000m以上なら最大
                        
                        importance = 0.7 * angle_factor + 0.3 * distance_factor
                        
                        # 詳細情報
                        details = {
                            "mark_name": mark_name,
                            "mark_position": {"latitude": mark_lat, "longitude": mark_lon},
                            "mark_distance": mark_distance,
                            "bearing_to_mark": bearing_to_mark,
                            "layline_type": layline_type,
                            "wind_direction": current_direction,
                            "is_upwind_mark": is_upwind_mark,
                            "laylines": laylines
                        }
                        
                        # StrategyPointContainerの作成
                        layline_point = StrategyPointContainer.from_coordinates(
                            "layline", lat, lon, timestamp,
                            importance=importance,
                            details=details
                        )
                        
                        layline_points.append(layline_point)
                
                except Exception as e:
                    warnings.warn(f"レイライン検出エラー（地点 {i}）: {e}")
                    continue
        
        return layline_points
    
    def detect_laylines(self, course_data: pd.DataFrame, wind_field: Dict[str, Any]) -> List[StrategyPointContainer]:
        """
        元のメソッドをオーバーライドして最適化バージョンを呼び出す
        
        Parameters:
        -----------
        course_data : pd.DataFrame
            コースデータ
        wind_field : Dict[str, Any]
            風の場データ
            
        Returns:
        --------
        List[StrategyPointContainer]
            検出されたレイラインポイントのリスト
        """
        return self.detect_laylines_optimized(course_data, wind_field)
    
    def detect_strategy_points(self, gps_data: Union[pd.DataFrame, GPSDataContainer], 
                             wind_field: Dict[str, Any]) -> List[StrategyPointContainer]:
        """
        すべての戦略ポイントを検出する統合メソッド
        
        Parameters:
        -----------
        gps_data : Union[pd.DataFrame, GPSDataContainer]
            GPS位置データ
        wind_field : Dict[str, Any]
            風の場データ
            
        Returns:
        --------
        List[StrategyPointContainer]
            検出されたすべての戦略ポイントのリスト
        """
        # GPSDataContainerからDataFrameを取得
        if isinstance(gps_data, GPSDataContainer):
            df = gps_data.data
        else:
            df = gps_data
        
        # 各タイプの戦略ポイントを検出
        wind_shifts = self.detect_wind_shifts(df, wind_field)
        laylines = self.detect_laylines(df, wind_field)
        
        # VMGCaluculatorが設定されている場合は最適タックも検出
        optimal_tacks = []
        if self.vmg_calculator is not None:
            if hasattr(self, 'detect_optimal_tacks') and callable(self.detect_optimal_tacks):
                try:
                    optimal_tacks = self.detect_optimal_tacks(df, wind_field)
                except Exception as e:
                    warnings.warn(f"最適タック検出エラー: {e}")
        
        # すべての戦略ポイントを結合
        all_points = wind_shifts + laylines + optimal_tacks
        
        # 時間順にソート
        sorted_points = sorted(all_points, key=lambda x: x.timestamp)
        
        return sorted_points
