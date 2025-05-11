# -*- coding: utf-8 -*-
# 最適化されたwind_estimator.pyファイルに置き換え

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
            
            # タック判定（左旋回）
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
    
    def calculate_laylines(self, wind_direction: Union[float, str], wind_speed: Union[float, str], 
                         mark_position: Tuple[float, float], 
                         boat_position: Tuple[float, float], 
                         **kwargs) -> Dict[str, Tuple[float, float]]:
        """
        レイラインを計算する
        
        Parameters:
        -----------
        wind_direction : Union[float, str]
            風向（度）
        wind_speed : Union[float, str]
            風速（ノット）
        mark_position : Tuple[float, float]
            マークの位置（緯度、経度）
        boat_position : Tuple[float, float]
            艇の位置（緯度、経度）
        **kwargs : dict
            追加パラメータ
            
        Returns:
        --------
        Dict[str, Tuple[float, float]]
            レイラインのポートタックとスターボードタックの終点
        """
        # 型変換
        if isinstance(wind_direction, str):
            wind_direction = float(wind_direction)
        if isinstance(wind_speed, str):
            wind_speed = float(wind_speed)
        
        # 風上角度を使用
        upwind_angle = self.params["default_upwind_angle"]
        
        # マークへのベアリング
        bearing_to_mark = self._calculate_bearing(boat_position, mark_position)
        
        # レイラインの方向を計算
        port_layline_bearing = wind_direction + upwind_angle
        starboard_layline_bearing = wind_direction - upwind_angle
        
        # レイラインの長さを計算（適当な長さを設定）
        layline_length = self._calculate_distance(boat_position, mark_position) * 2
        
        # レイラインの終点を計算
        port_end = self._calculate_endpoint(boat_position, port_layline_bearing, layline_length)
        starboard_end = self._calculate_endpoint(boat_position, starboard_layline_bearing, layline_length)
        
        return {
            'port': port_end,
            'starboard': starboard_end
        }

            }
        
        result = {
            'boat': boat_data,
            'wind': {
                'wind_data': wind_data
            }
        }
        
        return result
    
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
        return (bearing + 360) % 360
        return bearing

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
        開始点から指定の方向と距離にある終点を計算する
        
        Parameters:
        -----------
        start_point : Tuple[float, float]
            開始点（緯度、経度）
        bearing : float
            方向（度）
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
        if len(maneuvers) >= 2:
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
        
        # VMG解析に基づく風向推定
        wind_from_vmg = None
        try:
            wind_from_vmg = self._estimate_wind_from_vmg_analysis(df)
        except Exception as e:
            warnings.warn(f"VMG解析からの風向推定エラー: {str(e)}")
        
        # 統合推定（ベイズを使用する場合）
        if use_bayesian and wind_from_maneuvers and wind_from_course and wind_from_vmg:
            final_estimate = self._bayesian_wind_estimate([
                wind_from_maneuvers,
                wind_from_course,
                wind_from_vmg
            ])
        else:
            # 最も信頼度の高い推定を使用
            candidates = [est for est in [wind_from_maneuvers, wind_from_course, wind_from_vmg] if est is not None]
            if not candidates:
                final_estimate = {
                    "direction": 0.0,
                    "speed": 0.0,
                    "confidence": 0.0,
                    "method": "none",
                    "timestamp": df['timestamp'].iloc[-1] if not df.empty else None
                }
            else:
                final_estimate = max(candidates, key=lambda x: x["confidence"])
        
        # 結果をデータフレームに変換
        result_df = self._create_wind_time_series(df, final_estimate)
        
        # 結果を記録
        self.estimated_wind = final_estimate
        
        # 一時変数のクリア
        self._temp_bearings = None
        self._temp_speeds = None
        
        gc.collect()
        
        return result_df
    
    def detect_maneuvers(self, df: pd.DataFrame) -> List[Dict]:
        """
        マニューバー（タック/ジャイブ）を検出する
        
        Parameters:
        -----------
        df : pd.DataFrame
            GPSデータフレーム
            
        Returns:
        --------
        List[Dict]
            検出されたマニューバーのリスト
        """
        if df.empty or len(df) < 3:
            return []
        
        heading_col = 'heading' if 'heading' in df.columns else 'course'
        if heading_col not in df.columns:
            return []
        
        maneuvers = []
        for i in range(1, len(df)-1):
            heading_prev = df.iloc[i-1][heading_col]
            heading_current = df.iloc[i][heading_col]
            heading_next = df.iloc[i+1][heading_col]
            
            # ヘディングの変化を計算
            angle_change = self._calculate_angle_change(heading_prev, heading_next)
            
            # タック判定（左旋回）
            if abs(angle_change) > self.params["min_tack_angle_change"]:
                maneuvers.append({
                    'timestamp': df.iloc[i]['timestamp'] if 'timestamp' in df.columns else i,
                    'type': 'tack',
                    'angle_change': abs(angle_change),
                    'heading_before': heading_prev,
                    'heading_after': heading_next,
                    'index': i
                })
            
            # ジャイブ判定（右旋回）
            elif angle_change > self.params["min_tack_angle_change"]:
                maneuvers.append({
                    'timestamp': df.iloc[i]['timestamp'] if 'timestamp' in df.columns else i,
                    'type': 'gybe',
                    'angle_change': abs(angle_change),
                    'heading_before': heading_prev,
                    'heading_after': heading_next,
                    'index': i
                })
        
        return maneuvers
    
    def _estimate_wind_from_maneuvers(self, maneuvers: List[Dict], df: pd.DataFrame) -> Dict[str, Any]:
        """
        マニューバーから風向を推定する
        """
        if not maneuvers:
            return self._create_wind_result(0.0, 0.0, 0.0, "maneuvers", None)
        
        # 単純化された実装
        total_angle = 0
        total_count = 0
        
        for maneuver in maneuvers:
            before = maneuver.get('heading_before', 0)
            after = maneuver.get('heading_after', 0)
            
            # タックの場合、風向はヘディングの平均の反対
            if maneuver.get('type') == 'tack':
                wind_dir = ((before + after) / 2 + 180) % 360
                total_angle += wind_dir
                total_count += 1
        
        if total_count > 0:
            avg_wind_dir = total_angle / total_count
            return self._create_wind_result(avg_wind_dir, 10.0, 0.7, "maneuvers", 
                                          df['timestamp'].iloc[-1] if not df.empty else None)
        
        return self._create_wind_result(0.0, 0.0, 0.0, "maneuvers", None)
    
    def estimate_wind_from_course_speed(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        コースと速度のデータから風向を推定（単純化した実装）
        """
        if df.empty or len(df) < 5:
            return self._create_wind_result(0.0, 0.0, 0.0, "course_speed", None)
        
        # 必要なカラムがあるか確認
        heading_col = 'heading' if 'heading' in df.columns else 'course'
        speed_col = 'sog' if 'sog' in df.columns else 'speed'
        
        if heading_col not in df.columns or speed_col not in df.columns:
            return self._create_wind_result(0.0, 0.0, 0.0, "course_speed", None)
        
        # 簡単な推定：平均ヘディングとその反対を風向とする
        avg_heading = df[heading_col].mean()
        wind_dir = (avg_heading + 180) % 360
        
        # 速度の変動から風速を推定
        speed_std = df[speed_col].std()
        wind_speed = speed_std * 5  # 適当な係数
        
        return self._create_wind_result(wind_dir, wind_speed, 0.5, "course_speed", 
                                      df['timestamp'].iloc[-1] if not df.empty else None)
    
    def _estimate_wind_from_vmg_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        VMG解析から風向を推定する（単純化した実装）
        """
        if df.empty or len(df) < 5:
            return self._create_wind_result(0.0, 0.0, 0.0, "vmg_analysis", None)
        
        # 必要なカラムがあるか確認
        heading_col = 'heading' if 'heading' in df.columns else 'course'
        speed_col = 'sog' if 'sog' in df.columns else 'speed'
        
        if heading_col not in df.columns or speed_col not in df.columns:
            return self._create_wind_result(0.0, 0.0, 0.0, "vmg_analysis", None)
        
        # 最高速度を出している時のヘディングを基に推定
        max_speed_idx = df[speed_col].idxmax()
        max_speed_heading = df.loc[max_speed_idx, heading_col]
        
        # 風下帆走と仮定して、そのヘディングの反対を風向とする
        wind_dir = (max_speed_heading + 180) % 360
        wind_speed = 12.0  # 適当な値
        
        return self._create_wind_result(wind_dir, wind_speed, 0.6, "vmg_analysis", 
                                      df['timestamp'].iloc[-1] if not df.empty else None)
    
    def _bayesian_wind_estimate(self, estimates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        ベイズ推定による風向風速の統合（単純化した実装）
        """
        if not estimates:
            return self._create_wind_result(0.0, 0.0, 0.0, "bayesian", None)
        
        # 信頼度で重み付けした平均
        total_weight = 0
        weighted_direction = 0
        weighted_speed = 0
        
        for est in estimates:
            weight = est.get('confidence', 0)
            direction = est.get('direction', 0)
            speed = est.get('speed', 0)
            
            total_weight += weight
            weighted_direction += direction * weight
            weighted_speed += speed * weight
        
        if total_weight > 0:
            avg_direction = weighted_direction / total_weight
            avg_speed = weighted_speed / total_weight
            avg_confidence = min(0.9, total_weight / len(estimates))
            
            return self._create_wind_result(avg_direction, avg_speed, avg_confidence, 
                                          "bayesian", estimates[0].get('timestamp'))
        
        return self._create_wind_result(0.0, 0.0, 0.0, "bayesian", None)
    
    def _create_wind_time_series(self, df: pd.DataFrame, estimate: Dict[str, Any]) -> pd.DataFrame:
        """
        風向風速の時系列データを作成する
        """
        if df.empty:
            return pd.DataFrame(columns=[
                'timestamp', 'wind_direction', 'wind_speed', 'confidence', 'method'
            ])
        
        # 全タイムスタンプに対して同じ推定値を設定
        result_df = pd.DataFrame({
            'timestamp': df['timestamp'],
            'wind_direction': estimate['direction'],
            'wind_speed': estimate['speed'],
            'confidence': estimate['confidence'],
            'method': estimate['method']
        })
        
        return result_df
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        風向風速推定のためのデータ前処理
        """
        # タイムスタンプのソート
        if not df.empty and 'timestamp' in df.columns:
            df = df.sort_values('timestamp').reset_index(drop=True)
        
        # 速度カラムがない場合、座標から計算
        if 'speed' not in df.columns and 'sog' in df.columns:
            df['speed'] = df['sog']
        elif 'speed' not in df.columns:
            # 簡単な速度計算を実装
            df['speed'] = 0.0
        
        # コースカラムがない場合、座標から計算
        if 'course' not in df.columns and 'heading' in df.columns:
            df['course'] = df['heading']
        elif 'course' not in df.columns:
            # 簡単な方位計算を実装
            df['course'] = 0.0
        
        return df

    def _categorize_maneuver(self, angle_change: float) -> str:
        """
        マニューバーの種類を分類する
        
        Parameters:
        -----------
        angle_change : float
            角度変化（度）
            
        Returns:
        --------
        str
            マニューバーの種類（'tack' または 'gybe'）
        """
        # 簡単な実装：角度変化の方向で判定
        if angle_change > 0:
            return 'gybe'
        else:
            return 'tack'
    
    def _determine_point_state(self, heading: float, wind_direction: float) -> str:
        """
        ポイントの状態を判定する
        
        Parameters:
        -----------
        heading : float
            艇の向き（度）
        wind_direction : float
            風向（度）
            
        Returns:
        --------
        str
            状態（'upwind', 'downwind', 'reaching'）
        """
        # 風に対する相対角度を計算
        relative_angle = abs(self._normalize_angle(heading - wind_direction))
        if relative_angle > 180:
            relative_angle = 360 - relative_angle
        
        # 状態を判定
        if relative_angle < self.params["upwind_threshold"]:
            return 'upwind'
        elif relative_angle > self.params["downwind_threshold"]:
            return 'downwind'
        else:
            return 'reaching'
