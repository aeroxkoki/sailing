# -*- coding: utf-8 -*-
"""
Module for data connector between map layers and data sources.
This module provides functions for binding and data transformation between layers and data sources.
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
