# -*- coding: utf-8 -*-
"""
&e���ӹ

����nGPS���h�����K�&eݤ�Ȓ�Y���ӹ_��Л
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from app.models.strategy_point import StrategyPoint, StrategyDetectionResult
from app.schemas.strategy_detection import StrategyDetectionInput
from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
from sailing_data_processor.strategy.points import WindShiftPoint, TackPoint, LaylinePoint

def detect_strategies(
    params: StrategyDetectionInput,
    user_id: UUID,
    db: Session
) -> Dict[str, Any]:
    """
    &eݤ�Ȓ�
    
    Parameters:
    -----------
    params : StrategyDetectionInput
        &e������
    user_id : UUID
        ����ID
    db : Session
        �������÷��
        
    Returns:
    --------
    Dict[str, Any]
        &e�P�
    """
    try:
        # TODO: �÷��IDK�GPS���h������֗
        # ��o���hWf�n����(
        course_data = _get_demo_course_data()
        wind_field = _get_demo_wind_field()
        
        # &e�hn
        detector = StrategyDetectorWithPropagation()
        
        # &eݤ��n�
        # ����n�
        wind_shifts = detector.detect_wind_shifts_with_propagation(
            course_data=course_data,
            wind_field=wind_field
        )
        
        # �ïݤ��n�
        tack_points = detector.detect_optimal_tacks(
            course_data=course_data,
            wind_field=wind_field
        )
        
        # ���ݤ��n�
        layline_points = detector.detect_laylines(
            course_data=course_data,
            wind_field=wind_field
        )
        
        # �P��q
        strategy_points = _convert_to_strategy_points(
            wind_shifts=wind_shifts,
            tack_points=tack_points,
            layline_points=layline_points
        )
        
        # ��k�eOգ���
        filtered_points = _filter_by_sensitivity(
            strategy_points=strategy_points,
            sensitivity=params.detection_sensitivity
        )
        
        # ���bk	�
        result = _create_strategy_detection_result(
            strategy_points=filtered_points,
            session_id=str(params.session_id)
        )
        
        # TODO: P��������k�X�׷��	
        
        return result
    
    except Exception as e:
        return {"error": f"&e����: {str(e)}"}

def _get_demo_course_data() -> Dict[str, Any]:
    """
    ��(n�������
    
    Returns:
    --------
    Dict[str, Any]
        ������
    """
    # ���
    return {
        "start_time": datetime.now(),
        "legs": [
            {
                "path": {
                    "path_points": [
                        {"lat": 35.0, "lon": 139.0},
                        {"lat": 35.1, "lon": 139.1}
                    ]
                }
            }
        ]
    }

def _get_demo_wind_field() -> Dict[str, Any]:
    """
    ��(n�n4����
    
    Returns:
    --------
    Dict[str, Any]
        �n4���
    """
    import numpy as np
    
    # ���
    lat_grid, lon_grid = np.meshgrid(
        np.linspace(34.9, 35.2, 10),
        np.linspace(138.9, 139.2, 10)
    )
    
    return {
        "time": datetime.now(),
        "lat_grid": lat_grid,
        "lon_grid": lon_grid,
        "wind_direction": np.ones_like(lat_grid) * 270.0,  # �
        "wind_speed": np.ones_like(lat_grid) * 10.0,  # 10���
        "confidence": np.ones_like(lat_grid) * 0.8  # �<�80%
    }

def _convert_to_strategy_points(
    wind_shifts: List,
    tack_points: List,
    layline_points: List
) -> List[Dict[str, Any]]:
    """
    �U�_.&eݤ�Ȓqbk	�
    
    Parameters:
    -----------
    wind_shifts : List
        ����ݤ��n��
    tack_points : List
        �ïݤ��n��
    layline_points : List
        ���ݤ��n��
        
    Returns:
    --------
    List[Dict[str, Any]]
        qbk	�U�_&eݤ��
    """
    strategy_points = []
    
    # ����ݤ��n	�
    for point in wind_shifts:
        strategy_points.append({
            "timestamp": point.time_estimate,
            "latitude": point.position[0],
            "longitude": point.position[1],
            "strategy_type": "wind_shift",
            "confidence": point.shift_probability,
            "metadata": {
                "shift_angle": point.shift_angle,
                "before_direction": point.before_direction,
                "after_direction": point.after_direction,
                "strategic_score": point.strategic_score
            }
        })
    
    # �ïݤ��n	�
    for point in tack_points:
        strategy_points.append({
            "timestamp": point.time_estimate,
            "latitude": point.position[0],
            "longitude": point.position[1],
            "strategy_type": "tack",
            "confidence": 0.8,  # �n$
            "metadata": {
                "vmg_gain": point.vmg_gain if hasattr(point, 'vmg_gain') else 0.0,
                "strategic_score": point.strategic_score if hasattr(point, 'strategic_score') else 0.0
            }
        })
    
    # ���ݤ��n	�
    for point in layline_points:
        strategy_points.append({
            "timestamp": point.time_estimate,
            "latitude": point.position[0],
            "longitude": point.position[1],
            "strategy_type": "layline",
            "confidence": point.confidence if hasattr(point, 'confidence') else 0.8,
            "metadata": {
                "mark_id": point.mark_id if hasattr(point, 'mark_id') else "",
                "strategic_score": point.strategic_score if hasattr(point, 'strategic_score') else 0.0
            }
        })
    
    return strategy_points

def _filter_by_sensitivity(
    strategy_points: List[Dict[str, Any]],
    sensitivity: float
) -> List[Dict[str, Any]]:
    """
    ��k�eDf&eݤ�Ȓգ���
    
    Parameters:
    -----------
    strategy_points : List[Dict[str, Any]]
        &eݤ��n��
    sensitivity : float
        ��0-1	
        
    Returns:
    --------
    List[Dict[str, Any]]
        գ���U�_&eݤ��
    """
    # ��k�eO�<�n�$��
    # �L�D{i�$oNOj���Onݤ��L�U��	
    confidence_threshold = 1.0 - sensitivity
    
    filtered_points = [
        point for point in strategy_points
        if point["confidence"] >= confidence_threshold
    ]
    
    return filtered_points

def _create_strategy_detection_result(
    strategy_points: List[Dict[str, Any]],
    session_id: str
) -> Dict[str, Any]:
    """
    &e�P��API�Tbk	�
    
    Parameters:
    -----------
    strategy_points : List[Dict[str, Any]]
        �U�_&eݤ��
    session_id : str
        �÷��ID
        
    Returns:
    --------
    Dict[str, Any]
        API�Tbn&e�P�
    """
    # ���%nݤ��p�����
    tack_count = sum(1 for p in strategy_points if p["strategy_type"] == "tack")
    jibe_count = sum(1 for p in strategy_points if p["strategy_type"] == "jibe")
    wind_shift_count = sum(1 for p in strategy_points if p["strategy_type"] == "wind_shift")
    layline_count = sum(1 for p in strategy_points if p["strategy_type"] == "layline")
    
    # �h�n
    recommendations = _generate_recommendations(strategy_points)
    
    # ���\
    result = {
        "strategy_points": strategy_points,
        "created_at": datetime.now(),
        "session_id": session_id,
        "track_length": 0.0,  # TODO: ��n$��
        "total_tacks": tack_count,
        "total_jibes": jibe_count,
        "upwind_percentage": 0.0,  # TODO: ��n$��
        "downwind_percentage": 0.0,  # TODO: ��n$��
        "reaching_percentage": 0.0,  # TODO: ��n$��
        "performance_score": 0.0,  # TODO: ��n$��
        "total_wind_shifts": wind_shift_count,
        "total_layline_hits": layline_count,
        "recommendations": recommendations
    }
    
    return result

def _generate_recommendations(strategy_points: List[Dict[str, Any]]) -> List[str]:
    """
    &eݤ��k�eDf�h��
    
    Parameters:
    -----------
    strategy_points : List[Dict[str, Any]]
        &eݤ��
        
    Returns:
    --------
    List[str]
        �h�n��
    """
    recommendations = []
    
    # ����n��kdDfn�h�
    wind_shifts = [p for p in strategy_points if p["strategy_type"] == "wind_shift"]
    if len(wind_shifts) > 0:
        recommendations.append(
            f"{len(wind_shifts)}dn����L�U�~W_���nM�gij�ïLŁgY"
        )
    
    # �ïpkdDfn�h�
    tack_points = [p for p in strategy_points if p["strategy_type"] == "tack"]
    if len(tack_points) > 5:
        recommendations.append(
            "�ï�pLDgY
Łj�ï��YShg��L
W~Y"
        )
    elif len(tack_points) < 2 and len(strategy_points) > 0:
        recommendations.append(
            "�ï�pLjDgY�	k�[_�ïgVMG�
gM���'LB�~Y"
        )
    
    # ���0TkdDfn�h�
    layline_points = [p for p in strategy_points if p["strategy_type"] == "layline"]
    if len(layline_points) > 0:
        recommendations.append(
            "���k�k0TWfD~Y���k�eO~g�ï�E�[�h	)j4LB�~Y"
        )
    
    return recommendations
