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
    """戦略検出器を遅延ロード
    
    最初に strategy パッケージの遅延ロード関数を使用し、
    失敗した場合はダミー実装を提供します。
    
    Returns:
        StrategyDetectorWithPropagation: 戦略検出器クラス
    """
    global StrategyDetectorWithPropagation
    if StrategyDetectorWithPropagation is None:
        # パス情報をログに出力
        import sys
        import logging
        import os
        logger = logging.getLogger(__name__)
        logger.debug(f"Current directory: {os.getcwd()}")
        logger.debug(f"Root load_strategy_detector called with sys.path: {sys.path}")
        logger.debug(f"sailing_data_processor path: {__file__}")
        
        try:
            print("===== 戦略検出器ロード開始 =====")
            print(f"現在のディレクトリ: {os.getcwd()}")
            print(f"Python path: {sys.path}")
            print(f"sailing_data_processor path: {__file__}")
            print("Imported load_strategy_detector from root module")
            print("Root trying to load strategy detector with package loader")
            # まず strategy パッケージの遅延ロード関数を使用
            from .strategy import load_strategy_detector_with_propagation
            
            # 遅延ロード関数を呼び出す
            detector = load_strategy_detector_with_propagation()
            
            if detector is not None:
                StrategyDetectorWithPropagation = detector
                print(f"Successfully loaded strategy detector: {detector.__name__}")
                print(f"Successfully loaded StrategyDetectorWithPropagation via root loader: {detector.__name__}")
                print("===== 戦略検出器ロード完了 =====")
            else:
                # 失敗した場合はダミー実装を提供
                import warnings
                warnings.warn("Strategy package loader returned None, providing root dummy implementation")
                from .strategy.detector import StrategyDetector
                StrategyDetectorWithPropagation = create_dummy_strategy_detector(StrategyDetector)
                print("===== 戦略検出器ロード失敗: ダミー実装を使用 =====")
        except ImportError as e:
            import warnings
            warnings.warn(f"StrategyDetectorWithPropagation could not be imported: {e}")
            # テスト環境用のダミー実装を提供
            try:
                from .strategy.detector import StrategyDetector
                StrategyDetectorWithPropagation = create_dummy_strategy_detector(StrategyDetector)
                print("Created root dummy implementation after import error")
                print("===== 戦略検出器ロード失敗: ダミー実装を使用 =====")
            except ImportError:
                # 基本クラスのインポートも失敗した場合
                warnings.warn(f"StrategyDetector base class could not be imported")
                StrategyDetectorWithPropagation = None
                print("===== 戦略検出器ロード失敗: 基本クラスのインポート失敗 =====")
    
    return StrategyDetectorWithPropagation

def create_dummy_strategy_detector(base_class):
    """ダミーの戦略検出器を作成する補助関数
    
    テスト環境で使用するためのダミー実装を提供します。
    
    Args:
        base_class: 継承する基底クラス (通常は StrategyDetector)
        
    Returns:
        class: ダミー戦略検出器クラス
    """
    class DummyStrategyDetectorWithPropagation(base_class):
        """テスト用のダミー戦略検出器クラス
        
        テスト用のインターフェース互換のシンプルな実装を提供
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
            print("Created DummyStrategyDetectorWithPropagation instance")
        
        def detect_wind_shifts_with_propagation(self, course_data, wind_field):
            """テスト用の空実装 - 風向シフト検出"""
            print("Called dummy detect_wind_shifts_with_propagation")
            return []
            
        def _detect_wind_shifts_in_legs(self, course_data, wind_field, target_time):
            """テスト用の空実装 - レグ内風向シフト検出"""
            return []
            
        def _get_wind_at_position(self, lat, lon, time, wind_field):
            """テスト用の空実装 - 位置風情報取得"""
            return None
        
        def detect_optimal_tacks(self, course_data, wind_field):
            """テスト用の空実装 - 最適タック検出"""
            return []
            
        def detect_laylines(self, course_data, wind_field):
            """テスト用の空実装 - レイライン検出"""
            return []
    
    # クラス名を設定
    DummyStrategyDetectorWithPropagation.__name__ = "DummyStrategyDetectorWithPropagation"
    
    return DummyStrategyDetectorWithPropagation

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