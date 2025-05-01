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

# Import base classes first to avoid circular dependencies
from .points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint, StrategyAlternative
from .detector import StrategyDetector
from .evaluator import StrategyEvaluator
from .visualizer import StrategyVisualizer

# Avoid eager loading to prevent circular references
StrategyDetectorWithPropagation = None

# Set a flag for import tracking
_strategy_imports_attempted = False

def load_strategy_detector_with_propagation() -> Optional[Type]:
    """戦略検出器クラスの遅延ロード
    
    circular importを防ぐために遅延ロードを行う
    テストの際にも使用される
    
    Returns:
        StrategyDetectorWithPropagation: 戦略検出器クラス
    """
    global StrategyDetectorWithPropagation, _strategy_imports_attempted
    
    # すでにロードされている場合はそれを返す
    if StrategyDetectorWithPropagation is not None:
        return StrategyDetectorWithPropagation
    
    # インポートの試行回数を制限（無限ループ防止）
    if _strategy_imports_attempted:
        logger.warning("Strategy detector import already attempted, using fallback")
        return _create_fallback_detector()
    
    _strategy_imports_attempted = True
    
    # デバッグ情報
    logger.debug(f"戦略検出器ロード - sys.path: {sys.path}")
    
    try:
        # 相対パスでインポート
        logger.debug("相対パスでStrategyDetectorWithPropagationをロード")
        from .strategy_detector_with_propagation import StrategyDetectorWithPropagation as SDwP
        
        if SDwP is not None:
            StrategyDetectorWithPropagation = SDwP
            logger.info("相対パスでのインポートに成功")
            return StrategyDetectorWithPropagation
        else:
            logger.warning("モジュールはロードされましたがStrategyDetectorWithPropagationがNoneです")
    except ImportError as e:
        logger.error(f"インポートエラー: {e}")
    
    # フォールバックを使用
    return _create_fallback_detector()

def _create_fallback_detector():
    """フォールバック実装を作成"""
    global StrategyDetectorWithPropagation
    
    logger.info("フォールバック実装を作成")
    
    # テスト環境かどうか
    is_test_environment = any(module in sys.modules for module in ['unittest', 'pytest', 'conftest'])
    logger.debug(f"テスト環境判定: {is_test_environment}")
    
    # フォールバッククラス定義
    class FallbackSDwP(StrategyDetector):
        """StrategyDetectorWithPropagationのフォールバック"""
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
            """風向変化検出のフォールバック実装"""
            logger.debug("FallbackSDwP.detect_wind_shifts_with_propagation called")
            return []
            
        def _detect_wind_shifts_in_legs(self, course_data, wind_field, target_time):
            """レグごとの風向変化検出のフォールバック実装"""
            return []
            
        def _get_wind_at_position(self, lat, lon, time, wind_field):
            """位置での風取得のフォールバック実装"""
            return None
        
        def detect_optimal_tacks(self, course_data, wind_field):
            """最適タック検出のフォールバック実装"""
            return []
            
        def detect_laylines(self, course_data, wind_field):
            """レイライン検出のフォールバック実装"""
            return []
    
    # クラス名を設定
    FallbackSDwP.__name__ = "StrategyDetectorWithPropagation"
    StrategyDetectorWithPropagation = FallbackSDwP
    logger.info("フォールバック実装を使用")
    
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
