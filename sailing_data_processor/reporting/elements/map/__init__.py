# -*- coding: utf-8 -*-
"""
sailing_data_processor.reporting.elements.map

マップ関連の要素を提供するパッケージです。
GPSトラック、コース、風場などの空間データを視覚化するための要素が含まれます。
"""

from sailing_data_processor.reporting.elements.map.base_map_element import BaseMapElement
from sailing_data_processor.reporting.elements.map.track_map_element import TrackMapElement
from sailing_data_processor.reporting.elements.map.map_utils import (
    calculate_distance,
    calculate_bearing,
    create_color_scale,
    simplify_track,
    extract_track_segments,
    analyze_track_statistics,
    detect_significant_points,
    find_nearest_point
)

__all__ = [
    'BaseMapElement',
    'TrackMapElement',
    'calculate_distance',
    'calculate_bearing',
    'create_color_scale',
    'simplify_track',
    'extract_track_segments',
    'analyze_track_statistics',
    'detect_significant_points',
    'find_nearest_point'
]
