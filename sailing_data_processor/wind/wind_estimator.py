# -*- coding: utf-8 -*-
"""
sailing_data_processor.wind.wind_estimator モジュール

GPSデータから風向風速を推定する機能を提供するWindEstimatorクラス。
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import warnings

# 内部モジュールのインポート
from sailing_data_processor.wind.wind_estimator_utils import (
    normalize_angle, calculate_angle_change, calculate_bearing, 
    calculate_distance, calculate_endpoint, convert_angle_to_wind_vector,
    convert_wind_vector_to_angle, create_wind_result, get_conversion_functions
)
from sailing_data_processor.wind.wind_estimator_maneuvers import (
    determine_point_state, detect_tacks, detect_gybes, detect_maneuvers,
    categorize_maneuver
)
from sailing_data_processor.wind.wind_estimator_calculation import (
    calculate_vmg, estimate_wind_from_maneuvers, 
    estimate_wind_from_course_speed, preprocess_data
)

class WindEstimator:
    """
    風向風速推定クラス
    
    GPSデータから艇の動きを分析し、風向風速を推定するためのクラス。
    特に以下の機能を提供します：
    - タック/ジャイブなどのマニューバーの特定
    - 風速・風向の推定
    - 風上・風下方位の判定
    """
    
    def __init__(self, boat_type: str = "default"):
        """
        初期化
        
        Parameters:
        -----------
        boat_type : str, optional
            艇種（デフォルト: "default"）
        """
        # コード情報
        self.version = "2.1.0"  # 最適化バージョン
        self.name = "WindEstimator"
        
        # 艇種設定
        self.boat_type = boat_type
        
        # 風向風速推定のデフォルトパラメータ
        self.params = {
            # 風上判定の最大角度（度）
            "upwind_threshold": 45.0,
            # 風下判定の最小角度（度）
            "downwind_threshold": 120.0,
            # タック/ジャイブ検出の最小方位変化（度）
            "min_tack_angle_change": 60.0,
            # タック/ジャイブ検出の最小時間間隔（秒）
            "min_maneuver_duration": 3.0,
            # タック/ジャイブ検出の最大時間間隔（秒）
            "max_maneuver_duration": 20.0,
            # マニューバー検出の移動ウィンドウサイズ
            "maneuver_window_size": 5,
            # 風向推定の平滑化ウィンドウサイズ
            "wind_smoothing_window": 5,
            # 速度変化に基づくタック検出の閾値（%）
            "tack_speed_drop_threshold": 30.0,
            # 風向風速推定における最小速度閾値（ノット）
            "min_speed_threshold": 2.0,
            # 風上帆走時の艇速に対する見かけ風向の補正係数
            "upwind_correction_factor": 0.8,
            # 風下帆走時の艇速に対する見かけ風向の補正係数
            "downwind_correction_factor": 1.2,
            # 風向推定のための最適VMGでの風向に対する舵角の標準値（度）
            "default_upwind_angle": 42.0,
            "default_downwind_angle": 150.0,
            # キャッシュサイズ
            "cache_size": 128
        }
        
        # 艇種に応じたパラメータ調整
        self._adjust_params_by_boat_type(boat_type)
        
        # 風向風速の推定結果
        self.estimated_wind = {
            "direction": 0.0,   # 度（0-360、真北基準）
            "speed": 0.0,       # ノット
            "confidence": 0.0,  # 信頼度（0-1）
            "method": "none",   # 推定方法
            "timestamp": None   # タイムスタンプ
        }
        
        # マニューバー検出結果
        self.detected_maneuvers = []
        
    def _adjust_params_by_boat_type(self, boat_type: str) -> None:
        """
        艇種に応じたパラメータ調整
        
        Parameters:
        -----------
        boat_type : str
            艇種
        """
        # 艇種ごとのカスタム設定
        if boat_type.lower() == "laser":
            self.params["default_upwind_angle"] = 45.0
            self.params["default_downwind_angle"] = 140.0
            self.params["tack_speed_drop_threshold"] = 40.0
        elif boat_type.lower() == "470":
            self.params["default_upwind_angle"] = 42.0
            self.params["default_downwind_angle"] = 145.0
            self.params["tack_speed_drop_threshold"] = 35.0
        elif boat_type.lower() == "49er":
            self.params["default_upwind_angle"] = 38.0
            self.params["default_downwind_angle"] = 155.0
            self.params["tack_speed_drop_threshold"] = 30.0
    
    # 以下、ユーティリティ関数群を内部メソッドとして委譲
    
    def _normalize_angle(self, angle: float) -> float:
        return normalize_angle(angle)
    
    def _calculate_angle_change(self, angle1: float, angle2: float) -> float:
        return calculate_angle_change(angle1, angle2)
    
    def _calculate_bearing(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        return calculate_bearing(point1, point2)
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        return calculate_distance(point1, point2)
    
    def _calculate_endpoint(self, start_point: Tuple[float, float], bearing: float, distance: float) -> Tuple[float, float]:
        return calculate_endpoint(start_point, bearing, distance)
    
    def _convert_angle_to_wind_vector(self, angle: float, speed: float = 1.0) -> Tuple[float, float]:
        return convert_angle_to_wind_vector(angle, speed)
    
    def _convert_wind_vector_to_angle(self, vector: Tuple[float, float]) -> float:
        return convert_wind_vector_to_angle(vector)
    
    def _get_conversion_functions(self, latitude: float) -> Tuple[callable, callable]:
        return get_conversion_functions(latitude)
    
    def _create_wind_result(self, direction: float, speed: float, confidence: float, method: str, timestamp: Optional[datetime]) -> Dict[str, Any]:
        return create_wind_result(direction, speed, confidence, method, timestamp)
    
    def _calculate_vmg(self, boat_speed: float, boat_course: float, wind_direction: float) -> float:
        return calculate_vmg(boat_speed, boat_course, wind_direction)
    
    def _determine_point_state(self, relative_angle: float, upwind_range: float = None, downwind_range: float = None) -> str:
        if upwind_range is None:
            upwind_range = self.params["upwind_threshold"]
        if downwind_range is None:
            downwind_range = self.params["downwind_threshold"]
        return determine_point_state(relative_angle, upwind_range, downwind_range)
    
    def _categorize_maneuver(self, before_bearing: float, after_bearing: float, wind_direction: float, boat_type: str = None) -> Dict[str, Any]:
        return categorize_maneuver(
            before_bearing, after_bearing, wind_direction,
            self.params["upwind_threshold"], self.params["downwind_threshold"]
        )
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        return preprocess_data(data)
    
    def _estimate_wind_from_maneuvers(self, maneuvers: pd.DataFrame, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        return estimate_wind_from_maneuvers(maneuvers, data)
    
    def _estimate_wind_from_course_speed(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        return estimate_wind_from_course_speed(data)
    
    # 以下、パブリックAPI
    
    def detect_tacks(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        タックを検出する
        
        Parameters:
        -----------
        data : pd.DataFrame
            GPSデータ（heading/course列を含む）
            
        Returns:
        --------
        pd.DataFrame
            検出されたタックのデータフレーム
        """
        return detect_tacks(data, self.params["min_tack_angle_change"])
    
    def detect_gybes(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        ジャイブを検出する
        
        Parameters:
        -----------
        data : pd.DataFrame
            GPSデータ（heading/course列を含む）
            
        Returns:
        --------
        pd.DataFrame
            検出されたジャイブのデータフレーム
        """
        return detect_gybes(data, self.params["min_tack_angle_change"])
    
    def detect_maneuvers(self, data: pd.DataFrame, wind_direction=None) -> pd.DataFrame:
        """
        マニューバー（タック/ジャイブ）を検出する
        
        Parameters:
        -----------
        data : pd.DataFrame
            GPSデータ
        wind_direction : float, optional
            風向（度）。指定された場合、マニューバーの種類を風向に基づいて判定
            
        Returns:
        --------
        pd.DataFrame
            検出されたマニューバーのデータフレーム
        """
        return detect_maneuvers(data, wind_direction, self.params["min_tack_angle_change"])
    
    def calculate_laylines(self, wind_direction: Union[float, str], wind_speed: Union[float, str], 
                         mark_position: Dict[str, float], 
                         boat_position: Dict[str, float], 
                         **kwargs) -> Dict[str, Any]:
        """
        レイラインを計算する
        
        Parameters:
        -----------
        wind_direction : Union[float, str]
            風向（度）
        wind_speed : Union[float, str]
            風速（ノット）
        mark_position : Dict[str, float]
            マークの位置（'latitude', 'longitude'のキーを持つ辞書）
        boat_position : Dict[str, float]
            艇の位置（'latitude', 'longitude'のキーを持つ辞書）
        **kwargs : dict
            追加パラメータ
            
        Returns:
        --------
        Dict[str, Any]
            レイラインの情報を含む辞書
        """
        # 型変換（文字列から数値へ）
        if isinstance(wind_direction, str):
            wind_direction = float(wind_direction)
        if isinstance(wind_speed, str):
            wind_speed = float(wind_speed)
        
        # ポジションデータをタプルに変換
        mark_pos = (float(mark_position['latitude']), float(mark_position['longitude']))
        boat_pos = (float(boat_position['latitude']), float(boat_position['longitude']))
        
        # 風上角度を使用
        upwind_angle = self.params["default_upwind_angle"]
        
        # マークへのベアリング
        bearing_to_mark = self._calculate_bearing(boat_pos, mark_pos)
        
        # レイラインの方向を計算
        port_layline_bearing = self._normalize_angle(wind_direction + upwind_angle)
        starboard_layline_bearing = self._normalize_angle(wind_direction - upwind_angle)
        
        # レイラインの長さを計算（適当な長さを設定）
        layline_length = self._calculate_distance(boat_pos, mark_pos) * 2
        
        # レイラインの終点を計算
        port_end = self._calculate_endpoint(boat_pos, port_layline_bearing, layline_length)
        starboard_end = self._calculate_endpoint(boat_pos, starboard_layline_bearing, layline_length)
        
        # タックが必要かどうかを判定
        direct_bearing_diff = abs(self._calculate_angle_change(bearing_to_mark, wind_direction))
        tacking_required = direct_bearing_diff < upwind_angle
        
        return {
            'port': port_end,
            'starboard': starboard_end,
            'direct_bearing': bearing_to_mark,
            'tacking_required': tacking_required
        }
    
    def estimate_wind(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        GPS データから風向風速を推定する
        
        Parameters:
        -----------
        data : pd.DataFrame
            GPS データ
            
        Returns:
        --------
        Dict[str, Any]
            風向風速の推定結果
        """
        if data.empty:
            # 空のデータの場合、テスト用の構造を返す
            return {
                "boat": {"boat_id": "none"},
                "wind": {
                    "direction": 0.0,
                    "speed": 0.0,
                    "confidence": 0.0,
                    "wind_data": []
                }
            }
        
        # 風推定を実行
        wind_estimation = self.estimate_wind_from_single_boat(data)
        
        # 結果の構築
        result = {
            "boat": {"boat_id": data.get("boat_id", ["unknown"])[0] if isinstance(data.get("boat_id"), list) else "unknown"},
            "wind": {
                "direction": 0.0,
                "speed": 0.0,
                "confidence": 0.0,
                "wind_data": []
            }
        }
        
        # 風向推定結果をセット
        if isinstance(wind_estimation, pd.DataFrame) and not wind_estimation.empty:
            # 信頼度の高い結果を優先
            best_index = wind_estimation['confidence'].idxmax() if 'confidence' in wind_estimation.columns else 0
            best_estimate = wind_estimation.iloc[best_index]
            
            result["wind"] = {
                "direction": best_estimate.get('wind_direction', 0.0),
                "speed": best_estimate.get('wind_speed', 0.0),
                "confidence": best_estimate.get('confidence', 0.0),
                "wind_data": wind_estimation.to_dict('records')
            }
            
        return result
    
    def estimate_wind_from_single_boat(self, gps_data: pd.DataFrame, min_tack_angle: float = 30.0,
                                     boat_type: str = None, use_bayesian: bool = True) -> pd.DataFrame:
        """
        単一艇のGPSデータから風向風速を推定
        
        Parameters:
        -----------
        gps_data : pd.DataFrame
            GPSデータフレーム
        min_tack_angle : float, optional
            タック検出の最小角度（度）
        boat_type : str, optional
            艇種
        use_bayesian : bool, optional
            ベイズ推定を使用するか
            
        Returns:
        --------
        pd.DataFrame
            推定された風向風速のデータフレーム
        """
        # データ確認
        if gps_data.empty or len(gps_data) < 10:
            warnings.warn("データポイントが不足しています")
            return pd.DataFrame(columns=[
                'timestamp', 'wind_direction', 'wind_speed', 'confidence', 'method'
            ])
        
        # 必要なカラムのチェック
        required_columns = ['timestamp', 'latitude', 'longitude']
        if not all(col in gps_data.columns for col in required_columns):
            missing_cols = [col for col in required_columns if col not in gps_data.columns]
            warnings.warn(f"必要なカラムがありません: {missing_cols}")
            return pd.DataFrame(columns=[
                'timestamp', 'wind_direction', 'wind_speed', 'confidence', 'method'
            ])
        
        # 艇種の設定（指定があれば更新）
        if boat_type and boat_type != self.boat_type:
            self.boat_type = boat_type
            self._adjust_params_by_boat_type(boat_type)
        
        # データのコピーを作成
        df = gps_data.copy()
        
        # データの前処理
        df = self._preprocess_data(df)
        
        # マニューバー（タック/ジャイブ）の検出
        tack_params = {'min_tack_angle': min_tack_angle}
        maneuvers = self.detect_maneuvers(df)
        
        # マニューバーに基づく風向推定
        wind_from_maneuvers = None
        if not maneuvers.empty and len(maneuvers) >= 2:
            try:
                wind_from_maneuvers = self._estimate_wind_from_maneuvers(maneuvers, df)
            except Exception as e:
                warnings.warn(f"マニューバーからの風向推定エラー: {str(e)}")
        
        # コース/速度の変化に基づく風向推定
        wind_from_course = None
        try:
            wind_from_course = self._estimate_wind_from_course_speed(df)
        except Exception as e:
            warnings.warn(f"コース/速度からの風向推定エラー: {str(e)}")
        
        # 推定結果の統合
        results = []
        
        if wind_from_maneuvers:
            results.append({
                'timestamp': wind_from_maneuvers['timestamp'],
                'wind_direction': wind_from_maneuvers['direction'],
                'wind_speed': wind_from_maneuvers['speed'],
                'confidence': wind_from_maneuvers['confidence'],
                'method': wind_from_maneuvers['method']
            })
        
        if wind_from_course:
            results.append({
                'timestamp': wind_from_course['timestamp'],
                'wind_direction': wind_from_course['direction'],
                'wind_speed': wind_from_course['speed'],
                'confidence': wind_from_course['confidence'],
                'method': wind_from_course['method']
            })
        
        if not results:
            # デフォルト値を返す
            results.append({
                'timestamp': df.iloc[-1]['timestamp'] if 'timestamp' in df.columns else None,
                'wind_direction': 0.0,
                'wind_speed': 10.0,
                'confidence': 0.1,
                'method': 'default'
            })
        
        return pd.DataFrame(results)
