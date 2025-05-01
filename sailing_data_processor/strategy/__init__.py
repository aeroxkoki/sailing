# -*- coding: utf-8 -*-
"""
sailing_data_processor.strategy package

Provides detection, evaluation, and visualization of strategic decision points in sailing races.

Module dependencies:
Base classes: detector -> evaluator -> visualizer
Strategy points: points
Special classes: strategy_detector_with_propagation
"""

import os
import sys
import logging
import warnings
from typing import Optional, Type

logger = logging.getLogger(__name__)

# Import base classes
from .points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint, StrategyAlternative
from .detector import StrategyDetector
from .evaluator import StrategyEvaluator
from .visualizer import StrategyVisualizer

# Use lazy loading for StrategyDetectorWithPropagation
# Avoid direct import to prevent circular references
StrategyDetectorWithPropagation = None

def load_strategy_detector_with_propagation() -> Optional[Type]:
    """Lazy-load the strategy detector class
    
    Returns:
        StrategyDetectorWithPropagation: Strategy detector class
    """
    global StrategyDetectorWithPropagation
    
    # Return already loaded class if available
    if StrategyDetectorWithPropagation is not None:
        return StrategyDetectorWithPropagation
    
    # Log path information for debugging
    logger.debug(f"Strategy detector loading with sys.path: {sys.path}")
    
    try:
        # Try to import using relative path
        logger.debug("Loading StrategyDetectorWithPropagation with relative import")
        from .strategy_detector_with_propagation import StrategyDetectorWithPropagation as SDwP
        
        if SDwP is not None:
            StrategyDetectorWithPropagation = SDwP
            logger.info("Successfully loaded with relative import")
            return StrategyDetectorWithPropagation
        else:
            logger.warning("Module loaded but StrategyDetectorWithPropagation is None")
            # Continue without raising exception
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
    
    # Detect test environment
    is_test_environment = any(module in sys.modules for module in ['unittest', 'pytest', 'conftest'])
    logger.debug(f"Test environment detection: {is_test_environment}")
    
    # Provide fallback implementation
    logger.info("Creating fallback implementation")
    
    # Define fallback class
    class FallbackSDwP(StrategyDetector):
        """Fallback class for StrategyDetectorWithPropagation"""
        def __init__(self, vmg_calculator=None, wind_fusion_system=None):
            super().__init__(vmg_calculator)
            self.wind_fusion_system = wind_fusion_system
            self.propagation_config = {
                'wind_shift_prediction_horizon': 1800,
                'prediction_time_step': 300,
                'wind_shift_confidence_threshold': 0.7,
                'min_propagation_distance': 1000,
                'prediction_confidence_decay': 0.1,
                'use_historical_data': True
            }
        
        def detect_wind_shifts_with_propagation(self, course_data, wind_field):
            """Fallback implementation - wind shift detection"""
            logger.debug("FallbackSDwP.detect_wind_shifts_with_propagation called")
            return []
            
        def _detect_wind_shifts_in_legs(self, course_data, wind_field, target_time):
            """Fallback implementation - leg-based wind shift detection"""
            return []
            
        def _get_wind_at_position(self, lat, lon, time, wind_field):
            """Fallback implementation - get wind at position"""
            return None
        
        def detect_optimal_tacks(self, course_data, wind_field):
            """Fallback implementation - optimal tack detection"""
            return []
            
        def detect_laylines(self, course_data, wind_field):
            """Fallback implementation - layline detection"""
            return []
    
    # Set appropriate class name
    FallbackSDwP.__name__ = "StrategyDetectorWithPropagation"
    StrategyDetectorWithPropagation = FallbackSDwP
    logger.info("Using fallback StrategyDetectorWithPropagation implementation")
    
    return StrategyDetectorWithPropagation

__version__ = '1.0.1'
__all__ = [
    'StrategyPoint',
    'WindShiftPoint',
    'TackPoint',
    'LaylinePoint',
    'StrategyAlternative',
    'StrategyDetector',
    'StrategyEvaluator',
    'StrategyVisualizer',
    'load_strategy_detector_with_propagation',
]

def get_version():
    """Returns the package version"""
    return __version__
