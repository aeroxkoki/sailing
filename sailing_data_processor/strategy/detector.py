# -*- coding: utf-8 -*-
import numpy as np
import math
import warnings
from typing import Dict, List, Tuple, Optional, Union, Any
from datetime import datetime, timedelta
from functools import lru_cache

# 内部モジュールのインポート
from .points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint

class StrategyDetector:
    """戦略的判断ポイントの検出アルゴリズムを実装するクラス"""
    
    def __init__(self, vmg_calculator=None, wind_field_interpolator=None):
        """初期化"""
        self.vmg_calculator = vmg_calculator
        self.wind_field_interpolator = wind_field_interpolator
        
        # 検出設定
        self.config = {
            # 風向シフト検出設定
            "min_wind_shift_angle": 5.0,        # 最小風向シフト角度（度）
            "wind_forecast_interval": 300,      # 風予測間隔（秒）
            "max_wind_forecast_horizon": 1800,  # 最大風予測期間（秒）
            
            # タック検出設定
            "tack_search_radius": 500,          # タック探索半径（メートル）
            "min_vmg_improvement": 0.05,        # 最小VMG改善閾値（比率）
            "max_tacks_per_leg": 3,             # レグあたり最大タック数
            
            # レイライン検出設定
            "layline_safety_margin": 10.0,      # レイライン安全マージン（度）
            "min_mark_distance": 100,           # マークからの最小検出距離（メートル）
        }
    
    def _get_wind_at_position(self, lat: float, lon: float, time_point: Union[datetime, float, dict, None], 
                            wind_field: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """指定位置・時間の風情報を取得"""
        # dictの場合は"timestamp"キーから時間を取得
        if isinstance(time_point, dict) and "timestamp" in time_point:
            time_point = time_point["timestamp"]
            
        # WindFieldInterpolatorがあれば利用
        if self.wind_field_interpolator and time_point is not None and not isinstance(time_point, dict):
            try:
                # 時間補間を利用した風の場データ取得
                interpolated_field = self.wind_field_interpolator.interpolate_wind_field(
                    target_time=time_point,
                    resolution=None,  # デフォルト解像度
                    method="gp"       # ガウス過程補間
                )
                
                if interpolated_field:
                    return self._extract_wind_at_point(lat, lon, interpolated_field)
            except Exception as e:
                warnings.warn(f"風の場補間エラー: {e}")
        
        # 補間器がないか、失敗した場合は直接風の場から抽出
        return self._extract_wind_at_point(lat, lon, wind_field)

    def _extract_wind_at_point(self, lat: float, lon: float, wind_field: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """風の場データから特定地点の風情報を抽出"""
        try:
            # グリッドデータを取得
            lat_grid = wind_field["lat_grid"]
            lon_grid = wind_field["lon_grid"]
            wind_directions = wind_field["wind_direction"]
            wind_speeds = wind_field["wind_speed"]
            confidence = wind_field.get("confidence", np.ones_like(wind_directions) * 0.8)
            
            # グリッド範囲外の場合
            if (lat < np.min(lat_grid) or lat > np.max(lat_grid) or
                lon < np.min(lon_grid) or lon > np.max(lon_grid)):
                return None
            
            # NumPyベクトル化による最近傍点検索
            distances = (lat_grid - lat)**2 + (lon_grid - lon)**2
            closest_idx = np.unravel_index(np.argmin(distances), distances.shape)
            
            # そのポイントの風データを取得
            direction = float(wind_directions[closest_idx])
            speed = float(wind_speeds[closest_idx])
            conf = float(confidence[closest_idx])
            
            # 風の変動性を計算（近傍9点での標準偏差）
            variability = self._calculate_wind_variability(closest_idx, wind_directions, wind_speeds)
            
            return {
                "direction": direction,
                "speed": speed,
                "confidence": conf,
                "variability": variability
            }
            
        except Exception as e:
            warnings.warn(f"風データ抽出エラー: {e}")
            return None

    def _calculate_wind_variability(self, center_idx: Tuple[int, int], 
                                  wind_directions: np.ndarray, 
                                  wind_speeds: np.ndarray) -> float:
        """特定地点周辺の風の変動性を計算"""
        # グリッドサイズを取得
        grid_shape = wind_directions.shape
        i, j = center_idx
        
        # 近傍9点の範囲を定義
        i_range = range(max(0, i-1), min(grid_shape[0], i+2))
        j_range = range(max(0, j-1), min(grid_shape[1], j+2))
        
        # 近傍の風向風速を収集
        nearby_dirs = []
        nearby_speeds = []
        
        for ni in i_range:
            for nj in j_range:
                nearby_dirs.append(wind_directions[ni, nj])
                nearby_speeds.append(wind_speeds[ni, nj])
        
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
    
    # 必要最小限の機能としてダミーメソッドを定義
    def detect_wind_shifts(self, course_data, wind_field, target_time=None):
        return []
    
    def detect_optimal_tacks(self, course_data, wind_field):
        warnings.warn("VMGCalculatorが設定されていないため、最適タックポイントの検出ができません")
        return []
    
    def detect_laylines(self, course_data, wind_field):
        warnings.warn("VMGCalculatorが設定されていないため、レイラインポイントの検出ができません")
        return []

    def _angle_difference(self, angle1, angle2):
        """2つの角度間の最小差分を計算（-180〜180度の範囲）"""
        return ((angle1 - angle2 + 180) % 360) - 180

