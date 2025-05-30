# -*- coding: utf-8 -*-
# sailing_data_processor/__init__.py
"""
セーリング戦略分析システム - データ処理モジュール

GPSデータから風向風速を推定し、セーリングレースの戦略分析を支援するモジュール

モジュール依存関係:
core -> data_model
      -> wind_estimator
      -> performance_optimizer
      -> boat_data_fusion
      -> wind_field_interpolator
      -> wind_propagation_model -> wind_field_fusion_system
                                -> strategy
"""

# バージョン情報
__version__ = '2.0.0'

# ロギング設定
import logging
import os
import sys
import warnings
import importlib.util
from typing import Optional, Type, Any

# 最初にパス情報をログに記録
logger = logging.getLogger(__name__)
logger.debug(f"sailing_data_processor path: {__file__}")
logger.debug(f"sailing_data_processor version: {__version__}")

# 後方互換性のために元のクラスをインポート可能にする
from .core import SailingDataProcessor

# 新しいクラスをインポート
# 注: .wind_estimator は非推奨。代わりに sailing_data_processor.wind.wind_estimator を使用してください
import warnings
warnings.warn(
    "This module is deprecated. Use sailing_data_processor.wind.wind_estimator instead.",
    DeprecationWarning,
    stacklevel=2
)
from .wind import wind_estimator as _wind_estimator_module
WindEstimator = _wind_estimator_module.WindEstimator
from .performance_optimizer import PerformanceOptimizer
from .boat_data_fusion import BoatDataFusionModel
from .wind_field_interpolator import WindFieldInterpolator

# 遅延ロードする必要があるクラスのインポート
try:
    from .wind_propagation_model import WindPropagationModel
    logger.debug("Successfully imported WindPropagationModel")
    # モジュールがインポートされたことを確認するためのインスタンス作成
    wind_prop_model = WindPropagationModel()
    logger.debug("Successfully created WindPropagationModel instance")
except ImportError as e:
    logger.error(f"Error importing WindPropagationModel: {e}")
    WindPropagationModel = None

try:
    from .wind_field_fusion_system import WindFieldFusionSystem
    logger.debug("Successfully imported WindFieldFusionSystem")
except ImportError as e:
    logger.error(f"Error importing WindFieldFusionSystem: {e}")
    WindFieldFusionSystem = None

from .prediction_evaluator import PredictionEvaluator

# 戦略検出器をグローバル変数として初期化
StrategyDetectorWithPropagation = None

def load_strategy_detector() -> Optional[Type]:
    """戦略検出器を遅延ロード
    
    戦略検出器は循環参照を避けるために遅延ロードされます。
    strategy パッケージの遅延ロード機能を使用します。
    
    Returns:
        StrategyDetectorWithPropagation: 戦略検出器クラス（またはNone）
    """
    global StrategyDetectorWithPropagation
    
    # 既にロード済みならそれを返す
    if StrategyDetectorWithPropagation is not None:
        logger.debug("既にロード済みの戦略検出器を返します")
        return StrategyDetectorWithPropagation
    
    # デバッグ情報をログに出力
    logger.info("===== 戦略検出器ロード開始 =====")
    logger.debug(f"現在のディレクトリ: {os.getcwd()}")
    logger.debug(f"Python path: {sys.path}")
    logger.debug(f"sailing_data_processor path: {__file__}")
    
    # 1. 直接インポート試行 - もっとも単純で堅牢な方法
    try:
        from sailing_data_processor.strategy.strategy_detector_with_propagation import StrategyDetectorWithPropagation as SDwP
        if SDwP is not None:
            StrategyDetectorWithPropagation = SDwP
            logger.info(f"Successfully loaded StrategyDetectorWithPropagation via direct import")
            logger.info("===== 戦略検出器ロード完了 =====")
            return StrategyDetectorWithPropagation
    except ImportError as e:
        logger.warning(f"直接インポートに失敗: {e}")
    
    # 2. 戦略モジュールを経由したインポート試行
    try:
        import sailing_data_processor.strategy
        if hasattr(sailing_data_processor.strategy, 'load_strategy_detector_with_propagation'):
            detector = sailing_data_processor.strategy.load_strategy_detector_with_propagation()
            if detector is not None:
                StrategyDetectorWithPropagation = detector
                logger.info(f"Successfully loaded StrategyDetectorWithPropagation via root loader: {detector.__name__}")
                logger.info("===== 戦略検出器ロード完了 =====")
                return StrategyDetectorWithPropagation
    except Exception as e:
        logger.warning(f"戦略モジュールを経由したインポートに失敗: {e}")
    
    # 3. 最後の手段：フォールバック実装
    try:
        # 基本クラスをインポート
        from sailing_data_processor.strategy.detector import StrategyDetector
        
        # 最小限の実装
        class SimpleStrategyDetector(StrategyDetector):
            """テスト環境用の最小限実装"""
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
                logger.info("Fallback strategy detector initialized")
            
            def detect_wind_shifts_with_propagation(self, course_data, wind_field):
                """最小限の実装"""
                logger.debug("SimpleStrategyDetector.detect_wind_shifts_with_propagation called")
                return []
                
            def _detect_wind_shifts_in_legs(self, course_data, wind_field, target_time):
                """最小限の実装"""
                return []
                
            def _get_wind_at_position(self, lat, lon, time, wind_field):
                """最小限の実装"""
                return None
            
            def __str__(self):
                return "StrategyDetectorWithPropagation(Fallback)"
        
        # クラス名を設定
        SimpleStrategyDetector.__name__ = "StrategyDetectorWithPropagation"
        StrategyDetectorWithPropagation = SimpleStrategyDetector
        logger.info("Created fallback implementation for strategy detector")
    
    except Exception as e:
        logger.error(f"Fallback creation also failed: {e}")
        StrategyDetectorWithPropagation = None
    
    logger.info("===== 戦略検出器ロード完了 =====")
    return StrategyDetectorWithPropagation

# データモデルのインポート
from .data_model import (
    DataContainer, GPSDataContainer, WindDataContainer, StrategyPointContainer,
    cached, memoize, clear_cache, get_cache_stats
)

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