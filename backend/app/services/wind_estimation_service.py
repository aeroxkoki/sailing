# -*- coding: utf-8 -*-
"""
風向風速推定サービス

セーリングのGPSデータから風向風速を推定するサービス機能
"""

import io
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.wind_data import WindDataPoint, WindEstimationResult
from app.schemas.wind_estimation import WindEstimationInput
from sailing_data_processor.wind_estimator import WindEstimator

def estimate_wind(
    gps_data: bytes,
    params: WindEstimationInput,
    user_id: UUID,
    db: Session
) -> Dict[str, Any]:
    """
    GPSデータから風向風速を推定
    
    Parameters:
    -----------
    gps_data : bytes
        GPSデータの内容
    params : WindEstimationInput
        風向推定パラメータ
    user_id : UUID
        ユーザーID
    db : Session
        データベースセッション
        
    Returns:
    --------
    Dict[str, Any]
        風向風速結果
    """
    try:
        # GPSデータをDataFrameに変換
        df = _convert_bytes_to_dataframe(gps_data, params.file_format)
        
        if df is None or df.empty:
            return {"error": "有効なGPSデータが見つかりません"}
        
        # WindEstimatorを初期化
        estimator = WindEstimator(boat_type=params.boat_type)
        
        # 風向風速を推定
        wind_df = estimator.estimate_wind_from_single_boat(
            gps_data=df,
            min_tack_angle=params.min_tack_angle,
            boat_type=params.boat_type,
            use_bayesian=params.use_bayesian
        )
        
        if wind_df is None or wind_df.empty:
            return {"error": "風向推定ができませんでした"}
        
        # 結果をAPIレスポンス形式に変換
        result = _create_wind_estimation_result(wind_df, str(user_id))
        
        # TODO: 結果をデータベースに保存する処理
        
        return result
    
    except Exception as e:
        return {"error": f"風向推定エラー: {str(e)}"}

def _convert_bytes_to_dataframe(data: bytes, file_format: str) -> Optional[pd.DataFrame]:
    """
    バイトデータをPandas DataFrameに変換
    
    Parameters:
    -----------
    data : bytes
        バイトデータ
    file_format : str
        ファイル形式（'csv', 'gpx'）
        
    Returns:
    --------
    pd.DataFrame or None
        変換されたDataFrame
    """
    try:
        if file_format.lower() == 'csv':
            return pd.read_csv(io.BytesIO(data))
        elif file_format.lower() == 'gpx':
            # GPXファイルの解析
            import gpxpy
            import gpxpy.gpx
            
            gpx = gpxpy.parse(io.BytesIO(data))
            
            # ポイントを抽出
            points = []
            for track in gpx.tracks:
                for segment in track.segments:
                    for point in segment.points:
                        points.append({
                            'timestamp': point.time,
                            'latitude': point.latitude,
                            'longitude': point.longitude,
                            'elevation': point.elevation,
                            'speed': getattr(point, 'speed', None),
                            'course': getattr(point, 'course', None),
                        })
            
            return pd.DataFrame(points)
        elif file_format.lower() == 'fit':
            # TODO: FITファイル解析機能を実装
            # 未実装
            return None
        else:
            return None
    except Exception as e:
        print(f"変換エラー: {str(e)}")
        return None

def _create_wind_estimation_result(wind_df: pd.DataFrame, session_id: str) -> Dict[str, Any]:
    """
    風向推定結果をAPIレスポンス形式に変換
    
    Parameters:
    -----------
    wind_df : pd.DataFrame
        風向推定結果
    session_id : str
        セッションID
        
    Returns:
    --------
    Dict[str, Any]
        APIレスポンス形式の風向推定結果
    """
    # DataFrameから風データポイントを抽出
    wind_data_points = []
    
    for _, row in wind_df.iterrows():
        # 緯度経度が欠損している場合は0.0を使用
        lat = row.get('latitude', 0.0)
        lon = row.get('longitude', 0.0)
        
        point = {
            "timestamp": row['timestamp'],
            "latitude": lat,
            "longitude": lon,
            "speed": row['wind_speed'],
            "direction": row['wind_direction'],
            "confidence": row.get('confidence', 1.0)
        }
        wind_data_points.append(point)
    
    # 平均値の計算
    avg_speed = wind_df['wind_speed'].mean()
    avg_direction = _calculate_average_direction(wind_df['wind_direction'].values)
    
    result = {
        "wind_data": wind_data_points,
        "average_speed": avg_speed,
        "average_direction": avg_direction,
        "created_at": datetime.now(),
        "session_id": session_id
    }
    
    return result

def _calculate_average_direction(directions: np.ndarray) -> float:
    """
    平均風向を計算（単純平均ではなく角度の平均値を計算）
    
    Parameters:
    -----------
    directions : np.array
        風向のリスト
        
    Returns:
    --------
    float
        平均風向
    """
    # 角度をラジアンに変換
    rad = np.radians(directions)
    
    # sin, cosの平均を計算
    sin_mean = np.mean(np.sin(rad))
    cos_mean = np.mean(np.cos(rad))
    
    # 平均角度をラジアンから度に変換
    avg_direction = np.degrees(np.arctan2(sin_mean, cos_mean))
    
    # 0-360の範囲に正規化
    avg_direction = (avg_direction + 360) % 360
    
    return avg_direction