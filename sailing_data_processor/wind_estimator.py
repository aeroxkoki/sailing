# -*- coding: utf-8 -*-
"""
sailing_data_processor.wind_estimator モジュール（最適化版）

GPSデータから風向風速を推定する機能を提供するモジュール
パフォーマンス改善のために最適化されています
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Union, Any
import math
from functools import lru_cache
import warnings
import re
import gc

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
        
        # 計算用一時変数
        self._temp_bearings = None
        self._temp_speeds = None
        
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
        if data.empty or len(data) < 3:
            return pd.DataFrame()
        
        heading_col = 'heading' if 'heading' in data.columns else 'course'
        if heading_col not in data.columns:
            return pd.DataFrame()
        
        tacks = []
        for i in range(1, len(data)-1):
            heading_prev = data.iloc[i-1][heading_col]
            heading_current = data.iloc[i][heading_col]
            heading_next = data.iloc[i+1][heading_col]
            
            # ヘディングの変化を計算（180度をまたぐ場合の処理を含む）
            angle_change = self._calculate_angle_change(heading_prev, heading_next)
            
            # タック判定（角度が急激に変化）
            if abs(angle_change) > self.params["min_tack_angle_change"]:
                tacks.append({
                    'timestamp': data.iloc[i]['timestamp'] if 'timestamp' in data.columns else i,
                    'angle_change': abs(angle_change),
                    'heading_before': heading_prev,
                    'heading_after': heading_next,
                    'index': i
                })
        
        return pd.DataFrame(tacks)
    
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
        if data.empty or len(data) < 3:
            return pd.DataFrame()
        
        heading_col = 'heading' if 'heading' in data.columns else 'course'
        if heading_col not in data.columns:
            return pd.DataFrame()
        
        gybes = []
        for i in range(1, len(data)-1):
            heading_prev = data.iloc[i-1][heading_col]
            heading_current = data.iloc[i][heading_col]
            heading_next = data.iloc[i+1][heading_col]
            
            # ヘディングの変化を計算
            angle_change = self._calculate_angle_change(heading_prev, heading_next)
            
            # ジャイブ判定（右旋回）
            if angle_change > self.params["min_tack_angle_change"]:
                gybes.append({
                    'timestamp': data.iloc[i]['timestamp'] if 'timestamp' in data.columns else i,
                    'angle_change': abs(angle_change),
                    'heading_before': heading_prev,
                    'heading_after': heading_next,
                    'index': i
                })
        
        return pd.DataFrame(gybes)
    
    def detect_maneuvers(self, data: pd.DataFrame, wind_direction=None) -> List[Dict]:
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
        List[Dict]
            検出されたマニューバーのリスト
        """
        tacks = self.detect_tacks(data)
        gybes = self.detect_gybes(data)
        
        maneuvers = []
        
        # タックのデータを追加
        if not tacks.empty:
            for _, tack in tacks.iterrows():
                maneuver_data = {
                    'timestamp': tack['timestamp'],
                    'maneuver_type': 'tack',
                    'angle_change': tack['angle_change'],
                    'before_bearing': tack['heading_before'],
                    'after_bearing': tack['heading_after'],
                    'maneuver_confidence': 0.8,  # デフォルトの信頼度
                    'before_state': 'unknown',
                    'after_state': 'unknown'
                }
                
                # 風向が指定されている場合は状態を判定
                if wind_direction is not None:
                    maneuver_data['before_state'] = self._determine_point_state(
                        tack['heading_before'] - wind_direction)
                    maneuver_data['after_state'] = self._determine_point_state(
                        tack['heading_after'] - wind_direction)
                
                maneuvers.append(maneuver_data)
        
        # ジャイブのデータを追加
        if not gybes.empty:
            for _, gybe in gybes.iterrows():
                maneuver_data = {
                    'timestamp': gybe['timestamp'],
                    'maneuver_type': 'jibe',
                    'angle_change': gybe['angle_change'],
                    'before_bearing': gybe['heading_before'],
                    'after_bearing': gybe['heading_after'],
                    'maneuver_confidence': 0.8,  # デフォルトの信頼度
                    'before_state': 'unknown',
                    'after_state': 'unknown'
                }
                
                # 風向が指定されている場合は状態を判定
                if wind_direction is not None:
                    maneuver_data['before_state'] = self._determine_point_state(
                        gybe['heading_before'] - wind_direction)
                    maneuver_data['after_state'] = self._determine_point_state(
                        gybe['heading_after'] - wind_direction)
                
                maneuvers.append(maneuver_data)
        
        # タイムスタンプでソート
        maneuvers.sort(key=lambda x: x['timestamp'])
            
        return maneuvers
    
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
    
    def _calculate_vmg(self, boat_speed: float, boat_course: float, 
                      wind_direction: float) -> float:
        """
        VMG（Velocity Made Good）を計算する
        
        Parameters:
        -----------
        boat_speed : float
            艇速（ノット）
        boat_course : float
            艇の進行方向（度）
        wind_direction : float
            風向（度）
            
        Returns:
        --------
        float
            VMG（ノット）
        """
        # 風向に対する相対角度
        relative_angle = self._normalize_angle(boat_course - wind_direction)
        
        # VMG計算（風に対する速度成分）
        vmg = boat_speed * math.cos(math.radians(relative_angle))
        
        return vmg
    
    def _convert_angle_to_wind_vector(self, angle: float, speed: float = 1.0) -> Tuple[float, float]:
        """
        風向角度を風向ベクトルに変換する
        
        Parameters:
        -----------
        angle : float
            風向（度）
        speed : float, optional
            風速（ノット）
            
        Returns:
        --------
        Tuple[float, float]
            風向ベクトル（x, y成分）
        """
        # 北を0度として時計回りの角度から、数学的な角度（東が0度、反時計回り）に変換
        math_angle = 90 - angle
        
        x = speed * math.cos(math.radians(math_angle))
        y = speed * math.sin(math.radians(math_angle))
        
        return (x, y)
    
    def _convert_wind_vector_to_angle(self, vector: Tuple[float, float]) -> float:
        """
        風向ベクトルを風向角度に変換する
        
        Parameters:
        -----------
        vector : Tuple[float, float]
            風向ベクトル（x, y成分）
            
        Returns:
        --------
        float
            風向（度）
        """
        x, y = vector
        
        # ベクトルが原点の場合は0度を返す
        if abs(x) < 1e-10 and abs(y) < 1e-10:
            return 0.0
            
        # 数学的な角度（東が0度、反時計回り）を計算
        math_angle = math.degrees(math.atan2(y, x))
        
        # 北を0度として時計回りの角度に変換
        wind_angle = self._normalize_angle(90 - math_angle)
        
        # 風ベクトルは風が吹いてくる方向を表すため、180度回転させる
        wind_angle = self._normalize_angle(wind_angle + 180)
        
        return wind_angle
    
    def _get_conversion_functions(self, latitude: float) -> Tuple[callable, callable]:
        """
        指定された緯度における度とメートルの変換関数を返す
        
        Parameters:
        -----------
        latitude : float
            緯度
            
        Returns:
        --------
        Tuple[callable, callable]
            (緯度変換関数, 経度変換関数)のタプル
        """
        # 球体近似による1度あたりの距離（メートル）
        earth_radius = 6371000  # 地球の平均半径（メートル）
        
        # 緯度1度あたりのメートル距離（ほぼ一定）
        meters_per_lat = earth_radius * math.pi / 180
        
        # 経度1度あたりのメートル距離（緯度によって変化）
        meters_per_lon = meters_per_lat * math.cos(math.radians(latitude))
        
        # 緯度変換関数
        def lat_to_meters(lat_diff):
            return lat_diff * meters_per_lat
        
        # 経度変換関数
        def lon_to_meters(lon_diff):
            return lon_diff * meters_per_lon
        
        return lat_to_meters, lon_to_meters
    
    def _normalize_angle(self, angle: float) -> float:
        """
        角度を0-360度の範囲に正規化する
        
        Parameters:
        -----------
        angle : float
            角度（度）
            
        Returns:
        --------
        float
            正規化された角度（0-360度）
        """
        # まず360で割った余りを計算
        normalized = angle % 360
        
        # 負の値の場合は360を足す
        if normalized < 0:
            normalized += 360
            
        return normalized
    
    def _calculate_angle_change(self, angle1: float, angle2: float) -> float:
        """
        2つの角度の変化を計算する（-180〜180度）
        
        Parameters:
        -----------
        angle1, angle2 : float
            角度（度）
            
        Returns:
        --------
        float
            角度変化（度）
        """
        diff = angle2 - angle1
        
        # -180〜180度の範囲に正規化
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
            
        return diff
    
    def _calculate_bearing(self, point1: Tuple[float, float], 
                          point2: Tuple[float, float]) -> float:
        """
        2点間のベアリングを計算する
        
        Parameters:
        -----------
        point1, point2 : Tuple[float, float]
            位置（緯度、経度）
            
        Returns:
        --------
        float
            ベアリング（度）
        """
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # ラジアンに変換
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # ベアリング計算
        dlon = lon2 - lon1
        x = math.sin(dlon) * math.cos(lat2)
        y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.degrees(math.atan2(x, y))
        
        # 0-360度の範囲に正規化
        return self._normalize_angle(bearing)
    
    def _calculate_distance(self, point1: Tuple[float, float], 
                           point2: Tuple[float, float]) -> float:
        """
        2点間の距離を計算する（海里）
        
        Parameters:
        -----------
        point1, point2 : Tuple[float, float]
            位置（緯度、経度）
            
        Returns:
        --------
        float
            距離（海里）
        """
        lat1, lon1 = point1
        lat2, lon2 = point2
        
        # ラジアンに変換
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球の半径（海里）
        r = 3440.065
        
        return c * r
    
    def _calculate_endpoint(self, start_point: Tuple[float, float], 
                           bearing: float, distance: float) -> Tuple[float, float]:
        """
        始点からある方向と距離にある終点を計算する
        
        Parameters:
        -----------
        start_point : Tuple[float, float]
            始点（緯度、経度）
        bearing : float
            方位（度）
        distance : float
            距離（海里）
            
        Returns:
        --------
        Tuple[float, float]
            終点（緯度、経度）
        """
        lat1, lon1 = start_point
        
        # ラジアンに変換
        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        bearing = math.radians(bearing)
        
        # 地球の半径（海里）
        r = 3440.065
        
        # 角距離
        angular_distance = distance / r
        
        # 終点の計算
        lat2 = math.asin(math.sin(lat1) * math.cos(angular_distance) +
                        math.cos(lat1) * math.sin(angular_distance) * math.cos(bearing))
        
        lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(angular_distance) * math.cos(lat1),
                                math.cos(angular_distance) - math.sin(lat1) * math.sin(lat2))
        
        # 度に変換
        lat2 = math.degrees(lat2)
        lon2 = math.degrees(lon2)
        
        return (lat2, lon2)
    
    def _create_wind_result(self, direction: float, speed: float, 
                           confidence: float, method: str, 
                           timestamp: Optional[datetime]) -> Dict[str, Any]:
        """
        風向風速推定結果を作成する
        
        Parameters:
        -----------
        direction : float
            風向（度）
        speed : float  
            風速（ノット）
        confidence : float
            信頼度（0-1）
        method : str
            推定方法
        timestamp : Optional[datetime]
            タイムスタンプ
            
        Returns:
        --------
        Dict[str, Any]
            風向風速推定結果
        """
        return {
            "direction": direction,
            "speed": speed,
            "confidence": confidence,
            "method": method,
            "timestamp": timestamp
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
            return {
                "direction": 0.0,
                "speed": 0.0,
                "confidence": 0.0
            }
        
        # 風推定を実行
        wind_df = self.estimate_wind_from_single_boat(data)
        
        # 風向推定結果を取得
        if not wind_df.empty:
            # 信頼度の高い結果を優先
            best_estimate = wind_df.loc[wind_df['confidence'].idxmax()]
            
            return {
                "direction": best_estimate['wind_direction'],
                "speed": best_estimate['wind_speed'],
                "confidence": best_estimate['confidence']
            }
        else:
            # 推定できない場合はデフォルト値
            return {
                "direction": 0.0,
                "speed": 0.0,
                "confidence": 0.0
            }
    
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
        
        # 一時変数の初期化
        self._temp_bearings = None
        self._temp_speeds = None
        
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
            wind_from_course = self.estimate_wind_from_course_speed(df)
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
    
    def estimate_wind_from_course_speed(self, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        コースと速度の変化から風向風速を推定する
        
        Parameters:
        -----------
        data : pd.DataFrame
            GPSデータ
            
        Returns:
        --------
        Optional[Dict[str, Any]]
            推定結果
        """
        if data.empty or len(data) < 10:
            return None
        
        # 簡単な実装：平均的な方向から推定
        heading_col = 'heading' if 'heading' in data.columns else 'course'
        if heading_col not in data.columns:
            return None
        
        # 平均的な向きから風向を推定（簡略化）
        mean_heading = data[heading_col].mean()
        wind_direction = self._normalize_angle(mean_heading + 180)
        
        # 速度から風速を推定（簡略化）
        speed_col = 'sog' if 'sog' in data.columns else 'speed'
        if speed_col in data.columns:
            mean_speed = data[speed_col].mean()
            wind_speed = mean_speed * 0.7  # 簡単な推定
        else:
            wind_speed = 10.0  # デフォルト値
        
        return self._create_wind_result(
            direction=wind_direction,
            speed=wind_speed,
            confidence=0.5,
            method='course_speed',
            timestamp=data.iloc[-1]['timestamp'] if 'timestamp' in data.columns else None
        )
    
    def _estimate_wind_from_maneuvers(self, maneuvers, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        マニューバーから風向風速を推定する
        
        Parameters:
        -----------
        maneuvers : List[Dict] or pd.DataFrame
            検出されたマニューバー
        data : pd.DataFrame
            GPSデータ
            
        Returns:
        --------
        Optional[Dict[str, Any]]
            推定結果
        """
        # マニューバーが空かどうかを確認
        if isinstance(maneuvers, pd.DataFrame):
            if maneuvers.empty or len(maneuvers) < 2:
                return None
            # タックを抽出
            tacks = maneuvers[maneuvers['maneuver_type'] == 'tack']
            if tacks.empty:
                return None
            
            # タックの前後の方向から風向を推定
            wind_directions = []
            for _, tack in tacks.iterrows():
                before = tack['before_bearing']
                after = tack['after_bearing']
                
                # タックの前後の方向の平均が風向に対して約90度
                avg_heading = (before + after) / 2
                wind_dir = self._normalize_angle(avg_heading + 90)
                wind_directions.append(wind_dir)
        else:
            # リスト形式のマニューバー
            if not maneuvers or len(maneuvers) < 2:
                return None
            
            # タックを抽出
            tacks = [m for m in maneuvers if m.get('maneuver_type') == 'tack']
            if not tacks:
                return None
            
            # タックの前後の方向から風向を推定
            wind_directions = []
            for tack in tacks:
                before = tack['before_bearing']
                after = tack['after_bearing']
                
                # タックの前後の方向の平均が風向に対して約90度
                avg_heading = (before + after) / 2
                wind_dir = self._normalize_angle(avg_heading + 90)
                wind_directions.append(wind_dir)
        
        # 風向がない場合は終了
        if not wind_directions:
            return None
        
        # 平均風向
        mean_wind_direction = np.mean(wind_directions)
        
        # 風速は速度から推定（簡略化）
        speed_col = 'sog' if 'sog' in data.columns else 'speed'
        if speed_col in data.columns:
            wind_speed = data[speed_col].mean() * 0.8
        else:
            wind_speed = 12.0  # デフォルト値
        
        return self._create_wind_result(
            direction=mean_wind_direction,
            speed=wind_speed,
            confidence=0.7,
            method='maneuvers',
            timestamp=data.iloc[-1]['timestamp'] if 'timestamp' in data.columns else None
        )
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        データの前処理を行う
        
        Parameters:
        -----------
        data : pd.DataFrame
            生のGPSデータ
            
        Returns:
        --------
        pd.DataFrame
            前処理されたデータ
        """
        df = data.copy()
        
        # タイムスタンプの確認
        if 'timestamp' not in df.columns:
            df['timestamp'] = pd.to_datetime(df.index)
        
        # 速度の確認
        if 'sog' not in df.columns and 'speed' not in df.columns:
            # 位置から速度を計算する必要がある場合
            pass
        
        # ヘディングの確認
        if 'heading' not in df.columns and 'course' not in df.columns:
            # コースから計算する必要がある場合
            pass
        
        return df
    
    def _categorize_maneuver(self, before_bearing: float, after_bearing: float, 
                          wind_direction: float, boat_type: str = None) -> Dict[str, Any]:
        """
        マニューバーの種類を分類する
        
        Parameters:
        -----------
        before_bearing : float
            マニューバー前の方向（度）
        after_bearing : float
            マニューバー後の方向（度）
        wind_direction : float
            風向（度）
        boat_type : str, optional
            艇種
            
        Returns:
        --------
        Dict[str, Any]
            マニューバーの分類結果
        """
        # 風に対する相対角度
        rel_before = self._normalize_angle(before_bearing - wind_direction)
        rel_after = self._normalize_angle(after_bearing - wind_direction)
        
        # 角度変化
        angle_change = self._calculate_angle_change(before_bearing, after_bearing)
        abs_change = abs(angle_change)
        
        # 風に対する状態
        before_state = self._determine_point_state(rel_before, self.params["upwind_threshold"], 
                                                 self.params["downwind_threshold"])
        after_state = self._determine_point_state(rel_after, self.params["upwind_threshold"], 
                                                self.params["downwind_threshold"])
        
        # マニューバー分類
        maneuver_type = "unknown"
        confidence = 0.5
        
        # タック／ジャイブの判定
        if abs_change > 60:
            if before_state == 'upwind' and after_state == 'upwind':
                maneuver_type = "tack"
                confidence = 0.9
            elif before_state == 'downwind' and after_state == 'downwind':
                maneuver_type = "jibe"
                confidence = 0.9
            else:
                # 大きな角度変化があるが、状態変化が不明確な場合
                if abs_change > 120:
                    maneuver_type = "jibe"
                    confidence = 0.7
                else:
                    maneuver_type = "tack"
                    confidence = 0.7
        else:
            # より小さな角度変化の場合
            if before_state != after_state:
                if after_state == 'downwind':
                    maneuver_type = "bear_away"
                    confidence = 0.8
                else:
                    maneuver_type = "head_up"
                    confidence = 0.8
            else:
                # コース修正
                maneuver_type = "course_correction"
                confidence = 0.6
        
        return {
            "maneuver_type": maneuver_type,
            "confidence": confidence,
            "angle_change": abs_change,
            "before_state": before_state,
            "after_state": after_state
        }
    
    def _determine_point_state(self, relative_angle: float, 
                             upwind_range: float = None, 
                             downwind_range: float = None) -> str:
        """
        風に対する艇の状態を判定する
        
        Parameters:
        -----------
        relative_angle : float
            風に対する相対角度（度）
        upwind_range : float, optional
            風上判定の閾値
        downwind_range : float, optional
            風下判定の閾値
            
        Returns:
        --------
        str
            状態（'upwind', 'downwind', 'reaching'）
        """
        # デフォルト値の設定
        if upwind_range is None:
            upwind_range = self.params["upwind_threshold"]
        if downwind_range is None:
            downwind_range = self.params["downwind_threshold"]
        
        # 0-360度の範囲に正規化
        rel_angle = self._normalize_angle(relative_angle)
        
        # 絶対値で計算（0または180度からの距離）
        abs_angle = rel_angle
        if abs_angle > 180:
            abs_angle = 360 - abs_angle
        
        # 風上状態（0度付近）
        if abs_angle < upwind_range:
            return 'upwind'
        
        # 風下状態（180度付近）
        if abs_angle > 180 - downwind_range/2:
            return 'downwind'
        
        # それ以外はリーチング
        return 'reaching'
