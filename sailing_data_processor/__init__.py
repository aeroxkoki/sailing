# -*- coding: utf-8 -*-
# sailing_data_processor/__init__.py
"""
セーリング戦略分析システム - データ処理モジュール

GPSデータから風向風速を推定し、セーリングレースの戦略分析を支援するモジュール
"""

# バージョン情報
__version__ = '2.0.0'

# 後方互換性のために元のクラスをインポート可能にする
from .core import SailingDataProcessor

# 新しいクラスもインポート可能にする
from .wind_estimator import WindEstimator
from .performance_optimizer import PerformanceOptimizer
from .boat_data_fusion import BoatDataFusionModel
from .wind_field_interpolator import WindFieldInterpolator
from .wind_propagation_model import WindPropagationModel
from .wind_field_fusion_system import WindFieldFusionSystem
from .prediction_evaluator import PredictionEvaluator

# 将来的な循環参照を防ぐために、直接importは避け、遅延インポートを使う
StrategyDetectorWithPropagation = None

def load_strategy_detector():
    """戦略検出器を遅延ロード"""
    global StrategyDetectorWithPropagation
    if StrategyDetectorWithPropagation is None:
        try:
            from .strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation as SDwP
            StrategyDetectorWithPropagation = SDwP
        except ImportError:
            import warnings
            warnings.warn("StrategyDetectorWithPropagation could not be imported")
            StrategyDetectorWithPropagation = None
    return StrategyDetectorWithPropagation

# データモデルのインポート
from .data_model import (
    DataContainer, GPSDataContainer, WindDataContainer, StrategyPointContainer,
    cached, memoize, clear_cache, get_cache_stats
)

# 将来的に警告を表示するための準備
import warnings

# デフォルトでエクスポートするシンボル
__all__ = [
    # 従来のクラス
    'SailingDataProcessor',
    'WindEstimator',
    'PerformanceOptimizer',
    'BoatDataFusionModel',
    'WindFieldInterpolator', 
    'WindPropagationModel',
    'WindFieldFusionSystem',
    'PredictionEvaluator',
    
    # 戦略検出
    'load_strategy_detector',
    
    # データモデル
    'DataContainer',
    'GPSDataContainer', 
    'WindDataContainer',
    'StrategyPointContainer',
    
    # キャッシュ機能
    'cached',
    'memoize',
    'clear_cache',
    'get_cache_stats'
]
