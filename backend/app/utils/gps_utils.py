"""
GPS����(��ƣ�ƣ
"""

import math
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional, Union

import numpy as np
from geopy.distance import geodesic


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    ������l�(Wf2��n������	��
    
    Args:
        lat1: 0�1n�
        lon1: 0�1nL�
        lat2: 0�2n�
        lon2: 0�2nL�
        
    Returns:
        2��n������	
    """
    return geodesic((lat1, lon1), (lat2, lon2)).meters


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    2��n�M��	��
    
    Args:
        lat1: 0�1n��	
        lon1: 0�1nL��	
        lat2: 0�2n��	
        lon2: 0�2nL��	
        
    Returns:
        K�Bފn�M��0-360	
    """
    # 鸢�x	�
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # �M��
    y = math.sin(lon2_rad - lon1_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon2_rad - lon1_rad)
    bearing = math.atan2(y, x)
    
    # 鸢�K��x	�W0-360n��k�t
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing


def calculate_speed(
    lat1: float, lon1: float, timestamp1: datetime,
    lat2: float, lon2: float, timestamp2: datetime
) -> float:
    """
    2��n������	��
    
    Args:
        lat1: 0�1n�
        lon1: 0�1nL�
        timestamp1: 0�1nB;
        lat2: 0�2n�
        lon2: 0�2nL�
        timestamp2: 0�2nB;
        
    Returns:
        ����	
    """
    # �������	
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    
    # B���	
    time_diff = (timestamp2 - timestamp1).total_seconds()
    
    if time_diff <= 0:
        return 0.0
    
    # ��m/s	
    speed_ms = distance / time_diff
    
    # ���x	�1��� = 0.514444 m/s	
    speed_knots = speed_ms / 0.514444
    
    return speed_knots


def smooth_gps_data(
    latitudes: List[float],
    longitudes: List[float],
    timestamps: List[datetime],
    window_size: int = 5
) -> Tuple[List[float], List[float]]:
    """
    ��sGk��GPS���ns�
    
    Args:
        latitudes: �n��
        longitudes: L�n��
        timestamps: ��๿��n��
        window_size: s����ɦ���
        
    Returns:
        s�U�_�hL�n���
    """
    if len(latitudes) != len(longitudes) or len(latitudes) != len(timestamps):
        raise ValueError("Input lists must have the same length")
    
    if len(latitudes) < window_size:
        return latitudes, longitudes
    
    smooth_lat = []
    smooth_lon = []
    
    half_window = window_size // 2
    
    for i in range(len(latitudes)):
        # ���ɦn��z�
        start_idx = max(0, i - half_window)
        end_idx = min(len(latitudes), i + half_window + 1)
        
        # ���ɦ�n$nsG��
        lat_avg = sum(latitudes[start_idx:end_idx]) / (end_idx - start_idx)
        lon_avg = sum(longitudes[start_idx:end_idx]) / (end_idx - start_idx)
        
        smooth_lat.append(lat_avg)
        smooth_lon.append(lon_avg)
    
    return smooth_lat, smooth_lon


def detect_tacks_and_gybes(
    headings: List[float],
    timestamps: List[datetime],
    threshold_angle: float = 80.0,
    min_time_diff: float = 5.0
) -> List[Dict[str, Any]]:
    """
    �ïh���n�
    
    Args:
        headings: Gn�M�n���	
        timestamps: ��๿��n��
        threshold_angle: �M	n�$�	
        min_time_diff:  B����	
        
    Returns:
        �U�_�ï/���n����b	
    """
    if len(headings) != len(timestamps):
        raise ValueError("Input lists must have the same length")
    
    if len(headings) < 2:
        return []
    
    maneuvers = []
    last_maneuver_time = timestamps[0]
    
    for i in range(1, len(headings)):
        # �M�n	��
        heading_diff = abs((headings[i] - headings[i-1] + 180) % 360 - 180)
        
        # B���
        time_diff = (timestamps[i] - last_maneuver_time).total_seconds()
        
        # �$��H��M	Kd B�����_Y4
        if heading_diff > threshold_angle and time_diff > min_time_diff:
            # �ïK���K�$���nWf��koz�	
            maneuver_type = "tack" if 70 <= abs(headings[i] - headings[i-1]) <= 110 else "gybe"
            
            maneuvers.append({
                "timestamp": timestamps[i],
                "type": maneuver_type,
                "heading_before": headings[i-1],
                "heading_after": headings[i],
                "heading_change": heading_diff
            })
            
            last_maneuver_time = timestamps[i]
    
    return maneuvers


def calculate_vmg(
    boat_speed: float,
    boat_heading: float,
    wind_direction: float
) -> float:
    """
    VMGVelocity Made Good�
/��xn	��	��
    
    Args:
        boat_speed: G���	
        boat_heading: Gn�M��0-360	
        wind_direction: ��0-360�L9DfO��	
        
    Returns:
        VMG���cn$o�
xn2L�n$o�xn2L	
    """
    # GnMh�nҦ��
    angle_diff = abs((boat_heading - wind_direction + 180) % 360 - 180)
    
    # VMG�cos(angle_diff)g��xn�q�B��	
    vmg = boat_speed * math.cos(math.radians(angle_diff))
    
    return vmg
