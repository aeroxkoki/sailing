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
    from .strategy_detector_with_propagation import StrategyDetectorWithPropagation
except ImportError:
    import warnings
    warnings.warn("StrategyDetectorWithPropagation could not be imported")
    StrategyDetectorWithPropagation = None

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
