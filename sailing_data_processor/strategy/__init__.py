# -*- coding: utf-8 -*-
"""
sailing_data_processor.strategy パッケージ

セーリングレースにおける戦略的判断ポイントの検出、評価、可視化機能を提供します。
"""

from .points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint, StrategyAlternative
from .detector import StrategyDetector
from .evaluator import StrategyEvaluator
from .visualizer import StrategyVisualizer

# StrategyDetectorWithPropagation は遅延インポートを使用
# 循環参照を避けるため、直接インポートしない
StrategyDetectorWithPropagation = None

def load_strategy_detector_with_propagation():
    """戦略検出器を遅延ロード"""
    global StrategyDetectorWithPropagation
    if StrategyDetectorWithPropagation is None:
        try:
            # 絶対パスで試行
            from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation as SDwP
            StrategyDetectorWithPropagation = SDwP
        except ImportError:
            try:
                # 相対パスで試行
                from .strategy_detector_with_propagation import StrategyDetectorWithPropagation as SDwP
                StrategyDetectorWithPropagation = SDwP
            except ImportError:
                import warnings
                import sys
                import os
                
                warnings.warn("StrategyDetectorWithPropagation could not be imported")
                
                # ダミーの実装を提供
                from .detector import StrategyDetector
                
                # テスト用のダミークラス定義
                class SDwP(StrategyDetector):
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
                        
                    def _get_wind_at_position(self, lat, lon, time, wind_field):
                        """テスト用の空実装"""
                        return None
                
                StrategyDetectorWithPropagation = SDwP
                warnings.warn("Using dummy implementation of StrategyDetectorWithPropagation")
    
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
    'load_strategy_detector_with_propagation'
]

def get_version():
    """パッケージのバージョンを返します"""
    return __version__
