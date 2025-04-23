"""
¨¨¨šµüÓ¹

»üêó°nGPSÇü¿K‰¨¨’¨šY‹µüÓ¹_ı’Ğ›
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
    GPSÇü¿K‰¨¨’¨š
    
    Parameters:
    -----------
    gps_data : bytes
        GPSÇü¿nĞ¤È
    params : WindEstimationInput
        ¨¨šÑéáü¿
    user_id : UUID
        æü¶üID
    db : Session
        Çü¿Ùü¹»Ã·çó
        
    Returns:
    --------
    Dict[str, Any]
        ¨¨¨šPœ
    """
    try:
        # GPSÇü¿’DataFramek	Û
        df = _convert_bytes_to_dataframe(gps_data, params.file_format)
        
        if df is None or df.empty:
            return {"error": "Çü¿LcWO­¼~[“gW_"}
        
        # WindEstimator’
        estimator = WindEstimator(boat_type=params.boat_type)
        
        # ¨¨’¨š
        wind_df = estimator.estimate_wind_from_single_boat(
            gps_data=df,
            min_tack_angle=params.min_tack_angle,
            boat_type=params.boat_type,
            use_bayesian=params.use_bayesian
        )
        
        if wind_df is None or wind_df.empty:
            return {"error": "¨¨n¨šk1WW~W_"}
        
        # ¨šPœ’ì¹İó¹bk	Û
        result = _create_wind_estimation_result(wind_df, str(user_id))
        
        # TODO: Pœ’Çü¿Ùü¹kİXª×·çó	
        
        return result
    
    except Exception as e:
        return {"error": f"¨¨¨š¨éü: {str(e)}"}

def _convert_bytes_to_dataframe(data: bytes, file_format: str) -> Optional[pd.DataFrame]:
    """
    Ğ¤ÊêÇü¿’Pandas DataFramek	Û
    
    Parameters:
    -----------
    data : bytes
        Ğ¤ÊêÇü¿
    file_format : str
        Õ¡¤ëb'csv', 'gpx'	
        
    Returns:
    --------
    pd.DataFrame or None
        	ÛUŒ_DataFrame
    """
    try:
        if file_format.lower() == 'csv':
            return pd.read_csv(io.BytesIO(data))
        elif file_format.lower() == 'gpx':
            # GPXÑüµü’)(
            import gpxpy
            import gpxpy.gpx
            
            gpx = gpxpy.parse(io.BytesIO(data))
            
            # Çü¿İ¤óÈ’½ú
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
            # TODO: FITÕ¡¤ë­¼ænŸÅ
            # ş(o^şÜ
            return None
        else:
            return None
    except Exception as e:
        print(f"Çü¿	Û¨éü: {str(e)}")
        return None

def _create_wind_estimation_result(wind_df: pd.DataFrame, session_id: str) -> Dict[str, Any]:
    """
    ¨¨n¨šPœ’APIÜTbk	Û
    
    Parameters:
    -----------
    wind_df : pd.DataFrame
        ¨¨n¨šPœ
    session_id : str
        »Ã·çóID
        
    Returns:
    --------
    Dict[str, Any]
        APIÜTbn¨¨¨šPœ
    """
    # DataFrameK‰ÅjÇü¿’½ú
    wind_data_points = []
    
    for _, row in wind_df.iterrows():
        # ï¦L¦Å1LB‹4o]Œ’(jD4o0.0gã(
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
    
    # sG$n—
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
    sG¨’—†°Çü¿n_XsGgojD	
    
    Parameters:
    -----------
    directions : np.array
        ¨nM¦	
        
    Returns:
    --------
    float
        sG¨¦	
    """
    # Ò¦’é¸¢ók	Û
    rad = np.radians(directions)
    
    # sin, cosnsG’—
    sin_mean = np.mean(np.sin(rad))
    cos_mean = np.mean(np.cos(rad))
    
    # sGÒ¦’é¸¢óK‰¦k	Û
    avg_direction = np.degrees(np.arctan2(sin_mean, cos_mean))
    
    # 0-360¦nÄòkc
    avg_direction = (avg_direction + 360) % 360
    
    return avg_direction
