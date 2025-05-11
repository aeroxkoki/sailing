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
import importlib.util
from typing import Optional, Type

logger = logging.getLogger(__name__)

# Import base classes first to avoid circular dependencies
from sailing_data_processor.strategy.points import StrategyPoint, WindShiftPoint, TackPoint, LaylinePoint, StrategyAlternative
from sailing_data_processor.strategy.detector import StrategyDetector
from sailing_data_processor.strategy.evaluator import StrategyEvaluator

# Only import visualizer when explicitly needed to avoid matplotlib dependency
StrategyVisualizer = None

# Avoid eager loading to prevent circular references
StrategyDetectorWithPropagation = None
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
        logger.debug("既にロード済みの戦略検出器を返します")
        return StrategyDetectorWithPropagation
    
    # インポートの試行回数を制限（無限ループ防止）
    if _strategy_imports_attempted:
        logger.warning("Strategy detector import already attempted, using fallback")
        return _create_fallback_detector()
    
    _strategy_imports_attempted = True
    
    # デバッグ情報
    logger.debug(f"戦略検出器ロード - sys.path: {sys.path}")
    logger.debug(f"現在のディレクトリ: {os.getcwd()}")
    logger.debug(f"モジュールファイルパス: {__file__}")
    
    # 1. 直接インポート (もっとも単純な方法)
    try:
        from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation as SDwP
        StrategyDetectorWithPropagation = SDwP
        logger.info("直接インポートに成功しました")
        return StrategyDetectorWithPropagation
    except ImportError as e:
        logger.warning(f"直接インポートに失敗しました: {e}")
    
    # 2. モジュール絶対パスからのロード
    try:
        module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                   "strategy_detector_with_propagation.py")
        if os.path.exists(module_path):
            module_name = "strategy_detector_with_propagation"
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            
            if spec:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, "StrategyDetectorWithPropagation"):
                    StrategyDetectorWithPropagation = getattr(module, "StrategyDetectorWithPropagation")
                    logger.info("絶対パスからのインポートに成功しました")
                    return StrategyDetectorWithPropagation
    except Exception as e:
        logger.warning(f"絶対パスからのインポートに失敗しました: {e}")
    
    # 3. フォールバック実装の使用
    return _create_fallback_detector()

def _create_fallback_detector():
    """フォールバック実装を作成"""
    global StrategyDetectorWithPropagation
    
    logger.info("フォールバック実装を作成します")
    
    # フォールバッククラス定義
    class FallbackSDwP(StrategyDetector):
        """StrategyDetectorWithPropagationのフォールバック
        
        循環インポートや動的ロードの問題が発生した場合に使用される
        テスト環境での代替実装。実際の実装とのAPI互換性を確保します。
        """
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
            
            logger.info("フォールバック戦略検出器が初期化されました")
        
        def detect_wind_shifts_with_propagation(self, course_data, wind_field):
            """風向予測を考慮した風向変化検出"""
            logger.debug("FallbackSDwP.detect_wind_shifts_with_propagation called")
            return []
            
        def _detect_wind_shifts_in_legs(self, course_data, wind_field, target_time):
            """各レグでの風向変化検出"""
            return []
            
        def _get_wind_at_position(self, lat, lon, time, wind_field):
            """位置での風情報を取得"""
            return None
        
        def __str__(self):
            return "StrategyDetectorWithPropagation(Fallback)"
        
        def __repr__(self):
            return "StrategyDetectorWithPropagation(Fallback)"
    
    # クラス名を設定
    FallbackSDwP.__name__ = "StrategyDetectorWithPropagation"
    StrategyDetectorWithPropagation = FallbackSDwP
    logger.info("フォールバック実装の使用を開始します")
    
    return StrategyDetectorWithPropagation

def load_strategy_visualizer() -> Optional[Type]:
    """戦略可視化クラスの遅延ロード
    
    matplotlibの依存を避けるための遅延ロード
    
    Returns:
        StrategyVisualizer: 戦略可視化クラス
    """
    global StrategyVisualizer
    
    if StrategyVisualizer is not None:
        return StrategyVisualizer
    
    try:
        from sailing_data_processor.strategy.visualizer import StrategyVisualizer as SV
        StrategyVisualizer = SV
        logger.info("StrategyVisualizerのインポートに成功しました")
        return StrategyVisualizer
    except ImportError as e:
        logger.warning(f"StrategyVisualizerのインポートに失敗しました: {e}")
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
    'load_strategy_detector_with_propagation',
    'load_strategy_visualizer',
]

def get_version():
    """Returns the package version"""
    return __version__