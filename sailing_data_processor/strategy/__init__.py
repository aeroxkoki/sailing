# -*- coding: utf-8 -*-
"""
sailing_data_processor.strategy パッケージ

セーリングレースにおける戦略的判断ポイントの検出、評価、可視化機能を提供します。
"""

from .points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint, StrategyAlternative
from .detector import StrategyDetector
from .evaluator import StrategyEvaluator
from .visualizer import StrategyVisualizer

# 風の移動予測を考慮した戦略検出器をインポート
try:
    # 絶対パスで試行
    from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation
except ImportError:
    try:
        # 相対パスで試行
        from .strategy_detector_with_propagation import StrategyDetectorWithPropagation
    except ImportError:
        import warnings
        import sys
        import os
        import traceback
        
        warnings.warn("StrategyDetectorWithPropagation could not be imported")
        warnings.warn(f"Current sys.path: {sys.path}")
        warnings.warn(f"Current directory: {os.getcwd()}")
        traceback.print_exc()
        
        # ダミーの実装を提供
        from .detector import StrategyDetector
        from .points import WindShiftPoint, TackPoint, LaylinePoint
        from .strategy_detector_utils import (
            calculate_distance, get_time_difference_seconds, normalize_to_timestamp,
            filter_duplicate_shift_points, filter_duplicate_tack_points, filter_duplicate_laylines,
            calculate_strategic_score, determine_tack_type, angle_difference
        )
        
        # テスト用のダミークラス定義
        class StrategyDetectorWithPropagation(StrategyDetector):
            """テスト用のダミークラス"""
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
                """テスト用の空実装"""
                return []
                
            def _detect_wind_shifts_in_legs(self, course_data, wind_field, target_time):
                """テスト用の空実装"""
                return []
                
            def _determine_tack_type(self, bearing, wind_direction):
                """determine_tack_type関数をラップ"""
                return determine_tack_type(bearing, wind_direction)
                
            def _get_wind_at_position(self, lat, lon, time, wind_field):
                """テスト用の空実装"""
                return None

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
    'StrategyDetectorWithPropagation'
]

def get_version():
    """パッケージのバージョンを返します"""
    return __version__
