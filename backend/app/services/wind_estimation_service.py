"""
������ӹ

����nGPS���K������Y���ӹ_��Л
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
    GPS���K������
    
    Parameters:
    -----------
    gps_data : bytes
        GPS���nФ�
    params : WindEstimationInput
        ��������
    user_id : UUID
        ����ID
    db : Session
        �������÷��
        
    Returns:
    --------
    Dict[str, Any]
        ����P�
    """
    try:
        # GPS����DataFramek	�
        df = _convert_bytes_to_dataframe(gps_data, params.file_format)
        
        if df is None or df.empty:
            return {"error": "���LcWO���~[�gW_"}
        
        # WindEstimator�
        estimator = WindEstimator(boat_type=params.boat_type)
        
        # �����
        wind_df = estimator.estimate_wind_from_single_boat(
            gps_data=df,
            min_tack_angle=params.min_tack_angle,
            boat_type=params.boat_type,
            use_bayesian=params.use_bayesian
        )
        
        if wind_df is None or wind_df.empty:
            return {"error": "��n��k1WW~W_"}
        
        # ��P�����bk	�
        result = _create_wind_estimation_result(wind_df, str(user_id))
        
        # TODO: P��������k�X�׷��	
        
        return result
    
    except Exception as e:
        return {"error": f"�������: {str(e)}"}

def _convert_bytes_to_dataframe(data: bytes, file_format: str) -> Optional[pd.DataFrame]:
    """
    Ф������Pandas DataFramek	�
    
    Parameters:
    -----------
    data : bytes
        Ф�����
    file_format : str
        ա��b'csv', 'gpx'	
        
    Returns:
    --------
    pd.DataFrame or None
        	�U�_DataFrame
    """
    try:
        if file_format.lower() == 'csv':
            return pd.read_csv(io.BytesIO(data))
        elif file_format.lower() == 'gpx':
            # GPX�����)(
            import gpxpy
            import gpxpy.gpx
            
            gpx = gpxpy.parse(io.BytesIO(data))
            
            # ���ݤ�Ȓ��
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
            # TODO: FITա����n��
            # �(o^��
            return None
        else:
            return None
    except Exception as e:
        print(f"���	ۨ��: {str(e)}")
        return None

def _create_wind_estimation_result(wind_df: pd.DataFrame, session_id: str) -> Dict[str, Any]:
    """
    ��n��P��API�Tbk	�
    
    Parameters:
    -----------
    wind_df : pd.DataFrame
        ��n��P�
    session_id : str
        �÷��ID
        
    Returns:
    --------
    Dict[str, Any]
        API�Tbn����P�
    """
    # DataFrameK�Łj������
    wind_data_points = []
    
    for _, row in wind_df.iterrows():
        # �L��1LB�4o]��(jD4o0.0g�(
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
    
    # sG$n�
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
    sG��������n_�XsGgojD	
    
    Parameters:
    -----------
    directions : np.array
        �nM�	
        
    Returns:
    --------
    float
        sG��	
    """
    # Ҧ�鸢�k	�
    rad = np.radians(directions)
    
    # sin, cosnsG��
    sin_mean = np.mean(np.sin(rad))
    cos_mean = np.mean(np.cos(rad))
    
    # sGҦ�鸢�K��k	�
    avg_direction = np.degrees(np.arctan2(sin_mean, cos_mean))
    
    # 0-360�n��kc�
    avg_direction = (avg_direction + 360) % 360
    
    return avg_direction
